# Pass 701: skin workshop close-ups, animated (Chat E, construct surfaces, 2026-10-15). J on the site's 593 cards:
# "these i need to see animated on the site and closer up for each thing".
# Same scene as pass 593 (every construct texture and barrier surface on a suit, a 3x2 wall, a dome and a particle
# sphere; the five particle walls; rings; lanterns). Nothing about the designs changes; this pass only adds cameras:
#   "Cam <code> close"   one animated tour per texture, 160 frames (8 s): 40 frames close on each thing in turn,
#                        each a slow arc so the animated texture and the light play across it:
#                        1-40 wall, 41-80 dome, 81-120 particles, 121-160 suit (after the suit has formed).
#   "Cam wall W<n> close" each particle wall, a slow 120-frame arc at 5 blocks (the original camera was 7 out).
# Opens LanternLive\constructs\skin_workshop.blend (or the review build of it), saves
# LanternLive\constructs\skin_workshop_close.blend.
import math, os
import bpy
import numpy as np
from mathutils import Vector, Matrix

SRC = None
for cand in (os.path.join(FOLDER, "constructs", "skin_workshop.blend"),
             os.path.join(FOLDER, "_review_build", "constructs", "skin_workshop.blend")):
    if os.path.exists(cand):
        SRC = cand; break
if SRC is None:                                           # rebuild it from pass 593's script
    _s = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ".", "593_skin_workshop.update.py")
    exec(compile(open(_s).read(), _s, "exec"), {"bpy": bpy, "np": np, "FOLDER": FOLDER, "__name__": "__ll__"})
    SRC = os.path.join(FOLDER, "constructs", "skin_workshop.blend")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.data.scenes["Skin Workshop"]
col = scene.collection
OUT = os.path.join(FOLDER, "constructs", "skin_workshop_close.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
R = math.radians
SEG = 40
bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"     # steady arcs, hard cuts between things


def bbox(names):
    pts = []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        objs = [o] + [c for c in o.children_recursive if c.type == "MESH"]
        for ob in objs:
            if ob.type == "MESH":
                pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    if not pts:
        return None
    P = np.array([tuple(p) for p in pts])
    lo, hi = P.min(0), P.max(0)
    return (lo + hi) / 2, hi - lo


def look_rot(loc, target):
    return (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def key_arc(cam, f0, f1, centre, r, h, a0=-28.0, a1=28.0, lift=0.0):
    """Key a slow arc in front of `centre` (the -y side), azimuth a0 -> a1 degrees, every 4 frames (linear)."""
    steps = list(range(f0, f1 + 1, 4)) + ([f1] if (f1 - f0) % 4 else [])
    for f in steps:
        u = (f - f0) / max(1, f1 - f0)
        a = R(a0 + (a1 - a0) * u)
        loc = (centre[0] + r * math.sin(a), centre[1] - r * math.cos(a), centre[2] + h + lift * u)
        cam.location = loc; cam.rotation_euler = look_rot(loc, centre)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)


def new_cam(name, lens=35):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); col.objects.link(c)
    c.data.lens = lens; c.data.clip_start = 0.05
    return c


codes = sorted(n[4:-5] for n in (o.name for o in bpy.data.objects) if n.startswith("Cam ") and n.endswith(" suit"))
made = []


