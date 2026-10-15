# Pass 821: construct mech suits (Chat C, 2026-10-15, range 800-899).
# J on 810 G5: "mech suit needs a few design iterations as a big robotic suit, do one other size and a few animations for
# it, this may be a feature i can give to a villager or any kind of mob potentially".
# Three big designs (about 4 blocks tall) and one other size (compact, about 2.4 blocks, mob-sized), each piloted by
# a different mob to show any mob can get one. All play the same animations in a row:
#   1-24 form: the mech builds round the pilot from the feet up (pixels from the core), the pilot is lifted into the
#        cockpit (24-30), the canopy shuts and the core lights (30-36)
#   36-76 walk: four heavy steps (10 ticks each), the body bobs and sways, a dust ring on each footfall
#   76-96 punch: wind up, a big right punch with the torso twisting into it, a shock ring, recoil
#   96-126 stomp: crouch, jump (thrusters fire), land on both feet, a big ground ring
#   MA Titan frame (BR1 bricks, player pilot): square chest cockpit with a glass canopy, straight legs, block fists,
#      shoulder blocks with glowing vents
#   MB Strider (H1 hex, villager pilot): reverse-knee legs, slim waist, a raised pod cockpit with a visor slit, long arms
#      with three-claw hands
#   MC Juggernaut (W1 weave, zombie pilot): very wide armoured shoulders, hammer fists, back thrusters
#   MS Compact (X3D1 ripples, villager pilot): the Titan frame at 0.6 size - the "other size", for any mob
# Cameras "Cam <take>", "Cam <take> close", "Cam all". Builds LanternLive\constructs\mech_suits.blend.
SCENE_NAME = "Mech Suits"
OUT_REL = "constructs/mech_suits.blend"
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


