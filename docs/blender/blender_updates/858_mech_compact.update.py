# Pass 858: Compact mech: new textures, more detail (rings/suits chat, 2026-10-15, range 800-899). Source: pass 821.
# J rated 821 MS Compact (0.6 size) IMPROVE: "Different texture, more detailed designs for the robots".
# Three new compact mechs, each 0.6 of the full mech (built in full-size units, the whole mech scaled to 0.6), sized for
# a villager or a small mob (the pilot shrinks with the mech). None use X3D1 (J asked for a different texture); each
# has its own texture from docs/texture_library, and much more detail than 821 MS: panel seams, rivets, joint drums,
# working pistons (sleeve + rod that slide as the joints move), vent grilles, sensor eyes, antennae, exhausts.
# Every design is built a different way, forms a different way, moves its own way and has its own attack.
# Other 821 takes: MA and MC were followed up in 843/851, MB was dropped; none are rebuilt here.
# Same clock for all (20 ticks a second): 1-24 form, 24-30 board, 30-35 seal, 36-76 move, 76-96 attack,
#   96-126 finisher, 130 end.
#   MS1 Workhorse (W1 neon weave, villager): a stocky biped loader. Sensor head with three eyes and antennae, chest core,
#       radiator fins and two exhaust stacks on the back, vented hips/calves/pauldrons, pistons on every knee, ankle and
#       elbow, ram forearms with three-finger hands. Printed: a scan plane rises from the floor and extrudes every part
#       upward as it passes. Brisk march with steam puffs, the head scanning; piston punch (the forearm ram fires the
#       fist out); finisher: double ram slam into the ground from overhead.
#   MS2 Crawler (V1 crystal, baby zombie): a four-legged walker, low hull with a sensor cluster (five eyes), a raised
#       pilot pod with a glass sensor dome, crystal spikes, two pincer arms with hydraulic jaws, pistons on every leg.
#       Grown like crystal: hull first, then each leg grows joint by joint, claws, spikes last. Diagonal-pair trot;
#       pincer lunge (snaps both claws shut); finisher: rears up on its back legs and stomps, crystal spikes burst
#       out of the ground in a ring.
#   MS3 Treadline (R2K1 dark jade, villager): a tracked mini-mech. Twin treads with animated cleats and spoked road
#       wheels, a turret cockpit with a barred canopy, headlights, a spinning radar dish, exhausts and an engine box,
#       four deployable anchors, a drill right arm and a three-finger grab claw left. Assembled on rails: plates slide
#       in from the sides along two glowing rails. Drives forward and pivot-turns on its treads (turret keeps facing
#       ahead); drill thrust bursts a stone block; finisher: anchors punch down and the turret spins a full turn.
# Cameras "Cam <take>" (front three-quarter), "Cam <take> close", "Cam row MS".
# Builds LanternLive\constructs\mech_compact.blend.
SCENE_NAME = "Mech Compact"
OUT_REL = "constructs/mech_compact.blend"
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector, Quaternion

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


def add_uv(me, uvt=0.5):
    """Per-face box projection UVs (one texture tile per `uvt` metres) so strip textures map onto round parts too."""
    uv = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        n = np.abs(np.array(poly.normal)); ax = int(np.argmax(n)); o_ = [i for i in range(3) if i != ax]
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co[o_[0]] / uvt, co[o_[1]] / uvt)


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
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m); add_uv(me)
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
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m); add_uv(me)
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
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m); add_uv(me)
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
FLOOR = mat("M6 floor", (0.2, 0.22, 0.2), rough=0.9)
LBL = mat("M6 label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(858)
CM = cmats("M6", "green")
RM, W, GR, GL = CM["rim"], CM["glow"], CM["grip"], CM["glass"]
FRAME = mat("M6 dark frame", (0.02, 0.12, 0.05), emit=0.35, alpha=0.9, rough=0.25)      # inner skeleton, darker
SHOCK = mat("M6 shock glass", (0.06, 0.5, 0.15), emit=1.2, alpha=0.35, rough=0.1)
ROD = mat("M6 piston rod", (0.1, 0.75, 0.25), emit=1.4, alpha=0.95, rough=0.15, metal=0.4)
DIM = mat("M6 vent glow", (0.08, 0.7, 0.2), emit=1.6, alpha=0.9)
CRYST = strip_mat("M6 crystal spike texture", strip_image("green", "v1"), 5, emit=1.0, alpha=0.85)
STONE = mat("M6 stone", (0.32, 0.32, 0.33), rough=0.95)
TEX = {k: strip_mat(f"M6 {k} texture", strip_image("green", k), 5, emit=1.2, alpha=0.92)
       for k in ("w1", "v1")}
# R2K1 dark jade is mostly transparent in its own alpha (a skin overlay); as a hull it gets a flat 88% so it reads solid
TEX["r2k1"] = strip_mat("M6 r2k1 texture", strip_image("green", "r2k1"), 5, emit=1.2)
TEX["r2k1"].node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.88
try:
    TEX["r2k1"].surface_render_method = "BLENDED"
except Exception:
    pass
ROBE = mat("M6 villager robe", (0.35, 0.22, 0.12), rough=0.9)
VSKIN = mat("M6 villager skin", (0.72, 0.52, 0.4), rough=0.8)
ZSKIN = mat("M6 zombie skin", (0.3, 0.5, 0.3), rough=0.8)
ZSHIRT = mat("M6 zombie shirt", (0.1, 0.45, 0.5), rough=0.8)
BROW = mat("M6 brow", (0.15, 0.1, 0.05))


def pilot(tag, kind, parent, loc):
    """A pilot. kind: player / villager / zombie. Returns (rig, mats)."""
    M = player_mats(tag)
    if kind == "villager":
        M.update(skin=VSKIN, shirt=ROBE, pants=ROBE, boot=ROBE)
    elif kind == "zombie":
        M.update(skin=ZSKIN, shirt=ZSHIRT, pants=mat(f"{tag} pants", (0.2, 0.2, 0.45)))
    rig = make_player(tag, (0, 0, 0), M)
    if kind == "villager":
        box(f"{tag} nose", (-1 * P, 4 * P, 1 * P), (1 * P, 6 * P, 4 * P), VSKIN, rig["head"])
        box(f"{tag} brow", (-4 * P, 4 * P, 4.5 * P), (4 * P, 4.2 * P, 5.2 * P), BROW, rig["head"])
    rig["root"].parent = parent; rig["root"].location = loc
    return rig, M


def mparts(J, extra_skip=()):
    """The mech's own meshes (not the pilot, not effect meshes named in extra_skip)."""
    return [o for o in J["root"].children_recursive if o.type == "MESH" and " pilot" not in o.name
            and not any(k in o.name for k in extra_skip)]


def bev(o, w=0.035, seg=2):
    """Rounded edges on a plate (smoother, more machined than a raw cube)."""
    m_ = o.modifiers.new("bevel", "BEVEL"); m_.width = w; m_.segments = seg; m_.limit_method = "ANGLE"
    return o


def plate(name, a, c, m, par, w=0.035):
    return bev(box(name, a, c, m, par), w)


def arc(name, R_, r, a0, a1, m, loc, n=20, k=6):
    """Part of a torus in the XY plane, from angle a0 to a1 (radians): a slash trail."""
    vs, fs = [], []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        for j in range(k):
            b = 2 * math.pi * j / k
            rr = r * (0.3 + 0.7 * math.sin(math.pi * i / n))          # thin at both ends
            vs.append(((R_ + rr * math.cos(b)) * math.cos(a), (R_ + rr * math.cos(b)) * math.sin(a), rr * 2.5 * math.sin(b)))
    for i in range(n):
        for j in range(k):
            fs.append((i * k + j, (i + 1) * k + j, (i + 1) * k + (j + 1) % k, i * k + (j + 1) % k))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    return o


def hand(tag, wrist, T, at_z, n=4, flen=0.24, pw=0.27, thumb=True):
    """Palm below the wrist pivot and n two-joint fingers; returns the knuckle pivots to curl."""
    plate(f"{tag} palm", (-pw, -0.15, at_z - 0.3), (pw, 0.15, at_z), T, wrist, 0.03)
    plate(f"{tag} back plate", (-pw * 0.9, -0.19, at_z - 0.26), (pw * 0.9, -0.14, at_z - 0.04), RM, wrist, 0.01)
    kn = []
    for i in range(n):
        x = -pw + 0.04 + (2 * pw - 0.08) * (i + 0.5) / n
        k1 = empty(f"{tag} knuckle {i}", (x, 0.04, at_z - 0.3), wrist)
        box(f"{tag} finger {i} a", (-0.045, -0.06, -flen * 0.55), (0.045, 0.06, 0), T, k1)
        k2 = empty(f"{tag} finger joint {i}", (0, 0, -flen * 0.55), k1)
        box(f"{tag} finger {i} b", (-0.04, -0.055, -flen * 0.45), (0.04, 0.055, 0), T, k2)
        box(f"{tag} fingertip {i}", (-0.042, 0.02, -flen * 0.45), (0.042, 0.06, -flen * 0.3), RM, k2)
        kn.append((k1, k2))
    if thumb:
        k1 = empty(f"{tag} thumb", (0, 0.13, at_z - 0.1), wrist)
        box(f"{tag} thumb a", (-0.05, -0.04, -0.2), (0.05, 0.06, 0), T, k1)
        kn.append((k1, None))
    return kn


def curl(kn, f, v):
    """0 open hand, 1 a closed fist (fingers curl toward +Y, the front)."""
    for k1, k2 in kn:
        if k2 is None:
            key(k1, f, rot=(R(55 * v), 0, 0)); continue
        key(k1, f, rot=(R(85 * v), 0, 0)); key(k2, f, rot=(R(95 * v), 0, 0))


def leg_pivots(tag, hips, sx, hx, thigh, shin):
    hip = empty(f"{tag} hip {sx}", (sx * hx, 0, -0.1), hips)
    knee = empty(f"{tag} knee {sx}", (0, 0, -thigh), hip)
    ankle = empty(f"{tag} ankle {sx}", (0, 0, -shin), knee)
    return hip, knee, ankle


def cracks(tag, c, f, n=7, ln=2.2):
    """Ground cracks, instant on impact: glowing slits radiating from c, they linger then fade."""
    hub = empty(f"{tag} cracks", c)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        piv = empty(f"{tag} crack pivot {i}", (0, 0, 0), hub); piv.rotation_euler = (0, 0, a)
        L_ = ln * rng.uniform(0.6, 1.1)
        cr = box(f"{tag} crack {i}", (0, -0.035, 0.0), (L_, 0.035, 0.03), RM, piv)
        key(cr, 1, sc=0.0001); key(cr, f - 1, sc=0.0001); key(cr, f, sc=(0.5, 1, 1)); key(cr, f + 2, sc=(1, 1, 1))
        key(cr, f + 18, sc=(1, 1, 1)); key(cr, f + 22, sc=0.0001)
    return hub


def ring_fx(tag, c, f, r0, grow, life=7, axis="Z", th=0.04):
    t = torus(tag, r0, th, RM, loc=c, axis=axis)
    key(t, 1, sc=0.0001); key(t, f - 1, sc=0.0001); key(t, f, sc=(1, 1, 1)); key(t, f + life, sc=(grow, grow, 1 if axis == "Z" else grow))
    key(t, f + life + 1, sc=0.0001)
    return t


class Mech:
    """Joint keying helpers shared by all takes (every take still moves its own way)."""

    def __init__(s, tag, J, bx):
        s.tag, s.J, s.bx = tag, J, bx

    def leg(s, f, sx_, hip_x, knee_x, ankle_x=0.0, hip_z=0.0):
        for h, k, a, sx in s.J["legs"]:
            if sx == sx_:
                key(h, f, rot=(R(hip_x), 0, R(hip_z))); key(k, f, rot=(R(knee_x), 0, 0)); key(a, f, rot=(R(ankle_x), 0, 0))

    def arm(s, f, sx_, sh_x, el_x, sh_z=0.0, sh_y=0.0, el_z=0.0):
        for sh, el, sx in s.J["arms"]:
            if sx == sx_:
                key(sh, f, rot=(R(sh_x), R(sh_y), R(sh_z))); key(el, f, rot=(R(el_x), 0, R(el_z)))
        m = s.J.get("mirror")                               # the exo pilot's arms follow the mech's
        if m is not None:
            side = "r" if sx_ == 1 else "l"
            key(m["arm_" + side], f, rot=(R(sh_x), R(sh_y), R(sh_z))); key(m["fore_" + side], f, rot=(R(el_x * 0.8), 0, 0))

    def hips(s, f, z, rx=0.0, ry=0.0, rz=0.0):
        key(s.J["hips"], f, loc=(0, 0, z), rot=(R(-rx), R(ry), R(rz)))          # rx > 0 leans forward

    def torso(s, f, rx=0.0, ry=0.0, rz=0.0):
        key(s.J["torso"], f, rot=(R(-rx), R(ry), R(rz)))                        # rx > 0 leans forward

    def root(s, f, y, z=0.0, rz=0.0):
        key(s.J["root"], f, loc=(s.bx, y, z), rot=(0, 0, R(rz)))

    def fists(s, f, v, sides=(-1, 1)):
        for sx in sides:
            if sx in s.J.get("hands", {}):
                curl(s.J["hands"][sx], f, v)

    def hatch(s, f_open_until=30, f_shut=35):
        h = s.J["hatch"]; o = s.J.get("hatch_open", (R(100), 0, 0))
        key(h, 1, rot=o); key(h, f_open_until, rot=o); key(h, f_shut, rot=(0, 0, 0))




# ------------------------------------------------------------------ shared with 851: centre, jets, spin keys
def centre(o):
    return o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))


