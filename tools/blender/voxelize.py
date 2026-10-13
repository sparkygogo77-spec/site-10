"""Turns a lantern modelled in Blender into Minecraft-style pixel cubes on a fixed grid, coloured
from the model's own materials, and renders it from the sheet's angles at several grid sizes so
they can be compared.

    python tools/blender/voxelize.py <model.blend> <work dir> <out.png> --grids 1,0.5,0.25

A grid of 1 is the mod's unit (1/16 block, vanilla's pixel); 0.5 is 32 per block, 0.25 is 64.
"""
import math, os, sys, time
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image, ImageDraw

BLEND, WORK, OUT = sys.argv[1:4]
GRIDS = [float(g) for g in sys.argv[sys.argv.index("--grids") + 1].split(",")] if "--grids" in sys.argv else [1, 0.5, 0.25]
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
C8 = math.cos(math.radians(22.5))


def srgb_to_lin(c):
    c = np.asarray(c, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


EMB = np.asarray(Image.open(os.path.join(WORK, "emblem.png")).convert("RGB"))
CAP = np.asarray(Image.open(os.path.join(WORK, "captop.png")).convert("RGB"))

# ---- the source parts -----------------------------------------------------------------------------
THIN = ("glass_", "lens_", "port_dark", "cap_disc")
src = []
for o in scene.objects:
    if o.type != "MESH" or o.hide_render:
        continue
    bvh = BVHTree.FromObject(o, dg)
    mw = o.matrix_world.copy()
    inv = mw.inverted()
    pts = [mw @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    src.append({"o": o, "bvh": bvh, "inv": inv, "nm": inv.to_3x3().transposed(), "lo": lo, "hi": hi,
                "mat": o.active_material.name if o.active_material else "stone", "thin": o.name.startswith(THIN)})
LO = Vector((min(s["lo"].x for s in src), min(s["lo"].y for s in src), min(s["lo"].z for s in src)))
HI = Vector((max(s["hi"].x for s in src), max(s["hi"].y for s in src), max(s["hi"].z for s in src)))


def hash3(i, j, k):
    h = (i * 374761393 + j * 668265263 + k * 1274126177) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFF) / 0xFFFF


def colour(s, p, g, ijk):
    """(linear rgb, kind) for a cube at p taken by part s; kind 0 stone, 1 metal, 2 glow."""
    mat = s["mat"]
    lp = s["inv"] @ p
    r = hash3(*ijk)
    if mat == "emblem":
        u = lp.x / (2 * 3.75 / C8) + 0.5
        v = lp.y / (2 * 3.75 / C8) + 0.5
        px = EMB[int(np.clip(1 - v, 0, 0.999) * EMB.shape[0]), int(np.clip(u, 0, 0.999) * EMB.shape[1])]
        return srgb_to_lin(px), 2
    if mat == "lens":
        d = min(1.0, lp.length / (3.75 * 1.05))
        stops = [(0.0, (0.004, 0.03, 0.25)), (0.45, (0.03, 0.25, 1.0)), (0.85, (0.75, 0.92, 1.0))]
        f = 1 - d   # the gradient runs bright at the centre
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= f <= b:
                t = (f - a) / (b - a)
                return np.array(ca) * (1 - t) + np.array(cb) * t, 2
        return np.array(stops[-1][1]), 2
    if mat == "captop":
        u, v = lp.x / 6.3 + 0.5, lp.y / 6.3 + 0.5
        px = CAP[int(np.clip(1 - v, 0, 0.999) * CAP.shape[0]), int(np.clip(u, 0, 0.999) * CAP.shape[1])]
        return srgb_to_lin(px), 1
    if mat == "hollow":
        return np.array([0.004, 0.004, 0.004]), 0
    if mat == "bronze":
        return np.array([0.32, 0.17, 0.07]) * (0.8 + 0.45 * r), 1
    return np.array([0.07, 0.115, 0.2]) * (0.8 + 0.4 * r), 0


def voxelize(g):
    n = [int(math.ceil((HI[a] - LO[a]) / g)) + 2 for a in range(3)]
    occ = np.zeros(n, bool)
    col = np.zeros(n + [3])
    kind = np.zeros(n, np.int8)
    for i in range(n[0]):
        for j in range(n[1]):
            for k in range(n[2]):
                p = Vector((LO.x + (i - 0.5) * g, LO.y + (j - 0.5) * g, LO.z + (k - 0.5) * g))
                best = None
                for s in src:
                    if not (s["lo"].x - g <= p.x <= s["hi"].x + g and s["lo"].y - g <= p.y <= s["hi"].y + g
                            and s["lo"].z - g <= p.z <= s["hi"].z + g):
                        continue
                    loc, nrm, idx, dist = s["bvh"].find_nearest(s["inv"] @ p)
                    if loc is None:
                        continue
                    dist_w = (s["o"].matrix_world @ loc - p).length
                    inside = (s["inv"] @ p - loc).dot(nrm) < 0 and not s["thin"]
                    near = dist_w < g * 0.55
                    if inside or near:
                        score = (0 if s["thin"] else 1, dist_w)
                        if best is None or score < best[0]:
                            best = (score, s)
                if best:
                    c, kd = colour(best[1], p, g, (i, j, k))
                    occ[i, j, k] = True
                    col[i, j, k] = c
                    kind[i, j, k] = kd
    return occ, col, kind


def build(name, occ, col, kind, g):
    """Only the faces between a cube and empty space, as one mesh with per-face colour."""
    verts, faces, fcol, fmat = [], [], [], []
    vid = {}

    def v(x, y, z):
        key = (x, y, z)
        if key not in vid:
            vid[key] = len(verts)
            verts.append((LO.x + (x - 1) * g, LO.y + (y - 1) * g, LO.z + (z - 1) * g))
        return vid[key]
    dirs = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
            ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
            ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
            ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
            ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
            ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]
    I = np.argwhere(occ)
    for i, j, k in I:
        for (dx, dy, dz), corners in dirs:
            a, b, c = i + dx, j + dy, k + dz
            if 0 <= a < occ.shape[0] and 0 <= b < occ.shape[1] and 0 <= c < occ.shape[2] and occ[a, b, c]:
                continue
            faces.append([v(i + x, j + y, k + z) for x, y, z in corners])
            fcol.append(col[i, j, k])
            fmat.append(int(kind[i, j, k]))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    attr = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    cols = np.repeat(np.array(fcol), 4, axis=0)
    attr.data.foreach_set("color", np.hstack([cols, np.ones((len(cols), 1))]).ravel())
    me.polygons.foreach_set("material_index", fmat)
    for m in MATS:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    return o, len(faces)


