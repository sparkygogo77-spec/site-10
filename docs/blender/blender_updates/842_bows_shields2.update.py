# Pass 842: bows and shields, 3 variations each of 823 B1, B2, B3, H2, H3 (Chat C, 2026-10-15, range 800-899).
# J rated 823 B1/B2/B3/H2/H3 IMPROVE with no note: "3 new variations each", labelled, he picks. H1 was dropped.
# Earlier (808): "VERY in depth bow and arrow models, think modern day bow and arrows", "the shield is too small".
# Same shot as 823 (right-handed archer, ring on the draw hand, 20 ticks a second): the bow forms in the left hand,
# side-on stance, draw to the anchor under the jaw, hold, release, arrow 5 blocks a tick to a target 18 blocks out.
# Every take is built a different way:
#   B1a compound, swept riser: one bent deflex bar with glowing ports and a truss spine; binary eccentric cams that
#       roll 200 deg over on the draw; front rod + back bar; 4-pin sight; 4-vane arrow with a lighted nock;
#       forms from pixels streaming out of the ring
#   B1b compound, machined plate: CNC plate riser with triangle cut-outs (R2 texture); hybrid cams; drop-away rest that
#       flips up on the draw and drops at the shot; caliper release aid on the ring hand; offset V-bar; grows from the grip
#   B1c compound, sliced riser: riser stacked from 34 thin slices with windows, outline rails trace in first; single
#       cam + idler; target scope with lens and level; barrel-shaft arrow
#   B2a Olympic, shape-key limbs: ILF plate riser; smooth limbs whose whole curve changes on the draw (shape keys);
#       clicker snaps at 34; finger tab; spin-wing arrow that spins in flight
#   B2b Olympic, laminated limbs: twin twisting ribbon riser; limbs of 3 laminations in 6 segments that flex
#       progressively; forms from the limb tips in
#   B2c Olympic, faceted + roll: faceted crystal riser; stiff sharp-recurve limbs; the bow rolls forward out of the
#       open hand on the finger sling after the shot
#   B3a hunting, plate + mechanical heads: short ported riser (W1 texture); 7-pin sight; mechanical broadheads whose
#       blades flick open in the foam target
#   B3b hunting, truss + rangefinder: carbon-tube truss riser with nodes; rangefinder laser reads 18, the slider pin
#       drops to match; hinge release; 2-blade heads
#   B3c hunting, cube riser, two shots: riser of half-pixel cubes; release 25, the ring hand takes a second arrow from
#       the 6-arrow quiver, draws again and releases at 45; 4-blade heads
#   H2a tower, curved brick: 1.0 x 1.8 curved tower of offset BR1 brick courses; a hit ripple across the face
#   H2b tower, riot wall: 1.0 x 1.9 W1 panel with a viewport; rim traces, panel fades in; kneel and foot spike;
#       the hit spreads cracks that heal. rev 2 (J: "shield in third person collides with arms"): held from behind by
#       two grip bars just past the hands, arms clear of the wall at every frame
#   H2c tower, telescoping heater: 7 curved H1 slats slide out of the forearm into a 1.0 x 1.7 heater; slats rock back
#       in a wave from the hit
#   H3a dome, geodesic cap: 1.7 across, triangle cells, both hands bracing; forms in a spiral; rings of cells light
#       out from the hit
#   H3b dome, planted wall: 2.4 x 2.0 curved wall rising 1.6 blocks ahead from a glowing ground line, leaning in
#   H3c dome, twin shells: X3 outer shell 1.6 across over a counter-turning hex-ring lattice; hit pulse runs to the ring
# Cameras: bows "Cam <take>", "Cam <take> close", "Cam <take> target"; shields "Cam <take>", "Cam <take> back";
# "Cam all". Builds LanternLive\combat\bows_shields2.blend.
SCENE_NAME = "Bows and Shields 2"
OUT_REL = "combat/bows_shields2.blend"
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


FRAME_END = 64
BAY = 6.0
F_UP, F_DRAW, F_FULL, F_REL = 14, 18, 32, 42
FLOOR = mat("BS2 floor", (0.2, 0.22, 0.24), rough=0.9)
STRAW = mat("BS2 target straw", (0.75, 0.62, 0.35), rough=0.9)
RINGS = [mat(f"BW target ring {i}", c, rough=0.7) for i, c in enumerate(((0.9, 0.9, 0.85), (0.08, 0.08, 0.1), (0.1, 0.3, 0.9), (0.9, 0.1, 0.1), (1.0, 0.85, 0.1)))]
SHOT = mat("BS2 shot", (0.6, 0.15, 0.1), emit=1.0)
BOARD = mat("BS2 board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("BS2 text", (0.75, 1.0, 0.8), emit=1.2)
TXTH = mat("BS2 heading", (0.2, 1.0, 0.4), emit=2.2)
rng = np.random.default_rng(842)
CM = cmats("BS2", "green")
G, W, RM, GR = CM["glass"], CM["glow"], CM["rim"], CM["grip"]
STR = mat("BS2 string", (0.1, 1.0, 0.3), emit=2.0)
# ------------------------------------------------------------------ forward kinematics of make_player (root space)
def E(v):
    return Euler(tuple(R(a) for a in v), "XYZ").to_matrix()


def fk(pose_, side="r"):
    """Return (hand, ring point, elbow) in root space (player faces +Y) for a pose dict in degrees."""
    Rb = E(pose_.get("body", (0, 0, 0)))
    B = Vector((0, 0, 12 * P))
    sx = 1 if side == "r" else -1
    sh = B + Rb @ Vector((sx * 6 * P, 0, 10 * P))
    Ma = Rb @ E(pose_.get("arm_" + side, (0, 0, 0)))
    el = sh + Ma @ Vector((0, 0, -6 * P))
    Mf = Ma @ E(pose_.get("fore_" + side, (0, 0, 0)))
    hand = el + Mf @ Vector((0, 0, -6 * P))
    ring = el + Mf @ Vector((2.6 * P, 0, -4.1 * P))
    return hand, ring, el


def head_point(pose_, local):
    Rb = E(pose_.get("body", (0, 0, 0)))
    H = Vector((0, 0, 12 * P)) + Rb @ Vector((0, 0, 12 * P))
    hp = pose_.get("head", (0, 0, 0)); hp = (max(-57, min(57, hp[0])), hp[1], hp[2])
    return H + Rb @ E(hp) @ Vector(local)


def solve(pose_, side, target, which="hand", pref=None, w=0.002):
    """Coordinate descent on (arm x, y, z, elbow x) so the hand / ring lands on target (root space, metres);
    a light pull toward pref keeps it natural. Elbow bends one way only (0..150)."""
    pref = pref or [60.0, 0.0, 0.0, 40.0]
    x = list(pref)
    def cost(v):
        p = dict(pose_); p["arm_" + side] = (v[0], v[1], v[2]); p["fore_" + side] = (v[3], 0, 0)
        h, r_, _ = fk(p, side)
        pt = h if which == "hand" else r_
        return (pt - Vector(target)).length ** 2 + w * sum(((a - b) / 90.0) ** 2 for a, b in zip(v, pref)) * 0.01
    step = 20.0
    c = cost(x)
    while step > 0.05:
        moved = False
        for i in range(4):
            for d in (step, -step):
                y = list(x); y[i] += d
                if i == 3:
                    y[3] = min(150.0, max(0.0, y[3]))
                cy = cost(y)
                if cy < c:
                    x, c, moved = y, cy, True
        if not moved:
            step *= 0.5
    return (x[0], x[1], x[2]), (x[3], 0, 0), math.sqrt(max(0.0, c))


IDLE = dict(arm_r=(4, 0, -3), fore_r=(8, 0, 0), arm_l=(4, 0, 3), fore_l=(8, 0, 0), head=(0, 0, 0), body=(0, 0, 0),
            leg_r=(0, 0, 0), shin_r=(0, 0, 0), leg_l=(0, 0, 0), shin_l=(0, 0, 0))


def build_keys(keys):
    """keys: [(tick, dict)] where dict may hold ik_r / ik_l = (target, which, pref). Returns solved dicts + errors."""
    out, errs = [], []
    for f, d in keys:
        p = dict(IDLE); p.update({k: v for k, v in d.items() if not k.startswith("ik_")})
        for side in ("r", "l"):
            spec = d.get("ik_" + side)
            if spec:
                tgt, which, pref = spec
                if callable(tgt):
                    tgt = tgt(p)
                a, fo, err = solve(p, side, tgt, which, pref)
                p["arm_" + side], p["fore_" + side] = a, fo
                errs.append((f, side, round(err, 4)))
        out.append((f, p))
    return out, errs


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




def bx_(tag, nm, a, b, m, par):
    return box(f"{tag} {nm}", a, b, m, par)


# ================================================================== pass 842: new builders (variations of 823 B1-B3, H2, H3)
import bmesh
from mathutils import Quaternion
from mathutils.geometry import tessellate_polygon

LNOCK = mat("BS2 lighted nock", (0.12, 1.0, 0.3), emit=0.3)
anim_emit(LNOCK, [(1, 0.3), (41, 0.3), (42, 7.0), (46, 5.0)])
DARK = mat("BS2 carbon", (0.02, 0.12, 0.05), emit=0.35, alpha=0.9, rough=0.25)
LENS = mat("BS2 lens", (0.05, 0.6, 0.2), emit=0.6, alpha=0.35, rough=0.05)
LASER = mat("BS2 laser", (0.12, 1.0, 0.3), emit=6.0)
FOAM = [mat(f"BS2 foam {i}", c, rough=0.9) for i, c in enumerate(((0.85, 0.85, 0.8), (0.12, 0.13, 0.14), (0.85, 0.2, 0.1)))]


def mesh_obj(name, vs, fs, m, parent=None, smooth=False, uvt=0.25, loc=(0, 0, 0)):
    """A mesh from verts/faces with outward normals and per-face projected UVs (one tile per uvt metres)."""
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in vs], [], fs); me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    except Exception:
        pass
    bm.to_mesh(me); bm.free(); me.materials.append(m)
    uv = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        poly.use_smooth = smooth
        n = np.abs(np.array(poly.normal)); ax = int(np.argmax(n)); o_ = [i for i in range(3) if i != ax]
        for li in poly.loop_indices:
            co = np.array(me.vertices[me.loops[li].vertex_index].co)
            uv.data[li].uv = (co[o_[0]] / uvt, co[o_[1]] / uvt)
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    if parent is not None:
        o.parent = parent
    return o


def sweep_verts(pts, ws, ts, side=(1, 0, 0)):
    """Rectangular section swept along pts: width along `side`, thickness across the path. 4 verts per point."""
    pts = [Vector(p) for p in pts]; sd = Vector(side).normalized(); vs = []
    n_ = len(pts)
    for i, p in enumerate(pts):
        t = (pts[min(n_ - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
        nn = sd.cross(t)
        if nn.length < 1e-6:
            nn = Vector((0, 0, 1)).cross(t)
        nn.normalize()
        w = ws[i] if hasattr(ws, "__len__") else ws; th = ts[i] if hasattr(ts, "__len__") else ts
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            vs.append(p + sd * (a * w / 2) + nn * (b * th / 2))
    return vs


def sweep_faces(n_, closed=False):
    fs = []
    segs = n_ if closed else n_ - 1
    for i in range(segs):
        j = (i + 1) % n_
        for k in range(4):
            fs.append((i * 4 + k, i * 4 + (k + 1) % 4, j * 4 + (k + 1) % 4, j * 4 + k))
    if not closed:
        fs += [(0, 1, 2, 3)[::-1], tuple((n_ - 1) * 4 + k for k in range(4))]
    return fs


def sweep(name, pts, ws, ts, m, parent=None, side=(1, 0, 0), closed=False, smooth=False):
    return mesh_obj(name, sweep_verts(pts, ws, ts, side), sweep_faces(len(pts), closed), m, parent, smooth)


def rod(name, a, b, r, m, parent=None, n=8):
    """A round rod between two points (parent-local)."""
    a = Vector(a); b = Vector(b); d = b - a; L = max(1e-5, d.length)
    q = d.to_track_quat("Z", "Y")
    vs = []
    for k in range(n):
        an = 2 * math.pi * k / n
        for z in (0, L):
            vs.append(a + q @ Vector((r * math.cos(an), r * math.sin(an), z)))
    fs = [(2 * k, 2 * ((k + 1) % n), 2 * ((k + 1) % n) + 1, 2 * k + 1) for k in range(n)]
    fs += [tuple(2 * k for k in range(n))[::-1], tuple(2 * k + 1 for k in range(n))]
    return mesh_obj(name, vs, fs, m, parent, smooth=True)


def plate(name, outer, holes, x0, x1, m, parent=None, uvt=0.2):
    """A flat machined plate in the YZ plane (outline and holes as (y, z) loops), extruded from x0 to x1 along X."""
    loops = [outer] + list(holes)
    flat = [p for lp in loops for p in lp]
    tris = tessellate_polygon([[Vector((p[0], p[1], 0)) for p in lp] for lp in loops])
    N = len(flat)
    vs = [(x0, p[0], p[1]) for p in flat] + [(x1, p[0], p[1]) for p in flat]
    fs = [tuple(t) for t in tris] + [tuple(i + N for i in t) for t in tris]
    base = 0
    for lp in loops:
        n_ = len(lp)
        for i in range(n_):
            a = base + i; b = base + (i + 1) % n_
            fs.append((a, b, b + N, a + N))
        base += n_
    return mesh_obj(name, vs, fs, m, parent, uvt=uvt)


def loop2d(cx, cy, rx, ry, n=10, rot=0.0):
    return [(cx + rx * math.cos(2 * math.pi * k / n + rot), cy + ry * math.sin(2 * math.pi * k / n + rot)) for k in range(n)]


def tri2d(a, b, c, inset=0.0):
    ctr = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3)
    return [(p[0] + (ctr[0] - p[0]) * inset, p[1] + (ctr[1] - p[1]) * inset) for p in (a, b, c)]


def wpos(o):
    if o.type == "MESH" and len(o.data.vertices):
        return o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))
    return o.matrix_world.translation.copy()