def flare(o, f, l, w=1.0):
    """A jet (a cone along its own Z): length l (0 = off), width w."""
    key(o, f, sc=(w, w, max(0.0001, l)) if l > 0 else (1, 1, 0.0001))


def jet(name, r, ln, par, loc, rot=(0, 0, 0)):
    o = cyl(name, r, ln, W, 12, par, loc=loc, r2=0.02); o.rotation_euler = rot
    return o


def spin_keys(o, f0, f1, turns, axis=2, step=6):
    for f in range(f0, f1 + 1, step):
        r = [0, 0, 0]; r[axis] = R(360 * turns * (f - f0) / max(1, f1 - f0)); key(o, f, rot=tuple(r))


def pilot_seat_box(tag, torso, T, w=1.0, back=-0.6, front=0.55, roof=1.4):
    """Cockpit shell (as in 851): back, sides, floor (the pilot sits at seat (0, -0.05, -0.62))."""
    plate(f"{tag} chest back", (-w, back, 0.0), (w, back + 0.3, roof), T, torso)
    for sx in (-1, 1):
        plate(f"{tag} chest side {sx}", (sx * w - 0.15, back, 0.0), (sx * w + 0.15, front, roof - 0.05), T, torso)
    plate(f"{tag} chest floor", (-w, back, -0.05), (w, front, 0.1), T, torso)




# ------------------------------------------------------------------ 858: detail kit (pistons, vents, sensors, seams)
S6 = 0.6                                       # compact: every mech is built in full-size units and scaled to 0.6


def piston(tag, pa, la, pb, lb, r=0.05):
    """A hydraulic piston between two pivots: a dark sleeve on one end and a lit rod on the other, each aimed at the
    other end every frame (damped track), so it slides in and out as the joint moves."""
    ea = empty(f"{tag} piston base", la, pa); eb = empty(f"{tag} piston head", lb, pb)
    ta = empty(f"{tag} piston anchor a", la, pa); tb = empty(f"{tag} piston anchor b", lb, pb)   # untracked targets
    bpy.context.view_layer.update()
    L = (pb.matrix_world @ Vector(lb) - pa.matrix_world @ Vector(la)).length
    for e, t in ((ea, tb), (eb, ta)):
        c = e.constraints.new("DAMPED_TRACK"); c.target = t; c.track_axis = "TRACK_Z"
    cyl(f"{tag} piston sleeve", r * 1.55, 0.6 * L, FRAME, 10, ea)
    cyl(f"{tag} piston rod", r, 0.62 * L, ROD, 8, eb)
    ball(f"{tag} piston eye a", r * 1.8, FRAME, parent=ea, seg=8)
    ball(f"{tag} piston eye b", r * 1.8, FRAME, parent=eb, seg=8)
    return ea, eb


def vents(tag, par, a, b, n=4):
    """A vent grille: a dark recess and n slats stacked along Z, standing out of the thin side."""
    a = np.array(a, float); b = np.array(b, float); ext = np.abs(b - a); th = int(np.argmin(ext))
    box(f"{tag} vent recess", tuple(a), tuple(b), FRAME, par)
    dz = (b[2] - a[2]) / n
    for i in range(n):
        lo = a.copy(); hi = b.copy(); lo[2] = a[2] + i * dz + dz * 0.15; hi[2] = lo[2] + dz * 0.45
        lo[th] -= 0.018; hi[th] += 0.018
        box(f"{tag} vent slat {i}", tuple(lo), tuple(hi), GR, par)
    lo = a.copy(); hi = b.copy(); lo[th] = hi[th] = (a[th] + b[th]) / 2; lo[th] -= 0.005; hi[th] += 0.005
    box(f"{tag} vent glow", tuple(lo), tuple(hi), DIM, par)


def sensor(tag, par, loc, r, axis="Y"):
    """A sensor eye: dark housing, a lit lens and a rim ring, facing +axis."""
    v = {"Y": Vector((0, 1, 0)), "X": Vector((1, 0, 0)), "Z": Vector((0, 0, 1))}[axis]
    cyl(f"{tag} sensor housing", r * 1.35, 0.1, FRAME, 14, par, loc=loc, axis=axis)
    ball(f"{tag} sensor lens", r, W, loc=tuple(Vector(loc) + v * 0.06), parent=par, seg=12)
    torus(f"{tag} sensor rim", r * 1.35, 0.022, RM, loc=tuple(Vector(loc) + v * 0.1), parent=par, n=16, k=6, axis=axis)


def seam(tag, par, a, b):
    return box(f"{tag} seam", a, b, FRAME, par)


def rivets(tag, par, pts, s=0.03):
    for i, p in enumerate(pts):
        box(f"{tag} rivet {i}", tuple(np.array(p) - s), tuple(np.array(p) + s), FRAME, par)


def wpos(o, f):
    scene.frame_set(f); bpy.context.view_layer.update()
    return o.matrix_world.translation.copy()


