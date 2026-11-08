"""Render the site to PDFs for the "Portfolio as a PDF" builder.

Run after `mkdocs build`. Prints each page the builder offers (About, Resume, every project,
Certificates) from site/ with headless Chromium, renders a cover, and writes them all with a
manifest to site/pdf/. The builder page (docs/javascripts/pdf-builder.js) merges whichever ones
a visitor ticks, adding the contents page, page numbers and bookmarks.
    .venv/bin/python scripts/build_pdfs.py
Needs Playwright's Chromium (`playwright install chromium`); set PW_CHANNEL=chrome to print
with an installed Google Chrome instead.

Front matter it reads:
  deep_dives: [a.md, b.md]  a project's deep dives; the builder then offers Summary or Full
  pdf: false                leave the page out of the builder
  pdf: assets/resume.pdf    offer this file (relative to docs/) instead of printing the page
Videos and <model-viewer> CAD print as their poster image, with a link back to the page.
"""

import functools
import http.server
import json
import os
import random
import re
import shutil
import threading
from collections import deque
from datetime import date
from pathlib import Path

from mkdocs.config import load_config
from mkdocs.utils.meta import get_data
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS, SITE = ROOT / "docs", ROOT / "site"
OUT = SITE / "pdf"

# What the builder offers, in order. Projects come from the nav's Projects section (pages whose
# front matter has a duration).
GROUPS = [("About me", ["about.md", "resume.md"]), ("Projects", None), ("Certificates", ["certificates.md"])]


def page_url(src):
    """docs-relative source path -> site-relative URL (use_directory_urls)."""
    if src.endswith("index.md"):
        return src[: -len("index.md")]
    return src[: -len(".md")] + "/"


def front_matter(src):
    return get_data((DOCS / src).read_text())[1]


def nav_titles(nav, out=None):
    """Flatten the nav into {source path: nav title}."""
    out = {} if out is None else out
    for entry in nav:
        if isinstance(entry, dict):
            for title, value in entry.items():
                if isinstance(value, list):
                    nav_titles(value, out)
                else:
                    out[value] = title
    return out


def project_sources(nav):
    section = next(v for e in nav if isinstance(e, dict) for k, v in e.items() if k == "Projects")
    srcs = [e if isinstance(e, str) else next(iter(e.values())) for e in section]
    return [s for s in srcs if "duration" in front_matter(s)]


def count_pages(pdf):
    """Pages in a Chromium-printed PDF (it writes plain, uncompressed page dictionaries)."""
    return len(re.findall(rb"/Type\s*/Page(?![a-z])", pdf))


def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=directory))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


# Printed links would otherwise point at the local server: send them to the published site
RETARGET_LINKS = """site => {
  for (const a of document.querySelectorAll("a[href]"))
    if (a.href.startsWith(location.origin)) a.href = site + a.href.slice(location.origin.length + 1)
}"""


# Videos and 3D models can't go on paper: swap each one that has a poster for that still, with
# a note linking back to the page. Ones without a poster are hidden by print.css.
POSTER_STILLS = """async () => {
  const stills = []
  for (const media of document.querySelectorAll("video[poster], model-viewer[poster]")) {
    const kind = media.tagName === "VIDEO" ? "Video" : "Interactive 3D model"
    const img = Object.assign(document.createElement("img"), {
      src: new URL(media.getAttribute("poster"), location.href).href,
      alt: media.getAttribute("alt") || kind,
    })
    const note = Object.assign(document.createElement("a"), { href: location.href, textContent: `${kind} on the web version` })
    const still = Object.assign(document.createElement("span"), { className: "pf-still" })
    still.append(img, note)
    media.replaceWith(still)
    stills.push(img.decode().catch(() => {}))
  }
  await Promise.all(stills)
}"""


