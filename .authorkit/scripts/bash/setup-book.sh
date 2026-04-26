#!/usr/bin/env bash
set -e

JSON_MODE=false
TITLE=""
AUTHOR=""
LANGUAGE=""

show_help() {
  cat <<'EOF'
Usage: ./setup-book.sh [--json] [--title TITLE] [--author AUTHOR] [--language LANG]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json|-Json) JSON_MODE=true; shift ;;
    --title|-Title) TITLE="$2"; shift 2 ;;
    --author|-Author) AUTHOR="$2"; shift 2 ;;
    --language|-Language) LANGUAGE="$2"; shift 2 ;;
    --help|-h) show_help; exit 0 ;;
    *)
      echo "ERROR: Unknown option '$1'" >&2
      show_help
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_book_paths)"
cd "$REPO_ROOT"

mkdir -p "$BOOK_DIR" "$CHAPTERS_DIR"

if [[ -f "$REPO_ROOT/.authorkit/templates/concept-template.md" ]] && [[ ! -f "$BOOK_CONCEPT" ]]; then
  cp "$REPO_ROOT/.authorkit/templates/concept-template.md" "$BOOK_CONCEPT"
elif [[ ! -f "$BOOK_CONCEPT" ]]; then
  : > "$BOOK_CONCEPT"
fi

if [[ -f "$REPO_ROOT/.authorkit/templates/style-anchor-template.md" ]] && [[ ! -f "$STYLE_ANCHOR" ]]; then
  cp "$REPO_ROOT/.authorkit/templates/style-anchor-template.md" "$STYLE_ANCHOR"
elif [[ ! -f "$STYLE_ANCHOR" ]]; then
  : > "$STYLE_ANCHOR"
fi

BOOK_TOML="$BOOK_DIR/book.toml"

read_existing() {
  local key="$1"
  if [[ -f "$BOOK_TOML" ]]; then
    sed -n -E "s/^${key}[[:space:]]*=[[:space:]]*\"([^\"]*)\"[[:space:]]*$/\1/p" "$BOOK_TOML" | head -n 1
  fi
}

default_title="$(read_existing title)"
default_author="$(read_existing author)"
default_language="$(read_existing language)"

[[ -z "$default_title" ]] && default_title="Untitled Book"
[[ -z "$default_author" ]] && default_author="Unknown Author"
[[ -z "$default_language" ]] && default_language="en-US"

if $JSON_MODE; then
  BOOK_TITLE="${TITLE:-$default_title}"
  BOOK_AUTHOR="${AUTHOR:-$default_author}"
  BOOK_LANGUAGE="${LANGUAGE:-$default_language}"
else
  if [[ -n "$TITLE" ]]; then
    BOOK_TITLE="$TITLE"
  else
    read -r -p "Initialize book metadata (book.toml). Title [$default_title]: " input_title
    BOOK_TITLE="${input_title:-$default_title}"
  fi

  if [[ -n "$AUTHOR" ]]; then
    BOOK_AUTHOR="$AUTHOR"
  else
    read -r -p "Author [$default_author]: " input_author
    BOOK_AUTHOR="${input_author:-$default_author}"
  fi

  if [[ -n "$LANGUAGE" ]]; then
    BOOK_LANGUAGE="$LANGUAGE"
  else
    read -r -p "Language [$default_language]: " input_language
    BOOK_LANGUAGE="${input_language:-$default_language}"
  fi
fi

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
instructions = ".authorkit/templates/publishing/audio-instructions.txt"
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
tts_cost_per_1m_chars = 0.0
EOF

if $JSON_MODE; then
  printf '{"BOOK_DIR":"%s","CONCEPT_FILE":"%s","STYLE_ANCHOR":"%s","BOOK_TOML":"%s","HAS_GIT":%s}\n' \
    "$BOOK_DIR" "$BOOK_CONCEPT" "$STYLE_ANCHOR" "$BOOK_TOML" "$HAS_GIT"
else
  echo "BOOK_DIR: $BOOK_DIR"
  echo "CONCEPT_FILE: $BOOK_CONCEPT"
  echo "STYLE_ANCHOR: $STYLE_ANCHOR"
  echo "BOOK_TOML: $BOOK_TOML"
  echo "HAS_GIT: $HAS_GIT"
fi
