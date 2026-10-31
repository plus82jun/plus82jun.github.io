# Publications workflow

`tools/publications.csv` is the master list. `_publications/*.md` is generated from it.

## Update the site after a new paper

1. In Google Scholar, select all papers, then Export, then CSV.
2. Replace `tools/publications.csv` with the new file.
3. Run `python3 tools/build_publications.py` from the repository root.
4. Review `git diff`, commit, and push to `master`. GitHub Actions redeploys the site.

Do not edit `_publications/*.md` by hand; the script deletes and rewrites them.

## Per-paper extras: `tools/publication_overrides.csv`

Scholar's export cannot carry these, so they live in a separate file that survives a CSV replacement.
Each row starts with the paper key printed by the script (for example `park2026nanostructured`).

| column | meaning |
|---|---|
| `et_al` | `yes` if the author list in the export is truncated |
| `date` | optional `YYYY-MM-DD` (inside the paper's year) to control ordering within a year |
| `paperurl` | optional DOI or paper link; the theme labels it "Download Paper" |
| `note` | free text for yourself; not used |
| `accepted` | accepted date `YYYY-MM-DD` from the publisher; papers are numbered 1, 2, 3, ... in this order (oldest accepted = 1). Not shown on the site |
| `sort_before` | only for a paper whose accepted date is unknown: a paper key; this paper is numbered immediately before it |
| `authors` | optional verified full author list in Scholar format (`Last, First; Last, First`); replaces the exported list, so leave `et_al` empty when it is filled |

The key is built as `<first author last name><year><first title word>`, so it can change if the
title or first author changes in a later export. The script warns about override rows that no longer match.

## Numbering

The script writes `pub_no` into each paper and the Publications page lists papers by `pub_no` ascending with the number shown before the title. A new paper needs an `accepted` date (or `sort_before`) in the overrides file; otherwise the build stops.

## Notes

- Only the year is shown on the site. Without an override date, papers of the same year keep the CSV order.
- Titles are written as plain text; HTML characters are escaped. Characters such as `_` or `*` may be read as Markdown.
- This folder is excluded from the Jekyll build (`exclude:` in `_config.yml`).
