"""Build the giant-spider cave size study in Blender from spider_cave.py's grids, render check stills, save the .blend.

blender.exe -b --python spider_cave_blend.py -- <dir with C1.npz..> <out.blend> [--no-render]

Per take (C1, C2, C3), 220 blocks apart along X:
  cutaway  the cave cut in half north-south so the chamber, burrows and tunnels show in section (row at Z = 0)
  full     the whole cave for the inside camera (row at Z = 400)
Each has a spider stand-in at the take's leg span on the floor, one climbing out of the burrow nearest the camera, and a 1.8-block player.
"""
import json, math, os, sys
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
RENDER = "--no-render" not in argv
TAKES = ["C1", "C2", "C3"]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, rgb, rough=0.9, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


M_CHAMBER = mat("cave stone", (0.16, 0.15, 0.14))
M_TUNNEL = mat("burrow earth", (0.20, 0.12, 0.07))
M_CUT = mat("cut rock", (0.11, 0.11, 0.12))
M_SPIDER = mat("spider stand-in", (0.03, 0.025, 0.02), 0.5)
M_EYES = mat("spider eyes", (1, 0.8, 0.1), 0.4, (1, 0.75, 0.05), 8)
M_PLAYER = mat("player", (0.15, 0.3, 0.6), 0.6)
M_RING = mat("ring", (0.2, 1, 0.4), 0.3, (0.2, 1, 0.4), 12)
MATS = [M_CHAMBER, M_TUNNEL, M_CUT]
TUNNEL_TAGS = (2, 3, 4)


def voxel_mesh(name, solid, mask, cut_z=None):
    """Quads between solid and air. Material 0 = chamber air side, 1 = tunnel side, 2 = cut or outer face."""
    X, Y, Z = solid.shape
    s = solid.copy()
    if cut_z is not None:
        s[:, :, cut_z + 1:] = False
    pad = np.zeros((X + 2, Y + 2, Z + 2), bool)
    pad[1:-1, 1:-1, 1:-1] = s
    real_air = np.zeros_like(pad)
    real_air[1:-1, 1:-1, 1:-1] = ~solid
    mpad = np.zeros(pad.shape, np.uint8)
    mpad[1:-1, 1:-1, 1:-1] = mask
    verts, faces, mats = [], [], []
    # (axis, direction) -> quad corner offsets
    corner = {
        (0, 1): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (0, -1): [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
        (1, 1): [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], (1, -1): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        (2, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (2, -1): [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
    }
    for (ax, d), cs in corner.items():
        nb = np.roll(pad, -d, axis=ax)
        hit = pad & ~nb
        idx = np.argwhere(hit)
        if not len(idx):
            continue
        nidx = idx.copy(); nidx[:, ax] += d
        is_air = real_air[nidx[:, 0], nidx[:, 1], nidx[:, 2]]
        tag = mpad[nidx[:, 0], nidx[:, 1], nidx[:, 2]]
        m = np.where(~is_air, 2, np.where(np.isin(tag, TUNNEL_TAGS), 1, 0))
        base = idx - 1
        n0 = len(verts)
        quad = np.stack([base + np.array(c) for c in cs], 1).reshape(-1, 3)
        verts.extend(quad.tolist())
        k = np.arange(len(idx)) * 4 + n0
        faces.extend(np.stack([k, k + 1, k + 2, k + 3], 1).tolist())
        mats.extend(m.tolist())
    me = bpy.data.meshes.new(name)
    # grid (x, y, z) with y up -> Blender (x, -z, y)
    v = np.asarray(verts, float)
    me.from_pydata(np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1).tolist(), [], faces)
    for m_ in MATS:
        me.materials.append(m_)
    me.polygons.foreach_set("material_index", np.asarray(mats, np.int32))
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    return ob


def blob(name, loc, scale, m, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


def rod(name, a, b, r, m, parent):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a; L = float(np.linalg.norm(d))
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=L, location=tuple((a + b) / 2))
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    o.rotation_mode = "QUATERNION"
    from mathutils import Vector
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(d / L))
    o.parent = parent


def spider(name, loc, span, yaw=0.0, pitch=0.0):
    """Stand-in only: an empty with a body, a crown of eyes and 8 two-part legs reaching span blocks tip to tip."""
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    root.location = loc; root.rotation_euler = (pitch, 0, yaw)
    s = span / 10.0
    body_h = 1.4 * s
    blob(name + " abdomen", (0, -1.9 * s, body_h + 0.3 * s), (1.5 * s, 2.1 * s, 1.3 * s), M_SPIDER, root)
    blob(name + " head", (0, 0.6 * s, body_h), (1.0 * s, 1.1 * s, 0.8 * s), M_SPIDER, root)
    for i in range(8):
        e = blob(name + f" eye{i}", ((i - 3.5) * 0.18 * s, 1.55 * s, body_h + 0.35 * s + (i % 2) * 0.12 * s),
                 (0.09 * s,) * 3, M_EYES, root)
    for side in (-1, 1):
        for k in range(4):
            a = math.radians(-50 + k * 33)
            hip = (side * 0.7 * s, 0.6 * s - k * 0.35 * s, body_h)
            reach = span / 2 - 0.2
            knee = (side * (reach * 0.55) * math.cos(a), (reach * 0.55) * math.sin(-a) + 0.3 * s, body_h + 1.8 * s)
            foot = (side * reach * math.cos(a), reach * math.sin(-a), 0.05)
            rod(name + f" leg{side}{k}a", hip, knee, 0.16 * s, M_SPIDER, root)
            rod(name + f" leg{side}{k}b", knee, foot, 0.11 * s, M_SPIDER, root)
    return root


def player(name, loc):
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); root.location = loc
    for nm, l, dim, m in [("legs", (0, 0, 0.375), (0.5, 0.25, 0.75), M_PLAYER), ("body", (0, 0, 1.125), (0.5, 0.25, 0.75), M_PLAYER),
                          ("head", (0, 0, 1.75), (0.5, 0.5, 0.5), mat(name + " skin", (0.7, 0.5, 0.35)))]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=l)
        o = bpy.context.object; o.name = f"{name} {nm}"; o.scale = dim; o.data.materials.append(m)
        o.parent = root
    blob(name + " ring glow", (0.4, 0.3, 1.1), (0.08,) * 3, M_RING, root)
    lt = bpy.data.lights.new(name + " ring light", "POINT"); lt.energy = 300; lt.color = (0.3, 1, 0.45)
    lo = bpy.data.objects.new(name + " ring light", lt); sc.collection.objects.link(lo); lo.parent = root; lo.location = (0.5, 0.3, 1.3)
    return root


