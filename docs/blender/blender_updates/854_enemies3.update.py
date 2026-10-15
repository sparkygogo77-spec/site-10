# Pass 854: enemies3, "Enemies: scarier E1 round" (rings/suits chat, 2026-10-15, range 800-899). Follows 845.
# J rated all three 845 takes IMPROVE (ratings 19:14-19:21), his words:
#   E1a Veil Wisp:     "new variations, the veil should hide a light that timedly brights up with reveal"
#   E1b Mask Swarm:    "new designs, not scary enough"
#   E1c Stilt Stalker: "scarier, more complex, and animations for movement, no"
# So: three new siblings of each, nine takes, each built a different way. Scary = silhouette, wrong proportions,
# sudden motion after stillness, darkness with one hard light (the world is near black; each creature carries its own
# yellow light). Fear corps yellow for the creatures; the player's construct shot stays green. Original designs only.
#   E1a1 Curtain Veil: 16 long strips hang from a rail round a caged heart-light. The strips slide apart round the rail
#        like a drawn curtain, front first; the light is dim behind them and brightens exactly as the gap widens, flaring
#        as the front clears; the heart swings out on its chain at the player, who throws an arm over his eyes.
#   E1a2 Bell Veil: seven square cloth bands stacked under a wide brim, three lights in a column inside. The bands
#        telescope up bottom first and each light comes on as its band lifts (a light that climbs); long folded arms
#        unfold and reach with three thin fingers as it glides in; the player freezes and shivers.
#   E1a3 Scale Cocoon: five rings of overlapping scales wrapped round one eye. Ring by ring, top to bottom, the scales
#        snap open and the light steps up with each ring; the eye, looking away, snaps round and a hard spot gaze lifts
#        the player off his feet; the scales rattle. Death: the scales come loose and flutter down.
#   E1b1 Mask Totem: seven long bone masks stacked on a thin spine, 3 m tall, all facing away. One by one they creak
#        half round in the idle; then all snap to face the player at once and the spine whips over so the crowned top
#        mask hangs in his face; he falls back on the floor. Lit from below by one uplight.
#   E1b2 Stalk Crowd: nine round masks on thin two-part stalks rising from a black puddle, idly facing every way; the
#        puddle slides under the player, the masks snap to him together and the stalks stretch to ring his head, jaws
#        dropping open and chattering over a glowing mouth.
#   E1b3 Mosaic Face: one giant blank face 2.5 m tall built from ~45 small tiles, two deep eye-lights. Its head jerks
#        sideways; the tiles flip over from the middle out, each one a small face with lit eyes; then it bursts into a
#        turning cage of faces round the player's head, all staring in.
#   E1c1 Creeping Stalker: very long stilt legs with knees far above its back, a telescoping neck and a caged head with
#        a searchlight and a fanged jaw. It stalks in across the bay (real planted-foot steps), step-step-freeze, the head
#        sweeping the floor and snapping sideways at each stop; then rears, slams both front legs down either side of
#        the player and drives its head into his face, jaw chattering.
#   E1c2 Skitter Stalker: a flat body slung low between six stilt legs whose knees stand far above it, one eye-light,
#        mandibles, feelers. It crosses the bay in sudden sideways bursts (fast leg cycling), dead still between them,
#        always facing the player; then coils, pounces and lands astride him, its six legs caging him in.
#   E1c3 Unfolding Crawler: drags itself in low along the floor in lurches, folded legs peaking above its back like tent
#        poles; at the player it unfolds in six ticks to 3 m tall and its long neck hangs the head down upside down in
#        front of his face, twitching.
# Same clock for all (20 ticks a second): idle/approach 1-40, attack 41-80 at a player stand-in, death 81-130 (the
# player's green construct shot lands at 85; the light gutters, it falls apart). Legs in E1c use two-bone IK with
# planted feet, so they walk instead of stepping on the spot. Rows are 24 m apart (E1a, E1b, E1c), bays 9 m apart.
# Cameras "Cam <take>", "Cam <take> close", "Cam row E1a/E1b/E1c". Builds LanternLive\combat\enemies3.blend.
SCENE_NAME = "Enemies E1 scarier"
OUT_REL = "combat/enemies3.blend"
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



# ================================================================== pass 854: the nine new takes
FRAME_END = 130
BAY = 9.0                                      # bays along X in a row
ROW = 24.0                                     # rows far apart along Y (E1a row, E1b row, E1c row)
IDLE, ATK, DIE = 1, 41, 81
HIT = DIE + 4                                  # the player's construct shot lands
FLOOR = mat("EN floor", (0.13, 0.14, 0.13), rough=0.9)
LBL = mat("EN label", (0.3, 1.0, 0.45), emit=2.0)
SHADE = mat("EN shade", (0.025, 0.02, 0.032), rough=0.5)
PLATE = mat("EN dark plate", (0.075, 0.06, 0.09), rough=0.3, metal=0.4)
VOID = mat("EN void", (0.0, 0.0, 0.0), rough=1.0)
VEIL = mat("EN veil", (0.03, 0.026, 0.04), alpha=0.9, rough=0.7)
BONE = mat("EN mask bone", (0.46, 0.42, 0.34), rough=0.55)
PUD = mat("EN fear puddle", (0.012, 0.01, 0.016), rough=0.08)
FEAR = (1.0, 0.7, 0.03)                        # the fear corps' yellow (saturated, never white)
LCOL = (1.0, 0.68, 0.1)                        # the colour of the creature's one hard light
rng = np.random.default_rng(854)
CM = cmats("EN", "green")                      # the player's construct shot stays green
FLICK = [1.0, 0.0, 1.3, 0.0, 0.0, 0.7, 0.0, 0.35, 0.0, 0.0]


def fmat(name, e=1.0):
    return mat(name, FEAR, emit=e)


def death_mul(f):
    """The light gutters after the construct shot: a few flickers, then out."""
    if f < HIT:
        return 1.0
    i = f - HIT
    return FLICK[i] if i < len(FLICK) else 0.0


def plight(name, parent, loc, kind="POINT", size=0.02, spot=None, rot=None):
    ld = bpy.data.lights.new(name, kind); ld.color = LCOL; ld.shadow_soft_size = size
    if kind == "SPOT":
        ld.spot_size = R(spot or 30); ld.spot_blend = 0.12
    o = link(bpy.data.objects.new(name, ld)); o.location = loc
    if parent is not None:
        o.parent = parent
    if rot is not None:
        o.rotation_euler = rot
    return o


def drive(fn, emits=(), lights=(), frames=None):
    """Key a light level per frame: fn(f) -> level (1 = full), times each material's / light's scale; the death
    flicker is applied on top."""
    for f in (frames or range(1, HIT + 12)):
        v = max(0.0, fn(f)) * death_mul(f)
        for m, s in emits:
            inp = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
            inp.default_value = v * s; inp.keyframe_insert("default_value", frame=f)
        for lo, s in lights:
            lo.data.energy = v * s; lo.data.keyframe_insert("energy", frame=f)


def cage(tag, c0, c1, bt, m, parent):
    """A bar on every edge of a box (all twelve)."""
    c0, c1 = Vector(c0), Vector(c1)
    for ax in range(3):
        o1, o2 = [i for i in range(3) if i != ax]
        for u in (c0[o1], c1[o1]):
            for v in (c0[o2], c1[o2]):
                a_ = [0, 0, 0]; b_ = [0, 0, 0]
                a_[ax], b_[ax] = c0[ax], c1[ax]
                a_[o1], b_[o1] = u - bt, u + bt
                a_[o2], b_[o2] = v - bt, v + bt
                box(f"{tag} bar", a_, b_, m, parent)


def lerp(a, b, t):
    return a + (b - a) * t


def wp(f, pts, ease=smooth):
    """Waypoints [(frame, value)], eased between (values: float or Vector)."""
    if f <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f <= f1:
            return lerp(v0, v1, ease((f - f0) / max(1e-6, f1 - f0)))
    return pts[-1][1]


def aim_euler(d, prev=None, track="-Z"):
    q = Vector(d).to_track_quat(track, "Y")
    return q.to_euler("XYZ", prev) if prev is not None else q.to_euler("XYZ")


REST = dict(arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0), head=(0, 0, 0), leg_r=(0, 0, 0), leg_l=(0, 0, 0),
            shin_r=(0, 0, 0), shin_l=(0, 0, 0))
CROUCH = dict(arm_r=(165, 0, -35), arm_l=(165, 0, 35), body=(20, 0, 0), head=(25, 0, 0), leg_r=(55, 0, 0),
              leg_l=(55, 0, 0), shin_r=(-105, 0, 0), shin_l=(-105, 0, 0))


def ppose(prig, f, bx, py, dy=0.0, dz=0.0, dx=0.0, **kw):
    d = dict(REST); d.update(kw)
    pose(prig, f, root_loc=(bx + dx, py + dy, dz), **d)


def bay(tk, name, bx, by):
    tag = f"EN {tk}"
    box(f"{tag} floor", (bx - 4.3, by - 4.6, -0.02), (bx + 4.3, by + 9.6, 0), FLOOR)
    prig, _ = target(tag + " player", (bx, by - 1.8, 0), face=0.0)     # the player faces +Y toward the enemy
    label(f"{tk}  {name}", (bx, by + 9.3, 3.7), LBL, 0.28)
    return tag, prig


def finish(tag, prig, dst_fn):
    """The player raises the ring arm and fires the construct shot that kills it (lands at HIT)."""
    at(HIT - 8)
    pose(prig, HIT - 8, arm_r=tuple(math.degrees(a) for a in prig["arm_r"].rotation_euler))
    pose(prig, HIT - 6, arm_r=(90, 0, 0)); pose(prig, HIT + 6, arm_r=(90, 0, 0)); pose(prig, HIT + 20, arm_r=(10, 0, 0))
    at(HIT - 6)
    src = tuple(prig["ring_pt"].matrix_world.translation)
    at(HIT)
    shot(tag, src, tuple(dst_fn()), HIT)


