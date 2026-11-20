#!/usr/bin/env python3
"""Nightly consolidation ("dreaming"): find what the vault should merge, create, promote or decide,
and write it as a proposal the human approves or kills. Nothing in the vault is changed except
the proposal file itself.

Subcommands:
  scan     look at the last --days of activity and write proposals/dream-YYYY-MM-DD.md
  status   list every candidate across proposal files with its decision
  decide   record the human's verdict:  decide D-20260302-03 approve|kill [--note "why"]

Deterministic signals the scan looks for (the agent then adds judgement, see SKILL.md):
  merge       two pages whose titles share >= 60% of their words
  create      a [[link]] to a page that does not exist, used by 2+ pages
  promote     a lesson line ("lesson:", "rule:", "mistake:", "learned:") that appears 2+ times
  decide      an idea still at status new after stale_idea_days
  review      wiki pages still reviewed: false after 30 days (batched, max 10)

Killed candidates are remembered by a key and never proposed again, so the human does not
reject the same suggestion every night.

Usage:
  python dream_digest.py scan --days 7
  python dream_digest.py scan --days 1 --dry-run --max 5
  python dream_digest.py status --pending
  python dream_digest.py decide D-20260302-02 kill --note "two different kilns, keep both"

Env: VAULT_DIR when --vault is not given.
"""
import argparse
import hashlib
import os
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ALWAYS_SKIP = {".git", ".obsidian", ".trash", "node_modules", "archive", "proposals"}
WIKI = re.compile(r"\[\[([^\[\]|#]+)(?:[#|][^\[\]]*)?\]\]")
LESSON = re.compile(r"^\s*[-*]?\s*(lesson|rule|mistake|learned|note to self)\s*[:\-]\s*(.+)$", re.I | re.M)
CAND = re.compile(r"^### \[(D-\d{8}-\d{2})\] (\w+) \| (.+)$", re.M)
STOP = set("a an the and or of to in on for with is are was be it this that as at by from not how why what".split())
PAST = {"approve": "approved", "kill": "killed"}


def load(vault):
    s = vault / "SCHEMA.md"
    text = s.read_text(encoding="utf-8", errors="ignore") if s.exists() else ""
    prot = re.search(r"^protected:\s*\[(.*?)\]", text, re.M)
    idea = re.search(r"^stale_idea_days:\s*(\d+)", text, re.M)
    protected = {p.strip() for p in prot.group(1).split(",")} if prot else {"private"}
    pages = {}
    for f in vault.rglob("*.md"):
        rel = f.relative_to(vault)
        if rel.parts[0] in protected or any(p in ALWAYS_SKIP for p in rel.parts):
            continue
        pages[rel.as_posix()] = {"path": f, "text": f.read_text(encoding="utf-8", errors="ignore")}
    return pages, int(idea.group(1)) if idea else 30


def words(t):
    """Content words, with a crude plural fold so 'email' and 'emails' match."""
    out = set()
    for w in re.findall(r"[^\W_]+", t.lower()):
        if w in STOP or len(w) <= 2:
            continue
        out.add(w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w)
    return out


META = {"log.md", "GRAPH.md", "index.md", "SCHEMA.md", "TEMPLATE.md"}   # vault plumbing, not notes


def title(pg, p):
    m = re.search(r"^title:\s*(.+)$", pg["text"], re.M) or re.search(r"^#\s+(.+)$", pg["text"], re.M)
    return m.group(1).strip() if m else Path(p).stem.replace("-", " ")


def created(pg):
    m = re.search(r"^(?:created|fetched|date):\s*(\d{4}-\d{2}-\d{2})", pg["text"], re.M)
    return date.fromisoformat(m.group(1)) if m else datetime.fromtimestamp(pg["path"].stat().st_mtime).date()


def key(kind, targets):
    return hashlib.sha1((kind + "|" + "|".join(sorted(targets))).encode()).hexdigest()[:10]


