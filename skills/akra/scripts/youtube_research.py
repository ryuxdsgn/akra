#!/usr/bin/env python3
"""Find outlier Shorts in a channel's niche (modes `ideas`, `script`, `review`).

An outlier is a Short whose views are far above its own channel's usual views (median of that channel's
recent uploads), so a hit from a small channel counts and a big channel's ordinary video does not.
The result is a reference list to learn from (topic, title and hook patterns, length), never to copy.

Uses the YouTube Data API with the read-only login of youtube_stats.py (run `youtube_stats.py auth` once).
Quota: about 100 units per query plus ~2 per channel checked; the default daily quota is 10,000.

Usage:
  .venv-youtube/bin/python youtube_research.py outliers channels/<id>                  # queries from channel.json
  .venv-youtube/bin/python youtube_research.py outliers channels/<id> --query "cara kerja kulkas" --days 30
  .venv-youtube/bin/python youtube_research.py outliers channels/<id> --no-write --json

channel.json (optional):
  "research": {"queries": ["how things work", "engineering explained"], "days": 60, "min_ratio": 3, "min_views": 20000,
               "exclude_channels": ["UC..."]}
Without `research.queries` the channel's `niche` is the one query; keep queries short (2-4 words), like a viewer would type.
Writes channels/<id>/research/<YYYY-MM-DD>-outliers.md (the agent then updates research/patterns.md).
"""
import argparse
import datetime as dt
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MAX_SHORT_S = 180          # YouTube Shorts can be up to 3 minutes
RECENT_UPLOADS = 15        # uploads per channel used for its baseline
REGION = {"id": "ID", "en": None}   # language -> regionCode (None = worldwide)


