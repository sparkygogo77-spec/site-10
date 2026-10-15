# Pass 850: bows and shields round 3, 3 variations each of 842 B1a, B3a, B3b, B3c, H2a, H2c, H3b (Chat C, 2026-10-15).
# J rated these 842 takes IMPROVE with no note: "3 new variations each", labelled, he picks. Each new take keeps what
# made its parent itself (B1a the swept riser, B3a the W1 plate + mechanical heads, B3b the truss + rangefinder, B3c the
# cube riser + follow-up shots, H2a curved BR1 brick, H2c telescoping H1 heater, H3b the planted dome wall) and is built
# a different way. Dropped (not rebuilt): B1b, B1c, B2a, B2b, B2c, H3a, H3c. H2b was fixed in place in 842 (rev 2).
# Earlier (808): "VERY in depth bow and arrow models, think modern day bow and arrows", "the shield is too small".
# 842 H2b note: "shield in third person collides with arms": every hand-held shield here is held from behind on grip
# bars just past the hands (arms solved onto the bars), and is checked to never intersect the arms at any frame.
# Same bow shot as 842 (right-handed archer, ring on the draw hand, 20 ticks a second, target 18 blocks out).
#   B1a1 swept riser bent reflex over a zigzag Warren-truss spine; oval ports light at full draw; solid limbs, hybrid
#        cams, single-pin scope; forms as a pixel trace from the top cam down
#   B1a2 swept riser as a round tube with glowing collar ports, twin side spines; binary cams roll 220; 5-pin; long rod
#        + two back bars; spines trace first, ring pixels fill
#   B1a3 swept riser as a deep thin blade laddered to an arc spine; 8 ports light one by one on the draw; single cam
#   B3a1 W1 plate with long rimmed slots; single cam; 3-pin; hip quiver; 3-blade rear-deploying heads; plate thickens in
#   B3a2 two thin W1 plates held apart by glowing spacer bolts, slide together as it forms; long 2-blade claw heads
#   B3a3 W1 plate with two big rimmed windows; 7 pins in one column; 4-blade heads spin as they open; plate stamps in
#   B3b1 3D space-frame carbon riser; the rangefinder laser scans the target and counts 6, 12, 18; 3-blade heads
#   B3b2 bowstring-truss riser; rangefinder on the end of the front rod fires 3 pulses, reads 18; solid limbs
#   B3b3 K-truss riser with hex-nut nodes; the ring arm leads and points, a laser from the ring ranges the target
#   B3c1 cubes in a twisted double helix; a twist wave rolls through between shots; release 25 and 43
#   B3c2 cubes trace the riser outline only; no quiver: the second arrow is built at the hand from ring cubes
#   B3c3 dense 2x3 checker of small cubes; three fast shots (23, 38, 53)
#   H2a1 curved brick tower with a round arch top and keystone, bricks fly in from the ring; hit knocks bricks back
#   H2a2 stack-bond BR1 on a barrel surface (curved both ways), columns rise from the ground; hit flashes outward
#   H2a3 five flat facets in BR1 herringbone unfold like a folding screen; hit punches one brick out, it re-seats
#   H2c1 upright H1 columns telescope out sideways from the centre; hit shivers them sideways in a wave
#   H2c2 five nested heater-outline frames telescope out like a collapsible cup; hit pushes them back in turn
#   H2c3 roller shutter: nine hinged H1 slats unroll down from a header bar; hit ripples down the chain
#   H3b1 drawbridge: curved ribs lying flat swing up on hinges at the ground line into a quarter dome, H1 panels fill
#   H3b2 a curved band of H1 hex columns extrudes up from the ground line, leaning in like a dome
#   H3b3 a post spikes into the ground and three curved H1 screens slide out of it sideways
# Cameras: bows "Cam <take>", "Cam <take> close", "Cam <take> target"; shields "Cam <take>", "Cam <take> back";
# "Cam all". Builds LanternLive\combat\bows_shields3.blend.
SCENE_NAME = "Bows and Shields 3"
OUT_REL = "combat/bows_shields3.blend"
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
FLOOR = mat("BS3 floor", (0.2, 0.22, 0.24), rough=0.9)
STRAW = mat("BS3 target straw", (0.75, 0.62, 0.35), rough=0.9)
RINGS = [mat(f"BW target ring {i}", c, rough=0.7) for i, c in enumerate(((0.9, 0.9, 0.85), (0.08, 0.08, 0.1), (0.1, 0.3, 0.9), (0.9, 0.1, 0.1), (1.0, 0.85, 0.1)))]
SHOT = mat("BS3 shot", (0.6, 0.15, 0.1), emit=1.0)
BOARD = mat("BS3 board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("BS3 text", (0.75, 1.0, 0.8), emit=1.2)
TXTH = mat("BS3 heading", (0.2, 1.0, 0.4), emit=2.2)
rng = np.random.default_rng(850)
CM = cmats("BS3", "green")
G, W, RM, GR = CM["glass"], CM["glow"], CM["rim"], CM["grip"]
STR = mat("BS3 string", (0.1, 1.0, 0.3), emit=2.0)
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


# ================================================================== shared builders (from pass 842)
import bmesh
from mathutils import Quaternion
from mathutils.geometry import tessellate_polygon

LNOCK = mat("BS3 lighted nock", (0.12, 1.0, 0.3), emit=0.3)
anim_emit(LNOCK, [(1, 0.3), (41, 0.3), (42, 7.0), (46, 5.0)])
DARK = mat("BS3 carbon", (0.02, 0.12, 0.05), emit=0.35, alpha=0.9, rough=0.25)
LENS = mat("BS3 lens", (0.05, 0.6, 0.2), emit=0.6, alpha=0.35, rough=0.05)
LASER = mat("BS3 laser", (0.12, 1.0, 0.3), emit=6.0)
FOAM = [mat(f"BS3 foam {i}", c, rough=0.9) for i, c in enumerate(((0.85, 0.85, 0.8), (0.12, 0.13, 0.14), (0.85, 0.2, 0.1)))]


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
           barrel=False, wrap=True, mech_n=2, mech_len=0.045):
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
        for k in range(mech_n):
            pv = empty(f"{tag} mech pivot {k}", (0, 0, tip - 0.05), root); pv.rotation_euler = (0, 0, k * 2 * math.pi / mech_n)
            hinge = empty(f"{tag} mech hinge {k}", (0.008, 0, 0), pv)
            box(f"{tag} mech blade {k}", (-0.001, -0.0007, 0.0), (0.002, 0.0007, mech_len), RM, hinge)
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
def cam_pair(tag, root, H, L, a0, kind="binary", idler=False, split=True):
    """Compound limbs + cams. kind: binary (two equal cams), hybrid (big top, smaller bottom), single (cam + idler).
    Returns tips (empties at the cam axles, bottom then top), limb pivots [(pivot, sy, rest angle)], cam pivots."""
    tips, flex, cams = [], [], []
    for sy in (-1, 1):
        lp = empty(f"{tag} limb {sy}", (0, sy * H, -0.03), root); lp.rotation_euler = (R(sy * a0), 0, 0)
        flex.append((lp, sy, a0))
        if not split:                                    # one solid limb with a pocket block at the riser
            y1 = sy * L
            sweep(f"{tag} limb {sy} solid", [(0, 0, 0), (0, y1 * 0.5, 0.0), (0, y1, 0)], [0.036, 0.03, 0.024], [0.02, 0.015, 0.011], G, lp)
            bx_(tag, f"limb pocket {sy}", (-0.024, min(0, sy * 0.05), -0.016), (0.024, max(0, sy * 0.05), 0.016), RM, lp)
        for sx in ((-1, 1) if split else ()):            # split limbs, tapering, with a damper puck
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


# ================================================================== pass 850: the twelve bows (siblings of 842 B1a, B3a, B3b, B3c)
def port_mat(tag, k=0, e=1.0):
    return mat(f"{tag} port glow {k}", CM["c"], emit=e)


def swept_path(H, zmid, ztip, n=13):
    """A smooth riser centre line from tip to tip in the bow's YZ plane (z of the middle and of the tips)."""
    return [(0, y, ztip + (zmid - ztip) * max(0.0, math.cos(math.pi * y / (2 * H))) ** 1.5) for y in np.linspace(-H, H, n)]


def bow_B1a1(tag, par):
    """B1a sibling: the swept bar bends the other way (reflex: the middle forward) over a zigzag Warren-truss spine on
    the target side; oval ports that light at full draw; solid limbs; hybrid cams; single-pin scope."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.33
    pts = swept_path(H, -0.055, 0.0)
    sweep(f"{tag} riser", pts, 0.026, 0.05, G, root)
    sp = [(0, y, -0.04 - 0.075 * math.cos(math.pi * y / (2 * H))) for y in np.linspace(-H + 0.03, H - 0.03, 9)]
    sweep(f"{tag} riser spine", sp, 0.018, 0.016, G, root)
    first = []
    for k in range(8):                                   # Warren truss: ties zigzag between bar and spine
        y0 = -H + 0.05 + k * (2 * H - 0.1) / 8; y1 = y0 + (2 * H - 0.1) / 8
        a = (0, y0, -0.055 * max(0.0, math.cos(math.pi * y0 / (2 * H))) ** 1.5 - 0.02) if k % 2 == 0 else (0, y0, -0.04 - 0.075 * math.cos(math.pi * y0 / (2 * H)))
        b = (0, y1, -0.04 - 0.075 * math.cos(math.pi * y1 / (2 * H))) if k % 2 == 0 else (0, y1, -0.055 * max(0.0, math.cos(math.pi * y1 / (2 * H))) ** 1.5 - 0.02)
        first.append(rod(f"{tag} warren tie {k}", a, b, 0.005, RM, root))
    PM = port_mat(tag, 0, 0.8)
    for k, y in enumerate((-0.25, -0.15, 0.15, 0.25)):
        z = -0.055 * max(0.0, math.cos(math.pi * y / (2 * H))) ** 1.5
        t = torus(f"{tag} oval port {k}", 0.016, 0.0035, PM, (0.014, y, z), root, 16, 6, axis="X"); t.scale = (1, 1.6, 0.7)
    bx_(tag, "grip", (-0.018, -0.055, -0.015), (0.018, 0.055, 0.035), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.24, 52, "hybrid", split=False)
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 1, (0.045, 0.13, -0.07), housing=0.034, scope=True)
    stab(tag, root, 0.45, (0, -0.08, -0.07), w=3)
    stab(tag, root, 0.24, (0, -0.1, -0.03), ang=(-5, 115, 0), w=3)      # side bar
    rod(f"{tag} cable guard", (0.0, -0.07, 0.0), (0.03, -0.07, 0.14), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=170, nock_y=0.075, compound=True, full_glow=PM, first=first)


def bow_B1a2(tag, par):
    """B1a sibling: the swept bar is a round tube with glowing collar ports, braced by twin spines (one each side);
    split limbs; binary cams roll 220; 5-pin; long rod + two back bars."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.33
    pts = swept_path(H, 0.01, -0.06, 15)
    for k in range(len(pts) - 1):
        rod(f"{tag} tube {k}", pts[k], pts[k + 1], 0.017, G, root, 12)
    for k, i in enumerate((2, 4, 10, 12)):
        torus(f"{tag} collar port {k}", 0.021, 0.0045, W, pts[i], root, 20, 6, axis="Y")
    first = []
    for sx in (-1, 1):
        sp = [(sx * 0.024, y, -0.065 - 0.025 * math.cos(math.pi * y / (2 * H))) for y in np.linspace(-H + 0.03, H - 0.03, 9)]
        first.append(sweep(f"{tag} spine {sx}", sp, 0.008, 0.012, RM, root))
        for k, i in enumerate((1, 3, 5, 7)):
            p_ = sp[i]; q_ = pts[min(14, max(0, int(round((p_[1] + H) / (2 * H) * 14))))]
            first.append(rod(f"{tag} brace {sx} {k}", p_, (q_[0], q_[1], q_[2] - 0.012), 0.004, G, root))
    bx_(tag, "grip", (-0.018, -0.055, -0.015), (0.018, 0.055, 0.035), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.24, 64, "binary")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 5, (0.045, 0.13, -0.065), housing=0.034)
    stab(tag, root, 0.7, (0, -0.08, -0.08), w=3)
    v = empty(f"{tag} back bars", (0, -0.1, -0.03), root)
    for sx in (-1, 1):
        stab(tag, v, 0.3, (sx * 0.01, 0, 0), ang=(-22, sx * 32 + 180, 0), w=3)
    rod(f"{tag} cable guard", (0.0, -0.07, 0.0), (0.03, -0.07, 0.14), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=220, nock_y=0.075, compound=True, first=first)


