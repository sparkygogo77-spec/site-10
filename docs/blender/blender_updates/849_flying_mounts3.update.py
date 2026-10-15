# Pass 849: flying mounts, round 3 variations (2026-10-15). From 841 (Flying mounts: F1-F3 variations): J rated F1a,
# F1c, F2c, F3a, F3b, F3c IMPROVE with no note ("3 new variations each", labelled, he picks). Dropped: F1b, F2a, F2b.
# J on 809: "horse is the only flying construct i want right now, maybe well force the lantern user to learn to ride a
# flying creature, give me a flying baby dragon to ride on and also a ghast construct (it needs to fit the real model
# instead of colliding with it, but since ours is pure construct you can make a new textured ghast instead".
# Each new take keeps what made its parent (texture and construction idea) and is built and flies a different way.
# R2 K1 from docs/texture_library/green/r2k1/construct_r2k1_green.png; H1, W1, BR1 from the library too.
#   F1a1 winged horse, R2 K1: fan wings (nine slats fan open on one hub); crouch and spring take-off, a climbing circle
#   F1a2 winged horse, R2 K1: four wings (fore and hind pairs, out of phase, fast); keeps galloping, runs up the air in
#        three surges
#   F1a3 winged horse, R2 K1: Z-fold three-joint wings with three feather tiers; long run, one huge stroke, soars an S
#   F1c1 comet horse, H1: lathe body running into a ringed comet tail, hind legs fold into it; climbs, a barrel roll,
#        flakes stream from the tail tip
#   F1c2 comet horse, H1: body of eleven separate lathe slices with gaps; helix climb 1.5 turns to 10; light ribbons
#        from the hooves
#   F1c3 comet horse, H1: one-piece hull with a pointed rear, neck fins; three bounding leaps with hex shock rings, then
#        a dive and climb out; hex-plate flakes
#   F2c1 blocky glider, H1: wings of a 6 x 3 grid of loose cubes on six span joints (the flap runs out as a wave);
#        runs on all fours, launches, circles up a thermal
#   F2c2 blocky glider, H1: folding-screen wings (five hinged panels, zigzag-packed, snap flat); a construct pillar
#        lifts it, it dives off, pulls up into a glide; the pillar breaks
#   F2c3 blocky glider, H1: stepped pixel-art delta wings and a tail fin; hovers up on quick beats, darts, steep wingover
#   F3a1 ghast shell, R2 K1: one smooth rounded-cube shell (superellipsoid), cone sleeves; breathes, rises 3, glides out
#   F3a2 ghast shell, R2 K1: thin inner shell plus five barrel bands, banded sleeves; lifts to 6, turns in two 30-degree
#        steps
#   F3a3 ghast shell, R2 K1: chamfered gem-cut shell, quarter-twisted square sleeves, a rider rail; strafes sideways
#        while rising, swings round, climbs away
#   F3b1 ghast cage, W1: round rods with glowing balls at every crossing, coil-spring tentacles; three lift pulses, then
#        a slow turn
#   F3b2 ghast cage, W1: diamond lattice in a 12-edge glowing frame, square-frame tentacle stacks; five pulses that
#        zigzag
#   F3b3 ghast cage, W1: fine cage plus a turning gimbal ring with beads, lantern-tube tentacles; climbing corkscrew
#   F3c1 ghast strata, BR1: five slices front to back (not stacked), 12 glowing edges each; straight ramp climb
#   F3c2 ghast strata, BR1: three thick slabs that breathe by twisting; rises, turns right round, heads back
#   F3c3 ghast strata, BR1: four tiers widening downward (upside-down ziggurat), brick-ring sleeves; rises 7 through a
#        banked S
# Every construct tentacle rides the vanilla tentacle swing on its own pivot, so nothing cuts the real model. Cameras
# "Cam <take>" (follows, level horizon), "Cam <take> side", "Cam row F1a/F1c/F2c/F3a/F3b/F3c". Builds
# LanternLive\constructs\flying_mounts3.blend.
SCENE_NAME = "Flying Mounts 3"
OUT_REL = "constructs/flying_mounts3.blend"
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
FLOOR = mat("FM3 floor", (0.18, 0.21, 0.2), rough=0.9)
LBL = mat("FM3 label", (0.3, 1.0, 0.45), emit=2.0)
REAL = mat("FM3 real ghast (reference)", (0.62, 0.62, 0.6), alpha=0.45, rough=0.7)
REAL_DARK = mat("FM3 real ghast face", (0.08, 0.08, 0.09), alpha=0.6)
rng = np.random.default_rng(849)
CM = cmats("FM3", "green")
RM, W, GR, GL = CM["rim"], CM["glow"], CM["grip"], CM["glass"]
DARK_RIM = mat("FM3 dark jade rim", (0.03, 0.42, 0.16), emit=2.2)     # darker glow line for the dark-jade takes


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
TEX = {k: strip_mat(f"FM3 {k} texture", strip_image("green", k), 4, emit=1.3, alpha=0.9) for k in ("br1", "w1", "h1")}
TEX["r2k1"] = strip_mat("FM3 r2k1 dark jade texture", r2k1_image(), 4, emit=1.2, alpha=0.5, over=K1_BASE)


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


# ------------------------------------------------------------------ extra builders for this round
def fly2(root, pos, f0=FORM + 2, f1=FRAME_END, bank_k=0.0, pitch_k=1.0, extra=None, yaw_fn=None, max_pitch=35, max_roll=50):
    """fly() for this round: the heading is unwrapped (no spin when a circle crosses south), pitch and bank are clamped
    so a mount never stands on its tail or rolls over, and yaw_fn(u, f) -> radians can set the heading directly
    (strafing, turning on the spot)."""
    def at(f):
        return Vector(pos(max(0.0, (f - f0) / (f1 - f0)), f))
    def heading(f, prev):
        d = at(f + 1) - at(f - 1)
        if math.hypot(d.x, d.y) < 1e-3:
            return prev
        y_ = math.atan2(-d.x, d.y)
        while y_ - prev > math.pi:
            y_ -= 2 * math.pi
        while y_ - prev < -math.pi:
            y_ += 2 * math.pi
        return y_
    if " F3" in root.name:                      # a real-size ghast never banks hard
        max_roll = min(max_roll, 15)
    yaw = 0.0
    for f in range(1, f1 + 1, 2):
        u = max(0.0, (f - f0) / (f1 - f0))
        d = at(f + 1) - at(f - 1); h = math.hypot(d.x, d.y)
        if yaw_fn is None:
            yaw = heading(f, yaw); yaw2 = heading(f + 2, yaw)
            pitch = math.atan2(d.z, h) * pitch_k if h > 1e-3 else 0.0
        else:
            yaw = yaw_fn(u, f); yaw2 = yaw_fn(min(1.0, u + 2 / (f1 - f0)), f + 2); pitch = 0.0
        roll = -(yaw2 - yaw) * bank_k
        pitch = max(-R(max_pitch), min(R(max_pitch), pitch)); roll = max(-R(max_roll), min(R(max_roll), roll))
        if extra is not None:
            ep, er = extra(u, f); pitch += ep; roll += er
        key(root, f, loc=tuple(at(f)), rot=(pitch, roll, yaw))


fly = fly2                                      # every take in this round flies with the unwrapped, clamped version


def ramp(f, a, b):
    return min(1.0, max(0.0, (f - a) / max(1e-6, b - a)))


def lathe(name, prof, m, parent=None, n=18, loc=(0, 0, 0), uvt=0.5):
    """Revolve a profile [(radius, y)] about the local Y axis: one smooth piece."""
    vs, fs = [], []
    for r, y in prof:
        for j in range(n):
            a = 2 * math.pi * j / n
            vs.append((max(r, 1e-4) * math.cos(a), y, max(r, 1e-4) * math.sin(a)))
    for i in range(len(prof) - 1):
        for j in range(n):
            a = i * n + j; b_ = i * n + (j + 1) % n
            fs.append((a, b_, b_ + n, a + n))
    o = mesh(name, vs, fs, m, parent, smooth_=True, uvt=uvt); o.location = loc
    return o


