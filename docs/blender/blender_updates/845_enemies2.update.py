# Pass 845: enemies2, E1 variations (rings/suits chat, 2026-10-15, range 800-899). Follows 812.
# J rated 812 E1 Dread Wisp (fear) IMPROVE with no note: "3 new variations each", labelled, he picks. E2 Ember Brute
# and E3 Leech Mite were DROPPED. From 812, J picked "enemy designs (original fear creature, rage beast, parasite) with
# idle, attack and death animations". All original designs: no comic characters, corps logos or names.
# E1 was a gaunt shade with a halo of six yellow eye-plates, four tendrils and long clawed arms; its attack was a cone
# of yellow fear light. Each new take is a fear creature built a different way (shape, motion, construction):
#   E1a Veil Wisp: a hooded crown with a shroud of 14 hanging two-link strips and ONE big yellow eye hidden inside.
#       Idle: hovers, the strips ripple, the eye glimmers through the gaps. Attack: the shroud splits open like petals
#       at the front, the eye pushes out and a narrow gaze beam pins the player, who freezes and shivers, sliding back.
#       Death: the eye bursts first, the strips wilt outward one by one, then it falls apart into dark pixels.
#   E1b Mask Swarm: no body, a dark smoky core with ten floating mask-plates (two yellow eye slits each) orbiting it.
#       Idle: the masks circle on a tilted ring. Attack: the masks rush the player and ring his head facing inward,
#       blinking to new places every few ticks while their eyes flare; the player crouches with both arms over his
#       head. Death: the core pops, every mask's eyes go dark, the masks drop to the floor and crumble.
#   E1c Stilt Stalker: a dark body high on four long two-joint stilt legs, a telescoping four-part neck and a caged
#       head with three yellow eyes in a column. Idle: slow steps in place, the head sways. Attack: it leans in, the
#       neck slides out to the player's face, the eyes open top to bottom and a yellow fear pool spreads under the
#       player, who stumbles back. Death: the legs buckle one by one, it drops, then dissolves top down.
# Same clock for all (20 ticks a second): idle 1-40, attack 41-80 (at a player stand-in), death 81-130 (the player's
# construct shot hits it). Cameras "Cam <take>", "Cam <take> close", "Cam all". Builds LanternLive\combat\enemies2.blend.
SCENE_NAME = "Enemies E1 variations"
OUT_REL = "combat/enemies2.blend"
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
IDLE, ATK, DIE = 1, 41, 81
FLOOR = mat("EN floor", (0.16, 0.17, 0.16), rough=0.9)
LBL = mat("EN label", (0.3, 1.0, 0.45), emit=2.0)
SHADE = mat("EN shade", (0.03, 0.025, 0.04), rough=0.5)
PLATE = mat("EN dark plate", (0.08, 0.06, 0.1), rough=0.3, metal=0.4)
SMOKE = mat("EN smoke", (0.04, 0.03, 0.06), emit=0.0, alpha=0.7, rough=0.8)
YEL = mat("EN fear yellow", (1.0, 0.78, 0.04), emit=3.0)
YELC = mat("EN fear cone", (1.0, 0.75, 0.04), emit=1.5, alpha=0.3)
YELB = mat("EN fear beam core", (1.0, 0.75, 0.04), emit=2.5, alpha=0.6)
EYE_A = mat("EN E1a eye", (1.0, 0.78, 0.04), emit=3.0)
EYE_B = mat("EN E1b mask eyes", (1.0, 0.78, 0.04), emit=3.0)
EYE_C = mat("EN E1c eyes", (1.0, 0.78, 0.04), emit=3.0)
rng = np.random.default_rng(845)
CM = cmats("EN", "green")


def target(tag, loc, face=math.pi):
    M = player_mats(tag)
    rig = make_player(tag, loc, M, face=face)
    pose(rig, 1, arm_r=(0, 0, 0), arm_l=(0, 0, 0), head=(0, 0, 0), body=(0, 0, 0), leg_r=(0, 0, 0), leg_l=(0, 0, 0),
         shin_r=(0, 0, 0), shin_l=(0, 0, 0))
    return rig, M


