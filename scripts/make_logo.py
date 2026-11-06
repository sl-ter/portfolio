"""Generate the header logo icon and favicon.

Writes overrides/.icons/pf/<mark>.svg (filled shapes; Material colours it with currentColor)
and docs/assets/favicon.svg (same mark in the accent orange).
    .venv/bin/python scripts/make_logo.py

  mitsudomoe — three tomoe swirling around the centre, no outer ring
  flange     — outer ring, six bolt holes, bore
"""

from math import atan2, cos, pi, radians, sin
from pathlib import Path

MARK = "mitsudomoe"
ORANGE = "#ff4f00"

ROOT = Path(__file__).resolve().parent.parent
C = 12  # icon centre in a 24×24 viewBox


def polar(r, deg):
    return C + r * cos(radians(deg)), C + r * sin(radians(deg))


def arc_points(cx, cy, r, a0, a1, n=24):
    """Points along a circle from angle a0 to a1 (radians), inclusive."""
    return [(cx + r * cos(a0 + (a1 - a0) * i / n), cy + r * sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def to_path(points):
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in points) + "Z"


def mitsudomoe(R=11.4, g=1.4):
    """Three tomoe: round heads at mid-radius; each tail runs out along the rim and wraps the
    next head, separated from it by a gap of width g. Built as the outer disk minus the gaps
    (a thin band around one side of each head, plus the small triangle between the heads);
    the three pieces left over are the tomoe. Needs shapely (dev only): pip install shapely."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    # head radius h and centre distance a: adjacent heads sit g apart and each head just touches
    # the rim, so the band around it runs cleanly off the edge and the tail before it tapers
    # to a point where the band's outer edge crosses the rim
    h = (R - g / 3 ** 0.5) / (1 + 2 / 3 ** 0.5)
    a = R - h
    angles = [-90 + 120 * i for i in range(3)]
    heads = [polar(a, phi) for phi in angles]

    gaps = [Polygon(heads)]  # centre triangle between the heads (the heads are subtracted below)
    for i, (hx, hy) in enumerate(heads):
        px, py = heads[i - 1]
        start = atan2(py - hy, px - hx)                  # pointing at the previous head
        end = radians(angles[i])                         # straight out, where the head meets the rim
        if end > start:
            end -= 2 * pi
        wedge = Polygon([(hx, hy)] + [(hx + 30 * cos(t), hy + 30 * sin(t))
                                      for t in (start + (end - start) * j / 48 for j in range(49))])
        band = Point(hx, hy).buffer(h + g, 128).difference(Point(hx, hy).buffer(h, 128))
        gaps.append(band.intersection(wedge))
    gap = unary_union(gaps).difference(unary_union([Point(x, y).buffer(h, 128) for x, y in heads]))
    pieces = Point(C, C).buffer(R, 256).difference(gap)
    polys = sorted(getattr(pieces, "geoms", [pieces]), key=lambda poly: -poly.area)[:3]
    return "".join(to_path(list(poly.exterior.coords)[:-1]) for poly in polys), "nonzero"


def flange():
    def circle(cx, cy, r):
        return f"M{cx - r:.2f},{cy:.2f}a{r},{r} 0 1,0 {2 * r},0a{r},{r} 0 1,0 {-2 * r},0"

    def ring(cx, cy, r_out, r_in):
        return circle(cx, cy, r_out) + circle(cx, cy, r_in)

    d = ring(C, C, 11, 9.3) + ring(C, C, 3.3, 1.9)
    for i in range(6):
        d += ring(*polar(6.3, -90 + 60 * i), 1.75, 0.9)
    return d, "evenodd"


if __name__ == "__main__":
    d, rule = {"mitsudomoe": mitsudomoe, "flange": flange}[MARK]()
    icon = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill-rule="{rule}" d="{d}"/></svg>\n'
    (ROOT / "overrides/.icons/pf").mkdir(parents=True, exist_ok=True)
    (ROOT / f"overrides/.icons/pf/{MARK}.svg").write_text(icon)
    (ROOT / "docs/assets/favicon.svg").write_text(icon.replace("<path ", f'<path fill="{ORANGE}" ', 1))
    print("wrote", MARK)
