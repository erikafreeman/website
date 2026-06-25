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


def _norm_author(tok):
    """Normalise an author token to 'Surname I' (or a single name); skip consortia/et al."""
    import re
    t = tok.replace("**", "").replace("*", "").strip().lstrip("& ").strip()
    low = t.lower()
    if not t or "consortium" in low or "whondrs" in low or low.startswith("et al") or low in ("others", "and others"):
        return None
    t = re.sub(r"\bet al\.?", "", t, flags=re.I)
    t = re.sub(r"\b\d{4}\b", "", t).strip().strip(",").strip()
    if not t or t.lower() == "others":
        return None
    words = t.split()
    if len(words) >= 2 and re.fullmatch(r"[A-Z]{1,4}", words[-1]):
        return " ".join(words[:-1]) + " " + words[-1][0]
    return t


def _paper_authors(p, kind):
    raw = (p.get("coauthors") if kind == "first" else p.get("authors")) or ""
    names = {"Freeman E"}  # her own publication list — she is on every paper
    for tok in raw.split(","):
        nm = _norm_author(tok)
        if nm:
            names.add(nm)
    return names


def build_graph(first, contrib):
    """Co-authorship graph: node weight = papers; edge weight = shared papers."""
    from collections import defaultdict
    node_w, edges = defaultdict(int), defaultdict(int)
    papers = 0
    for entries, kind in ((first, "first"), (contrib, "contrib")):
        for p in entries:
            a = sorted(_paper_authors(p, kind))
            if not a:
                continue
            papers += 1
            for nm in a:
                node_w[nm] += 1
            for i in range(len(a)):
                for j in range(i + 1, len(a)):
                    edges[(a[i], a[j])] += 1
    return dict(node_w), dict(edges), papers


def force_layout(node_w, edges, W=860, H=620, iters=320):
    """Deterministic Fruchterman-Reingold layout; Erika pinned at centre."""
    import math
    nodes = list(node_w)
    n = len(nodes) or 1
    k = math.sqrt((W * H) / n) * 0.55
    cx, cy = W / 2, H / 2
    pos = {}
    for i, nd in enumerate(nodes):
        a = 2 * math.pi * i / n
        pos[nd] = [cx + W * 0.30 * math.cos(a), cy + H * 0.30 * math.sin(a)]
    if "Freeman E" in pos:
        pos["Freeman E"] = [cx, cy]
    adj = {}
    for (a, b), w in edges.items():
        adj.setdefault(a, {})[b] = w
        adj.setdefault(b, {})[a] = w
    t = W / 9.0
    for _ in range(iters):
        disp = {nd: [0.0, 0.0] for nd in nodes}
        for i in range(n):
            a = nodes[i]
            for j in range(i + 1, n):
                b = nodes[j]
                dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
                d = math.hypot(dx, dy) or 0.01
                f = k * k / d
                ux, uy = dx / d, dy / d
                disp[a][0] += ux * f; disp[a][1] += uy * f
                disp[b][0] -= ux * f; disp[b][1] -= uy * f
        for a, nbrs in adj.items():
            for b, w in nbrs.items():
                if a < b:
                    dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
                    d = math.hypot(dx, dy) or 0.01
                    f = (d * d / k) * (1 + 0.25 * (w - 1))
                    ux, uy = dx / d, dy / d
                    disp[a][0] -= ux * f; disp[a][1] -= uy * f
                    disp[b][0] += ux * f; disp[b][1] += uy * f
        for nd in nodes:
            if nd == "Freeman E":
                continue
            dx, dy = disp[nd]
            d = math.hypot(dx, dy) or 0.01
            step = min(d, t)
            pos[nd][0] = min(W - 34, max(34, pos[nd][0] + dx / d * step))
            pos[nd][1] = min(H - 24, max(24, pos[nd][1] + dy / d * step))
        t *= 0.97
    return pos


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def collab_svg(node_w, edges, pos, W=860, H=620):
    import math
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="collab-svg" role="img" aria-label="Co-author collaboration network">']
    for (a, b), w in edges.items():
        if a not in pos or b not in pos:
            continue
        op = min(0.5, 0.10 + 0.07 * w)
        s.append(f'<line x1="{pos[a][0]:.1f}" y1="{pos[a][1]:.1f}" x2="{pos[b][0]:.1f}" y2="{pos[b][1]:.1f}" stroke="#5d6b4e" stroke-width="{0.5 + 0.45 * w:.2f}" opacity="{op:.2f}"/>')
    labels = []
    for nd, c in node_w.items():
        x, y = pos[nd]
        is_e = nd == "Freeman E"
        r = max(11.0, 5 + 2.6 * math.sqrt(c)) if is_e else 4 + 2.3 * math.sqrt(c)
        fill = "#aecb86" if is_e else "#7d9466"
        nm = "Erika Freeman" if is_e else nd
        plural = "s" if c != 1 else ""
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="#11160f" stroke-width="1.2"><title>{_esc(nm)} — {c} paper{plural}</title></circle>')
        if is_e or c >= 2:
            lab = "Erika Freeman" if is_e else nd.rsplit(" ", 1)[0]
            labels.append((x + r + 3, y + 3.5, lab, is_e))
    for x, y, lab, is_e in labels:
        s.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{12 if is_e else 10.5}" fill="{"#e8efe0" if is_e else "#b9c4aa"}" font-family="Inter,sans-serif" font-weight="{600 if is_e else 400}">{_esc(lab)}</text>')
    s.append("</svg>")
    return "".join(s)


def build_collaborations(node_w, edges, pos, papers):
    n_co = len(node_w) - (1 if "Freeman E" in node_w else 0)
    svg = collab_svg(node_w, edges, pos)
    body = [
        "---",
        'title: ""',
        'pagetitle: "Collaboration network"',
        'description: "The co-author network behind Dr. Erika C. Freeman\'s publications — every collaborator, linked when they share a paper."',
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
        "# collaboration network {.section-title}",
        "",
        f"The people behind the papers: every co-author Erika has published with, linked whenever they share a paper. **{n_co} co-authors across {papers} works.** Node size scales with shared papers; clusters are research communities. Hover a node for the name.",
        "",
        "::: {.collab-figure}",
        "",
        "```{=html}",
        svg,
        "```",
        "",
        ":::",
        "",
        "::: {.personal-link}",
        "Affiliations aren't in the publication metadata, so this maps people, not institutions. [← Back to publications](publications.html)",
        ":::",
        "",
    ]
    (ROOT / "collaborations.qmd").write_text("\n".join(body), encoding="utf-8")


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
