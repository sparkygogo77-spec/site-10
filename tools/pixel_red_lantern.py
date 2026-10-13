"""The Red Lantern, rebuilt on Minecraft's pixel grid: every cube is one texture pixel (0.25 units,
64 per block), so the veins, the emblem, rivets and vents are drawn pixel by pixel.

Three clearly different takes on J's current model (red glass barrel, copper metal, the front emblem,
a frame with a hanging ring):
- r1 "Barrel": J's lantern refined. Round barrel of red glass with proud branching veins, two riveted
  copper hoops, a raised emblem medallion, vented stepped cap with a sunburst top, the Y-post frame,
  arch and ring, blood drips running over the fluted foot.
- r2 "Heart": a heart-shaped chamber in a cage of eight copper ribs, a studded girdle carrying a big
  emblem, a thorn crown on top, a claw-footed cup below and a leather-wrapped ring handle.
- r3 "Octagon": an eight-sided lamp with copper corner pillars and glass panels, the emblem cut
  through a front plate so the light shines out of it, a pagoda roof with curled eaves, a finial
  and a hook ring.

    python tools/pixel_red_lantern.py <out dir> [r1 r2 r3]

Writes red_<version>.npz: quads (n,4,3) in units of 1/16 block (x right, y back so the front faces
-y, z up), col (n,3) sRGB, kind (n) 0 matte / 1 metal / 4 glass / 5 glow, glow (n) 0..1.
"""
import math, os, sys
import numpy as np

G = 0.25
(EMPTY, GLASS, VEIN, VEIN_P, COPPER, COPPER_DK, COPPER_LT, DARK, EMB, EMB_HI, HOLE, DRIP, BRASS,
 LEATHER) = range(14)

PAL = {GLASS: (150, 18, 30), VEIN: (255, 78, 52), VEIN_P: (226, 44, 38), COPPER: (190, 110, 62),
       COPPER_DK: (118, 62, 34), COPPER_LT: (236, 162, 106), DARK: (40, 20, 18), EMB: (240, 26, 26),
       EMB_HI: (255, 132, 96), HOLE: (12, 6, 6), DRIP: (124, 6, 14), BRASS: (220, 176, 86),
       LEATHER: (74, 38, 26)}
KIND = {GLASS: 4, VEIN: 5, VEIN_P: 5, COPPER: 1, COPPER_DK: 1, COPPER_LT: 1, DARK: 0, EMB: 5,
        EMB_HI: 5, HOLE: 0, DRIP: 4, BRASS: 1, LEATHER: 0}
# how much each part lights up when the lantern is charged (the glass is scaled by height below)
GLOW = {GLASS: 0.35, VEIN: 1.0, VEIN_P: 0.85, EMB: 1.0, EMB_HI: 1.25, DRIP: 0.15}

xs = np.arange(-10, 10, G) + G / 2
zs = np.arange(0, 30, G) + G / 2
X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
R = np.hypot(X, Y)
ANG = np.arctan2(Y, X)


# ---- the emblem, drawn on a 22 x 22 pixel grid ----------------------------------------------------
def emblem(u, v, s=1.0):
    """The Red Lantern symbol at pixel offsets (u right, v up) from its centre, s = scale.
    Returns 0 nothing, 1 copper rim, 2 rivet, 3 dark backing, 4 symbol, 5 symbol highlight, 6 drip."""
    u, v = np.asarray(u) / s, np.asarray(v) / s
    r = np.hypot(u, v)
    out = np.zeros(np.broadcast(u, v).shape, np.int8)
    out[r <= 11] = 1                                     # copper rim, r 9..11
    out[r <= 9] = 3                                      # dark backing
    ring = (r >= 6.4) & (r <= 8.3)                       # the circle, two pixels thick
    bar = (np.abs(v) <= 1.6) & (np.abs(u) <= 10.2)       # the bar, cut right through the rim
    out[ring | bar] = 4
    out[((r >= 7.0) & (r <= 8.3) & (v > 1.6)) | ((v > 0.9) & (v <= 1.6) & (np.abs(u) <= 10.2))] = 5
    for du, n in ((-2.5, 2), (2.5, 3)):                  # blood running off the bar's underside
        out[(np.abs(u - du) <= 0.5) & (v < -1.6) & (v >= -1.6 - n)] = 6
    rv = np.zeros_like(r, bool)
    for a in (45, 135, 225, 315):                         # four rivets in the rim
        rv |= np.hypot(u - 10 * math.cos(math.radians(a)), v - 10 * math.sin(math.radians(a))) <= 0.75
    out[rv & (r > 9)] = 2
    return out