def bow_B1a3(tag, par):
    """B1a sibling: the swept bar is a deep thin blade with a ladder truss to a full-length arc spine; eight ports
    light one by one as the string comes back; single cam + idler; 3-pin."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.34
    pts = swept_path(H, 0.0, -0.05)
    sweep(f"{tag} blade riser", pts, 0.012, 0.07, G, root)
    sp = [(0, y, -0.07 - 0.07 * math.cos(math.pi * y / (2 * H))) for y in np.linspace(-H + 0.02, H - 0.02, 11)]
    first = [sweep(f"{tag} arc spine", sp, 0.016, 0.014, RM, root)]
    for k, y in enumerate(np.linspace(-H + 0.07, H - 0.07, 10)):
        if abs(y) < 0.06:
            continue
        zb = -0.05 + 0.05 * max(0.0, math.cos(math.pi * y / (2 * H))) ** 1.5 - 0.035
        first.append(rod(f"{tag} rung {k}", (0, y, zb), (0, y, -0.07 - 0.07 * math.cos(math.pi * y / (2 * H)) + 0.007), 0.004, G, root))
    pms = []
    for k, y in enumerate([-0.29, -0.22, -0.15, -0.08, 0.08, 0.15, 0.22, 0.29]):
        m_ = port_mat(tag, k, 0.3); pms.append((abs(y), m_))
        z = -0.05 + 0.05 * max(0.0, math.cos(math.pi * y / (2 * H))) ** 1.5
        cyl(f"{tag} port {k}", 0.009, 0.016, m_, 12, root, loc=(-0.008, y, z), axis="X")
    pms = [m_ for _, m_ in sorted(pms, key=lambda t: t[0])]          # light from the grip out to the tips
    bx_(tag, "grip", (-0.018, -0.055, -0.015), (0.018, 0.055, 0.035), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.25, 42, "single")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 3, (0.045, 0.13, -0.07), housing=0.03)
    stab(tag, root, 0.52, (0, -0.08, -0.09), w=4)
    rod(f"{tag} cable guard", (0.0, -0.07, 0.0), (0.03, -0.07, 0.14), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=260, nock_y=0.075, compound=True, port_mats=pms, first=first)


def w1_plate_outline(H):
    return [(-H, -0.07), (-0.08, -0.055), (-0.055, 0.035), (0.055, 0.035), (0.08, -0.055), (H, -0.07), (H, -0.02), (0.1, -0.005), (-0.1, -0.005), (-H, -0.02)]


def bow_B3a1(tag, par):
    """B3a sibling: W1 plate riser with long slotted ports; single cam; 3-pin; no quiver on the bow (hip quiver);
    3-blade rear-deploying mechanical heads. The plate grows in thickness, then the rest."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.3
    holes = [loop2d(sy * y, -0.045, rx, 0.009, 12) for sy in (-1, 1) for y, rx in ((0.13, 0.03), (0.21, 0.035))]
    pl = plate(f"{tag} riser", w1_plate_outline(H), holes, -0.014, 0.014, strip("w1", f"{tag} riser w1", alpha=0.92, emit=1.2), root, uvt=0.1)
    for k, (sy, y) in enumerate([(sy, y) for sy in (-1, 1) for y in (0.13, 0.21)]):
        sweep(f"{tag} slot rim {k}", [(0.0145, p[0], p[1]) for p in loop2d(sy * y, -0.045, 0.03 if y < 0.2 else 0.035, 0.009, 12)], 0.002, 0.003, W, root, closed=True)
    bx_(tag, "grip", (-0.018, -0.05, 0.0), (0.018, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 46, "single")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 3, (0.045, 0.13, -0.06), housing=0.03)
    stab(tag, root, 0.15, (0, -0.07, -0.07), w=3)
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=250, nock_y=0.075, compound=True, thick=pl)


def bow_B3a2(tag, par):
    """B3a sibling: two thin W1 plates with a gap, held by glowing spacer bolts; the plates slide together as it forms;
    binary cams; 5-pin; 3-arrow quiver; long 2-blade claw heads that open forward."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.28
    holes = [loop2d(sy * y, -0.045, 0.02, 0.013, 10) for sy in (-1, 1) for y in (0.13, 0.2)]
    WM = strip("w1", f"{tag} riser w1", alpha=0.92, emit=1.2)
    plates = []
    for sx in (-1, 1):
        hp = empty(f"{tag} half {sx}", (0, 0, 0), root)
        plate(f"{tag} riser half {sx}", w1_plate_outline(H), holes, sx * 0.006, sx * 0.018, WM, hp, uvt=0.1)
        plates.append((hp, sx))
    bolts = []
    for k, (y, z) in enumerate(((-0.24, -0.045), (-0.165, -0.045), (0.165, -0.045), (0.24, -0.045), (0.0, 0.02))):
        bolts.append(cyl(f"{tag} spacer bolt {k}", 0.006, 0.044, W, 10, root, loc=(-0.022, y, z), axis="X"))
    bx_(tag, "grip", (-0.02, -0.05, 0.0), (0.02, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 50, "binary")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 5, (0.045, 0.13, -0.06), housing=0.034)
    stab(tag, root, 0.22, (0, -0.07, -0.07), w=2)
    q, qa = quiver(tag, root, 3, (0.05, 0.0, 0.0), "mech")
    torus(f"{tag} wrist sling", 0.04, 0.005, RM, parent=root, loc=(0, 0, 0.0), axis="Y")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=190, nock_y=0.075, compound=True, quiver=qa, plates=plates, first=bolts)


def bow_B3a3(tag, par):
    """B3a sibling: W1 plate with two big rimmed windows; 7 pins in one column; 5-arrow quiver; 4-blade heads that
    spin as they open. The plate stamps in whole, then the window rims punch through."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    wins = [loop2d(sy * 0.17, -0.045, 0.07, 0.015, 16) for sy in (-1, 1)]
    pl = plate(f"{tag} riser", w1_plate_outline(H), wins, -0.014, 0.014, strip("w1", f"{tag} riser w1", alpha=0.92, emit=1.2), root, uvt=0.1)
    rims = []
    for k, w_ in enumerate(wins):
        for sx in (-1, 1):
            rims.append(sweep(f"{tag} window rim {k} {sx}", [(sx * 0.0155, p[0], p[1]) for p in w_], 0.003, 0.004, W, root, closed=True))
    bx_(tag, "grip", (-0.018, -0.05, 0.0), (0.018, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 48, "hybrid")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sb = empty(f"{tag} sight", (0.045, 0.13, -0.06), root)                # 7 pins stacked in one vertical column
    bx_(tag, "sight bar", (-0.004, -0.006, 0.0), (0.004, 0.006, 0.09), G, sb)
    bx_(tag, "sight guard", (-0.004, -0.03, -0.05), (0.004, 0.03, -0.044), RM, sb)
    bx_(tag, "sight guard b", (-0.004, -0.03, -0.016), (0.004, 0.03, -0.01), RM, sb)
    for k in range(7):
        ball(f"{tag} pin dot {k}", 0.0026, W, (0.0, 0.024 - k * 0.008, -0.03), sb, 8)
        bx_(tag, f"pin stalk {k}", (0.0, 0.0235 - k * 0.008, -0.031), (0.03, 0.0245 - k * 0.008, -0.029), DARK, sb)
    stab(tag, root, 0.2, (0, -0.07, -0.07), w=2)
    q, qa = quiver(tag, root, 5, (0.05, 0.0, 0.0), "mech")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=180, nock_y=0.075, compound=True, quiver=qa, stamp=pl, last=rims)


def truss(tag, root, pairs, nodes, rt=0.008, node_r=0.013, hexnode=False, tube_m=None):
    parts = []
    for k, (a, b, r_, m_) in enumerate(pairs):
        parts.append(rod(f"{tag} tube {k}", a, b, r_, m_, root))
    for k, nd in enumerate(nodes):
        if hexnode:
            parts.append(cyl(f"{tag} hex node {k}", node_r, 0.03, RM, 6, root, loc=(nd[0] - 0.015, nd[1], nd[2]), axis="X"))
        else:
            parts.append(ball(f"{tag} node {k}", node_r, RM, nd, root, 10))
    return parts


def bow_B3b1(tag, par):
    """B3b sibling: a 3D space-frame riser (two carbon chords either side joined by cross tubes and diagonals);
    the rangefinder laser scans across the target and counts up to 18; slider pin drops; 3-blade heads."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    ys = [-H, -0.16, -0.05, 0.05, 0.16, H]; zf = [-0.06, -0.08, -0.025, -0.025, -0.08, -0.06]
    pairs, nodes = [], []
    for sx in (-1, 1):
        f_ = [(sx * 0.02, y, z) for y, z in zip(ys, zf)]; nodes += f_
        pairs += [(f_[k], f_[k + 1], 0.009, DARK) for k in range(5)]
    back = [(0, -H + 0.02, -0.005), (0, -0.15, 0.005), (0, 0.15, 0.005), (0, H - 0.02, -0.005)]; nodes += back
    pairs += [(back[k], back[k + 1], 0.007, G) for k in range(3)]
    for sx in (-1, 1):
        for i, j in ((0, 0), (1, 1), (1, 0), (4, 2), (4, 3), (5, 3)):
            pairs.append(((sx * 0.02, ys[i], zf[i]), back[j], 0.005, G))
    for i in (0, 1, 4, 5):
        pairs.append(((-0.02, ys[i], zf[i]), (0.02, ys[i], zf[i]), 0.005, RM))
    truss(tag, root, pairs, nodes)
    bx_(tag, "grip", (-0.018, -0.05, -0.025), (0.018, 0.05, 0.035), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.21, 46, "hybrid")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sb, pins = sight_pins(tag, root, 1, (0.05, 0.13, -0.07), housing=0.03, scope=True)
    rf = empty(f"{tag} rangefinder", (0.0, 0.04, 0.02), sb)
    bx_(tag, "rangefinder body", (-0.012, -0.012, -0.04), (0.012, 0.012, 0.0), DARK, rf)
    cyl(f"{tag} rangefinder lens", 0.008, 0.004, LENS, 12, rf, loc=(0, 0, -0.044), axis="Z")
    stab(tag, root, 0.28, (0, -0.07, -0.07), w=2)
    q, qa = quiver(tag, root, 4, (0.05, 0.0, 0.0), "broad3")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=170, nock_y=0.075, compound=True, slide=pins[0], rf=rf, quiver=qa)


def bow_B3b2(tag, par):
    """B3b sibling: a bowstring-truss riser (curved top chord, straight back chord, posts and diagonals); the
    rangefinder rides on the end of the front rod and fires three pulses; solid limbs, binary cams; 2-blade heads."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    ys = np.linspace(-H, H, 7)
    top = [(0, y, -0.02 - 0.075 * math.cos(math.pi * y / (2 * H))) for y in ys]
    bot = [(0, y * 0.93, 0.0) for y in ys]
    pairs = [(top[k], top[k + 1], 0.01, DARK) for k in range(6)] + [(bot[k], bot[k + 1], 0.007, G) for k in range(6)]
    for k in range(1, 6):
        if abs(ys[k]) > 0.06:
            pairs.append((top[k], bot[k], 0.005, G))
    for k in (0, 1, 4, 5):
        pairs.append((top[k], bot[k + 1], 0.004, RM) if k < 3 else (top[k + 1], bot[k], 0.004, RM))
    truss(tag, root, pairs, top, node_r=0.012)
    bx_(tag, "grip", (-0.018, -0.05, -0.02), (0.018, 0.05, 0.035), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.21, 48, "binary", split=False)
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sb, pins = sight_pins(tag, root, 1, (0.05, 0.13, -0.07), housing=0.03)
    sp_ = stab(tag, root, 0.36, (0, -0.07, -0.09), w=1)
    rf = empty(f"{tag} rangefinder", (0, 0, -0.42), sp_)
    bx_(tag, "rangefinder body", (-0.016, -0.016, -0.05), (0.016, 0.016, 0.0), DARK, rf)
    cyl(f"{tag} rangefinder lens", 0.011, 0.004, LENS, 12, rf, loc=(0, 0, -0.054), axis="Z")
    q, qa = quiver(tag, root, 4, (0.05, 0.0, 0.0), "broad2")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=180, nock_y=0.075, compound=True, slide=pins[0], rf=rf, quiver=qa)


