# Pass 702: skin workshop variations (Chat E, construct surfaces, 2026-10-15). J rated 701 (18:00): KEEP BRD, BRJR,
# BRN, T9; DROP LANTERNS, RINGS, T3, T5; IMPROVE with no note on R2K1, T1, T2, T6, T7, X1, X3, X3D1, X5E, X5N ->
# three new labelled variations each (his standing rule). Every variation keeps the texture's own pattern and animated
# strip; it changes one thing, the same way for every texture, so they compare across the board:
#   a  deeper   - darker and more saturated (value x0.6, saturation x1.3, glow x0.7): J's "darker, smoother" taste
#   b  brighter - stronger glow in the texture's own hue (glow x1.6, saturation x1.3), never washed to white
#   c  finer    - the pattern twice as fine (2x tile density) and its animation half the speed (slower, calmer)
# Each variation is a copy of the texture's lane (A1 suit, 3x2 wall, dome, particle sphere) placed in its own row in
# front of the workshop, with the same 8 s close tour as 701: "Cam <code><a|b|c> close".
# Opens LanternLive\constructs\skin_workshop_close.blend, saves LanternLive\constructs\skin_variations.blend.
import math, os
import bpy
import numpy as np
from mathutils import Vector, Matrix

SRC = os.path.join(FOLDER, "constructs", "skin_workshop_close.blend")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.data.scenes["Skin Workshop"]
col = scene.collection
OUT = os.path.join(FOLDER, "constructs", "skin_variations.blend")
R = math.radians
SEG = 40
bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"

CODES = ["R2K1", "T1", "T2", "T6", "T7", "X1", "X3", "X3D1", "X5E", "X5N"]
VARS = {"a": ("deeper", dict(sat=1.3, val=0.6, glow=0.7)),
        "b": ("brighter", dict(sat=1.3, val=1.0, glow=1.6)),
        "c": ("finer", dict(sat=1.0, val=1.0, glow=1.0, uv=2.0, slow=2.0))}
ROW = {"a": -28.0, "b": -42.0, "c": -56.0}      # 701's red BRJ copy sits at -14


def bbox(names):
    pts = []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        for ob in [o] + [c for c in o.children_recursive]:
            if ob.type == "MESH":
                pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    if not pts:
        return None
    P = np.array([tuple(p) for p in pts])
    lo, hi = P.min(0), P.max(0)
    return (lo + hi) / 2, hi - lo


def look_rot(loc, target):
    return (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def key_arc(cam, f0, f1, centre, r, h, a0=-28.0, a1=28.0):
    steps = list(range(f0, f1 + 1, 4)) + ([f1] if (f1 - f0) % 4 else [])
    for f in steps:
        u = (f - f0) / max(1, f1 - f0)
        a = R(a0 + (a1 - a0) * u)
        loc = (centre[0] + r * math.sin(a), centre[1] - r * math.cos(a), centre[2] + h)
        cam.location = loc; cam.rotation_euler = look_rot(loc, centre)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)


def make_tour(code):
    c = bpy.data.objects.new(f"Cam {code} close", bpy.data.cameras.new(f"Cam {code} close")); col.objects.link(c)
    c.data.lens = 35; c.data.clip_start = 0.05
    parts = [("wall", [f"WS {code} wall"]), ("dome", [f"WS {code} dome"]), ("particles", [f"WS {code} particles"]),
             ("suit", [f"KL WS {code} {p}" for p in ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")])]
    for k, (what, names) in enumerate(parts):
        bb = bbox(names)
        if bb is None:
            continue
        centre, size = bb
        span = max(size[0], size[2])
        key_arc(c, 1 + k * SEG, (k + 1) * SEG, centre, 1.15 * span + (1.6 if what == "suit" else 0.9), 0.25 * span)


_cache = {}


def var_mat(m, v, p):
    if m is None or not m.use_nodes:
        return m
    key = (m.name, v)
    if key in _cache:
        return _cache[key]
    r = m.copy(); r.name = f"{m.name} {v}"
    N, Lk = r.node_tree.nodes, r.node_tree.links
    for node in list(N):
        if node.type == "BSDF_PRINCIPLED":
            es = node.inputs["Emission Strength"]
            if not es.links:
                es.default_value *= p["glow"]
            targets = [node.inputs["Base Color"], node.inputs["Emission Color"]]
        elif node.type == "EMISSION":
            st = node.inputs["Strength"]
            if not st.links:
                st.default_value *= p["glow"]
            targets = [node.inputs["Color"]]
        else:
            continue
        for sock in targets:
            if sock.links and (p["sat"] != 1.0 or p["val"] != 1.0):
                src = sock.links[0].from_socket
                hs = N.new("ShaderNodeHueSaturation")
                hs.inputs["Saturation"].default_value = p["sat"]; hs.inputs["Value"].default_value = p["val"]
                Lk.remove(sock.links[0]); Lk.new(src, hs.inputs["Color"]); Lk.new(hs.outputs["Color"], sock)
    if p.get("uv"):                                   # twice the tile density: scale the box UVs before they are used
        for uvn in [n for n in N if n.type == "UVMAP"]:
            outs = [lk.to_socket for lk in uvn.outputs["UV"].links]
            sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = p["uv"]
            for lk in list(uvn.outputs["UV"].links):
                Lk.remove(lk)
            Lk.new(uvn.outputs["UV"], sc.inputs[0])
            for to in outs:
                Lk.new(sc.outputs[0], to)
    if p.get("slow") and r.node_tree.animation_data:
        for fc in r.node_tree.animation_data.drivers:
            e = fc.driver.expression
            if e.startswith("frame/"):
                fc.driver.expression = f"frame/({e[6:]}*{p['slow']})"
    _cache[key] = r
    return r


def copy_lane(code, newcode, off, v, p):
    bpy.context.scene.frame_set(60)
    src = [o for o in bpy.data.objects if o.name.startswith(f"WS {code} ") or o.name.startswith(f"KL WS {code} ")]
    mw = {o: o.matrix_world.copy() for o in src}
    cp = {}
    for o in src:
        c = o.copy()
        if o.type == "MESH":
            c.data = o.data.copy()
        c.name = o.name.replace(f"WS {code} ", f"WS {newcode} ", 1)
        col.objects.link(c)
        cp[o] = c
    for o, c in cp.items():
        c.animation_data_clear()
        if o.parent in cp:
            c.parent = cp[o.parent]; c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        else:
            c.parent = None
        if c.type == "MESH":
            for i, m in enumerate(c.data.materials):
                c.data.materials[i] = var_mat(m, v, p)
        for mod in c.modifiers:
            if mod.type == "PARTICLE_SYSTEM":
                st = mod.particle_system.settings.copy(); mod.particle_system.settings = st
                if st.instance_object in cp:
                    st.instance_object = cp[st.instance_object]
    for o, c in cp.items():
        c.matrix_world = Matrix.Translation(off) @ mw[o]
    return len(cp)


made = []
for code in CODES:
    for v, (vname, p) in VARS.items():
        nc = code + v
        n = copy_lane(code, nc, Vector((0.0, ROW[v], 0.0)), v, p)
        make_tour(nc)
        made.append((nc, vname, n))
        print(nc, vname, n, "objects", flush=True)

scene.frame_start, scene.frame_end = 1, 160
scene.camera = bpy.data.objects.get("Cam R2K1a close")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("saved", OUT, len(made))
