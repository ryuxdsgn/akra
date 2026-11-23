#!/usr/bin/env python3
"""Validator for akra Episode Packages and Channel Profiles.

Standard library only, so it runs in Claude Code, Claude.ai code execution
and ChatGPT Code Interpreter.
"""
import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

WPM = 150
MIN_WORDS, MAX_WORDS = 75, 150
# Per-language script rules (30-60 s of narration). Indonesian words are longer (more syllables),
# so a calm read is ~125 words per minute instead of ~150.
LANGUAGES = {
    "en": {"wpm": WPM, "min_words": MIN_WORDS, "max_words": MAX_WORDS, "max_title": 60},
    "id": {"wpm": 125, "min_words": 62, "max_words": 125, "max_title": 70},
}
PLATFORMS = ("youtube", "facebook", "tiktok", "instagram")
MAX_HOOK_WORDS = 10

STATUSES = ("idea", "scripted", "visuals", "edited", "published")
SHOT_TYPES = ("diagram", "stock")  # diagram = HyperFrames scene (default); stock = credited footage
# Google Flow / Veo is no longer used. Old shot types and fields are tolerated in published
# packages (warning only) so the archive keeps validating; new packages must not use them.
LEGACY_SHOT_TYPES = ("veo", "flow_image")
LEGACY_EPISODE_FIELDS = ("credit_estimate",)
LEGACY_CHANNEL_FIELDS = ("credits_per_video",)
MIN_SHOT, MAX_SHOT = 2, 8  # seconds per shot
JOIN_TOLERANCE = 0.1  # seconds allowed between one shot's end and the next start
MAX_TITLE = 60
MIN_TAGS, MAX_TAGS = 3, 5
MUSIC_SOURCES = ("youtube_audio_library", "licensed", "none")
ORIGINALITY_KEYS = ("original_script", "custom_voice_direction", "manual_edit", "added_value")
_HASHTAG = re.compile(r"#\w+")  # letters, digits, underscore

CHANNEL_STATUSES = ("testing", "active", "paused")
MIN_PER_VIDEO = 75
CHANNEL_FIELDS = {
    "id": str,
    "name": str,
    "niche": str,
    "status": str,
    "voice": dict,
    "style_bible": str,
    "videos_per_day": int,
    "started_on": str,
}
_CHANNEL_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SLOT = re.compile(r"([01]\d|2[0-3]):[0-5]\d")
LEGACY_SLOT_TZ = "Asia/Jakarta"   # legacy `posting_slots_wib` = slots in Western Indonesian Time


def posting_slots(profile: dict):
    """(field, slots, IANA timezone) of a Channel Profile's posting slots, or None when it has none.

    `posting_slots` + `timezone` is the normal form; the legacy `posting_slots_wib` means timezone Asia/Jakarta."""
    if "posting_slots" in profile:
        return "posting_slots", profile["posting_slots"], profile.get("timezone")
    if "posting_slots_wib" in profile:
        return "posting_slots_wib", profile["posting_slots_wib"], LEGACY_SLOT_TZ
    return None


def _valid_timezone(name) -> bool:
    if not isinstance(name, str) or not name.strip():
        return False
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(name)
        return True
    except Exception:  # ZoneInfoNotFoundError, ValueError (bad key), missing tz database
        return False
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

REQUIRED_FIELDS = {
    "id": str,
    "channel": str,
    "niche": str,
    "topic": str,
    "status": str,
    "hook": str,
    "script": str,
    "shots": list,
    "title": str,
    "description": str,
    "hashtags": list,
    "ai_disclosure": bool,
    "music_source": str,
    "originality_checklist": dict,
}

_WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")

# ------------------------------------------------------------ policy gate
# YouTube policy items: references/youtube-policy.md (checked 2026-11-22). Keep these ids in sync with
# that file's "Pre-upload ids" line (a test compares them).
POLICY_EPOCH = date(2026, 11, 22)    # packages dated before this without policy_check are legacy
PRE_UPLOAD_IDS = ("YT-AUTH-1", "YT-AUTH-2", "YT-FACT-1", "YT-MED-1", "YT-REUSE-1", "YT-AD-2", "YT-COPY-1",
                  "YT-COPY-2", "YT-SYN-1", "YT-SHORT-1", "YT-META-1", "YT-AD-1", "YT-TAG-1", "YT-KIDS-1",
                  "YT-SYN-2", "YT-CRED-1", "YT-UP-1")
