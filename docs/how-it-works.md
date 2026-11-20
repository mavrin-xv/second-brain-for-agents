# How it works

## Three layers

The design follows the LLM wiki pattern from Karpathy's note: keep the sources, let the model write the wiki, and write the rules down.

| Layer | Folder | Who writes | Rule |
|---|---|---|---|
| Sources | `raw/` | capture | Never edited after saving. Each file keeps `source_url` and `fetched`. |
| Wiki | `wiki/sources`, `wiki/concepts`, `wiki/entities`, `wiki/answers` | the agent | Every claim cites a source page. New pages start `reviewed: false`. |
| Rules | `SCHEMA.md` | you, with the agent's proposals | Routing table, frontmatter, protected folders, thresholds. |

Your own words live outside the wiki: `inbox/` for quick thoughts, `daily/` for logs, `ideas/` and `decisions/` for things with a status. The agent saves them verbatim and does not rewrite them.

`index.md` lists every wiki page in one line each, so the agent can read one file to see what exists. `log.md` is append-only, one `## [YYYY-MM-DD] op | title` entry per write, so any session can see what the last one did.

## The daily loop

1. **Capture.** You send a thought or a link. The agent checks `SCHEMA.md` routing, searches for an existing page, and either appends to it or writes a new file with frontmatter. Links go to `raw/` as markdown.
2. **Ingest.** When raw files wait, the agent compiles up to five per run: a source page each, then updates to the concept and entity pages they touch. It shows the plan before writing. Contradictions go under "Open questions" on the page instead of being resolved silently.
3. **Query.** Before answering a question about your work, the agent searches the vault and cites what it found. An answer worth keeping is filed under `wiki/answers/`.

## The nightly loop

`templates/nightly.sh`, run by cron or Task Scheduler:

1. qmd re-index, if qmd is installed.
2. Graph: `GRAPH.md` plus "Referenced by" footers on pages with 3 or more inbound links.
3. Health: 14 checks into `proposals/health-DATE.txt`.
4. Ingest queue: what is still uncompiled.
5. Dreaming scan: `proposals/dream-DATE.md` with numbered candidates.

The job exits non-zero if a step fails, so a broken night shows up instead of an empty proposal file.

## Why the human approves

An agent that edits its own memory without review makes small errors that compound: a wrong merge loses a distinction, a promoted "rule" was a one-off, a created page invents what three notes only hinted at. The night run therefore writes proposals only. Each candidate has evidence paths and a stable key. You approve or kill by ID. Approved items are applied by the agent with you present. Killed keys are never proposed again, so the same bad idea does not come back every night.

## What the scripts do and do not do

The scripts are deterministic and cheap: they find structure (links, titles, dates, frontmatter, repeated lines). They never delete a file and never change what a note says. The judgement work (is this really a duplicate, what does this source claim, which rule is worth keeping) is done by the agent following `SKILL.md`, and the result is marked `reviewed: false` until you check it.

## Search

With qmd installed, `search.py` calls `qmd search` (BM25) or, with `--hybrid`, `qmd query` (vectors plus reranking), all local; the skill can also call `qmd vsearch` directly. Without qmd, `search.py` ranks with BM25 over titles and bodies, title and file-name words weighted three times. The built-in ranker skips protected folders. qmd indexes whatever collection you gave it, so set the collection up without them (`skills/vault-search/references/qmd-setup.md`).
