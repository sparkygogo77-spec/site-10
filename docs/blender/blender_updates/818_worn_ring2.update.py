# Pass 818: worn ring round 2 - glow, rays and smoke, and rising while holding space (Chat C, 2026-10-15, 800-899).
# J on 805: "W2 worn ring, i would want my arm to slowly glow very lightly the texture forms on my arm but i would mainly
# like light rays and smoke whatever can be done. scrap W3 ... seeing the arm like that doesnt match the head frame ...
# lower the arm because it never goes up like that and angle it less in the third person view and probably the first
# person view, unless someone is solely holding space while flying they shouldnt be able to do this, instead i would
# want the arm angled higher and sitting lower and you can see the top of your ring pulling you upward and in third
# person you could be looking down and holding space still."
# W2 (ring charged, standing): the arm glows very lightly while the construct texture forms on it, hand to shoulder,
# slowly (W1 weave, 25% opaque); then the ring gives off:
#   W2a light rays: six thin rays fanning out of the ring face, turning slowly, breathing in length
#   W2b smoke: soft green wisps leaving the ring, rising, curling and spreading as they fade
#   W2c rays and smoke together
# W4 (replaces W3) rise: only while holding space in flight. The ring arm reaches up ahead, not straight overhead; the
# body hangs under it; third person looks down at the ground falling away. In first person the arm sits low in the
# frame but points up, so you see the top of the ring pulling you. Three arm angles:
#   W4a 120 deg (arm forward-up)     W4b 135 deg     W4c 150 deg (the highest; still not overhead)
# Cameras "Cam <take> <name> - third person" / "- first person", "Cam all". Builds LanternLive\combat\worn_ring2.blend.
SCENE_NAME = "Worn Ring 2"
OUT_REL = "combat/worn_ring2.blend"
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
FLOOR = mat("WR2 floor", (0.2, 0.22, 0.24), rough=0.9)
BOARD = mat("WR2 board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("WR2 text", (0.75, 1.0, 0.8), emit=1.2)
TXTH = mat("WR2 heading", (0.2, 1.0, 0.4), emit=2.2)
rng = np.random.default_rng(818)
RINGC = (0.02, 0.85, 0.15)
SMOKE = mat("WR2 smoke", (0.05, 0.7, 0.22), emit=0.5, alpha=0.18, rough=0.9)
RAY = mat("WR2 ray", (0.05, 0.9, 0.25), emit=1.8, alpha=0.4, rough=0.2)
SKINTEX = strip_mat("WR2 arm texture", strip_image("green", "w1"), 4, emit=0.6, alpha=0.25)
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




def arm_texture(tag, parent, z_hand, z_top, f0, f1, w=2.15, n=6):
    """The construct texture forming on the arm: n thin shells appear in turn from the hand up to the top."""
    for k in range(n):
        za = z_hand + (z_top - z_hand) * k / n; zb = z_hand + (z_top - z_hand) * (k + 1) / n
        o = box(f"{tag} arm texture {k}", (-w * P, -w * P, min(za, zb)), (w * P, w * P, max(za, zb)), SKINTEX, parent)
        fa = int(f0 + (f1 - f0) * k / n)
        key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 6, sc=1.0)


def rays(tag, parent, f0, scale=1.0):
    """Six thin rays fanning out of the ring face (+X side of the hand), turning slowly, lengths breathing."""
    hub = empty(f"{tag} ray hub", (0.2 * P, 0, 0), parent); hub.rotation_mode = "XYZ"
    for k in range(6):
        a = k * math.pi / 3
        r_ = empty(f"{tag} ray {k}", (0, 0, 0), hub); r_.rotation_euler = (a, 0, 0)
        ray = box(f"{tag} ray beam {k}", (0, -0.006, -0.006), (0.6 * scale, 0.006, 0.006), RAY, r_)
        ray.rotation_euler = (0, R(-55), 0)                    # leaning out of the face, fanning like a crown
        key(ray, 1, sc=(0.0001, 1, 1)); key(ray, f0 + k * 2, sc=(0.0001, 1, 1))
        for f in range(f0 + k * 2 + 6, FRAME_END + 1, 10):
            key(ray, f, sc=(0.7 + 0.35 * math.sin(f * 0.17 + k * 1.3), 1, 1))
    for f in range(1, FRAME_END + 1, 20):
        key(hub, f, rot=(f * 0.02, 0, 0))


