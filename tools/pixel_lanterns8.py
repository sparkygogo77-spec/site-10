"""Pass 608: six variations of 607 D1b (Vault: molten), J's keeper: "this one is a keeper, i need more variation".

D1b's DNA, kept in every take: a glass vault between fluted gold pillars, gold drips running from the roof down the
panels and off the roof's edge, a stepped roof with a knuckled handle, see-through glass with the G3-flare core, the
sculpted port. Each take changes one big thing, built differently:
  D1b1 heavy pour: twice the drips, thicker, and gold pooling on the base steps;
  D1b2 hex molten: six panels and six pillars, drips between them;
  D1b3 tall molten: a taller, narrower vault, two-tier roof with a spiked crown, longer drips;
  D1b4 overflowing bowl: a glowing bowl crown that overflows, the drips start at the bowl and run over roof and panels;
  D1b5 caged molten: an outer cage of gold bars a pixel off the glass, drips caught between, a double knuckled handle;
  D1b6 squat molten: a lower, broader vault with deep dripping eaves and four short feet.
"""
import math
import numpy as np
from pixel_lanterns6 import G, grid, circle, ngon, glass, band, stepped, rod, ring_xz, EMPTY, SMOKE, GOLD, GOLD_DK, SILVER
import pixel_lanterns7 as P7
from pixel_lanterns7 import hollow, core, fin, drips, bowl, studs, knuckled_arch, sculpted_port, _pillars


def molten_vault(X, Y, Z, n=4, s=4.6, z0=5.0, z1=21.0, seed=81, n_drips=16, drip_r=1.0, roof=None, pillar_r=0.9,
                 handle="knuckle", base_extra=0.0, edge_drips=4, rnd=1.4):
    part = np.zeros(X.shape, np.int8)
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = s * (1 - 0.1 * np.sin(np.pi * H) ** 1.5) + 0.35 * np.exp(-((H - 0.5) / 0.12) ** 2)
    sec = ngon(X, Y, n, size, rnd=rnd if n == 4 else 0.0)
    glass(part, X, Y, Z, sec, z0, z1, seed=seed, craze=2.6, lines=4)
    hollow(part, sec)
    sh = lambda g: ngon(X, Y, n, s + g, rnd=rnd if n == 4 else 0.0)
    stepped(part, X, Y, Z, sh, z0, [(1.0, 0.5, GOLD_DK, None), (1.5 + base_extra, 0.75, GOLD, "zig"),
                                     (1.9 + base_extra, 0.5, GOLD, None), (1.4 + base_extra, 0.75, GOLD_DK, None),
                                     (2.2 + base_extra, 0.75, GOLD, "line")], down=True)
    zt = stepped(part, X, Y, Z, sh, z1, [(1.0, 0.5, GOLD_DK, None), (1.6, 0.75, GOLD, "dots"), (1.9, 0.5, GOLD, None)])
    zr = zt
    for k, (g, h) in enumerate(roof or ((1.6, 0.75), (0.9, 0.75), (0.2, 0.75), (-0.6, 0.75), (-1.5, 0.75))):
        band(part, X, Y, Z, sh(g), zt, zt + h, GOLD if k % 2 == 0 else GOLD_DK, "line" if k == 1 else None)
        zt += h
    # pillars at the corners
    R_c = s / math.cos(math.pi / n) * 0.9
    for k in range(n):
        a = -math.pi / 2 + math.pi / n + k * 2 * math.pi / n
        cx, cy = R_c * math.cos(a), R_c * math.sin(a)
        q = np.hypot(X - cx, Y - cy)
        pil = (q <= pillar_r) & (Z > z0 - 0.5) & (Z <= z1 + 0.5)
        part[pil] = GOLD
        ang = np.arctan2(Y - cy, X - cx)
        part[pil & (q > pillar_r - 0.3) & (np.round(ang / (math.pi / 4)) % 2 == 0)] = GOLD_DK
        for zc in (z0 + 0.6, z1 - 0.6, (z0 + z1) / 2):
            part[(q <= pillar_r + 0.25) & (np.abs(Z - zc) <= 0.3)] = GOLD
    # drips down the panels, and off the roof's edge (a stream and a bead below the eave)
    drips(part, X, Y, Z, sec, z1 - 0.1, n_drips, seed=seed * 10, zmin=z0 + 2.0)
    eave = s + 1.9
    rng = np.random.default_rng(seed + 5)
    for k in range(n):
        a = -math.pi / 2 + k * 2 * math.pi / n
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        for t in np.linspace(-0.7, 0.7, edge_drips):
            px, py = ux * eave + tx * t * eave * math.tan(math.pi / n), uy * eave + ty * t * eave * math.tan(math.pi / n)
            ln = rng.uniform(0.8, 2.4) * drip_r
            part[(np.hypot(X - px, Y - py) <= 0.25 * drip_r) & (Z > zr - ln) & (Z <= zr + 0.5)] = GOLD
            studs(part, X, Y, Z, [(px, py, zr - ln - 0.1)], r=0.35 * drip_r)
    if handle == "knuckle":
        knuckled_arch(part, X, Y, Z, zt - 0.5, 2.8, 3.6)
    elif handle == "double":
        knuckled_arch(part, X, Y, Z, zt - 0.5, 2.8, 3.6, y=-0.5)
        knuckled_arch(part, X, Y, Z, zt - 0.5, 2.8, 3.6, y=0.5)
    core(part, 0, 0, (z0 + z1) / 2, 2.8)
    pz = (z0 + z1) / 2
    sculpted_port(part, X, Y, Z, pz)
    return part, pz, sec, zt, zr


