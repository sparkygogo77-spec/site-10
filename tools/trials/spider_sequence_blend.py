"""Blender block-out of the three-part spider fight from spider_sequence.py.

blender.exe -b --python spider_sequence_blend.py -- <dir with sequence.npz> <out.blend> [--no-render]

Two copies of the grid: one cut in half north-south (row at Y = 0) for the section cameras, one whole (row further
south) for the inside cameras. Materials: cave stone, burrow earth, silk (funnel trap and the drop), webbed dirt (the
trap floor), cut stone / deepslate, grass. Stand-ins: the yellow construct spider (20-block leg span) in cave 1 and in
the trap, the real spider (36-block span, stone spikes on every leg tip) in the lair, a 1.8-block player, the net.
Cameras:
  01 overview cutaway   02 trap and net cutaway   03 cave 1 inside   04 funnel trap inside
  05 down from the net  06 lair floor
"""
import json, math, os, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
RENDER = "--no-render" not in argv
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_blender_kit as K
K.sc = sc
TEXTURED = "--flat" not in argv


def mat(name, rgb, rough=0.9, emit=None, strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


M = K.cave_materials(textured=TEXTURED)    # 0 rock .. 7 webbed dirt, 8 dripstone, 9 construct tip
M_CONSTRUCT = mat("yellow construct", (1.0, 0.8, 0.1), 0.3, (1.0, 0.75, 0.05), 3.0, alpha=0.75)
M_SPIDER = mat("real spider", (0.03, 0.025, 0.02), 0.5)
M_SPIKE = mat("web-rock spike", (0.45, 0.44, 0.42), 0.8)
M_EYES = mat("spider eyes", (1, 0.8, 0.1), 0.4, (1, 0.75, 0.05), 8)
M_PLAYER = mat("player", (0.15, 0.3, 0.6), 0.6)
M_RING = mat("ring", (0.2, 1, 0.4), 0.3, (0.2, 1, 0.4), 12)
M_NET = mat("cobweb net", (0.9, 0.9, 0.88), 0.5)
DEEP_IDX = 64 + 4
EARTH = (2, 3, 4, 6, 8)
SILK = (7, 9)

d = np.load(os.path.join(SRC, "sequence.npz"))
solid, mask, dirt, net, meta = d["solid"], d["mask"], d["dirt"], d["net"], json.loads(str(d["meta"]))
drip = d["drip"] if "drip" in d.files else np.zeros_like(mask)
X, Y, Z = solid.shape
ZC = Z // 2
ROW_FULL = -(Z + 300.0)


def B(x, y, z, row=0.0):
    """Grid (x, y up, z) to Blender (x, -z, y)."""
    return (x, -z + row, y)


def voxel_mesh(name, cut_z=None, outer=True):
    s = solid.copy()
    if cut_z is not None:
        s[:, :, cut_z + 1:] = False
    pad = np.zeros((X + 2, Y + 2, Z + 2), bool); pad[1:-1, 1:-1, 1:-1] = s
    real_air = np.zeros_like(pad); real_air[1:-1, 1:-1, 1:-1] = ~solid
    mpad = np.zeros(pad.shape, np.uint8); mpad[1:-1, 1:-1, 1:-1] = mask
    dpad = np.zeros_like(pad); dpad[1:-1, 1:-1, 1:-1] = dirt
    rpad = np.zeros(pad.shape, np.uint8); rpad[1:-1, 1:-1, 1:-1] = drip
    corner = {
        (0, 1): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (0, -1): [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
        (1, 1): [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], (1, -1): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        (2, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (2, -1): [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
    }
    verts, faces, mats = [], [], []
    for (ax, dd), cs in corner.items():
        hit = pad & ~np.roll(pad, -dd, axis=ax)
        idx = np.argwhere(hit)
        if not len(idx):
            continue
        n = idx.copy(); n[:, ax] += dd
        is_air = real_air[n[:, 0], n[:, 1], n[:, 2]]
        tag = mpad[n[:, 0], n[:, 1], n[:, 2]]
        own_dirt = dpad[idx[:, 0], idx[:, 1], idx[:, 2]]
        gy = idx[:, 1] - 1
        cutm = np.where(gy < DEEP_IDX, 4, 2)
        if ax == 1 and dd == 1:
            cutm = np.where(gy == Y - 1, 5, cutm)
        m = np.where(~is_air, cutm, np.where(tag == 5, 3, np.where(np.isin(tag, SILK), 6, np.where(np.isin(tag, EARTH), 1, 0))))
        m = np.where(own_dirt, 7, m)
        own_drip = rpad[idx[:, 0], idx[:, 1], idx[:, 2]]
        m = np.where(own_drip == 1, 8, np.where(own_drip == 2, 9, m))
        if not outer:
            idx, m = idx[is_air], m[is_air]
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


def rod(name, a, b, r, m, parent, cone=False):
    a, b = np.array(a, float), np.array(b, float)
    dv = b - a; L = float(np.linalg.norm(dv))
    if cone:
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=0, depth=L, location=tuple((a + b) / 2))
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=L, location=tuple((a + b) / 2))
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(dv / L))
    o.parent = parent


def spider(name, loc, span, body_m, yaw=0.0, spikes=False):
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    root.location = loc; root.rotation_euler = (0, 0, yaw)
    s = span / 10.0; bh = 1.4 * s
    blob(name + " abdomen", (0, -1.9 * s, bh + 0.3 * s), (1.5 * s, 2.1 * s, 1.3 * s), body_m, root)
    blob(name + " head", (0, 0.6 * s, bh), (1.0 * s, 1.1 * s, 0.8 * s), body_m, root)
    for i in range(8):
        blob(name + f" eye{i}", ((i - 3.5) * 0.18 * s, 1.55 * s, bh + 0.35 * s + (i % 2) * 0.12 * s), (0.09 * s,) * 3, M_EYES, root)
    for side in (-1, 1):
        for k in range(4):
            a = math.radians(-50 + k * 33); reach = span / 2 - 0.2
            hip = (side * 0.7 * s, 0.6 * s - k * 0.35 * s, bh)
            knee = (side * reach * 0.55 * math.cos(a), reach * 0.55 * math.sin(-a) + 0.3 * s, bh + 1.8 * s)
            foot = (side * reach * math.cos(a), reach * math.sin(-a), 0.05)
            rod(name + f" leg{side}{k}a", hip, knee, 0.16 * s, body_m, root)
            if spikes:   # the last 30% of each leg is a silk-bound stone spike
                tip0 = tuple(np.array(knee) + (np.array(foot) - np.array(knee)) * 0.7)
                rod(name + f" leg{side}{k}b", knee, tip0, 0.11 * s, body_m, root)
                rod(name + f" spike{side}{k}", tip0, foot, 0.22 * s, M_SPIKE, root, cone=True)
            else:
                rod(name + f" leg{side}{k}b", knee, foot, 0.11 * s, body_m, root)


def player(name, loc):
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); root.location = loc
    for nm, l, dim in [("legs", (0, 0, 0.375), (0.5, 0.25, 0.75)), ("body", (0, 0, 1.125), (0.5, 0.25, 0.75)), ("head", (0, 0, 1.75), (0.5, 0.5, 0.5))]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=l)
        o = bpy.context.object; o.name = f"{name} {nm}"; o.scale = dim; o.data.materials.append(M_PLAYER); o.parent = root
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


