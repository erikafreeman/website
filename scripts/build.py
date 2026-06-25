#!/usr/bin/env python3
"""
Build generated content from the single-source-of-truth data files.

Reads:   data/publications.yml, data/cv.yml
Writes:  publications.qmd   (website Publications page — fancy .pub layout)
         cv.qmd             (website CV page [html] + downloadable PDF [typst])

Runs automatically before every Quarto render (see `pre-render` in _quarto.yml),
so editing a YAML file and pushing updates the site page, the CV page, and the
CV PDF in one go.
"""

import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

STATUS_ORDER = ["published", "under_review", "in_prep", "technical_report"]
STATUS_LABEL = {
    "published": "Published",
    "under_review": "Under review",
    "in_prep": "In advanced preparation",
    "technical_report": "Technical reports",
}


def load(name):
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8"))


def esc_stars(s):
    """Escape equal-contribution asterisks so markdown doesn't read them as emphasis."""
    return (s or "").replace("*", r"\*")


def venue_line(p):
    venue, year, status = p.get("venue"), p.get("year"), p.get("status")
    if not venue:
        return None
    if status in ("published", "technical_report"):
        return f"{venue} · {year}" if year else venue
    if status == "under_review":
        return venue
    if status == "in_prep":
        return f"for {venue}"
    return venue


def groups(entries):
    """Yield (status, [entries]) in canonical order, skipping empty groups."""
    for status in STATUS_ORDER:
        items = [e for e in entries if e.get("status") == status]
        if items:
            yield status, items


# ── website Publications page ────────────────────────────────────────────────

def web_title(p):
    t = p["title"]
    if p.get("url"):
        link = f"[{t}]({p['url']})"
    else:
        link = t
    if p.get("preprint"):
        link = link + " *(preprint)*." if p.get("url") else f"{t} *(preprint)*."
    if p.get("note_html"):
        link += p["note_html"]
    return link


def web_entry(p, kind):
    # .pub-venue / .pub-authors are styled `display:block` in custom.scss, i.e.
    # they are bracketed spans, not fenced divs.
    out = ["::: {.pub}", web_title(p)]
    v = venue_line(p)
    if v:
        out.append("[" + v + "]{.pub-venue}")
    if kind == "first":
        co = p.get("coauthors") or ""
        authors = "with " + esc_stars(co) if co else "Sole author"
    else:
        authors = p.get("authors", "")
    out.append("[" + authors + "]{.pub-authors}")
    out.append(":::")
    return "\n".join(out)


def web_column(entries, kind, heading):
    out = ["::: {.pubs-col}", f"## {heading} ({len(entries)})", ""]
    for status, items in groups(entries):
        out.append("::: {.group-label}")
        out.append(STATUS_LABEL[status])
        out.append(":::")
        out.append("")
        for p in items:
            out.append(web_entry(p, kind))
            out.append("")
    if kind == "first" and any("*" in (e.get("coauthors") or "") for e in entries):
        out.append('::: {style="font-size: 0.78rem; color: #a8a8a8; margin-top: 1.5rem;"}')
        out.append(r"\* equal contribution")
        out.append(":::")
        out.append("")
    out.append(":::")
    return "\n".join(out)


def pub_chart(first, contrib):
    """Inline SVG bar chart of published output per year (first-author vs contributing)."""
    from collections import defaultdict
    fa, ca = defaultdict(int), defaultdict(int)
    for p in first:
        if p.get("status") == "published" and isinstance(p.get("year"), int):
            fa[p["year"]] += 1
    for p in contrib:
        if p.get("status") == "published" and isinstance(p.get("year"), int):
            ca[p["year"]] += 1
    if not (fa or ca):
        return ""
    yrs = list(range(min({*fa, *ca}), max({*fa, *ca}) + 1))
    maxv = max((fa[y] + ca[y]) for y in yrs) or 1
    W, H, x0, x1, base, top = 800, 270, 50, 780, 215, 40
    unit = (base - top) / maxv
    slot = (x1 - x0) / len(yrs)
    bw = min(46.0, slot * 0.62)
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="pub-chart-svg" role="img" aria-label="Peer-reviewed publications per year">']
    s.append(f'<line x1="{x0}" y1="{base}" x2="{x1}" y2="{base}" stroke="#3a3f36" stroke-width="1"/>')
    for i, y in enumerate(yrs):
        cx = x0 + slot * i + slot / 2
        bx = cx - bw / 2
        f, c = fa[y], ca[y]
        fh, ch = f * unit, c * unit
        if f:
            s.append(f'<rect x="{bx:.0f}" y="{base-fh:.0f}" width="{bw:.0f}" height="{fh:.0f}" rx="2" fill="#aecb86"/>')
        if c:
            s.append(f'<rect x="{bx:.0f}" y="{base-fh-ch:.0f}" width="{bw:.0f}" height="{ch:.0f}" rx="2" fill="#5d6b4e"/>')
        if f + c:
            s.append(f'<text x="{cx:.0f}" y="{base-fh-ch-7:.0f}" text-anchor="middle" font-size="13" fill="#cfd6c6" font-family="Inter,sans-serif">{f+c}</text>')
        s.append(f'<text x="{cx:.0f}" y="{base+20:.0f}" text-anchor="middle" font-size="12" fill="#9a9a9a" font-family="Inter,sans-serif">{y}</text>')
    s.append(f'<rect x="{x0}" y="10" width="12" height="12" rx="2" fill="#aecb86"/><text x="{x0+18}" y="20" font-size="12" fill="#9a9a9a" font-family="Inter,sans-serif">First author</text>')
    s.append(f'<rect x="{x0+118}" y="10" width="12" height="12" rx="2" fill="#5d6b4e"/><text x="{x0+136}" y="20" font-size="12" fill="#9a9a9a" font-family="Inter,sans-serif">Contributing</text>')
    s.append('</svg>')
    return ("::: {.pub-chart}\n"
            "[Peer-reviewed output by year]{.pub-chart-label}\n\n"
            "```{=html}\n" + "".join(s) + "\n```\n\n"
            ":::")


