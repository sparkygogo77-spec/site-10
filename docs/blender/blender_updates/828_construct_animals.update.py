# Pass 828: construct textures on animals - a pig and a warden (Chat C, 2026-10-15, range 800-899).
# J: "hex suits are good, stretch the textures over some animals too, just the construct textures and i want more
# example designs over a warden and pig".
# Each animal keeps the vanilla proportions (pixel boxes: pig body 10x16x8, head 8x8x8, legs 4x6x4; warden body
# 18x21x11, head 16x16x10 with two tendrils, arms 8x28x8, legs 6x13x6) and wears only the construct textures from the
# texture library, 88% opaque, stretched across each face. They walk on the spot and turn slowly so every side shows.
# Pigs:    P1 BR1 bricks          P2 H1 hex             P3 W1 weave            P4 X3D1 ripples
#          P5 two-tone (hex body, brick head and legs)  P6 hex with glowing seam lines and a glowing snout
#          P7 R2 in red with gold hooves
# Wardens: R1 H1 hex             R2 BR1 bricks         R3 X3D1 ripples        R4 W1 weave
#          R5 hex with a glowing chest heart that pulses, glowing tendril rims and rib lines
#          R6 two-tone: ripple body, brick arms and legs, weave head, heart pulse
# Cameras "Cam <key>", "Cam row pigs", "Cam row wardens", "Cam all". Builds LanternLive\constructs\construct_animals.blend.
SCENE_NAME = "Construct Animals"
OUT_REL = "constructs/construct_animals.blend"
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


