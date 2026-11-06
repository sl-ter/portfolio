"""Generate the header logo (a mitsudomoe: three tomoe swirling around the centre, no ring).

Writes overrides/.icons/pf/mitsudomoe.svg (filled; Material colours it with currentColor) and
docs/assets/favicon.svg (the same mark in the accent orange). Needs shapely (dev only):
    .venv/bin/pip install shapely && .venv/bin/python scripts/make_logo.py
"""

from math import atan2, cos, pi, radians, sin
from pathlib import Path

ORANGE = "#ff4f00"

ROOT = Path(__file__).resolve().parent.parent
C = 12  # icon centre in a 24×24 viewBox


def polar(r, deg):
    return C + r * cos(radians(deg)), C + r * sin(radians(deg))


def to_path(points):
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in points) + "Z"


def mitsudomoe(R=11.4, g=1.4):
    """Three tomoe: round heads at mid-radius; each tail runs out along the rim and wraps the
    next head, separated from it by a gap of width g. Built as the outer disk minus the gaps
    (a thin band around one side of each head, plus the small triangle between the heads);
    the three pieces left over are the tomoe."""
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
    return "".join(to_path(list(poly.exterior.coords)[:-1]) for poly in polys)


if __name__ == "__main__":
    icon = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill-rule="nonzero" d="{mitsudomoe()}"/></svg>\n'
    (ROOT / "overrides/.icons/pf").mkdir(parents=True, exist_ok=True)
    (ROOT / "overrides/.icons/pf/mitsudomoe.svg").write_text(icon)
    (ROOT / "docs/assets/favicon.svg").write_text(icon.replace("<path ", f'<path fill="{ORANGE}" ', 1))
    print("wrote overrides/.icons/pf/mitsudomoe.svg and docs/assets/favicon.svg")
