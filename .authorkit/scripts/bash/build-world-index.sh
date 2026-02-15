#!/usr/bin/env bash
set -e

JSON_MODE=false
ADD_FRONTMATTER=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --add-frontmatter) ADD_FRONTMATTER=true ;;
    --help|-h)
      cat <<'EOF'
Usage: ./build-world-index.sh [--json] [--add-frontmatter]
EOF
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

WORLD_DIR="$BOOK_DIR/World"
INDEX_FILE="$WORLD_DIR/_index.md"

if [[ ! -d "$WORLD_DIR" ]]; then
  echo "ERROR: World/ directory not found at $WORLD_DIR"
  echo "Run /authorkit.world.build first to create the world."
  exit 1
fi

python3 - "$WORLD_DIR" "$INDEX_FILE" "$ADD_FRONTMATTER" "$JSON_MODE" "$BOOK_DIR" <<'PY'
import json
import re
import sys
from pathlib import Path
from datetime import datetime

world_dir = Path(sys.argv[1])
index_file = Path(sys.argv[2])
add_frontmatter = sys.argv[3].lower() == "true"
json_mode = sys.argv[4].lower() == "true"
book_dir = sys.argv[5]

sub_dirs = ["Characters", "Places", "Organizations", "History", "Systems", "Notes"]
type_map = {
    "Characters": ("char-", "character"),
    "Places": ("place-", "place"),
    "Organizations": ("org-", "organization"),
    "History": ("event-", "event"),
    "Systems": ("sys-", "system"),
    "Notes": ("note-", "note"),
}

def kebab(s: str) -> str:
    s = re.sub(r"^(the|a|an)\\s+", "", s.strip().lower())
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

