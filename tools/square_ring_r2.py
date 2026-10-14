"""Exports J's square emblem ring picks from Blender pass 596 (P03 deep frame, N01 faithful gold body, N04 faithful
light lines) as worn-ring Blockbench models, in the layout tools/ring_bbmodel.py gives the other worn rings
(RingModels.Placement, 16 units = 1 skin pixel; one voxel = 0.25 model px = 1 unit, the same grid as the game ring).

The voxel builder below (palettes, TAKES, stone_tex, build_ring) is copied verbatim from
docs/blender/blender_updates/596_square_ring_r2.update.py, so the stone flecks and banding match the Blender sheet
(same seeds: 595 + the take's index). Only lin() differs: colours stay sRGB here.

Every voxel is a solid cube in its own (unlit) colour. Voxels that glow in 596 (the emerald cells, the core, the gem)
also get a "glow_s<k>_" copy painted bright in their emission colour (Blockbench glow is not additive, so no faint
halo boxes). k is the light stage, from 596's "dist": the light front spreads out from the core (dist 0, the gem's
table) to the face edge (dist 1) and the band (dist up to 2), so RingModels lights stage 0 first, then the rest.

    python tools/square_ring_r2.py src/main/resources/assets/lanternring [P03 N01 N04]
"""
import base64, io, json, math, os, sys, uuid
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
PICK = sys.argv[2:] or ["P03", "N01", "N04"]
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
exec(_src[_src.index("def _texel("):_src.index("AXES = {")])


def lin(rgb):
    return np.asarray(rgb, float)


METAL, GOLD, GEM, CORE, DARK = range(5)

# ------------------------------------------------------------------ palettes
METALS = {"silver": (150, 152, 156), "steel": (112, 118, 126), "gunmetal": (62, 66, 72), "pale": (196, 198, 202),
          "stone": (128, 130, 128), "gold": (206, 160, 56), "white": (214, 214, 208)}
GOLD_C = (240, 192, 66)
EM_DARK, EM_LIGHT = np.array((8, 82, 32), float), np.array((40, 196, 84), float)
CORE_C = (96, 255, 132)          # saturated, never white
DARK_C = (6, 48, 20)

