# Pass 841: flying mounts, F1-F3 variations (Chat C, 2026-10-15, range 800-899). Replaces 824 F1, F2, F3 (IMPROVE, no
# note: "3 new variations each", labelled, he picks). 824 F4 (harnessed ghast) has its own note and is not in this pass.
# J on 809: "horse is the only flying construct i want right now, maybe well force the lantern user to learn to ride a
# flying creature, give me a flying baby dragon to ride on and also a ghast construct (it needs to fit the real model
# instead of colliding with it, but since ours is pure construct you can make a new textured ghast instead".
# Textures are his construct picks from docs/texture_library: R2 K1 dark-jade fragments (default look), BR1, H1, W1.
#   F1a winged horse (R2 K1): 824's blocky horse plus feathered slat wings; gallops, leaps, wing-powered climb, glides
#   F1b hoop horse (W1): built as open hoops on a spine; never flies, it gallops up a road of light tiles that form just
#       ahead of the hooves and break up behind
#   F1c comet horse (H1): smooth tapered body; rears, launches, legs stretched fore and aft, light streamers from the
#       hooves; a swooping dive-and-climb with banks
#   F2a round wyrmling (BR1): ball body and head, bat wings on three finger bones; hovers straight up with heavy flaps,
#       then flies off weaving
#   F2b serpent hatchling (R2 K1): a long nine-link body that swims through the air in an S-wave, little fast wings
#   F2c blocky glider (H1): voxel boxes, wide four-finger wings; a leap, two big flaps, then a long banked glide
#   F3a snug shell (R2 K1): the real ghast (4.5-block body, vanilla tentacle layout and lengths) inside a bevelled
#       one-piece shell 0.06-0.16 off its skin, each tentacle in a round sleeve; rises and drifts in a slow turn
#   F3b lattice cage (W1): the real ghast seen through a 3 x 3 window cage, tentacles in stacked hoops; swims forward in
#       pulses
#   F3c brick strata (BR1): five stacked slabs that breathe apart, glow on every outer edge (all 12), segmented
#       tentacle sleeves, a protruding brow; rises high and banks round a wide turn
# Every construct tentacle rides the vanilla tentacle swing (xRot = 0.2 sin(0.3 t + i) + 0.4), so it never cuts the real
# model. Cameras "Cam <take>" (follows), "Cam <take> side", "Cam row F1/F2/F3". Builds
# LanternLive\constructs\flying_mounts2.blend.
SCENE_NAME = "Flying Mounts 2"
OUT_REL = "constructs/flying_mounts2.blend"
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
    a, b = np.minimum(np.array(a, float), np.array(b, float)), np.maximum(np.array(a, float), np.array(b, float))
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


def strip_mat(name, im, ft=4, emit=1.6, alpha=None, base_mul=1.0, over=None):
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
    colour = mc.outputs[2]
    if over is not None:                      # the strip's own alpha lays its lines over a solid base colour
        ma0 = N.new("ShaderNodeMix"); ma0.data_type = "FLOAT"; L.new(wv.outputs[0], ma0.inputs["Factor"])
        L.new(outs[0].outputs["Alpha"], ma0.inputs[2]); L.new(outs[1].outputs["Alpha"], ma0.inputs[3])
        mo = N.new("ShaderNodeMix"); mo.data_type = "RGBA"; L.new(ma0.outputs[0], mo.inputs["Factor"])
        mo.inputs[6].default_value = (*over, 1); L.new(mc.outputs[2], mo.inputs[7]); colour = mo.outputs[2]
        p.inputs["Alpha"].default_value = min(0.99, alpha if alpha is not None else 0.99)
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        alpha = None
    L.new(colour, p.inputs["Base Color"]); L.new(colour, p.inputs["Emission Color"])
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
FORM = 20
FLOOR = mat("FM2 floor", (0.18, 0.21, 0.2), rough=0.9)
LBL = mat("FM2 label", (0.3, 1.0, 0.45), emit=2.0)
REAL = mat("FM2 real ghast (reference)", (0.62, 0.62, 0.6), alpha=0.45, rough=0.7)
REAL_DARK = mat("FM2 real ghast face", (0.08, 0.08, 0.09), alpha=0.6)
rng = np.random.default_rng(841)
CM = cmats("FM2", "green")
RM, W, GR, GL = CM["rim"], CM["glow"], CM["grip"], CM["glass"]
DARK_RIM = mat("FM2 dark jade rim", (0.03, 0.42, 0.16), emit=2.2)     # darker glow line for the dark-jade takes


def r2k1_image():
    """J's default construct look: R2 small fragments in K1 dark jade (tools/construct_jade_game.py), dark jade lines
    over a jade base. From LanternLive\\texture_library\\green\\r2k1 if there, else the game's resource pack."""
    cands = [os.path.join(TEXLIB, "green", "r2k1", "construct_r2k1_green.png"),
             os.path.join(TEXLIB, "green", "r2k1", "construct_ripples_r2k1.png"),
             os.path.join(os.getcwd(), "src", "main", "resources", "resourcepacks", "constructs_jade_r1", "assets",
                          "lanternring", "textures", "block", "construct_ripples_r2k1.png")]
    for p in cands:
        if os.path.isfile(p):
            im = bpy.data.images.load(p)
            try:
                im.pack()
            except Exception:
                pass
            return im
    raise FileNotFoundError("construct_ripples_r2k1.png")


K1_BASE = (0.021, 0.19, 0.09)          # the K1 jade under the fragments, sRGB (40, 120, 85)
TEX = {k: strip_mat(f"FM2 {k} texture", strip_image("green", k), 4, emit=1.3, alpha=0.9) for k in ("br1", "w1", "h1")}
TEX["r2k1"] = strip_mat("FM2 r2k1 dark jade texture", r2k1_image(), 4, emit=1.2, alpha=0.5, over=K1_BASE)


def mesh(name, vs, fs, m, parent=None, smooth_=False, uvt=0.5):
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); me.materials.append(m)
    uv = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        poly.use_smooth = smooth_
        n = np.abs(np.array(poly.normal)); ax = int(np.argmax(n)); o_ = [i for i in range(3) if i != ax]
        for li in poly.loop_indices:
            co = np.array(me.vertices[me.loops[li].vertex_index].co)
            uv.data[li].uv = (co[o_[0]] / uvt, co[o_[1]] / uvt)
    o = link(bpy.data.objects.new(name, me))
    if parent is not None:
        o.parent = parent
    return o


