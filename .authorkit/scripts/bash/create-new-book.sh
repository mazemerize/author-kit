#!/usr/bin/env bash
set -e

JSON_MODE=false
SHORT_NAME=""
NUMBER=0

show_help() {
  cat <<'EOF'
Usage: ./create-new-book.sh [--json] [--short-name NAME] [--number N] <book description>
EOF
}

BOOK_DESC_PARTS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON_MODE=true; shift ;;
    --short-name) SHORT_NAME="$2"; shift 2 ;;
    --number) NUMBER="$2"; shift 2 ;;
    --help|-h) show_help; exit 0 ;;
    *) BOOK_DESC_PARTS+=("$1"); shift ;;
  esac
done

if [[ ${#BOOK_DESC_PARTS[@]} -eq 0 ]]; then
  show_help
  exit 1
fi

BOOK_DESC="${BOOK_DESC_PARTS[*]}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
cd "$REPO_ROOT"

BOOKS_DIR="$REPO_ROOT/books"
mkdir -p "$BOOKS_DIR"

clean_branch_name() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/-+/-/g; s/^-//; s/-$//'
}

get_highest_books() {
  local highest=0
  if [[ -d "$BOOKS_DIR" ]]; then
    while IFS= read -r name; do
      if [[ "$name" =~ ^([0-9]+)- ]]; then
        n=${BASH_REMATCH[1]}
        ((10#$n > highest)) && highest=$((10#$n))
      fi
    done < <(find "$BOOKS_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n')
  fi
  echo "$highest"
}

get_highest_branches() {
  local highest=0
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    while IFS= read -r line; do
      branch=$(echo "$line" | sed -E 's/^\*?\s+//; s#^remotes/[^/]+/##')
      if [[ "$branch" =~ ^([0-9]+)- ]]; then
        n=${BASH_REMATCH[1]}
        ((10#$n > highest)) && highest=$((10#$n))
      fi
    done < <(git branch -a 2>/dev/null)
  fi
  echo "$highest"
}

if [[ -n "$SHORT_NAME" ]]; then
  BRANCH_SUFFIX="$(clean_branch_name "$SHORT_NAME")"
else
  BRANCH_SUFFIX="$(clean_branch_name "$BOOK_DESC")"
  BRANCH_SUFFIX="$(echo "$BRANCH_SUFFIX" | cut -d'-' -f1-3)"
fi

HAS_GIT=false
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  HAS_GIT=true
fi

if [[ "$NUMBER" == "0" ]]; then
  hb=$(get_highest_books)
  hr=$(get_highest_branches)
  if ((hr > hb)); then NUMBER=$((hr + 1)); else NUMBER=$((hb + 1)); fi
fi

BOOK_NUM=$(printf '%03d' "$NUMBER")
BRANCH_NAME="$BOOK_NUM-$BRANCH_SUFFIX"

if [[ ${#BRANCH_NAME} -gt 244 ]]; then
  max_suffix=$((244 - 4))
  BRANCH_SUFFIX="${BRANCH_SUFFIX:0:$max_suffix}"
  BRANCH_SUFFIX="${BRANCH_SUFFIX%-}"
  BRANCH_NAME="$BOOK_NUM-$BRANCH_SUFFIX"
fi

if [[ "$HAS_GIT" == "true" ]]; then
  git checkout -b "$BRANCH_NAME" >/dev/null 2>&1 || true
fi

BOOK_DIR="$BOOKS_DIR/$BRANCH_NAME"
mkdir -p "$BOOK_DIR/chapters"

if [[ -f "$REPO_ROOT/.authorkit/templates/concept-template.md" ]]; then
  cp "$REPO_ROOT/.authorkit/templates/concept-template.md" "$BOOK_DIR/concept.md"
else
  : > "$BOOK_DIR/concept.md"
fi

export AUTHORKIT_BOOK="$BRANCH_NAME"

default_title="$(echo "$BRANCH_SUFFIX" | tr '-' ' ')"
default_author="Unknown Author"
default_language="en-US"

if $JSON_MODE; then
  BOOK_TITLE="$default_title"
  BOOK_AUTHOR="$default_author"
  BOOK_LANGUAGE="$default_language"
else
  read -r -p "Initialize book metadata (book.toml). Title [$default_title]: " input_title
  read -r -p "Author [$default_author]: " input_author
  read -r -p "Language [$default_language]: " input_language
  BOOK_TITLE="${input_title:-$default_title}"
  BOOK_AUTHOR="${input_author:-$default_author}"
  BOOK_LANGUAGE="${input_language:-$default_language}"
fi

BOOK_TOML="$BOOK_DIR/book.toml"
cat > "$BOOK_TOML" <<EOF
[book]
title = "$BOOK_TITLE"
author = "$BOOK_AUTHOR"
language = "$BOOK_LANGUAGE"
subtitle = ""

[build]
default_formats = ["docx"]
reference_docx = ".authorkit/templates/publishing/reference.docx"
epub_css = ".authorkit/templates/publishing/epub.css"

[audio]
provider = "openai"
model = "gpt-4o-mini-tts"
voice = "onyx"
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
tts_cost_per_1m_chars = 0.0
EOF

if $JSON_MODE; then
  printf '{"BRANCH_NAME":"%s","CONCEPT_FILE":"%s","BOOK_NUM":"%s","BOOK_DIR":"%s","BOOK_TOML":"%s","HAS_GIT":%s}\n' \
    "$BRANCH_NAME" "$BOOK_DIR/concept.md" "$BOOK_NUM" "$BOOK_DIR" "$BOOK_TOML" "$HAS_GIT"
else
  echo "BRANCH_NAME: $BRANCH_NAME"
  echo "CONCEPT_FILE: $BOOK_DIR/concept.md"
  echo "BOOK_NUM: $BOOK_NUM"
  echo "BOOK_DIR: $BOOK_DIR"
  echo "BOOK_TOML: $BOOK_TOML"
  echo "HAS_GIT: $HAS_GIT"
  echo "AUTHORKIT_BOOK environment variable set to: $BRANCH_NAME"
fi
