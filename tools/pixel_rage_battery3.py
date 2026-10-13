"""Red corps battery, round three (J, 2026-10-13): B2's build, now clad in a faceted crimson gem-block texture
("a diamond block texture ... in a nice crimson red"), in three reds with small design differences, and new
handles to try.

  C1 crimson : deep blood crimson. Classic facets: bevelled rim, a cut diamond in the middle, a few glints.
               The original arched rune handle.
  C2 ruby    : brighter, more saturated ruby. A double bevel and more sparkle. A round ring handle on a stem.
  C3 garnet  : dark garnet. Facets crossed by hairline cracks. Two curved horns rising from the clamps for a handle.

The gem pattern is our own (a 16 x 16 cut-gem tile, two tiles a block), painted on every face of the stone by
where the face sits, so it runs straight across the whole battery. Glowing parts keep their light.
    python tools/pixel_rage_battery3.py OUTDIR -> battery3_<v>_body.npz, battery3_<v>_plate.npz
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["pixel_rage_battery2.py", os.path.join(OUT, "_r2")]
sys.path.insert(0, HERE)
import pixel_rage_battery2 as P2  # noqa: E402
sys.argv = _argv
B = P2.B
X, Y, Z, R, TH, G = B.X, B.Y, B.Z, B.R, B.TH, B.G
LIGHT = np.array([-0.45, -0.75, 0.6]); LIGHT /= np.linalg.norm(LIGHT)

REDS = {
    "c1": [(28, 2, 8), (88, 6, 20), (150, 14, 34), (214, 52, 66), (255, 176, 180)],
    "c2": [(40, 0, 14), (120, 4, 34), (196, 12, 54), (250, 76, 108), (255, 208, 220)],
    "c3": [(20, 3, 5), (62, 8, 12), (110, 16, 22), (170, 48, 48), (236, 150, 140)],
}


def ramp(t, stops):
    t = np.clip(t, 0, 1) * (len(stops) - 1)
    i = np.minimum(t.astype(int), len(stops) - 2)
    f = (t - i)[..., None]
    f = f * f * (3 - 2 * f)
    s = np.array(stops, float)
    return s[i] * (1 - f) + s[i + 1] * f


def gem_tile(v):
    """16 x 16 tone map for one cut-gem tile (0 dark .. 1 glint)."""
    u, w = np.meshgrid(np.arange(16) + 0.5, np.arange(16) + 0.5, indexing="ij")
    du, dw = u - 8, w - 8
    d = np.abs(du) + np.abs(dw)
    t = np.full((16, 16), 0.5)
    quad = np.where(du < 0, np.where(dw < 0, 0.62, 0.48), np.where(dw < 0, 0.5, 0.36))   # four facets, lit from top-left
    t = np.where(d < 7.5, quad, t)
    t = np.where(d < 4.0, np.where(du + dw < 0, 0.86, 0.6), t)                         # the cut diamond in the middle
    t = np.where(np.abs(d - 4.0) < 0.5, 0.3, t)                                         # its girdle line
    edge = np.minimum.reduce([u, w, 16 - u, 16 - w])
    bevel_tl = (np.minimum(u, w) < 2.0) & (edge < 2.0)
    t = np.where(edge < 2.0, np.where((u < 2.0) | (w < 2.0), 0.78, 0.26), t)            # bevel: light top-left, dark bottom-right
    t = np.where(edge < 1.0, 0.12, t)                                                    # the dark seam between tiles
    if v == "c2":
        t = np.where((edge >= 2.0) & (edge < 3.0), np.where((u < 3) | (w < 3), 0.7, 0.32), t)   # a second bevel
    glints = [(5, 5), (6, 4), (10, 11)] if v != "c2" else [(5, 5), (6, 4), (4, 6), (10, 11), (11, 4), (3, 12)]
    for a, b in glints:
        t[a, b] = 1.0
    if v == "c3":
        cr = (np.abs(du * 0.7 - dw + 2.5) < 0.5) | (np.abs(du + dw * 0.45 - 4.5) < 0.45)
        t = np.where(cr & (edge >= 1.0), 0.08, t)                                        # hairline cracks
    return t


def strip_handle(part):
    m = (Z >= 30.5) & (np.abs(X) >= 10.9) & (np.abs(Y) < 2.6)
    m |= (Z >= 45.5)
    part[m & ~((Z >= 42.5) & (Z < 43.5) & (R < 9.5))] = B.EMPTY


def ring_handle(part):
    # a stem out of the cap and a round ring standing on it, a rune line glowing round its face
    part[(Z >= 42.5) & (Z < 45.0) & (R < 1.6)] = B.STONE
    rr = np.hypot(X, Z - 51.0)
    tor = (np.hypot(rr - 5.8, Y) < 1.3)
    part[tor] = B.STONE
    part[tor & (Y < -0.9) & (np.abs(rr - 5.8) < 0.35)] = B.RUNE
    for a in (0.0, math.pi):                                                           # two collars where it meets the stem
        pass
    part[(np.abs(Z - 45.2) < 0.6) & (R < 2.4)] = B.DARK


def horn_handle(part):
    for s in (-1, 1):
        for k in range(60):
            t = k / 59
            cx = s * (12.0 - 8.5 * t ** 1.5)
            cz = 37.5 + 13.0 * t
            r = 1.7 * (1 - 0.75 * t) + 0.25
            m = (np.hypot(X - cx, Z - cz) < r) & (np.abs(Y) < r * 0.9)
            part[m] = B.STONE
            if t > 0.88:
                part[m] = B.RUNE                                                        # glowing tips
        part[(np.abs(X - s * 11.5) < 2.6) & (np.abs(Y) < 2.4) & (np.abs(Z - 38.5) < 1.6)] = B.DARK


def gem_faces(q, c, k, v):
    """Repaint the stone faces (kinds 0, 1, 3) with the gem tile by where each face sits."""
    ctr = q.mean(1)
    span = q.max(1) - q.min(1)
    ax = np.argmin(span, 1)
    nrm = np.zeros((len(q), 3)); nrm[np.arange(len(q)), ax] = 1.0
    # which side the face points: compare with the voxel it came from (the corners sit on the face plane)
    tile = gem_tile(v)
    uv_axes = np.array([[1, 2], [0, 2], [0, 1]])[ax]
    cu = ctr[np.arange(len(q)), uv_axes[:, 0]]
    cv = ctr[np.arange(len(q)), uv_axes[:, 1]]
    iu = (np.floor(cu / G).astype(int)) % 16
    iv = (np.floor(-cv / G).astype(int)) % 16                                          # up is +z: flip so top-left is lit
    t = tile[iu, iv]
    stone = np.isin(k, (0, 1, 3))
    darken = np.where(k == 0, 0.6, 1.0)                                                 # parts that were shadowed stay deeper
    col = ramp(t * darken, REDS[v])
    shade = 0.75 + 0.35 * np.abs(nrm @ LIGHT)
    newc = np.clip(col * shade[:, None], 0, 255)
    c = np.where(stone[:, None], newc, c)
    k = np.where(stone & (t > 0.95), 3, k).astype(np.int8)                              # glints sparkle (fleck kind)
    return q, c.astype(np.float32), k


if __name__ == "__main__":
    for v in ("c1", "c2", "c3"):
        body, plate = P2.build()
        # J: "I shouldn't be able to see the logo where the red light should be": the hole is pure light now -
        # the claw-cut back wall becomes light too
        fy = -(9.0 + 3.4); prr = np.hypot(X, Z - 24.0)
        body[(prr < 5.8) & (Y >= fy + 1.0) & (Y < fy + 2.0)] = P2.PORTLIGHT
        if v != "c1":
            strip_handle(body)
            (ring_handle if v == "c2" else horn_handle)(body)
        for name, p in (("body", body), ("plate", plate)):
            q, c, k, g = B.quads(p, P2.pal)
            q, c, k = gem_faces(q, c, k, v)
            np.savez_compressed(os.path.join(OUT, f"battery3_{v}_{name}.npz"), quads=q, col=c, kind=k, glow=g)
            print(v, name, len(q), "faces", np.bincount(k, minlength=8))
