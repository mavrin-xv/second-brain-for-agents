---
name: knowledge-graph
description: Builds the vault's link graph from wikilinks, markdown links and optional whole-word mentions, writes GRAPH.md with clusters, most-linked pages, orphans and broken links, and maintains "Referenced by" backlink footers. Rewrites a file only when its bytes change and keeps each file's line endings. Use when someone says "build the graph", "what links to", "find orphan notes", "broken links", "map my vault", "backlinks", or after an ingest of several sources.
---

# Knowledge graph

A vault without links is a pile of files. The graph shows what is central, what is isolated and what points at nothing, so the agent and the human know where to look.

## Command

```bash
python3 skills/knowledge-graph/scripts/build_graph.py --dry-run          # stats only, writes nothing
python3 skills/knowledge-graph/scripts/build_graph.py                    # write GRAPH.md
python3 skills/knowledge-graph/scripts/build_graph.py --footers          # also "Referenced by" footers
python3 skills/knowledge-graph/scripts/build_graph.py --mentions --json  # count plain mentions too, JSON out
```

Always run `--dry-run` first on a vault you have not graphed before and show the human how many files would change.

## What counts as a link

1. `[[wikilink]]` that resolves by path, by relative path, or by a file name that is unique in the vault.
2. `[text](relative/path.md)`.
3. With `--mentions` only: the file name written as a whole word, for names with a hyphen (`kiln-drop-emails`) or at least 6 characters, excluding common words and dates.

Why whole words: substring matching counts `log` inside `catalog` and `plan` inside `planning`. On a vault of a few thousand notes that produced thousands of fake links in testing. See `references/graph-rules.md`.

## Reading GRAPH.md

- **Clusters**: pages grouped by folder (`wiki/concepts`, `wiki/entities`, ...), most linked first.
- **Most linked**: the 20 pages with the most inbound links. These are the vault's spine; keep them reviewed.
- **Orphans**: pages nothing links to. Daily notes, raw files and proposals are excluded on purpose. An orphan wiki page either needs a link from a related page or is a merge candidate.
- **Broken links**: `[[targets]]` that resolve to nothing. Fix the spelling, or, if 2+ pages link to it, it is a page that should exist (dreaming proposes it).

## Footers

With `--footers`, a page with at least `footer_threshold` inbound links (SCHEMA.md, default 3) gets:

```markdown
---
## Referenced by
_auto-generated, do not edit_
- [[wiki/concepts/kiln-drop-emails]]
```

The footer is rebuilt every run and removed when the page drops below the threshold. Links inside footers are ignored when counting, so footers never feed themselves. `raw/` files never get footers.

## When to run

- After ingesting 3 or more sources.
- Nightly, before dreaming (dreaming reads broken links).
- `vault-health` warns `stale-graph` when GRAPH.md is 7+ days older than the newest wiki page.

## Hard rules

- Never edit GRAPH.md by hand; it is regenerated.
- Never run on protected folders. The script skips them; do not pass them with `--vault`.
- Do not "fix" orphans by adding meaningless links. A link should be a sentence a reader would follow.

## Output

The stats line (`pages, links, orphans (share), broken links`), the files written, and the top 3 actions: which broken links to fix, which orphans to link or merge.
