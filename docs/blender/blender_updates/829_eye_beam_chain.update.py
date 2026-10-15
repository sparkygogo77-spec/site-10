# Pass 829: eye beam chain - corner hunter through every target (Chat C, 2026-10-15, range 800-899).
# J on 820 (Z1 corner hunter): "Corner hunter and the pattern should continue from there and go through each target to
# the last, if it hits a player it does not continue through them".
# The B1-look eye beams turn hard corners (Z1's pattern) to the first target, pass through it, then corner-hunt to the
# next, and so on to the last. Every target gets the kept outline flash (815 F3) as the beam passes through. If the
# next target is a PLAYER the beam stops in them: nothing after a player is hit.
#   C1 four mobs round two pillars: the beam chains through all four
#   C2 mob, mob, then a player: the beam stops in the player; the fourth mob, behind, is never touched
#   C3 five mobs in a loop round a pillar, with B1's soft glow (Z4)
# The front travels 3 blocks a tick so you can follow it; hold 40 ticks, then it pulls back from the eyes outward.
# Cameras "Cam <take> top", "Cam <take> side", "Cam <take> eyes", "Cam all". Builds LanternLive\combat\eye_beam_chain.blend.
SCENE_NAME = "Eye Beam Chain"
OUT_REL = "combat/eye_beam_chain.blend"
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


FRAME_END = 110
BAY = 9.0
F_FIRE, SPEED, HOLD = 12, 3.0, 40
FLOOR = mat("EB floor", (0.16, 0.17, 0.19), rough=0.9)
STONE = mat("EB pillar", (0.36, 0.37, 0.39), rough=0.9)
MOB = mat("EB mob", (0.3, 0.5, 0.28), rough=0.8)
HIT = mat("EB hit", (0.25, 1.0, 0.4), emit=2.0, alpha=0.5)
LBL = mat("EB label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(820)
CM = cmats("EB", "green")
CORE = mat("EB core", (0.15, 1.0, 0.3), emit=2.6)
SHEATH = mat("EB sheath", (0.06, 0.7, 0.2), emit=1.4, alpha=0.45, rough=0.1)
HALO = mat("EB glow", (0.05, 0.85, 0.25), emit=1.0, alpha=0.16, rough=0.3)


def segment(tag, p0, p1, f_start, f_done, f_back, f_gone, glow=False, scale=1.0):
    """One straight piece of beam from p0 to p1: grows from p0 as the front passes, holds, shrinks into p1's end."""
    d = Vector(p1) - Vector(p0); L = d.length
    root = empty(f"{tag} seg", tuple(p0)); root.rotation_mode = "QUATERNION"
    root.rotation_quaternion = d.to_track_quat("Y", "Z")
    parts = [cyl(f"{tag} core", 0.028 * scale, 1.0, CORE, 10, root, axis="Y"),
             cyl(f"{tag} sheath", 0.075 * scale, 1.0, SHEATH, 14, root, axis="Y")]
    for k, a in enumerate((0, math.pi)):
        ln = cyl(f"{tag} rim {k}", 0.008 * scale, 1.0, CM["rim"], 6, root, axis="Y"); ln.location = (0.078 * scale * math.cos(a), 0, 0.078 * scale * math.sin(a))
        parts.append(ln)
    if glow:
        parts.append(cyl(f"{tag} glow", 0.2 * scale, 1.0, HALO, 16, root, axis="Y"))
    for o in parts:
        key(o, 1, sc=(0.0001, 0.0001, 0.0001)); key(o, f_start, sc=(0.0001, 0.0001, 0.0001))
        key(o, f_start + 1, sc=(1, 0.01, 1)); key(o, max(f_done, f_start + 1) + 1, sc=(1, L, 1))
        key(o, f_back, sc=(1, L, 1)); key(o, f_gone, sc=(1, 0.0001, 1)); key(o, f_gone + 1, sc=(0.0001, 0.0001, 0.0001))
    # pulling back: the piece's start slides to its end as it shrinks (the beam leaves the eyes first)
    key(root, f_back, loc=tuple(p0)); key(root, f_gone, loc=tuple(p1))
    return root


def beam_path(tag, pts, f0, glow=False, scale=1.0, t0=0.0):
    """Lay a beam along a polyline; the front travels SPEED blocks a tick. Returns the tick the front arrives."""
    t = t0
    total = sum((Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:]))
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        L = (Vector(b) - Vector(a)).length
        fs = f0 + int(t / SPEED); fd = f0 + int((t + L) / SPEED)
        fb = f0 + HOLD + int(t / SPEED); fg = f0 + HOLD + int((t + L) / SPEED) + 1
        segment(f"{tag} {i}", a, b, fs, fd, fb, fg, glow, scale)
        if 0 < i:                                            # a bright joint at each corner
            j = ball(f"{tag} joint {i}", 0.06 * scale, CM["rim"], loc=tuple(a), seg=10)
            key(j, 1, sc=0.0001); key(j, fs, sc=0.0001); key(j, fs + 1, sc=1.0); key(j, fb, sc=1.0); key(j, fb + 1, sc=0.0001)
        t += L
    return f0 + int(t / SPEED)