def smoke(tag, src_obj, f0, up=(0, 0, 1)):
    """Soft wisps leaving the ring every 4 ticks, rising 0.6 m, curling, spreading and fading over 24 ticks."""
    for f in range(f0, FRAME_END - 6, 4):
        scene.frame_set(f); bpy.context.view_layer.update()
        p0 = src_obj.matrix_world.translation.copy()
        w = box(f"{tag} wisp {f}", (-0.03, -0.03, -0.03), (0.03, 0.03, 0.03), SMOKE); w.location = p0
        drift = Vector(rng.normal(0, 0.05, 3)); upv = Vector(up)
        key(w, 1, loc=tuple(p0), sc=0.0001); key(w, f - 1, loc=tuple(p0), sc=0.0001); key(w, f, loc=tuple(p0), sc=1.0)
        for k in (6, 12, 18, 24):
            u = k / 24
            curl = Vector((0.06 * math.sin(u * 5 + f), 0.06 * math.cos(u * 5 + f), 0))
            key(w, f + k, loc=tuple(p0 + upv * 0.6 * u + drift * u + curl), rot=(u * 2, u * 1.5, u), sc=1.0 + 2.2 * u if k < 24 else 0.0001)


def ring_mats(tag):
    M = player_mats(tag)
    M["ring"] = mat(f"{tag} ring face", RINGC, emit=1.6)
    return M


TAKES = [("W2a", "light rays", "W2"), ("W2b", "smoke", "W2"), ("W2c", "rays and smoke", "W2"),
         ("W4a", "rise, arm 120", 120), ("W4b", "rise, arm 135", 135), ("W4c", "rise, arm 150", 150)]
