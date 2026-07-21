#!/usr/bin/env python3
"""
Single source of truth: data/entries.json
Run this whenever you add/edit a publication or talk:

    python3 scripts/generate.py

It writes:
  - resources/generated/publications.tex   (\\input this into CV_Nanni.tex)
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

STATUS_NOTE_TEX = {
    "submitted": "Submitted to \\emph{{{venue}}}",
    "accepted": "Soon to appear in \\emph{{{venue}}}",
    "published": "Published in \\emph{{{venue}}}",
}

STATUS_NOTE_HTML = {
    "submitted": "Submitted to <em>{venue}</em>",
    "accepted": "Soon to appear in <em>{venue}</em>",
    "published": "Published in <em>{venue}</em>",
}


# ---------- shared helpers ----------

def tex_article_note(e):
    template = STATUS_NOTE_TEX.get(e.get("status"))
    venue = e.get("venue")
    if template and venue:
        return template.format(venue=venue)
    return None


def html_article_note(e):
    template = STATUS_NOTE_HTML.get(e.get("status"))
    venue = e.get("venue")
    if template and venue:
        return template.format(venue=venue)
    return None


def talk_date_label(date_str):
    year, month = date_str.split("-")
    return f"{month}.{year}"


# ---------- LaTeX generation ----------

def tex_article(e):
    note = tex_article_note(e)
    line = (
        f"\\cvlistitem{{ \\textit{{{e['title']}}}. "
        f"\\href{{https://arxiv.org/abs/{e['arxiv']}}}{{arXiv:{e['arxiv']}}}"
    )
    if note:
        line += f" ({note})"
    line += "}"
    return line


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

    articles_sorted = sorted(data.get("articles", []), key=lambda e: e.get("year", 0), reverse=True)
    (GEN_DIR / "publications.tex").write_text(
        "\n\n".join(tex_article(e) for e in articles_sorted) + "\n", encoding="utf-8"
    )

    talks_sorted = sorted(data.get("talks", []), key=lambda e: e["date"], reverse=True)
    (GEN_DIR / "talks.tex").write_text(
        "\n".join(tex_talk(e) for e in talks_sorted) + "\n", encoding="utf-8"
    )
    print(f"wrote {GEN_DIR/'publications.tex'} ({len(articles_sorted)} entries)")
    print(f"wrote {GEN_DIR/'talks.tex'} ({len(talks_sorted)} entries)")


# ---------- HTML generation ----------

def html_article(e):
    note = html_article_note(e)
    note_html = f" ({note})" if note else ""
    return (
        "                <li>\n"
        f"                    <strong>{e['title']}</strong> ({e['year']})<br>\n"
        f"                    <a href=\"https://arxiv.org/abs/{e['arxiv']}\">arXiv:{e['arxiv']}</a>{note_html}\n"
        "                </li>"
    )


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

    articles_sorted = sorted(data.get("articles", []), key=lambda e: e.get("year", 0), reverse=True)
    articles_html = "\n\n".join(html_article(e) for e in articles_sorted)
    html = replace_between(html, "<!-- PUBLICATIONS:START -->", "<!-- PUBLICATIONS:END -->", articles_html)

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
