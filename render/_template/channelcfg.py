"""Which channel an episode folder belongs to, and that channel's brand (channels/<id>/channel.json).

Folder layout:
    render/<channel-id>/ep-001/       -> channel <channel-id> (the normal layout)
    render/ep-001/                    -> the one channel whose channel.json has "render_layout": "flat"
                                         (older projects that started before channel folders); with no
                                         such channel, or more than one, this is a LayoutError
There is no built-in default channel.

channel.json keys read here (all optional):
    render_layout     "flat"                 -> this channel's episodes live directly in render/<ep-id>/
    language          "en" | "id"            -> <html lang>, caption line length
    brand.text        footer/brand line      (default: name in capitals)
    brand.font        font family            (default Montserrat)
    brand.colors      {bg, ink, muted, dim, primary, primary_light, accent, highlight, housing, edge}
    brand.cap_max_chars                      (default 20 en, 18 id: Indonesian words run longer)
    brand.cap_top                            caption top y in px (default 1185; lower it for full-body cartoon scenes)
    brand.speaker_colors                     {"HOST": "#FF9EBB", ...}: caption colour per transcript speaker
Missing values fall back to a neutral dark look (DEFAULT_COLORS, Montserrat). Set all of brand.colors to keep a
channel's look fixed when these defaults change.
"""
import json
import os

DEFAULT_COLORS = {          # neutral starter palette: slate background, warm sand primary, teal accent
    "bg": "#1F2933", "ink": "#F5F2EB", "muted": "#B5BEC6", "dim": "#7B8794",
    "primary": "#D4A373", "primary_light": "#E9C9A3", "accent": "#2BB3A3", "highlight": "#F07167",
    "housing": "#2C3843", "edge": "#52606D",
}
CAP_MAX = {"en": 20, "id": 18}


class LayoutError(ValueError):
    """An episode folder sits directly in render/ but no single channel claims that layout."""


def flat_channels(root):
    """Channel ids whose channel.json says "render_layout": "flat", sorted."""
    base = os.path.join(root, "channels")
    found = []
    for cid in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        path = os.path.join(base, cid, "channel.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                if json.load(f).get("render_layout") == "flat":
                    found.append(cid)
        except (OSError, ValueError):
            continue
    return found


def locate(here):
    """(project root, channel id) for an episode folder; the template folder has channel None."""
    here = os.path.abspath(here)
    parent = os.path.dirname(here)
    if os.path.basename(parent) != "render":
        return os.path.dirname(os.path.dirname(parent)), os.path.basename(parent)
    root = os.path.dirname(parent)
    name = os.path.basename(here)
    if name.startswith("_"):                      # render/_template and other non-episode folders
        return root, None
    flat = flat_channels(root)
    if len(flat) == 1:
        return root, flat[0]
    why = ("no channel declares" if not flat else f"several channels declare ({', '.join(flat)})")
    raise LayoutError(f"render/{name} has no channel folder and {why} \"render_layout\": \"flat\". "
                      f"Move it to render/<channel-id>/{name}, or set \"render_layout\": \"flat\" in exactly "
                      f"one channels/<id>/channel.json.")


def profile(here):
    root, channel = locate(here)
    path = os.path.join(root, "channels", channel or "", "channel.json")
    if not channel or not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def settings(here):
    root, channel = locate(here)
    prof = profile(here)
    brand = prof.get("brand", {})
    lang = prof.get("language", "en")
    return {
        "root": root,
        "channel": channel,
        "language": lang,
        "brand_text": brand.get("text") or (prof.get("name") or channel or "").upper(),
        "font": brand.get("font", "Montserrat"),
        "colors": {**DEFAULT_COLORS, **brand.get("colors", {})},
        "cap_max_chars": brand.get("cap_max_chars", CAP_MAX.get(lang, 20)),
        "speaker_colors": brand.get("speaker_colors", {}),
        "cap_top": brand.get("cap_top", 1185),
    }
