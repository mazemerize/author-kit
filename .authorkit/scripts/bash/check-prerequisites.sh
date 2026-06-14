#!/usr/bin/env bash
set -euo pipefail

JSON_MODE=false
REQUIRE_CHAPTERS=false
INCLUDE_CHAPTERS=false
PATHS_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --require-chapters) REQUIRE_CHAPTERS=true ;;
    --include-chapters) INCLUDE_CHAPTERS=true ;;
    --paths-only) PATHS_ONLY=true ;;
    --help|-h)
      cat <<'EOF'
Usage: check-prerequisites.sh [OPTIONS]

OPTIONS:
  --json               Output in JSON format
  --require-chapters   Require chapters.md to exist
  --include-chapters   Include chapters.md in AVAILABLE_DOCS list
  --paths-only         Only output path variables
  --help, -h           Show help message
EOF
      exit 0
      ;;
    *)
      echo "ERROR: Unknown option '$arg'" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_book_paths)"

if $PATHS_ONLY; then
  if $JSON_MODE; then
    book_paths_json
  else
    echo "REPO_ROOT: $REPO_ROOT"
    echo "BOOK_DIR: $BOOK_DIR"
    echo "BOOK_CONCEPT: $BOOK_CONCEPT"
    echo "STYLE_ANCHOR: $STYLE_ANCHOR"
    echo "OUTLINE: $OUTLINE"
    echo "CHAPTERS: $CHAPTERS"
  fi
  exit 0
fi

if [[ ! -d "$BOOK_DIR" ]]; then
  echo "ERROR: Book directory not found: $BOOK_DIR"
  echo "Run /authorkit.discuss first to create the book structure."
  exit 1
fi

if [[ ! -f "$OUTLINE" ]]; then
  echo "ERROR: outline.md not found in $BOOK_DIR"
  echo "Run /authorkit.write outline first to create the book outline."
  exit 1
fi

if $REQUIRE_CHAPTERS && [[ ! -f "$CHAPTERS" ]]; then
  echo "ERROR: chapters.md not found in $BOOK_DIR"
  echo "Run /authorkit.write first to create the chapter breakdown."
  exit 1
fi

dir_has_chapter_subdirs() {
  # Only pure-numeric chapter folders (e.g. 01, 02) that contain a draft.md
  # count as drafted chapters — this mirrors the CLI's discover_chapter_drafts
  # convention (book/chapters/NN/draft.md) so backups like `01-old/`, stray
  # dirs, or an empty `01/` don't make the dir look populated when
  # build/stats/status would find nothing.
  [[ -d "$1" ]] || return 1
  local entry base
  for entry in "$1"/*/; do
    [[ -d "$entry" ]] || continue
    base=$(basename "$entry")
    [[ "$base" =~ ^[0-9]+$ ]] || continue
    [[ -f "${entry}draft.md" ]] && return 0
  done
  return 1
}

docs=()
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$CHARACTERS" ]] && docs+=("characters.md")
if dir_has_chapter_subdirs "$CHAPTERS_DIR"; then
  docs+=("chapters/")
fi
if $INCLUDE_CHAPTERS && [[ -f "$CHAPTERS" ]]; then
  docs+=("chapters.md")
fi

if $JSON_MODE; then
  if [[ ${#docs[@]} -eq 0 ]]; then
    json_docs="[]"
  else
    json_docs=$(printf '"%s",' "${docs[@]}")
    json_docs="[${json_docs%,}]"
  fi
  printf '{"BOOK_DIR":"%s","STYLE_ANCHOR":"%s","AVAILABLE_DOCS":%s}\n' "$BOOK_DIR" "$STYLE_ANCHOR" "$json_docs"
else
  echo "BOOK_DIR:$BOOK_DIR"
  echo "STYLE_ANCHOR:$STYLE_ANCHOR"
  echo "AVAILABLE_DOCS:"
  # `check_file` returns 1 when the file is missing — that's expected for an
  # optional doc, but `set -e` would otherwise terminate the script. Disable
  # the side effect with `|| true` so we keep printing the full doc list.
  check_file "$RESEARCH" "research.md" || true
  check_file "$CHARACTERS" "characters.md" || true
  if dir_has_chapter_subdirs "$CHAPTERS_DIR"; then
    echo "  + chapters/"
  else
    echo "  - chapters/"
  fi
  if $INCLUDE_CHAPTERS; then
    check_file "$CHAPTERS" "chapters.md" || true
  fi
fi
