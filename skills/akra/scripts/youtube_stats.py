#!/usr/bin/env python3
"""Pull YouTube Analytics for a channel's published akra episodes (mode `review`).

Per video: views, average view duration, average % viewed, likes, comments, shares, subscribers gained,
and HOLD@3s, the share of viewers still watching 3 seconds in, read from the audience-retention curve.
HOLD@3s is the best signal the API gives for hook strength. The "stayed to watch / swiped away" figure
for Shorts exists only in YouTube Studio, so ask the user for it when it matters.

Setup (once per Google project):
  Cloud Console -> APIs & Services -> enable "YouTube Analytics API" (and "YouTube Data API v3", already on for uploads).
  .venv-youtube/bin/python youtube_stats.py auth [--channel channels/<id>]   # browser login, read-only scopes

Its token is separate from the upload token (.youtube-analytics-token.json, gitignored by the
.youtube-*token.json rule), so logging in here never touches the upload login. A channel with
`youtube_account` in channel.json gets its own token (.youtube-<account>-analytics-token.json).

Usage:
  .venv-youtube/bin/python youtube_stats.py pull channels/<id>            # table + review-log.csv rows
  .venv-youtube/bin/python youtube_stats.py pull channels/<id> --no-write # table only
  .venv-youtube/bin/python youtube_stats.py pull channels/<id> --json     # raw numbers for analysis

YouTube Analytics data lags about 2-3 days, so videos newer than that show as "too new".
"""
import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from youtube_upload import channel_for, root, token_name  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/youtube.readonly"]
TOKEN = token_name({}, "analytics")      # default; per channel via token_name(channel, "analytics")
LAG_DAYS = 2
METRICS = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained"
LOG_FIELDS = ["week", "episode_id", "published_on", "hook_type", "views", "stayed_to_watch_pct", "avg_view_duration_s",
              "likes", "comments", "shares", "subs_gained", "notes", "avg_view_pct", "hold_3s_pct", "duration_s", "title"]


def credentials(interactive=True, channel=None):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    r = root()
    tok = os.path.join(r, token_name(channel, "analytics"))
    creds = Credentials.from_authorized_user_file(tok, SCOPES) if os.path.exists(tok) else None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None                                   # Testing-mode refresh tokens expire after ~7 days
    if not creds or not creds.valid:
        if not interactive:
            sys.exit("not logged in for analytics: run `youtube_stats.py auth` first")
        flow = InstalledAppFlow.from_client_secrets_file(os.path.join(r, "client_secret.json"), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True,
                                      authorization_prompt_message="Opening the browser for Google login (analytics, read-only)...")
    open(tok, "w").write(creds.to_json())
    os.chmod(tok, 0o600)
    return creds


def video_id(url):
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def hook_type(ep):
    """Episode field wins; otherwise a rough guess from the hook text (same labels as review.md)."""
    if ep.get("hook_type"):
        return ep["hook_type"]
    h = ep.get("hook", "")
    hl = h.lower()
    if h.rstrip().endswith("?"):
        return "question"
    if re.search(r"\b(he|she|his|her|a man|a woman|a boy|a girl)\b", hl):
        return "story"
    if re.search(r"\b(but|still|never|not|on purpose|actually|isn't|doesn't|don't|can't|won't)\b|n't\b", hl):
        return "contradiction"
    if re.search(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million)\b", hl):
        return "number"
    if re.search(r"\b(you|your)\b", hl):
        return "you"
    return "statement"


def episodes(channel_dir):
    out = []
    for f in sorted(glob.glob(os.path.join(channel_dir, "episodes", "*.json"))):
        ep = json.load(open(f))
        vid = video_id(ep.get("youtube_url"))
        if ep.get("status") == "published" and vid:
            ep["_vid"] = vid
            ep["_pub"] = (ep.get("scheduled_at") or "")[:10]
            out.append(ep)
    return out


def hold_at(curve, seconds, duration):
    """Linear read of audienceWatchRatio at `seconds` from [(elapsedRatio, watchRatio), ...]."""
    if not curve or not duration:
        return None
    x = min(1.0, seconds / duration)
    pts = sorted(curve)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]


