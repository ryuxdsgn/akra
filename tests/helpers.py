"""Shared test fixtures for the akra validator."""
import contextlib
import copy
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "akra"
# The public tree ships the library engine without the rig or any library art; tests that need them skip there.
HAVE_RIG = (ROOT / "library" / "rig" / "__init__.py").is_file()
HAVE_ART = (ROOT / "library" / "characters").is_dir()
NO_RIG = "character rig not included in this distribution"
sys.path.insert(0, str(SKILL_DIR / "scripts"))


@contextlib.contextmanager
def builtin_toon(toon):
    """The toon rig as shipped: its add-on hooks are emptied while the block runs (public golden output)."""
    with mock.patch.object(toon, "_HATS", {}), mock.patch.object(toon, "_PRINTS", {}), \
            mock.patch.object(toon, "_FRONT_PROPS", []), mock.patch.object(toon, "_POSE_PROPS", []):
        yield toon


HOOK = "This ocean hides a second ocean."
_BODY_WORDS = (
    "Deep under the Pacific floor, scientists found water locked inside a blue "
    "mineral called ringwoodite. It sits about four hundred miles down, squeezed "
    "by heat and pressure. Nobody can swim in it, because the water is trapped in "
    "the crystal itself. But if you could squeeze it out, there might be three "
    "times more water down there than in every ocean on the surface. That changes "
    "how we think Earth got its seas. Maybe the water came from inside the planet, "
    "not from comets. So next time you see the waves, remember the hidden"
).split()


def make_script(total_words: int = 100) -> str:
    """Script that opens with HOOK and has exactly `total_words` words."""
    hook_words = HOOK.split()
    body = (_BODY_WORDS * 3)[: total_words - len(hook_words)]
    return " ".join(hook_words + body) + "."


def make_shots(ends=(8, 16, 24, 32, 40), shot_type: str = "diagram") -> list:
    shots, start = [], 0
    for i, end in enumerate(ends):
        shots.append({
            "t_start": start,
            "t_end": end,
            "narration": f"line {i + 1}",
            "type": shot_type,
            "prompt": "Deep blue crystal glowing underground, slow push-in, 9:16",
        })
        start = end
    return shots


_VALID = {
    "id": "ep-001",
    "channel": "deep-earth",
    "niche": "science facts",
    "topic": "Hidden ocean under the Pacific",
    "status": "scripted",
    "hook": HOOK,
    "script": make_script(100),
    "shots": make_shots(),
    "title": "There Is a Hidden Ocean Under Our Feet",
    "description": "Scientists found water locked inside ringwoodite deep under the Pacific.\n"
                   "Music: \"Pulsar\" by The Grey Room (YouTube Audio Library).",
    "hashtags": ["#shorts", "#science", "#ocean"],
    "ai_disclosure": True,
    "made_for_kids": False,
    "synthetic_content": False,
    "variation": {"story": "a diamond carries mantle water to the surface",
                  "setting": "cutaway of the mantle", "props": "ringwoodite crystal, diamond"},
    "sources": [{"claim": "ringwoodite in a diamond held water",
                 "url": "https://www.nature.com/articles/nature13080"}],
    "music_source": "youtube_audio_library",
    "originality_checklist": {
        "original_script": True,
        "custom_voice_direction": True,
        "manual_edit": True,
        "added_value": True,
    },
}


def make_valid() -> dict:
    return copy.deepcopy(_VALID)


def make_policy_check(**items) -> dict:
    """policy_check with every pre-upload id "pass" (override single ids with items)."""
    from validate_episode import PRE_UPLOAD_IDS
    marks = {i: "pass" for i in PRE_UPLOAD_IDS}
    marks.update({k.replace("_", "-"): v for k, v in items.items()})
    return {"checked_on": "2026-11-22", "items": marks}


def make_channel(**overrides) -> dict:
    ch = {
        "id": "deep-earth",
        "name": "Deep Earth Facts",
        "niche": "science facts",
        "status": "testing",
        "voice": {"provider": "elevenlabs", "voice_name": "Adam"},
        "style_bible": "Cinematic, deep blue palette, slow camera moves, 9:16.",
        "posting_slots": ["06:00"],
        "timezone": "America/New_York",
        "videos_per_day": 1,
        "started_on": "2026-11-09",
    }
    ch.update(overrides)
    return ch