def linear(o):
    ad = o.animation_data
    if ad and ad.action:
        try:
            fcs = ad.action.fcurves
        except Exception:
            fcs = [fc for l_ in ad.action.layers for s_ in l_.strips for cb in s_.channelbags for fc in cb.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def puff(tag, c, f, r=0.25, rise=0.6):
    """A small vent puff of see-through construct glass that rises and fades out."""
    b_ = ball(f"{tag} puff", r, SHOCK, loc=c, seg=10)
    key(b_, 1, sc=0.0001); key(b_, f - 1, sc=0.0001, loc=c); key(b_, f, sc=0.5, loc=c)
    key(b_, f + 5, sc=1.3, loc=tuple(Vector(c) + Vector((0, 0, rise)))); key(b_, f + 6, sc=0.0001)


# ================================================================== MS1 Workhorse (W1 weave, villager)
def build_MS1(tag, T):
    J = {"hz": 1.85}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.2), hips); J["torso"] = torso
    plate(f"{tag} pelvis", (-0.6, -0.4, -0.3), (0.6, 0.4, 0.15), T, hips)
    plate(f"{tag} cod plate", (-0.25, 0.38, -0.45), (0.25, 0.5, 0.05), T, hips, 0.03)
    seam(f"{tag} cod", hips, (-0.26, 0.5, -0.2), (0.26, 0.51, -0.18))
    for sx in (-1, 1):
        vents(f"{tag} hip {sx}", hips, (sx * 0.6 - 0.01, -0.25, -0.22), (sx * 0.6 + 0.01, 0.25, 0.08), 3)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.5, 0.75, 0.75)
        cyl(f"{tag} hip joint {sx}", 0.2, 0.32, FRAME, 14, hip, loc=(-0.16, 0, 0), axis="X")
        torus(f"{tag} hip joint ring {sx}", 0.2, 0.025, RM, loc=(sx * 0.17, 0, 0), parent=hip, n=16, k=6, axis="X")
        plate(f"{tag} thigh {sx}", (-0.2, -0.2, -0.68), (0.2, 0.2, -0.08), T, hip)
        plate(f"{tag} thigh guard {sx}", (-0.23, 0.2, -0.62), (0.23, 0.29, -0.14), T, hip, 0.025)
        seam(f"{tag} thigh {sx}", hip, (-0.23, 0.29, -0.39), (0.23, 0.3, -0.37))
        rivets(f"{tag} thigh {sx}", hip, [(xx, 0.3, zz) for xx in (-0.17, 0.17) for zz in (-0.2, -0.56)], 0.025)
        cyl(f"{tag} knee joint {sx}", 0.17, 0.36, FRAME, 14, knee, loc=(-0.18, 0, 0), axis="X")
        plate(f"{tag} knee cap {sx}", (-0.19, 0.14, -0.13), (0.19, 0.3, 0.16), T, knee, 0.03)
        plate(f"{tag} shin {sx}", (-0.18, -0.18, -0.68), (0.18, 0.2, -0.06), T, knee)
        plate(f"{tag} shin guard {sx}", (-0.2, 0.2, -0.6), (0.2, 0.27, -0.12), T, knee, 0.025)
        vents(f"{tag} calf {sx}", knee, (-0.13, -0.19, -0.55), (0.13, -0.17, -0.2), 3)
        ball(f"{tag} ankle ball {sx}", 0.13, FRAME, parent=ankle, seg=12)
        plate(f"{tag} foot {sx}", (-0.24, -0.3, -0.25), (0.24, 0.25, -0.04), T, ankle, 0.03)
        for k_, (x0, x1) in enumerate(((-0.24, -0.02), (0.02, 0.24))):
            plate(f"{tag} toe {sx} {k_}", (x0, 0.25, -0.25), (x1, 0.55, -0.1), T, ankle, 0.025)
            box(f"{tag} toe cap {sx} {k_}", (x0 + 0.03, 0.55, -0.23), (x1 - 0.03, 0.58, -0.13), RM, ankle)
        plate(f"{tag} heel spur {sx}", (-0.1, -0.45, -0.25), (0.1, -0.3, -0.12), T, ankle, 0.02)
        piston(f"{tag} calf {sx}", hip, (0, -0.24, -0.25), knee, (0, -0.22, -0.5), 0.05)
        piston(f"{tag} ankle {sx}", knee, (0, 0.24, -0.5), ankle, (0, 0.2, -0.08), 0.04)
        legs.append((hip, knee, ankle, sx))
    pilot_seat_box(tag, torso, T, 0.9, -0.6, 0.55, 1.4)
    plate(f"{tag} roof", (-1.0, -0.7, 1.35), (1.0, 0.62, 1.52), T, torso, 0.05)
    plate(f"{tag} chest lip", (-0.85, 0.5, 0.0), (0.85, 0.7, 0.36), T, torso, 0.04)
    seam(f"{tag} chest lip", torso, (-0.86, 0.7, 0.17), (0.86, 0.71, 0.19))
    cyl(f"{tag} chest core", 0.11, 0.06, W, 14, torso, loc=(0, 0.7, 0.18), axis="Y")
    torus(f"{tag} chest core rim", 0.15, 0.025, RM, loc=(0, 0.75, 0.18), parent=torso, n=16, k=6, axis="Y")
    rivets(f"{tag} chest lip", torso, [(xx, 0.71, zz) for xx in (-0.7, -0.4, 0.4, 0.7) for zz in (0.07, 0.29)], 0.025)
    for sx in (-1, 1):
        vents(f"{tag} chest side {sx}", torso, (sx * 1.06 - 0.01, -0.35, 0.3), (sx * 1.06 + 0.01, 0.3, 1.0), 5)
    hatch = empty(f"{tag} canopy hinge", (0, 0.55, 1.4), torso)
    box(f"{tag} canopy", (-0.76, 0.0, -1.05), (0.76, 0.05, 0.0), GL, hatch)
    for xx in (-0.26, 0.26):
        box(f"{tag} canopy bar", (xx - 0.03, 0.0, -1.05), (xx + 0.03, 0.08, 0.0), FRAME, hatch)
    box(f"{tag} canopy rail", (-0.78, 0.0, -0.08), (0.78, 0.09, 0.0), T, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    head = empty(f"{tag} sensor head", (0, 0.05, 1.52), torso); J["head"] = head
    plate(f"{tag} head block", (-0.36, -0.3, 0.0), (0.36, 0.34, 0.36), T, head, 0.04)
    sensor(f"{tag} main eye", head, (0, 0.3, 0.18), 0.1)
    for sx in (-1, 1):
        sensor(f"{tag} side eye {sx}", head, (sx * 0.24, 0.3, 0.24), 0.045)
        cyl(f"{tag} antenna {sx}", 0.018, 0.5, FRAME, 6, head, loc=(sx * 0.28, -0.22, 0.36))
        ball(f"{tag} antenna tip {sx}", 0.04, RM, loc=(sx * 0.28, -0.22, 0.87), parent=head, seg=8)
    pack = empty(f"{tag} radiator", (0, -0.62, 0.75), torso)
    plate(f"{tag} radiator body", (-0.62, -0.25, -0.6), (0.62, 0.05, 0.55), T, pack, 0.04)
    for i in range(6):
        xx = -0.5 + i * 0.2
        box(f"{tag} radiator fin {i}", (xx - 0.03, -0.42, -0.5), (xx + 0.03, -0.25, 0.45), GR, pack)
    stacks = []
    for sx in (-1, 1):
        cyl(f"{tag} exhaust stack {sx}", 0.1, 0.7, FRAME, 12, pack, loc=(sx * 0.48, -0.15, 0.4))
        torus(f"{tag} stack rim {sx}", 0.1, 0.025, RM, loc=(sx * 0.48, -0.15, 1.1), parent=pack, n=12, k=6)
        stacks.append(empty(f"{tag} stack tip {sx}", (sx * 0.48, -0.15, 1.15), pack))
        sj = jet(f"{tag} stack jet {sx}", 0.09, 0.7, pack, (sx * 0.48, -0.15, 1.1)); J.setdefault("sjets", []).append(sj)
    arms, hands, rams = [], {}, {}
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.25, 0, 1.1), torso)
        ball(f"{tag} shoulder ball {sx}", 0.22, FRAME, parent=sh, seg=14)
        plate(f"{tag} pauldron {sx}", (-0.36, -0.42, -0.08), (0.36, 0.42, 0.36), T, sh, 0.05)
        vents(f"{tag} pauldron {sx}", sh, (-0.25, 0.42, 0.0), (0.25, 0.44, 0.28), 3)
        plate(f"{tag} upper arm {sx}", (-0.16, -0.16, -0.62), (0.16, 0.16, -0.1), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.68), sh)
        cyl(f"{tag} elbow joint {sx}", 0.14, 0.32, FRAME, 12, el, loc=(-0.16, 0, 0), axis="X")
        plate(f"{tag} ram sleeve {sx}", (-0.22, -0.22, -0.48), (0.22, 0.22, 0.04), T, el, 0.04)
        torus(f"{tag} sleeve collar {sx}", 0.2, 0.03, RM, loc=(0, 0, -0.48), parent=el, n=16, k=6)
        seam(f"{tag} sleeve {sx}", el, (-0.23, -0.23, -0.25), (0.23, 0.23, -0.23))
        piston(f"{tag} elbow {sx}", sh, (0, 0.2, -0.18), el, (0, 0.22, -0.3), 0.045)
        ram = empty(f"{tag} ram {sx}", (0, 0, -0.4), el)
        cyl(f"{tag} ram rod {sx}", 0.11, 0.5, ROD, 12, ram, loc=(0, 0, -0.5))
        wrist = empty(f"{tag} wrist {sx}", (0, 0, -0.5), ram)
        plate(f"{tag} wrist cuff {sx}", (-0.2, -0.17, -0.06), (0.2, 0.17, 0.04), T, wrist, 0.02)
        hands[sx] = hand(f"{tag} hand {sx}", wrist, T, -0.04, 3, 0.26, 0.22)
        rams[sx] = ram; J.setdefault("wrists", {})[sx] = wrist
        arms.append((sh, el, sx))
    J.update(legs=legs, arms=arms, hands=hands, rams=rams, stacks=stacks)
    return J


