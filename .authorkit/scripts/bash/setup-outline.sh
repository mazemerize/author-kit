#!/usr/bin/env bash
set -e

JSON_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --help|-h)
      echo "Usage: ./setup-outline.sh [--json]"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_book_paths)"

test_book_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

mkdir -p "$BOOK_DIR" "$CHAPTERS_DIR"

template="$REPO_ROOT/.authorkit/templates/outline-template.md"
if [[ -f "$template" ]]; then
  cp "$template" "$OUTLINE"
else
  : > "$OUTLINE"
fi

if $JSON_MODE; then
  printf '{"BOOK_CONCEPT":"%s","OUTLINE":"%s","BOOK_DIR":"%s","CHAPTERS_DIR":"%s","BRANCH":"%s","HAS_GIT":%s}\n' \
    "$BOOK_CONCEPT" "$OUTLINE" "$BOOK_DIR" "$CHAPTERS_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
else
  echo "BOOK_CONCEPT: $BOOK_CONCEPT"
  echo "OUTLINE: $OUTLINE"
  echo "BOOK_DIR: $BOOK_DIR"
  echo "CHAPTERS_DIR: $CHAPTERS_DIR"
  echo "BRANCH: $CURRENT_BRANCH"
  echo "HAS_GIT: $HAS_GIT"
fi
