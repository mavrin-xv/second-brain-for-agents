#!/usr/bin/env python3
"""Create a new agent-maintained vault, or add whatever is missing to an existing one.

Copies the vault template (SCHEMA.md, index.md, log.md, folders, idea and decision
templates) into the target folder. Never overwrites a file that already exists, so it
is safe to re-run on a vault you already use.

Usage:
  python init_vault.py --vault ~/notes/vault          # create or top up
  python init_vault.py --vault ./vault --dry-run      # show what would be created

Env: VAULT_DIR is used when --vault is not given.
"""
import argparse
import os
import shutil
import sys
from datetime import date
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "vault-template"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"), help="target vault folder")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    a = ap.parse_args()

    if not TEMPLATE.is_dir():
        sys.exit(f"template not found at {TEMPLATE}")
    vault = Path(a.vault).expanduser().resolve()
    created, kept = [], 0
    for src in sorted(TEMPLATE.rglob("*")):
        rel = src.relative_to(TEMPLATE)
        dst = vault / rel
        if src.is_dir():
            if not dst.exists():
                created.append(rel.as_posix() + "/")
                if not a.dry_run:
                    dst.mkdir(parents=True, exist_ok=True)
            continue
        if src.name == ".gitkeep" and dst.parent.exists() and any(dst.parent.iterdir()):
            continue
        if dst.exists():
            kept += 1
            continue
        created.append(rel.as_posix())
        if not a.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    log = vault / "log.md"
    if created and not a.dry_run and log.exists():
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\n## [{date.today().isoformat()}] setup | vault initialised ({len(created)} items created)\n")

    verb = "would create" if a.dry_run else "created"
    print(f"vault: {a.vault}")
    print(f"{verb} {len(created)} item(s), kept {kept} existing file(s)")
    for c in created:
        print(f"  + {c}")


if __name__ == "__main__":
    main()
