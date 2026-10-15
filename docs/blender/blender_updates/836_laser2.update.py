# Pass 836: laser round 2 - more of L1, L2 and L3, and the game's twin helix made into a proper laser (Chat C, 2026-10-15).
# J on 834: "L1 -3 need more variations, l0 can be improved laser". L4 (charged) waits for his rating.
# Same timeline and kit as 834: fire 10, at the wall by 12, held to 40, thinned out by 44; core + camera-facing glow +
# haze + flares at the ring and the hit; saturated green, never white. The ring sits on the punching face.
#   L0 improved (the game's twin helix, kept as the idea but made crisp):
#     H1 crisp twin helix: two thin solid strands with a soft sheath each, opening out over the first 1.5 blocks, spinning
#     H2 helix round a lance: L1's lance down the middle, the twin strands wound round it
#     H3 braid: three strands wound tight and fast round a thin core
#   L1 hard-light lance:  N1 needle (thinner, longer streaks, faster)   N2 layered (two glows flowing at different speeds)
#                         N3 crackle (short broken streaks, flickering core)
#   L2 construct lance:   C1 weave flowing   C2 brick flowing   C3 hex on a see-through tube round the core, streak glow outside
#   L3 pulse lance:       P1 rapid pulses   P2 comet packets (sparse long bright packets)   P3 pulses + three O4 rims
# Cameras "Cam <take> close" (third person), "Cam <take> eye" (first person, MC FOV), "Cam <take> side", "Cam all".
# Builds LanternLive\combat\laser2.blend.
SCENE_NAME = "Laser 2"
OUT_REL = "combat/laser2.blend"
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



# ------------------------------------------------------------------ laser kit (832+): how the game would draw a laser.
# Everything is flat, camera-independent and cheap: a thin solid core, a "star" of 3 crossed quads along the beam
# (in game: ONE quad turned to the camera) whose shader is a soft bright-middle falloff times a pattern that scrolls
# toward the target, a flare ball at the ring and at the hit. Saturated green, never white.
GREEN = (0.03, 1.0, 0.22)


def mc_fov(c):
    """Sensor Fit Vertical (Minecraft's FOV is vertical); lens driven by the scene's MC FOV: lens = 12 / tan(fov / 2)."""
    if "MC FOV" not in scene.keys():
        scene["MC FOV"] = 70.0
        try:
            scene.id_properties_ui("MC FOV").update(min=30.0, max=110.0, description="Minecraft FOV (vertical) for every first-person camera")
        except Exception:
            pass
    c.data.sensor_fit = "VERTICAL"; c.data.sensor_height = 24.0; c.data.clip_start = 0.02
    fc = c.data.driver_add("lens"); d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "fov"; v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = '["MC FOV"]'
    d.expression = "12 / tan(radians(fov) / 2)"


def _frame_value(N, mul):
    n = N.new("ShaderNodeValue"); fc = n.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"; fc.driver.expression = f"frame*{mul}"
    return n


