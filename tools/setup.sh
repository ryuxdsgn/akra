#!/usr/bin/env bash
# One-time setup for akra on macOS/Linux. Run from anywhere:
#   tools/setup.sh              # .env from .env.example + check
#   tools/setup.sh --kokoro     # + local voice (Kokoro-82M, Apache-2.0, ~300 MB)
#   tools/setup.sh --youtube    # + YouTube upload/stats client
#   tools/setup.sh --all        # everything above
# Needs uv (https://docs.astral.sh/uv/) for the Python venvs. Never prints or sends keys.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

want_kokoro=0; want_youtube=0
for a in "$@"; do
  case "$a" in
    --kokoro) want_kokoro=1 ;;
    --youtube) want_youtube=1 ;;
    --all) want_kokoro=1; want_youtube=1 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created .env from .env.example (put your keys there; this file is never committed)."
fi

need_uv() {
  command -v uv >/dev/null || { echo "uv is not installed: https://docs.astral.sh/uv/getting-started/installation/" >&2; exit 1; }
}

if [ "$want_kokoro" = 1 ]; then
  need_uv
  [ -x .venv-kokoro/bin/python ] || uv venv --python 3.12 .venv-kokoro
  uv pip install --python .venv-kokoro/bin/python "kokoro>=0.9.4" soundfile
  echo "Kokoro ready: .venv-kokoro"
fi

if [ "$want_youtube" = 1 ]; then
  need_uv
  [ -x .venv-youtube/bin/python ] || uv venv --python 3.12 .venv-youtube
  uv pip install --python .venv-youtube/bin/python google-api-python-client google-auth-oauthlib
  echo "YouTube client ready: .venv-youtube (continue with the client_secret.json step in docs/setup.md)"
fi

echo
python3 tools/doctor.py