def bow_B3b3(tag, par):
    """B3b sibling: a K-truss riser (posts with K braces, hex-nut nodes); no rangefinder on the bow: the ring arm leads,
    points at the target and ranges it with a laser from the ring; the reading shows over the hand; slider pin drops."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    zf = lambda y: -0.085 + 0.02 * (abs(y) / H)
    posts = [-0.26, -0.15, 0.15, 0.26]
    front = [(0, y, zf(y)) for y in (-H, -0.26, -0.15, -0.06, 0.06, 0.15, 0.26, H)]
    back = [(0, y, 0.0) for y in (-H + 0.02, -0.26, -0.15, -0.06, 0.06, 0.15, 0.26, H - 0.02)]
    pairs = [(front[k], front[k + 1], 0.009, DARK) for k in range(7)] + [(back[k], back[k + 1], 0.007, G) for k in range(7) if k != 3]
    mids = []
    for y in posts:
        m_ = (0, y, zf(y) / 2); mids.append(m_)
        pairs += [((0, y, zf(y)), (0, y, 0.0), 0.006, G)]
        d = 0.09 if y < 0 else -0.09
        pairs += [(m_, (0, y + d, zf(y + d)), 0.004, RM), (m_, (0, y + d, 0.0), 0.004, RM)]
    truss(tag, root, pairs, front[1:-1] + mids, node_r=0.016, hexnode=True)
    bx_(tag, "grip", (-0.018, -0.05, -0.02), (0.018, 0.05, 0.035), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.21, 42, "single")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sb, pins = sight_pins(tag, root, 1, (0.05, 0.13, -0.07), housing=0.03)
    stab(tag, root, 0.3, (0, -0.07, -0.07), w=2)
    q, qa = quiver(tag, root, 4, (0.05, 0.0, 0.0), "broad2")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=200, nock_y=0.075, compound=True, slide=pins[0], quiver=qa)


def cube_z(y, H):
    return -0.035 + 0.035 * math.cos(math.pi * y / (2 * H))


def bow_B3c1(tag, par):
    """B3c sibling: the half-pixel cubes run in a twisted double helix along the riser; between the shots a twist
    wave rolls through the cubes; 4-arrow quiver; 3-blade heads."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    cubes = []
    for k in range(32):
        y = -H + 2 * H * k / 31; a = R(k * 17)
        for layer in (0, 1):
            ang = a + layer * math.pi
            c = bx_(tag, f"cube {k} {layer}", (-0.0095, -0.0095, -0.0095), (0.0095, 0.0095, 0.0095), G if (k + layer) % 2 else DARK, root)
            c.location = (0.012 * math.cos(ang), y, cube_z(y, H) + 0.016 * math.sin(ang)); c.rotation_euler = (0, ang, 0); cubes.append(c)
    bx_(tag, "grip", (-0.018, -0.05, -0.0), (0.018, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 52, "binary")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 4, (0.045, 0.13, -0.06), housing=0.032)
    stab(tag, root, 0.18, (0, -0.07, -0.06), w=3)
    q, qa = quiver(tag, root, 4, (0.05, 0.0, 0.0), "broad3")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=190, nock_y=0.075, compound=True, quiver=qa, twist=cubes)


def bow_B3c2(tag, par):
    """B3c sibling: the cubes trace only the riser's outline (hollow, like pixel art), filled solid at the grip; no
    quiver: the second arrow is built at the hand from cubes thrown off the ring; 4-blade heads."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    cubes = []
    for k in range(30):
        y = -H + 2 * H * k / 29; zc = cube_z(y, H); dep = 0.035 + 0.035 * math.cos(math.pi * y / (2 * H)) ** 2
        zs = list(np.arange(zc - dep / 2, zc + dep / 2 + 1e-6, 0.019)) if (abs(y) < 0.08 or k in (0, 29)) else [zc - dep / 2, zc + dep / 2]
        for j, z in enumerate(zs):
            c = bx_(tag, f"cube {k} {j}", (-0.013, -0.0095, -0.0095), (0.013, 0.0095, 0.0095), G if (k + j) % 2 else DARK, root)
            c.location = (0, y, z); cubes.append(c)
    bx_(tag, "grip", (-0.018, -0.05, -0.0), (0.018, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 54, "binary")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 3, (0.045, 0.13, -0.06), housing=0.03)
    stab(tag, root, 0.16, (0, -0.07, -0.06), w=4)
    torus(f"{tag} wrist sling", 0.04, 0.005, RM, parent=root, loc=(0, 0, 0.0), axis="Y")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=200, nock_y=0.075, compound=True, cubes=cubes)


def bow_B3c3(tag, par):
    """B3c sibling: a dense riser of small cubes, 2 wide and 3 deep in a checker; three fast shots (release 23, 38, 53)
    from a 6-arrow quiver; 2-blade heads."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par); H = 0.29
    cubes = []
    for k in range(30):
        y = -H + 2 * H * k / 29; zc = cube_z(y, H)
        for i, x in enumerate((-0.0075, 0.0075)):
            for j, dz in enumerate((-0.016, 0.0, 0.016)):
                c = bx_(tag, f"cube {k} {i} {j}", (-0.007, -0.0092, -0.007), (0.007, 0.0092, 0.007), G if (k + i + j) % 2 else DARK, root)
                c.location = (x, y, zc + dz); cubes.append(c)
    bx_(tag, "grip", (-0.018, -0.05, -0.0), (0.018, 0.05, 0.045), GR, root)
    tips, flex, cams = cam_pair(tag, root, H, 0.2, 50, "hybrid")
    torus(f"{tag} rest", 0.02, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
    sight_pins(tag, root, 2, (0.045, 0.13, -0.06), housing=0.03)
    stab(tag, root, 0.2, (0, -0.07, -0.06), w=3)
    q, qa = quiver(tag, root, 6, (0.05, 0.0, 0.0), "broad2")
    rod(f"{tag} cable guard", (0.0, -0.06, 0.0), (0.03, -0.06, 0.12), 0.004, G, root)
    return dict(root=root, tips=tips, flex=flex, cams=cams, roll=180, nock_y=0.075, compound=True, quiver=qa, cubes=cubes)


BOWS = {
 "B1a1": dict(name="swept riser: reflex + Warren truss", src="B1a", build=bow_B1a1, up=12, shots=[(14, 25, 32)], end=58,
              arrow=dict(vanes=3, vlen=0.085, vh=0.014, lit=True), form="trace",
              facts="swept bar bent reflex over a zigzag Warren-truss spine; oval ports light at full draw; solid limbs, hybrid cams; single-pin scope; 3-vane lighted nock",
              lines=["B1a sibling: the swept bar bends the other way (reflex)", "over a zigzag Warren-truss spine; oval ports light at full",
                     "draw; solid limbs, hybrid cams; single-pin scope; side bar.", "Forms as a pixel trace from the top cam down to the bottom."]),
 "B1a2": dict(name="swept riser: round tube, twin spines", src="B1a", build=bow_B1a2, up=12, shots=[(15, 26, 34)], end=60,
              arrow=dict(vanes=4, vlen=0.07, vh=0.012, helix=6, lit=True), form="first",
              facts="swept bar as a round tube with glowing collar ports, twin spines either side; split limbs, binary cams roll 220; 5-pin; long rod + 2 back bars",
              lines=["B1a sibling: the swept bar is a round tube with glowing", "collar ports, braced by twin spines either side; split limbs,",
                     "binary cams roll 220; 5-pin; long rod + two back bars.", "Spines trace in first, then ring pixels fill the rest."]),
 "B1a3": dict(name="swept riser: blade + ladder, ports count", src="B1a", build=bow_B1a3, up=12, shots=[(15, 27, 35)], end=60,
              arrow=dict(vanes=4, vlen=0.08, vh=0.012, lit=True), form="ring_out",
              facts="swept deep blade with a ladder truss to an arc spine; 8 ports light one by one on the draw; single cam + idler; 3-pin",
              lines=["B1a sibling: the swept bar is a deep thin blade, laddered", "to a full-length arc spine; eight ports light one by one",
                     "from the grip out as the string comes back; single cam +", "idler; 3-pin. Ring pixels stream out from the grip."]),
 "B3a1": dict(name="W1 plate: slots, rear-deploy heads", src="B3a", build=bow_B3a1, up=12, shots=[(14, 23, 29)], end=55,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="mech", mech_n=3), form="thick", target="foam", mech_open=70, hip_quiver=True,
              facts="W1 plate with long rimmed slots; single cam; 3-pin; hip quiver; 3-blade rear-deploying heads swing back in the foam",
              lines=["B3a sibling: W1 plate riser with long rimmed slots; single", "cam; 3-pin; short rod; hip quiver instead of a bow quiver.",
                     "3-blade rear-deploying heads: blades swing back open in", "the foam. The plate grows in thickness, then the rest."]),
 "B3a2": dict(name="W1 plate: split plates, claw heads", src="B3a", build=bow_B3a2, up=12, shots=[(14, 24, 30)], end=56,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="mech", mech_len=0.065), form="plates", target="foam", mech_open=-75,
              facts="two thin W1 plates with a gap held by glowing spacer bolts, slide together as it forms; binary cams; 5-pin; long 2-blade claw heads open forward",
              lines=["B3a sibling: two thin W1 plates with a gap, held by glowing", "spacer bolts; the halves slide together as it forms; binary",
                     "cams; 5-pin; 3-arrow quiver. Long 2-blade claw heads open", "forward in the foam."]),
 "B3a3": dict(name="W1 plate: big windows, spinning heads", src="B3a", build=bow_B3a3, up=12, shots=[(14, 24, 30)], end=56,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="mech", mech_n=4), form="stamp", target="foam", mech_open=-60, mech_spin=True,
              facts="W1 plate with two big glowing-rimmed windows; 7 pins in one column; 5-arrow quiver; 4-blade heads spin as they open",
              lines=["B3a sibling: W1 plate with two big windows, glowing rims;", "7 pins stacked in one column; 5-arrow quiver; hybrid cams.",
                     "4-blade mechanical heads spin as they open in the foam.", "The plate stamps in whole, then the rims punch through."]),
 "B3b1": dict(name="truss: space frame, scanning laser", src="B3b", build=bow_B3b1, up=12, shots=[(18, 27, 34)], end=58, release_aid=True,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad3"), form="nodes", target="foam",
              laser=dict(src="rf", on=11, off=18, scan=True, reads=[("6", 12, 14), ("12", 14, 16), ("18", 16, 27)]), slide_f=15,
              facts="3D space-frame carbon riser (two chords each side, cross tubes); laser scans the target 11-17 and counts 6, 12, 18; slider pin drops; 3-blade heads",
              lines=["B3b sibling: a 3D space-frame carbon riser, chords on both", "sides joined by cross tubes; the rangefinder laser scans",
                     "across the target 11-17 and counts 6, 12, 18; the slider", "pin drops to match; hinge release; 3-blade heads."]),
 "B3b2": dict(name="truss: bowstring truss, laser pulses", src="B3b", build=bow_B3b2, up=12, shots=[(18, 27, 34)], end=58,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad2"), form="nodes", target="foam",
              laser=dict(src="rf", pulses=[(12, 13), (14, 15), (16, 17)], reads=[("18", 16, 27)]), slide_f=16,
              facts="bowstring-truss riser (curved front chord, straight back chord); rangefinder on the end of the front rod fires 3 pulses 12-17, reads 18; solid limbs, binary; 2-blade",
              lines=["B3b sibling: a bowstring-truss riser (curved front chord,", "straight back chord, posts, diagonals); the rangefinder is",
                     "on the end of the front rod and fires 3 pulses 12-17,", "reads 18; solid limbs, binary cams; 2-blade heads."]),
 "B3b3": dict(name="truss: K-truss, ring ranges", src="B3b", build=bow_B3b3, up=6, point=(8, 15), shots=[(18, 27, 34)], end=58, release_aid=True,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad2"), form="nodes", target="foam",
              laser=dict(src="ring", on=9, off=15, reads=[("18", 11, 18)]), slide_f=13,
              facts="K-truss riser with hex-nut nodes; the ring arm leads and points at the target 8-15, a laser from the ring reads 18; slider pin drops; then the draw",
              lines=["B3b sibling: K-truss riser with hex-nut nodes. The ring arm", "leads: it points at the target 8-15 and a laser from the",
                     "ring ranges it, 18 shows over the hand; the slider pin", "drops; then the hand goes to the string. Single cam."]),
 "B3c1": dict(name="cube riser: twisted helix, two shots", src="B3c", build=bow_B3c1, up=10, shots=[(12, 20, 25), (31, 38, 43)], end=64,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad3", lit=True), form="sweep", target="foam",
              facts="half-pixel cubes in a twisted double helix; release 25; a twist wave rolls through the cubes 26-31 as the 2nd arrow comes from the quiver; release 43",
              lines=["B3c sibling: half-pixel cubes in a twisted double helix;", "release 25; while the ring hand takes the second arrow",
                     "from the 4-arrow quiver a twist wave rolls through the", "cubes; draws 31-38, releases 43. 3-blade heads."]),
 "B3c2": dict(name="cube riser: outline, arrow from ring", src="B3c", build=bow_B3c2, up=10, shots=[(12, 20, 25), (33, 40, 45)], end=66,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad4", lit=True), form="outline_cubes", target="foam", ring_reload=True,
              facts="cubes trace only the riser outline (solid at the grip); no quiver: the 2nd arrow is built at the hand from ring cubes 27-32; release 25 and 45",
              lines=["B3c sibling: cubes trace only the riser's outline, solid at", "the grip. No quiver: after the first shot (25) the ring",
                     "throws cubes that build the second arrow at the hand", "27-32; draws 33-40, releases 45. 4-blade heads."]),
 "B3c3": dict(name="cube riser: checker, three shots", src="B3c", build=bow_B3c3, up=10, shots=[(12, 19, 23), (28, 34, 38), (43, 49, 53)], end=70,
              arrow=dict(vanes=3, vlen=0.07, vh=0.016, point="broad2", lit=True), form="random", target="foam",
              facts="dense checker of small cubes 2 wide x 3 deep; three fast shots from the 6-arrow quiver, release 23, 38, 53; 2-blade heads",
              lines=["B3c sibling: a dense checker of small cubes, 2 wide x 3", "deep; three fast shots from the 6-arrow quiver: releases",
                     "23, 38 and 53; the cubes flash in at random.", "2-blade heads, lighted nocks."]),
}


