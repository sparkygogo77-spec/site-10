"""Ram barrier takes for J (Blender pass 410). Writes game-ready bbmodels for RamBarrierFx's model
hook: bbmodel/ram_barrier.bbmodel + textures/entity/bb/ram_barrier[_corps].png, origin at the
flyer's middle, facing north (-Z), radius 4.5 blocks, cap half-angle acos(0.57) = 55 degrees
(RamBarrier.RADIUS / CAP_COS).

Every take is axis-aligned voxels (no rotated cubes, so the game draws exactly what Blender shows),
4 model px per voxel, merged into runs along x. Cube names pick the game's draw path: "glass_*"
see-through and full-bright, "glow_*" the pack-safe glow. Colours come from one small swatch
texture painted per corps (five-stop palettes, no hue shift).

    python tools/ram_barrier_takes.py OUT_DIR
writes OUT_DIR/<take>/assets/lanternring/{bbmodel,textures/entity/bb}/... and prints box counts.
"""
import json
import math
import os
import random
import sys
import uuid

import numpy as np
from PIL import Image

R = 72.0          # 4.5 blocks in model px
CAP_COS = 0.57
G = 4             # voxel size, model px
TEX_W, TEX_H = 128, 64
MAX_RUN = 15      # voxels per merged run, so a box's UV fits its swatch band
# The game's BbModel reads box UV from uv_offset only; per-face UVs are just for Blockbench/Blender.
FACES = os.environ.get("FACES") == "1"

CORPS = {
    "green":  [(3, 9, 8), (10, 52, 36), (26, 124, 74), (96, 220, 150), (205, 255, 228)],
    "blue":   [(3, 6, 14), (10, 30, 72), (32, 84, 176), (112, 172, 255), (218, 236, 255)],
    "red":    [(10, 2, 3), (62, 8, 14), (146, 20, 34), (232, 72, 72), (255, 204, 194)],
    "yellow": [(10, 8, 2), (72, 54, 8), (176, 134, 22), (255, 216, 72), (255, 250, 212)],
    "violet": [(7, 3, 12), (42, 14, 72), (104, 42, 164), (192, 122, 255), (242, 222, 255)],
    "orange": [(10, 5, 2), (72, 30, 6), (184, 82, 16), (255, 162, 52), (255, 236, 202)],
}
SUFFIX = {"green": "", "blue": "_blue", "red": "_red", "yellow": "_yellow", "violet": "_violet", "orange": "_orange"}
# Swatch bands (rows of 16 px): material -> (band, draw prefix)
MATS = {"faint": (0, "glass"), "sheet": (1, "glass"), "glow": (2, "glow"), "hot": (3, "glow")}


def texture(corps):
    """Four 16 px bands: faint glass, sheet glass, glow, hot glow, with a soft painted grain."""
    p = CORPS[corps]
    rng = np.random.default_rng(3)
    img = np.zeros((TEX_H, TEX_W, 4), np.uint8)
    looks = {0: (p[2], 16), 1: (p[3], 42), 2: (p[3], 255), 3: (p[4], 255)}
    for band, (col, alpha) in looks.items():
        grain = np.ones((16, TEX_W))   # flat swatches: tiny files, and the shell reads clean
        rgb = np.clip(np.array(col, float)[None, None, :] * grain[..., None], 0, 255)
        img[band * 16:(band + 1) * 16, :, :3] = rgb.astype(np.uint8)
        img[band * 16:(band + 1) * 16, :, 3] = alpha
    return Image.fromarray(img, "RGBA")