def crumble(objs, f0, per=4, top_down=True, speed=0.04):
    at(f0)
    objs = sorted(objs, key=lambda o: (-1 if top_down else 1) * o.matrix_world.translation.z)
    for k, o in enumerate(objs):
        shatter([o], f0 + k // per, PLATE if "plate" in o.name or "bone" in o.name else SHADE, rng, "EN", n=1, speed=speed)


def enemy_root(tag, bx, by, dy=2.5):
    er = empty(f"{tag} enemy", (bx, by + dy, 0)); er.rotation_euler = (0, 0, math.pi)   # local +Y = toward the player
    return er


# ------------------------------------------------------------------ E1a family: the veil hides a light
def hood_spikes(tag, hd, n, r, z, m=PLATE, lean=-25, ln=0.22):
    for k in range(n):
        a = 2 * math.pi * k / n
        sp = empty(f"{tag} crown spike {k}", (r * math.cos(a), r * math.sin(a), z), hd)
        sp.rotation_euler = (0, R(lean), a)
        box(f"{tag} crown spike box {k}", (-0.022, -0.022, 0), (0.022, 0.022, ln), m, sp)


def take_a1(tag, prig, bx, by):
    """Curtain Veil: 16 long strips on a rail; they slide apart around the rail like a drawn curtain, front first."""
    py = by - 1.8
    er = enemy_root(tag, bx, by)
    body = empty(f"{tag} body", (0, 0, 1.75), er)
    hd = empty(f"{tag} hood", (0, 0, 0), body)
    box(f"{tag} hood low", (-0.3, -0.3, 0), (0.3, 0.3, 0.32), SHADE, hd)
    box(f"{tag} hood mid", (-0.22, -0.24, 0.32), (0.22, 0.2, 0.58), SHADE, hd)
    box(f"{tag} hood top", (-0.12, -0.2, 0.58), (0.12, 0.06, 0.8), SHADE, hd)
    box(f"{tag} hood tip plate", (-0.05, -0.24, 0.8), (0.05, -0.1, 1.04), PLATE, hd)
    box(f"{tag} face hole", (-0.19, 0.29, 0.03), (0.19, 0.305, 0.27), VOID, hd)
    hood_spikes(tag, hd, 6, 0.3, 0.26)
    torus(f"{tag} rail plate", 0.45, 0.025, PLATE, loc=(0, 0, -0.02), parent=body)
    E = fmat(f"{tag} heart", 0.5)
    chain = empty(f"{tag} chain", (0, 0, 0), body)
    box(f"{tag} chain plate", (-0.012, -0.012, -0.62), (0.012, 0.012, 0), PLATE, chain)
    heart = empty(f"{tag} heart", (0, 0, -0.62), chain)
    cage(f"{tag} heart cage plate", (-0.13, -0.13, -0.28), (0.13, 0.13, 0.0), 0.018, PLATE, heart)
    box(f"{tag} heart core", (-0.07, -0.07, -0.21), (0.07, 0.07, -0.07), E, heart)
    lt = plight(f"{tag} heart light", heart, (0, 0, -0.14))
    NS = 16; strips = []
    for k in range(NS):
        d0 = -math.pi + (k + 0.5) * 2 * math.pi / NS          # angle from the front (0 = toward the player)
        pv = empty(f"{tag} strip {k}", (0, 0, 0), body)
        box(f"{tag} strip cloth {k}", (-0.105, -0.012, -1.3), (0.105, 0.012, 0), VEIL, pv)
        box(f"{tag} strip hem plate {k}", (-0.04, -0.01, -1.48), (0.04, 0.01, -1.3), PLATE, pv)
        strips.append((pv, d0, k))

    def rev(f):
        return smooth((f - ATK - 2) / 12) * (1 - smooth((f - ATK - 30) / 6))

    def level(f):
        r = rev(f); v = (0.14 + 0.05 * math.sin(f * 0.6)) * (1 - r) + r
        if ATK + 13 <= f <= ATK + 30:
            v += 0.7 * math.exp(-(f - ATK - 13) / 3.5)          # the flare as the curtain clears
        return v
    drive(level, [(E, 4.0)], [(lt, 160.0)])
    for f in range(1, HIT + 3):
        t = f / 20.0
        lunge = smooth((f - ATK - 14) / 5) * (1 - smooth((f - ATK - 30) / 6))
        key(body, f, loc=(0, 0.6 * lunge, 1.75 + 0.06 * math.sin(t * 2.0)))
        key(hd, f, rot=(R(-6 * lunge), 0, R(5 * math.sin(t * 0.8) * (1 - lunge))))
        key(chain, f, rot=(R(55 * lunge + 3 * math.sin(t * 1.7)), 0, 0))
        for pv, d0, k in strips:
            ad = abs(d0)
            o = smooth((f - ATK - 2 - (ad / math.pi) * 8) / 5) * (1 - smooth((f - ATK - 30 - (1 - ad / math.pi) * 3) / 5))
            d = math.copysign(ad + (math.pi - ad) * 0.8 * o, d0)
            a = math.pi / 2 + d
            key(pv, f, loc=(0.45 * math.cos(a), 0.45 * math.sin(a), -0.02),
                rot=(R(-5 + 3 * math.sin(t * 2.4 + k) - 88 * o * (1 - o)), 0, a + math.pi / 2))
    # the player throws an arm over his eyes at the flare and backs off, knees buckling
    ppose(prig, ATK + 12, bx, py)
    ppose(prig, ATK + 15, bx, py, dy=-0.2, arm_l=(150, 0, -25), arm_r=(110, 0, 30), head=(-20, 0, 0), body=(-8, 0, 0))
    for i, f in enumerate(range(ATK + 17, ATK + 31, 2)):
        ppose(prig, f, bx, py, dy=-0.2 - 0.05 * i, dz=-0.02 * i, arm_l=(150, 0, -25), arm_r=(110, 0, 30), head=(-20, 0, 0),
              body=(-8, 0, 5 if i % 2 else -5), leg_r=(3 * i, 0, 0), shin_r=(-6 * i, 0, 0))
    ppose(prig, ATK + 36, bx, py, dy=-0.55)
    # death: the light gutters, the heart bursts, the strips drop, it sinks and falls apart
    for pv, d0, k in strips:
        at(HIT + 2)
        key(pv, HIT + 3 + k % 4, loc=tuple(pv.location), rot=tuple(pv.rotation_euler))
        key(pv, HIT + 10 + k % 4, loc=(pv.location.x * 1.4, pv.location.y * 1.4, -0.35),
            rot=(R(-70), 0, pv.rotation_euler.z))
    key(body, HIT + 4, loc=(0, 0, 1.75)); key(body, HIT + 20, loc=(0, 0, 1.0))
    at(HIT + 8)
    shatter(meshes(heart), HIT + 8, E, rng, tag, n=4, speed=0.07)
    crumble([o for o in meshes(er) if o not in meshes(heart)], HIT + 22)
    finish(tag, prig, lambda: body.matrix_world.translation)


def take_a2(tag, prig, bx, by):
    """Bell Veil: a stack of seven square bands under a wide brim; they telescope up bottom first, and three lights in
    a column come on one by one as their band lifts; long folded arms inside unfold and reach."""
    py = by - 1.8
    er = enemy_root(tag, bx, by)
    BZ = 2.05
    body = empty(f"{tag} body", (0, 0, BZ), er)
    box(f"{tag} brim plate", (-0.58, -0.58, 0), (0.58, 0.58, 0.05), PLATE, body)
    box(f"{tag} crown", (-0.22, -0.22, 0.05), (0.22, 0.22, 0.36), SHADE, body)
    box(f"{tag} peak", (-0.09, -0.16, 0.36), (0.09, 0.04, 0.68), SHADE, body)
    bands = []
    for i in range(7):
        w = 0.3 + 0.04 * i; z0 = -0.03 - i * 0.16; th = 0.03
        rg = empty(f"{tag} band {i}", (0, 0, z0), body)
        for a_, b_ in (((-w, w - th, -0.2), (w, w, 0)), ((-w, -w, -0.2), (w, -w + th, 0)),
                       ((-w, -w, -0.2), (-w + th, w, 0)), ((w - th, -w, -0.2), (w, w, 0))):
            box(f"{tag} band cloth {i}", a_, b_, VEIL, rg)
        box(f"{tag} band hem plate {i}", (-w - 0.005, w - 0.035, -0.2), (w + 0.005, w + 0.005, -0.17), PLATE, rg)
        bands.append((rg, z0, i))
    for k in range(6):
        a = 2 * math.pi * k / 6
        box(f"{tag} rib plate {k}", (0.17 * math.cos(a) - 0.015, 0.17 * math.sin(a) - 0.015, -1.15),
            (0.17 * math.cos(a) + 0.015, 0.17 * math.sin(a) + 0.015, -0.12), PLATE, body)
    cubes = []
    for j, z in enumerate((-0.3, -0.62, -0.94)):
        Ej = fmat(f"{tag} light {j}", 0.4)
        cubes.append((box(f"{tag} light cube {j}", (-0.065, -0.065, z - 0.065), (0.065, 0.065, z + 0.065), Ej, body), Ej, 2 * j + 1))
    lt = plight(f"{tag} column light", body, (0, 0, -0.62))
    arms = []
    for sx in (1, -1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 0.2, 0.05, -0.2), body)
        box(f"{tag} upper arm {sx}", (-0.035, -0.035, -0.78), (0.035, 0.035, 0), SHADE, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.78), sh)
        box(f"{tag} forearm {sx}", (-0.03, -0.03, -0.75), (0.03, 0.03, 0), SHADE, el)
        hand = empty(f"{tag} hand {sx}", (0, 0, -0.75), el)
        fingers = []
        for q in range(3):
            fg = empty(f"{tag} finger {sx} {q}", ((q - 1) * 0.03, 0, 0), hand)
            box(f"{tag} finger plate {sx} {q}", (-0.012, -0.012, -0.4), (0.012, 0.012, 0), PLATE, fg)
            fingers.append(fg)
        arms.append((sh, el, fingers, sx))

    def band_o(i, f):
        return smooth((f - ATK - 2 - (6 - i) * 1.4) / 3.5) * (1 - smooth((f - ATK - 30 - i * 0.8) / 4))

    for f in range(1, HIT + 3):
        t = f / 20.0
        glide = smooth((f - ATK - 13) / 5) * (1 - smooth((f - ATK - 30) / 6))
        key(body, f, loc=(0, 1.9 * glide, BZ + 0.05 * math.sin(t * 1.8) - 0.1 * glide), rot=(0, 0, R(3 * math.sin(t * 0.7))))
        for rg, z0, i in bands:
            o = band_o(i, f)
            key(rg, f, loc=(0, 0, lerp(z0, -0.02 - i * 0.012, o) + 0.01 * math.sin(t * 3 + i) * (1 - o)))
        reach = smooth((f - ATK - 14) / 4) * (1 - smooth((f - ATK - 30) / 6))
        for sh, el, fingers, sx in arms:
            key(sh, f, rot=(R(82 * reach), 0, R(sx * 13 * reach)))
            key(el, f, rot=(R(-160 * (1 - reach) + 4 * reach), 0, 0))
            for q, fg in enumerate(fingers):
                key(fg, f, rot=(R(10 * reach), R((q - 1) * 28 * reach), 0))
    for cb, Ej, ri in cubes:
        def lv(f, ri=ri):
            o = band_o(ri, f)
            v = (0.1 + 0.03 * math.sin(f * 0.7 + ri)) * (1 - o) + o
            f_open = ATK + 2 + (6 - ri) * 1.4 + 3.5
            if f_open <= f <= ATK + 30:
                v += 0.8 * math.exp(-(f - f_open) / 3)
            return v
        drive(lv, [(Ej, 3.6)])
    drive(lambda f: sum(band_o(ri, f) for _, _, ri in cubes) / 3 + 0.08, [], [(lt, 170.0)])
    # the player freezes as the hands come for him: arms half up, shivering, sliding back
    ppose(prig, ATK + 14, bx, py)
    ppose(prig, ATK + 18, bx, py, arm_r=(45, 0, 15), arm_l=(45, 0, -15), head=(-10, 0, 0), body=(-4, 0, 0))
    for i, f in enumerate(range(ATK + 19, ATK + 32, 2)):
        ppose(prig, f, bx, py, dy=-0.06 * i, arm_r=(45, 0, 15), arm_l=(45, 0, -15), head=(-10, 0, 0),
              body=(-6 - i * 0.6, 0, 4 if i % 2 else -4))
    ppose(prig, ATK + 36, bx, py, dy=-0.45)
    # death: the lights pop bottom up, the bands drop and stack on the floor, the arms fall limp
    for k, (cb, Ej, ri) in enumerate(reversed(cubes)):
        at(HIT + 6 + 3 * k)
        shatter([cb], HIT + 6 + 3 * k, Ej, rng, tag, n=4, speed=0.06)
    for rg, z0, i in bands:
        at(HIT + 2)
        key(rg, HIT + 8 + (6 - i), loc=tuple(rg.location))
        key(rg, HIT + 13 + (6 - i), loc=(0, 0, -BZ + 0.2 + (6 - i) * 0.03))
    for sh, el, fingers, sx in arms:
        key(sh, HIT + 6, rot=(0, 0, 0)); key(el, HIT + 6, rot=(0, 0, 0))
    crumble([o for o in meshes(er) if "light cube" not in o.name], HIT + 24)
    finish(tag, prig, lambda: body.matrix_world.translation + Vector((0, 0, -0.5)))