def archer_keys(T):
    """The shot keys for one or more shots (right-handed, ring on the draw hand); optional ring-arm point first."""
    aim_l = dict(arm_l=(90, 0, 90), fore_l=(0, 0, 0))
    HEAD = (-4, 0, 82)
    brace_pt = Vector((-18 * P + 0.22, -0.02, 22 * P + 0.02))
    anchor = Vector((-0.27, -0.03, 1.47))
    keys = [(1, {}), (T["up"], dict(head=(0, 0, 40), arm_l=(60, 0, 60), fore_l=(20, 0, 0), ik_r=(Vector((0.1, 0.25, 1.1)), "hand", [60, 0, 30, 60])))]
    if T.get("point"):                               # the ring arm leads: points at the target past the bow
        pa, pb = T["point"]
        pt = Vector((-0.6, 0.02, 1.6))
        keys += [(pa, dict(head=HEAD, **aim_l, ik_r=(pt, "hand", [120, 0, 70, 10]))), (pb, dict(head=HEAD, **aim_l, ik_r=(pt, "hand", [120, 0, 70, 10])))]
    for i, (fd, ff, fr) in enumerate(T["shots"]):
        if i == 0:
            keys.append((fd, dict(head=HEAD, **aim_l, ik_r=(brace_pt, "hand", [90, 0, 80, 20]))))
        keys += [(fd + int((ff - fd) * 0.55), dict(head=HEAD, **aim_l, ik_r=(brace_pt.lerp(anchor, 0.75), "hand", [100, 0, 100, 90]))),
                 (ff, dict(head=HEAD, **aim_l, ik_r=(anchor, "hand", [100, 0, 100, 120]))),
                 (fr, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.01, 0, 0)), "hand", [100, 0, 100, 120]))),
                 (fr + 2, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.12, -0.02, 0.0)), "hand", [100, 0, 100, 120])))]
        if i + 1 < len(T["shots"]):                  # reach to the quiver (or hold the hand up for the ring), back to the string
            nd = T["shots"][i + 1][0]
            if T.get("ring_reload"):
                rp = Vector((0.05, 0.3, 1.3))
                keys += [(fr + 4, dict(head=HEAD, **aim_l, ik_r=(rp, "hand", [80, 0, 40, 60]))), (nd - 3, dict(head=HEAD, **aim_l, ik_r=(rp, "hand", [80, 0, 40, 60])))]
            else:
                keys += [(min(fr + 5, nd - 3), dict(head=HEAD, **aim_l, ik_r=(lambda p: fk(p, "l")[0] + Vector((0.12, 0.05, -0.06)), "hand", [70, 0, 60, 40])))]
            keys += [(nd - 1, dict(head=HEAD, **aim_l, ik_r=(brace_pt, "hand", [90, 0, 80, 20])))]
    fr = T["shots"][-1][2]
    keys += [(fr + 10, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.14, -0.03, -0.02)), "hand", [100, 0, 100, 120])))]
    keys.append((min(T["end"] - 2, fr + 20), dict(head=(0, 0, 30), arm_l=(20, 0, 20), fore_l=(10, 0, 0))))
    return keys


def Mb_up(broot, p):
    """Position along the bow's limb axis (bow local +Y) at the forming frame."""
    return (broot.matrix_world.inverted() @ p).y


def build_bow_take(code, bi):
    T = BOWS[code]; bx = bi * BAY; tag = f"BS3 {code}"
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
    if T.get("hip_quiver"):                                  # a hip quiver on the right side of the belt
        hq = empty(f"{tag} hip quiver", (7.5 * P, 0.02, 0.02), rig["body"]); hq.rotation_euler = (R(-15), R(8), 0)
        cyl(f"{tag} hip quiver tube", 0.045, 0.32, DARK, 10, hq, loc=(0, 0, -0.3), axis="Z", r2=0.05)
        torus(f"{tag} hip quiver lip", 0.05, 0.006, RM, loc=(0, 0, 0.02), parent=hq)
        for k in range(3):
            a_, _ = arrow2(f"{tag} hip {k}", hq, L=0.55, point="mech", vanes=3, wrap=False, mech_n=3)
            a_.location = (0.02 * math.cos(k * 2.1), 0.02 * math.sin(k * 2.1), 0.14); a_.rotation_euler = (0, 0, k)
    peep = None
    if B["compound"]:
        peep = torus(f"{tag} peep", 0.008, 0.002, RM, axis="Z"); peep.rotation_mode = "QUATERNION"
        dloop = torus(f"{tag} d-loop", 0.009, 0.002, RM, axis="X"); dloop.rotation_mode = "QUATERNION"
    else:
        dloop = None
        kisser = ball(f"{tag} kisser", 0.006, W, (0, 0, 0), None, 10)
    target = make_target(tag, bx, T.get("target", "boss"))
    tgts = [target + Vector((0.0, 0, 0.05)), target + Vector((0.07, 0, -0.04)), target + Vector((-0.07, 0, -0.02))]
    flights = [None] * len(shots); hits = [None] * len(shots)
    qsrc = [None] + [B["quiver"][-i] for i in range(1, len(shots))] if (len(shots) > 1 and B.get("quiver")) else [None] * len(shots)

    def state(f):
        for i, (fd, ff, fr) in enumerate(shots):
            if fd <= f < fr:
                return smooth((f - fd) / (ff - fd)), None, i
            if fr <= f < fr + 5:
                return 0.0, f - fr, i
        return 0.0, None, None

    laser = None; LZ = T.get("laser")
    if LZ:
        laser = cyl(f"{tag} laser", 0.0018, 1.0, LASER, 6, None, axis="Z"); laser.rotation_mode = "QUATERNION"
        if LZ.get("pulses"):
            for k, (a_, b_) in enumerate(LZ["pulses"]):
                for f_, h in (((1, True), (a_, False), (b_, True)) if k == 0 else ((a_, False), (b_, True))):
                    laser.hide_render = h; laser.keyframe_insert("hide_render", frame=f_); laser.hide_viewport = h; laser.keyframe_insert("hide_viewport", frame=f_)
        else:
            show(laser, LZ["on"], LZ["off"])
        lsrc = B["rf"] if LZ["src"] == "rf" else rig["ring_pt"]
        for txt, a_, b_ in LZ["reads"]:
            rd = label(txt, (0.0, 0.0, 0.0), LASER, 0.035 if LZ["src"] == "rf" else 0.05, (0, 0, 0)); rd.parent = lsrc
            rd.location = (0.03, 0.02, -0.02) if LZ["src"] == "rf" else (0.0, 0.0, 0.0)
            rd.rotation_euler = (R(90), 0, R(90)); show(rd, a_, b_)
            if LZ["src"] != "rf":                         # over the hand, world-placed each frame below
                rd.parent = None; rd.rotation_euler = (R(90), 0, R(90)); ring_reads = rd
    tw0 = {c_.name: c_.rotation_euler[1] for c_ in B.get("twist", [])}
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
            key(B["slide"], f, loc=(0.0045, 0.018 - 0.03 * smooth((f - T.get("slide_f", 14)) / 4.0), -0.03))
        if "full_glow" in B:
            anim_emit(B["full_glow"], [(f, 0.8 + 4.2 * u)])
        for k, m_ in enumerate(B.get("port_mats", [])):
            anim_emit(m_, [(f, 0.3 + 4.5 * smooth(u * 8 - k))])
        if "twist" in B and len(shots) > 1:
            f0 = shots[0][2] + 1
            for k2, c_ in enumerate(B["twist"]):
                t2 = f - f0 - (k2 // 2) * 0.2
                key(c_, f, rot=(0, tw0[c_.name] + (R(90) * math.sin(math.pi * t2 / 4.0) if 0 < t2 < 4 else 0), 0))
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
            a = lsrc.matrix_world.translation.copy(); tg_ = tgts[0]
            if LZ.get("scan"):
                tg_ = tgts[0] + Vector((0.6 * math.cos((f - LZ["on"]) * 0.9), 0, 0.4 * math.sin((f - LZ["on"]) * 1.3))) * max(0, 1 - (f - LZ["on"]) / 6.0)
            d = tg_ - a
            if LZ["src"] != "rf":
                ring_reads.location = a + Vector((0.0, 0.05, 0.09)); ring_reads.keyframe_insert("location", frame=f)
            laser.location = a; laser.rotation_quaternion = d.to_track_quat("Z", "Y"); laser.scale = (1, 1, d.length)
            for path in ("location", "rotation_quaternion", "scale"):
                laser.keyframe_insert(path, frame=f)
        for i, (ar, ex) in enumerate(arrows):
            fd, ff, fr = shots[i]
            if f < fr:
                if i > 0 and T.get("ring_reload"):                                  # built at the hand, then to the string
                    t = smooth((f - (fd - 2)) / 2.0)
                    ar.location = (hand + Vector((0.0, 0.08, 0.04))).lerp(nock, t) if f < fd else nock
                    ar.rotation_quaternion = fwd.to_track_quat("-Z", "Y")
                elif i > 0 and f < shots[i - 1][2] + 3 and qsrc[i] is not None:     # still in the quiver
                    qm = qsrc[i].matrix_world
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
    for i in range(1, len(shots)):                                      # the quiver arrows that were taken
        if qsrc[i] is not None:
            key(qsrc[i], 1, sc=1.0); key(qsrc[i], shots[i - 1][2] + 3, sc=1.0); key(qsrc[i], shots[i - 1][2] + 4, sc=0.0001)
    pm_ = pixel_mesh(CM["pix"])
    for i, (ar, ex) in enumerate(arrows):                               # arrows form (the first on the string)
        a0 = 8 if i == 0 else shots[i - 1][2] + 3
        if i > 0 and T.get("ring_reload"):                              # cubes thrown off the ring build it at the hand
            a0 = shots[i - 1][2] + 6
            ms = [o for o in ar.children_recursive if o.type == "MESH"]
            for k, o in enumerate(ms):
                fa = a0 + int(5 * k / max(1, len(ms) - 1))
                key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 1, sc=1.0)
            for k in range(14):
                px = link(bpy.data.objects.new(f"{tag} reload cube", pm_)); fa = a0 + int(5 * k / 13) - 2
                scene.frame_set(fa); bpy.context.view_layer.update()
                s0 = rig["ring_pt"].matrix_world.translation.copy()
                scene.frame_set(fa + 2); bpy.context.view_layer.update()
                e0 = rig["hand_pt"].matrix_world.translation + Vector((0, 0.08, 0.04)) + (fwd * (-0.05 * k))
                key(px, 1, loc=s0, sc=0.0001); key(px, fa, loc=s0, sc=0.0001); key(px, fa + 1, loc=s0 + Vector((0, 0, 0.06)), sc=1.2)
                key(px, fa + 2, loc=e0, sc=0.8); key(px, fa + 3, loc=e0, sc=0.0001)
            continue
        for o in ar.children_recursive:
            if o.type == "MESH":
                if i == 0:
                    key(o, 1, sc=0.0001); key(o, a0, sc=0.0001); key(o, a0 + 4, sc=1.0)
                else:
                    key(o, 1, sc=0.0001); key(o, a0, sc=0.0001); key(o, a0 + 1, sc=1.0)
        mo = T.get("mech_open", -55)
        for h in ex.get("mech", []):                                    # mechanical blades flick open on impact
            key(h, 1, rot=(0, 0, 0)); key(h, hits[i] or END, rot=(0, 0, 0)); key(h, (hits[i] or END) + 1, rot=(0, R(mo), 0))
        if T.get("mech_spin") and hits[i]:                              # the whole head spins as it opens
            for h in ex.get("mech", []):
                pv = h.parent; r0 = pv.rotation_euler[2]
                key(pv, 1, rot=(0, 0, r0)); key(pv, hits[i], rot=(0, 0, r0)); key(pv, hits[i] + 4, rot=(0, 0, r0 + R(270)))
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
    first = B.get("first", [])
    if mode == "trace":          # a pixel trace from the top cam down to the bottom
        form_by(meshes, 3, fu, lambda p: -(Mb_up(broot, p)), ring_w, CM["pix"], tag, 0.4, fu)
    elif mode == "first":        # spines / bracing trace in first (top to bottom), then ring pixels fill the rest
        rest_ = [o for o in meshes if o not in first]
        form_by(first, 2, 7, lambda p: -(Mb_up(broot, p)), None, None, tag, 0.0, fu)
        form_by(rest_, 6, fu, lambda p: (p - ring_w).length, ring_w, CM["pix"], tag, 0.5, fu)
    elif mode == "ring_out":     # ring pixels to the grip first, then out to the tips
        form_by(meshes, 3, fu, lambda p: (p - grip_w).length, ring_w, CM["pix"], tag, 0.5, fu)
    elif mode == "thick":        # the riser plate grows in thickness, then the rest from the grip
        th = B["thick"]; rest_ = [o for o in meshes if o is not th]
        key(th, 1, sc=(0.0001, 1, 1)); key(th, 2, sc=(0.0001, 1, 1)); key(th, 6, sc=(1, 1, 1))
        form_by(rest_, 5, fu, lambda p: (p - grip_w).length, None, None, tag, 0.0, fu)
    elif mode == "plates":       # the two halves slide in from the sides, then bolts, then the rest
        for hp, sx in B["plates"]:
            key(hp, 1, loc=(sx * 0.25, 0, 0)); key(hp, 2, loc=(sx * 0.25, 0, 0)); key(hp, 7, loc=(0, 0, 0))
        rest_ = [o for o in meshes if o.parent not in [hp for hp, _ in B["plates"]]]
        form_by(rest_, 6, fu, lambda p: (p - grip_w).length, None, None, tag, 0.0, fu)
    elif mode == "stamp":        # the plate stamps in whole, the rest grows from the grip, the window rims punch last
        st = B["stamp"]; last = B["last"]; rest_ = [o for o in meshes if o is not st and o not in last]
        key(st, 1, sc=0.0001); key(st, 2, sc=0.0001); key(st, 3, sc=1.15); key(st, 4, sc=1.0)
        form_by(rest_, 4, fu - 2, lambda p: (p - grip_w).length, None, None, tag, 0.0, fu)
        for r_ in last:
            key(r_, 1, sc=0.0001); key(r_, fu - 2, sc=0.0001); key(r_, fu, sc=1.0)
    elif mode == "outline_cubes":  # outline cubes run up from the grip both ways, the grip fills last
        form_by(meshes, 2, fu, lambda p: -(p - grip_w).length, ring_w, CM["pix"], tag, 0.3, fu)
    elif mode == "random":       # cubes flash in at random
        form_by(meshes, 2, fu, lambda p: rng.random(), ring_w, CM["pix"], tag, 0.2, fu, grow=1)
    elif mode == "ring":           # pixels stream from the ring to every part, in order from the ring outward
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



