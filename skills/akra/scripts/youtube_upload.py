#!/usr/bin/env python3
"""Upload an akra episode to YouTube with the YouTube Data API v3 (OAuth, scope youtube.upload).

Setup once (from the project root):
  uv venv --python 3.12 .venv-youtube
  uv pip install --python .venv-youtube/bin/python google-api-python-client google-auth-oauthlib
  Google Cloud: enable "YouTube Data API v3", OAuth consent screen (External, add yourself as test user,
  scope .../auth/youtube.upload), OAuth client ID type "Desktop app" -> save the JSON as client_secret.json
  in the project root. client_secret*.json and .youtube-token.json are gitignored: never commit or paste them.

  .venv-youtube/bin/python youtube_upload.py auth [--channel channels/<id>]  # browser login once, stores the token
  .venv-youtube/bin/python youtube_upload.py upload channels/<id>/episodes/ep-007.json \
      [--file path.mp4] [--privacy private|unlisted|public] [--schedule]  [--dry-run]

upload first runs validate_episode.py (the full YouTube policy gate, references/youtube-policy.md) and
refuses while it fails, listing the policy items that are not "pass". It reads title, description, hashtags
(-> tags), made_for_kids (-> selfDeclaredMadeForKids), ai_disclosure / synthetic_content
(-> containsSyntheticMedia) and scheduled_at from the Episode Package. --schedule: upload private with publishAt = scheduled_at (YouTube publishes it then).
Without --schedule the privacy is --privacy (default private). Writes youtube_url + youtube_video_id back.

The Channel Profile (channels/<id>/channel.json, found from the episode path) sets defaultLanguage /
defaultAudioLanguage (`language`, default "en") and the category (`youtube_category_id`, default "28").
Each YouTube channel (Brand Account) needs its own login: set `youtube_account` in channel.json and the
token becomes .youtube-<account>-token.json (log in with `auth --channel channels/<id>`). Without it the
shared .youtube-token.json is used.

Unaudited API projects: YouTube locks API uploads to private. Until the project passes the YouTube API
Services audit, upload private and switch to public / schedule in YouTube Studio.
"""
import argparse
import datetime as dt
import json
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CATEGORY_SCIENCE_TECH = "28"


def root():
    d = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(d, "client_secret.json")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            sys.exit("client_secret.json not found in this folder or any parent")
        d = parent


def token_name(channel, kind=""):
    """Token file for a channel's YouTube account; kind "" = upload, "analytics" = read-only stats."""
    acct = (channel or {}).get("youtube_account")
    parts = [p for p in (acct, kind) if p]
    return ".youtube-" + "-".join(parts + ["token"]) + ".json"


def channel_for(path):
    """Channel Profile for an episode or channel folder path; {} if none is found."""
    d = os.path.abspath(path)
    if not os.path.isdir(d):
        d = os.path.dirname(d)
    for cand in (d, os.path.dirname(d)):
        f = os.path.join(cand, "channel.json")
        if os.path.isfile(f):
            with open(f, encoding="utf-8") as fh:
                return json.load(fh)
    return {}


def credentials(interactive=True, channel=None):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    r = root()
    tok = os.path.join(r, token_name(channel))
    creds = Credentials.from_authorized_user_file(tok, SCOPES) if os.path.exists(tok) else None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None                                   # refresh token expired (Testing mode: ~7 days)
    if not creds or not creds.valid:
        if not interactive:
            sys.exit(f"not logged in ({token_name(channel)}): run `youtube_upload.py auth"
                     + (f" --channel channels/{channel['id']}`" if (channel or {}).get("youtube_account") else "`")
                     + " first")
        flow = InstalledAppFlow.from_client_secrets_file(os.path.join(r, "client_secret.json"), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True,
                                      authorization_prompt_message="Opening the browser for Google login...")
    open(tok, "w").write(creds.to_json())
    os.chmod(tok, 0o600)
    return creds


