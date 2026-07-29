# Publications / talks: single source of truth

`data/entries.json` is now the only place you edit when you add a
conference, talk, poster, or paper. `scripts/generate.py` turns it into:

- `resources/generated/publications.tex` and `resources/generated/talks.tex`
  — `\input{}` into `CV_Nanni.tex` (already wired up)
- the `<!-- PUBLICATIONS:START/END -->` and `<!-- TALKS:START/END -->`
  blocks inside `index.html` — rewritten in place

`index.html` stays a plain static file. Nothing runs in the browser;
you just re-run the script locally whenever you change an entry, then
commit and push as usual.

## Day-to-day workflow

```bash
# 1. edit data/entries.json (add/change an entry)
# 2. regenerate everything:
python3 scripts/generate.py

# 3. recompile the CV:
cd resources && latexmk -pdf CV_Nanni.tex && cd ..

# 4. commit as usual — data/entries.json, index.html, resources/generated/*,
#    and the recompiled resources/out/CV_Nanni.pdf
```

The script is idempotent — running it twice in a row produces byte-identical
output, so it's safe to re-run any time you're not sure the site/CV are in
sync.

## What I changed in your repo

- `index.html`: the hardcoded `<li>` lists under "Preprints" and "Talks &
  Posters" are replaced by marker comments the script fills in.
- `resources/CV_Nanni.tex`: the `\cvlistitem{...}` and `\cventry{...}` lines
  in the Publications and Talks sections are replaced by
  `\input{generated/publications.tex}` / `\input{generated/talks.tex}`.
  Everything else in the CV (Education, Research visits, Teaching,
  Distinctions, Languages) is untouched — still edited by hand as before.
- `data/entries.json`: reconstructed from what was on the site and in the
  CV, reconciling several small mismatches between the two (see below).
- `resources/out/CV_Nanni.pdf`: recompiled from the new source, verified
  to build cleanly with `latexmk` (I test-compiled it — 3 pages, no
  errors, only harmless underfull-hbox line-breaking warnings).

## Things I reconciled between the old site and CV — please check

Comparing the two copies turned up genuine inconsistencies. I picked the
version I judged more likely correct; please double check:

- **North Carolina talk date**: site said 11.2023, CV said 11.2024. I went
  with **2024** (matches the CV and the "Research visits" section, which
  has you at UNC 04.11.2024–24.11.2024 — same trip). Fix `data/entries.json`
  if that's wrong.
- **North Carolina talk title/institution**: the CV had title "Talk at the
  University of North Carolina" with no institution field; the site had
  the real seminar name "Geometric Methods in Representation Theory" with
  institution "University of North Carolina". I used the site's more
  specific version in both outputs now.
- **Third preprint's title capitalization**: "lagrangian" (CV) vs
  "Lagrangian" (site). I standardized on "Lagrangian".
- **arXiv link style**: some entries used `doi.org/10.48550/arXiv...`,
  others `arxiv.org/abs/...`. Both resolve to the same paper; I standardized
  on `arxiv.org/abs/{id}` everywhere.
- **Talk dates**: some had a leading zero (`06.2025`), some didn't
  (`4.2026`), one even had a comma instead of a period (`04,2026`). All
  now consistently `MM.YYYY`.
- **Institution/country on the website**: the old site often dropped the
  institution and always dropped the country for talks (e.g. Nancy just
  said ", Nancy (02.2026)"). Since both outputs now come from the same
  data, the site shows the same institution/city/country detail the CV
  does. Let me know if you'd rather keep the site's talk lines terser.

## Extending later

- New fields: just add them to the entry dicts in `entries.json` and use
  them in `tex_article`/`html_article` (or the talk equivalents) in
  `scripts/generate.py`.
- Other CV sections (Research visits, Teaching, Distinctions) aren't wired
  into this system yet since they change rarely — say the word if you want
  those generated too.
- If you'd like this to run automatically on push (so you never forget to
  regenerate before committing), a short GitHub Action can do it — happy
  to add one.
