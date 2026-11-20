#!/usr/bin/env python3
"""Save a note into the right vault folder with frontmatter, never overwriting anything.

The body is written exactly as given (verbatim capture). A date-prefixed slug is made
from the title; if the file exists, -2, -3 ... is appended. Concept and entity pages are
topic pages, not dated notes: if one with the same slug exists, the script prints its path
and exits 3 so the agent updates it instead of creating a twin. One line is appended to log.md.

Usage:
  python new_note.py --type inbox --title "Call the kiln supplier about lead times"
  python new_note.py --type idea --title "Glaze workshop for beginners" --body "Saturday classes..."
  echo "long text" | python new_note.py --type inbox --title "Voice memo 14:02" --stdin
  python new_note.py --type entity --title "Kiln Supply Co" --tags supplier,kilns --dry-run

Types and folders:
  inbox -> inbox/        idea -> ideas/          decision -> decisions/
  daily -> daily/        concept -> wiki/concepts/   entity -> wiki/entities/
  answer -> wiki/answers/

Prints the path of the new file. Env: VAULT_DIR when --vault is not given.
"""
import argparse
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

FOLDERS = {
    "inbox": "inbox", "idea": "ideas", "decision": "decisions", "daily": "daily",
    "concept": "wiki/concepts", "entity": "wiki/entities", "answer": "wiki/answers",
}
DATED = {"inbox", "idea", "decision", "answer"}   # concept/entity pages are named by topic only


def slugify(text, max_words=7):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words[:max_words]) or "note"


def free_path(folder, stem):
    p = folder / f"{stem}.md"
    n = 2
    while p.exists():
        p = folder / f"{stem}-{n}.md"
        n += 1
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"))
    ap.add_argument("--type", required=True, choices=sorted(FOLDERS))
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--stdin", action="store_true", help="read the body from stdin")
    ap.add_argument("--tags", default="", help="comma separated")
    ap.add_argument("--source", default="", help="source page or URL this note came from")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    if not (vault / "SCHEMA.md").exists():
        sys.exit(f"no SCHEMA.md in {vault}. Run vault-setup/scripts/init_vault.py first.")
    body = sys.stdin.read() if a.stdin else a.body
    today = date.today().isoformat()
    folder = vault / FOLDERS[a.type]
    if a.type == "daily":
        stem = today
    elif a.type in DATED:
        stem = f"{today}-{slugify(a.title)}"
    else:
        stem = slugify(a.title)
        if (folder / f"{stem}.md").exists():
            print(f"exists: {(folder / f'{stem}.md').relative_to(vault).as_posix()}  (update this page, do not create a twin)")
            sys.exit(3)
    path = free_path(folder, stem)

    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    fm = ["---", f"type: {a.type}", f"title: {a.title}", f"created: {today}"]
    if a.type == "idea":
        fm += ["status: new", "effort: S"]
    if a.source:
        fm.append(f"source: {a.source}")
    fm += ["reviewed: false", f"tags: [{', '.join(tags)}]", "---", ""]
    text = "\n".join(fm) + (f"# {a.title}\n\n" if a.type != "inbox" else "") + body.rstrip() + "\n"

    if a.dry_run:
        print(f"[dry-run] would write {path.relative_to(vault).as_posix()}\n")
        print(text)
        return
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    log = vault / "log.md"
    with log.open("a", encoding="utf-8") as f:
        f.write(f"\n## [{today}] capture | {a.title}\n{path.relative_to(vault).as_posix()}\n")
    print(path.relative_to(vault).as_posix())


if __name__ == "__main__":
    main()
