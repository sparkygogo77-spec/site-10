"""Better Power Ring models (J: "I need a better lantern ring model"), on the pixel grid like the lanterns,
64 pixels per block (G = 0.25 model pixels). Original emblems, three options:
  a forged: heavy bevelled band, hexagonal bezel, a raised flame sigil inside a lit rim
  b crown:  the band splits into claw prongs gripping a glowing round gem with a cut starburst
  c sleek:  wide flat band with a glowing channel all the way round, an oval face with a ring of light

    python tools/pixel_ring.py OUTDIR -> OUTDIR/ring_<v>.npz (quads, col, kind)
The finger runs along y; the face looks up (+z). Kinds: 0 dark, 1 metal, 4 green light, 6 bright light.
"""
import os, sys
import numpy as np

G = 0.25
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
A = np.arange(-6, 6, G) + G / 2
X, Y, Z = np.meshgrid(A, np.arange(-3, 3, G) + G / 2, np.arange(-6, 6.5, G) + G / 2, indexing="ij")
EMPTY, BAND, BEZEL, GEM, LIT, DARK, PRONG = range(7)
R_IN = 2.6           # finger hole radius


def band(width, thick, bevel=True):
    r = np.hypot(X, Z)
    inside = (r >= R_IN) & (r <= R_IN + thick) & (np.abs(Y) <= width / 2)
    if bevel:   # round the outer edges
        inside &= (r - R_IN - thick + 0.4) < (width / 2 - np.abs(Y)) * 1.2 + 0.2
    return inside


def build(v):
    part = np.zeros(X.shape, np.int8)
    r = np.hypot(X, Z)
    if v == "a":
        part[band(2.6, 1.0)] = BAND
        top = Z - (R_IN + 0.7)
        hexd = np.maximum(np.abs(X) * 0.866 + np.abs(Y) * 0.5, np.abs(Y))
        bezel = (hexd <= 2.9) & (top >= 0) & (top <= 1.6)
        part[bezel] = BEZEL
        part[(hexd <= 2.3) & (top > 1.0) & (top <= 1.6)] = DARK                   # recessed face
        part[(hexd > 2.3) & (hexd <= 2.6) & (top > 1.2) & (top <= 1.8)] = LIT     # lit rim
        # A raised flame sigil: a teardrop pointing along +y.
        u, w = X, Y + 0.3
        flame = (np.hypot(u, w + 0.5) <= 1.5) | ((w > -0.5) & (np.abs(u) <= 1.5 * np.clip(1 - (w + 0.5) / 2.4, 0, 1) ** 1.3) & (w < 1.9))
        part[flame & (top > 1.4) & (top <= 2.1) & (hexd <= 2.3)] = GEM
        part[(np.hypot(u, w + 0.4) <= 0.45) & (top > 1.4) & (top <= 2.3)] = LIT   # white-hot heart
    elif v == "b":
        part[band(1.6, 0.7)] = BAND
        top = Z - (R_IN + 0.5)
        part[(np.hypot(X, Y) <= 2.0) & (top >= 0) & (top <= 0.6)] = BEZEL         # seat
        gem = np.hypot(np.hypot(X, Y) * 1.0, (top - 1.4) * 1.25) <= 1.7
        part[gem & (top > 0.4)] = GEM
        ang = np.arctan2(Y, X)
        star = (np.cos(ang * 8) > 0.82) & (np.hypot(X, Y) < 1.5) & (top > 2.2)
        part[gem & star] = LIT
        part[gem & (np.hypot(X, Y) < 0.5) & (top > 2.4)] = LIT
        for a in np.radians([45, 135, 225, 315]):                                  # four claw prongs
            cx, cy = 1.75 * np.cos(a), 1.75 * np.sin(a)
            pr = (np.hypot(X - cx, Y - cy) <= 0.38) & (top >= 0) & (top <= 2.0)
            tip = (np.hypot(X - cx * 0.85, Y - cy * 0.85) <= 0.32) & (top > 2.0) & (top <= 2.4)
            part[pr | tip] = PRONG
        # Shoulders sweeping up from the band to the seat.
        sh = (np.abs(Y) <= 0.8) & (np.abs(X) <= 2.4) & (top < 0) & (top > -0.9) & (r > R_IN + 0.6)
        part[sh & (part == EMPTY)] = BAND
    else:
        part[band(3.4, 0.8, bevel=False)] = BAND
        chan = (r > R_IN + 0.55) & (r <= R_IN + 0.8) & (np.abs(Y) <= 0.35)
        part[chan] = LIT                                                           # glowing channel
        top = Z - (R_IN + 0.6)
        oval = (X / 2.6) ** 2 + (Y / 1.9) ** 2
        part[(oval <= 1) & (top >= 0) & (top <= 0.8)] = BEZEL
        ring = (oval > 0.42) & (oval <= 0.7) & (top > 0.5) & (top <= 1.0)
        part[ring] = GEM
        notch = (np.cos(np.arctan2(Y / 1.9, X / 2.6) * 12) > 0.6) & (oval > 0.72) & (oval <= 0.88) & (top > 0.5) & (top <= 0.9)
        part[notch] = LIT
        part[(oval <= 0.15) & (top > 0.5) & (top <= 1.1)] = LIT
        part[(oval > 0.15) & (oval <= 0.42) & (top > 0.6) & (top <= 0.8)] = DARK
    return part