def build_publications(first, contrib):
    body = [
        "---",
        'title: ""',
        'pagetitle: "Publications"',
        'description: "Publications by Dr. Erika C. Freeman — peer-reviewed first-author and contributing papers in dissolved organic matter, FT-ICR-MS, and freshwater biogeochemistry."',
        "format:",
        "  html:",
        "    toc: false",
        "    page-layout: full",
        "---",
        "",
        "<!-- GENERATED by scripts/build.py from data/publications.yml — do not edit by hand. -->",
        "",
        "::: {.section-label}",
        "Publications",
        ":::",
        "# publications {.section-title}",
        "",
        pub_chart(first, contrib),
        "",
        "::: {.pubs-cols}",
        "",
        web_column(first, "first", "First-author publications"),
        "",
        web_column(contrib, "contrib", "Contributing-author publications"),
        "",
        ":::",
        "",
    ]
    (ROOT / "publications.qmd").write_text("\n".join(body), encoding="utf-8")


# ── CV page (html) + PDF (typst) ─────────────────────────────────────────────

def cv_cite(p, kind):
    if kind == "first":
        co = (p.get("coauthors") or "").replace("*", "")
        authors = "Freeman EC, " + co if co else "Freeman EC"
    else:
        authors = p.get("authors", "")
    title = p["title"].rstrip(".")
    venue, year, status = p.get("venue"), p.get("year"), p.get("status")
    if status == "published":
        if venue and year:
            tail = f"*{venue}* ({year})."
        elif venue:
            tail = f"*{venue}*."
        else:
            tail = f"({year})." if year else ""
    elif status == "technical_report":
        if venue and year:
            tail = f"{venue} ({year})."
        elif venue:
            tail = f"{venue}."
        else:
            tail = f"({year})." if year else ""
    elif status in ("under_review", "commentary", "in_prep"):
        default = {"under_review": "in review", "commentary": "submitted", "in_prep": "in prep"}[status]
        d = p.get("status_detail") or default
        tail = f"*{venue}*, {d}." if venue else f"{d[:1].upper()}{d[1:]}."
    else:
        tail = f"*{venue}*, in prep." if venue else "In prep."
    return f"- {authors}. {title}. {tail}"


def build_cv(cv, first, contrib, protocols):
    pr = cv["profile"]
    meta = (
        f"{pr['email']} · ORCID {pr['orcid']} · "
        f"Google Scholar {pr['scholar']} · {pr['website']} · "
        f"{pr['citizenship']} · {pr['languages']}"
    )

    n_pub_first = sum(1 for p in first if p.get("status") == "published")
    n_other_first = len(first) - n_pub_first
    n_contrib_pub = sum(1 for p in contrib if p.get("status") == "published")

    L = [
        "---",
        'title: ""',
        'pagetitle: "CV"',
        'description: "Curriculum vitae of Dr. Erika C. Freeman, Junior Group Leader (Tenure Track) at IGB Berlin."',
        "format:",
        "  html:",
        "    toc: false",
        "    page-layout: full",
        "  typst:",
        "    papersize: a4",
        "    margin: { x: 1.6cm, y: 1.5cm }",
        "    fontsize: 9.5pt",
        "---",
        "",
        "<!-- GENERATED by scripts/build.py from data/cv.yml + data/publications.yml. -->",
        "",
        ":::: {.cv-page}",
        "",
        f"# {pr['name']} {{.cv-name}}",
        "",
        "[" + pr["tagline"] + "]{.cv-tagline}",
        "",
        "[" + meta + "]{.cv-meta}",
        "",
        '::: {.content-visible when-format="html"}',
        "[Download PDF](cv.pdf){.cv-download}",
        ":::",
        "",
        "## Current position",
        "",
        cv["current_position"].strip(),
        "",
        "## Appointments",
        "",
        "| Role | Institution | Dates |",
        "|---|---|---|",
    ]
    for a in cv["appointments"]:
        L.append(f"| {a['role']} | {a['institution']} | {a['dates']} |")
    L += ["", "## Education", "", "| Degree | Institution | Date | Supervisor(s) |", "|---|---|---|---|"]
    for e in cv["education"]:
        L.append(f"| {e['degree']} | {e['institution']} | {e['date']} | {e.get('supervisors','')} |")

    def section(title, items):
        out = ["", f"## {title}", ""]
        out += [f"- {it}" for it in items]
        return out

    L += section("Research funding & analytical awards", cv["funding"])
    L += section("Honours & awards", cv["honours"])

    L += ["", "## Publications", ""]
    L += [
        f"Full record below. First author: **{n_pub_first} published**, "
        f"{n_other_first} in review or in preparation. "
        f"Co-author: **{n_contrib_pub} published**. "
        f"Metrics via ORCID {pr['orcid']} and Google Scholar ({pr['scholar']}).",
        "",
        "**First-author**",
        "",
    ]
    L += [cv_cite(p, "first") for p in first]
    L += ["", "**Contributing-author**", ""]
    L += [cv_cite(p, "contrib") for p in contrib]

    L += cv_protocols_block(protocols)

    L += section("Invited talks (selected)", cv["talks"])
    L += section("Teaching & mentoring", cv["teaching"])
    L += section("Service & esteem", cv["service"])
    L += ["", "## Skills", "", cv["skills"].strip(), "", "::::", ""]

    (ROOT / "cv.qmd").write_text("\n".join(L), encoding="utf-8")


