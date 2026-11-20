#!/usr/bin/env python3
"""Save an external source into raw/ as clean markdown, refusing duplicates.

Fetches a URL (or reads a local HTML/text file, or stdin), strips scripts, styles, nav,
header, footer, forms and asides, keeps headings, paragraphs, list items, quotes and code,
and writes raw/YYYY-MM-DD-<slug>.md with frontmatter (source_url, fetched, status: raw).

Before writing it scans raw/ for the same source_url. If found, it prints the existing
path and exits with code 3, so the agent updates instead of saving a second copy.

Usage:
  python fetch_source.py "https://example.com/post"
  python fetch_source.py --file saved-page.html --url "https://example.com/post"
  pbpaste | python fetch_source.py --stdin --title "Thread on pricing" --url "https://x.com/..."

Optional: if the `defuddle` CLI is on PATH (npm i -g defuddle-cli), pass --defuddle for
better article extraction. Stdlib only otherwise. Env: VAULT_DIR.
"""
import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

SKIP = {"script", "style", "nav", "header", "footer", "form", "aside", "noscript", "svg", "iframe", "button"}
BLOCK = {"p": "", "li": "- ", "blockquote": "> ", "pre": "```\n", "h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### "}


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.cur = None
        self.buf = []
        self.out = []
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        elif tag == "title":
            self.in_title = True
        elif tag in BLOCK and not self.skip:
            self.flush()
            self.cur = tag
        elif tag == "br" and self.cur:
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        elif tag == "title":
            self.in_title = False
        elif tag == self.cur:
            self.flush()

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.skip and self.cur:
            self.buf.append(data)

    def flush(self):
        if self.cur:
            text = re.sub(r"[ \t\r\f\v]+", " ", "".join(self.buf)).strip()
            if self.cur == "pre":
                text = "".join(self.buf).strip("\n")
            if len(text) > 1:
                prefix = BLOCK[self.cur]
                if self.cur == "li" and self.out and self.out[-1].startswith("- "):
                    self.out[-1] += "\n- " + text   # keep list items together
                    self.cur, self.buf = None, []
                    return
                self.out.append(prefix + text + ("\n```" if self.cur == "pre" else ""))
        self.cur, self.buf = None, []


def slugify(text, max_words=7):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join(re.findall(r"[a-z0-9]+", text.lower())[:max_words]) or "source"


def html_to_md(raw):
    p = Extract()
    p.feed(raw)
    p.flush()
    return html.unescape(p.title).strip(), "\n\n".join(p.out)


def find_duplicate(raw_dir, url):
    if not url or not raw_dir.exists():
        return None
    want = url.strip().rstrip("/")
    for f in raw_dir.glob("*.md"):
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:1500]
        except OSError:
            continue
        m = re.search(r"^source_url:\s*(\S+)\s*$", head, re.M)
        if m and m.group(1).rstrip("/") == want:
            return f
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?", help="URL to fetch")
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"))
    ap.add_argument("--file", help="local HTML or text file instead of fetching")
    ap.add_argument("--stdin", action="store_true", help="read text from stdin")
    ap.add_argument("--url", dest="url_opt", help="source URL to record when using --file/--stdin")
    ap.add_argument("--title", default="")
    ap.add_argument("--type", default="article", help="article | thread | transcript | repo | video | doc")
    ap.add_argument("--defuddle", action="store_true", help="use the defuddle CLI if installed")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    raw_dir = vault / "raw"
    url = a.url or a.url_opt or ""
    dup = find_duplicate(raw_dir, url)
    if dup:
        print(f"duplicate: already saved as {dup.relative_to(vault).as_posix()}")
        sys.exit(3)

    title, body = a.title, ""
    if a.stdin or a.file:
        text = sys.stdin.read() if a.stdin else Path(a.file).read_text(encoding="utf-8", errors="ignore")
        if re.search(r"<(html|body|p|div|article|h[1-6]|li)\b", text[:5000], re.I):   # pasted or saved HTML
            t, body = html_to_md(text)
            title = title or t
        else:
            body = text.strip()
    elif a.url:
        if a.defuddle and shutil.which("defuddle"):
            r = subprocess.run(["defuddle", "parse", a.url, "--markdown"], capture_output=True, text=True, encoding="utf-8")
            body = r.stdout.strip()
        if not body:
            req = urllib.request.Request(a.url, headers={"User-Agent": "Mozilla/5.0 (compatible; vault-fetch/0.1)"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                t, body = html_to_md(resp.read().decode(charset, errors="ignore"))
                title = title or t
    else:
        ap.error("give a URL, --file or --stdin")

    if len(body) < 200:
        print("warning: extracted under 200 characters. The page may need JavaScript or a login; "
              "paste the text with --stdin instead.", file=sys.stderr)
    title = title or (body.splitlines()[0][:80] if body else "untitled")
    title = title.replace("\n", " ").strip()
    today = date.today().isoformat()
    path = raw_dir / f"{today}-{slugify(title)}.md"
    n = 2
    while path.exists():
        path = raw_dir / f"{today}-{slugify(title)}-{n}.md"
        n += 1
    fm = f"---\ntype: raw\ntitle: {title}\nsource_url: {url}\nsource_type: {a.type}\nfetched: {today}\nstatus: raw\n---\n\n"
    text = fm + body + "\n"
    if a.dry_run:
        print(f"[dry-run] would write {path.relative_to(vault).as_posix()} ({len(body)} chars)")
        print(text[:800])
        return
    raw_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    log = vault / "log.md"
    if log.exists():
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\n## [{today}] save | {title}\n{path.relative_to(vault).as_posix()} ({len(body)} chars)\n")
    print(path.relative_to(vault).as_posix())


if __name__ == "__main__":
    main()
