"""Generate the home-page hero linework as inline-SVG Jinja partials.

Writes overrides/partials/hero-grid.html and overrides/partials/hero-drawing.html.
Two drawings are available; pick one with ART below, then run:
    .venv/bin/python scripts/make_hero_art.py

  network — a decentralised network (hubs with clusters, a backbone, cross-links) that fades
            out at its edges with stubs into the fade; nodes pop in and links grow, then site.js
            loops random signal routes across it (the accent), on a dot grid
  pcb    — a board layout: MCU fanning traces out to flash, resistors, crystal, vias and a
           JTAG header (the TCK line is the accent), on a dot grid
  flange — a dimensioned flange drawing (bolt circle, centre lines, A–A cut), on a line grid

Classes: `draw` strokes draw themselves in on load; everything else fades in after. The network
times each element itself (`pop`, `grow` with --d delays) to stage its build-up, and tags links
(data-a, data-b, indexes into the node list; stubs carry only data-a) and the nodes routes may
use (data-core) so site.js can route signals over them; the svg's data-intro says when the build-up ends.
Colours come from CSS (docs/stylesheets/extra.css), so both drawings follow light/dark mode.
"""

from math import atan2, cos, pi, radians, sin
from pathlib import Path

ART = "network"

OUT = Path(__file__).resolve().parent.parent / "overrides" / "partials"
W, H = 1600, 900


def svg(cls, body, align="xMaxYMid", attrs=""):
    return (
        f'<svg class="{cls}" viewBox="0 0 {W} {H}" preserveAspectRatio="{align} slice" '
        f'aria-hidden="true"{attrs}>\n' + "\n".join(body) + "\n</svg>\n"
    )


def path(points, cls, chamfer=0):
    """Polyline as a path; orthogonal corners are cut at 45° by `chamfer` (PCB-style routing)."""
    pts = [points[0]]
    for (x0, y0), (x1, y1), (x2, y2) in zip(points, points[1:], points[2:]):
        if chamfer:
            ux, uy = _unit(x1 - x0, y1 - y0)
            vx, vy = _unit(x2 - x1, y2 - y1)
            pts += [(x1 - ux * chamfer, y1 - uy * chamfer), (x1 + vx * chamfer, y1 + vy * chamfer)]
        else:
            pts.append((x1, y1))
    pts.append(points[-1])
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<path class="{cls}" pathLength="1" d="{d}"/>'


def _unit(dx, dy):
    n = (dx * dx + dy * dy) ** 0.5
    return dx / n, dy / n


def arrow(x, y, angle_deg, size=14, cls="head"):
    """Filled arrowhead with its tip at (x, y), pointing along angle_deg."""
    a = radians(angle_deg)
    bx, by = x - size * cos(a), y - size * sin(a)
    px, py = -sin(a) * size * 0.28, cos(a) * size * 0.28
    return f'<path class="{cls}" d="M{x:.1f},{y:.1f} L{bx + px:.1f},{by + py:.1f} L{bx - px:.1f},{by - py:.1f} Z"/>'


def text(x, y, s, cls="label"):
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}">{s}</text>'


# ---------------------------------------------------------------- grids