def iso_duration(s):
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    return sum(int(v or 0) * k for v, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def pull(a):
    from googleapiclient.discovery import build
    creds = credentials(interactive=False, channel=channel_for(a.channel_dir))
    yta = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    eps = episodes(a.channel_dir)
    if not eps:
        sys.exit("no published episodes with a youtube_url")
    today = dt.date.today()
    end = (today - dt.timedelta(days=LAG_DAYS)).isoformat()
    start = min(e["_pub"] for e in eps) or end

    # durations + public counters from the Data API (50 ids per call)
    meta = {}
    ids = [e["_vid"] for e in eps]
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="contentDetails,statistics,status", id=",".join(ids[i:i + 50])).execute()
        for it in r.get("items", []):
            meta[it["id"]] = dict(duration=iso_duration(it["contentDetails"]["duration"]),
                                  public_views=int(it["statistics"].get("viewCount", 0)),
                                  privacy=it["status"]["privacyStatus"])

    rows = {}
    if start <= end:
        cols = ["video"] + METRICS.split(",")
        r = yta.reports().query(ids="channel==MINE", startDate=start, endDate=end, metrics=METRICS, dimensions="video",
                                filters="video==" + ",".join(ids), maxResults=200, sort="-views").execute()
        for row in r.get("rows", []):
            rows[row[0]] = dict(zip(cols, row))

    report = []
    for e in eps:
        vid, m, r = e["_vid"], meta.get(e["_vid"], {}), rows.get(e["_vid"])
        rec = dict(episode_id=e["id"], title=e.get("title", ""), hook=e.get("hook", ""), hook_type=hook_type(e),
                   topic=e.get("topic", ""), published_on=e["_pub"], video_id=vid, duration_s=m.get("duration"),
                   privacy=m.get("privacy"), public_views=m.get("public_views"))
        too_new = not e["_pub"] or e["_pub"] > end
        if r and not too_new:
            rec.update(views=int(r["views"]), avg_view_duration_s=round(float(r["averageViewDuration"]), 1),
                       avg_view_pct=round(float(r["averageViewPercentage"]), 1), likes=int(r["likes"]),
                       comments=int(r["comments"]), shares=int(r["shares"]), subs_gained=int(r["subscribersGained"]),
                       minutes_watched=round(float(r["estimatedMinutesWatched"]), 1))
            try:
                c = yta.reports().query(ids="channel==MINE", startDate=e["_pub"], endDate=end, metrics="audienceWatchRatio",
                                        dimensions="elapsedVideoTimeRatio", filters=f"video=={vid}").execute()
                curve = [(float(x), float(y)) for x, y in c.get("rows", [])]
                h = hold_at(curve, 3, m.get("duration"))
                rec["hold_3s_pct"] = round(h * 100, 1) if h is not None else None
                h_end = hold_at(curve, (m.get("duration") or 1) - 1, m.get("duration"))
                rec["hold_end_pct"] = round(h_end * 100, 1) if h_end is not None else None
            except Exception as ex:                        # retention needs enough views; keep the rest of the row
                rec["hold_3s_pct"] = None
                rec["retention_error"] = str(ex)[:120]
        rec["status"] = "too new" if too_new else ("ok" if r else "no data yet")
        report.append(rec)

    # channel totals for the YPP check (Shorts views, last 90 days)
    ch = yt.channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"]
    d90 = (today - dt.timedelta(days=90 + LAG_DAYS)).isoformat()
    totals = dict(subscribers=int(ch.get("subscriberCount", 0)), channel_views=int(ch.get("viewCount", 0)), views_90d=None)
    try:
        r = yta.reports().query(ids="channel==MINE", startDate=d90, endDate=end, metrics="views",
                                dimensions="creatorContentType", filters="creatorContentType==SHORTS").execute()
        totals["views_90d"] = int(r["rows"][0][1]) if r.get("rows") else 0
    except Exception:
        r = yta.reports().query(ids="channel==MINE", startDate=d90, endDate=end, metrics="views").execute()
        totals["views_90d"] = int(r["rows"][0][0]) if r.get("rows") else 0
        totals["views_90d_note"] = "all content (Shorts filter unavailable)"

    if a.json:
        print(json.dumps(dict(as_of=end, totals=totals, videos=report), indent=2, ensure_ascii=False))
    else:
        print_table(report, totals, end)
    if not a.no_write:
        n = write_log(a.channel_dir, report, today)
        print(f"\nreview-log.csv: {n} row(s) written for {today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}")


