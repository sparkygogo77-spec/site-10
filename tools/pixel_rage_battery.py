"""The Red corps power battery, three takes for J (2026-10-13), from his reference sheet: a carved, weathered
stone battery with an arched rune handle, a capped top, a round front port wrapped in light, drum-like side
ports, a rune band above and below the barrel, and a stepped, buttressed base. Original marks only: the runes
are made up here, and the port carries a new sigil (three claw slashes in a ring), not any existing emblem.

  b1 monolith : the sheet's battery. Weathered red-brown stone, molten cracks over the barrel, glowing runes.
  b2 bleeding : darker stone; blood channels run from the port down the barrel into a brimming basin on the
                base, drips hang under the port.
  b3 engine   : rage made machine. Iron bands, the side panels opened to show glowing ribs and cables, spikes
                on the crown, a brighter core.

On the pixel grid like the lanterns: G = 0.5 model px (32 per block), about 3.3 blocks tall.
    python tools/pixel_rage_battery.py OUTDIR -> OUTDIR/battery_<v>.npz (quads, col, kind, glow)
z up, front faces -y. kinds: 0 shadowed stone, 1 stone/metal, 3 fleck, 4 dim glow (glass, blood), 5 vein/rune,
6 bright edge.
"""
import math, os, sys
import numpy as np

G = 0.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
AX = np.arange(-18, 18, G) + G / 2
AZ = np.arange(0, 54, G) + G / 2
X, Y, Z = np.meshgrid(AX, AX, AZ, indexing="ij")
R = np.hypot(X, Y)
TH = np.arctan2(Y, X)
rng = np.random.default_rng(31)
HASH = rng.random(X.shape)

EMPTY, STONE, DARK, FLECK, IRON, GLASS, BLOOD, VEIN, RUNE, BRIGHT = range(10)
PAL = {
    "b1": {STONE: (112, 52, 44), DARK: (58, 24, 22), FLECK: (150, 84, 70), IRON: (70, 62, 62),
           GLASS: (90, 6, 8), BLOOD: (150, 8, 12), VEIN: (230, 30, 24), RUNE: (255, 60, 40), BRIGHT: (255, 150, 120)},
    "b2": {STONE: (76, 30, 28), DARK: (36, 12, 12), FLECK: (110, 52, 46), IRON: (60, 52, 52),
           GLASS: (80, 2, 6), BLOOD: (170, 4, 14), VEIN: (220, 16, 24), RUNE: (255, 50, 40), BRIGHT: (255, 130, 110)},
    "b3": {STONE: (96, 46, 40), DARK: (44, 20, 18), FLECK: (140, 80, 66), IRON: (84, 78, 80),
           GLASS: (120, 10, 10), BLOOD: (160, 8, 10), VEIN: (245, 40, 24), RUNE: (255, 80, 50), BRIGHT: (255, 180, 140)},
}
KIND = {STONE: 1, DARK: 0, FLECK: 3, IRON: 1, GLASS: 4, BLOOD: 4, VEIN: 5, RUNE: 5, BRIGHT: 6}
GLOW = {GLASS: 0.35, BLOOD: 0.45, VEIN: 0.85, RUNE: 1.0, BRIGHT: 1.0}


def octr(x, y):
    return np.maximum(np.maximum(np.abs(x), np.abs(y)), (np.abs(x) + np.abs(y)) / math.sqrt(2))


def field3(seed, scale):
    """Smooth-ish 3D value noise on the grid (for cracks and weathering)."""
    r = np.random.default_rng(seed)
    n = [int(math.ceil(s / scale)) + 2 for s in X.shape]
    g = r.random(n)
    fx, fy, fz = [np.arange(s) * 1.0 / scale for s in X.shape]
    ix, iy, iz = [np.floor(f).astype(int) for f in (fx, fy, fz)]
    tx, ty, tz = [f - np.floor(f) for f in (fx, fy, fz)]
    tx, ty, tz = [t * t * (3 - 2 * t) for t in (tx, ty, tz)]
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (np.where(dx, tx, 1 - tx)[:, None, None] * np.where(dy, ty, 1 - ty)[None, :, None]
                     * np.where(dz, tz, 1 - tz)[None, None, :])
                out = out + w * g[np.ix_(ix + dx, iy + dy, iz + dz)]
    return out


