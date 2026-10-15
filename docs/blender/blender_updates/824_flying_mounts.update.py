# Pass 824: flying mounts - the horse flies, a baby dragon, a construct ghast (Chat C, 2026-10-15, range 800-899).
# J on 809: "horse is the only flying construct i want right now, maybe well force the lantern user to learn to ride a
# flying creature, give me a flying baby dragon to ride on and also a ghast construct (it needs to fit the real model
# instead of colliding with it, but since ours is pure construct you can make a new textured ghast instead".
#   F1 flying horse (BR1, as 809's V3): gallops, then runs up into the air; a light pad flashes under each hoof as it
#      strikes the air, so it reads as running on light; mane and tail stream
#   F2 baby dragon (X3D1): chubby, big head, short neck, stubby fast wings, short tail; a hop, flapping climb, a glide
#      and a bank, the rider's legs hanging either side
#   F3 construct ghast, real size (W1): the body is the ghast's own 4 x 4 x 4 block cube with nine tentacles in a 3 x 3
#      grid, so it sits exactly over the real model instead of cutting into it; a construct face; floats and drifts
#   F4 construct ghast, textured and harnessed (H1): the same size, a harness frame on top with four seats, goggles
#      over the eyes; rises with four riders, tentacles trailing
# Cameras "Cam <take>" (follows), "Cam <take> side", "Cam all". Builds LanternLive\constructs\flying_mounts.blend.
SCENE_NAME = "Flying Mounts"
OUT_REL = "constructs/flying_mounts.blend"
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


FRAME_END = 120
BAY = 14.0
FORM = 20
FLOOR = mat("FM floor", (0.18, 0.21, 0.2), rough=0.9)
LBL = mat("FM label", (0.3, 1.0, 0.45), emit=2.0)
GHOST = mat("FM real ghast outline", (0.9, 0.9, 0.9), alpha=0.08)
rng = np.random.default_rng(824)
CM = cmats("FM", "green")
RM, W, GR, GL = CM["rim"], CM["glow"], CM["grip"], CM["glass"]
TEX = {k: strip_mat(f"FM {k} texture", strip_image("green", k), 4, emit=1.3, alpha=0.9) for k in ("br1", "x3d1", "w1", "h1")}


def rider(tag, parent, loc, legs_down=False):
    M = player_mats(tag)
    rig = make_player(tag, (0, 0, 0), M)
    rig["root"].parent = parent; rig["root"].location = Vector(loc) - Vector((0, 0, 12 * P))
    if legs_down:
        pose(rig, 1, leg_r=(20, 0, 25), leg_l=(20, 0, -25), shin_r=(-30, 0, 0), shin_l=(-30, 0, 0), arm_r=(55, 0, 0), arm_l=(55, 0, 0),
             fore_r=(20, 0, 0), fore_l=(20, 0, 0), body=(-14, 0, 0), head=(10, 0, 0))
    else:
        pose(rig, 1, leg_r=(90, 0, 8), leg_l=(90, 0, -8), shin_r=(-90, 0, 0), shin_l=(-90, 0, 0), arm_r=(60, 0, 0), arm_l=(60, 0, 0),
             fore_r=(10, 0, 0), fore_l=(10, 0, 0), body=(-12, 0, 0), head=(8, 0, 0))
    return rig


def go(root, fn, f0=FORM + 2, f1=FRAME_END):
    for f in range(1, f1 + 1, 2):
        u = max(0.0, (f - f0) / (f1 - f0))
        loc, rot = fn(u, f)
        key(root, f, loc=loc, rot=rot)


def follow_cam(tag, root, back=7.0, up=2.8, side=2.4, look_up=1.2):
    c = cam(f"Cam {tag}", (0, 0, 0), (0, 1, 0), 30)
    c.parent = root; c.location = (side, -back, up)
    d = Vector((0, 1.8, look_up)) - Vector(c.location)
    c.rotation_euler = (math.atan2(math.hypot(d.x, d.y), -d.z), 0, math.atan2(d.y, d.x) - math.pi / 2)


def meshes(root):
    return [o for o in root.children_recursive if o.type == "MESH" and " rider " not in o.name]