def crown(prongs=4, height=1.0, halo=False, cut="round"):
    """Crown variations of option b (J picked b): prong count, gem height, a halo of small gems, the cut."""
    part = np.zeros(X.shape, np.int8)
    r = np.hypot(X, Z)
    part[band(1.6, 0.7)] = BAND
    top = Z - (R_IN + 0.5)
    part[(np.hypot(X, Y) <= 2.0) & (top >= 0) & (top <= 0.6)] = BEZEL
    gz = 1.4 * height
    if cut == "emerald":
        gem = (np.abs(X) <= 1.5) & (np.abs(Y) <= 1.15) & (top > 0.4) & (top <= gz + 1.2) & \
              (np.abs(X) + np.abs(Y) <= 2.3) & (np.abs(X) + (top - 0.4) * 0.5 <= 1.9)
        table = gem & (top > gz + 0.8)
    else:
        gem = np.hypot(np.hypot(X, Y), (top - gz) * 1.25) <= 1.7
        gem &= top > 0.4
        table = gem & (np.hypot(X, Y) < 0.5) & (top > gz + 1.0)
    part[gem] = GEM
    ang = np.arctan2(Y, X)
    part[gem & (np.cos(ang * 8) > 0.82) & (np.hypot(X, Y) < 1.5) & (top > gz + 0.8)] = LIT
    part[table] = LIT
    for a in np.radians(np.arange(prongs) * 360 / prongs + 180 / prongs):
        cx, cy = 1.75 * np.cos(a), 1.75 * np.sin(a)
        pr = (np.hypot(X - cx, Y - cy) <= 0.38) & (top >= 0) & (top <= gz + 0.6)
        tip = (np.hypot(X - cx * 0.85, Y - cy * 0.85) <= 0.32) & (top > gz + 0.6) & (top <= gz + 1.0)
        part[pr | tip] = PRONG
    if halo:
        for a in np.radians(np.arange(12) * 30):
            cx, cy = 2.4 * np.cos(a), 2.4 * np.sin(a)
            part[(np.hypot(X - cx, Y - cy) <= 0.35) & (top > 0.3) & (top <= 0.9)] = GEM
        part[(np.hypot(X, Y) > 2.0) & (np.hypot(X, Y) <= 2.85) & (top >= 0) & (top <= 0.4)] = BEZEL
    sh = (np.abs(Y) <= 0.8) & (np.abs(X) <= 2.4) & (top < 0) & (top > -0.9 - 0.6 * (height - 1)) & (r > R_IN + 0.6)
    part[sh & (part == EMPTY)] = BAND
    return part