def form_by(parts, f0, f1, order, src=None, pixm=None, tag="", stream=0.0, eval_frame=None, grow=2):
    """Each part pops in at a frame set by order(world pos) in [0, 1]; some get a pixel flying in from src first."""
    if eval_frame:
        scene.frame_set(eval_frame)
    bpy.context.view_layer.update()
    pos = [(o, wpos(o)) for o in parts]
    vals = [order(p) for _, p in pos]; lo, hi = min(vals), max(vals) + 1e-6
    pm = pixel_mesh(pixm or CM["pix"])
    out = {}
    for (o, p), v in zip(pos, vals):
        fa = int(round(f0 + (v - lo) / (hi - lo) * (f1 - f0)))
        sc0 = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, max(1, fa - 1), sc=0.0001); key(o, fa - 1 + grow, sc=sc0)
        out[o.name] = fa
        if src is not None and rng.random() < stream:
            px = link(bpy.data.objects.new(f"{tag} pixel", pm))
            s0 = Vector(src) + Vector(rng.uniform(-0.03, 0.03, 3)); fs = max(1, fa - 4)
            key(px, 1, loc=s0, sc=0.0001); key(px, fs, loc=s0, sc=0.0001); key(px, fs + 1, loc=s0, sc=1.0)
            key(px, fs + 2, loc=(s0 + p) / 2 + Vector((0, 0, 0.1)), sc=1.0); key(px, fa, loc=p, sc=0.7)
            key(px, fa + 1, loc=p, sc=0.0001)
    return out


def strip(look, name, alpha=0.9, emit=1.4, ft=5):
    m = strip_mat(name, strip_image("green", look), ft=ft, emit=emit, alpha=alpha)
    return m


def strip_alpha_socket(m):
    p = m.node_tree.nodes["Principled BSDF"]
    if p.inputs["Alpha"].links:
        return p.inputs["Alpha"].links[0].from_node.inputs[1]
    return p.inputs["Alpha"]


# ------------------------------------------------------------------ arrows
def arrow2(tag, par=None, L=0.74, r=0.0065, vanes=3, vlen=0.09, vh=0.014, helix=0.0, point="field", lit=False,
           barrel=False, wrap=True):
    """A modern arrow along local -Z (point forward), nock at z=0. Returns (root, extras dict)."""
    root = empty(f"{tag} arrow", (0, 0, 0), par)
    ex = {}
    if barrel:                                         # barrelled target shaft: fattest in the middle
        n = 9; pts = [(0, 0, -0.012 - L * k / (n - 1)) for k in range(n)]
        rs = [r * (0.75 + 0.35 * math.sin(math.pi * k / (n - 1))) for k in range(n)]
        for k in range(n - 1):
            cyl(f"{tag} shaft {k}", rs[k], L / (n - 1), G, 8, root, loc=(0, 0, pts[k + 1][2]), axis="Z", r2=rs[k])
    else:
        cyl(f"{tag} shaft", r, L, G, 8, root, loc=(0, 0, -L - 0.012), axis="Z")
    if wrap:
        cyl(f"{tag} wrap", r + 0.001, 0.13, DARK, 8, root, loc=(0, 0, -0.145), axis="Z")
    cyl(f"{tag} insert", r + 0.0007, 0.03, RM, 8, root, loc=(0, 0, -L - 0.04), axis="Z")
    tip = -L - 0.04
    if point == "field":
        cyl(f"{tag} point", r + 0.001, 0.035, RM, 8, root, loc=(0, 0, tip - 0.035), axis="Z", r2=0.0012)
    elif point == "bullet":
        cyl(f"{tag} point", r + 0.0005, 0.03, RM, 8, root, loc=(0, 0, tip - 0.03), axis="Z", r2=0.002)
        ball(f"{tag} point tip", 0.0022, RM, (0, 0, tip - 0.03), root, 8)
    elif point in ("broad2", "broad3", "broad4"):
        nb = int(point[-1])
        cyl(f"{tag} ferrule", r + 0.002, 0.065, RM, 8, root, loc=(0, 0, tip - 0.065), axis="Z", r2=0.0015)
        for k in range(nb):                            # each blade a thin triangle with a bleeder hole
            bl = empty(f"{tag} blade pivot {k}", (0, 0, tip), root); bl.rotation_euler = (0, 0, k * 2 * math.pi / nb)
            w_ = 0.028 if nb == 2 else 0.02
            plate(f"{tag} blade {k}", [(0.0, 0.0), (0.0, -0.06), (w_, -0.005)], [loop2d(w_ * 0.32, -0.018, 0.004, 0.006, 6)],
                  -0.0008, 0.0008, RM, bl).rotation_euler = (0, 0, R(-90))
    elif point == "mech":                              # expandable: blades folded along the ferrule, open on impact
        cyl(f"{tag} ferrule", r + 0.002, 0.06, RM, 8, root, loc=(0, 0, tip - 0.06), axis="Z", r2=0.0015)
        cyl(f"{tag} chisel", r + 0.002, 0.01, W, 8, root, loc=(0, 0, tip - 0.07), axis="Z", r2=0.0005)
        ex["mech"] = []
        for k in range(2):
            pv = empty(f"{tag} mech pivot {k}", (0, 0, tip - 0.05), root); pv.rotation_euler = (0, 0, k * math.pi)
            hinge = empty(f"{tag} mech hinge {k}", (0.008, 0, 0), pv)
            box(f"{tag} mech blade {k}", (-0.001, -0.0007, 0.0), (0.002, 0.0007, 0.045), RM, hinge)
            ex["mech"].append(hinge)
    for k in range(vanes):                             # vanes: a curved profile plate, optional helix
        vp = empty(f"{tag} vane pivot {k}", (0, 0, 0), root)
        vp.rotation_euler = (0, 0, k * 2 * math.pi / vanes)
        prof = [(-0.025, r), (-0.025 - vlen, r), (-0.025 - vlen * 0.75, r + vh), (-0.025 - vlen * 0.2, r + vh * 0.7)]
        v = plate(f"{tag} vane {k}", prof, [], -0.0007, 0.0007, RM if k else W, vp)
        v.rotation_euler = (R(90) + R(helix), 0, R(90))
    if lit:
        cyl(f"{tag} lighted nock", 0.006, 0.02, LNOCK, 8, root, loc=(0, 0, -0.014), axis="Z")
    box(f"{tag} nock", (-0.006, -0.006, -0.014), (0.006, 0.006, 0.006), W, root)
    box(f"{tag} nock throat", (-0.0065, -0.0015, -0.002), (0.0065, 0.0015, 0.0065), GR, root)
    return root, ex