for bi, (tk, name) in enumerate((("F1", "flying horse"), ("F2", "baby dragon"), ("F3", "ghast, real size"), ("F4", "ghast, harnessed"))):
    bx = bi * BAY
    tag = f"FM {tk}"
    box(f"{tag} floor", (bx - 6, -4, -0.02), (bx + 6, 40, 0), FLOOR)
    root = empty(f"{tag} mount", (bx, 0, 0))
    if tk == "F1":
        T = TEX["br1"]
        b = empty(f"{tag} body", (0, 0, 1.0), root)
        box(f"{tag} barrel", (-0.32, -0.8, -0.27), (0.32, 0.8, 0.32), T, b)
        nk = empty(f"{tag} neck", (0, 0.75, 0.15), b)
        box(f"{tag} neck box", (-0.18, -0.1, 0.0), (0.18, 0.27, 0.7), T, nk)
        hd = empty(f"{tag} head", (0, 0.2, 0.65), nk)
        box(f"{tag} head box", (-0.16, -0.05, -0.16), (0.16, 0.6, 0.16), T, hd)
        for s in (-1, 1):
            box(f"{tag} eye {s}", (s * 0.165 - 0.01, 0.32, 0.02), (s * 0.165 + 0.01, 0.38, 0.08), RM, hd)
            box(f"{tag} ear {s}", (s * 0.1 - 0.03, 0.0, 0.16), (s * 0.1 + 0.03, 0.06, 0.28), T, hd)
        mane = []
        for k in range(6):
            mn = empty(f"{tag} mane {k}", (0, -0.12, 0.1 * k + 0.05), nk)
            box(f"{tag} mane lock {k}", (-0.04, -0.2, -0.04), (0.04, 0.0, 0.05), RM, mn); mane.append(mn)
        tl = empty(f"{tag} tail", (0, -0.8, 0.2), b)
        for k in range(4):
            box(f"{tag} tail lock {k}", (-0.06, -0.08 - k * 0.18, -0.06), (0.06, -k * 0.18, 0.06), RM, tl)
        box(f"{tag} saddle", (-0.34, -0.25, 0.32), (0.34, 0.2, 0.38), GR, b)
        legs = []
        for (lx, ly, ph) in ((0.2, 0.65, 0.0), (-0.2, 0.65, 0.5), (0.2, -0.65, 0.25), (-0.2, -0.65, 0.75)):
            hip = empty(f"{tag} hip {lx} {ly}", (lx, ly, -0.2), b)
            box(f"{tag} upper leg {lx} {ly}", (-0.08, -0.08, -0.42), (0.08, 0.08, 0.0), T, hip)
            kn = empty(f"{tag} knee {lx} {ly}", (0, 0, -0.42), hip)
            box(f"{tag} lower leg {lx} {ly}", (-0.065, -0.065, -0.38), (0.065, 0.065, 0.0), T, kn)
            box(f"{tag} hoof {lx} {ly}", (-0.08, -0.08, -0.42), (0.08, 0.1, -0.36), RM, kn)
            legs.append((hip, kn, ph, lx, ly))
        rider(f"{tag} rider", b, (0, -0.05, 0.38))
        period = 10
        def path(u, f):
            y = 34 * u; z = max(0.0, (u - 0.2) / 0.8) ** 1.2 * 9
            pitch = -R(12) * min(1.0, max(0.0, (u - 0.18) * 6)) * (1 - max(0.0, u - 0.8) * 3)
            return (bx, y, z), (pitch, 0, 0)
        go(root, path)
        for f in range(1, FRAME_END + 1):
            run = min(1.0, max(0.0, (f - FORM) / 8))
            for hip, kn, ph, lx, ly in legs:
                a = 2 * math.pi * (f / period + ph)
                key(hip, f, rot=(R(38 * math.sin(a) * run), 0, 0)); key(kn, f, rot=(R(-50 * max(0.0, math.sin(a + 1.2)) * run), 0, 0))
            a = 2 * math.pi * f / period
            key(b, f, loc=(0, 0, 1.0 + 0.08 * abs(math.sin(a)) * run), rot=(R(4 * math.sin(a) * run), 0, 0))
            key(nk, f, rot=(R(-20 + 10 * math.sin(a) * run), 0, 0))
            key(tl, f, rot=(R(60 * run + 10 * math.sin(a)), 0, 0))
            for k, mn in enumerate(mane):
                key(mn, f, rot=(R(-30 * run + 12 * math.sin(a - k * 0.6)), 0, 0))
        # a light pad under each hoof as it strikes the air (airborne from about u = 0.2)
        for f in range(FORM + 20, FRAME_END, 5):
            u = (f - FORM - 2) / (FRAME_END - FORM - 2)
            y = 34 * u; z = max(0.0, (u - 0.2) / 0.8) ** 1.2 * 9
            if z < 0.2:
                continue
            for s in (-1, 1):
                pad = box(f"{tag} air pad {f} {s}", (bx + s * 0.2 - 0.14, y + 0.4 * s - 0.14, z - 0.02), (bx + s * 0.2 + 0.14, y + 0.4 * s + 0.14, z + 0.02), W)
                key(pad, 1, sc=0.0001); key(pad, f - 1, sc=0.0001); key(pad, f, sc=1.0); key(pad, f + 6, sc=(2.2, 2.2, 0.3)); key(pad, f + 7, sc=0.0001)
    elif tk == "F2":
        T = TEX["x3d1"]
        b = empty(f"{tag} body", (0, 0, 0.9), root)
        box(f"{tag} belly", (-0.42, -0.5, -0.35), (0.42, 0.55, 0.38), T, b)
        box(f"{tag} belly plate", (-0.3, -0.4, -0.38), (0.3, 0.45, -0.33), RM, b)
        nk = empty(f"{tag} neck", (0, 0.5, 0.15), b)
        box(f"{tag} neck box", (-0.2, 0.0, -0.18), (0.2, 0.3, 0.2), T, nk)
        hd = empty(f"{tag} head", (0, 0.3, 0.05), nk)
        box(f"{tag} skull", (-0.3, -0.05, -0.22), (0.3, 0.45, 0.28), T, hd)
        box(f"{tag} snout", (-0.18, 0.45, -0.18), (0.18, 0.7, 0.08), T, hd)
        jaw = empty(f"{tag} jaw", (0, 0.45, -0.18), hd)
        box(f"{tag} jaw box", (-0.15, 0.0, -0.08), (0.15, 0.24, 0.0), T, jaw)
        for s in (-1, 1):
            box(f"{tag} eye {s}", (s * 0.3 - 0.01, 0.2, 0.04), (s * 0.3 + 0.01, 0.34, 0.16), RM, hd)
            box(f"{tag} nub horn {s}", (s * 0.15 - 0.05, -0.1, 0.24), (s * 0.15 + 0.05, 0.02, 0.38), RM, hd)
        tail = []; prev = b; pos = (0, -0.5, 0.0)
        for i in range(4):
            s_ = empty(f"{tag} tail {i}", pos, prev); w_ = 0.18 - i * 0.035
            box(f"{tag} tail box {i}", (-w_, -0.28, -w_), (w_, 0, w_), T, s_); tail.append(s_); prev = s_; pos = (0, -0.27, 0)
        box(f"{tag} tail tip", (-0.05, -0.18, -0.02), (0.05, 0.0, 0.08), RM, prev)
        wings = []
        for s in (-1, 1):
            wr = empty(f"{tag} wing {s}", (s * 0.42, 0.15, 0.3), b)
            box(f"{tag} wing spar {s}", (0, -0.03, -0.03) if s > 0 else (-0.75, -0.03, -0.03), (0.75, 0.03, 0.03) if s > 0 else (0, 0.03, 0.03), RM, wr)
            for k in range(3):
                x0, x1 = k * 0.25, (k + 1) * 0.25
                if s < 0:
                    x0, x1 = -x1, -x0
                box(f"{tag} wing web {s} {k}", (x0, -0.55 + k * 0.1, -0.012), (x1, 0, 0.012), T, wr)
            wings.append((wr, s))
        for s in (-1, 1):
            for y in (0.3, -0.3):
                lg = empty(f"{tag} leg {s} {y}", (s * 0.3, y, -0.35), b)
                box(f"{tag} leg box {s} {y}", (-0.09, -0.09, -0.32), (0.09, 0.1, 0.0), T, lg)
                key(lg, FORM + 10, rot=(0, 0, 0)); key(lg, FORM + 16, rot=(R(-60), 0, 0))
        rider(f"{tag} rider", b, (0, -0.05, 0.4), legs_down=True)
        def path(u, f):
            y = 24 * u + 6 * u * u
            z = (0.0 if u < 0.08 else min(1.0, (u - 0.08) / 0.5) ** 0.8 * 7)
            bank = R(28) * math.sin(max(0.0, u - 0.6) / 0.4 * math.pi)
            x = bx + 3.0 * math.sin(max(0.0, u - 0.6) / 0.4 * math.pi)
            return (x, y, z), (-R(14) * min(1.0, u * 6) * (1 - u), bank, -bank * 0.4)
        go(root, path)
        for f in range(1, FRAME_END + 1):
            fly = min(1.0, max(0.0, (f - FORM) / 6))
            glide = 70 <= f <= 90
            a = 2 * math.pi * f / 7                                   # fast little flaps
            for wr, s in wings:
                ang = -12 if glide else -10 - 45 * math.sin(a) * fly
                key(wr, f, rot=(0, R(s * ang), 0))
            for i, s_ in enumerate(tail):
                key(s_, f, rot=(R(4 * math.sin(a * 0.4 - i * 0.6)), 0, R(12 * math.sin(a * 0.3 - i * 0.7))))
            key(nk, f, rot=(R(6 * math.sin(a * 0.5)), 0, 0)); key(jaw, f, rot=(R(-10 * max(0.0, math.sin(a * 0.15))), 0, 0))
            key(b, f, loc=(0, 0, 0.9 + (0.0 if glide else 0.06 * math.sin(a) * fly)))
    else:
        # the ghast: body is the real model's 16-pixel cube scaled to 4 blocks; nine tentacles in a 3 x 3 grid below
        T = TEX["w1" if tk == "F3" else "h1"]
        b = empty(f"{tag} body", (0, 0, 4.2), root)
        BS = 4.0
        box(f"{tag} real ghast (reference)", (-BS / 2 - 0.01, -BS / 2 - 0.01, -0.01), (BS / 2 + 0.01, BS / 2 + 0.01, BS + 0.01), GHOST, b)
        shell = 0.12                                           # the construct sits just outside the real model's cube
        for nm, a, c in (("front", (-BS / 2, BS / 2, 0), (BS / 2, BS / 2 + shell, BS)), ("back", (-BS / 2, -BS / 2 - shell, 0), (BS / 2, -BS / 2, BS)),
                         ("left", (-BS / 2 - shell, -BS / 2, 0), (-BS / 2, BS / 2, BS)), ("right", (BS / 2, -BS / 2, 0), (BS / 2 + shell, BS / 2, BS)),
                         ("top", (-BS / 2 - shell, -BS / 2 - shell, BS), (BS / 2 + shell, BS / 2 + shell, BS + shell)),
                         ("bottom", (-BS / 2 - shell, -BS / 2 - shell, -shell), (BS / 2 + shell, BS / 2 + shell, 0))):
            box(f"{tag} shell {nm}", a, c, T, b)
        for k in range(4):                                     # glowing edges
            sx, sy = (-1, -1, 1, 1)[k], (-1, 1, -1, 1)[k]
            box(f"{tag} edge {k}", (sx * (BS / 2 + shell) - 0.05, sy * (BS / 2 + shell) - 0.05, 0), (sx * (BS / 2 + shell) + 0.05, sy * (BS / 2 + shell) + 0.05, BS), RM, b)
        # the face (front, +Y): two eyes and a mouth, built on the shell
        fy = BS / 2 + shell
        for s in (-1, 1):
            box(f"{tag} eye {s}", (s * 0.9 - 0.4, fy, 2.2), (s * 0.9 + 0.4, fy + 0.06, 2.8), W, b)
            if tk == "F4":
                box(f"{tag} goggle {s}", (s * 0.9 - 0.55, fy + 0.06, 2.05), (s * 0.9 + 0.55, fy + 0.2, 2.95), GL, b)
                box(f"{tag} goggle rim {s}", (s * 0.9 - 0.58, fy + 0.2, 2.02), (s * 0.9 + 0.58, fy + 0.24, 2.1), RM, b)
        box(f"{tag} mouth", (-0.5, fy, 1.2), (0.5, fy + 0.06, 1.5), RM, b)
        tents = []
        for i in range(3):
            for j in range(3):
                x = (i - 1) * 1.25; y = (j - 1) * 1.25
                L = 1.4 + ((i * 3 + j) * 7 % 5) * 0.35           # varied lengths like the real tentacles
                prev = empty(f"{tag} tentacle {i}{j}", (x, y, -shell), b); chain = [prev]
                n = 4
                for k in range(n):
                    seg = box(f"{tag} tentacle seg {i}{j} {k}", (-0.2, -0.2, -L / n), (0.2, 0.2, 0.0), T if k < n - 1 else RM, prev)
                    nxt = empty(f"{tag} tentacle joint {i}{j} {k}", (0, 0, -L / n), prev); chain.append(nxt); prev = nxt
                tents.append((chain, i * 3 + j))
        if tk == "F4":                                         # harness frame on top with four seats
            top = BS + shell
            for s in (-1, 1):
                box(f"{tag} harness rail {s}", (s * 1.7 - 0.06, -1.9, top), (s * 1.7 + 0.06, 1.9, top + 0.2), RM, b)
                box(f"{tag} harness strap {s}", (-2.15, s * 1.2 - 0.08, -0.2), (2.15, s * 1.2 + 0.08, top + 0.06), GR, b)
            seats = [(-0.8, 0.8), (0.8, 0.8), (-0.8, -0.8), (0.8, -0.8)]
            for k, (sx, sy) in enumerate(seats):
                box(f"{tag} seat {k}", (sx - 0.35, sy - 0.3, top), (sx + 0.35, sy + 0.3, top + 0.12), GR, b)
                box(f"{tag} seat back {k}", (sx - 0.35, sy - 0.32, top), (sx + 0.35, sy - 0.26, top + 0.5), GL, b)
                rider(f"{tag} rider {k}", b, (sx, sy, top + 0.12))
        else:
            rider(f"{tag} rider", b, (0, 0.3, BS + shell))
        def path(u, f):
            y = 16 * u; z = (0.0 if u < 0.05 else 3.5 * min(1.0, (u - 0.05) / 0.6) ** 0.9)
            return (bx, y, z + 0.15 * math.sin(f * 0.12)), (0, 0, R(4) * math.sin(f * 0.05))
        go(root, path)
        for f in range(1, FRAME_END + 1, 2):
            moving = min(1.0, max(0.0, (f - FORM) / 10))
            for chain, idx in tents:
                for k, jt in enumerate(chain[:-1]):
                    key(jt, f, rot=(R((10 + 25 * moving) * (k > 0) * 0.6 + 12 * math.sin(f * 0.15 + idx + k * 0.8)),
                                    R(10 * math.sin(f * 0.12 + idx * 1.7 + k)), 0))
    parts = meshes(root)
    src = (bx, 0.0, 2.0)
    form_in([o for o in parts if "real ghast" not in o.name], 2, FORM, src, CM["pix"], rng, tag, order_axis=2 if tk in ("F3", "F4") else 1, stream=0.25)
    follow_cam(f"{tk}", root, back=8.0 if tk in ("F1", "F2") else 14.0, up=3.0 if tk in ("F1", "F2") else 7.0, side=2.4 if tk in ("F1", "F2") else 5.0,
               look_up=1.2 if tk in ("F1", "F2") else 4.5)
    cam(f"Cam {tk} side", (bx + 16, 14, 7.0), (bx, 14, 4.0), 30)
    label(f"{tk}  {name}", (bx, -2.0, 6.5 if tk in ("F3", "F4") else 3.2), LBL, 0.4, rot=(R(90), 0, 0))
    print(tk, "built", flush=True)
cam("Cam all", (1.5 * BAY, -26.0, 14.0), (1.5 * BAY, 10, 3.0), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam F2", 1, (0.35, 0.45, 0.6), 3.0


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
