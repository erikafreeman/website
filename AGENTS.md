# Working on this site (AI agents & collaborators)

**erikacfreeman.com** — a [Quarto](https://quarto.org) static site deployed to GitHub Pages.
Repo: github.com/erikafreeman/website. This file is read by Codex; Gemini CLI and others can be pointed at it too.

## Golden rule: one source of truth
- **Publications** → `data/publications.yml`. **CV content** → `data/cv.yml`.
- `scripts/build.py` (a Quarto `pre-render` hook) regenerates `publications.qmd`, `cv.qmd`, and the CV PDF from those YAMLs on every render.
- ⚠️ Do NOT hand-edit `publications.qmd` or `cv.qmd` — they are generated and overwritten. Edit the YAML.

## Where things live
| File | What |
|---|---|
| `index.qmd` | Homepage: hero + bio (hand-edited) |
| `projects.qmd`, `impact.qmd`, `contact.qmd` | Hand-edited pages |
| `custom.scss` | All design tokens & layout (palette, type, hero, grid) — edit here for styling |
| `_header.html` / `_footer.html` | Masthead + colophon injected on every page |
| `assets/` | Images (`portrait.jpg`, `projects/*.jpg`) |
| `data/*.yml` + `scripts/build.py` | Publications/CV source + generator |

## Build & preview
```bash
quarto preview     # local, auto-reload
quarto render      # build to _site/ (runs scripts/build.py first)
```
Needs Quarto (bundles Typst) + Python 3 with `pyyaml`.

## Deploy
GitHub Pages serves the **`gh-pages`** branch (rendered `_site/` only). The Action in
`.github/workflows/publish.yml` deploys on push to `main` *if* the pusher's token has the
`workflow` scope. Otherwise deploy manually from a COPY of `_site` (never `git init` inside the
source repo):
```bash
quarto render
cp -r _site /tmp/ghp && cd /tmp/ghp && touch .nojekyll
git init -b gh-pages && git add -A && git commit -m deploy
git push -f https://github.com/erikafreeman/website.git HEAD:gh-pages
```

## Multi-agent etiquette
- Work on a branch, open a PR. Keep the YAML data files as the single source of truth.
- `_site/` is gitignored on `main`; don't commit build output there.
- Match the existing voice: warm, direct, **no em-dashes**.