def print_page(page, base, src, site_url):
    page.goto(base + page_url(src), wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.evaluate(POSTER_STILLS)
    page.evaluate(RETARGET_LINKS, site_url)
    return page.pdf(format="Letter", print_background=True, prefer_css_page_size=True)


# ---------------------------------------------------------------- cover

def cover_route(drawing, hops=5, seed=3):
    """Light one route across the hero network for the cover, as site.js does on the home page."""
    core = [bool(m.group(1)) for m in re.finditer(r'<circle class="node[^>]*?( data-core="")?\s+style', drawing)]
    xy = [(float(x), float(y), float(r)) for x, y, r in
          re.findall(r'<circle class="node[^"]*" cx="([-\d.]+)" cy="([-\d.]+)" r="([\d.]+)"', drawing)]
    adj = {i: [] for i in range(len(xy))}
    for a, b in re.findall(r'data-a="(\d+)" data-b="(\d+)"', drawing):
        a, b = int(a), int(b)
        if core[a] and core[b]:
            adj[a].append(b)
            adj[b].append(a)
    rng = random.Random(seed)
    route = []
    for _ in range(50):
        src = rng.choice([i for i in adj if adj[i]])
        prev, depth, queue = {src: None}, {src: 0}, deque([src])
        while queue:
            u = queue.popleft()
            for v in sorted(adj[u], key=lambda _: rng.random()):
                if v not in prev:
                    prev[v], depth[v] = u, depth[u] + 1
                    queue.append(v)
        far = [v for v in depth if depth[v] == hops]
        if far:
            v = rng.choice(far)
            while v is not None:
                route.append(v)
                v = prev[v]
            break
    lines = "".join(f'<path class="signal" d="M{xy[a][0]},{xy[a][1]}L{xy[b][0]},{xy[b][1]}"/>'
                    for a, b in zip(route, route[1:]))
    dots = "".join(f'<circle class="hop" cx="{xy[i][0]}" cy="{xy[i][1]}" r="{xy[i][2] + 1.5}"/>' for i in route)
    return (drawing.replace('<g class="net-signal"></g>', f'<g class="net-signal">{lines}</g>')
                   .replace('<g class="net-hops"></g>', f'<g class="net-hops">{dots}</g>'))


def cover_html(cfg, built):
    partials = ROOT / "overrides" / "partials"
    drawing = cover_route((partials / "hero-drawing.html").read_text())
    grid = (partials / "hero-grid.html").read_text()
    logo = (ROOT / "overrides" / ".icons" / "pf" / "mitsudomoe.svg").read_text()
    contacts = [s for s in cfg.extra.get("social", []) if s.get("name")]
    contact_links = "".join(f'<a href="{s["link"]}">{s["name"]}</a>' for s in contacts)
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@600&display=block">
<style>
@page {{ size: Letter; margin: 0 }}
* {{ box-sizing: border-box; margin: 0; padding: 0 }}
html, body {{ width: 8.5in; height: 11in }}
body {{ position: relative; overflow: hidden; background: #fff; color: #1d2026;
       font: 400 11pt/1.5 "IBM Plex Sans", sans-serif; -webkit-print-color-adjust: exact }}
.art {{ position: absolute; left: 0; right: 0; top: 4.4in; height: 5.2in }}
.art svg {{ position: absolute; inset: 0; width: 100%; height: 100% }}
.pf-hero__grid .dot {{ fill: #c9ccd1 }}
.link {{ fill: none; stroke: #9aa0a8; stroke-width: 1.1 }}
.link.major {{ stroke-width: 2 }}
.node {{ fill: #5d636b }}
.signal {{ fill: none; stroke: #ff4f00; stroke-width: 3; stroke-linecap: round }}
.hop {{ fill: #ff4f00 }}
.fade {{ position: absolute; left: 0; right: 0; top: 4.4in; height: 1.2in;
         background: linear-gradient(#fff, rgba(255,255,255,0)) }}
.fade.bottom {{ top: 8.4in; background: linear-gradient(rgba(255,255,255,0), #fff) }}
header {{ position: absolute; top: 0.75in; left: 0.75in; right: 0.75in;
          display: flex; align-items: center; gap: 10pt; font-weight: 600; font-size: 10.5pt }}
header svg {{ width: 18pt; height: 18pt; fill: #1d2026 }}
header .rule {{ flex: 1; height: 1px; background: #d5d8dd }}
header .tag {{ color: #6b7079; font-weight: 400 }}
h1 {{ position: absolute; top: 1.85in; left: 0.75in; font: 600 46pt/1 "IBM Plex Sans Condensed", sans-serif;
      letter-spacing: -0.01em }}
.kicker {{ position: absolute; top: 2.75in; left: 0.75in; color: #ff4f00; font-weight: 600;
           font-size: 12pt; letter-spacing: 0.08em; text-transform: uppercase }}
.lede {{ position: absolute; top: 3.2in; left: 0.75in; width: 5.6in; color: #3c4048; font-size: 12pt }}
footer {{ position: absolute; left: 0.75in; right: 0.75in; bottom: 0.75in;
          display: flex; justify-content: space-between; align-items: flex-end; font-size: 9.5pt }}
footer a {{ color: #b83a00; font-weight: 600; text-decoration: none }}
footer .contacts {{ display: flex; gap: 0.3in }}
footer .site {{ text-align: right; color: #6b7079 }}
footer .site a {{ display: block }}
</style></head>
<body>
<div class="art">{grid}{drawing}</div><div class="fade"></div><div class="fade bottom"></div>
<header>{logo}<span>{cfg.site_name}</span><span class="rule"></span><span class="tag">{built:%B %Y}</span></header>
<h1>{cfg.extra["author"]}</h1>
<p class="kicker">Engineering Portfolio</p>
<p class="lede">{cfg.site_description}</p>
<footer><p class="contacts">{contact_links}</p>
<p class="site">The full portfolio, with video and interactive models<a href="{cfg.site_url}">View it online</a></p></footer>
</body></html>"""


# ---------------------------------------------------------------- main

def main():
    cfg = load_config(str(ROOT / "mkdocs.yml"))
    site_url = cfg.site_url.rstrip("/") + "/"
    titles = nav_titles(cfg.nav)
    built = date.today()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    server, base = serve(SITE)
    groups = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=os.environ.get("PW_CHANNEL") or None)
        page = browser.new_page(color_scheme="light", reduced_motion="reduce")

        def render(src, name):
            """PDF for one page (or the file its front matter points at) -> {file, pages}."""
            meta = front_matter(src)
            if isinstance(meta.get("pdf"), str):
                pdf = (DOCS / meta["pdf"]).read_bytes()
            else:
                pdf = print_page(page, base, src, site_url)
            (OUT / name).write_bytes(pdf)
            return {"file": name, "pages": count_pages(pdf)}

        for title, srcs in GROUPS:
            items = []
            for src in srcs or project_sources(cfg.nav):
                meta = front_matter(src)
                if meta.get("pdf") is False:
                    continue
                slug = page_url(src).strip("/").split("/")[-1]
                summary = render(src, f"{slug}.pdf")
                item = {
                    "id": slug,
                    "title": meta.get("title") or titles.get(src, slug),
                    "url": site_url + page_url(src),
                    "duration": meta.get("duration"),
                    "variants": {"summary": {"files": [summary["file"]], "pages": summary["pages"]}},
                }
                dives = [str(Path(src).parent / d) for d in meta.get("deep_dives") or []]
                if dives:
                    parts = [summary] + [render(d, f"{slug}--{Path(d).stem}.pdf") for d in dives]
                    item["variants"]["full"] = {"files": [x["file"] for x in parts],
                                                "pages": sum(x["pages"] for x in parts)}
                items.append(item)
                pages = ", ".join(f"{k} {v['pages']} pp" for k, v in item["variants"].items())
                print(f"  {item['title']}: {pages}")
            if items:
                groups.append({"title": title, "items": items})

        page.set_content(cover_html(cfg, built), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        cover = page.pdf(prefer_css_page_size=True, print_background=True)
        (OUT / "cover.pdf").write_bytes(cover)
        browser.close()
    server.shutdown()

    manifest = {
        "author": cfg.extra["author"],
        "title": "Engineering Portfolio",
        "site_url": site_url,
        "built": built.isoformat(),
        "cover": {"file": "cover.pdf", "pages": count_pages(cover)},
        "groups": groups,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print("wrote", OUT / "manifest.json")


if __name__ == "__main__":
    main()
