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

Front matter `skills` render as chips and feed the Skills page. Front matter and sections mirror the
vault intake notes (`Portfolio - <Project>.md`).
Wrap anything that shouldn't appear in the PDF (video, 3D viewers) in `<div class="web-only" markdown>`.