for bi, (tk, name, kind) in enumerate(TAKES):
    col = bpy.data.collections.new(f"{tk} {name}")
    ROOTCOL.children.link(col)
    bx = bi * BAY
    tag = f"WR2 {tk}"
    M = ring_mats(tag)
    eye = Vector((bx, 30.0, 1.62))
    fpr = fp_arms(tag, eye, M)
    title = f"Cam {tk} {name}"
    fcam = cam(f"{title} - first person", tuple(eye), tuple(eye + Vector((0, 3, 0))), 26)
    if kind == "W2":
        box(f"{tag} floor", (bx - 2.2, -3, -0.02), (bx + 2.2, 3, 0), FLOOR)
        box(f"{tag} fp floor", (bx - 2.2, 26, -0.02), (bx + 2.2, 40, 0), FLOOR)
        rig = make_player(tag, (bx, 0, 0), M, face=math.pi)
        # standing, ring hand a little forward and turned so the face is seen; a slow breath
        for f in range(1, FRAME_END + 1, 20):
            s = math.sin(f / FRAME_END * 2 * math.pi)
            pose(rig, f, arm_r=(38 + 3 * s, 0, -6), fore_r=(42, 0, 0), arm_l=(4, 0, 4), fore_l=(8, 0, 0), head=(-12, 0, 0),
                 body=(1.5 * s, 0, 0))
        for f in range(1, FRAME_END + 1, 20):
            fp_key(fpr, "r", f, eye, -6, 0.24, -0.24 + 0.01 * math.sin(f * 0.05), 0.78, 0)
            fp_key(fpr, "l", f, eye, -6, -0.55, -0.6, 0.4, 0)
            fcam.rotation_euler = (R(84), 0, 0); fcam.keyframe_insert("rotation_euler", frame=f)
        anim_emit(M["ring"], [(1, 1.2), (20, 1.2), (60, 2.2), (90, 2.0), (120, 2.2)])
        # the texture forms on the arm, hand to shoulder, ticks 10-70 (third person: forearm then upper arm)
        arm_texture(tag, rig["fore_r"], -6 * P, 0, 10, 40)
        arm_texture(tag + " upper", rig["arm_r"], -6 * P, 2 * P, 40, 70)
        arm_texture(tag + " fp", fpr["r"], -12 * P * 1.05, 0, 10, 70, w=2.15 * 1.05, n=8)
        if name in ("light rays", "rays and smoke"):
            rays(tag, rig["ring_pt"], 40); rays(tag + " fp", fpr["ring_pt"], 40, 0.8)
        if name in ("smoke", "rays and smoke"):
            smoke(tag, rig["ring_pt"], 40); smoke(tag + " fp", fpr["ring_pt"], 40)
        board_lines = ["For: the ring charged / a power ready, standing.",
                       "10-70  the arm glows very lightly as the construct",
                       "       texture forms on it, hand to shoulder",
                       "40->   " + {"light rays": "six thin rays fan out of the ring, turning slowly",
                                    "smoke": "soft wisps leave the ring, rise, curl, fade",
                                    "rays and smoke": "rays and smoke together"}[name],
                       "Ring glow 1.2 -> 2.2, always green."]
        cam(f"{title} - third person", (bx + 2.0, -3.9, 1.6), (bx, 0, 1.1), 40)
        board(tag, (bx, 1.6, 2.75), f"{tk}  {name.upper()}", board_lines)
    else:
        ang = kind
        box(f"{tag} floor", (bx - 2.2, -3, -0.02), (bx + 2.2, 3, 0), FLOOR)
        rig = make_player(tag, (bx, 0, 0.0), M, face=math.pi)
        # rising: holding space in flight. The ring arm reaches up ahead (not overhead), the body hangs under it,
        # legs trail a little, head down (40 deg, under the 57 limit) watching the ground fall away.
        for f in range(1, FRAME_END + 1, 4):
            u = min(1.0, f / 30.0)
            z = 0.4 + 0.07 * max(0, f - 10) + 0.0004 * max(0, f - 10) ** 2       # speeding up
            s = math.sin(f * 0.25)
            pose(rig, f, root_loc=(bx, 0, z),
                 arm_r=(ang * smooth(u) + 10 * (1 - smooth(u)), 0, -6), fore_r=(6, 0, 0),
                 arm_l=(-12 + 3 * s, 0, 12), fore_l=(18, 0, 0), body=(-4, 0, 0), head=(-40 * smooth(u), 0, 0),
                 leg_r=(-8 + 4 * s, 0, 0), shin_r=(-14, 0, 0), leg_l=(-4 - 4 * s, 0, 0), shin_l=(-20, 0, 0))
        anim_emit(M["ring"], [(1, 1.6), (20, 2.4), (FRAME_END, 2.4)])
        # the pull: thin streaks rushing down past the arm (the world moving away), from the ring upward is the pull
        for k in range(10):
            f0 = 14 + k * 9
            st = box(f"{tag} pull streak {k}", (-0.004, -0.004, 0), (0.004, 0.004, 0.5), RAY, rig["ring_pt"])
            off = Vector(rng.uniform(-0.12, 0.12, 3)); off.z = 0
            key(st, 1, loc=tuple(off), sc=0.0001); key(st, f0, loc=tuple(off + Vector((0, 0, -0.1))), sc=1.0)
            key(st, f0 + 8, loc=tuple(off + Vector((0, 0, 0.6))), sc=0.0001)
        # first person: the arm sits low in the frame but points up, the top of the ring face toward you
        lift = (ang - 120) / 30.0                                              # 0..1 across the three takes
        for f in range(1, FRAME_END + 1, 6):
            u = min(1.0, f / 30.0)
            hx, hy, hd = 0.18, -0.30 + smooth(u) * (0.08 + 0.06 * lift), 0.80 - smooth(u) * (0.18 + 0.12 * lift)
            fp_key(fpr, "r", f, eye, -10 * smooth(u), hx, hy + 0.006 * math.sin(f * 0.3), hd, 0)
            fp_key(fpr, "l", f, eye, -10 * smooth(u), -0.55, -0.6, 0.4, 0)
            fcam.rotation_euler = (R(90 - 10 * smooth(u)), 0, 0); fcam.keyframe_insert("rotation_euler", frame=f)
            key(fcam, f, loc=tuple(eye + Vector((0, 0, 0.07 * max(0, f - 10) + 0.0004 * max(0, f - 10) ** 2))))
            for side in ("r", "l"):                                            # the arms ride up with the camera
                sh = fpr[side]
                sh.location = sh.location + Vector((0, 0, 0.07 * max(0, f - 10) + 0.0004 * max(0, f - 10) ** 2))
                sh.keyframe_insert("location", frame=f)
        # the ground grid falling away under the first-person camera
        box(f"{tag} fp ground", (bx - 2.2, 24, -0.02), (bx + 2.2, 44, 0), FLOOR)
        cam(f"{title} - third person", (bx + 3.2, -4.8, 2.4), (bx, 0, 1.3), 35)
        tp = bpy.data.objects[f"{title} - third person"]
        for f in range(1, FRAME_END + 1, 10):                                 # the third-person camera follows up
            z = 0.4 + 0.07 * max(0, f - 10) + 0.0004 * max(0, f - 10) ** 2
            key(tp, f, loc=(bx + 3.2, -4.8, 2.4 + z - 0.4))
        board_lines = ["For: ONLY while holding space in flight (rising).",
                       f"Ring arm reaches up ahead at {ang} deg - not overhead;",
                       "the body hangs under it, legs trail, head down 40 deg",
                       "watching the ground fall away. First person: the arm",
                       "sits low in the frame, pointing up; you see the top",
                       "of the ring pulling you. Streaks run down past it."]
        board(tag, (bx, 1.6, 2.75), f"{tk}  RISE  (arm {ang} deg)", board_lines)
col = ROOTCOL
cam("Cam all", (2.5 * BAY, -16, 4.0), (2.5 * BAY, 0, 1.8), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam W2c rays and smoke - third person", 60, (0.3, 0.38, 0.5), 3.0


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