# ------------------------------------------------------------------ bow parts shared by the builders
def cam_pair(tag, root, H, L, a0, kind="binary", idler=False):
    """Compound limbs + cams. kind: binary (two equal cams), hybrid (big top, smaller bottom), single (cam + idler).
    Returns tips (empties at the cam axles, bottom then top), limb pivots [(pivot, sy, rest angle)], cam pivots."""
    tips, flex, cams = [], [], []
    for sy in (-1, 1):
        lp = empty(f"{tag} limb {sy}", (0, sy * H, -0.03), root); lp.rotation_euler = (R(sy * a0), 0, 0)
        flex.append((lp, sy, a0))
        for sx in (-1, 1):                               # split limbs, tapering, with a damper puck
            y1 = sy * L
            sweep(f"{tag} limb {sy} {sx}", [(sx * 0.016, 0, 0), (sx * 0.016, y1 * 0.5, 0.0), (sx * 0.016, y1, 0)],
                  [0.012, 0.011, 0.009], [0.018, 0.014, 0.01], G, lp)
            cyl(f"{tag} damper {sy} {sx}", 0.01, 0.012, DARK, 10, lp, loc=(sx * 0.016 - 0.006, y1 * 0.45, 0.0), axis="X")
        ax = empty(f"{tag} axle {sy}", (0, sy * L, 0), lp); tips.append(ax)
        rw = {"binary": 0.04, "hybrid": 0.045 if sy > 0 else 0.032, "single": 0.048 if sy < 0 else 0.026}[kind]
        cp = empty(f"{tag} cam pivot {sy}", (0, 0, 0), ax); cams.append((cp, sy)); cp.rotation_mode = "XYZ"
        # eccentric cam: an off-centre wheel profile plate with a cut-out, plus a module and a string track
        prof = [(math.cos(t) * rw * (1 + 0.28 * math.cos(t - 0.6)) + 0.008 * math.cos(t - 0.6),
                 math.sin(t) * rw * (1 + 0.28 * math.cos(t - 0.6))) for t in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
        holes = [] if rw < 0.03 else [loop2d(-rw * 0.25, 0.0, rw * 0.28, rw * 0.22, 8)]
        plate(f"{tag} cam {sy}", [(p[1], p[0]) for p in prof], [[(p[1], p[0]) for p in h] for h in holes], -0.009, 0.004, RM, cp)
        if rw >= 0.03:
            plate(f"{tag} cam module {sy}", [(p[1] * 0.55, p[0] * 0.55) for p in prof], [], 0.004, 0.008, W, cp)
        cyl(f"{tag} axle pin {sy}", 0.004, 0.03, GR, 6, ax, loc=(-0.015, 0, 0), axis="X")
    return tips, flex, cams


def sight_pins(tag, par, n, loc, housing=0.03, scope=False):
    sb = empty(f"{tag} sight", loc, par)
    bx_(tag, "sight bar", (-0.004, -0.006, 0.0), (0.004, 0.006, 0.09), G, sb)
    bx_(tag, "sight dovetail", (-0.006, -0.03, 0.0), (0.006, 0.03, 0.012), RM, sb)
    torus(f"{tag} sight housing", housing, 0.005, RM, parent=sb, loc=(0, 0, -0.03), axis="Z")
    pins = []
    for k in range(n):                                 # fibre pins: a stalk and a glowing dot
        y = housing * 0.6 - k * (housing * 1.2 / max(1, n - 1))
        stk = bx_(tag, f"pin stalk {k}", (housing * 0.15, y - 0.0012, -0.032), (housing, y + 0.0012, -0.028), DARK, sb)
        dot = ball(f"{tag} pin dot {k}", 0.0028, W, (housing * 0.15, y, -0.03), sb, 8)
        pins.append(dot)
    if scope:
        cyl(f"{tag} scope lens", housing * 0.9, 0.004, LENS, 16, sb, loc=(0, 0, -0.02), axis="Z")
        ball(f"{tag} level bubble", 0.004, W, (0, -housing - 0.006, -0.03), sb, 8)
    return sb, pins


def stab(tag, root, L, loc, ang=(0, 0, 0), w=3, side=False):
    p = empty(f"{tag} stab {L:.2f} {loc[0]:.2f}", loc, root); p.rotation_euler = tuple(R(a) for a in ang)
    cyl(f"{tag} stab rod {L:.2f}", 0.011, L, DARK, 10, p, loc=(0, 0, -L), axis="Z")
    cyl(f"{tag} stab collar {L:.2f}", 0.013, 0.02, RM, 10, p, loc=(0, 0, -0.02), axis="Z")
    for k in range(w):
        cyl(f"{tag} stab weight {L:.2f} {k}", 0.019, 0.016, RM if k % 2 == 0 else G, 12, p, loc=(0, 0, -L - 0.018 - k * 0.019), axis="Z")
    cyl(f"{tag} stab damper {L:.2f}", 0.014, 0.02, DARK, 12, p, loc=(0, 0, -L - 0.03 - w * 0.019), axis="Z", r2=0.008)
    return p


# ------------------------------------------------------------------ the eight bows (each riser built a different way)
def bow_B1a(tag, par):
    """Swept deflex riser (one bent bar with glowing ports), parallel limbs past horizontal, binary cams that roll over."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.33
    pts = [(0, -H, -0.06), (0, -0.22, -0.035), (0, -0.09, 0.0), (0, 0.0, 0.01), (0, 0.09, 0.0), (0, 0.22, -0.035), (0, H, -0.06)]
    sweep(f"{tag} riser", pts, 0.026, 0.05, G, root)
    sweep(f"{tag} riser spine", [(0.0, -H + 0.03, -0.095), (0, -0.12, -0.07), (0, 0.12, -0.07), (0, H - 0.03, -0.095)], 0.018, 0.016, G, root)
    for k, y in enumerate((-0.27, -0.17, 0.16, 0.25)):     # truss ties between spine and riser + ports
        rod(f"{tag} tie {k}", (0, y, -0.04), (0, y * 0.9, -0.085), 0.006, RM, root)
        torus(f"{tag} port {k}", 0.012, 0.0035, W, (0.014, y * 0.97, -0.05), root, 16, 6, axis="X")
    bx_(tag, "grip", (-0.018, -0.055, -0.015), (0.018, 0.055, 0.035), GR, root)
    for k in range(5):
        bx_(tag, f"grip groove {k}", (-0.019, -0.045 + k * 0.022, 0.03), (0.019, -0.04 + k * 0.022, 0.037), DARK, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.24, 62, "binary")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 4, (0.045, 0.13, -0.06))
    stab(tag, root, 0.62, (0, -0.08, -0.07), w=3)
    stab(tag, root, 0.3, (0, -0.1, -0.03), ang=(-20, 140, 0), w=4)       # back bar
    rod(f"{tag} cable guard", (0.0, -0.07, 0.0), (0.03, -0.07, 0.14), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=200, nock_y=0.075, compound=True)


def bow_B1b(tag, par):
    """Machined plate riser with triangle cut-outs (a real CNC look), hybrid cams, drop-away rest, offset V-bar."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.37
    outer = [(-H, -0.075), (-0.2, -0.08), (-0.07, -0.02), (-0.06, 0.035), (0.06, 0.035), (0.07, -0.02), (0.2, -0.08), (H, -0.075),
             (H, -0.03), (0.2, -0.035), (0.1, 0.01), (-0.1, 0.01), (-0.2, -0.035), (-H, -0.03)]
    holes = []
    for k in range(4):
        y0 = 0.1 + k * 0.065
        for sy in (-1, 1):
            a = (sy * y0, -0.072 + 0.003 * k); b = (sy * (y0 + 0.055), -0.074); c = (sy * (y0 + 0.03), -0.038 - 0.003 * k)
            holes.append(tri2d(a, b, c, 0.18) if sy > 0 else tri2d(a, c, b, 0.18))
    plate(f"{tag} riser", outer, holes, -0.013, 0.013, strip("r2", f"{tag} riser r2", alpha=0.92, emit=1.2), root, uvt=0.12)
    plate(f"{tag} riser rail", [(-H + 0.01, -0.082), (H - 0.01, -0.082), (H - 0.01, -0.076), (-H + 0.01, -0.076)], [], -0.015, 0.015, RM, root)
    bx_(tag, "grip", (-0.017, -0.05, -0.0), (0.017, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.25, 44, "hybrid")
    # drop-away rest: a launcher arm on a pivot, down at rest, up on the draw, drops at the shot
    rp = empty(f"{tag} rest pivot", (0.022, 0.06, -0.015), root)
    bx_(tag, "rest body", (-0.004, -0.02, -0.015), (0.012, 0.0, 0.015), DARK, rp)
    arm = empty(f"{tag} rest arm", (0.0, 0.0, 0.0), rp)
    bx_(tag, "rest launcher", (-0.022, -0.002, -0.003), (0.0, 0.002, 0.003), W, arm)
    bx_(tag, "rest fork", (-0.025, 0.0, -0.004), (-0.021, 0.012, 0.004), RM, arm)
    sight_pins(tag, root, 5, (0.045, 0.14, -0.07), housing=0.034)
    stab(tag, root, 0.55, (0, -0.06, -0.08), w=3)
    v = empty(f"{tag} v-bar", (0, -0.1, -0.03), root)
    for sx in (-1, 1):
        stab(tag, v, 0.26, (sx * 0.01, 0, 0), ang=(-25, sx * 35 + 180, 0), w=2)
    rod(f"{tag} cable guard", (0.0, -0.05, -0.0), (0.035, -0.05, 0.13), 0.004, G, root)
    bx_(tag, "cable slide", (0.025, -0.06, 0.12), (0.045, -0.04, 0.135), RM, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=150, nock_y=0.075, compound=True, rest=arm)


def bow_B1c(tag, par):
    """Pixel-sliced riser: the profile stacked from thin slices with traced outline rails; single cam + idler, a scope."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.34
    slices, rails = [], []
    n = 34
    for k in range(n):
        y = -H + (2 * H) * (k + 0.5) / n
        depth = 0.05 + 0.025 * math.cos(math.pi * y / H * 0.5) ** 2      # deeper in the middle
        zc = -0.04 + 0.04 * math.cos(math.pi * y / (2 * H))
        hole = abs(y) > 0.12 and (k % 4 in (1, 2))                     # windows through the slices
        if hole:
            slices.append(bx_(tag, f"slice {k} a", (-0.012, y - 0.0095, zc - depth / 2), (0.012, y + 0.0095, zc - depth / 2 + 0.012), G, root))
            slices.append(bx_(tag, f"slice {k} b", (-0.012, y - 0.0095, zc + depth / 2 - 0.012), (0.012, y + 0.0095, zc + depth / 2), G, root))
        else:
            slices.append(bx_(tag, f"slice {k}", (-0.012, y - 0.0095, zc - depth / 2), (0.012, y + 0.0095, zc + depth / 2), G if k % 2 else DARK, root))
    for side in (-1, 1):                                                 # outline rails traced along both faces
        pts = []
        for k in range(n + 1):
            y = -H + 2 * H * k / n
            depth = 0.05 + 0.025 * math.cos(math.pi * y / H * 0.5) ** 2; zc = -0.04 + 0.04 * math.cos(math.pi * y / (2 * H))
            pts.append((0, y, zc + side * depth / 2))
        rails.append(sweep(f"{tag} rail {side}", pts, 0.026, 0.004, RM, root))
    bx_(tag, "grip", (-0.017, -0.05, 0.0), (0.017, 0.05, 0.05), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.25, 40, "single")
    sight_pins(tag, root, 1, (0.05, 0.14, -0.08), housing=0.036, scope=True)
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    stab(tag, root, 0.7, (0, -0.07, -0.08), w=4)
    rod(f"{tag} cable guard", (0.0, -0.07, 0.0), (0.03, -0.07, 0.14), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=260, nock_y=0.075, compound=True, slices=slices, rails=rails)


def recurve_pts(sy, H, th0, k1, k2, L=0.62, n=14):
    """A recurve limb's centre line (bow frame): bends toward the archer (+Z), the last 30% curls back to the target."""
    pts = [Vector((0, sy * H, -0.03))]; th = R(th0); ds = L / (n - 1)
    for i in range(1, n):
        s = i / (n - 1)
        th = R(th0 + k1 * min(s, 0.7) - (k2 * (s - 0.7) if s > 0.7 else 0))
        p = pts[-1] + Vector((0, sy * math.cos(th) * ds, math.sin(th) * ds))
        pts.append(p)
    return pts


def bow_B2a(tag, par):
    """ILF Olympic recurve: limbs are smooth swept blades that bend by shape key (true curve change), clicker, plunger."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.3
    outer = [(-H, -0.06), (-0.12, -0.065), (-0.06, -0.02), (-0.055, 0.03), (0.055, 0.03), (0.08, 0.0), (0.2, 0.004), (H, -0.025), (H, -0.06),
             (0.12, -0.07), (-0.12, -0.07)]
    plate(f"{tag} riser", outer, [loop2d(-0.19, -0.04, 0.07, 0.012, 12), loop2d(0.2, -0.035, 0.05, 0.01, 10)], -0.014, 0.012, G, root)
    bx_(tag, "riser window shelf", (-0.016, 0.06, -0.03), (0.0, 0.065, 0.0), RM, root)
    bx_(tag, "grip", (-0.017, -0.06, -0.02), (0.017, 0.06, 0.04), GR, root)
    cyl(f"{tag} plunger", 0.004, 0.035, W, 8, root, loc=(-0.05, 0.078, -0.03), axis="X")
    cp = empty(f"{tag} clicker pivot", (-0.016, 0.08, -0.04), root)
    bx_(tag, "clicker blade", (-0.0015, -0.0005, -0.0), (0.0015, 0.008, 0.09), RM, cp)
    cp.rotation_euler = (R(-8), 0, 0)
    sb = empty(f"{tag} sight", (0.035, 0.15, -0.06), root)
    bx_(tag, "sight extension", (-0.006, -0.006, -0.32), (0.006, 0.006, 0.0), G, sb)
    bx_(tag, "sight block", (-0.012, -0.03, -0.34), (0.012, 0.03, -0.31), RM, sb)
    torus(f"{tag} sight aperture", 0.01, 0.0025, W, parent=sb, loc=(-0.02, 0.0, -0.33), axis="Z")
    stab(tag, root, 0.76, (0, -0.08, -0.07), w=3)
    v = empty(f"{tag} v-bar", (0, -0.1, -0.03), root)
    for sx in (-1, 1):
        stab(tag, v, 0.3, (sx * 0.01, 0, 0), ang=(-18, sx * 38 + 180, 0), w=2)
    tips = []; shapes = []
    for sy in (-1, 1):
        rest = recurve_pts(sy, H, 6, 40, 220); full = recurve_pts(sy, H, 13, 78, 230)
        ws = [0.044 - 0.03 * i / 13 for i in range(14)]; ts = [0.012 - 0.006 * i / 13 for i in range(14)]
        o = sweep(f"{tag} limb {sy}", rest, ws, ts, G, root, smooth=True)
        o.shape_key_add(name="Basis"); sk = o.shape_key_add(name="draw")
        for i, v_ in enumerate(sweep_verts(full, ws, ts)):
            sk.data[i].co = v_
        sweep(f"{tag} limb bolt {sy}", [rest[0] + Vector((0, -sy * 0.01, 0)), rest[0] + Vector((0, sy * 0.03, 0))], 0.05, 0.016, RM, root)
        tip = empty(f"{tag} tip {sy}", tuple(rest[-1]), root); tips.append(tip)
        shapes.append((sk, tip, rest[-1].copy(), full[-1].copy()))
    return dict(root=root, tips=tips, flex=[], shapes=shapes, nock_y=0.078, compound=False, clicker=cp)


def bow_B2b(tag, par):
    """Twin-ribbon riser (two twisting bands) and laminated limbs in 6 hinged segments that flex progressively."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.3
    for s in (-1, 1):
        pts = []
        for k in range(15):
            y = -H + 2 * H * k / 14
            ph = math.pi * k / 14 * 2
            pts.append((s * 0.008 * math.cos(ph), y, -0.04 + 0.022 * s * math.sin(ph) + 0.03 * math.cos(math.pi * y / (2 * H))))
        sweep(f"{tag} ribbon {s}", pts, 0.012, 0.03, G if s > 0 else RM, root, smooth=True)
    bx_(tag, "grip", (-0.016, -0.06, -0.01), (0.016, 0.06, 0.04), GR, root)
    cyl(f"{tag} plunger", 0.004, 0.035, W, 8, root, loc=(-0.05, 0.078, -0.03), axis="X")
    bx_(tag, "clicker", (-0.016, 0.08, -0.13), (-0.013, 0.084, -0.03), RM, root)
    sb = empty(f"{tag} sight", (0.035, 0.15, -0.06), root)
    bx_(tag, "sight extension", (-0.006, -0.006, -0.28), (0.006, 0.006, 0.0), G, sb)
    torus(f"{tag} sight aperture", 0.011, 0.003, W, parent=sb, loc=(-0.02, 0.0, -0.29), axis="Z")
    stab(tag, root, 0.7, (0, -0.08, -0.07), w=2)
    v = empty(f"{tag} v-bar", (0, -0.1, -0.03), root)
    for sx in (-1, 1):
        stab(tag, v, 0.28, (sx * 0.01, 0, 0), ang=(-30, sx * 30 + 180, 0), w=3)
    tips, chains = [], []
    rest_angles = [5, 8, 9, 10, -40, -50]
    for sy in (-1, 1):
        prev = empty(f"{tag} limb {sy}", (0, sy * H, -0.03), root); chain = []
        for k, ang in enumerate(rest_angles):
            seg = empty(f"{tag} limb seg {sy} {k}", (0, 0, 0) if k == 0 else (0, sy * 0.105, 0), prev)
            seg.rotation_euler = (R(sy * ang), 0, 0)
            w_ = 0.044 - 0.005 * k; ln = 0.105
            y0, y1 = (0, ln) if sy > 0 else (-ln, 0)
            bx_(tag, f"lam belly {sy} {k}", (-w_ / 2, y0, -0.006), (w_ / 2, y1, -0.002), G, seg)
            bx_(tag, f"lam core {sy} {k}", (-w_ / 2 + 0.003, y0, -0.002), (w_ / 2 - 0.003, y1, 0.002), DARK, seg)
            bx_(tag, f"lam back {sy} {k}", (-w_ / 2, y0, 0.002), (w_ / 2, y1, 0.006), RM if k >= 4 else G, seg)
            chain.append((seg, ang)); prev = seg
        tip = empty(f"{tag} tip {sy}", (0, sy * 0.105, 0), prev); tips.append(tip); chains.append((sy, chain))
    return dict(root=root, tips=tips, flex=[], chains=chains, nock_y=0.078, compound=False)


def bow_B2c(tag, par):
    """Faceted crystal riser (tilted blocks), rigid limbs on pivots with a sharp recurve, finger sling: the bow rolls
    forward out of the open hand after the shot (Olympic follow-through)."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.31
    for k in range(9):
        y = -H + 2 * H * (k + 0.5) / 9
        b = bx_(tag, f"facet {k}", (-0.014, -0.035, -0.035), (0.014, 0.035, 0.035), G if k % 2 else RM, root)
        b.location = (0, y, -0.04 + 0.025 * math.cos(math.pi * y / (2 * H))); b.rotation_euler = (R(45 + 8 * (k - 4)), R(10 * (-1) ** k), 0)
    bx_(tag, "grip", (-0.016, -0.06, -0.01), (0.016, 0.06, 0.04), GR, root)
    cyl(f"{tag} plunger", 0.004, 0.035, W, 8, root, loc=(-0.05, 0.078, -0.03), axis="X")
    bx_(tag, "clicker", (-0.016, 0.08, -0.13), (-0.013, 0.084, -0.03), RM, root)
    sb = empty(f"{tag} sight", (0.035, 0.15, -0.06), root)
    bx_(tag, "sight extension", (-0.006, -0.006, -0.3), (0.006, 0.006, 0.0), G, sb)
    torus(f"{tag} sight aperture", 0.011, 0.003, W, parent=sb, loc=(-0.02, 0.0, -0.31), axis="Z")
    stab(tag, root, 0.8, (0, -0.08, -0.07), w=3)
    v = empty(f"{tag} v-bar", (0, -0.1, -0.03), root)
    for sx in (-1, 1):
        stab(tag, v, 0.32, (sx * 0.01, 0, 0), ang=(-12, sx * 42 + 180, 0), w=2)
    tips, flex = [], []
    for sy in (-1, 1):
        lp = empty(f"{tag} limb {sy}", (0, sy * H, -0.03), root); lp.rotation_euler = (R(sy * 6), 0, 0)
        flex.append((lp, sy, 6))
        pts = recurve_pts(sy, 0.0, 0, 20, 360, 0.6, 10)
        pts = [p - Vector((0, 0, -0.03)) for p in pts]
        sweep(f"{tag} limb blade {sy}", pts, [0.046 - 0.032 * i / 9 for i in range(10)], 0.01, G, lp)
        sweep(f"{tag} limb edge {sy}", [p + Vector((0, 0, 0.006)) for p in pts], [0.03 - 0.02 * i / 9 for i in range(10)], 0.003, RM, lp)
        tips.append(empty(f"{tag} tip {sy}", tuple(pts[-1]), lp))
    sling = torus(f"{tag} finger sling", 0.05, 0.004, RM, parent=root, loc=(0.0, 0.0, 0.045), axis="Y")
    return dict(root=root, tips=tips, flex=flex, nock_y=0.078, compound=False, rollover=True, flexdeg=16)


def quiver(tag, root, n, loc, point):
    q = empty(f"{tag} quiver", loc, root)
    plate(f"{tag} quiver hood", [(0.2, -0.06), (0.32, -0.05), (0.33, 0.04), (0.2, 0.045)], [], -0.012, 0.03, G, q)
    bx_(tag, "quiver gripper", (-0.012, -0.22, -0.045), (0.03, -0.19, 0.03), RM, q)
    bx_(tag, "quiver spine", (0.004, -0.2, -0.03), (0.012, 0.21, -0.02), DARK, q)
    arrows = []
    for k in range(n):
        a_, _ = arrow2(f"{tag} quiver {k}", q, L=0.6, point=point, vanes=3, wrap=False)
        a_.location = (0.012, 0.3, -0.035 + k * 0.014); a_.rotation_euler = (R(-90), 0, 0)
        arrows.append(a_)
    return q, arrows


def bow_B3a(tag, par):
    """Short hunting plate riser with round ports, 7-pin sight on a slider, 5 mechanical broadheads in a quiver."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.28
    outer = [(-H, -0.07), (-0.08, -0.055), (-0.055, 0.035), (0.055, 0.035), (0.08, -0.055), (H, -0.07), (H, -0.02), (0.1, -0.005), (-0.1, -0.005), (-H, -0.02)]
    holes = [loop2d(sy * y, -0.045, 0.022, 0.014, 10) for sy in (-1, 1) for y in (0.13, 0.21)]
    plate(f"{tag} riser", outer, holes, -0.014, 0.014, strip("w1", f"{tag} riser w1", alpha=0.92, emit=1.2), root, uvt=0.1)
    bx_(tag, "grip", (-0.018, -0.05, 0.0), (0.018, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 48, "binary")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 7, (0.045, 0.13, -0.06), housing=0.036)
    stab(tag, root, 0.2, (0, -0.07, -0.07), w=2)
    q, qa = quiver(tag, root, 5, (0.05, 0.0, 0.0), "mech")
    torus(f"{tag} wrist sling", 0.04, 0.005, RM, parent=root, loc=(0, 0, 0.0), axis="Y")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=180, nock_y=0.075, compound=True, quiver=qa)


def bow_B3b(tag, par):
    """Carbon-tube truss riser (tubes and nodes, like a bike frame), single-pin slider sight with a rangefinder laser."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    nodes = [(0, -H, -0.06), (0, -0.16, -0.075), (0, -0.05, -0.02), (0, 0.05, -0.02), (0, 0.16, -0.075), (0, H, -0.06)]
    back = [(0, -H + 0.02, -0.01), (0, -0.15, 0.0), (0, 0.15, 0.0), (0, H - 0.02, -0.01)]
    for k in range(len(nodes) - 1):
        rod(f"{tag} tube front {k}", nodes[k], nodes[k + 1], 0.011, DARK, root)
    for k in range(len(back) - 1):
        rod(f"{tag} tube back {k}", back[k], back[k + 1], 0.008, G, root)
    for k, (a, b) in enumerate(((nodes[0], back[0]), (nodes[1], back[1]), (nodes[1], back[0]), (nodes[4], back[2]), (nodes[4], back[3]), (nodes[5], back[3]))):
        rod(f"{tag} tube web {k}", a, b, 0.006, G, root)
    for k, nd in enumerate(nodes + back):
        ball(f"{tag} node {k}", 0.014, RM, nd, root, 10)
    bx_(tag, "grip", (-0.018, -0.05, -0.025), (0.018, 0.05, 0.035), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.21, 44, "hybrid")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sb, pins = sight_pins(tag, root, 1, (0.05, 0.13, -0.07), housing=0.03)
    slide = pins[0]
    rf = empty(f"{tag} rangefinder", (0.0, 0.04, 0.02), sb)
    bx_(tag, "rangefinder body", (-0.012, -0.012, -0.04), (0.012, 0.012, 0.0), DARK, rf)
    cyl(f"{tag} rangefinder lens", 0.008, 0.004, LENS, 12, rf, loc=(0, 0, -0.044), axis="Z")
    stab(tag, root, 0.25, (0, -0.07, -0.07), w=2)
    q, qa = quiver(tag, root, 4, (0.05, 0.0, 0.0), "broad2")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=170, nock_y=0.075, compound=True, slide=slide, rf=rf, quiver=qa)


def bow_B3c(tag, par):
    """Chain-of-cubes riser (half-pixel cubes along the profile, two layers), 6-arrow quiver, built for a fast
    second shot: the draw hand takes a second arrow from the quiver and shoots again."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    cubes = []
    for k in range(30):
        y = -H + 2 * H * k / 29
        z = -0.035 + 0.035 * math.cos(math.pi * y / (2 * H))
        for layer, zz in enumerate((-0.022, 0.0, 0.022) if abs(y) < 0.1 else (-0.016, 0.016)):
            c = bx_(tag, f"cube {k} {layer}", (-0.013, -0.0095, -0.0095), (0.013, 0.0095, 0.0095), G if (k + layer) % 2 else DARK, root)
            c.location = (0, y, z + zz); c.rotation_euler = (R(8 * math.sin(k)), 0, 0); cubes.append(c)
    bx_(tag, "grip", (-0.018, -0.05, -0.0), (0.018, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 52, "binary")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 4, (0.045, 0.13, -0.06), housing=0.032)
    stab(tag, root, 0.18, (0, -0.07, -0.06), w=3)
    q, qa = quiver(tag, root, 6, (0.05, 0.0, 0.0), "broad4")
    torus(f"{tag} wrist sling", 0.04, 0.005, RM, parent=root, loc=(0, 0, 0.0), axis="Y")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=190, nock_y=0.075, compound=True, quiver=qa, cubes=cubes)