# ── Protocols (protocols.io) ─────────────────────────────────────────────────

PROTO_ORDER = ["published", "in_prep", "planned"]
PROTO_LABEL = {"published": "Published", "in_prep": "In preparation", "planned": "Planned"}


def proto_entry(p):
    title = p["title"]
    head = f"[{title}]({p['doi']})" if p.get("doi") else title
    out = ["::: {.pub}", head, "[" + (p.get("venue") or "protocols.io") + "]{.pub-venue}"]
    if p.get("note"):
        out.append("[" + p["note"] + "]{.pub-authors}")
    out.append(":::")
    return "\n".join(out)


def build_protocols(data):
    items = data.get("protocols", [])
    body = [
        "---",
        'title: ""',
        'pagetitle: "Protocols"',
        'description: "Open lab protocols from Dr. Erika C. Freeman, released on protocols.io with citable DOIs: DOM sampling, PPL extraction, FT-ICR-MS, and AI-assisted annotation."',
        "format:",
        "  html:",
        "    toc: false",
        "    page-layout: full",
        "---",
        "",
        "<!-- GENERATED by scripts/build.py from data/protocols.yml — do not edit by hand. -->",
        "",
        "::: {.section-label}",
        "Protocols",
        ":::",
        "# protocols {.section-title}",
        "",
        data.get("intro", "").strip(),
        "",
        "::: {.pubs-cols}",
        "",
        '::: {.pubs-col style="grid-column: 1 / -1;"}',
        "",
    ]
    for status in PROTO_ORDER:
        grp = [p for p in items if p.get("status") == status]
        if not grp:
            continue
        body += ["::: {.group-label}", PROTO_LABEL[status], ":::", ""]
        for p in grp:
            body += [proto_entry(p), ""]
    body += [":::", "", ":::", ""]
    (ROOT / "protocols.qmd").write_text("\n".join(body), encoding="utf-8")


def cv_protocols_block(data):
    pub = [p for p in data.get("protocols", []) if p.get("status") == "published"]
    out = ["", "## Protocols", ""]
    if pub:
        for p in pub:
            doi = f" {p['doi']}" if p.get("doi") else ""
            out.append(f"- {p['title']}. *{p.get('venue', 'protocols.io')}*.{doi}")
        n_other = len(data.get("protocols", [])) - len(pub)
        if n_other:
            out.append(f"- Additional protocols in preparation for protocols.io ({n_other}).")
    else:
        out.append(data.get("cv_statement",
                   "Lab DOM protocols being published openly on protocols.io; DOIs added as released.").strip())
    return out


def main():
    pubs = load("publications.yml")
    cv = load("cv.yml")
    protocols = load("protocols.yml")
    first_all = pubs.get("first_author", [])
    contrib_all = pubs.get("contributing", [])
    # pack_only entries stay off the public Publications PAGE, but the CV lists
    # the full pipeline (in-progress / in-review / commentary work included).
    first_pub = [p for p in first_all if not p.get("pack_only")]
    contrib_pub = [p for p in contrib_all if not p.get("pack_only")]
    build_publications(first_pub, contrib_pub)
    build_protocols(protocols)
    build_cv(cv, first_all, contrib_all, protocols)
    print(f"[build] publications.qmd: {len(first_pub)} first-author, {len(contrib_pub)} contributing (public)")
    print(f"[build] protocols.qmd: {len(protocols.get('protocols', []))} protocols")
    print("[build] cv.qmd: html + typst")


if __name__ == "__main__":
    main()