# ------------------------------------------------------------------ shields: shared

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



# ------------------------------------------------------------------ shields (850): held from behind, the arms never touch them
F_HIT = 30
STAND = dict(leg_l=(18, 0, 0), shin_l=(-14, 0, 0), leg_r=(-10, 0, 0), body=(-4, 0, 0))


def hold_pose(grips, legs=STAND):
    """Solve both arms so each hand's end sits on its grip (root space). Returns the pose dict."""
    HOLD = dict(IDLE); HOLD.update(legs)
    for side, g in grips.items():
        a, fo, err = solve(HOLD, side, Vector(g), "hand", [80.0, 0.0, 0.0, 30.0])
        HOLD["arm_" + side], HOLD["fore_" + side] = a, fo
    return HOLD


def hold_keys(rig, bx, HOLD, up=5, rel=(50, 58), give=0.035, root_z=0.0):
    """Arms up by `up`, hold, a recoil of the whole body + shield at the hit, let go after rel[0]."""
    K = dict(HOLD, root_loc=(0, 0, root_z))
    pose_keys(rig, bx, [(1, {}), (up, K), (F_HIT - 1, K), (F_HIT + 1, dict(K, head=(-8, 0, 0), root_loc=(0, -give, root_z))),
                        (F_HIT + 5, dict(K, root_loc=(0, -give * 0.3, root_z))), (F_HIT + 10, K), (rel[0], K), (rel[1], {})])


def grip_mounts(tag, sf, HOLD, back_y, length=0.22):
    """A grip bar just past each hand (across the forearm), and two standoffs from it forward to the shield's back
    surface; back_y(x, z) gives the back surface's y in the shield frame. Returns the parts."""
    parts = []
    for side in ("r", "l"):
        if ("arm_" + side) not in HOLD:
            continue
        hand, _, el = fk(HOLD, side)
        d = (hand - el).normalized()
        up = Vector((0, 0, 1)); up = (up - d * up.dot(d)).normalized()
        c = hand + d * 0.026 - sf.location
        a_, b_ = c - up * length / 2, c + up * length / 2
        parts.append(rod(f"{tag} grip bar {side}", a_, b_, 0.014, GR, sf, 10))
        for k, e in enumerate((a_, b_)):
            parts.append(rod(f"{tag} grip standoff {side} {k}", e, Vector((e.x, back_y(e.x, e.z) + 0.004, e.z)), 0.01, RM, sf, 8))
    return parts


def fade_out(objs, f0=50, f1=53):
    for o in objs:
        sc = tuple(o.scale)
        key(o, f0, sc=sc); key(o, f1, sc=0.0001)


def shield_frame_root(tag, rig, loc):
    return empty(f"{tag} shield frame", loc, rig["root"])


def curved_brick(name, a0, a1, z0, z1, Rc, th, m, par, n=5, zcurve=None):
    """One brick on a cylinder of radius Rc (axis z, centre at y=-Rc), optionally also bowed in z."""
    arc = np.linspace(a0, a1, n); vs = []
    for r_ in (Rc, Rc - th):
        for z in (z0, z1):
            for a in arc:
                bow = zcurve(z) if zcurve else 0.0
                vs.append((r_ * math.sin(a), r_ * math.cos(a) - Rc + bow, z))
    def vi(ri, zi, ai):
        return ri * 2 * n + zi * n + ai
    fs = []
    for ai in range(n - 1):
        fs += [(vi(0, 0, ai), vi(0, 0, ai + 1), vi(0, 1, ai + 1), vi(0, 1, ai)), (vi(1, 0, ai), vi(1, 1, ai), vi(1, 1, ai + 1), vi(1, 0, ai + 1)),
               (vi(0, 0, ai), vi(1, 0, ai), vi(1, 0, ai + 1), vi(0, 0, ai + 1)), (vi(0, 1, ai), vi(0, 1, ai + 1), vi(1, 1, ai + 1), vi(1, 1, ai))]
    fs += [(vi(0, 0, 0), vi(0, 1, 0), vi(1, 1, 0), vi(1, 0, 0)), (vi(0, 0, n - 1), vi(1, 0, n - 1), vi(1, 1, n - 1), vi(0, 1, n - 1))]
    return mesh_obj(name, vs, fs, m, par, uvt=0.3)


def wpos_l(o):
    """Mesh centre in its parent's space (for flying a part in from a point)."""
    return Vector(np.mean([v.co for v in o.data.vertices], axis=0))


def build_H2a1(tag, rig, bx):
    """Brick tower with an arched top: running-bond BR1 courses on a curve, the top course follows a round arch with a
    keystone; each brick flies in from the ring and lands (a mason laying it); the hit knocks the nearby bricks back
    and they settle one by one. 1.0 x 1.9."""
    HOLD = hold_pose({"r": (0.15, 0.42, 1.32), "l": (-0.15, 0.42, 1.12)})
    hold_keys(rig, bx, HOLD)
    sf = shield_frame_root(tag, rig, (0.0, 0.70, 0.98))
    BRM = strip("br1", f"{tag} bricks", alpha=0.9, emit=1.3)
    Rc, Wd, Ht, rows = 1.4, 1.0, 1.9, 10; span = Wd / Rc; th = 0.04
    bricks = []
    for i in range(rows):
        z0 = -Ht / 2 + i * (Ht - 0.3) / (rows - 1); z1 = z0 + (Ht - 0.3) / (rows - 1) - 0.012
        nb = 3; off = 0.5 if i % 2 else 0.0
        edges = sorted(set(min(span / 2, max(-span / 2, -span / 2 + (k + off) * span / nb)) for k in range(-1, nb + 1)))
        for k in range(len(edges) - 1):
            a0, a1 = edges[k] + 0.006 / Rc, edges[k + 1] - 0.006 / Rc
            if a1 - a0 < 0.02:
                continue
            bricks.append(curved_brick(f"{tag} brick {i} {k}", a0, a1, z0, z1, Rc, th, BRM, sf))
    arch = []                                            # the arch: voussoirs round a half circle on top
    za = Ht / 2 - 0.3; ra = Wd / 2
    for k in range(9):
        t0, t1 = math.pi * k / 9 + 0.01, math.pi * (k + 1) / 9 - 0.01
        vs = []
        for rr in (ra - 0.16, ra):
            for t in (t0, t1):
                x = rr * math.cos(t); z = za + rr * math.sin(t) * 0.6
                a = x / Rc
                vs += [(Rc * math.sin(a), Rc * math.cos(a) - Rc, z), (Rc * math.sin(a), Rc * math.cos(a) - Rc - th, z)]
        fs = [(0, 2, 6, 4), (1, 5, 7, 3), (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)]
        arch.append(mesh_obj(f"{tag} voussoir {k}", vs, fs, RM if k == 4 else BRM, sf, uvt=0.3))
    fill = mesh_obj(f"{tag} tympanum", [(Rc * math.sin(ra * math.cos(t) / Rc), Rc * math.cos(ra * math.cos(t) / Rc) - Rc - 0.02, za + (ra - 0.16) * math.sin(t) * 0.6) for t in np.linspace(0, math.pi, 12)],
                    [tuple(range(12))], mat(f"{tag} tympanum glass", tuple(np.array(CM["c"]) * 0.4), emit=0.8, alpha=0.5, rough=0.1), sf)
    grips = grip_mounts(tag, sf, HOLD, lambda x, z: Rc * math.cos(x / Rc) - Rc - th)
    for o in grips:
        key(o, 1, sc=0.0001); key(o, 4, sc=0.0001); key(o, 6, sc=1.0)
    # bricks fly in from the ring, bottom course first, one every third of a tick
    scene.frame_set(5); bpy.context.view_layer.update(); ring_w = rig["ring_pt"].matrix_world.translation.copy()
    allb = bricks + arch + [fill]
    order = sorted(allb, key=lambda o: (wpos(o).z, wpos(o).x))
    for k, o in enumerate(order):
        fa = 5 + int(k * 8 / len(order))
        home = o.location.copy()
        src = sf.matrix_world.inverted() @ (ring_w + Vector((0.0, 0.4, 0.15)))     # thrown from just ahead of the ring
        key(o, 1, loc=src - wpos_l(o), sc=0.0001); key(o, fa - 2, loc=src - wpos_l(o), sc=0.0001); key(o, fa - 1, loc=src - wpos_l(o), sc=0.4)
        key(o, fa, loc=home + Vector((0, 0.06, 0)), sc=1.0); key(o, fa + 1, loc=home, sc=1.0)
    imp_l = Vector((0.1, 0.0, 0.25))
    for o in bricks:                                     # the hit knocks the near bricks back; they settle in turn
        d = (wpos(o) - (sf.matrix_world @ imp_l)).length
        if d < 0.45:
            home = o.location.copy(); f0 = F_HIT + int(d * 10)
            key(o, F_HIT, loc=home); key(o, F_HIT + 1, loc=home + Vector((0, -0.05 * (1 - d / 0.45), 0)))
            key(o, f0 + 3, loc=home + Vector((0, 0.01, 0))); key(o, f0 + 5, loc=home)
    anim_emit(BRM, [(1, 1.3), (F_HIT, 1.3), (F_HIT + 1, 2.6), (F_HIT + 8, 1.3)])
    fade_out(allb + grips)
    return sf.matrix_world @ imp_l, 31