def take_a3(tag, prig, bx, by):
    """Scale Cocoon: five rings of overlapping scales wrapped round one eye-light; ring by ring, top to bottom, the
    scales snap open, and the light steps up with each ring; then the eye snaps round and pins the player."""
    py = by - 1.8
    er = enemy_root(tag, bx, by)
    body = empty(f"{tag} body", (0, 0, 1.7), er)
    hd = empty(f"{tag} hood", (0, 0, 0.0), body); hd.rotation_euler = (0, R(14), 0)
    box(f"{tag} hood low", (-0.2, -0.2, 0), (0.2, 0.2, 0.28), SHADE, hd)
    box(f"{tag} hood top", (-0.12, -0.16, 0.28), (0.12, 0.08, 0.46), SHADE, hd)
    hood_spikes(tag, hd, 3, 0.16, 0.3, lean=-40, ln=0.3)
    E = fmat(f"{tag} eye", 0.4)
    eye = empty(f"{tag} eye", (0, 0, -0.55), body)
    ball(f"{tag} eye ball", 0.17, E, parent=eye, seg=12)
    box(f"{tag} pupil", (-0.025, 0.155, -0.12), (0.025, 0.18, 0.12), VOID, eye)
    lt = plight(f"{tag} eye glow", body, (0, 0, -0.55))
    sp = plight(f"{tag} gaze light", eye, (0, 0.2, 0), kind="SPOT", size=0.01, spot=16, rot=(R(90), 0, 0))
    RHO = [0.22, 0.31, 0.35, 0.32, 0.22]; TILT = [-30, -10, 4, 20, 38]
    plates = []
    for r in range(5):
        for k in range(8):
            a = 2 * math.pi * k / 8 + (r % 2) * math.pi / 8
            pv = empty(f"{tag} scale {r} {k}", (RHO[r] * math.cos(a), RHO[r] * math.sin(a), -0.02 - r * 0.24), body)
            box(f"{tag} scale cloth {r} {k}", (-0.15, -0.016, -0.32), (0.15, 0.016, 0), VEIL, pv)
            box(f"{tag} scale edge plate {r} {k}", (-0.09, -0.02, -0.34), (0.09, 0.02, -0.3), PLATE, pv)
            plates.append((pv, a, r, k))

    def flip(r, f):
        return min(1.0, max(0.0, (f - (ATK + 3 + 3 * r)) / 2)) * (1 - smooth((f - ATK - 31 - r) / 4))

    def level(f):
        n = sum(flip(r, f) for r in range(5))
        v = 0.12 + 0.05 * math.sin(f * 0.5) + 0.88 * n / 5
        if ATK + 17 <= f <= ATK + 31:
            v += 0.7 * math.exp(-(f - ATK - 17) / 3)
        return v
    drive(level, [(E, 3.8)], [(lt, 120.0)])
    drive(lambda f: smooth((f - ATK - 19) / 2) * (1 - smooth((f - ATK - 31) / 4)), [], [(sp, 1400.0)])
    for f in range(1, HIT + 3):
        t = f / 20.0
        key(body, f, loc=(0, 0, 1.7 + 0.07 * math.sin(t * 1.9)))
        for pv, a, r, k in plates:
            o = flip(r, f)
            rattle = 9 * math.sin(f * 2.7 + k * 1.3 + r) if ATK + 19 <= f <= ATK + 30 else 0
            key(pv, f, rot=(R(lerp(TILT[r] + 2 * math.sin(t * 2 + r), -150, o) + rattle), 0, a + math.pi / 2))
        snap = smooth((f - ATK - 19) / 2)
        back = smooth((f - ATK - 31) / 5)
        away = R(150 + 30 * math.sin(t * 0.6))
        yaw = lerp(lerp(away, 0, snap), away, back)
        key(eye, f, rot=(R(lerp(-15, 7, snap)), 0, yaw))
    # pinned in the gaze: lifted off the floor, arms forced out, shaking
    ppose(prig, ATK + 19, bx, py)
    for i, f in enumerate(range(ATK + 21, ATK + 32, 2)):
        ppose(prig, f, bx, py, dz=0.25, dx=0.03 if i % 2 else -0.03, arm_r=(10, -75, 0), arm_l=(10, 75, 0),
              head=(18, 0, 0), leg_r=(-8, 0, 0), leg_l=(8, 0, 0), shin_r=(-20, 0, 0), shin_l=(-25, 0, 0))
    ppose(prig, ATK + 33, bx, py, dz=0.0, **dict(CROUCH, arm_r=(40, 0, 10), arm_l=(40, 0, -10)))
    ppose(prig, ATK + 36, bx, py)
    # death: the eye bursts, the scales come loose and flutter to the floor, the rest crumbles
    at(HIT + 7)
    shatter(meshes(eye), HIT + 7, E, rng, tag, n=5, speed=0.08)
    for pv, a, r, k in plates:
        at(HIT + 2)
        f0 = HIT + 3 + 2 * r + k % 3; p0 = Vector(pv.location); e0 = Vector(pv.rotation_euler)
        out = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.3, 0.7)
        key(pv, f0, loc=tuple(p0), rot=tuple(e0))
        key(pv, f0 + 4, loc=tuple(p0 + out * 0.6 + Vector((0, 0, -0.6 - 0.25 * r))), rot=(R(-40), R(rng.uniform(-40, 40)), e0.z))
        key(pv, f0 + 8, loc=tuple(p0 + out + Vector((0, 0, -1.68 - p0.z))), rot=(R(-88), R(rng.uniform(-10, 10)), e0.z))
    crumble([o for o in meshes(er) if o not in meshes(eye)], HIT + 22)
    finish(tag, prig, lambda: body.matrix_world.translation + Vector((0, 0, -0.5)))