POLICY_IDS = ("YT-CH-1", "YT-CH-2", "YT-CH-3", "YT-CH-4") + PRE_UPLOAD_IDS + ("YT-REV-1",)
# What a failed item costs (the [impact] tag in youtube-policy.md; the goal is that every episode stays monetizable).
BLOCKS, LIMITS, STRIKE = "blocks monetization", "limits ads", "strike/removal risk"
IMPACT = {
    "YT-CH-1": BLOCKS, "YT-CH-2": BLOCKS, "YT-CH-3": STRIKE, "YT-CH-4": STRIKE,
    "YT-AUTH-1": BLOCKS, "YT-AUTH-2": BLOCKS, "YT-FACT-1": STRIKE, "YT-MED-1": STRIKE, "YT-REUSE-1": BLOCKS,
    "YT-AD-2": LIMITS, "YT-COPY-1": STRIKE, "YT-COPY-2": STRIKE, "YT-SYN-1": STRIKE, "YT-SHORT-1": BLOCKS,
    "YT-META-1": STRIKE, "YT-AD-1": LIMITS, "YT-TAG-1": STRIKE, "YT-KIDS-1": STRIKE, "YT-SYN-2": STRIKE,
    "YT-CRED-1": STRIKE, "YT-UP-1": BLOCKS, "YT-REV-1": "process",
}
GATED_STATUSES = ("edited", "published")       # policy_check is required from here (and always for upload)
STYLE_FREE_STATUSES = ("idea", "scripted")      # beyond these the channel needs style_approved_on
VARIATION_KEYS = ("story", "setting", "props")
VARIATION_WINDOW = 3
SENSITIVE_TOPICS = ("health", "finance")
# Forbidden claim words per sensitive topic and language (whole words / phrases, case-insensitive).
# A Channel Profile adds its own with `forbidden_words`.
FORBIDDEN_WORDS = {
    "health": {"en": ("cure", "cures", "cured", "curing"), "id": ("menyembuhkan", "disembuhkan")},
    "finance": {"en": ("guaranteed profit", "guaranteed returns", "risk-free"),
                "id": ("pasti untung", "dijamin untung", "tanpa risiko")},
}
# Any one of these in the description counts as the disclaimer; `disclaimer` in the profile replaces them.
DISCLAIMER_MARKERS = {
    "health": {"en": ("not medical advice", "consult a doctor", "consult your doctor", "ask your doctor",
                      "talk to your doctor"),
               "id": ("bukan pengganti saran dokter", "bukan nasihat medis", "tanya dokter",
                      "konsultasikan dengan dokter")},
    "finance": {"en": ("not financial advice",), "id": ("bukan nasihat keuangan", "bukan saran investasi")},
}
MUSIC_LABELS = {"en": ("music:",), "id": ("musik:", "music:")}
_CREDENTIAL = re.compile(
    r"\b(dr|doctor|physician|nurse|md|m\.d|pharmacist|therapist|physiotherapist|nutritionist|dietitian"
    r"|dokter|dok|perawat|apoteker|fisioterapis|ahli gizi|financial (?:advis[eo]r|planner)|cfa|cfp"
    r"|penasihat keuangan|perencana keuangan)\b", re.I)
_URL = re.compile(r"https?://\S+")