def build_H2a2(tag, rig, bx):
    """Barrel brick tower: BR1 bricks in stack bond (columns) on a surface curved both ways (like a barrel stave), with
    a rim frame; the columns rise up from the ground in front of you; the hit flashes the mortar, brick by brick out
    from the impact. 1.05 x 1.85."""
    HOLD = hold_pose({"r": (0.16, 0.40, 1.30), "l": (-0.16, 0.40, 1.10)})
    hold_keys(rig, bx, HOLD)
    sf = shield_frame_root(tag, rig, (0.0, 0.70, 0.96))
    Rc, Wd, Ht, th = 1.1, 1.05, 1.85, 0.04; span = Wd / Rc
    zc = lambda z: -0.12 * (2 * z / Ht) ** 2             # bowed top and bottom back toward you
    bands = [strip("br1", f"{tag} bricks {k}", alpha=0.9, emit=1.3) for k in range(5)]
    imp_l = Vector((-0.1, 0.0, 0.2))
    cols = 5; rows = 12; bricks = []
    for c in range(cols):
        a0 = -span / 2 + c * span / cols + 0.006 / Rc; a1 = -span / 2 + (c + 1) * span / cols - 0.006 / Rc
        for r_ in range(rows):
            z0 = -Ht / 2 + r_ * Ht / rows; z1 = z0 + Ht / rows - 0.012
            xm = Rc * math.sin((a0 + a1) / 2); d = math.hypot(xm - imp_l.x, (z0 + z1) / 2 - imp_l.z)
            o = curved_brick(f"{tag} brick {c} {r_}", a0, a1, z0, z1, Rc, th, bands[min(4, int(d / 0.22))], sf, 4, zcurve=zc)
            bricks.append((o, c, r_))
    frame = []
    for s in (-1, 1):
        a = s * span / 2
        frame.append(sweep(f"{tag} rim post {s}", [(Rc * math.sin(a), Rc * math.cos(a) - Rc + zc(z) + 0.01, z) for z in np.linspace(-Ht / 2 - 0.02, Ht / 2 + 0.02, 9)],
                           0.045, 0.05, RM, sf, side=(math.cos(a), -math.sin(a), 0)))
    for z in (-Ht / 2 - 0.02, Ht / 2 + 0.02):
        frame.append(sweep(f"{tag} rim bar {z:.2f}", [(Rc * math.sin(a), Rc * math.cos(a) - Rc + zc(z) + 0.01, z) for a in np.linspace(-span / 2, span / 2, 9)], 0.045, 0.05, RM, sf, side=(0, 0, 1)))
    grips = grip_mounts(tag, sf, HOLD, lambda x, z: Rc * math.cos(x / Rc) - Rc - th + zc(z))
    for o in grips:
        key(o, 1, sc=0.0001); key(o, 4, sc=0.0001); key(o, 6, sc=1.0)
    for o, c, r_ in bricks:                              # columns rise from the ground: each brick slides up into place
        fa = 5 + r_ // 2 + abs(c - 2)
        home = o.location.copy()
        key(o, 1, loc=home + Vector((0, 0, -0.35)), sc=0.0001); key(o, fa - 1, loc=home + Vector((0, 0, -0.25)), sc=0.0001)
        key(o, fa, loc=home + Vector((0, 0, -0.08)), sc=1.0); key(o, fa + 2, loc=home, sc=1.0)
    for k, o in enumerate(frame):
        key(o, 1, sc=0.0001); key(o, 12, sc=0.0001); key(o, 14, sc=1.0)
    for k, m in enumerate(bands):
        anim_emit(m, [(1, 1.3), (F_HIT + k, 1.3), (F_HIT + k + 1, 3.6), (F_HIT + k + 4, 1.3)])
    fade_out([o for o, _, _ in bricks] + frame + grips)
    return sf.matrix_world @ imp_l, 31


def build_H2a3(tag, rig, bx):
    """Folding brick screen: five flat facets set at angles to make the curve, each faced with BR1 bricks in a
    herringbone pattern; the facets unfold out from the centre one like a folding screen; the hit punches one brick out
    of the wall and it flies back in and re-seats. 1.1 x 1.8."""
    HOLD = hold_pose({"r": (0.15, 0.42, 1.30), "l": (-0.15, 0.42, 1.10)})
    hold_keys(rig, bx, HOLD)
    sf = shield_frame_root(tag, rig, (0.0, 0.72, 0.97))
    BRM = strip("br1", f"{tag} bricks", alpha=0.9, emit=1.3)
    Ht = 1.8; fw = 0.22; n = 5; turn = R(14)
    GL = mat(f"{tag} facet glass", tuple(np.array(CM["c"]) * 0.35), emit=0.6, alpha=0.55)
    panels = []
    def facet(par, k, x0, x1):
        o = [bx_(tag, f"facet back {k}", (min(x0, x1), -0.03, -Ht / 2), (max(x0, x1), -0.022, Ht / 2), GL, par)]
        for j in range(12):                              # herringbone: alternating 45 degree bricks
            z = -Ht / 2 + (j + 0.5) * Ht / 12
            for i in range(2):
                b = bx_(tag, f"hb {k} {j} {i}", (-0.055, -0.02, -0.018), (0.055, 0.0, 0.018), BRM, par)
                b.location = (x0 + (x1 - x0) * (0.27 + 0.46 * i), 0, z); b.rotation_euler = (0, R(45 if (i + j) % 2 else -45), 0)
                o.append(b)
        o.append(bx_(tag, f"facet rail {k}", (x1 - 0.012, -0.032, -Ht / 2 - 0.02), (x1 + 0.012, 0.012, Ht / 2 + 0.02), RM, par))
        return o
    centre = empty(f"{tag} facet centre", (0, 0, 0), sf)
    panels += facet(centre, "c", -fw / 2, fw / 2)
    folds = []
    for sgn in (-1, 1):
        par = centre
        for k in range(1, 3):
            hg = empty(f"{tag} hinge {sgn} {k}", (sgn * fw / 2, 0, 0) if k == 1 else (sgn * fw, 0, 0), par)
            folds.append((hg, sgn, k))
            panels += facet(hg, f"{sgn} {k}", 0, sgn * fw)
            par = hg
    grips = grip_mounts(tag, sf, HOLD, lambda x, z: -0.03 - max(0.0, abs(x) - fw / 2) * 0.25)
    for o in grips:
        key(o, 1, sc=0.0001); key(o, 4, sc=0.0001); key(o, 6, sc=1.0)
    key(centre, 1, sc=0.0001); key(centre, 4, sc=0.0001); key(centre, 6, sc=1.0)
    for hg, sgn, k in folds:                             # unfold: folded flat behind the centre, swing out in turn
        key(hg, 1, rot=(0, 0, sgn * R(170))); key(hg, 4 + 2 * k, rot=(0, 0, sgn * R(170)))
        key(hg, 8 + 2 * k, rot=(0, 0, -sgn * (turn + R(4)))); key(hg, 10 + 2 * k, rot=(0, 0, -sgn * turn))
    scene.frame_set(F_HIT); bpy.context.view_layer.update()
    tgt_b = min([b for b in panels if " hb " in b.name], key=lambda b: (wpos(b) - (sf.matrix_world @ Vector((0.05, 0, 0.22)))).length)
    imp = wpos(tgt_b)
    h0 = tgt_b.location.copy(); r0 = tuple(tgt_b.rotation_euler)
    # punched out of the wall: it pops out sideways past the edge (never back toward the arms), tumbles, flies home
    key(tgt_b, F_HIT, loc=h0, rot=r0); key(tgt_b, F_HIT + 2, loc=h0 + Vector((0.12, 0.25, 0.1)), rot=(R(80), r0[1], R(40)))
    key(tgt_b, F_HIT + 7, loc=h0 + Vector((0.3, 0.35, 0.05)), rot=(R(200), r0[1], R(60))); key(tgt_b, F_HIT + 11, loc=h0 + Vector((0, 0.03, 0)), rot=r0)
    key(tgt_b, F_HIT + 12, loc=h0, rot=r0)
    anim_emit(BRM, [(1, 1.3), (F_HIT, 1.3), (F_HIT + 1, 2.4), (F_HIT + 6, 1.3)])
    fade_out([centre] + grips)
    return imp + Vector((0, 0.02, 0)), 31


def h1_slat(name, w, h, curve, m, par, th=0.03):
    pts = [(x, curve * (1 - (2 * x / max(1e-3, w)) ** 2), 0) for x in np.linspace(-w / 2, w / 2, 9)]
    return sweep(name, pts, h, th, m, par, side=(0, 0, 1))


def heater_w(t):
    return 1.0 if t < 0.5 else 1.0 - 0.85 * ((t - 0.5) / 0.5) ** 1.3


def build_H2c1(tag, rig, bx):
    """Telescoping fan heater: the H1 slats stand upright and slide out sideways from a centre slat (left and right in
    turn) into the heater outline; on the hit the slats shiver sideways in a wave. 1.0 x 1.7."""
    HOLD = hold_pose({"r": (0.15, 0.42, 1.32), "l": (-0.15, 0.42, 1.12)})
    hold_keys(rig, bx, HOLD)
    sf = shield_frame_root(tag, rig, (0.0, 0.72, 1.02))
    HM = strip("h1", f"{tag} hex", alpha=0.88, emit=1.3)
    Ht = 1.7; ncol = 7; cw = 1.0 / ncol; cols = []
    for c in range(ncol):
        xc = -0.5 + (c + 0.5) * cw; t_ = abs(xc) / 0.5
        top = Ht / 2                                     # pointed foot: each column stops where the heater is that wide
        tt = max([t for t in np.linspace(0, 1, 101) if heater_w(t) / 2 >= abs(xc) - cw * 0.3] or [0.5])
        bot = top - Ht * tt
        piv = empty(f"{tag} column pivot {c}", (0, 0, 0), sf)
        zs = np.linspace(bot, top, 6)
        s = sweep(f"{tag} column {c}", [(xc, -0.25 * xc * xc, z) for z in zs], cw - 0.012, 0.03, HM, piv, side=(1, 0.5 * xc, 0))
        e_ = sweep(f"{tag} column cap {c}", [(xc, -0.25 * xc * xc + 0.02, top + 0.01), (xc, -0.25 * xc * xc + 0.02, top + 0.03)], cw - 0.02, 0.02, RM, piv, side=(1, 0, 0))
        cols.append((piv, xc, c))
    grips = grip_mounts(tag, sf, HOLD, lambda x, z: -0.25 * x * x - 0.016)
    for o in grips:
        key(o, 1, sc=0.0001); key(o, 4, sc=0.0001); key(o, 6, sc=1.0)
    for piv, xc, c in cols:                              # all stacked at the centre, then telescope out sideways
        f_out = 5 + abs(c - 3)
        key(piv, 1, loc=(-xc, 0, 0), sc=0.0001); key(piv, 5, loc=(-xc, 0, 0), sc=1.0)
        key(piv, f_out, loc=(-xc, 0, 0)); key(piv, f_out + 3, loc=(0.03 * np.sign(xc), 0, 0)); key(piv, f_out + 5, loc=(0, 0, 0))
    imp_l = Vector((0.08, 0.0, 0.2))
    for piv, xc, c in cols:
        d = int(abs(xc - imp_l.x) / 0.14)
        key(piv, F_HIT + d, loc=(0, 0, 0)); key(piv, F_HIT + d + 2, loc=(0.03 * (1 if xc >= imp_l.x else -1), -0.03, 0)); key(piv, F_HIT + d + 5, loc=(-0.01 * (1 if xc >= imp_l.x else -1), 0, 0))
        key(piv, F_HIT + d + 8, loc=(0, 0, 0))
    fade_out([p for p, _, _ in cols] + grips)
    return sf.matrix_world @ imp_l, 31