entities = []
files_wo = []
for sub in sub_dirs:
    d = world_dir / sub
    if not d.is_dir():
        continue
    for f in sorted(d.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        rel = f"{sub}/{f.name}"
        m = re.match(r"---\\n(.*?)\\n---\\n", text, flags=re.S)
        if m:
            fm = m.group(1)
            def extract(key, default=""):
                mm = re.search(rf"^{key}:\\s*(.+)$", fm, re.M)
                return mm.group(1).strip() if mm else default
            name = extract("name") or f.stem.replace("-", " ").title()
            aliases = []
            am = re.search(r"^aliases:\\s*\\[([^\\]]*)\\]", fm, re.M)
            if am and am.group(1).strip(): aliases = [x.strip() for x in am.group(1).split(",")]
            ch = []
            cm = re.search(r"^chapters:\\s*\\[([^\\]]*)\\]", fm, re.M)
            if cm and cm.group(1).strip(): ch = [x.strip() for x in cm.group(1).split(",")]
            entities.append({
                "id": extract("id") or f"{type_map.get(sub, ('misc-','misc'))[0]}{kebab(name)}",
                "type": extract("type") or type_map.get(sub, ("misc-","misc"))[1],
                "name": name,
                "aliases": aliases,
                "chapters": ch,
                "first": extract("first_appearance", "CONCEPT"),
                "rel": rel,
                "has_frontmatter": True,
            })
        else:
            lines = text.splitlines()
            name = next((re.sub(r"^#\\s+", "", l).strip() for l in lines if l.startswith("# ")), f.stem.replace("-", " ").title())
            prefix, typ = type_map.get(sub, ("misc-", "misc"))
            ch = sorted(set(re.findall(r"\\((CONCEPT|CH\\d{2}|CH\\d{2}-rev|RETCON-\\d{4}-\\d{2}-\\d{2}|PIVOT-\\d{4}-\\d{2}-\\d{2})\\)", text)))
            ent = {
                "id": f"{prefix}{kebab(name)}",
                "type": typ,
                "name": name,
                "aliases": [],
                "chapters": ch,
                "first": next((x for x in ch if re.match(r"^CH\\d{2}$", x)), "CONCEPT"),
                "rel": rel,
                "has_frontmatter": False,
            }
            entities.append(ent)
            files_wo.append((f, ent))

if add_frontmatter:
    for f, ent in files_wo:
        block = "\\n".join([
            "---",
            f"id: {ent['id']}",
            f"type: {ent['type']}",
            f"name: {ent['name']}",
            "aliases: []",
            f"chapters: [{', '.join(ent['chapters'])}]" if ent['chapters'] else "chapters: []",
            f"first_appearance: {ent['first']}",
            "relationships: []",
            "tags: []",
            f"last_updated: {datetime.now().strftime('%Y-%m-%d')}",
            "---",
            "",
        ])
        f.write_text(block + f.read_text(encoding="utf-8"), encoding="utf-8")
        ent["has_frontmatter"] = True
    files_wo = []

if not entities:
    if json_mode:
        print(json.dumps({"BOOK_DIR": book_dir, "INDEX_FILE": str(index_file), "ENTITY_COUNT": 0, "ALIAS_COUNT": 0, "CHAPTER_COUNT": 0, "FILES_WITHOUT_FRONTMATTER": 0}, separators=(",", ":")))
    sys.exit(0)

entities.sort(key=lambda x: (x["type"], x["name"]))
registry = ["| ID | Type | Name | Aliases | File | Chapters | First Appearance | Flags |", "|----|------|------|---------|------|----------|-----------------|-------|"]
alias_rows = ["| Alias | Entity ID | Type | Ambiguous |", "|-------|-----------|------|-----------|"]
alias_map = {}
chapter_map = {}
for e in entities:
    chapters = ", ".join(e["chapters"])
    aliases = "; ".join(e["aliases"])
    flags = "[NO FRONTMATTER]" if not e["has_frontmatter"] else ""
    registry.append(f"| {e['id']} | {e['type']} | {e['name']} | {aliases} | {e['rel']} | {chapters} | {e['first']} | {flags} |")

    for a in [e["name"], *e["aliases"]]:
        key = a.lower()
        alias_map.setdefault(key, {"display": a, "entities": []})["entities"].append((e["id"], e["type"]))

    for ch in e["chapters"]:
        if re.match(r"^(CONCEPT|CH\\d{2}|CH\\d{2}-rev)$", ch):
            chapter_map.setdefault(ch, set()).add(e["id"])
        m = re.match(r"^(CH\\d{2})-rev$", ch)
        if m:
            chapter_map.setdefault(m.group(1), set()).add(e["id"])

alias_count = 0
for key in sorted(alias_map, key=lambda k: alias_map[k]["display"].lower()):
    ents = alias_map[key]["entities"]
    amb = "YES" if len(ents) > 1 else ""
    for eid, typ in ents:
      alias_rows.append(f"| {alias_map[key]['display']} | {eid} | {typ} | {amb} |")
      alias_count += 1

chapter_keys = []
if "CONCEPT" in chapter_map:
    chapter_keys.append("CONCEPT")
chapter_keys.extend(sorted([k for k in chapter_map if re.match(r"^CH\\d{2}$", k)]))
chapter_keys.extend(sorted([k for k in chapter_map if re.match(r"^CH\\d{2}-rev$", k)]))
manifest = []
for k in chapter_keys:
    manifest.extend([f"### {k}", ", ".join(sorted(chapter_map[k])), ""])

content = "\\n".join([
    "---",
    f"generated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}",
    f"entity_count: {len(entities)}",
    "schema_version: 1",
    "---",
    "",
    "# World Index",
    "",
    "## Entity Registry",
    "",
    *registry,
    "",
    "## Alias Lookup",
    "",
    *alias_rows,
    "",
    "## Chapter Manifest",
    "",
    *manifest,
    "## Statistics",
    "",
    f"- **Total entities**: {len(entities)}",
    f"- **Total aliases**: {alias_count}",
    f"- **Chapters tracked**: {len(chapter_keys)}",
    f"- **Files with frontmatter**: {sum(1 for e in entities if e['has_frontmatter'])}/{len(entities)}",
])
index_file.write_text(content, encoding="utf-8")

result = {"BOOK_DIR": book_dir, "INDEX_FILE": str(index_file), "ENTITY_COUNT": len(entities), "ALIAS_COUNT": alias_count, "CHAPTER_COUNT": len(chapter_keys), "FILES_WITHOUT_FRONTMATTER": len(files_wo)}
if json_mode:
    print(json.dumps(result, separators=(",", ":")))
else:
    for k,v in result.items():
        print(f"{k}: {v}")
PY
