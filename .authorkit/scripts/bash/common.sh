#!/usr/bin/env bash
# Common shell functions for Author Kit

# Canonical book directory names (lowercase).
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
  if [[ -n "${AUTHORKIT_BOOK:-}" ]]; then
    echo "$AUTHORKIT_BOOK"
    return
  fi

  if branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); then
    echo "$branch"
    return
  fi

  local repo_root books_dir latest_book="" highest=0
  repo_root="$(get_repo_root)"
  books_dir="$repo_root/books"

  if [[ -d "$books_dir" ]]; then
    while IFS= read -r name; do
      if [[ "$name" =~ ^([0-9]{3})- ]]; then
        local num="${BASH_REMATCH[1]}"
        if ((10#$num > highest)); then
          highest=$((10#$num))
          latest_book="$name"
        fi
      fi
    done < <(find "$books_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n')
  fi

  if [[ -n "$latest_book" ]]; then
    echo "$latest_book"
    return
  fi

  echo "main"
}

test_has_git() {
  git rev-parse --show-toplevel >/dev/null 2>&1
}

test_book_branch() {
  local branch="$1"
  local has_git="$2"

  if [[ "$has_git" != "true" ]]; then
    echo "[authorkit] Warning: Git repository not detected; skipped branch validation" >&2
    return 0
  fi

  if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
    echo "ERROR: Not on a book branch. Current branch: $branch"
    echo "Book branches should be named like: 001-book-name"
    return 1
  fi

  return 0
}

find_book_dir_by_prefix() {
  local repo_root="$1"
  local branch_name="$2"
  local books_dir="$repo_root/books"

  if [[ ! "$branch_name" =~ ^([0-9]{3})- ]]; then
    echo "$books_dir/$branch_name"
    return
  fi

  local prefix="${BASH_REMATCH[1]}"
  local matches=()

  if [[ -d "$books_dir" ]]; then
    while IFS= read -r name; do
      if [[ "$name" =~ ^${prefix}- ]]; then
        matches+=("$name")
      fi
    done < <(find "$books_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n')
  fi

  if [[ ${#matches[@]} -eq 0 ]]; then
    echo "$books_dir/$branch_name"
  elif [[ ${#matches[@]} -eq 1 ]]; then
    echo "$books_dir/${matches[0]}"
  else
    echo "ERROR: Multiple book directories found with prefix '$prefix': ${matches[*]}" >&2
    echo "Please ensure only one book directory exists per numeric prefix." >&2
    echo "$books_dir/$branch_name"
  fi
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

  book_dir="$(find_book_dir_by_prefix "$repo_root" "$current_branch")"

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
  local repo_root current_branch has_git book_dir
  repo_root="$(get_repo_root)"
  current_branch="$(get_current_branch)"
  if test_has_git; then has_git=true; else has_git=false; fi
  book_dir="$(find_book_dir_by_prefix "$repo_root" "$current_branch")"

  printf '{"REPO_ROOT":"%s","BRANCH":"%s","BOOK_DIR":"%s","BOOK_CONCEPT":"%s","OUTLINE":"%s","CHAPTERS":"%s"}\n' \
    "$repo_root" "$current_branch" "$book_dir" "$book_dir/concept.md" "$book_dir/outline.md" "$book_dir/chapters.md"
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