def build_H2c2(tag, rig, bx):
    """Nested telescoping heater: five heater-outline frames, each filled with H1, nest inside each other at a small
    boss and telescope forward and out, biggest last, like a collapsible cup; the hit pushes the rings back in depth
    order from the centre out. 1.0 x 1.7."""
    HOLD = hold_pose({"r": (0.15, 0.42, 1.30), "l": (-0.15, 0.42, 1.10)})
    hold_keys(rig, bx, HOLD)
    sf = shield_frame_root(tag, rig, (0.0, 0.84, 1.0))
    HM = strip("h1", f"{tag} hex", alpha=0.85, emit=1.2)
    def outline(s, n=14):
        right = [(0.5 * math.cos(u * math.pi / 2) ** 0.6, 0.85 - 1.7 * u ** 1.3) for u in np.linspace(0, 1, n)]
        left = [(-x, z) for x, z in reversed(right[:-1])]
        return [(x * s, z * s) for x, z in right + left[:-1]]
    def inside(pt, poly):
        x, z = pt; c = False
        for i in range(len(poly)):
            (x1, z1), (x2, z2) = poly[i], poly[i - 1]
            if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-12) + x1:
                c = not c
        return c
    STEP = 0.05
    rings = []
    scales = [0.25, 0.43, 0.61, 0.8, 1.0]
    for k, s in enumerate(scales):
        piv = empty(f"{tag} nest {k}", (0, 0, 0), sf)
        o_ = outline(s); i_ = outline(scales[k - 1] - 0.005) if k else []
        holder = empty(f"{tag} nest holder {k}", (0, 0, 0), piv); holder.rotation_euler = (0, 0, R(90))
        plate(f"{tag} nest fill {k}", [(-x, z) for x, z in o_], [[(-x, z) for x, z in i_]] if i_ else [], -0.012, 0.012, HM, holder, uvt=0.35)
        sweep(f"{tag} nest rim {k}", [(x, 0.0, z) for x, z in o_], 0.03, 0.03, RM, piv, side=(0, 1, 0), closed=True)
        rings.append((piv, k))
    boss = ball(f"{tag} boss", 0.06, W, (0, 0.03, 0.0), sf, 12)
    grips = grip_mounts(tag, sf, HOLD, lambda x, z: -0.012 - STEP * min([k for k, s_ in enumerate(scales) if inside((x, z), outline(s_))] or [4]))
    for o in grips:
        key(o, 1, sc=0.0001); key(o, 4, sc=0.0001); key(o, 6, sc=1.0)
    key(boss, 1, sc=0.0001); key(boss, 5, sc=0.0001); key(boss, 6, sc=1.0)
    for piv, k in rings:                                 # all nested small at the boss, telescope out, stepping back
        depth = -STEP * k
        f_ = 6 + k
        key(piv, 1, loc=(0, 0, 0), sc=0.0001); key(piv, 5, loc=(0, 0, 0), sc=0.0001); key(piv, 6, loc=(0, 0, 0), sc=scales[0] / scales[k])
        key(piv, f_, loc=(0, 0, 0), sc=scales[0] / scales[k]); key(piv, f_ + 3, loc=(0, depth + 0.01, 0), sc=1.03); key(piv, f_ + 5, loc=(0, depth, 0), sc=1.0)
    imp_l = Vector((0.05, 0.03, 0.15))
    for piv, k in rings:
        depth = -STEP * k
        key(piv, F_HIT + k, loc=(0, depth, 0)); key(piv, F_HIT + k + 2, loc=(0, depth - 0.025 * (5 - k) / 5, 0)); key(piv, F_HIT + k + 6, loc=(0, depth, 0))
    fade_out([p for p, _ in rings] + [boss] + grips)
    return sf.matrix_world @ imp_l, 31


def build_H2c3(tag, rig, bx):
    """Roller-shutter heater: a header bar forms over the grips, then nine thin H1 slats unroll down from it, each
    hinged to the one above, into the heater outline; the hit swings the hinged slats back in a ripple down the chain.
    1.0 x 1.7."""
    HOLD = hold_pose({"r": (0.15, 0.42, 1.32), "l": (-0.15, 0.42, 1.12)})
    hold_keys(rig, bx, HOLD)
    sf = shield_frame_root(tag, rig, (0.0, 0.70, 1.02))
    HM = strip("h1", f"{tag} hex", alpha=0.88, emit=1.3)
    Ht = 1.7; n = 9; sh = Ht / n
    header = sweep(f"{tag} header", [(x, 0.0, Ht / 2 + 0.03) for x in np.linspace(-0.55, 0.55, 2)], 0.07, 0.06, RM, sf, side=(0, 0, 1))
    roll = cyl(f"{tag} roll", 0.05, 1.08, G, 14, sf, loc=(-0.54, 0.08, Ht / 2 + 0.1), axis="X")     # the roll sits in front
    hinges = []; par = sf; z0 = Ht / 2
    for i in range(n):
        hg = empty(f"{tag} slat hinge {i}", (0, 0, z0) if i == 0 else (0, 0, -sh), par)
        w_ = heater_w((i + 0.5) / n)
        h1_slat(f"{tag} slat {i}", w_, sh - 0.01, 0.06, HM, hg).location = (0, -0.06, -sh / 2)
        cyl(f"{tag} knuckle {i}", 0.012, w_ * 0.9, RM, 8, hg, loc=(-w_ * 0.45, -0.03, 0), axis="X")
        hinges.append(hg); par = hg
    grips = grip_mounts(tag, sf, HOLD, lambda x, z: -0.06 * (2 * x) ** 2 * 0 - 0.06 + 0.06 * (1 - (2 * x) ** 2) - 0.016)
    for o in grips:
        key(o, 1, sc=0.0001); key(o, 4, sc=0.0001); key(o, 6, sc=1.0)
    key(header, 1, sc=0.0001); key(header, 4, sc=0.0001); key(header, 6, sc=1.0)
    key(roll, 1, sc=0.0001); key(roll, 4, sc=0.0001); key(roll, 6, sc=1.0); key(roll, 14, sc=1.0); key(roll, 16, sc=0.0001)
    for i, hg in enumerate(hinges):                      # unroll: each slat is rolled up (folded 90 back) until its turn
        f_ = 6 + i
        key(hg, 1, rot=(R(90), 0, 0), sc=0.0001); key(hg, f_ - 1, rot=(R(90), 0, 0), sc=0.0001); key(hg, f_, rot=(R(90), 0, 0), sc=1.0)
        key(hg, f_ + 2, rot=(R(-4), 0, 0)); key(hg, f_ + 4, rot=(0, 0, 0))
    imp_l = Vector((0.08, 0.0, 0.15))
    for i, hg in enumerate(hinges):                      # the hit: a backward swing ripples down the chain
        d = max(0, i - 3)
        key(hg, F_HIT + d, rot=(0, 0, 0)); key(hg, F_HIT + d + 2, rot=(R(-7 if i >= 3 else -2), 0, 0)); key(hg, F_HIT + d + 5, rot=(R(3), 0, 0))
        key(hg, F_HIT + d + 8, rot=(0, 0, 0))
    fade_out([hinges[0], header] + grips)
    return sf.matrix_world @ imp_l, 31


PUSH = dict(arm_r=(95, 0, 0), fore_r=(0, 0, 0), arm_l=(30, 0, -10), fore_l=(30, 0, 0), leg_l=(22, 0, 0), shin_l=(-18, 0, 0), leg_r=(-14, 0, 0), body=(-6, 0, 0))
PHOLD = dict(PUSH, arm_r=(88, 0, 4), fore_r=(10, 0, 0))


def push_keys(rig, bx):
    pose_keys(rig, bx, [(1, {}), (4, PUSH), (12, PHOLD), (30, PHOLD), (33, dict(PHOLD, body=(2, 0, 0))), (40, PHOLD), (56, {})])


def ring_pixels(tag, rig, targets, f0=3):
    scene.frame_set(f0 + 1); bpy.context.view_layer.update(); rw = rig["ring_pt"].matrix_world.translation.copy()
    for k, tgt in enumerate(targets):
        px = link(bpy.data.objects.new(f"{tag} push pixel", pixel_mesh(CM["pix"])))
        key(px, 1, loc=rw, sc=0.0001); key(px, f0, loc=rw, sc=0.0001); key(px, f0 + 1, loc=rw, sc=1.0); key(px, f0 + 4, loc=tgt, sc=0.8); key(px, f0 + 5, loc=tgt, sc=0.0001)