FRAME_END = 130
BAY = 9.0
FLOOR = mat("MS floor", (0.2, 0.22, 0.2), rough=0.9)
LBL = mat("MS label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(821)
CM = cmats("MS", "green")
RM, W, GR, GL = CM["rim"], CM["glow"], CM["grip"], CM["glass"]
TEX = {k: strip_mat(f"MS {k} texture", strip_image("green", k), 4, emit=1.3, alpha=0.92) for k in ("br1", "h1", "w1", "x3d1")}
ROBE = mat("MS villager robe", (0.35, 0.22, 0.12), rough=0.9)
VSKIN = mat("MS villager skin", (0.72, 0.52, 0.4), rough=0.8)
ZSKIN = mat("MS zombie skin", (0.3, 0.5, 0.3), rough=0.8)
ZSHIRT = mat("MS zombie shirt", (0.1, 0.45, 0.5), rough=0.8)
BROW = mat("MS brow", (0.15, 0.1, 0.05))


def pilot(tag, kind, parent, loc):
    """A seated pilot. kind: player / villager / zombie. Returns the rig root."""
    if kind == "player":
        M = player_mats(tag)
    else:
        M = player_mats(tag)
        if kind == "villager":
            M.update(skin=VSKIN, shirt=ROBE, pants=ROBE, boot=ROBE)
        else:
            M.update(skin=ZSKIN, shirt=ZSHIRT, pants=mat(f"{tag} pants", (0.2, 0.2, 0.45)))
    rig = make_player(tag, (0, 0, 0), M)
    if kind == "villager":                                   # the long nose and the brow
        box(f"{tag} nose", (-1 * P, 4 * P, 1 * P), (1 * P, 6 * P, 4 * P), VSKIN, rig["head"])
        box(f"{tag} brow", (-4 * P, 4 * P, 4.5 * P), (4 * P, 4.2 * P, 5.2 * P), BROW, rig["head"])
    rig["root"].parent = parent; rig["root"].location = loc
    return rig, M


def build_mech(tag, design, S, T):
    """Returns joints. Mech faces +Y in its own space; S scales everything (1 = about 4 blocks tall)."""
    J = {}
    root = empty(f"{tag} mech", (0, 0, 0)); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, 1.85 * S), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.15 * S), hips); J["torso"] = torso
    b = lambda nm, a, c, m, par: box(f"{tag} {nm}", tuple(np.array(a) * S), tuple(np.array(c) * S), m, par)
    b("pelvis", (-0.6, -0.4, -0.25), (0.6, 0.4, 0.2), T, hips)
    legs, arms = [], []
    digi = design == "MB"
    for sx in (-1, 1):
        hip = empty(f"{tag} hip {sx}", (sx * 0.45 * S, 0, -0.1 * S), hips)
        b(f"thigh {sx}", (-0.22, -0.22, -0.8), (0.22, 0.22, 0.0), T, hip)
        knee = empty(f"{tag} knee {sx}", (0, 0, -0.8 * S), hip)
        b(f"knee cap {sx}", (-0.25, -0.05 if not digi else -0.3, -0.12), (0.25, 0.3 if not digi else 0.05, 0.12), RM, knee)
        b(f"shin {sx}", (-0.2, -0.2, -0.8), (0.2, 0.2, 0.0), T, knee)
        ankle = empty(f"{tag} ankle {sx}", (0, 0, -0.8 * S), knee)
        b(f"foot {sx}", (-0.3, -0.35, -0.25), (0.3, 0.55, 0.0), T, ankle)
        b(f"toe {sx}", (-0.25, 0.55, -0.22), (0.25, 0.7, -0.05), RM, ankle)
        if digi:                                             # reverse knee rest pose
            hip.rotation_euler = (R(30), 0, 0); knee.rotation_euler = (R(-60), 0, 0); ankle.rotation_euler = (R(30), 0, 0)
        legs.append((hip, knee, ankle, sx))
    if design in ("MA", "MS"):
        b("chest back", (-0.85, -0.55, 0.0), (0.85, -0.25, 1.4), T, torso)
        for sx in (-1, 1):
            b(f"chest side {sx}", (sx * 0.85 - 0.15, -0.55, 0.0), (sx * 0.85 + 0.15, 0.5, 1.4), T, torso)
        b("chest floor", (-0.85, -0.55, -0.05), (0.85, 0.5, 0.1), T, torso)
        b("chest roof", (-0.9, -0.6, 1.3), (0.9, 0.55, 1.5), T, torso)
        b("core", (-0.18, -0.58, 0.55), (0.18, -0.5, 0.9), W, torso)
        hatch = empty(f"{tag} canopy hinge", (0, 0.5 * S, 1.4 * S), torso)
        b("canopy", (-0.7, 0.0, -1.3), (0.7, 0.06, 0.0), GL, hatch)
        b("canopy rim", (-0.72, 0.0, -1.32), (0.72, 0.08, -1.22), RM, hatch)
        J["hatch"] = hatch; J["seat"] = (0, -0.05 * S, -0.62 * S)
        for sx in (-1, 1):
            sh = empty(f"{tag} shoulder {sx}", (sx * 1.15 * S, 0, 1.15 * S), torso)
            b(f"shoulder block {sx}", (-0.32, -0.38, -0.1), (0.32, 0.38, 0.45), T, sh)
            b(f"vent {sx}", (sx * 0.33 - 0.02, -0.25, 0.05), (sx * 0.33 + 0.02, 0.25, 0.35), W, sh)
            b(f"upper arm {sx}", (-0.18, -0.18, -0.75), (0.18, 0.18, -0.05), T, sh)
            el = empty(f"{tag} elbow {sx}", (0, 0, -0.75 * S), sh)
            b(f"forearm {sx}", (-0.2, -0.2, -0.7), (0.2, 0.2, 0.0), T, el)
            b(f"fist {sx}", (-0.28, -0.28, -1.1), (0.28, 0.28, -0.7), T, el)
            b(f"knuckles {sx}", (-0.29, 0.22, -1.08), (0.29, 0.3, -0.75), RM, el)
            arms.append((sh, el, sx))
    elif design == "MB":
        b("waist", (-0.3, -0.25, 0.0), (0.3, 0.25, 0.6), T, torso)
        pod = empty(f"{tag} pod", (0, 0, 0.6 * S), torso); J["pod"] = pod
        b("pod floor", (-0.75, -0.6, 0.0), (0.75, 0.6, 0.12), T, pod)
        b("pod back", (-0.75, -0.6, 0.0), (0.75, -0.35, 1.5), T, pod)
        for sx in (-1, 1):
            b(f"pod side {sx}", (sx * 0.75 - 0.12, -0.6, 0.0), (sx * 0.75 + 0.12, 0.6, 1.5), T, pod)
        b("pod roof", (-0.8, -0.65, 1.45), (0.8, 0.65, 1.6), T, pod)
        hatch = empty(f"{tag} canopy hinge", (0, 0.6 * S, 1.45 * S), pod)
        b("visor", (-0.65, 0.0, -1.4), (0.65, 0.06, 0.0), GL, hatch)
        b("visor slit", (-0.6, 0.06, -0.55), (0.6, 0.09, -0.45), W, hatch)
        J["hatch"] = hatch; J["seat"] = (0, -0.05 * S, -0.55 * S)
        for sx in (-1, 1):
            sh = empty(f"{tag} shoulder {sx}", (sx * 0.95 * S, 0, 1.2 * S), pod)
            b(f"upper arm {sx}", (-0.12, -0.12, -0.95), (0.12, 0.12, 0.1), T, sh)
            el = empty(f"{tag} elbow {sx}", (0, 0, -0.95 * S), sh)
            b(f"forearm {sx}", (-0.14, -0.14, -0.95), (0.14, 0.14, 0.0), T, el)
            for k in range(3):
                a = k * 2 * math.pi / 3
                cl = b(f"claw {sx} {k}", (-0.04, -0.04, -0.35), (0.04, 0.04, 0.0), RM, el)
                cl.location = (0.1 * S * math.cos(a), 0.1 * S * math.sin(a), -0.95 * S); cl.rotation_euler = (R(15) * math.sin(a), R(-15) * math.cos(a), 0)
            arms.append((sh, el, sx))
        for sx in (-1, 1):
            b(f"antenna {sx}", (sx * 0.5 - 0.03, -0.3, 1.6), (sx * 0.5 + 0.03, -0.24, 2.1), RM, pod)
    else:                                                    # MC Juggernaut
        b("chest back", (-1.0, -0.6, 0.0), (1.0, -0.3, 1.5), T, torso)
        for sx in (-1, 1):
            b(f"chest side {sx}", (sx * 1.0 - 0.15, -0.6, 0.0), (sx * 1.0 + 0.15, 0.55, 1.5), T, torso)
        b("chest floor", (-1.0, -0.6, -0.05), (1.0, 0.55, 0.1), T, torso)
        b("chest roof", (-1.05, -0.65, 1.4), (1.05, 0.6, 1.6), T, torso)
        hatch = empty(f"{tag} canopy hinge", (0, 0.55 * S, 1.45 * S), torso)
        b("canopy", (-0.85, 0.0, -1.4), (0.85, 0.06, 0.0), GL, hatch)
        for k in range(3):
            b(f"canopy bar {k}", (-0.86, 0.0, -1.3 + k * 0.5), (0.86, 0.09, -1.22 + k * 0.5), RM, hatch)
        J["hatch"] = hatch; J["seat"] = (0, -0.05 * S, -0.55 * S)
        for sx in (-1, 1):
            nz = empty(f"{tag} thruster {sx}", (sx * 0.5 * S, -0.75 * S, 0.6 * S), torso)
            b(f"thruster body {sx}", (-0.2, -0.25, -0.2), (0.2, 0.15, 0.5), T, nz)
            fl = b(f"thruster flame {sx}", (-0.14, -0.2, -0.7), (0.14, 0.1, -0.2), W, nz)
            J[f"flame {sx}"] = fl
            sh = empty(f"{tag} shoulder {sx}", (sx * 1.4 * S, 0, 1.2 * S), torso)
            b(f"pauldron {sx}", (-0.5, -0.5, -0.2), (0.5, 0.5, 0.55), T, sh)
            b(f"pauldron plate {sx}", (-0.55, -0.55, 0.45), (0.55, 0.55, 0.62), RM, sh)
            b(f"upper arm {sx}", (-0.22, -0.22, -0.8), (0.22, 0.22, -0.1), T, sh)
            el = empty(f"{tag} elbow {sx}", (0, 0, -0.8 * S), sh)
            b(f"forearm {sx}", (-0.25, -0.25, -0.6), (0.25, 0.25, 0.0), T, el)
            hm = cyl(f"{tag} hammer {sx}", 0.38 * S, 0.7 * S, T, 12, el, loc=(-0.35 * S, 0, -0.95 * S), axis="X")
            cyl(f"{tag} hammer face {sx}", 0.4 * S, 0.06 * S, RM, 12, el, loc=(0.33 * S, 0, -0.95 * S), axis="X")
            arms.append((sh, el, sx))
    J["legs"], J["arms"] = legs, arms
    return J


