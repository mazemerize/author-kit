#!/usr/bin/env bash
set -e

# Deprecated compatibility shim. Use setup-book.sh instead.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/setup-book.sh"

if [[ ! -f "$TARGET" ]]; then
  echo "Missing setup script: $TARGET" >&2
  exit 1
fi

echo "[authorkit] create-new-book.sh is deprecated. Use setup-book.sh." >&2

forward=()
expects_value=false
for arg in "$@"; do
  if $expects_value; then
    forward+=("$arg")
    expects_value=false
    continue
  fi

  case "$arg" in
    --json|-Json|--help|-h|-Help)
      forward+=("$arg")
      ;;
    --title|-Title|--author|-Author|--language|-Language)
      forward+=("$arg")
      expects_value=true
      ;;
    *)
      # Ignore legacy positional description and removed options.
      ;;
  esac
done

"$TARGET" "${forward[@]}"