def _iso_date(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def episode_date(ep: dict):
    """`created_on`, else the date part of `scheduled_at`; None if neither is a valid date."""
    for key in ("created_on", "scheduled_at"):
        value = ep.get(key)
        if isinstance(value, str) and _iso_date(value[:10]):
            return _iso_date(value[:10])
    return None


def is_legacy(ep: dict) -> bool:
    """Legacy = `published`, or no `policy_check` and dated before POLICY_EPOCH. Legacy packages get
    policy-gate warnings instead of errors (the archive keeps validating)."""
    if ep.get("status") == "published":
        return True
    d = episode_date(ep)
    return "policy_check" not in ep and d is not None and d < POLICY_EPOCH


def _fold(text: str) -> str:
    return " ".join(str(text).casefold().split())


# Words that do not tell two topics apart ("How a fridge works" vs "Why your fridge ...").
_TOPIC_STOP = set("""a an the how why what when where who which does do did is are was were it its your you
your's our my of in on at to for from by with and or but so as that this these those be been being can
works work working really actually secret secretly inside behind keeps keep makes make made gets get
there here into out up down over under about after before just much more most very still even than
explained explain hidden""".split())
TOPIC_REPEAT_MIN = 0.6


def topic_words(ep: dict) -> set:
    """Key words of an episode's subject: the part of `topic` before ':' (else the title), lower case,
    without filler words, with a plain plural 's' removed."""
    text = ep.get("topic") or ep.get("title") or ""
    text = str(text).split(":")[0]
    words = set()
    for w in re.findall(r"[a-z0-9]+", text.casefold()):
        if w in _TOPIC_STOP or len(w) < 3:
            continue
        words.add(w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w)
    return words


def check_topic_repeat(ep: dict, others) -> list:
    """Errors when another episode of the same channel (any status, earlier or later) covers the same subject:
    the same `idea` id, or topic key words that overlap by TOPIC_REPEAT_MIN or more (Jaccard). Repeating a
    subject reads as repetitive content (YT-REUSE-1)."""
    if not isinstance(ep, dict):
        return []
    mine, errors = topic_words(ep), []
    for other in others or ():
        if not isinstance(other, dict) or other.get("id") == ep.get("id") \
                or other.get("channel") != ep.get("channel"):
            continue
        if ep.get("idea") and str(other.get("idea")) == str(ep.get("idea")):
            errors.append(f"topic: same idea {ep['idea']} as {other.get('id')} (YT-REUSE-1)")
            continue
        theirs = topic_words(other)
        if mine and theirs and len(mine & theirs) / len(mine | theirs) >= TOPIC_REPEAT_MIN:
            errors.append(f"topic: same subject as {other.get('id')} "
                          f"({', '.join(sorted(mine & theirs))}) (YT-REUSE-1)")
    return errors


def _has_phrase(text: str, phrase: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(_fold(phrase)) + r"(?!\w)", _fold(text)) is not None


def _natural(ep_id) -> tuple:
    return tuple(int(p) if p.isdigit() else p for p in re.split(r"(\d+)", str(ep_id)))


def previous_episodes(ep: dict, others) -> list:
    """The last VARIATION_WINDOW episodes of the same channel before `ep`, ordered by id (ep-009 < ep-010)."""
    key = _natural(ep.get("id"))
    prior = [o for o in others if isinstance(o, dict) and o.get("channel") == ep.get("channel")
             and o.get("id") != ep.get("id") and _natural(o.get("id")) < key]
    return sorted(prior, key=lambda o: _natural(o.get("id")))[-VARIATION_WINDOW:]


def missing_policy_items(ep: dict) -> list:
    """Pre-upload ids that are not "pass" in policy_check."""
    pc = ep.get("policy_check")
    items = pc.get("items") if isinstance(pc, dict) else None
    items = items if isinstance(items, dict) else {}
    return [i for i in PRE_UPLOAD_IDS if items.get(i) != "pass"]


_POLICY_ID = re.compile(r"\bYT-[A-Z]+-\d+\b")


# Workflow step of each pre-upload item (the sections of youtube-policy.md) and the episode status from which that
# step has been reached. Items of a step the episode has not reached yet are "pending", not "at risk".
STEP_OF = {**{i: "script" for i in ("YT-AUTH-1", "YT-AUTH-2", "YT-FACT-1", "YT-MED-1", "YT-REUSE-1", "YT-AD-2")},
           **{i: "build" for i in ("YT-COPY-1", "YT-COPY-2", "YT-SYN-1", "YT-SHORT-1")},
           **{i: "package" for i in ("YT-META-1", "YT-AD-1", "YT-TAG-1", "YT-KIDS-1", "YT-SYN-2", "YT-CRED-1")},
           "YT-UP-1": "pre-upload"}
STEP_REACHED_AT = {"script": "scripted", "build": "visuals", "package": "edited", "pre-upload": "edited"}


def step_reached(ep, policy_id) -> bool:
    """True when the episode's status has reached the workflow step of policy_id (unknown status or id: True)."""
    step = STEP_OF.get(policy_id)
    status = ep.get("status") if isinstance(ep, dict) else None
    if step is None or status not in STATUSES:
        return True
    return STATUSES.index(status) >= STATUSES.index(STEP_REACHED_AT[step])


def monetization_line(ep, problems) -> str:
    """One-line summary for the package step: `Monetization: OK`, `... pending` (policy_check not filled
    yet, before status edited), `... OK so far (pending: <ids> at <step>)` (only items of steps the status has not
    reached are open) or `... at risk: <ids> [impact]` (items of reached steps fail)."""
    if isinstance(ep, dict) and is_legacy(ep) and "policy_check" not in ep:
        return "Monetization: not checked (made before the policy gate)"
    ids = set()
    for p in problems:
        ids.update(_POLICY_ID.findall(p))
    if isinstance(ep, dict) and ("policy_check" in ep or ep.get("status") in GATED_STATUSES):
        ids.update(missing_policy_items(ep))
    order = {i: n for n, i in enumerate(POLICY_IDS)}
    ranked = sorted(ids, key=lambda i: order.get(i, len(order)))
    risk = [i for i in ranked if step_reached(ep, i)]
    later = [i for i in ranked if not step_reached(ep, i)]
    pending = ""
    if later:
        steps = []
        for step in dict.fromkeys(STEP_OF[i] for i in later):
            steps.append(", ".join(i for i in later if STEP_OF[i] == step) + f" at {step}")
        pending = "pending: " + "; ".join(steps)
    if risk:
        return ("Monetization: at risk: " + ", ".join(f"{i} [{IMPACT.get(i, '?')}]" for i in risk)
                + (f" ({pending})" if pending else ""))
    if pending:
        return f"Monetization: OK so far ({pending})"
    if isinstance(ep, dict) and "policy_check" not in ep and ep.get("status") not in GATED_STATUSES:
        return "Monetization: pending (fill policy_check at the package step)"
    return "Monetization: OK"


def _check_variation(ep: dict, previous) -> list:
    var = ep.get("variation")
    if not isinstance(var, dict) or any(not isinstance(var.get(k), str) or not var[k].strip()
                                        for k in VARIATION_KEYS):
        return ["variation: needs story, setting and props as non-empty text (YT-AUTH-2)"]
    errors = []
    for other in previous or ():
        ov = other.get("variation")
        if not isinstance(ov, dict):
            continue
        same = {k: isinstance(ov.get(k), str) and _fold(ov[k]) == _fold(var[k]) for k in VARIATION_KEYS}
        if same["story"]:
            errors.append(f"variation: same story as {other.get('id')} (YT-AUTH-2)")
        elif same["setting"] and same["props"]:
            errors.append(f"variation: same setting and props as {other.get('id')} (YT-AUTH-2)")
    return errors


def _check_sources(ep: dict) -> list:
    sources = ep.get("sources")
    if not isinstance(sources, list):
        return ["sources: missing, need a list of {claim, url} (YT-FACT-1)"]
    if not sources:
        if ep.get("no_factual_claims") is True:
            return []
        return ['sources: empty; add {claim, url} per factual claim, or set "no_factual_claims": true (YT-FACT-1)']
    bad = [str(i) for i, src in enumerate(sources)
           if not isinstance(src, dict) or not isinstance(src.get("claim"), str) or not src["claim"].strip()
           or not isinstance(src.get("url"), str) or not _URL.fullmatch(src["url"].strip())]
    if bad:
        return [f"sources[{', '.join(bad)}]: each source must be {{claim, url}} with an http(s) url (YT-FACT-1)"]
    return []


def _check_sensitive(ep: dict, profile: dict, lang: str) -> list:
    topic = profile.get("sensitive_topic")
    if topic not in SENSITIVE_TOPICS:
        return []
    errors = []
    words = list(FORBIDDEN_WORDS[topic].get(lang, ())) + list(FORBIDDEN_WORDS[topic].get("en", ()))
    words += [w for w in profile.get("forbidden_words") or () if isinstance(w, str) and w.strip()]
    for field in ("title", "description", "script"):
        hits = sorted({w for w in words if _has_phrase(ep.get(field, ""), w)})
        if hits:
            errors.append(f"{field}: forbidden on a {topic} channel: {', '.join(hits)} (YT-MED-1)")
    own = profile.get("disclaimer")
    markers = [own] if isinstance(own, str) and own.strip() else \
        list(DISCLAIMER_MARKERS[topic].get(lang, ())) + list(DISCLAIMER_MARKERS[topic]["en"])
    if not any(_has_phrase(ep.get("description", ""), m) for m in markers):
        errors.append(f"description: needs the {topic} disclaimer (e.g. {markers[0]!r}) (YT-MED-1)")
    return errors


def _check_music_credit(ep: dict, lang: str) -> list:
    if ep.get("music_source") == "none":
        return []
    desc = _fold(ep.get("description", ""))
    credit = ep.get("music_credit")
    if isinstance(credit, str) and credit.strip():
        return [] if _fold(credit) in desc else ["description: music_credit text is missing (YT-CRED-1)"]
    labels = MUSIC_LABELS.get(lang, MUSIC_LABELS["en"])
    if not any(label in desc for label in labels):
        return [f"description: needs a music credit line ({labels[0].capitalize()} ...) (YT-CRED-1)"]
    return []


def _check_policy_check(ep: dict, required: bool) -> list:
    if "policy_check" not in ep:
        if not required:
            return []
        return ["policy_check: missing; fill {checked_on, items} from references/youtube-policy.md "
                f"(missing: {', '.join(PRE_UPLOAD_IDS)})"]
    pc = ep["policy_check"]
    if not isinstance(pc, dict) or not isinstance(pc.get("items"), dict):
        return ["policy_check: must be {checked_on: YYYY-MM-DD, items: {id: \"pass\"}}"]
    errors = []
    if not _iso_date(pc.get("checked_on")):
        errors.append("policy_check: checked_on must be YYYY-MM-DD")
    unknown = sorted(k for k in pc["items"] if k not in POLICY_IDS)
    if unknown:
        errors.append(f"policy_check: unknown id(s) {', '.join(unknown)}")
    missing = missing_policy_items(ep)
    if missing and required:
        errors.append(f"policy_check: not pass: {', '.join(missing)}")
    return errors


def style_gate(profile) -> str:
    """'' if the channel's style bible is approved (style_approved_on), else the problem text."""
    if not isinstance(profile, dict):
        return ""
    when = profile.get("style_approved_on")
    if _iso_date(when):
        return ""
    return (f"style gate: channel {profile.get('id')!r} has no valid style_approved_on: render 2-3 sample style "
            "frames from style-bible.md, get the user's approval, then write the date "
            "(references/channel-setup.md)")


def _policy_problems(ep: dict, profile, previous, lang: str, for_upload: bool) -> list:
    errors = []
    for field in ("made_for_kids", "synthetic_content"):
        if not isinstance(ep.get(field), bool):
            errors.append(f"{field}: missing, must be true or false "
                          f"({'YT-KIDS-1' if field == 'made_for_kids' else 'YT-SYN-1'})")
    if ep.get("synthetic_content") is True and ep.get("ai_disclosure") is not True:
        errors.append("ai_disclosure: must be true when synthetic_content is true (YT-SYN-2)")
    errors += _check_variation(ep, previous)
    errors += _check_sources(ep)
    errors += _check_music_credit(ep, lang)
    errors += _check_policy_check(ep, for_upload or ep.get("status") in GATED_STATUSES)
    if isinstance(profile, dict):
        errors += _check_sensitive(ep, profile, lang)
        if ep.get("status") not in STYLE_FREE_STATUSES and style_gate(profile):
            errors.append(style_gate(profile))
    return errors


def policy_gate(ep: dict, profile=None, previous=(), language=None, for_upload=False) -> tuple:
    """(errors, warnings) of the YouTube policy gate. Legacy packages (is_legacy) give warnings only,
    except for an upload (`for_upload`), which always needs the full gate."""
    lang = language or (profile or {}).get("language") or ep.get("language") or "en"
    problems = _policy_problems(ep, profile, previous, lang, for_upload)
    if is_legacy(ep) and not for_upload:
        return [], [f"legacy package, policy gate: {p}" for p in problems]
    return problems, []



def count_words(text: str) -> int:
    return len(_WORD.findall(text))


def est_seconds(word_count: int, wpm: float = WPM) -> float:
    return word_count / wpm * 60


def _normalize(text: str) -> str:
    return " ".join(_WORD.findall(text.lower()))


def _check_fields(ep: dict) -> list:
    errors = []
    for field, typ in REQUIRED_FIELDS.items():
        if field not in ep:
            errors.append(f"{field}: missing")
        elif not isinstance(ep[field], typ):
            errors.append(f"{field}: must be {typ.__name__}")
    return errors


def _check_script(ep: dict, rules: dict) -> list:
    errors = []
    if ep["status"] not in STATUSES:
        errors.append(f"status: must be one of {', '.join(STATUSES)}")
    words = count_words(ep["script"])
    lo, hi = rules["min_words"], rules["max_words"]
    if not lo <= words <= hi:
        errors.append(
            f"script: {words} words, need {lo}-{hi} "
            f"(~{est_seconds(words, rules['wpm']):.0f}s, need 30-60s)"
        )
    hook_words = count_words(ep["hook"])
    if hook_words == 0 or hook_words > MAX_HOOK_WORDS:
        errors.append(f"hook: {hook_words} words, need 1-{MAX_HOOK_WORDS}")
    if not (_normalize(ep["script"]) + " ").startswith(_normalize(ep["hook"]) + " "):
        errors.append("hook: script must open with the hook")
    return errors


def _check_one_shot(i: int, shot) -> list:
    if not isinstance(shot, dict):
        return [f"shots[{i}]: must be an object"]
    errors = []
    for key in ("t_start", "t_end"):
        value = shot.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"shots[{i}]: {key} must be a finite number")
    if not errors and shot["t_end"] <= shot["t_start"]:
        errors.append(f"shots[{i}]: zero or negative length")
    if shot.get("type") not in SHOT_TYPES + LEGACY_SHOT_TYPES:
        errors.append(f"shots[{i}]: type must be one of {', '.join(SHOT_TYPES)}")
    prompt = shot.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        errors.append(f"shots[{i}]: prompt is empty")
    return errors