def super_shell(name, a, p, m, parent=None, centre=(0, 0, 0), seg=28):
    """A rounded-cube shell: |x/a|^p + |y/a|^p + |z/a|^p = 1, one piece, smooth."""
    vs, fs = [], []
    for i in range(seg // 2 + 1):
        th = math.pi * i / (seg // 2)
        for j in range(seg):
            ph = 2 * math.pi * j / seg
            u = np.array((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
            r = np.sum(np.abs(u) ** p) ** (-1 / p)
            vs.append(tuple(np.array(centre) + a * u * r))
    for i in range(seg // 2):
        for j in range(seg):
            q = i * seg + j; q2 = i * seg + (j + 1) % seg
            fs.append((q, q2, q2 + seg, q + seg))
    return mesh(name, vs, fs, m, parent, smooth_=True, uvt=1.0)


def helix_tube(name, rad, turns, z0, z1, tr, m, parent=None, steps=12, n=6):
    """A coil spring from z0 down to z1 (local), coil radius rad, tube radius tr: one mesh."""
    path = []
    tot = max(8, int(turns * steps))
    for k in range(tot + 1):
        t = k / tot; a = 2 * math.pi * turns * t
        path.append(Vector((rad * math.cos(a), rad * math.sin(a), z0 + (z1 - z0) * t)))
    vs, fs = [], []
    for k, c in enumerate(path):
        d = (path[min(k + 1, tot)] - path[max(k - 1, 0)]).normalized()
        u = d.cross(Vector((0, 0, 1))).normalized(); w = d.cross(u)
        for j in range(n):
            a = 2 * math.pi * j / n
            vs.append(tuple(c + (u * math.cos(a) + w * math.sin(a)) * tr))
    for k in range(tot):
        for j in range(n):
            q = k * n + j; q2 = k * n + (j + 1) % n
            fs.append((q, q2, q2 + n, q + n))
    return mesh(name, vs, fs, m, parent, smooth_=True)


def square_ring(name, half, w, z0, z1, m, parent=None):
    """A hollow square frame (outer half-size half, wall w) from z0 to z1: one mesh."""
    o_, i_ = half, half - w
    sq = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    vs = [(x * o_, y * o_, z0) for x, y in sq] + [(x * o_, y * o_, z1) for x, y in sq] + \
         [(x * i_, y * i_, z0) for x, y in sq] + [(x * i_, y * i_, z1) for x, y in sq]
    fs = []
    for k in range(4):
        k2 = (k + 1) % 4
        fs += [(k, k2, 4 + k2, 4 + k), (12 + k, 12 + k2, 8 + k2, 8 + k), (4 + k, 4 + k2, 12 + k2, 12 + k), (8 + k, 8 + k2, k2, k)]
    return mesh(name, vs, fs, m, parent)


def twist_prism(name, half, z0, z1, turn, m, parent=None, rings=10):
    """A square sleeve from z0 down to z1 that twists `turn` radians along its length: one mesh."""
    vs, fs = [], []
    for k in range(rings + 1):
        t = k / rings; a = turn * t + math.pi / 4; z = z0 + (z1 - z0) * t; r = half * math.sqrt(2)
        for j in range(4):
            b_ = a + j * math.pi / 2
            vs.append((r * math.cos(b_), r * math.sin(b_), z))
    for k in range(rings):
        for j in range(4):
            q = k * 4 + j; q2 = k * 4 + (j + 1) % 4
            fs.append((q, q2, q2 + 4, q + 4))
    fs += [(3, 2, 1, 0), tuple(rings * 4 + j for j in range(4))]
    return mesh(name, vs, fs, m, parent)


def edged_box(tag, nm, a, c, T, parent, e=0.035):
    """A slab with a glow line on all 12 of its edges."""
    box(f"{tag} {nm} body", a, c, T, parent, uvt=1.0)
    xs, ys, zs = (a[0], c[0]), (a[1], c[1]), (a[2], c[2])
    for x in xs:
        for y in ys:
            box(f"{tag} {nm} edge z", (x - e, y - e, zs[0]), (x + e, y + e, zs[1]), RM, parent)
        for z in zs:
            box(f"{tag} {nm} edge y", (x - e, ys[0], z - e), (x + e, ys[1], z + e), RM, parent)
    for y in ys:
        for z in zs:
            box(f"{tag} {nm} edge x", (xs[0], y - e, z - e), (xs[1], y + e, z + e), RM, parent)


def horse_anim(b, nk, tl, mane, f, run, air):
    a2 = 2 * math.pi * f / 10
    key(b, f, loc=(0, 0, 1.0 + 0.08 * abs(math.sin(a2)) * run * (1 - air)))
    key(nk, f, rot=(R(-20 + 10 * math.sin(a2) * run - 15 * air), 0, 0))
    key(tl, f, rot=(R(60 * max(run, air) + 10 * math.sin(a2)), 0, 0))
    for k, mn in enumerate(mane):
        key(mn, f, rot=(R(-30 * run - 25 * air + 12 * math.sin(a2 - k * 0.6)), 0, 0))


# ================================================================== F1a: winged horse, R2 K1 (three new builds)
def build_F1a1(tag, root, bx):
    """Fan wings: nine slats on ONE pivot per side that fan open like a folding fan (folded, they lie flat along the
    flank). Standing spring take-off, no gallop; a full climbing circle to 9 blocks."""
    T = TEX["r2k1"]
    b, nk, tl, mane, legs = horse_blocky(tag, root, T, DARK_RIM)
    wings = []
    for s in (-1, 1):
        wr = empty(f"{tag} fan root {s}", (s * 0.34, 0.25, 0.28), b)
        ball(f"{tag} fan hub {s}", 0.07, DARK_RIM, parent=wr, seg=8)
        slats = []
        for k in range(9):
            fe = empty(f"{tag} fan slat pivot {s} {k}", (0, 0, 0.004 * k), wr)
            ln = 0.85 + 0.09 * k
            box(f"{tag} fan slat {s} {k}", (-0.075, -ln, -0.012), (0.075, -0.08, 0.012), T, fe)
            box(f"{tag} fan rib {s} {k}", (-0.015, -ln, -0.02), (0.015, -0.08, 0.02), DARK_RIM, fe)
            slats.append((fe, k))
        wings.append((wr, slats, s))
    R_ = 4.5
    def pos(u, f):
        hop = 1.2 * smooth(ramp(f, 28, 34))
        g = ramp(f, 32, FRAME_END)
        ph = 2 * math.pi * 1.0 * g
        z = hop + 7.8 * smooth(ramp(f, 32, 104))
        return (bx - R_ * (1 - math.cos(ph)), 1.5 * smooth(ramp(f, 28, 34)) + R_ * math.sin(ph), z)
    def extra(u, f):
        crouch = math.sin(math.pi * ramp(f, 22, 30))
        return R(-14) * crouch + R(18) * math.sin(math.pi * ramp(f, 29, 38)), 0.0
    fly(root, pos, bank_k=2.5, pitch_k=0.6, extra=extra)
    for f in range(1, FRAME_END + 1):
        crouch = math.sin(math.pi * ramp(f, 22, 30))
        air = smooth(ramp(f, 30, 36))
        for hip, kn, ph, front in legs:
            h = -35 * crouch * (1 if front else -1) + air * (25 if front else -20)
            k = 50 * crouch * (-1 if front else 1) - air * (90 if front else -55)
            key(hip, f, rot=(R(h), 0, 0)); key(kn, f, rot=(R(k), 0, 0))
        key(b, f, loc=(0, 0, 1.0 - 0.18 * crouch))
        key(nk, f, rot=(R(-20 - 12 * air), 0, 0))
        key(tl, f, rot=(R(30 + 30 * air + 8 * math.sin(f * 0.4)), 0, 0))
        for k, mn in enumerate(mane):
            key(mn, f, rot=(R(-20 - 30 * air + 10 * math.sin(f * 0.6 - k * 0.6)), 0, 0))
        open_ = smooth(ramp(f, 24, 30))
        a = 2 * math.pi * (f - 30) / 13
        beat = 0.0 if f < 29 else (70 * math.sin(a) if f < 96 else 6)
        if 29 <= f <= 36:
            beat = 75 * math.cos(math.pi * ramp(f, 29, 36))       # one huge downstroke for the spring
        for wr, slats, s in wings:
            key(wr, f, rot=(0, R(-s * beat * open_), 0))
            for fe, k in slats:
                fanned = s * (8 + 88 * k / 8) * open_
                key(fe, f, rot=(0, 0, R(fanned)))
    return 1, 80


def build_F1a2(tag, root, bx):
    """Four wings, dragonfly style: a short fore pair and a hind pair of feather slats beating out of phase, fast. The
    legs never stop galloping: it runs up the air in three surges, each one a step higher."""
    T = TEX["r2k1"]
    b, nk, tl, mane, legs = horse_blocky(tag, root, T, DARK_RIM)
    wings = []
    for wy, lag in ((0.5, 0.0), (-0.45, 0.5)):
        for s in (-1, 1):
            wr = empty(f"{tag} wing {wy} {s}", (s * 0.33, wy, 0.26), b)
            box(f"{tag} wing bar {wy} {s}", (0, -0.035, -0.03), (s * 0.95, 0.035, 0.03), DARK_RIM, wr)
            for k in range(5):
                fe = empty(f"{tag} quill {wy} {s} {k}", (s * (0.12 + 0.2 * k), 0, 0), wr)
                fe.rotation_euler = (0, 0, R(-s * (3 * k - 4)))
                ln = 0.42 + 0.08 * k
                box(f"{tag} quill slat {wy} {s} {k}", (-0.08, -ln, -0.012), (0.08, 0.02, 0.012), T, fe)
            wings.append((wr, s, lag))
    steps = [(38, 2.6), (60, 2.6), (82, 2.6)]
    def pos(u, f):
        z = sum(h * smooth(ramp(f, f0_, f0_ + 12)) for f0_, h in steps)
        return (bx + 0.6 * math.sin(f * 0.05), 30 * u, z)
    fly(root, pos, pitch_k=0.6, max_pitch=25)
    for f in range(1, FRAME_END + 1):
        run = ramp(f, FORM, FORM + 6)
        surge = sum(math.sin(math.pi * ramp(f, f0_, f0_ + 12)) for f0_, _ in steps)
        gallop(legs, f, run, period=8 if surge > 0.1 else 10)
        horse_anim(b, nk, tl, mane, f, run, 0.0)
        on = ramp(f, 30, 36)
        for wr, s, lag in wings:
            a = 2 * math.pi * (f / 7 + lag)
            up = (12 + (35 + 20 * surge) * math.sin(a)) * on
            key(wr, f, rot=(0, R(-s * up), R(s * 60 * (1 - on))))
    return 1, 72


def build_F1a3(tag, root, bx):
    """Z-fold wings: a three-joint arm (shoulder, elbow, wrist) that folds in a Z against the flank, with feathers in
    three tiers (short coverts, mid secondaries, long primaries). A long run, ONE huge stroke, then it soars on held
    wings through an S-turn, with two small trim flaps."""
    T = TEX["r2k1"]
    b, nk, tl, mane, legs = horse_blocky(tag, root, T, DARK_RIM)
    wings = []
    for s in (-1, 1):
        sh = empty(f"{tag} shoulder {s}", (s * 0.33, 0.4, 0.3), b)
        box(f"{tag} humerus {s}", (0, -0.04, -0.035), (s * 0.45, 0.04, 0.035), DARK_RIM, sh)
        el = empty(f"{tag} elbow {s}", (s * 0.45, 0, 0), sh)
        box(f"{tag} radius {s}", (0, -0.035, -0.03), (s * 0.45, 0.035, 0.03), DARK_RIM, el)
        wr_ = empty(f"{tag} wrist {s}", (s * 0.45, 0, 0), el)
        box(f"{tag} hand bone {s}", (0, -0.03, -0.025), (s * 0.4, 0.03, 0.025), DARK_RIM, wr_)
        for par, n_, ln0, dl, tier in ((sh, 4, 0.3, 0.02, "covert"), (el, 4, 0.62, 0.04, "secondary"), (wr_, 5, 0.85, 0.09, "primary")):
            for k in range(n_):
                fe = empty(f"{tag} {tier} {s} {k}", (s * (0.06 + 0.1 * k), 0, 0.02 if tier == "covert" else 0), par)
                fe.rotation_euler = (0, 0, R(-s * (6 * k if tier == "primary" else 0)))
                ln = ln0 + dl * k
                box(f"{tag} {tier} slat {s} {k}", (-0.06, -ln, -0.012), (0.06, 0.02, 0.012), T, fe)
        wings.append((sh, el, wr_, s))
    def pos(u, f):
        z = 6.8 * smooth(ramp(f, 52, 84)) + 0.6 * smooth(ramp(f, 92, 104))
        x = bx + 3.0 * math.sin(2 * math.pi * ramp(f, 64, FRAME_END))
        return (x, 30 * u, z)
    fly(root, pos, bank_k=6.0, pitch_k=0.7)
    for f in range(1, FRAME_END + 1):
        run = ramp(f, FORM, FORM + 6)
        air = smooth(ramp(f, 50, 56))
        gallop(legs, f, run * (1 - air), tuck=air * 0.5, stretch=air * 0.5)
        horse_anim(b, nk, tl, mane, f, run * (1 - air), air)
        unfold = smooth(ramp(f, 44, 52))
        stroke = 0.0
        if 48 <= f <= 60:
            stroke = 70 * math.cos(math.pi * ramp(f, 48, 60))         # up at 48, all the way down by 60
        trim = 18 * math.sin(math.pi * ramp(f, 90, 96)) + 18 * math.sin(math.pi * ramp(f, 98, 104))
        held = 14 * smooth(ramp(f, 58, 66))                             # the soaring dihedral
        for sh, el, wr_, s in wings:
            up = stroke + held * (1 if f > 58 else 0) + trim
            key(sh, f, rot=(0, R(-s * up), R(s * 70 * (1 - unfold))))
            key(el, f, rot=(0, R(s * 6 * (1 if f > 58 else 0)), R(-s * 140 * (1 - unfold))))
            key(wr_, f, rot=(0, R(-s * 0.3 * stroke), R(s * 120 * (1 - unfold))))
    return 1, 78


# ================================================================== F1c: comet horse, H1 (three new builds)
def smooth_legs(tag, b, T, spots, r_top=0.11, r_mid=0.065):
    legs = []
    for (lx, ly, ph) in spots:
        hip = empty(f"{tag} hip {lx} {ly}", (lx, ly, -0.18), b)
        cyl(f"{tag} thigh {lx} {ly}", 0.07, 0.45, T, n=10, parent=hip, loc=(0, 0, -0.45), r2=r_top)
        kn = empty(f"{tag} knee {lx} {ly}", (0, 0, -0.45), hip)
        cyl(f"{tag} shin {lx} {ly}", 0.045, 0.4, T, n=10, parent=kn, loc=(0, 0, -0.4), r2=r_mid)
        cyl(f"{tag} hoof {lx} {ly}", 0.075, 0.07, RM, n=10, parent=kn, loc=(0, 0, -0.45))
        legs.append((hip, kn, ph, ly > 0))
    return legs


def smooth_head(tag, b, T, loc=(0, 0.65, 0.18), crest_n=0):
    nk = empty(f"{tag} neck", loc, b); nk.rotation_euler = (R(-30), 0, 0)
    lathe(f"{tag} neck", [(0.0, 0.0), (0.22, 0.02), (0.2, 0.3), (0.14, 0.62), (0.0, 0.72)], T, nk).rotation_euler = (R(90), 0, 0)
    hd = empty(f"{tag} head", (0, 0.0, 0.66), nk); hd.rotation_euler = (R(-60), 0, 0)
    lathe(f"{tag} skull", [(0.0, -0.08), (0.14, 0.0), (0.16, 0.18), (0.11, 0.42), (0.0, 0.5)], T, hd)
    for s in (-1, 1):
        ball(f"{tag} eye {s}", 0.035, RM, loc=(s * 0.13, 0.12, 0.06), parent=hd, seg=8)
        cyl(f"{tag} ear {s}", 0.04, 0.16, T, n=8, parent=hd, loc=(s * 0.07, -0.04, 0.1), r2=0.0)
    return nk, hd


def flakes(tag, pts_fn, frames, m, size=0.05, life=8, drop=0.15, hexa=False):
    """Light flakes left behind at world points pts_fn(f) -> [Vector], each fading over `life` ticks."""
    pm = pixel_mesh(m, size)
    if hexa:
        hm = bpy.data.meshes.get(f"{tag} hex flake")
        if hm is None:
            o = cyl(f"{tag} hex flake proto", size * 1.6, size * 0.6, m, n=6); hm = o.data; hm.name = f"{tag} hex flake"
            bpy.data.objects.remove(o)
        pm = hm
    for f in frames:
        scene.frame_set(f)
        for hp in pts_fn(f):
            px = link(bpy.data.objects.new(f"{tag} flake", pm))
            key(px, 1, loc=hp, sc=0.0001); key(px, f - 1, loc=hp, sc=0.0001); key(px, f, loc=hp, sc=1.0)
            key(px, f + life, loc=hp + Vector((0, 0, -drop)), sc=0.0001)
    scene.frame_set(1)


def build_F1c1(tag, root, bx):
    """Comet tail: smooth H1 body whose hind end runs out into a long tapering comet tail of six rings round a cone;
    the hind legs fold up into it in flight. Rears, launches, climbs, rolls once round its own length at the top,
    then a shallow dive. The flakes stream from the tail tip like a comet."""
    T = TEX["h1"]
    b = empty(f"{tag} body", (0, 0, 1.0), root)
    lathe(f"{tag} barrel", [(0.0, 0.85), (0.22, 0.8), (0.34, 0.5), (0.36, 0.0), (0.3, -0.5), (0.18, -0.85), (0.0, -0.95)], T, b, n=20)
    nk, hd = smooth_head(tag, b, T)
    tl = empty(f"{tag} tail", (0, -0.9, 0.05), b)
    cyl(f"{tag} tail cone", 0.17, 1.6, T, n=12, parent=tl, axis="Y", r2=0.0).rotation_euler = (0, 0, R(180))
    for k in range(6):
        torus(f"{tag} tail ring {k}", 0.22 - 0.03 * k, 0.025, RM, loc=(0, -0.15 - 0.24 * k, 0), parent=tl, axis="Y", n=16, k=5)
    tip = empty(f"{tag} tail tip", (0, -1.6, 0), tl)
    box(f"{tag} saddle", (-0.32, -0.25, 0.3), (0.32, 0.2, 0.37), GR, b)
    legs = smooth_legs(tag, b, T, ((0.18, 0.5, 0.0), (-0.18, 0.5, 0.5), (0.18, -0.5, 0.25), (-0.18, -0.5, 0.75)))
    rider(f"{tag} rider", b, (0, -0.05, 0.37))
    def pos(u, f):
        z = 7.0 * smooth(ramp(f, FORM + 6, 64)) - 2.5 * smooth(ramp(f, 92, FRAME_END))
        return (bx, 32 * u, z)
    def extra(u, f):
        return R(30) * math.sin(math.pi * ramp(f, FORM + 1, FORM + 13)), 0.0
    fly(root, pos, pitch_k=0.8, extra=extra)
    for f in range(1, FRAME_END + 1):
        rear = ramp(f, FORM, FORM + 4) * (1 - ramp(f, FORM + 10, FORM + 14))
        st = smooth(ramp(f, FORM + 8, FORM + 14))
        for hip, kn, ph, front in legs:
            if front:
                h = 80 * rear * (1 - st) + 72 * st; k = -100 * rear * (1 - st) - 8 * st
            else:
                h = -10 * rear * (1 - st) - 95 * st; k = 70 * st          # folded up into the comet tail
            key(hip, f, rot=(R(h), 0, 0)); key(kn, f, rot=(R(k), 0, 0))
        key(tl, f, rot=(R(-6 + 4 * math.sin(f * 0.3)), 0, R(8 * math.sin(f * 0.22))))
        roll = 2 * math.pi * smooth(ramp(f, 66, 86))
        key(b, f, loc=(0, 0, 1.0), rot=(0, roll, 0))
    flakes(tag, lambda f: [tip.matrix_world @ Vector((0, 0, 0))], range(FORM + 14, FRAME_END - 1, 1), W, 0.06, life=10, drop=0.05)
    return 1, 76


def build_F1c2(tag, root, bx):
    """Ring-sliced body: the same smooth comet silhouette but built as eleven separate lathe slices with thin gaps (the
    sky shows between them). Gallops a few strides, then climbs a tight helix one and a half turns up to 10 blocks;
    the hooves draw ribbons of light, not flakes."""
    T = TEX["h1"]
    b = empty(f"{tag} body", (0, 0, 1.0), root)
    prof = lambda y: 0.36 * math.sqrt(max(0.0, 1 - (y / 0.9) ** 2))
    for k in range(11):
        y0 = -0.88 + 0.16 * k; y1 = y0 + 0.13
        lathe(f"{tag} slice {k}", [(0.0, y0), (prof(y0), y0), (prof((y0 + y1) / 2), (y0 + y1) / 2), (prof(y1), y1), (0.0, y1)], T, b, n=18)
    nk, hd = smooth_head(tag, b, T)
    tl = empty(f"{tag} tail", (0, -0.85, 0.12), b)
    for k in range(4):
        lathe(f"{tag} tail slice {k}", [(0.0, -0.2 * k), (0.11 - 0.025 * k, -0.2 * k), (0.1 - 0.025 * k, -0.2 * k - 0.15), (0.0, -0.2 * k - 0.15)], T, tl, n=10)
    box(f"{tag} saddle", (-0.3, -0.25, 0.3), (0.3, 0.2, 0.36), GR, b)
    legs = smooth_legs(tag, b, T, ((0.18, 0.55, 0.0), (-0.18, 0.55, 0.5), (0.18, -0.55, 0.25), (-0.18, -0.55, 0.75)))
    rider(f"{tag} rider", b, (0, -0.05, 0.36))
    Rh = 4.0
    def pos(u, f):
        g = ramp(f, 38, FRAME_END)
        ph = 2 * math.pi * 1.5 * g
        y0 = 6.0 * ramp(f, FORM + 2, 38)
        return (bx - Rh * (1 - math.cos(ph)), y0 + Rh * math.sin(ph), 10.0 * smooth(ramp(f, 34, 112)))
    fly(root, pos, bank_k=3.0, pitch_k=0.7)
    for f in range(1, FRAME_END + 1):
        run = ramp(f, FORM, FORM + 4); air = smooth(ramp(f, 34, 40))
        gallop(legs, f, run * (1 - air), stretch=air)
        key(b, f, loc=(0, 0, 1.0 + 0.07 * abs(math.sin(f * 0.63)) * run * (1 - air)))
        key(tl, f, rot=(R(-20 * air + 30 * (1 - air) + 6 * math.sin(f * 0.3)), 0, R(8 * math.sin(f * 0.2))))
    # ribbons: a thin glowing strip between successive hoof positions, fading over 10 ticks
    bpy.context.view_layer.update()
    prev = {}
    for f in range(36, FRAME_END - 1, 2):
        scene.frame_set(f)
        for idx, (hip, kn, ph, front) in enumerate(legs):
            hp = kn.matrix_world @ Vector((0, 0, -0.45))
            if idx in prev and (hp - prev[idx]).length > 0.05:
                rb = bar(f"{tag} ribbon {idx} {f}", tuple(prev[idx]), tuple(hp), 0.035, W, n=4)
                show(rb, f, f + 10)
                key(rb, f + 6, sc=1.0); key(rb, f + 10, sc=(0.2, 0.2, 1.0))
            prev[idx] = hp
    scene.frame_set(1)
    return 1, 80


def build_F1c3(tag, root, bx):
    """One-piece lathe body: barrel and tail turned as a single smooth piece with a pointed rear. Three bounding leaps,
    each higher, a hex shock ring at every push-off; the third leap takes it up, a dive, and a climb out. Its flakes
    are little hex plates."""
    T = TEX["h1"]
    b = empty(f"{tag} body", (0, 0, 1.0), root)
    lathe(f"{tag} hull", [(0.0, 0.82), (0.2, 0.78), (0.33, 0.45), (0.35, 0.0), (0.3, -0.45), (0.2, -0.8), (0.1, -1.1),
                          (0.03, -1.5), (0.0, -1.62)], T, b, n=20)
    nk, hd = smooth_head(tag, b, T, crest_n=0)
    for k in range(4):
        cyl(f"{tag} neck fin {k}", 0.05, 0.16, RM, n=4, parent=nk, loc=(0, -0.16, 0.12 + 0.14 * k), r2=0.0).rotation_euler = (R(-120), 0, 0)
    tl = empty(f"{tag} tail", (0, -1.0, 0.0), b)
    box(f"{tag} saddle", (-0.32, -0.25, 0.3), (0.32, 0.2, 0.37), GR, b)
    legs = smooth_legs(tag, b, T, ((0.18, 0.5, 0.0), (-0.18, 0.5, 0.5), (0.18, -0.45, 0.25), (-0.18, -0.45, 0.75)), r_top=0.12, r_mid=0.07)
    rider(f"{tag} rider", b, (0, -0.05, 0.37))
    bounds = [(26, 38, 1.4), (40, 54, 3.2)]
    def pos(u, f):
        z = sum(h * math.sin(math.pi * ramp(f, a, c)) for a, c, h in bounds)
        z += 7.0 * smooth(ramp(f, 54, 80)) - 3.0 * math.sin(math.pi * ramp(f, 84, 106))
        x = bx + 2.5 * math.sin(math.pi * ramp(f, 82, 112))
        return (x, 32 * u, z)
    fly(root, pos, bank_k=5.0, pitch_k=0.8)
    for f in range(1, FRAME_END + 1):
        flight = 0.0
        for a, c, h in bounds:
            flight = max(flight, math.sin(math.pi * ramp(f, a, c)))
        flight = max(flight, smooth(ramp(f, 56, 62)))
        run = ramp(f, FORM, FORM + 4)
        for hip, kn, ph, front in legs:
            sw = 30 * math.sin(2 * math.pi * f / 9 + ph * 6) * run * (1 - flight)
            h = sw + flight * (75 if front else -70); k = -45 * max(0.0, math.sin(2 * math.pi * f / 9 + ph * 6 + 1.2)) * run * (1 - flight) - flight * (10 if front else -8)
            key(hip, f, rot=(R(h), 0, 0)); key(kn, f, rot=(R(k), 0, 0))
        key(nk, f, rot=(R(-30 - 12 * flight), 0, 0))
    # a hex shock ring at each push-off, flat on the ground under the horse, widening and fading
    for f0 in (26, 40, 56):
        scene.frame_set(f0)
        p = root.matrix_world.translation.copy()
        ring = torus(f"{tag} push ring {f0}", 0.5, 0.05, W, loc=(p.x, p.y, max(0.03, p.z + 0.03)), n=6, k=4)
        show(ring, f0, f0 + 9)
        key(ring, f0, sc=0.5); key(ring, f0 + 8, sc=2.6)
    scene.frame_set(1)
    flakes(tag, lambda f: [kn.matrix_world @ Vector((0, 0, -0.45)) for hip, kn, ph, front in legs[2:]],
           range(58, FRAME_END - 1, 2), W, 0.05, life=9, drop=0.1, hexa=True)
    return 1, 66


# ================================================================== F2c: blocky glider, H1 (three new builds)
def dragon_blocky(tag, root, T, long_=False):
    """The F2c voxel dragon: chest, hips, back spikes, neck, boxy head, five-box tail, four box legs, rider."""
    b = empty(f"{tag} body", (0, 0, 0.9), root)
    box(f"{tag} chest", (-0.38, -0.1, -0.32), (0.38, 0.5, 0.36), T, b)
    box(f"{tag} hips", (-0.32, -0.75 if long_ else -0.55, -0.28), (0.32, -0.1, 0.3), T, b)
    for k in range(4):
        box(f"{tag} back spike {k}", (-0.04, 0.35 - 0.25 * k, 0.36), (0.04, 0.45 - 0.25 * k, 0.5 - 0.02 * k), RM, b)
    nk = empty(f"{tag} neck", (0, 0.5, 0.15), b)
    box(f"{tag} neck box", (-0.17, 0.0, -0.15), (0.17, 0.25, 0.2), T, nk)
    hd = empty(f"{tag} head", (0, 0.25, 0.05), nk)
    box(f"{tag} skull", (-0.26, -0.05, -0.2), (0.26, 0.38, 0.24), T, hd)
    box(f"{tag} snout", (-0.16, 0.38, -0.16), (0.16, 0.64, 0.06), T, hd)
    for s in (-1, 1):
        box(f"{tag} eye {s}", (s * 0.26 - 0.01, 0.2, 0.04), (s * 0.26 + 0.01, 0.32, 0.12), RM, hd)
        box(f"{tag} horn {s}", (s * 0.18 - 0.04, -0.15, 0.2), (s * 0.18 + 0.04, -0.02, 0.42), RM, hd)
    tail = []; prev = b; p_ = (0, -0.75 if long_ else -0.55, 0.0)
    for i in range(5):
        s_ = empty(f"{tag} tail {i}", p_, prev); w_ = 0.16 - i * 0.025
        box(f"{tag} tail box {i}", (-w_, -0.26, -w_), (w_, 0, w_), T, s_); tail.append(s_); prev = s_; p_ = (0, -0.26, 0)
    legs = []
    for s in (-1, 1):
        for y in (0.25, -0.35):
            lg = empty(f"{tag} leg {s} {y}", (s * 0.28, y, -0.3), b)
            box(f"{tag} leg box {s} {y}", (-0.09, -0.09, -0.3), (0.09, 0.1, 0.0), T, lg)
            legs.append((lg, s, y))
    rider(f"{tag} rider", b, (0, 0.05, 0.4), legs_down=True)
    return b, nk, tail, legs, prev


def tail_wave(tail, f, amp=8):
    for i, s_ in enumerate(tail):
        key(s_, f, rot=(R(-4 + 4 * math.sin(f * 0.15 - i * 0.6)), 0, R(amp * math.sin(f * 0.12 - i * 0.7))))


def build_F2c1(tag, root, bx):
    """Voxel-grid wings: each wing is a 6 x 3 grid of loose H1 cubes on six chained span joints, so a flap travels out
    along the wing as a wave. Runs on all fours, launches, then circles up a thermal to 8 blocks on spread wings."""
    T = TEX["h1"]
    b, nk, tail, legs, tail_end = dragon_blocky(tag, root, T)
    wings = []
    for s in (-1, 1):
        prev = empty(f"{tag} wing root {s}", (s * 0.38, 0.3, 0.25), b); joints = [prev]
        for c in range(6):
            j = empty(f"{tag} wing col {s} {c}", (s * (0.0 if c == 0 else 0.2), 0, 0), prev)
            rows = 3 if c < 4 else 2
            for r_ in range(rows):
                y0 = -0.06 - 0.24 * r_
                box(f"{tag} wing cube {s} {c} {r_}", (s * 0.01, y0 - 0.2, -0.04), (s * 0.19, y0, 0.04), T if (c + r_) % 2 == 0 else GL, j)
            box(f"{tag} wing spar {s} {c}", (s * 0.0, -0.04, -0.05), (s * 0.2, 0.04, 0.05), RM, j)
            joints.append(j); prev = j
        wings.append((joints, s))
    Rt = 4.5
    def pos(u, f):
        g = ramp(f, 46, FRAME_END); ph = 2 * math.pi * 1.2 * g
        y0 = 7.0 * ramp(f, FORM + 2, 46)
        z = 1.2 * smooth(ramp(f, 40, 46)) + 6.8 * smooth(ramp(f, 46, 116))
        return (bx + Rt * (1 - math.cos(ph)), y0 + Rt * math.sin(ph), z)
    fly(root, pos, bank_k=5.0, pitch_k=0.5)
    for f in range(1, FRAME_END + 1):
        run = ramp(f, FORM, FORM + 4) * (1 - smooth(ramp(f, 40, 44)))
        for lg, s, y in legs:
            key(lg, f, rot=(R(40 * math.sin(2 * math.pi * f / 8 + (0 if (s > 0) == (y > 0) else math.pi)) * run - 70 * ramp(f, 42, 48)), 0, 0))
        open_ = smooth(ramp(f, 36, 42))
        flap = ramp(f, 38, 40) * (1 - smooth(ramp(f, 70, 78)))
        for joints, s in wings:
            key(joints[0], f, rot=(0, 0, R(s * 75 * (1 - open_))))
            for c, j in enumerate(joints[1:]):
                w = (22 if c else 30) * math.sin(2 * math.pi * f / 12 - c * 0.7) * flap + (3 + 2 * math.sin(f * 0.2 - c)) * (1 - flap) * open_
                key(j, f, rot=(0, R(-s * w), 0))
        tail_wave(tail, f)
        key(nk, f, rot=(R(-6 * open_), 0, 0))
    return 1, 84


def build_F2c2(tag, root, bx):
    """Folding-screen wings: five rigid H1 panels per side hinged edge to edge, packed in a zigzag on the back and
    snapping open flat. A construct pillar grows under it and lifts it 4.5 blocks; it dives off, opens, pulls up into a
    long glide; the pillar breaks up behind."""
    T = TEX["h1"]
    b, nk, tail, legs, tail_end = dragon_blocky(tag, root, T, long_=True)
    wings = []
    for s in (-1, 1):
        wr = empty(f"{tag} wing root {s}", (s * 0.38, 0.32, 0.3), b)
        prev = wr; hinges = []
        for k in range(5):
            h = empty(f"{tag} hinge {s} {k}", (s * (0.0 if k == 0 else 0.32), 0, 0), prev)
            ln = 1.0 - 0.1 * abs(k - 1.5)
            box(f"{tag} panel {s} {k}", (s * 0.01, -ln, -0.02), (s * 0.31, 0.04, 0.02), T, h)
            box(f"{tag} hinge rod {s} {k}", (s * -0.02, -ln, -0.03), (s * 0.02, 0.04, 0.03), RM, h)
            hinges.append(h); prev = h
        box(f"{tag} tip rod {s}", (s * 0.3, -0.8, -0.03), (s * 0.34, 0.04, 0.03), RM, prev)
        wings.append((wr, hinges, s))
    top = 4.5
    pillar = []
    for k in range(9):
        pz = k * 0.5
        seg = box(f"{tag} pillar {k}", (bx - 0.6, -0.6, pz), (bx + 0.6, 0.6, pz + 0.46), T)
        edge = box(f"{tag} pillar band {k}", (bx - 0.63, -0.63, pz + 0.42), (bx + 0.63, 0.63, pz + 0.48), RM)
        for o in (seg, edge):
            fa = FORM + 1 + int(k * 1.5)
            key(o, 1, sc=0.0001); key(o, fa - 1, sc=0.0001); key(o, fa + 1, sc=1.0)
            o.data.transform(Matrix.Translation((-bx, 0, -(pz + 0.23)))); o.location = (bx, 0, pz + 0.23)
            pillar.append(o)
    def pos(u, f):
        lift = top * smooth(ramp(f, FORM + 1, FORM + 15))
        dive = -2.2 * math.sin(math.pi * ramp(f, 40, 58)) + 3.0 * smooth(ramp(f, 54, 100))
        y = 22 * smooth(ramp(f, 38, FRAME_END)) + 8 * ramp(f, 60, FRAME_END)
        return (bx + 2.0 * math.sin(math.pi * ramp(f, 70, FRAME_END)), y, lift + dive * ramp(f, 38, 40))
    fly(root, pos, bank_k=6.0, pitch_k=0.7)
    for f in range(1, FRAME_END + 1):
        open_ = smooth(ramp(f, 40, 46))
        glide_flap = 14 * math.sin(math.pi * ramp(f, 56, 64))
        for wr, hinges, s in wings:
            key(wr, f, rot=(0, R(-s * (20 * (1 - open_) + glide_flap + 3)), 0))
            for k, h in enumerate(hinges):
                fold = (1 - open_) * (150 if k % 2 else -150) * (0 if k == 0 else 1)
                key(h, f, rot=(0, R(s * fold), 0))
        for lg, s, y in legs:
            key(lg, f, rot=(R(-70 * ramp(f, 38, 44)), 0, 0))
        tail_wave(tail, f, 6)
        key(nk, f, rot=(R(10 * math.sin(math.pi * ramp(f, 38, 50)) - 6 * open_), 0, 0))
    shatter(pillar, 52, CM["pix"], rng, tag, n=2)
    return 1, 70


def build_F2c3(tag, root, bx):
    """Stepped delta: each wing one rigid pixel-art triangle (rows of H1 boxes, each row narrower going back) and a box
    tail fin. Hovers straight up on four quick short beats, then darts forward and swings into a steep 70-degree
    banked wingover turn and glides out."""
    T = TEX["h1"]
    b, nk, tail, legs, tail_end = dragon_blocky(tag, root, T)
    box(f"{tag} tail fin", (-0.02, -0.3, 0.0), (0.02, 0.0, 0.32), RM, tail_end)
    box(f"{tag} tail fin plate", (-0.25, -0.32, -0.02), (0.25, -0.05, 0.02), T, tail_end)
    wings = []
    for s in (-1, 1):
        wr = empty(f"{tag} delta root {s}", (s * 0.38, 0.45, 0.25), b)
        rows = 7
        for r_ in range(rows):
            span = 1.65 * (1 - r_ / rows) + 0.15
            y0 = -0.17 * r_
            box(f"{tag} delta row {s} {r_}", (0, y0 - 0.16, -0.025), (s * span, y0, 0.025), T, wr)
            box(f"{tag} delta step {s} {r_}", (s * (span - 0.06), y0 - 0.16, -0.035), (s * span, y0, 0.035), RM, wr)
        box(f"{tag} delta spar {s}", (0, -0.04, -0.04), (s * 1.8, 0.04, 0.04), RM, wr)
        wings.append((wr, s))
    def yaw(u, f):
        return R(120) * smooth(ramp(f, 66, 92))
    def pos(u, f):
        hover = 3.0 * smooth(ramp(f, 22, 46))
        p = Vector((0.0, 0.5 * ramp(f, 22, 48)))
        for ff in range(48, int(f) + 1):
            yw = yaw(0, ff); p += Vector((-math.sin(yw), math.cos(yw))) * 0.36 * smooth(ramp(ff, 48, 56))
        return (bx + p.x, p.y, hover + 1.5 * smooth(ramp(f, 48, 70)))
    def extra(u, f):                                      # the wingover: a steep 70-degree bank through the turn
        return 0.0, -R(70) * math.sin(math.pi * ramp(f, 62, 96))
    fly2(root, pos, yaw_fn=yaw, extra=extra)
    for f in range(1, FRAME_END + 1):
        beat = ramp(f, 22, 24) * (1 - ramp(f, 46, 48))
        a = 2 * math.pi * (f - 22) / 6
        for wr, s in wings:
            up = 45 * math.sin(a) * beat + (1 - beat) * (4 + 2 * math.sin(f * 0.25)) * ramp(f, FORM, 24)
            key(wr, f, rot=(0, R(-s * up), R(s * 50 * (1 - ramp(f, FORM, 24)))))
        for lg, s, y in legs:
            key(lg, f, rot=(R(-75 * ramp(f, 44, 50)), 0, 0))
        tail_wave(tail, f, 5)
        key(b, f, loc=(0, 0, 0.9 + 0.05 * math.sin(a) * beat), rot=(R(-16 * beat), 0, 0))
    return 1, 90


# ================================================================== F3a: ghast snug shell, R2 K1 (three new builds)
def build_F3a1(tag, root, bx):
    """Rounded-cube shell: one smooth superellipsoid piece (no flat faces, no bevel), 0.26 off the skin at the
    faces and clear of the real cube's corners; tapered cone sleeves. It breathes (shell swells 3%), rises 3, then glides
    straight out, speeding up, with a slow side-to-side sway."""
    T = TEX["r2k1"]
    b, tents = real_ghast(tag, root)
    shell = super_shell(f"{tag} shell", BS / 2 + 0.26, 16.0, T, b, centre=(0, 0, 0), seg=44)
    shell.location = (0, 0, BS / 2)
    ghast_face(tag, b, BS / 2 + 0.3, DARK_RIM, DARK_RIM)
    for piv, L, i in tents:
        cyl(f"{tag} sleeve {i}", 0.45, L + 0.06 + G - 0.1, T, n=12, parent=piv, loc=(0, 0, -L - 0.08), r2=0.58)
        ball(f"{tag} sleeve tip {i}", 0.44, DARK_RIM, loc=(0, 0, -L - 0.08), parent=piv, seg=8).scale = (1, 1, 0.4)
    rider(f"{tag} rider", b, (0, 0.4, BS + 0.29))
    def pos(u, f):
        y = 18 * ramp(f, 40, FRAME_END) ** 1.6
        return (bx + 1.5 * math.sin(2 * math.pi * f / 70), y, 3.0 * smooth(ramp(f, 22, 50)) + 0.12 * math.sin(f * 0.15))
    fly2(root, pos, yaw_fn=lambda u, f: R(-8) * math.cos(2 * math.pi * f / 70) * ramp(f, 30, 50),
         extra=lambda u, f: (0.0, R(5) * math.sin(2 * math.pi * f / 70) * ramp(f, 30, 50)))
    for f in range(1, FRAME_END + 1, 2):
        br = 0.5 + 0.5 * math.sin(2 * math.pi * f / 36)
        key(shell, f, sc=1.0 + 0.03 * br)
    return 2, 82


def build_F3a2(tag, root, bx):
    """Banded double shell: a thin snug inner shell (bevelled, 0.08 off) and five rounded square bands around it like
    hoops on a barrel, each sleeve with three bands too. Lifts straight up to 6, then cruises, turning its heading
    in two clean 30-degree steps."""
    T = TEX["r2k1"]
    b, tents = real_ghast(tag, root)
    sh = 0.08
    inner = box(f"{tag} inner shell", (-BS / 2 - sh, -BS / 2 - sh, -sh), (BS / 2 + sh, BS / 2 + sh, BS + sh), T, b, uvt=1.0)
    bevel(inner, 0.12, 2)
    for k in range(5):
        z = 0.35 + (BS - 0.7) * k / 4
        band = torus(f"{tag} band {k}", (BS / 2 + 0.24) / math.cos(math.pi / 4), 0.12, T if k % 2 else DARK_RIM, loc=(0, 0, z), parent=b, n=4, k=8)
        band.rotation_euler = (0, 0, R(45))
    ghast_face(tag, b, BS / 2 + sh + 0.02, DARK_RIM, DARK_RIM)
    for piv, L, i in tents:
        cyl(f"{tag} sleeve {i}", 0.42, L + G - 0.04, T, n=12, parent=piv, loc=(0, 0, -L - 0.06))
        for k in range(3):
            torus(f"{tag} sleeve band {i} {k}", 0.48, 0.05, DARK_RIM, loc=(0, 0, -0.5 - (L - 0.6) * k / 2), parent=piv, n=12, k=5)
    rider(f"{tag} rider", b, (0, 0.4, BS + sh))
    def yaw(u, f):
        return R(30) * smooth(ramp(f, 66, 74)) + R(30) * smooth(ramp(f, 92, 100))
    def pos(u, f):
        z = 6.0 * smooth(ramp(f, 22, 58)) + 0.1 * math.sin(f * 0.13)
        p = Vector((0.0, 0.0))
        for ff in range(60, int(f) + 1, 2):
            yw = yaw(0, ff); p += Vector((-math.sin(yw), math.cos(yw))) * 0.24
        return (bx + p.x, p.y, z)
    fly2(root, pos, bank_k=3.0, yaw_fn=yaw)
    return 2, 88


def build_F3a3(tag, root, bx):
    """Chamfered shell: one piece, a single 45-degree chamfer on every edge (a faceted gem look instead of round),
    0.14 off the skin; each sleeve a square prism twisted a quarter turn; a handrail for the rider. Strafes sideways
    four blocks while rising, then swings round and climbs away."""
    T = TEX["r2k1"]
    b, tents = real_ghast(tag, root)
    sh = 0.14
    shell = box(f"{tag} shell", (-BS / 2 - sh, -BS / 2 - sh, -sh), (BS / 2 + sh, BS / 2 + sh, BS + sh), T, b, uvt=1.0)
    bevel(shell, 0.42, 1)
    for p_ in shell.data.polygons:
        p_.use_smooth = False
    ghast_face(tag, b, BS / 2 + sh, DARK_RIM, DARK_RIM)
    for piv, L, i in tents:
        twist_prism(f"{tag} sleeve {i}", G + 0.18, G - 0.1, -L - 0.08, R(90) * (1 if i % 2 else -1), T, piv)
        box(f"{tag} sleeve cap {i}", (-G - 0.19, -G - 0.19, -L - 0.12), (G + 0.19, G + 0.19, -L - 0.06), DARK_RIM, piv)
    rail = empty(f"{tag} rail", (0, 0.4, BS + sh), b)
    for s in (-1, 1):
        bar(f"{tag} rail post {s}", (s * 0.4, 0.45, 0), (s * 0.4, 0.45, 0.35), 0.03, DARK_RIM, rail)
    bar(f"{tag} rail bar", (-0.42, 0.45, 0.35), (0.42, 0.45, 0.35), 0.03, DARK_RIM, rail)
    rider(f"{tag} rider", b, (0, 0.4, BS + sh))
    def yaw(u, f):
        return R(-50) * smooth(ramp(f, 64, 84))
    def pos(u, f):
        x = bx + 4.0 * smooth(ramp(f, 26, 62))
        yw = yaw(u, f)
        d = 12 * ramp(f, 72, FRAME_END) ** 1.3
        return (x - math.sin(yw) * d, math.cos(yw) * d, 2.5 * smooth(ramp(f, 22, 60)) + 3.0 * smooth(ramp(f, 72, 116)))
    def extra(u, f):
        return 0.0, R(-8) * math.sin(math.pi * ramp(f, 26, 62))
    fly2(root, pos, bank_k=2.0, yaw_fn=yaw, extra=extra)
    return 2, 70


# ================================================================== F3b: ghast lattice cage, W1 (three new builds)
def build_F3b1(tag, root, bx):
    """Round-bar cage: the 3 x 3 windows built from round rods with a glowing ball at every crossing; each tentacle in
    one long coil spring. Lifts in three vertical pulses (cage squeezes each time), then cruises forward on a slow
    turn."""
    T = TEX["w1"]
    b, tents = real_ghast(tag, root)
    cage = empty(f"{tag} cage", (0, 0, BS / 2), b)
    h = BS / 2 + 0.14; t = 0.06
    lines = [-h + 2 * h * k / 3 for k in range(4)]
    for ax in range(3):
        others = [i for i in range(3) if i != ax]
        for s in (-1, 1):
            for d in others:
                o2 = [i for i in others if i != d][0]
                for c in lines:
                    a = [0.0] * 3; bb = [0.0] * 3
                    a[ax] = bb[ax] = s * h; a[o2] = bb[o2] = c; a[d] = -h; bb[d] = h
                    bar(f"{tag} rod {ax}{s}{d}{c:.1f}", tuple(a), tuple(bb), t, T if abs(abs(c) - h) > 0.01 else RM, cage, n=8)
            for c1 in lines:
                for c2 in lines:
                    p = [0.0] * 3; p[ax] = s * h; p[others[0]] = c1; p[others[1]] = c2
                    ball(f"{tag} node {ax}{s}{c1:.1f}{c2:.1f}", 0.11, RM, loc=tuple(p), parent=cage, seg=8)
    ghast_face(tag, b, BS / 2 + 0.2, W, RM)
    for piv, L, i in tents:
        helix_tube(f"{tag} coil {i}", 0.5, max(3, L / 0.45), -0.3, -L - 0.05, 0.05, T if i % 2 else RM, piv)
    rider(f"{tag} rider", b, (0, 0.4, BS + 0.2))
    lifts = [FORM + 4, FORM + 18, FORM + 32]
    def pos(u, f):
        z = sum(2.0 * smooth(ramp(f, p0, p0 + 9)) for p0 in lifts) + 0.1 * math.sin(f * 0.15)
        g = ramp(f, 62, FRAME_END); th = R(50) * g
        Rr = 12.0
        return (bx - Rr * (1 - math.cos(th)) * 0.6, Rr * math.sin(th) * 1.1, z)
    fly(root, pos, pitch_k=0.0, bank_k=3.0)
    for f in range(1, FRAME_END + 1):
        sq = sum(math.sin(math.pi * ramp(f, p0, p0 + 9)) for p0 in lifts)
        key(cage, f, sc=(1 + 0.025 * sq, 1 + 0.025 * sq, 1 - 0.02 * sq))
    return 2, 75


def build_F3b2(tag, root, bx):
    """Diamond lattice: every face crossed by diagonal bars (a diamond grid, 3 x 3 diamonds) inside a frame that glows
    on all 12 edges; tentacles in stacks of square frames. Swims in five pulses that zigzag, turning left, right,
    left, like a jellyfish steering."""
    T = TEX["w1"]
    b, tents = real_ghast(tag, root)
    cage = empty(f"{tag} cage", (0, 0, BS / 2), b)
    h = BS / 2 + 0.13; t = 0.055
    for ax in range(3):
        u_, v_ = [i for i in range(3) if i != ax]
        for s in (-1, 1):
            for sign in (1, -1):
                for c in (-4 * h / 3, -2 * h / 3, 0.0, 2 * h / 3, 4 * h / 3):
                    pts = []
                    for uu in (-h, h):
                        vv = sign * (c - uu)
                        if -h - 1e-6 <= vv <= h + 1e-6:
                            pts.append((uu, vv))
                    for vv in (-h, h):
                        uu = c - sign * vv
                        if -h - 1e-6 <= uu <= h + 1e-6:
                            pts.append((uu, vv))
                    pts = sorted(set((round(p[0], 4), round(p[1], 4)) for p in pts))
                    if len(pts) < 2:
                        continue
                    A = [0.0] * 3; B = [0.0] * 3
                    A[ax] = B[ax] = s * h; A[u_], A[v_] = pts[0]; B[u_], B[v_] = pts[-1]
                    if (Vector(A) - Vector(B)).length > 0.2:
                        bar(f"{tag} diag {ax}{s}{sign}{c:.1f}", tuple(A), tuple(B), t, T, cage, n=6)
    e = 0.06
    for x in (-h, h):
        for y in (-h, h):
            box(f"{tag} frame z", (x - e, y - e, -h - e), (x + e, y + e, h + e), RM, cage)
        for z in (-h, h):
            box(f"{tag} frame y", (x - e, -h - e, z - e), (x + e, h + e, z + e), RM, cage)
    for y in (-h, h):
        for z in (-h, h):
            box(f"{tag} frame x", (-h - e, y - e, z - e), (h + e, y + e, z + e), RM, cage)
    ghast_face(tag, b, BS / 2 + 0.2, W, RM)
    for piv, L, i in tents:
        n = max(3, int(L / 0.45))
        for k in range(n):
            z = -0.3 - (L - 0.3) * k / max(1, n - 1)
            square_ring(f"{tag} frame {i} {k}", 0.5, 0.08, z - 0.06, z + 0.06, T if k % 2 else RM, piv)
    rider(f"{tag} rider", b, (0, 0.4, BS + 0.19))
    pulses = [FORM + 6 + 19 * k for k in range(5)]
    sides = [0, 1, -1, 1, -1]
    def yaw(u, f):
        return sum(R(22) * (sides[k] - (sides[k - 1] if k else 0)) * smooth(ramp(f, p0 - 3, p0 + 6)) for k, p0 in enumerate(pulses))
    def pos(u, f):
        p = Vector((0.0, 0.0))
        for ff in range(1, int(f) + 1):
            push = sum(math.sin(math.pi * ramp(ff, p0, p0 + 9)) for p0 in pulses) * 0.5
            yw = yaw(0, ff); p += Vector((-math.sin(yw), math.cos(yw))) * push
        return (bx + p.x, p.y, 3.5 * smooth(ramp(f, 22, 50)) + 0.1 * math.sin(f * 0.15))
    def extra(u, f):
        return sum(R(5) * math.sin(math.pi * ramp(f, p0, p0 + 9)) for p0 in pulses), 0.0
    fly2(root, pos, bank_k=3.0, yaw_fn=yaw, extra=extra)
    for f in range(1, FRAME_END + 1):
        sq = sum(math.sin(math.pi * ramp(f, p0, p0 + 9)) for p0 in pulses)
        key(cage, f, sc=(1 - 0.03 * sq + 0.03, 1 + 0.02 * sq + 0.03, 1 - 0.03 * sq + 0.03))
    return 2, 72


def build_F3b3(tag, root, bx):
    """Cage and gimbal: a fine 3 x 3 cage of thin square bars round the ghast, with a wide equator ring outside it that
    turns slowly, carrying six beads; each tentacle a lantern tube (hoops tied by three rods). Rises to 6 and drifts in
    a slow climbing corkscrew."""
    T = TEX["w1"]
    b, tents = real_ghast(tag, root)
    cage = empty(f"{tag} cage", (0, 0, BS / 2), b)
    h = BS / 2 + 0.1; t = 0.045
    for ax in range(3):
        for k in range(4):
            c = -h + 2 * h * k / 3
            for s in (-1, 1):
                for d in range(3):
                    if d == ax:
                        continue
                    other = [i for i in range(3) if i not in (ax, d)][0]
                    a = [0.0] * 3; bb = [0.0] * 3
                    a[ax] = s * h - t; bb[ax] = s * h + t; a[other] = c - t; bb[other] = c + t; a[d] = -h - t; bb[d] = h + t
                    box(f"{tag} bar {ax}{k}{s}{d}", tuple(a), tuple(bb), RM if k in (0, 3) else T, cage)
    ring = empty(f"{tag} gimbal", (0, 0, BS * 0.42), b)
    torus(f"{tag} gimbal ring", 4.3, 0.1, T, parent=ring, n=48, k=8)
    torus(f"{tag} gimbal rim", 4.3, 0.035, RM, loc=(0, 0, 0.1), parent=ring, n=48, k=5)
    for k in range(6):
        a = 2 * math.pi * k / 6
        ball(f"{tag} gimbal bead {k}", 0.2, W, loc=(4.3 * math.cos(a), 4.3 * math.sin(a), 0), parent=ring, seg=10)
    for s in (-1, 1):
        bar(f"{tag} gimbal strut {s}", (s * (h + 0.05), 0, 0), (s * 4.2, 0, 0), 0.04, RM, b).location = (s * (h + 0.05), 0, BS * 0.42)
    ghast_face(tag, b, BS / 2 + 0.16, W, RM)
    for piv, L, i in tents:
        n = max(3, int(L / 0.5))
        for k in range(n):
            z = -0.3 - (L - 0.3) * k / max(1, n - 1)
            torus(f"{tag} hoop {i} {k}", 0.46, 0.04, T if k % 2 else RM, loc=(0, 0, z), parent=piv, n=14, k=5)
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.3
            bar(f"{tag} tube rod {i} {k}", (0.46 * math.cos(a), 0.46 * math.sin(a), -0.3), (0.46 * math.cos(a), 0.46 * math.sin(a), -L), 0.025, RM, piv, n=5)
    rider(f"{tag} rider", b, (0, 0.4, BS + 0.15))
    def pos(u, f):
        g = ramp(f, 40, FRAME_END); th = 2 * math.pi * 0.75 * g
        Rr = 5.5
        return (bx + Rr * (1 - math.cos(th)) * -1, 4.0 * g + Rr * math.sin(th), 6.0 * smooth(ramp(f, 22, 60)) + 2.0 * g)
    fly(root, pos, pitch_k=0.0, bank_k=2.0)
    for f in range(1, FRAME_END + 1, 2):
        key(ring, f, rot=(0, 0, R(1.6 * f)))
    return 2, 90


# ================================================================== F3c: ghast brick strata, BR1 (three new builds)
def build_F3c1(tag, root, bx):
    """Front-to-back strata: the five slabs are stacked along the ghast's length (vertical slices), not up its height;
    they breathe apart front to back, all 12 edges of each glow, the brow rides the front slice, segmented sleeves.
    A long straight ramp climb to 6, then levels off."""
    T = TEX["br1"]
    b, tents = real_ghast(tag, root)
    sh = 0.12; n = 5; ws = (BS + 2 * sh) / n
    slices = []
    for k in range(n):
        y0 = -BS / 2 - sh + ws * k
        sl = empty(f"{tag} slice {k}", (0, y0 + ws / 2, 0), b)
        edged_box(tag, f"slice {k}", (-BS / 2 - sh, -ws / 2 + 0.02, -sh), (BS / 2 + sh, ws / 2 - 0.02, BS + sh), T, sl)
        slices.append((sl, y0 + ws / 2, k))
    front = slices[-1][0]
    fy = ws / 2 - 0.02
    brow = empty(f"{tag} brow", (0, fy, 10.9 * G), front)
    box(f"{tag} brow ledge", (-BS / 2 + 0.2, 0, -0.1), (BS / 2 - 0.2, 0.45, 0.14), T, brow)
    box(f"{tag} brow glow", (-BS / 2 + 0.2, 0.43, -0.12), (BS / 2 - 0.2, 0.47, 0.0), RM, brow)
    ghast_face(tag, front, fy + 0.04, W, RM)
    for piv, L, i in tents:
        m_ = max(2, int(L / 0.6))
        for k in range(m_):
            z1 = -sh - (L - sh + 0.06) * k / m_; z2 = -sh - (L - sh + 0.06) * (k + 1) / m_ + 0.06
            box(f"{tag} sleeve {i} {k}", (-G - 0.1, -G - 0.1, z2), (G + 0.1, G + 0.1, z1), T if k % 2 == 0 else GL, piv)
    rider(f"{tag} rider", b, (0, 0.4, BS + sh))
    def pos(u, f):
        return (bx + 0.6 * math.sin(f * 0.04), 26 * u, 6.0 * smooth(ramp(f, 26, 96)) + 0.1 * math.sin(f * 0.1))
    fly(root, pos, pitch_k=0.0)
    for f in range(1, FRAME_END + 1):
        br = 0.5 + 0.5 * math.sin(2 * math.pi * f / 40)
        for sl, yc, k in slices:
            key(sl, f, loc=(0, yc + (k - 2) * 0.035 * br, 0))
    return 2, 80


def build_F3c2(tag, root, bx):
    """Twisting strata: three thick slabs, 0.2 off the skin, that breathe by TWISTING (top and bottom turn up to 4
    degrees opposite ways round the still middle), all 12 edges of each glowing; brow on the top slab. Rises 5, turns
    right round on the spot, and heads back the way it came."""
    T = TEX["br1"]
    b, tents = real_ghast(tag, root)
    sh = 0.2; n = 3; hs = (BS + 2 * sh) / n
    slabs = []
    for k in range(n):
        z0 = -sh + hs * k
        sl = empty(f"{tag} slab {k}", (0, 0, z0 + hs / 2), b)
        edged_box(tag, f"slab {k}", (-BS / 2 - sh, -BS / 2 - sh, -hs / 2 + 0.025), (BS / 2 + sh, BS / 2 + sh, hs / 2 - 0.025), T, sl, e=0.045)
        slabs.append((sl, k))
    top, mid = slabs[2][0], slabs[1][0]
    fy = BS / 2 + sh
    brow = empty(f"{tag} brow", (0, fy, -hs / 2 + 0.05), top)
    box(f"{tag} brow ledge", (-BS / 2 + 0.2, 0, -0.1), (BS / 2 - 0.2, 0.5, 0.14), T, brow)
    box(f"{tag} brow glow", (-BS / 2 + 0.2, 0.48, -0.12), (BS / 2 - 0.2, 0.52, 0.0), RM, brow)
    zc_mid = -sh + hs * 1.5
    for s in (-1, 1):
        box(f"{tag} eye {s}", (s * 3 * G - 1.3 * G, fy, 7.6 * G - zc_mid), (s * 3 * G + 1.3 * G, fy + 0.05, 10.4 * G - zc_mid), W, mid)
    box(f"{tag} mouth", (-2.4 * G, fy, 3.6 * G - zc_mid), (2.4 * G, fy + 0.05, 5.4 * G - zc_mid), RM, mid)
    for piv, L, i in tents:
        m_ = max(2, int(L / 0.75))
        for k in range(m_):
            z1 = -sh - (L - sh + 0.06) * k / m_; z2 = -sh - (L - sh + 0.06) * (k + 1) / m_ + 0.08
            box(f"{tag} sleeve {i} {k}", (-G - 0.12, -G - 0.12, z2), (G + 0.12, G + 0.12, z1), T if k % 2 == 0 else GL, piv)
    rider(f"{tag} rider", b, (0, 0.4, BS + sh))
    def yaw(u, f):
        return R(180) * smooth(ramp(f, 52, 92))
    def pos(u, f):
        fwd = 9.0 * smooth(ramp(f, 24, 52))
        back = 7.0 * smooth(ramp(f, 90, FRAME_END))
        return (bx + 3.0 * math.sin(math.pi * ramp(f, 52, 92)), fwd - back, 5.0 * smooth(ramp(f, 22, 60)) + 0.1 * math.sin(f * 0.1))
    fly2(root, pos, bank_k=1.5, yaw_fn=yaw)
    for f in range(1, FRAME_END + 1):
        tw = R(4) * math.sin(2 * math.pi * f / 36)
        key(slabs[0][0], f, rot=(0, 0, -tw)); key(slabs[2][0], f, rot=(0, 0, tw))
    return 2, 72


def build_F3c3(tag, root, bx):
    """Stepped skirt: four slabs that widen going DOWN (0.2 to 0.56 off the skin), a ziggurat upside down, all 12 edges
    of each glowing; the sleeves are stacks of square brick rings with gaps. The slabs breathe apart. Rises 7 through a
    wide banked S."""
    T = TEX["br1"]
    b, tents = real_ghast(tag, root)
    n = 4; hs = (BS + 0.4) / n
    slabs = []
    for k in range(n):
        off = 0.56 - 0.12 * k
        z0 = -0.2 + hs * k
        sl = empty(f"{tag} tier {k}", (0, 0, z0 + hs / 2), b)
        edged_box(tag, f"tier {k}", (-BS / 2 - off, -BS / 2 - off, -hs / 2 + 0.02), (BS / 2 + off, BS / 2 + off, hs / 2 - 0.02), T, sl, e=0.04)
        slabs.append((sl, z0 + hs / 2, k))
    fy = BS / 2 + 0.56 - 0.12 * 2
    brow = empty(f"{tag} brow", (0, BS / 2 + 0.2, 10.9 * G), b)
    box(f"{tag} brow ledge", (-BS / 2 + 0.2, 0, -0.1), (BS / 2 - 0.2, 0.45, 0.14), T, brow)
    box(f"{tag} brow glow", (-BS / 2 + 0.2, 0.43, -0.12), (BS / 2 - 0.2, 0.47, 0.0), RM, brow)
    t2, z2c = slabs[2][0], slabs[2][1]; t1, z1c = slabs[1][0], slabs[1][1]
    y2 = BS / 2 + 0.32; y1 = BS / 2 + 0.44
    for s in (-1, 1):                                   # eyes on tier 2's face, mouth on tier 1's (it sticks out more)
        box(f"{tag} eye {s}", (s * 3 * G - 1.3 * G, y2, 2.3 - z2c), (s * 3 * G + 1.3 * G, y2 + 0.05, 10.4 * G - z2c), W, t2)
    box(f"{tag} mouth", (-2.4 * G, y1, 1.15 - z1c), (2.4 * G, y1 + 0.05, 1.6 - z1c), RM, t1)
    for piv, L, i in tents:
        m_ = max(3, int(L / 0.45))
        for k in range(m_):
            z1 = -0.25 - (L - 0.25) * k / m_
            square_ring(f"{tag} brick ring {i} {k}", G + 0.16, 0.12, z1 - 0.28, z1, T if k % 2 == 0 else RM, piv)
    rider(f"{tag} rider", b, (0, 0.4, BS + 0.2))
    def pos(u, f):
        x = bx + 7.0 * math.sin(2 * math.pi * ramp(f, 30, FRAME_END)) * 0.8
        return (x, 22 * ramp(f, 24, FRAME_END), 7.0 * smooth(ramp(f, 22, 100)) + 0.1 * math.sin(f * 0.1))
    fly(root, pos, pitch_k=0.0, bank_k=4.0)
    for f in range(1, FRAME_END + 1):
        br = 0.5 + 0.5 * math.sin(2 * math.pi * f / 40)
        for sl, zc, k in slabs:
            key(sl, f, loc=(0, 0, zc + (k - 1.5) * 0.05 * br))
    return 2, 85


# ================================================================== layout: six rows, far apart in X
TAKES = [("F1a1", "winged horse: fan wings, spring take-off", build_F1a1, 0.0),
         ("F1a2", "winged horse: four wings, runs up the air", build_F1a2, 18.0),
         ("F1a3", "winged horse: Z-fold wings, one stroke, soar", build_F1a3, 36.0),
         ("F1c1", "comet horse: comet tail, roll", build_F1c1, 70.0),
         ("F1c2", "comet horse: ring slices, helix climb", build_F1c2, 88.0),
         ("F1c3", "comet horse: one-piece hull, bounds", build_F1c3, 106.0),
         ("F2c1", "blocky glider: voxel-grid wings, thermal", build_F2c1, 140.0),
         ("F2c2", "blocky glider: folding panels, pillar launch", build_F2c2, 158.0),
         ("F2c3", "blocky glider: stepped delta, hover, wingover", build_F2c3, 180.0),
         ("F3a1", "ghast shell: rounded cube, breathing", build_F3a1, 215.0),
         ("F3a2", "ghast shell: banded double shell", build_F3a2, 245.0),
         ("F3a3", "ghast shell: chamfered, twisted sleeves", build_F3a3, 275.0),
         ("F3b1", "ghast cage: round rods, coil springs", build_F3b1, 320.0),
         ("F3b2", "ghast cage: diamond lattice, zigzag", build_F3b2, 350.0),
         ("F3b3", "ghast cage: gimbal ring, lantern tubes", build_F3b3, 380.0),
         ("F3c1", "ghast strata: front-to-back slices", build_F3c1, 425.0),
         ("F3c2", "ghast strata: twisting slabs, turnabout", build_F3c2, 455.0),
         ("F3c3", "ghast strata: stepped skirt, banked S", build_F3c3, 485.0)]
MODEL_AT = {}
for tk, name, fn, bx in TAKES:
    tag = f"FM3 {tk}"
    big = tk.startswith("F3")
    box(f"{tag} floor", (bx - (13 if big else 8), -8, -0.02), (bx + (13 if big else 8), 40, 0), FLOOR)
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
    label(f"{tk}  {name}", (bx, -3.0, 9.5 if big else 3.4), LBL, 0.5 if big else 0.28, rot=(R(90), 0, 0))
    print(tk, "built", flush=True)
for grp, cx, big in (("F1a", 18.0, False), ("F1c", 88.0, False), ("F2c", 158.0, False),
                     ("F3a", 245.0, True), ("F3b", 350.0, True), ("F3c", 455.0, True)):
    if big:
        cam(f"Cam row {grp}", (cx, -50.0, 16.0), (cx, 6, 5.0), 30)
    else:
        cam(f"Cam row {grp}", (cx, -26.0, 8.0), (cx, 8, 2.5), 30)
print("MODEL_AT", json.dumps(MODEL_AT))
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam F1a1", 1, (0.35, 0.45, 0.6), 3.0

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
