#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PINKFISH_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SECRETS_FILE="$SCRIPT_DIR/secrets.env"

if [[ -f "$SECRETS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$SECRETS_FILE"
else
    echo "Warning: $SECRETS_FILE not found; notifications will be skipped." >&2
    echo "Copy secrets.env.example to secrets.env and fill in your values." >&2
fi

LOCAL_SECRETS_FILE="$SCRIPT_DIR/secrets.env.local"
if [[ -f "$LOCAL_SECRETS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$LOCAL_SECRETS_FILE"
fi

if [[ -f "$PINKFISH_ROOT/venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$PINKFISH_ROOT/venv/bin/activate"
fi

cd "$SCRIPT_DIR"
exec python signals.py --no-open "$@"