def runes(band, seed, cell=2.0, height=None):
    """Made-up glyphs carved round a band: each angular cell gets a little 3x3 stroke pattern."""
    r = np.random.default_rng(seed)
    z0, z1 = Z[band].min(), Z[band].max()
    arc = TH * 11.0                       # ~11 px radius: arc length in px
    cu = np.floor(arc / (cell * 2)).astype(int)
    u = (arc / (cell * 2)) % 1
    v = (Z - z0) / max(z1 - z0, 1e-6)
    pats = r.random((400, 3, 3)) < 0.42
    pats[:, 1, 1] |= r.random(400) < 0.5
    pats[r.random(400) < 0.18] = False    # some blank spaces between words
    gx = np.clip((u * 4).astype(int) - 0, 0, 3) - 0
    gy = np.clip(((v - 0.15) / 0.7 * 3).astype(int), -1, 3)
    ok = (gx >= 0) & (gx < 3) & (gy >= 0) & (gy < 3) & (u > 0.12) & (u < 0.88)
    p = pats[cu % 400, np.clip(gx, 0, 2), np.clip(gy, 0, 2)]
    return band & ok & p


def battery(v):
    part = np.zeros(X.shape, np.int8)
    weather = field3(7 if v != "b2" else 8, 3.0)
    crackf = field3(11, 4.0)

    def put(m, c):
        part[m] = c

    # ---- base: stepped octagon with buttresses -------------------------------------------------------------
    o = octr(X, Y)
    put((Z < 2.5) & (o < 15.5), DARK)
    put((Z >= 2.5) & (Z < 5) & (o < 14), STONE)
    put((Z >= 5) & (Z < 7) & (o < 12.5), STONE)
    put((Z >= 7) & (Z < 8) & (o < 11.5), DARK)
    for k in range(8):                                     # buttress blocks round the lower step
        a = k * math.pi / 4 + math.pi / 8
        u = X * math.cos(a) + Y * math.sin(a); w = -X * math.sin(a) + Y * math.cos(a)
        put((Z >= 2.5) & (Z < 7.5 - (k % 2) * 1.5) & (u > 11) & (u < 16) & (np.abs(w) < 2.0), STONE)
        put((Z >= 2.5) & (Z < 7.5 - (k % 2) * 1.5) & (u > 15) & (u < 16) & (np.abs(w) < 1.2) & (np.abs(Z - 5) < 1.2), RUNE)
    # rune band above the base
    band = (Z >= 8) & (Z < 11.5) & (R < 10.5)
    put(band, STONE)
    put(runes(band & (R > 9.6), 41), RUNE)
    put((Z >= 11.5) & (Z < 13) & (R < 9.2), DARK)

    # ---- barrel ---------------------------------------------------------------------------------------------
    zb0, zb1 = 13.0, 35.0
    prof = 9.0 + 3.4 * np.sin(np.clip((Z - zb0) / (zb1 - zb0), 0, 1) * math.pi)
    barrel = (Z >= zb0) & (Z < zb1) & (R < prof)
    put(barrel, STONE)
    skin = barrel & (R > prof - 1.0)
    put(skin & (weather < 0.32), DARK)
    put(skin & (HASH < 0.025), FLECK)
    crack = skin & (np.abs(crackf - 0.5) < 0.022) & (Y > -prof + 1.5)
    put(crack, VEIN)

    # ---- the front port -------------------------------------------------------------------------------------
    pc = np.array([0.0, 0.0, 24.0])
    pr = np.hypot(X - pc[0], Z - pc[2])
    front_y = -(9.0 + 3.4)                                  # barrel front at its widest
    ring = (pr < 8.5) & (Y < front_y + 2.5) & (Y > front_y - 2.5)
    put(ring & (pr >= 6.4), STONE)
    put(ring & (pr >= 6.4) & (Y < front_y - 1.8), DARK)
    put(ring & (pr >= 6.4) & (weather < 0.35) & (Y < front_y - 1.5), DARK)
    put(ring & (pr >= 5.6) & (pr < 6.4), BRIGHT)             # the light ring round the port
    disc = (pr < 5.6) & (Y < front_y + 1.0) & (Y > front_y - 1.2)
    put(disc, GLASS)
    # the sigil: three claw slashes inside a thin ring
    lx, lz = X - pc[0], Z - pc[2]
    sig = disc & (Y < front_y - 0.5)
    for off in (-2.2, 0.0, 2.2):
        d = np.abs((lx - off) * 0.94 + lz * 0.34) - (0.55 - 0.08 * np.abs(lz) / 4.5)
        put(sig & (d < 0) & (np.abs(lz) < 4.3 - 0.6 * abs(off)), RUNE)
    put(sig & (np.abs(pr - 4.8) < 0.35), RUNE)
    # glow spilling round the port into the barrel
    put(barrel & (R > prof - 0.6) & (np.abs(pr - 9.4) < 0.5) & (Y < -6), VEIN)

    # ---- side drums -----------------------------------------------------------------------------------------
    for s in (-1, 1):
        dr = np.hypot(Y, Z - 24.0)
        drum = (s * X > 10.5) & (s * X < 14.5) & (dr < 6.5)
        put(drum, STONE)
        put(drum & (s * X > 14.0) & (dr < 4.5), DARK)
        put(drum & (s * X > 13.6) & (np.abs(dr - 5.3) < 0.45), BRIGHT)
        put(drum & (np.abs(dr - 6.0) < 0.5) & (HASH < 0.5) & (s * X < 13.0), DARK)
        put(drum & (s * X > 14.0) & (dr < 4.5) & runes((s * X > 14.0) & (dr < 4.5) & (dr > 2.5), 51 + s), RUNE)

    # ---- collar, top rune band, cap ---------------------------------------------------------------------------
    put((Z >= 35) & (Z < 37) & (R < 9.0), DARK)
    band2 = (Z >= 37) & (Z < 40.5) & (R < 10.2)
    put(band2, STONE)
    put(runes(band2 & (R > 9.3), 43), RUNE)
    cap = (Z >= 40.5) & (Z < 42.5) & (R < 9.0)
    put(cap, STONE)
    top = cap & (Z >= 42)
    put(top & (np.abs(R - 6.0) < 0.4), DARK)
    put(top & (R < 3.2) & (np.abs(np.sin(TH * 6 + R * 0.9)) < 0.35), DARK)      # an iris of blades
    put(top & (R < 1.0), VEIN)

    # ---- the arched handle with rune channels ----------------------------------------------------------------
    for s in (-1, 1):
        post = (np.abs(X - s * 12.5) < 1.5) & (np.abs(Y) < 1.8) & (Z >= 30) & (Z < 50)
        put(post, STONE)
        put(post & (Y < -1.2) & (np.abs(X - s * 12.5) < 0.6) & (Z > 32) & (Z < 49) & runes(post & (Y < -1.2), 61 + s), RUNE)
        clamp = (np.abs(X - s * 11.5) < 2.6) & (np.abs(Y) < 2.4) & (np.abs(Z - 38.5) < 1.6)
        put(clamp, DARK)
    bar = (np.abs(X) < 14.0) & (np.abs(Y) < 1.8) & (Z >= 48) & (Z < 51)
    put(bar, STONE)
    put(bar & (Y < -1.2) & (np.abs(Z - 49.5) < 0.6) & (np.abs(X) < 11) & runes(bar & (Y < -1.2), 71), RUNE)
    for xx_ in (-6, 0, 6):
        put((np.abs(X - xx_) < 1.2) & (np.abs(Y) < 2.3) & (Z >= 47.5) & (Z < 51.5), DARK)

    # ---- variants ---------------------------------------------------------------------------------------------
    if v == "b2":
        # blood channels from under the port, down the barrel, over the base step into a basin
        for x0 in (-3.0, -1.0, 1.0, 3.0):
            ch = (np.abs(X - x0) < 0.55) & (Y < 0) & (Z >= 8) & (Z < 16.5 + abs(x0) * 0.3)
            surf = (R > prof - 0.9) & (R < prof + 0.1) | ((Z < 13) & (R > 8.7) & (R < 10.6))
            put(ch & surf, BLOOD)
        basin = (Z >= 7) & (Z < 8.2) & (o < 12.2) & (o > 10.6)
        put(basin, BLOOD)
        put((Z >= 6.5) & (Z < 8.2) & (o >= 12.2) & (o < 12.8), DARK)
        for x0, ln in ((-4.0, 3.0), (-1.5, 4.5), (1.0, 2.2), (3.5, 3.6), (5.2, 1.6)):     # drips under the port
            dz = 24 - 6.6 - Z
            put((np.abs(X - x0) < 0.4 + 0.25 * (dz > ln - 0.8)) & (np.abs(Y - front_y + 0.5) < 0.6) & (dz > 0) & (dz < ln), BLOOD)
        put(skin & (np.abs(crackf - 0.5) < 0.035) & (Y < 0), BLOOD)
    if v == "b3":
        for zb in (15.5, 32.5):
            band3 = (np.abs(Z - zb) < 0.9) & (R < prof + 0.6) & (R > prof - 0.6)
            put(band3, IRON)
            put(band3 & (np.abs(np.sin(TH * 12)) < 0.12), BRIGHT)
        # open side panels with glowing ribs and cables
        for s in (-1, 1):
            win = barrel & (s * Y > -2) & (np.abs(X) > prof * 0.55) & (np.abs(Z - 24) < 7.5) & (np.abs(X) < prof) & (s * X > 0)
            put(win & (R > prof - 2.2), EMPTY)
            ribs = win & (R > prof - 2.6) & (R <= prof - 2.2)
            put(ribs, GLASS)
            for k in range(5):
                put(win & (np.abs(Z - (18.5 + k * 2.8)) < 0.45) & (R > prof - 2.4) & (R < prof - 1.2), IRON)
            put(win & (R > prof - 2.4) & (R < prof - 1.4) & (np.abs(np.sin(Z * 2.1 + TH * 9)) < 0.18), VEIN)
        for k in range(8):                                  # spikes round the crown
            a = k * math.pi / 4
            cx, cy = 8.0 * math.cos(a), 8.0 * math.sin(a)
            d = np.hypot(X - cx, Y - cy)
            put((Z >= 42.5) & (Z < 46.5) & (d < (46.5 - Z) * 0.32), IRON)
        put(disc & (Y > front_y - 0.6), BRIGHT)             # a brighter core behind the sigil
    return part