def anim_MS1(M):
    J = M.J; hz = J["hz"]; tg = M.tag
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0); M.arm(1, sx, 8, 20, sx * 8); key(J["rams"][sx], 1, loc=(0, 0, -0.4))
    M.fists(1, 0.4); M.hips(1, hz); M.torso(1); M.root(1, 0)
    for o in J["sjets"]:
        for f, l in ((1, 0), (106, 0), (107, 1.3), (113, 1.0), (116, 0)):
            flare(o, f, l)
    # 36-76: brisk march, four 10-tick steps of 0.6 m; the calf and ankle pistons pump; steam puffs at each footfall
    M.root(36, 0); M.hips(36, hz)
    for k in range(4):
        f0 = 36 + k * 10; sx = 1 if k % 2 == 0 else -1
        M.leg(f0, sx, -14, 0, 10); M.leg(f0 + 4, sx, 38, -60, 18); M.leg(f0 + 8, sx, 20, -6, -12); M.leg(f0 + 10, sx, 14, 0, -10)
        M.leg(f0, -sx, 14, 0, -10); M.leg(f0 + 6, -sx, -4, -8, 6); M.leg(f0 + 10, -sx, -14, 0, 10)
        M.hips(f0 + 3, hz + 0.06, 5, 0, -sx * 3); M.hips(f0 + 8, hz - 0.08, 7, 0, sx * 2)
        M.torso(f0 + 5, 0, 0, sx * 6)
        M.arm(f0 + 5, sx, -22, 30, sx * 8); M.arm(f0 + 5, -sx, 28, 35, -sx * 8)
        M.root(f0 + 10, 0.6 * (k + 1))
        for st in J["stacks"]:
            c = wpos(st, f0 + 8)
            puff(f"{tg} step puff {k} {st.name[-2:]}", tuple(c), f0 + 9, 0.12, 0.4)
    head = J["head"]
    key(head, 36, rot=(0, 0, 0)); key(head, 48, rot=(0, 0, R(28))); key(head, 62, rot=(0, 0, R(-28))); key(head, 74, rot=(0, 0, 0))
    M.hips(76, hz); M.torso(76)
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0); M.arm(76, sx, 8, 20, sx * 8)
    # 76-96: piston punch: brace, cock the right arm, snap it level and the ram fires the fist out 0.65, then pulls back
    M.leg(80, -1, 26, -22, -4); M.leg(80, 1, -12, 0, 10); M.hips(80, hz - 0.12, 4)
    M.torso(80, 0, 0, -22); M.arm(80, 1, 45, 110, 10); M.arm(80, -1, 55, 105, -10)
    M.torso(83, 6, 0, 16); M.arm(83, 1, 90, 0, 0); M.arm(83, -1, 30, 90, -10)
    ram = J["rams"][1]
    key(ram, 82, loc=(0, 0, -0.4)); key(ram, 84, loc=(0, 0, -1.05)); key(ram, 87, loc=(0, 0, -1.05)); key(ram, 91, loc=(0, 0, -0.4))
    M.fists(80, 1.0); M.torso(90, 2, 0, 6); M.arm(91, 1, 70, 40, 5)
    M.hips(94, hz); M.torso(96)
    for sx in (-1, 1):
        M.leg(96, sx, 0, 0); M.arm(96, sx, 15, 30, sx * 8)
    c = wpos(J["wrists"][1], 84)
    ring_fx(f"{tg} punch ring", tuple(c + Vector((0, 0.25, 0))), 84, 0.18, 4.5, 6, axis="Y", th=0.025)
    ring_fx(f"{tg} punch ring 2", tuple(c + Vector((0, 0.5, 0))), 85, 0.12, 3.5, 5, axis="Y", th=0.02)
    # 96-126: double ram slam: both arms up overhead, crash down into a crouch, both rams fire the fists into the ground
    M.arm(100, 1, 165, 25, 8); M.arm(100, -1, 165, 25, -8); M.torso(100, -10); M.hips(100, hz + 0.05)
    for sx in (-1, 1):
        M.leg(100, sx, 0, 0); M.leg(104, sx, 40, -70, 30); M.leg(114, sx, 40, -70, 30); M.leg(124, sx, 0, 0)
        M.arm(104, sx, 72, 0, sx * 4); M.arm(114, sx, 72, 0, sx * 4); M.arm(120, sx, 30, 40, sx * 8); M.arm(126, sx, 15, 30, sx * 8)
        r_ = J["rams"][sx]
        key(r_, 103, loc=(0, 0, -0.4)); key(r_, 106, loc=(0, 0, -1.0)); key(r_, 112, loc=(0, 0, -1.0)); key(r_, 117, loc=(0, 0, -0.4))
    M.torso(104, 30); M.torso(114, 30); M.torso(124)
    M.hips(104, hz - 0.42, 8); M.hips(114, hz - 0.42, 8); M.hips(124, hz)
    M.fists(98, 1.0)
    a = wpos(J["wrists"][1], 106); b = wpos(J["wrists"][-1], 106); c = (a + b) / 2
    print(tg, "slam fists at z %.2f / %.2f" % (a.z, b.z), flush=True)
    cracks(tg, (c.x, c.y + 0.1, 0.01), 106, 8, 1.6)
    ring_fx(f"{tg} slam ring", (c.x, c.y + 0.1, 0.04), 106, 0.4, 6.0, 9)
    ring_fx(f"{tg} slam ring 2", (c.x, c.y + 0.1, 0.06), 108, 0.3, 3.8, 7, th=0.03)


def form_MS1(M, J, src):
    """Printed: a glowing scan plane rises from the floor and each part is extruded upward as the plane passes it,
    the pistons last, then the core lights."""
    bpy.context.view_layer.update()
    parts = mparts(J, ("jet",))
    zs = [centre(o).z for o in parts]; lo, hi = min(zs), max(zs) + 1e-6
    bx = J["root"].matrix_world.translation.x
    pl = cyl(f"{M.tag} scan plane", 1.25, 0.015, SHOCK, 32, None, loc=(bx, 0, 0.0))
    pr = torus(f"{M.tag} scan ring", 1.25, 0.03, RM, loc=(0, 0, 0.0), parent=pl, n=32, k=6)
    key(pl, 1, loc=(bx, 0, 0.02), sc=0.0001); key(pl, 2, loc=(bx, 0, 0.02), sc=1.0)
    key(pl, 21, loc=(bx, 0, hi + 0.1), sc=1.0); key(pl, 22, loc=(bx, 0, hi + 0.1), sc=0.0001)
    linear(pl)
    for o, z in zip(parts, zs):
        fa = int(round(2 + (z - lo) / (hi - lo) * 18))
        if "piston" in o.name:
            fa = min(23, fa + 2)
        sc0 = tuple(o.scale)
        key(o, 1, sc=(sc0[0], sc0[1], 0.0001)); key(o, max(1, fa - 1), sc=(sc0[0], sc0[1], 0.0001)); key(o, fa + 1, sc=sc0)


