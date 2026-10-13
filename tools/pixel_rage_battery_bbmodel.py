"""Writes the final Red corps battery (J, 2026-10-13) as the Blockbench models the mod draws:
  bbmodel/red_battery.bbmodel        - the battery: C1 build (arched rune handle), smooth glossy crimson stone
                                       (the crimson diamond's centre colour), glowing parts as "glow_" cubes
  bbmodel/red_battery_cover.bbmodel  - the port cover, separate so the game can dissolve it on charge
and textures/entity/bb/<name>.png. Neighbouring voxels of the same colour merge into boxes; every box is painted
one flat colour per face (box UV at 2 texels per model px, one per voxel).

    python tools/pixel_rage_battery_bbmodel.py OUTDIR [c1|c2|c3]
"""
import math, os, sys, io, json, uuid, base64
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = sys.argv[1]
VER = sys.argv[2] if len(sys.argv) > 2 else "c1"
_argv, sys.argv = sys.argv, ["pixel_rage_battery3.py", os.path.join(OUT, "_tmp")]
import pixel_rage_battery3 as P3  # noqa: E402
sys.argv = _argv
P2, B = P3.P2, P3.B
A = OUT
DENSITY = 2
CLEAR = (0, 0, 0, 0)
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])

CRIMSON = (188, 30, 47)
STONE_COL = {B.STONE: CRIMSON, B.DARK: (110, 16, 28), B.FLECK: (214, 60, 74), B.IRON: (70, 22, 26),
             P2.PLATE: CRIMSON, P2.GROOVE: (96, 12, 22)}
GLOW_COL = {B.GLASS: (150, 8, 14), B.BLOOD: (170, 4, 14), B.VEIN: (230, 30, 24), B.RUNE: (255, 60, 40),
            B.BRIGHT: (255, 150, 120), P2.PORTLIGHT: (255, 70, 50)}
NAME = {B.STONE: "stone", B.DARK: "stone_dark", B.FLECK: "stone_glint", B.IRON: "iron", P2.PLATE: "cover",
        P2.GROOVE: "cover_groove", B.GLASS: "glow_glass", B.BLOOD: "glow_blood", B.VEIN: "glow_vein",
        B.RUNE: "glow_rune", B.BRIGHT: "glow_bright", P2.PORTLIGHT: "glow_port"}


def boxes(mask):
    m = mask.copy(); out = []; S = m.shape
    for k in range(S[2]):
        for j in range(S[1]):
            for i in range(S[0]):
                if not m[i, j, k]:
                    continue
                i2 = i
                while i2 + 1 < S[0] and m[i2 + 1, j, k]:
                    i2 += 1
                j2 = j
                while j2 + 1 < S[1] and m[i:i2 + 1, j2 + 1, k].all():
                    j2 += 1
                k2 = k
                while k2 + 1 < S[2] and m[i:i2 + 1, j:j2 + 1, k2 + 1].all():
                    k2 += 1
                m[i:i2 + 1, j:j2 + 1, k:k2 + 1] = False
                out.append((i, j, k, i2, j2, k2))
    return out


def flat(rgb, shade=1.0):
    c = tuple(int(min(255, v * shade)) for v in rgb) + (255,)
    def paint(face, w, h):
        s = {"up": 1.08, "down": 0.8, "north": 1.0, "south": 0.95, "east": 0.92, "west": 0.92}[face]
        cc = tuple(int(min(255, v * s)) for v in c[:3]) + (255,)
        return [[cc] * w for _ in range(h)]
    return paint


def model(name, part):
    G = B.G
    x0, y0, z0 = B.AX[0] - G / 2, B.AX[0] - G / 2, B.AZ[0] - G / 2
    m = Model(name, DENSITY)
    n = 0
    for pid in sorted(set(np.unique(part).tolist()) - {B.EMPTY}):
        col = STONE_COL.get(pid) or GLOW_COL.get(pid)
        for (i, j, k, i2, j2, k2) in boxes(part == pid):
            fx, fy, fz = x0 + i * G, y0 + j * G, z0 + k * G
            tx, ty, tz = x0 + (i2 + 1) * G, y0 + (j2 + 1) * G, z0 + (k2 + 1) * G
            # model space (x right, y back, z up) -> Blockbench (x, y up, z): front (-y) faces north (-z)
            frm, to = [-tx, fz, fy], [-fx, tz, ty]
            m.cube(f"{NAME[pid]}_{n}", frm, to, flat(col))
            n += 1
    return m, n


if __name__ == "__main__":
    body, plate = P2.build()
    fy = -(9.0 + 3.4); prr = np.hypot(B.X, B.Z - 24.0)
    body[(prr < 5.8) & (B.Y >= fy + 1.0) & (B.Y < fy + 2.0)] = P2.PORTLIGHT
    if VER != "c1":
        P3.strip_handle(body)
        (P3.ring_handle if VER == "c2" else P3.horn_handle)(body)
    # J wants the stone smooth (one crimson, no pattern), so all the stone kinds merge into one: far fewer boxes.
    # Voxels hidden inside the shape take the same kind, so the boxes run through them.
    for k in (B.DARK, B.FLECK, B.IRON):
        body[body == k] = B.STONE
    plate[np.isin(plate, (B.FLECK, P2.GROOVE))] = P2.PLATE
    for k in (B.BRIGHT,):
        pass
    occ = body > 0
    inner = occ.copy()
    for ax in range(3):
        for sg in (1, -1):
            inner &= np.roll(occ, sg, axis=ax)
    body[inner] = B.STONE
    for name, p in (("red_battery", body), ("red_battery_cover", plate)):
        mdl, n = model(name, p)
        mdl.write()
        print(name, n, "boxes")
