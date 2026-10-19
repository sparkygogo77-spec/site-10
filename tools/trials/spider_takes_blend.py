"""Spider takes and funnel-trap takes for J to rate (2026-10-19).

blender.exe -b --python spider_takes_blend.py -- <out.blend> [--no-render]

Row 1 (y = 0): real spiders R1 hunter, R2 brute, R3 funnel-web, 36-block leg span, web-rock spikes on every leg.
Row 2 (y = -120): yellow construct spiders C1 solid light, C2 lattice, C3 shards, 20-block leg span.
Row 3 (y = -240): funnel traps T1 silk funnel, T2 sheet webs, T3 earth funnel, cut in half, mid-crumble: the outer
ring of webbed dirt is gone and chunks are falling toward the net. A C1 construct spider and the player inside each.
Every take has a 1.8-block player for scale and its own camera ("NN code name").
"""
import math, os, sys
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_blender_kit as K

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
RENDER = "--no-render" not in argv
bpy.ops.wm.read_factory_settings(use_empty=True)
K.sc = bpy.context.scene
sc = K.sc
CM = K.cave_materials(textured=True)
cams = []


def ground(name, loc, size, m):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)


# Row 1 and 2: spider lineups on rock floors
ROUND2 = "--round2" in argv     # J's picks: R2 brute; C3 dropped, C1/C2 reworked as C1a, C1b, C2a; no trap room
if ROUND2:
    ROWS = ((("R2",), 36, 60, 0.0), (("C1a", "C1b", "C2a"), 20, 40, -120.0))
else:
    ROWS = ((("R1", "R2", "R3"), 36, 60, 0.0), (("C1", "C2", "C3"), 20, 40, -120.0))
NAMES = {"R1": "hunter", "R2": "brute", "R3": "funnel-web", "C1": "solid light", "C2": "lattice", "C3": "shards",
         "C1a": "scale shell", "C1b": "dread armour", "C2a": "lightning lattice"}
for row, (takes, span, gap, y0) in enumerate(ROWS):
    ground(f"floor row {row + 1}", (gap, y0, 0), gap * 3.5, CM[0])
    for i, t in enumerate(takes):
        x = i * gap
        nm = NAMES[t]
        if t in ("C1a", "C1b", "C2a"):
            K.construct_spider(t, f"{t} {nm}", (x, y0, 0), span, yaw=math.radians(200))
        else:
            K.spider(t, f"{t} {nm}", (x, y0, 0), span, yaw=math.radians(200))
        K.player(f"{t} player", (x + span * 0.42, y0 - span * 0.25, 0))
        d = span * 1.15
        if ROUND2:   # three-quarter view from above so the back and abdomen show
            cams.append(K.camera(f"{len(cams) + 1:02d} {t} {nm}", (x + d * 0.85, y0 - d * 0.7, span * 0.75), (x, y0 - span * 0.05, span * 0.08), 30))
        else:
            cams.append(K.camera(f"{len(cams) + 1:02d} {t} {nm}", (x + d * 0.55, y0 - d * 0.95, span * 0.38), (x, y0, span * 0.1), 30))
        K.light(f"{t} key", (x + d * 0.6, y0 - d * 0.8, span * 0.9), 9000 * (span / 20) ** 2, (1, 0.95, 0.9), "AREA", span * 0.6)
        K.light(f"{t} rim", (x - d * 0.5, y0 + d * 0.7, span * 0.6), 5000 * (span / 20) ** 2, (0.7, 0.8, 1.0), "AREA", span * 0.5)

