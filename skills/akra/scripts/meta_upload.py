#!/usr/bin/env python3
"""Post an akra episode as a Facebook Page Reel and an Instagram Reel (Meta Graph API, Page token).

Setup once per channel (from the project root, same venv as youtube_upload.py: .venv-youtube has `requests`):
  Before: a Facebook Page (Instagram professional account linked to it, if you post to Instagram) and a Meta app
  (developers.facebook.com; `setup` prints the steps). Then, in your own Terminal:

  .venv-youtube/bin/python meta_upload.py setup --channel channels/<id> [--platforms fb,ig] [--page <id>]

  setup asks for META_APP_ID / META_APP_SECRET when .env lacks them (secret typed hidden, saved to .env, chmod 600),
  logs in through the browser, lets you pick the Page, asks which platforms to schedule (Facebook, Instagram or
  both), writes facebook_page / instagram / meta.platforms to channel.json and, when Instagram is on, installs the
  launchd job that runs `due` every 10 minutes (macOS; prints a cron line elsewhere).

  .venv-youtube/bin/python meta_upload.py auth --channel channels/<id>   # log in again (token only)
  .venv-youtube/bin/python meta_upload.py upload channels/<id>/episodes/ep-012.json --schedule [--only fb|ig]
                                        # posts to channel.json meta.platforms; --only overrides for one episode
  .venv-youtube/bin/python meta_upload.py due [--channel channels/<id>]  # publish Instagram Reels that are due

auth: Facebook Login in the browser -> long-lived user token -> Page token (does not expire) + the linked
Instagram account id, stored in .meta-<account>-token.json (gitignored, chmod 600).

upload --schedule:
  Facebook: the Reel is uploaded now and scheduled by Facebook at scheduled_at (needs 15+ min ahead).
  Instagram: the Graph API cannot schedule. The episode is marked `instagram_pending` and `due` uploads and
  publishes it once scheduled_at has passed (run `due` from launchd/cron every 10 min; the Mac must be on).
--at <ISO+offset> sets a Meta-only slot (meta_scheduled_at) when it differs from the YouTube scheduled_at.
Without --schedule both are published now. Writes facebook_* / instagram_* fields back to the episode.
Caption = episode description + hashtags (#shorts dropped).
"""
import argparse
import datetime as dt
import getpass
import glob
import http.server
import re
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.parse
import webbrowser

try:
    import requests
except ImportError:                                           # setup/doctor helpers work without it
    requests = None

GRAPH = "https://graph.facebook.com/v23.0"
RUPLOAD = "https://rupload.facebook.com"
SCOPES = ["pages_show_list", "pages_read_engagement", "pages_manage_posts", "business_management",
          "instagram_basic", "instagram_content_publish"]
PORT = 8765
REDIRECT = f"http://localhost:{PORT}/"
PLATFORMS = {"fb": "facebook", "ig": "instagram"}
LABEL = "com.akra.meta-due"
APP_STEPS = """No Meta keys yet. Create an app once (free, development mode is enough):
  1. developers.facebook.com -> My Apps -> Create app -> use case "Manage everything on your Page"
     (+ "Manage messaging & content on Instagram" if posting to Instagram).
  2. In each use case: Customize -> Add permissions pages_show_list, pages_read_engagement, pages_manage_posts,
     business_management (+ instagram_basic, instagram_content_publish).
  3. Facebook Login -> Settings -> Valid OAuth Redirect URIs: http://localhost:8765/
  4. App settings -> Basic: copy the App ID and App Secret here (never into a chat)."""


def root():
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, "skills", "akra")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            sys.exit("project root (skills/akra) not found")
        d = parent


