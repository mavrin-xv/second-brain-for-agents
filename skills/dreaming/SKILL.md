---
name: dreaming
description: Nightly consolidation for an agent-maintained vault. Scans recent activity and writes a proposal file of numbered candidates (merge near-duplicate pages, create pages that many notes link to, promote lessons written twice into rules, decide on stuck ideas, review old unchecked pages). The human approves or kills each one. Only approved items are applied, and killed ones are never proposed again. Use when someone says "dream", "consolidate my notes", "nightly review", "what should I merge", "tidy the vault overnight", "morning proposals", or when setting up a scheduled vault job.
---

# Dreaming

Sleep consolidates memory: the day's fragments get merged, linked and promoted into something you can use. This skill does that for a vault, with one difference that matters: **the agent proposes, the human decides**. An agent that rewrites its own memory unsupervised drifts, and nobody notices until the notes are wrong.

## The loop

```
night:    health + graph -> dream_digest.py scan -> proposals/dream-YYYY-MM-DD.md
morning:  human reads 3 to 10 candidates -> approve / kill each
day:      agent applies approved items only -> log -> next night skips everything already proposed
```

## Step 1: scan (scheduled, unattended)

```bash
python3 skills/knowledge-graph/scripts/build_graph.py
python3 skills/vault-health/scripts/vault_health.py --fail-on error || true   # its report goes in the morning summary
python3 skills/dreaming/scripts/dream_digest.py scan --days 1
```

The script finds five kinds of candidates by rule:

| Kind | Signal |
|---|---|
| merge | two wiki, idea or decision pages whose titles share 60%+ of their words, at least one touched in the window |
| create | a `[[link]]` to a missing page used by 2+ pages |
| promote | a `lesson:` / `rule:` / `mistake:` / `learned:` line written 2+ times in the window |
| decide | an idea at `status: new` past `stale_idea_days` |
| review | wiki pages still `reviewed: false` after 30 days (batched, 10 at most) |

Every candidate gets an ID (`D-YYYYMMDD-NN`), a `key` (hash of kind + evidence files), evidence paths, a proposal and `decision: pending`. A key that appears in any earlier proposal file is skipped, so a killed idea is not proposed again tomorrow.

Exact file format: `references/proposal-format.md`. Scheduling recipes for cron, launchd, Windows Task Scheduler and agent harness schedulers: `references/scheduling.md`.

## Step 2: add judgement (agent, optional, still unattended)

The script only sees structure. If the run has a model available, read the day's new pages and add up to 5 more candidates by hand in the same format, numbered after the script's. Good ones:

- Two pages that say the same thing in different words (titles differ, content overlaps).
- A claim on one page contradicted by a newer source.
- A decision whose "Revisit when" condition is now true.
- A pattern across 3+ daily notes the human has not named.

Before adding a `promote` candidate, search `decisions/`, `SCHEMA.md` and any rules files for the same rule. Do not propose a rule that already exists.

Never edit a wiki page in this step. The only file the night run writes is the proposal file (plus its log line, and GRAPH.md from the graph step).

## Step 3: morning review (human)

Show pending candidates, shortest first:

```bash
python3 skills/dreaming/scripts/dream_digest.py status --pending
```

Present each as one line plus the evidence paths. The human answers per ID. Record it:

```bash
python3 skills/dreaming/scripts/dream_digest.py decide D-20260302-01 approve
python3 skills/dreaming/scripts/dream_digest.py decide D-20260302-02 kill --note "two different kilns"
```

Silence is not approval. Anything not answered stays `pending` and shows again next morning. If the same candidate sits pending for 3 mornings, ask once whether to kill it.

## Step 4: apply approved items (agent)

Only items with `decision: approved`. For each:

- **merge**: move the unique content of the newer page into the older one with its citations, replace the newer page's body with `Merged into [[older]]` (keep the file so links do not break), update `index.md`.
- **create**: write the page from what the linking pages say, cite them, `reviewed: false`, add to index.
- **promote**: add the rule, worded once, where the human said (SCHEMA.md hard rules, a skill, a rules file). Quote the evidence lines in the log.
- **decide**: ask the human the test-or-kill question; set the idea's `status` to their answer.
- **review**: list the pages for the human to read; they set `reviewed: true` themselves.

Log each one: `## [YYYY-MM-DD] apply | D-20260302-01 merge: kiln drop email into kiln drop emails`.

## Hard rules

- The night run never edits, moves or deletes a note.
- Never apply a candidate that is `pending` or `killed`.
- Never re-propose a killed key. If circumstances changed, the human can bring it back by hand.
- Never delete files when merging. Leave a pointer.
- At most 10 candidates per night (`--max`). The script keeps merge and create first and states how many it held back.

## Output

Night: the proposal file path and candidate count. Morning: the pending list. Apply: one line per applied item.
