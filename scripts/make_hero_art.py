"""Generate the home-page hero linework (a drafting sheet) as inline-SVG Jinja partials.

Writes overrides/partials/hero-grid.html and overrides/partials/hero-drawing.html.
Run after changing geometry:  .venv/bin/python scripts/make_hero_art.py
"""

from math import cos, sin, radians
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "overrides" / "partials"
W, H = 1600, 900
CX, CY = 1140, 430  # centre of the part, right of the hero text


def grid() -> str:
    lines = []
    for x in range(0, W + 1, 20):
        cls = "major" if x % 100 == 0 else "minor"
        lines.append(f'<line class="{cls}" x1="{x}" y1="0" x2="{x}" y2="{H}"/>')
    for y in range(0, H + 1, 20):
        cls = "major" if y % 100 == 0 else "minor"
        lines.append(f'<line class="{cls}" x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
    return (
        f'<svg class="pf-hero__grid" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
        f'aria-hidden="true">\n' + "\n".join(lines) + "\n</svg>\n"
    )


def arrow(x, y, angle_deg, size=14):
    """Filled arrowhead with its tip at (x, y), pointing along angle_deg."""
    a = radians(angle_deg)
    bx, by = x - size * cos(a), y - size * sin(a)
    px, py = -sin(a) * size * 0.28, cos(a) * size * 0.28
    return f'<path class="head" d="M{x:.1f},{y:.1f} L{bx + px:.1f},{by + py:.1f} L{bx - px:.1f},{by - py:.1f} Z"/>'


def drawing() -> str:
    d = []
    # Centre lines (chain), drawn first so outlines sit on top
    d.append(f'<line class="center" x1="{CX - 400}" y1="{CY}" x2="{CX + 400}" y2="{CY}"/>')
    d.append(f'<line class="center" x1="{CX}" y1="{CY - 380}" x2="{CX}" y2="{CY + 380}"/>')
    d.append(f'<circle class="center" cx="{CX}" cy="{CY}" r="210"/>')  # bolt circle

    # Part outline: flange, hub, bore
    for r in (300, 120, 62):
        d.append(f'<circle class="draw" pathLength="1" cx="{CX}" cy="{CY}" r="{r}"/>')

    # Six bolt holes on the bolt circle; the first is called out in the accent colour
    for i in range(6):
        a = radians(-90 + i * 60)
        hx, hy = CX + 210 * cos(a), CY + 210 * sin(a)
        cls = "draw accent" if i == 1 else "draw"
        d.append(f'<circle class="{cls}" pathLength="1" cx="{hx:.1f}" cy="{hy:.1f}" r="18"/>')
        d.append(f'<line class="center" x1="{hx - 30:.1f}" y1="{hy:.1f}" x2="{hx + 30:.1f}" y2="{hy:.1f}"/>')
        d.append(f'<line class="center" x1="{hx:.1f}" y1="{hy - 30:.1f}" x2="{hx:.1f}" y2="{hy + 30:.1f}"/>')

    # Leader to the accented hole
    a = radians(-30)
    hx, hy = CX + 210 * cos(a), CY + 210 * sin(a)
    ex, ey = hx + 13 * cos(a), hy + 13 * sin(a)
    kx, ky = hx + 150, hy - 120
    d.append(f'<polyline class="dim accent" points="{ex:.1f},{ey:.1f} {kx:.1f},{ky:.1f} {kx + 90:.1f},{ky:.1f}"/>')
    d.append(arrow(ex, ey, 180 + 38.7).replace('class="head"', 'class="head accent"'))
    d.append(f'<text class="label accent" x="{kx + 6:.1f}" y="{ky - 10:.1f}">Ø36 × 6 EQ SP</text>')

    # Diameter dimension across the flange at 210°→30°
    a = radians(-150)
    x1, y1 = CX + 300 * cos(a), CY + 300 * sin(a)
    x2, y2 = CX - 300 * cos(a), CY - 300 * sin(a)
    d.append(f'<line class="dim" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    d.append(arrow(x1, y1, 30))
    d.append(arrow(x2, y2, -150))
    d.append(f'<text class="label" x="{CX - 175}" y="{CY + 70}" transform="rotate(30 {CX - 175} {CY + 70})">Ø600</text>')

    # Linear dimension under the part with extension lines
    y = CY + 360
    d.append(f'<line class="ext" x1="{CX - 300}" y1="{CY + 20}" x2="{CX - 300}" y2="{y + 12}"/>')
    d.append(f'<line class="ext" x1="{CX + 300}" y1="{CY + 20}" x2="{CX + 300}" y2="{y + 12}"/>')
    d.append(f'<line class="dim" x1="{CX - 300}" y1="{y}" x2="{CX + 300}" y2="{y}"/>')
    d.append(arrow(CX - 300, y, 180))
    d.append(arrow(CX + 300, y, 0))
    d.append(f'<text class="label" x="{CX - 16}" y="{y - 10}">600</text>')

    # Angular dimension between two bolt holes
    r = 360
    a1, a2 = radians(-90), radians(-30)
    p1 = (CX + r * cos(a1), CY + r * sin(a1))
    p2 = (CX + r * cos(a2), CY + r * sin(a2))
    d.append(f'<path class="dim" d="M{p1[0]:.1f},{p1[1]:.1f} A{r},{r} 0 0,1 {p2[0]:.1f},{p2[1]:.1f}"/>')
    d.append(arrow(*p1, 180))
    d.append(arrow(*p2, 60))
    am = radians(-60)
    d.append(f'<text class="label" x="{CX + (r + 14) * cos(am):.1f}" y="{CY + (r + 14) * sin(am):.1f}">60°</text>')

    # Section cut A–A through the hub
    for sx in (CX - 360, CX + 360):
        d.append(f'<line class="cut" x1="{sx}" y1="{CY - 40}" x2="{sx}" y2="{CY + 40}"/>')
        d.append(f'<text class="label" x="{sx - 7}" y="{CY - 52}">A</text>')

    return (
        f'<svg class="pf-hero__drawing" viewBox="0 0 {W} {H}" preserveAspectRatio="xMaxYMid slice" '
        f'aria-hidden="true">\n' + "\n".join(d) + "\n</svg>\n"
    )


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hero-grid.html").write_text(grid())
    (OUT / "hero-drawing.html").write_text(drawing())
    print("wrote", OUT / "hero-grid.html", OUT / "hero-drawing.html")
