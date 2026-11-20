#!/usr/bin/env python3
"""Build the vault's link graph: GRAPH.md, backlink footers, orphans and broken links.

What counts as a link from page A to page B:
  1. a [[wikilink]] in A that resolves to B (by path, or by file name when unique)
  2. a markdown link [text](relative/path.md) in A that resolves to B
  3. with --mentions: a whole-token mention of B's file name in A's text, only for
     names that are hyphenated (cold-email-playbook) or at least 6 characters long and
     not a common word. Substring matching is deliberately not used: it produces
     hundreds of fake links for short names like log.md or plan.md.

Writes:
  GRAPH.md                generated map: clusters by folder, backlink index, orphans, broken links
  "## Referenced by"      footer on pages with >= footer_threshold inbound links (SCHEMA.md,
                          default 3), with --footers. Stale generated footers are removed.

Files are rewritten only when their bytes change, and each file keeps its own line endings,
so mtimes stay meaningful for health checks. Protected folders from SCHEMA.md are never
read or written.

Usage:
  python build_graph.py                       # write GRAPH.md
  python build_graph.py --footers --mentions  # also footers, also plain mentions
  python build_graph.py --dry-run             # print stats, write nothing
  python build_graph.py --json                # stats + orphans + broken links as JSON

Env: VAULT_DIR when --vault is not given.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ALWAYS_SKIP = {".git", ".obsidian", ".trash", "node_modules", "archive"}
GENERATED = {"GRAPH.md"}
NOT_ORPHANS = {"index.md", "log.md", "SCHEMA.md", "GRAPH.md", "TEMPLATE.md", "README.md"}
STOPWORDS = set("""index readme template notes note this that agent agents log logs todo tasks task board
skill skills rules plan strategy summary overview changelog license memory backlog header main test
draft copy post posts home about graph inbox ideas daily schema sources source concepts entities answers
pricing people things""".split())
WIKI = re.compile(r"\[\[([^\[\]|#]+)(?:[#|][^\[\]]*)?\]\]")
MDLINK = re.compile(r"\]\(([^)\s]+?\.md)(?:#[^)]*)?\)")
SPLIT = re.compile(r"[\s`'\"()\[\]{}<>|,;:!?*\\=+]+")
FOOTER = re.compile(r"\n*---\n## Referenced by\n(?:_[^\n]*\n)?(?:- [^\n]*\n?)*\s*$")


def schema(vault):
    s = vault / "SCHEMA.md"
    text = s.read_text(encoding="utf-8", errors="ignore") if s.exists() else ""
    prot = re.search(r"^protected:\s*\[(.*?)\]", text, re.M)
    thr = re.search(r"^footer_threshold:\s*(\d+)", text, re.M)
    protected = {p.strip().strip("'\"") for p in prot.group(1).split(",") if p.strip()} if prot else {"private"}
    return protected, int(thr.group(1)) if thr else 3


def title_of(text, path):
    if path.name in ("SCHEMA.md", "TEMPLATE.md"):   # their frontmatter is an example, not a title
        return path.stem if path.name == "SCHEMA.md" else f"{path.parent.name} template"
    m = re.search(r"^title:\s*(.+)$", text, re.M) or re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else path.stem


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"))
    ap.add_argument("--footers", action="store_true", help="maintain '## Referenced by' footers")
    ap.add_argument("--mentions", action="store_true", help="count whole-token file-name mentions as links")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    protected, threshold = schema(vault)
    pages = {}
    for f in sorted(vault.rglob("*.md")):
        rel = f.relative_to(vault)
        if rel.parts[0] in protected or any(p in ALWAYS_SKIP for p in rel.parts) or rel.name in GENERATED:
            continue
        raw = f.read_bytes()
        pages[rel.as_posix()] = {"file": f, "raw": raw, "text": raw.decode("utf-8", errors="ignore")}
    by_stem = defaultdict(list)
    for p in pages:
        by_stem[Path(p).stem.lower()].append(p)

    def resolve(target, src):
        t = target.strip().replace("\\", "/")
        if t.endswith(".md"):
            t = t[:-3]
        for cand in (t + ".md", (Path(src).parent / (t + ".md")).as_posix()):
            cand = os.path.normpath(cand).replace("\\", "/")
            if cand in pages:
                return cand
        hits = by_stem.get(Path(t).name.lower(), [])
        return hits[0] if len(hits) == 1 else None

    inbound, broken = defaultdict(set), []
    for src, pg in pages.items():
        body = FOOTER.sub("", pg["text"])
        body = re.sub(r"```.*?```|`[^`\n]*`", "", body, flags=re.S)   # links inside code are examples
        for m in WIKI.finditer(body):
            dst = resolve(m.group(1), src)
            if dst and dst != src:
                inbound[dst].add(src)
            elif not dst:
                broken.append((src, m.group(1)))
        for m in MDLINK.finditer(body):
            if m.group(1).startswith("http"):
                continue
            dst = resolve(m.group(1), src)
            if dst and dst != src:
                inbound[dst].add(src)
            elif not dst:
                broken.append((src, m.group(1)))
        if a.mentions:
            toks = {t.lower().rstrip(".") for t in SPLIT.split(body) if t}
            toks |= {t[:-3] for t in toks if t.endswith(".md")}
            for stem, paths in by_stem.items():
                if len(paths) != 1 or paths[0] == src or stem in STOPWORDS or re.fullmatch(r"\d{4}-\d{2}-\d{2}", stem):
                    continue
                if ("-" in stem or len(stem) >= 6) and stem in toks:
                    inbound[paths[0]].add(src)

    orphans = [p for p in pages if not inbound.get(p) and Path(p).name not in NOT_ORPHANS
               and not p.startswith(("daily/", "raw/", "proposals/"))]
    stats = {"pages": len(pages), "links": sum(len(v) for v in inbound.values()),
             "orphans": len(orphans), "broken": len(broken),
             "zero_backlink_share": round(len(orphans) / max(1, len(pages)), 3)}

    if a.json:
        print(json.dumps({"stats": stats, "orphans": orphans, "broken": broken}, indent=2))
        if a.dry_run:
            return

    clusters = defaultdict(list)
    for p in pages:
        parts = Path(p).parts
        clusters["/".join(parts[:2]) if parts[0] == "wiki" and len(parts) > 2 else (parts[0] if len(parts) > 1 else "(root)")].append(p)
    today = date.today().isoformat()
    out = [f"# Vault graph", f"_Generated {today} by build_graph.py. Do not edit by hand._", "",
           f"{stats['pages']} pages, {stats['links']} links, {stats['orphans']} orphans, {stats['broken']} broken links.", "",
           "## Clusters", ""]
    for c in sorted(clusters):
        out.append(f"### {c} ({len(clusters[c])})")
        for p in sorted(clusters[c], key=lambda x: -len(inbound.get(x, ()))):
            n = len(inbound.get(p, ()))
            out.append(f"- [{title_of(pages[p]['text'], Path(p))}]({p}) | {n} inbound")
        out.append("")
    out += ["## Most linked", ""]
    for p, srcs in sorted(inbound.items(), key=lambda kv: -len(kv[1]))[:20]:
        out.append(f"- {p} <- " + ", ".join(sorted(srcs)[:8]) + (" ..." if len(srcs) > 8 else ""))
    out += ["", "## Orphans (no inbound links)", ""] + ([f"- {p}" for p in sorted(orphans)] or ["- none"])
    out += ["", "## Broken links", ""] + ([f"- {s}: [[{t}]]" for s, t in broken] or ["- none"])
    graph_text = "\n".join(out) + "\n"

    writes = []
    gpath = vault / "GRAPH.md"
    old = gpath.read_text(encoding="utf-8") if gpath.exists() else ""
    if re.sub(r"_Generated .*?_", "", old) != re.sub(r"_Generated .*?_", "", graph_text):
        writes.append((gpath, graph_text.encode("utf-8")))

    if a.footers:
        for p, pg in pages.items():
            if Path(p).name in NOT_ORPHANS or p.startswith("raw/"):
                continue   # raw/ is immutable
            srcs = sorted(inbound.get(p, ()))
            if len(srcs) < threshold and not FOOTER.search(pg["text"]):
                continue   # no footer before, none needed now: leave the file alone
            eol = "\r\n" if b"\r\n" in pg["raw"] else "\n"
            text = pg["text"].replace("\r\n", "\n")
            base = FOOTER.sub("", text).rstrip("\n") + "\n"
            if len(srcs) >= threshold:
                base += "\n---\n## Referenced by\n_auto-generated, do not edit_\n" + "".join(
                    f"- [[{Path(s).with_suffix('').as_posix()}]]\n" for s in srcs)
            new = base.replace("\n", eol).encode("utf-8")
            if new != pg["raw"]:
                writes.append((pg["file"], new))

    if not a.json:
        print(f"graph: {stats['pages']} pages, {stats['links']} links, {stats['orphans']} orphans "
              f"({stats['zero_backlink_share']:.0%}), {stats['broken']} broken links")
        print(f"{'would write' if a.dry_run else 'wrote'} {len(writes)} file(s)")
        for f, _ in writes:
            print(f"  ~ {f.relative_to(vault).as_posix()}")
    if not a.dry_run:
        for f, data in writes:
            f.write_bytes(data)
        if writes and (vault / "log.md").exists():
            with (vault / "log.md").open("a", encoding="utf-8") as lf:
                lf.write(f"\n## [{today}] graph | {stats['links']} links, {stats['orphans']} orphans, {stats['broken']} broken\n")


if __name__ == "__main__":
    main()
