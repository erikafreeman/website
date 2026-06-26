#!/usr/bin/env python3
"""Post-render: inject a <link rel="canonical"> into every built HTML page,
pointing at the production domain (site-url). Quarto does not emit canonical
tags itself. Runs after `quarto render` (see `post-render` in _quarto.yml)."""

import pathlib

SITE = pathlib.Path(__file__).resolve().parent.parent / "_site"
# Canonical points at the live site. While DNS still shows the old Canva page at
# erikacfreeman.com, point canonicals at the GitHub Pages URL so search engines
# index the current content. Switch back to https://erikacfreeman.com once DNS flips.
BASE = "https://erikafreeman.github.io/website"


def main():
    if not SITE.exists():
        return
    n = 0
    for p in SITE.rglob("*.html"):
        rel = p.relative_to(SITE).as_posix()
        url = BASE + "/" + ("" if rel == "index.html" else rel)
        html = p.read_text(encoding="utf-8")
        if 'rel="canonical"' in html or "</head>" not in html:
            continue
        html = html.replace("</head>", f'  <link rel="canonical" href="{url}">\n</head>', 1)
        p.write_text(html, encoding="utf-8")
        n += 1
    print(f"[postprocess] canonical added to {n} pages")


if __name__ == "__main__":
    main()