def proposals(vault):
    out = []
    for f in sorted((vault / "proposals").glob("dream-*.md")):
        text = f.read_text(encoding="utf-8")
        for block in re.split(r"(?=^### \[D-)", text, flags=re.M):
            m = CAND.match(block)
            if not m:
                continue
            k = re.search(r"^key: (\w+)", block, re.M)
            d = re.search(r"^decision: (\w+)", block, re.M)
            out.append({"id": m.group(1), "kind": m.group(2), "title": m.group(3), "file": f,
                        "key": k.group(1) if k else "", "decision": d.group(1) if d else "pending"})
    return out


def scan(vault, days, dry, limit=10):
    pages, idea_days = load(vault)
    today = date.today()
    seen = {c["key"] for c in proposals(vault)}          # never re-propose anything already proposed
    cands = []

    recent = [p for p, pg in pages.items() if (today - created(pg)).days <= days
              or time.time() - pg["path"].stat().st_mtime <= days * 86400]
    recent = [p for p in recent if Path(p).name not in META]

    wiki = [p for p in pages if p.startswith(("wiki/", "ideas/", "decisions/")) and Path(p).name != "TEMPLATE.md"]
    for i, p in enumerate(wiki):
        for q in wiki[i + 1:]:
            if p not in recent and q not in recent:
                continue
            a, b = words(title(pages[p], p)), words(title(pages[q], q))
            if len(a) >= 2 and len(b) >= 2 and len(a & b) / len(a | b) >= 0.6:
                cands.append(("merge", f"{title(pages[p], p)} / {title(pages[q], q)}", [p, q],
                              "Titles overlap. Read both; merge into the older page if they cover the same thing, "
                              "otherwise add a line to each saying how they differ."))

    missing = defaultdict(set)
    stems = {Path(p).stem.lower() for p in pages} | {p[:-3].lower() for p in pages}
    for p, pg in pages.items():
        if Path(p).name in META:
            continue
        body = re.sub(r"```.*?```|`[^`\n]*`", "", pg["text"], flags=re.S)   # links in code are examples
        for m in WIKI.finditer(body):
            t = m.group(1).strip().lower()
            if t not in stems and Path(t).name not in stems:
                missing[m.group(1).strip()].add(p)
    for t, srcs in missing.items():
        if len(srcs) >= 2:
            cands.append(("create", t, sorted(srcs), f"{len(srcs)} pages link to [[{t}]] but it does not exist. "
                          "Create it from what those pages say, cite them."))

    lessons = defaultdict(list)
    for p in recent:
        for m in LESSON.finditer(pages[p]["text"]):
            lessons[" ".join(sorted(words(m.group(2))))[:80]].append((p, m.group(2).strip()))
    for k, hits in lessons.items():
        if len(hits) >= 2 and k:
            cands.append(("promote", hits[0][1][:70], sorted({h[0] for h in hits}),
                          f"Lesson written {len(hits)} times. Propose it as a standing rule in SCHEMA.md "
                          "or the right skill, worded once."))

    for p, pg in pages.items():
        if p.startswith("ideas/") and Path(p).name != "TEMPLATE.md" and re.search(r"^status:\s*new", pg["text"], re.M):
            age = (today - created(pg)).days
            if age > idea_days:
                cands.append(("decide", title(pg, p), [p], f"Idea at status new for {age} days. "
                              "Ask: test it this week (name the step) or kill it (name the reason)."))

    stale = sorted(p for p, pg in pages.items() if p.startswith("wiki/")
                   and re.search(r"^reviewed:\s*false", pg["text"], re.M) and (today - created(pg)).days > 30)
    if stale:
        cands.append(("review", f"{len(stale[:10])} wiki pages waiting for review", stale[:10],
                      "Pages the agent wrote 30+ days ago that nobody checked. Skim, fix, set reviewed: true."))

    order = {"merge": 0, "create": 1, "promote": 2, "decide": 3, "review": 4}
    fresh = sorted((c for c in cands if key(c[0], c[2]) not in seen), key=lambda c: order[c[0]])
    overflow = max(0, len(fresh) - limit)
    fresh = fresh[:limit]
    stamp = today.strftime("%Y%m%d")
    lines = [f"# Dreaming proposals {today.isoformat()}", "",
             f"Window: last {days} day(s). {len(recent)} page(s) changed. {len(fresh)} new candidate(s), "
             f"{len(cands) - len(fresh) - overflow} already proposed before and skipped."
             + (f" {overflow} more held back by --max {limit}." if overflow else ""), "",
             "Approve or kill each one: `dream_digest.py decide <ID> approve|kill`. Nothing is applied until approved.", ""]
    if recent:
        lines += ["## Activity", ""] + [f"- {p}" for p in sorted(recent)[:40]] + [""]
    lines += ["## Candidates", ""]
    for n, (kind, t, targets, why) in enumerate(fresh, 1):
        lines += [f"### [D-{stamp}-{n:02d}] {kind} | {t}", f"key: {key(kind, targets)}", "evidence:"]
        lines += [f"- {x}" for x in targets]
        lines += [f"proposal: {why}", "decision: pending", ""]
    if not fresh:
        lines.append("Nothing new to propose. A quiet night is a fine result.")
    text = "\n".join(lines) + "\n"

    out = vault / "proposals" / f"dream-{today.isoformat()}.md"
    if dry:
        print(text)
        return
    if out.exists():
        sys.exit(f"{out.relative_to(vault).as_posix()} already exists. Review it first, or delete it to re-scan.")
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if (vault / "log.md").exists():
        with (vault / "log.md").open("a", encoding="utf-8") as f:
            f.write(f"\n## [{today.isoformat()}] dream | {len(fresh)} candidate(s)\n{out.relative_to(vault).as_posix()}\n")
    print(f"{out.relative_to(vault).as_posix()}: {len(fresh)} candidate(s)")