BOWS = {
 "B1a": dict(name="compound: swept riser", src="B1", build=bow_B1a, up=12, shots=[(15, 26, 34)], end=60,
             arrow=dict(vanes=4, vlen=0.075, vh=0.012, lit=True), form="ring",
             facts="one swept deflex riser with ports and a truss spine; parallel limbs; binary cams roll 200 deg on the draw; front + back bar; 4-pin; 4-vane arrow, lighted nock",
             lines=["Swept deflex riser (one bent bar) with glowing ports and", "a truss spine; parallel limbs past horizontal; binary cams",
                    "roll over on the draw; 0.62 front rod + back bar; 4-pin sight.", "Arrow: 4 vanes, lighted nock. Forms from ring pixels."]),
 "B1b": dict(name="compound: machined plate", src="B1", build=bow_B1b, up=12, shots=[(14, 24, 31)], end=58, release_aid=True,
             arrow=dict(vanes=3, vlen=0.09, vh=0.016), form="grip",
             facts="CNC plate riser with triangle cut-outs (R2 texture); hybrid cams; drop-away rest flips up, drops at the shot; caliper release opens at 31; offset V-bar",
             lines=["CNC plate riser with triangle cut-outs (your R2 texture);", "hybrid cams; drop-away rest flips up on the draw and drops",
                    "at the shot; caliper release on the ring hand opens at 31;", "front rod + offset V-bar; 5-pin sight. Builds out from the grip."]),
 "B1c": dict(name="compound: sliced riser", src="B1", build=bow_B1c, up=14, shots=[(16, 28, 36)], end=62,
             arrow=dict(vanes=4, vlen=0.06, vh=0.011, lit=True, barrel=True), form="outline",
             facts="riser stacked from 34 slices with windows, outline rails trace first; single cam + idler; scope with lens and level; 0.7 rod",
             lines=["Riser stacked from thin slices with windows; outline rails", "trace in first, then the slices fill; single cam + idler;",
                    "target scope with lens and level bubble; 0.7 front rod.", "Arrow: barrel shaft, 4 short vanes, lighted nock."]),
 "B2a": dict(name="Olympic: shape-key limbs", src="B2", build=bow_B2a, up=12, shots=[(15, 28, 35)], end=62, tab=True,
             arrow=dict(vanes=3, vlen=0.07, vh=0.012, helix=8, barrel=True, point="bullet"), form="tips", spin=1.2, clicker=True,
             facts="ILF riser plate with windows; limbs are smooth blades whose curve changes on the draw (shape key); clicker snaps at 34; spin-wing arrow spins in flight",
             lines=["ILF plate riser; limbs are smooth tapered blades whose whole", "curve changes on the draw (real bend, not a hinge); clicker",
                    "snaps at 34, release 35; finger tab; 0.76 long rod + V-bar.", "Barrelled target arrow with spin wings, spins in flight."]),
 "B2b": dict(name="Olympic: laminated limbs", src="B2", build=bow_B2b, up=12, shots=[(14, 26, 33)], end=60, tab=True,
             arrow=dict(vanes=3, vlen=0.06, vh=0.012, helix=12, point="bullet"), form="tips_in", spin=1.6,
             facts="twin twisting ribbon riser; limbs of 3 laminations in 6 hinged segments flexing more toward the tips; forms tip to centre",
             lines=["Twin twisting ribbon riser; each limb is 3 laminations in", "6 segments that flex progressively, most at the tips;",
                    "forms from the limb tips in to the grip; long rod + V-bar.", "Target arrow with curled spin wings."]),
 "B2c": dict(name="Olympic: faceted, bow rolls", src="B2", build=bow_B2c, up=12, shots=[(15, 27, 34)], end=62, tab=True,
             arrow=dict(vanes=3, vlen=0.065, vh=0.013, helix=8, point="bullet", barrel=True), form="facets", spin=1.0,
             facts="faceted crystal riser; rigid sharp-recurve limbs; after the shot the bow rolls forward out of the open hand on a finger sling",
             lines=["Faceted crystal riser; stiff sharp-recurve limbs on pivots;", "after the shot the bow rolls forward out of the open hand",
                    "and hangs on the finger sling (Olympic follow-through);", "0.8 long rod + wide V-bar."]),
 "B3a": dict(name="hunting: plate + mech heads", src="B3", build=bow_B3a, up=12, shots=[(14, 24, 30)], end=56,
             arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="mech"), form="grip", target="foam",
             facts="short ported plate riser (W1 texture); 7-pin sight; 5 mechanical broadheads in the quiver; blades open on impact in a foam block",
             lines=["Short plate riser with round ports (your W1 texture);", "7-pin sight, short stabiliser, wrist sling, 5-arrow quiver.",
                    "Mechanical broadhead: blades fold along the ferrule and", "flick open when it hits the foam block target."]),
 "B3b": dict(name="hunting: truss + rangefinder", src="B3", build=bow_B3b, up=12, shots=[(17, 26, 33)], end=58, release_aid=True,
             arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad2"), form="nodes", target="foam", laser=True,
             facts="carbon tube truss riser with nodes; rangefinder laser 12-17 reads 18, the single slider pin drops to 18; 2-blade cut-on-contact head",
             lines=["Carbon-tube truss riser (tubes between nodes); rangefinder", "laser 12-17 reads 18 blocks, the single slider pin drops to",
                    "match; hinge release; 4-arrow quiver.", "Arrow: 2-blade cut-on-contact broadhead."]),
 "B3c": dict(name="hunting: cube riser, two shots", src="B3", build=bow_B3c, up=10, shots=[(12, 20, 25), (33, 40, 45)], end=66,
             arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad4", lit=True), form="sweep", target="foam",
             facts="riser of half-pixel cubes; draw 12-20, release 25; takes a 2nd arrow from the quiver 27-32, draws 33-40, release 45",
             lines=["Riser chained from half-pixel cubes; compact; 6-arrow", "quiver. Fast hunter's follow-up: release 25, the ring hand",
                    "takes a second arrow from the quiver 27-32, draws 33-40,", "releases 45. 4-blade broadheads, lighted nocks."]),
}


