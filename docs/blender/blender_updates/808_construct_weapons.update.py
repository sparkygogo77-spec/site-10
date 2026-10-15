# Pass 808: construct weapons (Chat C, 2026-10-15, range 800-899).
# J picked "more construct weapons (bow and arrows, shield, spear, whip/lasso, chain, gauntlet), each forming pixel by
# pixel". Each take: ticks 1-20 the weapon forms from the ring (grip first, tip last, pixels streaming from the ring),
# then it does its job against a dummy 6 blocks ahead. Hard-light glass is 62% opaque (never above 99%), glow saturated.
#   K1 bow: forms in the left hand, the arrow forms at the ring; draw, hold, loose; the arrow flies and sticks.
#   K2 shield: a hex shield forms on the ring forearm; guard up; a shot hits it and breaks into pixels, the shield flashes.
#   K3 spear: forms long; draw back, thrust, then throw: it flies and sticks in the dummy.
#   K4 whip: 16 links; wound back, then lashed forward so the wave runs out to the tip and cracks at the dummy.
#   K5 chain: links swung round overhead twice, then thrown out to wrap the dummy, then pulled back in.
#   K6 gauntlet: a big construct fist grows over the hand; wind up, punch, a shock ring at the hit.
# Cameras "Cam <take>" (from the right, behind), "Cam <take> front", "Cam all". Writes LanternLive\combat\weapons_poses.json
# and builds LanternLive\combat\construct_weapons.blend.
SCENE_NAME = "Construct Weapons"
OUT_REL = "combat/construct_weapons.blend"
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
BAY = 5.0
FORM = 20
FLOOR = mat("CW floor", (0.18, 0.2, 0.22), rough=0.9)
DUMMY = mat("CW dummy", (0.3, 0.45, 0.3), rough=0.8)
SHOT = mat("CW shot", (0.6, 0.15, 0.1), emit=1.0)
LBL = mat("CW label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(808)
CM = cmats("CW", "green")
G, W, RM, GR = CM["glass"], CM["glow"], CM["rim"], CM["grip"]
dump = {"format": "per take: weapon, forming ticks, hit ticks; 20 ticks a second", "takes": {}}


def wpos(o, f):
    scene.frame_set(f); bpy.context.view_layer.update()
    return o.matrix_world.translation.copy()


def parts_of(root):
    return [o for o in root.children_recursive if o.type == "MESH"]


TAKES = [("K1", "bow"), ("K2", "shield"), ("K3", "spear"), ("K4", "whip"), ("K5", "chain"), ("K6", "gauntlet")]
for bi, (tk, name) in enumerate(TAKES):
    bx = bi * BAY
    box(f"CW {tk} floor", (bx - 2.2, -3, -0.02), (bx + 2.2, 8, 0), FLOOR)
    dm = box(f"CW {tk} dummy", (bx - 0.25, 5.8, 0), (bx + 0.25, 6.2, 1.8), DUMMY)
    M = player_mats(f"CW {tk}")
    rig = make_player(f"CW {tk}", (bx, 0, 0), M)
    hl = empty(f"CW {tk} hand point l", (0, 0, -6 * P), rig["fore_l"])
    hr = rig["hand_pt"]
    # the ring raised to make the weapon (forming), then the action
    pose(rig, 1, arm_r=(0, 0, 0), fore_r=(0, 0, 0), arm_l=(0, 0, 0), fore_l=(0, 0, 0), head=(0, 0, 0), body=(0, 0, 0))
    pose(rig, 6, arm_r=(80, 0, 0), fore_r=(20, 0, 0))
    hits = []
    if tk == "K1":
        pose(rig, FORM, arm_r=(80, 0, 0), fore_r=(20, 0, 0), arm_l=(10, 0, 0))
        pose(rig, FORM + 6, arm_l=(90, 0, -8), arm_r=(90, 0, 12), fore_r=(0, 0, 0), head=(0, 0, 0))
        pose(rig, FORM + 14, arm_r=(92, 0, 40), fore_r=(120, 0, 0))             # drawn back to the cheek
        pose(rig, FORM + 24, arm_r=(92, 0, 40), fore_r=(120, 0, 0))
        pose(rig, FORM + 26, arm_r=(95, 0, 60), fore_r=(40, 0, 0))              # loose
        pose(rig, FRAME_END, arm_l=(20, 0, 0), arm_r=(10, 0, 0), fore_r=(0, 0, 0))
        root = empty(f"CW {tk} bow", (0, 0, 0), hl)
        for k in range(-6, 7):                                                 # the limbs: an arc of 13 boxes
            y = k * 0.07; z = 0.1 * (1 - (k / 6) ** 2) + 0.02
            box(f"CW {tk} limb {k}", (-0.02, y - 0.036, z - 0.02), (0.02, y + 0.036, z + 0.02), RM if abs(k) == 6 else G, root)
        box(f"CW {tk} bow grip", (-0.025, -0.05, 0.0), (0.025, 0.05, 0.05), GR, root)
        string = box(f"CW {tk} string", (-0.005, -0.42, -0.005), (0.005, 0.42, 0.005), W, root)
        string.location = (0, 0, -0.08)
        key(string, FORM + 6, loc=(0, 0, -0.08), sc=(1, 1, 1)); key(string, FORM + 14, loc=(0, 0, -0.32), sc=(1, 0.9, 1))
        key(string, FORM + 24, loc=(0, 0, -0.32), sc=(1, 0.9, 1)); key(string, FORM + 25, loc=(0, 0, -0.02), sc=(1, 1, 1))
        key(string, FORM + 27, loc=(0, 0, -0.12), sc=(1, 1, 1)); key(string, FORM + 29, loc=(0, 0, -0.08), sc=(1, 1, 1))
        form_in(parts_of(root), 2, FORM, tuple(wpos(rig["ring_pt"], 6)), CM["pix"], rng, f"CW {tk}", order_axis=2)
        # the arrow: forms at the ring as the hand draws, flies on the loose (world space), sticks in the dummy
        arrow = empty(f"CW {tk} arrow", (0, 0, 0))
        box(f"CW {tk} arrow shaft", (-0.012, -0.36, -0.012), (0.012, 0.32, 0.012), W, arrow)
        box(f"CW {tk} arrow head", (-0.03, 0.32, -0.03), (0.03, 0.42, 0.03), RM, arrow)
        for s_ in (-1, 1):
            box(f"CW {tk} arrow fletch {s_}", (s_ * 0.05 - 0.005, -0.38, -0.004), (s_ * 0.005, -0.28, 0.004), G, arrow)
        p0 = wpos(rig["ring_pt"], FORM + 14)
        for f in range(FORM + 6, FORM + 25):
            pp = wpos(rig["ring_pt"], f); key(arrow, f, loc=tuple(pp + Vector((-0.06, 0.3, 0.02))))
        hit_f = FORM + 28
        key(arrow, hit_f, loc=(bx, 5.72, p0.z + 0.05)); key(arrow, FRAME_END, loc=(bx, 5.72, p0.z + 0.05))
        form_in(parts_of(arrow), FORM + 6, FORM + 14, None, CM["pix"], rng, f"CW {tk}", order_axis=1)
        hits = [hit_f]
    elif tk == "K2":
        pose(rig, FORM, arm_r=(80, 0, 0), fore_r=(20, 0, 0))
        pose(rig, FORM + 6, arm_r=(85, 0, 10), fore_r=(85, 0, 0), head=(5, 0, 0))     # guard: forearm up in front
        pose(rig, FORM + 22, arm_r=(85, 0, 10), fore_r=(85, 0, 0))
        pose(rig, FORM + 24, arm_r=(80, 0, 10), fore_r=(95, 0, 0), body=(-5, 0, 0))    # the shot knocks it back a touch
        pose(rig, FORM + 32, arm_r=(85, 0, 10), fore_r=(85, 0, 0), body=(0, 0, 0))
        pose(rig, FRAME_END, arm_r=(10, 0, 0), fore_r=(0, 0, 0))
        SG = mat("CW shield glass", tuple(np.array(CM["c"]) * 0.5), emit=0.9, alpha=0.62, rough=0.15)
        root = empty(f"CW {tk} shield", (0, -3.5 * P, -3 * P), rig["fore_r"])
        for q in range(-3, 4):                                                 # a hex of glass tiles, rim round it
            for r in range(-3, 4):
                if abs(q) + abs(r) + abs(-q - r) > 6:
                    continue
                x = 0.085 * (q + r / 2); z = 0.074 * r
                edge = abs(q) + abs(r) + abs(-q - r) == 6
                box(f"CW {tk} tile {q} {r}", (x - 0.04, -0.02, z - 0.035), (x + 0.04, 0.02 if edge else 0.0, z + 0.035), RM if edge else SG, root)
        box(f"CW {tk} boss", (-0.05, -0.05, -0.05), (0.05, 0.0, 0.05), W, root)
        form_in(parts_of(root), 4, FORM, tuple(wpos(rig["ring_pt"], 6)), CM["pix"], rng, f"CW {tk}", order_axis=0)
        sb = box(f"CW {tk} incoming shot", (-0.08, -0.08, -0.08), (0.08, 0.08, 0.08), SHOT)
        hit_f = FORM + 23; guard = wpos(root, hit_f)
        key(sb, 1, loc=(bx, 5.5, 1.4), sc=0.0001); key(sb, FORM + 14, loc=(bx, 5.5, 1.4), sc=1.0)
        key(sb, hit_f, loc=tuple(guard + Vector((0, 0.15, 0))), sc=1.0)
        sb.scale = (1, 1, 1); shatter([sb], hit_f + 1, SHOT, rng, f"CW {tk}", n=6, speed=0.08)
        anim_emit(SG, [(1, 0.9), (hit_f, 0.9), (hit_f + 1, 3.5), (hit_f + 6, 0.9)])
        hits = [hit_f]
    elif tk == "K3":
        pose(rig, FORM, arm_r=(80, 0, 0), fore_r=(20, 0, 0))
        pose(rig, FORM + 6, arm_r=(70, 0, 0), fore_r=(20, 0, 0), body=(0, 0, 10))
        pose(rig, FORM + 12, arm_r=(80, 0, 0), fore_r=(10, 0, 0), body=(0, 0, 25), root_loc=(bx, -0.2, 0))   # drawn back
        pose(rig, FORM + 16, arm_r=(92, 0, 0), fore_r=(0, 0, 0), body=(8, 0, -5), root_loc=(bx, 0.4, 0))    # thrust
        hits.append(FORM + 16)
        pose(rig, FORM + 22, arm_r=(80, 0, 0), fore_r=(10, 0, 0), body=(0, 0, 10), root_loc=(bx, 0.2, 0))
        pose(rig, FORM + 28, arm_r=(170, 0, 0), fore_r=(20, 0, 0), body=(-8, 0, 15), root_loc=(bx, 0.1, 0))  # overhand
        pose(rig, FORM + 32, arm_r=(70, 0, 0), fore_r=(0, 0, 0), body=(10, 0, -5), root_loc=(bx, 0.3, 0))    # throw
        pose(rig, FRAME_END, arm_r=(10, 0, 0), fore_r=(0, 0, 0), body=(0, 0, 0), root_loc=(bx, 0.3, 0))
        root = empty(f"CW {tk} spear", (0, 0, 0), hr)
        box(f"CW {tk} shaft", (-0.022, -0.022, -1.25), (0.022, 0.022, 0.55), GR, root)
        for k in range(5):
            z = -0.95 + k * 0.32
            box(f"CW {tk} band {k}", (-0.03, -0.03, z), (-0.0 + 0.03, 0.03, z + 0.03), W, root)
        box(f"CW {tk} head", (-0.06, -0.012, -1.55), (0.06, 0.012, -1.25), G, root)
        box(f"CW {tk} head edge", (-0.012, -0.02, -1.62), (0.012, 0.02, -1.22), RM, root)
        form_in(parts_of(root), 2, FORM, tuple(wpos(rig["ring_pt"], 6)), CM["pix"], rng, f"CW {tk}", order_axis=1)
        # thrown: from FORM + 32 the spear flies in world space (unparented copy keyed), the held one vanishes
        fly = empty(f"CW {tk} thrown spear", (0, 0, 0))
        for o in parts_of(root):
            c_ = o.copy(); c_.data = o.data; c_.animation_data_clear(); link(c_); c_.parent = fly
            c_.location = o.location; c_.scale = (1, 1, 1)
        fly.rotation_mode = "XYZ"
        rel = wpos(hr, FORM + 32)
        key(fly, 1, loc=tuple(rel), rot=(R(90), 0, 0), sc=0.0001); key(fly, FORM + 31, sc=0.0001)
        key(fly, FORM + 32, loc=tuple(rel), rot=(R(90), 0, 0), sc=1.0)
        key(fly, FORM + 38, loc=(bx, 5.4, 1.2), rot=(R(84), 0, 0), sc=1.0); key(fly, FRAME_END, loc=(bx, 5.4, 1.2), sc=1.0)
        key(root, FORM + 31, sc=1.0); key(root, FORM + 32, sc=0.0001)
        hits.append(FORM + 38)
    elif tk in ("K4", "K5"):
        n = 16 if tk == "K4" else 12
        L_ = 0.16 if tk == "K4" else 0.22
        if tk == "K4":
            pose(rig, FORM, arm_r=(80, 0, 0), fore_r=(20, 0, 0))
            pose(rig, FORM + 8, arm_r=(160, 0, -20), fore_r=(30, 0, 0), body=(0, 0, 15))     # wound back over the shoulder
            pose(rig, FORM + 14, arm_r=(80, 0, 10), fore_r=(0, 0, 0), body=(5, 0, -10))      # lash
            pose(rig, FORM + 18, arm_r=(60, 0, 10), fore_r=(0, 0, 0), body=(5, 0, -10))
            pose(rig, FORM + 40, arm_r=(40, 0, 0), fore_r=(10, 0, 0), body=(0, 0, 0))
        else:
            pose(rig, FORM, arm_r=(80, 0, 0), fore_r=(20, 0, 0))
            pose(rig, FORM + 4, arm_r=(170, 0, 0), fore_r=(0, 0, 0))                          # up, swinging overhead
            pose(rig, FORM + 24, arm_r=(170, 0, 0), fore_r=(0, 0, 0))
            pose(rig, FORM + 28, arm_r=(80, 0, 0), fore_r=(0, 0, 0), body=(6, 0, 0))          # throw
            pose(rig, FORM + 42, arm_r=(80, 0, 0), fore_r=(0, 0, 0))
            pose(rig, FORM + 50, arm_r=(70, 0, 0), fore_r=(60, 0, 0), body=(-6, 0, 0))        # pull back
        pose(rig, FRAME_END, arm_r=(10, 0, 0), fore_r=(0, 0, 0), body=(0, 0, 0))
        handle = box(f"CW {tk} handle", (-0.025, -0.025, -0.2), (0.025, 0.025, 0.02), GR, hr)
        links = []
        for i in range(n):
            if tk == "K4":
                o = box(f"CW {tk} link {i}", (-0.025, -0.025, -0.025), (0.025, 0.025, 0.025), RM if i == n - 1 else G)
            else:
                o = torus(f"CW {tk} link {i}", 0.06, 0.015, RM if i % 3 == 0 else W, axis="Y" if i % 2 else "X")
            links.append(o)
        # procedural keys: the chain hangs from the handle tip; positions per tick in world space
        targ = Vector((bx, 5.75, 1.2))
        for f in range(1, FRAME_END + 1):
            h = wpos(handle, f) + Vector((0, 0, 0)); scene.frame_set(f)
            tip_dir = (handle.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            hb = handle.matrix_world @ Vector((0, 0, -0.2))
            pts = []
            for i in range(n):
                s = (i + 1) / n
                if tk == "K4":
                    k_ = f - FORM
                    if k_ < 10:                                                    # hanging, trailing behind the hand
                        p = hb + Vector((0, -0.25 * s, -s * n * L_ * 0.7))
                    elif k_ < 26:                                                  # the wave runs out to the tip
                        u = (k_ - 10) / 16.0
                        out = min(1.0, u * 1.6 / max(s, 0.15)) if s > 0 else 1
                        straight = hb + (targ - hb) * s * min(1.0, (n * L_) / (targ - hb).length) * 1.45
                        back = hb + Vector((0, -0.6 * s, 0.4 * s))
                        wave = Vector((0, 0, 0.35 * math.sin(math.pi * s) * (1 - u)))
                        p = back.lerp(straight, smooth(out)) + wave
                    else:
                        u = min(1.0, (k_ - 26) / 14.0)
                        straight = hb + (targ - hb) * s * min(1.0, (n * L_) / (targ - hb).length) * 1.45
                        p = straight.lerp(hb + Vector((0, 0.2 * s, -s * n * L_ * 0.8)), smooth(u))
                else:
                    k_ = f - FORM
                    if k_ < 4:
                        p = hb + Vector((0, 0, -s * n * L_ * 0.8))
                    elif k_ < 26:                                                  # whirled overhead, two turns
                        a = (k_ - 4) / 22.0 * 4 * math.pi
                        rr = s * 1.3
                        p = hb + Vector((rr * math.cos(a), rr * math.sin(a), 0.15 * s))
                    elif k_ < 32:                                                  # thrown straight out
                        u = (k_ - 26) / 6.0
                        a = 4 * math.pi; ring_p = hb + Vector((s * 1.3 * math.cos(a), s * 1.3 * math.sin(a), 0.15 * s))
                        p = ring_p.lerp(hb + (targ - hb) * s, smooth(u))
                    elif k_ < 42:                                                  # wrapped round the dummy's middle
                        wrap = max(0.0, (s - 0.6) / 0.4)
                        a = wrap * 4 * math.pi
                        base_ = hb + (targ - hb) * min(s, 0.6) / 0.6 * 0.96
                        p = base_ + (Vector((0.32 * math.cos(a), 0.22 * math.sin(a), -0.05 * wrap * 4)) if wrap > 0 else Vector())
                    else:                                                          # pulled back in
                        u = min(1.0, (k_ - 42) / 12.0)
                        p = (hb + (targ - hb) * s).lerp(hb + Vector((0, 0.1 * s, -s * n * L_ * 0.6)), smooth(u))
                pts.append(p)
            for i, o in enumerate(links):
                key(o, f, loc=tuple(pts[i]))
        form_in(links + [handle], 2, FORM, tuple(wpos(rig["ring_pt"], 6)), CM["pix"], rng, f"CW {tk}", order_axis=1)
        hits = [FORM + 24] if tk == "K4" else [FORM + 32]
    else:
        pose(rig, FORM, arm_r=(80, 0, 0), fore_r=(20, 0, 0))
        pose(rig, FORM + 8, arm_r=(70, 0, 10), fore_r=(100, 0, 0), body=(0, 0, 30), root_loc=(bx, -0.1, 0))      # wind up
        pose(rig, FORM + 12, arm_r=(92, 0, 0), fore_r=(0, 0, 0), body=(10, 0, -15), root_loc=(bx, 0.5, 0))       # punch
        pose(rig, FORM + 20, arm_r=(90, 0, 0), fore_r=(0, 0, 0), body=(6, 0, -10), root_loc=(bx, 0.5, 0))
        pose(rig, FRAME_END, arm_r=(10, 0, 0), fore_r=(0, 0, 0), body=(0, 0, 0), root_loc=(bx, 0.5, 0))
        root = empty(f"CW {tk} gauntlet", (0, 0, -3 * P), rig["fore_r"])
        # a big fist: 2.2x the hand, four knuckle blocks, a cuff with glowing bands, rim along the knuckles
        box(f"CW {tk} palm", (-0.2, -0.2, -0.42), (0.2, 0.2, -0.1), G, root)
        for k in range(4):
            x = -0.15 + k * 0.1
            box(f"CW {tk} knuckle {k}", (x - 0.045, -0.12, -0.52), (x + 0.045, 0.21, -0.42), G, root)
            box(f"CW {tk} knuckle rim {k}", (x - 0.047, 0.12, -0.53), (x + 0.047, 0.22, -0.5), RM, root)
        box(f"CW {tk} thumb", (0.2, -0.05, -0.38), (0.27, 0.12, -0.2), G, root)
        box(f"CW {tk} cuff", (-0.17, -0.17, -0.1), (0.17, 0.17, 0.16), GR, root)
        for z in (-0.06, 0.06):
            box(f"CW {tk} cuff band {z}", (-0.18, -0.18, z), (0.18, 0.18, z + 0.03), W, root)
        form_in(parts_of(root), 2, FORM, tuple(wpos(rig["ring_pt"], 6)), CM["pix"], rng, f"CW {tk}", order_axis=2)
        hit_f = FORM + 12
        sw = torus(f"CW {tk} shock ring", 0.3, 0.025, RM, loc=(bx, 5.75, 1.3), axis="Y")
        key(sw, 1, sc=0.0001); key(sw, hit_f - 1, sc=0.0001); key(sw, hit_f, sc=0.6); key(sw, hit_f + 8, sc=3.5)
        key(sw, hit_f + 9, sc=0.0001)
        hits = [hit_f]
    for h in hits:                                                            # the dummy rocks on each hit
        key(dm, h - 1, rot=(0, 0, 0)); key(dm, h + 2, rot=(R(-10), 0, 0)); key(dm, h + 8, rot=(0, 0, 0))
    dump["takes"][tk] = {"weapon": name, "forming_ticks": [1, FORM], "hit_ticks": hits}
    cam(f"Cam {tk}", (bx + 3.2, -2.6, 2.2), (bx, 2.4, 1.0), 32)
    cam(f"Cam {tk} front", (bx - 0.8, 4.6, 1.6), (bx, 0, 1.1), 35)
    label(f"{tk}  {name}", (bx, 7.0, 2.4), LBL, 0.26)
    print(tk, name, "built", flush=True)
with open(os.path.join(FOLDER, "combat", "weapons_poses.json"), "w") as fh:
    json.dump(dump, fh, indent=1)
cam("Cam all", (2.5 * BAY, -16.0, 9.0), (2.5 * BAY, 2.5, 0.8), 24)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam K1", 1, (0.3, 0.38, 0.5), 3.0


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
