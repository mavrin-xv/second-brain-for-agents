# Health checks in detail

Severity tiers follow the error / warning / info split used by kfchou/wiki-skills: errors break the vault for the agent, warnings are drift, info is context.

## Errors

**broken-link.** A `[[target]]` or `[text](path.md)` that matches no file by path, relative path or file name. Links inside code spans, code blocks and generated footers are ignored. Links to files that exist outside the scanned set (for example inside a protected folder) are not reported, because the script cannot tell a typo from a private page.

**bad-frontmatter.** Only checked for `wiki/` pages: they need `type`, `title` and `reviewed`. Inbox and daily notes may have no frontmatter.

**missing-raw.** A source page whose `raw:` field points at a file that does not exist. Usually a renamed raw file. Raw files are never renamed by this pack, so this means a human or another tool moved it.

## Warnings

**uncited.** Concept, entity and answer pages with an empty `sources:` and no `[[sources/...]]` link in the body. Source pages are exempt (they cite raw via `raw:`).

**orphan.** A wiki page with no inbound links from any scanned page. `index.md` counts as an inbound link, so a page listed in the index is not an orphan.

**stale-raw.** A raw file whose file name appears in no wiki page, older than `stale_raw_days`. Default 3 days: a source not compiled within a few days is usually never compiled.

**stale-inbox.** An inbox note older than `stale_inbox_days` (default 7).

**stuck-idea.** An idea with `status: new` older than `stale_idea_days` (default 30). The fix is a decision, not more notes.

**stale-graph.** GRAPH.md missing, or 7+ days older than the newest wiki page.

**not-in-index.** A wiki page whose path or file name does not appear in `index.md`.

**duplicate-title.** Two wiki pages whose titles match after lowercasing, removing punctuation and a simple plural fold (`email` = `emails`). Different topics with the same title exist; the fix may be renaming one, not merging.

## Info

**thin.** A concept page with exactly one source. Fine for new pages; a signal for pages the vault leans on.

**unreviewed.** Count and share of wiki pages with `reviewed` not `true`. A share that keeps rising means the human is not keeping up with the agent; slow the ingest rate.

**quiet-log.** Days since the newest `## [YYYY-MM-DD]` entry in `log.md`.

## Known false positives

- Wikilinks to headings in the same page (`[[#Section]]`) are skipped, but links to headings in other pages resolve by page only.
- A raw file referenced only by its URL, not its file name, counts as not compiled. Use the `raw:` field on the source page.
- Titles in non-Latin scripts are compared word by word after lowercasing; the plural fold only applies to words ending in a Latin "s".
