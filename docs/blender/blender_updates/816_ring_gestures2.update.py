# Pass 816: ring-hand gestures, round 2 (Chat C, 2026-10-15, range 800-899).
# J on 814: "the X4 ring the camera names need another description or in blender I need a better description of what
# the model is for, as the ring goes on what in the x4 description, these animations were also subpar they dont look
# well". Screenshots: in first person the ring face filled the view and glowed white; the oath column and the burst
# ring swallowed the camera.
# What changed:
#  - Every take sits in its own collection named for what it is for, has a description board behind it (what it is,
#    when the game would play it, the beats by tick), and its cameras say what they show.
#  - Hands land exactly where they should: a small solver places the hand (or the ring) on the chest, the brow or the
#    other hand each key, so the fist meets the chest, the ring touches the forehead, the left hand meets the right.
#  - Motion has anticipation, a snap, overshoot and a settle; the head and body follow a tick or two behind the arm;
#    weight shifts through the legs.
#  - First person is built for the camera: both arms, hands placed on screen (inside the 26 mm frame), the ring face
#    turned to the eye, glow at most 2.4 so it stays green, effects kept clear of the lens.
#  - X4 is now plainly "put the ring on": the ring is a separate object, held in the left hand, slid onto the right
#    hand, clicks, then the power-up.
#   X1 Cast (point)            X2 Oath (fist raised)        X3 Focus (ring to the brow)       X4 Put the ring on
# Cameras "Cam X<n> <name> - third person" and "... - first person", "Cam all". Writes LanternLive\combat\
# gestures2_poses.json and builds LanternLive\combat\ring_gestures2.blend.
SCENE_NAME = "Ring Gestures 2"
OUT_REL = "combat/ring_gestures2.blend"
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector

R = math.radians
OUT = os.path.join(FOLDER, *OUT_REL.split("/"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get(SCENE_NAME)
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(SCENE_NAME)
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
_prefs = bpy.context.preferences.edit
_prefs.keyframe_new_interpolation_type = "BEZIER"
P = 1 / 16                                     # one Minecraft pixel in metres
CORPS = {"green": (0.12, 1.0, 0.3), "red": (1.0, 0.05, 0.08), "yellow": (1.0, 0.8, 0.04), "violet": (0.6, 0.1, 1.0),
         "blue": (0.08, 0.35, 1.0), "orange": (1.0, 0.4, 0.03)}       # saturated, never white
LIB = {"red": "crimson"}                      # texture library folder names


def link(o):
    col.objects.link(o)
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    o = link(bpy.data.objects.new(name, None)); o.location = loc; o.rotation_mode = "XYZ"
    if parent is not None:
        o.parent = parent
    return o


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_start = 0.02
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


def mat(name, rgb, emit=0.0, alpha=1.0, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


def anim_emit(m, keys):
    """Keyframe a material's emission strength: keys = [(frame, strength)]."""
    s = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, v in keys:
        s.default_value = v; s.keyframe_insert("default_value", frame=f)


def anim_alpha(m, keys):
    s = m.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    for f, v in keys:
        s.default_value = min(0.99, v); s.keyframe_insert("default_value", frame=f)


def cmats(tag, corps="green"):
    """Construct materials in a corps colour: hard-light glass (at most 99% opaque), glow, rim, pixel."""
    c = np.array(CORPS[corps])
    return {"glass": mat(f"{tag} hard-light glass", tuple(c * 0.5), emit=0.9, alpha=0.62, rough=0.15),
            "glow": mat(f"{tag} glow", tuple(c), emit=3.2), "rim": mat(f"{tag} rim", tuple(c), emit=3.8),
            "grip": mat(f"{tag} grip", tuple(c * 0.18), emit=0.6, rough=0.3), "pix": mat(f"{tag} pixel", tuple(c), emit=5.0),
            "c": tuple(c)}


def box(name, a, b, m, parent=None, uvt=0.5):
    """Axis box from corner a to b; UVs projected per face (one texture tile per `uvt` metres)."""
    a = np.array(a, float); b = np.array(b, float)
    v = [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update(); me.materials.append(m)
    uv = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        n = np.abs(np.array(poly.normal)); ax = int(np.argmax(n)); o_ = [i for i in range(3) if i != ax]
        for li in poly.loop_indices:
            co = np.array(me.vertices[me.loops[li].vertex_index].co)
            uv.data[li].uv = (co[o_[0]] / uvt, co[o_[1]] / uvt)
    o = link(bpy.data.objects.new(name, me))
    if parent is not None:
        o.parent = parent
    return o


def cyl(name, r, h, m, n=16, parent=None, loc=(0, 0, 0), axis="Z", r2=None):
    """A cylinder (or cone with r2) along an axis, base at loc."""
    r2 = r if r2 is None else r2
    vs = []
    for k in range(n):
        a = 2 * math.pi * k / n
        vs.append((r * math.cos(a), r * math.sin(a), 0)); vs.append((r2 * math.cos(a), r2 * math.sin(a), h))
    fs = [(2 * k, 2 * ((k + 1) % n), 2 * ((k + 1) % n) + 1, 2 * k + 1) for k in range(n)]
    fs += [tuple(2 * k for k in range(n))[::-1], tuple(2 * k + 1 for k in range(n))]
    if axis != "Z":
        rot = {"X": Matrix.Rotation(R(90), 3, "Y"), "Y": Matrix.Rotation(R(-90), 3, "X")}[axis]
        vs = [tuple(rot @ Vector(v)) for v in vs]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    for p_ in me.polygons:
        p_.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    if parent is not None:
        o.parent = parent
    return o


def ball(name, r, m, loc=(0, 0, 0), parent=None, seg=16):
    vs, fs = [], []
    for i in range(seg // 2 + 1):
        th = math.pi * i / (seg // 2)
        for j in range(seg):
            ph = 2 * math.pi * j / seg
            vs.append((r * math.sin(th) * math.cos(ph), r * math.sin(th) * math.sin(ph), r * math.cos(th)))
    for i in range(seg // 2):
        for j in range(seg):
            a = i * seg + j; b = i * seg + (j + 1) % seg
            fs.append((a, b, b + seg, a + seg))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    for p_ in me.polygons:
        p_.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    if parent is not None:
        o.parent = parent
    return o


def torus(name, R_, r, m, loc=(0, 0, 0), parent=None, n=32, k=8, axis="Z"):
    vs, fs = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        for j in range(k):
            b = 2 * math.pi * j / k
            v = Vector(((R_ + r * math.cos(b)) * math.cos(a), (R_ + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            if axis == "Y":
                v = Matrix.Rotation(R(90), 3, "X") @ v
            elif axis == "X":
                v = Matrix.Rotation(R(90), 3, "Y") @ v
            vs.append(tuple(v))
    for i in range(n):
        for j in range(k):
            fs.append((i * k + j, ((i + 1) % n) * k + j, ((i + 1) % n) * k + (j + 1) % k, i * k + (j + 1) % k))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    for p_ in me.polygons:
        p_.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    if parent is not None:
        o.parent = parent
    return o


def key(o, f, loc=None, rot=None, sc=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if sc is not None:
        o.scale = (sc,) * 3 if np.isscalar(sc) else sc; o.keyframe_insert("scale", frame=f)


def show(o, f_on, f_off=None):
    """Hidden until f_on, shown until f_off (render and viewport)."""
    for f, h in ((1, True), (f_on, False)) + (((f_off, True),) if f_off else ()):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = h; o.keyframe_insert("hide_viewport", frame=f)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def label(text, loc, m, size=0.22, rot=(R(90), 0, 0)):
    cu = bpy.data.curves.new("label " + text[:20], "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = link(bpy.data.objects.new("label " + text[:20], cu)); o.location = loc; o.rotation_euler = rot
    o.data.materials.append(m)
    return o


_pixmesh = {}


def pixel_mesh(m, s=0.03):
    if m.name not in _pixmesh:
        pm = bpy.data.meshes.new("px " + m.name)
        pm.from_pydata([(x, y, z) for x in (-s, s) for y in (-s, s) for z in (-s, s)], [],
                       [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
        pm.materials.append(m); _pixmesh[m.name] = pm
    return _pixmesh[m.name]


def form_in(parts, f0, f1, src, pixm, rng, tag, order_axis=2, stream=0.5):
    """Construct forming, pixel by pixel: each part grows in from nothing in order along an axis (world position),
    and some get a pixel that flies from `src` (world point, e.g. the ring) to them first."""
    bpy.context.view_layer.update()
    pos = [(o, o.matrix_world @ (Vector(np.mean([v.co for v in o.data.vertices], axis=0)) if o.type == "MESH" else Vector())) for o in parts]
    vals = [p[order_axis] for _, p in pos]; lo, hi = min(vals), max(vals) + 1e-6
    pm = pixel_mesh(pixm)
    for o, p in pos:
        fa = int(round(f0 + 2 + (p[order_axis] - lo) / (hi - lo) * (f1 - f0 - 4))) + int(rng.integers(0, 2))
        sc0 = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, fa - 1, sc=0.0001); key(o, fa + 1, sc=sc0)
        if src is not None and rng.random() < stream:
            px = link(bpy.data.objects.new(f"{tag} pixel", pm))
            s0 = Vector(src) + Vector(rng.uniform(-0.03, 0.03, 3)); fs = max(1, fa - 5)
            key(px, 1, loc=s0, sc=0.0001); key(px, fs, loc=s0, sc=0.0001); key(px, fs + 1, loc=s0, sc=1.0)
            key(px, fs + 3, loc=(s0 + p) / 2 + Vector((0, 0, 0.15)), sc=1.0); key(px, fa, loc=p, sc=0.7)
            key(px, fa + 1, loc=p, sc=0.0001)


def shatter(parts, f, pixm, rng, tag, n=3, speed=0.12, life=14):
    """Construct breaking: each part vanishes at f and throws n pixels outward that fall and shrink."""
    bpy.context.view_layer.update()
    pm = pixel_mesh(pixm)
    for o in parts:
        sc0 = tuple(o.scale)
        key(o, f - 1, sc=sc0); key(o, f, sc=0.0001)
        c = o.matrix_world @ (Vector(np.mean([v.co for v in o.data.vertices], axis=0)) if o.type == "MESH" else Vector())
        for _ in range(n):
            px = link(bpy.data.objects.new(f"{tag} shard", pm))
            v = Vector(rng.normal(0, 1, 3)); v.z = abs(v.z) + 0.5; v = v.normalized() * speed * rng.uniform(0.6, 1.4)
            key(px, 1, loc=c, sc=0.0001); key(px, f - 1, loc=c, sc=0.0001); key(px, f, loc=c, sc=1.0)
            p_ = Vector(c)
            for k in range(1, life + 1, 3):
                p_ = c + v * k + Vector((0, 0, -0.006 * k * k))
                key(px, f + k, loc=p_, sc=max(0.0001, 1 - k / life))


# ------------------------------------------------------------------ a blocky player (Minecraft proportions, knees, elbows)
def make_player(tag, loc, mats, face=0.0):
    """Faces +Y. Pivots: root, body, head (neck), arm_r/arm_l (shoulder), fore_r/fore_l (elbow), leg_r/leg_l (hip),
    shin_r/shin_l (knee). The player's right is +X. Ring on the right hand. Returns dict of pivots and the ring point."""
    sk, sh, pa, bo = mats["skin"], mats["shirt"], mats["pants"], mats["boot"]
    root = empty(f"{tag} root", loc); root.rotation_euler = (0, 0, face)
    body = empty(f"{tag} body", (0, 0, 12 * P), root)
    box(f"{tag} torso", (-4 * P, -2 * P, 0), (4 * P, 2 * P, 12 * P), mats.get("torso", sh), body)
    head = empty(f"{tag} neck", (0, 0, 12 * P), body)
    box(f"{tag} head", (-4 * P, -4 * P, 0), (4 * P, 4 * P, 8 * P), mats.get("head", sk), head)
    box(f"{tag} eye r", (1 * P, 4 * P, 3 * P), (3 * P, 4.15 * P, 4 * P), mats["eye"], head)
    box(f"{tag} eye l", (-3 * P, 4 * P, 3 * P), (-1 * P, 4.15 * P, 4 * P), mats["eye"], head)
    rig = {"root": root, "body": body, "head": head}
    for side, sx in (("r", 1), ("l", -1)):
        arm = empty(f"{tag} shoulder {side}", (sx * 6 * P, 0, 10 * P), body)
        box(f"{tag} upper arm {side}", (-2 * P, -2 * P, -6 * P), (2 * P, 2 * P, 2 * P), mats.get("arm", sh), arm)
        fore = empty(f"{tag} elbow {side}", (0, 0, -6 * P), arm)
        box(f"{tag} forearm {side}", (-2 * P, -2 * P, -6 * P), (2 * P, 2 * P, 0), mats.get("fore", sk), fore)
        leg = empty(f"{tag} hip {side}", (sx * 2 * P, 0, 0), body)
        box(f"{tag} thigh {side}", (-2 * P, -2 * P, -6 * P), (2 * P, 2 * P, 0), mats.get("leg", pa), leg)
        shin = empty(f"{tag} knee {side}", (0, 0, -6 * P), leg)
        box(f"{tag} shin {side}", (-2 * P, -2 * P, -6 * P), (2 * P, 2 * P, 0), mats.get("shin", bo), shin)
        rig["arm_" + side] = arm; rig["fore_" + side] = fore; rig["leg_" + side] = leg; rig["shin_" + side] = shin
    # the ring, right hand: a gold band and a green face on the back of the hand
    fr = rig["fore_r"]
    box(f"{tag} ring band", (-2.2 * P, -2.2 * P, -4.6 * P), (2.2 * P, 2.2 * P, -3.6 * P), mats["gold"], fr)
    box(f"{tag} ring face", (2.2 * P, -1.0 * P, -5.0 * P), (2.9 * P, 1.0 * P, -3.2 * P), mats["ring"], fr)
    rig["ring_pt"] = empty(f"{tag} ring point", (2.6 * P, 0, -4.1 * P), fr)
    rig["hand_pt"] = empty(f"{tag} hand point", (0, 0, -6 * P), fr)
    return rig


def pose(rig, f, **kw):
    """pose(rig, frame, arm_r=(x, y, z) degrees, ..., root_loc=(x, y, z)); neck pitch is capped at 57 degrees (J)."""
    for k, v in kw.items():
        if k == "root_loc":
            key(rig["root"], f, loc=v); continue
        if k == "head":
            v = (max(-57, min(57, v[0])), v[1], v[2])
        key(rig[k], f, rot=tuple(R(a) for a in v))


def player_mats(tag, shirt=(0.05, 0.3, 0.14), pants=(0.03, 0.05, 0.08)):
    return {"skin": mat(f"{tag} skin", (0.62, 0.42, 0.3)), "shirt": mat(f"{tag} shirt", shirt),
            "pants": mat(f"{tag} pants", pants), "boot": mat(f"{tag} boots", (0.06, 0.06, 0.07)),
            "eye": mat(f"{tag} eyes", (0.05, 0.6, 0.2), emit=1.5), "gold": mat(f"{tag} ring gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0),
            "ring": mat(f"{tag} ring face", (0.12, 1.0, 0.3), emit=5.0)}


def strip_image(corps, look):
    p = os.path.join(TEXLIB, LIB.get(corps, corps), look, f"construct_{look}_{LIB.get(corps, corps)}.png")
    im = bpy.data.images.get(os.path.basename(p))
    if im is None:
        im = bpy.data.images.load(p)
        try:
            im.pack()
        except Exception:
            pass
    return im


def strip_mat(name, im, ft=4, emit=1.6, alpha=None, base_mul=1.0):
    """Animated construct strip: UV fract, frame k = floor(frame/ft) mod n, v' = (fract(v)+n-1-k)/n, two samples
    crossfaded (the game's interpolate)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.3
    n = max(1, im.size[1] // max(1, im.size[0]))
    uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "uv"
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uvn.outputs["UV"], sep.inputs[0])
    fu = N.new("ShaderNodeMath"); fu.operation = "FRACT"; L.new(sep.outputs[0], fu.inputs[0])
    fv = N.new("ShaderNodeMath"); fv.operation = "FRACT"; L.new(sep.outputs[1], fv.inputs[0])
    tick = N.new("ShaderNodeValue"); fc = tick.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"; fc.driver.expression = f"frame/{ft}"
    fl = N.new("ShaderNodeMath"); fl.operation = "FLOOR"; L.new(tick.outputs[0], fl.inputs[0])
    wv = N.new("ShaderNodeMath"); wv.operation = "SUBTRACT"; L.new(tick.outputs[0], wv.inputs[0]); L.new(fl.outputs[0], wv.inputs[1])
    outs = []
    for step in (0, 1):
        tex = N.new("ShaderNodeTexImage"); tex.image = im; tex.interpolation = "Closest"
        k = N.new("ShaderNodeMath"); k.operation = "ADD"; k.inputs[1].default_value = step; L.new(fl.outputs[0], k.inputs[0])
        km = N.new("ShaderNodeMath"); km.operation = "FLOORED_MODULO"; km.inputs[1].default_value = n; L.new(k.outputs[0], km.inputs[0])
        a_ = N.new("ShaderNodeMath"); a_.operation = "SUBTRACT"; a_.inputs[0].default_value = n - 1; L.new(km.outputs[0], a_.inputs[1])
        b_ = N.new("ShaderNodeMath"); b_.operation = "ADD"; L.new(fv.outputs[0], b_.inputs[0]); L.new(a_.outputs[0], b_.inputs[1])
        c_ = N.new("ShaderNodeMath"); c_.operation = "DIVIDE"; c_.inputs[1].default_value = n; L.new(b_.outputs[0], c_.inputs[0])
        cmb = N.new("ShaderNodeCombineXYZ"); L.new(fu.outputs[0], cmb.inputs[0]); L.new(c_.outputs[0], cmb.inputs[1])
        L.new(cmb.outputs[0], tex.inputs["Vector"]); outs.append(tex)
    mc = N.new("ShaderNodeMix"); mc.data_type = "RGBA"; L.new(wv.outputs[0], mc.inputs["Factor"])
    L.new(outs[0].outputs["Color"], mc.inputs[6]); L.new(outs[1].outputs["Color"], mc.inputs[7])
    L.new(mc.outputs[2], p.inputs["Base Color"]); L.new(mc.outputs[2], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = emit
    if alpha is not None:
        ma = N.new("ShaderNodeMix"); ma.data_type = "FLOAT"; L.new(wv.outputs[0], ma.inputs["Factor"])
        L.new(outs[0].outputs["Alpha"], ma.inputs[2]); L.new(outs[1].outputs["Alpha"], ma.inputs[3])
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = min(0.99, alpha)
        L.new(ma.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], p.inputs["Alpha"])
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


TEXLIB = os.path.join(FOLDER, "texture_library")
if not os.path.isdir(TEXLIB):
    _here = os.path.dirname(os.path.abspath(bpy.data.filepath)) if bpy.data.filepath else ""
    for cand in (os.path.join(os.getcwd(), "docs", "texture_library"), os.path.join(_here, "texture_library")):
        if os.path.isdir(cand):
            TEXLIB = cand
            break


def fp_arm(tag, eye, mats):
    """First-person right arm (as in pass 803): shoulder at eye + (0.36, 0.12, -0.42), a 4x12x4 px arm, ring on.
    Returns (shoulder pivot, grip pivot, ring point empty). Rotation (pitch, 0, yaw) in degrees, pitch 90 = ahead."""
    sh = empty(f"{tag} fp shoulder", tuple(Vector(eye) + Vector((0.36, 0.12, -0.42))))
    px = P * 1.05
    box(f"{tag} fp sleeve", (-2 * px, -2 * px, -8 * px), (2 * px, 2 * px, 0), mats["shirt"], sh)
    box(f"{tag} fp hand", (-2 * px, -2 * px, -12 * px), (2 * px, 2 * px, -8 * px), mats["skin"], sh)
    box(f"{tag} fp ring band", (-2.2 * px, -2.2 * px, -10.6 * px), (2.2 * px, 2.2 * px, -9.6 * px), mats["gold"], sh)
    box(f"{tag} fp ring face", (-1.0 * px, 2.2 * px, -11.0 * px), (1.0 * px, 2.9 * px, -9.2 * px), mats["ring"], sh)
    grip = empty(f"{tag} fp grip", (0, 0, -11 * px), sh)
    rp = empty(f"{tag} fp ring point", (0, 2.6 * px, -10.1 * px), sh)
    return sh, grip, rp


def fp_pose(sh, f, pitch, yaw=14, roll=22, base=None, reach=0.0):
    e_ = Euler((R(pitch), 0, R(yaw)), "XYZ"); e_.rotate_axis("Z", R(roll))
    sh.rotation_euler = e_; sh.keyframe_insert("rotation_euler", frame=f)
    if base is not None:
        key(sh, f, loc=tuple(Vector(base) + Vector((0, reach, 0))))


FRAME_END = 64
BAY = 5.0
ROOTCOL = col
FLOOR = mat("RG2 floor", (0.2, 0.22, 0.24), rough=0.9)
BOARD = mat("RG2 board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("RG2 text", (0.75, 1.0, 0.8), emit=1.2)
TXTH = mat("RG2 heading", (0.2, 1.0, 0.4), emit=2.2)
rng = np.random.default_rng(816)
CM = cmats("RG2", "green")
XH = mat("RG2 crosshair", (0.85, 0.85, 0.85), emit=1.0)
SOFT = mat("RG2 soft glow", (0.1, 0.9, 0.3), emit=1.6, alpha=0.35, rough=0.2)
RINGC = (0.02, 0.85, 0.15)                         # saturated: viewport and render both stay green


# ------------------------------------------------------------------ forward kinematics of make_player (root space)
def E(v):
    return Euler(tuple(R(a) for a in v), "XYZ").to_matrix()


def fk(pose_, side="r"):
    """Return (hand, ring point, elbow) in root space (player faces +Y) for a pose dict in degrees."""
    Rb = E(pose_.get("body", (0, 0, 0)))
    B = Vector((0, 0, 12 * P))
    sx = 1 if side == "r" else -1
    sh = B + Rb @ Vector((sx * 6 * P, 0, 10 * P))
    Ma = Rb @ E(pose_.get("arm_" + side, (0, 0, 0)))
    el = sh + Ma @ Vector((0, 0, -6 * P))
    Mf = Ma @ E(pose_.get("fore_" + side, (0, 0, 0)))
    hand = el + Mf @ Vector((0, 0, -6 * P))
    ring = el + Mf @ Vector((2.6 * P, 0, -4.1 * P))
    return hand, ring, el


def head_point(pose_, local):
    Rb = E(pose_.get("body", (0, 0, 0)))
    H = Vector((0, 0, 12 * P)) + Rb @ Vector((0, 0, 12 * P))
    hp = pose_.get("head", (0, 0, 0)); hp = (max(-57, min(57, hp[0])), hp[1], hp[2])
    return H + Rb @ E(hp) @ Vector(local)


def solve(pose_, side, target, which="hand", pref=None, w=0.002):
    """Coordinate descent on (arm x, y, z, elbow x) so the hand / ring lands on target (root space, metres);
    a light pull toward pref keeps it natural. Elbow bends one way only (0..150)."""
    pref = pref or [60.0, 0.0, 0.0, 40.0]
    x = list(pref)
    def cost(v):
        p = dict(pose_); p["arm_" + side] = (v[0], v[1], v[2]); p["fore_" + side] = (v[3], 0, 0)
        h, r_, _ = fk(p, side)
        pt = h if which == "hand" else r_
        return (pt - Vector(target)).length ** 2 + w * sum(((a - b) / 90.0) ** 2 for a, b in zip(v, pref)) * 0.01
    step = 20.0
    c = cost(x)
    while step > 0.05:
        moved = False
        for i in range(4):
            for d in (step, -step):
                y = list(x); y[i] += d
                if i == 3:
                    y[3] = min(150.0, max(0.0, y[3]))
                cy = cost(y)
                if cy < c:
                    x, c, moved = y, cy, True
        if not moved:
            step *= 0.5
    return (x[0], x[1], x[2]), (x[3], 0, 0), math.sqrt(max(0.0, c))


IDLE = dict(arm_r=(4, 0, -3), fore_r=(8, 0, 0), arm_l=(4, 0, 3), fore_l=(8, 0, 0), head=(0, 0, 0), body=(0, 0, 0),
            leg_r=(0, 0, 0), shin_r=(0, 0, 0), leg_l=(0, 0, 0), shin_l=(0, 0, 0))


def build_keys(keys):
    """keys: [(tick, dict)] where dict may hold ik_r / ik_l = (target, which, pref). Returns solved dicts + errors."""
    out, errs = [], []
    for f, d in keys:
        p = dict(IDLE); p.update({k: v for k, v in d.items() if not k.startswith("ik_")})
        for side in ("r", "l"):
            spec = d.get("ik_" + side)
            if spec:
                tgt, which, pref = spec
                if callable(tgt):
                    tgt = tgt(p)
                a, fo, err = solve(p, side, tgt, which, pref)
                p["arm_" + side], p["fore_" + side] = a, fo
                errs.append((f, side, round(err, 4)))
        out.append((f, p))
    return out, errs


# ------------------------------------------------------------------ first person: both arms placed in camera space
FP_LEN = 12 * P * 1.05


def fp_arms(tag, eye, M, wrist=False):
    """Camera looks along +Y. Each arm is one 4x12x4 box from a shoulder below the view; keys place the hand at a
    camera-space point (x right, y up, d depth) and turn the forearm (roll) so the ring face meets the eye."""
    rigs = {}
    for side, sx in (("r", 1), ("l", -1)):
        sh = empty(f"{tag} fp shoulder {side}", eye); sh.rotation_mode = "QUATERNION"
        px = P * 1.05
        box(f"{tag} fp sleeve {side}", (-2 * px, -2 * px, -8 * px), (2 * px, 2 * px, 0), M["shirt"], sh)
        if wrist and side == "r":
            # X1 (J): the hand on its own wrist pivot so the fist can turn, and the ring worn like a bracelet
            wr = empty(f"{tag} fp wrist", (0, 0, -8 * px), sh); rigs["wrist"] = wr
            box(f"{tag} fp hand {side}", (-2 * px, -2 * px, -4 * px), (2 * px, 2 * px, 0), M["skin"], wr)
            box(f"{tag} fp knuckles", (-2.05 * px, 1.2 * px, -4.05 * px), (2.05 * px, 2.05 * px, -3.0 * px), M["skin"], wr)
            box(f"{tag} fp ring band", (-2.3 * px, -2.3 * px, -7.9 * px), (2.3 * px, 2.3 * px, -6.9 * px), M["gold"], sh)
            box(f"{tag} fp ring face", (-1.1 * px, 2.3 * px, -8.2 * px), (1.1 * px, 2.8 * px, -6.6 * px), M["ring"], sh)
            rigs["ring_pt"] = empty(f"{tag} fp ring point", (0, 2.7 * px, -7.4 * px), sh)
            rigs["knuckle_pt"] = empty(f"{tag} fp knuckle point", (0, 1.6 * px, -4.2 * px), wr)
            rigs["hand_" + side] = empty(f"{tag} fp hand point {side}", (0, 0, -4 * px), wr)
            rigs[side] = sh
            continue
        box(f"{tag} fp hand {side}", (-2 * px, -2 * px, -12 * px), (2 * px, 2 * px, -8 * px), M["skin"], sh)
        if side == "r":
            box(f"{tag} fp ring band", (-2.2 * px, -2.2 * px, -10.6 * px), (2.2 * px, 2.2 * px, -9.6 * px), M["gold"], sh)
            box(f"{tag} fp ring face", (-1.0 * px, 2.2 * px, -11.0 * px), (1.0 * px, 2.7 * px, -9.2 * px), M["ring"], sh)
            rigs["ring_pt"] = empty(f"{tag} fp ring point", (0, 2.6 * px, -10.1 * px), sh)
        rigs["hand_" + side] = empty(f"{tag} fp hand point {side}", (0, 0, -12 * px), sh)
        rigs[side] = sh
    return rigs


def fp_key(rigs, side, f, eye, cam_pitch, x, y, d, roll):
    """Place an FP arm so its hand is at camera-space (x, y, d), with the camera pitched cam_pitch degrees."""
    Rc = Matrix.Rotation(R(cam_pitch), 3, "X")
    hand = Vector(eye) + Rc @ Vector((x, d, y))
    base = Vector(eye) + Rc @ Vector(((0.42 if side == "r" else -0.42), 0.05, -0.62))
    dirv = (hand - base).normalized()
    q = dirv.to_track_quat("-Z", "Y")
    q = q @ Matrix.Rotation(R(roll), 3, "Z").to_quaternion()
    sh = rigs[side]
    sh.location = hand - dirv * FP_LEN; sh.keyframe_insert("location", frame=f)
    sh.rotation_quaternion = q; sh.keyframe_insert("rotation_quaternion", frame=f)


def board(tag, loc, title, lines):
    """A dark board with the take's name and what it is for, facing the third-person camera (-Y)."""
    n = len(lines)
    box(f"{tag} board", (loc[0] - 1.7, loc[1], loc[2] - 0.2 - 0.13 * n), (loc[0] + 1.7, loc[1] + 0.05, loc[2] + 0.42), BOARD)
    label(title, (loc[0], loc[1] - 0.02, loc[2] + 0.12), TXTH, 0.2)
    cu = bpy.data.curves.new(f"{tag} notes", "FONT"); cu.body = "\n".join(lines); cu.size = 0.095; cu.align_x = "LEFT"
    o = link(bpy.data.objects.new(f"{tag} notes", cu)); o.location = (loc[0] - 1.6, loc[1] - 0.02, loc[2] - 0.05)
    o.rotation_euler = (R(90), 0, 0); o.data.materials.append(TXT)


# ------------------------------------------------------------------ the four takes
FORE = lambda p: head_point(p, (0, 4.6 * P, 5.5 * P))               # just in front of the brow
CHEST = lambda p: Vector((0.6 * P, 3.2 * P, 19.5 * P))               # over the heart, in front of the shirt
TAKES = {
    "X1": dict(
        name="Cast", full="X1  CAST - point the ring and fire",
        lines=["For: firing a power (Blast, Beam) - plays once per shot.",
               "1-6   ready: weight back, ring hand drawn in by the shoulder",
               "6-10  strike: the arm snaps straight out, the left arm swings",
               "      back to balance, left foot steps forward",
               "10-12 the ring flares (glow 2.4), the bolt leaves it",
               "12-30 hold on target, a small recoil, then settle",
               "30-44 back to rest with a little overshoot"],
        keys=[(1, {}),
              (6, dict(body=(2, 0, -14), head=(0, 0, 12), ik_r=(Vector((3 * P, 2 * P, 20 * P)), "hand", [40, 0, 0, 90]),
                       leg_r=(-4, 0, 0), leg_l=(6, 0, 0))),
              (10, dict(body=(-6, 0, 10), head=(4, 0, -8), arm_r=(90, 0, 4), fore_r=(0, 0, 0),
                        arm_l=(-28, 8, 0), fore_l=(35, 0, 0),
                        leg_r=(-14, 0, 0), leg_l=(22, 0, 0), shin_l=(-12, 0, 0), root_loc=(0, 0, -0.03))),
              (12, dict(body=(-4, 0, 8), head=(3, 0, -6), arm_r=(96, 0, 4), fore_r=(4, 0, 0),
                        arm_l=(-28, 8, 0), fore_l=(35, 0, 0),
                        leg_r=(-14, 0, 0), leg_l=(22, 0, 0), shin_l=(-12, 0, 0), root_loc=(0, 0, -0.03))),
              (28, dict(body=(-5, 0, 9), head=(3, 0, -7), arm_r=(91, 0, 4), fore_r=(0, 0, 0),
                        arm_l=(-28, 8, 0), fore_l=(35, 0, 0),
                        leg_r=(-14, 0, 0), leg_l=(22, 0, 0), shin_l=(-12, 0, 0), root_loc=(0, 0, -0.03))),
              (38, dict(arm_r=(-6, 0, -3), arm_l=(-4, 0, 3), body=(1, 0, -2), root_loc=(0, 0, 0))),
              (44, {})],
        fp=[(1, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (6, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (14, 0, ("r", 0.33, -0.25, 0.82, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (28, 0, ("r", 0.33, -0.25, 0.82, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (40, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)), (44, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0))],
        wrist=[(1, -90), (6, -90), (14, 10), (28, 10), (40, -90)],
        ring=[(1, 1.6), (9, 1.6), (10, 2.4), (14, 2.2), (28, 2.0), (40, 1.6)]),
    "X2": dict(
        name="Oath", full="X2  OATH - fist to the heart, then raised",
        lines=["For: the lantern oath / a charge-complete emote.",
               "1-8   the ring fist comes to the heart, head bows",
               "8-18  held: a slow breath",
               "18-22 the fist drives straight up (overshoot at 23),",
               "      the head lifts after it (max 40 deg), chest out",
               "22-30 a column of light rises from the ring",
               "30-46 held, the column pulses",
               "46-60 the fist comes down, light fades"],
        keys=[(1, {}),
              (8, dict(head=(-18, 0, 0), body=(-4, 0, 0), ik_r=(CHEST, "hand", [30, 0, 30, 120]))),
              (18, dict(head=(-20, 0, 0), body=(-5, 0, 0), ik_r=(CHEST, "hand", [30, 0, 30, 120]))),
              (22, dict(head=(10, 0, 0), body=(5, 0, 0), arm_r=(176, 0, -6), fore_r=(6, 0, 0), arm_l=(-6, 0, 6), fore_l=(20, 0, 0))),
              (23, dict(head=(24, 0, 0), body=(6, 0, 0), arm_r=(182, 0, -6), fore_r=(0, 0, 0), arm_l=(-8, 0, 6), fore_l=(24, 0, 0))),
              (26, dict(head=(36, 0, 0), body=(5, 0, 0), arm_r=(178, 0, -6), fore_r=(2, 0, 0), arm_l=(-8, 0, 6), fore_l=(24, 0, 0))),
              (46, dict(head=(40, 0, 0), body=(5, 0, 0), arm_r=(178, 0, -6), fore_r=(2, 0, 0), arm_l=(-8, 0, 6), fore_l=(24, 0, 0))),
              (56, dict(head=(4, 0, 0), arm_r=(20, 0, -4), fore_r=(20, 0, 0))), (60, {})],
        fp=[(1, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (8, -14, ("r", 0.05, -0.26, 0.75, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (18, -16, ("r", 0.05, -0.27, 0.75, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (22, 10, ("r", 0.15, 0.22, 0.95, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (26, 30, ("r", 0.14, 0.17, 0.92, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (46, 32, ("r", 0.14, 0.18, 0.92, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (56, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)), (60, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0))],
        ring=[(1, 1.6), (8, 2.0), (18, 2.2), (22, 2.4), (46, 3.0), (58, 1.6)]),
    "X3": dict(
        name="Focus", full="X3  FOCUS - ring to the brow",
        lines=["For: charging the ring at a lantern, or a 'focus' power-up.",
               "1-12  the ring hand comes up; the ring stops on the brow",
               "      (placed exactly), the head bows 20 deg to meet it",
               "12-16 contact: the ring flares, the eyes light",
               "16-40 held with two slow breaths (chest rises and falls)",
               "40-52 the head lifts first, then the hand comes away"],
        keys=[(1, {}),
              (8, dict(head=(-8, 0, 0), body=(-3, 0, 0), ik_r=(lambda p: FORE(p) + Vector((0, 0.06, -0.04)), "ring", [130, 0, 40, 110]))),
              (12, dict(head=(-20, 0, 0), body=(-6, 0, 0), ik_r=(FORE, "ring", [130, 0, 40, 110]))),
              (24, dict(head=(-22, 0, 0), body=(-4, 0, 0), ik_r=(FORE, "ring", [130, 0, 40, 110]))),
              (34, dict(head=(-20, 0, 0), body=(-7, 0, 0), ik_r=(FORE, "ring", [130, 0, 40, 110]))),
              (40, dict(head=(-21, 0, 0), body=(-5, 0, 0), ik_r=(FORE, "ring", [130, 0, 40, 110]))),
              (44, dict(head=(2, 0, 0), body=(-2, 0, 0), ik_r=(lambda p: FORE(p) + Vector((0, 0.08, -0.05)), "ring", [130, 0, 40, 110]))),
              (52, {})],
        fp=[(1, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (8, -8, ("r", 0.06, 0.20, 0.70, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (12, -20, ("r", 0.08, 0.22, 0.30, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (40, -21, ("r", 0.08, 0.22, 0.30, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (44, 0, ("r", 0.08, 0.10, 0.75, 0), ("l", -0.55, -0.6, 0.4, 0)), (52, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0))],
        ring=[(1, 1.6), (11, 1.6), (13, 2.4), (20, 2.4), (28, 3.0), (36, 2.4), (44, 1.6)]),
    "X4": dict(
        name="Put the ring on", full="X4  PUT THE RING ON - equip power-up",
        lines=["For: the moment the ring goes into the new ring slot",
               "(right hand). The ring is a separate object here.",
               "1-8   the left hand holds the ring up; the right hand rises",
               "8-16  the left hand slides the ring onto the right hand",
               "16    click - the ring is on; one soft glow swells and fades;",
               "      the left hand pulls away in 3 ticks",
               "18-22 power-up: the fist clenches, arms drive down and out,",
               "      knees bend, head up; a wave of bright light to 80 blocks",
               "22-34 held, glowing    34-46 stand back up to rest"],
        keys=[(1, dict(head=(-14, 0, 0), ik_r=(Vector((1.5 * P, 6.5 * P, 15 * P)), "hand", [60, 0, 20, 60]),
                       ik_l=(Vector((-1.5 * P, 7.5 * P, 17 * P)), "hand", [70, 0, -20, 60]))),
              (8, dict(head=(-16, 0, 0), ik_r=(Vector((1.5 * P, 7 * P, 17 * P)), "hand", [70, 0, 20, 50]),
                       ik_l=(lambda p: fk(p, "r")[0] + Vector((-4.2 * P, 0.5 * P, -0.5 * P)), "hand", [70, 0, -25, 60]))),
              (16, dict(head=(-16, 0, 0), ik_r=(Vector((1.5 * P, 7 * P, 17 * P)), "hand", [70, 0, 20, 50]),
                        ik_l=(lambda p: fk(p, "r")[1] + Vector((-4.6 * P, 0.4 * P, 0)), "hand", [70, 0, -25, 60]))),
              (18, dict(head=(-6, 0, 0), ik_r=(Vector((1.5 * P, 7 * P, 17 * P)), "hand", [70, 0, 20, 50]), arm_l=(-8, 6, 0), fore_l=(12, 0, 0))),
              (19, dict(head=(16, 0, 0), body=(-8, 0, 0), arm_r=(-14, -22, 0), fore_r=(36, 0, 0), arm_l=(-6, 8, 0), fore_l=(12, 0, 0),
                        leg_r=(28, 0, 6), shin_r=(-48, 0, 0), leg_l=(28, 0, -6), shin_l=(-48, 0, 0), root_loc=(0, 0, -0.12))),
              (22, dict(head=(20, 0, 0), body=(-6, 0, 0), arm_r=(-10, -26, 0), fore_r=(30, 0, 0), arm_l=(-5, 8, 0), fore_l=(12, 0, 0),
                        leg_r=(24, 0, 6), shin_r=(-42, 0, 0), leg_l=(24, 0, -6), shin_l=(-42, 0, 0), root_loc=(0, 0, -0.1))),
              (34, dict(head=(18, 0, 0), body=(-6, 0, 0), arm_r=(-10, -24, 0), fore_r=(30, 0, 0), arm_l=(-5, 8, 0), fore_l=(12, 0, 0),
                        leg_r=(24, 0, 6), shin_r=(-42, 0, 0), leg_l=(24, 0, -6), shin_l=(-42, 0, 0), root_loc=(0, 0, -0.1))),
              (46, dict(root_loc=(0, 0, 0)))],
        fp=[(1, -12, ("r", 0.20, -0.27, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (5, -12, ("r", 0.20, -0.27, 0.80, 0), ("l", -0.17, -0.25, 0.80, 0)),
            (9, -12, ("r", 0.20, -0.27, 0.80, 0), ("l", -0.07, -0.24, 0.80, 0)),
            (16, -12, ("r", 0.20, -0.27, 0.80, 0), ("l", -0.07, -0.24, 0.80, 0)),
            (19, -12, ("r", 0.20, -0.26, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (24, -12, ("r", 0.21, -0.24, 0.79, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (34, -10, ("r", 0.21, -0.24, 0.79, 0), ("l", -0.55, -0.6, 0.4, 0)),
            (46, 0, ("r", 0.38, -0.30, 0.80, 0), ("l", -0.55, -0.6, 0.4, 0))],
        ring=[(1, 1.2), (15, 1.2), (17, 2.4), (24, 2.2), (34, 1.9), (46, 1.6)]),
}

# J on X4: "looks good, but i dont like the ring at all that comes out id prefer i send a wave of bright light out like 80
# blocks". Same X4 animation; the light ring is replaced by a wave of light reaching 80 blocks (4 blocks a tick, 20 ticks).
TAKES["X4"]["wave"] = "dome"
TAKES["X4"]["bx"] = 780.0                                     # far from the others so the 80-block waves never cross them
TAKES["X4b"] = dict(TAKES["X4"], name="Put the ring on, ground wave", full="X4b  PUT THE RING ON - ground wave", wave="ground", bx=260.0)
TAKES["X4c"] = dict(TAKES["X4"], name="Put the ring on, double wave", full="X4c  PUT THE RING ON - double wave", wave="double", bx=520.0)
for _k, _w in (("X4", "dome of light"), ("X4b", "a wall of light along the ground"), ("X4c", "two domes of light, 6 ticks apart")):
    TAKES[_k] = dict(TAKES[_k]); TAKES[_k]["lines"] = list(TAKES[_k]["lines"])
    TAKES[_k]["lines"][-2] = f"      knees bend, head up; {_w} out to 80 blocks"
WAVE = {}


def glow_halo(tag, parent, camobj, f0=16, size=0.5):
    """One camera-facing quad with a soft round falloff (an additive-style sprite) on the ring: it swells and fades
    once after the click. In game: a single billboard particle plus the ring's emissive ramp."""
    me = bpy.data.meshes.new(tag + " halo")
    me.from_pydata([(-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0)], [], [(0, 1, 2, 3)]); me.update()
    m = bpy.data.materials.new(tag + " halo"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    sc_ = N.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs["Scale"].default_value = 2.0
    L.new(tc.outputs["Object"], sc_.inputs[0])
    gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; L.new(sc_.outputs[0], gr.inputs["Vector"])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.2; L.new(gr.outputs["Fac"], pw.inputs[0])
    inten = N.new("ShaderNodeValue"); inten.name = "intensity"
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(pw.outputs[0], mul.inputs[0]); L.new(inten.outputs[0], mul.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.06, 1.0, 0.28, 1); em.inputs["Strength"].default_value = 3.0
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(mul.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    me.materials.append(m)
    o = link(bpy.data.objects.new(tag + " halo", me)); o.parent = parent
    con = o.constraints.new("TRACK_TO"); con.target = camobj; con.track_axis = "TRACK_Z"; con.up_axis = "UP_Y"
    for f, v, sz in ((1, 0.0, 0.0001), (f0 - 1, 0.0, 0.0001), (f0, 0.9, size * 0.6), (f0 + 4, 1.0, size * 1.4), (f0 + 10, 0.45, size * 1.1),
                     (f0 + 18, 0.15, size * 0.9), (f0 + 30, 0.0, size * 0.8)):
        inten.outputs[0].default_value = v; inten.outputs[0].keyframe_insert("default_value", frame=f)
        o.scale = (sz, sz, sz); o.keyframe_insert("scale", frame=f)
    return o


def wall_ring(name, m, h):
    """An open ring wall, radius 1, height h (no caps), for scaling outward in x and y only."""
    n = 64; vs = []; fs = []
    for k in range(n):
        a = 2 * math.pi * k / n
        vs += [(math.cos(a), math.sin(a), 0), (math.cos(a), math.sin(a), h)]
    for k in range(n):
        fs.append((2 * k, 2 * ((k + 1) % n), 2 * ((k + 1) % n) + 1, 2 * k + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def light_wave(tag, center, kind, f0=19, reach=80.0, speed=4.0):
    """A wave of bright light from the player out to `reach` blocks at `speed` blocks a tick, fading as it goes."""
    dur = int(reach / speed)
    c = Vector(center)
    fl = ball(f"{tag} flash", 0.4, mat(f"{tag} flash", (0.05, 0.9, 0.25), emit=2.2, alpha=0.6), loc=tuple(c + Vector((0, 0, 1.0))), seg=16)
    key(fl, 1, sc=0.0001); key(fl, f0 - 1, sc=0.0001); key(fl, f0, sc=1.0); key(fl, f0 + 2, sc=1.2); key(fl, f0 + 4, sc=0.0001)
    lt = bpy.data.lights.new(f"{tag} wave light", "POINT"); lt.color = (0.2, 1.0, 0.35); lt.shadow_soft_size = 1.0
    lo = link(bpy.data.objects.new(f"{tag} wave light", lt)); lo.location = c + Vector((0, 0, 1.5))
    for f, e in ((1, 0), (f0 - 1, 0), (f0, 5000), (f0 + 4, 2500), (f0 + dur, 0)):
        lt.energy = e; lt.keyframe_insert("energy", frame=f)
    starts = [(f0, 0.25)] + ([(f0 + 6, 0.15)] if kind == "double" else [])
    for k, (fs, a0) in enumerate(starts):
        wm = mat(f"{tag} wave {k}", (0.03, 0.85, 0.2), emit=1.6, alpha=a0, rough=0.2)
        if kind in ("dome", "double"):
            w = ball(f"{tag} wave dome {k}", 1.0, wm, loc=tuple(c), seg=40)
        else:
            w = wall_ring(f"{tag} wave wall {k}", wm, 2.5); w.location = c
        band = wall_ring(f"{tag} wave front {k}", mat(f"{tag} wave front {k}", (0.05, 0.95, 0.25), emit=2.6, alpha=0.8), 0.25)
        band.location = c + Vector((0, 0, 0.02))
        for o, flat in ((w, kind == "ground"), (band, True)):
            key(o, 1, sc=0.0001); key(o, fs - 1, sc=0.0001)
            for i in range(0, dur + 1, 2):
                r = max(0.5, speed * i)
                key(o, fs + i, sc=(r, r, 1.0) if flat else (r, r, r))
            key(o, fs + dur + 1, sc=0.0001)
        anim_alpha(wm, [(fs, a0), (fs + dur // 3, a0 * 0.6), (fs + dur, 0.0)])


dump = {"format": "per take: solved third-person keys [tick, {part: [x, y, z] degrees}] (player faces +Y; arm x 90 = ahead, "
                  "head x + = look up, max 57), solver error (m), first-person keys [tick, camera pitch, [side, x, y, depth, roll]]",
        "takes": {}}
for bi, tk in enumerate(TAKES):
    T = TAKES[tk]
    cname = f"{tk} {T['name']}"
    col = bpy.data.collections.new(f"{tk} {T['name']} - {T['lines'][0][5:].rstrip('.')}")
    ROOTCOL.children.link(col)
    bx = T.get("bx", bi * BAY)
    tag = f"RG2 {tk}"
    box(f"{tag} floor", (bx - 2.2, -3, -0.02), (bx + 2.2, 3, 0), FLOOR)
    FPY = 120.0 if tk.startswith("X4") else 30.0           # X4: first person out of the wave's 80-block reach
    box(f"{tag} fp floor", (bx - 2.2, FPY - 4, -0.02), (bx + 2.2, FPY + 10, 0), FLOOR)
    M = player_mats(tag)
    M["ring"] = mat(f"{tag} ring face", RINGC, emit=1.6)
    rig = make_player(tag, (bx, 0, 0), M, face=math.pi)
    solved, errs = build_keys(T["keys"])
    for f, p in solved:
        pp = dict(p)
        rl = pp.pop("root_loc", (0, 0, 0))
        pp["root_loc"] = (bx + rl[0], rl[1], rl[2])
        pose(rig, f, **pp)
    anim_emit(M["ring"], T["ring"])
    eye = Vector((bx, FPY, 1.62))
    fpr = fp_arms(tag, eye, M, wrist=(tk == "X1"))
    fcam = cam(f"Cam {tk} {T['name']} - first person", tuple(eye), tuple(eye + Vector((0, 3, 0))), 26)
    for f, pitch, rspec, lspec in T["fp"]:
        for side, x, y, d, roll in (rspec, lspec):
            fp_key(fpr, side, f, eye, pitch, x, y, d, roll)
        fcam.rotation_euler = (R(90 + pitch), 0, 0); fcam.keyframe_insert("rotation_euler", frame=f)
    if "wrist" in T:                                             # the wrist turn, eased (smooth start and stop)
        _w = fpr["wrist"]; _w.rotation_mode = "XYZ"
        for f, a in T["wrist"]:
            key(_w, f, rot=(R(a), 0, 0))
        try:
            for fc in _w.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"; kp.easing = "AUTO"
        except Exception:
            pass
    fcam.data.lens = 10.4                                      # 120 degree horizontal view (36 mm sensor), as J plays
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        box(f"{tag} fp crosshair {nm_}", a_, b_, XH, fcam)
    # ------------------------------------------------------------ effects per take (kept off the lens in first person)
    if tk == "X1":
        b = ball(f"{tag} bolt 3p", 0.05, CM["rim"], parent=rig["ring_pt"])
        key(b, 1, loc=(0, 0, 0), sc=0.0001); key(b, 10, loc=(0, 0, 0), sc=0.0001); key(b, 11, loc=(0, 0, -0.1), sc=1.0)
        key(b, 19, loc=(0, 0, -6.0), sc=0.8); key(b, 20, loc=(0, 0, -6.0), sc=0.0001)
        scene.frame_set(14); bpy.context.view_layer.update()
        p0 = fpr["knuckle_pt"].matrix_world.translation.copy(); aim = Vector(eye) + Vector((0, 24.0, 0))
        bf = ball(f"{tag} bolt fp", 0.04, CM["rim"])
        key(bf, 1, loc=tuple(p0), sc=0.0001); key(bf, 13, loc=tuple(p0), sc=0.0001); key(bf, 14, loc=tuple(p0), sc=1.0)
        for k in range(1, 9):
            key(bf, 14 + k, loc=tuple(p0.lerp(aim, (k / 8) ** 1.2)), sc=1.0)
        key(bf, 23, loc=tuple(aim), sc=0.0001)
        for parent, nm, f0 in ((rig["ring_pt"], "3p", 10), (fpr["knuckle_pt"], "fp", 14)):
            fl = ball(f"{tag} muzzle flare {nm}", 0.04, SOFT, parent=parent)
            key(fl, 1, sc=0.0001); key(fl, f0 - 1, sc=0.0001); key(fl, f0, sc=1.0); key(fl, f0 + 2, sc=2.0); key(fl, f0 + 5, sc=0.0001)
    elif tk == "X2":
        for parent, nm, h in ((rig["ring_pt"], "3p", 7.0), (fpr["ring_pt"], "fp", 7.0)):
            c = cyl(f"{tag} oath column {nm}", 0.05, h, SOFT, 12, parent, axis="Z", loc=(0, 0, -0.08))
            c.rotation_euler = (math.pi, 0, 0)
            key(c, 1, sc=(1, 1, 0.0001)); key(c, 22, sc=(1, 1, 0.0001)); key(c, 30, sc=(1, 1, 1))
            for f in range(32, 47, 3):
                key(c, f, sc=(1 + 0.25 * math.sin(f), 1 + 0.25 * math.sin(f), 1))
            key(c, 50, sc=(1, 1, 0.0001))
            cc = cyl(f"{tag} oath core {nm}", 0.015, h, CM["glow"], 8, parent, axis="Z", loc=(0, 0, -0.08))
            cc.rotation_euler = (math.pi, 0, 0)
            key(cc, 1, sc=(1, 1, 0.0001)); key(cc, 22, sc=(1, 1, 0.0001)); key(cc, 28, sc=(1, 1, 1)); key(cc, 48, sc=(1, 1, 1)); key(cc, 50, sc=(1, 1, 0.0001))
    elif tk == "X3":
        anim_emit(M["eye"], [(1, 1.5), (12, 1.5), (14, 3.0), (40, 3.0), (46, 1.5)])
        glow = box(f"{tag} brow glow", (-2.5 * P, 4.05 * P, 4.5 * P), (2.5 * P, 4.3 * P, 7.2 * P), SOFT, rig["head"])
        key(glow, 1, sc=0.0001); key(glow, 12, sc=0.0001); key(glow, 14, sc=1.0); key(glow, 40, sc=1.0); key(glow, 44, sc=0.0001)
        # first person: the view tints green while the ring touches the brow
        VA = mat(f"{tag} fp screen glow", (0.1, 0.9, 0.3), emit=1.2, alpha=0.0)
        veil = box(f"{tag} fp screen glow", (-0.5, -0.3, -0.125), (0.5, 0.3, -0.12), VA, fcam)
        anim_alpha(VA, [(1, 0.0), (12, 0.0), (14, 0.28), (24, 0.16), (30, 0.26), (40, 0.16), (44, 0.0)])
    else:
        # the ring as its own object: in the left hand, slid onto the right hand, then it is part of the hand
        loose = empty(f"{tag} loose ring", (0, 0, 0))
        box(f"{tag} loose ring band", (-2.2 * P, -2.2 * P, -0.5 * P), (2.2 * P, 2.2 * P, 0.5 * P), M["gold"], loose)
        box(f"{tag} loose ring face", (2.2 * P, -1.0 * P, -0.9 * P), (2.9 * P, 1.0 * P, 0.9 * P), M["ring"], loose)
        floose = empty(f"{tag} fp loose ring", (0, 0, 0))
        px = P * 1.05
        box(f"{tag} fp loose band", (-2.2 * px, -2.2 * px, -0.5 * px), (2.2 * px, 2.2 * px, 0.5 * px), M["gold"], floose)
        box(f"{tag} fp loose face", (-1.0 * px, 2.2 * px, -0.9 * px), (1.0 * px, 2.7 * px, 0.9 * px), M["ring"], floose)
        worn = [o for o in col.objects if o.type == "MESH" and ("ring band" in o.name or "ring face" in o.name) and "loose" not in o.name]
        for o in worn:
            key(o, 1, sc=0.0001); key(o, 15, sc=0.0001); key(o, 16, sc=1.0)
        for f in range(1, 17):
            scene.frame_set(f); bpy.context.view_layer.update()
            u = smooth((f - 8) / 8.0)
            for lo, lhand, rring, band in ((loose, rig["fore_l"].matrix_world @ Vector((0, 0, -5.5 * P)), rig["ring_pt"], rig["fore_r"]),
                                           (floose, fpr["hand_l"].matrix_world.translation, fpr["ring_pt"], fpr["r"])):
                tgt = rring.matrix_world.translation if lo is loose else rring.matrix_world.translation
                if lo is loose:
                    band_pt = rig["fore_r"].matrix_world @ Vector((0, 0, -4.1 * P))
                else:
                    band_pt = fpr["r"].matrix_world @ Vector((0, 0, -10.1 * px))
                p = lhand.lerp(band_pt, u) if f >= 8 else lhand
                rot = band.matrix_world.to_euler() if f >= 8 else band.matrix_world.to_euler()
                lo.rotation_mode = "XYZ"
                key(lo, f, loc=tuple(p), rot=tuple(rot), sc=1.0)
        key(loose, 17, sc=0.0001); key(floose, 17, sc=0.0001)
        # power-up: a wave of bright light out to 80 blocks (third person round the player, first person round the eye)
        light_wave(tag + " 3p", (bx, 0, 0), T["wave"])
        cam(f"Cam {tk} {T['name']} - wave wide", (bx + 45, -75, 45), (bx, 0, 0), 26)
        big = box(f"{tag} wide ground", (bx - 90, -90, -0.035), (bx + 90, 120, -0.03), FLOOR)
        shells = []
        parts_ = [rig[k] for k in ("body", "head", "arm_r", "arm_l", "fore_r", "fore_l", "leg_r", "leg_l", "shin_r", "shin_l")]
        for o in list(col.objects):
            if o.type == "MESH" and o.parent in parts_ and "ring" not in o.name and "eye" not in o.name and "glow" not in o.name:
                vs = np.array([v.co for v in o.data.vertices]); a, b = vs.min(0) - 0.4 * P, vs.max(0) + 0.4 * P
                s_ = box(o.name + " outline", tuple(a), tuple(b), CM["glass"], o.parent); shells.append(s_)
        for s_ in shells:
            key(s_, 1, sc=0.0001); key(s_, 18, sc=0.0001); key(s_, 19, sc=1.0); key(s_, 22, sc=1.0); key(s_, 27, sc=0.0001)
    c3 = cam(f"Cam {tk} {T['name']} - third person", (bx + 2.4, -5.8, 1.9), (bx, 0, 1.25), 40)
    if tk.startswith("X4"):
        glow_halo(tag + " 3p", rig["ring_pt"], c3, 16, 0.35)
        glow_halo(tag + " fp", fpr["ring_pt"], fcam, 16, 0.35)
    board(tag, (bx, 1.6, 2.75), T["full"], T["lines"])
    dump["takes"][tk] = {"name": T["full"], "for": T["lines"][0],
                         "third_person": [[f, {k: [round(a, 1) for a in v] for k, v in p.items() if k != "root_loc"}] for f, p in solved],
                         "solver_error_m": errs, "first_person": [[f, pt, list(r_), list(l_)] for f, pt, r_, l_ in T["fp"]]}
    print(tk, "solver errors (m):", errs, flush=True)
col = ROOTCOL
about = ["ABOUT THIS FILE (pass 816)",
         "Ring-hand gestures, round 2. Ring on the right hand.",
         "Each take: third-person camera (whole body) + first-person",
         "camera (what you see). Boards say what each one is for.",
         "Play from frame 1; each take is 44-60 ticks at 20 a second."]
cu = bpy.data.curves.new("RG2 about", "FONT"); cu.body = "\n".join(about); cu.size = 0.13; cu.align_x = "LEFT"
ab = link(bpy.data.objects.new("RG2 about this file", cu)); ab.location = (-4.4, 1.0, 2.6); ab.rotation_euler = (R(90), 0, 0)
ab.data.materials.append(TXT)
with open(os.path.join(FOLDER, "combat", "gestures2_poses.json"), "w") as fh:
    json.dump(dump, fh, indent=1)
cam("Cam all", (1.5 * BAY - 1.0, -13, 3.6), (1.5 * BAY - 1.0, 0, 1.4), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam X4 Put the ring on - third person", 1, (0.3, 0.38, 0.5), 3.0


# ------------------------------------------------------------------ stage, light, bloom, save
scene.frame_start, scene.frame_end = 1, FRAME_END
world = bpy.data.worlds.new(SCENE_NAME + " world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (*WORLD_RGB, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new(SCENE_NAME + " sun", bpy.data.lights.new(SCENE_NAME + " sun", "SUN")))
sun.data.energy = SUN; sun.rotation_euler = (R(45), R(-10), R(-30))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new(SCENE_NAME + " Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm_, val in (("Size", 0.5), ("Strength", 0.45), ("Threshold", 1.0)):
        if nm_ in gl.inputs:
            gl.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects[START_CAM]
scene.frame_set(START_FRAME)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def _after():
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    for sp in a.spaces:
                        if sp.type == "VIEW_3D":
                            sp.region_3d.view_perspective = "CAMERA"
                            sp.shading.type = "MATERIAL"
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
