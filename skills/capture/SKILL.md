---
name: capture
description: Saves thoughts, todos, ideas, decisions and links into the right vault folder with frontmatter, verbatim and without duplicates, then logs the write. Fetches a URL or pasted page into raw/ as clean markdown and refuses a URL that is already saved. Use when someone says "save this", "capture", "remember this", "note this down", "add to inbox", "save this link", "clip this article", "log this decision", or pastes a link or voice memo with no other instruction.
---

# Capture

Two jobs: put the human's own words somewhere safe, and put external sources into `raw/` so `wiki-ingest` can compile them. Capture never summarises or rewrites. Compiling is a separate step.

## Before you write

1. Read `SCHEMA.md` in the vault. If missing, stop and run `vault-setup`.
2. Route the item with the decision order in `SCHEMA.md` (copy in `skills/vault-setup/references/routing-rules.md`).
3. For concepts and entities: search first (`vault-search`). If a page exists, update it instead.

## Human words: new_note.py

```bash
python3 skills/capture/scripts/new_note.py --type inbox --title "call supplier about cone 6 shelves"
python3 skills/capture/scripts/new_note.py --type idea --title "Beginner glaze workshop" --body "3 hours, 6 people"
echo "<transcript text>" | python3 skills/capture/scripts/new_note.py --type inbox --title "voice memo 14:02" --stdin
python3 skills/capture/scripts/new_note.py --type decision --title "No wholesale in 2026" --body "..."
```

- Types: `inbox`, `idea`, `decision`, `daily`, `concept`, `entity`, `answer`.
- The body is written exactly as given. Do not fix typos, do not translate, do not tidy. The human's phrasing is data.
- Dated types get `YYYY-MM-DD-slug.md`. Concept and entity pages get a topic slug; if that page exists the script prints its path and exits 3, so you update it.
- Every new note starts `reviewed: false`. Field rules per type: `references/frontmatter.md`.
- Ideas get `status: new`. Fill the idea template sections (What, Why now, Next step, Kill if) from what the human said. If the human gave no kill criterion, ask for one in a single question; do not invent it.

## External sources: fetch_source.py

```bash
python3 skills/capture/scripts/fetch_source.py https://example.com/post
python3 skills/capture/scripts/fetch_source.py --file page.html --url https://example.com/post
pbpaste | python3 skills/capture/scripts/fetch_source.py --stdin --url https://example.com/thread --type thread
python3 skills/capture/scripts/fetch_source.py https://example.com/post --defuddle   # if defuddle is installed
```

- Writes `raw/YYYY-MM-DD-slug.md` with `source_url`, `source_type`, `fetched`, `status: raw`.
- Exit code 3 with "duplicate: already saved as ..." means the URL is in `raw/` already. Tell the human where, do not save again.
- A warning "extracted under 200 characters" means the page needs JavaScript or a login. Ask the human to paste the text and re-run with `--stdin`. Do not save an empty shell.
- Social posts, videos and PDFs: get the text with whatever tool the harness has (a browser tool, a transcript tool, a PDF reader), then pipe it in with `--stdin --type thread|transcript|doc`. See `references/source-types.md`.
- If the human added an opinion with the link, put it as the first body line: `> note: <their words>`.

## After capture

- Raw source saved: offer to compile it now (`wiki-ingest`). If they say later, it shows up in the ingest queue and in health after `stale_raw_days`.
- Inbox note saved: nothing else. Triage happens in the nightly run or when the human asks.
- Decision saved: link it from any idea or concept page it affects.

## Hard rules

- Never write into `raw/` by hand. Use the script so the duplicate check runs.
- Never edit an existing `raw/` or `inbox/` file.
- Never capture into a protected folder.
- One capture, one log line. The scripts do this; if you write a file yourself, append the line.

## Output

One line per item: the path written, or the existing path when it was a duplicate. No summary of the content unless asked.
