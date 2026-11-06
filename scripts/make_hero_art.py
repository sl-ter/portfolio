"""Generate the home-page hero art as inline-SVG Jinja partials.

Writes overrides/partials/hero-grid.html (a dot grid) and overrides/partials/hero-drawing.html:
a decentralised network (hubs with clusters, a backbone, cross-links) that fades out at its edges,
with stubs reaching into the fade. Run after changing the network:
    .venv/bin/python scripts/make_hero_art.py

Nodes pop in and links grow (`pop`, `grow`, each with its own --d delay) to stage the build-up;
the svg's data-intro says when it ends. Links carry data-a/data-b (indexes into the node list;
stubs carry only data-a) and routable nodes carry data-core, so site.js can loop signal routes
over the network. Colours come from extra.css, so the art follows light/dark mode.
"""

from math import atan2, cos, pi, sin
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "overrides" / "partials"
W, H = 1600, 900


def svg(cls, body, align="xMaxYMid", attrs=""):
    return (
        f'<svg class="{cls}" viewBox="0 0 {W} {H}" preserveAspectRatio="{align} slice" '
        f'aria-hidden="true"{attrs}>\n' + "\n".join(body) + "\n</svg>\n"
    )


def line(a, b, cls, attrs=""):
    """A link as a path with pathLength=1, so CSS can draw it in with a dash offset."""
    return (f'<path class="{cls}" pathLength="1" d="M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}" '
            f'{attrs}/>')


def dot_grid():
    body = [
        '<defs><pattern id="pf-dots" width="20" height="20" patternUnits="userSpaceOnUse">'
        '<circle class="dot" cx="10" cy="10" r="1.2"/></pattern></defs>',
        f'<rect width="{W}" height="{H}" fill="url(#pf-dots)"/>',
    ]
    return svg("pf-hero__grid", body, "xMidYMid")