def env(key):
    if os.environ.get(key):
        return os.environ[key]
    f = os.path.join(root(), ".env")
    if os.path.exists(f):
        for line in open(f, encoding="utf-8"):
            if line.startswith(key + "="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    sys.exit(f"{key} missing: add it to .env")


def channel_for(path):
    d = os.path.abspath(path)
    if not os.path.isdir(d):
        d = os.path.dirname(d)
    for cand in (d, os.path.dirname(d)):
        f = os.path.join(cand, "channel.json")
        if os.path.isfile(f):
            return json.load(open(f, encoding="utf-8"))
    sys.exit(f"channel.json not found for {path}")


def token_path(ch):
    return os.path.join(root(), f".meta-{ch.get('meta_account') or ch['id']}-token.json")


def api(method, path, **params):
    r = requests.request(method, path if path.startswith("http") else f"{GRAPH}/{path}", data=params if method != "GET" else None,
                         params=params if method == "GET" else None, timeout=120)
    j = r.json() if r.content else {}
    if r.status_code >= 400 or "error" in j:
        sys.exit(f"Graph API error on {path}: {json.dumps(j.get('error', j))[:500]}")
    return j


# ---- auth ----------------------------------------------------------------------------------------------
def oauth_pages():
    """Browser Facebook Login -> the Pages this login manages, each with its linked Instagram username."""
    app_id, secret = env("META_APP_ID"), env("META_APP_SECRET")
    state, got = secrets.token_urlsafe(16), {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "state" in q:
                got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Login complete. You can close this tab.</h2>".encode())

        def log_message(self, *_):
            pass

    url = "https://www.facebook.com/v23.0/dialog/oauth?" + urllib.parse.urlencode(
        {"client_id": app_id, "redirect_uri": REDIRECT, "state": state, "scope": ",".join(SCOPES), "response_type": "code"})
    srv = http.server.HTTPServer(("localhost", PORT), H)
    print("Facebook login (Page admin) in the browser...", flush=True)
    print("LOGIN_URL " + url, flush=True)
    if not os.environ.get("META_NO_BROWSER"):
        webbrowser.open(url)
    while "state" not in got:
        srv.handle_request()
    if got.get("state") != state:
        sys.exit("state mismatch: login cancelled")
    if "code" not in got:
        sys.exit(f"login failed: {got.get('error_description') or got}")
    short = api("GET", "oauth/access_token", client_id=app_id, client_secret=secret, redirect_uri=REDIRECT, code=got["code"])
    long_ = api("GET", "oauth/access_token", grant_type="fb_exchange_token", client_id=app_id, client_secret=secret,
                fb_exchange_token=short["access_token"])
    pages = api("GET", "me/accounts", access_token=long_["access_token"], fields="id,name,access_token,instagram_business_account")
    out = []
    for p in pages.get("data", []):
        ig = (p.get("instagram_business_account") or {}).get("id")
        name = api("GET", ig, fields="username", access_token=p["access_token"]).get("username") if ig else None
        out.append({**p, "ig_user_id": ig, "ig_username": name})
    return out


def pick_page(pages, page_id=None, ask=None):
    """The Page to use: page_id when given, the only one, or the user's pick (ask(prompt) -> answer)."""
    if not pages:
        sys.exit("this login manages no Facebook Page (create a Page first, or log in as a Page admin)")
    if page_id:
        page = next((p for p in pages if p["id"] == str(page_id)), None)
        return page or sys.exit(f"Page {page_id} not in the pages this login manages: {[p['name'] for p in pages]}")
    if len(pages) == 1:
        return pages[0]
    lines = [f"  {i}. {p['name']} (id {p['id']}, Instagram @{p.get('ig_username') or '-'})" for i, p in enumerate(pages, 1)]
    if ask is None:
        sys.exit("this login manages several Pages, repeat with --page <id>:\n" + "\n".join(lines))
    print("Pages managed by this login:\n" + "\n".join(lines))
    while True:
        a = ask("Pilih nomor Page: ").strip()
        if a.isdigit() and 1 <= int(a) <= len(pages):
            return pages[int(a) - 1]
        print(f"type a number 1-{len(pages)}")


def save_token(ch, page):
    tok = {"page_id": page["id"], "page_name": page["name"], "page_token": page["access_token"],
           "ig_user_id": page.get("ig_user_id"), "ig_username": page.get("ig_username"),
           "saved": dt.datetime.now().isoformat(timespec="seconds")}
    p = token_path(ch)
    with open(p, "w") as f:
        f.write(json.dumps(tok, indent=2))
    os.chmod(p, 0o600)
    return p


def auth(a):
    ch = channel_for(a.channel)
    page_id = str((ch.get("facebook_page") or {}).get("id") or sys.exit("channel.json has no facebook_page.id (run setup)"))
    page = pick_page(oauth_pages(), page_id)
    want = (ch.get("instagram") or {}).get("handle")
    if want and page.get("ig_username") and page["ig_username"].lower() != want.lower():
        sys.exit(f"Page is linked to Instagram @{page['ig_username']}, channel.json expects @{want}")
    p = save_token(ch, page)
    print(f"logged in: Page '{page['name']}', Instagram @{page.get('ig_username') or '-'} -> {os.path.basename(p)}")


# ---- setup ---------------------------------------------------------------------------------------------
def parse_platforms(text):
    """'fb', 'ig', 'fb,ig', '1', '2', '3' (menu numbers) -> ['facebook'] / ['instagram'] / both."""
    t = (text or "").strip().lower().replace(" ", "")
    menu = {"1": ["facebook"], "2": ["instagram"], "3": ["facebook", "instagram"]}
    if t in menu:
        return menu[t]
    names = []
    for part in t.split(","):
        key = {"facebook": "fb", "instagram": "ig"}.get(part, part)
        if key not in PLATFORMS:
            raise ValueError(f"unknown platform: {part!r} (use fb, ig, or fb,ig)")
        if PLATFORMS[key] not in names:
            names.append(PLATFORMS[key])
    return [n for n in ("facebook", "instagram") if n in names]


def set_env(key, value, root_dir=None):
    """Write KEY=value into <root>/.env (replace or append), file mode 600. The value is never printed."""
    f = os.path.join(root_dir or root(), ".env")
    lines = open(f, encoding="utf-8").read().splitlines() if os.path.exists(f) else []
    lines = [ln for ln in lines if not ln.startswith(key + "=")] + [f"{key}={value}"]
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    os.chmod(f, 0o600)


def has_env(key, root_dir=None):
    if os.environ.get(key):
        return True
    f = os.path.join(root_dir or root(), ".env")
    return os.path.exists(f) and any(ln.startswith(key + "=") and ln.split("=", 1)[1].strip().strip("\"'")
                                     for ln in open(f, encoding="utf-8"))


def channel_platforms(ch, only=None):
    """Platforms one upload posts to: --only, else channel.json meta.platforms, else both (older channels)."""
    if only:
        return [PLATFORMS[only]]
    return list((ch.get("meta") or {}).get("platforms") or ["facebook", "instagram"])


def apply_channel(ch, page, platforms):
    """channel.json fields setup writes (in place): facebook_page.id, instagram handle, meta.platforms."""
    fb = dict(ch.get("facebook_page") or {})
    fb["id"] = page["id"]
    ch["facebook_page"] = fb
    if "instagram" in platforms:
        ig = dict(ch.get("instagram") or {})
        ig["handle"] = page["ig_username"]
        ig.setdefault("url", f"https://www.instagram.com/{page['ig_username']}/")
        ig["linked_page"] = True
        ch["instagram"] = ig
    ch["meta"] = {**(ch.get("meta") or {}), "platforms": platforms}
    return ch


def plist_text(python, script, workdir, log):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key><array>
    <string>{python}</string>
    <string>{script}</string>
    <string>due</string>
  </array>
  <key>WorkingDirectory</key><string>{workdir}</string>
  <key>StartInterval</key><integer>600</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict></plist>
"""


def due_python(root_dir):
    venv = os.path.join(root_dir, ".venv-youtube", "bin", "python")
    return venv if os.path.isfile(venv) else sys.executable


def install_due(root_dir=None, home=None, run=subprocess.run, platform=sys.platform):
    """Install the launchd job that runs `due` every 10 min. Returns 'installed', 'unchanged' or 'cron'."""
    root_dir = root_dir or root()
    home = home or os.path.expanduser("~")
    script = os.path.join(root_dir, "skills", "akra", "scripts", "meta_upload.py")
    if platform != "darwin":
        print(f"not macOS: add this to crontab -e:\n*/10 * * * * cd {root_dir} && {due_python(root_dir)} {script} due")
        return "cron"
    path = os.path.join(home, "Library", "LaunchAgents", LABEL + ".plist")
    text = plist_text(due_python(root_dir), script, root_dir, os.path.join(home, "Library", "Logs", "akra-meta-due.log"))
    if os.path.exists(path) and open(path, encoding="utf-8").read() == text:
        return "unchanged"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    domain = f"gui/{os.getuid()}"
    run(["launchctl", "bootout", domain, path], capture_output=True)
    r = run(["launchctl", "bootstrap", domain, path], capture_output=True)
    if r.returncode:
        sys.exit(f"launchctl bootstrap failed ({r.returncode}); run: launchctl bootstrap {domain} {path}")
    return "installed"


def setup(a):
    interactive = sys.stdin.isatty()
    ask = input if interactive else None
    rd = root()
    ch_dir = os.path.abspath(a.channel)
    ch_file = os.path.join(ch_dir, "channel.json")
    ch = channel_for(a.channel)
    if not (has_env("META_APP_ID", rd) and has_env("META_APP_SECRET", rd)):
        print(APP_STEPS)
        if not interactive:
            sys.exit("fill META_APP_ID and META_APP_SECRET in .env, or run this setup in your own Terminal")
        set_env("META_APP_ID", input("META_APP_ID: ").strip() or sys.exit("App ID is empty"), rd)
        set_env("META_APP_SECRET", getpass.getpass("META_APP_SECRET (hidden): ").strip() or sys.exit("App Secret is empty"), rd)
        print("saved to .env")
    if a.platforms:
        platforms = parse_platforms(a.platforms)
    elif interactive:
        while True:
            try:
                platforms = parse_platforms(input("Schedule to where? 1 = Facebook, 2 = Instagram, 3 = both: "))
                break
            except ValueError as e:
                print(e)
    else:
        sys.exit("choose a platform: --platforms fb, ig, or fb,ig")
    page = pick_page(oauth_pages(), a.page or (ch.get("facebook_page") or {}).get("id"), ask)
    if "instagram" in platforms and not page.get("ig_username"):
        sys.exit(f"Page '{page['name']}' is not linked to a professional Instagram account: link it first, or choose --platforms fb")
    want = (ch.get("instagram") or {}).get("handle")
    if "instagram" in platforms and want and want.lower() != page["ig_username"].lower():
        sys.exit(f"Page '{page['name']}' is linked to @{page['ig_username']}, channel.json says @{want}")
    save_token(ch, page)
    apply_channel(ch, page, platforms)
    with open(ch_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(ch, indent=2, ensure_ascii=False) + "\n")
    print(f"channel {ch['id']}: Page '{page['name']}'" + (f", Instagram @{page['ig_username']}" if "instagram" in platforms else "")
          + f", platform: {', '.join(platforms)}")
    if "instagram" in platforms and not a.no_due:
        print({"installed": "Instagram automatic job (due, every 10 minutes) installed",
               "unchanged": "Instagram automatic job already installed",
               "cron": "add the cron line above so Instagram gets posted"}[install_due(rd)])
    print("done: later uploads use these platforms (--only fb|ig for an exception)")


def load_token(ch):
    p = token_path(ch)
    if not os.path.exists(p):
        sys.exit(f"not logged in: run `meta_upload.py auth --channel channels/{ch['id']}` first")
    return json.load(open(p))


# ---- posting -------------------------------------------------------------------------------------------
def caption(ep):
    tags = " ".join(h for h in ep.get("hashtags", []) if h.lower() != "#shorts")
    text = re.sub(r"#shorts\b[ \t]*", "", ep["description"], flags=re.I).strip()
    return (text + ("\n\n" + tags if tags and tags not in text else ""))[:2200]


def video_file(ep, ep_path, override=None):
    f = override or ep.get("render")
    if not f:
        sys.exit("episode has no render path")
    f = f if os.path.isabs(f) else os.path.join(root(), f)
    if not os.path.isfile(f):
        alt = glob.glob(os.path.join(os.path.dirname(ep_path), f"{ep['id']}-assets", "*.mp4"))
        f = alt[0] if alt else sys.exit(f"video not found: {f}")
    return f


def rupload(url, token, f):
    size = os.path.getsize(f)
    with open(f, "rb") as fh:
        r = requests.post(url, data=fh, timeout=900, headers={"Authorization": f"OAuth {token}", "offset": "0",
                                                              "file_size": str(size), "Content-Type": "application/octet-stream"})
    if r.status_code >= 400:
        sys.exit(f"upload failed ({r.status_code}): {r.text[:400]}")
    return r.json() if r.content else {}


def when_utc(ep):
    w = dt.datetime.fromisoformat(ep.get("meta_scheduled_at") or ep["scheduled_at"])
    if w.tzinfo is None:
        sys.exit("scheduled_at needs a timezone offset")
    return w


def post_facebook(ep, f, tok, schedule):
    pid, t = tok["page_id"], tok["page_token"]
    start = api("POST", f"{pid}/video_reels", upload_phase="start", access_token=t)
    vid = start["video_id"]
    rupload(start.get("upload_url") or f"{RUPLOAD}/video-upload/v23.0/{vid}", t, f)
    fin = {"upload_phase": "finish", "video_id": vid, "description": caption(ep), "access_token": t}
    if schedule:
        w = when_utc(ep)
        if w <= dt.datetime.now(w.tzinfo) + dt.timedelta(minutes=15):
            sys.exit(f"slot {w.isoformat()} is not 15+ min in the future")
        fin.update(video_state="SCHEDULED", scheduled_publish_time=str(int(w.timestamp())))
    else:
        fin["video_state"] = "PUBLISHED"
    api("POST", f"{pid}/video_reels", **fin)
    ep["facebook_video_id"] = vid
    ep["facebook_url"] = f"https://www.facebook.com/reel/{vid}"
    print(f"facebook: {ep['facebook_url']}  " + (f"scheduled {when_utc(ep).isoformat()}" if schedule else "published"))


def post_instagram(ep, f, tok):
    ig, t = tok.get("ig_user_id") or sys.exit("no Instagram account linked to the Page (run auth again)"), tok["page_token"]
    c = api("POST", f"{ig}/media", media_type="REELS", upload_type="resumable", caption=caption(ep), share_to_feed="true", access_token=t)
    cid = c["id"]
    rupload(c.get("uri") or f"{RUPLOAD}/ig-api-upload/v23.0/{cid}", t, f)
    for _ in range(90):                                       # processing usually takes 30-90 s
        s = api("GET", cid, fields="status_code,status", access_token=t)
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            sys.exit(f"instagram processing failed: {s}")
        time.sleep(10)
    else:
        sys.exit("instagram processing timed out")
    media = api("POST", f"{ig}/media_publish", creation_id=cid, access_token=t)["id"]
    link = api("GET", media, fields="permalink", access_token=t).get("permalink")
    ep["instagram_media_id"], ep["instagram_url"] = media, link
    ep["instagram_published_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    ep.pop("instagram_pending", None)
    print(f"instagram: {link}")


def save(ep, path):
    json.dump(ep, open(path, "w"), indent=2, ensure_ascii=False)


def upload(a):
    ep = json.load(open(a.episode, encoding="utf-8"))
    ch = channel_for(a.episode)
    tok = load_token(ch)
    f = video_file(ep, a.episode, a.file)
    if a.at:                                                  # Meta slot differs from the YouTube scheduled_at
        dt.datetime.fromisoformat(a.at).utcoffset() is not None or sys.exit("--at needs a timezone offset")
        ep["meta_scheduled_at"] = a.at
    if a.dry_run:
        print(json.dumps({"video": f, "scheduled_at": ep.get("scheduled_at"), "caption": caption(ep)}, indent=2, ensure_ascii=False))
        return
    plats = channel_platforms(ch, a.only)
    for name in ("facebook", "instagram"):
        if name not in plats:
            print(f"{name}: skipped (not in channel meta.platforms)")
    if "facebook" in plats:
        if ep.get("facebook_video_id") and not a.force:
            print(f"facebook: already posted ({ep['facebook_url']}), use --force to post again")
        else:
            post_facebook(ep, f, tok, a.schedule)
            save(ep, a.episode)
    if "instagram" in plats:
        if ep.get("instagram_media_id") and not a.force:
            print(f"instagram: already posted ({ep['instagram_url']})")
        elif a.schedule:
            ep["instagram_pending"] = True
            print(f"instagram: queued, `due` publishes it after {when_utc(ep).isoformat()}")
        else:
            post_instagram(ep, f, tok)
        save(ep, a.episode)


MIN_GAP = dt.timedelta(minutes=55)   # one Instagram post per channel per hour, even after the Mac slept


def due(a):
    pattern = os.path.join(root(), a.channel if a.channel else "channels/*", "episodes", "*.json")
    now, last, eps = dt.datetime.now(dt.timezone.utc), {}, []
    for p in sorted(glob.glob(pattern)):
        ep = json.load(open(p, encoding="utf-8"))
        cid = os.path.basename(os.path.dirname(os.path.dirname(p)))
        if ep.get("instagram_published_at"):
            last[cid] = max(last.get(cid, ""), ep["instagram_published_at"])
        if ep.get("instagram_pending") and not ep.get("instagram_media_id") and when_utc(ep) <= now:
            eps.append((when_utc(ep), cid, p, ep))
    for _, cid, p, ep in sorted(eps, key=lambda x: x[0]):
        if cid in last and now - dt.datetime.fromisoformat(last[cid]) < MIN_GAP:
            continue
        print(f"{os.path.basename(p)}: publishing to Instagram (slot {when_utc(ep).isoformat()})", flush=True)
        ch = channel_for(p)
        post_instagram(ep, video_file(ep, p), load_token(ch))
        save(ep, p)
        last[cid] = ep["instagram_published_at"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("auth")
    s.add_argument("--channel", required=True, help="channels/<id>")
    u = sub.add_parser("upload")
    u.add_argument("episode")
    u.add_argument("--file")
    u.add_argument("--schedule", action="store_true")
    u.add_argument("--at", help="Meta slot (ISO with offset) instead of scheduled_at, e.g. 2026-01-15T19:00:00-05:00")
    u.add_argument("--only", choices=["fb", "ig"])
    u.add_argument("--dry-run", action="store_true")
    u.add_argument("--force", action="store_true")
    st = sub.add_parser("setup", help="Meta keys + login + pick Page + pick platforms + Instagram automatic job")
    st.add_argument("--channel", required=True, help="channels/<id>")
    st.add_argument("--platforms", help="fb, ig, or fb,ig (without it: asked)")
    st.add_argument("--page", help="Page id if the login manages several Pages")
    st.add_argument("--no-due", action="store_true", help="do not install the launchd automatic job")
    d = sub.add_parser("due")
    d.add_argument("--channel", help="channels/<id> (default: all channels)")
    a = ap.parse_args()
    {"auth": auth, "setup": setup, "upload": upload, "due": due}[a.cmd](a)


if __name__ == "__main__":
    main()
