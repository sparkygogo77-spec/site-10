# Pass 860: ring glow in first person - replacements for the light rays (Chat C, 2026-10-15).
# Why: J on the in-game glow (bug note docs/handoff/bugs/2026-10-15-green-glow-interference.md, Bridge 6%, ring charge
#   100%, Complementary Unbound patched): "these light rays from blender are not it" -- pale green light streaks smeared
#   down the ring arm and sleeve, big translucent green panes near the camera, a green haze; also "the glow is bad".
#   Earlier: "W2 light rays and smoke look bad". He likes solid, readable lines, darker cores, saturated steady glow,
#   never white.
# Rules every take keeps: NOTHING on or along the arm/sleeve; no translucent sheets or volumes near the camera; no light
#   shafts or billboards; a small emissive area (so a shader pack's bloom stays small); saturated green, never white.
# Rig: pass 856's first- and third-person arms; the ring on the fist's punching face over the middle finger (the jar's
#   placement). First-person cameras are 120 deg horizontal with a crosshair.
# Timeline (every take): 1-60 ring charge rises 0 -> 100%; 60-90 holds at 100%; 90-120 Bridge mode is used: the ring arm
#   pushes forward and a short Bridge construct forms ahead on the ground, tile by tile (91-103), then holds.
# Takes:
#   G1 face glow = charge: only the ring's face glows, steady, its brightness is the charge. Nothing else.
#   G2 rim line: a thin solid light line traces round the ring's gold rim as charge rises (full loop at 100%), steady.
#   G3 orbit pixels: up to 4 small solid pixel motes circle slowly within 2 px of the ring face, one per 25% charge.
#   G4 face meter: the ring face is a 5-step meter (5 slices), dark to lit from one edge as charge rises; Bridge's cost drops a step.
#   G5 pulse on use: the ring stays dark while charging and holding; using Bridge gives one quick short pulse, then gone.
#   G6 knuckle light: a tiny point light over the back of the fist lights the knuckles only (no geometry), steady, = charge.
# Cameras "Cam <code> - first person" (120 deg, crosshair) and "Cam <code> - third person", plus "Cam all".
# Builds LanternLive\combat\ring_glow.blend.
SCENE_NAME = "Ring Glow"
OUT_REL = "combat/ring_glow.blend"
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



def ring_on_fist(tag, parent, end_z, px, back="x"):
    """The jar's placement: on the punching face (at end_z, facing -Z), 1 px in from the back of the hand (+X, or +Y
    for the first-person rig), over the middle finger. Gold frame, green face standing out, a band over the back."""
    mt = empty(f"{tag} ring mount", (0, 0, end_z), parent)
    if back == "y":
        mt.rotation_euler = (0, 0, R(90))                                   # +X (back) -> +Y
    c = 0.6 * px                                                           # 2 px back edge - 1.4 px
    box(f"{tag} ring band", (1.95 * px, -0.55 * px, 0), (2.25 * px, 0.55 * px, 1.4 * px), M["gold"], mt)
    box(f"{tag} ring frame", (c - 1.25 * px, -1.25 * px, -0.45 * px), (c + 1.25 * px, 1.25 * px, 0), M["gold"], mt)
    box(f"{tag} ring face", (c - 0.95 * px, -0.95 * px, -1.0 * px), (c + 0.95 * px, 0.95 * px, -0.4 * px), M["ring"], mt)
    return empty(f"{tag} ring point", (c, 0, -1.15 * px), mt)


def hand_3p(tag, rig, M):
    """Rebuild the right forearm with a wrist so the fist can bend back, and move the ring to the punching face."""
    for nm in ("forearm r", "ring band", "ring face", "ring point", "hand point"):
        o = bpy.data.objects.get(f"{tag} {nm}")
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    fr = rig["fore_r"]
    box(f"{tag} forearm r", (-2 * P, -2 * P, -4 * P), (2 * P, 2 * P, 0), M["skin"], fr)
    wr = empty(f"{tag} wrist r", (0, 0, -4 * P), fr)
    box(f"{tag} hand r", (-2 * P, -2 * P, -2 * P), (2 * P, 2 * P, 0), M["skin"], wr)
    box(f"{tag} knuckles r", (1.2 * P, -2.05 * P, -2.05 * P), (2.05 * P, 2.05 * P, -1.1 * P), M["skin"], wr)
    rig["wrist_r"] = wr
    rig["ring_pt"] = ring_on_fist(tag + " 3p", wr, -2 * P, P, "x")
    rig["hand_pt"] = empty(f"{tag} hand point", (0, 0, -2 * P), wr)


FP_LEN = 12 * P * 1.05