FRAME_END = 160
FLOOR = mat("CA floor", (0.18, 0.2, 0.2), rough=0.9)
LBL = mat("CA label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(828)
CM = cmats("CA", "green")
_tm = {}


def T(look, corps="green", uvt=0.5):
    k = (look, corps)
    if k not in _tm:
        _tm[k] = strip_mat(f"CA {look} {corps}", strip_image(corps, look), 4, emit=1.2, alpha=0.88)
    return _tm[k]


def seam_mat(corps):
    return mat(f"CA seam {corps}", CORPS[corps], emit=3.0)


def turn(root, f0=1, f1=FRAME_END):
    _p = bpy.context.preferences.edit; _o = _p.keyframe_new_interpolation_type; _p.keyframe_new_interpolation_type = "LINEAR"
    key(root, f0, rot=(0, 0, R(-30))); key(root, f1, rot=(0, 0, R(-30 + 360)))
    _p.keyframe_new_interpolation_type = _o


def pig(tag, loc, mats, extra=None):
    """Vanilla pig proportions (1 px = 1/16 block). mats: dict body/head/legs/snout -> material."""
    root = empty(f"{tag} root", loc); turner = empty(f"{tag} turner", (0, 0, 0), root)
    q = P
    body = empty(f"{tag} body", (0, 0, 12 * q), turner)
    box(f"{tag} body box", (-5 * q, -8 * q, -4 * q), (5 * q, 8 * q, 4 * q), mats["body"], body, uvt=1.0)
    head = empty(f"{tag} head", (0, 8 * q, 2 * q), body)
    box(f"{tag} head box", (-4 * q, 0, -4 * q), (4 * q, 8 * q, 4 * q), mats["head"], head, uvt=0.5)
    box(f"{tag} snout", (-2 * q, 8 * q, -3 * q), (2 * q, 9 * q, 0), mats["snout"], head, uvt=0.25)
    for sx in (-1, 1):
        box(f"{tag} eye {sx}", (sx * 3 * q - 0.5 * q, 8.02 * q, 1 * q), (sx * 3 * q + 0.5 * q, 8.1 * q, 2 * q), CM["rim"], head)
    legs = []
    for lx, ly, ph in ((-3, 5, 0), (3, 5, math.pi), (-3, -5, math.pi), (3, -5, 0)):
        lg = empty(f"{tag} leg {lx} {ly}", (lx * q, ly * q, -4 * q), body)
        box(f"{tag} leg box {lx} {ly}", (-2 * q, -2 * q, -6 * q), (2 * q, 2 * q, 0), mats["legs"], lg, uvt=0.5)
        box(f"{tag} hoof {lx} {ly}", (-2.05 * q, -2.05 * q, -6.05 * q), (2.05 * q, 2.05 * q, -5.2 * q), mats.get("hoof", mats["legs"]), lg)
        legs.append((lg, ph))
    if extra:
        extra(tag, body, head)
    for f in range(1, FRAME_END + 1, 2):
        a = f * 0.35
        for lg, ph in legs:
            key(lg, f, rot=(R(28 * math.sin(a + ph)), 0, 0))
        key(head, f, rot=(R(4 * math.sin(a * 0.5)), 0, 0))
    turn(turner)
    return root


def warden(tag, loc, mats, extra=None):
    """Vanilla warden proportions: body 18x21x11, head 16x16x10 with tendrils, arms 8x28x8, legs 6x13x6."""
    root = empty(f"{tag} root", loc); turner = empty(f"{tag} turner", (0, 0, 0), root)
    q = P
    hips = empty(f"{tag} hips", (0, 0, 13 * q), turner)
    body = empty(f"{tag} body", (0, 0, 0), hips)
    box(f"{tag} body box", (-9 * q, -5.5 * q, 0), (9 * q, 5.5 * q, 21 * q), mats["body"], body, uvt=1.2)
    head = empty(f"{tag} head", (0, 0, 21 * q), body)
    box(f"{tag} head box", (-8 * q, -5 * q, 0), (8 * q, 5 * q, 16 * q), mats["head"], head, uvt=1.0)
    tendrils = []
    for sx in (-1, 1):
        td = empty(f"{tag} tendril {sx}", (sx * 8 * q, 0, 12 * q), head)
        box(f"{tag} tendril box {sx}", (0, -0.5 * q, -2 * q) if sx > 0 else (-16 * q, -0.5 * q, -2 * q),
            (16 * q, 0.5 * q, 10 * q) if sx > 0 else (0, 0.5 * q, 10 * q), mats.get("tendril", mats["head"]), td, uvt=0.6)
        tendrils.append((td, sx))
    arms, legs = [], []
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 13 * q, 0, 19 * q), body)
        box(f"{tag} arm box {sx}", (-4 * q, -4 * q, -28 * q), (4 * q, 4 * q, 0), mats["arms"], sh, uvt=1.0)
        arms.append((sh, sx))
        lg = empty(f"{tag} leg {sx}", (sx * 5.9 * q, 0, 0), hips)
        box(f"{tag} leg box {sx}", (-3 * q, -3 * q, -13 * q), (3 * q, 3 * q, 0), mats["legs"], lg, uvt=0.8)
        legs.append((lg, sx))
    if extra:
        extra(tag, body, head, tendrils)
    for f in range(1, FRAME_END + 1, 2):
        a = f * 0.18
        for sh, sx in arms:
            key(sh, f, rot=(R(18 * math.sin(a + (0 if sx > 0 else math.pi))), 0, 0))
        for lg, sx in legs:
            key(lg, f, rot=(R(20 * math.sin(a + (math.pi if sx > 0 else 0))), 0, 0))
        key(hips, f, loc=(0, 0, 13 * q + 0.03 * abs(math.sin(a))))
        for td, sx in tendrils:
            key(td, f, rot=(0, R(sx * 12 * math.sin(a * 1.3)), 0))
        key(head, f, rot=(R(3 * math.sin(a)), 0, 0))
    turn(turner)
    return root


def pig_seams(corps):
    sm = seam_mat(corps)
    def extra(tag, body, head):
        q = P
        for y in (-5, -1, 3):
            box(f"{tag} seam {y}", (-5.1 * q, y * q, -4.1 * q), (5.1 * q, y * q + 0.4 * q, 4.1 * q), sm, body)
        box(f"{tag} spine seam", (-0.3 * q, -8.05 * q, 4.0 * q), (0.3 * q, 8.05 * q, 4.15 * q), sm, body)
        box(f"{tag} snout glow", (-2.05 * q, 8.95 * q, -3.05 * q), (2.05 * q, 9.1 * q, 0.05 * q), sm, head)
    return extra