def emblem_to_parts(e):
    m = np.full(e.shape, EMPTY, np.int8)
    for code, pid in ((1, COPPER), (2, BRASS), (3, DARK), (4, EMB), (5, EMB_HI), (6, EMB)):
        m[e == code] = pid
    return m


def medallion(part, cx, cz, fy, s=1.0, depth=1.0):
    """A raised emblem disc on the front: backing plate from the body out to fy, the rim one pixel
    proud of that, the symbol one pixel proud of the backing."""
    u = (X - cx) / G
    v = (Z - cz) / G
    e = emblem(u, v, s)
    pid = emblem_to_parts(e)
    back = (e > 0) & (Y >= fy) & (Y <= fy + depth)
    part[back] = np.where(e[back] == 3, DARK, COPPER_DK)
    lay = (Y >= fy - G) & (Y < fy) & np.isin(e, (1, 2, 4, 5, 6))
    part[lay] = pid[lay]
    top = (Y >= fy - 2 * G) & (Y < fy - G) & np.isin(e, (2, 5))
    part[top] = pid[top]


# ---- veins: branching paths drawn on the unwrapped glass --------------------------------------------
def vein_map(nu, nz, seed, trunks, branch=0.07, wander=0.35, from_top=0.3):
    """A (nu, nz) map of 0 none / 1 thin / 2 thick vein pixels, u wrapping round the body."""
    rng = np.random.default_rng(seed)
    M = np.zeros((nu, nz), np.int8)
    stack = []
    for _ in range(trunks):
        up = rng.random() > from_top
        stack.append((rng.uniform(0, nu), 0 if up else nz - 1, 1 if up else -1,
                      rng.normal(0, 0.4), 2, int(rng.integers(nz // 2, nz))))
    while stack:
        u, z, dz, du, w, n = stack.pop()
        for _ in range(n):
            if not 0 <= z < nz:
                break
            ui = int(u) % nu
            M[ui, z] = max(M[ui, z], w)
            if w == 2:
                M[(ui + 1) % nu, z] = max(M[(ui + 1) % nu, z], 1)
            du = np.clip(du + rng.normal(0, wander), -1.6, 1.6)
            if abs(du) > 1:               # a sideways step: fill the corner so the line stays joined
                u += math.copysign(1, du)
                M[int(u) % nu, z] = max(M[int(u) % nu, z], w)
            else:
                u += du
            z += dz
            if rng.random() < branch and len(stack) < 400:
                stack.append((u, z, dz, -du + rng.choice((-1.2, 1.2)), 1, int(rng.integers(4, nz // 3))))
            if w == 2 and rng.random() < 0.012:
                w = 1
    return M


def paint_veins(part, body, d, z0, z1, seed, trunks, **kw):
    """Veins on the glass surface: thin ones flush, thick ones standing a pixel proud."""
    nu = int(round(2 * math.pi * 5.5 / G))
    nz = int(round((z1 - z0) / G))
    M = vein_map(nu, nz, seed, trunks, **kw)
    ui = (((ANG + math.pi) / (2 * math.pi)) * nu).astype(int) % nu
    zi = np.clip(((Z - z0) / G).astype(int), 0, nz - 1)
    v = M[ui, zi]
    skin = body & (d <= 0) & (d > -G) & (part == GLASS)
    part[skin & (v >= 1)] = VEIN
    proud = body & (d > 0) & (d <= G) & (part == EMPTY) & (v == 2)
    part[proud] = VEIN_P


def torus_xz(cx, cz, rad, tube, y0=0.0):
    return np.hypot(np.hypot(X - cx, Z - cz) - rad, Y - y0) <= tube


def torus_yz(cy, cz, rad, tube, x0=0.0):
    return np.hypot(np.hypot(Y - cy, Z - cz) - rad, X - x0) <= tube


def drips(part, angles, z_top, z_bot, r_at, rng):
    """Blood running down over the foot: a one-pixel line a pixel proud, ending in a 2x2 bead."""
    for a in angles:
        length = rng.uniform(0.5, 1.0) * (z_top - z_bot)
        zb = z_top - length
        da = np.abs((np.degrees(ANG) - a + 180) % 360 - 180) * math.pi / 180 * 5.5
        r_here = r_at(Z)
        line = (da < G * 0.5) & (Z <= z_top) & (Z > zb) & (R > r_here) & (R <= r_here + G)
        bead = (da < G) & (Z <= zb + 2 * G) & (Z > zb - G) & (R > r_here) & (R <= r_here + 2 * G)
        part[(line | bead) & (part == EMPTY)] = DRIP


# ---- r1: the barrel ---------------------------------------------------------------------------------
def build_r1():
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 4.0, 17.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    rad = 5.0 + 0.55 * np.sin(math.pi * H)
    d = R - rad
    body = (Z > z0) & (Z <= z1)
    part[body & (d <= 0)] = GLASS
    paint_veins(part, body, d, z0, z1, seed=11, trunks=9)
    # riveted hoops, two pixels tall and a pixel proud
    for zc in (8.0, 13.5):
        rc = 5.0 + 0.55 * math.sin(math.pi * (zc - z0) / (z1 - z0))
        hoop = (np.abs(Z - zc) <= G) & (R <= rc + G) & (R > rc - G)
        part[hoop] = COPPER
        part[(np.abs(Z - zc) <= G) & (R > rc + G) & (R <= rc + 2 * G) & (np.abs(Z - zc) <= G / 2 + 0.01)
             & (((np.degrees(ANG) + 180) // 2.5).astype(int) % 12 == 0)] = BRASS
        part[(Z > zc - G * 1.01) & (Z <= zc - G * 0.99) & (R <= rc + G) & (R > rc)] = COPPER_DK
    # fluted stepped foot
    flute = ((np.degrees(ANG) + 180) // 7.5).astype(int) % 2 == 0
    part[(Z <= 0.75) & (R <= 6.75)] = COPPER_DK
    part[(Z > 0.75) & (Z <= 1.25) & (R <= 6.5)] = COPPER_LT
    part[(Z > 1.25) & (Z <= 2.0) & (R <= 6.1)] = COPPER
    lip = (Z > 2.0) & (Z <= z0) & (R <= 5.85)
    part[lip] = COPPER
    part[lip & flute & (R > 5.6)] = COPPER_DK
    part[(Z > z0 - G) & (Z <= z0) & (R <= 6.0)] = COPPER_LT
    # cap: lip, vented drum, step, sunburst top
    part[(Z > z1) & (Z <= z1 + 0.5) & (R <= 5.3)] = COPPER_DK
    drum = (Z > z1 + 0.5) & (Z <= z1 + 2.5) & (R <= 4.4)
    part[drum] = COPPER
    vent = drum & (R > 4.4 - G) & (Z > z1 + 1.0) & (Z <= z1 + 2.0) & \
           (((np.degrees(ANG) + 180 + 11.25) // 22.5).astype(int) % 2 == 0) & \
           (np.abs(((np.degrees(ANG) + 180) % 22.5) - 11.25) < 4)
    part[vent] = HOLE
    part[(Z > z1 + 2.5) & (Z <= z1 + 3.25) & (R <= 3.9)] = COPPER_DK
    top = (Z > z1 + 3.25) & (Z <= z1 + 3.75) & (R <= 3.5)
    part[top] = COPPER_DK
    ray = ((np.degrees(ANG) + 180) // 15).astype(int) % 2 == 0
    part[top & (Z > z1 + 3.5) & (R <= 2.75) & ray] = BRASS
    part[top & (Z > z1 + 3.5) & (R <= 1.0)] = BRASS
    # emblem medallion on the front, back plate on the back
    ez = 10.75
    fy = -(5.0 + 0.55 * math.sin(math.pi * (ez - z0) / (z1 - z0))) - 0.5
    part[(np.hypot(X, Z - ez) <= 11 * G) & (Y < fy + 1.0) & (Y > fy) & (part == EMPTY)] = COPPER_DK
    medallion(part, 0.0, ez, fy)
    by = 5.4
    plate = (np.abs(X) <= 2.0) & (np.abs(Z - ez) <= 2.0) & (Y > 4.5) & (Y <= by + G)
    part[plate] = COPPER_DK
    part[plate & (Y > by) & (np.abs(X) <= 1.75) & (np.abs(Z - ez) <= 1.75)] = COPPER
    for sx in (-1.5, 1.5):
        for sz in (-1.5, 1.5):
            part[(np.hypot(X - sx, Z - ez - sz) <= 0.3) & (Y > by) & (Y <= by + 2 * G)] = BRASS
    part[(np.abs(X) <= 0.4) & (np.abs(Z - ez) <= 0.75) & (Y > by + G) & (Y <= by + 2 * G)] = BRASS
    # frame: two posts, Y forks, an arch, the hanging ring
    for sx in (-1, 1):
        post = (np.abs(X - sx * 6.9) <= 0.375) & (np.abs(Y) <= 0.25) & (Z > 0.75) & (Z <= 19.5)
        part[post] = COPPER
        part[(np.abs(X - sx * 6.6) <= 0.6) & (np.abs(Y) <= 0.5) & (Z > 0.5) & (Z <= 1.75)] = COPPER_DK
        for zb in (8.0, 13.5):                         # brackets tying the posts to the hoops
            part[(np.abs(Z - zb) <= G) & (np.abs(Y) <= G) & (sx * X > 5.3) & (sx * X < 6.6)] = COPPER_DK
        fork = (np.abs(X - sx * (6.9 + (Z - 19.5) * 0.45)) <= 0.375) & (np.abs(Y) <= 0.25) & \
               (Z > 19.5) & (Z <= 23.5)
        part[fork] = COPPER
        part[(np.abs(X - sx * (6.9 + 4 * 0.45)) <= 0.5) & (np.abs(Y) <= 0.375) & (Z > 23.25) & (Z <= 23.75)] = COPPER_LT
    arch = (np.abs(np.hypot(X, Z - 19.5) - 6.9) <= 0.375) & (np.abs(Y) <= 0.25) & (Z > 19.5)
    part[arch] = COPPER
    part[torus_xz(0, 27.6, 1.15, 0.33)] = COPPER_LT
    part[(np.abs(X) <= 0.5) & (np.abs(Y) <= 0.375) & (Z > 26.0) & (Z <= 26.6)] = COPPER_DK
    rng = np.random.default_rng(3)
    drips(part, (-120, -60, -10, 35, 100, 160), z0, 1.5, lambda z: np.where(z > 2, 5.85, 6.1), rng)
    return part, (z0, z1), ez


# ---- r2: the heart ----------------------------------------------------------------------------------
def build_r2():
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 5.0, 19.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    rad = 6.2 * np.sqrt(np.clip(1 - ((H - 0.42) / 0.62) ** 2, 0.02, 1))
    d = R - rad
    body = (Z > z0) & (Z <= z1)
    part[body & (d <= 0)] = GLASS
    paint_veins(part, body, d, z0, z1, seed=23, trunks=14, branch=0.1, wander=0.45)
    # eight copper ribs following the body, two pixels wide, a pixel proud
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        arc = np.abs(np.angle(np.exp(1j * (ANG - a)))) * np.maximum(rad, 1)
        rib = body & (arc <= G * 1.01) & (d > -G) & (d <= G)
        part[rib] = COPPER
        part[rib & (arc > G * 0.5) & (d > 0)] = COPPER_DK
    # studded girdle carrying the emblem
    gz = 11.0
    rg = 6.2 * math.sqrt(max(1 - (((gz - z0) / (z1 - z0) - 0.42) / 0.62) ** 2, 0.02))
    gird = (np.abs(Z - gz) <= 0.5) & (R <= rg + G) & (R > rg - G)
    part[gird] = COPPER_DK
    part[(np.abs(Z - gz) <= G) & (R > rg + G) & (R <= rg + 2 * G) &
         (((np.degrees(ANG) + 180) // 3.75).astype(int) % 6 == 0)] = BRASS
    fy = -rg - 0.5
    part[(np.hypot(X, Z - gz) <= 14 * G) & (Y < fy + 1.25) & (Y > fy) & (part == EMPTY)] = COPPER_DK
    medallion(part, 0.0, gz, fy, s=1.3)
    # claw cup and three claw feet
    cup = (Z > 2.25) & (Z <= z0 + 0.25) & (R <= 2.6 + (Z - 2.25) * 0.7)
    part[cup] = COPPER
    part[cup & (Z > z0 - 0.25)] = COPPER_LT
    part[(Z > 1.5) & (Z <= 2.25) & (R <= 2.9)] = COPPER_DK
    for k in range(3):
        a = math.radians(90 + 120 * k)
        ca, sa = math.cos(a), math.sin(a)
        along = X * ca + Y * sa
        across = -X * sa + Y * ca
        # a claw arching from the cup out and down to a three-toed foot
        cz = 2.6 - 0.12 * (along - 2.0) ** 2
        claw = (along > 1.5) & (along <= 5.5) & (np.abs(across) <= 0.375) & (np.abs(Z - cz) <= 0.4)
        part[claw & (Z > 0)] = COPPER
        for t in (-0.6, 0.0, 0.6):
            toe = (np.hypot(along - 5.5, across - t) <= 0.35) & (Z <= 0.75)
            part[toe] = COPPER_DK
        part[(np.hypot(along - 5.6, across) <= 0.3) & (Z > 0.75) & (Z <= 1.25)] = BRASS
    # neck, thorn crown, stem and knob
    part[(Z > z1 - 0.25) & (Z <= z1 + 1.0) & (R <= 2.7)] = COPPER_DK
    part[(Z > z1 + 1.0) & (Z <= z1 + 1.75) & (R <= 3.1) & (R > 1.6)] = COPPER
    for k in range(8):
        a = math.radians(45 * k)
        cx, cy = 2.6 * math.cos(a), 2.6 * math.sin(a)
        t = np.clip((Z - (z1 + 1.75)) / 2.5, 0, 1)
        lean = 0.5 * t
        thorn = (np.hypot(X - cx * (1 + lean / 2.6), Y - cy * (1 + lean / 2.6)) <= 0.55 * (1 - t) + 0.05) & \
                (Z > z1 + 1.75) & (Z <= z1 + 4.25)
        part[thorn] = COPPER if k % 2 else COPPER_LT
    part[(Z > z1 + 1.0) & (Z <= z1 + 3.5) & (R <= 0.75)] = COPPER_DK
    part[(np.hypot(R, Z - (z1 + 4.0)) <= 0.8)] = BRASS
    # the ring handle: copper ring with a leather-wrapped grip at the top
    ring = torus_xz(0, z1 + 8.0, 3.2, 0.45)
    part[ring & (Z > z1 + 4.6)] = COPPER
    wrap = torus_xz(0, z1 + 8.0, 3.2, 0.6) & (Z > z1 + 9.5)
    part[wrap] = LEATHER
    part[wrap & ((np.floor(np.degrees(np.arctan2(Z - z1 - 8.0, X)) / 8) % 2) == 0) &
         (np.hypot(np.hypot(X, Z - z1 - 8.0) - 3.2, Y) > 0.45)] = COPPER_DK
    return part, (z0, z1), gz


# ---- r3: the octagon ---------------------------------------------------------------------------------
def oct_d(apothem):
    """Distance outside a regular octagon with flat faces front/back/left/right (positive outside)."""
    k = math.cos(math.radians(45))
    return np.maximum.reduce([np.abs(X), np.abs(Y), (np.abs(X) + np.abs(Y)) * k]) - apothem


def build_r3():
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 3.5, 17.5
    A = 5.0
    d = oct_d(A - G)
    body = (Z > z0) & (Z <= z1)
    part[body & (d <= 0)] = GLASS
    paint_veins(part, body, d, z0, z1, seed=37, trunks=10, branch=0.08)
    corner_r = A / math.cos(math.radians(22.5))
    # plinth
    part[(Z <= 1.0) & (oct_d(6.25) <= 0)] = COPPER_DK
    part[(Z > 1.0) & (Z <= 2.0) & (oct_d(5.9) <= 0)] = COPPER
    pl = (Z > 2.0) & (Z <= z0) & (oct_d(5.6) <= 0)
    part[pl] = COPPER_DK
    part[pl & (oct_d(5.6) > -G) & (Z > 2.5) & (Z <= 3.0)] = COPPER_LT
    # frame bars round every face: bottom, middle, top
    for za, zb in ((z0, z0 + 0.75), (10.25, 10.75), (z1 - 0.75, z1)):
        part[(Z > za) & (Z <= zb) & (oct_d(A + G) <= 0) & (oct_d(A - 2 * G) > 0)] = COPPER
    # corner pillars with a groove, a base block and a capital
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        cx, cy = corner_r * math.cos(a), corner_r * math.sin(a)
        pil = (np.maximum(np.abs(X - cx), np.abs(Y - cy)) <= 0.4) & (Z > z0) & (Z <= z1)
        part[pil] = COPPER
        part[pil & (np.hypot(X - cx, Y - cy) <= 0.2)] = COPPER_DK
        for za, zb in ((z0, z0 + 0.75), (z1 - 0.75, z1)):
            part[(np.maximum(np.abs(X - cx), np.abs(Y - cy)) <= 0.6) & (Z > za) & (Z <= zb)] = COPPER_LT
    # the front plate with the emblem cut through it; the glass behind the cut glows
    ez = 10.5
    fy = -(A + G)
    u, v = X / G, (Z - ez) / G
    e = emblem(u, v, 1.15)
    plate = (np.abs(X) <= 3.25) & (Z > z0 + 1.0) & (Z <= z1 - 1.0) & (Y > fy - G) & (Y <= fy + G)
    part[plate] = COPPER
    edge = plate & ((np.abs(X) > 3.0) | (Z <= z0 + 1.25) | (Z > z1 - 1.25))
    part[edge] = COPPER_DK
    cut = plate & np.isin(e, (4, 5, 6))
    part[cut] = EMPTY
    behind = (Y > fy + G) & (Y <= fy + 2 * G) & np.isin(e, (4, 5, 6))
    part[behind] = np.where(e[behind] == 5, EMB_HI, EMB)
    part[plate & (e == 1) & (Y <= fy)] = COPPER_LT
    part[(Y > fy - 2 * G) & (Y <= fy - G) & (e == 2)] = BRASS
    for sx, sz in ((-2.75, z0 + 1.75), (2.75, z0 + 1.75), (-2.75, z1 - 1.75), (2.75, z1 - 1.75)):
        part[(np.hypot(X - sx, Z - sz) <= 0.3) & (Y > fy - 2 * G) & (Y <= fy - G)] = BRASS
    # pagoda roof: eave with curled corners, two tiers, ridges, finial and hook ring
    eave = (Z > z1) & (Z <= z1 + 0.75) & (oct_d(6.4) <= 0)
    part[eave] = COPPER_DK
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        cr = 6.4 / math.cos(math.radians(22.5))
        cx, cy = (cr - 0.3) * math.cos(a), (cr - 0.3) * math.sin(a)
        part[(np.hypot(X - cx, Y - cy) <= 0.45) & (Z > z1 + 0.5) & (Z <= z1 + 1.5)] = COPPER_LT
    t = np.clip((Z - (z1 + 0.75)) / 2.5, 0, 1)
    tier1 = (Z > z1 + 0.75) & (Z <= z1 + 3.25) & (oct_d(5.6 - 2.6 * t) <= 0)
    part[tier1] = COPPER
    ridge = tier1 & (np.abs(np.angle(np.exp(1j * (ANG - math.radians(22.5)) * 4))) < 0.35) & \
            (oct_d(5.6 - 2.6 * t) > -G)
    part[ridge] = COPPER_LT
    band = (Z > z1 + 3.25) & (Z <= z1 + 3.75) & (oct_d(3.2) <= 0)
    part[band] = COPPER_DK
    t2 = np.clip((Z - (z1 + 3.75)) / 1.75, 0, 1)
    part[(Z > z1 + 3.75) & (Z <= z1 + 5.5) & (oct_d(2.6 - 1.4 * t2) <= 0)] = COPPER
    part[np.hypot(R, Z - (z1 + 6.25)) <= 0.9] = BRASS
    part[torus_yz(0, z1 + 8.4, 1.35, 0.33)] = COPPER_LT
    rng = np.random.default_rng(9)
    drips(part, (-100, -75, 15, 140, 200), z0 + 0.25, 1.0, lambda z: np.where(z > 2, 5.6 / math.cos(math.radians(22.5)) * 0.95, 5.9), rng)
    return part, (z0, z1), ez


BUILDS = {"r1": build_r1, "r2": build_r2, "r3": build_r3}


def quads(part, zr, ez):
    """Every exposed cube face as a quad, coloured with a little per-pixel variation and a soft
    occlusion term from the neighbouring cubes."""
    occ = part > 0
    z0, z1 = zr
    # crevice darkening: how many of the 26 neighbours are filled
    pad = np.pad(occ, 1).astype(np.int8)
    nb = sum(np.roll(np.roll(np.roll(pad, a, 0), b, 1), c, 2)
             for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1))[1:-1, 1:-1, 1:-1]
    Q, C, K, W = [], [], [], []
    for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        nb_occ = np.roll(occ, (-n[0], -n[1], -n[2]), (0, 1, 2))
        ax = int(np.argmax(np.abs(n)))
        edge = [slice(None)] * 3
        edge[ax] = -1 if n[ax] > 0 else 0
        nb_occ[tuple(edge)] = False
        exp = occ & ~nb_occ
        idx = np.argwhere(exp)
        if not len(idx):
            continue
        i, j, k = idx.T
        pid = part[i, j, k]
        c = np.stack([xs[i], xs[j], zs[k]], -1)
        # occlusion sampled from the cell the face looks into
        oi, oj, ok = (np.clip(i + n[0], 0, occ.shape[0] - 1), np.clip(j + n[1], 0, occ.shape[1] - 1),
                      np.clip(k + n[2], 0, occ.shape[2] - 1))
        ao = 1.0 - 0.035 * np.clip(nb[oi, oj, ok] - 3, 0, 12)
        h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
        base = np.array([PAL[p] for p in pid], float)
        col = base * (0.94 + 0.12 * h[:, None] / 255) * ao[:, None]
        # the glass is deepest at its ends, clearest in the middle
        hz = np.clip((c[:, 2] - z0) / (z1 - z0), 0, 1)
        gl = pid == GLASS
        col[gl] *= (0.72 + 0.4 * np.sin(math.pi * hz[gl]))[:, None]
        kind = np.array([KIND[p] for p in pid], np.int8)
        g = np.array([GLOW.get(p, 0.0) for p in pid], float)
        g[gl] *= 0.5 + 0.8 * np.sin(math.pi * hz[gl])
        hv = ((i * 2654435761) ^ (j * 40503) ^ (k * 2246822519)) & 1023
        g *= np.where(np.isin(pid, (GLASS, VEIN, VEIN_P)), 0.7 + 0.3 * hv / 1023, 1.0)
        nv = np.array(n, float)
        a = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
        b = np.cross(nv, a)
        f0 = c + nv * G / 2
        corners = [f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        if np.dot(np.cross(corners[1][0] - corners[0][0], corners[2][0] - corners[0][0]), nv) < 0:
            corners = corners[::-1]
        Q.append(np.stack(corners, 1)); C.append(np.clip(col, 0, 255)); K.append(kind); W.append(g)
    return (np.concatenate(Q).astype(np.float32), np.concatenate(C).astype(np.float32),
            np.concatenate(K), np.concatenate(W).astype(np.float32))


if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[2:] or list(BUILDS)
    for name in names:
        part, zr, ez = BUILDS[name]()
        q, c, k, w = quads(part, zr, ez)
        np.savez_compressed(os.path.join(OUT, f"red_{name}.npz"), quads=q, col=c, kind=k, glow=w,
                            emblem_z=ez)
        print(name, int((part > 0).sum()), "cubes,", len(q), "faces")