# ------------------------------------------------------------------ E1b family: masks, scarier
def take_b1(tag, prig, bx, by):
    """Mask Totem: seven long masks stacked on a thin spine, 3 m tall, all facing away; one by one they creak half
    round; then all snap to face the player at once and the spine whips over so the top mask hangs in his face."""
    py = by - 1.8
    er = enemy_root(tag, bx, by)
    E = fmat(f"{tag} eyes", 0.3)
    box(f"{tag} base plate", (-0.16, -0.16, 0), (0.16, 0.16, 0.2), PLATE, er)
    N = 7; SEG = 0.43
    joints, mps = [], []
    prev = er
    for i in range(N):
        j = empty(f"{tag} joint {i}", (0, 0, 0.2) if i == 0 else (0, 0, SEG), prev)
        box(f"{tag} spine {i}", (-0.03, -0.03, 0), (0.03, 0.03, SEG), SHADE, j)
        mp = empty(f"{tag} mask {i}", (0, 0, 0.2), j)
        top = i == N - 1
        hw, hh = (0.15, 0.26) if top else (0.12, 0.2)
        box(f"{tag} mask bone {i}", (-hw, -0.02, -hh), (hw, 0.02, hh), BONE, mp)
        box(f"{tag} mask back plate {i}", (-hw + 0.02, -0.05, -hh + 0.02), (hw - 0.02, -0.02, hh - 0.02), PLATE, mp)
        for s in (-1, 1):
            box(f"{tag} mask eye {i} {s}", (s * 0.06 - 0.015, 0.02, 0.0), (s * 0.06 + 0.015, 0.03, 0.13 if top else 0.11), E, mp)
        box(f"{tag} mask mouth {i}", (-0.012, 0.02, -hh + 0.04), (0.012, 0.028, -0.05), VOID, mp)
        if top:
            for q in range(5):
                s_ = empty(f"{tag} top spike {q}", ((q - 2) * 0.06, 0, hh), mp); s_.rotation_euler = (0, R((q - 2) * 14), 0)
                box(f"{tag} top spike plate {q}", (-0.012, -0.012, 0), (0.012, 0.012, 0.18 + 0.06 * (q == 2)), PLATE, s_)
        joints.append(j); mps.append(mp); prev = j
    up = plight(f"{tag} uplight", er, (0, 0.4, 0.08))
    # the bend that hangs the top mask in the player's face: relative joint angles shaped c*w, the base slides s
    W = [0.0, 0.25, 0.45, 0.7, 0.95, 1.15, 1.3]

    def chain(c):
        p = Vector((0, 0, 0.2)); cum = 0; pts = []; cums = []
        for i in range(N):
            cum += -c * W[i]
            d = Vector((0, -math.sin(-cum) * -1, math.cos(cum)))
            d = Vector((0, -math.sin(cum), math.cos(cum)))
            pts.append(p + d * 0.2); cums.append(cum); p = p + d * SEG
        return pts, cums
    best = None
    for ci in range(1, 120):
        c = ci * 0.005
        pts, cums = chain(c)
        s = 4.3 - 0.45 - pts[-1].y
        if 0.4 <= s <= 2.6:
            err = abs(pts[-1].z - 1.72)
            if best is None or err < best[0]:
                best = (err, c, s, cums)
    _, cB, sB, cumsB = best
    print(tag, "bend", round(cB, 3), "slide", round(sB, 2))
    away = [math.pi] * N
    for i, mp in enumerate(mps):
        fk = 5 + int(4.5 * i)
        key(mp, 1, rot=(0, 0, math.pi)); key(mp, fk, rot=(0, 0, math.pi)); key(mp, fk + 5, rot=(0, 0, math.pi - 1.0))
        key(mp, ATK, rot=(0, 0, math.pi - 1.0))
        key(mp, ATK + 2, rot=(0, R(25) if i == N - 1 else 0, 0))         # all snap round at once
        key(mp, ATK + 6, rot=(0, R(25) if i == N - 1 else 0, 0))
        key(mp, ATK + 12, rot=(-cumsB[i], R(40) if i == N - 1 else 0, 0))
        key(mp, ATK + 30, rot=(-cumsB[i], R(40) if i == N - 1 else 0, 0))
        key(mp, ATK + 36, rot=(0, 0, 0))
    for i, j in enumerate(joints):
        rel = -cB * W[i]
        key(j, 1, rot=(0, 0, 0)); key(j, ATK + 6, rot=(0, 0, 0)); key(j, ATK + 12, rot=(rel, 0, 0))
        for q, f in enumerate(range(ATK + 14, ATK + 30, 2)):
            key(j, f, rot=(rel + R(2.5 if (q + i) % 2 else -2.5), R(1.5 if q % 2 else -1.5), 0))
        key(j, ATK + 30, rot=(rel, 0, 0)); key(j, ATK + 36, rot=(0, 0, 0))
    y0 = by + 2.5
    key(er, ATK + 6, loc=(bx, y0, 0)); key(er, ATK + 12, loc=(bx, y0 - sB, 0)); key(er, ATK + 30, loc=(bx, y0 - sB, 0))
    key(er, ATK + 36, loc=(bx, y0, 0))
    drive(lambda f: (0.15 if f < ATK else (1.6 if f < ATK + 4 else (1.0 if f <= ATK + 31 else 0.45))), [(E, 3.2)], [(up, 70.0)])
    # the player flinches, then falls back onto the floor and stares up at it
    ppose(prig, ATK + 2, bx, py)
    ppose(prig, ATK + 5, bx, py, arm_r=(60, 0, 20), arm_l=(60, 0, -20), head=(10, 0, 0))
    sit = dict(dy=-0.25, dz=-0.38, body=(18, 0, 0), head=(30, 0, 0), leg_r=(85, 0, 5), leg_l=(80, 0, -5),
               arm_r=(-35, 0, 15), arm_l=(-35, 0, -15))
    ppose(prig, ATK + 12, bx, py, **sit)
    ppose(prig, ATK + 30, bx, py, **sit)
    ppose(prig, ATK + 36, bx, py, dy=-0.25)
    # death: the eyes go out, the column buckles and falls back, the masks crumble top down
    rnd = [R(rng.uniform(-35, 35)) for _ in range(N)]
    for i, j in enumerate(joints):
        key(j, HIT + 2, rot=(0, 0, 0))
        key(j, HIT + 6 + i, rot=((R(55) if i == 0 else rnd[i]), rnd[(i + 3) % N] * 0.4, 0))
    crumble(meshes(er), HIT + 18, per=3)
    finish(tag, prig, lambda: joints[3].matrix_world.translation)


