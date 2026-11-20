---
name: vault-health
description: Runs 14 health checks on an agent-maintained markdown vault (broken links, missing frontmatter, uncited wiki pages, orphans, raw sources never compiled, stale inbox, ideas stuck at status new, stale graph, pages missing from the index, duplicate titles) and gives a score to track week over week. Reports and proposes fixes, never deletes. Use when someone says "check my vault", "vault health", "lint the wiki", "what is broken in my notes", "clean up my second brain", or as a weekly or nightly check.
---

# Vault health

Vaults rot quietly: sources saved and never read, ideas that never get a yes or no, links to pages that were renamed, two pages on the same topic. This skill finds that drift and turns it into a short fix list.

## Command

```bash
python3 skills/vault-health/scripts/vault_health.py                  # human report
python3 skills/vault-health/scripts/vault_health.py --json           # for dreaming or a dashboard
python3 skills/vault-health/scripts/vault_health.py --fail-on error  # exit 1 on any error (cron, CI)
```

Thresholds come from `SCHEMA.md` frontmatter: `stale_raw_days`, `stale_inbox_days`, `stale_idea_days`.

## Checks

| Severity | Check | Fix |
|---|---|---|
| error | broken-link | Fix the target, or create the page if 2+ pages want it |
| error | bad-frontmatter | Add `type`, `title`, `reviewed` |
| error | missing-raw | Source page points at a raw file that is gone. Find it or mark the page `confidence: low` |
| warn | uncited | Add `sources:` or inline `([[sources/...]])` |
| warn | orphan | Link it from the closest related page, or propose a merge |
| warn | stale-raw | Compile it (`wiki-ingest`) or tell the human it is not worth it |
| warn | stale-inbox | Triage: route each note per SCHEMA, or ask |
| warn | stuck-idea | Ask the human: test this week, or kill with a reason |
| warn | stale-graph | Run `knowledge-graph` |
| warn | not-in-index | Add a line to `index.md` |
| warn | duplicate-title | Propose a merge (do not merge yourself) |
| info | thin | Concept backed by one source; look for a second |
| info | unreviewed | Share of wiki pages the human has not checked |
| info | quiet-log | Days since the last log entry; a long gap means the routine stopped |

Details and false-positive notes: `references/checks.md`.

## Procedure

1. Run the script. Read the score and the counts.
2. Fix errors you caused in this session right away (broken links, frontmatter). These are mechanical.
3. For everything that needs a judgement (merge, kill an idea, drop a source), do not act. List it for the human, grouped, at most 10 items, highest severity first:
   ```
   Vault health 62/100 (last week 70)
   1. Merge? wiki/concepts/kiln-drop-email.md and kiln-drop-emails.md have the same title
   2. Decide: "Beginner glaze workshop" idea at status new for 46 days. Test or kill?
   3. Compile or drop: raw/2026-02-20-pricing-handmade-goods-thread.md, 12 days waiting
   ```
4. Log one line: `## [YYYY-MM-DD] lint | score 62, 3 errors, 7 warnings`.

## Score

`100 - 8 x errors - 2 x warnings`, floor 0. It is a trend line, not a grade. Compare it with last week's log line. A vault of a few hundred pages that is in active use usually carries some warnings; aim for zero errors and a score that does not fall.

## Hard rules

- Never delete, move or rename a note to fix a warning.
- Never set `reviewed: true`.
- Never compile, merge or kill on your own inside a health run. Health reports; the human decides; other skills act.

## Output

Score line, then the grouped fix list. Full issue list only when asked or with `--json`.