def _check_shots(ep: dict, rules: dict) -> list:
    shots = ep["shots"]
    if not shots:
        return ["shots: at least one shot is required"]
    errors = []
    for i, shot in enumerate(shots):
        errors += _check_one_shot(i, shot)
    if errors:
        return errors

    for i, shot in enumerate(shots):
        length = shot["t_end"] - shot["t_start"]
        if not MIN_SHOT - JOIN_TOLERANCE <= length <= MAX_SHOT + JOIN_TOLERANCE:
            errors.append(f"shots[{i}]: {length:.1f}s long, need {MIN_SHOT}-{MAX_SHOT}s")
    ordered = sorted(shots, key=lambda s: s["t_start"])
    if abs(ordered[0]["t_start"]) > JOIN_TOLERANCE:
        errors.append("shots: must start at 0")
    for prev, cur in zip(ordered, ordered[1:]):
        delta = cur["t_start"] - prev["t_end"]
        if delta > JOIN_TOLERANCE:
            errors.append(f"shots: gap between {prev['t_end']}s and {cur['t_start']}s")
        elif delta < -JOIN_TOLERANCE:
            errors.append(f"shots: overlap at {cur['t_start']}s")
    duration = ep.get("vo_duration") or est_seconds(count_words(ep["script"]), rules["wpm"])
    if ordered[-1]["t_end"] < duration - 1:
        errors.append(f"shots: cover only {ordered[-1]['t_end']}s of ~{duration:.0f}s narration")
    if ep["status"] != "published":
        for i, shot in enumerate(shots):
            if shot["type"] in LEGACY_SHOT_TYPES:
                errors.append(f"shots[{i}]: {shot['type']} is a legacy Google Flow type, "
                              "rebuild it as a diagram scene")
    return errors