def laser_mat(name, pattern="streak", flow=0.6, strength=2.4, alpha=0.85, rgb=GREEN, falloff=2.2, lib=None, tile_u=1.0,
              pulse_len=2.5, pulse_cut=0.6, streak_len=0.35, streak_x=9.0):
    """u (0..1) runs across the ribbon, v along it in blocks. pattern: streak (noise drawn out along the beam), pulse
    (bright bands running to the target), lib (one of J's construct strips flowing), plain. flow in blocks a tick."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); uv = N.new("ShaderNodeUVMap"); uv.uv_map = "uv"
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs["UV"], sep.inputs[0])
    a = N.new("ShaderNodeMath"); a.operation = "MULTIPLY_ADD"; a.inputs[1].default_value = 2.0; a.inputs[2].default_value = -1.0
    L.new(sep.outputs[0], a.inputs[0])
    ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(a.outputs[0], ab.inputs[0])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L.new(ab.outputs[0], inv.inputs[1])
    fall = N.new("ShaderNodeMath"); fall.operation = "POWER"; fall.inputs[1].default_value = falloff; L.new(inv.outputs[0], fall.inputs[0])
    tk = _frame_value(N, flow)
    vflow = N.new("ShaderNodeMath"); vflow.operation = "SUBTRACT"; L.new(sep.outputs[1], vflow.inputs[0]); L.new(tk.outputs[0], vflow.inputs[1])
    pat = None
    if pattern == "streak":
        cx = N.new("ShaderNodeMath"); cx.operation = "MULTIPLY"; cx.inputs[1].default_value = streak_x; L.new(sep.outputs[0], cx.inputs[0])
        cy = N.new("ShaderNodeMath"); cy.operation = "MULTIPLY"; cy.inputs[1].default_value = streak_len; L.new(vflow.outputs[0], cy.inputs[0])
        cmb = N.new("ShaderNodeCombineXYZ"); L.new(cx.outputs[0], cmb.inputs[0]); L.new(cy.outputs[0], cmb.inputs[1])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 3.0
        L.new(cmb.outputs[0], nz.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.7
        mr.inputs["To Min"].default_value = 0.35; mr.inputs["To Max"].default_value = 1.0; L.new(nz.outputs["Fac"], mr.inputs["Value"])
        pat = mr.outputs[0]
    elif pattern == "pulse":
        sw = N.new("ShaderNodeMath"); sw.operation = "MULTIPLY"; sw.inputs[1].default_value = 2 * math.pi / pulse_len; L.new(vflow.outputs[0], sw.inputs[0])
        sn = N.new("ShaderNodeMath"); sn.operation = "SINE"; L.new(sw.outputs[0], sn.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = pulse_cut; mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = 0.45; mr.inputs["To Max"].default_value = 1.4; L.new(sn.outputs[0], mr.inputs["Value"])
        pat = mr.outputs[0]
    elif pattern == "lib":
        im = strip_image("green", lib)
        n_fr = max(1, im.size[1] // max(1, im.size[0]))
        cu_ = N.new("ShaderNodeMath"); cu_.operation = "MULTIPLY"; cu_.inputs[1].default_value = tile_u; L.new(sep.outputs[0], cu_.inputs[0])
        cv_ = N.new("ShaderNodeMath"); cv_.operation = "MULTIPLY"; cv_.inputs[1].default_value = 2.0; L.new(vflow.outputs[0], cv_.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"; L.new(cv_.outputs[0], fr.inputs[0])
        fv = N.new("ShaderNodeMath"); fv.operation = "DIVIDE"; fv.inputs[1].default_value = n_fr; L.new(fr.outputs[0], fv.inputs[0])
        cmb = N.new("ShaderNodeCombineXYZ"); L.new(cu_.outputs[0], cmb.inputs[0]); L.new(fv.outputs[0], cmb.inputs[1])
        tx = N.new("ShaderNodeTexImage"); tx.image = im; tx.interpolation = "Closest"; L.new(cmb.outputs[0], tx.inputs["Vector"])
        bw = N.new("ShaderNodeRGBToBW"); L.new(tx.outputs["Color"], bw.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.3; mr.inputs["To Max"].default_value = 1.5
        L.new(bw.outputs[0], mr.inputs["Value"])
        pat = mr.outputs[0]
    k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = alpha; L.new(fall.outputs[0], k.inputs[0])
    if pat is not None:
        k2 = N.new("ShaderNodeMath"); k2.operation = "MULTIPLY"; L.new(k.outputs[0], k2.inputs[0]); L.new(pat, k2.inputs[1])
        mn = N.new("ShaderNodeMath"); mn.operation = "MINIMUM"; mn.inputs[1].default_value = 0.99; L.new(k2.outputs[0], mn.inputs[0])
        k = mn
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1); em.inputs["Strength"].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(k.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def star(name, L, width, m, parent, v0=0.0, n=3):
    """n quads crossed round +Y, length L, width `width`; UV u across 0..1, v along in blocks (starting at v0)."""
    vs, fs, uvs = [], [], []
    for i in range(n):
        a = math.pi * i / n
        dx, dz = math.cos(a) * width / 2, math.sin(a) * width / 2
        b = len(vs)
        vs += [(-dx, 0, -dz), (dx, 0, dz), (dx, L, dz), (-dx, L, -dz)]
        uvs += [(0, v0), (1, v0), (1, v0 + L), (0, v0 + L)]
        fs.append((b, b + 1, b + 2, b + 3))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    uvl = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    o = link(bpy.data.objects.new(name, me)); o.parent = parent
    return o


def flare_mat(name, strength=2.2, rgb=GREEN):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    sc_ = N.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs["Scale"].default_value = 2.0
    L.new(tc.outputs["Object"], sc_.inputs[0])
    gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; L.new(sc_.outputs[0], gr.inputs["Vector"])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.6; L.new(gr.outputs["Fac"], pw.inputs[0])
    k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = 0.8; L.new(pw.outputs[0], k.inputs[0])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1); em.inputs["Strength"].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(k.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def flare(name, m, loc, parent=None):
    """A soft ball of light seen the same from every side: three crossed unit quads with a radial falloff (in game: one
    camera-facing sprite)."""
    vs, fs = [], []
    for ax in range(3):
        b = len(vs)
        for (p, q) in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
            v = [0.0, 0.0, 0.0]; v[(ax + 1) % 3] = p; v[(ax + 2) % 3] = q; vs.append(tuple(v))
        fs.append((b, b + 1, b + 2, b + 3))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    if parent is not None:
        o.parent = parent
    return o


def ring_on_fist(tag, parent, end_z, px, M, back="x"):
    """The jar's ring placement: on the punching face (end_z, facing -Z), 1 px in from the back of the hand, over the
    middle finger. Gold frame, green face standing out, a band over the back."""
    mt = empty(f"{tag} ring mount", (0, 0, end_z), parent)
    if back == "y":
        mt.rotation_euler = (0, 0, math.radians(90))
    c = 0.6 * px
    box(f"{tag} ring band", (1.95 * px, -0.55 * px, 0), (2.25 * px, 0.55 * px, 1.4 * px), M["gold"], mt)
    box(f"{tag} ring frame", (c - 1.25 * px, -1.25 * px, -0.45 * px), (c + 1.25 * px, 1.25 * px, 0), M["gold"], mt)
    box(f"{tag} ring face", (c - 0.95 * px, -0.95 * px, -1.0 * px), (c + 0.95 * px, 0.95 * px, -0.4 * px), M["ring"], mt)
    return empty(f"{tag} ring point", (c, 0, -1.15 * px), mt)


def jar_ring(tag, rig, M):
    """Move make_player's ring from the back of the hand to the punching face (jar placement)."""
    for nm in ("ring band", "ring face", "ring point"):
        o = bpy.data.objects.get(f"{tag} {nm}")
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    rig["ring_pt"] = ring_on_fist(tag + " jar", rig["fore_r"], -6 * P, P, M, "x")