def warden_heart(corps, ribs=True, tendril_rims=True):
    sm = seam_mat(corps)
    hm = mat(f"CA heart {corps}", CORPS[corps], emit=3.5)
    def extra(tag, body, head, tendrils):
        q = P
        heart = box(f"{tag} chest heart", (-3 * q, -5.8 * q, 11 * q), (3 * q, -5.5 * q, 17 * q), hm, body)
        anim_emit(hm, [(f, 2.0 + 2.5 * max(0.0, math.sin(f * 0.3)) ** 6) for f in range(1, FRAME_END + 1, 2)])
        if ribs:
            for k in range(4):
                z = 3 + k * 2.2
                box(f"{tag} rib {k}", (-8 * q, -5.7 * q, z * q), (8 * q, -5.5 * q, (z + 0.6) * q), sm, body)
        if tendril_rims:
            for td, sx in tendrils:
                x0, x1 = (0, 16 * q) if sx > 0 else (-16 * q, 0)
                box(f"{tag} tendril rim {sx}", (x0, -0.6 * q, 9.4 * q), (x1, 0.6 * q, 10.1 * q), sm, td)
    return extra


PIGS = [("P1", "BR1 bricks", dict(body=T("br1"), head=T("br1"), legs=T("br1"), snout=T("br1")), None),
        ("P2", "H1 hex", dict(body=T("h1"), head=T("h1"), legs=T("h1"), snout=T("h1")), None),
        ("P3", "W1 weave", dict(body=T("w1"), head=T("w1"), legs=T("w1"), snout=T("w1")), None),
        ("P4", "X3D1 ripples", dict(body=T("x3d1"), head=T("x3d1"), legs=T("x3d1"), snout=T("x3d1")), None),
        ("P5", "two-tone: hex body, brick head and legs", dict(body=T("h1"), head=T("br1"), legs=T("br1"), snout=T("h1")), None),
        ("P6", "hex with glowing seams and snout", dict(body=T("h1"), head=T("h1"), legs=T("h1"), snout=T("h1")), pig_seams("green")),
        ("P7", "R2 in red, gold hooves", dict(body=T("r2", "red"), head=T("r2", "red"), legs=T("r2", "red"), snout=T("r2", "red"),
                                               hoof=mat("CA gold hoof", (1.0, 0.75, 0.15), emit=1.5)), None)]
WARDENS = [("R1", "H1 hex", dict(body=T("h1"), head=T("h1"), arms=T("h1"), legs=T("h1")), None),
           ("R2", "BR1 bricks", dict(body=T("br1"), head=T("br1"), arms=T("br1"), legs=T("br1")), None),
           ("R3", "X3D1 ripples", dict(body=T("x3d1"), head=T("x3d1"), arms=T("x3d1"), legs=T("x3d1")), None),
           ("R4", "W1 weave", dict(body=T("w1"), head=T("w1"), arms=T("w1"), legs=T("w1")), None),
           ("R5", "hex, pulsing chest heart, glowing tendrils and ribs", dict(body=T("h1"), head=T("h1"), arms=T("h1"), legs=T("h1")),
            warden_heart("green")),
           ("R6", "two-tone: ripple body, brick limbs, weave head, heart", dict(body=T("x3d1"), head=T("w1"), arms=T("br1"), legs=T("br1"),
                                                                             tendril=T("w1")), warden_heart("green", ribs=False))]
for i, (k, nm, ms, ex) in enumerate(PIGS):
    x = i * 2.4
    box(f"CA {k} pad", (x - 1.0, -1.0, -0.02), (x + 1.0, 1.0, 0), FLOOR)
    pig(f"CA {k}", (x, 0, 0), ms, ex)
    label(f"{k}  {nm}", (x, -1.1, 1.45), LBL, 0.11)
    cam(f"Cam {k}", (x + 1.4, -2.2, 1.3), (x, 0, 0.6), 35)
for i, (k, nm, ms, ex) in enumerate(WARDENS):
    x = i * 4.5
    box(f"CA {k} pad", (x - 2.0, 6.0, -0.02), (x + 2.0, 10.0, 0), FLOOR)
    warden(f"CA {k}", (x, 8.0, 0), ms, ex)
    label(f"{k}  {nm}", (x, 5.6, 3.6), LBL, 0.18)
    cam(f"Cam {k}", (x + 2.8, 3.4, 2.6), (x, 8.0, 1.8), 35)
cam("Cam row pigs", (7.2, -13.0, 3.5), (7.2, 0, 0.5), 26)
cam("Cam row wardens", (11.25, -11.0, 6.0), (11.25, 8.0, 1.8), 24)
cam("Cam all", (11.0, -18.0, 9.0), (11.0, 4.0, 1.0), 30)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam row wardens", 40, (0.3, 0.38, 0.5), 3.0


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
