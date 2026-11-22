"""Load library items (builtin + local) and build library/catalog.json (builtin only)."""
import json
from pathlib import Path

from library.schema import validate_item


class LibraryError(Exception):
    pass


def _files(root):
    """Item files under a library root: characters/*.json, envs/*.json, top-level poses/*.json."""
    for sub in ("characters", "envs", "poses"):
        d = Path(root) / sub
        if d.is_dir():
            yield from sorted(d.glob("*.json"))


def _load_root(root):
    items = {}
    for path in _files(root):
        try:
            item = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise LibraryError(f"{path}: invalid JSON: {e}")
        errs = validate_item(item)
        if errs:
            raise LibraryError(f"{path}: " + "; ".join(errs))
        want = item["id"].replace("/", ".") if item["kind"] == "pose" else item["id"]
        if path.stem != want:
            raise LibraryError(f"{path}: id {item['id']!r} does not match filename")
        if item["id"] in items:
            raise LibraryError(f"duplicate id {item['id']!r} ({path})")
        items[item["id"]] = item
    return items


def _merge(builtin, local_root):
    items = dict(builtin)
    if local_root is not None:
        for iid, item in _load_root(local_root).items():
            if iid in items:
                raise LibraryError(f"local item id {iid!r} shadows a builtin item")
            items[iid] = item
    return items


def load_items(builtin_root, local_root=None):
    return _merge(_load_root(builtin_root), local_root)


def build_catalog(repo_root, local_root=None):
    repo_root = Path(repo_root)
    builtin = _load_root(repo_root / "library")
    _merge(builtin, local_root)  # validates local items and shadowing
    catalog = {"items": [builtin[i] for i in sorted(builtin)]}
    (repo_root / "library" / "catalog.json").write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    return catalog