def fp_arms(tag, eye, M):
    """Camera looks along +Y. Each arm is a 4x12x4 box from a shoulder below the view; the right one has a wrist 4 px
    from the end so the fist can bend back. The back of the right hand is local +Y (up at roll 0)."""
    rigs = {}
    px = P * 1.05
    for side in ("r", "l"):
        sh = empty(f"{tag} fp shoulder {side}", eye); sh.rotation_mode = "QUATERNION"
        box(f"{tag} fp sleeve {side}", (-2 * px, -2 * px, -8 * px), (2 * px, 2 * px, 0), M["shirt"], sh)
        if side == "r":
            wr = empty(f"{tag} fp wrist", (0, 0, -8 * px), sh); rigs["wrist"] = wr
            box(f"{tag} fp hand r", (-2 * px, -2 * px, -4 * px), (2 * px, 2 * px, 0), M["skin"], wr)
            box(f"{tag} fp knuckles", (-2.05 * px, 1.2 * px, -4.05 * px), (2.05 * px, 2.05 * px, -3.1 * px), M["skin"], wr)
            rigs["ring_pt"] = ring_on_fist(tag + " fp", wr, -4 * px, px, "y")
        else:
            box(f"{tag} fp hand l", (-2 * px, -2 * px, -12 * px), (2 * px, 2 * px, -8 * px), M["skin"], sh)
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


def fp_ring_key(rigs, f, eye, pitch, x, y, d, bend):
    """Key the right FP arm and wrist so the RING (not the arm end) lands at camera-space (x, y, d): the fist is a
    4-px cube, so bending it back pulls the ring 0.1-0.2 m toward you; three corrections cancel that."""
    Rc = Matrix.Rotation(R(pitch), 3, "X")
    key(rigs["wrist"], f, rot=(R(bend), 0, 0))
    want = Vector(eye) + Rc @ Vector((x, d, y)); tx, ty, td = x, y, d
    for _ in range(4):
        fp_key(rigs, "r", f, eye, pitch, tx, ty, td, 0)
        scene.frame_set(f); bpy.context.view_layer.update()
        err = Rc.inverted() @ (want - rigs["ring_pt"].matrix_world.translation)
        tx, td, ty = tx + err.x, td + err.y, ty + err.z


def board(tag, loc, title, lines):
    n = len(lines)
    box(f"{tag} board", (loc[0] - 1.7, loc[1], loc[2] - 0.2 - 0.13 * n), (loc[0] + 1.7, loc[1] + 0.05, loc[2] + 0.42), BOARD)
    label(title, (loc[0], loc[1] - 0.02, loc[2] + 0.12), TXTH, 0.2)
    cu = bpy.data.curves.new(f"{tag} notes", "FONT"); cu.body = "\n".join(lines); cu.size = 0.095; cu.align_x = "LEFT"
    o = link(bpy.data.objects.new(f"{tag} notes", cu)); o.location = (loc[0] - 1.6, loc[1] - 0.02, loc[2] - 0.05)
    o.rotation_euler = (R(90), 0, 0); o.data.materials.append(TXT)



