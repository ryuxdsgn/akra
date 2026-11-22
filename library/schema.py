"""Item schema: validate_item returns a list of error strings (empty list = valid)."""
import re
from datetime import date

KINDS = ("character", "pose", "env")
STATUSES = ("draft", "vetted")
ORIGINS = ("builtin", "generated")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STYLES = ("hw", "toon")
NEEDS = ("chair", "rail", "ik_target")
HEX = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
COMMON_REQUIRED = ("id", "kind", "name", "tags", "style", "status", "origin", "created",
                   "created_by", "preview", "examples")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _str_list(v):
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _nonempty_str(v):
    return isinstance(v, str) and bool(v.strip())


def _common(item, errs):
    for f in COMMON_REQUIRED:
        if f not in item:
            errs.append(f"missing field: {f}")
    for f in ("id", "name", "created_by", "preview"):
        if f in item and not _nonempty_str(item[f]):
            errs.append(f"{f} must be a non-empty string")
    if "kind" in item and item["kind"] not in KINDS:
        errs.append(f"kind must be one of {KINDS}")
    if "status" in item and item["status"] not in STATUSES:
        errs.append(f"status must be one of {STATUSES}")
    if "origin" in item and item["origin"] not in ORIGINS:
        errs.append(f"origin must be one of {ORIGINS}")
    if "style" in item and item["style"] not in STYLES:
        errs.append(f"style must be one of {STYLES}")
    for f in ("tags", "examples"):
        if f in item and not _str_list(item[f]):
            errs.append(f"{f} must be a list of strings")
    if "created" in item:
        c = item["created"]
        ok = isinstance(c, str) and DATE.match(c)
        if ok:
            try:
                date.fromisoformat(c)
            except ValueError:
                ok = False
        if not ok:
            errs.append("created must be an ISO date string (YYYY-MM-DD)")
    if "public" in item and not isinstance(item["public"], bool):
        errs.append("public must be a boolean")
    tc = item.get("token_cost")
    if "token_cost" in item and (not isinstance(tc, int) or isinstance(tc, bool) or tc < 0):
        errs.append("token_cost must be an int >= 0")
    if item.get("origin") == "generated" and "token_cost" not in item:
        errs.append("token_cost is required when origin is generated")


def _variant_spec_ok(spec):
    if not isinstance(spec, dict):
        return False
    if set(spec) == {"type"}:
        return spec["type"] in ("color", "bool")
    if set(spec) == {"type", "nullable"}:
        return spec["type"] == "color" and spec["nullable"] is True
    if set(spec) == {"enum"}:
        return _str_list(spec["enum"]) and len(spec["enum"]) > 0
    if set(spec) == {"min", "max"}:
        return _num(spec["min"]) and _num(spec["max"]) and spec["min"] <= spec["max"]
    return False


def _character(item, errs):
    for f in ("base_look", "variants", "face", "scale_hint"):
        if f not in item:
            errs.append(f"missing field: {f}")
    if "base_look" in item and not isinstance(item["base_look"], dict):
        errs.append("base_look must be a dict")
    if "variants" in item:
        if not isinstance(item["variants"], dict):
            errs.append("variants must be a dict")
        else:
            for k, spec in item["variants"].items():
                if not _variant_spec_ok(spec):
                    errs.append(f"variants.{k} must be {{type: color|bool}}, {{type: color, nullable: true}}, {{enum: [...]}} or {{min, max}}")
    if "face" in item:
        if item["face"] not in STYLES:
            errs.append(f"face must be one of {STYLES}")
        elif item.get("style") in STYLES and item["face"] != item["style"]:
            errs.append("face must equal style")
    if "scale_hint" in item and not _num(item["scale_hint"]):
        errs.append("scale_hint must be a number")
    if isinstance(item.get("base_look"), dict):
        _look_options(item, errs)
    if "costume" in item:
        try:
            from library.rig.costumes import COSTUMES
        except ModuleNotFoundError as e:
            if e.name not in ("library.rig", "library.rig.costumes"):
                raise
            errs.append("costume needs the character rig (library/rig/), which is not included in this distribution")
            return
        if item["costume"] not in COSTUMES:
            errs.append(f"costume {item['costume']!r} is not a known costume ({sorted(COSTUMES)})")
        elif item.get("style") != "hw":
            errs.append("costume is only supported for style hw")