def take_b2(tag, prig, bx, by):
    """Stalk Crowd: nine round masks on thin stalks rising from a black puddle, idly facing every way; they snap to
    the player together, the stalks stretch 4 m to ring his head and the jaws drop open, chattering."""
    py = by - 1.8
    er = enemy_root(tag, bx, by)
    C = Vector((bx, by + 2.5, 0))
    H = Vector((bx, py, 1.75))
    E = fmat(f"{tag} eyes", 0.3)
    pud = cyl(f"{tag} puddle", 0.95, 0.015, PUD, 24, loc=tuple(C + Vector((0, 0, 0.004))))
    lt = plight(f"{tag} puddle light", None, tuple(C + Vector((0, -0.1, 0.18))))
    NK = 9
    st = []
    for k in range(NK):
        a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.1, 0.6)
        base = C + Vector((rr * math.cos(a), rr * math.sin(a), 0.01))
        h = rng.uniform(0.8, 1.7); phi = rng.uniform(-math.pi, math.pi); scl = rng.uniform(0.85, 1.2)
        s1 = box(f"{tag} stalk a {k}", (-0.025, -0.025, 0), (0.025, 0.025, 1), SHADE)
        s2 = box(f"{tag} stalk b {k}", (-0.02, -0.02, 0), (0.02, 0.02, 1), SHADE)
        m_ = empty(f"{tag} mask {k}", tuple(base)); m_.scale = (scl,) * 3
        box(f"{tag} mask bone {k}", (-0.15, -0.02, -0.05), (0.15, 0.02, 0.2), BONE, m_)
        box(f"{tag} mask cheek bone {k}", (-0.12, -0.02, -0.12), (0.12, 0.02, -0.05), BONE, m_)
        box(f"{tag} mask brow plate {k}", (-0.16, 0.0, 0.13), (0.16, 0.04, 0.16), PLATE, m_)
        for s in (-1, 1):
            box(f"{tag} mask eye {k} {s}", (s * 0.065 - 0.035, 0.02, 0.05), (s * 0.065 + 0.035, 0.03, 0.12), E, m_)
        box(f"{tag} mouth glow {k}", (-0.09, -0.035, -0.15), (0.09, -0.025, -0.02), E, m_)
        jaw = empty(f"{tag} jaw {k}", (0, 0, -0.05), m_)
        box(f"{tag} jaw bone {k}", (-0.11, -0.02, -0.16), (0.11, 0.02, 0), BONE, jaw)
        for q in range(4):
            box(f"{tag} tooth plate {k} {q}", (-0.075 + q * 0.05, 0.0, 0.0), (-0.06 + q * 0.05, 0.02, 0.035), BONE, jaw)
        psi = R(-150 + 300 * k / (NK - 1))
        T = H + Vector((0.62 * math.sin(psi), 0.62 * math.cos(psi), 0.24 * math.sin(3 * k)))
        st.append(dict(base=base, h=h, phi=phi, s1=s1, s2=s2, m=m_, jaw=jaw, T=T, k=k, p1=None, p2=None, pm=None, py_=None))
    pud_y = lambda f: 1.7 * smooth((f - ATK - 4) / 10) * (1 - smooth((f - ATK - 30) / 8))

    def reach(k, f):
        return smooth((f - ATK - 5 - 0.7 * k) / 5) * (1 - smooth((f - ATK - 29 - 0.4 * k) / 6))
    tips = {}
    for f in range(1, HIT + 3):
        t = f / 20.0
        key(pud, f, loc=tuple(C + Vector((0, -pud_y(f), 0.004))), sc=(1 + 0.2 * pud_y(f), 1 + 1.1 * pud_y(f), 1))
        for s in st:
            k = s["k"]
            idle = s["base"] + Vector((0.15 * math.sin(t * 0.9 + k), 0.15 * math.cos(t * 0.7 + k * 1.3), s["h"] + 0.08 * math.sin(t * 1.3 + k)))
            e = reach(k, f)
            jit = Vector((0.03 * math.sin(f * 2.1 + k), 0.03 * math.cos(f * 1.7 + k), 0.03 * math.sin(f * 2.9 + k))) * e
            tip = idle.lerp(s["T"], e) + jit
            tips[(k, f)] = tip
            base = s["base"]
            mid = base.lerp(tip, 0.5) + Vector((0, 0, 0.25 + 0.5 * e))
            for nm, a_, b_ in (("s1", base, mid), ("s2", mid, tip)):
                d = b_ - a_
                pk = "p1" if nm == "s1" else "p2"
                s[pk] = aim_euler(d, s[pk], "Z")
                key(s[nm], f, loc=tuple(a_), rot=tuple(s[pk]), sc=(1, 1, max(0.01, d.length)))
            if f < ATK:
                yaw = s["phi"] + 0.35 * math.sin(t * 0.5 + k)
                rot = (R(-10), 0.0, yaw)
            else:
                rot, s["py_"] = face_rot(tuple(H - tip), s["py_"] if s["py_"] is not None else s["phi"])
            if f >= ATK and s["py_"] is None:
                s["py_"] = rot[2]
            s["pm"] = Euler(rot)
            key(s["m"], f, loc=tuple(tip), rot=rot)
            op = 0
            if ATK + 12 <= f <= ATK + 28:
                op = 45 if (f // 3) % 2 == 0 else 15
            elif ATK + 8 <= f < ATK + 12 or ATK + 28 < f <= ATK + 31:
                op = 10
            key(s["jaw"], f, rot=(R(op), 0, 0))
    drive(lambda f: (0.12 if f < ATK else (1.5 if f < ATK + 4 else (1.0 if f <= ATK + 31 else 0.4))), [(E, 3.4)], [(lt, 90.0)])
    # the player curls up under the ring of faces
    ppose(prig, ATK + 8, bx, py)
    ppose(prig, ATK + 13, bx, py, dz=-0.26, **CROUCH)
    ppose(prig, ATK + 31, bx, py, dz=-0.26, **CROUCH)
    ppose(prig, ATK + 36, bx, py)
    # death: the stalks wilt to the floor, the masks land face down, the puddle shrinks, all crumbles
    for s in st:
        k = s["k"]; f0 = HIT + 3 + k % 4
        tip0 = tips[(k, HIT + 2)]
        out = (tip0 - s["base"]); out.z = 0
        out = out.normalized() if out.length > 1e-3 else Vector((1, 0, 0))
        land = s["base"] + out * rng.uniform(0.7, 1.4); land.z = 0.06
        for i in range(0, 9):
            f = f0 + i; u = i / 8
            tip = tip0.lerp(land, u); tip.z = lerp(tip0.z, 0.06, u * u)
            mid = s["base"].lerp(tip, 0.5) + Vector((0, 0, 0.25 * (1 - u)))
            for nm, a_, b_ in (("s1", s["base"], mid), ("s2", mid, tip)):
                d = b_ - a_; pk = "p1" if nm == "s1" else "p2"
                s[pk] = aim_euler(d, s[pk], "Z")
                key(s[nm], f, loc=tuple(a_), rot=tuple(s[pk]), sc=(1, 1, max(0.01, d.length)))
            key(s["m"], f, loc=tuple(tip), rot=(lerp(s["pm"].x, R(-88), u), s["pm"].y, s["pm"].z))
    key(pud, HIT + 14, sc=(1, 1, 1)); key(pud, HIT + 30, sc=(0.3, 0.3, 1))
    objs = []
    for s in st:
        objs += [s["s1"], s["s2"]] + meshes(s["m"])
    crumble(objs, HIT + 20, per=5)
    finish(tag, prig, lambda: C + Vector((0, 0, 1.0)))


def take_b3(tag, prig, bx, by):
    """Mosaic Face: one giant blank face 2.5 m tall built from small tiles, two eye holes with a light deep inside.
    Its head jerks sideways; the tiles flip over from the middle out, each one a small face; then it bursts into a
    cage of faces round the player's head, all staring in, and turns."""
    py = by - 1.8
    H = Vector((bx, py, 1.75))
    E = fmat(f"{tag} tile eyes", 0.0)
    EB = fmat(f"{tag} deep eyes", 0.8)
    fc = empty(f"{tag} face", (bx, by + 2.5, 2.0))
    tiles = []
    SP = 0.28
    for r in range(9):
        for c in range(7):
            if ((c - 3) / 3.55) ** 2 + ((r - 4.3) / 4.7) ** 2 > 1.0:
                continue
            if r in (5, 6) and c in (1, 2, 4, 5):
                continue
            if r == 2 and c in (2, 3, 4):
                continue
            o = empty(f"{tag} tile {r} {c}", (0, 0, 0))
            box(f"{tag} tile bone {r} {c}", (-0.125, -0.02, -0.125), (0.125, 0.02, 0.125), BONE, o)
            box(f"{tag} tile back plate {r} {c}", (-0.1, -0.035, -0.1), (0.1, -0.02, 0.1), PLATE, o)
            for s in (-1, 1):
                box(f"{tag} tile eye {r} {c} {s}", (s * 0.05 - 0.022, 0.02, 0.02), (s * 0.05 + 0.022, 0.03, 0.06), E, o)
            box(f"{tag} tile mouth {r} {c}", (-0.05, 0.02, -0.08), (0.05, 0.027, -0.06), VOID, o)
            off = Vector(((c - 3) * SP, 0, (r - 4) * SP))
            tiles.append(dict(o=o, off=off, dist=off.length, k=len(tiles), prev=None))
    for s in (-1, 1):
        box(f"{tag} deep eye {s}", (s * 0.42 - 0.09, 0.4, 0.36), (s * 0.42 + 0.09, 0.48, 0.48), EB, fc)
    lt = plight(f"{tag} deep light", fc, (0, 0.6, 0.35))
    NT = len(tiles)
    gold = math.pi * (3 - math.sqrt(5))
    for tl in tiles:
        i = tl["k"]
        z = 1 - 2 * (i + 0.5) / NT; z = -0.3 + (z + 1) * 0.65
        rr = math.sqrt(max(0.0, 1 - z * z)); th = gold * i
        tl["u"] = Vector((rr * math.cos(th), rr * math.sin(th), z)).normalized()

    def face_state(f):
        roll = R(32) * smooth((f - ATK) / 2) * (1 - smooth((f - ATK - 30) / 6))
        lean = 0.9 * smooth((f - ATK) / 4) * (1 - smooth((f - ATK - 30) / 6))
        Cf = Vector((bx, by + 2.5 - lean, 2.0 + 0.06 * math.sin(f / 20 * 1.6)))
        return Cf, roll
    for f in range(1, HIT + 2):
        Cf, roll = face_state(f)
        key(fc, f, loc=tuple(Cf), rot=(0, roll, 0))
        for tl in tiles:
            k = tl["k"]
            ph = min(1.0, max(0.0, (f - (ATK + 4 + tl["dist"] * 2.2)) / 2))
            yawF = math.pi * ph
            rl = roll * (1 - 2 * ph)
            off = tl["off"]
            p = Cf + Vector((off.x * math.cos(roll) + off.z * math.sin(roll), 0, -off.x * math.sin(roll) + off.z * math.cos(roll)))
            ef = Vector((0, rl, yawF))
            if f < ATK and (f + 7 * k) % 29 < 2:
                p += Vector((0, -0.05, 0.03)); ef.y += 0.2
            s_ = smooth((f - ATK - 14 - (k % 6) * 0.5) / 5) * (1 - smooth((f - ATK - 30 - (k % 5) * 0.4) / 6))
            if s_ > 0:
                w = 0.07 * max(0, f - ATK - 14)
                u = tl["u"]; u = Vector((u.x * math.cos(w) - u.y * math.sin(w), u.x * math.sin(w) + u.y * math.cos(w), u.z))
                ps = H + u * 0.72
                es, tl["prev"] = face_rot(tuple(-u), tl["prev"] if tl["prev"] is not None else yawF)
                p = p.lerp(ps, s_)
                ef = ef.lerp(Vector(es), s_)
            tl["e"] = ef; tl["p"] = p
            key(tl["o"], f, loc=tuple(p), rot=tuple(ef))
    drive(lambda f: (0.0 if f < ATK + 4 else (1.0 if f <= ATK + 34 else 0.7)), [(E, 3.2)])
    drive(lambda f: (0.25 + 0.05 * math.sin(f * 0.4) if f < ATK else (1.6 if f < ATK + 5 else 1.0)), [(EB, 3.6)], [(lt, 180.0)])
    # the player cowers inside the cage of faces
    ppose(prig, ATK + 11, bx, py)
    ppose(prig, ATK + 16, bx, py, dz=-0.26, **CROUCH)
    ppose(prig, ATK + 31, bx, py, dz=-0.26, **CROUCH)
    ppose(prig, ATK + 36, bx, py)
    # death: the tiles fall from the middle out and tumble to the floor, then crumble
    for tl in tiles:
        f0 = HIT + 2 + int(tl["dist"] * 2.5)
        p0, e0 = tl["p"], tl["e"]
        drift = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.6, 0.1), 0))
        sgn = 1 if rng.random() < 0.5 else -1
        for i in range(0, 11):
            u = i / 10
            p = p0 + drift * u; p.z = lerp(p0.z, 0.03, u * u)
            key(tl["o"], f0 + i, loc=tuple(p), rot=(lerp(e0.x, sgn * math.pi / 2, u), e0.y, e0.z))
    objs = []
    for tl in tiles:
        objs += meshes(tl["o"])
    crumble(objs + meshes(fc), HIT + 24, per=8)
    finish(tag, prig, lambda: face_state(HIT)[0])


# ------------------------------------------------------------------ E1c family: stilt stalkers that move (IK legs)
def ik_knee(h, foot, L1, L2, pole):
    d = foot - h; dist = d.length
    dc = min(max(dist, abs(L1 - L2) + 1e-3), L1 + L2 - 1e-3)
    u = d.normalized()
    a = (L1 * L1 - L2 * L2 + dc * dc) / (2 * dc)
    hh = math.sqrt(max(0.0, L1 * L1 - a * a))
    w = pole - u * pole.dot(u)
    w = w.normalized() if w.length > 1e-6 else Vector((0, 0, 1))
    return h + u * a + w * hh, h + u * dc


def make_leg(tag, i, hip, rest, L1, L2, pole, grp, w1=0.05, w2=0.032):
    th = empty(f"{tag} leg {i} thigh pivot", (0, 0, 0))
    box(f"{tag} thigh {i}", (-w1, -w1, -L1), (w1, w1, 0), SHADE, th)
    box(f"{tag} thigh plate {i}", (-w1 - 0.02, -w1 - 0.02, -L1 * 0.55), (w1 + 0.02, w1 + 0.02, -L1 * 0.3), PLATE, th)
    box(f"{tag} knee spike plate {i}", (-0.015, -0.015, -L1 - 0.02), (0.015, 0.015, -L1 + 0.2), PLATE, th)
    sh = empty(f"{tag} leg {i} shin pivot", (0, 0, 0))
    box(f"{tag} knee cap plate {i}", (-0.07, -0.07, -0.07), (0.07, 0.07, 0.07), PLATE, sh)
    box(f"{tag} shin {i}", (-w2, -w2, -L2), (w2, w2, 0), SHADE, sh)
    box(f"{tag} foot spike plate {i}", (-0.014, -0.014, -L2 - 0.07), (0.014, 0.014, -L2), PLATE, sh)
    return dict(i=i, hip=Vector(hip), rest=Vector(rest), L1=L1, L2=L2, pole=Vector(pole), grp=grp, th=th, sh=sh,
                planted=None, step=None, pt=None, ps=None, ov0=None)


