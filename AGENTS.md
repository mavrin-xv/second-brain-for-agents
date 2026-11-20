# AGENTS.md

Notes for coding agents (Claude Code, Codex, Cursor, others) working on this repository.

## What this is

Seven Agent Skills for keeping a markdown vault. The product is the `SKILL.md` text plus small stdlib Python scripts. There is no server and no database: the vault is plain files.

## Layout

- `skills/<name>/SKILL.md`: what the agent does and when. Frontmatter has `name` (same as the folder) and `description` only. Keep each under 500 lines; long material goes in `references/`.
- `skills/<name>/scripts/*.py`: Python 3.8+, standard library only. Every script takes `--vault` (default `$VAULT_DIR`, then `./vault`) and `--help`.
- `skills/vault-setup/assets/vault-template/`: what `init_vault.py` copies. `SCHEMA.md` there is the config file the other scripts parse (`protected:`, `stale_*_days:`, `footer_threshold:`).
- `examples/sample-vault/`: an invented ceramics studio with planted problems (a duplicate page, a broken link used three times, an uncompiled raw file, a stuck idea, a repeated lesson). Tests and docs depend on those problems; do not fix them.
- `templates/nightly.sh`: the scheduled job.

## Rules

- Scripts never delete files and never edit the content of a note. The only page edit a script makes is the generated `## Referenced by` footer, and only with `--footers`.
- Write a file only when its bytes change, and keep the file's line endings.
- Skip folders listed under `protected:` in every script that reads the vault.
- No real names, companies, URLs other than example.com, ids or tokens in examples. Use the ceramics studio, Acme or Northwind.

## Checks before you finish

Run on a copy of the sample vault, never on the original:

```bash
cp -r examples/sample-vault /tmp/sv && export VAULT_DIR=/tmp/sv
for f in skills/*/scripts/*.py; do python3 "$f" --help >/dev/null || echo "FAIL $f"; done
python3 skills/vault-health/scripts/vault_health.py          # expect 62/100, 3 errors, 7 warnings
python3 skills/knowledge-graph/scripts/build_graph.py --dry-run   # expect 3 broken links
python3 skills/dreaming/scripts/dream_digest.py scan --days 400 --dry-run   # expect 5 candidates
python3 skills/capture/scripts/new_note.py --type concept --title "Kiln drop emails"; echo $?   # expect 3
bash -n install.sh templates/nightly.sh
```

If you change a check or a candidate rule, update the expected numbers here and the outputs in `examples/walkthrough.md`.