def d1b1_heavy(X, Y, Z):
    part, pz, sec, zt, zr = molten_vault(X, Y, Z, seed=81, n_drips=34, drip_r=1.35, edge_drips=6)
    rng = np.random.default_rng(811)
    for _ in range(14):                                                   # gold pooling on the base steps
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(5.6, 6.6)
        studs(part, X, Y, Z, [(rr * math.cos(a), rr * math.sin(a), 4.1)], r=rng.uniform(0.5, 0.9))
    return part, pz


def d1b2_hex(X, Y, Z):
    part, pz, *_ = molten_vault(X, Y, Z, n=6, s=4.8, seed=82, n_drips=18, edge_drips=3,
                                roof=((1.6, 0.75), (0.9, 0.75), (0.2, 0.75), (-0.6, 0.75), (-1.5, 0.75), (-2.3, 0.5)))
    return part, pz


def d1b3_tall(X, Y, Z):
    part, pz, sec, zt, zr = molten_vault(X, Y, Z, s=3.9, z0=4.5, z1=24.0, seed=83, n_drips=18, drip_r=1.2,
                                         roof=((1.6, 0.75), (0.8, 0.5), (1.2, 0.5), (0.2, 0.75), (-0.6, 0.75), (-1.4, 0.5)),
                                         handle=None)
    r = np.hypot(X, Y)
    for k in range(8):                                                    # spiked crown
        a = k * math.pi / 4
        rod(part, X, Y, Z, [(2.0 * math.cos(a), 2.0 * math.sin(a), zt), (2.5 * math.cos(a), 2.5 * math.sin(a), zt + 1.6 + 0.6 * (k % 2))], 0.3)
    part[(Z > zt) & (Z <= zt + 2.0) & (r <= 0.8)] = GOLD_DK
    ring_xz(part, X, Y, Z, zt + 3.0, 1.0, 0.3, GOLD, axis="y")
    return part, pz


def d1b4_bowl(X, Y, Z):
    part, pz, sec, zt, zr = molten_vault(X, Y, Z, seed=84, n_drips=20, handle=None)
    bowl(part, X, Y, Z, zt + 2.4, 2.6)
    part[(Z > zt) & (Z <= zt + 0.6) & (np.hypot(X, Y) <= 1.0)] = GOLD_DK
    rng = np.random.default_rng(841)
    for _ in range(9):                                                    # overflow: streams over the bowl's lip, down the roof
        a = rng.uniform(0, 2 * math.pi)
        ux, uy = math.cos(a), math.sin(a)
        pts = [(2.7 * ux, 2.7 * uy, zt + 2.4), (3.4 * ux, 3.4 * uy, zt + 0.6), (5.5 * ux, 5.5 * uy, zr + 0.6),
               (6.3 * ux, 6.3 * uy, zr - rng.uniform(0.8, 2.2))]
        rod(part, X, Y, Z, pts, 0.3)
        studs(part, X, Y, Z, [pts[-1]], r=0.45)
    return part, pz


def d1b5_caged(X, Y, Z):
    part, pz, sec, zt, zr = molten_vault(X, Y, Z, seed=85, n_drips=12, handle="double", pillar_r=1.0)
    z0, z1 = 5.0, 21.0
    for k in range(4):                                                    # outer cage: bars a pixel off each panel
        a = -math.pi / 2 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        for t in (-2.2, -0.9, 0.9, 2.2):
            if k == 0 and abs(t) < 1.5:
                continue                                                  # leave the port clear
            px, py = ux * 5.9 + tx * t, uy * 5.9 + ty * t
            part[(np.hypot(X - px, Y - py) <= 0.3) & (Z > z0) & (Z <= z1)] = GOLD
            studs(part, X, Y, Z, [(px, py, z0 + 5 + 3 * ((k + int(t * 10)) % 3))], r=0.42)   # drips caught on the bars
        part[(np.abs((X * ux + Y * uy) - 5.9) <= 0.3) & (np.abs(X * tx + Y * ty) <= 2.6) &
             (np.abs(Z - (z0 + z1) / 2) <= 0.3) & ~((k == 0) & (np.abs(X) < 2.8))] = GOLD_DK
    return part, pz


def d1b6_squat(X, Y, Z):
    part, pz, sec, zt, zr = molten_vault(X, Y, Z, s=5.6, z0=6.0, z1=17.0, seed=86, n_drips=18, edge_drips=5, drip_r=1.25,
                                         roof=((2.4, 0.5), (1.8, 0.75), (0.9, 0.75), (0.0, 0.75), (-1.0, 0.75), (-2.0, 0.75),
                                               (-3.0, 0.5)), base_extra=0.4)
    for sx in (-1, 1):                                                    # four short feet
        for sy in (-1, 1):
            q = np.hypot(X - sx * 5.6, Y - sy * 5.6)
            part[(q <= 1.0) & (Z > 0.5) & (Z <= 2.4)] = GOLD
            part[(q <= 1.3) & (Z > 0.0) & (Z <= 0.5)] = GOLD_DK
    return part, pz


DESIGNS = {"D1b1": ("Molten: heavy pour", d1b1_heavy), "D1b2": ("Molten: hex", d1b2_hex),
           "D1b3": ("Molten: tall", d1b3_tall), "D1b4": ("Molten: overflowing bowl", d1b4_bowl),
           "D1b5": ("Molten: caged", d1b5_caged), "D1b6": ("Molten: squat", d1b6_squat)}


def build(code):
    X, Y, Z = grid()
    return DESIGNS[code][1](X, Y, Z)


quads = P7.quads
model_boxes = P7.model_boxes
