#!/usr/bin/env python3
"""
Single source of truth: data/entries.json
Run this whenever you add/edit a publication or talk:

    python3 scripts/generate.py

It writes:
  - resources/generated/papers.tex         (\\input under "Papers" in CV_Nanni.tex)
  - resources/generated/preprints.tex      (\\input under "Preprints" in CV_Nanni.tex)
  - resources/generated/talks.tex          (\\input this into CV_Nanni.tex)
  - index.html                             (rewritten in place, between markers)

Nothing here runs in the browser -- index.html stays a plain static file,
you just regenerate it locally whenever you change an entry, then commit
and push like normal.

Math in titles is NOT escaped: write titles as you would in LaTeX
(e.g. "$K3^{[n]}$-type manifolds"); if index.html ever gets MathJax/KaTeX
added, the same syntax will render there too.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "entries.json"
INDEX_FILE = ROOT / "index.html"
GEN_DIR = ROOT / "resources" / "generated"

PREPRINT_STATUSES = ("preprint", "submitted")


# ---------- shared helpers ----------

def journal_ref(e, em):
    """Bibliographic line after the title, e.g. 'Math. Z. 314 (2), Art. 30 (2026)'.
    `em` wraps the journal name (HTML <em> or LaTeX emph)."""
    status, journal = e.get("status"), e.get("journal")
    if status == "published" and journal:
        ref = em(journal)
        if e.get("volume"):
            ref += f" {e['volume']}"
        if e.get("issue"):
            ref += f" ({e['issue']})"
        if e.get("number"):
            ref += f", {e['number']}"
        if e.get("pub_year"):
            ref += f" ({e['pub_year']})"
        return ref
    if status == "accepted" and journal:
        return f"To appear in {em(journal)}"
    if status == "submitted" and journal:
        return f"Submitted to {em(journal)}"
    return "arXiv preprint"  # the caller appends the visible arXiv link and the year


def split_articles(data):
    """Preprints (newest first) and publications (to appear first, then newest published)."""
    arts = data.get("articles", [])
    pre = sorted([e for e in arts if e.get("status") in PREPRINT_STATUSES], key=lambda e: e.get("year", 0), reverse=True)
    pub = sorted([e for e in arts if e.get("status") not in PREPRINT_STATUSES],
                 key=lambda e: (e.get("status") == "accepted", e.get("pub_year") or e.get("year", 0)), reverse=True)
    return pre, pub


def title_url(e):
    return f"https://doi.org/{e['doi']}" if e.get("doi") else f"https://arxiv.org/abs/{e['arxiv']}"


def ref_end(e):
    """Separator after the journal reference: skip the extra full stop when it already ends with one
    (e.g. 'To appear in Kyoto J. Math.')."""
    ends_with_dot = e.get("status") in ("accepted", "submitted") and (e.get("journal") or "").endswith(".")
    return " " if ends_with_dot else ". "


def show_arxiv_link(e):
    """Only accepted (not yet published) papers get a separate arXiv link: preprints already link
    the title to arXiv, and published papers show their DOI instead."""
    return e.get("status") not in PREPRINT_STATUSES and not e.get("doi")


def talk_date_label(date_str):
    year, month = date_str.split("-")
    return f"{month}.{year}"


# ---------- LaTeX generation ----------

def tex_article(e):
    em = lambda j: "\\emph{" + j + "}"
    line = "\\cvlistitem{\\href{" + title_url(e) + "}{\\textit{" + e["title"] + "}}. " + journal_ref(e, em)
    if show_arxiv_link(e):
        line += ref_end(e) + "\\href{https://arxiv.org/abs/" + e["arxiv"] + "}{arXiv:" + e["arxiv"] + "} (" + str(e["year"]) + ")"
    if e.get("doi"):
        line += ". \\href{https://doi.org/" + e["doi"] + "}{doi:" + e["doi"] + "}"
    if e.get("status") in PREPRINT_STATUSES and not e.get("doi"):
        line += ", \\href{https://arxiv.org/abs/" + e["arxiv"] + "}{arXiv:" + e["arxiv"] + "} (" + str(e["year"]) + ")"
    return line + ".}" if not line.endswith(".") else line + "}"


def tex_talk(e):
    event = e["event"]
    if e.get("event_link"):
        event_tex = f"\\href{{{e['event_link']}}}{{{event}}}"
    else:
        event_tex = event
    title = f"{e['kind']} at {event_tex}" if e.get("kind") else event_tex
    institution = e.get("institution") or ""
    city = e.get("city") or ""
    country = e.get("country") or ""
    date = talk_date_label(e["date"])
    return f"\\cventry{{{date}}}{{{title}}}{{{institution}}}{{{city}}}{{{country}}}{{}}"


def write_latex(data):
    GEN_DIR.mkdir(parents=True, exist_ok=True)

    pre, pub = split_articles(data)
    articles_sorted = pub + pre
    # two lists, \input under the "Papers" and "Preprints" subsections of the CV
    (GEN_DIR / "papers.tex").write_text("\n\n".join(tex_article(e) for e in pub) + "\n", encoding="utf-8")
    (GEN_DIR / "preprints.tex").write_text("\n\n".join(tex_article(e) for e in pre) + "\n", encoding="utf-8")

    talks_sorted = sorted(data.get("talks", []), key=lambda e: e["date"], reverse=True)
    (GEN_DIR / "talks.tex").write_text(
        "\n".join(tex_talk(e) for e in talks_sorted) + "\n", encoding="utf-8"
    )
    print(f"wrote {GEN_DIR/'papers.tex'} ({len(pub)}) and {GEN_DIR/'preprints.tex'} ({len(pre)})")
    print(f"wrote {GEN_DIR/'talks.tex'} ({len(talks_sorted)} entries)")


# ---------- HTML generation ----------

def html_article(e):
    em = lambda j: f"<em>{j}</em>"
    line = f'<a href="{title_url(e)}"><em>{e["title"]}</em></a>. {journal_ref(e, em)}'
    if show_arxiv_link(e):
        line += ref_end(e) + f'<a href="https://arxiv.org/abs/{e["arxiv"]}">arXiv:{e["arxiv"]}</a> ({e["year"]})'
    if e.get("doi"):
        line += f'. <a href="https://doi.org/{e["doi"]}">doi:{e["doi"]}</a>'
    if e.get("status") in PREPRINT_STATUSES and not e.get("doi"):
        line += f', <a href="https://arxiv.org/abs/{e["arxiv"]}">arXiv:{e["arxiv"]}</a> ({e["year"]})'
    return f"                <li>{line}.</li>"


def html_talk(e):
    event = e["event"]
    if e.get("event_link"):
        event_html = f'<a href="{e["event_link"]}">{event}</a>'
    else:
        event_html = event
    bits = [f"{e['kind']} at <em>{event_html}</em>" if e.get("kind") else f"<em>{event_html}</em>"]
    location_bits = [b for b in [e.get("institution"), e.get("city"), e.get("country")] if b]
    if location_bits:
        bits.append(", " + ", ".join(location_bits))
    bits.append(f" ({talk_date_label(e['date'])})")
    if e.get("notes"):
        bits.append(f' – <a href="{e["notes"]}">notes</a>')
    return f"                <li>{''.join(bits)}</li>"


def replace_between(html, start_marker, end_marker, new_content):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    replacement = f"{start_marker}\n{new_content}\n                {end_marker}"
    new_html, count = pattern.subn(replacement, html)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one match for markers {start_marker!r}/{end_marker!r}, found {count}"
        )
    return new_html


def write_html(data):
    html = INDEX_FILE.read_text(encoding="utf-8")

    pre, pub = split_articles(data)
    html = replace_between(html, "<!-- PREPRINTS:START -->", "<!-- PREPRINTS:END -->", "\n".join(html_article(e) for e in pre))
    html = replace_between(html, "<!-- PUBLICATIONS:START -->", "<!-- PUBLICATIONS:END -->", "\n".join(html_article(e) for e in pub))
    articles_sorted = pre + pub

    talks_sorted = sorted(data.get("talks", []), key=lambda e: e["date"], reverse=True)
    talks_html = "\n".join(html_talk(e) for e in talks_sorted)
    html = replace_between(html, "<!-- TALKS:START -->", "<!-- TALKS:END -->", talks_html)

    INDEX_FILE.write_text(html, encoding="utf-8")
    print(f"wrote {INDEX_FILE} ({len(articles_sorted)} articles, {len(talks_sorted)} talks)")


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    write_latex(data)
    write_html(data)


if __name__ == "__main__":
    main()