def vox_mat(name, metal, glow):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute")
    at.attribute_name = "col"
    L.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.4 if metal else 0.85
    bsdf.inputs["Metallic"].default_value = 0.9 if metal else 0.0
    if glow:
        L.new(at.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
    return m


MATS = [vox_mat("vox_stone", False, False), vox_mat("vox_metal", True, False), vox_mat("vox_glow", False, True)]

for o in list(scene.objects):
    if o.type == "MESH":
        o.hide_render = True
scene.cycles.samples = 16
SIZE = 360
scene.render.resolution_x = scene.render.resolution_y = SIZE
cam = scene.camera
target = Vector((0, 0, 11.3))
VIEWS = [("FRONT", 0, 6), ("LEFT", 90, 6), ("FRONT LEFT", 40, 14)]
rows = []
for g in GRIDS:
    t0 = time.time()
    occ, col, kind = voxelize(g)
    obj, nf = build(f"vox_{g}", occ, col, kind, g)
    t1 = time.time()
    tiles = []
    for label, yaw, pitch in VIEWS:
        y, p = math.radians(yaw), math.radians(pitch)
        d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
        cam.location = target + d * 80
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(WORK, f"vox_{g}_{label.replace(' ', '_')}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        tiles.append(path)
    obj.hide_render = True
    per_block = int(round(16 / g))
    rows.append((f"grid {g} unit = {per_block} per block: {int(occ.sum()):,} cubes, {nf:,} faces ({2 * nf:,} triangles)", tiles))
    print(rows[-1][0], f"voxelized in {t1 - t0:.0f}s")

sheet_views = []
W = SIZE * (len(VIEWS))
img = Image.new("RGB", (W, (SIZE + 28) * len(rows)), (40, 40, 44))
d = ImageDraw.Draw(img)
for r, (label, tiles) in enumerate(rows):
    y0 = r * (SIZE + 28)
    d.text((8, y0 + 8), label, fill=(240, 240, 240))
    for c, path in enumerate(tiles):
        img.paste(Image.open(path).convert("RGB"), (c * SIZE, y0 + 28))
img.save(OUT)
print("wrote", OUT)