def camera(name, loc, target, lens=24):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 2000
    c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return c


def light(name, loc, energy, color, kind="POINT", size=1.0):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = color
    if kind == "AREA":
        lt.size = size
    o = bpy.data.objects.new(name, lt); sc.collection.objects.link(o); o.location = loc
    return o


cams = []
for ti, take in enumerate(TAKES):
    d = np.load(os.path.join(SRC, take + ".npz"))
    solid, mask, meta = d["solid"], d["mask"], json.loads(str(d["meta"]))
    X, Y, Z = solid.shape
    c = X // 2
    ox = ti * 220.0
    yf = meta["y_floor"] + 1
    span = meta["span"]
    for row, cut in (("cutaway", c), ("full", None)):
        oy = 0.0 if row == "cutaway" else -400.0
        o = voxel_mesh(f"{take} cave {row}", solid, mask, cut)
        o.location = (ox - c, oy + c, 0)
        centre = (ox, oy, yf)
        spider(f"{take} spider {row}", (ox - 4, oy + 6, yf), span, yaw=math.radians(200))
        h = min((x for x in meta["holes"] if x["z"] < -2), key=lambda x: abs(x["x"]))   # a burrow on the kept half
        spider(f"{take} spider burrow {row}", (ox + h["x"], oy - h["z"], yf - span * 0.18), span * 0.98,
               yaw=math.atan2(-h["z"], h["x"]) + math.pi / 2, pitch=math.radians(-25))
        player(f"{take} player {row}", (ox - meta["R"] * 0.55, oy, yf))
        if row == "cutaway":
            dist = meta["R"] * 2.6
            cams.append(camera(f"{ti * 2 + 1:02d} {take} cutaway", (ox + dist * 0.35, oy - dist, yf + dist * 0.55),
                               (ox, oy + 4, yf - meta["depth"] * 0.4), 30))
            light(f"{take} key", (ox + 20, oy - 120, yf + 90), 150000 * (meta["R"] / 32) ** 2, (1, 0.95, 0.9), "AREA", 80)
            light(f"{take} cave glow", (ox, oy + 6, yf + meta["H"] * 0.6), 9000 * (meta["R"] / 32) ** 2, (1, 0.85, 0.35))
        else:
            ex = ox - meta["R"] * 0.78
            cams.append(camera(f"{ti * 2 + 2:02d} {take} inside", (ex, oy + 1.5, yf + 1.62), (ox + meta["R"] * 0.5, oy - 2, yf + 3), 18))
            for k in range(5):
                a = k / 5 * math.tau
                light(f"{take} inside glow {k}", (ox + math.cos(a) * meta["R"] * 0.6, oy + math.sin(a) * meta["R"] * 0.6, yf + meta["H"] * 0.55),
                      5000 * (meta["R"] / 32) ** 1.5, (1, 0.8, 0.3))
    print(take, "faces", sum(len(o.data.polygons) for o in sc.objects if o.type == "MESH" and o.name.startswith(take + " cave")))

w = bpy.data.worlds.new("World"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.012, 0.016, 1)
sc.render.engine = "CYCLES"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dt in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = dt
            prefs.get_devices()
            if any(dv.type == dt for dv in prefs.devices):
                for dv in prefs.devices:
                    dv.use = dv.type == dt
                sc.cycles.device = "GPU"
                print("GPU", dt)
                break
        except TypeError:
            continue
except Exception as e:
    print("GPU setup failed", e)
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "Standard"
sc.camera = cams[0]

bpy.ops.wm.save_as_mainfile(filepath=OUT)
if RENDER:
    rdir = os.path.join(os.path.dirname(OUT), "renders")
    os.makedirs(rdir, exist_ok=True)
    for cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", cam.name)
    sc.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("done", OUT)