def animate(tag, J, S, bx, digi=False, thrusters=False):
    root, hips, torso, hatch = J["root"], J["hips"], J["torso"], J["hatch"]
    legs, arms = J["legs"], J["arms"]
    rest = {id(h): (R(30), 0, 0) if digi else (0, 0, 0) for h, k, a, sx in legs}
    rest_k = (R(-60), 0, 0) if digi else (0, 0, 0)
    rest_a = (R(30), 0, 0) if digi else (0, 0, 0)
    def legpose(f, sx_, hip_x, knee_x, ankle_x=0.0):
        for h, k, a, sx in legs:
            if sx == sx_:
                key(h, f, rot=(rest[id(h)][0] + R(hip_x), 0, 0)); key(k, f, rot=(rest_k[0] + R(knee_x), 0, 0))
                key(a, f, rot=(rest_a[0] + R(ankle_x), 0, 0))
    def armpose(f, sx_, sh_x, el_x, sh_z=0.0):
        for sh, el, sx in arms:
            if sx == sx_:
                key(sh, f, rot=(R(sh_x), 0, R(sh_z))); key(el, f, rot=(R(el_x), 0, 0))
    hz = 1.85 * S
    # 1-36: form, board, canopy shuts (the canopy hinge is open at -100 deg, i.e. swung up)
    key(hatch, 1, rot=(R(-100), 0, 0)); key(hatch, 30, rot=(R(-100), 0, 0)); key(hatch, 35, rot=(0, 0, 0))
    for sx in (-1, 1):
        legpose(1, sx, 0, 0); armpose(1, sx, 0, 10)
    key(hips, 1, loc=(0, 0, hz), rot=(0, 0, 0)); key(torso, 1, rot=(0, 0, 0))
    key(root, 1, loc=(bx, 0, 0)); key(root, 36, loc=(bx, 0, 0))
    # 36-76: four heavy steps forward (+Y), 10 ticks each, step length 0.9*S
    for i in range(4):
        f0 = 36 + i * 10; sx = 1 if i % 2 == 0 else -1
        legpose(f0, sx, 0, 0); legpose(f0 + 5, sx, 28, -40, 10); legpose(f0 + 10, sx, 0, 0)
        legpose(f0, -sx, 0, 0); legpose(f0 + 5, -sx, -12, 0); legpose(f0 + 10, -sx, 0, 0)
        armpose(f0 + 5, sx, -15, 15); armpose(f0 + 5, -sx, 18, 25)
        key(root, f0 + 10, loc=(bx, (i + 1) * 0.9 * S, 0))
        key(hips, f0, loc=(0, 0, hz), rot=(0, 0, 0)); key(hips, f0 + 5, loc=(0, 0, hz + 0.08 * S), rot=(0, R(3 * sx), 0))
        key(hips, f0 + 10, loc=(0, 0, hz - 0.06 * S), rot=(0, 0, 0))
        ring = torus(f"{tag} step ring {i}", 0.35 * S, 0.03, RM, loc=(bx + sx * 0.45 * S, (i + 1) * 0.9 * S + 0.3 * S, 0.04))
        key(ring, 1, sc=0.0001); key(ring, f0 + 9, sc=0.0001); key(ring, f0 + 10, sc=(1, 1, 1)); key(ring, f0 + 16, sc=(3, 3, 1))
        key(ring, f0 + 17, sc=0.0001)
    y_end = 4 * 0.9 * S
    key(hips, 76, loc=(0, 0, hz))
    for sx in (-1, 1):
        armpose(76, sx, 0, 10)
    # 76-96: punch: wind up (torso twists away), then a big right punch, shock ring, recoil
    key(torso, 76, rot=(0, 0, 0)); key(torso, 82, rot=(0, 0, R(-25))); key(torso, 86, rot=(0, 0, R(20))); key(torso, 96, rot=(0, 0, 0))
    armpose(82, 1, 40, 100); armpose(86, 1, 92, 0); armpose(90, 1, 88, 5); armpose(96, 1, 0, 10)
    armpose(82, -1, 30, 60); armpose(86, -1, -10, 40); armpose(96, -1, 0, 10)
    scene.frame_set(86); bpy.context.view_layer.update()
    fist = next(el for sh, el, sx in arms if sx == 1)
    fp_ = fist.matrix_world @ Vector((0, 0, -1.0 * S))
    sr = torus(f"{tag} punch ring", 0.3 * S, 0.03, RM, loc=tuple(fp_ + Vector((0, 0.4 * S, 0))), axis="Y")
    key(sr, 1, sc=0.0001); key(sr, 85, sc=0.0001); key(sr, 86, sc=1.0); key(sr, 92, sc=3.5); key(sr, 93, sc=0.0001)
    # 96-126: stomp: crouch, jump, land
    for sx in (-1, 1):
        legpose(96, sx, 0, 0); legpose(102, sx, 35, -70, 35); legpose(106, sx, -5, 0, 0); legpose(114, sx, 10, -20, 10)
        legpose(118, sx, 35, -70, 35); legpose(126, sx, 0, 0)
        armpose(102, sx, -30, 40); armpose(106, sx, 60, 20); armpose(118, sx, -20, 50); armpose(126, sx, 0, 10)
    key(hips, 96, loc=(0, 0, hz)); key(hips, 102, loc=(0, 0, hz - 0.45 * S)); key(hips, 106, loc=(0, 0, hz + 0.3 * S))
    key(hips, 112, loc=(0, 0, hz + 1.6 * S)); key(hips, 118, loc=(0, 0, hz - 0.45 * S)); key(hips, 126, loc=(0, 0, hz))
    gr = torus(f"{tag} land ring", 0.6 * S, 0.04, RM, loc=(bx, y_end, 0.04))
    key(gr, 1, sc=0.0001); key(gr, 117, sc=0.0001); key(gr, 118, sc=(1, 1, 1)); key(gr, 126, sc=(5, 5, 1)); key(gr, 127, sc=0.0001)
    if thrusters:
        for sx in (-1, 1):
            fl = J[f"flame {sx}"]
            key(fl, 1, sc=(1, 1, 0.0001)); key(fl, 104, sc=(1, 1, 0.0001)); key(fl, 106, sc=(1, 1, 1.6)); key(fl, 112, sc=(1, 1, 1.2))
            key(fl, 115, sc=(1, 1, 0.0001))


