#!/usr/bin/env python3
"""List raw sources that have not been compiled into the wiki yet, oldest first.

A raw file counts as compiled when any page under wiki/ mentions its file name
(for example a source page with `raw: raw/2026-03-02-cold-email-teardown.md`).
Raw files are never modified to mark them, because raw/ is immutable.

Usage:
  python ingest_queue.py                 # table of pending sources
  python ingest_queue.py --json          # machine-readable
  python ingest_queue.py --stale-days 3  # exit 1 if anything waits longer than 3 days

Env: VAULT_DIR when --vault is not given.
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path


def frontmatter(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def age_days(fm, path):
    for key in ("fetched", "created", "date"):
        v = fm.get(key, "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return (date.today() - date.fromisoformat(v)).days
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        return (date.today() - date.fromisoformat(m.group(1))).days
    return (date.today() - datetime.fromtimestamp(path.stat().st_mtime).date()).days


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--stale-days", type=int, default=None, help="exit 1 if any pending file is older")
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    raw_dir, wiki_dir = vault / "raw", vault / "wiki"
    if not raw_dir.is_dir():
        sys.exit(f"no raw/ folder in {vault}")
    wiki_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in wiki_dir.rglob("*.md")) if wiki_dir.exists() else ""

    pending = []
    for f in sorted(raw_dir.rglob("*.md")):
        if f.name.startswith(".") or "processed" in f.parts:
            continue
        if f.name in wiki_text or f.stem in wiki_text:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        fm = frontmatter(text)
        pending.append({
            "path": f.relative_to(vault).as_posix(),
            "title": fm.get("title") or f.stem,
            "type": fm.get("source_type", "?"),
            "age_days": age_days(fm, f),
            "chars": len(text),
        })
    pending.sort(key=lambda r: -r["age_days"])

    if a.json:
        print(json.dumps(pending, indent=2))
    elif not pending:
        print("ingest queue empty: every raw source has a wiki page")
    else:
        print(f"{len(pending)} raw source(s) waiting to be compiled:")
        for r in pending:
            print(f"  {r['age_days']:>3}d  {r['type']:<10} {r['chars']:>7} ch  {r['path']}  ({r['title'][:60]})")
    if a.stale_days is not None and any(r["age_days"] > a.stale_days for r in pending):
        sys.exit(1)


if __name__ == "__main__":
    main()