def slab(name, pts, th, m, parent=None):
    """A flat polygon (list of (x, y, z) points, in order) given thickness th along its normal: a wing membrane."""
    p = [Vector(q) for q in pts]
    n = (p[1] - p[0]).cross(p[2] - p[0]).normalized() * (th / 2)
    vs = [tuple(q - n) for q in p] + [tuple(q + n) for q in p]
    k = len(p)
    fs = [tuple(range(k))[::-1], tuple(range(k, 2 * k))] + [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
    return mesh(name, vs, fs, m, parent)


def bar(name, a, b, r, m, parent=None, n=8):
    """A round rod from a to b (local points)."""
    a = Vector(a); b = Vector(b); d = b - a
    o = cyl(name, r, d.length, m, n=n, parent=parent, loc=tuple(a))
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return o


def bevel(o, w=0.12, seg=3):
    md = o.modifiers.new("bevel", "BEVEL"); md.width = w; md.segments = seg; md.limit_method = "ANGLE"
    for p_ in o.data.polygons:
        p_.use_smooth = True
    return o


def rider(tag, parent, loc, legs_down=False):
    M = player_mats(tag)
    rig = make_player(tag, (0, 0, 0), M)
    rig["root"].parent = parent; rig["root"].location = Vector(loc) - Vector((0, 0, 12 * P))
    if legs_down:
        pose(rig, 1, leg_r=(20, 0, 25), leg_l=(20, 0, -25), shin_r=(-30, 0, 0), shin_l=(-30, 0, 0), arm_r=(55, 0, 0), arm_l=(55, 0, 0),
             fore_r=(20, 0, 0), fore_l=(20, 0, 0), body=(-14, 0, 0), head=(10, 0, 0))
    else:
        pose(rig, 1, leg_r=(90, 0, 8), leg_l=(90, 0, -8), shin_r=(-90, 0, 0), shin_l=(-90, 0, 0), arm_r=(60, 0, 0), arm_l=(60, 0, 0),
             fore_r=(10, 0, 0), fore_l=(10, 0, 0), body=(-12, 0, 0), head=(8, 0, 0))
    return rig


def fly(root, pos, f0=FORM + 2, f1=FRAME_END, bank_k=0.0, pitch_k=1.0, extra=None):
    """Key the mount along pos(u, f) -> (x, y, z); it faces where it moves (yaw), noses up/down with the climb and
    banks into turns. extra(u, f) -> (dpitch, droll) in radians adds poses (a rear, a flap pitch)."""
    def at(f):
        return Vector(pos(max(0.0, (f - f0) / (f1 - f0)), f))
    yaw_prev = 0.0
    for f in range(1, f1 + 1, 2):
        u = max(0.0, (f - f0) / (f1 - f0))
        p0, p1 = at(f - 1), at(f + 1)
        d = p1 - p0
        h = math.hypot(d.x, d.y)
        yaw = math.atan2(-d.x, d.y) if h > 1e-3 else yaw_prev
        pitch = math.atan2(d.z, h) * pitch_k if h > 1e-3 else 0.0
        d2 = at(f + 3) - at(f + 1); yaw2 = math.atan2(-d2.x, d2.y) if math.hypot(d2.x, d2.y) > 1e-3 else yaw
        roll = -(yaw2 - yaw) * bank_k
        if extra is not None:
            ep, er = extra(u, f); pitch += ep; roll += er
        key(root, f, loc=tuple(at(f)), rot=(pitch, roll, yaw)); yaw_prev = yaw


def follow_cam(tag, root, back=7.0, up=2.8, side=2.4, look_up=1.2):
    """Follows the mount's position and heading only (never its pitch or bank), so the horizon stays level."""
    rig = empty(f"Cam {tag} rig")
    cl = rig.constraints.new("COPY_LOCATION"); cl.target = root
    cr = rig.constraints.new("COPY_ROTATION"); cr.target = root; cr.use_x = False; cr.use_y = False
    c = cam(f"Cam {tag}", (0, 0, 0), (0, 1, 0), 30)
    c.parent = rig; c.location = (side, -back, up)
    d = Vector((0, 1.8, look_up)) - Vector(c.location)
    c.rotation_euler = (math.atan2(math.hypot(d.x, d.y), -d.z), 0, math.atan2(d.y, d.x) - math.pi / 2)
    return c


def meshes(root):
    return [o for o in root.children_recursive if o.type == "MESH" and " rider " not in o.name and "real ghast" not in o.name]


def gallop(legs, f, run, period=10, tuck=0.0, stretch=0.0):
    """Horse legs: (hip, knee, phase, front?) - run 0..1 gallop strength, tuck 0..1 folds the legs, stretch 0..1 reaches
    the front legs forward and the hind legs back (the flying pose)."""
    for hip, kn, ph, front in legs:
        a = 2 * math.pi * (f / period + ph)
        g = 38 * math.sin(a) * run
        h = g * (1 - tuck - stretch) + (70 if front else -60) * stretch + (25 if front else -20) * tuck
        k = -50 * max(0.0, math.sin(a + 1.2)) * run * (1 - stretch) - (95 if front else -60) * tuck
        key(hip, f, rot=(R(h), 0, 0)); key(kn, f, rot=(R(k), 0, 0))


# ================================================================== F1: the flying horse
def horse_blocky(tag, root, T, trim):
    """824's horse: box barrel, neck, head, ears, 6-lock mane, 4-lock tail, saddle, four 2-part legs."""
    b = empty(f"{tag} body", (0, 0, 1.0), root)
    box(f"{tag} barrel", (-0.32, -0.8, -0.27), (0.32, 0.8, 0.32), T, b)
    nk = empty(f"{tag} neck", (0, 0.75, 0.15), b)
    box(f"{tag} neck box", (-0.18, -0.1, 0.0), (0.18, 0.27, 0.7), T, nk)
    hd = empty(f"{tag} head", (0, 0.2, 0.65), nk)
    box(f"{tag} head box", (-0.16, -0.05, -0.16), (0.16, 0.6, 0.16), T, hd)
    for s in (-1, 1):
        box(f"{tag} eye {s}", (s * 0.165 - 0.01, 0.32, 0.02), (s * 0.165 + 0.01, 0.38, 0.08), trim, hd)
        box(f"{tag} ear {s}", (s * 0.1 - 0.03, 0.0, 0.16), (s * 0.1 + 0.03, 0.06, 0.28), T, hd)
    mane = []
    for k in range(6):
        mn = empty(f"{tag} mane {k}", (0, -0.12, 0.1 * k + 0.05), nk)
        box(f"{tag} mane lock {k}", (-0.04, -0.2, -0.04), (0.04, 0.0, 0.05), trim, mn); mane.append(mn)
    tl = empty(f"{tag} tail", (0, -0.8, 0.2), b)
    for k in range(4):
        box(f"{tag} tail lock {k}", (-0.06, -0.08 - k * 0.18, -0.06), (0.06, -k * 0.18, 0.06), trim, tl)
    box(f"{tag} saddle", (-0.34, -0.25, 0.32), (0.34, 0.2, 0.38), GR, b)
    legs = []
    for (lx, ly, ph) in ((0.2, 0.65, 0.0), (-0.2, 0.65, 0.5), (0.2, -0.65, 0.25), (-0.2, -0.65, 0.75)):
        hip = empty(f"{tag} hip {lx} {ly}", (lx, ly, -0.2), b)
        box(f"{tag} upper leg {lx} {ly}", (-0.08, -0.08, -0.42), (0.08, 0.08, 0.0), T, hip)
        kn = empty(f"{tag} knee {lx} {ly}", (0, 0, -0.42), hip)
        box(f"{tag} lower leg {lx} {ly}", (-0.065, -0.065, -0.38), (0.065, 0.065, 0.0), T, kn)
        box(f"{tag} hoof {lx} {ly}", (-0.08, -0.08, -0.42), (0.08, 0.1, -0.36), trim, kn)
        legs.append((hip, kn, ph, ly > 0))
    rider(f"{tag} rider", b, (0, -0.05, 0.38))
    return b, nk, tl, mane, legs


def build_F1a(tag, root, bx):
    """Winged horse, R2 K1: feathered slat wings on the shoulders. Gallop, leap, wing-driven climb, glide."""
    T = TEX["r2k1"]
    b, nk, tl, mane, legs = horse_blocky(tag, root, T, DARK_RIM)
    wings = []
    for s in (-1, 1):
        wr = empty(f"{tag} wing {s}", (s * 0.33, 0.35, 0.25), b)
        box(f"{tag} wing arm {s}", (0, -0.05, -0.04), (s * 0.7, 0.05, 0.04), DARK_RIM, wr)
        tip = empty(f"{tag} wing tip {s}", (s * 0.7, 0, 0), wr)
        box(f"{tag} wing hand {s}", (0, -0.04, -0.03), (s * 0.55, 0.04, 0.03), DARK_RIM, tip)
        for k in range(7):                       # long feather slats, longest at the tip, each slightly spread
            ln = 0.55 + 0.12 * k if k < 5 else 1.05 - 0.15 * (k - 5)
            x = s * (0.12 + 0.18 * k)
            par = wr if k < 4 else tip
            x_ = x if k < 4 else x - s * 0.7
            fe = empty(f"{tag} feather {s} {k}", (x_, 0, 0), par); fe.rotation_euler = (0, 0, R(-s * (4 * k - 8)))
            box(f"{tag} feather slat {s} {k}", (-0.07, -ln, -0.012), (0.07, 0.0, 0.012), T, fe)
        wings.append((wr, tip, s))
    def pos(u, f):
        y = 32 * u
        z = 0.0 if u < 0.22 else 8.5 * smooth((u - 0.22) / 0.45)
        return (bx, y, z)
    fly(root, pos, pitch_k=0.8)
    for f in range(1, FRAME_END + 1):
        run = min(1.0, max(0.0, (f - FORM) / 6))
        air = smooth((f - 44) / 6)
        gallop(legs, f, run * (1 - air), tuck=air * 0.6, stretch=air * 0.4)
        glide = f >= 92
        a = 2 * math.pi * f / 12
        for wr, tip, s in wings:
            up = (0 if glide else 55 * math.sin(a)) * min(1.0, max(0.0, (f - 36) / 6))
            fold = 70 * (1 - min(1.0, max(0.0, (f - 32) / 8)))            # folded along the body while galloping
            key(wr, f, rot=(0, R(-s * (up - 8)), R(s * fold)))
            key(tip, f, rot=(0, R(-s * (-18 * math.sin(a - 0.8) if not glide else -4)), 0))
        a2 = 2 * math.pi * f / 10
        key(b, f, loc=(0, 0, 1.0 + 0.08 * abs(math.sin(a2)) * run * (1 - air)))
        key(nk, f, rot=(R(-20 + 10 * math.sin(a2) * run - 15 * air), 0, 0))
        key(tl, f, rot=(R(60 * run + 10 * math.sin(a2)), 0, 0))
        for k, mn in enumerate(mane):
            key(mn, f, rot=(R(-30 * run - 25 * air + 12 * math.sin(a2 - k * 0.6)), 0, 0))
    return 1, 80


def build_F1b(tag, root, bx):
    """Hoop horse, W1: an open frame of hoops threaded on a spine rod; gallops up a road of light tiles that form
    under the hooves just ahead and break up behind. It never leaves the road: running on light."""
    T = TEX["w1"]
    b = empty(f"{tag} body", (0, 0, 1.05), root)
    bar(f"{tag} spine", (0, -0.85, 0.05), (0, 0.85, 0.12), 0.05, RM, b)
    for k in range(6):                              # barrel hoops, fattest in the middle
        y = -0.7 + 0.28 * k; r = 0.34 - 0.06 * abs(k - 2.5) ** 1.3
        torus(f"{tag} barrel hoop {k}", r, 0.06, T, loc=(0, y, 0.0), parent=b, axis="Y", n=20, k=6)
    nk = empty(f"{tag} neck", (0, 0.85, 0.1), b); nk.rotation_euler = (R(-35), 0, 0)
    for k in range(4):
        torus(f"{tag} neck hoop {k}", 0.2 - 0.02 * k, 0.045, T, loc=(0, 0, 0.18 * k), parent=nk, n=16, k=6)
    bar(f"{tag} neck rod", (0, 0, 0), (0, 0, 0.7), 0.04, RM, nk)
    hd = empty(f"{tag} head", (0, 0.0, 0.72), nk); hd.rotation_euler = (R(-50), 0, 0)
    for k in range(3):
        torus(f"{tag} head hoop {k}", 0.15 - 0.025 * k, 0.04, T, loc=(0, 0.06 + 0.2 * k, 0), parent=hd, axis="Y", n=16, k=6)
    for s in (-1, 1):
        box(f"{tag} eye {s}", (s * 0.15 - 0.02, 0.12, 0.03), (s * 0.15 + 0.02, 0.2, 0.08), RM, hd)
        bar(f"{tag} ear {s}", (s * 0.07, 0.0, 0.1), (s * 0.09, -0.02, 0.3), 0.025, RM, hd)
    mane = []
    for k in range(5):                                 # mane: flat ribbons that stream
        mn = empty(f"{tag} mane {k}", (0, -0.18, 0.14 * k + 0.05), nk)
        box(f"{tag} mane ribbon {k}", (-0.015, -0.32, -0.05), (0.015, 0.0, 0.05), T, mn); mane.append(mn)
    tl = empty(f"{tag} tail", (0, -0.85, 0.12), b)
    for k in range(3):
        box(f"{tag} tail ribbon {k}", (-0.02 + 0.05 * (k - 1), -0.7, -0.05), (0.02 + 0.05 * (k - 1), 0.0, 0.05), T, tl)
    box(f"{tag} saddle pad", (-0.3, -0.25, 0.3), (0.3, 0.2, 0.35), GR, b)
    legs = []
    for (lx, ly, ph) in ((0.18, 0.6, 0.0), (-0.18, 0.6, 0.5), (0.18, -0.6, 0.25), (-0.18, -0.6, 0.75)):
        hip = empty(f"{tag} hip {lx} {ly}", (lx, ly, -0.15), b)
        bar(f"{tag} thigh {lx} {ly}", (0, 0, 0), (0, 0, -0.45), 0.05, RM, hip)
        torus(f"{tag} knee ring {lx} {ly}", 0.08, 0.03, T, loc=(0, 0, -0.45), parent=hip, n=12, k=5)
        kn = empty(f"{tag} knee {lx} {ly}", (0, 0, -0.45), hip)
        bar(f"{tag} cannon {lx} {ly}", (0, 0, 0), (0, 0, -0.38), 0.04, RM, kn)
        torus(f"{tag} hoof ring {lx} {ly}", 0.08, 0.035, T, loc=(0, 0, -0.42), parent=kn, n=12, k=5)
        legs.append((hip, kn, ph, ly > 0))
    rider(f"{tag} rider", b, (0, -0.05, 0.35))
    def ht(u):
        return 9.0 * smooth((u - 0.12) / 0.75)
    def pos(u, f):
        return (bx, 30 * u, ht(u))
    fly(root, pos, pitch_k=0.9)
    period = 10
    for f in range(1, FRAME_END + 1):
        run = min(1.0, max(0.0, (f - FORM) / 6))
        gallop(legs, f, run, period=period)
        a = 2 * math.pi * f / period
        key(b, f, loc=(0, 0, 1.05 + 0.08 * abs(math.sin(a)) * run), rot=(R(4 * math.sin(a) * run), 0, 0))
        key(tl, f, rot=(R(55 * run + 12 * math.sin(a)), 0, 0))
        for k, mn in enumerate(mane):
            key(mn, f, rot=(R(-35 * run + 14 * math.sin(a - k * 0.7)), 0, 0))
    # the road: a tile forms under where the hooves will land 4 ticks ahead, then breaks behind
    for f in range(FORM + 6, FRAME_END - 2, 3):
        u = (f + 4 - FORM - 2) / (FRAME_END - FORM - 2)
        if u <= 0.1:
            continue
        y = 30 * u; z = ht(u); slope = math.atan2(ht(u + 0.01) - ht(u - 0.01), 0.6)
        tile = box(f"{tag} road tile {f}", (-0.45, -0.5, -0.04), (0.45, 0.5, 0.0), T)
        tile.location = (bx, y, z); tile.rotation_euler = (slope, 0, 0)
        edge = box(f"{tag} road edge {f}", (-0.47, -0.52, -0.06), (0.47, 0.52, -0.04), RM, tile)
        key(tile, 1, sc=0.0001); key(tile, f - 1, sc=0.0001); key(tile, f + 1, sc=1.0); key(tile, f + 14, sc=1.0)
        key(tile, f + 18, sc=(1.3, 1.3, 0.2)); key(tile, f + 19, sc=0.0001)
    return 1, 80


def build_F1c(tag, root, bx):
    """Comet horse, H1: a smooth tapered body (ellipsoids and cones, no boxes); rears, launches, legs stretched fore and
    aft; light streamers trail from the hooves; swoops down and climbs again with banked turns."""
    T = TEX["h1"]
    b = empty(f"{tag} body", (0, 0, 1.0), root)
    bd = ball(f"{tag} barrel", 0.36, T, parent=b, seg=20); bd.scale = (0.95, 2.35, 1.0)
    nk = empty(f"{tag} neck", (0, 0.65, 0.18), b); nk.rotation_euler = (R(-30), 0, 0)
    cyl(f"{tag} neck cone", 0.24, 0.72, T, n=14, parent=nk, r2=0.13)
    hd = empty(f"{tag} head", (0, 0.0, 0.72), nk); hd.rotation_euler = (R(-60), 0, 0)
    h_ = ball(f"{tag} skull", 0.16, T, loc=(0, 0.14, 0), parent=hd, seg=14); h_.scale = (0.9, 1.9, 1.0)
    for s in (-1, 1):
        ball(f"{tag} eye {s}", 0.035, RM, loc=(s * 0.13, 0.2, 0.06), parent=hd, seg=8)
        cyl(f"{tag} ear {s}", 0.04, 0.16, T, n=8, parent=hd, loc=(s * 0.07, 0.0, 0.1), r2=0.0)
    crest = []
    for k in range(5):                                  # a crest of blade fins instead of a mane
        mn = empty(f"{tag} crest {k}", (0, -0.14, 0.14 * k + 0.05), nk)
        slab(f"{tag} crest fin {k}", [(0, 0.04, 0), (0, -0.32, 0.06), (0, -0.05, 0.14)], 0.02, RM, mn); crest.append(mn)
    tl = empty(f"{tag} tail", (0, -0.82, 0.15), b)
    cyl(f"{tag} tail cone", 0.12, 0.9, T, n=10, parent=tl, axis="Y", r2=0.0).rotation_euler = (0, 0, R(180))
    box(f"{tag} saddle", (-0.32, -0.25, 0.32), (0.32, 0.2, 0.38), GR, b)
    legs = []
    hooves = []
    for (lx, ly, ph) in ((0.18, 0.55, 0.0), (-0.18, 0.55, 0.5), (0.18, -0.55, 0.25), (-0.18, -0.55, 0.75)):
        hip = empty(f"{tag} hip {lx} {ly}", (lx, ly, -0.18), b)
        cyl(f"{tag} thigh {lx} {ly}", 0.07, 0.45, T, n=10, parent=hip, loc=(0, 0, -0.45), r2=0.11)
        kn = empty(f"{tag} knee {lx} {ly}", (0, 0, -0.45), hip)
        cyl(f"{tag} shin {lx} {ly}", 0.045, 0.4, T, n=10, parent=kn, loc=(0, 0, -0.4), r2=0.065)
        cyl(f"{tag} hoof {lx} {ly}", 0.075, 0.07, RM, n=10, parent=kn, loc=(0, 0, -0.45))
        legs.append((hip, kn, ph, ly > 0)); hooves.append((lx, ly))
    rider(f"{tag} rider", b, (0, -0.05, 0.38))
    def pos(u, f):
        y = 32 * u
        z = 7.5 * smooth((u - 0.06) / 0.3) - 3.5 * math.sin(math.pi * min(1.0, max(0.0, (u - 0.42) / 0.36)))
        x = bx + 4.0 * math.sin(2 * math.pi * max(0.0, u - 0.36) / 0.64)
        return (x, y, z)
    def extra(u, f):
        rear = R(32) * math.sin(math.pi * min(1.0, max(0.0, (f - FORM - 1) / 12)))     # rears up, then launches
        return rear, 0.0
    fly(root, pos, bank_k=6.0, pitch_k=0.8, extra=extra)
    for f in range(1, FRAME_END + 1):
        rear = min(1.0, max(0.0, (f - FORM) / 4)) * (1 - min(1.0, max(0.0, (f - FORM - 10) / 4)))
        st = smooth((f - FORM - 8) / 6)
        for hip, kn, ph, front in legs:
            if front:
                h = 80 * rear * (1 - st) + 70 * st + 6 * math.sin(f * 0.4 + ph * 6) * st
                k = -100 * rear * (1 - st) - 10 * st
            else:
                h = -10 * rear * (1 - st) - 65 * st + 6 * math.sin(f * 0.4 + ph * 6) * st
                k = 15 * st
            key(hip, f, rot=(R(h), 0, 0)); key(kn, f, rot=(R(k), 0, 0))
        key(tl, f, rot=(R(-12 + 8 * math.sin(f * 0.3)), 0, R(10 * math.sin(f * 0.2))))
        for k, mn in enumerate(crest):
            key(mn, f, rot=(R(-10 * st + 8 * math.sin(f * 0.5 - k * 0.6)), 0, 0))
    # streamers: little light flakes left behind by each hoof, fading over 8 ticks
    bpy.context.view_layer.update()
    pm = pixel_mesh(W, 0.05)
    for f in range(FORM + 14, FRAME_END - 1, 2):
        scene.frame_set(f)
        for (lx, ly), (hip, kn, ph, front) in zip(hooves, legs):
            hp = (kn.matrix_world @ Vector((0, 0, -0.45)))
            px = link(bpy.data.objects.new(f"{tag} streamer", pm))
            key(px, 1, loc=hp, sc=0.0001); key(px, f - 1, loc=hp, sc=0.0001); key(px, f, loc=hp, sc=1.0)
            key(px, f + 8, loc=hp + Vector((0, 0, -0.15)), sc=0.0001)
    scene.frame_set(1)
    return 1, 60


# ================================================================== F2: the baby dragon
def build_F2a(tag, root, bx):
    """Round wyrmling, BR1: ball body and head, bat wings stretched on three finger bones; hovers straight up with heavy
    flaps (it can take off on the spot), then flies off weaving."""
    T = TEX["br1"]
    b = empty(f"{tag} body", (0, 0, 0.85), root)
    bd = ball(f"{tag} belly", 0.48, T, parent=b, seg=20); bd.scale = (1.0, 1.15, 0.92)
    ball(f"{tag} belly glow", 0.3, RM, loc=(0, 0.15, -0.28), parent=b, seg=12).scale = (1.0, 1.2, 0.45)
    nk = empty(f"{tag} neck", (0, 0.45, 0.25), b)
    hd = empty(f"{tag} head", (0, 0.25, 0.18), nk)
    ball(f"{tag} head ball", 0.34, T, parent=hd, seg=18)
    sn = ball(f"{tag} snout", 0.2, T, loc=(0, 0.32, -0.08), parent=hd, seg=14); sn.scale = (0.9, 1.1, 0.7)
    for s in (-1, 1):
        ball(f"{tag} eye {s}", 0.07, RM, loc=(s * 0.2, 0.22, 0.08), parent=hd, seg=10)
        cyl(f"{tag} horn {s}", 0.06, 0.24, RM, n=8, parent=hd, loc=(s * 0.14, -0.1, 0.22), r2=0.0).rotation_euler = (R(-35), R(s * 15), 0)
    tail = []; prev = b; pos_ = (0, -0.5, -0.05)
    for i in range(5):
        s_ = empty(f"{tag} tail {i}", pos_, prev)
        ball(f"{tag} tail bead {i}", 0.15 - 0.022 * i, T, parent=s_, seg=10); tail.append(s_); prev = s_; pos_ = (0, -0.2, 0)
    cyl(f"{tag} tail spade", 0.1, 0.18, RM, n=4, parent=prev, loc=(0, -0.05, 0), axis="Y", r2=0.0).rotation_euler = (0, 0, R(180))
    wings = []
    for s in (-1, 1):
        wr = empty(f"{tag} wing {s}", (s * 0.4, 0.1, 0.3), b)
        bar(f"{tag} wing arm {s}", (0, 0, 0), (s * 0.45, 0.05, 0.12), 0.035, RM, wr)
        hand = Vector((s * 0.45, 0.05, 0.12))
        tips = [hand + Vector((s * 0.7, 0.05, 0.1)), hand + Vector((s * 0.6, -0.4, 0.0)), hand + Vector((s * 0.3, -0.62, -0.05))]
        for k, t in enumerate(tips):
            bar(f"{tag} finger {s} {k}", tuple(hand), tuple(t), 0.022, RM, wr)
        pts = [Vector((0, 0, 0)), hand, tips[0], tips[1], tips[2], Vector((0, -0.42, 0))]
        for k in range(len(pts) - 2):
            slab(f"{tag} membrane {s} {k}", [tuple(pts[0] if k == 0 else hand), tuple(pts[k + 1] if k == 0 else pts[k + 1]), tuple(pts[k + 2])], 0.02, T, wr)
        slab(f"{tag} membrane {s} back", [(0, 0, 0), tuple(tips[2]), (0, -0.42, 0)], 0.02, T, wr)
        wings.append((wr, s))
    for s in (-1, 1):
        for y in (0.25, -0.25):
            lg = empty(f"{tag} leg {s} {y}", (s * 0.3, y, -0.35), b)
            cyl(f"{tag} leg {s} {y} stub", 0.09, 0.25, T, n=8, parent=lg, loc=(0, 0, -0.25))
            key(lg, FORM + 4, rot=(0, 0, 0)); key(lg, FORM + 12, rot=(R(-55), 0, 0))
    rider(f"{tag} rider", b, (0, -0.1, 0.42), legs_down=True)
    def pos(u, f):
        z = 5.0 * smooth(u / 0.33)
        g = max(0.0, (u - 0.3) / 0.7)
        return (bx + 2.5 * math.sin(2 * math.pi * g * 1.3) * g, 26 * g ** 1.2, z + 1.5 * g)
    def extra(u, f):
        hover = 1.0 - smooth((u - 0.25) / 0.12)
        return R(-6) * hover + R(4) * math.sin(f * 2 * math.pi / 10), 0.0
    fly(root, pos, bank_k=4.0, pitch_k=0.5, extra=extra)
    for f in range(1, FRAME_END + 1):
        fl = min(1.0, max(0.0, (f - FORM + 2) / 4))
        a = 2 * math.pi * f / 10                                    # heavy, slower flaps
        for wr, s in wings:
            key(wr, f, rot=(R(-12 * math.cos(a) * fl), R(-s * (8 + 62 * math.sin(a) * fl)), R(s * 10 * fl)))
        for i, s_ in enumerate(tail):
            key(s_, f, rot=(R(-8 + 6 * math.sin(a - i * 0.7)), 0, R(16 * math.sin(f * 0.18 - i * 0.6))))
        key(b, f, loc=(0, 0, 0.85 + 0.1 * math.sin(a - 1.0) * fl))
        key(nk, f, rot=(R(5 * math.sin(a - 0.5)), 0, 0))
    return 1, 70


def build_F2b(tag, root, bx):
    """Serpent hatchling, R2 K1: a long nine-link body that swims through the air in an S-wave; small fast wings on
    the shoulders; a frill head."""
    T = TEX["r2k1"]
    b = empty(f"{tag} body", (0, 0, 0.8), root)
    links = []; prev = b; p_ = (0, 0.9, 0)
    for i in range(9):                                         # link 0 at the front; the chain runs back (-Y)
        s_ = empty(f"{tag} link {i}", p_, prev)
        w_ = 0.26 if i < 3 else 0.26 - 0.022 * (i - 2)
        seg = ball(f"{tag} link body {i}", w_, T, parent=s_, loc=(0, -0.17, 0), seg=14); seg.scale = (1.0, 1.35, 0.9)
        box(f"{tag} link ridge {i}", (-0.03, -0.26, w_ * 0.82), (0.03, -0.06, w_ * 0.82 + 0.08), DARK_RIM, s_)
        links.append(s_); prev = s_; p_ = (0, -0.36, 0)
    hd = empty(f"{tag} head", (0, 0.05, 0.05), links[0])
    h_ = ball(f"{tag} skull", 0.27, T, loc=(0, 0.18, 0), parent=hd, seg=16); h_.scale = (0.9, 1.4, 0.8)
    for s in (-1, 1):
        ball(f"{tag} eye {s}", 0.05, DARK_RIM, loc=(s * 0.18, 0.3, 0.08), parent=hd, seg=8)
        slab(f"{tag} frill {s}", [(s * 0.15, 0.0, 0.1), (s * 0.45, -0.15, 0.25), (s * 0.4, -0.25, -0.05), (s * 0.15, -0.05, -0.05)], 0.02, DARK_RIM, hd)
    cyl(f"{tag} tail fin", 0.14, 0.3, DARK_RIM, n=4, parent=links[-1], loc=(0, -0.3, 0), axis="Y", r2=0.0).rotation_euler = (0, 0, R(180))
    wings = []
    for s in (-1, 1):
        wr = empty(f"{tag} wing {s}", (s * 0.22, -0.15, 0.12), links[1])
        slab(f"{tag} wing {s} blade", [(0, 0.05, 0), (s * 0.6, 0.0, 0.1), (s * 0.75, -0.2, 0.05), (s * 0.3, -0.3, 0), (0, -0.2, 0)], 0.02, T, wr)
        bar(f"{tag} wing {s} bone", (0, 0.05, 0), (s * 0.75, -0.2, 0.05), 0.02, DARK_RIM, wr)
        wings.append((wr, s))
    rider(f"{tag} rider", links[2], (0, -0.17, 0.22), legs_down=True)
    def pos(u, f):
        return (bx + 1.2 * math.sin(2 * math.pi * u * 1.2), 30 * u, 6.5 * smooth((u - 0.02) / 0.6))
    fly(root, pos, bank_k=3.0, pitch_k=0.6)
    for f in range(1, FRAME_END + 1):
        sw = min(1.0, max(0.0, (f - FORM + 4) / 8))
        for i, s_ in enumerate(links):
            if i == 0:
                continue
            key(s_, f, rot=(R(5 * math.sin(f * 0.25 - i * 0.6) * sw), 0, R(11 * math.sin(2 * math.pi * f / 18 - i * 1.1) * sw)))
        key(hd, f, rot=(0, 0, R(-14 * math.sin(2 * math.pi * f / 18) * sw)))
        a = 2 * math.pi * f / 5                                     # small fast wings
        for wr, s in wings:
            key(wr, f, rot=(0, R(-s * (10 + 40 * math.sin(a) * sw)), 0))
    return 1, 75


def build_F2c(tag, root, bx):
    """Blocky glider, H1: chunky voxel boxes, wide four-finger wings made of stepped boxes; a leap, two big
    downstrokes, then a long banked glide."""
    T = TEX["h1"]
    b = empty(f"{tag} body", (0, 0, 0.9), root)
    box(f"{tag} chest", (-0.38, -0.1, -0.32), (0.38, 0.5, 0.36), T, b)
    box(f"{tag} hips", (-0.32, -0.55, -0.28), (0.32, -0.1, 0.3), T, b)
    for k in range(4):
        box(f"{tag} back spike {k}", (-0.04, 0.35 - 0.25 * k, 0.36), (0.04, 0.45 - 0.25 * k, 0.5 - 0.02 * k), RM, b)
    nk = empty(f"{tag} neck", (0, 0.5, 0.15), b)
    box(f"{tag} neck box", (-0.17, 0.0, -0.15), (0.17, 0.25, 0.2), T, nk)
    hd = empty(f"{tag} head", (0, 0.25, 0.05), nk)
    box(f"{tag} skull", (-0.26, -0.05, -0.2), (0.26, 0.38, 0.24), T, hd)
    box(f"{tag} snout", (-0.16, 0.38, -0.16), (0.16, 0.64, 0.06), T, hd)
    box(f"{tag} brow", (-0.28, 0.2, 0.18), (0.28, 0.4, 0.26), T, hd)
    for s in (-1, 1):
        box(f"{tag} eye {s}", (s * 0.26 - 0.01, 0.2, 0.04), (s * 0.26 + 0.01, 0.32, 0.12), RM, hd)
        box(f"{tag} horn {s}", (s * 0.18 - 0.04, -0.15, 0.2), (s * 0.18 + 0.04, -0.02, 0.42), RM, hd)
    tail = []; prev = b; p_ = (0, -0.55, 0.0)
    for i in range(5):
        s_ = empty(f"{tag} tail {i}", p_, prev); w_ = 0.16 - i * 0.025
        box(f"{tag} tail box {i}", (-w_, -0.26, -w_), (w_, 0, w_), T, s_); tail.append(s_); prev = s_; p_ = (0, -0.26, 0)
    wings = []
    for s in (-1, 1):
        wr = empty(f"{tag} wing {s}", (s * 0.38, 0.3, 0.25), b)
        box(f"{tag} wing arm {s}", (0, -0.04, -0.04), (s * 0.55, 0.04, 0.04), RM, wr)
        wt = empty(f"{tag} wing hand {s}", (s * 0.55, 0, 0), wr)
        box(f"{tag} wing hand bone {s}", (0, -0.04, -0.04), (s * 0.5, 0.04, 0.04), RM, wt)
        for k in range(4):                     # stepped panels: each finger a box strip going back
            x0, x1 = 0.25 * k, 0.25 * (k + 1)
            ln = 0.95 - 0.12 * abs(k - 1.2)
            par = wr if k < 2 else wt
            off = 0 if k < 2 else 0.5
            box(f"{tag} wing panel {s} {k}", (s * (x0 - off), -ln, -0.015), (s * (x1 - off), 0.0, 0.015), T, par)
            box(f"{tag} wing finger {s} {k}", (s * (x1 - off) - 0.025, -ln, -0.025), (s * (x1 - off) + 0.025, 0, 0.025), RM, par)
        wings.append((wr, wt, s))
    for s in (-1, 1):
        for y in (0.25, -0.35):
            lg = empty(f"{tag} leg {s} {y}", (s * 0.28, y, -0.3), b)
            box(f"{tag} leg box {s} {y}", (-0.09, -0.09, -0.3), (0.09, 0.1, 0.0), T, lg)
            key(lg, FORM + 4, rot=(0, 0, 0)); key(lg, FORM + 10, rot=(R(-70), 0, 0))
    rider(f"{tag} rider", b, (0, 0.05, 0.4), legs_down=True)
    def pos(u, f):
        f_ = f
        z = 1.6 * smooth((f_ - FORM - 2) / 5) + 4.8 * smooth((f_ - FORM - 6) / 22) - 1.8 * smooth((f_ - 60) / 60)
        g = max(0.0, (u - 0.35) / 0.65)
        return (bx - 5.0 * (1 - math.cos(math.pi * g)) / 2 * 1.4, 30 * u, z)
    fly(root, pos, bank_k=9.0, pitch_k=0.5)
    for f in range(1, FRAME_END + 1):
        fl = min(1.0, max(0.0, (f - FORM) / 4))
        flapping = FORM + 4 <= f <= FORM + 26
        a = 2 * math.pi * (f - FORM - 4) / 11
        for wr, wt, s in wings:
            if flapping:
                up = 60 * math.cos(a); tip = -25 * math.sin(a)
            else:
                up = 4 * fl + 2 * math.sin(f * 0.2); tip = -3
            key(wr, f, rot=(0, R(-s * up), R(s * 30 * (1 - fl))))
            key(wt, f, rot=(0, R(-s * tip), 0))
        for i, s_ in enumerate(tail):
            key(s_, f, rot=(R(-4 + 4 * math.sin(f * 0.15 - i * 0.6)), 0, R(8 * math.sin(f * 0.12 - i * 0.7))))
        key(nk, f, rot=(R(-6 * fl), 0, 0))
    return 1, 82


# ================================================================== F3: the ghast, real size
G = 4.5 / 16                     # the real ghast renders its 16-px model at 4.5x: one model pixel = 0.28125 m
BS = 16 * G                      # 4.5 m body cube
TENT_LEN = [8, 13, 9, 11, 11, 10, 12, 9, 12]       # vanilla GhastModel: new Random(1660L), nextInt(7) + 8 per tentacle
BODY_Z = 4.2                    # body bottom height above the mount root


def real_ghast(tag, root):
    """The real ghast (the mob underneath, shown faintly): body cube and nine 2 x L x 2 px tentacles, laid out and
    swung exactly as vanilla GhastModel (x = (i%3 - (i/3%2)/2 + 0.25 - 1) * 5 px, z = (i/3 - 1) * 5 px, pivot 1 px
    up inside the body; xRot = 0.2 sin(0.3 t + i) + 0.4). Returns (body, [(pivot, length m, i)])."""
    b = empty(f"{tag} body", (0, 0, BODY_Z), root)
    box(f"{tag} real ghast body", (-BS / 2, -BS / 2, 0), (BS / 2, BS / 2, BS), REAL, b)
    fy = BS / 2
    for s in (-1, 1):                                # the real face (front, +Y)
        box(f"{tag} real ghast eye {s}", (s * 3 * G - G, fy, 8 * G), (s * 3 * G + G, fy + 0.02, 10 * G), REAL_DARK, b)
    box(f"{tag} real ghast mouth", (-2 * G, fy, 4 * G), (2 * G, fy + 0.02, 5 * G), REAL_DARK, b)
    tents = []
    for i in range(9):
        mx = ((i % 3 - (i // 3 % 2) * 0.5 + 0.25) - 1.0) * 5.0
        mz = (i // 3 - 1.0) * 5.0
        piv = empty(f"{tag} tentacle {i}", (mx * G, -mz * G, 1 * G), b)        # model -Z is the face: Blender +Y
        L = TENT_LEN[i] * G
        box(f"{tag} real ghast tentacle {i}", (-G, -G, -L), (G, G, 0), REAL, piv)
        tents.append((piv, L, i))
    for f in range(1, FRAME_END + 1):
        for piv, L, i in tents:
            key(piv, f, rot=(-(0.2 * math.sin(0.3 * f + i) + 0.4), 0, 0))
    return b, tents


def ghast_face(tag, b, fy, m_eye, m_mouth):
    for s in (-1, 1):
        box(f"{tag} eye {s}", (s * 3 * G - 1.3 * G, fy, 7.6 * G), (s * 3 * G + 1.3 * G, fy + 0.05, 10.4 * G), m_eye, b)
    box(f"{tag} mouth", (-2.4 * G, fy, 3.6 * G), (2.4 * G, fy + 0.05, 5.4 * G), m_mouth, b)


def build_F3a(tag, root, bx):
    """Snug shell, R2 K1: one bevelled shell 0.06-0.16 off the real ghast's skin (rounded corners clear the real
    cube's corners), each tentacle in a round sleeve on its own pivot; rises and drifts in a slow turn."""
    T = TEX["r2k1"]
    b, tents = real_ghast(tag, root)
    sh = 0.16
    shell = box(f"{tag} shell", (-BS / 2 - sh, -BS / 2 - sh, -sh), (BS / 2 + sh, BS / 2 + sh, BS + sh), T, b, uvt=1.0)
    bevel(shell, 0.22, 3)
    ghast_face(tag, b, BS / 2 + sh, DARK_RIM, DARK_RIM)
    for piv, L, i in tents:
        cyl(f"{tag} sleeve {i}", 0.46, L - 0.06 + G - sh * 0.5, T, n=12, parent=piv, loc=(0, 0, -L - 0.06))
        ball(f"{tag} sleeve tip {i}", 0.2, DARK_RIM, loc=(0, 0, -L - 0.06), parent=piv, seg=8).scale = (1, 1, 0.5)
    rider(f"{tag} rider", b, (0, 0.4, BS + sh))
    def pos(u, f):
        ang = R(35) * smooth((u - 0.3) / 0.7)
        d = 13 * u
        return (bx - d * math.sin(ang) * 0.5, d, 4.0 * smooth((u - 0.03) / 0.6) + 0.12 * math.sin(f * 0.12))
    fly(root, pos, pitch_k=0.0, bank_k=2.0)
    return 2, 80


def build_F3b(tag, root, bx):
    """Lattice cage, W1: a window cage of bars 0.1 off the real ghast (each face a 3 x 3 grid of panes, the real ghast
    seen through), each tentacle in a stack of hoops; swims forward in pulses, a squeeze of the cage on each push."""
    T = TEX["w1"]
    b, tents = real_ghast(tag, root)
    cage = empty(f"{tag} cage", (0, 0, BS / 2), b)
    h = BS / 2 + 0.12; t = 0.07
    for ax in range(3):                         # bars on all faces: 4 lines per direction per face pair
        for k in range(4):
            c = -h + 2 * h * k / 3
            for s in (-1, 1):
                for d in range(3):
                    if d == ax:
                        continue
                    o_ = [0, 0, 0]; o_[ax] = s * h
                    other = [i for i in range(3) if i not in (ax, d)][0]
                    a = [0.0] * 3; bb = [0.0] * 3
                    a[ax] = s * h - t; bb[ax] = s * h + t
                    a[other] = c - t; bb[other] = c + t
                    a[d] = -h - t; bb[d] = h + t
                    box(f"{tag} bar {ax}{k}{s}{d}", tuple(a), tuple(bb), T if k in (1, 2) else RM, cage)
    for s in (-1, 1):                            # pane glass, very faint, so the cage reads as windows
        box(f"{tag} pane front {s}", (-h, s * h - 0.01, -h), (h, s * h + 0.01, h), GL, cage)
    ghast_face(tag, b, BS / 2 + 0.2, W, RM)
    for piv, L, i in tents:
        n = max(3, int(L / 0.42))
        for k in range(n):
            z = -0.35 - (L - 0.35) * k / max(1, n - 1)
            torus(f"{tag} hoop {i} {k}", 0.42, 0.05, T if k % 2 else RM, loc=(0, 0, z), parent=piv, n=14, k=5)
        bar(f"{tag} hoop rod {i}", (0.42, 0, -0.35), (0.42, 0, -L), 0.03, RM, piv)
    rider(f"{tag} rider", b, (0, 0.4, BS + 0.19))
    pulses = [FORM + 6 + 20 * k for k in range(5)]
    def ypos(f):
        return sum(3.0 * smooth((f - p0) / 9) for p0 in pulses)
    def pos(u, f):
        return (bx, ypos(f), 3.5 * smooth((u - 0.03) / 0.5) + 0.1 * math.sin(f * 0.15))
    def extra(u, f):
        return sum(R(5) * math.sin(math.pi * min(1.0, max(0.0, (f - p0) / 9))) for p0 in pulses), 0.0
    fly(root, pos, pitch_k=0.0, extra=extra)
    for f in range(1, FRAME_END + 1):
        sq = sum(math.sin(math.pi * min(1.0, max(0.0, (f - p0) / 9))) for p0 in pulses)
        key(cage, f, sc=(1 - 0.03 * sq, 1 + 0.02 * sq, 1 - 0.03 * sq))
    return 2, 70


def build_F3c(tag, root, bx):
    """Brick strata, BR1: five stacked slabs 0.12 off the skin that breathe apart (gaps open to 0.06), a glow line on
    every edge of every slab, a protruding brow over the eyes, tentacles in segmented square sleeves; rises high and
    banks round a wide turn."""
    T = TEX["br1"]
    b, tents = real_ghast(tag, root)
    sh = 0.12; n = 5; hs = (BS + 2 * sh) / n; e = 0.035
    slabs = []
    for k in range(n):
        z0 = -sh + hs * k
        sl = empty(f"{tag} slab {k}", (0, 0, z0 + hs / 2), b)
        a = (-BS / 2 - sh, -BS / 2 - sh, -hs / 2 + 0.02); c = (BS / 2 + sh, BS / 2 + sh, hs / 2 - 0.02)
        box(f"{tag} slab body {k}", a, c, T, sl, uvt=1.0)
        xs, ys, zs = (a[0], c[0]), (a[1], c[1]), (a[2], c[2])
        for x in xs:                                   # all 12 edges glow, so no single line looks stray
            for y in ys:
                box(f"{tag} edge {k} z {x:.1f} {y:.1f}", (x - e, y - e, zs[0]), (x + e, y + e, zs[1]), RM, sl)
            for z in zs:
                box(f"{tag} edge {k} y {x:.1f} {z:.1f}", (x - e, ys[0], z - e), (x + e, ys[1], z + e), RM, sl)
        for y in ys:
            for z in zs:
                box(f"{tag} edge {k} x {y:.1f} {z:.1f}", (xs[0], y - e, z - e), (xs[1], y + e, z + e), RM, sl)
        slabs.append((sl, z0 + hs / 2, k))
    fy = BS / 2 + sh
    brow = empty(f"{tag} brow", (0, fy, 10.9 * G), b)
    box(f"{tag} brow ledge", (-BS / 2 + 0.2, 0, -0.1), (BS / 2 - 0.2, 0.45, 0.14), T, brow)
    box(f"{tag} brow glow", (-BS / 2 + 0.2, 0.43, -0.12), (BS / 2 - 0.2, 0.47, 0.0), RM, brow)
    ghast_face(tag, b, fy + 0.04, W, RM)
    for piv, L, i in tents:
        m_ = max(2, int(L / 0.6))
        for k in range(m_):
            z1 = -sh - (L - sh + 0.06) * k / m_; z2 = -sh - (L - sh + 0.06) * (k + 1) / m_ + 0.06
            box(f"{tag} sleeve {i} {k}", (-G - 0.1, -G - 0.1, z2), (G + 0.1, G + 0.1, z1), T if k % 2 == 0 else GL, piv)
    rider(f"{tag} rider", b, (0, 0.4, BS + sh + 2 * 0.06))
    def pos(u, f):
        th = R(110) * smooth((u - 0.25) / 0.75)
        rr = 10.0
        d = 6 * min(u, 0.25) / 0.25
        return (bx - rr * (1 - math.cos(th)), d + rr * math.sin(th), 7.0 * smooth((u - 0.02) / 0.65) + 0.1 * math.sin(f * 0.1))
    fly(root, pos, pitch_k=0.0, bank_k=4.0)
    for f in range(1, FRAME_END + 1):
        br = 0.5 + 0.5 * math.sin(2 * math.pi * f / 40)
        for sl, zc, k in slabs:
            key(sl, f, loc=(0, 0, zc + (k - 2) * 0.03 * br))
        key(brow, f, loc=(0, fy, 10.9 * G + 0.03 * br))
    return 2, 85


# ================================================================== layout: three rows, far apart in X
TAKES = [("F1a", "winged horse, R2 K1", build_F1a, 0.0), ("F1b", "hoop horse on a light road, W1", build_F1b, 18.0),
         ("F1c", "comet horse, H1", build_F1c, 36.0),
         ("F2a", "round wyrmling, BR1", build_F2a, 70.0), ("F2b", "serpent hatchling, R2 K1", build_F2b, 88.0),
         ("F2c", "blocky glider, H1", build_F2c, 106.0),
         ("F3a", "ghast snug shell, R2 K1", build_F3a, 145.0), ("F3b", "ghast lattice cage, W1", build_F3b, 175.0),
         ("F3c", "ghast brick strata, BR1", build_F3c, 205.0)]
MODEL_AT = {}
for tk, name, fn, bx in TAKES:
    tag = f"FM2 {tk}"
    big = tk.startswith("F3")
    box(f"{tag} floor", (bx - (12 if big else 7), -6, -0.02), (bx + (12 if big else 7), 40, 0), FLOOR)
    root = empty(f"{tag} mount", (bx, 0, 0))
    kind, mf = fn(tag, root, bx)
    MODEL_AT[tk] = mf
    parts = meshes(root)
    form_in(parts, 2, FORM, (bx, 0.0, 2.0), CM["pix"], rng, tag, order_axis=2 if big else 1, stream=0.2)
    if big:
        follow_cam(tk, root, back=17.0, up=9.0, side=7.0, look_up=4.5)
        cam(f"Cam {tk} side", (bx + 26, 12, 10.0), (bx, 10, 6.0), 30)
    else:
        follow_cam(tk, root, back=8.0, up=3.0, side=2.6, look_up=1.2)
        cam(f"Cam {tk} side", (bx + 15, 14, 6.0), (bx, 14, 4.0), 30)
    label(f"{tk}  {name}", (bx, -3.0, 9.5 if big else 3.4), LBL, 0.6 if big else 0.32, rot=(R(90), 0, 0))
    print(tk, "built", flush=True)
cam("Cam row F1", (18.0, -24.0, 8.0), (18.0, 8, 2.0), 30)
cam("Cam row F2", (88.0, -24.0, 8.0), (88.0, 8, 2.5), 30)
cam("Cam row F3", (175.0, -48.0, 16.0), (175.0, 6, 5.0), 30)
print("MODEL_AT", json.dumps(MODEL_AT))
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam F1a", 1, (0.35, 0.45, 0.6), 3.0


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