def make_target(tag, bx, kind):
    if kind == "foam":
        tg = empty(f"{tag} target", (bx, 18.3, 1.3))
        box(f"{tag} foam core", (-0.45, -0.2, -0.45), (0.45, 0.25, 0.45), FOAM[0], tg)
        for k in range(1, 5):                            # dark foam layers between light ones, seen from the sides
            box(f"{tag} foam layer {k}", (-0.46, -0.2 + k * 0.09, -0.46), (0.46, -0.17 + k * 0.09, 0.46), FOAM[1], tg)
        cyl(f"{tag} vital", 0.12, 0.01, FOAM[2], 20, tg, loc=(0, -0.205, 0), axis="Y")
        box(f"{tag} target stand", (bx - 0.4, 18.2, 0), (bx + 0.4, 18.6, 0.85), STRAW)
        return Vector((bx, 18.1, 1.3))
    tg = empty(f"{tag} target", (bx, 18.3, 1.36)); tg.rotation_euler = (R(90), 0, 0)
    cyl(f"{tag} boss", 0.6, 0.3, STRAW, 24, tg, loc=(0, 0, -0.15))
    for i, m in enumerate(RINGS):
        cyl(f"{tag} face {i}", 0.55 - i * 0.11, 0.01, m, 24, tg, loc=(0, 0, 0.15 + i * 0.003))
    box(f"{tag} target stand", (bx - 0.05, 18.4, 0), (bx + 0.05, 18.5, 0.9), STRAW)
    return Vector((bx, 18.0, 1.36))


def archer_keys(T):
    """The shot keys for one or two shots (right-handed, ring on the draw hand)."""
    aim_l = dict(arm_l=(90, 0, 90), fore_l=(0, 0, 0))
    HEAD = (-4, 0, 82)
    brace_pt = Vector((-18 * P + 0.22, -0.02, 22 * P + 0.02))
    anchor = Vector((-0.27, -0.03, 1.47))
    keys = [(1, {}), (T["up"], dict(head=(0, 0, 40), arm_l=(60, 0, 60), fore_l=(20, 0, 0), ik_r=(Vector((0.1, 0.25, 1.1)), "hand", [60, 0, 30, 60])))]
    for i, (fd, ff, fr) in enumerate(T["shots"]):
        if i == 0:
            keys.append((fd, dict(head=HEAD, **aim_l, ik_r=(brace_pt, "hand", [90, 0, 80, 20]))))
        keys += [(fd + int((ff - fd) * 0.55), dict(head=HEAD, **aim_l, ik_r=(brace_pt.lerp(anchor, 0.75), "hand", [100, 0, 100, 90]))),
                 (ff, dict(head=HEAD, **aim_l, ik_r=(anchor, "hand", [100, 0, 100, 120]))),
                 (fr, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.01, 0, 0)), "hand", [100, 0, 100, 120]))),
                 (fr + 2, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.12, -0.02, 0.0)), "hand", [100, 0, 100, 120])))]
        if i + 1 < len(T["shots"]):                  # reach to the quiver on the bow, then back to the string
            nd = T["shots"][i + 1][0]
            keys += [(fr + 5, dict(head=HEAD, **aim_l, ik_r=(lambda p: fk(p, "l")[0] + Vector((0.12, 0.05, -0.06)), "hand", [70, 0, 60, 40]))),
                     (nd - 1, dict(head=HEAD, **aim_l, ik_r=(brace_pt, "hand", [90, 0, 80, 20])))]
    fr = T["shots"][-1][2]
    keys += [(fr + 10, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.14, -0.03, -0.02)), "hand", [100, 0, 100, 120])))]
    if not T.get("rollover_hold"):
        keys.append((min(T["end"] - 2, fr + 20), dict(head=(0, 0, 30), arm_l=(20, 0, 20), fore_l=(10, 0, 0))))
    return keys


def build_bow_take(code, bi):
    T = BOWS[code]; bx = bi * BAY; tag = f"BS2 {code}"
    box(f"{tag} floor", (bx - 2.6, -3, -0.02), (bx + 2.6, 21, 0), FLOOR)
    M = player_mats(tag); M["ring"] = mat(f"{tag} ring face", (0.02, 0.85, 0.15), emit=1.6)
    rig = make_player(tag, (bx, 0, 0), M, face=-math.pi / 2)
    solved, errs = build_keys(archer_keys(T))
    for f, p in solved:
        pp = dict(p); pp["root_loc"] = (bx, 0, 0); pose(rig, f, **pp)
    hl = empty(f"{tag} bow hand", (0, 0, -6 * P), rig["fore_l"])
    B = T["build"](tag, hl)
    broot = B["root"]
    END = T["end"]; shots = T["shots"]
    # accessories on the ring hand
    if T.get("tab"):
        box(f"{tag} finger tab", (-2.3 * P, -2.3 * P, -6.6 * P), (2.3 * P, -1.6 * P, -4.2 * P), RM, rig["fore_r"])
    jaws = []
    if T.get("release_aid"):
        box(f"{tag} release strap", (-2.3 * P, -2.3 * P, -1.5 * P), (2.3 * P, 2.3 * P, 0.0), DARK, rig["fore_r"])
        rod(f"{tag} release stem", (0, 0, -1.0 * P), (0, 0, -8.5 * P), 0.004, G, rig["fore_r"])
        hd = empty(f"{tag} release head", (0, 0, -8.6 * P), rig["fore_r"])
        box(f"{tag} release body", (-0.01, -0.008, -0.02), (0.01, 0.008, 0.0), RM, hd)
        for s in (-1, 1):
            j = empty(f"{tag} jaw {s}", (s * 0.006, 0, -0.02), hd)
            box(f"{tag} jaw blade {s}", (-0.002, -0.004, -0.012), (0.002, 0.004, 0.0), W, j); jaws.append((j, s))
    # brace: the string line between the tips at rest
    scene.frame_set(1); bpy.context.view_layer.update()
    inv = broot.matrix_world.inverted()
    tl = [inv @ t.matrix_world.translation for t in B["tips"]]
    brace = (tl[0].z + tl[1].z) / 2 + (0.0 if B["compound"] else 0.0)
    ny = B["nock_y"]
    # arrows: one per shot
    arrows = []
    for i in range(len(shots)):
        a_, ex = arrow2(f"{tag} shot {i}", None, **{k: v for k, v in T["arrow"].items()})
        a_.rotation_mode = "QUATERNION"; arrows.append((a_, ex))
    string_parts = []
    for sy in (-1, 1):
        s_ = cyl(f"{tag} string {sy}", 0.0025, 1.0, STR, 6, None, axis="Z"); s_.rotation_mode = "QUATERNION"; string_parts.append((s_, sy))
        s2 = cyl(f"{tag} serving {sy}", 0.0034, 1.0, DARK, 6, None, axis="Z"); s2.rotation_mode = "QUATERNION"; string_parts.append((s2, sy * 3))
        if B["compound"]:
            c_ = cyl(f"{tag} cable {sy}", 0.0018, 1.0, G, 5, None, axis="Z"); c_.rotation_mode = "QUATERNION"; string_parts.append((c_, sy * 2))
    peep = None
    if B["compound"]:
        peep = torus(f"{tag} peep", 0.008, 0.002, RM, axis="Z"); peep.rotation_mode = "QUATERNION"
        dloop = torus(f"{tag} d-loop", 0.009, 0.002, RM, axis="X"); dloop.rotation_mode = "QUATERNION"
    else:
        dloop = None
        kisser = ball(f"{tag} kisser", 0.006, W, (0, 0, 0), None, 10)
    target = make_target(tag, bx, T.get("target", "boss"))
    tgts = [target + Vector((0.0, 0, 0.05)), target + Vector((0.07, 0, -0.04))]
    flights = [None] * len(shots); hits = [None] * len(shots)
    quiver_src = B.get("quiver", [None])[-1] if len(shots) > 1 else None

    def state(f):
        for i, (fd, ff, fr) in enumerate(shots):
            if fd <= f < fr:
                return smooth((f - fd) / (ff - fd)), None, i
            if fr <= f < fr + 5:
                return 0.0, f - fr, i
        return 0.0, None, None

    laser = None
    if T.get("laser"):
        laser = cyl(f"{tag} laser", 0.0018, 1.0, LASER, 6, None, axis="Z"); laser.rotation_mode = "QUATERNION"
        show(laser, 12, 18)
        rd = label("18", (0.0, 0.0, 0.0), LASER, 0.035, (0, 0, 0)); rd.parent = B["rf"]; rd.location = (0.03, 0.02, -0.02)
        rd.rotation_euler = (R(90), 0, R(90)); show(rd, 14, 26)
    for f in range(1, END + 1):
        scene.frame_set(f); bpy.context.view_layer.update()
        u, snap, si = state(f)
        # limb flex, cams roll, shape keys, rest, clicker, rollover, jaws: keyed first, then re-evaluated
        for lp, sy, a0 in B.get("flex", []):
            key(lp, f, rot=(R(sy * (a0 + B.get("flexdeg", 14) * u)), 0, 0))
        for cp, sy in B.get("cams", []):
            key(cp, f, rot=(R(-sy * B["roll"] * u), 0, 0))
        for sk, tip, a, b in B.get("shapes", []):
            sk.value = u; sk.keyframe_insert("value", frame=f); key(tip, f, loc=tuple(a.lerp(b, u)))
        for sy, chain in B.get("chains", []):
            for k, (seg, ang) in enumerate(chain):
                key(seg, f, rot=(R(sy * (ang + u * (3 + 4 * k))), 0, 0))
        if "rest" in B:
            on = any(fd - 2 <= f < fr + 1 for fd, ff, fr in shots)
            key(B["rest"], f, rot=(0, 0, R(0 if on else -70)))
        if B.get("clicker") is not None:
            ff, fr = shots[0][1], shots[0][2]
            key(B["clicker"], f, rot=(R(-8 if f < fr - 1 else 12), 0, 0))
        if B.get("rollover"):
            fr = shots[0][2]
            t = smooth((f - fr) / 8.0)
            key(broot, f, rot=(R(-62 * t), 0, R(4 * t)), loc=(0, -0.05 * t, -0.02 + 0.03 * t))
        for j, s in jaws:
            closed = any(fd - 1 <= f < fr for fd, ff, fr in shots)
            key(j, f, rot=(0, R(0 if closed else s * 35), 0))
        if "slide" in B:
            key(B["slide"], f, loc=(0.0045, 0.018 - 0.03 * smooth((f - 14) / 4.0), -0.03))
        scene.frame_set(f); bpy.context.view_layer.update()
        Mb = broot.matrix_world
        fwd = (Mb.to_3x3() @ Vector((0, 0, -1))).normalized(); up = (Mb.to_3x3() @ Vector((0, 1, 0))).normalized()
        tipw = [t.matrix_world.translation.copy() for t in B["tips"]]
        rest_nock = Mb @ Vector((0, ny, brace))
        hand = rig["hand_pt"].matrix_world.translation.copy()
        if u > 0:
            nock = rest_nock.lerp(hand + Vector((0, 0, 0.02)), u)
        elif snap is not None:
            nock = rest_nock + fwd * (0.03 * math.cos(snap * 2.4) * math.exp(-snap * 0.6))
        else:
            nock = rest_nock
        for s_, sy in string_parts:
            a = tipw[0] if sy < 0 else tipw[1]
            if abs(sy) == 1:
                b = nock
            elif abs(sy) == 3:                        # centre serving: the last 9 cm each side of the nock
                b = nock; a = nock + (a - nock).normalized() * 0.09
            else:
                b = Mb @ Vector((0.016, (0.18 if sy > 0 else -0.18), brace - 0.01))
            d = b - a; L = max(1e-4, d.length)
            s_.location = a; s_.rotation_quaternion = d.to_track_quat("Z", "Y"); s_.scale = (1, 1, L)
            for path in ("location", "rotation_quaternion", "scale"):
                s_.keyframe_insert(path, frame=f)
        if peep is not None:
            peep.location = nock + up * 0.11; peep.rotation_quaternion = fwd.to_track_quat("Z", "Y")
            peep.keyframe_insert("location", frame=f); peep.keyframe_insert("rotation_quaternion", frame=f)
            dloop.location = nock - fwd * 0.012; dloop.rotation_quaternion = fwd.to_track_quat("Z", "Y")
            dloop.keyframe_insert("location", frame=f); dloop.keyframe_insert("rotation_quaternion", frame=f)
        if dloop is None:
            kisser.location = nock + up * 0.085; kisser.keyframe_insert("location", frame=f)
        if laser is not None:
            a = B["rf"].matrix_world.translation; d = tgts[0] - a
            laser.location = a; laser.rotation_quaternion = d.to_track_quat("Z", "Y"); laser.scale = (1, 1, d.length)
            for path in ("location", "rotation_quaternion", "scale"):
                laser.keyframe_insert(path, frame=f)
        for i, (ar, ex) in enumerate(arrows):
            fd, ff, fr = shots[i]
            if f < fr:
                if i > 0 and f < shots[i - 1][2] + 3 and quiver_src is not None:     # still in the quiver
                    qm = quiver_src.matrix_world
                    ar.location = qm.translation; ar.rotation_quaternion = qm.to_quaternion()
                elif i > 0 and f < fd:                                             # carried to the string
                    t = smooth((f - shots[i - 1][2] - 3) / max(1, fd - shots[i - 1][2] - 3))
                    ar.location = hand.lerp(rest_nock, t); ar.rotation_quaternion = fwd.to_track_quat("-Z", "Y")
                else:
                    ar.location = nock; ar.rotation_quaternion = fwd.to_track_quat("-Z", "Y")
                ar.keyframe_insert("location", frame=f); ar.keyframe_insert("rotation_quaternion", frame=f)
            else:
                if flights[i] is None:
                    flights[i] = nock.copy()
                p0 = flights[i]; k = f - fr; tg = tgts[i]
                stop = (tg - p0).length - 0.6
                dist = min(5.0 * k, stop)
                if hits[i] is None and 5.0 * k >= stop:
                    hits[i] = f
                p = p0 + (tg - p0).normalized() * dist + Vector((0, 0, -0.0004 * dist * dist))
                q = (tg - p0).normalized().to_track_quat("-Z", "Y")
                if T.get("spin") and hits[i] is None:
                    q = q @ Quaternion((0, 0, 1), T["spin"] * k)
                elif T.get("spin"):
                    q = q @ Quaternion((0, 0, 1), T["spin"] * (hits[i] - fr))
                ar.location = p; ar.rotation_quaternion = q
                ar.keyframe_insert("location", frame=f); ar.keyframe_insert("rotation_quaternion", frame=f)
    if quiver_src is not None:                                          # the quiver arrow that was taken
        key(quiver_src, 1, sc=1.0); key(quiver_src, shots[0][2] + 3, sc=1.0); key(quiver_src, shots[0][2] + 4, sc=0.0001)
    for i, (ar, ex) in enumerate(arrows):                               # arrows form (the first on the string)
        a0 = 8 if i == 0 else shots[0][2] + 3
        for o in ar.children_recursive:
            if o.type == "MESH":
                if i == 0:
                    key(o, 1, sc=0.0001); key(o, a0, sc=0.0001); key(o, a0 + 4, sc=1.0)
                else:
                    key(o, 1, sc=0.0001); key(o, a0, sc=0.0001); key(o, a0 + 1, sc=1.0)
        for h in ex.get("mech", []):                                    # mechanical blades flick open on impact
            key(h, 1, rot=(0, 0, 0)); key(h, hits[i] or END, rot=(0, 0, 0)); key(h, (hits[i] or END) + 1, rot=(0, R(-55), 0))
        if hits[i]:
            ripple = torus(f"{tag} hit flash {i}", 0.05, 0.006, CM["pix"], loc=tuple(tgts[i] + Vector((0, -0.1, 0))), axis="Y")
            key(ripple, 1, sc=0.0001); key(ripple, hits[i] - 1, sc=0.0001); key(ripple, hits[i], sc=1.0); key(ripple, hits[i] + 4, sc=2.6)
            key(ripple, hits[i] + 5, sc=0.0001)
    # the bow forms, each a different way
    meshes = [o for o in broot.children_recursive if o.type == "MESH"]
    ring_src = None
    scene.frame_set(4); bpy.context.view_layer.update(); ring_w = rig["ring_pt"].matrix_world.translation.copy()
    scene.frame_set(T["up"]); bpy.context.view_layer.update(); grip_w = broot.matrix_world.translation.copy()
    fu = T["up"]
    mode = T["form"]
    if mode == "ring":           # pixels stream from the ring to every part, in order from the ring outward
        form_by(meshes, 3, fu, lambda p: (p - ring_w).length, ring_w, CM["pix"], tag, 0.55, fu)
    elif mode == "grip":         # grows out from the grip
        form_by(meshes, 2, fu, lambda p: (p - grip_w).length, None, None, tag, 0.0, fu)
    elif mode == "outline":      # outline rails trace end to end first, then slices and parts fill
        rails = B["rails"]; rest = [o for o in meshes if o not in rails]
        for k, r_ in enumerate(rails):
            key(r_, 1, sc=(1, 0.0001, 1)); key(r_, 2 + k, sc=(1, 0.0001, 1)); key(r_, 6 + k, sc=(1, 1, 1))
        form_by(rest, 6, fu, lambda p: (p - grip_w).length, None, None, tag, 0.0, fu)
    elif mode in ("tips", "tips_in"):  # from the limb tips in to the grip (or the reverse)
        sgn = -1 if mode == "tips_in" else 1
        form_by(meshes, 2, fu, lambda p: sgn * (p - grip_w).length, ring_w, CM["pix"], tag, 0.3, fu)
    elif mode == "facets":       # random facets flash in like crystals growing
        form_by(meshes, 2, fu, lambda p: rng.random(), None, None, tag, 0.0, fu, grow=1)
    elif mode == "nodes":        # nodes first, then the tubes between them, then the rest
        form_by(meshes, 2, fu, lambda p: (0 if False else 0) + (p - grip_w).length * 0.3 + rng.random() * 0.2, ring_w, CM["pix"], tag, 0.25, fu)
    else:                        # a sweep from bottom to top
        form_by(meshes, 2, fu, lambda p: p.z, ring_w, CM["pix"], tag, 0.35, fu)
    for s_, sy in string_parts:
        s_.hide_render = True; s_.keyframe_insert("hide_render", frame=1); s_.hide_render = False; s_.keyframe_insert("hide_render", frame=fu - 2)
    for o in [peep, dloop] if peep is not None else [kisser]:
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=fu - 2)
    cam(f"Cam {code}", (bx + 3.6, -1.0, 2.0), (bx - 0.2, 1.2, 1.3), 32)
    cam(f"Cam {code} close", (bx + 2.3, 1.2, 1.75), (bx - 0.1, 0.45, 1.4), 32)
    cam(f"Cam {code} target", (bx + 1.5, 16.0, 1.8), (bx, 18.2, 1.35), 30)
    board(tag, (bx, 3.0, 3.0), f"{code}  {T['name'].upper()}", T["lines"])
    return errs


