"""Library loader: style lock, variant checks, env bake hooks and a per-project usage record."""
import importlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

from library.catalog import LibraryError, load_items

RIG_MISSING = ("character rig not included in this distribution; draw characters in your scenes "
               "or add your own rig (see references/library.md)")

_HEX6 = re.compile(r"^#[0-9A-Fa-f]{6}$")
# .lib_used.json keeps one entry per script (build.py, cover.py, ...) under "by_script"; each process replaces only
# its own entry on its first write (pruning items that script no longer uses) and merges after that. The top-level
# "items"/"custom" are the union over all scripts, which is what QA and freeze read.
_WRITTEN = set()


def find_repo_root(start):
    p = Path(start).resolve()
    for d in (p, *p.parents):
        if (d / "library").is_dir() and (d / "skills" / "akra").is_dir():
            return d
    raise LibraryError(f"no repo root (library/ and skills/akra/) above {start}")


class RigNotIncluded(LibraryError):
    """The character rig (library/rig/) is not part of this tree."""


def load_rig(style):
    """The rig module for a style (library/rig/hw.py or library/rig/toon.py); RigNotIncluded when it is absent."""
    name = "hw" if style == "hw" else "toon"
    try:
        return importlib.import_module(f"library.rig.{name}")
    except ModuleNotFoundError as e:
        if e.name in ("library.rig", f"library.rig.{name}"):
            raise RigNotIncluded(RIG_MISSING) from None
        raise


def _costume(rig, svg, cid, look, name):
    try:
        from library.rig.costumes import costume
    except ModuleNotFoundError as e:
        if e.name in ("library.rig", "library.rig.costumes"):
            raise RigNotIncluded(RIG_MISSING) from None
        raise
    return costume(rig, svg, cid, look, name)


def _check_variant(item, name, value):
    specs = item.get("variants", {})
    if not isinstance(specs, dict) or name not in specs:
        raise LibraryError(f"{item['id']}: unknown variant {name!r}")
    spec = specs[name]
    if spec.get("type") == "bool":
        if not isinstance(value, bool):
            raise LibraryError(f"{item['id']}: variant {name!r} must be true or false, got {value!r}")
    elif "type" in spec:
        if value is None and spec.get("nullable"):
            return
        if not (isinstance(value, str) and _HEX6.match(value)):
            raise LibraryError(f"{item['id']}: variant {name!r} must be a #RRGGBB color, got {value!r}")
    elif "enum" in spec:
        if value not in spec["enum"]:
            raise LibraryError(f"{item['id']}: variant {name!r} must be one of {spec['enum']}, got {value!r}")
    else:
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and spec["min"] <= value <= spec["max"]
        if not ok:
            raise LibraryError(f"{item['id']}: variant {name!r} must be within {spec['min']}..{spec['max']}, got {value!r}")