def line_grid():
    lines = []
    for x in range(0, W + 1, 20):
        cls = "major" if x % 100 == 0 else "minor"
        lines.append(f'<line class="{cls}" x1="{x}" y1="0" x2="{x}" y2="{H}"/>')
    for y in range(0, H + 1, 20):
        cls = "major" if y % 100 == 0 else "minor"
        lines.append(f'<line class="{cls}" x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
    return svg("pf-hero__grid", lines, "xMidYMid")


def dot_grid():
    body = [
        '<defs><pattern id="pf-dots" width="20" height="20" patternUnits="userSpaceOnUse">'
        '<circle class="dot" cx="10" cy="10" r="1.2"/></pattern></defs>',
        f'<rect width="{W}" height="{H}" fill="url(#pf-dots)"/>',
    ]
    return svg("pf-hero__grid", body, "xMidYMid")


# ---------------------------------------------------------------- network

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
        d.append(path([nodes[new][:2], nodes[old][:2]], cls).replace(
            "/>", f' data-a="{a}" data-b="{b}" style="--d: {start:.2f}s; --t: {link_t}s"/>'))
    for i, x, y in stubs:
        d.append(path([nodes[i][:2], (x, y)], "link stub grow").replace(
            "/>", f' data-a="{i}" style="--d: {pop[i] + 0.15:.2f}s; --t: 0.6s"/>'))
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


# ---------------------------------------------------------------- pcb

def pcb():
    d = []
    T = "draw trace"

    # Board outline, mounting holes, overall width dimension
    bx0, by0, bx1, by1 = 760, 110, 1520, 790
    d.append(f'<rect class="draw" pathLength="1" x="{bx0}" y="{by0}" width="{bx1 - bx0}" '
             f'height="{by1 - by0}" rx="24"/>')
    for hx, hy in ((bx0 + 40, by0 + 40), (bx1 - 40, by0 + 40), (bx0 + 40, by1 - 40), (bx1 - 40, by1 - 40)):
        d.append(f'<circle class="fade pad" cx="{hx}" cy="{hy}" r="22"/>')
        d.append(f'<circle class="fade pad" cx="{hx}" cy="{hy}" r="11"/>')
    y = by1 + 40
    d.append(f'<line class="ext" x1="{bx0}" y1="{by1 + 8}" x2="{bx0}" y2="{y + 12}"/>')
    d.append(f'<line class="ext" x1="{bx1}" y1="{by1 + 8}" x2="{bx1}" y2="{y + 12}"/>')
    d.append(f'<line class="dim" x1="{bx0}" y1="{y}" x2="{bx1}" y2="{y}"/>')
    d.append(arrow(bx0, y, 180))
    d.append(arrow(bx1, y, 0))
    d.append(text((bx0 + bx1) / 2 - 24, y - 10, "76.20"))

    # U1: 32-pin QFP, 8 pads a side
    cx, cy, half = 1090, 450, 75
    offs = [-56, -40, -24, -8, 8, 24, 40, 56]
    d.append(f'<rect class="draw" pathLength="1" x="{cx - half}" y="{cy - half}" width="{2 * half}" height="{2 * half}"/>')
    d.append(f'<circle class="fade pad" cx="{cx - half + 16}" cy="{cy - half + 16}" r="4"/>')
    d.append(text(cx - 16, cy + 7, "U1", "ref"))
    pad_len, pad_w = 22, 6
    for o in offs:
        d.append(f'<rect class="fade pad" x="{cx + half + 4}" y="{cy + o - 3}" width="{pad_len}" height="{pad_w}"/>')
        d.append(f'<rect class="fade pad" x="{cx - half - 4 - pad_len}" y="{cy + o - 3}" width="{pad_len}" height="{pad_w}"/>')
        d.append(f'<rect class="fade pad" x="{cx + o - 3}" y="{cy - half - 4 - pad_len}" width="{pad_w}" height="{pad_len}"/>')
        d.append(f'<rect class="fade pad" x="{cx + o - 3}" y="{cy + half + 4}" width="{pad_w}" height="{pad_len}"/>')
    right_x = cx + half + 4 + pad_len     # outer ends of the pads
    left_x = cx - half - 4 - pad_len
    top_y = cy - half - 4 - pad_len
    bot_y = cy + half + 4 + pad_len

    # J1: JTAG header on the right edge; U1's right side fans out to it
    jx, nets = 1440, ["VCC", "TCK", "TMS", "TDI", "TDO", "GND"]
    jys = [cy - 75 + 30 * i for i in range(6)]
    d.append(f'<rect class="draw" pathLength="1" x="{jx - 22}" y="{jys[0] - 22}" width="44" height="{jys[-1] - jys[0] + 44}"/>')
    d.append(text(jx - 20, jys[0] - 34, "J1", "ref"))
    d.append(text(jx + 30, jys[0] - 34, "JTAG", "ref accent"))
    for i, (o, jy) in enumerate(zip(offs[1:7], jys)):
        py = cy + o
        dy = jy - py
        bend = 1255
        pts = [(right_x, py), (bend, py), (bend + abs(dy), jy), (jx - 10, jy)]
        accent = nets[i] == "TCK"
        d.append(path(pts, T + (" accent" if accent else "")))
        shape = (f'<rect class="fade pad" x="{jx - 10}" y="{jy - 10}" width="20" height="20"/>' if i == 0
                 else f'<circle class="fade pad" cx="{jx}" cy="{jy}" r="10"/>')
        d.append(shape)
        d.append(text(jx + 32, jy + 5, nets[i], "net" + (" accent" if accent else "")))

    # U2: SOIC-8 flash, up and left; the 4 leftmost top pads of U1 run a bus to it
    ux0, uy0, uw, uh = 860, 140, 100, 70
    d.append(f'<rect class="draw" pathLength="1" x="{ux0}" y="{uy0}" width="{uw}" height="{uh}"/>')
    d.append(text(ux0 + uw / 2 - 14, uy0 + uh / 2 + 7, "U2", "ref"))
    u2_pads = [875, 898, 921, 944]
    for px in u2_pads:
        d.append(f'<rect class="fade pad" x="{px - 4}" y="{uy0 + uh}" width="8" height="22"/>')
        d.append(f'<rect class="fade pad" x="{px - 4}" y="{uy0 - 22}" width="8" height="22"/>')
    for i, (o, px) in enumerate(zip(offs[:4], u2_pads)):
        sx, level = cx + o, 300 - 16 * i
        d.append(path([(sx, top_y), (sx, level), (px, level), (px, uy0 + uh + 22)], T, chamfer=10))
    # remaining top pads drop to vias
    for i, o in enumerate(offs[4:]):
        vy = top_y - 30 - 14 * i
        d.append(path([(cx + o, top_y), (cx + o, vy)], T))
        d.append(f'<circle class="fade pad" cx="{cx + o}" cy="{vy - 7}" r="7"/>')

    # R1–R4: series resistors left of U1, fed by a fanned bus from U1's left side
    rx = 880
    rys = [cy - 90 + 60 * i for i in range(4)]
    for i, (o, ry) in enumerate(zip(offs[2:6], rys)):
        py = cy + o
        dy = ry - py
        bend = left_x - 30
        d.append(path([(left_x, py), (bend, py), (bend - abs(dy), ry), (rx + 12, ry)], T))
        d.append(f'<rect class="fade pad" x="{rx - 2}" y="{ry - 7}" width="14" height="14"/>')
        d.append(f'<rect class="fade pad" x="{rx - 30}" y="{ry - 7}" width="14" height="14"/>')
        d.append(text(rx - 34, ry - 14, f"R{i + 1}", "ref small"))
        d.append(path([(rx - 30, ry), (rx - 64, ry)], T))
        d.append(f'<circle class="fade pad" cx="{rx - 71}" cy="{ry}" r="7"/>')

    # Y1: crystal under U1's left bottom pads, with load caps C1/C2 to ground vias
    yx, yy = cx - 100, 640
    d.append(f'<rect class="draw" pathLength="1" x="{yx}" y="{yy}" width="80" height="34" rx="17"/>')
    d.append(text(yx + 26, yy + 60, "Y1", "ref small"))
    for k, o in enumerate(offs[0:2]):
        px = yx + 14 + 52 * k
        d.append(path([(cx + o, bot_y), (cx + o, bot_y + 30), (px, bot_y + 30 + abs(px - cx - o)), (px, yy + 8)], T))
        d.append(f'<rect class="fade pad" x="{px - 7}" y="{yy + 8}" width="14" height="18"/>')
        c = (px - 70, yy + 80) if k == 0 else (px + 70, yy + 80)
        d.append(path([(px, yy + 26), (px, yy + 50), (c[0], yy + 50), (c[0], c[1] - 10)], T, chamfer=8))
        d.append(f'<rect class="fade pad" x="{c[0] - 7}" y="{c[1] - 10}" width="14" height="10"/>')
        d.append(f'<rect class="fade pad" x="{c[0] - 7}" y="{c[1] + 4}" width="14" height="10"/>')
        d.append(text(c[0] + 12 if k else c[0] - 30, c[1] + 6, f"C{k + 1}", "ref small"))
    # remaining bottom pads out to staggered vias
    for i, o in enumerate(offs[2:]):
        vy = bot_y + 30 + 26 * (i % 2)
        d.append(path([(cx + o, bot_y), (cx + o, vy)], T))
        d.append(f'<circle class="fade pad" cx="{cx + o}" cy="{vy + 7}" r="7"/>')

    return svg("pf-hero__drawing", d)


# ---------------------------------------------------------------- flange

def flange():
    d = []
    CX, CY = 1140, 430
    d.append(f'<line class="center" x1="{CX - 400}" y1="{CY}" x2="{CX + 400}" y2="{CY}"/>')
    d.append(f'<line class="center" x1="{CX}" y1="{CY - 380}" x2="{CX}" y2="{CY + 380}"/>')
    d.append(f'<circle class="center" cx="{CX}" cy="{CY}" r="210"/>')
    for r in (300, 120, 62):
        d.append(f'<circle class="draw" pathLength="1" cx="{CX}" cy="{CY}" r="{r}"/>')
    for i in range(6):
        a = radians(-90 + i * 60)
        hx, hy = CX + 210 * cos(a), CY + 210 * sin(a)
        cls = "draw accent" if i == 1 else "draw"
        d.append(f'<circle class="{cls}" pathLength="1" cx="{hx:.1f}" cy="{hy:.1f}" r="18"/>')
        d.append(f'<line class="center" x1="{hx - 30:.1f}" y1="{hy:.1f}" x2="{hx + 30:.1f}" y2="{hy:.1f}"/>')
        d.append(f'<line class="center" x1="{hx:.1f}" y1="{hy - 30:.1f}" x2="{hx:.1f}" y2="{hy + 30:.1f}"/>')
    a = radians(-30)
    hx, hy = CX + 210 * cos(a), CY + 210 * sin(a)
    ex, ey = hx + 13 * cos(a), hy + 13 * sin(a)
    kx, ky = hx + 150, hy - 120
    d.append(f'<polyline class="dim accent" points="{ex:.1f},{ey:.1f} {kx:.1f},{ky:.1f} {kx + 90:.1f},{ky:.1f}"/>')
    d.append(arrow(ex, ey, 180 + 38.7, cls="head accent"))
    d.append(text(kx + 6, ky - 10, "Ø36 × 6 EQ SP", "label accent"))
    a = radians(-150)
    x1, y1 = CX + 300 * cos(a), CY + 300 * sin(a)
    x2, y2 = CX - 300 * cos(a), CY - 300 * sin(a)
    d.append(f'<line class="dim" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    d.append(arrow(x1, y1, 30))
    d.append(arrow(x2, y2, -150))
    d.append(f'<text class="label" x="{CX - 175}" y="{CY + 70}" transform="rotate(30 {CX - 175} {CY + 70})">Ø600</text>')
    y = CY + 360
    d.append(f'<line class="ext" x1="{CX - 300}" y1="{CY + 20}" x2="{CX - 300}" y2="{y + 12}"/>')
    d.append(f'<line class="ext" x1="{CX + 300}" y1="{CY + 20}" x2="{CX + 300}" y2="{y + 12}"/>')
    d.append(f'<line class="dim" x1="{CX - 300}" y1="{y}" x2="{CX + 300}" y2="{y}"/>')
    d.append(arrow(CX - 300, y, 180))
    d.append(arrow(CX + 300, y, 0))
    d.append(text(CX - 16, y - 10, "600"))
    r = 360
    a1, a2 = radians(-90), radians(-30)
    p1 = (CX + r * cos(a1), CY + r * sin(a1))
    p2 = (CX + r * cos(a2), CY + r * sin(a2))
    d.append(f'<path class="dim" d="M{p1[0]:.1f},{p1[1]:.1f} A{r},{r} 0 0,1 {p2[0]:.1f},{p2[1]:.1f}"/>')
    d.append(arrow(*p1, 180))
    d.append(arrow(*p2, 60))
    am = radians(-60)
    d.append(text(CX + (r + 14) * cos(am), CY + (r + 14) * sin(am), "60°"))
    for sx in (CX - 360, CX + 360):
        d.append(f'<line class="cut" x1="{sx}" y1="{CY - 40}" x2="{sx}" y2="{CY + 40}"/>')
        d.append(text(sx - 7, CY - 52, "A"))
    return svg("pf-hero__drawing", d)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    grid, drawing = {"network": (dot_grid, network), "pcb": (dot_grid, pcb), "flange": (line_grid, flange)}[ART]
    (OUT / "hero-grid.html").write_text(grid())
    (OUT / "hero-drawing.html").write_text(drawing())
    print(f"wrote {ART}:", OUT / "hero-grid.html", OUT / "hero-drawing.html")
