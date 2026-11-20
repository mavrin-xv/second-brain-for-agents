#!/usr/bin/env python3
"""Vault health check: finds the drift that turns a second brain into a warehouse.

Checks (severity in brackets). Thresholds come from SCHEMA.md frontmatter.
  [error] broken-link        [[wikilink]] or relative .md link that resolves to nothing
  [error] bad-frontmatter    wiki page without frontmatter or without type/title/reviewed
  [error] missing-raw        source page whose `raw:` file does not exist
  [warn]  uncited            concept/entity/answer page with no `sources:` and no [[sources/...]] link
  [warn]  orphan             wiki page nothing links to
  [warn]  stale-raw          raw source not compiled after stale_raw_days (default 3)
  [warn]  stale-inbox        inbox note untriaged after stale_inbox_days (default 7)
  [warn]  stuck-idea         idea at status new after stale_idea_days (default 30)
  [warn]  stale-graph        GRAPH.md missing or 7+ days older than the newest wiki page
  [warn]  not-in-index       wiki page missing from index.md
  [warn]  duplicate-title    two pages with the same normalised title
  [info]  thin               concept page backed by a single source
  [info]  unreviewed         share of wiki pages still reviewed: false
  [info]  quiet-log          days since the last log.md entry

Score = 100 - 8 per error - 2 per warning (floor 0). It is a trend line, not a grade:
compare it week to week.

Usage:
  python vault_health.py                     # human report
  python vault_health.py --json              # for dashboards or the dreaming step
  python vault_health.py --fail-on error     # exit 1 when any error exists (cron / CI)

Env: VAULT_DIR when --vault is not given.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ALWAYS_SKIP = {".git", ".obsidian", ".trash", "node_modules", "archive"}
WIKI = re.compile(r"\[\[([^\[\]|#]+)(?:[#|][^\[\]]*)?\]\]")
MDLINK = re.compile(r"\]\(([^)\s]+?\.md)(?:#[^)]*)?\)")
FOOTER = re.compile(r"\n*---\n## Referenced by\n.*\Z", re.S)
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def fm_of(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.split("#")[0].strip()
    return out


def schema(vault):
    s = vault / "SCHEMA.md"
    text = s.read_text(encoding="utf-8", errors="ignore") if s.exists() else ""
    fm = fm_of(text) or {}
    prot = re.search(r"^protected:\s*\[(.*?)\]", text, re.M)
    return {
        "protected": {p.strip().strip("'\"") for p in prot.group(1).split(",") if p.strip()} if prot else {"private"},
        "raw": int(fm.get("stale_raw_days", 3)), "inbox": int(fm.get("stale_inbox_days", 7)),
        "idea": int(fm.get("stale_idea_days", 30)),
    }


def day_of(fm, path):
    for k in ("created", "fetched", "date"):
        v = (fm or {}).get(k, "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return date.fromisoformat(v)
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    return date.fromisoformat(m.group(1)) if m else datetime.fromtimestamp(path.stat().st_mtime).date()


def norm_title(t):
    """Lowercase words with a crude plural fold, so 'Kiln drop email' == 'Kiln drop emails'."""
    ws = re.findall(r"[^\W_]+", t.lower())
    return " ".join(w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w for w in ws)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["error", "warn"], default=None)
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    cfg = schema(vault)
    today = date.today()
    pages = {}
    for f in sorted(vault.rglob("*.md")):
        rel = f.relative_to(vault)
        if rel.parts[0] in cfg["protected"] or any(p in ALWAYS_SKIP for p in rel.parts):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        pages[rel.as_posix()] = {"path": f, "text": text, "fm": fm_of(text)}
    by_stem = defaultdict(list)
    for p in pages:
        by_stem[Path(p).stem.lower()].append(p)

    def resolve(t, src):
        t = t.strip().replace("\\", "/")
        t = t[:-3] if t.endswith(".md") else t
        for c in (t + ".md", os.path.normpath((Path(src).parent / (t + ".md")).as_posix()).replace("\\", "/")):
            if c in pages:
                return c
        if (vault / (t + ".md")).exists() or (vault / t).exists():
            return "(exists-outside-scan)"
        hits = by_stem.get(Path(t).name.lower(), [])
        return hits[0] if hits else None

    issues = []
    def add(sev, code, path, msg):
        issues.append({"severity": sev, "check": code, "path": path, "detail": msg})

    inbound = defaultdict(set)
    for src, pg in pages.items():
        if Path(src).name in ("TEMPLATE.md", "SCHEMA.md"):
            continue
        body = CODE.sub("", FOOTER.sub("", pg["text"]))
        for rx in (WIKI, MDLINK):
            for m in rx.finditer(body):
                tgt = m.group(1)
                if tgt.startswith("http"):
                    continue
                dst = resolve(tgt, src)
                if dst is None:
                    add("error", "broken-link", src, f"link to '{tgt}' resolves to nothing")
                elif dst != src:
                    inbound[dst].add(src)

    wiki = {p: pg for p, pg in pages.items() if p.startswith("wiki/")}
    index_text = pages.get("index.md", {}).get("text", "")
    titles = defaultdict(list)
    for p, pg in wiki.items():
        fm = pg["fm"]
        if fm is None or not all(k in fm for k in ("type", "title", "reviewed")):
            add("error", "bad-frontmatter", p, "needs frontmatter with type, title, reviewed")
            fm = fm or {}
        kind = fm.get("type", "")
        if kind == "source" and fm.get("raw") and not (vault / fm["raw"]).exists():
            add("error", "missing-raw", p, f"raw file {fm['raw']} not found")
        if kind in ("concept", "entity", "answer"):
            cited = fm.get("sources", "").strip("[] ") or "[[sources/" in pg["text"]
            if not cited:
                add("warn", "uncited", p, "no sources: and no [[sources/...]] citation")
            n_src = len({m for m in re.findall(r"\[\[(sources/[^\]|#]+)", pg["text"])} |
                        {s.strip() for s in fm.get("sources", "").strip("[]").split(",") if s.strip()})
            if kind == "concept" and n_src == 1:
                add("info", "thin", p, "backed by one source")
        if not inbound.get(p):
            add("warn", "orphan", p, "no page links here")
        stem = Path(p).stem
        if stem not in index_text and p not in index_text:
            add("warn", "not-in-index", p, "missing from index.md")
        titles[norm_title(fm.get("title") or stem)].append(p)
    for t, ps in titles.items():
        if len(ps) > 1:
            add("warn", "duplicate-title", ps[0], "same title as " + ", ".join(ps[1:]))

    wiki_blob = "\n".join(pg["text"] for pg in wiki.values())
    for p, pg in pages.items():
        age = (today - day_of(pg["fm"], pg["path"])).days
        if p.startswith("raw/") and pg["path"].stem not in wiki_blob and age > cfg["raw"]:
            add("warn", "stale-raw", p, f"{age} days without a wiki page")
        if p.startswith("inbox/") and age > cfg["inbox"]:
            add("warn", "stale-inbox", p, f"{age} days in inbox")
        if p.startswith("ideas/") and Path(p).name != "TEMPLATE.md" and (pg["fm"] or {}).get("status", "") == "new" and age > cfg["idea"]:
            add("warn", "stuck-idea", p, f"status new for {age} days, decide: test or kill")

    newest = max((pg["path"].stat().st_mtime for pg in wiki.values()), default=0)
    g = vault / "GRAPH.md"
    if wiki and not g.exists():
        add("warn", "stale-graph", "GRAPH.md", "missing, run knowledge-graph")
    elif wiki and newest - g.stat().st_mtime > 7 * 86400:
        add("warn", "stale-graph", "GRAPH.md", f"{int((newest - g.stat().st_mtime) / 86400)} days older than newest wiki page")

    unrev = sum(1 for pg in wiki.values() if (pg["fm"] or {}).get("reviewed", "false") != "true")
    if wiki:
        add("info", "unreviewed", "wiki/", f"{unrev}/{len(wiki)} pages reviewed: false ({unrev / len(wiki):.0%})")
    logs = re.findall(r"^## \[(\d{4}-\d{2}-\d{2})\]", pages.get("log.md", {}).get("text", ""), re.M)
    if logs:
        add("info", "quiet-log", "log.md", f"last entry {(today - date.fromisoformat(max(logs))).days} days ago")

    E = sum(i["severity"] == "error" for i in issues)
    W = sum(i["severity"] == "warn" for i in issues)
    score = max(0, 100 - 8 * E - 2 * W)
    result = {"vault": str(vault), "date": today.isoformat(), "pages": len(pages), "wiki_pages": len(wiki),
              "score": score, "errors": E, "warnings": W, "issues": issues}
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"vault health {score}/100  ({len(pages)} pages, {len(wiki)} wiki, {E} errors, {W} warnings)")
        for sev in ("error", "warn", "info"):
            group = [i for i in issues if i["severity"] == sev]
            if group:
                print(f"\n{sev.upper()} ({len(group)})")
                for i in group:
                    print(f"  {i['check']:<16} {i['path']}: {i['detail']}")
    if a.fail_on == "error" and E or a.fail_on == "warn" and (E or W):
        sys.exit(1)


if __name__ == "__main__":
    main()
