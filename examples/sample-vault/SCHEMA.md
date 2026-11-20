---
protected: [private]
stale_raw_days: 3
stale_inbox_days: 7
stale_idea_days: 30
footer_threshold: 3
---
# Vault schema

This file is the contract between you and the agent that maintains this vault. The agent reads it before every write. Edit it freely; the scripts read the frontmatter above.

## Purpose

Notes for a two-person ceramics studio: sales drops, suppliers, pricing, workshops.

## Who owns what

| Folder | Written by | Rule |
|---|---|---|
| `inbox/` | you or the agent | Raw thoughts, saved as typed. Never edited. Triaged within `stale_inbox_days`. |
| `raw/` | the agent (on your request) | Immutable sources: articles, transcripts, threads. Read, never modified, never deleted. |
| `wiki/sources/` | the agent | One summary page per raw source. |
| `wiki/concepts/` | the agent | One page per idea, framework or method. |
| `wiki/entities/` | the agent | One page per person, company, tool or product. |
| `wiki/answers/` | the agent | Good answers to your questions, filed back so they compound. |
| `ideas/` | you, structured by the agent | Things you might build or do. Carry a kill criterion. |
| `decisions/` | you, drafted by the agent | One file per decision: context, options, choice, date. |
| `daily/` | the agent | One file per calendar day. Append-only. |
| `proposals/` | the agent (dreaming) | Consolidation proposals. Nothing in here is applied until you approve it. |
| `private/` | you | Protected. Agents never read or write here. |
| `index.md` | the agent | Catalog of wiki pages, one line each. Updated on every ingest. |
| `log.md` | the agent | Append-only operation log. |
| `GRAPH.md` | the graph script | Generated. Do not edit by hand. |

## Routing: where a new thing goes

Ask these in order and stop at the first yes:

1. Is it a thought, todo or idea fragment typed by the human? -> `inbox/`, saved verbatim.
2. Is it an external source (URL, article, transcript, thread, PDF text)? -> `raw/`, then compile with wiki-ingest.
3. Is it something to build, sell or test? -> `ideas/` with the idea template.
4. Is it a choice that was made, with reasons? -> `decisions/`.
5. Is it about one named person, company, tool or product? -> `wiki/entities/`.
6. Is it a reusable concept or method? -> `wiki/concepts/`.
7. Is it an answer worth keeping? -> `wiki/answers/`.
8. Is it about today only? -> `daily/YYYY-MM-DD.md`.
9. None of the above -> `inbox/` and ask.

## Hard rules for the agent

- Never modify or delete anything in `raw/`.
- Never read or write `private/` or any folder listed under `protected`.
- Never delete a note. Propose deletions in `proposals/`; the human decides.
- Every page you write starts with `reviewed: false`. Only the human sets `reviewed: true`.
- Every claim on a wiki page cites its source page: `([[sources/slug]])`.
- Every write appends one line to `log.md`: `## [YYYY-MM-DD] <op> | <title>`.
- Search before you create. If a page on the topic exists, update it instead of making a second one.

## Frontmatter

```yaml
---
type: source | concept | entity | answer | idea | decision | inbox | daily
title: Short human title
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [sources/slug]        # wiki pages only
reviewed: false
confidence: high | medium | low  # wiki pages only
tags: []
---
```
