"""Render the link-preview image (docs/assets/social-card.png, 1200x630) that LinkedIn, Slack,
iMessage and the like show when someone shares the site. Rerun after changing the hero art,
the logo or the site description:
    .venv/bin/python scripts/make_social_card.py
Needs Playwright's Chromium (or PW_CHANNEL=chrome), like build_pdfs.py.
"""

import os
from pathlib import Path

from mkdocs.config import load_config
from playwright.sync_api import sync_playwright

from build_pdfs import cover_route

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "social-card.png"


def card_html(cfg):
    partials = ROOT / "overrides" / "partials"
    drawing = cover_route((partials / "hero-drawing.html").read_text())
    grid = (partials / "hero-grid.html").read_text()
    logo = (ROOT / "overrides" / ".icons" / "pf" / "mitsudomoe.svg").read_text()
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=JetBrains+Mono:wght@700&display=block">
<style>
* {{ box-sizing: border-box; margin: 0 }}
body {{ width: 1200px; height: 630px; overflow: hidden; position: relative; background: #1c2025;
       color: #eef0f3; font: 400 24px/1.45 "IBM Plex Sans", sans-serif }}
.art {{ position: absolute; inset: 0 }}
.art svg {{ position: absolute; inset: 0; width: 100%; height: 100% }}
.art::after {{ content: ""; position: absolute; inset: 0;
              background: linear-gradient(90deg, #1c2025 40%, rgba(28, 32, 37, 0) 66%) }}
.dot {{ fill: rgba(255, 255, 255, 0.07) }}
.link {{ fill: none; stroke: rgba(222, 228, 236, 0.38); stroke-width: 1.1 }}
.link.major {{ stroke-width: 2 }}
.node {{ fill: #9ea3ab }}
.signal {{ fill: none; stroke: #ff4f00; stroke-width: 3; stroke-linecap: round }}
.hop {{ fill: #ff4f00 }}
.text {{ position: absolute; left: 72px; top: 0; bottom: 0; width: 640px;
         display: flex; flex-direction: column; justify-content: center }}
.brand {{ display: flex; align-items: center; gap: 14px; margin-bottom: 40px; font-weight: 600; font-size: 22px }}
.brand svg {{ width: 34px; height: 34px; fill: #eef0f3 }}
h1 {{ font: 700 76px/1.05 "JetBrains Mono", monospace; letter-spacing: -0.04em }}
.kicker {{ margin: 18px 0 22px; color: #ff4f00; font-weight: 600; font-size: 20px;
           letter-spacing: 0.1em; text-transform: uppercase }}
.lede {{ max-width: 600px; color: rgba(238, 240, 243, 0.78); font-size: 21px }}
.url {{ position: absolute; left: 72px; bottom: 44px; color: rgba(238, 240, 243, 0.55); font-size: 20px }}
</style></head>
<body>
<div class="art">{grid}{drawing}</div>
<div class="text">
  <div class="brand">{logo}<span>{cfg.site_name}</span></div>
  <h1>{cfg.extra["author"]}</h1>
  <p class="kicker">Engineering Portfolio</p>
  <p class="lede">{cfg.site_description}</p>
</div>
<p class="url">{cfg.site_url.removeprefix("https://").rstrip("/")}</p>
</body></html>"""


if __name__ == "__main__":
    cfg = load_config(str(ROOT / "mkdocs.yml"))
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=os.environ.get("PW_CHANNEL") or None)
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        page.set_content(card_html(cfg), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(OUT), type="png")
        browser.close()
    print("wrote", OUT)