# opt-in look options, drawn by the rig when present (library/rig/chibi.py imports these; the schema stays dependency-free)
PROPORTIONS = ("default", "chibi")
FACE_LAYOUTS = ("default", "standard")
STANCES = ("default", "standard")
HAIR_PRESETS = ("side_part", "bob", "soft_short")
HAIR_STYLES = {"hw": ("short", "parted", "bald", "kid"), "toon": ("short", "parted", "bald", "kid", "curly", "bun")}


def _look_options(item, errs):
    """Opt-in look options and hair styles the item's rig can draw."""
    bl, style = item["base_look"], item.get("style")
    for key, allowed in (("proportions", PROPORTIONS), ("face_layout", FACE_LAYOUTS), ("stance", STANCES)):
        if key in bl and bl[key] not in allowed:
            errs.append(f"base_look.{key} must be one of {allowed}")
    if style == "toon" and bl.get("face_layout") == "standard" and bl.get("face") != "toon":
        errs.append("base_look.face_layout 'standard' needs base_look.face 'toon' for style toon")
    if bl.get("stance") == "standard" and not (style == "toon" and bl.get("line")):
        errs.append("base_look.stance 'standard' is for line-art toon looks (style toon + base_look.line); hw legs already stand straight")
    if style in HAIR_STYLES:
        known = HAIR_STYLES[style] + HAIR_PRESETS
        if "hair_style" in bl and bl["hair_style"] not in known:
            errs.append(f"base_look.hair_style must be one of {known}")
        spec = item.get("variants", {}).get("hair_style") if isinstance(item.get("variants"), dict) else None
        if isinstance(spec, dict) and _str_list(spec.get("enum")):
            bad = [h for h in spec["enum"] if h not in known]
            if bad:
                errs.append(f"variants.hair_style has unknown styles {bad}")


def _env(item, errs):
    for f in ("module", "function", "variants", "backdrop", "safe_area", "palette"):
        if f not in item:
            errs.append(f"missing field: {f}")
    for f in ("module", "function"):
        if f in item and not _nonempty_str(item[f]):
            errs.append(f"{f} must be a non-empty string")
    if "variants" in item:
        v = item["variants"]
        if not _str_list(v) or not v:
            errs.append("variants must be a non-empty list of strings")
        elif "default" not in v:
            errs.append("variants must contain 'default'")
    if "backdrop" in item and not (isinstance(item["backdrop"], str) and HEX.match(item["backdrop"])):
        errs.append("backdrop must be a hex color")
    if "backdrops" in item:
        b = item["backdrops"]
        if not (isinstance(b, dict) and all(isinstance(v, str) and HEX.match(v) for v in b.values())):
            errs.append("backdrops must map variant names to hex colors")
        elif isinstance(item.get("variants"), list):
            for v in b:
                if v not in item["variants"]:
                    errs.append(f"backdrops key {v!r} is not a variant")
    if "palette" in item:
        p = item["palette"]
        if not isinstance(p, list) or not all(isinstance(c, str) and HEX.match(c) for c in p):
            errs.append("palette must be a list of hex colors")
    if "safe_area" in item:
        s = item["safe_area"]
        ok = isinstance(s, list) and len(s) == 4 and all(_num(x) for x in s)
        if ok:
            x0, y0, x1, y1 = s
            ok = 0 <= x0 < x1 <= 1080 and 0 <= y0 < y1 <= 1920
        if not ok:
            errs.append("safe_area must be [x0, y0, x1, y1] inside 0..1080 x 0..1920")


def _pose(item, errs):
    for f in ("params_file", "needs"):
        if f not in item:
            errs.append(f"missing field: {f}")
    if "params_file" in item and not _nonempty_str(item["params_file"]):
        errs.append("params_file must be a non-empty string")
    if "needs" in item:
        n = item["needs"]
        if not isinstance(n, list) or any(x not in NEEDS for x in n):
            errs.append(f"needs must be a list drawn from {NEEDS}")


def validate_item(item):
    if not isinstance(item, dict):
        return ["item must be a dict"]
    errs = []
    _common(item, errs)
    kind = item.get("kind")
    if kind == "character":
        _character(item, errs)
    elif kind == "env":
        _env(item, errs)
    elif kind == "pose":
        _pose(item, errs)
    return errs