# ------------------------------------------------------------------ shields
def shield_frame(tag, parent, centre_w, f=20):
    """An empty under the forearm whose axes are world-aligned at the guard (x right, y toward the threat, z up) and
    whose origin sits at centre_w then."""
    scene.frame_set(f); bpy.context.view_layer.update()
    Mw = parent.matrix_world
    e = empty(f"{tag} shield frame", (0, 0, 0), parent)
    e.location = Mw.inverted() @ Vector(centre_w)
    e.rotation_euler = Mw.to_3x3().normalized().inverted().to_euler()
    return e


GUARD = dict(arm_r=(80, 0, 10), fore_r=(85, 0, 0), arm_l=(70, 0, -20), fore_l=(70, 0, 0), leg_l=(18, 0, 0), shin_l=(-14, 0, 0), leg_r=(-10, 0, 0), body=(-4, 0, 0))
GIVE = dict(arm_r=(72, 0, 10), fore_r=(95, 0, 0), arm_l=(64, 0, -20), fore_l=(78, 0, 0), leg_l=(14, 0, 0), shin_l=(-10, 0, 0), leg_r=(-14, 0, 0), body=(4, 0, 0))
F_HIT = 30


def pose_keys(rig, bx, keys):
    for f, d in keys:
        pp = dict(IDLE); pp.update(d); rl = pp.pop("root_loc", (0, 0, 0)); pp["root_loc"] = (bx + rl[0], rl[1], rl[2]); pose(rig, f, **pp)


def incoming(tag, bx, impact_w):
    sb = box(f"{tag} incoming shot", (-0.1, -0.1, -0.1), (0.1, 0.1, 0.1), SHOT)
    key(sb, 1, loc=(bx, 8.0, 1.4), sc=0.0001); key(sb, 20, loc=(bx, 8.0, 1.4), sc=1.0); key(sb, F_HIT, loc=tuple(impact_w + Vector((0, 0.12, 0))), sc=1.0)
    sb.scale = (1, 1, 1); shatter([sb], F_HIT + 1, SHOT, rng, tag, n=8, speed=0.08)


def impact_world(obj_parent, local, f=F_HIT):
    scene.frame_set(f); bpy.context.view_layer.update()
    return obj_parent.matrix_world @ Vector(local)


def build_H2a(tag, rig, bx):
    """Curved brick tower: courses of offset bricks on a cylinder (your BR1 bricks), built course by course from the
    forearm out; a hit sends a ripple ring across the face. 1.0 x 1.8 blocks."""
    pose_keys(rig, bx, [(1, {}), (6, GUARD), (28, GUARD), (31, GIVE), (40, GUARD), (56, {})])
    sf = shield_frame(tag, rig["fore_r"], (bx, 0.48, 0.95))
    BRM = strip("br1", f"{tag} bricks", alpha=0.9, emit=1.3)
    Rc = 1.15; Wd = 1.0; Ht = 1.8; rows = 9; parts = []
    span = Wd / Rc
    for i in range(rows):
        z0 = -Ht / 2 + i * Ht / rows; z1 = z0 + Ht / rows - 0.012
        nb = 4; off = 0.5 if i % 2 else 0.0
        edges = [(-span / 2 + (k + off) * span / nb) for k in range(-1, nb + 1)]
        edges = sorted(set(min(span / 2, max(-span / 2, e)) for e in edges))
        for k in range(len(edges) - 1):
            a0, a1 = edges[k] + 0.006 / Rc, edges[k + 1] - 0.006 / Rc
            if a1 - a0 < 0.02:
                continue
            arc = np.linspace(a0, a1, 5)
            vs = []
            for r_ in (Rc, Rc + 0.035):
                for z in (z0, z1):
                    for a in arc:
                        vs.append((r_ * math.sin(a), r_ * math.cos(a) - Rc, z))
            n = len(arc)
            def vi(ri, zi, ai):
                return ri * 2 * n + zi * n + ai
            fs = []
            for ai in range(n - 1):
                fs += [(vi(0, 0, ai), vi(0, 0, ai + 1), vi(0, 1, ai + 1), vi(0, 1, ai)), (vi(1, 0, ai), vi(1, 1, ai), vi(1, 1, ai + 1), vi(1, 0, ai + 1)),
                       (vi(0, 0, ai), vi(1, 0, ai), vi(1, 0, ai + 1), vi(0, 0, ai + 1)), (vi(0, 1, ai), vi(0, 1, ai + 1), vi(1, 1, ai + 1), vi(1, 1, ai))]
            fs += [(vi(0, 0, 0), vi(0, 1, 0), vi(1, 1, 0), vi(1, 0, 0)), (vi(0, 0, n - 1), vi(1, 0, n - 1), vi(1, 1, n - 1), vi(0, 1, n - 1))]
            parts.append(mesh_obj(f"{tag} brick {i} {k}", vs, fs, BRM, sf, uvt=0.3))
    for s in (-1, 1):                                    # rim posts down both edges and a top and bottom lip
        a = s * span / 2
        parts.append(sweep(f"{tag} rim {s}", [(Rc * math.sin(a), (Rc * math.cos(a) - Rc), z) for z in (-Ht / 2, Ht / 2)], 0.05, 0.05, RM, sf, side=(0, 1, 0)))
    for z in (-Ht / 2 - 0.02, Ht / 2 + 0.02):
        parts.append(sweep(f"{tag} lip {z:.2f}", [(Rc * math.sin(a), (Rc * math.cos(a) - Rc) + 0.02, z) for a in np.linspace(-span / 2, span / 2, 9)], 0.04, 0.03, RM, sf, side=(0, 0, 1)))
    parts.append(box(f"{tag} handle", (-0.08, -0.06, -0.04), (0.08, -0.01, 0.04), GR, sf))
    form_by(parts, 2, 10, lambda p: (p - rig["fore_r"].matrix_world.translation).length, None, None, tag, 0.0, 10)
    imp_l = (0.1, 0.08, 0.25)
    imp = impact_world(sf, imp_l)
    rp = torus(f"{tag} ripple", 0.06, 0.012, CM["pix"], parent=sf, loc=(0.1, 0.06, 0.25), axis="Y")
    key(rp, 1, sc=0.0001); key(rp, F_HIT, sc=0.0001); key(rp, F_HIT + 1, sc=1.0); key(rp, F_HIT + 6, sc=8.0); key(rp, F_HIT + 7, sc=0.0001)
    anim_emit(BRM, [(1, 1.3), (F_HIT, 1.3), (F_HIT + 1, 3.0), (F_HIT + 8, 1.3)])
    return imp, 31