def body_matrix(pos, eul):
    return Matrix.Translation(pos) @ Euler(eul, "XYZ").to_matrix().to_4x4()


def run_stalker(body, legs, body_fn, f_end, step_dur, thresh, lift, lead=0.5, override=None, after=None):
    """Simulate a planted-foot gait: each foot stays put until the body has carried its rest spot more than `thresh`
    away, then steps (lifting) to where the rest spot will be; opposite gait groups never step together. Knees by
    two-bone IK, bent toward the pole (up and out). `override(leg, f, M)` can place a foot by hand."""
    for f in range(1, f_end + 1):
        pos, eul = body_fn(f)
        M = body_matrix(pos, eul)
        pn, en = body_fn(f + 1); Mn = body_matrix(pn, en)
        key(body, f, loc=tuple(pos), rot=tuple(eul))
        for lg in legs:
            ideal = M @ lg["rest"]; ideal.z = 0.0
            if lg["planted"] is None:
                lg["planted"] = ideal.copy()
            ov = override(lg, f, M) if override else None
            if ov is not None:
                foot = Vector(ov); lg["planted"] = Vector((foot.x, foot.y, 0.0)) if foot.z < 0.05 else foot.copy(); lg["step"] = None
            else:
                if lg["planted"].z > 0.05:                  # released from a raised override: step down
                    lg["step"] = (f - 1, lg["planted"].copy(), ideal.copy()); lg["planted"] = ideal.copy()
                foot = None
                if lg["step"] is not None:
                    f0, a, b = lg["step"]; t = (f - f0) / step_dur
                    if t >= 1:
                        lg["planted"] = b.copy(); lg["step"] = None; foot = b.copy()
                    else:
                        foot = a.lerp(b, smooth(t)); foot.z += lift * math.sin(math.pi * t) + max(0, a.z) * (1 - t)
                if foot is None:
                    foot = lg["planted"].copy()
                if lg["step"] is None and (ideal - lg["planted"]).length > thresh and \
                        not any(o["step"] is not None and o["grp"] != lg["grp"] for o in legs):
                    vel = Mn.translation - M.translation; vel.z = 0
                    tgt = ideal + vel * step_dur * lead; tgt.z = 0.0
                    lg["step"] = (f, lg["planted"].copy(), tgt)
            hip = M @ lg["hip"]; pole = M.to_3x3() @ lg["pole"]
            knee, foot_r = ik_knee(hip, foot, lg["L1"], lg["L2"], pole)
            lg["pt"] = aim_euler(knee - hip, lg["pt"]); lg["ps"] = aim_euler(foot_r - knee, lg["ps"])
            key(lg["th"], f, loc=tuple(hip), rot=tuple(lg["pt"]))
            key(lg["sh"], f, loc=tuple(knee), rot=tuple(lg["ps"]))
        if after:
            after(f, M)


def aim_local(M, base_local, target):
    """Pitch and yaw (radians) for a child of the body at base_local so its +Y points at a world target."""
    base = M @ Vector(base_local)
    d = M.to_3x3().inverted() @ (Vector(target) - base)
    return math.atan2(d.z, math.hypot(d.x, d.y)), math.atan2(-d.x, d.y), d.length