# ================================================================== MS2 Crawler (V1 crystal, baby zombie)
def build_MS2(tag, T):
    J = {"hz": 1.3}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hull", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} pod", (0, -0.1, 0.22), hips); J["torso"] = torso
    plate(f"{tag} hull", (-0.85, -0.95, -0.35), (0.85, 0.95, 0.22), T, hips, 0.06)
    plate(f"{tag} belly", (-0.6, -0.7, -0.52), (0.6, 0.7, -0.33), FRAME, hips, 0.04)
    nose = plate(f"{tag} nose plate", (-0.7, 0.0, -0.3), (0.7, 0.28, 0.12), T, hips, 0.04)
    nose.location = (0, 0.92, 0.05); nose.rotation_euler = (R(-18), 0, 0)
    seam(f"{tag} hull", hips, (-0.86, 0.95, -0.1), (0.86, 0.96, -0.08))
    for sx in (-1, 1):
        seam(f"{tag} hull side {sx}", hips, (sx * 0.85 - 0.005, -0.9, -0.1), (sx * 0.85 + 0.005, 0.9, -0.08))
    sensor(f"{tag} main eye", hips, (0, 0.95, -0.12), 0.13)
    for sx in (-1, 1):
        sensor(f"{tag} side eye {sx}", hips, (sx * 0.42, 0.95, -0.02), 0.07)
        sensor(f"{tag} low eye {sx}", hips, (sx * 0.25, 0.95, -0.25), 0.045)
    vents(f"{tag} rear", hips, (-0.55, -0.97, -0.28), (0.55, -0.95, 0.12), 4)
    for i, (xx, yy, h) in enumerate(((-0.55, -0.65, 0.4), (0.55, -0.65, 0.4), (-0.6, 0.6, 0.3), (0.6, 0.6, 0.3), (0, -0.85, 0.5))):
        cyl(f"{tag} crystal spike {i}", 0.1, h, T, 6, hips, loc=(xx, yy, 0.2), r2=0.0)
    pilot_seat_box(tag, torso, T, 0.75, -0.6, 0.5, 1.3)
    plate(f"{tag} pod roof", (-0.85, -0.7, 1.26), (0.85, 0.6, 1.42), T, torso, 0.05)
    hatch = empty(f"{tag} canopy hinge", (0, 0.5, 1.3), torso)
    box(f"{tag} canopy", (-0.62, 0.0, -1.1), (0.62, 0.05, 0.0), GL, hatch)
    box(f"{tag} canopy rib", (-0.03, 0.0, -1.1), (0.03, 0.08, 0.0), FRAME, hatch)
    box(f"{tag} canopy sill", (-0.64, 0.0, -1.1), (0.64, 0.09, -1.02), T, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    dome = empty(f"{tag} sensor dome", (0, -0.1, 1.42), torso); J["head"] = dome
    ball(f"{tag} dome", 0.2, GL, parent=dome, seg=14)
    sensor(f"{tag} dome eye", dome, (0, 0.12, 0.05), 0.06)
    for sx in (-1, 1):
        cyl(f"{tag} antenna {sx}", 0.018, 0.55, FRAME, 6, torso, loc=(sx * 0.6, -0.55, 1.42))
        ball(f"{tag} antenna tip {sx}", 0.04, RM, loc=(sx * 0.6, -0.55, 1.98), parent=torso, seg=8)
        vents(f"{tag} pod side {sx}", torso, (sx * 0.91 - 0.01, -0.4, 0.4), (sx * 0.91 + 0.01, 0.2, 1.0), 4)
    legs4 = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            base = empty(f"{tag} leg base {sx}{sy}", (sx * 0.8, sy * 0.72, -0.12), hips)
            base.rotation_euler = (0, 0, math.atan2(sy, sx) - math.pi / 2)
            cyl(f"{tag} coxa {sx}{sy}", 0.19, 0.28, FRAME, 14, base, loc=(0, 0, -0.14))
            torus(f"{tag} coxa ring {sx}{sy}", 0.19, 0.025, RM, loc=(0, 0, 0.14), parent=base, n=16, k=6)
            yaw = empty(f"{tag} leg yaw {sx}{sy}", (0, 0, 0), base)
            fem = empty(f"{tag} femur {sx}{sy}", (0, 0.1, 0), yaw); fem.rotation_euler = (R(35), 0, 0)
            plate(f"{tag} femur plate {sx}{sy}", (-0.13, 0.0, -0.12), (0.13, 0.9, 0.12), T, fem, 0.03)
            cyl(f"{tag} femur crystal {sx}{sy}", 0.07, 0.22, T, 6, fem, loc=(0, 0.45, 0.12), r2=0.0)
            seam(f"{tag} femur {sx}{sy}", fem, (-0.135, 0.44, -0.12), (0.135, 0.46, 0.12))
            knee = empty(f"{tag} leg knee {sx}{sy}", (0, 0.9, 0), fem); knee.rotation_euler = (R(-20), 0, 0)
            ball(f"{tag} knee ball {sx}{sy}", 0.15, FRAME, parent=knee, seg=12)
            cyl(f"{tag} tibia {sx}{sy}", 0.12, -1.55, T, 8, knee, r2=0.05)
            torus(f"{tag} tibia band {sx}{sy}", 0.11, 0.022, RM, loc=(0, 0, -0.35), parent=knee, n=12, k=6)
            cyl(f"{tag} foot tip {sx}{sy}", 0.06, -0.18, RM, 6, knee, loc=(0, 0, -1.55), r2=0.0)
            piston(f"{tag} leg {sx}{sy}", yaw, (0, 0.18, -0.32), fem, (0, 0.55, -0.1), 0.04)
            legs4.append((yaw, fem, knee, sx, sy))
    claws = {}
    for sx in (-1, 1):
        sh = empty(f"{tag} pincer shoulder {sx}", (sx * 0.45, 1.02, -0.2), hips); sh.rotation_euler = (R(-12), 0, 0)
        ball(f"{tag} pincer ball {sx}", 0.12, FRAME, parent=sh, seg=10)
        plate(f"{tag} pincer arm {sx}", (-0.08, 0.0, -0.08), (0.08, 0.5, 0.08), T, sh, 0.02)
        el = empty(f"{tag} pincer elbow {sx}", (0, 0.5, 0), sh)
        cyl(f"{tag} pincer elbow joint {sx}", 0.08, 0.2, FRAME, 10, el, loc=(-0.1, 0, 0), axis="X")
        plate(f"{tag} pincer base {sx}", (-0.12, 0.0, -0.12), (0.12, 0.26, 0.12), T, el, 0.03)
        up = empty(f"{tag} jaw top {sx}", (0, 0.26, 0.04), el)
        plate(f"{tag} jaw top plate {sx}", (-0.06, 0.0, 0.0), (0.06, 0.34, 0.07), T, up, 0.015)
        box(f"{tag} jaw top tip {sx}", (-0.05, 0.3, -0.03), (0.05, 0.36, 0.05), RM, up)
        dn = empty(f"{tag} jaw low {sx}", (0, 0.26, -0.04), el)
        plate(f"{tag} jaw low plate {sx}", (-0.06, 0.0, -0.07), (0.06, 0.34, 0.0), T, dn, 0.015)
        box(f"{tag} jaw low tip {sx}", (-0.05, 0.3, -0.05), (0.05, 0.36, 0.03), RM, dn)
        piston(f"{tag} pincer {sx}", hips, (sx * 0.45, 0.92, -0.42), el, (0, 0.12, -0.1), 0.03)
        claws[sx] = (sh, el, up, dn)
    J.update(legs=[], arms=[], hands={}, legs4=legs4, claws=claws)
    return J


def ms2_leg(J, f, sx, sy, yaw=0.0, lift=0.0, knee=0.0):
    for yw, fe, kn, x_, y_ in J["legs4"]:
        if x_ == sx and y_ == sy:
            key(yw, f, rot=(0, 0, R(yaw))); key(fe, f, rot=(R(35 + lift), 0, 0)); key(kn, f, rot=(R(-20 + knee), 0, 0))


def ms2_claw(J, f, sx, sh_x=-12, el_x=0, sh_z=0, jaw=0):
    sh, el, up, dn = J["claws"][sx]
    key(sh, f, rot=(R(sh_x), 0, R(sh_z))); key(el, f, rot=(R(el_x), 0, 0))
    key(up, f, rot=(R(jaw), 0, 0)); key(dn, f, rot=(R(-jaw), 0, 0))


def anim_MS2(M):
    J = M.J; hz = J["hz"]; tg = M.tag
    M.hatch(); M.hips(1, hz); M.root(1, 0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ms2_leg(J, 1, sx, sy); ms2_leg(J, 35, sx, sy)
        ms2_claw(J, 1, sx, -12, 10, 0, 6); ms2_claw(J, 35, sx, -12, 10, 0, 6)
    # 36-71: a trot, diagonal pairs swapping every 5 ticks; each swing leg lifts, swings 18 degrees ahead and plants
    M.root(36, 0); M.hips(36, hz)
    A = [(-1, 1), (1, -1)]; B = [(1, 1), (-1, -1)]
    for p in range(7):
        f0 = 36 + p * 5; sw, st = (A, B) if p % 2 == 0 else (B, A)
        for sx, sy in sw:
            ms2_leg(J, f0, sx, sy, -sx * 9); ms2_leg(J, f0 + 2, sx, sy, 0, 24, -14); ms2_leg(J, f0 + 5, sx, sy, sx * 9)
        for sx, sy in st:
            ms2_leg(J, f0 + 5, sx, sy, -sx * 9)
        M.hips(f0 + 2, hz + 0.05, 2, (3 if p % 2 else -3)); M.hips(f0 + 5, hz - 0.02, 1, 0)
        M.root(f0 + 5, 0.34 * (p + 1))
        for sx in (-1, 1):
            ms2_claw(J, f0 + 2, sx, -12 + 6 * (1 if p % 2 else -1) * sx, 10, 0, 22 if p in (2, 5) else 4)
    y = 0.34 * 7
    for sx in (-1, 1):
        for sy in (-1, 1):
            ms2_leg(J, 74, sx, sy); ms2_leg(J, 76, sx, sy)
    key(J["head"], 36, rot=(0, 0, 0)); key(J["head"], 50, rot=(0, 0, R(40))); key(J["head"], 64, rot=(0, 0, R(-40))); key(J["head"], 74, rot=(0, 0, 0))
    M.hips(76, hz); M.root(76, y)
    # 76-96: pincer lunge: sinks onto the back legs, claws up and open; lunges 0.6 m, both pincers snap shut on a target
    M.hips(80, hz - 0.18, -8); M.root(80, y - 0.15)
    for sx in (-1, 1):
        ms2_claw(J, 76, sx, -12, 10, 0, 6); ms2_claw(J, 80, sx, 35, 60, -sx * 10, 45)
        ms2_leg(J, 80, sx, -1, 0, -12, 25); ms2_leg(J, 80, sx, 1, 0, 8, -6)
        ms2_claw(J, 83, sx, 2, 0, sx * 6, 45); ms2_claw(J, 84, sx, 0, 0, sx * 4, -4); ms2_claw(J, 90, sx, 0, 0, sx * 4, -4)
        ms2_leg(J, 83, sx, -1, 0, 0, -10); ms2_leg(J, 83, sx, 1, 0, -14, 20)
        ms2_claw(J, 96, sx, -12, 10, 0, 6)
        for sy in (-1, 1):
            ms2_leg(J, 92, sx, sy); ms2_leg(J, 96, sx, sy)
    M.hips(83, hz - 0.05, 12); M.root(83, y + 0.6); M.hips(90, hz, 4); M.root(92, y + 0.4); M.hips(96, hz); M.root(96, y + 0.4)
    c = (wpos(J["claws"][1][2], 84) + wpos(J["claws"][-1][2], 84)) / 2 + Vector((0, 0.2, 0))
    ring_fx(f"{tg} snap ring", tuple(c), 84, 0.15, 4.0, 6, axis="Y", th=0.025)
    ring_fx(f"{tg} snap ring 2", tuple(c), 86, 0.1, 3.0, 5, axis="X", th=0.02)
    # 96-126: rear and spike slam: rears up on its back legs, front legs and claws high, drops and stomps; V1 crystal
    # spikes burst out of the ground in a ring
    y2 = y + 0.4
    M.hips(101, hz + 0.32, -24); M.hips(104, hz + 0.34, -26); M.hips(106, hz - 0.12, 6); M.hips(112, hz - 0.1, 4); M.hips(122, hz)
    for sx in (-1, 1):
        ms2_leg(J, 101, sx, 1, sx * 8, 48, -30); ms2_leg(J, 104, sx, 1, sx * 8, 52, -34)
        ms2_leg(J, 106, sx, 1, sx * 4, -6, 10); ms2_leg(J, 112, sx, 1, sx * 4, -6, 10); ms2_leg(J, 122, sx, 1)
        ms2_leg(J, 101, sx, -1, 0, -18, 30); ms2_leg(J, 104, sx, -1, 0, -18, 30); ms2_leg(J, 106, sx, -1, 0, 8, -6); ms2_leg(J, 122, sx, -1)
        ms2_claw(J, 101, sx, 60, 40, -sx * 20, 40); ms2_claw(J, 104, sx, 70, 40, -sx * 20, 40)
        ms2_claw(J, 106, sx, -30, 0, sx * 10, 0); ms2_claw(J, 114, sx, -30, 0, sx * 10, 0); ms2_claw(J, 124, sx, -12, 10, 0, 6)
    scene.frame_set(106); bpy.context.view_layer.update()
    c = J["root"].matrix_world.translation.copy(); c.y += 0.5
    ring_fx(f"{tg} stomp ring", (c.x, c.y, 0.04), 106, 0.4, 6.5, 9)
    cracks(tg, (c.x, c.y, 0.01), 106, 7, 1.5)
    for i in range(10):
        a = 2 * math.pi * i / 10 + 0.15
        r_ = 1.45 + 0.2 * (i % 2)
        sp = cyl(f"{tg} spike {i}", 0.16, 0.9 + 0.3 * (i % 3) / 2, CRYST, 6, None, loc=(c.x + r_ * math.cos(a), c.y + r_ * math.sin(a), -0.05), r2=0.0)
        sp.rotation_euler = (R(18) * math.sin(a), -R(18) * math.cos(a), a)
        fs = 106 + (i % 3)
        key(sp, 1, sc=0.0001); key(sp, fs, sc=0.0001); key(sp, fs + 2, sc=(1, 1, 1.15)); key(sp, fs + 3, sc=1.0)
        key(sp, 118, sc=1.0); key(sp, 122, sc=(1, 1, 0.0001))


def form_MS2(M, J, src):
    """Grown like crystal: the hull and pod swell from the middle, then each leg grows out joint by joint (femur, then
    tibia, then the tip), the claws reach out, and the crystal spikes pop last."""
    bpy.context.view_layer.update()
    c0 = J["hips"].matrix_world.translation
    for o in mparts(J):
        n = o.name; sc0 = tuple(o.scale)
        if "crystal" in n:
            fa = int(rng.integers(19, 23)); s0 = (0.0001,) * 3; over = (1.0, 1.0, 1.3)
        elif "femur plate" in n or "pincer arm" in n:
            fa = 11 if "femur" in n else 15; s0 = (1, 0.0001, 1); over = (1, 1.08, 1)
        elif "tibia" in n and "band" not in n:
            fa = 15; s0 = (1, 1, 0.0001); over = (1, 1, 1.08)
        elif "foot tip" in n or "jaw" in n or "piston" in n or "tibia band" in n:
            fa = 18; s0 = (0.0001,) * 3; over = (1.15,) * 3
        elif any(k in n for k in ("femur", "knee", "coxa", "pincer", "leg")):
            fa = 10 if "coxa" in n else 13; s0 = (0.0001,) * 3; over = (1.1,) * 3
        else:
            d = (centre(o) - c0).length
            fa = int(3 + min(1.0, d / 1.9) * 7); s0 = (0.0001,) * 3; over = (1.12,) * 3
        key(o, 1, sc=s0); key(o, max(1, fa - 3), sc=s0); key(o, fa, sc=tuple(a * b for a, b in zip(sc0, over))); key(o, fa + 2, sc=sc0)
    # crystal seeds on the ground under the legs, gone once the mech is whole
    for i in range(6):
        a = 2 * math.pi * i / 6
        s_ = cyl(f"{M.tag} seed {i}", 0.12, 0.45, CRYST, 6, None, loc=(c0.x + 0.9 * math.cos(a), c0.y + 0.9 * math.sin(a), 0.0), r2=0.0)
        key(s_, 1, sc=0.0001); key(s_, 2, sc=1.0); key(s_, 16, sc=1.0); key(s_, 20, sc=0.0001)


# ================================================================== MS3 Treadline (R2K1 dark jade, villager)
TR_HALF, TR_RAD, TR_N = 0.8, 0.3, 20


def tread_pt(s):
    Lp = 4 * TR_HALF + 2 * math.pi * TR_RAD
    laps = math.floor(s / Lp); s = s - laps * Lp; base = -2 * math.pi * laps
    if s < 2 * TR_HALF:
        return Vector((0, TR_HALF - s, -TR_RAD)), base
    s -= 2 * TR_HALF
    if s < math.pi * TR_RAD:
        t = s / TR_RAD
        return Vector((0, -TR_HALF - TR_RAD * math.sin(t), -TR_RAD * math.cos(t))), base - t
    s -= math.pi * TR_RAD
    if s < 2 * TR_HALF:
        return Vector((0, -TR_HALF + s, TR_RAD)), base - math.pi
    s -= 2 * TR_HALF; t = s / TR_RAD
    return Vector((0, TR_HALF + TR_RAD * math.sin(t), TR_RAD * math.cos(t))), base - math.pi - t


def build_MS3(tag, T):
    J = {"hz": 0.95}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} chassis", (0, 0, J["hz"]), root); J["hips"] = hips
    turret = empty(f"{tag} turret", (0, 0, 0.27), hips)
    torso = empty(f"{tag} torso", (0, 0, 0.0), turret); J["torso"] = torso
    plate(f"{tag} chassis body", (-0.62, -0.85, -0.32), (0.62, 0.85, 0.15), T, hips, 0.05)
    g = plate(f"{tag} glacis", (-0.6, 0.0, -0.25), (0.6, 0.3, 0.1), T, hips, 0.04); g.location = (0, 0.82, 0.02); g.rotation_euler = (R(-30), 0, 0)
    seam(f"{tag} chassis", hips, (-0.63, -0.85, -0.1), (0.63, 0.85, -0.08))
    sensor(f"{tag} low eye", hips, (0, 0.95, -0.12), 0.06)
    cyl(f"{tag} turret ring", 0.62, 0.13, FRAME, 24, hips, loc=(0, 0, 0.14))
    torus(f"{tag} turret ring glow", 0.63, 0.025, RM, loc=(0, 0, 0.21), parent=hips, n=32, k=6)
    treads = {}
    for sx in (-1, 1):
        tr = empty(f"{tag} tread {sx}", (sx * 0.86, 0, -0.58), hips)
        wheels = []
        for i, yy in enumerate((-TR_HALF, -0.27, 0.27, TR_HALF)):
            wp = empty(f"{tag} wheel pivot {sx} {i}", (0, yy, 0), tr)
            cyl(f"{tag} wheel {sx} {i}", TR_RAD - 0.06, 0.3, FRAME, 16, wp, loc=(-0.15, 0, 0), axis="X")
            cyl(f"{tag} wheel hub {sx} {i}", 0.09, 0.34, RM, 6, wp, loc=(-0.17, 0, 0), axis="X")
            for k in range(3):
                sp = box(f"{tag} wheel spoke {sx} {i} {k}", (0.155, -0.02, -0.2), (0.17, 0.02, 0.2), GR, wp)
                sp.rotation_euler = (R(60 * k), 0, 0)
            wheels.append(wp)
        out = sx * 0.24
        plate(f"{tag} tread skirt {sx}", (min(out, out + sx * 0.05), -0.75, -0.05), (max(out, out + sx * 0.05), 0.75, 0.28), T, tr, 0.02)
        plate(f"{tag} fender {sx}", (-0.25, -1.12, 0.36), (0.25, 1.12, 0.43), T, tr, 0.02)
        rivets(f"{tag} skirt {sx}", tr, [(out + sx * 0.05, yy, 0.18) for yy in (-0.6, -0.2, 0.2, 0.6)], 0.025)
        cleats = []
        Lp = 4 * TR_HALF + 2 * math.pi * TR_RAD
        for k in range(TR_N):
            cl = box(f"{tag} cleat {sx} {k}", (-0.21, -0.075, -0.035), (0.21, 0.075, 0.035), T, tr)
            box(f"{tag} cleat grouser {sx} {k}", (-0.21, -0.02, -0.07), (0.21, 0.02, -0.035), GR, cl)
            cleats.append((cl, k * Lp / TR_N))
        treads[sx] = (tr, wheels, cleats)
    anchors = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            an = empty(f"{tag} anchor {sx}{sy}", (sx * 0.5, sy * 0.95, -0.2), hips)
            cyl(f"{tag} anchor sleeve {sx}{sy}", 0.08, 0.3, FRAME, 10, hips, loc=(sx * 0.5, sy * 0.95, -0.25))
            cyl(f"{tag} anchor rod {sx}{sy}", 0.05, 0.55, ROD, 8, an, loc=(0, 0, -0.5))
            plate(f"{tag} anchor pad {sx}{sy}", (-0.14, -0.14, -0.6), (0.14, 0.14, -0.5), T, an, 0.02)
            anchors.append(an)
    pilot_seat_box(tag, torso, T, 0.85, -0.6, 0.55, 1.45)
    plate(f"{tag} roof", (-0.98, -0.7, 1.42), (0.98, 0.64, 1.58), T, torso, 0.05)
    plate(f"{tag} brow plate", (-0.9, 0.55, 1.3), (0.9, 0.72, 1.48), T, torso, 0.03)
    hatch = empty(f"{tag} canopy hinge", (0, 0.55, 1.42), torso)
    box(f"{tag} canopy", (-0.72, 0.0, -1.32), (0.72, 0.05, 0.0), GL, hatch)
    for xx in (-0.36, 0.0, 0.36):
        box(f"{tag} grille bar", (xx - 0.03, 0.0, -1.32), (xx + 0.03, 0.08, 0.0), FRAME, hatch)
    box(f"{tag} grille cross", (-0.72, 0.0, -0.7), (0.72, 0.08, -0.64), FRAME, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    for sx in (-1, 1):
        sensor(f"{tag} headlight {sx}", torso, (sx * 0.62, 0.72, 1.39), 0.07)
        vents(f"{tag} side {sx}", torso, (sx * 1.01 - 0.01, -0.4, 0.25), (sx * 1.01 + 0.01, 0.25, 0.95), 5)
    mast = empty(f"{tag} radar mast", (-0.62, -0.45, 1.58), torso)
    cyl(f"{tag} mast pole", 0.04, 0.5, FRAME, 8, mast)
    dish = empty(f"{tag} radar dish", (0, 0, 0.5), mast); J["dish"] = dish
    cyl(f"{tag} dish", 0.26, 0.12, T, 16, dish, loc=(0, -0.04, 0), axis="Y", r2=0.08)
    torus(f"{tag} dish rim", 0.26, 0.02, RM, loc=(0, -0.04, 0), parent=dish, n=20, k=6, axis="Y")
    ball(f"{tag} dish feed", 0.04, W, loc=(0, 0.18, 0), parent=dish, seg=8)
    stacks = []
    for i, xx in enumerate((0.42, 0.7)):
        cyl(f"{tag} exhaust {i}", 0.08, 0.55, FRAME, 12, torso, loc=(xx, -0.62, 1.0))
        torus(f"{tag} exhaust rim {i}", 0.08, 0.02, RM, loc=(xx, -0.62, 1.55), parent=torso, n=12, k=6)
        stacks.append(empty(f"{tag} exhaust tip {i}", (xx, -0.62, 1.6), torso))
    plate(f"{tag} engine box", (-0.3, -0.85, 0.3), (0.85, -0.6, 1.0), T, torso, 0.04)
    vents(f"{tag} engine", torso, (-0.2, -0.87, 0.4), (0.75, -0.85, 0.9), 4)
    arms = []
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.15, 0, 1.0), torso)
        ball(f"{tag} shoulder ball {sx}", 0.2, FRAME, parent=sh, seg=14)
        plate(f"{tag} pauldron {sx}", (-0.3, -0.36, -0.06), (0.3, 0.36, 0.3), T, sh, 0.04)
        vents(f"{tag} pauldron {sx}", sh, (sx * 0.3 - 0.01, -0.22, 0.0), (sx * 0.3 + 0.01, 0.22, 0.24), 3)
        plate(f"{tag} upper arm {sx}", (-0.15, -0.15, -0.6), (0.15, 0.15, -0.08), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.65), sh)
        cyl(f"{tag} elbow joint {sx}", 0.13, 0.3, FRAME, 12, el, loc=(-0.15, 0, 0), axis="X")
        piston(f"{tag} elbow {sx}", sh, (0, 0.18, -0.16), el, (0, 0.2, -0.28), 0.04)
        if sx == 1:                       # right: a drill
            cyl(f"{tag} drill housing", 0.22, -0.42, T, 16, el, loc=(0, 0, 0.02), r2=0.2)
            torus(f"{tag} drill collar", 0.21, 0.03, RM, loc=(0, 0, -0.4), parent=el, n=16, k=6)
            dr = empty(f"{tag} drill", (0, 0, -0.42), el); J["drill"] = dr
            cyl(f"{tag} drill cone", 0.19, -0.7, T, 12, dr, r2=0.0)
            for k in range(4):
                torus(f"{tag} drill flute {k}", 0.17 * (1 - (k + 0.5) / 4.6), 0.022, RM, loc=(0, 0, -0.1 - k * 0.15), parent=dr, n=12, k=5)
            for k in range(3):
                bl = box(f"{tag} drill blade {k}", (-0.012, 0.0, -0.62), (0.012, 0.16, -0.05), GR, dr)
                bl.rotation_euler = (R(-12), 0, R(120 * k))
            J["drill_tip"] = empty(f"{tag} drill tip", (0, 0, -0.72), dr)
        else:                             # left: a three-finger grab claw
            plate(f"{tag} claw forearm", (-0.2, -0.2, -0.42), (0.2, 0.2, 0.02), T, el, 0.04)
            wrist = empty(f"{tag} claw wrist", (0, 0, -0.42), el)
            J["hands"] = {-1: hand(f"{tag} claw", wrist, T, 0.0, 3, 0.32, 0.21)}
        arms.append((sh, el, sx))
    J.update(legs=[], arms=arms, treads=treads, anchors=anchors, stacks=stacks, turret=turret)
    J.setdefault("hands", {})
    return J