def build_H2b(tag, rig, bx):
    """Riot wall: one flat panel of your W1 weave with a viewport slot; the rim traces round the outline first, then the
    panel fades in; the player drops to a knee and plants the foot spike. A hit spreads cracks that heal. 1.0 x 1.9.
    rev 2 (J: "shield in third person collides with arms"): the wall is held from behind by two grip bars, one per hand,
    each 1.2 cm in front of the hand's end, on standoffs to the panel; the arms never touch the wall (checked every frame)."""
    LEGS = dict(leg_l=(85, 0, 0), shin_l=(-85, 0, 0), leg_r=(0, 0, 0), shin_r=(-90, 0, 0), body=(-2, 0, 0))
    HOLD = dict(IDLE); HOLD.update(LEGS)
    sf = empty(f"{tag} shield frame", (0.02, 0.66, 1.27), rig["root"])      # root space: bottom 2 cm off the ground kneeling
    grips = {"r": Vector((0.15, 0.42, 1.3)), "l": Vector((-0.15, 0.42, 1.08))}
    for side in ("r", "l"):
        a, fo, err = solve(HOLD, side, grips[side], "hand", [80.0, 0.0, 0.0, 30.0])
        HOLD["arm_" + side], HOLD["fore_" + side] = a, fo
    K = dict(HOLD, root_loc=(0, 0, -0.3))
    pose_keys(rig, bx, [(1, {}), (5, K), (28, K), (30, dict(K, head=(-8, 0, 0), root_loc=(0, -0.035, -0.3))),
                        (34, dict(K, root_loc=(0, -0.012, -0.3))), (40, K), (53, K), (61, {})])
    Wd, Ht = 1.0, 1.9
    outer = [(-Wd / 2 + 0.08, -Ht / 2), (Wd / 2 - 0.08, -Ht / 2), (Wd / 2, -Ht / 2 + 0.08), (Wd / 2, Ht / 2 - 0.12), (Wd / 2 - 0.12, Ht / 2),
             (-Wd / 2 + 0.12, Ht / 2), (-Wd / 2, Ht / 2 - 0.12), (-Wd / 2, -Ht / 2 + 0.08)]
    slot = [(-0.3, 0.55), (0.3, 0.55), (0.3, 0.63), (-0.3, 0.63)]
    PM = strip("w1", f"{tag} weave", alpha=0.85, emit=1.3)
    # plate() builds in YZ extruded along X; build then turn it to face +Y
    holder = empty(f"{tag} panel holder", (0, 0, 0), sf); holder.rotation_euler = (0, 0, R(90))
    pan = plate(f"{tag} panel", [(-x, z) for x, z in outer], [[(-x, z) for x, z in slot]], -0.015, 0.015, PM, holder, uvt=0.35)
    glassm = mat(f"{tag} viewport glass", (0.05, 0.5, 0.18), emit=0.4, alpha=0.3, rough=0.05)
    glass = plate(f"{tag} viewport", [(-x, z) for x, z in slot], [], -0.006, 0.006, glassm, holder)
    loop = outer + [outer[0]]
    rim = []
    for k in range(len(outer)):
        a = Vector((loop[k][0], 0.0, loop[k][1])); b = Vector((loop[k + 1][0], 0.0, loop[k + 1][1]))
        rim.append(sweep(f"{tag} rim {k}", [a, b], 0.06, 0.035, RM, sf, side=(0, 1, 0)))
    spike = empty(f"{tag} foot", (0, 0, -Ht / 2), sf)
    plate(f"{tag} foot spike", [(-0.1, 0.0), (0.1, 0.0), (0.0, -0.18)], [], -0.02, 0.02, RM, spike).rotation_euler = (0, 0, R(90))
    # grip bars: across each forearm's axis, just past the hand, joined to the panel's back by two standoffs
    held = []
    for side in ("r", "l"):
        hand, _, el = fk(HOLD, side)
        d = (hand - el).normalized()
        up = Vector((0, 0, 1)); up = (up - d * up.dot(d)).normalized()
        c = hand + d * (0.012 + 0.014) - sf.location
        a_, b_ = c - up * 0.11, c + up * 0.11
        held.append(rod(f"{tag} grip bar {side}", a_, b_, 0.014, GR, sf, 10))
        for k, e in enumerate((a_, b_)):
            held.append(rod(f"{tag} grip standoff {side} {k}", e, Vector((e.x, -0.016, e.z)), 0.01, RM, sf, 8))
    # formation (once the hands are up): rim traces 5-10, panel fades in 9-14, grips 6-8, spike drives at 11
    for k, r_ in enumerate(rim):
        f_ = 5 + int(k * 5 / len(rim))
        key(r_, 1, sc=(0.0001, 1, 1)); key(r_, f_, sc=(0.0001, 1, 1)); key(r_, f_ + 1, sc=(1, 1, 1))
    for o in held:
        key(o, 1, sc=0.0001); key(o, 6, sc=0.0001); key(o, 8, sc=1.0)
    key(glass, 1, sc=0.0001); key(glass, 10, sc=0.0001); key(glass, 12, sc=1.0)
    al = strip_alpha_socket(PM)
    for f_, v in ((1, 0.0), (9, 0.0), (14, 0.85), (50, 0.85), (53, 0.0)):
        al.default_value = v; al.keyframe_insert("default_value", frame=f_)
    key(spike, 1, sc=0.0001); key(spike, 9, sc=0.0001, loc=(0, 0, -Ht / 2 + 0.2)); key(spike, 11, sc=1.0, loc=(0, 0, -Ht / 2))
    for o in rim + held + [glass, spike]:                # it lets go before the arms come down
        key(o, 50, sc=1.0); key(o, 53, sc=(0.0001, 1, 1) if o in rim else 0.0001)
    dust = box(f"{tag} plant dust", (-0.05, -0.05, -0.05), (0.05, 0.05, 0.05), CM["pix"])
    scene.frame_set(11); bpy.context.view_layer.update(); foot_w = spike.matrix_world.translation.copy()
    dust.location = foot_w; shatter([dust], 11, CM["pix"], rng, tag, n=10, speed=0.06, life=10)
    imp_l = (-0.12, 0.04, 0.2)
    imp = impact_world(sf, imp_l)
    for k in range(9):                                   # cracks: thin glowing lines from the hit point, then heal
        an = 2 * math.pi * k / 9 + rng.uniform(-0.2, 0.2); ln = rng.uniform(0.18, 0.4)
        cp = empty(f"{tag} crack {k}", (imp_l[0], 0.025, imp_l[2]), sf); cp.rotation_euler = (0, -an, 0)
        c = box(f"{tag} crack line {k}", (0, -0.003, -0.004), (ln, 0.003, 0.004), CM["pix"], cp)
        key(c, 1, sc=(0.0001, 1, 1)); key(c, F_HIT, sc=(0.0001, 1, 1)); key(c, F_HIT + 2, sc=(1, 1, 1)); key(c, F_HIT + 12, sc=(1, 1, 1)); key(c, F_HIT + 18, sc=(0.0001, 1, 1))
    return imp, 31


def build_H2c(tag, rig, bx):
    """Telescoping heater: seven curved slats of your H1 hex stack at the forearm, then slide out up and down into a
    heater-shield outline 1.0 x 1.7 with an overshoot; on the hit the slats rock back one after another (a wave)."""
    pose_keys(rig, bx, [(1, {}), (5, GUARD), (28, GUARD), (31, GIVE), (40, GUARD), (56, {})])
    sf = shield_frame(tag, rig["fore_r"], (bx, 0.46, 1.0))
    HM = strip("h1", f"{tag} hex", alpha=0.88, emit=1.3)
    rows = 7; Ht = 1.7; slats = []
    for i in range(rows):
        zc = Ht / 2 - (i + 0.5) * Ht / rows
        t = i / (rows - 1)
        w_ = 1.0 if t < 0.5 else 1.0 - 0.85 * ((t - 0.5) / 0.5) ** 1.3   # heater: square top, pointed bottom
        piv = empty(f"{tag} slat pivot {i}", (0, 0, 0), sf)
        pts = [(x, 0.08 * (1 - (2 * x / 1.0) ** 2), 0) for x in np.linspace(-w_ / 2, w_ / 2, 9)]
        s = sweep(f"{tag} slat {i}", pts, Ht / rows + 0.03, 0.03, HM, piv, side=(0, 0, 1))
        sweep(f"{tag} slat edge {i}", [(p[0], p[1] + 0.02, Ht / rows / 2 + 0.01) for p in pts], 0.02, 0.012, RM, piv, side=(0, 0, 1))
        slats.append((piv, zc, s))
    box(f"{tag} handle", (-0.1, -0.07, -0.05), (0.1, -0.02, 0.05), GR, sf)
    boss = ball(f"{tag} boss", 0.07, W, (0, 0.12, Ht / 2 - 1.5 * Ht / rows), sf, 12)
    for i, (piv, zc, s) in enumerate(slats):
        f_out = 3 + abs(i - 1)                           # slide out from the second slat (the forearm) both ways
        key(piv, 1, loc=(0, 0, Ht / 2 - 1.5 * Ht / rows), sc=0.0001); key(piv, 2, loc=(0, 0, Ht / 2 - 1.5 * Ht / rows), sc=1.0)
        key(piv, f_out, loc=(0, 0, Ht / 2 - 1.5 * Ht / rows))
        key(piv, f_out + 3, loc=(0, 0, zc + (0.04 if zc > 0 else -0.04)))
        key(piv, f_out + 5, loc=(0, 0, zc))
    imp_l = (0.08, 0.1, 0.2)
    imp = impact_world(sf, imp_l)
    for i, (piv, zc, s) in enumerate(slats):             # the wave: each slat rocks back, delayed by distance
        d = int(abs(zc - imp_l[2]) / 0.25)
        key(piv, 1, rot=(0, 0, 0)); key(piv, F_HIT + d, rot=(0, 0, 0)); key(piv, F_HIT + d + 2, rot=(R(-14), 0, 0)); key(piv, F_HIT + d + 6, rot=(R(4), 0, 0))
        key(piv, F_HIT + d + 9, rot=(0, 0, 0))
    form_by([boss], 6, 7, lambda p: 0, None, None, tag)
    return imp, 32


def build_H3a(tag, rig, bx):
    """Geodesic cap: triangle cells cut from a subdivided sphere (radius 1.3, 1.7 across), held out with both hands; it
    forms in a spiral from the centre; the hit lights rings of cells outward from the impact."""
    BRACE = dict(GUARD, arm_l=(78, 0, -30), fore_l=(80, 0, 0))
    BGIVE = dict(GIVE, arm_l=(70, 0, -30), fore_l=(88, 0, 0))
    pose_keys(rig, bx, [(1, {}), (6, BRACE), (28, BRACE), (31, BGIVE), (40, BRACE), (56, {})])
    sf = shield_frame(tag, rig["fore_r"], (bx, 0.55, 1.05))
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.3)
    Rs = 1.3; cap = math.cos(R(42))
    bands = [mat(f"{tag} cell band {k}", tuple(np.array(CORPS["green"]) * 0.5), emit=0.9, alpha=0.6, rough=0.15) for k in range(7)]
    imp_l = Vector((0.15, 0.05, 0.2))
    cells = []
    for fc in bm.faces:
        c = fc.calc_center_median()
        if c.normalized().y < cap:
            continue
        vs = [v.co.copy() for v in fc.verts]
        ctr = sum(vs, Vector()) / 3
        inner = [ctr + (v - ctr) * 0.86 for v in vs]
        nrm = ctr.normalized()
        top = [v - Vector((0, Rs, 0)) for v in inner]
        bot = [v - nrm * 0.03 - Vector((0, Rs, 0)) for v in inner]
        allv = top + bot
        fs = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        d = (Vector(ctr - Vector((0, Rs, 0))) - imp_l).length
        band = bands[min(6, int(d / 0.22))]
        o = mesh_obj(f"{tag} cell {len(cells)}", [tuple(v) for v in allv], fs, band, sf)
        cells.append(o)
    bm.free()
    # struts along each cell's centre (a frame), plus a rim ring
    rim = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        rr = Rs * math.sin(R(42))
        rim.append((rr * math.cos(a), Rs * cap - Rs + 0.0, rr * math.sin(a)))
    rimo = sweep(f"{tag} rim", rim, 0.05, 0.03, RM, sf, side=(0, 1, 0), closed=True)
    box(f"{tag} handle", (-0.1, -0.12 - 0.3, -0.05), (0.1, -0.07 - 0.3, 0.05), GR, sf)
    rod(f"{tag} handle strut", (0, -0.37, 0), (0, -0.05, 0), 0.02, G, sf)
    form_by(cells, 2, 11, lambda p: math.atan2((p - sf.matrix_world.translation).z, (p - sf.matrix_world.translation).x) / (2 * math.pi)
            + (p - sf.matrix_world.translation).length * 1.4, None, None, tag, 0.0, 11)
    key(rimo, 1, sc=0.0001); key(rimo, 10, sc=0.0001); key(rimo, 12, sc=1.0)
    for k, m in enumerate(bands):
        anim_emit(m, [(1, 0.9), (F_HIT + k, 0.9), (F_HIT + k + 1, 4.0), (F_HIT + k + 4, 0.9)])
    imp = impact_world(sf, tuple(imp_l + Vector((0, 0.04, 0))))
    return imp, 31