class Library:
    def __init__(self, project_dir, channel_id):
        self.project_dir = Path(project_dir)
        self.channel_id = channel_id
        self.repo_root = find_repo_root(self.project_dir)
        frozen = self.project_dir.resolve() / "_lib_frozen"
        if frozen.is_dir():
            import library as _pkg
            if frozen not in Path(_pkg.__file__).resolve().parents:
                raise LibraryError("live library imported but episode is frozen — import character (shim) before library")
            self._lib_dir, local = frozen / "library", frozen / "_library"
        else:
            self._lib_dir, local = self.repo_root / "library", self.repo_root / "channels" / "_library"
        self._local_dir = local if local.is_dir() else None
        self.items = load_items(self._lib_dir, self._local_dir)
        cfg_path = self.repo_root / "channels" / channel_id / "library.json"
        if cfg_path.is_file():
            cfg = json.loads(cfg_path.read_text())
            self.style = cfg["style"]
            self.visual_mode = cfg.get("visual_mode")
            self.selected = list(cfg.get("items", []))
        else:
            raise LibraryError(f"channels/{channel_id}/library.json is missing; create it (style, visual_mode, items)")
        self._rig = None                  # loaded on first use: env-only projects need no rig
        self._used_path = self.project_dir / ".lib_used.json"
        self._custom_looks = 0
        self._record = {"style": self.style, "items": {}, "custom": []}

    @property
    def rig(self):
        if self._rig is None:
            self._rig = load_rig(self.style)
        return self._rig

    @rig.setter
    def rig(self, module):
        self._rig = module

    # -- helpers
    def _save(self):
        self.project_dir.mkdir(parents=True, exist_ok=True)
        key = str(self._used_path.resolve())
        script = Path(sys.argv[0]).name if sys.argv and sys.argv[0] else "<interactive>"
        old = {}
        if self._used_path.is_file():
            try:
                old = json.loads(self._used_path.read_text())
            except (json.JSONDecodeError, OSError):
                old = {}
        if old.get("style") != self.style:
            old = {}
        by_script = dict(old.get("by_script", {}))
        mine = {"items": dict(self._record["items"]), "custom": list(self._record["custom"])}
        if key in _WRITTEN and script in by_script:          # later write in this process: merge
            prev = by_script[script]
            mine["items"] = dict(prev.get("items", {})) | mine["items"]
            mine["custom"] += [c for c in prev.get("custom", []) if c not in mine["custom"]]
        by_script[script] = mine
        _WRITTEN.add(key)
        items, custom = {}, []
        for entry in by_script.values():
            for iid, status in entry.get("items", {}).items():
                items[iid] = "draft" if "draft" in (status, items.get(iid)) else status
            custom += [c for c in entry.get("custom", []) if c not in custom]
        out = {"style": self.style, "items": items, "custom": custom, "by_script": by_script}
        tmp = self._used_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, self._used_path)

    def _use(self, item_id, kind):
        item = self.items.get(item_id)
        if item is None or item["kind"] != kind:
            raise LibraryError(f"unknown {kind} item {item_id!r}")
        if item["style"] != self.style:
            raise LibraryError(f"{item_id}: style {item['style']!r} does not match channel style {self.style!r}")
        if self.selected and item_id not in self.selected:
            raise LibraryError(f"{item_id}: not in the items selected for channel {self.channel_id}")
        if item["status"] == "draft" and item_id not in self._record["items"]:
            print(f"warning: library item {item_id} is a draft", file=sys.stderr)
        if self._record["items"].get(item_id) != item["status"]:
            self._record["items"][item_id] = item["status"]
            self._save()
        return item

    def _custom(self, name):
        if name not in self._record["custom"]:
            self._record["custom"].append(name)
        self._save()

    # -- API
    def look(self, item_id, **variants):
        item = self._use(item_id, "character")
        for k, v in variants.items():
            _check_variant(item, k, v)
        return self.rig.look(**(dict(item["base_look"]) | variants))

    def character(self, item_id, cid, x, y_feet, s=1.0, facing="right", **variants):
        item = self._use(item_id, "character")
        L = self.look(item_id, **variants)
        svg = self.rig.character(cid, x, y_feet, s=s, look=L, facing=facing)
        if item.get("costume"):
            svg = _costume(self.rig, svg, cid, L, item["costume"])
        return svg

    def pose(self, name):
        if name not in self.rig.POSES:
            raise LibraryError(f"unknown pose {name!r} for style {self.style!r}")
        return name

    def env(self, item_id, variant="default"):
        item = self._use(item_id, "env")
        if variant not in item["variants"]:
            raise LibraryError(f"{item_id}: unknown variant {variant!r} (have {item['variants']})")
        mod_file = self._module_path(item)
        spec = importlib.util.spec_from_file_location(f"_libenv_{item_id.replace('-', '_')}", mod_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, item["function"])
        return (lambda rnd, fl: fn(rnd, fl, variant)), item.get("backdrops", {}).get(variant, item["backdrop"])

    def _module_path(self, item):
        for root in (self._local_dir, self._lib_dir):
            if root is None:
                continue
            p = root / "envs" / item["module"]
            if p.is_file():
                return p
        raise LibraryError(f"{item['id']}: module {item['module']!r} not found")

    def custom_look(self, **kw):
        self._custom_looks += 1
        self._custom(f"look:{self._custom_looks}")
        return self.rig.look(**kw)

    def custom_pose(self, name, **params):
        if "face" in params:
            params["face"] = tuple(params["face"])
        self.rig.POSES[name] = dict(params)
        self._custom(name)
        return name
