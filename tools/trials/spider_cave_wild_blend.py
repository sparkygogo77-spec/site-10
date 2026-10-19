"""Blender build for spider_cave_wild.py (round 3): six seeds, each cut in half along its length, at real heights.

blender.exe -b --python spider_cave_wild_blend.py -- <dir with V1.npz..> <out.blend> [--no-render]

Layout: V1-V3 in one row, V4-V6 in the next (cutaway row at Y = 0 / -400). A second, uncut copy of each sits 900
blocks further south for its inside camera. The grid's z=0 is world y -64; the cut face is grass on top (y 72, a
typical plains surface), stone down to y 4, deepslate below. Each has a spider stand-in and a 1.8-block player.
Cameras: "NN Vk cutaway" and "NN Vk inside" (from the floor by a column, looking along the cave).
"""
import json, math, os, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
RENDER = "--no-render" not in argv
TAKES = sorted(f[:-4] for f in os.listdir(SRC) if f.startswith("V") and f.endswith(".npz"))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, rgb, rough=0.9, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"] if m.node_tree else None
    if b is None:
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


M = [mat("cave wall", (0.17, 0.16, 0.14)), mat("burrow earth", (0.20, 0.12, 0.07)), mat("cut stone", (0.20, 0.20, 0.21)),
     mat("entrance shaft", (0.25, 0.32, 0.42)), mat("cut deepslate", (0.06, 0.06, 0.07)), mat("grass", (0.18, 0.35, 0.10))]
M_SPIDER = mat("spider stand-in", (0.03, 0.025, 0.02), 0.5)
M_EYES = mat("spider eyes", (1, 0.8, 0.1), 0.4, (1, 0.75, 0.05), 8)
M_PLAYER = mat("player", (0.15, 0.3, 0.6), 0.6)
M_RING = mat("ring", (0.2, 1, 0.4), 0.3, (0.2, 1, 0.4), 12)
DEEP_IDX = 64 + 4      # grid index of world y 4: deepslate below


def voxel_mesh(name, solid, mask, cut_z=None, outer=True):
    X, Y, Z = solid.shape
    s = solid.copy()
    if cut_z is not None:
        s[:, :, cut_z + 1:] = False
    pad = np.zeros((X + 2, Y + 2, Z + 2), bool); pad[1:-1, 1:-1, 1:-1] = s
    real_air = np.zeros_like(pad); real_air[1:-1, 1:-1, 1:-1] = ~solid
    mpad = np.zeros(pad.shape, np.uint8); mpad[1:-1, 1:-1, 1:-1] = mask
    corner = {
        (0, 1): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (0, -1): [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
        (1, 1): [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], (1, -1): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        (2, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (2, -1): [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
    }
    verts, faces, mats = [], [], []
    for (ax, d), cs in corner.items():
        hit = pad & ~np.roll(pad, -d, axis=ax)
        idx = np.argwhere(hit)
        if not len(idx):
            continue
        n = idx.copy(); n[:, ax] += d
        is_air = real_air[n[:, 0], n[:, 1], n[:, 2]]
        tag = mpad[n[:, 0], n[:, 1], n[:, 2]]
        gy = idx[:, 1] - 1
        cutm = np.where(gy < DEEP_IDX, 4, 2)
        if ax == 1 and d == 1:
            cutm = np.where(gy == Y - 1, 5, cutm)
        m = np.where(~is_air, cutm, np.where(tag == 5, 3, np.where(np.isin(tag, (2, 3, 4, 6)), 1, 0)))
        if not outer:
            keep = is_air
            idx, m = idx[keep], m[keep]
        base = idx - 1
        quad = np.stack([base + np.array(c) for c in cs], 1).reshape(-1, 3)
        k = np.arange(len(idx)) * 4 + len(verts)
        verts.extend(quad.tolist()); faces.extend(np.stack([k, k + 1, k + 2, k + 3], 1).tolist()); mats.extend(m.tolist())
    me = bpy.data.meshes.new(name)
    v = np.asarray(verts, float)
    me.from_pydata(np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1).tolist(), [], faces)
    for m_ in M:
        me.materials.append(m_)
    me.polygons.foreach_set("material_index", np.asarray(mats, np.int32))
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.001, verts=bm.verts, edges=bm.edges, delimit={"MATERIAL"})
    bm.to_mesh(me); bm.free(); me.update()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


def blob(name, loc, scale, m, parent):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); o.parent = parent
    return o


def rod(name, a, b, r, m, parent):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a; L = float(np.linalg.norm(d))
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=L, location=tuple((a + b) / 2))
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(d / L))
    o.parent = parent


def spider(name, loc, span, yaw=0.0):
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    root.location = loc; root.rotation_euler = (0, 0, yaw)
    s = span / 10.0; bh = 1.4 * s
    blob(name + " abdomen", (0, -1.9 * s, bh + 0.3 * s), (1.5 * s, 2.1 * s, 1.3 * s), M_SPIDER, root)
    blob(name + " head", (0, 0.6 * s, bh), (1.0 * s, 1.1 * s, 0.8 * s), M_SPIDER, root)
    for i in range(8):
        blob(name + f" eye{i}", ((i - 3.5) * 0.18 * s, 1.55 * s, bh + 0.35 * s + (i % 2) * 0.12 * s), (0.09 * s,) * 3, M_EYES, root)
    for side in (-1, 1):
        for k in range(4):
            a = math.radians(-50 + k * 33); reach = span / 2 - 0.2
            hip = (side * 0.7 * s, 0.6 * s - k * 0.35 * s, bh)
            knee = (side * reach * 0.55 * math.cos(a), reach * 0.55 * math.sin(-a) + 0.3 * s, bh + 1.8 * s)
            foot = (side * reach * math.cos(a), reach * math.sin(-a), 0.05)
            rod(name + f" leg{side}{k}a", hip, knee, 0.16 * s, M_SPIDER, root)
            rod(name + f" leg{side}{k}b", knee, foot, 0.11 * s, M_SPIDER, root)