def anim_MS3(M):
    J = M.J; hz = J["hz"]; tg = M.tag; bx = M.bx; rt = J["root"]
    M.hatch(); M.hips(1, hz); M.torso(1)
    for sx in (-1, 1):
        M.arm(1, sx, 20, 50, sx * 6)
    M.fists(1, 0.3)
    for an in J["anchors"]:
        key(an, 1, loc=(an.location.x, an.location.y, -0.2))
    # 36-76: drives 1.6 m forward, pivot-turns 40 degrees left on its treads and back, the turret holding the cockpit
    # on the front all the time; the radar dish spins the whole clip
    off = 0.86 * S6

    def drive(f):
        dF = 1.6 * smooth((f - 36) / 20)
        th = 0.0
        if 56 <= f <= 63:
            th = 40 * smooth((f - 56) / 7)
        elif 63 < f <= 70:
            th = 40 * (1 - smooth((f - 63) / 7))
        return dF, th
    for f in list(range(1, 36, 34)) + list(range(36, 77)):
        dF, th = drive(f)
        rt.location = (bx, dF, 0); rt.rotation_euler = (0, 0, R(th))
        rt.keyframe_insert("location", frame=f); rt.keyframe_insert("rotation_euler", frame=f)
        key(J["turret"], f, rot=(0, 0, R(-th)))
        for sx in (-1, 1):
            d = (dF + sx * R(th) * off) / S6
            tr, wheels, cleats = J["treads"][sx]
            for wp in wheels:
                key(wp, f, rot=(-d / (TR_RAD - 0.03), 0, 0))
            for cl, s0 in cleats:
                p, a = tread_pt(s0 + d)
                key(cl, f, loc=tuple(p), rot=(a, 0, 0))
    for sx in (-1, 1):
        for wp in J["treads"][sx][1]:
            linear(wp)
        for cl, _ in J["treads"][sx][2]:
            linear(cl)
    M.hips(36, hz); M.hips(40, hz, -4); M.hips(52, hz, 0); M.hips(57, hz, 5); M.hips(62, hz, 0); M.hips(72, hz, 3); M.hips(76, hz)
    for sx in (-1, 1):
        M.arm(40, sx, 10, 60, sx * 6); M.arm(70, sx, 10, 60, sx * 6); M.arm(76, sx, 20, 50, sx * 6)
    for k, f in enumerate((38, 46, 54, 62)):
        for st in J["stacks"]:
            puff(f"{tg} exhaust puff {k}", tuple(wpos(st, f)), f + 1, 0.11, 0.5)
    spin_keys(J["dish"], 1, 130, 5, 2, 2); linear(J["dish"])
    y = 1.6
    # 76-96: drill thrust: the drill spins up, the turret winds left, then it drives the drill straight into a stone
    # block ahead; sparks, the block bursts
    dr = J["drill"]
    for f in (1, 76):
        key(dr, f, rot=(0, 0, 0))
    spin_keys(dr, 76, 126, 7, 2, 2); linear(dr)
    M.torso(80, 0, 0, 18); M.arm(80, 1, 55, 70, 8); M.arm(80, -1, 40, 80, -6)
    M.torso(84, 4, 0, -10); M.arm(84, 1, 90, 0, 0); M.hips(84, hz, 6)
    M.torso(90, 4, 0, -10); M.arm(90, 1, 90, 0, 0); M.hips(90, hz, 6)
    M.torso(95, 0, 0, 0); M.arm(95, 1, 30, 50, 6); M.arm(95, -1, 20, 50, -6); M.hips(95, hz)
    tip = wpos(J["drill_tip"], 85)
    blks = []                                  # a two-block stone pillar; the drill bites into the top block
    for k in range(2):
        b_ = plate(f"{tg} stone block {k}", (-0.3, -0.3, -0.3), (0.3, 0.3, 0.3), STONE, None, 0.01)
        b_.location = (tip.x, tip.y + 0.3, tip.z - 0.6 * k); blks.append(b_)
        key(b_, 1, sc=0.0001); key(b_, 77, sc=0.0001); key(b_, 79, sc=1.0)
    print(tg, "drill tip at frame 85: z %.2f" % tip.z, flush=True)
    shatter(blks[:1], 89, STONE, rng, tg + " stone", 10, 0.12, 14)
    shatter(blks[1:], 92, STONE, rng, tg + " stone low", 6, 0.08, 12)
    for k, f in enumerate((85, 87, 89)):
        ring_fx(f"{tg} drill sparks {k}", tuple(tip + Vector((0, 0.05, 0))), f, 0.1, 3.0, 4, axis="Y", th=0.02)
    # 96-126: anchored spin: four anchors punch into the ground, the turret spins a full turn with both arms out and
    # the drill screaming, a ring of light sweeps round; anchors pull up
    for an in J["anchors"]:
        x_, y_ = an.location.x, an.location.y
        key(an, 96, loc=(x_, y_, -0.2)); key(an, 99, loc=(x_, y_, -0.66)); key(an, 118, loc=(x_, y_, -0.66)); key(an, 122, loc=(x_, y_, -0.2))
    M.hips(99, hz + 0.04); M.hips(118, hz + 0.04); M.hips(122, hz)
    tt = J["turret"]
    key(tt, 96, rot=(0, 0, 0)); key(tt, 101, rot=(0, 0, R(-20)))
    key(tt, 104, rot=(0, 0, R(60))); key(tt, 107, rot=(0, 0, R(160))); key(tt, 110, rot=(0, 0, R(260))); key(tt, 113, rot=(0, 0, R(345)))
    key(tt, 117, rot=(0, 0, R(360)))
    for sx in (-1, 1):
        M.arm(100, sx, 20, 20, 0, -sx * 80); M.arm(114, sx, 20, 20, 0, -sx * 80); M.arm(120, sx, 20, 50, sx * 6)
    c = wpos(J["torso"], 107)
    tr_ = arc(f"{tg} spin trail", 1.25, 0.08, 0.0, 2 * math.pi * 0.85, SHOCK, (c.x, c.y, c.z + 0.6))
    key(tr_, 1, sc=0.0001, rot=(0, 0, 0)); key(tr_, 102, sc=0.0001, rot=(0, 0, R(30))); key(tr_, 104, sc=1.0, rot=(0, 0, R(60)))
    key(tr_, 113, sc=1.0, rot=(0, 0, R(340))); key(tr_, 115, sc=0.0001, rot=(0, 0, R(360)))
    ring_fx(f"{tg} spin ring", (c.x, c.y, 0.05), 104, 0.6, 3.5, 12)
    cracks(tg, (c.x, c.y, 0.01), 99, 6, 1.2)