FRAME_END = 120
BAY = 24.0
ROOTCOL = col
FLOOR = mat("RG floor", (0.2, 0.22, 0.24), rough=0.9)
BOARD = mat("RG board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("RG text", (0.55, 0.85, 0.6), emit=1.0)
TXTH = mat("RG heading", (0.1, 0.9, 0.3), emit=1.8)
XH = mat("RG crosshair", (0.7, 0.72, 0.7), emit=0.8)
METER = mat("RG charge bar", (0.02, 0.8, 0.15), emit=1.2)
GLOW_RGB = (0.02, 0.9, 0.12)                  # every emissive colour: saturated green, never white
DARK_RGB = (0.01, 0.16, 0.04)                 # an unlit ring face: dark green glass
BRIDGE = strip_mat("RG bridge", strip_image("green", "br1"), 5, emit=0.8, alpha=0.8)
rng = np.random.default_rng(860)


def charge(f):
    return min(1.0, max(0.0, (f - 1) / 59.0))


def lit_mat(name, emit_keys, rgb=GLOW_RGB, base=DARK_RGB):
    """Opaque, dark-based, emitting saturated green; emission strength keyed."""
    m = mat(name, base, emit=1.0, rough=0.3)
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (*rgb, 1)
    anim_emit(m, emit_keys)
    return m


def fp_cam(name, eye):
    """120 deg horizontal eye camera with a crosshair (as 859)."""
    c = cam(name, tuple(eye), tuple(eye + Vector((0, 3, 0))), 18 / math.tan(R(60)))
    c.data.sensor_fit = "HORIZONTAL"; c.data.sensor_width = 36.0; c.data.clip_start = 0.02
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        box(f"{name} crosshair {nm_}", a_, b_, XH, c)
    return c


def mount_of(pt):
    return pt.parent


def rim_loop(tag, mt, px, m, segs_per_side=4, keys=None):
    """A thin solid line round the ring's gold rim (just outside the face, on the frame's front), split into segments.
    keys(k, n) -> list of (frame, scale) for segment k of n; None = always shown."""
    c = 0.6 * px; r = 1.12 * px; t = 0.11 * px; z0, z1 = -0.62 * px, -0.42 * px
    corners = [(c - r, -r), (c + r, -r), (c + r, r), (c - r, r)]
    n = 4 * segs_per_side; k = 0; objs = []
    for s in range(4):
        (xa, ya), (xb, yb) = corners[s], corners[(s + 1) % 4]
        for j in range(segs_per_side):
            u0, u1 = j / segs_per_side, (j + 1) / segs_per_side
            pa = (xa + (xb - xa) * u0, ya + (yb - ya) * u0); pb = (xa + (xb - xa) * u1, ya + (yb - ya) * u1)
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            piv = empty(f"{tag} rim pivot {k}", (mid[0], mid[1], 0), mt)
            lo = (min(pa[0], pb[0]) - mid[0] - t, min(pa[1], pb[1]) - mid[1] - t, z0)
            hi = (max(pa[0], pb[0]) - mid[0] + t, max(pa[1], pb[1]) - mid[1] + t, z1)
            o = box(f"{tag} rim line {k}", lo, hi, m, piv)
            if keys:
                for f, s_ in keys(k, n):
                    key(piv, f, sc=s_)
            objs.append(o); k += 1
    return objs


def bridge(tag, start, step, n=14, w=1.0, f0=91, f1=103):
    """Bridge: a short flat path of construct tiles forming from the near end outward (one tile per tick), held.
    start = world point of the near end's centre, step = world vector per tile (0.5 m). See-through (0.8)."""
    for k in range(n):
        p = Vector(start) + Vector(step) * (k + 0.5)
        hw = Vector(step).normalized().cross(Vector((0, 0, 1))) * (w / 2)
        e = Vector((abs(step[0]) * 0.48 + abs(hw.x), abs(step[1]) * 0.48 + abs(hw.y), 0))
        piv = empty(f"{tag} bridge tile {k}", tuple(p))
        box(f"{tag} bridge tile {k} mesh", (-e.x, -e.y, 0), (e.x, e.y, 0.12), BRIDGE, piv)
        fa = int(round(f0 + (f1 - f0) * k / (n - 1)))
        key(piv, 1, sc=0.0001); key(piv, fa - 1, sc=0.0001); key(piv, fa + 1, sc=1.0)


# ----------------------------------------------------------------- the six ideas (built on one ring: its mount + rig)
def fx_G1(tag, pt, px, eye_obj):
    """Face glow = charge: emission 0.1 -> 2.2 over 1-60, steady; a small lift when Bridge fires."""
    m = lit_mat(f"{tag} G1 face", [(f, 0.1 + 2.1 * charge(f)) for f in range(1, 61, 6)] + [(60, 2.2), (90, 2.2), (92, 2.6), (97, 2.2), (120, 2.2)])
    return m


def fx_G2(tag, pt, px, eye_obj):
    """Rim line traced by charge (16 segments, one appears each ~3.7 ticks), steady 1.8; face dim."""
    line = lit_mat(f"{tag} G2 rim", [(1, 1.8)])
    def keys(k, n):
        fa = 1 + int(round(59 * (k + 1) / n))
        return [(1, 0.0001), (fa - 2, 0.0001), (fa, 1.0)]
    rim_loop(tag + " G2", mount_of(pt), px, line, keys=keys)
    return lit_mat(f"{tag} G2 face", [(1, 0.35)])


def fx_G3(tag, pt, px, eye_obj):
    """Four small solid pixel motes (0.5 px) circle the face at 1.8 px radius, 0.8 px out front; one lap per 60 ticks.
    One appears at each 25% of charge. When Bridge fires they tuck in to 1.2 px for a few ticks."""
    mt = mount_of(pt); c = 0.6 * px
    mm = lit_mat(f"{tag} G3 mote", [(1, 2.0)])
    pm = pixel_mesh(mm, 0.25 * px)
    for j in range(4):
        o = link(bpy.data.objects.new(f"{tag} G3 mote {j}", pm)); o.parent = mt
        fa = 15 * (j + 1)
        for f in list(range(1, FRAME_END + 1, 2)) + [fa - 1, fa]:
            a = (f - 1) * 2 * math.pi / 60 + j * math.pi / 2
            rr = 1.8 * px
            if 90 <= f <= 98:
                rr = (1.8 - 0.6 * math.sin((f - 90) / 8 * math.pi)) * px
            key(o, f, loc=(c + rr * math.cos(a), rr * math.sin(a), -0.8 * px), sc=0.0001 if f < fa else 1.0)
    return lit_mat(f"{tag} G3 face", [(1, 0.4), (60, 0.9)])


def fx_G4(tag, pt, px, eye_obj):
    """The face is a 5-step meter: 5 full-depth slices across the face (so they read from any side), each lights
    (0 -> 2.0 in 2 ticks) at 20/40/60/80/100%. Bridge's cost drops the top slice at 92; it refills by 112."""
    mt = mount_of(pt); c = 0.6 * px; bw = 1.96 * px / 5
    for k in range(5):
        fa = 1 + 12 * (k + 1)
        keys = [(1, 0.0), (fa - 2, 0.0), (fa, 2.0)]
        if k == 4:
            keys += [(91, 2.0), (93, 0.0), (110, 0.0), (112, 2.0)]
        m = lit_mat(f"{tag} G4 bar {k}", keys)
        y0 = -0.98 * px + k * bw
        box(f"{tag} G4 bar {k}", (c - 0.98 * px, y0 + 0.03 * px, -1.03 * px), (c + 0.98 * px, y0 + bw - 0.03 * px, -0.42 * px), m, mt)
    return lit_mat(f"{tag} G4 face", [(1, 0.0)])


def fx_G5(tag, pt, px, eye_obj):
    """Dark through charging and holding; on use (90) one quick pulse: face 0 -> 2.6 -> 0 over 90-96 and the rim line
    pops out over 90-94, gone by 96."""
    line = lit_mat(f"{tag} G5 rim", [(1, 0.0), (89, 0.0), (91, 2.4), (96, 0.0)])
    rim_loop(tag + " G5", mount_of(pt), px, line, segs_per_side=1,
             keys=lambda k, n: [(1, 0.0001), (89, 0.0001), (90, 1.0), (95, 1.0), (96, 0.0001)])
    return lit_mat(f"{tag} G5 face", [(1, 0.0), (89, 0.0), (91, 2.6), (93, 1.6), (96, 0.0)])


def fx_G6(tag, pt, px, eye_obj):
    """A tiny point light 1 px above the back of the fist, over the knuckles; energy = charge (0 -> 0.12 W), green,
    short reach (EEVEE cutoff 0.06 m, stops before the sleeve), no geometry. The face itself only glows a little."""
    mt = mount_of(pt); c = 0.6 * px
    ld = bpy.data.lights.new(f"{tag} G6 knuckle light", "POINT")
    ld.color = (0.0, 1.0, 0.1); ld.shadow_soft_size = 0.004
    try:
        ld.use_custom_distance = True; ld.cutoff_distance = 0.06
    except Exception:
        pass
    lo = link(bpy.data.objects.new(f"{tag} G6 knuckle light", ld)); lo.parent = mt; lo.location = (3.0 * px, 0, 0.6 * px)
    for f, e in [(f, 0.12 * charge(f)) for f in range(1, 61, 6)] + [(60, 0.12), (90, 0.12), (120, 0.12)]:
        ld.energy = e; ld.keyframe_insert("energy", frame=f)
    return lit_mat(f"{tag} G6 face", [(1, 0.3), (60, 0.8)])


TAKES = [("G1", "face glow = charge", fx_G1,
          ["Only the ring's face glows, steady.", "Brightness = charge (dim at 0%, full at 100%).", "Nothing else, nothing on the arm."]),
         ("G2", "rim line", fx_G2,
          ["A thin solid light line traces round the ring's", "gold rim as charge rises: a full loop = 100%.", "Steady, no fade, face stays dim."]),
         ("G3", "orbit pixels", fx_G3,
          ["Small solid pixels circle within 2 px of the", "ring face, slowly. One more at each 25% charge.", "They tuck in for a moment when Bridge fires."]),
         ("G4", "face meter", fx_G4,
          ["The ring face is a 5-step meter, dark -> lit", "from one edge as charge rises.", "Bridge's cost drops a step, then it refills."]),
         ("G5", "pulse on use", fx_G5,
          ["Dark while charging and holding.", "Using Bridge: one quick short pulse on the", "ring (face + rim, 90-96), then gone."]),
         ("G6", "knuckle light", fx_G6,
          ["A tiny point light just off the ring face", "lights the knuckles only (no geometry).", "Steady, brightness = charge."])]


def fp_ring_pose(fpr, f, eye):
    """856's W2 framing (ring right of the crosshair, fist bent back 50); 90-96 the arm pushes out and down toward
    the Bridge and holds there."""
    if f < 90:
        x, y, d = 0.2, -0.16 + 0.008 * math.sin(f * 0.05), 0.56
    else:
        u = smooth((f - 90) / 5.0)
        x, y, d = 0.2 - 0.03 * u, -0.16 - 0.05 * u, 0.56 + 0.1 * u
    fp_ring_key(fpr, f, eye, -6, x, y, d, 50 - 15 * (smooth((f - 90) / 5.0) if f >= 90 else 0))
    fp_key(fpr, "l", f, eye, -6, -0.55, -0.6, 0.4, 0)


DIAG = {}
for bi, (tk, name, fx, lines) in enumerate(TAKES):
    col = bpy.data.collections.new(f"{tk} {name}")
    ROOTCOL.children.link(col)
    bx = bi * BAY
    tag = f"RG {tk}"
    M = player_mats(tag)
    eye = Vector((bx, 30.0, 1.62))
    fpr = fp_arms(tag, eye, M)
    fpr["wrist"].rotation_mode = "XYZ"
    fcam = fp_cam(f"Cam {tk} - first person", eye)
    fcam.rotation_euler = (R(90 - 6), 0, 0)
    box(f"{tag} floor", (bx - 3, -9, -0.02), (bx + 3, 3, 0), FLOOR)
    box(f"{tag} fp floor", (bx - 3, 26, -0.02), (bx + 3, 42, 0), FLOOR)
    rig = make_player(tag, (bx, 0, 0), M, face=math.pi)
    hand_3p(tag, rig, M)
    for f in sorted(set(list(range(1, 90, 10)) + [89, 90, 92, 95, 100, 110, 120])):
        s = math.sin(f / FRAME_END * 2 * math.pi)
        u = smooth((f - 90) / 5.0) if f >= 90 else 0.0
        pose(rig, f, arm_r=(38 + 3 * s + 50 * u, 0, -6), fore_r=(42 - 34 * u, 0, -70 + 60 * u), arm_l=(4, 0, 4), fore_l=(8, 0, 0),
             head=(-12 - 18 * u, 0, 0), body=(1.5 * s, 0, 0), wrist_r=(0, -40 + 20 * u, 0))
        fp_ring_pose(fpr, f, eye)
    c3 = cam(f"Cam {tk} - third person", (bx + 3.4, -3.6, 1.9), (bx, -1.4, 0.95), 28)
    # the ring's face: the take decides how it glows (fx returns the face material) and adds its own bits
    for side, pt, px, eo in (("3p", rig["ring_pt"], P, c3), ("fp", fpr["ring_pt"], P * 1.05, fcam)):
        fm = fx(f"{tag} {side}", pt, px, eo)
        face = bpy.data.objects[f"{tag} {side} ring face"]
        face.data = face.data.copy(); face.data.materials[0] = fm
    bridge(f"{tag} 3p", (bx, -0.7, 0), (0, -0.5, 0))
    bridge(f"{tag} fp", (bx, eye.y + 1.0, 0), (0, 0.5, 0))
    board(tag, (bx, 1.6, 2.75), f"{tk}  {name.upper()}",
          lines + ["1-60 charge 0->100%  60-90 hold  90-120 Bridge used", "(bar below = charge)"])
    bar = box(f"{tag} charge bar", (0, 0, 0), (3.2, 0.04, 0.06), METER)
    bar.location = (bx - 1.6, 1.58, 2.75 - 0.2 - 0.13 * (len(lines) + 2) - 0.12)
    key(bar, 1, sc=(0.0001, 1, 1)); key(bar, 60, sc=(1, 1, 1))
    DIAG[tk] = (fcam, fpr["ring_pt"])
col = ROOTCOL
from bpy_extras.object_utils import world_to_camera_view
for fr_ in (75, 100):
    scene.frame_set(fr_); bpy.context.view_layer.update()
    for tk, (fc, pt) in DIAG.items():
        v = world_to_camera_view(scene, fc, pt.matrix_world.translation)
        print(f"DIAG {fr_} {tk}: ring at screen ({v.x:.2f}, {v.y:.2f}) depth {v.z:.2f}")
cam("Cam all", ((len(TAKES) - 1) / 2 * BAY, -150, 20.0), ((len(TAKES) - 1) / 2 * BAY, 0, 1.8), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam G1 - first person", 75, (0.16, 0.2, 0.28), 2.2



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
