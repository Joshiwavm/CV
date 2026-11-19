#!/usr/bin/env python3
"""Build publications_list.tex from an ADS/SciX BibTeX export.

Usage
-----
  python3 scripts/make_publications.py                 # reads content/publications.bib
  python3 scripts/make_publications.py --fetch         # first downloads it from ADS
                                                       #   (needs env var ADS_API_TOKEN)

How to refresh by hand: run the ADS/SciX search for author:"van Marrewijk, J.",
select all -> Export -> BibTeX, and save the result as content/publications.bib.

Output: entries are grouped by my position in the author list
(1st, 2nd, 3rd, other) and sorted newest first within each group.
My name is printed in bold.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "content" / "publications.bib"
OUT = ROOT / "content" / "publications_list.tex"
QUERY = 'author:"van Marrewijk, J."'
NAME_RE = re.compile(r"marrewijk", re.IGNORECASE)
MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), start=1)}
GROUPS = [(1, "First author"), (2, "Second author"), (3, "Third author"), (99, "Co-author")]
MAX_AUTHORS = 5  # show this many names, then "et al."
EXCLUDE_TYPES = {"inproceedings", "dataset", "software"}  # proceedings, VizieR catalogues, Zenodo software
EXCLUDE_TITLE = re.compile(r"^\s*\{?\s*(Correction to|Erratum)", re.IGNORECASE)


# ----------------------------------------------------------------------------- fetch
def fetch_from_ads(path: Path) -> None:
    token = os.environ.get("ADS_API_TOKEN")
    if not token:
        sys.exit("ADS_API_TOKEN is not set; export publications.bib by hand instead.")
    hdr = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    q = urllib.parse.urlencode({"q": QUERY, "fl": "bibcode", "rows": 2000,
                                "fq": "database:(astronomy OR physics)"})
    req = urllib.request.Request(f"https://api.adsabs.harvard.edu/v1/search/query?{q}", headers=hdr)
    bibcodes = [d["bibcode"] for d in json.load(urllib.request.urlopen(req))["response"]["docs"]]
    body = json.dumps({"bibcode": bibcodes}).encode()
    req = urllib.request.Request("https://api.adsabs.harvard.edu/v1/export/bibtex",
                                 data=body, headers=hdr, method="POST")
    path.write_text(json.load(urllib.request.urlopen(req))["export"], encoding="utf-8")
    print(f"fetched {len(bibcodes)} entries from ADS -> {path.name}")


# ----------------------------------------------------------------------------- parse
def parse_bibtex(text: str) -> list[dict]:
    """Minimal BibTeX parser that handles the brace/quote styles ADS produces."""
    entries, i = [], 0
    while (m := re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.S).search(text, i)):
        etype, key, j = m.group(1).lower(), m.group(2), m.end()
        fields, depth, start = {}, 1, j
        # find end of entry by brace matching
        k = j
        while k < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        body = text[start:k - 1]
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            name, p = fm.group(1).lower(), fm.end()
            if p < len(body) and body[p] == "{":
                d, q = 0, p
                while q < len(body):
                    d += {"{": 1, "}": -1}.get(body[q], 0)
                    q += 1
                    if d == 0:
                        break
                val = body[p + 1:q - 1]
            elif p < len(body) and body[p] == '"':
                q = body.index('"', p + 1)
                val = body[p + 1:q]
            else:
                val = re.match(r"[^,\n]*", body[p:]).group(0)
            fields.setdefault(name, val.strip())
        entries.append({"type": etype, "key": key, **fields})
        i = k
    return entries


def split_authors(field: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for tok in re.split(r"(\s+and\s+|[{}])", field):
        if tok == "{":
            depth += 1
        elif tok == "}":
            depth -= 1
        if depth == 0 and re.fullmatch(r"\s+and\s+", tok or ""):
            parts.append(cur.strip())
            cur = ""
        else:
            cur += tok or ""
    if cur.strip():
        parts.append(cur.strip())
    return parts


def clean_author(a: str) -> str:
    a = re.sub(r"\\textbf\s*", "", a)          # drop bold already present in old bib files
    prev = None
    while prev != a:                            # strip braces around plain text only,
        prev = a                                # keep accent groups like {\'e} intact
        a = re.sub(r"\{([^{}\\]*)\}", r"\1", a)
    a = re.sub(r"\s+", " ", a).strip()
    return a


# ----------------------------------------------------------------------------- format
def ordinal(n: int) -> str:
    suf = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suf}"


PARTICLES = ("van der ", "van den ", "van ", "von ", "de ", "der ", "den ", "da ", "di ", "du ", "le ", "la ")


def surname_keys(name: str) -> set[str]:
    """Possible sort keys for a surname: as written and without a particle
    (alphabetical lists file 'van Marrewijk' under V or under M)."""
    sur = name.split(",")[0]
    sur = re.sub(r"\\[a-zA-Z]+|[^A-Za-z ]", "", sur).strip().lower()
    keys = {sur}
    for p in PARTICLES:
        if sur.startswith(p):
            keys.add(sur[len(p):])
    return keys


def is_alphabetical(names: list[str]) -> bool:
    """True if, after a block of lead authors, the rest of the list is alphabetical."""
    keys = [surname_keys(n) for n in names]
    for lead in range(0, max(0, len(keys) - 7)):
        tail = keys[lead:]
        pairs = list(zip(tail, tail[1:]))
        ok = sum(any(x <= y for x in kx for y in ky) for kx, ky in pairs)
        if ok / len(pairs) >= 0.9:
            return True
    return False


def fmt_authors(authors: list[str], pos: int) -> str:
    names = [clean_author(a) for a in authors]
    truncated = bool(names) and names[-1].lower().startswith("et al")
    if truncated:
        names = names[:-1]
    me = r"\textbf{van Marrewijk, J.}"           # same spelling of my name everywhere
    shown = [me if i == pos else n for i, n in enumerate(names[:MAX_AUTHORS], start=1)]
    s = ", ".join(shown)
    if len(names) > MAX_AUTHORS or truncated:
        s += ", et al."
        n_tot = f"{len(names)}+" if truncated else str(len(names))
        note = f"{n_tot} authors"
        if (pos == 0 or pos > 3) and is_alphabetical(names):   # only relevant for co-author papers
            note += ", alphabetical"
        s += f" ({note})"
    return s


def fmt_entry(e: dict, pos: int) -> str:
    title = e.get("title", "").strip()
    title = title[1:-1] if title.startswith("{") and title.endswith("}") else title
    title = title.replace("\u2500", "--")
    journal = e.get("journal") or e.get("booktitle") or e.get("howpublished") or ""
    bits = [fmt_authors(split_authors(e.get("author", "")), pos), rf"\emph{{{title}}}"]
    is_preprint = "arxiv" in journal.lower()
    if e["type"] == "software":
        bits.append(f"software, {e.get('publisher', 'Zenodo')}")
    elif journal and not is_preprint:
        jref = journal
        if e.get("volume"):
            jref += f", {e['volume']}"
        if e.get("eid") or e.get("pages"):
            jref += f", {e.get('eid') or e.get('pages')}"
        bits.append(jref)
    links = []
    if e.get("eprint"):
        links.append(rf"\href{{https://arxiv.org/abs/{e['eprint']}}}{{arXiv:{e['eprint']}}}")
    if e.get("doi") and not e.get("eprint"):
        links.append(rf"\href{{https://doi.org/{e['doi']}}}{{DOI}}")
    if e.get("adsurl"):
        links.append(rf"\href{{{e['adsurl']}}}{{ADS}}")
    if is_preprint:
        bits.append("preprint")
    text = ", ".join(bits)
    if links:
        text += r" \textcolor{muted}{\small[" + r" \textbar{} ".join(links) + "]}"
    return text


def author_position(e: dict) -> int:
    for idx, a in enumerate(split_authors(e.get("author", "")), start=1):
        if NAME_RE.search(a):
            return idx
    return 0


def sort_key(e: dict):
    year = int(re.sub(r"\D", "", e.get("year", "0")) or 0)
    month = MONTHS.get(e.get("month", "").strip("{} ").lower()[:3], 0)
    return (-year, -month, e.get("key", ""))


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download publications.bib from ADS first")
    ap.add_argument("--bib", type=Path, default=BIB)
    args = ap.parse_args()
    if args.fetch:
        fetch_from_ads(args.bib)
    if not args.bib.exists():
        sys.exit(f"{args.bib} not found: export your ADS/SciX library as BibTeX to this file.")

    entries = parse_bibtex(args.bib.read_text(encoding="utf-8"))
    seen, unique = set(), []
    for e in entries:                                  # drop duplicates and non-papers
        if e["type"] in EXCLUDE_TYPES or EXCLUDE_TITLE.search(e.get("title", "")):
            continue
        if e["key"] not in seen:
            seen.add(e["key"])
            unique.append(e)

    lines = ["% AUTO-GENERATED by scripts/make_publications.py from publications.bib -- do not edit.", ""]
    total = 0
    for limit, label in GROUPS:
        group = []
        for e in unique:
            pos = author_position(e)
            g = pos if 1 <= pos <= 3 else 99
            if g == limit:
                group.append((e, pos))
        if not group:
            continue
        group.sort(key=lambda t: sort_key(t[0]))
        total += len(group)
        lines.append(rf"\cvsubsection{{{label} ({len(group)})}}")
        for e, pos in group:
            lines.append(rf"\cvitem{{{e.get('year', '')}}}{{{fmt_entry(e, pos)}}}")
        lines.append("")
    hidden = [e["key"] for e in unique if author_position(e) == 0]
    if hidden:
        print(f"note: {len(hidden)} entries list me beyond the exported authors -> 'Co-author'")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {total} entries -> {OUT.name}")


if __name__ == "__main__":
    import urllib.parse  # noqa: E402  (only needed for --fetch)
    main()