def form_MS3(M, J, src):
    """Assembled on rails: two glowing rails run out either side, every plate slides in along them from its own side
    (centre parts drop in from above), bottom first, and clamps with a small overshoot."""
    bpy.context.view_layer.update()
    bx = J["root"].matrix_world.translation.x
    rails = []
    for sx in (-1, 1):
        for z in (0.05, 1.4):
            r_ = box(f"{M.tag} rail {sx} {z}", (bx + sx * 0.6, -0.05, z), (bx + sx * 3.8, 0.05, z + 0.06), RM)
            key(r_, 1, sc=0.0001); key(r_, 2, sc=1.0); key(r_, 22, sc=1.0); key(r_, 24, sc=0.0001); rails.append(r_)
    parts = mparts(J, ("cleat",))
    zs = [centre(o).z for o in parts]; lo, hi = min(zs), max(zs) + 1e-6
    for o, z in zip(parts, zs):
        c = centre(o); dx = c.x - bx
        off = Vector((3.2 * (1 if dx > 0 else -1), 0, 0)) if abs(dx) > 0.25 else Vector((0, 0, 2.5))
        offl = o.parent.matrix_world.to_3x3().inverted() @ off
        l0 = Vector(o.location); fa = int(round(4 + (z - lo) / (hi - lo) * 16)) + int(rng.integers(0, 2))
        sc0 = tuple(o.scale)
        key(o, 1, loc=tuple(l0 + offl), sc=0.0001); key(o, fa - 4, loc=tuple(l0 + offl), sc=0.0001)
        key(o, fa - 3, loc=tuple(l0 + offl), sc=sc0); key(o, fa, loc=tuple(l0 - offl * 0.03), sc=sc0); key(o, fa + 1, loc=tuple(l0), sc=sc0)
    for o in mparts(J):
        if "cleat" in o.name and "grouser" not in o.name:
            sc0 = tuple(o.scale); key(o, 1, sc=0.0001); key(o, 4, sc=0.0001); key(o, 6, sc=sc0)


