# Source types

How to get clean text into `raw/` for each kind of source. The rule is the same for all: the raw file holds the source text, not your summary.

| Source | How to get the text | `--type` |
|---|---|---|
| Blog post, docs page, newsletter on the web | `fetch_source.py <url>`. If under 200 chars, use `--defuddle` or a browser tool and `--stdin`. | `article` |
| Page behind a login or built with JavaScript | Open it with a browser automation tool (for example Playwright), copy the main text, pipe with `--stdin --url <url>`. | `article` |
| X / Threads / Reddit / forum thread | A browser tool or the platform's export. Keep author handles and order of replies. | `thread` |
| YouTube or podcast | A transcript tool (for example yt-dlp subtitles, or Whisper on the audio). Keep timestamps every few minutes. | `transcript` |
| PDF | `pdftotext file.pdf -` or the harness PDF reader. Keep page numbers as `[p. 4]` markers. | `doc` |
| GitHub repo | README plus the file tree (`git ls-files` or the web tree). Note the license. | `repo` |
| Email or chat export the human forwards | `--stdin`. Remove other people's contact details before saving. | `doc` |

## Cleaning rules

- Keep headings, lists, code blocks and quotes. Drop navigation, cookie banners, share buttons, related-post lists.
- Keep numbers, dates and names exactly. They are what the wiki page will cite.
- Do not translate. If the source is in another language, the wiki page can be in the vault's language; the raw file stays original.
- Very long sources (over about 30,000 words): save in parts, `-part-1`, `-part-2`, each with the same `source_url` plus `#part-N`.

## defuddle

defuddle (https://github.com/kepano/defuddle, MIT) extracts the main content of a page and drops clutter. If installed (`npm install -g defuddle`), `--defuddle` uses `defuddle parse <url> --markdown` and falls back to the built-in extractor when it returns nothing.