def quads(part, pal):
    occ = part > 0
    P = np.pad(occ, 1)
    Q, C, K, W = [], [], [], []
    light = np.array([-0.45, -0.75, 0.6]); light /= np.linalg.norm(light)
    for axis in range(3):
        for sgn in (1, -1):
            sh = np.roll(P, -sgn, axis=axis)[1:-1, 1:-1, 1:-1]
            expo = occ & ~sh
            idx = np.argwhere(expo)
            if not len(idx):
                continue
            ctr = np.stack([AX[idx[:, 0]], AX[idx[:, 1]], AZ[idx[:, 2]]], 1)
            n = np.zeros(3); n[axis] = sgn
            a = np.zeros(3); a[(axis + 1) % 3] = 1
            b = np.cross(n, a)
            f0 = ctr + n * G / 2
            cs = np.stack([f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))], 1)
            pid = part[idx[:, 0], idx[:, 1], idx[:, 2]]
            base = np.array([pal[p] for p in pid], float)
            kind = np.array([KIND[p] for p in pid], np.int8)
            glow = np.array([GLOW.get(p, 0.0) for p in pid], np.float32)
            jit = 1.0 + (HASH[idx[:, 0], idx[:, 1], idx[:, 2]] - 0.5) * 0.18
            shade = (0.78 + 0.3 * max(0.0, float(n @ light))) * jit
            col = np.clip(base * np.where(glow[:, None] > 0.5, 1.0, shade[:, None]), 0, 255)
            Q.append(cs); C.append(col); K.append(kind); W.append(glow)
    return (np.concatenate(Q).astype(np.float32), np.concatenate(C).astype(np.float32),
            np.concatenate(K), np.concatenate(W))


if __name__ == "__main__":
    for v in ("b1", "b2", "b3"):
        q, c, k, g = quads(battery(v), PAL[v])
        np.savez_compressed(os.path.join(OUT, f"battery_{v}.npz"), quads=q, col=c, kind=k, glow=g)
        print(v, len(q), "faces", np.bincount(k, minlength=7))
