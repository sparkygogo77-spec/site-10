# Pass 856: worn ring round 4 - the arm glow forming made plain to see (W2d2), three new orbit-mote builds (W2f1-3),
# and the rise's fist bend narrowed to 45-65 deg (W5a1-4 up from W5a, W5b1-3 down from W5b) (Chat C, 2026-10-15).
# Source: pass 831 (worn ring round 3). J's 831 ratings (all IMPROVE; W2e and W5c dropped):
#   W2d halo: "Cant see the arm glow forming,"
#   W2f orbit motes: no note -> 3 new variations, each keeps the motes circling the fist, built a different way
#   W5a rise, fist back 45: "few more variations up to 65 degrees from this one, keep this one though"
#   W5b rise, fist back 75: "go down in degrees"
#   Earlier (818): "W4b rise at 135 is good; turn the hand more, ring on the fist's top as in the jar, an angle that
#   shows the ring while flying up". W2 light rays and smoke "look bad" (none here).
# Ring placement as the jar (RingModels.placement): punching face, 1 px in from the back of the hand, over the middle
# finger. MC FOV scene property drives every first-person camera (Sensor Fit Vertical), as in 831.
# Takes:
#   W2d2 halo, arm glow you can see: W2d's breathing halo, plus the construct texture now builds up the arm in 10 bright
#        slices from the fist to the shoulder (ticks 10-60), a glowing collar riding the forming edge and pixels flying
#        from the ring to it; the first-person arm sits higher and more central so the sleeve is in view the whole time.
#   W2f1 orbit, carousel: 8 pixel motes on ONE flat ring around the wrist, spinning and bobbing, appearing one by one.
#   W2f2 orbit, comet: ONE bigger mote looping a figure-8 round the ring fast, with a 6-step fading tail.
#   W2f3 orbit, helix: 3 motes spiral UP the arm from the fist toward the elbow, each with a 2-step trail, and respawn.
#   W5a  rise, fist back 45 (as before): 831's W5a unchanged, the reference.
#   W5a1 / W5a2 / W5a3 / W5a4: W5a with the fist bent back 50 / 55 / 60 / 65 deg.
#   W5b1 / W5b2 / W5b3: "go down in degrees" from W5b's 75: the fist swings to 75 on lift-off (as W5b) then settles
#        back to 65 / 60 / 55 deg by tick 46 and holds there (so these differ from W5a's same angles in the motion).
# Cameras "Cam <take> <name> - third person" / "- first person", "Cam all". Builds LanternLive\combat\worn_ring4.blend.
SCENE_NAME = "Worn Ring 4"
OUT_REL = "combat/worn_ring4.blend"
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
BAY = 5.0
ROOTCOL = col
FLOOR = mat("WR4 floor", (0.2, 0.22, 0.24), rough=0.9)
BOARD = mat("WR4 board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("WR4 text", (0.75, 1.0, 0.8), emit=1.2)
TXTH = mat("WR4 heading", (0.2, 1.0, 0.4), emit=2.2)
rng = np.random.default_rng(856)
RINGC = (0.02, 0.85, 0.15)
RAY = mat("WR4 streak", (0.05, 0.9, 0.25), emit=1.8, alpha=0.4, rough=0.2)
SKINTEX = strip_mat("WR4 arm texture", strip_image("green", "w1"), 4, emit=0.6, alpha=0.25)
MOTE = [mat(f"WR4 mote {i}", (0.03, 0.95, 0.25), emit=2.4 - 0.5 * i, alpha=a) for i, a in enumerate((0.95, 0.65, 0.4, 0.2))]
scene["MC FOV"] = 70.0
try:
    ui = scene.id_properties_ui("MC FOV"); ui.update(min=30.0, max=110.0, soft_min=30.0, soft_max=110.0, step=100,
                                                       description="Minecraft FOV (vertical) for every first-person camera")
except Exception as e:
    print("fov ui:", e)


def mc_fov(c):
    """Sensor Fit Vertical (Minecraft's FOV is vertical); lens driven by the scene's MC FOV: lens = 12 / tan(fov / 2)."""
    c.data.sensor_fit = "VERTICAL"; c.data.sensor_height = 24.0; c.data.clip_start = 0.02
    fc = c.data.driver_add("lens"); d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "fov"; v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = '["MC FOV"]'
    d.expression = "12 / tan(radians(fov) / 2)"


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


def arm_texture(tag, parent, z_hand, z_top, f0, f1, w=2.15, n=6):
    for k in range(n):
        za = z_hand + (z_top - z_hand) * k / n; zb = z_hand + (z_top - z_hand) * (k + 1) / n
        o = box(f"{tag} arm texture {k}", (-w * P, -w * P, min(za, zb)), (w * P, w * P, max(za, zb)), SKINTEX, parent)
        fa = int(f0 + (f1 - f0) * k / n)
        key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 6, sc=1.0)


