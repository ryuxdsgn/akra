#!/usr/bin/env python3
"""Package the akra skill for Claude.ai, ChatGPT (Custom GPT) and Gemini (Gem).

Usage: python3 tools/build_dist.py [--src skills/akra] [--out dist]
"""
import argparse
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

CHATGPT_LIMIT = 8000  # max characters in a Custom GPT "Instructions" field
GEMINI_MAX_FILES = 10  # max knowledge files per Gem (verify in Gemini)
GEMINI_SKIP_REFS = {"library.md"}  # local-only mode (needs Python and the repo filesystem); keeps a Gem within the file limit
GEMINI_MERGE_REFS = {"youtube-policy.md": "rules.md"}  # appended to another knowledge file to stay within the file limit
PLATFORMS = ("claude-ai", "chatgpt", "gemini")
SKIP = {"__pycache__", ".DS_Store"}

CHATGPT_HEADER = """# akra (Custom GPT)
Files mentioned below as `references/<name>.md`, `templates/<name>` and `scripts/validate_episode.py` are uploaded as Knowledge files named `<name>` (without folders). Read them from Knowledge when the router says so. Use Code Interpreter to run `validate_episode.py`. Uploaded files sit in one flat folder, so always pass the profile explicitly: `python3 validate_episode.py validate <episode.json> --channel <channel.json>`.

## In this GPT
- New user, no profile pasted: greet in their language, say in one line what you do here, then run mode `channel` (niche, language, concept, visual style, voice, schedule). Give `channel.json` and `style-bible.md` as code blocks to save, and ask them to paste `channel.json` at the start of every new chat.
- You write and plan: channel, niche, ideas, script, storyboard, TTS text, title/description/hashtags, validation, weekly review from numbers they paste.
- You cannot make voice, render video or upload here. For `build`, deliver the storyboard, the TTS text and the voice settings, and say the full pipeline (voice, render, QA, YouTube upload) runs on their own computer with Codex or Claude Code: github.com/ryuxdsgn/akra, docs/setup.md.
- Never ask for an API key, token or password; this GPT needs none. Keys live only in the user's own `.env` / `client_secret.json`.

"""

GPT_SETUP = """# Creating the "Akra" Custom GPT

1. ChatGPT -> Explore GPTs -> Create -> **Configure** tab.
2. **Name:** Akra - Shorts Writer
3. **Description:** Plan a faceless YouTube Shorts channel and write scripts, storyboards and upload packages in your channel's language.
4. **Instructions:** paste the whole content of `instructions.md` (under the 8,000 character limit).
5. **Conversation starters:**
   - Create a new channel for me
   - Fill the idea bank for my channel
   - Write the next Shorts script
   - Prepare the title, description and hashtags
6. **Knowledge:** upload all files in the `knowledge/` folder.
7. **Capabilities:** turn on **Code Interpreter & Data Analysis** (for `validate_episode.py`) and **Web Search** (niche and fact research). Image generation is not needed.
8. **Actions:** leave empty. This GPT uses no API key.
9. Save with the visibility you want (Only me, Anyone with the link, or the GPT Store).

Voiceover, video render and automatic upload do not run in ChatGPT. For those, use Codex or Claude Code on your own computer (see docs/setup.md in the repo).
"""

GEMINI_HEADER = """# akra (Gemini Gem)
Files mentioned below as `references/<name>.md` are uploaded as Knowledge files named `<name>.md` (without folders), except `references/youtube-policy.md`, which is the second half of `rules.md`. All `templates/<name>` files are merged into one Knowledge file, `templates.md`, one section per template. This Gem cannot run Python: always validate with the manual checklist in rules.md and report each item as pass or fail.

"""


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\r?\n.*?\r?\n---(?:\r?\n)+", "", text, count=1, flags=re.S)


def _files(src: Path):
    """Every file under src, following symlinked folders (no loops)."""
    seen = set()
    for dirpath, dirnames, filenames in os.walk(src, followlinks=True):
        real = os.path.realpath(dirpath)
        if real in seen:
            dirnames[:] = []
            continue
        seen.add(real)
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP)
        for name in sorted(filenames):
            if name not in SKIP:
                yield Path(dirpath) / name