def take_c1(tag, prig, bx, by):
    """Creeping Stalker: four very long stilt legs with knees high above its back, a telescoping neck, a caged head
    with a searchlight. It stalks in across the bay step-step-freeze, head sweeping the floor, snapping its head
    sideways when it stops; then rears, slams both front legs down either side of the player and drives its head
    into his face with the jaw open."""
    py = by - 1.8
    FACE = Vector((bx, py - 0.35 + 0.3, 1.7))
    body = empty(f"{tag} body", (bx, by + 7.3, 1.9))
    box(f"{tag} torso", (-0.3, -0.45, -0.16), (0.3, 0.45, 0.2), SHADE, body)
    for k in range(3):
        y = -0.3 + k * 0.3
        box(f"{tag} spine plate {k}", (-0.12, y - 0.09, 0.2), (0.12, y + 0.09, 0.34 - k * 0.03), PLATE, body)
        for sx in (1, -1):
            box(f"{tag} rib plate {k} {sx}", (sx * 0.3 - 0.02, y - 0.02, -0.12), (sx * 0.3 + 0.02 * sx, y + 0.02, 0.16), PLATE, body)
    box(f"{tag} belly plate", (-0.22, -0.35, -0.24), (0.22, 0.35, -0.16), PLATE, body)
    for q in range(4):
        box(f"{tag} rag {q}", (-0.2 + q * 0.13, -0.2 + 0.1 * q, -0.85 + 0.08 * q), (-0.17 + q * 0.13, -0.17 + 0.1 * q, -0.2), SHADE, body)
    nk = empty(f"{tag} neck base", (0, 0.45, 0.05), body)
    segs, prev_ = [], nk
    for k in range(4):
        hw = 0.09 - k * 0.015
        s_ = empty(f"{tag} neck {k}", (0, 0.0 if k == 0 else 0.12, 0), prev_)
        box(f"{tag} neck box {k}", (-hw, 0.0, -hw), (hw, 0.8, hw), SHADE if k % 2 else PLATE, s_)
        segs.append(s_); prev_ = s_
    hd = empty(f"{tag} head", (0, 0.8, 0), segs[-1])
    cage(f"{tag} cage plate", (-0.17, 0.0, -0.2), (0.17, 0.36, 0.2), 0.02, PLATE, hd)
    box(f"{tag} skull", (-0.12, 0.03, -0.12), (0.12, 0.22, 0.17), SHADE, hd)
    E = fmat(f"{tag} eyes", 1.0)
    eyes = []
    for k, z in enumerate((0.11, 0.02, -0.07)):
        e = empty(f"{tag} eye {k}", (0, 0.24, z), hd)
        ball(f"{tag} eye ball {k}", 0.045, E, parent=e, seg=10)
        eyes.append(e)
    box(f"{tag} mouth glow", (-0.1, 0.05, -0.2), (0.1, 0.3, -0.17), E, hd)
    jaw = empty(f"{tag} jaw", (0, 0.0, -0.2), hd)
    box(f"{tag} jaw plate", (-0.15, 0.0, -0.06), (0.15, 0.38, 0), PLATE, jaw)
    for q in range(5):
        box(f"{tag} fang plate {q}", (-0.12 + q * 0.06, 0.32, 0), (-0.1 + q * 0.06, 0.36, 0.09), BONE, jaw)
    sp = plight(f"{tag} searchlight", hd, (0, 0.3, 0.0), kind="SPOT", size=0.01, spot=34, rot=(R(80), 0, 0))
    legs = []
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        legs.append(make_leg(tag, i, (sx * 0.28, sy * 0.42, -0.06), (sx * 1.3, sy * 1.4, 0), 1.6, 1.8,
                             (sx * 0.55, sy * 0.25, 1.0), 0 if (sx * sy) > 0 else 1))
    Y = [(1, by + 7.3), (10, by + 5.9), (17, by + 5.9), (27, by + 4.3), (34, by + 4.3), (42, by + 2.7),
         (ATK + 6, by + 2.7), (ATK + 10, by + 1.9), (ATK + 30, by + 1.9), (ATK + 38, by + 2.7)]
    Z = [(1, 1.9), (27, 1.9), (30, 1.72), (34, 1.72), (37, 1.9), (ATK + 2, 1.9), (ATK + 7, 2.45), (ATK + 10, 1.55),
         (ATK + 30, 1.55), (ATK + 38, 1.9), (HIT + 2, 1.9), (HIT + 16, 0.45)]
    PIT = [(ATK + 2, 0.0), (ATK + 7, R(28)), (ATK + 10, R(-10)), (ATK + 30, R(-10)), (ATK + 38, 0.0),
           (HIT + 2, 0.0), (HIT + 16, R(-8))]
    ROL = [(HIT + 2, 0.0), (HIT + 16, R(14))]

    def body_fn(f):
        t = f / 20.0
        moving = 1 if (f < 10 or 17 <= f < 27 or 34 <= f < 42) else 0
        z = wp(f, Z) + 0.04 * math.sin(t * 9) * moving
        ty = 0.5 * math.sin(f * 2.3) if ATK + 11 <= f <= ATK + 29 else 0
        return Vector((bx + 0.01 * ty, wp(f, Y), z)), (wp(f, PIT) + R(ty), wp(f, ROL), math.pi + R(3 * math.sin(t * 0.7)))

    def override(lg, f, M):
        i = lg["i"]
        if i < 2 and ATK + 3 <= f <= ATK + 31:
            sx = 1 if i == 0 else -1
            if lg["ov0"] is None:
                lg["ov0"] = lg["planted"].copy()
            raised = lambda ff: body_matrix(*body_fn(ff)) @ Vector((sx * 0.9, 1.5, 0.5))
            T = Vector((bx - sx * 0.78, py + 0.35, 0.0))          # the enemy faces -Y, so its right (+X local) is -X world
            if f <= ATK + 7:
                return lg["ov0"].lerp(raised(f), smooth((f - ATK - 3) / 4))
            if f <= ATK + 10:
                u = (f - ATK - 7) / 3
                return raised(ATK + 7).lerp(T, u * u)
            return T
        if f >= HIT + 2:
            if lg.get("dead") is None:
                lg["dead"] = lg["planted"].copy()
            out = (lg["dead"] - M.translation); out.z = 0; out.normalize()
            return lg["dead"] + out * 1.1 * smooth((f - HIT - 2 - 3 * i) / 6)
        return None

    def after(f, M):
        t = f / 20.0
        # neck: idle looks down ahead and sweeps the floor; freezes snap the head sideways; attack aims at the face
        ip, iy = R(-32), R(35 * math.sin(t * 1.6))
        if 10 <= f < 17 or 27 <= f < 34:
            iy = R(12)
        p_, y_, dist = aim_local(M, (0, 0.45, 0.05), FACE)
        w = smooth((f - ATK - 4) / 4) * (1 - smooth((f - ATK - 31) / 6))
        if f >= HIT + 2:
            pd = smooth((f - HIT - 2) / 10)
            key(nk, f, rot=(lerp(ip, R(-70), pd), 0, R(15) * pd))
        else:
            key(nk, f, rot=(lerp(ip, p_, w), 0, lerp(iy, y_, w)))
        ext = smooth((f - ATK - 10) / 5) * (1 - smooth((f - ATK - 30) / 6))
        gap = min(0.75, max(0.12, (dist - 0.45 - 0.8) / 3))
        for k, s_ in enumerate(segs):
            if k > 0:
                key(s_, f, loc=(0, lerp(0.12, gap, ext), 0))
        roll = 0
        if 11 <= f < 16:
            roll = R(78)
        elif 28 <= f < 33:
            roll = R(-70)
        key(hd, f, rot=(R(-20) * (1 - w), roll, 0))
        jo = 0
        if ATK + 14 <= f <= ATK + 30:
            jo = R(-45 if (f // 3) % 2 == 0 else -28)
        key(jaw, f, rot=(jo, 0, 0))
    run_stalker(body, legs, body_fn, HIT + 18, step_dur=4, thresh=0.45, lift=0.32, lead=0.6, override=override, after=after)
    for k, e in enumerate(eyes):
        key(e, 1, sc=(1, 1, 0.2)); key(e, ATK + 12 + 2 * k, sc=(1, 1, 0.2)); key(e, ATK + 14 + 2 * k, sc=(1.25, 1.25, 1.25))
        key(e, ATK + 31, sc=(1.25, 1.25, 1.25)); key(e, ATK + 36, sc=(1, 1, 0.35))
    drive(lambda f: (0.35 if f < ATK + 12 else (1.0 if f <= ATK + 31 else 0.5)), [(E, 4.0)])
    drive(lambda f: (1.0 if f < ATK + 10 else (1.6 if f <= ATK + 31 else 1.0)), [], [(sp, 320.0)])
    # the player: the legs slam down either side, he jerks back with arms up, frozen as the face comes in
    ppose(prig, ATK + 9, bx, py)
    ppose(prig, ATK + 11, bx, py, dy=-0.15, arm_r=(130, 0, 30), arm_l=(120, 0, -30), head=(20, 0, 0), body=(12, 0, 0))
    for i, f in enumerate(range(ATK + 14, ATK + 31, 2)):
        ppose(prig, f, bx, py, dy=-0.35, arm_r=(95, 0, 25), arm_l=(90, 0, -25), head=(8, 0, 0), body=(14, 0, 4 if i % 2 else -4))
    ppose(prig, ATK + 36, bx, py, dy=-0.35)
    objs = meshes(body) + [o for lg in legs for o in meshes(lg["th"]) + meshes(lg["sh"])]
    crumble(objs, HIT + 22, per=5)
    finish(tag, prig, lambda: body.matrix_world.translation)


def take_c2(tag, prig, bx, by):
    """Skitter Stalker: a flat body slung low between six stilt legs whose knees stand far above it; one eye and a
    light on a head under its front. It crosses the bay in sudden sideways bursts, freezing dead still between them,
    always facing the player; then it coils and pounces, landing astride him with its legs caging him in."""
    py = by - 1.8
    P0 = Vector((bx, py, 0))
    body = empty(f"{tag} body", (bx - 2.8, by + 6.8, 0.95))
    box(f"{tag} carapace", (-0.36, -0.42, -0.1), (0.36, 0.42, 0.12), SHADE, body)
    box(f"{tag} belly plate", (-0.26, -0.32, -0.16), (0.26, 0.32, -0.1), PLATE, body)
    for q in range(5):
        y = -0.3 + q * 0.15
        s_ = empty(f"{tag} crest {q}", (0, y, 0.12), body); s_.rotation_euler = (R(-25), 0, 0)
        box(f"{tag} crest plate {q}", (-0.018, -0.018, 0), (0.018, 0.018, 0.22 + 0.06 * math.sin(q)), PLATE, s_)
    nk = empty(f"{tag} neck", (0, 0.42, -0.04), body)
    box(f"{tag} neck box", (-0.05, 0, -0.05), (0.05, 0.2, 0.05), SHADE, nk)
    hd = empty(f"{tag} head", (0, 0.2, 0), nk)
    box(f"{tag} head box", (-0.11, 0.0, -0.1), (0.11, 0.2, 0.08), SHADE, hd)
    E = fmat(f"{tag} eye", 1.0)
    box(f"{tag} eye", (-0.06, 0.2, -0.05), (0.06, 0.215, 0.05), E, hd)
    for s in (-1, 1):
        m_ = empty(f"{tag} mandible {s}", (s * 0.08, 0.18, -0.09), hd); m_.rotation_euler = (R(-30), 0, R(s * 20))
        box(f"{tag} mandible plate {s}", (-0.012, 0, -0.012), (0.012, 0.18, 0.012), PLATE, m_)
    feelers = []
    for s in (-1, 1):
        fe = empty(f"{tag} feeler {s}", (s * 0.06, 0.18, 0.06), hd)
        box(f"{tag} feeler plate {s}", (-0.007, 0, -0.007), (0.007, 0.75, 0.007), PLATE, fe)
        feelers.append((fe, s))
    sp = plight(f"{tag} eye light", hd, (0, 0.22, 0), kind="SPOT", size=0.01, spot=30, rot=(R(90), 0, 0))
    legs = []
    i = 0
    for sx in (1, -1):
        for yk in (1, 0, -1):
            grp = 0 if (sx > 0) == (yk != 0) else 1
            legs.append(make_leg(tag, i, (sx * 0.3, yk * 0.32, 0), (sx * 1.35, yk * 1.15, 0), 1.25, 1.35,
                                 (sx * 0.25, yk * 0.1, 1.0), grp, w1=0.04, w2=0.026))
            legs[-1]["sx"], legs[-1]["yk"] = sx, yk
            i += 1
    XY = [(1, (-2.8, 6.8)), (6, (-2.8, 6.8)), (9, (2.4, 5.9)), (16, (2.4, 5.9)), (19, (-2.0, 4.4)), (26, (-2.0, 4.4)),
          (28, (1.3, 3.3)), (37, (1.3, 3.3)), (39, (0.0, 2.6))]
    XY = [(f, Vector((bx + x, by + y, 0))) for f, (x, y) in XY]
    LAND = Vector((bx, py + 0.3, 2.15))
    HOME = Vector((bx, by + 2.6, 0.95))

    def body_fn(f):
        if f <= ATK:
            p = wp(f, XY)
            z = 0.95 - (0.2 * smooth((f - 29) / 8) if 28 <= f <= 39 else 0)
            z -= 0.15 * smooth((f - 37) / 2) * 0 + 0.0
            p = Vector((p.x, p.y, z))
        elif f <= ATK + 6:
            p = HOME.copy(); p.z = lerp(0.95, 0.5, smooth((f - ATK) / 6))
        elif f <= ATK + 12:
            u = (f - ATK - 6) / 6
            a = Vector((bx, by + 2.6, 0.5)); p = a.lerp(LAND, u); p.z = lerp(0.5, LAND.z, u) + 1.2 * math.sin(math.pi * u)
        elif f <= ATK + 30:
            p = LAND + Vector((0, 0, 0.04 * math.sin(f * 2.5)))
        elif f <= ATK + 36:
            u = (f - ATK - 30) / 6
            p = LAND.lerp(HOME, smooth(u)); p.z += 0.9 * math.sin(math.pi * u)
        elif f < HIT + 2:
            p = HOME.copy()
        else:
            p = HOME.copy(); p.z = lerp(0.95, 0.3, smooth((f - HIT - 4) / 8))
        d = P0 - Vector((p.x, p.y, 0))
        yaw = math.atan2(d.y, d.x) - math.pi / 2 if d.length > 1.0 else math.pi
        while yaw < 0:
            yaw += 2 * math.pi
        rl = R(18) * smooth((f - HIT - 4) / 8) if f >= HIT + 2 else 0
        return p, (0.0, rl, yaw)

    def override(lg, f, M):
        sx, yk = lg["sx"], lg["yk"]
        tuck = M @ Vector((sx * 0.55, yk * 0.45, -0.45))
        if ATK + 6 <= f < ATK + 12 or ATK + 30 <= f < ATK + 36:
            return tuck
        if ATK + 12 <= f < ATK + 30:
            a = math.atan2(yk * 0.9, sx) + math.pi
            return P0 + Vector((1.15 * math.cos(a), 1.15 * math.sin(a), 0))
        if f >= HIT + 2:
            if lg.get("dead") is None:
                lg["dead"] = lg["planted"].copy()
            curl = M @ Vector((sx * 0.3, yk * 0.3, -0.12))
            return lg["dead"].lerp(curl, smooth((f - HIT - 2 - lg["i"]) / 6))
        return None

    def after(f, M):
        p_, y_, _ = aim_local(M, (0, 0.42, -0.04), (bx, py + 0.25, 1.65))
        key(nk, f, rot=(max(R(-85), min(R(30), p_)), 0, y_))
        moving = any(f0 < f <= f1 for f0, f1 in ((6, 9), (16, 19), (26, 28), (37, 39)))
        for fe, s in feelers:
            jerk = ((f * 7 + s * 3) % 11 < 2)
            key(fe, f, rot=(R(10 + (25 if jerk else 0) + (20 if moving else 0) * math.sin(f * 3)), 0, R(s * (18 + (20 if jerk else 0)))))
    run_stalker(body, legs, body_fn, HIT + 16, step_dur=2, thresh=0.28, lift=0.22, lead=0.6, override=override, after=after)
    drive(lambda f: (0.6 if f < ATK + 6 else (1.4 if f <= ATK + 31 else 0.6)), [(E, 4.0)], [(sp, 260.0)])
    # the player: it lands astride him; he drops into a crouch with his arms over his head
    ppose(prig, ATK + 9, bx, py)
    ppose(prig, ATK + 13, bx, py, dz=-0.26, **CROUCH)
    ppose(prig, ATK + 30, bx, py, dz=-0.26, **CROUCH)
    ppose(prig, ATK + 36, bx, py)
    objs = meshes(body) + [o for lg in legs for o in meshes(lg["th"]) + meshes(lg["sh"])]
    crumble(objs, HIT + 20, per=6)
    finish(tag, prig, lambda: body.matrix_world.translation)


def take_c3(tag, prig, bx, by):
    """Unfolding Crawler: it drags itself in low along the floor, its folded legs peaking far above its back like
    tent poles; at the player it unfolds in a few ticks to 3 m tall and lowers its head, upside down on a long
    hanging neck, right in front of his face."""
    py = by - 1.8
    PB = -0.3                                              # the player's step back
    FACE = Vector((bx, py + PB + 0.3, 1.72))
    body = empty(f"{tag} body", (bx, by + 7.4, 0.42))
    box(f"{tag} torso", (-0.2, -0.6, -0.12), (0.2, 0.6, 0.14), SHADE, body)
    for q in range(5):
        y = -0.5 + q * 0.25
        box(f"{tag} ridge plate {q}", (-0.08, y - 0.06, 0.14), (0.08, y + 0.06, 0.26 + 0.04 * (q % 2)), PLATE, body)
    for q in range(4):
        box(f"{tag} rag {q}", (-0.16 + q * 0.1, -0.3 + q * 0.15, -0.6), (-0.13 + q * 0.1, -0.27 + q * 0.15, -0.12), SHADE, body)
    nb = empty(f"{tag} neck base", (0, 0.6, 0.02), body)
    segs, prev_ = [], nb
    for k in range(3):
        s_ = empty(f"{tag} neck {k}", (0, 0.0 if k == 0 else 0.9, 0), prev_)
        w = 0.05 - k * 0.006
        box(f"{tag} neck box {k}", (-w, 0.0, -w), (w, 0.9, w), SHADE, s_)
        for q in range(3):
            box(f"{tag} vertebra plate {k} {q}", (-w - 0.02, 0.1 + q * 0.25, -w - 0.02), (w + 0.02, 0.16 + q * 0.25, w + 0.03), PLATE, s_)
        segs.append(s_); prev_ = s_
    hd = empty(f"{tag} head", (0, 0.9, 0), segs[-1]); hd.rotation_mode = "YXZ"
    box(f"{tag} skull", (-0.11, -0.04, -0.3), (0.11, 0.14, 0.14), SHADE, hd)
    box(f"{tag} brow plate", (-0.13, 0.1, 0.0), (0.13, 0.17, 0.05), PLATE, hd)
    E = fmat(f"{tag} eye slit", 1.0)
    box(f"{tag} eye slit", (-0.1, 0.14, -0.035), (0.1, 0.152, 0.0), E, hd)
    box(f"{tag} mouth", (-0.03, 0.14, -0.27), (0.03, 0.15, -0.1), VOID, hd)
    sp = plight(f"{tag} eye light", hd, (0, 0.18, -0.02), kind="SPOT", size=0.01, spot=28, rot=(R(90), 0, 0))
    legs = []
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        rest = (sx * 0.95, 1.55, 0) if sy > 0 else (sx * 1.0, -1.2, 0)
        legs.append(make_leg(tag, i, (sx * 0.22, sy * 0.55, -0.02), rest, 1.75, 1.9, (sx * 0.3, sy * 0.25, 1.0),
                             0 if sx * sy > 0 else 1, w1=0.045, w2=0.03))
    Y0 = by + 7.4

    def crawl_y(f):
        y = Y0
        for i in range(5):
            y -= 1.0 * smooth((f - (2 + 8 * i)) / 4)
        return y

    def body_fn(f):
        mv = sum(math.sin(math.pi * min(1, max(0, (f - (2 + 8 * i)) / 4))) for i in range(5))
        if f <= ATK + 2:
            y = crawl_y(f); z = 0.42 + 0.06 * mv; pit = R(-6) * mv; rl = R(6) * mv * (1 if (f // 8) % 2 else -1)
        elif f <= ATK + 30:
            u = smooth((f - ATK - 2) / 6)
            y = lerp(by + 2.4, by + 1.1, u); z = lerp(0.42, 2.9, u); pit = R(10) * u; rl = R(3) * math.sin(f * 0.5) * u
        elif f < HIT + 2:
            u = smooth((f - ATK - 30) / 8)
            y = lerp(by + 1.1, by + 2.4, u); z = lerp(2.9, 1.7, u); pit = R(10) * (1 - u); rl = 0.0
        else:
            u = min(1.0, (f - HIT - 2) / 10)
            y = by + 2.4; z = lerp(1.7, 0.28, u * u); pit = 0.0; rl = R(18) * u
        return Vector((bx, y, z)), (pit, rl, math.pi)

    def override(lg, f, M):
        if f >= HIT + 2:
            if lg.get("dead") is None:
                lg["dead"] = lg["planted"].copy()
            out = lg["dead"] - M.translation; out.z = 0; out.normalize()
            return lg["dead"] + out * 0.9 * smooth((f - HIT - 2 - 2 * lg["i"]) / 6)
        if ATK + 2 <= f <= ATK + 30 and lg.get("hold") is None:
            lg["hold"] = lg["planted"].copy()
        if ATK + 2 <= f <= ATK + 30:
            return lg["hold"]
        return None
    BEND = [0.0, R(-32), R(-34)]

    def neck_fk(M, th, yw):
        base = M @ Vector((0, 0.6, 0.02)); R3 = M.to_3x3() @ Euler((th, 0, yw), "XYZ").to_matrix()
        p = base.copy(); cum = 0
        for k in range(3):
            cum += BEND[k]
            d = R3 @ Euler((cum, 0, 0), "XYZ").to_matrix() @ Vector((0, 1, 0))
            p = p + d * 0.9
        return p

    def after(f, M):
        hang = smooth((f - ATK - 4) / 6) * (1 - smooth((f - ATK - 30) / 8)) if f < HIT + 2 else 0
        crawl = [R(-12), R(4), R(18)]
        if hang > 0:
            _, yw, _ = aim_local(M, (0, 0.6, 0.02), FACE + Vector((0, 0.42, 0)))
            best = (1e9, 0)
            for di in range(-150, 31):
                p = neck_fk(M, R(di), yw)
                e_ = (p - (FACE + Vector((0, 0.42, 0)))).length
                if e_ < best[0]:
                    best = (e_, R(di))
            th = best[1]
        else:
            th, yw = crawl[0], 0.0
        if f >= HIT + 2:
            pd = smooth((f - HIT - 2) / 10)
            key(nb, f, rot=(lerp(R(-12), R(-60), pd), 0, R(10) * pd))
            for k in (1, 2):
                key(segs[k], f, rot=(lerp(crawl[k], R(-25), pd), 0, 0))
            key(hd, f, rot=(R(-20), 0, 0))
            return
        key(nb, f, rot=(lerp(crawl[0], th, hang), 0, lerp(0, yw, hang)))
        for k in (1, 2):
            key(segs[k], f, rot=(lerp(crawl[k], BEND[k], hang), 0, R(4 * math.sin(f * 0.3 + k)) * (1 - hang)))
        cum = lerp(sum(crawl), th + BEND[1] + BEND[2], hang)
        roll = math.pi * smooth((f - ATK - 6) / 5) * (1 - smooth((f - ATK - 30) / 6))
        twitch = 0
        for fj, a in ((ATK + 14, 25), (ATK + 19, -20), (ATK + 23, 30), (ATK + 27, -15)):
            if fj <= f < fj + 3:
                twitch = R(a)
        key(hd, f, rot=(-cum + R(10) * (1 - hang), roll + twitch, 0))
    run_stalker(body, legs, body_fn, HIT + 16, step_dur=5, thresh=0.55, lift=0.38, lead=0.6, override=override, after=after)
    drive(lambda f: (0.3 if f < ATK + 6 else (1.5 if f < ATK + 10 else (1.0 if f <= ATK + 31 else 0.4))), [(E, 4.0)], [(sp, 260.0)])
    # the player looks up as it rises, then backs off a step, frozen, arms half up
    ppose(prig, ATK + 4, bx, py)
    ppose(prig, ATK + 8, bx, py, head=(40, 0, 0), arm_r=(60, 0, 20), arm_l=(60, 0, -20))
    for i, f in enumerate(range(ATK + 12, ATK + 31, 2)):
        ppose(prig, f, bx, py, dy=PB, head=(12, 0, 0), arm_r=(70, 0, 20), arm_l=(70, 0, -20), body=(8, 0, 3 if i % 2 else -3))
    ppose(prig, ATK + 36, bx, py, dy=PB)
    objs = meshes(body) + [o for lg in legs for o in meshes(lg["th"]) + meshes(lg["sh"])]
    crumble(objs, HIT + 22, per=6)
    finish(tag, prig, lambda: body.matrix_world.translation)


TAKES = (
    ("E1a1", "Curtain Veil", take_a1, 0, 0, ATK + 16), ("E1a2", "Bell Veil", take_a2, 1, 0, ATK + 18),
    ("E1a3", "Scale Cocoon", take_a3, 2, 0, ATK + 22),
    ("E1b1", "Mask Totem", take_b1, 0, 1, ATK + 16), ("E1b2", "Stalk Crowd", take_b2, 1, 1, ATK + 16),
    ("E1b3", "Mosaic Face", take_b3, 2, 1, ATK + 22),
    ("E1c1", "Creeping Stalker", take_c1, 0, 2, ATK + 18), ("E1c2", "Skitter Stalker", take_c2, 1, 2, ATK + 16),
    ("E1c3", "Unfolding Crawler", take_c3, 2, 2, ATK + 14),
)
for tk, name, fn, ci, ri, peak in TAKES:
    bx, by = ci * BAY, ri * ROW
    tag, prig = bay(tk, name, bx, by)
    fn(tag, prig, bx, by)
    if ri == 2:
        cam(f"Cam {tk}", (bx + 6.4, by - 6.6, 3.9), (bx, by + 2.4, 1.3), 26)
        cam(f"Cam {tk} close", (bx + 1.3, by - 4.6, 2.1), (bx, by + 2.4, 1.7), 26)
    else:
        cam(f"Cam {tk}", (bx + 4.6, by - 5.6, 2.9), (bx, by + 0.9, 1.4), 30)
        cam(f"Cam {tk} close", (bx + 1.1, by - 4.3, 2.05), (bx, by + 2.0, 1.7), 30)
    print(tk, "peak", peak)
for ri, rn in enumerate(("E1a", "E1b", "E1c")):
    cam(f"Cam row {rn}", (BAY, ri * ROW - 17, 7.5), (BAY, ri * ROW + 2.5, 1.2), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam E1a1", 1, (0.04, 0.043, 0.058), 0.4
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