def _check_metadata(ep: dict, rules: dict) -> list:
    errors = []
    title = ep["title"].strip()
    if not title:
        errors.append("title: is empty")
    elif len(title) > rules["max_title"]:
        errors.append(f"title: {len(title)} chars, max {rules['max_title']}")
    if not ep["description"].strip():
        errors.append("description: is empty")
    tags = ep["hashtags"]
    if not MIN_TAGS <= len(tags) <= MAX_TAGS:
        errors.append(f"hashtags: {len(tags)} given, need {MIN_TAGS}-{MAX_TAGS}")
    for tag in tags:
        if not isinstance(tag, str) or not _HASHTAG.fullmatch(tag):
            errors.append(f"hashtags: {tag!r} must look like #word (no spaces)")
    if ep["music_source"] not in MUSIC_SOURCES:
        errors.append(f"music_source: must be one of {', '.join(MUSIC_SOURCES)}")
    checklist = ep["originality_checklist"]
    missing = [k for k in ORIGINALITY_KEYS if checklist.get(k) is not True]
    if missing:
        errors.append(f"originality_checklist: not confirmed: {', '.join(missing)}")
    return errors


def _legacy_shot_types(ep: dict) -> list:
    shots = ep.get("shots") if isinstance(ep, dict) else None
    if not isinstance(shots, list):
        return []
    return [i for i, s in enumerate(shots) if isinstance(s, dict) and s.get("type") in LEGACY_SHOT_TYPES]


def warnings(ep: dict, profile=None, previous=(), language=None) -> list:
    """Non-blocking notes: legacy (Google Flow era) content, and policy-gate items a legacy package misses."""
    if not isinstance(ep, dict):
        return []
    notes = [f"{f}: legacy Flow field, ignored" for f in LEGACY_EPISODE_FIELDS if f in ep]
    if ep.get("status") == "published":
        notes += [f"shots[{i}]: legacy {ep['shots'][i]['type']} shot; Flow no longer used"
                  for i in _legacy_shot_types(ep)]
    if not _check_fields(ep):
        notes += policy_gate(ep, profile, previous, language)[1]
    return notes


def channel_warnings(profile: dict) -> list:
    """Non-blocking notes about legacy fields in a Channel Profile."""
    if not isinstance(profile, dict):
        return []
    return [f"{f}: legacy Flow field, ignored" for f in LEGACY_CHANNEL_FIELDS if f in profile]


def validate(ep: dict, language=None, profile=None, previous=(), for_upload=False) -> list:
    """Return a list of problems; an empty list means the episode is valid.

    `language` (from the Channel Profile) picks the script rules; else the episode's own
    `language` field, else English. `profile` (the Channel Profile) adds the style gate and the
    sensitive-topic rules; `previous` (earlier episodes of the channel) feeds the variation rule.
    `for_upload` requires the full policy gate even for legacy packages.
    """
    if not isinstance(ep, dict):
        return ["episode: must be a JSON object"]
    errors = _check_fields(ep)
    if errors:
        return errors
    lang = language or ep.get("language") or "en"
    if lang not in LANGUAGES:
        return [f"language: {lang!r} not supported, use one of {', '.join(LANGUAGES)}"]
    rules = LANGUAGES[lang]
    vo = ep.get("vo_duration")
    if vo is not None and (isinstance(vo, bool) or not isinstance(vo, (int, float))
                           or not math.isfinite(vo) or vo <= 0):
        return ["vo_duration: must be a positive number of seconds"]
    errors = _check_script(ep, rules) + _check_shots(ep, rules) + _check_metadata(ep, rules)
    return errors + policy_gate(ep, profile, previous, lang, for_upload)[0]


