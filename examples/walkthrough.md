# Walkthrough on the sample vault

Every output below is copied from a real run on a copy of `examples/sample-vault/` (an invented two-person ceramics studio). Run it yourself on a copy so the original keeps its planted problems:

```bash
cp -r examples/sample-vault /tmp/sample-vault
export VAULT_DIR=/tmp/sample-vault
```

The vault has six planted problems: a twin page (`kiln-drop-email` next to `kiln-drop-emails`), a link to a missing page used three times, a raw source never compiled, an idea stuck at `status: new`, an old inbox note, and the same lesson written in two daily notes.

## 1. Health check

```text
$ python3 skills/vault-health/scripts/vault_health.py
vault health 62/100  (15 pages, 4 wiki, 3 errors, 7 warnings)

ERROR (3)
  broken-link      daily/2026-02-28.md: link to 'concepts/drop-scarcity' resolves to nothing
  broken-link      daily/2026-03-01.md: link to 'concepts/drop-scarcity' resolves to nothing
  broken-link      wiki/concepts/kiln-drop-emails.md: link to 'concepts/drop-scarcity' resolves to nothing

WARN (7)
  uncited          wiki/concepts/kiln-drop-email.md: no sources: and no [[sources/...]] citation
  orphan           wiki/concepts/kiln-drop-email.md: no page links here
  duplicate-title  wiki/concepts/kiln-drop-email.md: same title as wiki/concepts/kiln-drop-emails.md
  stuck-idea       ideas/2026-01-05-beginner-glaze-workshop.md: status new for 319 days, decide: test or kill
  stale-inbox      inbox/2026-02-01-call-supplier.md: 292 days in inbox
  stale-raw        raw/2026-02-20-pricing-handmade-goods-thread.md: 273 days without a wiki page
  stale-graph      GRAPH.md: missing, run knowledge-graph

INFO (3)
  thin             wiki/concepts/kiln-drop-emails.md: backed by one source
  unreviewed       wiki/: 2/4 pages reviewed: false (50%)
  quiet-log        log.md: last entry 282 days ago
```

The day counts depend on today's date.

## 2. What is waiting to be compiled

```text
$ python3 skills/wiki-ingest/scripts/ingest_queue.py
1 raw source(s) waiting to be compiled:
  273d  thread         418 ch  raw/2026-02-20-pricing-handmade-goods-thread.md  (Thread on pricing handmade goods by the hour)
```

The agent then runs `wiki-ingest` on it: plan first, one source page, updates to the concept pages it touches, a log line.

## 3. Search before answering

Without qmd installed, the built-in BM25 ranker answers:

```text
$ python3 skills/vault-search/scripts/search.py "drop email timing" -n 3
  4.26  wiki/concepts/kiln-drop-email.md
        title: Kiln drop email
  3.52  wiki/concepts/kiln-drop-emails.md
        Send one email per firing with three finished pieces and a fixed drop time ([[sources/pottery-newsletter-teardown]]). Name the glaze in the subject line. Relate
  3.01  raw/2026-02-10-email-teardown-of-a-pottery-newsletter.md
        The studio sends one email per kiln firing, not per week. Each email shows three finished pieces, the firing date and a fixed drop time. Pieces sell out within
```

The twin page ranks first because its title matches. That is the duplicate doing damage: the agent would read the thin page instead of the cited one.

## 4. Capture refuses twins

```text
$ python3 skills/capture/scripts/new_note.py --type concept --title "Kiln drop emails"
exists: wiki/concepts/kiln-drop-emails.md  (update this page, do not create a twin)
$ echo $?
3

$ python3 skills/capture/scripts/new_note.py --type inbox --title "ask Kiln Supply Co about cone 6 shelf prices"
inbox/2026-11-20-ask-kiln-supply-co-about-cone-6.md
```

Pasted HTML becomes markdown on the way into `raw/`:

```text
$ echo "<h1>Drop timing</h1><p>Shops that announce the drop two days ahead sell out faster.</p><ul><li>Announce Tuesday</li><li>Drop Thursday 7pm</li></ul>" \
    | python3 skills/capture/scripts/fetch_source.py --stdin --url https://example.com/drop-timing --title "Drop timing thread" --type thread --dry-run
...
# Drop timing

Shops that announce the drop two days ahead sell out faster.

- Announce Tuesday
- Drop Thursday 7pm
```

## 5. Graph

```text
$ python3 skills/knowledge-graph/scripts/build_graph.py --footers
graph: 16 pages, 6 links, 4 orphans (25%), 3 broken links
wrote 1 file(s)
  ~ GRAPH.md
```

End of the generated `GRAPH.md`:

```text
## Orphans (no inbound links)

- ideas/2026-01-05-beginner-glaze-workshop.md
- inbox/2026-02-01-call-supplier.md
- inbox/2026-11-20-ask-kiln-supply-co-about-cone-6.md
- wiki/concepts/kiln-drop-email.md

## Broken links

- daily/2026-02-28.md: [[concepts/drop-scarcity]]
- daily/2026-03-01.md: [[concepts/drop-scarcity]]
- wiki/concepts/kiln-drop-emails.md: [[concepts/drop-scarcity]]
```

No page has 3 inbound links yet, so no footers were written and no note was touched. Run it twice and the second run writes 0 files.

## 6. Dreaming: night scan, morning decisions

```text
$ python3 skills/dreaming/scripts/dream_digest.py scan --days 400
proposals/dream-2026-11-20.md: 5 candidate(s)

$ python3 skills/dreaming/scripts/dream_digest.py status --pending
D-20261120-01  pending  merge    Kiln drop email / Kiln drop emails
D-20261120-02  pending  create   concepts/drop-scarcity
D-20261120-03  pending  promote  announce the drop time two days ahead, not the same morning
D-20261120-04  pending  decide   Beginner glaze workshop on Saturdays
D-20261120-05  pending  review   2 wiki pages waiting for review

$ python3 skills/dreaming/scripts/dream_digest.py decide D-20261120-01 approve
D-20261120-01: approved

$ python3 skills/dreaming/scripts/dream_digest.py decide D-20261120-02 kill --note "covered in kiln-drop-emails"
D-20261120-02: killed
```

(`--days 400` because the sample notes are old; the nightly job uses `--days 1`.)

The killed candidate in the proposal file:

```text
### [D-20261120-02] create | concepts/drop-scarcity
key: ef1f9ef5cd
evidence:
- daily/2026-02-28.md
- daily/2026-03-01.md
- wiki/concepts/kiln-drop-emails.md
proposal: 3 pages link to [[concepts/drop-scarcity]] but it does not exist. Create it from what those pages say, cite them.
decision: killed 2026-11-20 | covered in kiln-drop-emails
```

Its key is remembered. Tomorrow's scan finds the same broken link and skips it. The broken link itself is still reported by `vault-health`: killing the "create" proposal means "do not make that page", so the fix is to edit the three links, which the agent proposes when you run the health skill.

`log.md` after the morning:

```text
## [2026-11-20] dream | 5 candidate(s)
proposals/dream-2026-11-20.md

## [2026-11-20] approve | D-20261120-01 merge: Kiln drop email / Kiln drop emails

## [2026-11-20] kill | D-20261120-02 create: concepts/drop-scarcity
```

The agent then applies D-20261120-01 only (dreaming SKILL.md, step 4): moves anything unique from `kiln-drop-email.md` into `kiln-drop-emails.md`, leaves `Merged into [[concepts/kiln-drop-emails]]` in the old file, updates the index, logs it.
