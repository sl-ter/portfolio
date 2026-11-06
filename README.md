# Engineering Portfolio

Source for https://sl-ter.github.io/portfolio/ — Material for MkDocs, deployed to GitHub Pages
by `.github/workflows/deploy.yml` on every push to `main`.

## Local preview

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve        # http://127.0.0.1:8000/portfolio/
```

## Adding a project

1. Copy `templates/project-summary.md` to `docs/projects/<slug>/index.md`.
2. Put images in `docs/projects/<slug>/img/`. Keep photos under ~300 KB.
3. Add the page to `nav` in `mkdocs.yml`. Nav order is the site and PDF-builder order.
4. Run `.venv/bin/mkdocs build --strict` before pushing.

Front matter `skills` render as chips in the project header. Front matter and sections mirror the
vault intake notes (`Portfolio - <Project>.md`).
Wrap anything that shouldn't appear in the PDF (video, 3D viewers) in `<div class="web-only" markdown>`.

## Design

- `overrides/home.html`: landing page. Its project spotlights and cards are built from each project's
  front matter in nav order; the affiliation spotlights come from `extra.affiliations` in mkdocs.yml.
- `overrides/main.html`: renders the project header (hero, title, tagline, duration, role, skill chips)
  for any page whose front matter has `duration`.
- `scripts/make_hero_art.py`: regenerates the hero linework (`overrides/partials/hero-*.html`).
  Two drawings: `pcb` (default) and `flange`; switch with `ART` at the top of the script.
- Hero parallax: CSS scroll-driven animations in `extra.css` (compositor-smooth, like Material's own
  landing page). `docs/javascripts/site.js` adds site-wide damped scrolling via Lenis (pinned on
  jsDelivr in `mkdocs.yml`; tune `lerp`), a parallax fallback for browsers without scroll-driven
  animations, and smooth in-page jumps (TOC, footnotes, back-to-top).
- Palette: graphite + international orange (`docs/stylesheets/extra.css` tokens). Type: IBM Plex Sans,
  headlines in IBM Plex Sans Condensed.