# Row 3: funnel trap takes
R, H, DIRT, N = 12, 14, 3, 44
for i, (t, nm) in enumerate(() if ROUND2 else (("T1", "silk funnel"), ("T2", "sheet webs"), ("T3", "earth funnel"))):
    X = Z = N; Y = 44
    cx = cz = N // 2
    fy = 26                                     # top of the dirt floor
    xs = (np.arange(X) - cx)[:, None, None]; zs = (np.arange(Z) - cz)[None, None, :]; ys = np.arange(Y)[None, :, None]
    rr = np.sqrt(xs ** 2 + zs ** 2)
    tt = np.clip((ys - fy) / H, 0, 1)
    lean = {"T1": 0.45, "T2": 0.15, "T3": 0.6}[t]
    room = (ys > fy) & (ys <= fy + H) & (rr <= R * (1 - lean * tt ** 2))
    drop = (ys <= fy - DIRT) & (ys > 2) & (rr <= 10 + 0.08 * (fy - ys))
    air = room | drop
    rng = np.random.default_rng(i + 5)
    dirt = (ys > fy - DIRT) & (ys <= fy) & (rr <= R + 0.5)
    crumbled = dirt & (rr > R - 3.5 + rng.random((X, 1, Z)) * 1.5)        # outer ring already gone
    holes = dirt & (rng.random((X, Y, Z)) < 0.05) & (rr > 5)                # cracks opening further in
    dirt = dirt & ~crumbled & ~holes
    air |= crumbled | holes
    solid = ~air
    solid[:, :, cz + 1:] = False                                            # cut in half to see in
    mask_wall = {"T1": 6, "T2": 0, "T3": 1}[t]

    def face_mat(idx, nidx, ax, d, dirt=dirt, room=room, drop=drop, mask_wall=mask_wall):
        own_d, _ = K.safe_get(dirt, idx, False)
        in_room, _ = K.safe_get(room, nidx, False)
        in_drop, _ = K.safe_get(drop, nidx, False)
        real_air, ok = K.safe_get(air, nidx, False)
        m = np.where(real_air & ok, np.where(in_room, mask_wall, np.where(in_drop, 6, 0)), 2)
        return np.where(own_d, 7, m)
    ox = i * 70.0; oy = -240.0
    o = K.voxel_mesh(f"{t} {nm}", solid, face_mat, CM)
    o.location = (ox - cx, oy + cz, 0)

    def B(x, y, z):
        return (ox - cx + x, oy + cz - z, y)
    # falling dirt chunks between the floor and the net
    for j in range(14):
        a = rng.uniform(math.pi, math.tau); r_ = rng.uniform(R - 3, R)
        K.box(f"{t} falling dirt {j}", B(cx + math.cos(a) * r_, fy - rng.uniform(3, 10), cz + math.sin(a) * r_ * 0.5),
              (1, 1, 1), CM[7], None).rotation_euler = tuple(rng.uniform(0, 1, 3))
    # the net
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=11, fill_type="NGON", location=B(cx, fy - 12, cz))
    net = bpy.context.object; net.name = f"{t} net"; net.data.materials.append(CM[6])
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=10); bpy.ops.object.mode_set(mode="OBJECT")
    for v in net.data.vertices:
        v.co.z -= 2.5 * (1 - min(1, math.hypot(v.co.x, v.co.y) / 11) ** 2)
    w = net.modifiers.new("strands", "WIREFRAME"); w.thickness = 0.12
    if t == "T2":   # sheet webs strung across the room, plus tufts in the corners
        for j in range(5):
            bpy.ops.mesh.primitive_plane_add(size=1, location=B(cx + rng.uniform(-5, 5), fy + rng.uniform(5, 12), cz - rng.uniform(2, 8)))
            p = bpy.context.object; p.name = f"{t} web sheet {j}"; p.scale = (rng.uniform(8, 14), rng.uniform(4, 8), 1)
            p.rotation_euler = tuple(rng.uniform(-0.8, 0.8, 3)); p.data.materials.append(CM[6])
            bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=6); bpy.ops.object.mode_set(mode="OBJECT")
            ww = p.modifiers.new("strands", "WIREFRAME"); ww.thickness = 0.06
    if t == "T3":   # roots through the earth walls, silk patches
        for j in range(10):
            a = rng.uniform(math.pi, math.tau); y_ = fy + rng.uniform(2, H - 2)
            p0 = Vector(B(cx + math.cos(a) * (R + 1), y_, cz + math.sin(a) * (R + 1)))
            p1 = Vector(B(cx + math.cos(a) * (R - 4), y_ - rng.uniform(2, 6), cz + math.sin(a) * (R - 4)))
            K.box(f"{t} root {j}", tuple((p0 + p1) / 2), (0.5, (p1 - p0).length, 0.5), CM[1], None, along=p1 - p0)
    K.spider("C1", f"{t} construct spider", B(cx + 2, fy + 1, cz - 4), 20, yaw=math.radians(30))
    K.player(f"{t} player", B(cx - 6, fy + 1, cz - 1))
    cams.append(K.camera(f"{len(cams) + 1:02d} {t} {nm}", B(cx + 10, fy + 14, cz + 52), B(cx, fy + 2, cz), 28))
    K.light(f"{t} key", B(cx, fy + 10, cz + 40), 12000, (1, 0.95, 0.9), "AREA", 30)
    K.light(f"{t} trap glow", B(cx, fy + 8, cz - 4), 600, (1, 0.85, 0.5))
    K.light(f"{t} drop glow", B(cx, fy - 18, cz - 2), 2500, (0.7, 0.8, 1.0))

w = bpy.data.worlds.new("World"); sc.world = w
try:
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.022, 0.03, 1)
except Exception as e:
    print("world", e)
sc.render.engine = "CYCLES"; sc.cycles.samples = 64; sc.cycles.use_denoising = True; sc.cycles.use_preview_denoising = True
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
try:
    sc.render.film_transparent = False
except Exception:
    pass
sc.camera = cams[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
if RENDER:
    rdir = os.path.join(os.path.dirname(OUT), "renders_takes2" if ROUND2 else "renders_takes")
    os.makedirs(rdir, exist_ok=True)
    for cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".png")
        bpy.ops.render.render(write_still=True)
    sc.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("done", OUT, len(cams), "cameras")