# ---------------------------------------------------------------- channels

def validate_channel(profile: dict) -> list:
    """Return a list of problems with a Channel Profile; empty means valid."""
    if not isinstance(profile, dict):
        return ["channel: must be a JSON object"]
    errors = []
    for field, typ in CHANNEL_FIELDS.items():
        if field not in profile:
            errors.append(f"{field}: missing")
        elif not isinstance(profile[field], typ):
            errors.append(f"{field}: must be {typ.__name__}")
    if errors:
        return errors
    if not _CHANNEL_ID.fullmatch(profile["id"]):
        errors.append("id: use lowercase letters, digits and '-' only")
    for field in ("name", "niche", "style_bible"):
        if not profile[field].strip():
            errors.append(f"{field}: is empty")
    if profile["status"] not in CHANNEL_STATUSES:
        errors.append(f"status: must be one of {', '.join(CHANNEL_STATUSES)}")
    voice = profile["voice"]
    for key in ("provider", "voice_name"):
        if not isinstance(voice.get(key), str) or not voice[key].strip():
            errors.append(f"voice: {key} is required")
    if "render_layout" in profile and profile["render_layout"] != "flat":
        errors.append('render_layout: only "flat" is allowed (omit it for render/<channel-id>/<ep-id>)')
    errors += _check_slots(profile)
    vpd = profile["videos_per_day"]
    if isinstance(vpd, bool) or vpd < 1:
        errors.append("videos_per_day: must be an integer >= 1")
    try:
        if not _DATE.fullmatch(profile["started_on"]):
            raise ValueError
        date.fromisoformat(profile["started_on"])
    except ValueError:
        errors.append("started_on: must be YYYY-MM-DD")
    return errors + _check_channel_extras(profile)


def _check_slots(profile: dict) -> list:
    found = posting_slots(profile)
    if found is None:
        return ["posting_slots: missing (a list of HH:MM times, with `timezone`)"]
    field, slots, tz = found
    errors = []
    if "posting_slots" in profile and "posting_slots_wib" in profile:
        errors.append("posting_slots_wib: legacy field, remove it when posting_slots is set")
    if not isinstance(slots, list):
        return errors + [f"{field}: must be list"]
    if not slots:
        errors.append(f"{field}: at least one HH:MM slot is required")
    for slot in slots:
        if not isinstance(slot, str) or not _SLOT.fullmatch(slot):
            errors.append(f"{field}: {slot!r} is not a valid HH:MM time")
    if field == "posting_slots":
        if not _valid_timezone(tz):
            errors.append(f"timezone: {tz!r} is not an IANA time zone name (e.g. \"UTC\", \"America/New_York\")")
    elif "timezone" in profile and profile["timezone"] != LEGACY_SLOT_TZ:
        errors.append(f"timezone: posting_slots_wib is always {LEGACY_SLOT_TZ}; use posting_slots for another zone")
    return errors


_HEX = re.compile(r"#[0-9A-Fa-f]{6}")


def _check_channel_extras(profile: dict) -> list:
    """Optional fields for non-English and multi-platform channels."""
    errors = []
    if "language" in profile and profile["language"] not in LANGUAGES:
        errors.append(f"language: must be one of {', '.join(LANGUAGES)}")
    if "platforms" in profile:
        plats = profile["platforms"]
        if not isinstance(plats, list) or not plats or any(p not in PLATFORMS for p in plats):
            errors.append(f"platforms: must be a non-empty list from {', '.join(PLATFORMS)}")
    if "meta" in profile:
        meta = profile["meta"]
        plats = meta.get("platforms") if isinstance(meta, dict) else None
        if (not isinstance(plats, list) or not plats or len(set(plats)) != len(plats)
                or any(p not in ("facebook", "instagram") for p in plats)):
            errors.append("meta: platforms must be a non-empty list from facebook, instagram")
        elif not (profile.get("facebook_page") or {}).get("id"):
            errors.append("meta: needs facebook_page.id (run meta_upload.py setup)")
        elif "instagram" in plats and not (profile.get("instagram") or {}).get("handle"):
            errors.append("meta: instagram in platforms needs instagram.handle (run meta_upload.py setup)")
    if "youtube_category_id" in profile:
        cat = profile["youtube_category_id"]
        if not isinstance(cat, str) or not cat.isdigit():
            errors.append("youtube_category_id: must be a string of digits, e.g. \"17\"")
    if "youtube_account" in profile:
        acct = profile["youtube_account"]
        if not isinstance(acct, str) or not _CHANNEL_ID.fullmatch(acct):
            errors.append("youtube_account: use lowercase letters, digits and '-' only")
    errors += _check_channel_policy(profile)
    if "brand" in profile:
        brand = profile["brand"]
        if not isinstance(brand, dict):
            errors.append("brand: must be an object")
        else:
            for key in ("text", "font"):
                if key in brand and (not isinstance(brand[key], str) or not brand[key].strip()):
                    errors.append(f"brand: {key} must be a non-empty string")
            colors = brand.get("colors", {})
            if not isinstance(colors, dict) or any(not isinstance(v, str) or not _HEX.fullmatch(v)
                                                   for v in colors.values()):
                errors.append("brand: colors must map names to #RRGGBB")
    return errors


