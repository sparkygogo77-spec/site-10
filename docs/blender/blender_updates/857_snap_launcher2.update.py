# Pass 857: snap launcher 2 - "Catapult: forms the way it launches" (Chat C, 2026-10-15, range 800-899).
# Variations of 822 S1 catapult cradle (IMPROVE). J: "The construct should form in whatever way the catapult will
# launch it, not from me". 822 S2 ram boat and S3 gold catapult were dropped, so only S1's three new siblings are here.
# Kept from S1: the boat cradle (hull, ribs, bow, stern, hinged sides) in the block the mob is about to step on, the
# snap at 31, hold while it struggles, let go at 44, a 10-block throw and a landing ring. Gone: the track built out
# from the player. Nothing streams from the ring; every piece forms along the launch path and the mob flies that path.
#   S1a arc traced back: the throw arc draws itself backward from the landing ring (5) to the mob's next block (6-18);
#       the arm and cradle form off the arc's foot, cup first (18-28); on release the arm whips up and the mob rides
#       the same arc, which wipes out behind it.
#   S1b arm sweep frame: the arm appears at the top of its throw (12) and sweeps down through the throw path (14-24),
#       leaving its curved side rails, struts and a stop beam behind; the hull forms under it; release whips it back
#       up the rails in 3 ticks and the mob leaves the cup at the stop.
#   S1c rising launch rail: a 40-degree launch rail rises out of the ground under the mob's next block along the launch
#       axis, foot first (12-24); the cradle rises up out of the floor at its foot (22-28); release shoots the cradle
#       up the rail in 3 ticks, it stops dead and the mob flies on.
# Cameras "Cam <take>", "Cam <take> top", "Cam all". Builds LanternLive\constructs\snap_launcher2.blend.
SCENE_NAME = "Snap Launcher 2"
OUT_REL = "constructs/snap_launcher2.blend"
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


