# Frontmatter per note type

Fields the scripts write, and the fields `vault-health` checks. Keep values on one line; the scripts parse simple `key: value` lines, not nested YAML.

| Type | Folder | Required | Optional |
|---|---|---|---|
| inbox | `inbox/` | type, title, created, reviewed | tags, source |
| raw | `raw/` | type, title, source_url, source_type, fetched, status | none |
| source | `wiki/sources/` | type, title, created, raw, reviewed | confidence, tags |
| concept | `wiki/concepts/` | type, title, created, sources, reviewed | updated, confidence, tags |
| entity | `wiki/entities/` | type, title, created, sources, reviewed | updated, tags, url |
| answer | `wiki/answers/` | type, title, created, sources, reviewed | question, tags |
| idea | `ideas/` | type, title, created, status, reviewed | effort, tags |
| decision | `decisions/` | type, title, created, reviewed | revisit, tags |

## Values

- `reviewed`: `false` when the agent writes or changes the page. Only the human sets `true`. If the agent edits a reviewed page, it sets it back to `false` and says so in the log line.
- `confidence`: `high` when two or more independent sources agree, `medium` for one good source, `low` for a single weak or opinion source.
- `status` (ideas): `new`, `testing`, `building`, `killed`, `done`. An idea left at `new` past `stale_idea_days` gets a decide prompt from dreaming.
- `status` (raw): `raw` until compiled. `wiki-ingest` does not change it (raw is immutable); compiled state is read from whether a source page cites the file.
- `sources`: list of wiki source page slugs, `[sources/pottery-newsletter-teardown]`.
- Dates are `YYYY-MM-DD`. The scripts read `created`, then `fetched`, then the date in the file name.
