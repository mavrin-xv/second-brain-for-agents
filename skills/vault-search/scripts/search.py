#!/usr/bin/env python3
"""Search the vault: qmd when it is installed, a built-in BM25 ranker when it is not.

The fallback needs nothing but Python. It ranks every markdown file with BM25, gives
titles and file names 3x weight, skips protected folders listed in SCHEMA.md, and prints
the best matching line of each hit so the agent can decide what to open.

Usage:
  python search.py "pricing objections"            # top 8 hits
  python search.py "kiln supplier" -n 3 --json
  python search.py "cold email" --folder wiki      # only inside wiki/
  python search.py "cold email" --no-qmd           # force the fallback

qmd (https://github.com/tobi/qmd) gives better recall on big vaults:
  npm install -g @tobilu/qmd && qmd collection add ./vault --name vault && qmd embed
With qmd present this script calls `qmd search` (BM25) or, with --hybrid, `qmd query`.
Env: VAULT_DIR when --vault is not given.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ALWAYS_SKIP = {".git", ".obsidian", ".trash", "node_modules"}
TOKEN = re.compile(r"[a-z0-9][a-z0-9\-]*[a-z0-9]|[a-z0-9]", re.I)
STOP = set("a an the and or of to in on for with is are was be it this that as at by from not but if".split())


def protected(vault):
    schema = vault / "SCHEMA.md"
    if not schema.exists():
        return {"private"}
    m = re.search(r"^protected:\s*\[(.*?)\]", schema.read_text(encoding="utf-8", errors="ignore"), re.M)
    return {p.strip().strip("'\"") for p in m.group(1).split(",") if p.strip()} if m else {"private"}


def tokens(text):
    return [t for t in (w.lower() for w in TOKEN.findall(text)) if t not in STOP]


def bm25(vault, query, folder, n):
    skip = protected(vault) | ALWAYS_SKIP
    base = vault / folder if folder else vault
    docs = []
    for f in base.rglob("*.md"):
        rel = f.relative_to(vault)
        if rel.parts[0] in skip or any(p in ALWAYS_SKIP for p in rel.parts):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        title = re.search(r"^title:\s*(.+)$", text, re.M) or re.search(r"^#\s+(.+)$", text, re.M)
        head = (title.group(1) if title else "") + " " + f.stem.replace("-", " ")
        tf = Counter(tokens(text))
        for t in tokens(head):
            tf[t] += 3
        docs.append((rel.as_posix(), text, tf, sum(tf.values())))
    if not docs:
        return []
    q = tokens(query)
    N = len(docs)
    avg = sum(d[3] for d in docs) / N
    df = Counter(t for d in docs for t in set(d[2]) if t in q)
    k1, b = 1.4, 0.75
    hits = []
    for path, text, tf, length in docs:
        s = 0.0
        for t in q:
            if tf[t]:
                idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * length / avg))
        if s > 0:
            best = max(text.splitlines(), key=lambda line: sum(line.lower().count(t) for t in q), default="")
            hits.append({"path": path, "score": round(s, 2), "line": best.strip()[:160]})
    hits.sort(key=lambda h: -h["score"])
    return hits[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query")
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "vault"))
    ap.add_argument("-n", type=int, default=8)
    ap.add_argument("--folder", default="", help="limit to a subfolder, e.g. wiki or decisions")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-qmd", action="store_true")
    ap.add_argument("--hybrid", action="store_true", help="with qmd: use `qmd query` (vector + rerank)")
    a = ap.parse_args()
    vault = Path(a.vault).expanduser().resolve()

    qmd = shutil.which("qmd")
    if qmd and not a.no_qmd and not a.folder:
        cmd = [qmd, "query" if a.hybrid else "search", a.query, "-n", str(a.n)] + (["--json"] if a.json else [])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0 and r.stdout.strip():
            print(r.stdout.strip())
            return
        print("qmd returned nothing, falling back to built-in search", file=sys.stderr)

    hits = bm25(vault, a.query, a.folder, a.n)
    if a.json:
        print(json.dumps(hits, indent=2))
        return
    if not hits:
        print("no hits. Try fewer or different words, or a synonym.")
        return
    for h in hits:
        print(f"{h['score']:>6}  {h['path']}\n        {h['line']}")


if __name__ == "__main__":
    main()