def _write_zip(src: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for path in _files(src):
            z.write(path, f"{src.name}/{path.relative_to(src).as_posix()}")
    return target


def _folder_files(src: Path, folder: str) -> list:
    return [p for p in sorted((src / folder).iterdir()) if p.is_file() and p.name not in SKIP]


def _merged_templates(src: Path) -> str:
    parts = ["# Templates\n"]
    for path in _folder_files(src, "templates"):
        lang = {".json": "json", ".csv": "csv"}.get(path.suffix, "markdown")
        parts.append(f"\n## {path.name}\n\n````{lang}\n{path.read_text(encoding='utf-8').rstrip()}\n````\n")
    return "".join(parts)


def _write_chat_bundle(src: Path, target: Path, header: str, gemini: bool, setup: str = "") -> Path:
    knowledge = target / "knowledge"
    knowledge.mkdir(parents=True)
    if setup:
        (target / "gpt-setup.md").write_text(setup, encoding="utf-8")
    body = _strip_frontmatter((src / "SKILL.md").read_text(encoding="utf-8"))
    (target / "instructions.md").write_text(header + body, encoding="utf-8")
    for path in _folder_files(src, "references"):
        if gemini and path.name in GEMINI_SKIP_REFS:
            continue
        if f"references/{path.name}" not in body:   # only what the router points to (local add-on docs stay local)
            continue
        if gemini and path.name in GEMINI_MERGE_REFS:
            continue
        shutil.copy2(path, knowledge / path.name)
    if gemini:
        for name, into in GEMINI_MERGE_REFS.items():
            if f"references/{name}" in body and (src / "references" / name).is_file():
                with open(knowledge / into, "a", encoding="utf-8") as fh:
                    fh.write("\n\n" + (src / "references" / name).read_text(encoding="utf-8"))
        (knowledge / "templates.md").write_text(_merged_templates(src), encoding="utf-8")
        count = sum(1 for p in knowledge.iterdir() if p.is_file())
        if count > GEMINI_MAX_FILES:
            raise ValueError(f"gemini knowledge: {count} files > {GEMINI_MAX_FILES}")
    else:
        for path in _folder_files(src, "templates"):
            shutil.copy2(path, knowledge / path.name)
        shutil.copy2(src / "scripts" / "validate_episode.py", knowledge / "validate_episode.py")
    return target


def build(src: Path, out: Path) -> dict:
    """Build every platform bundle into `out`, replacing earlier output."""
    src, out = Path(src).resolve(), Path(out).resolve()
    if not (src / "SKILL.md").is_file():
        raise ValueError(f"{src}: SKILL.md not found")
    if out == src or out in src.parents:
        raise ValueError(f"{out}: output folder must not contain the skill source")
    instructions = CHATGPT_HEADER + _strip_frontmatter((src / "SKILL.md").read_text(encoding="utf-8"))
    if len(instructions) > CHATGPT_LIMIT:
        raise ValueError(f"chatgpt instructions: {len(instructions)} > {CHATGPT_LIMIT} chars")
    for platform in PLATFORMS:  # only ever delete what this tool creates
        if (out / platform).is_dir():
            shutil.rmtree(out / platform)
    return {
        "claude-ai": _write_zip(src, out / "claude-ai" / f"{src.name}.zip"),
        "chatgpt": _write_chat_bundle(src, out / "chatgpt", CHATGPT_HEADER, gemini=False, setup=GPT_SETUP),
        "gemini": _write_chat_bundle(src, out / "gemini", GEMINI_HEADER, gemini=True),
    }


def main(argv: list) -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", type=Path, default=root / "skills" / "akra")
    parser.add_argument("--out", type=Path, default=root / "dist")
    args = parser.parse_args(argv)
    try:
        paths = build(args.src, args.out)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc.filename or args.out}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    for platform, path in paths.items():
        print(f"{platform:10} {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