def shell_cells():
    """Voxel centres on the cap: one voxel thick round radius R, inside the cap angle."""
    n = int(R // G) + 2
    cells = []
    for ix in range(-n, n + 1):
        for iy in range(-n, n + 1):
            for iz in range(-n, 1):
                c = np.array([ix * G, iy * G, iz * G], float)
                d = np.linalg.norm(c)
                if d < 1e-6 or abs(d - R) > G * 0.62:
                    continue
                fwd = -c[2] / d                      # forward is -Z
                if fwd >= CAP_COS:
                    cells.append((ix, iy, iz, fwd, math.atan2(c[1], c[0])))
    return cells


def classify(take, cells, rng):
    """material per voxel (or None to leave it out), plus extra small cubes (motes)."""
    out, motes = {}, []
    edge = CAP_COS + 0.06
    for ix, iy, iz, fwd, az in cells:
        key = (ix, iy, iz)
        rim = fwd < edge
        ang = math.degrees(math.acos(min(1, fwd)))     # 0 at the prow, 55 at the rim
        if take == "R1_glass_shell":
            out[key] = "glow" if rim else "sheet"
        elif take == "R2_lattice":
            spoke = min(abs(((math.degrees(az) % 30) + 30) % 30 - 15) - 15, 0) == 0  # placeholder
            on_meridian = abs(((math.degrees(az) + 15) % 30) - 15) < (G / (R * math.sin(math.radians(max(ang, 1)))) * 57.3) * 0.6
            on_ring = min(abs(ang - a) for a in (18, 36)) < 2.0
            if rim:
                out[key] = "hot"
            elif ang < 5:
                out[key] = "glow"
            elif on_meridian or on_ring:
                out[key] = "glow"
            else:
                out[key] = "faint" if rng.random() < 0.0 else None
        elif take == "R3_particle_field":
            out[key] = "faint"
            if rng.random() < 0.55:
                motes.append((ix * G + rng.uniform(-1.2, 1.2), iy * G + rng.uniform(-1.2, 1.2),
                              iz * G + rng.uniform(-1.2, 1.2), 1.0 if rng.random() < 0.8 else 1.5,
                              "hot" if rng.random() < 0.25 else "glow"))
            if rim and rng.random() < 0.5:
                out[key] = "glow"
        elif take == "R4_pressure_rings":
            band = min(abs(ang - a) for a in (0, 18, 34, 50))
            if ang < 4:
                out[key] = "hot"
            elif band < 2.2:
                out[key] = "glow"
            elif band < 5:
                out[key] = "faint"
            else:
                out[key] = None
    return out, motes


def cube(name, frm, to, mat):
    band, prefix = MATS[mat]
    return {
        "name": f"{prefix}_{name}", "box_uv": True,
        "from": [round(v, 2) for v in frm], "to": [round(v, 2) for v in to],
        "origin": [round((a + b) / 2, 2) for a, b in zip(frm, to)],
        "uv_offset": [0, band * 16], "faces": box_faces(frm, to, band) if FACES else {},
        "type": "cube",
    }


def box_faces(frm, to, band):
    """Face UVs that match Minecraft box UV from uv_offset (0, band*16)."""
    w, h, d = (to[i] - frm[i] for i in range(3))
    u, v = 0, band * 16
    return {
        "east": {"uv": [u, v + d, u + d, v + d + h], "texture": 0},
        "north": {"uv": [u + d, v + d, u + d + w, v + d + h], "texture": 0},
        "west": {"uv": [u + d + w, v + d, u + 2 * d + w, v + d + h], "texture": 0},
        "south": {"uv": [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h], "texture": 0},
        "up": {"uv": [u + d, v, u + d + w, v + d], "texture": 0},
        "down": {"uv": [u + d + w, v, u + d + 2 * w, v + d], "texture": 0},
    }


THIN = 1.0       # tile thickness in model px: a thin shell, not a wall of blocks


def tile(ix, iy, iz):
    """A voxel cell as a thin tile across its most outward-facing axis (no rotated cubes)."""
    c = np.array([ix * G, iy * G, iz * G], float)
    axis = int(np.argmax(np.abs(c)))
    frm = [c[k] - G / 2 for k in range(3)]
    to = [c[k] + G / 2 for k in range(3)]
    frm[axis], to[axis] = c[axis] - THIN / 2, c[axis] + THIN / 2
    return axis, frm, to


def build(take, seed=5):
    rng = random.Random(seed)
    mats, motes = classify(take, shell_cells(), rng)
    elements = []
    # Tiles facing along y or z that sit side by side along x merge into one plate.
    rows, singles = {}, []
    for (ix, iy, iz), m in mats.items():
        if not m:
            continue
        axis, frm, to = tile(ix, iy, iz)
        if axis == 0:
            singles.append((frm, to, m))
        else:
            rows.setdefault((axis, iy, iz, m), []).append(ix)
    k = 0
    for (axis, iy, iz, m), xs in sorted(rows.items()):
        xs.sort()
        start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x == prev + 1 and x - start < MAX_RUN:
                prev = x
                continue
            _, f0, _ = tile(start, iy, iz)
            _, _, t1 = tile(prev, iy, iz)
            elements.append(cube(f"{k}", f0, t1, m))
            k += 1
            if x is not None:
                start = prev = x
    for frm, to, m in singles:
        elements.append(cube(f"{k}", frm, to, m))
        k += 1
    for (x, y, z, sz, m) in motes:
        elements.append(cube(f"m{k}", (x - sz / 2, y - sz / 2, z - sz / 2), (x + sz / 2, y + sz / 2, z + sz / 2), m))
        k += 1
    return {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": True},
        "name": "ram_barrier", "model_identifier": "ram_barrier", "visible_box": [10, 10, 0],
        "resolution": {"width": TEX_W, "height": TEX_H},
        "elements": elements,
        "textures": [{"name": "ram_barrier.png", "width": TEX_W, "height": TEX_H, "uv_width": TEX_W,
                      "uv_height": TEX_H, "id": "0", "uuid": str(uuid.uuid4())}],
    }


TAKES = ["R1_glass_shell", "R2_lattice", "R3_particle_field", "R4_pressure_rings"]

if __name__ == "__main__":
    out = sys.argv[1]
    for take in TAKES:
        root = f"{out}/{take}/assets/lanternring"
        os.makedirs(f"{root}/bbmodel", exist_ok=True)
        os.makedirs(f"{root}/textures/entity/bb", exist_ok=True)
        model = build(take)
        json.dump(model, open(f"{root}/bbmodel/ram_barrier.bbmodel", "w"))
        for corps, sfx in SUFFIX.items():
            texture(corps).save(f"{root}/textures/entity/bb/ram_barrier{sfx}.png", optimize=True)
        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(root) for f in fs)
        print(f"{take}: {len(model['elements'])} boxes, {size / 1024:.0f} KB with six corps textures")