def mob(tag, loc):
    r = empty(f"{tag} mob", loc)
    parts = [box(f"{tag} mob body", (-0.3, -0.45, 0.4), (0.3, 0.45, 0.95), MOB, r),
             box(f"{tag} mob head", (-0.22, -0.85, 0.7), (0.22, -0.4, 1.1), MOB, r)]
    for x in (-0.2, 0.2):
        for y in (-0.3, 0.3):
            parts.append(box(f"{tag} mob leg {x} {y}", (x - 0.08, y - 0.08, 0), (x + 0.08, y + 0.08, 0.4), MOB, r))
    return r, parts


def hit(tag, r, parts, f):
    for o in parts:                                          # the outline flash J kept (815 F3), then a small knock
        vs = np.array([v.co for v in o.data.vertices]); a, b = vs.min(0) - 0.035, vs.max(0) + 0.035
        s_ = box(o.name + " hit", tuple(a), tuple(b), HIT, o.parent)
        key(s_, 1, sc=0.0001); key(s_, f - 1, sc=0.0001); key(s_, f, sc=1.0); key(s_, f + 3, sc=1.0); key(s_, f + 9, sc=0.0001)
    p0 = Vector(r.location)
    key(r, f - 1, loc=tuple(p0), rot=(0, 0, 0)); key(r, f + 3, loc=tuple(p0 + Vector((0, 0.4, 0.3))), rot=(R(-15), 0, 0))
    key(r, f + 8, loc=tuple(p0 + Vector((0, 0.7, 0))), rot=(0, 0, 0))




def corner_path(a, b, z, first_x=True):
    """Z1's pattern between two points: hard right-angle turns (x then y, or y then x) at beam height z."""
    a = Vector(a); b = Vector(b)
    if first_x:
        return [(b.x, a.y, z), (b.x, b.y, z)]
    return [(a.x, b.y, z), (b.x, b.y, z)]


def player_target(tag, loc):
    M = player_mats(tag)
    rig = make_player(tag, loc, M, face=math.pi)
    parts = [o for o in rig["root"].children_recursive if o.type == "MESH"]
    return rig["root"], parts


