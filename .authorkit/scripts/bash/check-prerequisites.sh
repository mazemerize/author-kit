#!/usr/bin/env bash
set -e

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

test_book_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

if $PATHS_ONLY; then
  if $JSON_MODE; then
    book_paths_json
  else
    echo "REPO_ROOT: $REPO_ROOT"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "BOOK_DIR: $BOOK_DIR"
    echo "BOOK_CONCEPT: $BOOK_CONCEPT"
    echo "OUTLINE: $OUTLINE"
    echo "CHAPTERS: $CHAPTERS"
  fi
  exit 0
fi

if [[ ! -d "$BOOK_DIR" ]]; then
  echo "ERROR: Book directory not found: $BOOK_DIR"
  echo "Run /authorkit.conceive first to create the book structure."
  exit 1
fi

if [[ ! -f "$OUTLINE" ]]; then
  echo "ERROR: outline.md not found in $BOOK_DIR"
  echo "Run /authorkit.outline first to create the book outline."
  exit 1
fi

if $REQUIRE_CHAPTERS && [[ ! -f "$CHAPTERS" ]]; then
  echo "ERROR: chapters.md not found in $BOOK_DIR"
  echo "Run /authorkit.chapters first to create the chapter breakdown."
  exit 1
fi

docs=()
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$CHARACTERS" ]] && docs+=("characters.md")
if [[ -d "$CHAPTERS_DIR" ]] && find "$CHAPTERS_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1 | grep -q .; then
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
  printf '{"BOOK_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$BOOK_DIR" "$json_docs"
else
  echo "BOOK_DIR:$BOOK_DIR"
  echo "AVAILABLE_DOCS:"
  check_file "$RESEARCH" "research.md"
  check_file "$CHARACTERS" "characters.md"
  check_dir_has_files "$CHAPTERS_DIR" "chapters/"
  if $INCLUDE_CHAPTERS; then
    check_file "$CHAPTERS" "chapters.md"
  fi
fi