# ------------------------------------------------------------------ the takes (every one different)
TAKES = [
    # ---- J's picks, refined
    dict(code="P01", name="Faithful plus", shape="octa", metal="stone", rings=2, core="2", relief="frames", bars="solid",
         sides="solid", corners="square", glow="rings", stone="speckle", bevel=True, engrave=True),
    dict(code="P02", name="Gold-trimmed plus", shape="octa", metal="silver", trim="gold", rope=True, rings=2, core="2",
         relief="frames", bars="solid", sides="solid", corners="square", bezel=True, glow="all", stone="speckle", bevel=True),
    dict(code="P03", name="Deep frame plus", shape="octa", metal="gunmetal", frame=2, rings=1, core="facet",
         relief="frames", bars="solid", sides="solid", corners="square", glow="all", stone="malachite", bevel=True, engrave=True),
    dict(code="P04", name="Radiant updated", shape="round", metal="pale", rings=3, core="facet", relief="facet",
         bars="gradient", sides="gradient", corners="square", extra="spokes8", glow="all", stone="speckle", bevel=True),
    # ---- Faithful family
    dict(code="N01", name="Faithful gold body", shape="octa", metal="gold", rings=2, core="2", relief="frames",
         bars="solid", sides="solid", corners="square", glow="rings", stone="malachite", bevel=True),
    dict(code="N02", name="Faithful shoulder inlays", shape="octa", metal="stone", inlay=True, rings=2, core="plus",
         relief="frames", bars="solid", sides="cells", corners="square", glow="rings", stone="speckle", bevel=True),
    dict(code="N03", name="Faithful three rings", shape="cathedral", metal="steel", rings=3, core="facet",
         relief="pyramid", bars="solid", sides="gradient", corners="square", glow="core", stone="speckle", engrave=True),
    dict(code="N04", name="Faithful light lines", shape="stepped", metal="stone", rings=2, core="2", relief="frames",
         bars="line", sides="solid", corners="notched", glow="bars", stone="malachite", engrave=True),
    # ---- Gold-trimmed family
    dict(code="N05", name="Gold edge engraved", shape="knife", metal="steel", trim="gold", engrave=True, rings=2,
         core="diamond", relief="dome", bars="gradient", sides="solid", corners="square", glow="rings", stone="speckle", bevel=True),
    dict(code="N06", name="Two-tone", shape="octa", metal="silver", two_tone=True, rings=3, core="2", relief="frames",
         bars="cells", sides="solid", corners="square", bezel=True, glow="all", stone="malachite", bevel=True),
    dict(code="N07", name="Rope and claws", shape="taper", metal="pale", rope=True, rings=2, core="plus", relief="frames",
         bars="solid", sides="cells", corners="claws", bezel=True, glow="rings", stone="speckle"),
    dict(code="N08", name="White gold channel", shape="channel", metal="white", trim="gold", rings=2, core="facet",
         relief="frames", bars="solid", sides="gradient", corners="square", glow="bars", stone="speckle", bevel=True),
    # ---- Deep frame family
    dict(code="N09", name="Deep frame studs", shape="octa", metal="gunmetal", frame=2, rings=1, core="big", relief="frames",
         bars="solid", sides="solid", corners="studs", glow="all", stone="malachite", bevel=True),
    dict(code="N10", name="Deep frame gold body", shape="cathedral", metal="gold", frame=2, rings=1, core="cushion",
         relief="frames", bars="double", sides="solid", corners="square", glow="all", stone="speckle", bevel=True),
    dict(code="N11", name="Deep frame vault", shape="round", metal="steel", frame=2, rings=2, core="big", relief="inset",
         bars="line", sides="solid", corners="square", glow="bars", stone="malachite", engrave=True),
    dict(code="N12", name="Deep frame cathedral", shape="cathedral", metal="gunmetal", frame=2, rings=2, core="facet",
         relief="pyramid", bars="cells", sides="cells", corners="notched", glow="rings", stone="speckle", inlay=True),
    # ---- Radiant family
    dict(code="N13", name="Radiant eight", shape="round", metal="silver", rings=2, core="plus", relief="facet",
         bars="gradient", sides="gradient", corners="square", extra="spokes8", glow="all", stone="malachite", bevel=True),
    dict(code="N14", name="Radiant sunburst", shape="ribbed", metal="pale", rings=3, core="diamond", relief="dome",
         bars="gradient", sides="gradient", corners="square", extra="spokes", glow="all", stone="speckle", bevel=True),
    dict(code="N15", name="Radiant gold", shape="round", metal="gold", rings=2, core="facet", relief="facet",
         bars="solid", sides="solid", corners="square", extra="spokes", glow="rings", stone="malachite", bevel=True, rope=True),
    dict(code="N16", name="Radiant veins", shape="veins", metal="gunmetal", rings=2, core="facet", relief="facet",
         bars="line", sides="gradient", corners="square", extra="spokes8", glow="all", stone="speckle"),
]


def stone_tex(rgb, u, v, style, rng):
    """J's photo: the stone is mottled, with dark flecks (speckle) or soft bands (malachite)."""
    rgb = np.asarray(rgb, float)
    if style == "speckle":
        r = rng.random()
        k = rng.uniform(0.72, 1.22)
        if r < 0.13:
            k = 0.38
        elif r > 0.95:
            k = 1.45
        return rgb * k
    if style == "malachite":
        band = 0.5 + 0.5 * math.sin(0.95 * u + 0.45 * v + 1.8 * math.sin(0.38 * v + 0.2 * u))
        return (EM_DARK * 0.65) * (1 - band) + rgb * 1.18 * band
    return rgb