TAKES = [("MA", "Titan frame", 1.0, "br1", "player"), ("MB", "Strider", 1.0, "h1", "villager"),
         ("MC", "Juggernaut", 1.0, "w1", "zombie"), ("MS", "Compact (0.6 size)", 0.6, "x3d1", "villager")]
for bi, (tk, name, S, look, pk) in enumerate(TAKES):
    bx = bi * BAY
    tag = f"MS {tk}"
    box(f"{tag} floor", (bx - 4, -4, -0.02), (bx + 4, 12, 0), FLOOR)
    design = "MA" if tk == "MS" else tk
    J = build_mech(tag, design, S, TEX[look])
    animate(tag, J, S, bx, digi=design == "MB", thrusters=design == "MC")
    # the pilot: stands where the mech forms, lifted into the seat 24-30, then sits for the rest
    seat_parent = J.get("pod", J["torso"])
    prig, PM = pilot(f"{tag} pilot", pk, seat_parent, J["seat"])
    pr = prig["root"]
    ps = 0.6 / 0.6 if tk != "MS" else 1.0
    scene.frame_set(1); bpy.context.view_layer.update()
    seat_world = seat_parent.matrix_world @ Vector(J["seat"])
    stand_local = seat_parent.matrix_world.inverted() @ Vector((bx, 0.0, 0.0))
    key(pr, 1, loc=tuple(stand_local)); key(pr, 24, loc=tuple(stand_local)); key(pr, 30, loc=J["seat"])
    pose(prig, 1, leg_r=(0, 0, 0), leg_l=(0, 0, 0), shin_r=(0, 0, 0), shin_l=(0, 0, 0), arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0))
    pose(prig, 24, leg_r=(0, 0, 0), leg_l=(0, 0, 0), shin_r=(0, 0, 0), shin_l=(0, 0, 0), arm_r=(40, 0, 0), arm_l=(40, 0, 0))
    pose(prig, 30, leg_r=(90, 0, 6), leg_l=(90, 0, -6), shin_r=(-90, 0, 0), shin_l=(-90, 0, 0), arm_r=(60, 0, 0), arm_l=(60, 0, 0),
         fore_r=(20, 0, 0), fore_l=(20, 0, 0))
    if tk == "MS":                                           # the compact mech is sized for a mob: the pilot shrinks to fit (villager scale)
        pr.scale = (0.62, 0.62, 0.62)
    # forming: everything grows in from the feet up, pixels streaming from the core position
    parts = [o for o in J["root"].children_recursive if o.type == "MESH"]
    form_in(parts, 2, 24, (bx, 0.0, 2.2 * S), CM["pix"], rng, tag, order_axis=2, stream=0.35)
    cam(f"Cam {tk}", (bx + 5.0 * S + 1.5, 9.0 * S + 3.0, 3.4 * S + 0.6), (bx, 2.0 * S, 1.9 * S), 32)
    cam(f"Cam {tk} close", (bx + 2.2 * S, 6.0 * S + 1.0, 3.0 * S), (bx, 1.5 * S, 2.4 * S), 32)
    cam(f"Cam {tk} back", (bx - 3.0 * S, -6.0 * S, 3.2 * S), (bx, 1.0, 2.0 * S), 32)
    label(f"{tk}  {name}  - pilot: {pk}", (bx, -3.0, 5.0), LBL, 0.32, rot=(R(90), 0, R(180)))
    print(tk, "built", flush=True)
cam("Cam all", (1.5 * BAY, 24, 10), (1.5 * BAY, 2, 2.0), 30)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam MA", 1, (0.35, 0.45, 0.6), 3.0


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