def print_table(report, totals, end):
    ok = [r for r in report if r["status"] == "ok"]
    print(f"Data through {end} (YouTube lags ~{LAG_DAYS} days)\n")
    print(f"{'ep':7} {'views':>7} {'avg%':>6} {'hold3s':>7} {'end%':>6} {'avgs':>5} {'likes':>5} {'subs':>4}  hook type      title")
    for r in sorted(ok, key=lambda r: -(r.get("avg_view_pct") or 0)):
        f = lambda k, w, p=0: (f"{r[k]:>{w}.{p}f}" if isinstance(r.get(k), (int, float)) else f"{'-':>{w}}")  # noqa: E731
        print(f"{r['episode_id']:7} {f('views', 7)} {f('avg_view_pct', 6, 1)} {f('hold_3s_pct', 7, 1)} {f('hold_end_pct', 6, 1)} "
              f"{f('avg_view_duration_s', 5, 1)} {f('likes', 5)} {f('subs_gained', 4)}  {r['hook_type']:13}  {r['title'][:44]}")
    rest = [r for r in report if r["status"] != "ok"]
    if rest:
        print("\nnot counted yet: " + ", ".join(f"{r['episode_id']} ({r['status']})" for r in rest))
    if ok:
        by = {}
        for r in ok:
            by.setdefault(r["hook_type"], []).append(r)
        print("\nby hook type (mean avg% / mean hold@3s / n):")
        for k, v in sorted(by.items(), key=lambda kv: -sum(x.get("avg_view_pct") or 0 for x in kv[1]) / len(kv[1])):
            h = [x["hold_3s_pct"] for x in v if x.get("hold_3s_pct") is not None]
            hs = f"{sum(h) / len(h):5.1f}%" if h else "    - "
            print(f"  {k:13} {sum(x.get('avg_view_pct') or 0 for x in v) / len(v):5.1f}%  {hs}  n={len(v)}")
        if not any(r.get("hold_3s_pct") is not None for r in ok):
            print("  (hold@3s: YouTube returns no retention curve until a video has enough views)")
    print(f"\nYPP (re-check the current rules on YouTube): subscribers {totals['subscribers']:,} / 1,000 · "
          f"Shorts views 90d {totals['views_90d']:,} / 10,000,000" + (f" ({totals['views_90d_note']})" if totals.get("views_90d_note") else ""))


def write_log(channel_dir, report, today):
    """Upsert one row per (week, episode) into review-log.csv; extra columns are appended to the header."""
    path = os.path.join(channel_dir, "review-log.csv")
    week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    old = []
    if os.path.exists(path):
        with open(path, newline="") as fh:
            old = list(csv.DictReader(fh))
    keep = [r for r in old if not (r.get("week") == week and any(r.get("episode_id") == x["episode_id"] for x in report))]
    new = []
    for r in report:
        if r["status"] != "ok":
            continue
        new.append({k: ("" if r.get(k) is None else r.get(k, "")) for k in LOG_FIELDS} | dict(week=week, stayed_to_watch_pct=""))
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(keep + new)
    return len(new)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("auth")
    p.add_argument("--channel", help="channels/<id> whose youtube_account to log in to")
    p = sub.add_parser("pull")
    p.add_argument("channel_dir")
    p.add_argument("--no-write", action="store_true", help="do not touch review-log.csv")
    p.add_argument("--json", action="store_true", help="print raw numbers as JSON")
    a = ap.parse_args()
    if a.cmd == "auth":
        channel = channel_for(a.channel) if a.channel else {}
        credentials(interactive=True, channel=channel)
        print(f"logged in: token saved to {token_name(channel, 'analytics')}")
    else:
        from googleapiclient.errors import HttpError
        try:
            pull(a)
        except HttpError as ex:
            msg = str(ex)
            if "accessNotConfigured" in msg or "has not been used" in msg:
                link = re.search(r"https://console\.developers\.google\.com/apis/api/[^\s\"']+", msg)
                sys.exit("YouTube Analytics API is not enabled for this Google project. Enable it"
                         + (f" here: {link.group(0)}" if link else " in Cloud Console")
                         + " , wait a few minutes, then run pull again.")
            if ex.resp.status in (401, 403):
                sys.exit(f"YouTube refused the request ({ex.resp.status}). Run `youtube_stats.py auth` again; details: {msg[:300]}")
            raise


if __name__ == "__main__":
    main()