def signet(trim="gold", worn=True):
    """J's "Lanterns show" feel (reports/Lanterns show power ring design.md), original emblem: a thick dark
    band, a low round signet face clearly wider than the band, a metal trim ring round the face, a deep
    green gem built of nested rings, and one simple original mark in the middle (a standing flame)."""
    part = np.zeros(X.shape, np.int8)
    r = np.hypot(X, Z)
    part[band(1.9, 0.9)] = BAND
    if worn:   # cracks: dark grooves running round the band
        crack = (np.abs(np.sin(np.arctan2(Z, X) * 7 + Y * 1.3)) < 0.12) & (r > R_IN + 0.6)
        part[band(1.9, 0.9) & crack] = DARK
    top = Z - (R_IN + 0.8)
    rr = np.hypot(X, Y)
    part[(rr <= 2.9) & (top >= -0.3) & (top <= 0.5)] = BAND          # the face's seat, band coloured
    part[(rr > 2.3) & (rr <= 2.9) & (top > 0.5) & (top <= 0.9)] = PRONG   # the trim ring (gold or silver)
    gem = (rr <= 2.3) & (top > 0.4) & (top <= 0.9)
    part[gem] = GEM
    part[gem & (((rr > 1.45) & (rr <= 1.75)) | (rr <= 0.5))] = LIT    # nested rings: a lit ring and a heart
    part[gem & (rr > 0.5) & (rr <= 0.8)] = DARK
    # The original mark: a small standing flame, raised a pixel above the gem.
    u, w = X, Y + 0.2
    flame = (np.hypot(u, w + 0.35) <= 0.75) | ((w > -0.35) & (np.abs(u) <= 0.75 * np.clip(1 - (w + 0.35) / 1.5, 0, 1) ** 1.3) & (w < 1.15))
    part[flame & (top > 0.9) & (top <= 1.2) & (rr <= 1.4)] = LIT
    return part


def square():
    """J's own concept image: a chunky faceted gunmetal band; a square gold face wider than the band with a
    green bar along its top and bottom edges, and between them a stepped gold frame round an octagonal,
    faceted emerald on a deep green ground."""
    part = np.zeros(X.shape, np.int8)
    ax, az = np.abs(X), np.abs(Z)
    oct_r = np.maximum(np.maximum(ax, az), (ax + az) / 1.35)          # faceted, octagonal outer profile
    inside = (oct_r <= R_IN + 1.3) & (np.hypot(X, Z) >= R_IN) & (np.abs(Y) <= 2.2)
    part[inside] = BAND
    top = Z - (R_IN + 1.0)
    ay = np.abs(Y)
    sq = (ax <= 2.95) & (ay <= 2.95)
    part[sq & (top >= -0.6) & (top < 0.25)] = BEZEL                  # the gold back plate
    lvl = (top >= 0.25) & (top < 0.75)                               # the face's first layer
    rim = lvl & sq & ((ax > 2.65) | (ay > 2.7))
    bars = lvl & (ax <= 2.95) & (ay >= 1.7) & (ay <= 2.95)
    part[bars] = PRONG
    part[bars & (ax <= 2.6) & (ay >= 1.95) & (ay <= 2.7)] = GEM       # wide green bars inside a thin gold outline
    part[rim] = PRONG
    mid = lvl & (ay < 1.7) & (ax <= 2.65)
    part[mid] = DARK                                                   # deep green ground
    # Stepped gold frame: posts at the sides, steps toward the gem at each corner.
    part[mid & (ax >= 1.95) & (ax <= 2.3)] = PRONG
    step = mid & (((ax >= 1.45) & (ax <= 1.75) & (ay >= 1.1) & (ay <= 1.6)) |
                  ((ay >= 1.4) & (ay <= 1.65) & (ax >= 0.9) & (ax <= 1.75)) |
                  ((ay >= 1.45) & (ay < 1.7) & (ax <= 0.95)))
    part[step] = PRONG
    # The octagonal faceted emerald, standing proud of the face.
    gem = (np.maximum(ax, ay) <= 1.3) & ((ax + ay) <= 1.85)
    part[gem & (top >= 0.25) & (top < 1.35 - 0.35 * np.maximum(ax, ay))] = GEM
    part[gem & (np.maximum(ax, ay) <= 0.55) & (top >= 0.9) & (top < 1.35)] = LIT       # the table catches the light
    return part


SQUARE_COL = {BAND: ((84, 86, 90), 1), BEZEL: ((196, 152, 58), 1), GEM: ((24, 170, 60), 4), LIT: ((150, 240, 160), 6),
              DARK: ((10, 64, 28), 0), PRONG: ((216, 176, 76), 1)}

SIGNETS = {"l1": dict(trim="gold", worn=True), "l2": dict(trim="silver", worn=False), "l3": dict(trim="gold", worn=True)}
STONE = {BAND: ((44, 46, 44), 1), BEZEL: ((44, 46, 44), 1), GEM: ((28, 150, 60), 4), LIT: ((150, 235, 150), 6),
         DARK: ((14, 16, 14), 0), PRONG: ((190, 146, 56), 1)}