def quad(name, m, parent, camobj, s=1.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-s / 2, -s / 2, 0), (s / 2, -s / 2, 0), (s / 2, s / 2, 0), (-s / 2, s / 2, 0)], [], [(0, 1, 2, 3)]); me.update()
    me.materials.append(m)
    o = link(bpy.data.objects.new(name, me)); o.parent = parent
    con = o.constraints.new("TRACK_TO"); con.target = camobj; con.track_axis = "TRACK_Z"; con.up_axis = "UP_Y"
    return o


def halo_mat(tag):
    """Soft round falloff, saturated green, never white: emission 2.0 mixed with transparency by a squared radial."""
    m = bpy.data.materials.new(tag + " halo"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    sc_ = N.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs["Scale"].default_value = 2.0
    L.new(tc.outputs["Object"], sc_.inputs[0])
    gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; L.new(sc_.outputs[0], gr.inputs["Vector"])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.4; L.new(gr.outputs["Fac"], pw.inputs[0])
    inten = N.new("ShaderNodeValue"); inten.name = "intensity"
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(pw.outputs[0], mul.inputs[0]); L.new(inten.outputs[0], mul.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.03, 1.0, 0.22, 1); em.inputs["Strength"].default_value = 2.0
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(mul.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m, inten


def fx_halo(tag, pt, camobj, size, f0=40):
    """W2d: one billboard on the ring, fading in 40-52 then breathing slowly (period 40 ticks), 0.45-0.7 strength."""
    m, inten = halo_mat(tag)
    o = quad(tag + " halo", m, pt, camobj)
    for f in [1, f0] + list(range(f0 + 12, FRAME_END + 1, 10)):
        u = 0.0 if f <= f0 else 0.575 + 0.125 * math.sin((f - f0) * 2 * math.pi / 40)
        inten.outputs[0].default_value = u; inten.outputs[0].keyframe_insert("default_value", frame=f)
        s = size * (0.7 if f <= f0 else 1.0 + 0.08 * math.sin((f - f0) * 2 * math.pi / 40))
        o.scale = (s, s, s); o.keyframe_insert("scale", frame=f)


def fx_motes(tag, pt, camobj, s=0.035, f0=40):
    """W2e: one square mote every 3 ticks off the ring; drifts up 0.45 m over 20 ticks with a sway, shrinks out.
    World-space (they stay behind as the hand moves), like particles."""
    for f in range(f0, FRAME_END - 4, 3):
        scene.frame_set(f); bpy.context.view_layer.update()
        p0 = pt.matrix_world.translation.copy() + Vector(rng.uniform(-0.03, 0.03, 3))
        o = quad(f"{tag} mote {f}", MOTE[0], None, camobj, s)
        ph = rng.uniform(0, 6.28)
        key(o, 1, loc=tuple(p0), sc=0.0001); key(o, f - 1, loc=tuple(p0), sc=0.0001)
        for k in range(0, 21, 4):
            u = k / 20
            sway = Vector((0.035 * math.sin(ph + u * 6), 0.035 * math.cos(ph + u * 5), 0))
            sz = (1.0 - u) * (1.15 if (k // 4) % 2 else 0.85)               # shrinking, a little flicker
            key(o, f + k, loc=tuple(p0 + Vector((0, 0, 0.45 * u)) + sway * u), sc=max(sz, 0.0001))


def fx_orbit(tag, pt, camobj, r=0.13, s=0.03, f0=40):
    """W2f: three motes on tilted orbits round the fist (one turn per 40 ticks), each trailing 3 fading copies."""
    for j in range(3):
        tilt = Matrix.Rotation(R(35 + 50 * j), 3, "X") @ Matrix.Rotation(R(120 * j), 3, "Z")
        for t, m in enumerate(MOTE):
            o = quad(f"{tag} orbit {j} {t}", m, pt, camobj, s * (1.0 - 0.18 * t))
            key(o, 1, sc=0.0001); key(o, f0 - 1 + 2 * t, sc=0.0001)
            for f in range(f0 + 2 * t, FRAME_END + 1, 2):
                a = (f - 1.5 * t) * 2 * math.pi / 40 + j * 2.1
                p = tilt @ Vector((r * math.cos(a), r * math.sin(a), 0))
                key(o, f, loc=tuple(p), sc=1.0)


def ring_mats(tag):
    M = player_mats(tag)
    M["ring"] = mat(f"{tag} ring face", RINGC, emit=1.6)
    return M


def rise_z(f):
    return 0.07 * max(0, f - 10) + 0.0004 * max(0, f - 10) ** 2


W2_BEND = 50
SKINTEX2 = strip_mat("WR4 arm texture bright", strip_image("green", "w1"), 4, emit=1.5, alpha=0.75)
COLLAR = mat("WR4 forming edge", (0.02, 0.9, 0.12), emit=2.0, alpha=0.85, rough=0.2)
TAIL = [mat(f"WR4 comet {i}", (0.03, 0.95, 0.25), emit=2.6 - 0.32 * i, alpha=0.95 - 0.14 * i) for i in range(7)]


def arm_glow_build(tag, slices, f0, f1, src_pt, w=2.3, px=P):
    """W2d2: the arm glow forming, built so you can see it: `slices` = [(parent, z_lo, z_hi)] in order from the fist
    up the arm. Each slice of bright construct texture grows in from the fist side over 5 ticks, a glowing collar rides
    its leading edge, and a pixel flies from the ring to it. Bright (1.5) but green, never white."""
    n = len(slices); pm = pixel_mesh(COLLAR)
    for k, (par, za, zb) in enumerate(slices):
        fa = int(round(f0 + (f1 - f0) * k / n))
        # grows from the fist end (za, nearer the fist) toward zb: an empty at za scales along Z
        piv = empty(f"{tag} glow slice pivot {k}", (0, 0, za), par)
        o = box(f"{tag} glow slice {k}", (-w * px, -w * px, 0), (w * px, w * px, zb - za), SKINTEX2, piv)
        if zb < za:
            o.scale = (1, 1, 1)
        key(piv, 1, sc=(1, 1, 0.0001)); key(piv, fa, sc=(1, 1, 0.0001)); key(piv, fa + 5, sc=(1, 1, 1))
        cl = box(f"{tag} glow edge {k}", (-(w + 0.35) * px, -(w + 0.35) * px, -0.4 * px), ((w + 0.35) * px, (w + 0.35) * px, 0.4 * px),
                 COLLAR, par)
        key(cl, 1, loc=(0, 0, za), sc=0.0001); key(cl, fa - 1, loc=(0, 0, za), sc=0.0001)
        key(cl, fa, loc=(0, 0, za), sc=1.0); key(cl, fa + 5, loc=(0, 0, zb), sc=1.0); key(cl, fa + 6, loc=(0, 0, zb), sc=0.0001)
        # a pixel from the ring to the slice's middle
        scene.frame_set(max(1, fa - 4)); bpy.context.view_layer.update()
        s0 = src_pt.matrix_world.translation.copy()
        scene.frame_set(fa); bpy.context.view_layer.update()
        tgt = par.matrix_world @ Vector((w * px, 0, (za + zb) / 2))
        pxo = link(bpy.data.objects.new(f"{tag} glow pixel {k}", pm))
        key(pxo, 1, loc=tuple(s0), sc=0.0001); key(pxo, fa - 5, loc=tuple(s0), sc=0.0001); key(pxo, fa - 4, loc=tuple(s0), sc=0.6)
        key(pxo, fa - 2, loc=tuple((s0 + tgt) / 2 + Vector((0, 0, 0.06))), sc=0.6); key(pxo, fa, loc=tuple(tgt), sc=0.45)
        key(pxo, fa + 1, loc=tuple(tgt), sc=0.0001)


def fx_carousel(tag, pt, camobj, r=0.12, s=0.026, f0=40, n=8):
    """W2f1: n motes on one flat ring round the fist (plane across the arm), the ring spins once per 30 ticks, each
    mote bobs along the arm; they appear one by one (2 ticks apart). No trails."""
    hub = empty(f"{tag} carousel", (0, 0, 0), pt)
    for f in range(1, FRAME_END + 1, 3):
        key(hub, f, rot=(0, 0, (f - f0) * 2 * math.pi / 30))
    for j in range(n):
        o = quad(f"{tag} carousel mote {j}", MOTE[0], hub, camobj, s)
        a = 2 * math.pi * j / n; fa = f0 + 2 * j
        key(o, 1, loc=(r * math.cos(a), r * math.sin(a), 0), sc=0.0001); key(o, fa - 1, loc=(r * math.cos(a), r * math.sin(a), 0), sc=0.0001)
        for f in range(fa, FRAME_END + 1, 3):
            bob = 0.025 * math.sin(f * 2 * math.pi / 20 + j * 1.3)
            key(o, f, loc=(r * math.cos(a), r * math.sin(a), bob), sc=1.0 if f > fa else 0.5)


def fx_comet(tag, pt, camobj, r=0.14, s=0.045, f0=40):
    """W2f2: one bigger mote looping a figure-8 round the ring (a lap per 24 ticks), with a 6-step fading tail
    (each copy one tick behind and smaller)."""
    for t, m in enumerate(TAIL):
        o = quad(f"{tag} comet {t}", m, pt, camobj, s * (1.0 - 0.11 * t))
        key(o, 1, sc=0.0001); key(o, f0 - 1 + t, sc=0.0001)
        for f in range(f0 + t, FRAME_END + 1):
            a = (f - t - f0) * 2 * math.pi / 24
            p = Vector((r * math.sin(a), 0.6 * r * math.sin(2 * a), 0.35 * r * math.cos(a)))
            key(o, f, loc=tuple(p), sc=1.0)


def fx_helix(tag, par, z0, z1, rad, camobj, s=0.028, f0=40, life=30):
    """W2f3: three motes spiral up the arm (two turns from the fist toward the elbow over `life` ticks), each with a
    2-step trail, then start again at the fist. Parented to the arm, so they wrap it."""
    for j in range(3):
        for t, m in enumerate(MOTE[:3]):
            o = quad(f"{tag} helix {j} {t}", m, par, camobj, s * (1.0 - 0.2 * t))
            start = f0 + 10 * j + 2 * t
            key(o, 1, loc=(rad, 0, z0), sc=0.0001); key(o, start - 1, loc=(rad, 0, z0), sc=0.0001)
            c0 = start
            while c0 < FRAME_END:
                for k in range(0, life + 1, 2):
                    u = k / life; a = u * 4 * math.pi + j * 2.1
                    sz = 0.0001 if (k == 0 or k == life) else 1.0
                    key(o, c0 + k, loc=(rad * math.cos(a), rad * math.sin(a), z0 + (z1 - z0) * u), sc=sz)
                c0 += life + 1


def bend_at(kind, f, su):
    """Fist bend at tick f: an int bends to that angle with the lift-off (su); (a, b) swings to a on lift-off like
    W5b, then settles back to b between ticks 30 and 46."""
    if isinstance(kind, tuple):
        a, b = kind
        return a * su if f <= 30 else a + (b - a) * smooth((f - 30) / 16)
    return kind * su


TAKES = [("W2d2", "halo, arm glow you can see", "glow"),
         ("W2f1", "orbit, carousel", "carousel"), ("W2f2", "orbit, comet", "comet"), ("W2f3", "orbit, helix", "helix"),
         ("W5a", "rise, fist back 45 (as before)", 45),
         ("W5a1", "rise, fist back 50", 50), ("W5a2", "rise, fist back 55", 55), ("W5a3", "rise, fist back 60", 60),
         ("W5a4", "rise, fist back 65", 65),
         ("W5b1", "rise, fist back 75 to 65", (75, 65)), ("W5b2", "rise, fist back 75 to 60", (75, 60)),
         ("W5b3", "rise, fist back 75 to 55", (75, 55))]
W2KINDS = ("glow", "carousel", "comet", "helix")
DIAG = {}
for bi, (tk, name, kind) in enumerate(TAKES):
    col = bpy.data.collections.new(f"{tk} {name}")
    ROOTCOL.children.link(col)
    bx = bi * BAY
    tag = f"WR4 {tk}"
    M = ring_mats(tag)
    eye = Vector((bx, 30.0, 1.62))
    fpr = fp_arms(tag, eye, M)
    fpr["wrist"].rotation_mode = "XYZ"
    title = f"Cam {tk} {name}"
    fcam = cam(f"{title} - first person", tuple(eye), tuple(eye + Vector((0, 3, 0))), 26)
    mc_fov(fcam)
    if kind in W2KINDS:
        box(f"{tag} floor", (bx - 2.2, -3, -0.02), (bx + 2.2, 3, 0), FLOOR)
        box(f"{tag} fp floor", (bx - 2.2, 26, -0.02), (bx + 2.2, 40, 0), FLOOR)
        rig = make_player(tag, (bx, 0, 0), M, face=math.pi)
        hand_3p(tag, rig, M)
        glow = kind == "glow"
        # W2d2: the first-person arm sits higher and more to the middle and the camera looks down a little more, so
        # the sleeve (where the glow forms) stays in view; the other W2 takes keep 831's framing.
        fx_, fy_, fd_, cp_ = (0.12, -0.08, 0.62, -12) if glow else (0.2, -0.16, 0.6, -6)
        for f in range(1, FRAME_END + 1, 20):
            s = math.sin(f / FRAME_END * 2 * math.pi)
            pose(rig, f, arm_r=(38 + 3 * s, 0, -6), fore_r=(42, 0, -70), arm_l=(4, 0, 4), fore_l=(8, 0, 0), head=(-12, 0, 0),
                 body=(1.5 * s, 0, 0), wrist_r=(0, -40, 0))
            fcam.rotation_euler = (R(90 + cp_), 0, 0); fcam.keyframe_insert("rotation_euler", frame=f)
            fp_ring_key(fpr, f, eye, cp_, fx_, fy_ + 0.01 * math.sin(f * 0.05), fd_, W2_BEND)
            fp_key(fpr, "l", f, eye, cp_, -0.55, -0.6, 0.4, 0)
        anim_emit(M["ring"], [(1, 0.9), (20, 0.9), (60, 1.5), (90, 1.35), (120, 1.5)])
        c3 = cam(f"{title} - third person", (bx + 2.0, -3.9, 1.6), (bx, 0, 1.1), 40)
        if glow:
            # fist (wrist), forearm, upper arm: 10 slices from the knuckles to the shoulder, ticks 10-60
            sl3 = [(rig["wrist_r"], -2 * P, -1 * P), (rig["wrist_r"], -1 * P, 0)]
            sl3 += [(rig["fore_r"], -4 * P + k * P, -3 * P + k * P) for k in range(4)]
            sl3 += [(rig["arm_r"], -6 * P + k * 2 * P, -4 * P + k * 2 * P) for k in range(4)]
            arm_glow_build(tag + " 3p", sl3, 10, 60, rig["ring_pt"])
            pxf = P * 1.05
            slf = [(fpr["wrist"], -4 * pxf + k * pxf, -3 * pxf + k * pxf) for k in range(4)]
            slf += [(fpr["r"], -8 * pxf + k * 4 * pxf / 3, -8 * pxf + (k + 1) * 4 * pxf / 3) for k in range(6)]
            arm_glow_build(tag + " fp", slf, 10, 60, fpr["ring_pt"], px=pxf)
            fx_halo(tag + " 3p", rig["ring_pt"], c3, 0.3, f0=60); fx_halo(tag + " fp", fpr["ring_pt"], fcam, 0.22, f0=60)
        else:
            arm_texture(tag, rig["fore_r"], -4 * P, 0, 10, 40, n=4)
            arm_texture(tag + " upper", rig["arm_r"], -6 * P, 2 * P, 40, 70)
            arm_texture(tag + " fp", fpr["r"], -8 * P * 1.05, 0, 10, 70, w=2.15 * 1.05, n=6)
        if kind == "carousel":
            fx_carousel(tag + " 3p", rig["ring_pt"], c3); fx_carousel(tag + " fp", fpr["ring_pt"], fcam, 0.09, 0.022)
        if kind == "comet":
            fx_comet(tag + " 3p", rig["ring_pt"], c3); fx_comet(tag + " fp", fpr["ring_pt"], fcam, 0.1, 0.034)
        if kind == "helix":
            fx_helix(tag + " 3p", rig["fore_r"], -6.5 * P, 0, 3.2 * P, c3)
            fx_helix(tag + " fp", fpr["wrist"], -4.5 * P * 1.05, 3 * P * 1.05, 3.6 * P * 1.05, fcam, 0.028, life=24)   # fp: round the fist, in view
        board_lines = ["For: the ring charged / a power ready, standing.",
                       "Ring on the punching face (jar placement).",
                       {"glow": "10-60  bright texture builds fist -> shoulder,",
                        "carousel": "10-70  the construct texture forms on the arm",
                        "comet": "10-70  the construct texture forms on the arm",
                        "helix": "10-70  the construct texture forms on the arm"}[kind],
                       {"glow": "       a glowing edge rides it, pixels fly in",
                        "carousel": "40->   8 motes on one spinning ring round the fist",
                        "comet": "40->   one comet mote loops a figure-8, 6-step tail",
                        "helix": "40->   3 motes spiral up the arm to the elbow"}[kind],
                       "60->   one soft glow sprite on the ring" if glow else "Ring glow 0.9 -> 1.5, saturated green."]
        board(tag, (bx, 1.6, 2.75), f"{tk}  {name.upper()}", board_lines)
    else:
        box(f"{tag} floor", (bx - 2.2, -3, -0.02), (bx + 2.2, 3, 0), FLOOR)
        rig = make_player(tag, (bx, 0, 0.0), M, face=math.pi)
        hand_3p(tag, rig, M)
        # W4b kept: arm 135 deg, body hangs under it, head down 40, legs trail; back of the hand turned up and the fist
        # bent back at the wrist (bend_at: W5a-style straight to the angle, W5b-style 75 then settle down).
        best = None
        for tw in (-90, 90):
            pose(rig, 200, arm_r=(135, 0, -6), fore_r=(6, 0, tw), wrist_r=(0, 0, 0))
            scene.frame_set(200); bpy.context.view_layer.update()
            up = (rig["wrist_r"].matrix_world.to_3x3() @ Vector((1, 0, 0))).z
            if best is None or up > best[1]:
                best = (tw, up)
        for o in (rig["arm_r"], rig["fore_r"], rig["wrist_r"]):
            if o.animation_data:
                o.animation_data_clear()
        TW = best[0]
        fr3 = sorted(set(list(range(1, FRAME_END + 1, 4)) + ([30, 38, 46] if isinstance(kind, tuple) else [])))
        for f in fr3:
            u = min(1.0, f / 30.0); su = smooth(u)
            s = math.sin(f * 0.25)
            pose(rig, f, root_loc=(bx, 0, 0.4 + rise_z(f)),
                 arm_r=(135 * su + 10 * (1 - su), 0, -6), fore_r=(6, 0, TW * su),
                 arm_l=(-12 + 3 * s, 0, 12), fore_l=(18, 0, 0), body=(-4, 0, 0), head=(-40 * su, 0, 0),
                 leg_r=(-8 + 4 * s, 0, 0), shin_r=(-14, 0, 0), leg_l=(-4 - 4 * s, 0, 0), shin_l=(-20, 0, 0),
                 wrist_r=(0, -bend_at(kind, f, su), 0))
        anim_emit(M["ring"], [(1, 1.1), (20, 1.6), (FRAME_END, 1.6)])
        for k in range(10):                                                    # W4b's pull streaks, kept
            f0 = 14 + k * 9
            st = box(f"{tag} pull streak {k}", (-0.004, -0.004, 0), (0.004, 0.004, 0.5), RAY, rig["ring_pt"])
            off = Vector(rng.uniform(-0.12, 0.12, 3)); off.z = 0
            key(st, 1, loc=tuple(off), sc=0.0001); key(st, f0, loc=tuple(off + Vector((0, 0, -0.1))), sc=1.0)
            key(st, f0 + 8, loc=tuple(off + Vector((0, 0, 0.6))), sc=0.0001)
        frf = sorted(set(list(range(1, FRAME_END + 1, 6)) + ([30, 38, 46] if isinstance(kind, tuple) else [])))
        for f in frf:
            u = min(1.0, f / 30.0); su = smooth(u)
            ef = eye + Vector((0, 0, rise_z(f)))
            fcam.rotation_euler = (R(90 - 10 * su), 0, 0); fcam.keyframe_insert("rotation_euler", frame=f)
            key(fcam, f, loc=tuple(ef))
            fp_ring_key(fpr, f, ef, -10 * su, 0.16, -0.26 + su * 0.12 + 0.006 * math.sin(f * 0.3), 0.75 - su * 0.15,
                        bend_at(kind, f, su))
            fp_key(fpr, "l", f, ef, -10 * su, -0.55, -0.6, 0.4, 0)
        box(f"{tag} fp ground", (bx - 2.2, 24, -0.02), (bx + 2.2, 44, 0), FLOOR)
        c3 = cam(f"{title} - third person", (bx + 3.2, -4.8, 2.4), (bx, 0, 1.3), 35)
        for f in range(1, FRAME_END + 1, 10):
            key(c3, f, loc=(bx + 3.2, -4.8, 2.4 + rise_z(f)))
        if isinstance(kind, tuple):
            bl = [f"New: the fist swings back {kind[0]} on lift-off (as W5b),",
                  f"then settles down to {kind[1]} deg by tick 46 and holds."]
            ttl = f"{tk}  RISE, FIST BACK {kind[0]} -> {kind[1]}"
        else:
            bl = [f"Back of the hand up, fist bent back {kind} deg at the",
                  "wrist so the ring on the punching face shows." + ("  (W5a as before)" if tk == "W5a" else "")]
            ttl = f"{tk}  RISE, FIST BACK {kind}"
        board_lines = ["For: ONLY while holding space in flight (rising).",
                       "W4b kept: ring arm up ahead at 135 deg, head down 40."] + bl
        board(tag, (bx, 1.6, 2.75), ttl, board_lines)
    DIAG[tk] = (fcam, fpr["ring_pt"])
col = ROOTCOL
# check: where the ring sits in each first-person view at tick 70 and whether its face looks at the eye
from bpy_extras.object_utils import world_to_camera_view
scene.frame_set(70); bpy.context.view_layer.update()
for tk, (fc, pt) in DIAG.items():
    p = pt.matrix_world.translation
    v = world_to_camera_view(scene, fc, p)
    nrm = (pt.parent.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    toeye = (fc.matrix_world.translation - p).normalized()
    print(f"DIAG {tk}: ring at screen ({v.x:.2f}, {v.y:.2f}) depth {v.z:.2f}  face-to-eye angle {math.degrees(nrm.angle(toeye)):.0f}")
cam("Cam all", ((len(TAKES) - 1) / 2 * BAY, -44, 6.0), ((len(TAKES) - 1) / 2 * BAY, 0, 1.8), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam W2d2 halo, arm glow you can see - first person", 50, (0.3, 0.38, 0.5), 3.0


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
