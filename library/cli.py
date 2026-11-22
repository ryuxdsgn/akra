"""Library command line: python3 library/cli.py <list|build-catalog|preview|vet|freeze|promote> ..."""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):  # run as a script: put the repo root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from library.catalog import LibraryError, build_catalog, load_items  # noqa: E402
from library.freeze import freeze  # noqa: E402
from library.schema import validate_item  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
_CHANNEL_ONLY = ("real_name", "notes")


def _roots(root):
    local = root / "channels" / "_library"
    return root / "library", (local if local.is_dir() else None)


def _locate(root, iid):
    """-> (item, item_file, base_dir, is_local) for an id in library/ or channels/_library/."""
    for base, is_local in ((root / "library", False), (root / "channels" / "_library", True)):
        for sub in ("characters", "envs", "poses"):
            d = base / sub
            for f in sorted(d.glob("*.json")) if d.is_dir() else ():
                item = json.loads(f.read_text())
                if item.get("id") == iid:
                    return item, f, base, is_local
    raise LibraryError(f"unknown item {iid!r}")


def _preview_file(item, base):
    return base / item["preview"]


def cmd_list(args, root):
    items = load_items(*_roots(root))
    for iid in sorted(items):
        it = items[iid]
        if args.kind and it["kind"] != args.kind or args.style and it["style"] != args.style \
                or args.status and it["status"] != args.status:
            continue
        print(f"{iid}  {it['kind']}  {it['style']}  {it['status']}  {it['origin']}")
    return 0


def _render(item, base, root):
    from library.preview import render_preview
    out = render_preview(item, _preview_file(item, base), root=root, base=base)
    print(out)
    return out


def cmd_build_catalog(args, root):
    lib, local = _roots(root)
    build_catalog(root, local)
    print(f"wrote {lib / 'catalog.json'}")
    if args.previews:
        for iid in sorted(load_items(lib, local)):  # strictly serial: one Chrome process at a time
            item, _, base, _ = _locate(root, iid)
            _render(item, base, root)
    return 0


def cmd_preview(args, root):
    item, _, base, _ = _locate(root, args.id)
    _render(item, base, root)
    return 0


def cmd_vet(args, root):
    item, f, base, _ = _locate(root, args.id)
    png = _preview_file(item, base)
    if not png.is_file():
        print(f"error: preview {png} is missing; run `preview {args.id}` first", file=sys.stderr)
        return 1
    if png.stat().st_mtime < f.stat().st_mtime:
        print(f"error: preview {png} is older than {f.name}; regenerate it", file=sys.stderr)
        return 1
    item["status"] = "vetted"
    errs = validate_item(item)
    if errs:
        print("error: " + "; ".join(errs), file=sys.stderr)
        return 1
    f.write_text(json.dumps(item, indent=2) + "\n")
    os.utime(png, None)                       # the preview still shows this item: keep it fresher than the file
    build_catalog(root, _roots(root)[1])      # catalog.json carries status
    print(f"{args.id}: vetted")
    return 0


def cmd_freeze(args, root):
    done = freeze(Path(args.project), refresh=args.refresh)
    print("frozen" if done else "nothing to do")
    return 0


def cmd_promote(args, root):
    item, f, base, is_local = _locate(root, args.id)
    if not is_local:
        print(f"error: {args.id} is already builtin", file=sys.stderr)
        return 1
    if item.get("status") != "vetted":
        print(f"error: {args.id} is {item.get('status')!r}; vet it before promoting", file=sys.stderr)
        return 1
    if not args.yes:
        print(f"error: refusing to promote {args.id} to library/ without --yes", file=sys.stderr)
        return 1
    dropped = [k for k in _CHANNEL_ONLY if k in item]
    for k in dropped:
        del item[k]
    item["origin"] = "builtin"
    item["examples"] = []
    errs = validate_item(item)
    if errs:
        print("error: " + "; ".join(errs), file=sys.stderr)
        return 1
    lib = root / "library"
    moves = [(f, lib / f.parent.name / f.name)]                     # (source, destination), moved
    copies = []                                                      # shared helpers, copied
    if item["kind"] == "pose":
        moves.append((base / item["params_file"], lib / item["params_file"]))
    if item["kind"] == "env":
        mod = base / "envs" / item["module"]
        moves.append((mod, lib / "envs" / item["module"]))
        for helper in re.findall(r'with_name\(["\'](_[\w]+\.py)["\']\)', mod.read_text() if mod.is_file() else ""):
            src, dst = base / "envs" / helper, lib / "envs" / helper
            if dst.is_file():
                if src.is_file() and src.read_bytes() != dst.read_bytes():
                    print(f"error: helper {helper} differs from library/envs/{helper}; merge it by hand", file=sys.stderr)
                    return 1
            elif src.is_file():
                copies.append((src, dst))
            else:
                print(f"error: helper {helper} imported by {item['module']} not found", file=sys.stderr)
                return 1
    png = base / item["preview"]
    if png.is_file():
        moves.append((png, lib / item["preview"]))
    for src, dst in moves[1:]:
        if not src.is_file():
            print(f"error: {src} is missing", file=sys.stderr)
            return 1
    clash = [str(dst.relative_to(root)) for _, dst in moves if dst.exists()]
    if clash:
        print(f"error: {', '.join(clash)} already exists; rename the item before promoting", file=sys.stderr)
        return 1
    for src, dst in copies:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
    dst0 = moves[0][1]
    dst0.parent.mkdir(parents=True, exist_ok=True)
    dst0.write_text(json.dumps(item, indent=2) + "\n")
    f.unlink()
    for src, dst in moves[1:]:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    build_catalog(root, _roots(root)[1])      # the promoted item is builtin now
    print(f"promoted {args.id} to library/")
    if dropped:
        print("dropped fields: " + ", ".join(dropped))
    return 0


def main(argv=None, root=None):
    root = Path(root) if root else REPO
    ap = argparse.ArgumentParser(prog="library/cli.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--kind", choices=("character", "pose", "env"))
    p.add_argument("--style", choices=("hw", "toon"))
    p.add_argument("--status", choices=("draft", "vetted"))
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("build-catalog")
    p.add_argument("--previews", action="store_true")
    p.set_defaults(fn=cmd_build_catalog)
    for name, fn in (("preview", cmd_preview), ("vet", cmd_vet), ("promote", cmd_promote)):
        p = sub.add_parser(name)
        p.add_argument("id")
        if name == "promote":
            p.add_argument("--yes", action="store_true")
        p.set_defaults(fn=fn)
    p = sub.add_parser("freeze")
    p.add_argument("project")
    p.add_argument("--refresh", action="store_true")
    p.set_defaults(fn=cmd_freeze)
    args = ap.parse_args(argv)
    try:
        return args.fn(args, root)
    except LibraryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