def network(seed=7):
    """Decentralised network: a dozen hubs, each with its own cluster of satellites (some of them
    sub-hubs with leaves), a heavier hub-to-hub backbone, and lighter cross-links between
    clusters. It runs past the visible area and fades out under an elliptical mask, with stub
    links reaching off into the fade, so it reads as part of a larger network."""
    import random

    rng = random.Random(seed)
    CX, CY, RX, RY = 1250, 450, 570, 430           # visible core: the mask's ellipse
    bx0, by0, bx1, by1 = 700, -40, 1800, 940       # where nodes may go (beyond the viewBox)
    rho = lambda x, y: (((x - CX) / RX) ** 2 + ((y - CY) / RY) ** 2) ** 0.5

    nodes, kind, parent = [], [], []               # (x, y, r); "hub" | "sub" | "leaf"

    def free(x, y, gap):
        return bx0 <= x <= bx1 and by0 <= y <= by1 and rho(x, y) < 1.12 and \
            all((x - a) ** 2 + (y - b) ** 2 >= gap ** 2 for a, b, _ in nodes)

    # Hubs: dart-throwing with a generous spacing, so clusters have room and spacing varies
    for _ in range(4000):
        x, y = rng.uniform(bx0, bx1), rng.uniform(by0, by1)
        if free(x, y, 225):
            nodes.append((x, y, round(rng.uniform(11.5, 16.5), 1))); kind.append("hub"); parent.append(None)
    hubs = list(range(len(nodes)))

    def scatter(around, count, dmin, dmax, gap, rmin, rmax, k):
        made = []
        ax, ay, _ = nodes[around]
        for _ in range(count):
            for _ in range(60):
                t, d = rng.uniform(0, 2 * pi), rng.uniform(dmin, dmax)
                x, y = ax + d * cos(t), ay + d * sin(t)
                if free(x, y, gap):
                    nodes.append((x, y, round(rng.uniform(rmin, rmax), 1))); kind.append(k); parent.append(around)
                    made.append(len(nodes) - 1)
                    break
        return made

    for h in hubs:
        for sat in scatter(h, rng.randint(3, 7), 62, 168, 46, 3.5, 7.5, "leaf"):
            if rng.random() < 0.3:                     # promote to a sub-hub with its own leaves
                x, y, _ = nodes[sat]
                nodes[sat] = (x, y, round(rng.uniform(8, 10.5), 1)); kind[sat] = "sub"
                scatter(sat, rng.randint(1, 3), 45, 100, 38, 3, 5, "leaf")

    n = len(nodes)
    dist = lambda a, b: ((nodes[a][0] - nodes[b][0]) ** 2 + (nodes[a][1] - nodes[b][1]) ** 2) ** 0.5
    links = {}                                         # (a, b) -> "major" | ""

    def link(a, b, weight=""):
        if a != b:
            links.setdefault((min(a, b), max(a, b)), weight)

    # Backbone: Gabriel graph among hubs
    for i, a in enumerate(hubs):
        for b in hubs[i + 1:]:
            if dist(a, b) > 470:
                continue
            mx, my = (nodes[a][0] + nodes[b][0]) / 2, (nodes[a][1] + nodes[b][1]) / 2
            if all((nodes[c][0] - mx) ** 2 + (nodes[c][1] - my) ** 2 >= (dist(a, b) / 2) ** 2
                   for c in hubs if c not in (a, b)):
                link(a, b, "major")
    # Spokes, then cross-links: each non-hub sometimes also reaches its nearest outside node
    for i in range(n):
        if parent[i] is not None:
            link(i, parent[i])
    for i in range(n):
        if kind[i] == "hub":
            continue
        others = sorted((j for j in range(n) if j != i and j != parent[i]), key=lambda j: dist(i, j))
        if rng.random() < 0.45 and dist(i, others[0]) < 155:
            link(i, others[0])
        near_hub = min((h for h in hubs if h != parent[i]), key=lambda h: dist(i, h))
        if rng.random() < 0.25 and dist(i, near_hub) < 210:
            link(i, near_hub)

    # Stubs: outer nodes reach off into the fade, implying more network beyond
    stubs = []
    for i, (x, y, _) in enumerate(nodes):
        if rho(x, y) > 0.7:
            for _ in range(rng.choice((1, 1, 2))):
                base = atan2((y - CY) / RY, (x - CX) / RX)
                t, length = base + rng.uniform(-0.7, 0.7), rng.uniform(100, 250)
                stubs.append((i, x + length * cos(t), y + length * sin(t)))

    # Build-up timeline: nodes pop in random order; links and stubs grow once their nodes exist
    order = list(range(n)); rng.shuffle(order)
    pop = {node: 0.15 + 1.2 * k / n for k, node in enumerate(order)}
    link_t, intro = 0.45, 0
    # Routable nodes: everything still visible through the fade, so routes reach the outer edges
    core = lambda i: rho(nodes[i][0], nodes[i][1]) < 0.9 and nodes[i][1] < 800

    d = [f'''<defs>
<radialGradient id="pf-net-fade-grad" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="{RX}"
  gradientTransform="translate({CX} {CY}) scale(1 {RY / RX:.3f}) translate({-CX} {-CY})">
<stop offset="0.5" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<mask id="pf-net-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
<rect width="{W}" height="{H}" fill="url(#pf-net-fade-grad)"/></mask>
</defs>''', '<g mask="url(#pf-net-fade)">', '<g class="net-links">']
    for (a, b), weight in sorted(links.items()):
        new, old = (a, b) if pop[a] >= pop[b] else (b, a)
        start = pop[new] + 0.12
        intro = max(intro, start + link_t)
        cls = "link major grow" if weight else "link grow"
        d.append(line(nodes[new], nodes[old], cls, f'data-a="{a}" data-b="{b}" style="--d: {start:.2f}s; --t: {link_t}s"'))
    for i, x, y in stubs:
        d.append(line(nodes[i], (x, y), "link stub grow", f'data-a="{i}" style="--d: {pop[i] + 0.15:.2f}s; --t: 0.6s"'))
    d.append('</g>')
    d.append('<g class="net-nodes">')
    for i, (x, y, r) in enumerate(nodes):
        flag = ' data-core=""' if core(i) else ""
        d.append(f'<circle class="node {kind[i]} pop" cx="{x:.1f}" cy="{y:.1f}" r="{r}"{flag} '
                 f'style="--d: {pop[i]:.2f}s"/>')
    d.append('</g>')
    # site.js draws the looping routes and lights their nodes here, inside the mask, so routes
    # that reach the outer nodes (or run off along a stub) fade out with the network
    d.append('<g class="net-signal"></g>')
    d.append('<g class="net-hops"></g>')
    d.append('</g>')
    return svg("pf-hero__drawing", d, attrs=f' data-intro="{intro:.2f}"')


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hero-grid.html").write_text(dot_grid())
    (OUT / "hero-drawing.html").write_text(network())
    print("wrote", OUT / "hero-grid.html", OUT / "hero-drawing.html")
