# Folder layout

Copy of the ownership table in the vault template's `SCHEMA.md`. The three-layer idea (immutable sources, an agent-owned wiki, a schema file) follows Karpathy's LLM wiki pattern; `ideas/`, `decisions/`, `daily/` and `proposals/` are additions for operators who also run a business from the vault.

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

## Why these folders and not PARA or Zettelkasten

The folders are split by who writes and how the content changes, not by topic. That is what an agent needs to know before writing: can I edit this, must I keep it verbatim, must I never touch it. Topic lives in tags, links and the graph. You can still keep PARA folders for your own notes; mark them in `SCHEMA.md` and the agent will treat them as human-owned.