def status(vault, pending_only):
    rows = proposals(vault)
    if pending_only:
        rows = [r for r in rows if r["decision"] == "pending"]
    if not rows:
        print("no candidates" + (" pending" if pending_only else ""))
    for r in rows:
        print(f"{r['id']}  {r['decision']:<8} {r['kind']:<8} {r['title'][:70]}")


def decide(vault, cid, verdict, note):
    for r in proposals(vault):
        if r["id"] == cid:
            text = r["file"].read_text(encoding="utf-8")
            start = text.index(f"### [{cid}]")
            end = text.find("\n### [", start + 1)
            end = len(text) if end == -1 else end
            block = text[start:end]
            stamp = date.today().isoformat()
            new = re.sub(r"^decision: \w+.*$", f"decision: {PAST[verdict]} {stamp}" + (f" | {note}" if note else ""),
                         block, count=1, flags=re.M)
            r["file"].write_text(text[:start] + new + text[end:], encoding="utf-8")
            if (vault / "log.md").exists():
                with (vault / "log.md").open("a", encoding="utf-8") as f:
                    f.write(f"\n## [{stamp}] {verdict} | {cid} {r['kind']}: {r['title'][:60]}\n")
            print(f"{cid}: {PAST[verdict]}")
            return
    sys.exit(f"{cid} not found in proposals/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--max", type=int, default=10, help="most candidates per night (default 10)")
    st = sub.add_parser("status")
    st.add_argument("--pending", action="store_true")
    d = sub.add_parser("decide")
    d.add_argument("id")
    d.add_argument("verdict", choices=["approve", "kill"])
    d.add_argument("--note", default="")
    a = ap.parse_args()
    vault = Path(a.vault).expanduser().resolve()
    if a.cmd == "scan":
        scan(vault, a.days, a.dry_run, a.max)
    elif a.cmd == "status":
        status(vault, a.pending)
    else:
        decide(vault, a.id, a.verdict, a.note)


if __name__ == "__main__":
    main()