def player(name, loc):
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); root.location = loc
    for nm, l, dim, m in [("legs", (0, 0, 0.375), (0.5, 0.25, 0.75), M_PLAYER), ("body", (0, 0, 1.125), (0.5, 0.25, 0.75), M_PLAYER),
                          ("head", (0, 0, 1.75), (0.5, 0.5, 0.5), M_PLAYER)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=l)
        o = bpy.context.object; o.name = f"{name} {nm}"; o.scale = dim; o.data.materials.append(m); o.parent = root
    blob(name + " ring glow", (0.4, 0.3, 1.1), (0.08,) * 3, M_RING, root)
    lt = bpy.data.lights.new(name + " ring light", "POINT"); lt.energy = 300; lt.color = (0.3, 1, 0.45)
    lo = bpy.data.objects.new(name + " ring light", lt); sc.collection.objects.link(lo); lo.parent = root; lo.location = (0.5, 0.3, 1.3)


def camera(name, loc, target, lens=24):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 3000
    c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c)
    c.location = loc; c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return c


def light(name, loc, energy, color, kind="POINT", size=1.0):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = color
    if kind == "AREA":
        lt.size = size
    o = bpy.data.objects.new(name, lt); sc.collection.objects.link(o); o.location = loc


def floor_z(mask, x, z):
    """Lowest cave-floor air in this column (ignores the tunnels underneath)."""
    col = np.flatnonzero(mask[x, :, z] == 1)
    return int(col.min()) if len(col) else 40


cams = []
for ti, take in enumerate(TAKES):
    d = np.load(os.path.join(SRC, take + ".npz"))
    solid, mask, meta = d["solid"], d["mask"], json.loads(str(d["meta"]))
    X, Y, Z = solid.shape
    cx, cz = X // 2, Z // 2
    ox, oy = (ti % 3) * 450.0, -(ti // 3) * 450.0
    for row in ("cutaway", "full"):
        ry = oy if row == "cutaway" else oy - 1000.0
        o = voxel_mesh(f"{take} cave {row}", solid, mask, cz if row == "cutaway" else None, outer=row == "cutaway")
        o.location = (ox - cx, ry + cz, 0)
        fz = floor_z(mask, cx, cz)
        spider(f"{take} spider {row}", (ox + 4, ry + 8, fz), meta["span"], yaw=math.radians(160))
        fz2 = floor_z(mask, cx - 30, cz)
        player(f"{take} player {row}", (ox - 30, ry + 2, fz2))
        top = meta["cave_top_y"] - meta["y_min"]
        if row == "cutaway":
            dist = X * 1.2
            cams.append(camera(f"{ti * 2 + 1:02d} {take} cutaway", (ox + dist * 0.15, ry - dist, Y * 0.7), (ox, ry, Y * 0.55), 32))
            light(f"{take} key", (ox + dist * 0.3, ry - dist, Y * 1.3), 400000, (1, 0.95, 0.9), "AREA", 160)
            light(f"{take} cave glow", (ox, ry + 10, (fz + top) / 2), 30000, (1, 0.85, 0.35))
        else:
            c0 = meta["columns"][0] if meta["columns"] else [0, 0, 3]
            px, pz = cx - meta["length"] * 0.42, cz
            fz3 = floor_z(mask, int(px), int(pz))
            cams.append(camera(f"{ti * 2 + 2:02d} {take} inside", (ox + px - cx, ry, fz3 + 3), (ox + 20, ry - 4, fz + 6), 16))
            for k in range(6):
                a = k / 6 * math.tau
                light(f"{take} inside glow {k}", (ox + math.cos(a) * meta["length"] * 0.3, ry + math.sin(a) * meta["width"] * 0.3, (fz + top) / 2),
                      20000, (1, 0.8, 0.3))
    print(take, "faces", sum(len(o.data.polygons) for o in sc.objects if o.type == "MESH" and o.name.startswith(take + " cave")))

w = bpy.data.worlds.new("World"); sc.world = w
try:
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.5, 0.7, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4
except Exception as e:
    print("world", e)
sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.use_denoising = True
prefs = bpy.context.preferences.addons["cycles"].preferences
for dt in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dt; prefs.get_devices()
        if any(dv.type == dt for dv in prefs.devices):
            for dv in prefs.devices:
                dv.use = dv.type == dt
            sc.cycles.device = "GPU"; print("GPU", dt); break
    except TypeError:
        continue
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "Standard"
sc.camera = cams[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
if RENDER:
    rdir = os.path.join(os.path.dirname(OUT), "renders_wild")
    os.makedirs(rdir, exist_ok=True)
    for cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".png")
        bpy.ops.render.render(write_still=True)
    sc.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("done", OUT)
