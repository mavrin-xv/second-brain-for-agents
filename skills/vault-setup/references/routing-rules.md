# Routing rules

The agent asks these questions in order for every new item and stops at the first yes. Same text as in `SCHEMA.md`.

## Decision order

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

## Edge cases

| Item | Goes to | Why |
|---|---|---|
| A voice memo transcript that is the human's own thinking | `inbox/` | It is a thought, not a source. Verbatim. |
| A transcript of someone else's talk | `raw/` | External source. Compile later. |
| "Remind me to call the supplier" | `inbox/` | Todo. Triage moves it to a task tool if the user has one. |
| A link with one sentence of the human's opinion | `raw/` for the link, the opinion as a `> note:` line at the top of the raw file's body | Opinion stays attached to the source. |
| A product idea with a price | `ideas/` | Build or sell. Fill the kill criterion. |
| "We will not do wholesale this year" | `decisions/` | A choice with a reason. |
| A competitor's pricing page | `raw/` then `wiki/entities/<competitor>.md` | Source first, entity page cites it. |
| An answer the agent gave that the human liked | `wiki/answers/` | Filed back so the next question starts from it. |
| A rule the agent keeps relearning | nowhere yet | Write it as `lesson:` in today's daily note. Dreaming proposes it as a rule once it repeats. |
