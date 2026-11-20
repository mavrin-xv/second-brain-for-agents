---
name: wiki-ingest
description: Compiles raw sources in the vault into wiki pages, the Karpathy LLM wiki way. Writes one source summary, then updates or creates the concept and entity pages it touches, with a citation on every claim, then updates index.md and log.md. Shows the plan before writing and flags contradictions instead of overwriting. Use when someone says "ingest", "compile this", "process my raw folder", "add this to the wiki", "what is waiting to be compiled", or right after capture saves a source.
---

# Wiki ingest

`raw/` holds what the world said. `wiki/` holds what the vault knows, written by the agent, each claim pointing back to a source. Ingest is the step between them. One source usually touches 3 to 10 wiki pages.

## Step 1: pick what to compile

```bash
python3 skills/wiki-ingest/scripts/ingest_queue.py            # oldest first
python3 skills/wiki-ingest/scripts/ingest_queue.py --json
python3 skills/wiki-ingest/scripts/ingest_queue.py --stale-days 3   # exit 1 if anything waits longer (cron)
```

A raw file counts as compiled when any wiki page mentions its file name (the source page's `raw:` field does this). If the human named a source, compile that one. Otherwise take the oldest. Do at most 5 sources in one run: quality drops after that and the human cannot review it.

## Step 2: read and plan (no writes yet)

1. Read the whole raw file.
2. Read `index.md`. Run `vault-search` for the 3 to 5 main topics of the source to find pages that already cover them.
3. Write a short plan and show it to the human before writing:
   ```
   Source: raw/2026-02-10-email-teardown-of-a-pottery-newsletter.md
   New:     wiki/sources/pottery-newsletter-teardown.md
   Update:  wiki/concepts/kiln-drop-emails.md   (+ subject line rule, + cadence evidence)
   Create:  wiki/concepts/drop-scarcity.md      (linked from 3 pages, no page yet)
   Conflict: kiln-drop-emails.md says "weekly is fine"; source says weekly digests lowered sales. Will note both.
   ```
4. If the human is not around (a scheduled run), write the plan into `proposals/ingest-YYYY-MM-DD.md` and stop. Unattended runs never edit wiki pages.

## Step 3: write

Use the page shapes in `references/page-templates.md`.

1. **Source page** `wiki/sources/<slug>.md`: what the source is, who made it, the 3 to 7 claims worth keeping with the numbers, and what it does not cover. Frontmatter `raw:` points at the raw file.
2. **Concept and entity pages**: add the new claims under the right heading, each ending with `([[sources/<slug>]])`. Add the source to `sources:`. Recompute `confidence` (high needs two independent sources). Set `updated:` and `reviewed: false`.
3. **Contradictions**: never delete the old claim. Add a `## Open questions` item: what each source says, with both citations. The human resolves it.
4. **New pages** only when the topic is central to the source and no page covers it. Otherwise add a line to the nearest existing page.
5. **Links**: use `[[folder/slug]]` wikilinks. Link new pages from at least one existing page so they are not orphans.

## Step 4: index and log

- `index.md`: one line per new page under its section, `- [[concepts/slug]]: one-line summary`. Update the summary of changed pages if it no longer fits.
- `log.md`: one entry per source:
  ```
  ## [2026-02-11] ingest | Pottery newsletter teardown
  wiki/sources/pottery-newsletter-teardown.md, wiki/concepts/kiln-drop-emails.md (updated)
  ```

## Step 5: check

Run `python3 skills/vault-health/scripts/vault_health.py` and fix any new `broken-link`, `uncited` or `not-in-index` issue you caused before reporting.

## Answers compound too

When the human asks a question and the answer took real work (several pages, a comparison, a calculation), offer to file it as `wiki/answers/<slug>.md` with citations. Next time the same question starts from that page.

## Hard rules

- Never modify, rename or delete a raw file.
- Never write a claim without a citation. If you are adding your own reasoning, label it `Inference:` and cite what it is inferred from.
- Never set `reviewed: true`.
- Never merge two existing pages during ingest. Propose it; dreaming and the human handle merges.

## Failure modes

- Source is thin or opinion-only: write the source page with `confidence: low`, skip concept updates, say so.
- Source repeats what the wiki already has: add it to `sources:` of the existing page (it raises confidence), no new prose.
- Raw file is truncated or junk: do not compile. Tell the human, suggest a re-capture with `--stdin`.

## Output

The plan (step 2), then a list of files written or changed, and the health result line.