def build_H3b1(tag, rig, bx):
    """Drawbridge dome: the ring hand pushes, the ground line glows 1.6 blocks ahead, and nine curved ribs lying flat
    on the ground swing up on hinges at the line (each arching over toward you like a quarter dome), with H1 panels
    between; the hit bends the struck ribs back and they spring home. 2.4 x 2.0."""
    push_keys(rig, bx)
    wall = empty(f"{tag} wall", (bx, 1.6, 0))
    MM = strip("h1", f"{tag} membrane", alpha=0.8, emit=1.2)
    Rw = 1.7; arc = 1.4; Ht = 2.0; nr = 9
    angs = np.linspace(-arc / 2, arc / 2, nr)
    def base(a):
        return Vector((Rw * math.sin(a), Rw * math.cos(a) - Rw, 0))
    def prof(h):                                         # quarter-dome profile: leans back more and more with height
        return -0.55 * (h / Ht) ** 2
    ribs = []
    for k, a in enumerate(angs):
        hg = empty(f"{tag} rib hinge {k}", tuple(base(a)), wall); hg.rotation_euler = (0, 0, -a)
        pts = [(0, prof(h), h) for h in np.linspace(0, Ht, 9)]
        sweep(f"{tag} rib {k}", pts, 0.05, 0.05, RM if k in (0, nr - 1) else G, hg, side=(1, 0, 0))
        ribs.append((hg, a, k))
    panels = []
    for k in range(nr - 1):
        for j in range(4):
            h0, h1 = j * Ht / 4, (j + 1) * Ht / 4
            def Pp(a, h):
                b = base(a); n_ = Vector((math.sin(a), math.cos(a), 0))
                return b + n_ * prof(h) + Vector((0, 0, h))
            a0, a1 = angs[k], angs[k + 1]
            vs = [Pp(a0, h0), Pp(a1, h0), Pp(a1, h1), Pp(a0, h1)]; vs2 = [v + Vector((0, -0.015, 0)) for v in vs]
            panels.append(mesh_obj(f"{tag} panel {k} {j}", [tuple(v) for v in vs + vs2], [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], MM, wall, uvt=0.4))
    gl = sweep(f"{tag} ground line", [tuple(base(a) + Vector((0, 0, 0.005))) for a in np.linspace(-arc / 2, arc / 2, 16)], 0.12, 0.01, CM["pix"], wall, side=(0, 0, 1))
    key(gl, 1, sc=(0.0001, 1, 1)); key(gl, 5, sc=(0.0001, 1, 1)); key(gl, 7, sc=(1, 1, 1)); key(gl, 14, sc=(1, 1, 1)); key(gl, 16, sc=(1, 1, 0.0001))
    for hg, a, k in ribs:                                # flat on the ground pointing away, then swing up, centre first
        f_ = 6 + int(abs(k - nr // 2))
        key(hg, 1, rot=(R(-88), 0, -a), sc=0.0001); key(hg, f_ - 1, rot=(R(-88), 0, -a), sc=0.0001); key(hg, f_, rot=(R(-88), 0, -a), sc=1.0)
        key(hg, f_ + 3, rot=(R(4), 0, -a)); key(hg, f_ + 5, rot=(0, 0, -a))
    form_by(panels, 11, 15, lambda p: p.z + abs(p.x - bx) * 0.3, None, None, tag)
    ring_pixels(tag, rig, [Vector((bx, 1.6, 0)) + base(angs[0] + (angs[-1] - angs[0]) * k / 9) for k in range(10)])
    imp_l = Vector((0.15, 0.0, 1.2))
    for hg, a, k in ribs:
        d = abs(base(a).x - imp_l.x)
        if d < 0.5:
            key(hg, F_HIT, rot=(0, 0, -a)); key(hg, F_HIT + 1, rot=(R(5 * (1 - d / 0.5)), 0, -a)); key(hg, F_HIT + 5, rot=(R(-2 * (1 - d / 0.5)), 0, -a)); key(hg, F_HIT + 8, rot=(0, 0, -a))
    return Vector((bx, 1.6, 0)) + base(0.09) + Vector((0, prof(1.2), 1.2)), 31


def build_H3b2(tag, rig, bx):
    """Hex column wall: the ring hand pushes and a curved band of H1 hex columns extrudes up out of the ground line 1.6
    blocks ahead, each to its own height, leaning in at the top like a dome (a basalt-column wall); the hit sinks the
    struck columns and they pop back up. 2.4 x 2.0."""
    push_keys(rig, bx)
    wall = empty(f"{tag} wall", (bx, 1.6, 0))
    MM = strip("h1", f"{tag} columns", alpha=0.85, emit=1.2)
    Rw = 1.7; arc = 1.45; Ht = 2.0
    cols = []
    rcol = 0.085
    k = 0
    for row in range(2):
        nc = 15 - row
        for i in range(nc):
            a = -arc / 2 + (i + 0.5 * row + 0.25) * arc / 15
            r_ = Rw - row * 0.13
            b = Vector((r_ * math.sin(a), r_ * math.cos(a) - Rw, 0))
            h = Ht * (0.86 + 0.14 * math.cos(3 * a + row)) - row * 0.18
            piv = empty(f"{tag} column pivot {k}", tuple(b), wall); piv.rotation_euler = (R(-12), 0, -a)
            c = cyl(f"{tag} column {k}", rcol, h, MM, 6, piv)
            cyl(f"{tag} column cap {k}", rcol * 1.02, 0.03, RM, 6, piv, loc=(0, 0, h - 0.03))
            cols.append((piv, b, h, k)); k += 1
    gl = sweep(f"{tag} ground line", [(Rw * math.sin(a), Rw * math.cos(a) - Rw, 0.005) for a in np.linspace(-arc / 2, arc / 2, 16)], 0.2, 0.01, CM["pix"], wall, side=(0, 0, 1))
    key(gl, 1, sc=(0.0001, 1, 1)); key(gl, 5, sc=(0.0001, 1, 1)); key(gl, 7, sc=(1, 1, 1)); key(gl, 14, sc=(1, 1, 1)); key(gl, 16, sc=(1, 1, 0.0001))
    for piv, b, h, k in cols:                            # extrude up from the ground, from the middle out, overshoot
        f_ = 6 + int(abs(b.x) / 0.25) + (k % 2)
        key(piv, 1, sc=(1, 1, 0.0001)); key(piv, f_, sc=(1, 1, 0.0001)); key(piv, f_ + 3, sc=(1, 1, 1.08)); key(piv, f_ + 5, sc=(1, 1, 1.0))
    ring_pixels(tag, rig, [Vector((bx, 1.6, 0)) + Vector((Rw * math.sin(a), Rw * math.cos(a) - Rw, 0)) for a in np.linspace(-arc / 2, arc / 2, 10)])
    imp_l = Vector((0.15, 0.0, 1.25))
    for piv, b, h, k in cols:
        d = abs(b.x - imp_l.x)
        if d < 0.45:
            s = 1 - 0.25 * (1 - d / 0.45)
            key(piv, F_HIT, sc=(1, 1, 1)); key(piv, F_HIT + 2, sc=(1, 1, s)); key(piv, F_HIT + 7 + int(d * 10), sc=(1, 1, 1.04)); key(piv, F_HIT + 9 + int(d * 10), sc=(1, 1, 1))
    return Vector((bx + 0.15, 1.6 + 0.0, 1.25)), 31


def build_H3b3(tag, rig, bx):
    """Folding-screen dome: the ring hand pushes, a post plants in the ground 1.6 blocks ahead, and three curved
    H1 panels slide out of it sideways (centre, then left and right), each leaning in at the top like part of a dome;
    the hit shoves the panels sideways and a dent ring spreads. 2.4 x 2.0."""
    push_keys(rig, bx)
    wall = empty(f"{tag} wall", (bx, 1.6, 0))
    MM = strip("h1", f"{tag} membrane", alpha=0.8, emit=1.2)
    Rw = 1.7; Ht = 2.0
    post = cyl(f"{tag} post", 0.05, Ht + 0.12, RM, 10, wall, loc=(0, 0.05, 0))
    spike = cyl(f"{tag} post spike", 0.05, 0.25, RM, 10, wall, loc=(0, 0.05, -0.2), r2=0.005)
    def surf(a, h):
        lean = 0.3 * (h / Ht) ** 2
        r_ = Rw - lean
        return Vector((r_ * math.sin(a), r_ * math.cos(a) - Rw, h))
    panels = []
    for k, (a0, a1) in enumerate(((-0.24, 0.24), (-0.72, -0.2), (0.2, 0.72))):
        sl = empty(f"{tag} slider {k}", (0, 0, 0), wall)
        vs, fs = [], []
        na, nh = 7, 6
        for i in range(nh):
            for j in range(na):
                vs.append(tuple(surf(a0 + (a1 - a0) * j / (na - 1), Ht * i / (nh - 1)) + Vector((0, -0.03 * k, 0))))
        off = len(vs)
        vs += [(v[0], v[1] - 0.015, v[2]) for v in vs]
        for i in range(nh - 1):
            for j in range(na - 1):
                a_ = i * na + j
                fs.append((a_, a_ + 1, a_ + na + 1, a_ + na)); fs.append((off + a_ + na, off + a_ + na + 1, off + a_ + 1, off + a_))
        mesh_obj(f"{tag} screen {k}", vs, fs, MM, sl, uvt=0.4)
        for e in (a0, a1):
            sweep(f"{tag} screen edge {k} {e:.2f}", [tuple(surf(e, h) + Vector((0, -0.03 * k, 0))) for h in np.linspace(0, Ht, 7)], 0.04, 0.04, RM, sl, side=(1, 0, 0))
        sweep(f"{tag} screen top {k}", [tuple(surf(a, Ht) + Vector((0, -0.03 * k, 0))) for a in np.linspace(a0, a1, 7)], 0.04, 0.04, RM, sl, side=(0, 0, 1))
        panels.append((sl, k, (a0 + a1) / 2))
    key(post, 1, sc=0.0001, loc=(0, 0.05, 1.0)); key(post, 5, sc=0.0001, loc=(0, 0.05, 1.0)); key(post, 6, sc=1.0, loc=(0, 0.05, 0.6)); key(post, 8, loc=(0, 0.05, 0.0), sc=1.0)
    key(spike, 1, sc=0.0001); key(spike, 7, sc=0.0001); key(spike, 8, sc=1.0)
    for sl, k, am in panels:                             # each panel slides out of the post, rotating round the arc
        f_ = 8 if k == 0 else 10
        key(sl, 1, rot=(0, 0, 0), sc=0.0001); key(sl, f_, rot=(0, 0, am), sc=(0.0001, 1, 1)); key(sl, f_ + 1, rot=(0, 0, am * 0.9), sc=(0.25, 1, 1))
        key(sl, f_ + 4, rot=(0, 0, -0.05 * np.sign(am)), sc=(1.0, 1, 1)); key(sl, f_ + 6, rot=(0, 0, 0), sc=(1, 1, 1))
    ring_pixels(tag, rig, [Vector((bx, 1.65, 0.05 + 0.2 * k)) for k in range(10)])
    imp_l = surf(0.09, 1.25)
    for sl, k, am in panels:
        key(sl, F_HIT, rot=(0, 0, 0)); key(sl, F_HIT + 2, rot=(0, 0, -0.03 + 0.01 * k)); key(sl, F_HIT + 6, rot=(0, 0, 0.012)); key(sl, F_HIT + 9, rot=(0, 0, 0))
    dent = torus(f"{tag} dent ring", 0.08, 0.012, CM["pix"], loc=tuple(imp_l + Vector((0, -0.04, 0))), parent=wall, axis="Y")
    key(dent, 1, sc=0.0001); key(dent, F_HIT, sc=0.0001); key(dent, F_HIT + 1, sc=1.0); key(dent, F_HIT + 6, sc=5.0); key(dent, F_HIT + 7, sc=0.0001)
    return Vector((bx, 1.6, 0)) + imp_l, 31


SHIELDS = {
 "H2a1": dict(name="curved brick: arch top, laid brick by brick", src="H2a", build=build_H2a1, end=60,
              facts="curved BR1 tower 1.0 x 1.9 with a round arch top and keystone; each brick flies in from the ring 5-13; held from behind on two grip bars; hit knocks near bricks back, they settle",
              lines=["H2a sibling: curved BR1 brick tower, 1.0 x 1.9, with a round", "arch top and keystone; each brick flies in from the ring and",
                     "lands, course by course 5-13 (a mason laying it); held on", "two grip bars. The hit knocks the near bricks back; they settle."]),
 "H2a2": dict(name="curved brick: barrel stack bond, mortar flash", src="H2a", build=build_H2a2, end=60,
              facts="BR1 bricks in stack bond on a barrel surface (curved both ways), rim frame; columns rise from the ground 5-13; hit flashes the bricks outward from the impact",
              lines=["H2a sibling: BR1 bricks in stack-bond columns on a barrel", "surface (curved side to side and top to bottom), rim frame;",
                     "the columns rise up out of the ground 5-13; held on two", "grip bars. The hit flashes the bricks outward, band by band."]),
 "H2a3": dict(name="curved brick: herringbone folding screen", src="H2a", build=build_H2a3, end=60,
              facts="five flat facets angled into a curve, faced with BR1 herringbone; facets unfold from the centre 6-16; the hit punches one brick out, it flies back and re-seats",
              lines=["H2a sibling: five flat facets set at angles to make the", "curve, each faced with BR1 bricks in herringbone; the facets",
                     "unfold out from the centre like a folding screen 6-16.", "The hit punches one brick out; it flies back in and re-seats."]),
 "H2c1": dict(name="telescoping heater: sideways fan", src="H2c", build=build_H2c1, end=60,
              facts="7 upright H1 columns slide out sideways from the centre into a 1.0 x 1.7 heater (5-13); hit shivers the columns sideways in a wave",
              lines=["H2c sibling: seven upright H1 columns, stacked at the centre,", "telescope out sideways (left and right in turn) into the",
                     "heater outline 5-13 with an overshoot; held on two grip", "bars. The hit shivers the columns sideways in a wave."]),
 "H2c2": dict(name="telescoping heater: nested rings", src="H2c", build=build_H2c2, end=60,
              facts="5 nested heater-outline frames filled with H1 telescope forward and out from a boss (6-15) like a collapsible cup; hit pushes the rings back in depth order",
              lines=["H2c sibling: five heater-outline frames, each filled with H1,", "nest at a small boss and telescope out and back, biggest",
                     "last, like a collapsible cup (6-15); held on two grip bars.", "The hit pushes the rings back one after another."]),
 "H2c3": dict(name="telescoping heater: roller shutter", src="H2c", build=build_H2c3, end=60,
              facts="header bar over the grips, 9 thin hinged H1 slats unroll down into the heater outline 6-18; hit swings the hinged slats back in a ripple down the chain",
              lines=["H2c sibling: a header bar forms over the grips, then nine", "thin H1 slats unroll down from it, each hinged to the one",
                     "above, into the heater outline 6-18. The hit swings the", "hinged slats back in a ripple down the chain."]),
 "H3b1": dict(name="planted wall: drawbridge ribs", src="H3b", build=build_H3b1, end=60,
              facts="push; ground line 1.6 ahead; 9 curved ribs lying flat swing up on hinges at the line (6-15) arching over like a quarter dome, H1 panels fill; hit bends the struck ribs",
              lines=["H3b sibling: the ring hand pushes, a line glows 1.6 blocks", "ahead and nine curved ribs lying flat swing up on hinges",
                     "at it, arching over toward you like a quarter dome; H1", "panels fill 11-15. The hit bends the struck ribs back."]),
 "H3b2": dict(name="planted wall: hex columns", src="H3b", build=build_H3b2, end=60,
              facts="push; a curved band of 29 H1 hex columns extrudes up from the ground line 1.6 ahead (6-14), leaning in like a dome; hit sinks the struck columns, they pop back",
              lines=["H3b sibling: the ring hand pushes and a curved band of H1", "hex columns extrudes up out of the ground 1.6 blocks ahead,",
                     "each its own height, leaning in like a dome (6-14). The hit", "sinks the struck columns and they pop back up."]),
 "H3b3": dict(name="planted wall: sliding screens", src="H3b", build=build_H3b3, end=60,
              facts="push; a post plants 1.6 ahead (5-8), three curved H1 screens slide out of it sideways (8-16), leaning in like a dome; hit shoves the screens, dent ring",
              lines=["H3b sibling: the ring hand pushes, a post spikes into the", "ground 1.6 blocks ahead, and three curved H1 screens slide",
                     "out of it sideways, leaning in like a dome (8-16). The hit", "shoves the screens sideways and a dent ring spreads."]),
}


def build_shield_take(code, bi):
    T = SHIELDS[code]; bx = bi * BAY; tag = f"BS3 {code}"
    box(f"{tag} floor", (bx - 2.6, -3, -0.02), (bx + 2.6, 9, 0), FLOOR)
    M = player_mats(tag); M["ring"] = mat(f"{tag} ring face", (0.02, 0.85, 0.15), emit=1.6)
    rig = make_player(tag, (bx, 0, 0), M)
    imp, mf = T["build"](tag, rig, bx)
    incoming(tag, bx, imp)
    far = code.startswith("H3b")
    cam(f"Cam {code}", (bx + 3.4, 5.6 if far else 4.6, 2.1), (bx, 0.6 if far else 0.3, 1.1), 32)
    cam(f"Cam {code} back", (bx + 2.6, -3.6, 2.0), (bx, 0.6 if far else 0.3, 1.1), 32)
    board(tag, (bx, 3.0, 3.0), f"{code}  {T['name'].upper()}", T["lines"])
    return mf


ORDER = list(BOWS) + list(SHIELDS)
dump = {"takes": {}}
for bi, code in enumerate(ORDER):
    if code in BOWS:
        dump["takes"][code] = {"solver_error_m": build_bow_take(code, bi)}
    else:
        build_shield_take(code, bi)
    print(code, "built", flush=True)
FRAME_END = max([BOWS[c]["end"] for c in BOWS] + [SHIELDS[c]["end"] for c in SHIELDS])


with open(os.path.join(FOLDER, "combat", "bows_shields3_poses.json"), "w") as fh:
    json.dump(dump, fh, indent=1)
cam("Cam all", ((len(ORDER) - 1) * BAY / 2, -52.0, 14.0), ((len(ORDER) - 1) * BAY / 2, 4.0, 0.6), 14)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam B1a1 close", 1, (0.3, 0.38, 0.5), 3.0


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