def build_H3b(tag, rig, bx):
    """Planted dome wall: the ring hand pushes out and a curved wall rises from a glowing line on the ground 1.3 blocks
    ahead: ribs lean in like a dome, membrane panels of your H1 hex between them. 2.4 wide x 2.0 high. A hit dents it."""
    PUSH = dict(arm_r=(95, 0, 0), fore_r=(0, 0, 0), arm_l=(30, 0, -10), fore_l=(30, 0, 0), leg_l=(22, 0, 0), shin_l=(-18, 0, 0), leg_r=(-14, 0, 0), body=(-6, 0, 0))
    HOLD = dict(PUSH, arm_r=(88, 0, 4), fore_r=(10, 0, 0))
    pose_keys(rig, bx, [(1, {}), (4, PUSH), (12, HOLD), (30, HOLD), (33, dict(HOLD, body=(2, 0, 0))), (40, HOLD), (56, {})])
    wall = empty(f"{tag} wall", (bx, 1.6, 0))
    MM = strip("h1", f"{tag} membrane", alpha=0.8, emit=1.2)
    Rw = 1.7; arc = 1.4; Ht = 2.0; nr = 9; parts_r, parts_m = [], []
    def P_(a, h):
        lean = 0.25 * (h / Ht) ** 2                     # the top leans back toward the player like a dome
        r_ = Rw - lean
        return Vector((r_ * math.sin(a), r_ * math.cos(a) - Rw, h))
    angs = np.linspace(-arc / 2, arc / 2, nr)
    for k, a in enumerate(angs):
        pts = [P_(a, h) for h in np.linspace(0, Ht, 8)]
        parts_r.append(sweep(f"{tag} rib {k}", pts, 0.05, 0.05, RM if k in (0, nr - 1) else G, wall, side=(math.cos(a), -math.sin(a), 0)))
    for k in range(nr - 1):
        for j in range(4):
            h0, h1 = j * Ht / 4, (j + 1) * Ht / 4
            a0, a1 = angs[k], angs[k + 1]
            vs = [P_(a0, h0), P_(a1, h0), P_(a1, h1), P_(a0, h1)]
            vs2 = [v + Vector((0, -0.015, 0)) for v in vs]
            parts_m.append(mesh_obj(f"{tag} panel {k} {j}", [tuple(v) for v in vs + vs2], [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], MM, wall, uvt=0.4))
    cap = sweep(f"{tag} cap", [P_(a, Ht) for a in np.linspace(-arc / 2, arc / 2, 16)], 0.05, 0.05, RM, wall, side=(0, 0, 1))
    gl = sweep(f"{tag} ground line", [P_(a, 0.005) for a in np.linspace(-arc / 2, arc / 2, 16)], 0.12, 0.01, CM["pix"], wall, side=(0, 0, 1))
    key(gl, 1, sc=(0.0001, 1, 1)); key(gl, 5, sc=(0.0001, 1, 1)); key(gl, 7, sc=(1, 1, 1)); key(gl, 14, sc=(1, 1, 1)); key(gl, 16, sc=(1, 1, 0.0001))
    for k, r_ in enumerate(parts_r):                     # ribs rise out of the ground line, centre first
        f_ = 6 + int(abs(k - nr // 2))
        key(r_, 1, sc=(1, 1, 0.0001)); key(r_, f_, sc=(1, 1, 0.0001)); key(r_, f_ + 3, sc=(1, 1, 1.05)); key(r_, f_ + 4, sc=(1, 1, 1))
    form_by(parts_m, 9, 14, lambda p: p.z + abs(p.x - bx) * 0.3, None, None, tag)
    key(cap, 1, sc=0.0001); key(cap, 13, sc=0.0001); key(cap, 14, sc=1.0)
    scene.frame_set(4); bpy.context.view_layer.update(); rw = rig["ring_pt"].matrix_world.translation.copy()
    for k in range(10):                                  # pixels from the ring to the ground line
        px = link(bpy.data.objects.new(f"{tag} push pixel", pixel_mesh(CM["pix"])))
        tgt = Vector((bx, 1.6, 0)) + P_(angs[0] + (angs[-1] - angs[0]) * k / 9, 0.02)
        key(px, 1, loc=rw, sc=0.0001); key(px, 3, loc=rw, sc=0.0001); key(px, 4, loc=rw, sc=1.0); key(px, 7, loc=tgt, sc=0.8); key(px, 8, loc=tgt, sc=0.0001)
    # the hit: a dent dimple and the wall shudders
    imp_l = Vector((0.15, 0.06, 1.3))
    dent = ball(f"{tag} dent", 0.16, CM["glow"], tuple(imp_l), wall, 14)
    key(dent, 1, sc=0.0001); key(dent, F_HIT, sc=(0.0001, 0.0001, 0.0001)); key(dent, F_HIT + 1, sc=(1, 0.3, 1)); key(dent, F_HIT + 6, sc=(1.6, 0.15, 1.6)); key(dent, F_HIT + 10, sc=0.0001)
    key(wall, 1, loc=(bx, 1.6, 0)); key(wall, F_HIT, loc=(bx, 1.6, 0)); key(wall, F_HIT + 1, loc=(bx, 1.63, 0)); key(wall, F_HIT + 3, loc=(bx, 1.585, 0)); key(wall, F_HIT + 6, loc=(bx, 1.6, 0))
    return Vector((bx, 1.6, 0)) + imp_l, 31


def build_H3c(tag, rig, bx):
    """Twin shells: a smooth outer dome of your X3 quantum texture turning one way over an inner lattice of hex rings
    turning the other; 1.6 across. A hit flashes the outer shell and a pulse runs back down the arm to the ring."""
    pose_keys(rig, bx, [(1, {}), (6, GUARD), (28, GUARD), (31, GIVE), (40, GUARD), (56, {})])
    sf = shield_frame(tag, rig["fore_r"], (bx, 0.5, 1.15))
    XM = strip("x3d1", f"{tag} outer shell", alpha=0.6, emit=1.1, ft=5)
    Rs = 0.95; capd = 58
    outer_p = empty(f"{tag} outer spin", (0, -Rs * math.cos(R(capd)) + 0.0, 0), sf)
    inner_p = empty(f"{tag} inner spin", (0, -Rs * math.cos(R(capd)) - 0.04, 0), sf)
    vs, fs = [], []
    nr, na = 8, 32
    for i in range(nr + 1):
        th = R(capd) * i / nr
        for j in range(na):
            ph = 2 * math.pi * j / na
            vs.append((Rs * math.sin(th) * math.cos(ph), Rs * math.cos(th), Rs * math.sin(th) * math.sin(ph)))
    for i in range(nr):
        for j in range(na):
            a = i * na + j; b = i * na + (j + 1) % na
            fs.append((a, b, b + na, a + na))
    shell = mesh_obj(f"{tag} outer shell", vs, fs, XM, outer_p, smooth=True, uvt=0.35)
    shell.location = (0, -Rs, 0); shell.location = (0, -Rs + Rs * math.cos(R(capd)), 0)
    rimpts = [(Rs * math.sin(R(capd)) * math.cos(2 * math.pi * k / 40), Rs * math.cos(R(capd)), Rs * math.sin(R(capd)) * math.sin(2 * math.pi * k / 40)) for k in range(40)]
    rim = sweep(f"{tag} rim", rimpts, 0.045, 0.03, RM, shell, side=(0, 1, 0), closed=True)
    rings = []
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=Rs - 0.06)
    for v in bm.verts:
        n = v.co.normalized()
        if n.y < math.cos(R(capd - 4)):
            continue
        t = torus(f"{tag} lattice ring {len(rings)}", 0.075, 0.008, CM["glow"], loc=tuple(v.co - Vector((0, Rs - Rs * math.cos(R(capd)), 0))), parent=inner_p, n=6, k=4, axis="Y")
        t.rotation_mode = "QUATERNION"; t.rotation_quaternion = n.to_track_quat("Z", "Y") @ Quaternion((1, 0, 0), R(90))
        rings.append(t)
    bm.free()
    box(f"{tag} handle", (-0.08, -0.12 - 0.35, -0.05), (0.08, -0.07 - 0.35, 0.05), GR, sf)
    rod(f"{tag} handle strut", (0, -0.42, 0), (0, -0.1, 0), 0.02, G, sf)
    _prefs.keyframe_new_interpolation_type = "LINEAR"
    for f_, a in ((1, 0.0), (66, 1.0)):                    # slow counter-rotation about the forward axis
        key(outer_p, f_, rot=(0, R(70) * a, 0)); key(inner_p, f_, rot=(0, -R(110) * a, 0))
    _prefs.keyframe_new_interpolation_type = "BEZIER"
    form_by(rings, 2, 8, lambda p: (p - sf.matrix_world.translation).length, None, None, tag, 0.0, 8)
    al = strip_alpha_socket(XM)
    for f_, v in ((1, 0.0), (7, 0.0), (11, 0.6)):
        al.default_value = v; al.keyframe_insert("default_value", frame=f_)
    key(rim, 1, sc=0.0001); key(rim, 7, sc=0.0001); key(rim, 9, sc=1.0)
    anim_emit(XM, [(1, 1.1), (F_HIT, 1.1), (F_HIT + 1, 4.0), (F_HIT + 6, 1.1)])
    imp = impact_world(sf, (0.12, 0.04, 0.18))
    pulse = ball(f"{tag} pulse", 0.035, CM["pix"], (0, 0, 0), None, 10)
    for f_ in range(F_HIT, F_HIT + 7):
        scene.frame_set(f_); bpy.context.view_layer.update()
        t = (f_ - F_HIT) / 6
        rp = rig["ring_pt"].matrix_world.translation.copy()
        key(pulse, f_, loc=tuple(imp.lerp(rp, smooth(t))))
    key(pulse, 1, sc=0.0001); key(pulse, F_HIT - 1, sc=0.0001); key(pulse, F_HIT, sc=1.0); key(pulse, F_HIT + 6, sc=1.0); key(pulse, F_HIT + 7, sc=0.0001)
    return imp, 31


SHIELDS = {
 "H2a": dict(name="tower: curved brick", src="H2", build=build_H2a, end=60,
             facts="curved tower 1.0 x 1.8 of offset BR1 brick courses built from the forearm out; hit ripple across the face",
             lines=["Curved tower, 1.0 x 1.8 blocks: 9 courses of offset bricks", "(your BR1) on a curve, rim posts and lips; forms course by",
                    "course out from the forearm 2-11; the hit at 30 sends a", "ripple ring across the face."]),
 "H2b": dict(name="tower: riot wall, kneel", src="H2", build=build_H2b, end=62,
             facts="rev 2: flat W1 panel 1.0 x 1.9 with viewport held from behind by two grip bars (no arm contact); kneel, rim traces 5-10, panel fades in 9-14, foot spike plants at 11; cracks spread and heal",
             lines=["Riot wall, 1.0 x 1.9 (rev 2): W1 weave panel, viewport slot,", "held from behind by two grip bars, arms clear of it; kneel,",
                    "rim traces 5-10, panel fades in 9-14, spike plants at 11;", "the hit spreads glowing cracks that heal by 48."]),
 "H2c": dict(name="tower: telescoping heater", src="H2", build=build_H2c, end=60,
             facts="7 curved H1 slats slide out of the forearm into a 1.0 x 1.7 heater outline (3-11); hit rocks the slats back in a wave",
             lines=["Telescoping heater, 1.0 x 1.7: seven curved slats (your H1)", "slide out of the forearm up and down 3-11 with an overshoot;",
                    "heater outline (square top, pointed foot); on the hit the", "slats rock back one after another, a wave from the impact."]),
 "H3a": dict(name="dome: geodesic cap", src="H3", build=build_H3a, end=60,
             facts="geodesic cap of ~100 triangle cells, 1.7 across, both hands bracing; forms in a spiral 2-11; rings of cells light out from the hit",
             lines=["Geodesic cap, 1.7 across: triangle cells cut from a sphere,", "rim ring, both hands bracing; forms in a spiral from the",
                    "centre 2-11; the hit lights rings of cells outward,", "one ring a tick."]),
 "H3b": dict(name="dome: planted wall", src="H3", build=build_H3b, end=60,
             facts="push from the ring hand; a curved wall 2.4 x 2.0 rises 1.6 blocks ahead from a ground line (6-14), leaning in like a dome; hit dents it",
             lines=["Planted dome wall, 2.4 wide x 2.0 high, 1.6 blocks ahead:", "the ring hand pushes, a line glows on the ground, ribs rise",
                    "6-12 leaning in like a dome, H1 hex panels fill 9-14.", "The hit dents it and the wall shudders."]),
 "H3c": dict(name="dome: twin shells", src="H3", build=build_H3c, end=60,
             facts="outer X3 shell 1.6 across turning one way over an inner lattice of hex rings turning the other; hit flashes, pulse runs to the ring",
             lines=["Twin shells, 1.6 across: a smooth outer dome (your X3", "quantum) slowly turning over an inner lattice of hex rings",
                    "turning the other way; the hit flashes the shell and a", "pulse runs back down the arm into the ring."]),
}


def build_shield_take(code, bi):
    T = SHIELDS[code]; bx = bi * BAY; tag = f"BS2 {code}"
    box(f"{tag} floor", (bx - 2.6, -3, -0.02), (bx + 2.6, 9, 0), FLOOR)
    M = player_mats(tag); M["ring"] = mat(f"{tag} ring face", (0.02, 0.85, 0.15), emit=1.6)
    rig = make_player(tag, (bx, 0, 0), M)
    imp, mf = T["build"](tag, rig, bx)
    incoming(tag, bx, imp)
    far = code == "H3b"
    cam(f"Cam {code}", (bx + 3.4, 5.6 if far else 4.6, 2.1), (bx, 0.6 if far else 0.3, 1.1), 32)
    cam(f"Cam {code} back", (bx + 2.6, -3.6, 2.0), (bx, 0.6 if far else 0.3, 1.1), 32)
    board(tag, (bx, 3.0, 3.0), f"{code}  {T['name'].upper()}", T["lines"])
    return mf


ORDER = ["B1a", "B1b", "B1c", "B2a", "B2b", "B2c", "B3a", "B3b", "B3c", "H2a", "H2b", "H2c", "H3a", "H3b", "H3c"]
dump = {"takes": {}}
for bi, code in enumerate(ORDER):
    if code in BOWS:
        dump["takes"][code] = {"solver_error_m": build_bow_take(code, bi)}
    else:
        build_shield_take(code, bi)
    print(code, "built", flush=True)
FRAME_END = max([BOWS[c]["end"] for c in BOWS] + [SHIELDS[c]["end"] for c in SHIELDS])


with open(os.path.join(FOLDER, "combat", "bows_shields2_poses.json"), "w") as fh:
    json.dump(dump, fh, indent=1)
cam("Cam all", (7 * BAY, -30.0, 9.0), (7 * BAY, 2.0, 1.2), 20)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam B1a close", 1, (0.3, 0.38, 0.5), 3.0


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
