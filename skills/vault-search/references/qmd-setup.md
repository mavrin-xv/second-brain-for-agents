# qmd setup

qmd (https://github.com/tobi/qmd, MIT) is a local search engine for markdown: BM25, vector search and a hybrid mode with reranking, all on your machine. The built-in fallback in `search.py` is fine up to a few hundred pages. Past that, or when you want "find the note about X even if I used other words", install qmd.

## Install and index

```bash
npm install -g @tobilu/qmd
qmd collection add ./vault --name vault
qmd embed            # builds vectors, first run downloads small local models
```

After adding or changing notes:

```bash
qmd update           # re-index changed files
qmd embed            # embed new chunks
```

Put `qmd update && qmd embed` in the nightly job (see `skills/dreaming/references/scheduling.md`).

## Commands the agent uses

| Need | Command |
|---|---|
| Keyword search, fast | `qmd search "kiln shelves" -n 8` |
| Meaning search | `qmd vsearch "why customers stopped opening emails"` |
| Best quality, slower | `qmd query "should we do wholesale"` |
| Open one document | `qmd get <path or id>` |

## Keep protected folders out

The index should not contain `private/` or any protected folder. Either keep protected folders outside the vault root, or add the vault with a mask that leaves them out, for example one collection per allowed folder:

```bash
qmd collection add ./vault/wiki --name wiki
qmd collection add ./vault/decisions --name decisions
```

## MCP

qmd also runs as an MCP server (`qmd mcp`), so agents that speak MCP can search without shelling out. Check the qmd README for the current setup for your harness.