def _check_channel_policy(profile: dict) -> list:
    """Optional policy fields of a Channel Profile (references/youtube-policy.md, channel step)."""
    errors = []
    if "style_approved_on" in profile and not _iso_date(profile["style_approved_on"]):
        errors.append("style_approved_on: must be YYYY-MM-DD")
    if "made_for_kids" in profile and not isinstance(profile["made_for_kids"], bool):
        errors.append("made_for_kids: must be true or false")
    topic = profile.get("sensitive_topic")
    if topic is not None and topic not in SENSITIVE_TOPICS:
        errors.append(f"sensitive_topic: must be one of {', '.join(SENSITIVE_TOPICS)} or null")
    for key in ("persona", "disclaimer"):
        if key in profile and not isinstance(profile[key], str):
            errors.append(f"{key}: must be text")
    words = profile.get("forbidden_words", [])
    if not isinstance(words, list) or any(not isinstance(w, str) or not w.strip() for w in words):
        errors.append("forbidden_words: must be a list of words or phrases")
    persona = profile.get("persona")
    if topic in SENSITIVE_TOPICS and isinstance(persona, str):
        hit = _CREDENTIAL.search(persona)
        if hit:
            errors.append(f"persona: claims a credential ({hit.group(0)!r}) on a {topic} channel; "
                          "no AI expert persona (YT-CH-2)")
    return errors