ROOKIE = {BAND: ((22, 24, 24), 1), BEZEL: ((22, 24, 24), 1), GEM: ((30, 190, 74), 4), LIT: ((190, 255, 190), 6),
          DARK: ((6, 10, 8), 0), PRONG: ((176, 180, 184), 1)}
JADE = {BAND: ((52, 50, 46), 1), BEZEL: ((52, 50, 46), 1), GEM: ((40, 120, 70), 4), LIT: ((120, 200, 140), 6),
        DARK: ((16, 18, 16), 0), PRONG: ((150, 116, 50), 1)}

CROWNS = {
    "b1": dict(prongs=6, height=1.45),
    "b2": dict(prongs=4, height=1.0),
    "b3": dict(prongs=4, height=1.1, halo=True),
    "b4": dict(prongs=4, height=1.0, cut="emerald"),
}
SILVER = {BAND: ((150, 154, 158), 1), BEZEL: ((120, 124, 128), 1), GEM: ((30, 200, 70), 4), LIT: ((200, 255, 190), 6),
          DARK: ((10, 22, 14), 0), PRONG: ((170, 174, 178), 1)}
GOLD = {BAND: ((196, 150, 50), 1), BEZEL: ((170, 126, 40), 1), GEM: ((30, 200, 70), 4), LIT: ((200, 255, 190), 6),
        DARK: ((10, 22, 14), 0), PRONG: ((214, 170, 70), 1)}
BLACK = {BAND: ((26, 30, 28), 1), BEZEL: ((40, 44, 42), 1), GEM: ((30, 210, 80), 4), LIT: ((200, 255, 190), 6),
         DARK: ((10, 22, 14), 0), PRONG: ((170, 174, 178), 1)}

COL = {
    "a": {BAND: ((62, 72, 66), 1), BEZEL: ((84, 96, 88), 1), GEM: ((40, 210, 80), 4), LIT: ((210, 255, 200), 6),
          DARK: ((10, 22, 14), 0), PRONG: ((84, 96, 88), 1)},
    "b": {BAND: ((150, 154, 158), 1), BEZEL: ((120, 124, 128), 1), GEM: ((30, 200, 70), 4), LIT: ((200, 255, 190), 6),
          DARK: ((10, 22, 14), 0), PRONG: ((170, 174, 178), 1)},
    "c": {BAND: ((22, 26, 24), 1), BEZEL: ((36, 42, 38), 1), GEM: ((50, 230, 90), 4), LIT: ((190, 255, 180), 6),
          DARK: ((8, 14, 10), 0), PRONG: ((36, 42, 38), 1)},
}


def quads(part, v):
    occ = part > 0
    S = occ.shape
    Q, C, K = [], [], []
    for i, j, k in np.argwhere(occ):
        pid = int(part[i, j, k])
        c = np.array([X[i, j, k], Y[i, j, k], Z[i, j, k]])
        base, kind = COL[v][pid]
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a, b, cc = i + n[0], j + n[1], k + n[2]
            if 0 <= a < S[0] and 0 <= b < S[1] and 0 <= cc < S[2] and occ[a, b, cc]:
                continue
            nv = np.array(n, float)
            col = np.array(base, float)
            # Metal: brighter where the face looks outward from the finger, darker inside the hole.
            if kind == 1:
                out = np.dot(nv, np.array([c[0], 0, c[2]]) / (np.hypot(c[0], c[2]) + 1e-6))
                col *= 0.75 + 0.45 * max(0.0, out) + (0.15 if n[2] > 0 else 0)
            ax = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            bx = np.cross(nv, ax)
            f0 = c + nv * G / 2
            cs = [f0 + (ax * sa + bx * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(np.clip(col, 0, 255)); K.append(kind)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


COL.update({"b1": SILVER, "b2": GOLD, "b3": SILVER, "b4": BLACK, "l1": STONE, "l2": ROOKIE, "l3": JADE, "sq": SQUARE_COL})
_build = build


def build(v):
    if v == "sq":
        return square()
    if v in SIGNETS:
        return signet(**SIGNETS[v])
    return crown(**CROWNS[v]) if v in CROWNS else _build(v)


if __name__ == "__main__":
    for v in ("a", "b", "c", "b1", "b2", "b3", "b4", "l1", "l2", "l3", "sq"):
        q, c, k = quads(build(v), v)
        np.savez_compressed(os.path.join(OUT, f"ring_{v}.npz"), quads=q, col=c, kind=k)
        print(v, len(q), "faces", np.bincount(k, minlength=7))
