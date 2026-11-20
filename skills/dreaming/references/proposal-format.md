# Proposal file format

One file per night: `proposals/dream-YYYY-MM-DD.md`. The script parses it back for `status` and `decide`, so keep the candidate block shape exact when adding candidates by hand.

```markdown
# Dreaming proposals 2026-03-02

Window: last 1 day(s). 6 page(s) changed. 3 new candidate(s), 2 already proposed before and skipped.

Approve or kill each one: `dream_digest.py decide <ID> approve|kill`. Nothing is applied until approved.

## Activity

- daily/2026-03-01.md
- wiki/concepts/kiln-drop-email.md

## Candidates

### [D-20260302-01] merge | Kiln drop email / Kiln drop emails
key: 3f9c2a7b10
evidence:
- wiki/concepts/kiln-drop-email.md
- wiki/concepts/kiln-drop-emails.md
proposal: Titles overlap. Read both; merge into the older page if they cover the same thing, otherwise add a line to each saying how they differ.
decision: pending
```

## Fields

| Line | Rule |
|---|---|
| `### [D-YYYYMMDD-NN] kind \| title` | ID is the scan date plus a two-digit counter. Kind is one word: merge, create, promote, decide, review, or your own (contradiction, revisit). |
| `key:` | 10 hex chars. The script computes it from kind + sorted evidence paths. For hand-added candidates, make one up that is unique; it is only used for "do not propose again". |
| `evidence:` | One path per line, relative to the vault. At least one. |
| `proposal:` | One or two sentences: what to do and why. Name the target file for merges. |
| `decision:` | `pending`, then `approved YYYY-MM-DD` or `killed YYYY-MM-DD \| note`. Written by `decide`. |

## Hand-added candidates

Number them after the script's last one. Example of a judgement candidate:

```markdown
### [D-20260302-04] contradiction | Weekly digests: fine or harmful?
key: hand_0302_04
evidence:
- wiki/concepts/kiln-drop-emails.md
- wiki/sources/drop-timing-thread.md
proposal: kiln-drop-emails.md says weekly digests are fine; the new source says sales fell with them. Add both to Open questions and ask which matches our list.
decision: pending
```

`key:` must match `\w+` for the parser, so use letters, digits and underscores only (`hand_0302_04`).
