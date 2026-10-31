#!/usr/bin/env python3
"""Build the Publications collection from a Google Scholar CSV export.

Master data : tools/publications.csv           (Scholar export, replace the whole file to update)
Extras      : tools/publication_overrides.csv  (optional per-paper settings, see README.md)
Output      : _publications/*.md               (generated; do not edit by hand)

Usage (from the repository root):
    python3 tools/build_publications.py
    python3 tools/build_publications.py --csv new.csv --out /tmp/test_pubs   # dry test elsewhere
"""
import argparse
import csv
import html
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent

# How the site owner appears in the Scholar export (Last, First) and how to display it.
OWN_NAMES = {("choi", "junhyeok"), ("choi", "jun-hyeok")}
OWN_DISPLAY = "Junhyeok Choi"

ARTICLES = {"a", "an", "the"}
TRUTHY = {"1", "y", "yes", "true", "x"}
TRUNCATION_MARKERS = {"...", "…", "others", "et al", "et al."}


def norm(s):
    """Normalise whitespace and the special hyphens that publisher exports contain."""
    s = (s or "").replace("‐", "-").replace("‑", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def split_authors(raw):
    """Return (list of 'First Last' strings, truncated flag)."""
    names, truncated = [], False
    for part in norm(raw).split(";"):
        part = part.strip()
        if not part:
            continue
        if part.lower() in TRUNCATION_MARKERS:
            truncated = True
            continue
        if "," in part:
            last, first = [x.strip() for x in part.split(",", 1)]
            if (last.lower(), first.lower()) in OWN_NAMES:
                names.append("<b>%s</b>" % OWN_DISPLAY)
            else:
                names.append("%s %s" % (first, last))
        else:
            names.append(part)
    return names, truncated


def make_key(first_author_raw, year, title):
    first = norm(first_author_raw).split(";")[0].split(",")[0]
    first = unicodedata.normalize("NFKD", first).encode("ascii", "ignore").decode()
    first = re.sub(r"[^a-z0-9]", "", first.lower()) or "paper"
    words = [w for w in re.findall(r"[A-Za-z0-9]+", title) if w.lower() not in ARTICLES]
    word = words[0].lower() if words else "paper"
    return "%s%s%s" % (first, year, word)


def read_overrides(path):
    out = {}
    if not path.exists():
        return out
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            key = (row.get("key") or "").strip()
            if key and not key.startswith("#"):
                out[key] = {k: (v or "").strip() for k, v in row.items()}
    return out


def yaml_double(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def yaml_single(s):
    return "'%s'" % s.replace("'", "''")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(ROOT / "tools" / "publications.csv"))
    ap.add_argument("--overrides", default=str(ROOT / "tools" / "publication_overrides.csv"))
    ap.add_argument("--out", default=str(ROOT / "_publications"))
    args = ap.parse_args()

    out_dir = pathlib.Path(args.out)
    with open(args.csv, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if norm(r.get("Title"))]
    if not rows:
        sys.exit("No rows found in %s; refusing to delete existing files." % args.csv)
    overrides = read_overrides(pathlib.Path(args.overrides))

    entries, used_keys, per_year = [], {}, {}
    for r in rows:
        title = norm(r["Title"])
        year = norm(r.get("Year"))
        if not re.fullmatch(r"\d{4}", year):
            sys.exit("Row without a valid Year: %s" % title)
        key = make_key(r.get("Authors", ""), year, title)
        n = used_keys.get(key, 0)
        used_keys[key] = n + 1
        if n:
            key += "bcdefghij"[n - 1]
        entries.append((key, r, title, year))

    unknown = set(overrides) - {e[0] for e in entries}
    for k in sorted(unknown):
        print("WARNING: overrides row '%s' matches no paper (typo or removed paper?)" % k)

    # Number papers in order of acceptance (1 = accepted first). The accepted date comes from
    # the overrides file. A paper with an unknown date can use sort_before=<key> to be placed
    # immediately before that paper. Any other paper without a date stops the build.
    sort_keys = {}
    for key, r, title, year in entries:
        ov = overrides.get(key, {})
        acc, before = ov.get("accepted", ""), ov.get("sort_before", "")
        if acc:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", acc):
                sys.exit("accepted for %s must be YYYY-MM-DD: %r" % (key, acc))
            sort_keys[key] = (acc, 1)
    for key, r, title, year in entries:
        ov = overrides.get(key, {})
        before = ov.get("sort_before", "")
        if key in sort_keys:
            continue
        if before and before in sort_keys:
            sort_keys[key] = (sort_keys[before][0], 0)
        else:
            sys.exit("No accepted date (or valid sort_before) for %s in %s" % (key, args.overrides))
    ordered = sorted((e[0] for e in entries), key=lambda k: (sort_keys[k], [e[0] for e in entries].index(k)))
    pub_no = {k: i + 1 for i, k in enumerate(ordered)}

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.md"):
        old.unlink()

    for key, r, title, year in entries:
        ov = overrides.get(key, {})
        names, truncated = split_authors(r.get("Authors", ""))
        if ov.get("authors"):
            # Verified full author list ("Last, First; Last, First"); replaces the truncated export.
            names, truncated = split_authors(ov["authors"])
        if ov.get("et_al", "").lower() in TRUTHY:
            truncated = True
        authors = ", ".join(names) + (", et al." if truncated else "")

        date = ov.get("date", "")
        if date:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or not date.startswith(year):
                sys.exit("Override date for %s must be YYYY-MM-DD within %s: %r" % (key, year, date))
        else:
            idx = per_year.get(year, 0)
            per_year[year] = idx + 1
            if idx > 27:
                sys.exit("More than 28 papers without an override date in %s" % year)
            # Only the year is displayed; the day just keeps the CSV order within a year.
            date = "%s-01-%02d" % (year, 28 - idx)

        venue = html.escape(norm(r.get("Publication")), quote=False)
        vol, num = norm(r.get("Volume")), norm(r.get("Number"))
        pages = norm(r.get("Pages")).replace("--", "-")
        pages = re.sub(r"(?<=\w)-(?=\w)", "–", pages) if re.fullmatch(r"\w+-\w+", pages) else pages
        tail = ""
        if vol:
            tail += ", %s" % vol + ("(%s)" % num if num else "")
        if pages:
            tail += ", %s" % pages
        citation = "%s. (%s). &quot;%s.&quot; <i>%s</i>%s." % (
            authors, year, html.escape(title, quote=False), venue, tail)
        citation = citation.replace("..", ".")

        lines = [
            "---",
            "title: %s" % yaml_double(title),
            "collection: publications",
            "category: manuscripts",
            "permalink: /publication/%s-%s" % (date, key),
            "date: %s" % date,
            "venue: %s" % yaml_single(venue),
            "pub_no: %d" % pub_no[key],
        ]
        if ov.get("paperurl"):
            lines.append("paperurl: %s" % yaml_single(ov["paperurl"]))
        lines += ["citation: %s" % yaml_single(citation), "---", ""]
        (out_dir / ("%s-%s.md" % (date, key))).write_text("\n".join(lines), encoding="utf-8")
        print("#%d  %s  %s%s" % (pub_no[key], date, key, "  [et al.]" if truncated else ""))

    print("Wrote %d files to %s" % (len(entries), out_dir))


if __name__ == "__main__":
    main()