def body_for(ep, privacy, schedule, channel=None):
    channel = channel or {}
    lang = channel.get("language", "en")
    tags = [h.lstrip("#") for h in ep.get("hashtags", []) if h.lstrip("#").lower() != "shorts"]
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": bool(ep.get("made_for_kids", False)),
              "containsSyntheticMedia": bool(ep.get("ai_disclosure", False) or ep.get("synthetic_content", False))}
    if schedule:
        when = dt.datetime.fromisoformat(ep["scheduled_at"])
        if when <= dt.datetime.now(when.tzinfo) + dt.timedelta(minutes=15):
            sys.exit(f"scheduled_at {ep['scheduled_at']} is not in the future (needs 15+ min)")
        status.update(privacyStatus="private", publishAt=when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return {"snippet": {"title": ep["title"][:100], "description": ep["description"], "tags": tags,
                        "categoryId": channel.get("youtube_category_id", CATEGORY_SCIENCE_TECH),
                        "defaultLanguage": lang, "defaultAudioLanguage": lang},
            "status": status}


def policy_gate(ep_path):
    """Run validate_episode.py on the package (full YouTube policy gate, no legacy downgrade).
    Exits with the problems and the missing policy ids (references/youtube-policy.md) if it fails."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import validate_episode
    try:
        errors, _, missing = validate_episode.validate_file(ep_path, for_upload=True)
    except ValueError as exc:
        sys.exit(f"refusing to upload: {exc}")
    if errors:
        print(f"refusing to upload: validation failed ({len(errors)} problem(s))")
        for e in errors:
            print(f"  - {e}")
        if missing:
            print("policy items not pass (references/youtube-policy.md): " + ", ".join(missing))
        print(validate_episode.monetization_line(json.load(open(ep_path)), errors))
        sys.exit("fix the package, run validate_episode.py validate until OK, then ask the user again")


def upload(a):
    ep_path = os.path.abspath(a.episode)
    policy_gate(ep_path)
    ep = json.load(open(ep_path))
    for k in ("title", "description"):
        if not ep.get(k):
            sys.exit(f"episode has no {k}: run /akra package first")
    mp4 = a.file or os.path.join(os.path.dirname(ep_path), f"{ep['id']}-assets", f"{ep['id']}.mp4")
    if not os.path.isfile(mp4):
        sys.exit(f"video not found: {mp4}")
    if ep.get("youtube_url") and not a.force:
        sys.exit(f"already uploaded: {ep['youtube_url']} (use --force to upload again)")
    channel = channel_for(ep_path)
    body = body_for(ep, a.privacy, a.schedule, channel)
    print(json.dumps(body, indent=2, ensure_ascii=False))
    print(f"file: {mp4} ({os.path.getsize(mp4)/1e6:.1f} MB)  account token: {token_name(channel)}")
    if a.dry_run:
        return
    import socket
    import time
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    socket.setdefaulttimeout(180)                    # slow links: the default write timeout drops 4 MB chunks
    yt = build("youtube", "v3", credentials=credentials(interactive=False, channel=channel))
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(mp4, mimetype="video/mp4", chunksize=1024 * 1024, resumable=True))
    resp, fails = None, 0
    while resp is None:
        try:
            st, resp = req.next_chunk(num_retries=3)
        except (TimeoutError, socket.timeout, ConnectionError, OSError) as e:   # resumable: retry the same chunk
            fails += 1
            if fails > 8:
                raise
            print(f"  network error ({e.__class__.__name__}), retry {fails}/8", flush=True)
            time.sleep(min(30, 3 * fails))
            continue
        if st:
            print(f"  {int(st.progress() * 100)}%", flush=True)
    vid = resp["id"]
    got = resp.get("status", {})
    print(f"uploaded: https://youtube.com/shorts/{vid}  privacy={got.get('privacyStatus')} publishAt={got.get('publishAt')}")
    wanted_public = body["status"]["privacyStatus"] != "private"
    if (wanted_public and got.get("privacyStatus") == "private") or (body["status"].get("publishAt") and not got.get("publishAt")):
        print("! YouTube kept the video private (API project not audited yet): set public / schedule in YouTube Studio")
    ep["youtube_video_id"] = vid
    ep["youtube_url"] = f"https://youtube.com/shorts/{vid}"
    json.dump(ep, open(ep_path, "w"), indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("auth")
    p.add_argument("--channel", help="channels/<id> whose youtube_account to log in to")
    u = sub.add_parser("upload")
    u.add_argument("episode")
    u.add_argument("--file")
    u.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    u.add_argument("--schedule", action="store_true", help="private + publishAt = scheduled_at")
    u.add_argument("--dry-run", action="store_true")
    u.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.cmd == "auth":
        channel = channel_for(a.channel) if a.channel else {}
        credentials(interactive=True, channel=channel)
        print(f"logged in: token saved to {token_name(channel)}")
    else:
        upload(a)


if __name__ == "__main__":
    main()
