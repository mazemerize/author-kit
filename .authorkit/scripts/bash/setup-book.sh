#!/usr/bin/env bash
set -euo pipefail

JSON_MODE=false
TITLE=""
AUTHOR=""
SUBTITLE=""
LANGUAGE=""
# Tracks whether each --flag was explicitly supplied (vs left unset). Empty
# string is a legitimate value (e.g. --subtitle ""), so we can't infer this
# from the variable contents alone.
TITLE_SET=false
AUTHOR_SET=false
SUBTITLE_SET=false
LANGUAGE_SET=false

show_help() {
  cat <<'EOF'
Usage: ./setup-book.sh [--json] [--title TITLE] [--author AUTHOR] [--subtitle SUBTITLE] [--language LANG]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON_MODE=true; shift ;;
    --title) TITLE="$2"; TITLE_SET=true; shift 2 ;;
    --author) AUTHOR="$2"; AUTHOR_SET=true; shift 2 ;;
    --subtitle) SUBTITLE="$2"; SUBTITLE_SET=true; shift 2 ;;
    --language) LANGUAGE="$2"; LANGUAGE_SET=true; shift 2 ;;
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

# Resolve a usable Python interpreter for the in-place TOML edit helper. Walk
# both `python3` and `python` and verify each candidate actually executes
# Python — `command -v` alone isn't enough on Windows, where it finds the
# Microsoft Store alias stub (`%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe`)
# that emits a UTF-16 "Python was not found" message and exits non-zero
# instead of running.
PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "ERROR: Python (python3 or python) is required for setup-book.sh but was not found on PATH." >&2
  echo "Install Python 3.11+ or run 'authorkit check' to see which dependencies are missing." >&2
  exit 1
fi

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

# Replace `key = "..."` for a top-level [book] string key, in place. Leaves the
# rest of the file (other sections, comments, custom keys) untouched. Uses a
# tempfile + mv pattern for BSD/GNU `sed` portability.
replace_book_string() {
  local file="$1" key="$2" value="$3"
  if ! grep -qE "^${key}[[:space:]]*=" "$file"; then
    return 0
  fi
  local tmp
  tmp="$(mktemp)"
  "$PYTHON_BIN" - "$file" "$key" "$value" >"$tmp" <<'PY'
import sys
path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, "r", encoding="utf-8") as fh:
    text = fh.read()
import re
pattern = re.compile(r'^' + re.escape(key) + r'\s*=\s*"[^"]*"\s*$', re.MULTILINE)
escaped = value.replace("\\", "\\\\").replace('"', '\\"')
new_text, count = pattern.subn(f'{key} = "{escaped}"', text, count=1)
sys.stdout.write(new_text if count else text)
PY
  mv "$tmp" "$file"
}

default_title="$(read_existing title)"
default_author="$(read_existing author)"
default_subtitle="$(read_existing subtitle)"
default_language="$(read_existing language)"

[[ -z "$default_title" ]] && default_title="Untitled Book"
[[ -z "$default_author" ]] && default_author="Unknown Author"
[[ -z "$default_language" ]] && default_language="en-US"

if [[ ! -f "$BOOK_TOML" ]]; then
  # Fresh install: write the full template. `tts_cost_per_1m_chars` ships
  # commented out so users opt in (see README "Book Export"). All other fields
  # have safe defaults that book_core.parse_book_config tolerates.
  if $JSON_MODE; then
    BOOK_TITLE="${TITLE:-$default_title}"
    BOOK_AUTHOR="${AUTHOR:-$default_author}"
    BOOK_SUBTITLE="${SUBTITLE:-$default_subtitle}"
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

    if [[ -n "$SUBTITLE" ]]; then
      BOOK_SUBTITLE="$SUBTITLE"
    else
      read -r -p "Subtitle [$default_subtitle]: " input_subtitle
      BOOK_SUBTITLE="${input_subtitle:-$default_subtitle}"
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
subtitle = "$BOOK_SUBTITLE"

[build]
default_formats = ["docx"]
reference_docx = ".authorkit/templates/publishing/reference.docx"
epub_css = ".authorkit/templates/publishing/epub.css"

[audio]
provider = "openai"
model = "gpt-4o-mini-tts"
voice = "marin"
instructions = ".authorkit/templates/publishing/audio-instructions.txt"
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
# tts_cost_per_1m_chars = 0.000015   # uncomment and set to enable cost estimates in `authorkit book stats`
EOF
else
  # File exists — preserve all user customizations. Only update the four [book]
  # string fields, and only when the corresponding flag was explicitly passed
  # (JSON mode) or the user typed a new value at the prompt (interactive mode).
  if $JSON_MODE; then
    if $TITLE_SET; then replace_book_string "$BOOK_TOML" title "$TITLE"; fi
    if $AUTHOR_SET; then replace_book_string "$BOOK_TOML" author "$AUTHOR"; fi
    if $SUBTITLE_SET; then replace_book_string "$BOOK_TOML" subtitle "$SUBTITLE"; fi
    if $LANGUAGE_SET; then replace_book_string "$BOOK_TOML" language "$LANGUAGE"; fi
  else
    if $TITLE_SET; then
      replace_book_string "$BOOK_TOML" title "$TITLE"
    else
      read -r -p "Update book metadata (book.toml). Title [$default_title]: " input_title
      if [[ -n "$input_title" && "$input_title" != "$default_title" ]]; then
        replace_book_string "$BOOK_TOML" title "$input_title"
      fi
    fi
    if $AUTHOR_SET; then
      replace_book_string "$BOOK_TOML" author "$AUTHOR"
    else
      read -r -p "Author [$default_author]: " input_author
      if [[ -n "$input_author" && "$input_author" != "$default_author" ]]; then
        replace_book_string "$BOOK_TOML" author "$input_author"
      fi
    fi
    if $SUBTITLE_SET; then
      replace_book_string "$BOOK_TOML" subtitle "$SUBTITLE"
    else
      read -r -p "Subtitle [$default_subtitle]: " input_subtitle
      if [[ -n "$input_subtitle" && "$input_subtitle" != "$default_subtitle" ]]; then
        replace_book_string "$BOOK_TOML" subtitle "$input_subtitle"
      fi
    fi
    if $LANGUAGE_SET; then
      replace_book_string "$BOOK_TOML" language "$LANGUAGE"
    else
      read -r -p "Language [$default_language]: " input_language
      if [[ -n "$input_language" && "$input_language" != "$default_language" ]]; then
        replace_book_string "$BOOK_TOML" language "$input_language"
      fi
    fi
  fi
fi

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