FRAME_END = 80
BAY = 8.0
REL = 44
FLOOR = mat("SL floor", (0.2, 0.22, 0.2), rough=0.9)
STONE = mat("SL wall", (0.42, 0.42, 0.44), rough=0.9)
MOB = mat("SL mob", (0.3, 0.5, 0.28), rough=0.8)
MARK = mat("SL target block", (0.2, 1.0, 0.4), emit=1.5, alpha=0.25)
BOARD = mat("SL board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("SL text", (0.75, 1.0, 0.8), emit=1.2)
TXTH = mat("SL heading", (0.2, 1.0, 0.4), emit=2.2)
rng = np.random.default_rng(857)
GREEN = cmats("SL", "green")
GOLD = {"glass": mat("SL gold glass", (0.55, 0.38, 0.04), emit=0.9, alpha=0.62, rough=0.15),
        "glow": mat("SL gold glow", (1.0, 0.72, 0.08), emit=3.0), "rim": mat("SL gold rim", (1.0, 0.75, 0.1), emit=3.6),
        "grip": mat("SL gold grip", (0.2, 0.13, 0.02), emit=0.6), "pix": mat("SL gold pixel", (1.0, 0.75, 0.1), emit=4.0)}
# ------------------------------------------------------------------ first person: both arms placed in camera space
FP_LEN = 12 * P * 1.05


def fp_arms(tag, eye, M):
    """Camera looks along +Y. Each arm is one 4x12x4 box from a shoulder below the view; keys place the hand at a
    camera-space point (x right, y up, d depth) and turn the forearm (roll) so the ring face meets the eye."""
    rigs = {}
    for side, sx in (("r", 1), ("l", -1)):
        sh = empty(f"{tag} fp shoulder {side}", eye); sh.rotation_mode = "QUATERNION"
        px = P * 1.05
        box(f"{tag} fp sleeve {side}", (-2 * px, -2 * px, -8 * px), (2 * px, 2 * px, 0), M["shirt"], sh)
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




def mob(tag, loc):
    r = empty(f"{tag} mob", loc); r.rotation_euler = (0, 0, R(90))           # walks toward -X
    parts = [box(f"{tag} mob body", (-0.3, -0.45, 0.4), (0.3, 0.45, 0.95), MOB, r),
             box(f"{tag} mob head", (-0.22, 0.4, 0.7), (0.22, 0.85, 1.1), MOB, r)]
    legs = []
    for x in (-0.2, 0.2):
        for y in (-0.3, 0.3):
            lg = empty(f"{tag} mob hip {x} {y}", (x, y, 0.4), r)
            parts.append(box(f"{tag} mob leg {x} {y}", (-0.08, -0.08, -0.4), (0.08, 0.08, 0), MOB, lg)); legs.append((lg, x * y > 0))
    return r, parts, legs


def build_cradle(tag, bx, cy, C, prow=False, arm=False):
    """A boat-shaped cradle 1 block wide, 1.4 long, in the block (bx, cy). Sides are hinged so they can snap up."""
    root = empty(f"{tag} cradle", (bx, cy, 0.0))
    parts = [box(f"{tag} hull floor", (-0.5, -0.7, 0.0), (0.5, 0.7, 0.12), C["glass"], root)]
    for k, y in enumerate((-0.55, -0.15, 0.25)):
        parts.append(box(f"{tag} rib {k}", (-0.52, y, 0.0), (0.52, y + 0.08, 0.16), C["rim"], root))
    for sy, nm in ((-0.75, "stern"), (0.75, "bow")):
        parts.append(box(f"{tag} {nm}", (-0.45, sy - 0.08, 0.0), (0.45, sy + 0.08, 0.35 if nm == "stern" else 0.3), C["glass"], root))
    sides = []
    for sx in (-1, 1):
        h = empty(f"{tag} side hinge {sx}", (sx * 0.5, 0, 0.1), root)
        s_ = box(f"{tag} side {sx}", (-0.05 if sx > 0 else -0.05, -0.65, 0.0), (0.05, 0.65, 0.5), C["glass"], h)
        r_ = box(f"{tag} side rim {sx}", (-0.06, -0.65, 0.46), (0.06, 0.65, 0.52), C["rim"], h)
        parts += [s_, r_]; sides.append((h, sx))
    out = {"root": root, "parts": parts, "sides": sides}
    if prow:                                                 # the ram: a capped prow on the front of the boat
        ram = cyl(f"{tag} ram", 0.22, 0.9, C["glass"], 12, root, loc=(0, 0.7, 0.35), axis="Y", r2=0.12)
        cap = cyl(f"{tag} ram cap", 0.16, 0.15, C["rim"], 12, root, loc=(0, 1.55, 0.35), axis="Y")
        out["parts"] += [ram, cap]
    if arm:                                                  # the catapult arm, hinged at the stern, lying flat under the mob
        hinge = empty(f"{tag} arm hinge", (0, -0.7, 0.14), root); hinge.rotation_mode = "XYZ"
        beam = box(f"{tag} arm beam", (-0.08, 0.0, 0.0), (0.08, 1.3, 0.08), C["glow"], hinge)
        cup = box(f"{tag} arm cup", (-0.4, 0.9, 0.0), (0.4, 1.35, 0.14), C["rim"], hinge)
        out["parts"] += [beam, cup]; out["arm"] = hinge
    return out

# ------------------------------------------------------------------ pass 857: the catapult forms the way it launches
TAKE_INFO = {
    "S1a": ("arc traced back", ["Hold right click: the throw arc draws itself BACKWARD,",
                               "from the landing ring (tick 5) to the mob's next block",
                               "(6-18); the cradle and arm form off the arc's foot",
                               "(18-28). Let go (44): it flies along that same arc."]),
    "S1b": ("arm sweep frame", ["Hold right click: the arm appears at the top of its",
                               "throw (12) and sweeps down through it (14-24), leaving",
                               "the side rails, struts and stop beam behind; the hull",
                               "forms under it (22-28). Let go (44): the arm whips up."]),
    "S1c": ("rising launch rail", ["Hold right click: a launch rail rises out of the ground",
                                  "under the mob's next block, along the launch axis",
                                  "(12-24); the cradle rises in at its foot (22-28).",
                                  "Let go (44): it shoots up the rail and flings the mob."]),
}
LAND = 10.0                                  # landing distance from the cradle (blocks), as S1
PEAK = 4.0                                   # arc height above the cup


def seg(name, p, q, m, w=0.05, parent=None):
    """A box from point p to point q (world, in the YZ plane of the take), w half-thick; returns (pivot, box)."""
    p = Vector(p); q = Vector(q); d = q - p
    piv = empty(name + " pivot", tuple((p + q) / 2), parent)
    piv.rotation_euler = (math.atan2(d.z, d.y), 0, 0)
    L_ = d.length
    b = box(name, (-w, -L_ / 2, -w), (w, L_ / 2, w), m, piv)
    return piv, b


def pop(o, fa, sc0=None, over=1.18):
    """Pop in at fa: nothing until fa-1, overshoot, settle."""
    sc0 = tuple(o.scale) if sc0 is None else sc0
    key(o, 1, sc=0.0001); key(o, fa - 1, sc=0.0001)
    key(o, fa + 1, sc=tuple(s * over for s in sc0)); key(o, fa + 2, sc=sc0)


def mob_held(r, mlegs, bx, cy, z=0.12, f0=32, f1=REL):
    for f in range(f0, f1, 2):
        key(r, f, loc=(bx, cy, z), rot=(R(rng.uniform(-8, 8)), R(rng.uniform(-8, 8)), R(90 + rng.uniform(-15, 15))))
        for lg, ph in mlegs:
            key(lg, f, rot=(R(rng.uniform(-40, 40)), 0, 0))


def land_fx(tag, C, bx, y, f):
    lr = torus(f"{tag} land ring", 0.4, 0.03, C["rim"], loc=(bx, y, 0.04))
    key(lr, 1, sc=0.0001); key(lr, f - 1, sc=0.0001); key(lr, f, sc=(1, 1, 1)); key(lr, f + 8, sc=(4, 4, 1)); key(lr, f + 9, sc=0.0001)


def cradle_body(tag, bx, cy, C):
    """The S1 boat cradle (hull, ribs, bow, stern, hinged sides) without its arm."""
    return build_cradle(tag, bx, cy, C, prow=False, arm=False)


def front_arm(tag, cr, C):
    """The catapult arm, hinged at the BOW end and lying flat back along the hull under the mob, so it swings up and
    over toward the throw (+Y). Rotation X goes negative to swing up. Cup centre is 1.1 back from the hinge."""
    hinge = empty(f"{tag} arm hinge", (0, 0.62, 0.14), cr["root"]); hinge.rotation_mode = "XYZ"
    beam = box(f"{tag} arm beam", (-0.08, -1.25, 0.0), (0.08, 0.0, 0.08), C["glow"], hinge)
    cup = box(f"{tag} arm cup", (-0.4, -1.35, 0.0), (0.4, -0.85, 0.14), C["rim"], hinge)
    return hinge, [beam, cup]


def cup_world(bx, cy, th_deg, r=1.1, hz=0.14, hy=0.62):
    th = R(th_deg)
    return Vector((bx, cy + hy - r * math.cos(th), hz - r * math.sin(th)))


def arc_pt(p0, p1, peak, u):
    """Throw arc from p0 to p1 (p1 on the ground), peaking `peak` above the straight line."""
    return p0.lerp(p1, u) + Vector((0, 0, peak * 4 * u * (1 - u)))


TAKES = [("S1a", GREEN), ("S1b", GREEN), ("S1c", GREEN)]
for bi, (tk, C0) in enumerate(TAKES):
    name, notes = TAKE_INFO[tk]
    bx = bi * BAY
    tag = f"SL {tk}"
    C = cmats(tag, "green")                          # own materials per take, so keyed glow stays per take
    box(f"{tag} floor", (bx - 3.5, -3, -0.02), (bx + 3.5, 22, 0), FLOOR)
    M = player_mats(tag)
    rig = make_player(tag, (bx, 0, 0), M)
    pose(rig, 1, arm_r=(0, 0, 0), fore_r=(0, 0, 0), head=(0, 0, 0))
    pose(rig, 5, arm_r=(85, 0, 0), fore_r=(5, 0, 0), head=(-8, 0, 0))                 # aiming, holding right click
    for f in range(8, REL, 6):
        pose(rig, f, arm_r=(85 + 2 * math.sin(f), 0, 0), fore_r=(5, 0, 0), head=(-8, 0, 0))
    pose(rig, REL, arm_r=(85, 0, 0), fore_r=(5, 0, 0)); pose(rig, REL + 3, arm_r=(118, 0, 0), fore_r=(0, 0, 0), head=(4, 0, 0))
    pose(rig, REL + 14, arm_r=(10, 0, 0), fore_r=(8, 0, 0), head=(0, 0, 0))
    anim_emit(M["ring"], [(1, 1.6), (5, 2.4), (REL, 2.4), (REL + 1, 3.2), (REL + 8, 1.6)])
    cy = 6.0
    # the mob walks along x toward the line; the block it is about to step on glows (as S1)
    r, mparts, mlegs = mob(tag, (bx + 4.0, cy, 0))
    for f in range(1, 32):
        x = bx + 4.0 - 4.0 * min(1.0, (f - 1) / 29.0)
        key(r, f, loc=(x, cy, 0))
        for lg, ph in mlegs:
            key(lg, f, rot=(R(30 * math.sin(f * 0.9 + (math.pi if ph else 0))), 0, 0))
    mark = box(f"{tag} next block", (bx - 0.5, cy - 0.5, 0.0), (bx + 0.5, cy + 0.5, 1.0), MARK)
    key(mark, 1, sc=0.0001); key(mark, 13, sc=0.0001); key(mark, 14, sc=1.0); key(mark, 30, sc=1.0); key(mark, 31, sc=0.0001)
    cr = cradle_body(tag, bx, cy, C)
    for h, sx in cr["sides"]:                               # sides lie open, then SNAP shut at 31
        key(h, 1, rot=(0, R(sx * 80), 0)); key(h, 30, rot=(0, R(sx * 80), 0)); key(h, 31, rot=(0, R(-sx * 6), 0)); key(h, 33, rot=(0, 0, 0))
    snap = torus(f"{tag} snap ring", 0.6, 0.02, C["rim"], loc=(bx, cy, 0.3))
    key(snap, 1, sc=0.0001); key(snap, 30, sc=0.0001); key(snap, 31, sc=(1, 1, 1)); key(snap, 36, sc=(2.2, 2.2, 1)); key(snap, 37, sc=0.0001)
    mob_held(r, mlegs, bx, cy)
    p_land = Vector((bx, cy + LAND, 0.0))
    extra = []                                              # construct pieces that break at the end
    if tk in ("S1a", "S1b"):
        hinge, arm_parts = front_arm(tag, cr, C)
        TOP = -115
        p_rel = cup_world(bx, cy, TOP) + Vector((0, 0, 0.3))
        DUR = 15
        L0 = REL + 3                                         # mob leaves the cup
        if tk == "S1a":
            # 1) the throw arc draws itself backward: landing ring first, then the arc from the landing end to the cradle
            land_mark = torus(f"{tag} target ring", 0.45, 0.03, C["rim"], loc=tuple(p_land + Vector((0, 0, 0.03))))
            pop(land_mark, 5, (1, 1, 1))
            ARC = mat(f"{tag} arc", C["c"], emit=3.0, alpha=0.8)
            anim_emit(ARC, [(1, 3.0), (18, 3.0), (24, 1.0), (REL, 1.0), (REL + 1, 4.0), (REL + 12, 2.0)])
            NS = 22
            pts = [arc_pt(p_rel, p_land, PEAK, i / NS) for i in range(NS + 1)]
            arc_segs = []
            for i in range(NS):
                piv, b = seg(f"{tag} arc seg {i:02d}", pts[i], pts[i + 1], ARC, w=0.035)
                fa = int(round(6 + (NS - 1 - i) / (NS - 1) * 12))          # far end first (6) back to the foot (18)
                pop(b, fa, (1, 1, 1), over=1.6)
                fv = int(round(L0 + (i + 0.5) / NS * DUR))                    # wiped out right behind the flying mob
                key(b, fv, sc=(1, 1, 1)); key(b, fv + 1, sc=0.0001)
                arc_segs.append(b)
            # runner pixels travel the arc backward while it draws (they ride from the target into the cradle)
            pm = pixel_mesh(C["pix"])
            for j in range(6):
                px = link(bpy.data.objects.new(f"{tag} runner", pm)); s0 = 5 + 2 * j
                key(px, 1, loc=tuple(p_land), sc=0.0001); key(px, s0, loc=tuple(p_land), sc=0.0001)
                for k in range(0, 11):
                    key(px, s0 + 1 + k, loc=tuple(arc_pt(p_rel, p_land, PEAK, 1 - k / 10)), sc=1.4)
                key(px, s0 + 12, sc=0.0001)
            # 2) the cradle and arm form off the arc's foot: cup first, then down the arm, then the hull bow to stern
            bpy.context.view_layer.update()
            order = arm_parts[::-1] + sorted(cr["parts"], key=lambda o: -(o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))).y)
            for k, o in enumerate(order):
                pop(o, int(round(18 + k / (len(order) - 1) * 10)))
            # the arm is "landed" from the arc: it sits up at the throw angle as it forms and drops flat by 28
            key(hinge, 1, rot=(R(TOP), 0, 0)); key(hinge, 19, rot=(R(TOP), 0, 0)); key(hinge, 26, rot=(0, 0, 0))
        else:
            # S1b: the arm appears at the TOP of its throw and sweeps down through it, leaving the frame behind
            key(hinge, 1, rot=(R(TOP), 0, 0)); key(hinge, 14, rot=(R(TOP), 0, 0)); key(hinge, 24, rot=(R(-4), 0, 0)); key(hinge, 26, rot=(0, 0, 0))
            for o in arm_parts:
                pop(o, 12, over=1.3)
            hw = Vector((bx, cy + 0.62, 0.14))
            # stop beam + two struts at the top of the throw (formed first, with the arm)
            ex = []
            for sx in (-0.5, 0.5):
                top = cup_world(bx, cy, TOP - 3, r=0.95) + Vector((sx, 0, 0))
                piv, b = seg(f"{tag} strut {sx}", hw + Vector((sx, 0, 0)), top, C["rim"], w=0.04); pop(b, 13); ex.append(b)
                post = box(f"{tag} post {sx}", (bx + sx - 0.05, cy + 0.57, 0.0), (bx + sx + 0.05, cy + 0.67, 0.2), C["glass"]); pop(post, 13); ex.append(post)
            tb = cup_world(bx, cy, TOP - 3, r=0.95)
            stop = box(f"{tag} stop beam", (bx - 0.55, tb.y - 0.06, tb.z - 0.06), (bx + 0.55, tb.y + 0.06, tb.z + 0.06), C["glow"]); pop(stop, 13); ex.append(stop)
            # the cup's swept path left behind as two curved side rails, one segment per angle as the arm passes
            NR = 10
            for sx in (-0.48, 0.48):
                for i in range(NR):
                    a0 = TOP + (0 - TOP) * i / NR; a1 = TOP + (0 - TOP) * (i + 1) / NR
                    p_ = cup_world(bx, cy, a0, r=1.15) + Vector((sx, 0, 0)); q_ = cup_world(bx, cy, a1, r=1.15) + Vector((sx, 0, 0))
                    piv, b = seg(f"{tag} sweep rail {sx} {i}", p_, q_, C["rim"] if i % 3 == 0 else C["glass"], w=0.035)
                    pop(b, int(round(14 + (i + 0.5) / NR * 10)), over=1.4); ex.append(b)
            # the hull forms under the arm as it comes down: hinge end first, stern last (22-28)
            bpy.context.view_layer.update()
            order = sorted(cr["parts"], key=lambda o: -(o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))).y)
            for k, o in enumerate(order):
                pop(o, int(round(21 + k / (len(order) - 1) * 7)))
            extra += ex
        # release: the arm whips up through the same path to the top in 3 ticks and the mob leaves the cup along the arc
        key(hinge, REL, rot=(0, 0, 0)); key(hinge, REL + 3, rot=(R(TOP), 0, 0)); key(hinge, REL + 5, rot=(R(TOP + 6), 0, 0))
        key(hinge, REL + 9, rot=(R(TOP), 0, 0)); key(hinge, REL + 18, rot=(R(-20), 0, 0))
        key(r, REL, loc=(bx, cy, 0.12), rot=(0, 0, R(90)))
        key(r, REL + 2, loc=tuple(cup_world(bx, cy, -70) + Vector((0, 0, 0.1))), rot=(R(-20), 0, R(90)))
        for k in range(0, DUR + 1):
            u = k / DUR
            key(r, L0 + k, loc=tuple(arc_pt(p_rel, p_land, PEAK, u)), rot=(-u * 6, 0, R(90)))
        land = L0 + DUR
        land_fx(tag, C, bx, p_land.y, land)
        key(r, land + 6, loc=(bx, p_land.y + 0.6, 0), rot=(0, 0, R(90)))
        shatter(cr["parts"] + arm_parts + extra, REL + 22, C["pix"], rng, tag, n=1, speed=0.06)
    else:
        # S1c: a launch rail rises out of the ground under the load, along the launch axis (40 deg up, toward +Y)
        ANG = R(40); RL = 3.0
        dirv = Vector((0, math.cos(ANG), math.sin(ANG)))
        foot = Vector((bx, cy, 0.05)); top = foot + dirv * RL
        NR = 8
        rail_parts = []
        for i in range(NR):
            a_ = foot + dirv * (RL * i / NR); b_ = foot + dirv * (RL * (i + 1) / NR)
            fa = int(round(12 + i / (NR - 1) * 12))                       # under the load first, then out along the axis
            for sx in (-0.42, 0.42):
                piv, b = seg(f"{tag} rail {sx} {i}", a_ + Vector((sx, 0, 0)), b_ + Vector((sx, 0, 0)), C["rim"], w=0.045)
                rail_parts.append(b)
                p_end = piv.location.copy()
                key(piv, 1, loc=tuple(p_end - Vector((0, 0, 1.6 + p_end.z)))); key(piv, fa - 2, loc=tuple(p_end - Vector((0, 0, 1.6 + p_end.z))))
                key(piv, fa + 1, loc=tuple(p_end + Vector((0, 0, 0.06)))); key(piv, fa + 2, loc=tuple(p_end))
                pop(b, fa - 1, (1, 1, 1), over=1.0)
            # a crosstie and a leg down to the ground per segment (the leg rises with it)
            mid = (a_ + b_) / 2
            tie = box(f"{tag} tie {i}", (bx - 0.45, mid.y - 0.05, mid.z - 0.04), (bx + 0.45, mid.y + 0.05, mid.z + 0.03), C["glass"])
            pop(tie, fa + 1); rail_parts.append(tie)
            if mid.z > 0.3:
                leg = box(f"{tag} leg {i}", (bx - 0.06, mid.y - 0.06, 0.0), (bx + 0.06, mid.y + 0.06, mid.z), C["glass"])
                key(leg, 1, sc=(1, 1, 0.0001)); key(leg, fa - 1, sc=(1, 1, 0.0001)); key(leg, fa + 1, sc=(1, 1, 1)); rail_parts.append(leg)
        stopb = box(f"{tag} rail stop", (bx - 0.5, top.y - 0.05, top.z - 0.12), (bx + 0.5, top.y + 0.1, top.z + 0.12), C["glow"])
        pop(stopb, 25, over=1.4); rail_parts.append(stopb)
        # the cradle rises up out of the floor at the rail's foot (22-28), already tilted onto the rail
        root = cr["root"]
        key(root, 1, loc=(bx, cy, -0.9), rot=(0, 0, 0)); key(root, 22, loc=(bx, cy, -0.9))
        key(root, 27, loc=(bx, cy, 0.05)); key(root, 28, loc=(bx, cy, 0.0))
        for o in cr["parts"]:
            key(o, 1, sc=0.0001); key(o, 21, sc=0.0001); key(o, 22, sc=tuple(o.scale) if o.scale.x > 0.001 else (1, 1, 1))
        # release: cradle tips onto the rail and shoots up it in 3 ticks, stops dead at the top; the mob flies on
        key(root, REL, loc=(bx, cy, 0.0), rot=(0, 0, 0)); key(root, REL + 1, loc=tuple(foot + dirv * 0.2), rot=(ANG, 0, 0))
        key(root, REL + 4, loc=tuple(top - dirv * 0.75), rot=(ANG, 0, 0)); key(root, REL + 6, loc=tuple(top - dirv * 0.85), rot=(ANG, 0, 0))
        for f in range(REL, REL + 5):
            u = (f - REL) / 4
            key(r, f, loc=tuple(foot.lerp(top - dirv * 0.75, u * u) + Vector((0, 0, 0.15))), rot=(-ANG * u, 0, R(90)))
        s0 = top + Vector((0, 0, 0.25)); D = p_land.y - s0.y; DUR = 12
        vy = D / DUR; vz = vy * math.tan(ANG); g = 2 * (s0.z + vz * DUR) / DUR ** 2
        for k in range(1, DUR + 1):
            key(r, REL + 4 + k, loc=(bx, s0.y + vy * k, max(0.0, s0.z + vz * k - g * k * k / 2)), rot=(-ANG + k / DUR * 1.4, 0, R(90)))
        land = REL + 4 + DUR
        land_fx(tag, C, bx, p_land.y, land)
        key(r, land + 6, loc=(bx, p_land.y + 0.6, 0), rot=(0, 0, R(90)))
        shatter(cr["parts"] + rail_parts, REL + 22, C["pix"], rng, tag, n=1, speed=0.06)
    board(tag, (bx, 21.5, 3.2), f"{tk}  {name.upper()}", notes)
    cam(f"Cam {tk}", (bx + 5.5, -2.5, 4.5), (bx, 6.0, 0.8), 30)
    cam(f"Cam {tk} top", (bx + 0.3, 8.0, 18.0), (bx + 0.3, 8.1, 0.0), 35)
    print(tk, "built", flush=True)
cam("Cam all", (BAY, -12.0, 10.0), (BAY, 8.0, 0.5), 30)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam S1a", 1, (0.35, 0.45, 0.6), 3.0



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