def _load_json(path: Path):
    """Return parsed JSON or raise ValueError with a readable message."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError:
        raise ValueError(f"{path}: not UTF-8 text (save the file as UTF-8)")
    except FileNotFoundError:
        raise ValueError(f"{path}: file not found")
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc.msg}, line {exc.lineno})")
    except OSError as exc:
        raise ValueError(f"{path}: {exc.strerror}")


def _find_profile(episode_path: Path, explicit) -> Path:
    if explicit:
        return Path(explicit)
    here = episode_path.resolve().parent
    for candidate in (here / "channel.json", here.parent / "channel.json"):
        if candidate.is_file():
            return candidate
    return here.parent / "channel.json"


def _flat_layout(root: Path, channel: str) -> bool:
    """True when channels/<id>/channel.json sets "render_layout": "flat" (episodes live in render/<ep-id>)."""
    try:
        prof = json.loads((root / "channels" / channel / "channel.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return False
    return isinstance(prof, dict) and prof.get("render_layout") == "flat"


def _channel_errors(ep: dict, episode_path: Path, explicit=None) -> list:
    profile_path = _find_profile(episode_path, explicit)
    if not profile_path.is_file():
        return [f"channel: no profile found at {profile_path}"]
    try:
        profile = _load_json(profile_path)
    except ValueError as exc:
        return [f"channel: cannot read profile ({exc})"]
    problems = validate_channel(profile)
    if problems:
        return [f"channel: profile is invalid ({p})" for p in problems]
    if profile["id"] != ep.get("channel"):
        return [f"channel: episode says {ep.get('channel')!r} but profile is {profile['id']!r}"]
    return []


def capacity(root: Path) -> dict:
    """Daily load of channels that are testing or active, against their posting slots.

    Per channel: `videos_per_day` vs the number of posting slots; a channel with more
    videos than slots is listed in "over_slots". Totals: videos, slots and agent minutes per
    day (`MIN_PER_VIDEO` each, built serially) to compare with the user's time and token budget.
    Unreadable or invalid profiles are listed in "skipped".
    """
    root = Path(root)
    channels, skipped, over, per_channel = [], [], [], {}
    videos, slots = 0, 0
    for profile_path in sorted(root.glob("*/channel.json")):
        try:
            profile = _load_json(profile_path)
        except ValueError as exc:
            skipped.append(str(exc))
            continue
        problems = validate_channel(profile)
        if problems:
            skipped.append(f"{profile_path}: {problems[0]}")
            continue
        if profile["status"] == "paused":
            continue
        cid, vpd, n_slots = profile["id"], profile["videos_per_day"], len(posting_slots(profile)[1])
        channels.append(cid)
        per_channel[cid] = {"videos_per_day": vpd, "slots": n_slots}
        videos += vpd
        slots += n_slots
        if vpd > n_slots:
            over.append(cid)
    return {
        "videos_per_day": videos,
        "slots_per_day": slots,
        "minutes_per_day": videos * MIN_PER_VIDEO,
        "per_channel": per_channel,
        "over_slots": over,
        "channels": channels,
        "skipped": skipped,
    }


# --------------------------------------------------------------------- CLI

def _load_profile(path: Path, channel_path=None):
    profile_path = _find_profile(path, channel_path)
    if not profile_path.is_file():
        return None
    try:
        profile = _load_json(profile_path)
    except ValueError:
        return None                                  # reported by _channel_errors
    return profile if isinstance(profile, dict) else None


def _sibling_episodes(path: Path, previous_paths=None) -> list:
    """Episode Packages to compare `variation` with: `previous_paths`, else the other *.json next to `path`."""
    paths = previous_paths if previous_paths is not None else sorted(Path(path).resolve().parent.glob("*.json"))
    out = []
    for p in paths:
        p = Path(p)
        if p.resolve() == Path(path).resolve() or p.name == "channel.json":
            continue
        try:
            data = _load_json(p)
        except ValueError:
            continue
        if isinstance(data, dict):
            out.append(data)
    return out


def validate_file(path: Path, channel_path=None, previous_paths=None, for_upload=False) -> tuple:
    """(errors, warnings, missing policy ids) for an Episode Package file, with its Channel Profile and
    the previous episodes of the channel. Raises ValueError if the file cannot be read."""
    path = Path(path)
    ep = _load_json(path)
    profile = _load_profile(path, channel_path)
    language = profile.get("language") if profile and profile.get("language") in LANGUAGES else None
    if not isinstance(ep, dict):
        return validate(ep), [], list(PRE_UPLOAD_IDS)
    siblings = _sibling_episodes(path, previous_paths)
    previous = previous_episodes(ep, siblings)
    errors = validate(ep, language, profile, previous, for_upload)
    if not is_legacy(ep):
        errors += check_topic_repeat(ep, siblings)
    errors += _channel_errors(ep, path, channel_path)
    return errors, warnings(ep, profile, previous, language), missing_policy_items(ep)


def _cmd_validate(path: Path, channel_path=None, previous_paths=None) -> int:
    try:
        errors, notes, _ = validate_file(path, channel_path, previous_paths)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for note in notes:
        print(f"warning: {note}")
    try:
        ep = _load_json(path)
    except ValueError:
        ep = None
    summary = monetization_line(ep, errors + [n for n in notes if "policy gate" in n])
    if errors:
        print(f"{path}: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        print(summary)
        return 1
    print(f"OK {path}")
    for w in _library_warnings(path):
        print(f"  warning: {w}")
    print(summary)
    return 0


_DIRECT_RIG = re.compile(r"^\s*from\s+character\s+import\b|^\s*import\s+character\s+as\b"
                         r"|(?<![\w.])character\.(?!py\b)[A-Za-z_]\w*", re.M)


def _library_warnings(path: Path) -> list:
    """Non-fatal: a render project that calls the rig directly instead of library.lib.Library.
    The bare `import character` shim line in the template build.py is fine; only rig use through it warns."""
    path = Path(path).resolve()
    if path.parent.name != "episodes" or len(path.parents) < 4:
        return []
    channel, root = path.parent.parent.name, path.parents[3]
    render = root / "render"
    cands = [render / channel / path.stem]
    if _flat_layout(root, channel):
        cands.insert(0, render / path.stem)   # flat layout (channel.json "render_layout": "flat"): render/<ep-id>
    for proj in cands:
        if not proj.is_dir() or (proj / ".lib_used.json").exists():
            continue
        for py in sorted(proj.glob("*.py")):
            if py.name in ("character.py", "mocap.py"):
                continue
            text = "\n".join(line.split("#", 1)[0] for line in py.read_text(errors="ignore").splitlines())
            if _DIRECT_RIG.search(text):
                return ["render project calls the rig directly; use library.lib.Library"]
    return []


def _cmd_validate_channel(path: Path) -> int:
    try:
        profile = _load_json(path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = validate_channel(profile)
    for note in channel_warnings(profile):
        print(f"warning: {note}")
    if errors:
        print(f"{path}: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK {path}")
    return 0


def _cmd_log(root: Path, channel) -> int:
    rows = []
    for path in sorted(Path(root).glob("*/episodes/*.json")):
        cid = path.parent.parent.name
        if channel and cid != channel:
            continue
        try:
            ep = _load_json(path)
            if not isinstance(ep, dict):
                raise ValueError("not an object")
            rows.append((cid, str(ep.get("id", path.stem)), str(ep.get("status", "?")), str(ep.get("title", ""))))
        except ValueError:
            rows.append((cid, path.name, "UNREADABLE", ""))
    if not rows:
        print("no episodes found")
        return 0
    header = ("channel", "id", "status", "title")
    widths = [max(len(r[i]) for r in rows + [header]) for i in range(3)]
    for r in [header] + rows:
        print(" | ".join(r[i].ljust(widths[i]) for i in range(3)) + " | " + r[3])
    return 0


def _cmd_capacity(root: Path) -> int:
    cap = capacity(root)
    print(f"channels (testing/active): {', '.join(cap['channels']) or '-'}")
    for cid, row in cap["per_channel"].items():
        verdict = "OVER" if cid in cap["over_slots"] else "fits"
        print(f"  {cid}: {row['videos_per_day']} video(s)/day, {row['slots']} slot(s): {verdict}")
    print(f"videos per day: {cap['videos_per_day']} (slots: {cap['slots_per_day']})")
    print(f"minutes per day: {cap['minutes_per_day']} (at {MIN_PER_VIDEO} min/video, serial)"
          " - compare with your daily time and token budget")
    for item in cap["skipped"]:
        print(f"skipped: {item}")
    return 0


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(prog="validate_episode.py", description="akra checks")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate", help="check one Episode Package")
    p.add_argument("path", type=Path)
    p.add_argument("--channel", type=Path, help="Channel Profile to check against "
                   "(default: channel.json next to the episode, then ../channel.json)")
    p.add_argument("--previous", type=Path, nargs="+", help="earlier Episode Packages of the channel for the "
                   "variation rule (default: the other episodes in the same folder)")
    p = sub.add_parser("validate-channel", help="check one Channel Profile")
    p.add_argument("path", type=Path)
    p = sub.add_parser("log", help="list episodes of every channel")
    p.add_argument("root", type=Path)
    p.add_argument("--channel")
    p = sub.add_parser("capacity", help="daily load across channels vs posting slots")
    p.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _cmd_validate(args.path, args.channel, args.previous)
    if args.cmd == "validate-channel":
        return _cmd_validate_channel(args.path)
    if args.cmd == "log":
        return _cmd_log(args.root, args.channel)
    return _cmd_capacity(args.root)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
