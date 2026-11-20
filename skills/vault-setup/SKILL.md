---
name: vault-setup
description: Creates or tops up a markdown vault that an AI agent maintains itself, with SCHEMA.md routing rules, index.md, log.md and folders for inbox, raw sources, wiki pages, ideas, decisions, daily notes and proposals. Use when someone says "set up a second brain", "start a vault", "make my notes agent-readable", "Obsidian vault for Claude", "LLM wiki", or when another vault skill finds no SCHEMA.md.
---

# Vault setup

One command creates the vault skeleton. The agent then follows `SCHEMA.md` for every later write.

## When to run

- No vault yet, or the folder has notes but no `SCHEMA.md`.
- Another skill in this pack stopped with "no SCHEMA.md".
- After upgrading this pack: re-running adds new template files and never overwrites existing ones.

## Procedure

1. Ask where the vault lives if it is not obvious. Default: `./vault`. An existing Obsidian vault is fine: point at its root.
2. Dry run first and show the plan:
   ```bash
   python3 skills/vault-setup/scripts/init_vault.py --vault ./vault --dry-run
   ```
3. Run it for real (same command without `--dry-run`). It never overwrites a file.
4. Open `vault/SCHEMA.md` with the user and fill three things:
   - `protected:` folders the agent must never read or write (default `[private]`). Add journals, health, client folders.
   - Thresholds: `stale_raw_days`, `stale_inbox_days`, `stale_idea_days`, `footer_threshold`. Defaults are fine for a start.
   - One line under "Purpose" saying what this vault is for. The agent routes better with it.
5. Tell the agent harness about the vault. Add this line to the project's `CLAUDE.md` or `AGENTS.md`:
   ```
   Vault at ./vault. Before writing anything there, read vault/SCHEMA.md and follow it.
   ```
6. Optional: install qmd for better search (see `skills/vault-search/references/qmd-setup.md`).
7. Optional: schedule the nightly run (see `skills/dreaming/references/scheduling.md`).

## Existing notes

If the user already has hundreds of notes, do not move them. Run setup, leave their folders alone, and let `vault-health` and `knowledge-graph` report what is there. Routing applies to new writes. Offer a migration only when the user asks, and propose it as a list in `proposals/` first.

## What the template contains

Read `references/folder-layout.md` for the folder table and `references/routing-rules.md` for the decision order the agent uses to pick a folder. Both are copies of what lands in `SCHEMA.md`, kept here so the agent can read them without a vault.

## Hard rules

- Never overwrite an existing `SCHEMA.md`, `index.md` or `log.md`. Merge by hand if the user wants the new version.
- Never create folders inside a protected folder.
- Setup writes one `setup` line to `log.md`. Nothing else.

## Output

Report: vault path, items created, items kept, and the two or three SCHEMA fields the user still needs to fill.