FRAME_END = 60
BAY = 5.0
F_FIRE, F_HIT, F_END, F_GONE = 10, 12, 40, 44
FLOOR = mat("LZ2 floor", (0.16, 0.17, 0.19), rough=0.9)
WALL = mat("LZ2 wall", (0.3, 0.31, 0.33), rough=0.9)
LBL = mat("LZ2 label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(836)
CM = cmats("LZ2", "green")
CORE = mat("LZ2 core", (0.1, 1.0, 0.3), emit=1.9)
STRAND = mat("LZ2 strand", (0.08, 1.0, 0.28), emit=2.0)
SHEATH = mat("LZ2 strand sheath", GREEN, emit=1.1, alpha=0.3, rough=0.2)
FLARE = flare_mat("LZ2 flare")
SPARK = mat("LZ2 spark", (0.1, 1.0, 0.3), emit=3.0)
HAZE = laser_mat("LZ2 haze", "plain", strength=1.0, alpha=0.22, falloff=3.0)       # check: the haze hid the patterns


def life(o, w=1.0, wobble=0.0):
    key(o, 1, sc=(0.0001, 0.0001, 0.0001)); key(o, F_FIRE - 1, sc=(0.0001, 0.0001, 0.0001))
    key(o, F_FIRE, sc=(w, 0.02, w)); key(o, F_HIT, sc=(w, 1, w))
    for f in range(F_HIT + 1, F_END, 2):
        ww = w * (1 + wobble * math.sin(f * 2.3 + rng.uniform(0, 0.8)))
        key(o, f, sc=(ww, 1, ww))
    key(o, F_END, sc=(w, 1, w)); key(o, F_GONE, sc=(0.05 * w, 1, 0.05 * w)); key(o, F_GONE + 1, sc=(0.0001, 0.0001, 0.0001))


def pop(o, s0, s1, f0, hold):
    key(o, 1, sc=0.0001); key(o, f0 - 1, sc=0.0001); key(o, f0, sc=s0); key(o, f0 + 2, sc=s1)
    for f in range(f0 + 4, hold, 3):
        key(o, f, sc=s1 * (0.85 + 0.15 * math.sin(f * 1.9)))
    key(o, hold + 3, sc=0.0001)


def helix_curve(name, parent, L, r, twist, phase, bevel, m, emerge=1.5):
    """One smooth strand along +Y (a bevelled curve), radius opening from 0 to r over `emerge` blocks; it grows out of
    the ring with bevel_factor_end 0 -> 1 over F_FIRE..F_HIT (in game: a ribbon strip per strand)."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); n = int(L / 0.08) + 1; sp.points.add(n - 1)
    for i in range(n):
        y = L * i / (n - 1); a = phase + y * twist; rr = r * min(1.0, y / emerge)
        sp.points[i].co = (rr * math.cos(a), y, rr * math.sin(a), 1)
    cu.bevel_factor_mapping_end = "SPLINE"; cu.materials.append(m)
    o = link(bpy.data.objects.new(name, cu)); o.parent = parent
    for f, v in ((1, 0.0), (F_FIRE, 0.0), (F_HIT, 1.0)):
        cu.bevel_factor_end = v; cu.keyframe_insert("bevel_factor_end", frame=f)
    key(o, 1, sc=1.0); key(o, F_END, sc=1.0); key(o, F_GONE, sc=(0.05, 1, 0.05)); key(o, F_GONE + 1, sc=0.0001)
    return o


def strands(tag, root, L, n, r, twist, spin, core_b=0.016, sheath_b=0.05):
    h = empty(f"{tag} strands", (0, 0, 0), root); h.rotation_mode = "XYZ"
    for s in range(n):
        ph = 2 * math.pi * s / n
        helix_curve(f"{tag} strand {s}", h, L, r, twist, ph, core_b, STRAND)
        helix_curve(f"{tag} strand sheath {s}", h, L, r, twist, ph, sheath_b, SHEATH)
    for f in range(F_FIRE, F_GONE + 1, 2):
        key(h, f, rot=(0, (f - F_FIRE) * spin, 0))


def tex_tube(name, r, L, m, parent, n=16):
    segs = max(2, int(L / 0.5)); vs, uvs, fs = [], [], []
    for i in range(segs + 1):
        y = L * i / segs
        for k in range(n + 1):
            a = 2 * math.pi * k / n
            vs.append((r * math.cos(a), y, r * math.sin(a))); uvs.append((k / n * 2, y))
    W = n + 1
    for i in range(segs):
        for k in range(n):
            fs.append((i * W + k, i * W + k + 1, (i + 1) * W + k + 1, (i + 1) * W + k))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    uvl = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    o = link(bpy.data.objects.new(name, me)); o.parent = parent
    return o


def rims(tag, root, L, n, r=0.1, twist=0.8, spin=0.12):
    h = empty(f"{tag} rims", (0, 0, 0), root); h.rotation_mode = "XYZ"
    for s in range(n):
        helix_curve(f"{tag} rim {s}", h, L, r, twist, 2 * math.pi * s / n, 0.008, CM["rim"], emerge=0.3)
    for f in range(F_FIRE, F_GONE + 1, 4):
        key(h, f, rot=(0, (f - F_FIRE) * spin, 0))


G = dict(core=0.032, glow=0.42, pattern="streak", flow=0.6, strength=1.6, wob=0.15)
TAKES = [
    ("H1", "crisp twin helix", "L0 improved", dict(core=0.0, glow=0.0, haze=0.6, helix=(2, 0.13, 2.2, 0.13))),
    ("H2", "helix round a lance", "L0 improved", dict(helix=(2, 0.17, 1.6, 0.1))),
    ("H3", "braid", "L0 improved", dict(core=0.02, glow=0.26, helix=(3, 0.07, 4.5, 0.25), sb=0.035)),
    ("N1", "needle", "L1", dict(core=0.018, glow=0.24, flow=1.4, streak_len=0.12, haze=0.5)),
    ("N2", "layered", "L1", dict(flow=1.3, glow=0.3, layer=dict(w=0.75, flow=0.35, streak_len=0.5, strength=1.2))),
    ("N3", "crackle", "L1", dict(streak_x=22.0, streak_len=0.9, flow=1.0, wob=0.4)),
    ("C1", "weave flowing", "L2", dict(pattern="lib", lib="w1", glow=0.55)),
    ("C2", "brick flowing", "L2", dict(pattern="lib", lib="br1", glow=0.55)),
    ("C3", "hex tube", "L2", dict(tube="h1", glow=0.5)),
    ("P1", "rapid pulses", "L3", dict(pattern="pulse", flow=2.0, pulse_len=1.0, pulse_cut=0.3)),
    ("P2", "comet packets", "L3", dict(pattern="pulse", flow=2.6, pulse_len=5.0, pulse_cut=0.85, rims=2)),
    ("P3", "pulses + three rims", "L3", dict(pattern="pulse", flow=1.2, rims=3)),
]
for bi, (tk, name, fam, o_) in enumerate(TAKES):
    opt = dict(G); opt.update(o_)
    bx = bi * BAY
    tag = f"LZ2 {tk}"
    box(f"{tag} floor", (bx - 2.2, -3, -0.02), (bx + 2.2, 19, 0), FLOOR)
    box(f"{tag} wall", (bx - 2.0, 17.0, 0), (bx + 2.0, 18.0, 3.0), WALL)
    M = player_mats(tag)
    M["ring"] = mat(f"{tag} ring face", (0.02, 0.85, 0.15), emit=1.6)
    rig = make_player(tag, (bx, 0, 0), M)
    jar_ring(tag, rig, M)
    pose(rig, 1, arm_r=(0, 0, 0), fore_r=(0, 0, 0), head=(0, 0, 0))
    pose(rig, F_FIRE - 4, arm_r=(90, 0, 0), fore_r=(0, 0, 0), head=(0, 0, 0), arm_l=(10, 0, 0))
    pose(rig, F_FIRE + 1, arm_r=(86, 0, 0), fore_r=(0, 0, 0))
    pose(rig, F_FIRE + 4, arm_r=(90, 0, 0), fore_r=(0, 0, 0))
    pose(rig, F_GONE + 2, arm_r=(90, 0, 0), fore_r=(0, 0, 0))
    pose(rig, FRAME_END, arm_r=(10, 0, 0), fore_r=(0, 0, 0))
    anim_emit(M["ring"], [(1, 1.1), (F_FIRE - 2, 1.1), (F_FIRE, 1.8), (F_END, 1.6), (F_GONE, 1.1)])
    scene.frame_set(F_FIRE + 4); bpy.context.view_layer.update()
    o0 = rig["ring_pt"].matrix_world.translation.copy() + Vector((0, 0.02, 0))
    LEN = 17.0 - o0.y
    root = empty(f"{tag} beam", tuple(o0))
    hitp = Vector((o0.x, 16.98, o0.z))
    if opt["core"] > 0:
        life(cyl(f"{tag} core", opt["core"], LEN, CORE, 10, root, axis="Y"), 1.0, opt["wob"])
    if opt["glow"] > 0:
        gm = laser_mat(f"{tag} glow", opt["pattern"], flow=opt["flow"], strength=opt["strength"], alpha=0.95 if opt["pattern"] == "lib" else 0.85,
                       falloff=1.2 if opt["pattern"] == "lib" else 2.2, lib=opt.get("lib"),
                       pulse_len=opt.get("pulse_len", 2.5), pulse_cut=opt.get("pulse_cut", 0.6),
                       streak_len=opt.get("streak_len", 0.35), streak_x=opt.get("streak_x", 9.0))
        life(star(f"{tag} glow", LEN, opt["glow"], gm, root), 1.0, 0.06)
    if "layer" in opt:
        ly = opt["layer"]
        lm = laser_mat(f"{tag} outer glow", "streak", flow=ly["flow"], strength=ly["strength"], alpha=0.6, streak_len=ly["streak_len"])
        life(star(f"{tag} outer glow", LEN, ly["w"], lm, root), 1.0, 0.04)
    life(star(f"{tag} haze", LEN, opt.get("haze", 0.75), HAZE, root), 1.0, 0.04)
    if "helix" in opt:
        n_, r_, tw_, sp_ = opt["helix"]
        strands(tag, root, LEN, n_, r_, tw_, sp_, sheath_b=opt.get("sb", 0.05))
    if "tube" in opt:
        tm = laser_mat(f"{tag} tube", "lib", flow=0.6, strength=1.3, alpha=0.5, falloff=0.0, lib=opt["tube"], tile_u=2.0)
        life(tex_tube(f"{tag} textured tube", 0.1, LEN, tm, root), 1.0, 0.03)
    if "rims" in opt:
        rims(tag, root, LEN, opt["rims"])
    pop(flare(f"{tag} muzzle flare", FLARE, (0, 0, 0), root), 0.25, 0.42, F_FIRE, F_END)
    pop(flare(f"{tag} hit flare", FLARE, tuple(hitp)), 0.4, 0.9, F_HIT, F_END)
    if fam == "L3":
        pm = pixel_mesh(SPARK, 0.03)
        for f0 in range(F_HIT, F_END - 2, 2):
            for _ in range(4):
                px = link(bpy.data.objects.new(f"{tag} spark", pm))
                v = Vector((rng.normal(0, 0.06), -abs(rng.normal(0.08, 0.04)), rng.normal(0.04, 0.05)))
                key(px, 1, loc=tuple(hitp), sc=0.0001); key(px, f0 - 1, loc=tuple(hitp), sc=0.0001); key(px, f0, loc=tuple(hitp), sc=1.0)
                for k in (3, 6, 9, 12):
                    key(px, f0 + k, loc=tuple(hitp + v * k + Vector((0, 0, -0.004 * k * k))), sc=max(0.0001, 1 - k / 12))
    cam(f"Cam {tk} close", (bx + 2.4, 5.0, 1.8), (bx, 9.0, 1.3), 30)
    cam(f"Cam {tk} side", (bx + 6.5, 6.0, 2.4), (bx, 8.5, 1.2), 30)
    scene.frame_set(F_FIRE); bpy.context.view_layer.update()
    hp = rig["head"].matrix_world @ Vector((0, 4.5 * P, 3.5 * P))
    mc_fov(cam(f"Cam {tk} eye", tuple(hp), tuple(hp + Vector((0, 10, -0.9))), 20))
    label(f"{tk}  {name}  ({fam})", (bx, 18.0, 3.4), LBL, 0.26)
cam("Cam all", (5.5 * BAY, -14.0, 9.0), (5.5 * BAY, 9, 1.0), 22)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam H1 close", 24, (0.12, 0.14, 0.18), 1.5


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