def iso_duration(s):
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    return sum(int(v or 0) * k for v, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def settings(channel, a):
    """Queries, window, threshold and region from channel.json, overridden by command-line flags."""
    r = channel.get("research") or {}
    queries = a.query or r.get("queries") or ([channel["niche"]] if channel.get("niche") else [])
    if not queries:
        sys.exit("no query: add research.queries (or niche) to channel.json, or pass --query")
    lang = channel.get("language", "en")
    return {"queries": queries,
            "days": a.days or r.get("days") or 60,
            "min_ratio": a.min_ratio or r.get("min_ratio") or 3.0,
            "min_views": a.min_views if a.min_views is not None else r.get("min_views", 20_000),
            "language": lang,
            "region": REGION.get(lang, lang.upper() if len(lang) == 2 else None),
            "exclude": set(r.get("exclude_channels") or []) | ({channel["youtube_channel_id"]} if channel.get("youtube_channel_id") else set())}


def baseline(views, exclude=None):
    """Median views of a channel's recent uploads, leaving out the candidate itself. None if too few."""
    vals = [v for vid, v in views if vid != exclude]
    return statistics.median(vals) if len(vals) >= 3 else None


def score(videos, baselines, min_ratio, exclude_channels=(), min_views=0):
    """videos: [{id, channel_id, views, duration_s, ...}]; baselines: {channel_id: [(video_id, views), ...]}.
    Returns Shorts with ratio = views / channel median >= min_ratio and views >= min_views, best first."""
    out = []
    for v in videos:
        if v["channel_id"] in exclude_channels or not 0 < v["duration_s"] <= MAX_SHORT_S or v["views"] < min_views:
            continue
        base = baseline(baselines.get(v["channel_id"], []), v["id"])
        if not base:
            continue
        ratio = v["views"] / base
        if ratio >= min_ratio:
            out.append(dict(v, baseline=round(base), ratio=round(ratio, 1)))
    return sorted(out, key=lambda x: (-x["ratio"], -x["views"]))


def render_md(rows, cfg, today):
    q = ", ".join(f'"{x}"' for x in cfg["queries"])
    lines = [f"# Outlier Shorts · {today}", "",
             f"Queries: {q} · last {cfg['days']} days · region {cfg['region'] or 'worldwide'} · "
             f"outlier = views ≥ {cfg['min_ratio']}× that channel's median of its recent uploads and ≥ {cfg.get('min_views', 0):,} views.",
             "Search results include off-topic hits (memes, other niches): skip them when updating patterns.md.",
             "Learn the pattern (topic, title/hook, length, angle); never copy a title or script.", ""]
    if not rows:
        return "\n".join(lines + ["No outliers found. Widen the window (--days) or try other queries.", ""])
    lines += ["| # | × median | views | subs | age (d) | dur (s) | title | channel | query |",
              "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        title = r["title"].replace("|", "/")
        lines.append(f"| {i} | {r['ratio']} | {r['views']:,} | {r.get('subs', 0):,} | {r['age_days']} | {r['duration_s']} "
                     f"| [{title}](https://youtube.com/shorts/{r['id']}) | {r['channel'].replace('|', '/')} | {r['query']} |")
    return "\n".join(lines + [""])


def _chunks(xs, n=50):
    return [xs[i:i + n] for i in range(0, len(xs), n)]


def fetch(yt, cfg, now):
    """Search each query, then load stats for the hits and a baseline for each hit's channel."""
    after = (now - dt.timedelta(days=cfg["days"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    hits = {}
    for q in cfg["queries"]:
        kw = dict(part="id", q=q, type="video", videoDuration="short", order="viewCount",
                  publishedAfter=after, maxResults=50, relevanceLanguage=cfg["language"])
        if cfg["region"]:
            kw["regionCode"] = cfg["region"]
        for it in yt.search().list(**kw).execute().get("items", []):
            hits.setdefault(it["id"]["videoId"], q)
    videos = []
    for ids in _chunks(list(hits)):
        for it in yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids)).execute().get("items", []):
            pub = dt.datetime.fromisoformat(it["snippet"]["publishedAt"].replace("Z", "+00:00"))
            videos.append({"id": it["id"], "title": it["snippet"]["title"], "channel": it["snippet"]["channelTitle"],
                           "channel_id": it["snippet"]["channelId"], "views": int(it["statistics"].get("viewCount", 0)),
                           "duration_s": iso_duration(it["contentDetails"]["duration"]),
                           "age_days": (now - pub).days, "query": hits[it["id"]]})
    chans = sorted({v["channel_id"] for v in videos} - cfg["exclude"])
    subs, uploads = {}, {}
    for ids in _chunks(chans):
        for it in yt.channels().list(part="statistics,contentDetails", id=",".join(ids)).execute().get("items", []):
            subs[it["id"]] = int(it["statistics"].get("subscriberCount", 0) or 0)
            uploads[it["id"]] = it["contentDetails"]["relatedPlaylists"]["uploads"]
    baselines = {}
    for cid, pl in uploads.items():
        items = yt.playlistItems().list(part="contentDetails", playlistId=pl, maxResults=RECENT_UPLOADS).execute().get("items", [])
        vids = [i["contentDetails"]["videoId"] for i in items]
        if vids:
            stats = yt.videos().list(part="statistics", id=",".join(vids)).execute().get("items", [])
            baselines[cid] = [(s["id"], int(s["statistics"].get("viewCount", 0))) for s in stats]
    for v in videos:
        v["subs"] = subs.get(v["channel_id"], 0)
    return videos, baselines


def search_credentials(channel):
    """Search reads public data only, so any read-only login works: the channel's own analytics token,
    else the default one (.youtube-analytics-token.json)."""
    from youtube_upload import root, token_name
    from youtube_stats import credentials
    if channel.get("youtube_account") and not os.path.exists(os.path.join(root(), token_name(channel, "analytics"))):
        channel = {}
    return credentials(interactive=False, channel=channel)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("outliers")
    p.add_argument("channel_dir")
    p.add_argument("--query", action="append", help="search query (repeatable); default: channel.json research.queries or niche")
    p.add_argument("--days", type=int, help="look back this many days (default 60)")
    p.add_argument("--min-ratio", type=float, help="views / channel median to count as outlier (default 3)")
    p.add_argument("--min-views", type=int, help="ignore Shorts below this many views (default 20000)")
    p.add_argument("--no-write", action="store_true", help="print only; do not write research/<date>-outliers.md")
    p.add_argument("--json", action="store_true", help="print rows as JSON")
    a = ap.parse_args()

    from youtube_upload import channel_for
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    channel = channel_for(a.channel_dir)
    if not channel:
        sys.exit(f"{a.channel_dir}: channel.json not found")
    cfg = settings(channel, a)
    yt = build("youtube", "v3", credentials=search_credentials(channel), cache_discovery=False)
    now = dt.datetime.now(dt.timezone.utc)
    try:
        videos, baselines = fetch(yt, cfg, now)
    except HttpError as ex:
        if ex.resp.status == 403 and "quota" in str(ex).lower():
            sys.exit("YouTube API daily quota used up; try again tomorrow (quota resets at midnight Pacific time).")
        if ex.resp.status in (401, 403):
            sys.exit(f"YouTube refused the request ({ex.resp.status}). Run `youtube_stats.py auth` again; details: {str(ex)[:300]}")
        raise
    rows = score(videos, baselines, cfg["min_ratio"], cfg["exclude"], cfg["min_views"])
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    today = now.astimezone(dt.timezone(dt.timedelta(hours=7))).date().isoformat()
    md = render_md(rows, cfg, today)
    print(md)
    if not a.no_write:
        out = os.path.join(a.channel_dir, "research", f"{today}-outliers.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(md)
        print(f"written: {out} ({len(rows)} outliers from {len(videos)} Shorts)")


if __name__ == "__main__":
    main()
