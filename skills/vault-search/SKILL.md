---
name: vault-search
description: Searches the markdown vault before the agent answers or writes, using qmd (local BM25, vector and hybrid search) when installed and a built-in BM25 ranker with no dependencies when it is not. Skips protected folders, shows the best matching line per hit, and files good answers back into the wiki. Use when someone asks "what do we know about", "search my notes", "find in vault", "did I write about", "have we decided", or before creating any new page, so the agent updates instead of duplicating.
---

# Vault search

Search first, then answer or write. The cheapest way to keep a vault clean is never creating the second page about the same thing.

## Command

```bash
python3 skills/vault-search/scripts/search.py "drop email subject line"
python3 skills/vault-search/scripts/search.py "kiln supplier lead time" -n 3 --json
python3 skills/vault-search/scripts/search.py "wholesale" --folder decisions     # one folder, built-in ranker
python3 skills/vault-search/scripts/search.py "why did sales drop" --hybrid       # qmd vector + rerank
```

- With qmd on PATH the script calls `qmd search` (or `qmd query` with `--hybrid`). Without qmd, or with `--no-qmd` or `--folder`, it ranks with BM25, titles and file names weighted 3x.
- Protected folders from `SCHEMA.md` are never searched by the fallback. If you index the vault with qmd, exclude them there too (see `references/qmd-setup.md`).

## How to search well

1. Run 2 or 3 short queries with different words, not one long sentence. BM25 matches words, so "price increase" and "raise prices" find different pages.
2. Open the top 3 hits. Read `index.md` too if the vault is small (under about 200 pages): it is faster than searching.
3. For "have we decided" questions, search `--folder decisions` first.
4. Answer from the pages, citing them as `[[path]]`. If the pages disagree, say so and cite both.
5. If nothing is found, say "nothing in the vault" plainly. Do not fill the gap from memory without labelling it.

## File the answer back

If the answer combined 3 or more pages or needed a calculation, offer: "File this as `wiki/answers/<slug>.md`?" On yes, write it with the answer template in `skills/wiki-ingest/references/page-templates.md`, add it to `index.md`, log a `query` line.

## Before creating a page

Search for the title words and two synonyms. If a hit covers the same topic, update it. If two hits cover it, do not create a third: propose a merge in your reply.

## Output

Hits as `score  path` with the best line, then your answer with citations. Keep raw search output out of the final answer unless the human asked for it.
