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
## Media

`scripts/compress_media.sh <slug> <file>... [--mute]` shrinks photos (max 1800 px JPEG) and clips
(720p H.264 + poster) into `docs/projects/<slug>/img/` and prints the Markdown to paste. Snippets for
video, silent loops and CAD (`<model-viewer>`, GLB + iso-render poster) are in the template.

- In the PDF, every `<video>` or `<model-viewer>` with a `poster` prints as that image with a
  "on the web version" link (`build_pdfs.py`); ones without a poster are left out.
- `site.js` loads model-viewer (pinned on jsDelivr) only on pages that use it, and keeps looping
  clips still for visitors who prefer reduced motion. It also works around Material's instant
  navigation leaving viewers without a `src` (see `loadModelViewer`).
- For anything else that should differ between web and PDF: `<div class="web-only" markdown>` and
  `<div class="print-only" markdown>`.

## Portfolio as a PDF

Visitors tick sections on `pdf-builder.md` and download one merged PDF.

- `scripts/build_pdfs.py` (runs in CI after `mkdocs build`) prints About, Resume, every project and
  Certificates from `site/` with headless Chromium, renders a cover (the hero network with one route
  lit), and writes them with `manifest.json` to `site/pdf/`. Print layout: `docs/stylesheets/print.css`.
- `docs/javascripts/pdf-builder.js` builds the checklist from the manifest and merges the ticked PDFs
  in the browser with pdf-lib: cover, linked contents page, page numbers, bookmarks.
- Front matter: `deep_dives: [x.md]` lets a project go in as Summary or Full; `pdf: false` leaves a
  page out; `pdf: assets/resume.pdf` offers that file instead of printing the page.
- Try it locally (the builder needs the generated PDFs, so `mkdocs serve` alone shows a notice):

  ```sh
  .venv/bin/pip install -r requirements-pdf.txt && .venv/bin/playwright install chromium
  .venv/bin/mkdocs build && .venv/bin/python scripts/build_pdfs.py
  python3 -m http.server -d site 8001   # http://127.0.0.1:8001/pdf-builder/
  ```

## Design

- `overrides/home.html`: landing page. Its project spotlights and cards are built from each project's
  front matter in nav order; the affiliation spotlights come from `extra.affiliations` in mkdocs.yml.
- `overrides/main.html`: renders the project header (hero, title, tagline, duration, role, skill chips)
  for any page whose front matter has `duration`.
- `scripts/make_hero_art.py`: regenerates the hero network (`overrides/partials/hero-*.html`), a
  decentralised hubs-and-clusters network that builds itself and fades out at its edges; `site.js`
  then loops orange signal routes across it. (Earlier PCB and flange drawings are in git history.)
- `scripts/make_logo.py`: regenerates the mitsudomoe header mark and favicon. Needs `shapely` in the
  venv (`.venv/bin/pip install shapely`); the site build doesn't. The mark turns with the scroll.
- Header: `site_name` ("Personal Portfolio") labels the bar; tab titles use `extra.author`.
  The bar is graphite in dark mode and light grey in light mode (`extra.css`).
- Hero parallax: CSS scroll-driven animations in `extra.css` (compositor-smooth, like Material's own
  landing page). `docs/javascripts/site.js` adds site-wide damped scrolling via Lenis (pinned on
  jsDelivr in `mkdocs.yml`; tune `lerp`), a parallax fallback for browsers without scroll-driven
  animations, and smooth in-page jumps (TOC, footnotes, back-to-top).
- Palette: graphite + international orange (`docs/stylesheets/extra.css` tokens). Type: IBM Plex Sans,
  headlines in IBM Plex Sans Condensed, the name on the home page in JetBrains Mono.
- Deploys stamp `?v=<commit>` onto our own CSS/JS URLs (see `deploy.yml`), so browsers never mix
  fresh pages with a cached older `site.js` or `extra.css`.
