#!/usr/bin/env bash
# Common shell functions for Author Kit

# Canonical book directory names (lowercase).
AUTHORKIT_BOOK_DIR="book"
AUTHORKIT_WORLD_DIR="world"
AUTHORKIT_CHAPTERS_DIR="chapters"
AUTHORKIT_CHECKLISTS_DIR="checklists"
AUTHORKIT_DIST_DIR="dist"

get_repo_root() {
  if git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
    echo "$git_root"
    return
  fi
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$script_dir/../../.." && pwd
}

get_current_branch() {
  if branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); then
    if [[ -n "$branch" ]]; then
      echo "$branch"
      return
    fi
  fi
  echo "main"
}

test_has_git() {
  git rev-parse --show-toplevel >/dev/null 2>&1
}

test_book_branch() {
  # Deprecated no-op retained for compatibility with older scripts.
  return 0
}

get_book_paths() {
  local repo_root current_branch has_git book_dir
  repo_root="$(get_repo_root)"
  current_branch="$(get_current_branch)"

  if test_has_git; then
    has_git="true"
  else
    has_git="false"
  fi

  book_dir="$repo_root/$AUTHORKIT_BOOK_DIR"

  cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git'
BOOK_DIR='$book_dir'
BOOK_CONCEPT='$book_dir/concept.md'
OUTLINE='$book_dir/outline.md'
CHAPTERS='$book_dir/chapters.md'
RESEARCH='$book_dir/research.md'
CHARACTERS='$book_dir/characters.md'
WORLD_DIR='$book_dir/$AUTHORKIT_WORLD_DIR'
CHAPTERS_DIR='$book_dir/$AUTHORKIT_CHAPTERS_DIR'
CHECKLISTS_DIR='$book_dir/$AUTHORKIT_CHECKLISTS_DIR'
DIST_DIR='$book_dir/$AUTHORKIT_DIST_DIR'
EOF
}

book_paths_json() {
  local repo_root has_git book_dir
  repo_root="$(get_repo_root)"
  if test_has_git; then has_git=true; else has_git=false; fi
  book_dir="$repo_root/$AUTHORKIT_BOOK_DIR"

  printf '{"REPO_ROOT":"%s","BOOK_DIR":"%s","BOOK_CONCEPT":"%s","OUTLINE":"%s","CHAPTERS":"%s","HAS_GIT":%s}\n' \
    "$repo_root" "$book_dir" "$book_dir/concept.md" "$book_dir/outline.md" "$book_dir/chapters.md" "$has_git"
}

check_file() {
  local path="$1" desc="$2"
  if [[ -f "$path" ]]; then
    echo "  + $desc"
    return 0
  fi
  echo "  - $desc"
  return 1
}

check_dir_has_files() {
  local path="$1" desc="$2"
  if [[ -d "$path" ]] && find "$path" -type f | head -n 1 | grep -q .; then
    echo "  + $desc"
    return 0
  fi
  echo "  - $desc"
  return 1
}