def make_tour(code):
    parts = [("wall", [f"WS {code} wall"], 1.0), ("dome", [f"WS {code} dome"], 1.0),
             ("particles", [f"WS {code} particles"], 1.0),
             ("suit", [f"KL WS {code} {p}" for p in ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")], 1.0)]
    c = new_cam(f"Cam {code} close")
    for k, (what, names, _) in enumerate(parts):
        bb = bbox(names)
        if bb is None:
            continue
        centre, size = bb
        span = max(size[0], size[2])
        r = 1.15 * span + (1.6 if what == "suit" else 0.9)   # fills about two thirds of the frame (whole suit, head to boots)
        h = 0.25 * span
        f0, f1 = 1 + k * SEG, (k + 1) * SEG
        key_arc(c, f0, f1, centre, r, h)
    made.append(code)


for code in codes:
    make_tour(code)


# ------------------------------------------------------------------ J (site, 701 BRJ): "Test with red"
# A copy of the BR1 jade lane (suit, wall, dome, particles) 14 blocks in front of it, every material hue-shifted from jade
# to the Red corps' crimson (hue 0.40 -> 0.0, a little more saturation); its own tour "Cam BRJR close".
RED_EDGE = (1.0, 0.12, 0.08, 1)
_red_cache = {}


def red_mat(m):
    if m is None or not m.use_nodes:
        return m
    if m.name in _red_cache:
        return _red_cache[m.name]
    r = m.copy(); r.name = m.name + " RED"
    N, Lk = r.node_tree.nodes, r.node_tree.links
    for node in list(N):
        targets = []
        if node.type == "BSDF_PRINCIPLED":
            targets = [node.inputs["Base Color"], node.inputs["Emission Color"]]
        elif node.type == "EMISSION":
            targets = [node.inputs["Color"]]
        for sock in targets:
            if sock.links:
                src = sock.links[0].from_socket
                hs = N.new("ShaderNodeHueSaturation")
                hs.inputs["Hue"].default_value = 0.135; hs.inputs["Saturation"].default_value = 1.2
                Lk.remove(sock.links[0]); Lk.new(src, hs.inputs["Color"]); Lk.new(hs.outputs["Color"], sock)
            else:
                c = sock.default_value
                if c[1] > c[0] + 0.1:                               # a green default (the forming edge, emblems)
                    lum = max(c[0], c[1], c[2])
                    sock.default_value = (lum, 0.12 * lum, 0.08 * lum, 1)
    _red_cache[m.name] = r
    return r


bpy.context.scene.frame_set(60)
src = [o for o in bpy.data.objects if o.name.startswith("WS BRJ ") or o.name.startswith("KL WS BRJ ")]
mw = {o: o.matrix_world.copy() for o in src}
cp = {}
for o in src:
    c = o.copy()
    if o.data is not None and o.type == "MESH":
        c.data = o.data.copy()
    c.name = o.name.replace("WS BRJ ", "WS BRJR ", 1)
    col.objects.link(c)
    cp[o] = c
OFF = Vector((0.0, -14.0, 0.0))        # in front of the row: behind every other tour camera, so no other clip sees it
for o, c in cp.items():
    c.animation_data_clear()
    if o.parent in cp:
        c.parent = cp[o.parent]; c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
    else:
        c.parent = None
        m_ = mw[o].copy(); m_.translation = m_.translation + OFF
        c.matrix_world = m_
    if c.type == "MESH":
        for i, m in enumerate(c.data.materials):
            c.data.materials[i] = red_mat(m)
    for mod in c.modifiers:
        if mod.type == "PARTICLE_SYSTEM":
            st = mod.particle_system.settings.copy(); mod.particle_system.settings = st
            if st.instance_object in cp:
                st.instance_object = cp[st.instance_object]
for o, c in cp.items():                                       # children keep their pose: re-apply after parenting
    if o.parent in cp:
        c.matrix_world = Matrix.Translation(OFF) @ mw[o]
make_tour("BRJR")

walls = []
for i in range(1, 6):
    bb = bbox([f"Wall option W{i}"])
    if bb is None:
        continue
    centre, size = bb
    c = new_cam(f"Cam wall W{i} close", 32)
    key_arc(c, 1, 120, (centre[0], centre[1], 1.5), 5.0, 0.3, -30.0, 30.0)
    walls.append(f"W{i}")

scene.frame_start, scene.frame_end = 1, 160
scene.camera = bpy.data.objects.get(f"Cam {made[0]} close") if made else scene.camera
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("saved", OUT, "tours", len(made), made, "walls", walls)
