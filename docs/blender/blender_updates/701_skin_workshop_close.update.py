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
from mathutils import Vector

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
for code in codes:
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