def shot(tag, src, dst, f_hit):
    """A construct shot from the player's ring to the enemy (6 ticks)."""
    o = ball(f"{tag} construct shot", 0.12, CM["rim"])
    key(o, 1, loc=src, sc=0.0001); key(o, f_hit - 7, loc=src, sc=0.0001); key(o, f_hit - 6, loc=src, sc=1.0)
    key(o, f_hit, loc=dst, sc=1.0); key(o, f_hit + 1, loc=dst, sc=0.0001)


def meshes(root):
    return [o for o in root.children_recursive if o.type == "MESH"]


def at(f):
    scene.frame_set(f); bpy.context.view_layer.update()


def face_rot(d, prev=None):
    """Euler (pitch, 0, yaw) turning local +Y toward d; yaw unwrapped next to prev."""
    yaw = math.atan2(d[1], d[0]) - math.pi / 2
    if prev is not None:
        while yaw - prev > math.pi:
            yaw -= 2 * math.pi
        while yaw - prev < -math.pi:
            yaw += 2 * math.pi
    return (math.atan2(d[2], math.hypot(d[0], d[1])), 0.0, yaw), yaw


TAKES = (("E1a", "Veil Wisp"), ("E1b", "Mask Swarm"), ("E1c", "Stilt Stalker"))
for bi, (tk, name) in enumerate(TAKES):
    bx = bi * BAY
    tag = f"EN {tk}"
    box(f"{tag} floor", (bx - 4, -4, -0.02), (bx + 4, 6, 0), FLOOR)
    prig, PM = target(tag + " player", (bx, -1.8, 0), face=0.0)          # the player faces +Y toward the enemy
    eroot = empty(f"{tag} enemy", (bx, 2.5, 0)); eroot.rotation_euler = (0, 0, math.pi)   # enemy local +Y = toward player
    at(1)
    extra = []                                       # enemy meshes not parented under eroot
    if tk == "E1a":
        # ---- Veil Wisp: hooded crown, a shroud of 14 two-link strips, one big eye hidden inside
        body = empty(f"{tag} body", (0, 0, 1.55), eroot)
        hd = empty(f"{tag} crown", (0, 0, 0), body)
        box(f"{tag} hood", (-0.26, -0.26, 0.0), (0.26, 0.26, 0.34), SHADE, hd)
        box(f"{tag} hood top", (-0.18, -0.18, 0.34), (0.18, 0.18, 0.46), SHADE, hd)
        for k in range(8):
            a = 2 * math.pi * k / 8
            sp = empty(f"{tag} crown spike {k}", (0.27 * math.cos(a), 0.27 * math.sin(a), 0.3), hd)
            sp.rotation_euler = (0, R(-25), a)
            box(f"{tag} crown spike box {k}", (-0.025, -0.025, 0), (0.025, 0.025, 0.22), PLATE, sp)
        box(f"{tag} collar", (-0.34, -0.34, -0.06), (0.34, 0.34, 0.02), PLATE, body)
        strips = []
        NS = 14
        for k in range(NS):
            a = 2 * math.pi * k / NS
            pv = empty(f"{tag} strip {k}", (0.32 * math.cos(a), 0.32 * math.sin(a), -0.04), body)
            box(f"{tag} strip top {k}", (-0.07, -0.012, -0.55), (0.07, 0.012, 0.0), SHADE, pv)
            lo = empty(f"{tag} strip joint {k}", (0, 0, -0.55), pv)
            box(f"{tag} strip low {k}", (-0.055, -0.01, -0.5), (0.055, 0.01, 0.0), PLATE, lo)
            box(f"{tag} strip tip {k}", (-0.02, -0.01, -0.62), (0.02, 0.01, -0.5), PLATE, lo)
            yaw = a + math.pi / 2                   # local X tangential, local -Y outward
            front = max(0.0, math.cos(a - math.pi / 2))   # 1 at the front strip (enemy +Y), 0 at the sides/back
            strips.append((pv, lo, yaw, front, k))
        eye = empty(f"{tag} eye", (0, 0, -0.25), body)
        ball(f"{tag} eye ball", 0.16, EYE_A, parent=eye, seg=16)
        box(f"{tag} pupil", (-0.03, 0.15, -0.09), (0.03, 0.18, 0.09), SHADE, eye)
        beam = cyl(f"{tag} gaze beam", 0.04, 4.0, YELC, 20, eye, loc=(0, 0.16, 0), axis="Y", r2=0.2)
        core = cyl(f"{tag} gaze core", 0.015, 4.0, YELB, 12, eye, loc=(0, 0.16, 0), axis="Y", r2=0.05)
        for b_ in (beam, core):
            key(b_, 1, sc=(1, 0.0001, 1)); key(b_, ATK + 13, sc=(0.0001, 0.0001, 0.0001))
            key(b_, ATK + 14, sc=(1, 0.05, 1)); key(b_, ATK + 17, sc=(1, 1, 1)); key(b_, ATK + 31, sc=(1, 1, 1))
            key(b_, ATK + 33, sc=(0.0001, 1, 0.0001))
        anim_emit(EYE_A, [(f, (0.8 + 0.6 * (0.5 + 0.5 * math.sin(f * 0.45))) if f < ATK + 8 else (4.5 if f <= ATK + 32 else 1.4))
                          for f in list(range(1, ATK + 8, 2)) + [ATK + 10, ATK + 32, ATK + 36]])
        for f in range(1, FRAME_END + 1, 2):
            t = f / 20.0
            key(body, f, loc=(0, 0, 1.55 + 0.1 * math.sin(t * 2.2)))
            key(hd, f, rot=(R(4 * math.sin(t * 1.3)), 0, R(8 * math.sin(t * 0.9))))
            if f >= DIE + 6:
                continue
            for pv, lo, yaw, front, k in strips:
                op = 0.0
                if ATK + 6 <= f <= ATK + 34:            # the front opens like petals
                    op = smooth((f - ATK - 6) / 6) * (1 - smooth((f - ATK - 30) / 4)) * front ** 2
                ripple = 10 * math.sin(t * 3.2 + k * 0.9)
                key(pv, f, rot=(R(-12 - 105 * op + ripple * (1 - op)), 0, yaw))
                key(lo, f, rot=(R(-8 * math.sin(t * 3.2 + k * 0.9 - 1.0) + 40 * op), 0, 0))
        key(eye, ATK + 6, loc=(0, 0, -0.25), sc=1.0); key(eye, ATK + 12, loc=(0, 0.42, -0.2), sc=1.35)
        key(eye, ATK + 32, loc=(0, 0.42, -0.2), sc=1.35); key(eye, ATK + 37, loc=(0, 0, -0.25), sc=1.0)
        # the player freezes in the gaze: arms half up, shivers, slides back
        pose(prig, ATK + 14, arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0), head=(0, 0, 0), root_loc=(bx, -1.8, 0))
        pose(prig, ATK + 17, arm_r=(45, 0, 15), arm_l=(45, 0, -15), head=(-10, 0, 0))
        for i, f in enumerate(range(ATK + 18, ATK + 32, 2)):
            pose(prig, f, body=(-6 - i * 0.6, 0, 4 if i % 2 else -4), root_loc=(bx, -1.8 - 0.06 * i, 0))
        pose(prig, ATK + 32, arm_r=(45, 0, 15), arm_l=(45, 0, -15), body=(-8, 0, 0), head=(-10, 0, 0), root_loc=(bx, -2.25, 0))
        pose(prig, ATK + 38, arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0), head=(0, 0, 0), root_loc=(bx, -1.8, 0))
        hit = DIE + 4
        dst_off = Vector((0, 0, 1.3))
        # death: the eye bursts, the strips wilt outward one by one, then it falls apart into dark pixels
        at(hit + 2)
        shatter(meshes(eye), hit + 2, EYE_A, rng, tag, n=5, speed=0.07)
        order = sorted(strips, key=lambda s_: -s_[3])
        for i, (pv, lo, yaw, front, k) in enumerate(order):
            fw = hit + 4 + i
            key(pv, fw, rot=(R(-12), 0, yaw)); key(pv, fw + 5, rot=(R(-100), 0, yaw)); key(lo, fw + 5, rot=(R(70), 0, 0))
        key(body, hit + 18, loc=(0, 0, 1.4)); key(body, hit + 26, loc=(0, 0, 0.9))
        at(hit + 26)
        rest = [o for o in meshes(eroot) if o not in meshes(eye)]
        rest.sort(key=lambda o: o.matrix_world.translation.z)
        for k, o in enumerate(rest):
            shatter([o], hit + 26 + k // 4, SHADE if "strip top" in o.name or "hood" in o.name else PLATE, rng, tag, n=1, speed=0.04)
        peak = ATK + 20
    elif tk == "E1b":
        # ---- Mask Swarm: a smoky core and ten floating masks with yellow eye slits
        body = empty(f"{tag} core", (0, 0, 1.5), eroot)
        for k, (o_, r_) in enumerate((((0, 0, 0), 0.22), ((0.1, 0.05, 0.08), 0.15), ((-0.09, -0.04, -0.07), 0.16))):
            ball(f"{tag} smoke {k}", r_, SMOKE, loc=o_, parent=body, seg=12)
        ball(f"{tag} ember", 0.05, YEL, parent=body, seg=8)
        C = Vector((bx, 2.5, 1.5))
        masks = []
        NM = 10
        for k in range(NM):
            m_ = empty(f"{tag} mask {k}", (0, 0, 0)); m_.rotation_mode = "XYZ"; m_.scale = (1.5, 1.5, 1.5)
            box(f"{tag} mask plate {k}", (-0.13, -0.02, -0.17), (0.13, 0.02, 0.15), PLATE, m_)
            box(f"{tag} mask brow {k}", (-0.14, -0.01, 0.06), (0.14, 0.045, 0.1), SHADE, m_)
            box(f"{tag} mask chin {k}", (-0.08, -0.02, -0.22), (0.08, 0.02, -0.17), PLATE, m_)
            for s in (-1, 1):
                box(f"{tag} mask eye {k} {s}", (s * 0.065 - 0.04, 0.02, 0.0), (s * 0.065 + 0.04, 0.03, 0.035), EYE_B, m_)
            box(f"{tag} mask mouth {k}", (-0.05, 0.02, -0.11), (0.05, 0.026, -0.095), SHADE, m_)
            masks.append(m_)
            extra.append(m_)
        prev = [None] * NM

        def orbit_key(f):
            t = f / 20.0
            for k, m_ in enumerate(masks):
                ph = 2 * math.pi * k / NM + t * 1.1
                p = C + Vector((0.95 * math.cos(ph), 0.95 * math.sin(ph), 0.3 * math.sin(ph + 0.6) + 0.08 * math.sin(t * 2)))
                rot, prev[k] = face_rot((math.cos(ph), math.sin(ph), 0), prev[k])
                key(m_, f, loc=tuple(p), rot=rot)

        for f in range(1, ATK + 5, 2):
            orbit_key(f)
        # the player cowers: crouch, both arms over the head
        pose(prig, ATK + 8, arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0), head=(0, 0, 0), leg_r=(0, 0, 0), leg_l=(0, 0, 0),
             shin_r=(0, 0, 0), shin_l=(0, 0, 0), root_loc=(bx, -1.8, 0))
        crouch = dict(arm_r=(165, 0, -35), arm_l=(165, 0, 35), body=(20, 0, 0), head=(25, 0, 0), leg_r=(55, 0, 0),
                      leg_l=(55, 0, 0), shin_r=(-105, 0, 0), shin_l=(-105, 0, 0))
        pose(prig, ATK + 13, root_loc=(bx, -1.8, -0.26), **crouch)
        pose(prig, ATK + 33, root_loc=(bx, -1.8, -0.26), **crouch)
        pose(prig, ATK + 39, arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0), head=(0, 0, 0), leg_r=(0, 0, 0), leg_l=(0, 0, 0),
             shin_r=(0, 0, 0), shin_l=(0, 0, 0), root_loc=(bx, -1.8, 0))
        at(ATK + 20)
        H = prig["head"].matrix_world @ Vector((0, 0, 4 * P))
        # attack: rush in and ring the head facing inward, blinking to new places every 4 ticks
        blinks = list(range(ATK + 12, ATK + 33, 4))
        for k, m_ in enumerate(masks):
            for bi_, fb in enumerate(blinks):
                al = 2 * math.pi * k / NM + bi_ * 0.83 + (k % 3) * 0.2
                p = H + Vector((0.78 * math.cos(al), 0.78 * math.sin(al), 0.3 * math.sin(3 * al + bi_)))
                rot, prev[k] = face_rot(tuple(H - p), prev[k])
                if bi_ > 0:
                    key(m_, fb - 1, loc=tuple(m_.location), rot=tuple(m_.rotation_euler))
                key(m_, fb, loc=tuple(p), rot=rot)
            key(m_, ATK + 35, loc=tuple(m_.location), rot=tuple(m_.rotation_euler))
        for f in range(ATK + 41, DIE + 5, 2):
            orbit_key(f)
        anim_emit(EYE_B, [(1, 2.0), (ATK + 10, 2.0)] + [(f, 6.0 if (f // 2) % 2 else 3.0) for f in range(ATK + 12, ATK + 34, 2)]
                  + [(ATK + 36, 2.0), (DIE + 6, 2.0), (DIE + 9, 0.0)])
        hit = DIE + 4
        dst_off = Vector((0, 0, 1.5))
        at(hit + 1)
        shatter(meshes(body), hit + 1, YEL, rng, tag, n=3, speed=0.08)
        # the masks go dark, drop to the floor face up, then crumble
        at(DIE + 5)
        for k, m_ in enumerate(masks):
            p0 = Vector(m_.location); fl = DIE + 7 + k % 4
            land = Vector((p0.x + rng.uniform(-0.2, 0.2), p0.y + rng.uniform(-0.2, 0.2), 0.03))
            key(m_, fl, loc=tuple(p0 + Vector((0, 0, 0.06))))
            key(m_, fl + 5, loc=tuple(land + Vector((0, 0, 0.45))), rot=(R(60), 0, m_.rotation_euler.z))
            key(m_, fl + 8, loc=tuple(land), rot=(R(90), 0, m_.rotation_euler.z + R(rng.uniform(-40, 40))))
        at(hit + 30)
        for k, m_ in enumerate(masks):
            shatter(meshes(m_), hit + 30 + k, PLATE, rng, tag, n=1, speed=0.03)
        peak = ATK + 20
    else:
        # ---- Stilt Stalker: a dark body on four long stilt legs, a telescoping neck and a caged head with three eyes
        BZ = 1.94
        body = empty(f"{tag} body", (0, 0, BZ), eroot)
        box(f"{tag} torso", (-0.3, -0.38, -0.16), (0.3, 0.38, 0.2), SHADE, body)
        for k in range(3):
            y = -0.25 + k * 0.25
            box(f"{tag} spine plate {k}", (-0.12, y - 0.08, 0.2), (0.12, y + 0.08, 0.32 - k * 0.03), PLATE, body)
        box(f"{tag} belly", (-0.22, -0.3, -0.24), (0.22, 0.3, -0.16), PLATE, body)
        legs = []
        for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
            d = Vector((sx, sy * 0.8, 0)).normalized()
            hip = empty(f"{tag} hip {k}", (sx * 0.26, sy * 0.3, -0.1), body)
            box(f"{tag} thigh {k}", (-0.05, -0.05, -1.2), (0.05, 0.05, 0.0), SHADE, hip)
            box(f"{tag} thigh plate {k}", (-0.07, -0.07, -0.6), (0.07, 0.07, -0.3), PLATE, hip)
            kn = empty(f"{tag} knee {k}", (0, 0, -1.2), hip)
            box(f"{tag} knee cap {k}", (-0.07, -0.07, -0.07), (0.07, 0.07, 0.07), PLATE, kn)
            box(f"{tag} shin {k}", (-0.035, -0.035, -1.38), (0.035, 0.035, 0.0), SHADE, kn)
            box(f"{tag} foot spike {k}", (-0.015, -0.015, -1.45), (0.015, 0.015, -1.38), PLATE, kn)
            psi = math.atan2(-d.x, d.y)
            legs.append((hip, kn, psi, k))
        nk = empty(f"{tag} neck base", (0, 0.38, 0.05), body)
        segs = []
        prev_ = nk
        for k in range(4):
            hw = 0.09 - k * 0.015
            s_ = empty(f"{tag} neck {k}", (0, 0.0 if k == 0 else 0.12, 0), prev_)
            box(f"{tag} neck box {k}", (-hw, 0.0, -hw), (hw, 0.8, hw), SHADE if k % 2 else PLATE, s_)
            segs.append(s_); prev_ = s_
        hd = empty(f"{tag} head", (0, 0.8, 0), segs[-1])
        c0, c1 = Vector((-0.17, 0.0, -0.2)), Vector((0.17, 0.34, 0.2))
        bt = 0.02
        for ax in range(3):                        # a bar on every edge of the cage (all twelve)
            o1, o2 = [i for i in range(3) if i != ax]
            for u in (c0[o1], c1[o1]):
                for v in (c0[o2], c1[o2]):
                    a_ = [0, 0, 0]; b_ = [0, 0, 0]
                    a_[ax], b_[ax] = c0[ax], c1[ax]
                    a_[o1], b_[o1] = u - bt, u + bt
                    a_[o2], b_[o2] = v - bt, v + bt
                    box(f"{tag} cage bar", a_, b_, PLATE, hd)
        box(f"{tag} skull", (-0.12, 0.03, -0.17), (0.12, 0.22, 0.17), SHADE, hd)
        eyes = []
        for k, z in enumerate((0.1, 0.0, -0.1)):
            e = empty(f"{tag} eye {k}", (0, 0.24, z), hd)
            ball(f"{tag} eye ball {k}", 0.045, EYE_C, parent=e, seg=10)
            eyes.append(e)
            key(e, 1, sc=(1, 1, 0.15)); key(e, ATK + 13 + 3 * k, sc=(1, 1, 0.15)); key(e, ATK + 16 + 3 * k, sc=(1.2, 1.2, 1.2))
            key(e, ATK + 33, sc=(1.2, 1.2, 1.2)); key(e, ATK + 37, sc=(1, 1, 0.3))
        anim_emit(EYE_C, [(1, 1.2), (ATK + 12, 1.2), (ATK + 20, 4.5), (ATK + 33, 4.5), (ATK + 38, 1.5)])
        pool = cyl(f"{tag} fear pool", 1.3, 0.02, YELC, 32, loc=(bx, -1.8, 0.01))
        extra.append(pool)
        key(pool, 1, sc=0.0001); key(pool, ATK + 15, sc=0.0001); key(pool, ATK + 16, sc=(0.05, 0.05, 1))
        key(pool, ATK + 23, sc=(1, 1, 1)); key(pool, ATK + 31, sc=(1.1, 1.1, 1)); key(pool, ATK + 35, sc=0.0001)
        # idle: slow steps in place, head sways; attack: lean in, neck slides out to the player's face
        for f in range(1, DIE + 6, 2):
            t = f / 20.0
            lean = smooth((f - ATK - 2) / 8) * (1 - smooth((f - ATK - 32) / 7))
            for hip, kn, psi, k in legs:
                ph = t * 3.0 + (0 if k in (0, 3) else math.pi)
                lift = max(0.0, math.sin(ph)) * (1 - lean)
                fwd = 6 * lean * (1 if k < 2 else -0.4)
                key(hip, f, rot=(R(50 + 10 * lift + fwd), 0, psi)); key(kn, f, rot=(R(-90 - 14 * lift), 0, 0))
            key(body, f, loc=(0, 0.3 * lean, BZ + 0.04 * math.sin(t * 6) + 0.1 * lean), rot=(R(-5 * lean), 0, R(3 * math.sin(t))))
            ext = smooth((f - ATK - 5) / 9) * (1 - smooth((f - ATK - 33) / 6))
            for k, s_ in enumerate(segs):
                if k > 0:
                    key(s_, f, loc=(0, 0.12 + 0.6 * ext, 0))
            key(nk, f, rot=(R(38 * (1 - ext) + 6 * ext + 4 * math.sin(t * 1.4)), 0, R(10 * math.sin(t * 0.8) * (1 - ext))))
            key(hd, f, rot=(R(-30 * (1 - ext)), 0, R(6 * math.sin(t * 1.7))))
        # the player stumbles back from the face, arms flung up
        pose(prig, ATK + 15, arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0), head=(0, 0, 0), root_loc=(bx, -1.8, 0))
        pose(prig, ATK + 19, arm_r=(120, 0, 30), arm_l=(110, 0, -30), body=(-18, 0, 0), head=(-20, 0, 0), root_loc=(bx, -2.2, 0))
        pose(prig, ATK + 25, body=(-12, 0, 6), root_loc=(bx, -2.55, 0)); pose(prig, ATK + 31, body=(-12, 0, -6), root_loc=(bx, -2.7, 0))
        pose(prig, ATK + 38, arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0), head=(0, 0, 0), root_loc=(bx, -2.7, 0))
        hit = DIE + 4
        dst_off = Vector((0, 0, BZ))
        # death: the legs buckle one by one, it drops, then dissolves top down
        for i, (hip, kn, psi, k) in enumerate(legs):
            fb = hit + 3 + 4 * i
            key(hip, fb, rot=(R(50), 0, psi)); key(kn, fb, rot=(R(-90), 0, 0))
            key(hip, fb + 4, rot=(R(86), 0, psi)); key(kn, fb + 4, rot=(R(-170), 0, 0))
        key(body, hit + 2, loc=(0, 0, BZ), rot=(0, 0, 0)); key(body, hit + 8, loc=(0, 0, BZ - 0.25), rot=(R(8), R(-6), 0))
        key(body, hit + 18, loc=(0, 0, 0.8), rot=(R(-10), R(12), 0))
        key(nk, hit + 6, rot=(R(30), 0, 0)); key(nk, hit + 18, rot=(R(5), 0, R(15)))
        key(hd, hit + 18, rot=(R(-5), 0, 0))
        anim_emit(EYE_C, [(hit + 4, 1.5), (hit + 10, 0.0)])
        at(hit + 26)
        rest = sorted(meshes(eroot), key=lambda o: -o.matrix_world.translation.z)
        for k, o in enumerate(rest):
            shatter([o], hit + 26 + k // 4, SHADE, rng, tag, n=1, speed=0.04)
        peak = ATK + 22
    # the player fires the construct shot that kills it
    at(hit - 8)
    pose(prig, hit - 8, arm_r=tuple(math.degrees(a) for a in prig["arm_r"].rotation_euler))
    pose(prig, hit - 6, arm_r=(90, 0, 0)); pose(prig, hit + 6, arm_r=(90, 0, 0)); pose(prig, hit + 20, arm_r=(10, 0, 0))
    at(hit - 6)
    src = tuple(prig["ring_pt"].matrix_world.translation)
    at(hit)
    dst = tuple(eroot.matrix_world.translation + dst_off)
    shot(tag, src, dst, hit)
    if tk == "E1c":
        cam(f"Cam {tk}", (bx + 5.2, -6.2, 3.4), (bx, 0.6, 1.4), 30)
        cam(f"Cam {tk} close", (bx + 5.6, -0.2, 2.2), (bx, 0.0, 1.5), 30)
    else:
        cam(f"Cam {tk}", (bx + 4.5, -5.5, 2.8), (bx, 0.8, 1.1), 30)
        cam(f"Cam {tk} close", (bx + 4.6, -0.1, 2.0), (bx, 0.1, 1.4), 30) if tk == "E1a" else \
            cam(f"Cam {tk} close", (bx + 3.6, -4.6, 2.8), (bx, -1.6, 1.2), 30)
    label(f"{tk}  {name}", (bx, 5.5, 3.4), LBL, 0.28)
    print(tk, "peak", peak)
cam("Cam all", (BAY, -17, 7.5), (BAY, 1, 1.2), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam E1a", 1, (0.18, 0.2, 0.26), 2.0
FRAME_END = 130


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