# ------------------------------------------------------------------ voxel builder (0.25 model px per voxel)
def build_ring(t, rng):
    """Returns occupancy-kind grid, colour grid (linear rgb), glow and dist grids, indexed [x, y, z].
    x: across the face / along the finger (band width); y: across the face; z: up (face on top)."""
    fw = t.get("fw", 24); bh = t.get("bh", 5); frame = t.get("frame", 1)
    NX, NY, NZ = fw + 8, max(fw + 8, 42), 52
    K = np.full((NX, NY, NZ), -1, np.int8)
    C = np.zeros((NX, NY, NZ, 3), np.float32)
    GL = np.zeros((NX, NY, NZ), np.float32); DI = np.zeros((NX, NY, NZ), np.float32)
    xc, yc, zc = NX / 2, NY / 2, 18.0
    ri = 10.4
    metal = np.array(METALS[t["metal"]], float)
    shape = t["shape"]

    def put(x, y, z, k, rgb, glow=0.0, dist=0.0, noise=0.06):
        if 0 <= x < NX and 0 <= y < NY and 0 <= z < NZ:
            K[x, y, z] = k
            c = np.asarray(rgb, float) * (1.0 + rng.uniform(-noise, noise))
            C[x, y, z] = lin(np.clip(c, 0, 255)); GL[x, y, z] = glow; DI[x, y, z] = dist

    # ---- the band (a loop round the x axis, face on top)
    t_top, t_bot, w_top, w_bot = 6.0, 3.0, 18.0, 9.0
    if shape == "taper":
        t_bot, w_bot = 2.4, 6.0
    if shape == "cathedral":
        t_top, w_top = 8.0, 20.0
    for x in range(NX):
        for y in range(NY):
            for z in range(NZ):
                dy, dz = y + 0.5 - yc, z + 0.5 - zc
                th = math.atan2(dy, dz)                       # 0 at the top
                f = (1 - math.cos(th)) / 2                    # 0 top .. 1 bottom
                if shape == "stepped":
                    f = math.floor(f * 5) / 5
                if shape == "cathedral":
                    ff = min(1.0, max(0.0, (f - 0.12) / 0.5))
                else:
                    ff = f
                tt = t_top + (t_bot - t_top) * ff ** 0.8
                ww = w_top + (w_bot - w_top) * ff
                xcen = xc + (2.5 * math.sin(2 * th) if shape == "twist" else 0.0)
                ax = abs(x + 0.5 - xcen)
                if ax > ww / 2:
                    continue
                if shape in ("octa", "stepped", "cathedral", "split", "channel", "ribbed", "gallery", "veins", "taper", "twist"):
                    r = max(abs(dy), abs(dz), (abs(dy) + abs(dz)) / 1.35)
                else:
                    r = math.hypot(dy, dz)
                if shape == "ribbed" and int((th + math.pi) * ri / 2.0) % 2 == 0:
                    tt += 1.2
                if shape == "knife":
                    tt = tt * (1 - 0.55 * (ax / (ww / 2)) ** 2) + 0.6
                if not (ri <= r <= ri + tt):
                    continue
                if shape == "split" and f < 0.33 and ax < 2.0:
                    continue
                if shape == "gallery" and 0.1 < f < 0.32 and r > ri + 1.2 and (int(x + 0.5 * z) % 4 == 0) and ax < ww / 2 - 1.5:
                    continue
                k, rgb, gl, di = METAL, metal * (0.82 + 0.3 * (r - ri) / max(tt, 1e-3)), 0.0, 0.0
                if t.get("trim") == "gold" and ax > ww / 2 - 1.2:
                    k, rgb = GOLD, GOLD_C
                if shape == "channel" and r > ri + tt - 1.5 and ax < 1.2:
                    k, rgb, gl, di = GEM, EM_LIGHT, 0.8, 1.0 + f
                if shape == "veins" and r > ri + tt - 1.2 and int((th + math.pi) * ri / 1.6) % 4 == 0:
                    k, rgb, gl, di = GEM, EM_LIGHT * 0.9, 0.7, 1.0 + f
                if t.get("two_tone") and f > 0.42 and k == METAL:
                    k, rgb = GOLD, np.array(GOLD_C) * 0.92
                if t.get("engrave") and k == METAL and r > ri + tt - 1.0 and abs(ax - (ww / 2 - 2.2)) < 0.55:
                    rgb = np.asarray(rgb, float) * 0.5
                if t.get("rope") and ax > ww / 2 - 1.2:
                    k = GOLD
                    rgb = np.array(GOLD_C) * (0.72 if int((th + math.pi) * ri / 1.1 + x * 0.5) % 2 else 1.05)
                if t.get("inlay") and k == METAL and 0.07 < f < 0.24 and r > ri + tt - 1.0 and ax < 1.6 and int((th + math.pi) * ri / 1.5) % 3 == 0:
                    k, rgb, gl, di = GEM, EM_LIGHT, 0.6, 0.95
                if k == METAL and r < ri + 1.0:
                    rgb = np.asarray(rgb, float) * 1.18             # polished inside
                put(x, y, z, k, rgb, gl, di, noise=0.1 if k == METAL else 0.05)

    # ---- the face
    zf = int(round(zc + ri + t_top)) - 1
    x0, y0 = int(xc - fw / 2), int(yc - fw / 2)
    cs = fw - 2 * bh
    sx = (fw - cs) // 2
    dmax = (cs - 1) // 2
    gold_d = {0} | {2 * k for k in range(1, t["rings"]) if 2 * k < dmax}
    if t["rings"] >= 3 and cs >= 14:
        gold_d = {0} | {k * max(2, dmax // t["rings"]) for k in range(1, t["rings"])}
    relief = t["relief"]
    if t.get("bezel"):
        for u in range(-1, fw + 1):
            for v in range(-1, fw + 1):
                if u in (-1, fw) or v in (-1, fw):
                    for z in (zf - 1, zf):
                        put(x0 + u, y0 + v, z, GOLD, np.array(GOLD_C) * 0.85)
    for u in range(fw):
        for v in range(fw):
            corner = (u in (0, fw - 1)) and (v in (0, fw - 1))
            if t["corners"] == "notched" and (min(u, fw - 1 - u) < 2 and min(v, fw - 1 - v) < 2):
                continue
            cu, cv = u + 0.5 - fw / 2, v + 0.5 - fw / 2
            dist = max(abs(cu), abs(cv)) / (fw / 2)
            # base plate (gold, 2 thick)
            for z in (zf, zf + 1):
                put(x0 + u, y0 + v, z, GOLD, np.array(GOLD_C) * 0.8, 0.0, dist)
            kind, rgb, h, glow = GOLD, GOLD_C, 2, 0.0
            on_frame = min(u, v, fw - 1 - u, fw - 1 - v) < frame
            in_bar = v < bh or v >= fw - bh
            if on_frame:
                kind, h = GOLD, 2
            elif in_bar:
                bv = v if v < bh else fw - 1 - v                 # 0 at the outer edge
                rim = bv == bh - 1 or bv < frame
                if rim:
                    kind, h = GOLD, 2
                else:
                    kind, h = GEM, 1
                    tt_ = abs(cu) / (fw / 2)
                    rgb = EM_DARK + (EM_LIGHT - EM_DARK) * (0.55 if t["bars"] != "gradient" else 1 - tt_)
                    glow = {"bars": 0.9, "all": 0.7}.get(t["glow"], 0.25)
                    if t["bars"] == "cells" and (u - frame) % 5 == 4:
                        kind, h, glow = GOLD, 2, 0.0
                    if t["bars"] == "line" and bv == (bh - 1 + frame) // 2:
                        kind, rgb, glow = CORE, CORE_C, 0.8
                    if t["bars"] == "double" and bv == frame:
                        kind, h, glow = GOLD, 2, 0.0
            else:
                in_center = sx <= u < fw - sx
                if not in_center:
                    su = u if u < sx else fw - 1 - u
                    if su == sx - 1:
                        kind, h = GOLD, 2
                    else:
                        kind, h = GEM, 1
                        vv = (v - bh) / max(1, fw - 2 * bh - 1)
                        rgb = EM_DARK + (EM_LIGHT - EM_DARK) * (0.45 if t["sides"] != "gradient" else 0.2 + 0.8 * (1 - abs(vv - 0.5) * 2))
                        glow = {"all": 0.7, "bars": 0.35}.get(t["glow"], 0.25)
                        if t["sides"] == "cells" and (v - bh) % 4 == 3:
                            kind, h, glow = GOLD, 2, 0.0
                else:
                    a_, b_ = u - sx, v - bh
                    d = min(a_, b_, cs - 1 - a_, cs - 1 - b_)
                    if d in gold_d:
                        kind, h, glow = GOLD, 2, 0.0
                    else:
                        kind, h = GEM, 1
                        rgb = EM_DARK + (EM_LIGHT - EM_DARK) * (d / max(1, dmax)) ** 0.9
                        glow = {"rings": 0.75, "all": 0.8, "bars": 0.45}.get(t["glow"], 0.2) * (0.4 + 0.6 * d / max(1, dmax))
                        core = False
                        ccu, ccv = a_ + 0.5 - cs / 2, b_ + 0.5 - cs / 2
                        if t["core"] == "2":
                            core = d >= dmax
                        elif t["core"] == "plus":
                            core = (abs(ccu) < 1 and abs(ccv) < 2.6) or (abs(ccv) < 1 and abs(ccu) < 2.6)
                        elif t["core"] == "diamond":
                            core = abs(ccu) + abs(ccv) <= 2.6
                        elif t["core"] == "big":
                            core = max(abs(ccu), abs(ccv)) <= 2.0
                        elif t["core"] == "cushion":
                            core = max(abs(ccu), abs(ccv)) <= 2.0 and abs(ccu) + abs(ccv) <= 3.6
                        if core:
                            kind, rgb, glow = CORE, CORE_C, 1.0
                        if t.get("extra") in ("spokes", "spokes8") and not core and abs(abs(ccu) - abs(ccv)) < 0.6 and d >= 1:
                            kind, h, glow = GOLD, 2, 0.0
                        if t.get("extra") == "spokes8" and not core and min(abs(ccu), abs(ccv)) < 0.6 and d >= 1:
                            kind, h, glow = GOLD, 2, 0.0
                        if t["core"] == "facet":
                            m_, s_ = max(abs(ccu), abs(ccv)), abs(ccu) + abs(ccv)
                            if m_ <= 3.6 and s_ <= 5.2:
                                kind = GEM; rgb = EM_DARK + (EM_LIGHT - EM_DARK) * min(1.0, 1.1 - m_ / 4.5)
                                h = 1 + int(round(3.2 - m_ * 0.7)); glow = max(glow, 0.7)
                                if m_ <= 1.0:
                                    kind, rgb, glow = CORE, CORE_C, 1.0
                    # relief inside the centre square
                    if relief == "pyramid":
                        h += min(d, dmax) // 2
                    elif relief == "dome":
                        h += int(round(2.5 * (1 - (max(abs(a_ + 0.5 - cs / 2), abs(b_ + 0.5 - cs / 2)) / (cs / 2)) ** 2)))
                    elif relief == "facet" and d >= 2:
                        h += min(3, d - 1)
            if relief == "inset" and kind == GOLD:
                h += 1
            if kind == GEM and t.get("stone"):
                rgb = stone_tex(rgb, u, v, t["stone"], rng)
            if kind == GOLD:
                edge = min(u, v, fw - 1 - u, fw - 1 - v)
                rgb = np.array(GOLD_C) * (0.86 if edge == 0 else 1.08 if not on_frame else 1.0)
                if t.get("bevel") and edge == 0 and h > 1:
                    h -= 1                                         # bevelled outer edge, as on J's photo
            if relief == "frames" and kind == GOLD and not on_frame:
                h += 0                                            # J's image: thin gold outlines standing proud
            for k in range(h):
                z = zf + 2 + k
                top = k == h - 1
                c_ = rgb if (top or kind != GOLD) else np.array(GOLD_C) * 0.85
                kk = kind if (top or kind == GOLD) else (DARK if kind == GEM else kind)
                if kind == CORE and not top:
                    kk, c_ = GEM, EM_LIGHT
                put(x0 + u, y0 + v, z, kk, c_, glow if top or kind == GEM else 0.0, dist, noise=0.04)
            # corner studs / claws
            if corner and t["corners"] == "studs":
                for k in range(3):
                    put(x0 + u, y0 + v, zf + 2 + h + k - 1, GOLD, GOLD_C)
    if t["corners"] == "claws":
        for (u, v) in ((-1, -1), (fw, -1), (-1, fw), (fw, fw)):
            for k in range(6):
                put(x0 + u, y0 + v, zf - 1 + k, GOLD, GOLD_C)
            du = 1 if u < 0 else -1; dv = 1 if v < 0 else -1
            put(x0 + u + du, y0 + v + dv, zf + 4, GOLD, GOLD_C)
    return K, C, GL, DI, (x0, y0, zf, fw)



# ------------------------------------------------------------------ export (this tool)
STAGES = 8                # light stages: dist 0..2 in steps of 0.25
DROP = -8.0               # the band reaches this far down into the fist, like ring_forged
EMIT = {GEM: 1.0, CORE: 1.0, DARK: 0.45}


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


def to_srgb8(c):
    return tuple(int(round(min(255, max(0, v)))) for v in c) + (255,)


def emission(rgb, glow):
    """596's emission colour: the voxel's own green pushed toward saturation (never white), in linear light."""
    lin_ = (np.asarray(rgb, float) / 255.0) ** 2.2
    ec = np.clip(lin_ * np.array([0.6, 1.6, 0.8]), 0, 1) ** (1 / 2.2) * 255
    return ec * (0.7 + 0.3 * min(1.0, glow))


INWARD = {"east": (-0.5, 0, 0), "west": (0.5, 0, 0), "up": (0, -0.5, 0), "down": (0, 0.5, 0),
          "north": (0, 0, 0.5), "south": (0, 0, -0.5)}
SHADE = {"up": 1.0, "down": 0.55}


def export(code):
    i = next(n for n, t in enumerate(TAKES) if t["code"] == code)
    t = TAKES[i]
    rng = np.random.default_rng(595 + i)
    K, C, GL, DI, (x0, y0, zf, fw) = build_ring(t, rng)
    NX, NY, NZ = K.shape
    xc, yc, zc = NX // 2, NY // 2, 18
    # 596 grid [x along the finger, y across, z up] -> Blockbench [x across, y out of the fist, z along the finger]
    Kb, Gb, Db = (a.transpose(1, 2, 0) for a in (K, GL, DI))
    Cb = C.transpose(1, 2, 0, 3)
    off = np.array([-yc, -zc + DROP, -xc], float)            # bb coordinate of voxel index 0
    occ = Kb >= 0
    glows = occ & (Gb > 0) & np.isin(Kb, list(EMIT))
    stage = np.minimum(STAGES - 1, (Db / 0.25).astype(int))
    name = f"ring_sq_{code.lower()}"
    model = Model(name, density=1)

    def painter(frm, to, glow):
        def paint(face, w, h):
            rows = []
            for v in range(h):
                row = []
                for u in range(w):
                    p = np.array(_texel(frm, to, face, u, v, w, h)) + INWARD[face] - off
                    ix, iy, iz = (min(s - 1, max(0, int(math.floor(c)))) for c, s in zip(p, Kb.shape))
                    rgb = Cb[ix, iy, iz]
                    if glow:
                        k = int(Kb[ix, iy, iz])
                        row.append(to_srgb8(emission(rgb, Gb[ix, iy, iz]) * EMIT.get(k, 1.0) ** 0.5))
                    else:
                        row.append(to_srgb8(rgb * SHADE.get(face, 0.8)))
                rows.append(row)
            return rows
        return paint

    def cubes(mask, prefix, glow, inflate=0.0):
        n = 0
        for (i_, j, k, i2, j2, k2) in boxes(mask):
            frm = [float(i_ + off[0]), float(j + off[1]), float(k + off[2])]
            to = [float(i2 + 1 + off[0]), float(j2 + 1 + off[1]), float(k2 + 1 + off[2])]
            model.cube(f"{prefix}{n}", frm, to, painter(frm, to, glow), inflate=inflate)
            n += 1
        return n

    nb = cubes(occ, "body_", False)
    ng = [cubes(glows & (stage == s), f"glow_s{s}_", True, inflate=0.02) for s in range(STAGES)]
    model.write()
    top = max(c["to"][1] for c in model.cubes)
    print(name, nb, "body cubes, glow cubes by stage", ng, "; face top", top, "units =", round(top / 16, 3), "skin px")


if __name__ == "__main__":
    for code in PICK:
        export(code)