# ------------------------------------------------------------------ build the three takes
TAKES = [("MS1", "Workhorse", "w1", "villager", build_MS1, anim_MS1, form_MS1, 84),
         ("MS2", "Crawler", "v1", "zombie", build_MS2, anim_MS2, form_MS2, 107),
         ("MS3", "Treadline", "r2k1", "villager", build_MS3, anim_MS3, form_MS3, 108)]
BAY = 14.0
for bi, (tk, name, look, pk, bf, af, ff, peak) in enumerate(TAKES):
    bx = bi * BAY
    tag = f"M6 {tk}"
    box(f"{tag} floor", (bx - 5, -5, -0.02), (bx + 5, 11, 0), FLOOR)
    J = bf(tag, TEX[look])
    J["root"].location = (bx, 0, 0); J["root"].scale = (S6,) * 3
    M = Mech(tag, J, bx)
    seat_parent = J["torso"]
    prig, PM = pilot(f"{tag} pilot", pk, seat_parent, J["seat"])
    af(M)
    pr = prig["root"]
    scene.frame_set(1); bpy.context.view_layer.update()
    stand_local = seat_parent.matrix_world.inverted() @ Vector((bx, 0.0, 0.0))
    key(pr, 1, loc=tuple(stand_local)); key(pr, 24, loc=tuple(stand_local)); key(pr, 30, loc=J["seat"])
    pose(prig, 1, leg_r=(0, 0, 0), leg_l=(0, 0, 0), shin_r=(0, 0, 0), shin_l=(0, 0, 0), arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0))
    pose(prig, 24, leg_r=(0, 0, 0), leg_l=(0, 0, 0), shin_r=(0, 0, 0), shin_l=(0, 0, 0), arm_r=(40, 0, 0), arm_l=(40, 0, 0))
    pose(prig, 30, leg_r=(90, 0, 6), leg_l=(90, 0, -6), shin_r=(-90, 0, 0), shin_l=(-90, 0, 0), arm_r=(60, 0, 0), arm_l=(60, 0, 0),
         fore_r=(20, 0, 0), fore_l=(20, 0, 0))
    if pk == "zombie":                                       # zombie arms stay out in front, as zombies do
        pose(prig, 1, arm_r=(90, 0, 0), arm_l=(90, 0, 0)); pose(prig, 24, arm_r=(90, 0, 0), arm_l=(90, 0, 0))
    scene.frame_set(1); bpy.context.view_layer.update()
    ring_world = prig["ring_pt"].matrix_world.translation.copy()
    ff(M, J, tuple(ring_world))
    if tk == "MS3":                                          # from the drill side, so the pillar doesn't hide the bite
        cam(f"Cam {tk}", (bx + 6.4, 5.6, 2.4), (bx, 2.2, 0.9), 30)
    else:
        cam(f"Cam {tk}", (bx + 3.8, 7.6, 2.6), (bx, 2.1, 1.0), 30)
    cam(f"Cam {tk} close", (bx + 2.0, 5.0, 1.9), (bx, 2.2, 1.0), 30)
    label(f"{tk}  {name}  - pilot: {'baby zombie' if pk == 'zombie' else pk}", (bx, -3.0, 3.6), LBL, 0.28, rot=(R(90), 0, R(180)))
    print(tk, "built", flush=True)
cam("Cam row MS", (BAY, 30, 8), (BAY, 2.0, 1.2), 30)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam MS1", 1, (0.35, 0.45, 0.6), 3.0




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

