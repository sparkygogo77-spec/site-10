# Pass 811: a lantern shrine (Chat C, 2026-10-15, range 800-899).
# J picked "a lantern shrine or base (charging altar or tower, glow reacting to the charge)". The glow follows one
# charge value, scene["lit"]: 0 at rest, up to 1 as a player holds the ring to it (ticks 20-140), 1.3 overcharge at
# 150, held, then a slow fade. Every lit part has a threshold, so the light climbs the build in order.
#   S1 charging altar: a three-step dais, an altar with the lantern on it, runes on the steps lighting step by step,
#      four braziers last.
#   S2 lantern tower: an eight-block tower, windows lighting floor by floor, a crown of light and a beam up at full.
#   S3 pillar ring: eight pillars round the lantern, lighting one after another round the circle; at full, arcs of
#      light join their tops and a beam goes up the middle.
# Stone is dark; the glow is saturated green. Cameras "Cam <take>", "Cam <take> close", "Cam all". Builds
# LanternLive\lanterns\lantern_shrine.blend.
SCENE_NAME = "Lantern Shrine"
OUT_REL = "lanterns/lantern_shrine.blend"
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


FRAME_END = 260
BAY = 16.0
FLOOR = mat("LS floor", (0.15, 0.17, 0.16), rough=0.9)
STONE = mat("LS stone", (0.16, 0.17, 0.18), rough=0.75)
STONE2 = mat("LS dark stone", (0.05, 0.06, 0.06), rough=0.6)
GOLDM = mat("LS gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0)
LBL = mat("LS label", (0.3, 1.0, 0.45), emit=2.0)
GREEN = (0.12, 1.0, 0.3)
scene["lit"] = 0.0
for f, v in ((1, 0.0), (20, 0.0), (140, 1.0), (150, 1.3), (190, 1.3), (250, 0.0)):
    scene["lit"] = v; scene.keyframe_insert('["lit"]', frame=f)
_lm = {}


def lit_mat(th, k=4.0, alpha=1.0, tex=None):
    """A green that lights when lit passes th (over 0.25 of charge), up to k; overcharge pushes it 30% higher."""
    nm = f"LS lit {th:.2f} {k} {alpha} {tex}"
    if nm in _lm:
        return _lm[nm]
    m = strip_mat(nm, strip_image("green", tex), 4, emit=k, alpha=alpha) if tex else mat(nm, GREEN, emit=k, alpha=alpha)
    s = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    fc = s.driver_add("default_value"); d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "lit"; v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = '["lit"]'
    d.expression = f"max(0, min(1, (lit - {th}) * 4)) * {k} * (1 + max(0, lit - 1))"
    _lm[nm] = m
    return m


def lantern(tag, loc, s=1.0):
    """A blocky lantern: gold caps, a glowing body (lights first), a handle."""
    r = empty(f"{tag} lantern", loc)
    box(f"{tag} lantern base", (-0.35 * s, -0.35 * s, 0), (0.35 * s, 0.35 * s, 0.12 * s), GOLDM, r)
    box(f"{tag} lantern body", (-0.28 * s, -0.28 * s, 0.12 * s), (0.28 * s, 0.28 * s, 0.82 * s), lit_mat(0.0, 4.5, 0.9, "x3d1"), r)
    box(f"{tag} lantern band", (-0.31 * s, -0.31 * s, 0.42 * s), (0.31 * s, 0.31 * s, 0.5 * s), GOLDM, r)
    box(f"{tag} lantern top", (-0.33 * s, -0.33 * s, 0.82 * s), (0.33 * s, 0.33 * s, 0.94 * s), GOLDM, r)
    box(f"{tag} lantern handle", (-0.05 * s, -0.2 * s, 0.94 * s), (0.05 * s, 0.2 * s, 1.1 * s), GOLDM, r)
    li = bpy.data.lights.new(f"{tag} lantern light", "POINT"); li.color = (0.25, 1.0, 0.4); li.shadow_soft_size = 0.4
    fc = li.driver_add("energy"); v = fc.driver.variables.new(); v.name = "lit"; v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = '["lit"]'
    fc.driver.expression = "lit * lit * 300 * s_".replace("s_", str(s))
    lo = link(bpy.data.objects.new(f"{tag} lantern light", li)); lo.location = Vector(loc) + Vector((0, 0, 0.5 * s))
    return r


def beam(tag, loc, h, th, r_=0.25):
    b = cyl(f"{tag} beam", r_, h, lit_mat(th, 3.0, 0.5), 16, loc=loc)
    c = cyl(f"{tag} beam core", r_ * 0.35, h, lit_mat(th, 2.4), 12, loc=loc)
    for o in (b, c):                                             # rises when the charge passes th
        key(o, 1, sc=(1, 1, 0.0001)); key(o, 140, sc=(1, 1, 0.0001)); key(o, 148, sc=(1, 1, 1))
        key(o, 200, sc=(1, 1, 1)); key(o, 215, sc=(1, 1, 0.0001))


def charger(tag, loc, face):
    M = player_mats(tag)
    rig = make_player(tag, loc, M, face=face)
    pose(rig, 1, arm_r=(0, 0, 0), fore_r=(0, 0, 0)); pose(rig, 18, arm_r=(100, 0, 0), fore_r=(0, 0, 0))
    pose(rig, 200, arm_r=(100, 0, 0)); pose(rig, 215, arm_r=(0, 0, 0))
    anim_emit(M["ring"], [(1, 5), (20, 5), (140, 9), (150, 12), (190, 12), (250, 5)])


for bi, (tk, name) in enumerate((("S1", "charging altar"), ("S2", "lantern tower"), ("S3", "pillar ring"))):
    bx = bi * BAY
    tag = f"LS {tk}"
    box(f"{tag} floor", (bx - 7.5, -7, -0.02), (bx + 7.5, 8, 0), FLOOR)
    if tk == "S1":
        for i, (hw, z) in enumerate(((3.0, 0.0), (2.2, 0.35), (1.4, 0.7))):
            box(f"{tag} step {i}", (bx - hw, -hw, z), (bx + hw, hw, z + 0.35), STONE)
            n = 4 + 4 * (2 - i)
            for k in range(n):                                   # runes round each step's riser, step by step
                a = 2 * math.pi * k / n; th = 0.15 + 0.2 * (2 - i)
                x, y = math.cos(a), math.sin(a)
                m_ = max(abs(x), abs(y)); x, y = x / m_ * (hw + 0.01), y / m_ * (hw + 0.01)
                box(f"{tag} rune {i} {k}", (bx + x - 0.12, y - 0.12, z + 0.08), (bx + x + 0.12, y + 0.12, z + 0.27), lit_mat(th, 3.5))
        box(f"{tag} altar", (bx - 0.7, -0.5, 1.05), (bx + 0.7, 0.5, 1.95), STONE2)
        box(f"{tag} altar inlay", (bx - 0.72, -0.52, 1.75), (bx + 0.72, 0.52, 1.8), lit_mat(0.05, 3.0))
        lantern(tag, (bx, 0, 1.95), 1.0)
        for sx in (-1, 1):
            for sy in (-1, 1):
                bz = box(f"{tag} brazier {sx} {sy}", (bx + sx * 2.7 - 0.2, sy * 2.7 - 0.2, 0.35), (bx + sx * 2.7 + 0.2, sy * 2.7 + 0.2, 1.1), STONE2)
                fl_ = box(f"{tag} brazier flame {sx} {sy}", (bx + sx * 2.7 - 0.14, sy * 2.7 - 0.14, 1.1), (bx + sx * 2.7 + 0.14, sy * 2.7 + 0.14, 1.45), lit_mat(0.85, 4.0, 0.9))
                for f in range(150, 200, 3):
                    key(fl_, f, sc=(1, 1, 1 + 0.25 * math.sin(f * 1.3 + sx + sy)))
        beam(tag, (bx, 0, 3.0), 30.0, 0.95)
        charger(tag, (bx, -3.6, 0), 0.0)
        look = (bx, 0, 1.4)
    elif tk == "S2":
        H = 8
        for z in range(H):
            for ix in range(3):
                for iy in range(3):
                    if ix == 1 and iy == 1:
                        continue
                    edge = (ix, iy) in ((1, 0), (0, 1), (2, 1), (1, 2))
                    m_ = lit_mat(0.08 + 0.85 * z / H, 3.2, 0.95, "br1") if edge and z % 2 == 1 else STONE
                    box(f"{tag} block {z} {ix} {iy}", (bx - 1.5 + ix, -1.5 + iy, z), (bx - 0.5 + ix, -0.5 + iy, z + 1), m_)
            if z % 2 == 0:
                box(f"{tag} ledge {z}", (bx - 1.6, -1.6, z + 0.92), (bx + 1.6, 1.6, z + 1.0), lit_mat(0.08 + 0.85 * z / H, 2.0))
        lantern(tag, (bx, 0, H), 1.4)
        for k in range(8):                                        # the crown: 8 spikes of light at the top
            a = 2 * math.pi * k / 8
            cyl(f"{tag} crown {k}", 0.1, 1.2, lit_mat(0.9, 4.0), 6, loc=(bx + 1.3 * math.cos(a), 1.3 * math.sin(a), H), r2=0.0)
        beam(tag, (bx, 0, H + 1.6), 30.0, 0.95)
        charger(tag, (bx, -3.0, 0), 0.0)
        look = (bx, 0, 4.0)
    else:
        lantern(tag, (bx, 0, 0.6), 1.2)
        box(f"{tag} plinth", (bx - 0.6, -0.6, 0), (bx + 0.6, 0.6, 0.6), STONE2)
        tops = []
        for k in range(8):
            a = 2 * math.pi * k / 8 + math.pi / 2; x, y = bx + 4 * math.cos(a), 4 * math.sin(a)
            th = 0.1 + 0.75 * k / 8                               # lights round the circle, one after another
            box(f"{tag} pillar {k}", (x - 0.4, y - 0.4, 0), (x + 0.4, y + 0.4, 3.2), STONE)
            box(f"{tag} pillar seam {k}", (x - 0.42, y - 0.42, 0.4), (x + 0.42, y + 0.42, 2.8), lit_mat(th, 2.8, 0.9, "w1"))
            box(f"{tag} pillar cap {k}", (x - 0.5, y - 0.5, 3.2), (x + 0.5, y + 0.5, 3.45), lit_mat(th, 4.0))
            tops.append(Vector((x, y, 3.5)))
        for k in range(8):                                        # arcs between neighbouring tops at full charge
            a_, b_ = tops[k], tops[(k + 1) % 8]
            for j in range(8):
                u0, u1 = j / 8, (j + 1) / 8
                p0 = a_.lerp(b_, u0) + Vector((0, 0, 0.8 * math.sin(math.pi * u0)))
                p1 = a_.lerp(b_, u1) + Vector((0, 0, 0.8 * math.sin(math.pi * u1)))
                d = p1 - p0
                s_ = cyl(f"{tag} arc {k} {j}", 0.05, d.length, lit_mat(0.97, 4.0), 6, loc=tuple(p0))
                s_.rotation_mode = "QUATERNION"; s_.rotation_quaternion = d.to_track_quat("Z", "Y")
        beam(tag, (bx, 0, 1.7), 30.0, 0.95)
        charger(tag, (bx, -2.0, 0), 0.0)
        look = (bx, 0, 1.6)
    cam(f"Cam {tk}", (bx + 9, -11, 7.5), (look[0], look[1], look[2] + 1.0), 30)
    cam(f"Cam {tk} close", (bx + 3.0, -5.5, 2.2), look, 35)
    label(f"{tk}  {name}", (bx, 7.5, 5.0), LBL, 0.5)
cam("Cam all", (BAY, -34, 16), (BAY, 0, 3.0), 28)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam S1", 160, (0.03, 0.04, 0.06), 0.4


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