def net_object(name, row):
    ys = np.flatnonzero(net.any(axis=(0, 2)))
    if not len(ys):
        return
    ny = int(ys[0]); cells = np.argwhere(net[:, ny, :])
    cx_, cz_ = cells.mean(0); r = max(np.ptp(cells[:, 0]), np.ptp(cells[:, 1])) / 2 + 0.5
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=r, fill_type="NGON", location=B(cx_ + 0.5, ny + 0.5, cz_ + 0.5, row))
    o = bpy.context.object; o.name = name; o.data.materials.append(M_NET)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=10); bpy.ops.object.mode_set(mode="OBJECT")
    for v in o.data.vertices:   # sag in the middle
        rr = math.hypot(v.co.x, v.co.y) / r
        v.co.z -= 2.5 * (1 - min(1, rr) ** 2)
    w = o.modifiers.new("web strands", "WIREFRAME"); w.thickness = 0.12


def floor_of(x, z, tags=(1,)):
    col = np.flatnonzero(np.isin(mask[int(x), :, int(z)], tags))
    return int(col.min()) if len(col) else Y // 2


c1 = meta["cave1"]; lair = meta["lair"]; trap = meta["trap"]
c1x = c1["offset"][0] + c1["size"][0] // 2
lx = lair["offset"][0] + lair["size"][0] // 2
tx, tz = trap["x"], trap["z"]
fy_trap = trap["floor_y"] - meta["y_min"]
cams = []
for row_name, row in (("cutaway", 0.0), ("full", ROW_FULL)):
    vo = voxel_mesh(f"sequence {row_name}", ZC if row_name == "cutaway" else None, outer=row_name == "cutaway")
    vo.location.y = row
    net_object(f"cobweb net {row_name}", row)
    f1 = floor_of(c1x, ZC)
    K.spider("C1", f"construct spider cave1 {row_name}", B(c1x + 10, f1, ZC - 8, row), 20, yaw=math.radians(110))
    K.spider("C1", f"construct spider trap {row_name}", B(tx + 2, fy_trap + 1, tz - 3, row), 20, yaw=math.radians(200))
    fl = floor_of(lx, ZC)
    K.spider("R3", f"real spider {row_name}", B(lx + 10, fl, ZC - 10, row), 36, yaw=math.radians(150))
    player(f"player cave1 {row_name}", B(c1x - 20, floor_of(c1x - 20, ZC), ZC, row))
    player(f"player trap {row_name}", B(tx - 7, fy_trap + 1, tz, row))
    player(f"player lair {row_name}", B(lx - 25, floor_of(lx - 25, ZC), ZC, row))
    light(f"cave1 glow {row_name}", B(c1x, f1 + 25, ZC, row), 60000, (1, 0.85, 0.35))
    light(f"trap glow {row_name}", B(tx, fy_trap + 9, tz, row), 500, (1, 0.9, 0.7))
    for k in range(5):
        a = k / 5 * math.tau
        light(f"lair glow {k} {row_name}", B(lx + math.cos(a) * 60, fl + 30, ZC + math.sin(a) * 45, row), 25000, (0.75, 0.8, 1.0))
    if row_name == "cutaway":
        cams.append(camera("01 overview cutaway", B(X * 0.5, Y * 0.75, ZC + X * 0.95, row), B(X * 0.5, Y * 0.5, ZC, row), 30))
        cams.append(camera("02 trap and net cutaway", B(tx + 25, fy_trap + 5, ZC + 150, row), B(tx, fy_trap - 20, ZC, row), 30))
        light("key", B(X * 0.5, Y * 1.4, ZC + X, row), 1500000, (1, 0.95, 0.9), "AREA", 300)
        light("trap key", B(tx, fy_trap + 5, ZC + 60, row), 60000, (1, 0.95, 0.9), "AREA", 40)
    else:
        cams.append(camera("03 cave 1 inside", B(c1x - 45, f1 + 4, ZC + 6, row), B(c1x + 20, f1 + 6, ZC - 6, row), 18))
        cams.append(camera("04 funnel trap inside", B(tx - 10, fy_trap + 4, tz + 1, row), B(tx + 6, fy_trap + 1, tz - 2, row), 14))
        cams.append(camera("05 down from the net", B(tx, fy_trap - 13, tz, row), B(lx + 10, fl, ZC - 10, row), 18))
        cams.append(camera("07 lair ceiling spikes", B(lx - 40, fl + 4, ZC + 10, row), B(lx + 10, fl + 45, ZC - 20, row), 16))
        cams.append(camera("06 lair floor", B(lx - 50, floor_of(lx - 50, ZC) + 3, ZC + 8, row), B(lx + 10, fl + 8, ZC - 10, row), 18))

w = bpy.data.worlds.new("World"); sc.world = w
try:
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.5, 0.7, 1) if row_name == "cutaway" else (0.35, 0.5, 0.7, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4
except Exception as e:
    print("world", e)
sc.render.engine = "CYCLES"; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.cycles.use_preview_denoising = True
prefs = bpy.context.preferences.addons["cycles"].preferences
for dt in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dt; prefs.get_devices()
        if any(dv.type == dt for dv in prefs.devices):
            for dv in prefs.devices:
                dv.use = dv.type == dt
            sc.cycles.device = "GPU"; break
    except TypeError:
        continue
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "Standard"
sc.camera = cams[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
if RENDER:
    rdir = os.path.join(os.path.dirname(OUT), "renders_sequence")
    os.makedirs(rdir, exist_ok=True)
    for cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".png")
        bpy.ops.render.render(write_still=True)
    sc.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("done", OUT)
