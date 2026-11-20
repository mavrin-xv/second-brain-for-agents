# Graph rules and the mistakes behind them

Each rule here exists because the simpler version failed on a real vault of a few thousand notes.

## Whole-word mentions, never substrings

Counting a page as linked whenever its file name appears inside another file's text made short names (`log`, `plan`, `index`, `notes`) look like the most connected pages in the vault, with thousands of fake inbound links. The graph became useless for finding the spine. Now:

- Mentions are off by default (`--mentions` turns them on).
- A mention counts only as a whole token after splitting on spaces and punctuation.
- Only names with a hyphen, or at least 6 characters, count.
- A stopword list removes names like `readme`, `pricing`, `strategy`, `inbox`, `daily`.
- Date-only names (`2026-03-01`) never count.
- A name that exists twice in the vault (two `notes.md` in different folders) is ambiguous and never counts.

## Write only when bytes change

Rewriting every file on every run changes modification times. Health checks use mtimes to find stale pages and the nightly scan uses them to find "recent activity". A graph run that touched 3,000 files made everything look edited today. Now the script compares the new bytes with the old and writes only real changes. GRAPH.md is compared without its "Generated" date line.

## Keep line endings

Files edited on Windows have CRLF, files written by scripts have LF. Normalising them made every file show as changed in git. The script detects each file's ending and writes the footer with the same ending.

## Footers ignore footers

If backlinks inside a "Referenced by" footer counted as links, two pages that reference each other would keep each other above the threshold forever. Footer blocks are stripped before links are counted.

## Threshold of 3

A footer listing one backlink adds noise to every page. Three inbound links is where a page starts acting as a hub and the list helps a reader. Change it in `SCHEMA.md` (`footer_threshold`).

## Raw is read-only

`raw/` files are sources and must stay byte-identical to what was captured. They are counted as link sources (a raw file can link out) but never get footers.

## Exclusions from orphans

Daily notes, raw files and proposals are not expected to be linked. `index.md`, `log.md`, `SCHEMA.md`, `GRAPH.md`, templates and READMEs are infrastructure. Listing them as orphans hides the real ones.