LAYOUT = {
    "C1": dict(pillars=[(-1.0, 4.0), (2.0, 8.0)], targets=[("mob", (2.2, 5.0)), ("mob", (-2.0, 7.5)), ("mob", (1.0, 10.5)), ("mob", (-2.5, 12.0))]),
    "C2": dict(pillars=[(0.0, 4.5)], targets=[("mob", (2.0, 6.0)), ("mob", (-2.2, 8.0)), ("player", (1.5, 10.0)), ("mob", (-1.0, 12.5))]),
    "C3": dict(pillars=[(0.0, 8.0)], targets=[("mob", (2.0, 5.0)), ("mob", (2.5, 9.5)), ("mob", (0.0, 11.5)), ("mob", (-2.5, 9.5)), ("mob", (-2.0, 5.5))]),
}
for bi, (tk, name) in enumerate((("C1", "chain through four"), ("C2", "stops at a player"), ("C3", "loop of five + glow"))):
    bx = bi * BAY
    tag = f"EB {tk}"
    L_ = LAYOUT[tk]
    box(f"{tag} floor", (bx - 4, -3, -0.02), (bx + 4, 15, 0), FLOOR)
    M = player_mats(tag)
    rig = make_player(tag, (bx, 0, 0), M)
    pose(rig, 1, head=(0, 0, 0)); pose(rig, F_FIRE - 4, head=(-6, 0, 0)); pose(rig, F_FIRE + HOLD + 10, head=(-6, 0, 0))
    pose(rig, F_FIRE + HOLD + 16, head=(0, 0, 0))
    anim_emit(M["eye"], [(1, 1.5), (F_FIRE - 3, 1.5), (F_FIRE - 1, 4.0), (F_FIRE + HOLD + 20, 4.0), (F_FIRE + HOLD + 24, 1.5)])
    for k, (px_, py_) in enumerate(L_["pillars"]):
        box(f"{tag} pillar {k}", (bx + px_ - 0.6, py_ - 0.5, 0), (bx + px_ + 0.6, py_ + 0.5, 3.0), STONE)
    scene.frame_set(F_FIRE); bpy.context.view_layer.update()
    eyes = [rig["head"].matrix_world @ Vector((sx * 2 * P, 4.3 * P, 3.5 * P)) for sx in (-1, 1)]
    ez = eyes[0].z
    tgts = []
    for k, (kind, (tx, ty)) in enumerate(L_["targets"]):
        if kind == "mob":
            r, parts = mob(f"{tag} {k}", (bx + tx, ty, 0)); hz = 0.75
        else:
            r, parts = player_target(f"{tag} target player", (bx + tx, ty, 0)); hz = 1.2
        tgts.append((kind, r, parts, Vector((bx + tx, ty, hz))))
    # the chain: eyes -> out 2 blocks -> corner hunt to target 1 -> through it -> corner hunt to target 2 ... ; stop at a player
    for e_i, e in enumerate(eyes):
        dx = (e_i - 0.5) * 0.12
        pts = [tuple(e), (e.x + dx, 2.0, ez - 0.2)]
        arrive = []
        cur = Vector(pts[-1])
        for k, (kind, r, parts, c) in enumerate(tgts):
            c2 = c + Vector((dx, 0, 0))
            leg = corner_path(cur, c2, c2.z, first_x=(k % 2 == 0))
            pts += leg
            L = sum((Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:]))
            arrive.append((k, F_FIRE + int(L / SPEED)))
            cur = c2
            if kind == "player":
                break
            # pass straight through the target and out 0.8 blocks before turning again
            out = c2 + (c2 - Vector(pts[-2])).normalized() * 0.8
            out.z = c2.z
            pts.append(tuple(out)); cur = out
        beam_path(f"{tag} eye {e_i}", pts, F_FIRE, glow=tk == "C3")
    for k, f_hit in arrive:
        kind, r, parts, c = tgts[k]
        hit(f"{tag} {k}", r, parts, f_hit)
    if tk == "C3":
        for k, (kind, r, parts, c) in enumerate(tgts):
            lt = bpy.data.lights.new(f"{tag} beam light {k}", "POINT"); lt.color = (0.2, 1.0, 0.35); lt.shadow_soft_size = 0.4
            lo = link(bpy.data.objects.new(f"{tag} beam light {k}", lt)); lo.location = c + Vector((0, 0, 0.5))
            for f, e_ in ((1, 0), (F_FIRE + 2 * k, 0), (F_FIRE + 2 * k + 2, 25), (F_FIRE + HOLD, 25), (F_FIRE + HOLD + 8, 0)):
                lt.energy = e_; lt.keyframe_insert("energy", frame=f)
    cam(f"Cam {tk} top", (bx + 0.3, 6.5, 17.0), (bx + 0.3, 6.6, 0.0), 30)
    cam(f"Cam {tk} side", (bx + 8.0, -3.0, 5.0), (bx, 6.5, 0.8), 30)
    scene.frame_set(F_FIRE); bpy.context.view_layer.update()
    hp = rig["head"].matrix_world.translation
    cam(f"Cam {tk} eyes", tuple(hp + Vector((0.5, -1.4, 0.5))), tuple(hp + Vector((0, 2.0, 0.1))), 30)
    label(f"{tk}  {name}", (bx, 14.5, 2.8), LBL, 0.35)
    print(tk, "arrivals", arrive, flush=True)
cam("Cam all", (BAY, -16.0, 16.0), (BAY, 6.5, 0.5), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam C1 top", 30, (0.12, 0.14, 0.18), 1.5


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
