# Pass 851: mech suits, MCb and MCc variations (rings/suits chat, 2026-10-15, range 800-899). Follows 843.
# J rated 843 MCb Rocket Juggernaut and MCc Breaker IMPROVE with no note: "3 new variations each", labelled, he picks.
# MAb, MAc and MCa were dropped; MAa got J's note ("Give this bot the hammer and make it for the villagers") and was
# changed in place in 843 (rev 2). Each new take keeps what made its parent itself and is built a different way:
#   MCb = R1 green cells, a villager pilot, rockets and jets; MCc = H1 hex, a zombie pilot, horns and a two-handed
#   construct war hammer (a solid 3D block, both fists solved onto the haft; the head lands face first).
# Same clock for all (20 ticks a second): 1-24 form, 24-30 board, 30-35 seal, 36-76 move, 76-96 attack,
#   96-126 finisher, 130 end.
#   MCb1 Hover Tank: no legs, a round hover skirt with flared flaps, a ram plow, two shoulder rocket pods. Unpacks out of
#       a construct cube. Glides an S-curve banking into the turns; a four-rocket salvo that arcs onto the ground;
#       a pack-boosted ram charge, plow first.
#   MCb2 Jump Jet: lean, digitigrade legs with calf jets, drum pauldrons, elbow-jet gauntlets. Unfolds joint by joint
#       like a folded toy. Moves in three jet hops; elbow-jet dash punches (right, left); boomerang rocket fists that
#       swing out wide, clash in front and loop back.
#   MCb3 Orbit Juggernaut: heavy body, floating limbs (orbiting cells instead of upper arms), a halo collar, a
#       four-nozzle cross pack. Spirals in from a vortex. Stomping walk; a drill fist that corkscrews out on a chain of
#       cells; meteor fists: both blast up out of sight and dive onto the ground ahead.
#   MCc1 Anvil Breaker: squat, bull horns, front tassets, an anvil hammer (flat face + horn). Built out from the planted
#       hammer. Crutch-walks, planting the hammer ahead and stepping up to it; a side swing through a hex construct
#       wall (J on 503: from the side when it hits a wall); a jump smash with a hex shockwave.
#   MCc2 Ram Breaker: tall and lean, curled ram horns, hex scale skirt, a long spiked maul carried on the shoulder.
#       Rises up out of the floor. Stalking walk; overhead from the shoulder, face first; throws the maul end over
#       end, it lands face first 4 m ahead, and it is called back to the hand.
#   MCc3 Earthshaker: widest, crown of horns, hanging hex chains, a huge two-faced block hammer. Gathers from shards
#       lying round it (a shatter in reverse). A charging run, hammer low; a double tap; the fissure: a one-knee slam
#       and hex pillars burst up in a line ahead.
# Cameras "Cam <take>" (front three-quarter), "Cam <take> close", "Cam row MCb", "Cam row MCc".
# Builds LanternLive\constructs\mech_suits3.blend.
SCENE_NAME = "Mech Suits 3"
OUT_REL = "constructs/mech_suits3.blend"
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
BAY = 18.0                                     # takes 18 m apart along X; the MCc row starts at x = 72
FLOOR = mat("M3 floor", (0.2, 0.22, 0.2), rough=0.9)
LBL = mat("M3 label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(851)
CM = cmats("M3", "green")
RM, W, GR, GL = CM["rim"], CM["glow"], CM["grip"], CM["glass"]
FRAME = mat("M3 dark frame", (0.02, 0.12, 0.05), emit=0.35, alpha=0.9, rough=0.25)      # inner skeleton, darker
SHOCK = mat("M3 shock glass", (0.06, 0.5, 0.15), emit=1.2, alpha=0.35, rough=0.1)
TEX = {k: strip_mat(f"M3 {k} texture", strip_image("green", k), 5, emit=1.2, alpha=0.92)
       for k in ("r1", "h1")}
ROBE = mat("M3 villager robe", (0.35, 0.22, 0.12), rough=0.9)
VSKIN = mat("M3 villager skin", (0.72, 0.52, 0.4), rough=0.8)
ZSKIN = mat("M3 zombie skin", (0.3, 0.5, 0.3), rough=0.8)
ZSHIRT = mat("M3 zombie shirt", (0.1, 0.45, 0.5), rough=0.8)
BROW = mat("M3 brow", (0.15, 0.1, 0.05))


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




# ------------------------------------------------------------------ shared for 851: jets, hammers and two-handed grips
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


def hq(d, n):
    """Hammer orientation: haft along d (hammer +Z, toward the head), striking face normal n (hammer +Y)."""
    d = Vector(d).normalized(); n = Vector(n); n = (n - d * n.dot(d)).normalized()
    return Matrix((n.cross(d), n, d)).transposed().to_quaternion()


def make_hammer(tag, torso, J, lo, hd, style, T):
    """A solid 3D construct hammer (bevelled blocks). Hammer space: origin between the hands, +Z along the haft to the
    head (centred at z = hd), +Y the striking face. Returns the hammer empty; J gets hammer, hammer_head, head_ext."""
    hm = empty(f"{tag} hammer", (0, 0.9, 0.5), torso); hm.rotation_mode = "QUATERNION"
    cyl(f"{tag} hammer haft", 0.075, hd + lo, FRAME, 12, hm, loc=(0, 0, -lo))
    plate(f"{tag} hammer pommel", (-0.13, -0.13, -lo - 0.2), (0.13, 0.13, -lo + 0.02), T, hm, 0.03)
    for k in range(3):
        torus(f"{tag} hammer grip wrap {k}", 0.088, 0.022, RM, loc=(0, 0, -lo + 0.35 + k * 0.4), parent=hm, n=16, k=6)
    hp = empty(f"{tag} hammer head pivot", (0, 0, hd), hm)
    if style == "anvil":                     # MCc1: a flat anvil face on +Y, a tapered horn on -Y
        plate(f"{tag} hammer head", (-0.34, -0.42, -0.32), (0.34, 0.42, 0.32), T, hp, 0.06)
        plate(f"{tag} hammer face", (-0.42, 0.42, -0.4), (0.42, 0.56, 0.4), T, hp, 0.04)
        box(f"{tag} hammer face glow", (-0.26, 0.56, -0.24), (0.26, 0.575, 0.24), W, hp)
        cyl(f"{tag} hammer horn", 0.24, -0.6, T, 10, hp, loc=(0, -0.42, 0.05), axis="Y", r2=0.03)
        for sz in (-1, 1):
            plate(f"{tag} hammer band {sz}", (-0.37, -0.3, sz * 0.2 - 0.05), (0.37, 0.3, sz * 0.2 + 0.05), RM, hp, 0.015)
        J["head_ext"] = (0.42, 0.58, 0.4)
    elif style == "maul":                    # MCc2: one face on +Y, a back spike on -Y, a long haft
        plate(f"{tag} hammer head", (-0.3, -0.38, -0.36), (0.3, 0.38, 0.36), T, hp, 0.06)
        plate(f"{tag} hammer face", (-0.34, 0.38, -0.4), (0.34, 0.5, 0.4), T, hp, 0.04)
        box(f"{tag} hammer face glow", (-0.2, 0.5, -0.24), (0.2, 0.515, 0.24), W, hp)
        cyl(f"{tag} hammer spike", 0.2, -0.7, RM, 6, hp, loc=(0, -0.38, 0), axis="Y", r2=0.0)
        cyl(f"{tag} hammer top spike", 0.1, 0.4, RM, 6, hp, loc=(0, 0, 0.36), r2=0.0)
        J["head_ext"] = (0.34, 0.52, 0.4)
    else:                                    # MCc3: a huge two-faced block
        plate(f"{tag} hammer head", (-0.5, -0.48, -0.42), (0.5, 0.48, 0.42), T, hp, 0.08)
        for sy in (-1, 1):
            lo_, hi_ = sorted((sy * 0.48, sy * 0.6))
            plate(f"{tag} hammer face {sy}", (-0.54, lo_, -0.46), (0.54, hi_, 0.46), T, hp, 0.05)
            lo_, hi_ = sorted((sy * 0.6, sy * 0.615))
            box(f"{tag} hammer face glow {sy}", (-0.3, lo_, -0.26), (0.3, hi_, 0.26), W, hp)
        for sx in (-1, 1):
            cyl(f"{tag} hammer hex cheek {sx}", 0.3, 0.06, RM, 6, hp, loc=(sx * 0.5 if sx > 0 else -0.56, 0, 0), axis="X")
        J["head_ext"] = (0.56, 0.62, 0.46)
    plate(f"{tag} hammer collar", (-0.16, -0.16, -J["head_ext"][2] - 0.16), (0.16, 0.16, -J["head_ext"][2] + 0.02), T, hp, 0.03)
    J.update(hammer=hm, hammer_head=hp, hd=hd, haft_lo=lo)
    return hm


def head_on_ground(J, xy, d, n):
    """Pivot for a hammer whose head rests on the ground at xy (world), haft along d, face normal n."""
    q = hq(d, n); ex = J["head_ext"]
    zs = [(q @ Vector((a * ex[0], b * ex[1], c * ex[2]))).z for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
    head = Vector((xy[0], xy[1], -min(zs) + 0.01))
    return head - q @ Vector((0, 0, J["hd"]))


_TW = {}


def tw(M, f):
    k = (M.tag, f)
    if k not in _TW:
        scene.frame_set(f); bpy.context.view_layer.update(); _TW[k] = M.J["torso"].matrix_world.copy()
    return _TW[k]


def impact(M, f, ahead, tilt=12, side=0.0, yaw=0.0, sR=0.15, sL=-0.3):
    """A world key: the head lands face first on the ground in front of the shoulders. `ahead` is a starting guess;
    drive_hammer moves it to the farthest distance both fists can still reach."""
    return (f, "I", (ahead, tilt, side, yaw), None, None, sR, sL)


def impact_pose(M, f, ahead, tilt, side, yaw):
    J = M.J; T_ = tw(M, f); Rz = Matrix.Rotation(R(yaw), 3, "Z") @ Matrix.Rotation(J["root"].rotation_euler.z, 3, "Z")
    t = R(tilt)
    d = Rz @ Vector((0, math.cos(t), -math.sin(t))); n = Rz @ Vector((0, -math.sin(t), -math.cos(t)))
    sh = T_ @ Vector((0, 0, J["arm_geo"][1])); sh.z = 0
    return head_on_ground(J, sh + Rz @ Vector((side, ahead, 0)), d, n), d, n


class Grip:
    """Two-handed grip: both fists solved onto the haft every frame (damped least squares on 4 angles)."""

    def __init__(s, J):
        s.shx, s.shz, s.up, s.fist = J["arm_geo"]

    def fk(s, sx, x):
        Rs = Euler((R(x[0]), R(x[1]), R(x[2])), "XYZ").to_matrix(); Re = Euler((R(x[3]), 0, 0), "XYZ").to_matrix()
        return Vector((sx * s.shx, 0, s.shz)) + Rs @ (Vector((0, 0, -s.up)) + Re @ s.fist)

    def ik(s, sx, target, prev, retry=False):
        x = np.array(prev, float); t = np.array(target, float)
        lo = np.array([-120, -70, -100, 5]); hi = np.array([200, 70, 100, 150])
        for _ in range(200):
            f0 = np.array(s.fk(sx, x)) - t
            if np.linalg.norm(f0) < 1e-3:
                break
            Jm = np.zeros((3, 4))
            for i in range(4):
                dx = x.copy(); dx[i] += 0.2
                Jm[:, i] = (np.array(s.fk(sx, dx)) - t - f0) / 0.2
            x = np.clip(x - np.linalg.solve(Jm.T @ Jm + 1e-5 * np.eye(4), Jm.T @ f0), lo, hi)
        err = float(np.linalg.norm(np.array(s.fk(sx, x)) - t))
        if err > 0.02 and not retry:
            for seed in ([60, 0, sx * 30, 60], [100, 0, -sx * 30, 40], [30, sx * 40, 0, 90], [140, 0, 0, 30]):
                y_, e_ = s.ik(sx, target, seed, True)
                if e_ < err - 0.01:
                    x, err = y_, e_
        return x, err


def drive_hammer(M, keys, free=()):
    """keys: (frame, space, pivot, haft dir, face normal, right grip s, left grip s). space "T" = torso space, "W" =
    world (converted with that frame's torso, so a planted head stays put), "I" = an impact (see impact()).
    Every frame the hammer is keyed and both arms are solved onto the haft, except in `free` frame ranges (a thrown
    hammer). Grips slide along the haft to where each shoulder reaches comfortably; if a fist still can't reach, the
    hammer is nudged toward it (never in impact holds, whose distance is chosen to be reachable)."""
    J = M.J; hm = J["hammer"]; G = Grip(J); hd = J["hd"]; reach = G.up + G.fist.length
    keys = sorted(keys, key=lambda k: k[0])
    s_lo = -J.get("haft_lo", 1.0) + 0.12; s_hi = hd - J["head_ext"][2] - 0.25

    def grips(p, q, sR0, sL0, prev_s):
        ss = np.linspace(s_lo, s_hi, 48); best = None
        for sR in ss:
            for sL in ss:
                if sR - sL < 0.28 or sR - sL > 0.75:
                    continue
                c = 0.0
                for sx, s_ in ((1, sR), (-1, sL)):
                    dist = (p + q @ Vector((0, 0, s_)) - Vector((sx * G.shx, 0, G.shz))).length
                    c += max(0.0, dist - 0.92 * reach) ** 2 * 50 + max(0.0, 0.55 * reach - dist) ** 2 * 50
                c += 0.15 * ((sR - sR0) ** 2 + (sL - sL0) ** 2)
                if prev_s is not None:
                    c += 2.0 * ((sR - prev_s[0]) ** 2 + (sL - prev_s[1]) ** 2)
                if best is None or c < best[0]:
                    best = (c, sR, sL)
        return best[1], best[2]

    def solve(p, q, sR, sL, prev, nudge=True):
        out = {}
        for it in range(4 if nudge else 1):
            res = Vector(); err = 0.0
            for sx, s_ in ((1, sR), (-1, sL)):
                tgt = p + q @ Vector((0, 0, s_))
                x, e = G.ik(sx, tgt, prev[sx]); out[sx] = x; err = max(err, e)
                res += (G.fk(sx, x) - tgt) / 2
            if err < 0.03 or not nudge:
                break
            p = p + res
        return p, out, err

    # impacts: the farthest distance both fists reach
    fixed = []; last_i = None
    for k in keys:
        if k[1] != "I":
            fixed.append(k); last_i = None; continue
        f, _, (ahead, tilt, side, yaw), _, _, sR0, sL0 = k
        if last_i is not None and last_i[0] == k[2]:          # a hold: the head stays exactly where it landed
            fixed.append((f,) + last_i[1][1:]); continue
        T_ = tw(M, f); Ti = T_.inverted(); qi = T_.to_3x3().normalized().to_quaternion().inverted()
        best = None
        for tl in (tilt, tilt + 6, tilt + 12, tilt + 18, tilt + 24):    # steeper only when the arms can't reach
            for a_ in np.linspace(3.2, 1.0, 23):
                pw, d, n = impact_pose(M, f, a_ + 0.15, tl, side, yaw)
                p = Ti @ pw; q = qi @ hq(d, n)
                sR, sL = grips(p, q, sR0, sL0, None)
                _, _, err = solve(p, q, sR, sL, {1: [60, 0, 20, 40], -1: [60, 0, -20, 40]}, False)
                if best is None or err < best[0] - 1e-3:
                    best = (err, a_ + 0.15, sR, sL, tl)
                if err < 0.02:
                    break
            if best[0] < 0.02:
                break
        tilt = best[4]
        a_ = max(1.0, best[1] - 0.15)                            # a margin: the torso still settles during a hold
        pw, d, n = impact_pose(M, f, a_, tilt, side, yaw)
        fixed.append((f, "W", pw, d, n, best[2], best[3])); last_i = (k[2], fixed[-1])
        print(M.tag, "impact at", f, "ahead %.2f m tilt %d err %.2f" % (a_, tilt, best[0]), flush=True)
    keys = fixed

    def conv(k, f):
        _, sp, p, d, n, sR, sL = k
        q = hq(d, n)
        if sp == "T":
            return Vector(p), q, sR, sL
        T_ = tw(M, f)
        qi = T_.to_3x3().normalized().to_quaternion().inverted()
        return T_.inverted() @ Vector(p), qi @ q, sR, sL

    holds = set()
    for a, b in zip(keys, keys[1:]):
        if a[1] == "W" and b[1] == "W" and (Vector(a[2]) - Vector(b[2])).length < 1e-4:
            holds.update(range(a[0], b[0] + 1))
    prev = {1: [40, 0, 30, 60], -1: [40, 0, -30, 60]}; worst = (0.0, 0); qp = None; prev_s = None
    for f in range(1, FRAME_END + 1):
        k0 = keys[0]; k1 = keys[-1]
        for a, b in zip(keys, keys[1:]):
            if a[0] <= f <= b[0]:
                k0, k1 = a, b; break
        p0, q0, r0, l0 = conv(k0, f); p1, q1, r1, l1 = conv(k1, f)
        t = 0.0 if k1[0] == k0[0] else smooth((f - k0[0]) / (k1[0] - k0[0]))
        t = 0.0 if f < k0[0] else 1.0 if f > k1[0] else t
        if q0.dot(q1) < 0:
            q1 = -q1
        p_ = p0.lerp(p1, t); q_ = q0.slerp(q1, t); sR = r0 + (r1 - r0) * t; sL = l0 + (l1 - l0) * t
        if qp is not None and qp.dot(q_) < 0:
            q_ = -q_
        qp = q_
        if not any(a <= f <= b for a, b in free):
            sR, sL = grips(p_, q_, sR, sL, prev_s); prev_s = (sR, sL)
            p_, xs, err = solve(p_, q_, sR, sL, prev, f not in holds)
            for sx in (1, -1):
                prev[sx] = list(xs[sx])
                for sh, el, sx_ in J["arms"]:
                    if sx_ == sx:
                        x = xs[sx]; key(sh, f, rot=(R(x[0]), R(x[1]), R(x[2]))); key(el, f, rot=(R(x[3]), 0, 0))
            if f > 14 and err > worst[0]:
                worst = (err, f)
        else:
            prev_s = None
        hm.location = p_; hm.rotation_quaternion = q_
        hm.keyframe_insert("location", frame=f); hm.keyframe_insert("rotation_quaternion", frame=f)
    print(M.tag, "grip worst miss %.3f m at frame %d" % worst, flush=True)


def head_world(M, f):
    scene.frame_set(f); bpy.context.view_layer.update()
    return M.J["hammer_head"].matrix_world.translation.copy()


def hex_ring(tag, c, f, r0, grow, life=8):
    t = torus(tag, r0, 0.05, RM, loc=c, n=6, k=6); t.rotation_euler = (0, 0, R(30))
    key(t, 1, sc=0.0001); key(t, f - 1, sc=0.0001); key(t, f, sc=(1, 1, 1)); key(t, f + life, sc=(grow, grow, 1))
    key(t, f + life + 1, sc=0.0001)
    return t


def pilot_seat_box(tag, torso, T, w=1.0, back=-0.6, front=0.55, roof=1.4):
    """Cockpit shell common to the 851 mechs: back, sides, floor (the pilot sits at seat (0, -0.05, -0.62))."""
    plate(f"{tag} chest back", (-w, back, 0.0), (w, back + 0.3, roof), T, torso)
    for sx in (-1, 1):
        plate(f"{tag} chest side {sx}", (sx * w - 0.15, back, 0.0), (sx * w + 0.15, front, roof - 0.05), T, torso)
    plate(f"{tag} chest floor", (-w, back, -0.05), (w, front, 0.1), T, torso)


# ================================================================== MCb1 Hover Tank (R1, villager)
def build_MCb1(tag, T):
    J = {"hz": 1.2}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.2), hips); J["torso"] = torso
    # no legs: a round hover skirt with eight flared flaps, a ram plow in front, a glow ring and a downward jet
    cyl(f"{tag} skirt deck", 1.15, 0.35, T, 24, hips, loc=(0, 0, -0.75), r2=0.95)
    cyl(f"{tag} skirt hub", 0.8, 0.55, T, 20, hips, loc=(0, 0, -0.4), r2=0.65)
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        pv = empty(f"{tag} flap pivot {i}", (1.02 * math.cos(a), 1.02 * math.sin(a), -0.42), hips)
        pv.rotation_euler = (R(22), 0, a - math.pi / 2)
        plate(f"{tag} skirt flap {i}", (-0.3, 0.0, -0.42), (0.3, 0.1, 0.0), T if i % 2 else RM, pv, 0.02)
    torus(f"{tag} skirt glow", 0.95, 0.04, W, loc=(0, 0, -0.8), parent=hips)
    J["pads"] = [cyl(f"{tag} skirt jet", 0.85, -0.7, W, 20, hips, loc=(0, 0, -0.82), r2=0.15)]
    plate(f"{tag} ram plow", (-0.95, 1.05, -0.95), (0.95, 1.3, -0.2), T, hips, 0.05)
    plate(f"{tag} plow edge", (-0.97, 1.28, -0.98), (0.97, 1.36, -0.85), RM, hips, 0.02)
    pilot_seat_box(tag, torso, T, 1.05)
    plate(f"{tag} roof", (-1.15, -0.72, 1.38), (1.15, 0.65, 1.58), T, torso, 0.05)
    plate(f"{tag} chin bar", (-0.8, 0.45, -0.15), (0.8, 0.7, 0.12), RM, torso, 0.03)
    hatch = empty(f"{tag} canopy hinge", (0, 0.55, 1.42), torso)
    box(f"{tag} canopy", (-0.88, 0.0, -1.38), (0.88, 0.06, 0.0), GL, hatch)
    box(f"{tag} canopy slat", (-0.9, 0.0, -0.5), (0.9, 0.1, -0.42), RM, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    # shoulder rocket pods, 2 x 2 tubes each, aimed forward
    pods = {}
    for sx in (-1, 1):
        pod = empty(f"{tag} pod {sx}", (sx * 0.72, -0.1, 1.58), torso)
        plate(f"{tag} pod body {sx}", (-0.36, -0.45, 0.0), (0.36, 0.45, 0.5), T, pod, 0.05)
        plate(f"{tag} pod rail {sx}", (sx * 0.36 - 0.03, -0.45, 0.05), (sx * 0.36 + 0.03, 0.45, 0.45), RM, pod, 0.01)
        mz = []
        for i, (xx, zz) in enumerate(((-0.15, 0.13), (0.15, 0.13), (-0.15, 0.37), (0.15, 0.37))):
            torus(f"{tag} pod muzzle {sx} {i}", 0.09, 0.025, RM, loc=(xx, 0.46, zz), parent=pod, axis="Y", n=12, k=6)
            mz.append(empty(f"{tag} muzzle {sx} {i}", (xx, 0.5, zz), pod))
        pods[sx] = (pod, mz)
    pack = empty(f"{tag} booster pack", (0, -0.78, 0.75), torso)
    plate(f"{tag} pack body", (-0.6, -0.3, -0.55), (0.6, 0.15, 0.6), T, pack, 0.05)
    jets = []
    for sx in (-1, 1):
        cyl(f"{tag} pack nozzle {sx}", 0.2, 0.3, FRAME, 12, pack, loc=(sx * 0.32, -0.3, -0.1), axis="Y", r2=0.26).rotation_euler = (0, 0, R(180))
        jets.append(jet(f"{tag} pack jet {sx}", 0.22, 1.1, pack, (sx * 0.32, -0.6, -0.1), (R(90), 0, 0)))
    arms = []
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.38, 0, 1.0), torso)
        plate(f"{tag} pauldron {sx}", (-0.32, -0.42, -0.2), (0.32, 0.42, 0.3), T, sh, 0.05)
        plate(f"{tag} upper arm {sx}", (-0.18, -0.18, -0.7), (0.18, 0.18, -0.1), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.72), sh)
        plate(f"{tag} gauntlet {sx}", (-0.32, -0.32, -0.6), (0.32, 0.32, 0.0), T, el, 0.05)
        torus(f"{tag} gauntlet ring {sx}", 0.31, 0.03, RM, loc=(0, 0, -0.55), parent=el)
        plate(f"{tag} fist {sx}", (-0.3, -0.3, -1.05), (0.3, 0.3, -0.6), T, el, 0.06)
        for k in range(4):
            box(f"{tag} knuckle {sx} {k}", (-0.28 + k * 0.145, 0.26, -1.03), (-0.17 + k * 0.145, 0.34, -0.82), RM, el)
        arms.append((sh, el, sx))
    J.update(legs=[], arms=arms, hands={}, pods=pods, jets=jets)
    return J


def anim_MCb1(M):
    J = M.J; hz = J["hz"]; rt = J["root"]; bx = M.bx; lift = 0.45
    M.hatch()
    for sx in (-1, 1):
        M.arm(1, sx, 0, 15, sx * 6)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    sk = J["pads"][0]
    for f, l in ((1, 0), (34, 0), (37, 1.0), (96, 1.0), (100, 1.6), (106, 1.6), (110, 1.0)):
        flare(sk, f, l)
    for o in J["jets"]:
        for f, l in ((1, 0), (97, 0), (99, 1.4), (106, 1.4), (108, 0)):
            flare(o, f, l)
    # 36-76: lifts on the skirt and glides an S-curve, yawing into its heading and banking into each turn
    M.hips(36, hz); M.hips(40, hz + lift)
    for f in range(40, 75, 3):
        u = (f - 40) / 34; dx = 0.9 * math.sin(2 * math.pi * u); y = 3.6 * u
        vx = 0.9 * 2 * math.pi * math.cos(2 * math.pi * u); vy = 3.6
        yaw = math.atan2(-vx, vy)
        key(rt, f, loc=(bx + dx, y, 0), rot=(0, 0, yaw))
        M.hips(f, hz + lift + 0.05 * math.sin(f * 0.6), 6, -10 * math.cos(2 * math.pi * u))
    key(rt, 76, loc=(bx, 3.6, 0), rot=(0, 0, 0))
    for sx in (-1, 1):
        M.arm(44, sx, -20, 30, sx * 15); M.arm(72, sx, -20, 30, sx * 15); M.arm(76, sx, 10, 40, sx * 6)
    M.hips(76, hz + lift, 0)
    y = 3.6
    # 76-96: rocket salvo: the pods tip up, four rockets fire one per two ticks and arc onto the ground ahead
    for sx in (-1, 1):
        pod = J["pods"][sx][0]
        key(pod, 1, rot=(0, 0, 0)); key(pod, 76, rot=(0, 0, 0)); key(pod, 78, rot=(R(18), 0, 0)); key(pod, 89, rot=(R(18), 0, 0)); key(pod, 93, rot=(0, 0, 0))
    for k, f in enumerate((79, 81, 83, 85)):
        M.torso(f, -5); M.torso(f + 1, 0)
    M.hips(96, hz + lift)
    targets = [(-1.3, 5.6), (1.2, 5.2), (-0.4, 6.4), (0.6, 6.0)]
    rocket_mesh = None
    for k, (f, sx, i) in enumerate(((79, 1, 0), (81, -1, 1), (83, 1, 3), (85, -1, 2))):
        scene.frame_set(f); bpy.context.view_layer.update()
        p0 = J["pods"][sx][1][i].matrix_world.translation.copy()
        p1 = Vector((bx + targets[k][0], y + targets[k][1], 0.1))
        rk = empty(f"{M.tag} rocket {k}"); rk.rotation_mode = "QUATERNION"
        cyl(f"{M.tag} rocket body {k}", 0.08, 0.32, T_R1, 8, rk, loc=(0, 0, -0.16), r2=0.08)
        cyl(f"{M.tag} rocket nose {k}", 0.08, 0.14, RM, 8, rk, loc=(0, 0, 0.16), r2=0.0)
        fl = cyl(f"{M.tag} rocket flame {k}", 0.07, -0.45, W, 8, rk, loc=(0, 0, -0.16), r2=0.0)
        last = None
        for j in range(0, 7):
            u = j / 6; p = p0.lerp(p1, u) + Vector((0, 0, 1.4 * 4 * u * (1 - u)))
            dv = (p1 - p0) + Vector((0, 0, 1.4 * 4 * (1 - 2 * u)))
            q = Vector((0, 0, 1)).rotation_difference(dv.normalized())
            if last is not None and last.dot(q) < 0:
                q = -q
            last = q
            rk.location = p; rk.rotation_quaternion = q
            rk.keyframe_insert("location", frame=f + j); rk.keyframe_insert("rotation_quaternion", frame=f + j)
        key(rk, 1, sc=0.0001); key(rk, f - 1, sc=0.0001); key(rk, f, sc=1.0); key(rk, f + 6, sc=1.0); key(rk, f + 7, sc=0.0001)
        ring_fx(f"{M.tag} rocket ring {k}", (p1.x, p1.y, 0.04), f + 6, 0.3, 4.0, 7, th=0.035)
        pf = ball(f"{M.tag} rocket burst {k}", 0.5, SHOCK, loc=(p1.x, p1.y, 0.1), seg=14)
        key(pf, 1, sc=0.0001); key(pf, f + 5, sc=0.0001); key(pf, f + 6, sc=0.6); key(pf, f + 10, sc=1.6); key(pf, f + 11, sc=0.0001)
    # 96-126: ram charge: sinks and leans back, the pack fires, it rushes 3 m plow first, hits, rocks back, settles
    M.hips(99, hz + 0.15, -8); M.torso(99, -10)
    M.hips(104, hz + 0.2, 20); M.torso(104, 18); M.hips(108, hz + 0.25, -6); M.torso(108, -6)
    M.hips(114, hz + lift, 0); M.torso(114); M.hips(126, hz + lift); M.torso(126)
    for sx in (-1, 1):
        M.arm(99, sx, -30, 40, sx * 10); M.arm(104, sx, 50, 70, sx * 5); M.arm(110, sx, 10, 40, sx * 6); M.arm(126, sx, 10, 40, sx * 6)
    key(rt, 99, loc=(bx, y - 0.3, 0), rot=(0, 0, 0)); key(rt, 105, loc=(bx, y + 3.0, 0), rot=(0, 0, 0))
    key(rt, 109, loc=(bx, y + 2.6, 0), rot=(0, 0, 0)); key(rt, 126, loc=(bx, y + 2.6, 0), rot=(0, 0, 0))
    ring_fx(f"{M.tag} ram ring", (bx, y + 4.5, 0.9), 105, 0.5, 5.0, 7, axis="Y")
    ring_fx(f"{M.tag} ram ring 2", (bx, y + 4.6, 0.9), 107, 0.4, 3.5, 6, axis="Y", th=0.03)
    cracks(M.tag, (bx, y + 4.4, 0.01), 105, 7, 2.0)


def form_MCb1(M, J, src):
    """Unpacks from a cube: a glowing construct cube swells at the chest, bursts, and every part flies out of it to
    its place (skirt first, pods and pack last), overshooting a little."""
    bpy.context.view_layer.update()
    c0 = J["torso"].matrix_world @ Vector((0, 0, 0.7))
    cube = box(f"{M.tag} pack cube", (-0.5, -0.5, -0.5), (0.5, 0.5, 0.5), SHOCK); cube.location = c0
    key(cube, 1, sc=0.0001, rot=(0, 0, 0)); key(cube, 2, sc=0.2, rot=(0, 0, 0)); key(cube, 10, sc=1.3, rot=(R(30), R(20), R(90)))
    key(cube, 11, sc=0.0001)
    for o in mparts(J, ("jet",)):
        c = centre(o); l0 = Vector(o.location)
        off = l0 + o.parent.matrix_world.to_3x3().inverted() @ (c0 - c)
        late = any(s in o.name for s in ("pod", "muzzle", "pack", "nozzle", "fist", "knuckle"))
        fa = int(rng.integers(17, 21)) if late else int(12 + max(0.0, c.z) / 3.5 * 5) + int(rng.integers(0, 2))
        key(o, 1, loc=tuple(off), sc=0.0001); key(o, 10, loc=tuple(off), sc=0.0001); key(o, 11, loc=tuple(off), sc=0.35)
        key(o, fa, loc=tuple(l0), sc=1.12); key(o, fa + 2, loc=tuple(l0), sc=1.0)


# ================================================================== MCb2 Jump Jet (R1, villager)
def build_MCb2(tag, T):
    J = {"hz": 1.75}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.15), hips); J["torso"] = torso
    plate(f"{tag} pelvis", (-0.55, -0.4, -0.3), (0.55, 0.4, 0.12), T, hips)
    legs, calf = [], []
    for sx in (-1, 1):                                   # digitigrade legs: knee forward, shin back, tall feet, claws
        hip = empty(f"{tag} hip {sx}", (sx * 0.52, 0, -0.1), hips)
        th = plate(f"{tag} thigh {sx}", (-0.2, -0.2, -0.76), (0.2, 0.2, 0.05), T, hip); th.rotation_euler = (R(28), 0, 0)
        knee = empty(f"{tag} knee {sx}", (0, 0.35, -0.65), hip)
        ball(f"{tag} knee ball {sx}", 0.17, FRAME, parent=knee)
        sh_ = plate(f"{tag} shin {sx}", (-0.16, -0.16, -0.72), (0.16, 0.16, 0.0), T, knee); sh_.rotation_euler = (R(-35), 0, 0)
        cyl(f"{tag} calf nozzle {sx}", 0.1, 0.22, FRAME, 10, knee, loc=(0, -0.3, -0.42), r2=0.13)
        calf.append(jet(f"{tag} calf jet {sx}", 0.11, -0.7, knee, (0, -0.3, -0.42)))
        ankle = empty(f"{tag} ankle {sx}", (0, -0.4, -0.57), knee)
        plate(f"{tag} instep {sx}", (-0.14, -0.12, -0.43), (0.14, 0.14, 0.0), T, ankle, 0.03)
        for k, xx in enumerate((-0.17, 0.0, 0.17)):
            plate(f"{tag} toe claw {sx} {k}", (xx - 0.06, -0.05, -0.43), (xx + 0.06, 0.62, -0.31), RM if k == 1 else T, ankle, 0.02)
        plate(f"{tag} heel spur {sx}", (-0.05, -0.42, -0.43), (0.05, -0.1, -0.33), RM, ankle, 0.015)
        legs.append((hip, knee, ankle, sx))
    pilot_seat_box(tag, torso, T, 0.95)
    plate(f"{tag} roof", (-1.0, -0.66, 1.38), (1.0, 0.5, 1.56), T, torso, 0.05)
    nose = plate(f"{tag} nose wedge", (-0.75, 0.0, -0.35), (0.75, 0.55, 0.0), T, torso, 0.05); nose.location = (0, 0.5, 0.1); nose.rotation_euler = (R(-30), 0, 0)
    hatch = empty(f"{tag} canopy hinge", (0, 0.55, 1.42), torso)
    box(f"{tag} canopy", (-0.8, 0.0, -1.38), (0.8, 0.06, 0.0), GL, hatch)
    for sx in (-1, 1):
        box(f"{tag} canopy brace {sx}", (sx * 0.4 - 0.04, 0.0, -1.38), (sx * 0.4 + 0.04, 0.1, 0.0), RM, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    pack = empty(f"{tag} pack", (0, -0.72, 0.9), torso)
    plate(f"{tag} pack body", (-0.5, -0.25, -0.5), (0.5, 0.12, 0.5), T, pack, 0.05)
    for sx in (-1, 1):
        plate(f"{tag} pack fin {sx}", (sx * 0.5, -0.3, -0.1), (sx * 0.85, -0.05, 0.75), RM, pack, 0.02)
    arms, fists = [], {}
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.25, 0, 1.15), torso)
        cyl(f"{tag} pauldron drum {sx}", 0.36, 0.5, T, 16, sh, loc=(-0.25, 0, 0.05), axis="X")
        torus(f"{tag} pauldron band {sx}", 0.37, 0.035, RM, loc=(0, 0, 0.05), parent=sh, axis="X")
        plate(f"{tag} upper arm {sx}", (-0.17, -0.17, -0.72), (0.17, 0.17, -0.1), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.75), sh)
        cyl(f"{tag} jet gauntlet {sx}", 0.3, 0.72, T, 16, el, loc=(0, 0, -0.72), r2=0.26)
        torus(f"{tag} gauntlet ring {sx}", 0.3, 0.03, RM, loc=(0, 0, -0.66), parent=el)
        cyl(f"{tag} elbow nozzle {sx}", 0.16, 0.18, FRAME, 10, el, loc=(0, -0.1, 0.0), r2=0.2)
        ej = jet(f"{tag} elbow jet {sx}", 0.17, 0.9, el, (0, -0.1, 0.18))
        rf = empty(f"{tag} rocket fist {sx}", (0, 0, -0.75), el)
        plate(f"{tag} fist {sx}", (-0.3, -0.3, -0.5), (0.3, 0.3, 0.0), T, rf, 0.06)
        for k in range(4):
            box(f"{tag} fist knuckle {sx} {k}", (-0.27 + k * 0.14, 0.25, -0.48), (-0.17 + k * 0.14, 0.34, -0.28), RM, rf)
        fj = jet(f"{tag} fist jet {sx}", 0.16, 0.6, rf, (0, 0, 0.0))
        fists[sx] = (rf, fj, ej)
        arms.append((sh, el, sx))
    J.update(legs=legs, arms=arms, hands={}, calf=calf, fists=fists)
    return J


def anim_MCb2(M):
    J = M.J; hz = J["hz"]
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0); M.arm(1, sx, 10, 30, sx * 6)
    M.hips(1, hz); M.torso(1); M.root(1, 0)
    for o in J["calf"]:
        flare(o, 1, 0)
    for sx in (-1, 1):
        rf, fj, ej = J["fists"][sx]
        flare(fj, 1, 0); flare(ej, 1, 0); key(rf, 1, loc=(0, 0, -0.75), rot=(0, 0, 0))
    # 36-75: three jet hops: crouch, the calf jets fire, a 1.2 m arc, a crouched landing
    M.root(36, 0)
    for i in range(3):
        f0 = 36 + i * 13
        for sx in (-1, 1):
            M.leg(f0, sx, 0, 0); M.leg(f0 + 3, sx, 25, -40, 15); M.leg(f0 + 5, sx, -12, 12, -10)
            M.leg(f0 + 8, sx, 30, -30, 10); M.leg(f0 + 11, sx, 25, -40, 15); M.leg(f0 + 13, sx, 0, 0)
            M.arm(f0 + 3, sx, -30, 40, sx * 10); M.arm(f0 + 7, sx, 40, 50, sx * 20); M.arm(f0 + 11, sx, -10, 40, sx * 8)
        M.hips(f0, hz); M.hips(f0 + 3, hz - 0.3, 10); M.hips(f0 + 5, hz + 0.15, -4); M.hips(f0 + 8, hz + 0.95, 6)
        M.hips(f0 + 11, hz - 0.3, 12); M.hips(f0 + 13, hz)
        M.root(f0 + 5, i * 1.2); M.root(f0 + 11, (i + 1) * 1.2)
        for o in J["calf"]:
            flare(o, f0 + 3, 0); flare(o, f0 + 4, 1.4, 1.2); flare(o, f0 + 8, 0.6); flare(o, f0 + 9, 0)
        ring_fx(f"{M.tag} hop ring {i}", (M.bx, (i + 1) * 1.2 + 0.2, 0.04), f0 + 11, 0.4, 3.5, 6, th=0.03)
    y = 3.6
    M.root(76, y)
    # 76-96: elbow-jet dash punches: the elbow jet fires and drives a straight right, the body lunging 1.4 m; then the left
    rf, fj, ejr = J["fists"][1]; ejl = J["fists"][-1][2]
    M.arm(76, 1, 10, 30, 6); M.arm(78, 1, 30, 110); M.arm(81, 1, 92, 0); M.arm(84, 1, 85, 5); M.arm(88, 1, 20, 60)
    M.arm(76, -1, 10, 30, -6); M.arm(80, -1, 40, 100); M.arm(84, -1, 40, 100); M.arm(87, -1, 92, 0); M.arm(90, -1, 85, 5)
    M.arm(96, 1, 10, 30, 6); M.arm(96, -1, 10, 30, -6)
    M.torso(78, 0, 0, 12); M.torso(81, 8, 0, -22); M.torso(84, 4, 0, -10); M.torso(87, 8, 0, 20); M.torso(92); M.torso(96)
    M.root(79, y); M.root(82, y + 1.0); M.root(88, y + 1.4); M.root(96, y + 1.4)
    for sx in (-1, 1):
        M.leg(79, sx, 0, 0); M.leg(82, sx, 30 * sx, -30 if sx > 0 else -5, 10); M.leg(88, sx, 0, 0)
    M.hips(82, hz - 0.15, 6); M.hips(90, hz)
    flare(ejr, 78, 0); flare(ejr, 79, 1.5, 1.2); flare(ejr, 82, 0.8); flare(ejr, 83, 0)
    flare(ejl, 85, 0); flare(ejl, 86, 1.3, 1.1); flare(ejl, 88, 0.6); flare(ejl, 89, 0)
    ring_fx(f"{M.tag} punch ring r", (M.bx + 1.25, y + 3.4, 2.75), 82, 0.3, 3.5, 6, axis="Y")
    ring_fx(f"{M.tag} punch ring l", (M.bx - 1.25, y + 3.6, 2.75), 88, 0.25, 3.0, 5, axis="Y", th=0.03)
    y2 = y + 1.4
    # 96-126: boomerang rocket fists: both fire, swing out wide, cross and clash in front, loop back to the wrists
    for sx in (-1, 1):
        M.arm(99, sx, 88, 0, -sx * 4); M.arm(118, sx, 88, 0, -sx * 4); M.arm(124, sx, 10, 30, sx * 6)
        M.leg(99, sx, 15, -25, 10); M.leg(118, sx, 15, -25, 10); M.leg(124, sx, 0, 0)
        rf, fj, ej = J["fists"][sx]
        key(rf, 100, loc=(0, 0, -0.75), rot=(0, 0, 0))
        for j in range(1, 19):
            u = j / 18
            x = -sx * 1.25 * math.sin(math.pi * u) + sx * 1.1 * math.sin(2 * math.pi * u)
            z = -0.75 - 1.4 * (1 - math.cos(2 * math.pi * u))
            key(rf, 100 + j, loc=(x, 0, z), rot=(0, 0, R(sx * 720 * u)))
        flare(fj, 99, 0); flare(fj, 100, 1.4, 1.2); flare(fj, 117, 1.0); flare(fj, 118, 0)
    M.hips(99, hz - 0.2, 4); M.hips(118, hz - 0.2, 4); M.hips(124, hz); M.torso(100, -6); M.torso(118, -6); M.torso(124)
    scene.frame_set(109); bpy.context.view_layer.update()
    c = (J["fists"][1][0].matrix_world.translation + J["fists"][-1][0].matrix_world.translation) / 2
    ring_fx(f"{M.tag} clash ring", tuple(c), 109, 0.4, 5.0, 7, axis="Y")
    bm = ball(f"{M.tag} clash burst", 0.5, SHOCK, loc=tuple(c), seg=16)
    key(bm, 1, sc=0.0001); key(bm, 108, sc=0.0001); key(bm, 109, sc=0.8); key(bm, 113, sc=2.4); key(bm, 114, sc=0.0001)


def form_MCb2(M, J, src):
    """Unfolds like a folded toy, joint by joint from the hips out: each joint starts folded flat and swings open,
    its plates popping in as it opens."""
    scene.frame_set(1); bpy.context.view_layer.update()
    order = []
    for h, k, a, sx in J["legs"]:
        order += [h, k, a]
    for sh, el, sx in J["arms"]:
        order += [sh, el]
    order += [o for o in J["torso"].children if o.type == "EMPTY" and "pack" in o.name]
    done = set()
    for i, pv in enumerate(order):
        fa = 4 + i
        r0 = tuple(pv.rotation_euler)
        nm = pv.name
        fo = (R(-110), 0, 0) if " knee" in nm else (R(120), 0, 0) if " ankle" in nm or " elbow" in nm else (0, R(100) if "-1" in nm else R(-100), 0) if "shoulder" in nm else (R(90), 0, 0)
        fr = tuple(a + b for a, b in zip(r0, fo))
        key(pv, 1, rot=fr); key(pv, fa, rot=fr); key(pv, fa + 3, rot=tuple(a - 0.12 * b for a, b in zip(r0, fo))); key(pv, fa + 5, rot=r0)
        for o in pv.children:
            if o.type == "MESH" and o not in done and "jet" not in o.name and " pilot" not in o.name:
                done.add(o); sc0 = tuple(o.scale)
                key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 2, sc=sc0)
    for o in mparts(J, ("jet",)):
        if o not in done:
            done.add(o); sc0 = tuple(o.scale); fa = int(rng.integers(14, 20))
            key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 2, sc=sc0)


# ================================================================== MCb3 Orbit Juggernaut (R1, villager)
def build_MCb3(tag, T):
    J = {"hz": 1.45}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.15), hips); J["torso"] = torso
    plate(f"{tag} pelvis", (-0.65, -0.45, -0.3), (0.65, 0.45, 0.15), T, hips)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.52, 0.55, 0.55)
        plate(f"{tag} thigh {sx}", (-0.28, -0.28, -0.5), (0.28, 0.28, 0.0), T, hip)
        plate(f"{tag} floating knee {sx}", (-0.2, 0.25, -0.12), (0.2, 0.42, 0.18), RM, knee, 0.04)
        plate(f"{tag} shin {sx}", (-0.3, -0.3, -0.5), (0.3, 0.3, -0.05), T, knee)
        plate(f"{tag} stomp foot {sx}", (-0.42, -0.45, -0.28), (0.42, 0.62, 0.0), T, ankle, 0.06)
        torus(f"{tag} foot glow {sx}", 0.34, 0.03, W, loc=(0, 0.08, -0.26), parent=ankle)
        legs.append((hip, knee, ankle, sx))
    pilot_seat_box(tag, torso, T, 1.0)
    plate(f"{tag} roof", (-1.05, -0.68, 1.38), (1.05, 0.6, 1.6), T, torso, 0.05)
    torus(f"{tag} collar halo", 0.55, 0.05, W, loc=(0, -0.1, 1.8), parent=torso)
    hatch = empty(f"{tag} canopy hinge", (0, 0.55, 1.42), torso)
    box(f"{tag} canopy", (-0.85, 0.0, -1.38), (0.85, 0.06, 0.0), GL, hatch)
    box(f"{tag} canopy ring bar", (-0.87, 0.0, -0.9), (0.87, 0.1, -0.82), RM, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    pack = empty(f"{tag} booster pack", (0, -0.78, 0.8), torso)
    plate(f"{tag} pack body", (-0.7, -0.3, -0.6), (0.7, 0.15, 0.7), T, pack, 0.05)
    jets = []
    for i, (xx, zz, r_) in enumerate(((0, 0.38, 0.17), (0, -0.38, 0.17), (-0.42, 0, 0.13), (0.42, 0, 0.13))):
        cyl(f"{tag} nozzle {i}", r_, 0.25, FRAME, 12, pack, loc=(xx, -0.3, zz), axis="Y", r2=r_ * 1.3).rotation_euler = (0, 0, R(180))
        jets.append(jet(f"{tag} pack jet {i}", r_, 1.0, pack, (xx, -0.55, zz), (R(90), 0, 0)))
    arms, fists = [], {}
    for sx in (-1, 1):                                   # floating limbs: no upper arm, just orbiting cells
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.45, 0, 1.15), torso)
        plate(f"{tag} floating pauldron {sx}", (-0.42, -0.45, 0.12), (0.42, 0.45, 0.5), T, sh, 0.06)
        torus(f"{tag} shoulder orbit {sx}", 0.22, 0.035, RM, parent=sh, axis="X")
        orb = empty(f"{tag} arm orbit {sx}", (0, 0, -0.38), sh)
        for k in range(3):
            a = 2 * math.pi * k / 3
            box(f"{tag} orbit cell {sx} {k}", (-0.08, -0.08, -0.08), (0.08, 0.08, 0.08), T, orb).location = (0.2 * math.cos(a), 0.2 * math.sin(a), 0)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.75), sh)
        torus(f"{tag} elbow orbit {sx}", 0.18, 0.03, RM, parent=el, axis="X")
        plate(f"{tag} floating gauntlet {sx}", (-0.3, -0.3, -0.62), (0.3, 0.3, -0.12), T, el, 0.05)
        rf = empty(f"{tag} fist {sx}", (0, 0, -0.72), el)
        plate(f"{tag} fist block {sx}", (-0.34, -0.34, -0.58), (0.34, 0.34, -0.05), T, rf, 0.07)
        for k in range(4):
            box(f"{tag} fist knuckle {sx} {k}", (-0.31 + k * 0.16, 0.29, -0.56), (-0.19 + k * 0.16, 0.39, -0.32), RM, rf)
        fj = jet(f"{tag} fist jet {sx}", 0.17, 0.6, rf, (0, 0, -0.02))
        chain = []
        for k in range(8):
            cc = box(f"{tag} chain cell {sx} {k}", (-0.07, -0.07, -0.07), (0.07, 0.07, 0.07), W if k % 2 else T, el)
            cc.location = (0, 0, -0.72); chain.append(cc)
        fists[sx] = (rf, fj, chain, orb)
        arms.append((sh, el, sx))
    J.update(legs=legs, arms=arms, hands={}, jets=jets, fists=fists)
    return J


def anim_MCb3(M):
    J = M.J; hz = J["hz"]; bx = M.bx
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0); M.arm(1, sx, 0, 20, sx * 6)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    for o in J["jets"]:
        for f, l in ((1, 0), (97, 0), (99, 1.4), (104, 1.4), (106, 0.5), (118, 0.5), (120, 0)):
            flare(o, f, l)
    for sx in (-1, 1):
        rf, fj, chain, orb = J["fists"][sx]
        spin_keys(orb, 1, 130, sx * 6, 2, 5)
        flare(fj, 1, 0); key(rf, 1, loc=(0, 0, -0.72), rot=(0, 0, 0))
        for cc in chain:
            key(cc, 1, loc=(0, 0, -0.72), sc=0.0001)
    # 36-76: four stomping steps, the floating fists bob out of time with the body
    for i in range(4):
        f0 = 36 + i * 10; sx = 1 if i % 2 == 0 else -1
        M.leg(f0, sx, 0, 0); M.leg(f0 + 4, sx, 35, -55, 18); M.leg(f0 + 10, sx, 0, 0); M.leg(f0 + 5, -sx, -10, 0)
        M.hips(f0, hz - 0.06); M.hips(f0 + 4, hz + 0.08, 0, 3 * sx, -4 * sx); M.hips(f0 + 10, hz - 0.06)
        M.arm(f0 + 5, sx, -20, 25, sx * 8); M.arm(f0 + 5, -sx, 25, 30, -sx * 8)
        M.root(f0 + 10, (i + 1) * 0.9)
        ring_fx(f"{M.tag} stomp ring {i}", (bx + sx * 0.52, (i + 1) * 0.9 + 0.1, 0.04), f0 + 10, 0.4, 3.0, 6, th=0.03)
        for s2 in (-1, 1):
            rf = J["fists"][s2][0]
            key(rf, f0 + (3 if s2 == sx else 8), loc=(0, 0.05, -0.62)); key(rf, f0 + (8 if s2 == sx else 3), loc=(0, -0.03, -0.82))
    y = 3.6
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0); M.arm(76, sx, 0, 20, sx * 6); key(J["fists"][sx][0], 76, loc=(0, 0, -0.72))
    M.hips(76, hz)
    # 76-96: drill fist: the right arm aims, the fist spins up and corkscrews 4 m out on a chain of cells, then reels in
    rf, fj, chain, orb = J["fists"][1]
    M.arm(79, 1, 90, 0); M.arm(92, 1, 88, 0); M.arm(96, 1, 0, 20, 6); M.torso(79, 0, 0, -12); M.torso(92, 0, 0, -8); M.torso(96)
    M.arm(79, -1, 35, 70, -10); M.arm(92, -1, 35, 70, -10); M.arm(96, -1, 0, 20, -6)
    M.leg(79, -1, 15, -15); M.leg(92, -1, 15, -15); M.leg(96, -1, 0, 0); M.hips(80, hz - 0.08); M.hips(92, hz)
    ext = {79: -0.72, 84: -4.7, 88: -4.7, 93: -0.72}
    for f, z in ext.items():
        key(rf, f, loc=(0, 0, z))
        for k, cc in enumerate(chain):
            key(cc, f, loc=(0, 0, -0.72 + (z + 0.72) * (k + 1) / 9))
    spin_keys(rf, 79, 93, 5, 2, 2)
    for cc in chain:
        key(cc, 79, sc=0.0001); key(cc, 80, sc=1.0); key(cc, 92, sc=1.0); key(cc, 93, sc=0.0001)
    flare(fj, 79, 0); flare(fj, 80, 1.5, 1.2); flare(fj, 84, 1.0); flare(fj, 85, 0)
    ring_fx(f"{M.tag} drill ring", (bx + 1.45, y + 4.9, 2.75), 84, 0.3, 3.5, 7, axis="Y")
    ring_fx(f"{M.tag} drill ring 2", (bx + 1.45, y + 5.0, 2.75), 86, 0.25, 2.8, 6, axis="Y", th=0.03)
    # 96-126: meteor fists: both fists blast straight up out of sight, then dive onto the ground ahead and float back
    for sx in (-1, 1):
        M.arm(99, sx, 170, 10, -sx * 6); M.arm(102, sx, 160, 10, -sx * 6); M.arm(108, sx, 45, 20, sx * 4); M.arm(118, sx, 45, 20, sx * 4)
        M.arm(124, sx, 0, 20, sx * 6)
        M.leg(99, sx, 20, -40, 20); M.leg(108, sx, 0, 0); M.leg(112, sx, 25, -45, 20); M.leg(118, sx, 0, 0)
    M.hips(99, hz - 0.25); M.hips(103, hz + 0.1); M.hips(112, hz - 0.25); M.hips(118, hz); M.torso(112, 12); M.torso(118)
    for k, sx in enumerate((1, -1)):
        rf, fj, chain, orb = J["fists"][sx]
        scene.frame_set(101); bpy.context.view_layer.update()
        p0 = rf.matrix_world.translation.copy()
        land = 110 + 2 * k
        tgt = Vector((bx + sx * 0.9, y + 3.6, 0.3))
        mf = empty(f"{M.tag} meteor fist {sx}"); mf.rotation_mode = "XYZ"
        plate(f"{M.tag} meteor block {sx}", (-0.34, -0.34, -0.3), (0.34, 0.34, 0.3), TEX["r1"], mf, 0.07)
        for kk in range(4):
            box(f"{M.tag} meteor knuckle {sx} {kk}", (-0.31 + kk * 0.16, -0.39, -0.28), (-0.19 + kk * 0.16, -0.29, -0.04), RM, mf)
        tail = cyl(f"{M.tag} meteor tail {sx}", 0.3, 1.6, W, 12, mf, loc=(0, 0, 0.3), r2=0.02)
        key(mf, 1, loc=tuple(p0), rot=(0, 0, 0), sc=0.0001); key(mf, 101, loc=tuple(p0), rot=(0, 0, 0), sc=0.0001)
        key(mf, 102, loc=tuple(p0), rot=(R(180), 0, 0), sc=1.0); key(mf, 105, loc=tuple(p0 + Vector((0, 0, 9))), rot=(R(180), 0, 0), sc=1.0)
        key(mf, land - 4, loc=tuple(tgt + Vector((0, -1.0, 9))), rot=(0, 0, 0), sc=1.0)
        key(mf, land, loc=tuple(tgt), rot=(0, 0, 0), sc=1.0); key(mf, land + 5, loc=tuple(tgt), rot=(0, 0, 0), sc=1.0)
        key(tail, 1, sc=1.0); key(tail, land, sc=1.0); key(tail, land + 1, sc=(1, 1, 0.0001))
        scene.frame_set(122); bpy.context.view_layer.update()
        key(mf, 122, loc=tuple(rf.matrix_world.translation), rot=(0, 0, 0), sc=1.0); key(mf, 123, sc=0.0001)
        sc0 = tuple(rf.scale)
        key(rf, 101, sc=sc0); key(rf, 102, sc=0.0001); key(rf, 122, sc=0.0001); key(rf, 123, sc=sc0)
        ring_fx(f"{M.tag} meteor ring {sx}", (tgt.x, tgt.y, 0.04), land, 0.5, 5.0, 9)
        cracks(f"{M.tag} meteor {sx}", (tgt.x, tgt.y, 0.01), land, 6, 1.8)


def form_MCb3(M, J, src):
    """A vortex: every part spirals in from a wide whirl round the mech, the circle tightening and dropping, the
    floating fists last."""
    bpy.context.view_layer.update()
    c0 = J["root"].matrix_world.translation.copy()
    for o in mparts(J, ("jet", "chain")):
        c = centre(o); l0 = Vector(o.location); P3i = o.parent.matrix_world.to_3x3().inverted()
        last = any(s in o.name for s in ("fist", "knuckle", "gauntlet"))
        fa = int(rng.integers(18, 22)) if last else int(6 + (c.z / 3.4) * 9) + int(rng.integers(0, 3))
        fs = max(2, fa - 8); th0 = math.atan2(c.y - c0.y, c.x - c0.x)
        key(o, 1, sc=0.0001); key(o, fs - 1, sc=0.0001)
        for f in range(fs, fa + 1, 2):
            u = (f - fs) / max(1, fa - fs)
            r_ = 3.0 * (1 - u); a = th0 + 2.2 * math.pi * (1 - u)
            wpos = Vector((c0.x + (math.hypot(c.x - c0.x, c.y - c0.y) + r_) * math.cos(a), c0.y + (math.hypot(c.x - c0.x, c.y - c0.y) + r_) * math.sin(a), c.z + 1.8 * (1 - u)))
            key(o, f, loc=tuple(l0 + P3i @ (wpos - c)), sc=0.5 + 0.5 * u)
        key(o, fa, loc=tuple(l0), sc=1.0)


# ================================================================== MCc shared body (H1, zombie, horned)
def mcc_body(tag, T, J, hz, shx, shz, up, fore, w=0.95):
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, hz), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.15), hips); J["torso"] = torso
    plate(f"{tag} pelvis", (-0.65, -0.45, -0.25), (0.65, 0.45, 0.15), T, hips)
    pilot_seat_box(tag, torso, T, w)
    hatch = empty(f"{tag} visor hinge", (0, 0.55, 1.4), torso)
    box(f"{tag} visor", (-w + 0.15, 0.0, -1.35), (w - 0.15, 0.06, 0.0), GL, hatch)
    plate(f"{tag} visor plate", (-w + 0.13, 0.0, -0.7), (w - 0.13, 0.12, 0.0), T, hatch, 0.02)
    box(f"{tag} visor slit", (-0.55, 0.12, -0.45), (0.55, 0.15, -0.36), W, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    arms = []
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * shx, 0, shz), torso)
        plate(f"{tag} upper arm {sx}", (-0.2, -0.2, -up + 0.05), (0.2, 0.2, -0.1), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -up), sh)
        cyl(f"{tag} elbow joint {sx}", 0.15, 0.36, FRAME, 12, el, loc=(-0.18, 0, 0), axis="X")
        plate(f"{tag} vambrace {sx}", (-0.24, -0.24, -fore + 0.3), (0.24, 0.24, 0.0), T, el, 0.04)
        plate(f"{tag} gauntlet {sx}", (-0.27, -0.2, -fore - 0.12), (0.27, 0.3, -fore + 0.3), T, el, 0.05)
        arms.append((sh, el, sx))
    J.update(arms=arms, hands={}, arm_geo=(shx, shz, up, Vector((0, 0.06, -fore))))
    return root, hips, torso


# ================================================================== MCc1 Anvil Breaker
def build_MCc1(tag, T):
    J = {"hz": 1.6}
    root, hips, torso = mcc_body(tag, T, J, 1.6, 1.2, 1.05, 0.72, 0.85, 1.0)
    for i, xx in enumerate((-0.45, 0.0, 0.45)):                 # three heavy front tassets
        pv = empty(f"{tag} tasset pivot {i}", (xx, 0.42, -0.15), hips); pv.rotation_euler = (R(10), 0, 0)
        plate(f"{tag} tasset {i}", (-0.22, 0.0, -0.55), (0.22, 0.1, 0.0), RM if i == 1 else T, pv, 0.02)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.5, 0.6, 0.6)
        plate(f"{tag} thigh {sx}", (-0.3, -0.3, -0.6), (0.3, 0.3, 0.0), T, hip)
        plate(f"{tag} knee cop {sx}", (-0.28, 0.15, -0.15), (0.28, 0.38, 0.2), RM, knee, 0.04)
        plate(f"{tag} greave {sx}", (-0.3, -0.3, -0.6), (0.3, 0.32, 0.0), T, knee)
        plate(f"{tag} boot {sx}", (-0.4, -0.45, -0.3), (0.4, 0.6, 0.0), T, ankle, 0.05)
        legs.append((hip, knee, ankle, sx))
    plate(f"{tag} roof", (-1.1, -0.66, 1.36), (1.1, 0.62, 1.55), T, torso, 0.06)
    plate(f"{tag} belly plate", (-0.8, 0.5, 0.1), (0.8, 0.65, 0.5), RM, torso, 0.03)
    head = empty(f"{tag} helm", (0, 0.1, 1.5), torso); J["head"] = head
    plate(f"{tag} low helm", (-0.6, -0.45, 0.0), (0.6, 0.45, 0.32), T, head, 0.06)
    for sx in (-1, 1):                                          # bull horns, out then forward
        h1 = cyl(f"{tag} horn {sx} a", 0.15, 0.6, T, 8, head, loc=(sx * 0.55, 0.1, 0.15), r2=0.1); h1.rotation_euler = (0, R(sx * 80), 0)
        h2 = cyl(f"{tag} horn {sx} b", 0.1, 0.55, RM, 8, head, loc=(sx * 1.12, 0.12, 0.2), r2=0.01); h2.rotation_euler = (R(-75), 0, R(-sx * 15))
    for sx in (-1, 1):
        sh = J["arms"][0 if sx < 0 else 1][0]
        plate(f"{tag} pauldron {sx}", (-0.45, -0.5, -0.15), (0.45, 0.5, 0.42), T, sh, 0.07)
        plate(f"{tag} pauldron ridge {sx}", (-0.08, -0.5, 0.4), (0.08, 0.5, 0.58), RM, sh, 0.02)
    make_hammer(tag, torso, J, 0.95, 1.2, "anvil", T)
    J["legs"] = legs
    return J


def anim_MCc1(M):
    J = M.J; hz = J["hz"]; bx = M.bx
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0)
    M.hips(1, hz); M.torso(1); M.root(1, 0)
    # 36-75: crutch walk: plants the anvil 1.7 m ahead, takes two steps up to it, plants again (three times)
    M.root(36, 0)
    plants = []
    for i in range(3):
        f0 = 36 + i * 13; y0 = i * 1.2
        M.root(f0 + 4, y0); M.root(f0 + 13, y0 + 1.2)
        for j, sx in enumerate((1, -1)):
            fs = f0 + 4 + j * 4
            M.leg(fs, sx, 0, 0); M.leg(fs + 2, sx, 30, -45, 15); M.leg(fs + 5, sx, 0, 0)
        M.hips(f0 + 4, hz, 10); M.hips(f0 + 8, hz + 0.06, 6); M.hips(f0 + 13, hz, 2)
        M.torso(f0 + 2, -4); M.torso(f0 + 4, 10); M.torso(f0 + 13, 2)
        plants.append((f0 + 4, f0 + 13, y0))
    M.root(76, 3.6); M.hips(76, hz); M.torso(76)
    y = 3.6
    # 76-96: side swing (J on 503: from the side when it hits a wall): a short draw right, swung across at waist height,
    # the face leading, through a hex construct wall that breaks
    M.torso(80, 0, 0, 30); M.torso(83, 4, 0, -10); M.torso(86, 6, 0, -38); M.torso(92, 0, 0, -10); M.torso(96)
    M.hips(80, hz - 0.1); M.hips(86, hz - 0.18); M.hips(96, hz)
    M.leg(78, -1, 0, 0); M.leg(81, -1, 25, -25, 0); M.leg(90, -1, 25, -25, 0); M.leg(96, -1, 0, 0)
    # 96-126: jump smash: crouch with the hammer up, leap 1.2 m forward and up, crash down face first, hex shockwave
    for sx in (-1, 1):
        M.leg(97, sx, 0, 0); M.leg(100, sx, 40, -80, 40); M.leg(103, sx, -10, 0); M.leg(106, sx, 30, -40, 10)
        M.leg(109, sx, 45, -90, 45); M.leg(118, sx, 45, -90, 45); M.leg(126, sx, 0, 0)
    M.hips(97, hz); M.hips(100, hz - 0.45); M.hips(104, hz + 1.2); M.hips(106, hz + 0.9); M.hips(109, hz - 0.55); M.hips(118, hz - 0.55); M.hips(126, hz)
    M.torso(100, -6); M.torso(104, -14); M.torso(109, 40); M.torso(118, 38); M.torso(126)
    M.root(100, y); M.root(109, y + 1.2); M.root(126, y + 1.2)

    G = (0, 0.82, 0.6)
    REST_D = Vector((0, 0.15, -1)).normalized()
    keys = []
    T1 = tw(M, 1)
    restW = head_on_ground(J, T1 @ Vector((0, 1.05, 0)), REST_D, Vector((0, 1, 0.15)))
    keys += [(1, "W", restW, REST_D, Vector((0, 1, 0.15)), -0.55, -0.85), (33, "W", restW, REST_D, Vector((0, 1, 0.15)), -0.55, -0.85)]
    for f_plant, f_end, y0 in plants:
        # the head is lifted and set down 1.7 m ahead of the chest; the haft swings over it as the body walks up
        T_ = tw(M, f_plant); hxy = T_ @ Vector((0, 1.7, 0)); hxy.x = bx
        g = T_ @ Vector(G); dW = (Vector((bx, hxy.y, 0.4)) - g).normalized()
        nW = Vector((0, dW.z, -dW.y))
        piv = head_on_ground(J, hxy, dW, nW)
        s_mid = J["hd"] - (Vector((bx, hxy.y, 0.4)) - g).length
        keys.append((f_plant - 2, "T", Vector((0, 0.95, 0.55)), Vector((0, 0.8, 0.3)).normalized(), Vector((0, 0.3, -0.8)), -0.2, -0.55))
        keys.append((f_plant, "W", piv, dW, nW, s_mid + 0.15, s_mid - 0.2))
        T2 = tw(M, f_end); g2 = T2 @ Vector(G); h0 = piv + hq(dW, nW) @ Vector((0, 0, J["hd"]))
        d2 = (h0 - g2).normalized(); n2 = Vector((0, d2.z, -d2.y))
        piv2 = h0 - d2 * J["hd"]; s2 = J["hd"] - (h0 - g2).length
        keys.append((f_end - 1, "W", piv2, d2, n2, s2 + 0.15, s2 - 0.2))
    CARRY = (Vector((0.05, 0.85, 0.55)), Vector((-0.55, 0.15, 1)).normalized(), Vector((0, 1, 0)), 0.2, -0.35)
    keys.append((76, "T", *CARRY))

    def flat(f, p, d, sR=0.05, sL=-0.35):
        d = Vector(d).normalized()
        return (f, "T", Vector(p), d, Vector((-d.y, d.x, 0.0)), sR, sL)
    keys += [flat(80, (0.25, 0.7, 0.35), (1, -0.2, 0.1)), flat(83, (0.05, 0.8, 0.35), (0.3, 1, 0.05)),
             flat(86, (-0.15, 0.75, 0.35), (-0.9, 0.6, 0.05)), flat(89, (-0.2, 0.7, 0.4), (-1, 0.1, 0.15)),
             (95, "T", *CARRY)]
    OVER = (Vector((0, 0.35, 1.4)), Vector((0, -0.45, 1)).normalized(), Vector((0, 1, 0.45)), 0.15, -0.3)
    keys += [(100, "T", *OVER), (106, "T", Vector((0, 0.4, 1.45)), Vector((0, -0.2, 1)).normalized(), Vector((0, 1, 0.2)), 0.15, -0.3)]
    imp = impact(M, 109, 2.15, 14)
    keys += [imp, (imp[0] + 9,) + imp[1:], (124, "T", *CARRY), (130, "T", *CARRY)]
    drive_hammer(M, keys)
    J["rest_head"] = head_world(M, 12)
    # the wall: hex bricks, standing ahead from frame 70, broken by the swing at 85
    h85 = head_world(M, 85)
    wall = []
    for r_ in range(4):
        for c_ in range(3):
            x0 = h85.x - 1.05 + c_ * 0.7 + (0.35 if r_ % 2 else 0) - 0.2
            wall.append(plate(f"{M.tag} wall brick {r_} {c_}", (x0, h85.y - 0.15, r_ * 0.55), (x0 + 0.66, h85.y + 0.15, r_ * 0.55 + 0.52), WALL_H1, None, 0.03))
    for o in wall:
        key(o, 1, sc=0.0001); key(o, 69, sc=0.0001); key(o, 72, sc=1.0)
    shatter(wall, 85, CM["pix"], rng, M.tag + " wall", 3, 0.16, 15)
    ring_fx(f"{M.tag} swing ring", tuple(h85), 85, 0.3, 3.5, 6, axis="X", th=0.03)
    h = head_world(M, 109)
    hex_ring(f"{M.tag} hex wave", (h.x, h.y, 0.05), 109, 0.6, 7.0, 10)
    hex_ring(f"{M.tag} hex wave 2", (h.x, h.y, 0.07), 111, 0.5, 4.5, 8)
    cracks(M.tag, (h.x, h.y, 0.01), 109, 8, 2.6)


def form_MCc1(M, J, src):
    """Built out from the hammer: the anvil appears planted first, the haft rises, then the plates pop out from the
    grip outward (nearest first) with a hex ripple on the ground."""
    bpy.context.view_layer.update()
    hparts = [o for o in mparts(J) if "hammer" in o.name]
    for o in hparts:
        sc0 = tuple(o.scale); fa = 2 if "head" in o.name or "face" in o.name or "horn" in o.name or "band" in o.name else 5
        key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 2, sc=tuple(v * 1.15 for v in sc0)); key(o, fa + 3, sc=sc0)
    h = J.get("rest_head") or J["hammer_head"].matrix_world.translation
    g = J["hammer"].matrix_world.translation
    rest = [o for o in mparts(J) if o not in hparts]
    ds = [(o, (centre(o) - g).length) for o in rest]; hi = max(d for _, d in ds) + 1e-6
    for o, d in ds:
        fa = int(7 + d / hi * 13) + int(rng.integers(0, 2)); sc0 = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 2, sc=tuple(v * 1.12 for v in sc0)); key(o, fa + 3, sc=sc0)
    hex_ring(f"{M.tag} form ripple", (h.x, h.y, 0.04), 4, 0.4, 5.0, 12)


# ================================================================== MCc2 Ram Breaker
def build_MCc2(tag, T):
    J = {"hz": 2.15}
    root, hips, torso = mcc_body(tag, T, J, 2.15, 1.12, 1.2, 0.85, 0.95, 0.9)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.42, 0.92, 0.92)
        plate(f"{tag} thigh {sx}", (-0.2, -0.22, -0.92), (0.2, 0.22, 0.0), T, hip)
        plate(f"{tag} knee spike plate {sx}", (-0.18, 0.15, -0.15), (0.18, 0.32, 0.2), RM, knee, 0.03)
        cyl(f"{tag} knee spike {sx}", 0.08, 0.3, RM, 6, knee, loc=(0, 0.3, 0.02), axis="Y", r2=0.0)
        plate(f"{tag} greave {sx}", (-0.2, -0.2, -0.92), (0.2, 0.24, 0.0), T, knee)
        plate(f"{tag} boot {sx}", (-0.28, -0.38, -0.25), (0.28, 0.5, 0.0), T, ankle, 0.05)
        legs.append((hip, knee, ankle, sx))
    for i in range(5):                                           # a hex scale skirt: narrow hanging strips
        a = -math.pi * 0.8 + i * (math.pi * 1.6 / 4)
        pv = empty(f"{tag} scale pivot {i}", (0.62 * math.sin(a), 0.46 * math.cos(a), -0.1), hips); pv.rotation_euler = (R(8), 0, -a)
        cyl(f"{tag} skirt scale {i}", 0.16, -0.65, T if i % 2 else RM, 6, pv, loc=(0, 0, 0), r2=0.1)
    plate(f"{tag} roof", (-0.98, -0.66, 1.36), (0.98, 0.6, 1.52), T, torso, 0.05)
    head = empty(f"{tag} helm", (0, 0.05, 1.5), torso); J["head"] = head
    plate(f"{tag} helm", (-0.45, -0.45, 0.0), (0.45, 0.45, 0.5), T, head, 0.07)
    plate(f"{tag} helm brow", (-0.47, 0.35, 0.22), (0.47, 0.5, 0.36), RM, head, 0.02)
    for sx in (-1, 1):                                           # ram horns curling round the helm sides
        hn = arc(f"{tag} ram horn {sx}", 0.3, 0.09, R(-60), R(220), T, (0, 0, 0), 18, 6)
        hn.parent = head; hn.location = (sx * 0.52, 0.0, 0.3); hn.rotation_euler = (0, R(90 * sx), 0)
        torus(f"{tag} horn ring {sx}", 0.13, 0.03, RM, loc=(sx * 0.5, -0.1, 0.45), parent=head, axis="X")
    for sx in (-1, 1):
        sh = J["arms"][0 if sx < 0 else 1][0]
        plate(f"{tag} pauldron {sx}", (-0.38, -0.42, -0.1), (0.38, 0.42, 0.38), T, sh, 0.06)
        cyl(f"{tag} pauldron spike {sx}", 0.1, 0.45, RM, 6, sh, loc=(sx * 0.1, 0, 0.36), r2=0.0).rotation_euler = (0, R(sx * 20), 0)
    make_hammer(tag, torso, J, 1.25, 1.55, "maul", T)
    J["legs"] = legs
    return J


def anim_MCc2(M):
    J = M.J; hz = J["hz"]; bx = M.bx
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    # 36-76: a stalking walk: four long steps, leaning in, the maul on the right shoulder
    for i in range(4):
        f0 = 36 + i * 10; sx = 1 if i % 2 == 0 else -1
        M.leg(f0, sx, -8, 0); M.leg(f0 + 4, sx, 38, -55, 15); M.leg(f0 + 10, sx, 10, -5)
        M.leg(f0, -sx, 10, -5); M.leg(f0 + 5, -sx, -14, -8); M.leg(f0 + 10, -sx, -8, 0)
        M.hips(f0, hz - 0.08, 8); M.hips(f0 + 5, hz + 0.04, 8, 3 * sx, -6 * sx); M.hips(f0 + 10, hz - 0.08, 8)
        M.torso(f0 + 5, 6, 0, 8 * sx); M.torso(f0 + 10, 6)
        M.root(f0 + 10, (i + 1) * 0.9)
    y = 3.6
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0)
    M.hips(76, hz); M.torso(76)
    # 76-96: overhead from the shoulder: up and over in 3 ticks, face first into the ground, held, back to the shoulder
    M.torso(78, -8); M.torso(81, 34); M.torso(87, 32); M.torso(94); M.hips(78, hz + 0.05); M.hips(81, hz - 0.45); M.hips(87, hz - 0.43); M.hips(94, hz)
    for sx in (-1, 1):
        M.leg(81, sx, 30 if sx < 0 else -10, -50 if sx < 0 else -5, 20 if sx < 0 else 5); M.leg(87, sx, 30 if sx < 0 else -10, -50 if sx < 0 else -5, 20 if sx < 0 else 5)
        M.leg(94, sx, 0, 0)
    # 96-126: the throw: cocked back over the head, hurled end over end, lands face first 4 m ahead, then recalled
    M.torso(99, -14, 0, 18); M.torso(102, 22, 0, -12); M.torso(106, 8); M.torso(113, 10); M.torso(118, -4); M.torso(122)
    M.hips(99, hz - 0.1); M.hips(102, hz - 0.2); M.hips(108, hz); M.hips(118, hz - 0.12); M.hips(122, hz)
    for sx in (-1, 1):
        M.leg(99, sx, -15 if sx > 0 else 25, -10 if sx > 0 else -30); M.leg(102, sx, 30 if sx > 0 else -12, -30 if sx > 0 else -4); M.leg(108, sx, 0, 0)
    # arms during the flight (hands off the haft): follow-through, then the right hand reaches to call it back
    M.arm(103, 1, 70, 10, -10); M.arm(103, -1, 50, 30, 10); M.arm(108, 1, 30, 30); M.arm(108, -1, 20, 30)
    M.arm(113, 1, 95, 0, 5); M.arm(113, -1, 15, 30); M.arm(116, 1, 95, 0, 5)

    SH = (Vector((0.62, 0.35, 1.3)), Vector((-0.2, -0.85, 0.45)).normalized(), Vector((0, 0, 1)), 0.05, -0.65)
    SH2 = lambda sx: (Vector((0.62, 0.38, 1.3 + 0.03 * sx)), Vector((-0.2 + 0.05 * sx, -0.85, 0.45)).normalized(), Vector((0, 0, 1)), 0.05, -0.65)
    T1 = tw(M, 1)
    RD = Vector((0.0, 0.1, -1)).normalized()
    restW = head_on_ground(J, T1 @ Vector((0.2, 1.05, 0)), RD, Vector((0, 1, 0.1)))
    keys = [(1, "W", restW, RD, Vector((0, 1, 0.1)), -0.55, -0.9), (31, "W", restW, RD, Vector((0, 1, 0.1)), -0.55, -0.9), (36, "T", *SH)]
    for i in range(4):
        keys.append((36 + i * 10 + 5, "T", *SH2(1 if i % 2 == 0 else -1)))
    keys += [(76, "T", *SH), (78, "T", Vector((0.1, 0.25, 1.55)), Vector((0, -0.2, 1)).normalized(), Vector((0, 1, 0.2)), 0.05, -0.6)]
    imp = impact(M, 81, 2.55, 14, 0.1, sR=0.05, sL=-0.6)
    keys += [imp, (87,) + imp[1:], (94, "T", *SH)]
    keys += [(96, "T", *SH), (99, "T", Vector((0.05, -0.1, 1.55)), Vector((0, -1, 0.6)).normalized(), Vector((0, 0.3, 1)), 0.05, -0.55)]
    # flight in world space, frames 100-108, end over end about X, landing face first
    rel = (100, "T", Vector((0.0, 0.7, 1.9)), Vector((0, 0.6, 1)).normalized(), Vector((0, 1, -0.6)), 0.05, -0.55)   # release
    lp, ld, ln_ = impact_pose(M, 108, 4.4, 30, 0.0, 0.0)
    land = (108, "W", lp, ld, ln_, 0.05, -0.55)
    T100 = tw(M, 100); q100 = T100.to_3x3().normalized().to_quaternion()
    p0 = T100 @ rel[2]; d0 = q100 @ rel[3]; n0 = q100 @ rel[4]
    qa = hq(d0, n0); qb = hq(land[3], land[4])
    keys.append((100, "W", p0, d0, n0, 0.05, -0.55))
    ang = 2 * math.pi
    for f in range(101, 108):
        u = (f - 100) / 8
        q = Quaternion((1, 0, 0), ang * u) @ qa.slerp(qb, u)
        p = p0.lerp(land[2], u) + Vector((0, 0, 1.6 * 4 * u * (1 - u)))
        keys.append((f, "W", p, q @ Vector((0, 0, 1)), q @ Vector((0, 1, 0)), 0.05, -0.55))
    keys += [land, (113,) + land[1:]]
    T116 = tw(M, 116); q116 = T116.to_3x3().normalized().to_quaternion()
    keys.append((116, "W", T116 @ Vector((0.4, 2.3, 1.6)), q116 @ Vector((0, -0.4, 1)).normalized(), q116 @ Vector((0, 1, 0.4)), 0.05, -0.6))
    keys += [(119, "T", *SH), (130, "T", *SH)]
    drive_hammer(M, keys, free=((100, 118),))
    h = head_world(M, 81)
    cracks(M.tag, (h.x, h.y, 0.01), 81, 8, 2.6); ring_fx(f"{M.tag} smash ring", (h.x, h.y, 0.04), 81, 0.6, 6.0, 9)
    h = head_world(M, 108)
    cracks(M.tag + " land", (h.x, h.y, 0.01), 108, 7, 2.2); ring_fx(f"{M.tag} land ring", (h.x, h.y, 0.04), 108, 0.6, 5.5, 9)
    hex_ring(f"{M.tag} land hex", (h.x, h.y, 0.06), 110, 0.4, 3.5, 7)
    J["rest_head"] = head_world(M, 12)


def form_MCc2(M, J, src):
    """Pushed up out of the floor: a hex pad glows, then every plate rises from under the ground into place, lowest
    first, the maul last, standing on its head."""
    bpy.context.view_layer.update()
    pad = hex_ring(f"{M.tag} rise pad", tuple(J["root"].matrix_world.translation + Vector((0, 0, 0.04))), 2, 1.6, 1.3, 20)
    parts = mparts(J); zs = [(o, centre(o)) for o in parts]; top = max(c.z for _, c in zs) + 1e-6
    for o, c in zs:
        hm_ = "hammer" in o.name
        fa = int(rng.integers(17, 21)) if hm_ else int(4 + c.z / top * 13) + int(rng.integers(0, 2))
        l0 = Vector(o.location); P3i = o.parent.matrix_world.to_3x3().inverted()
        down = l0 + P3i @ Vector((0, 0, -(c.z + 0.6)))
        key(o, 1, loc=tuple(down), sc=0.0001); key(o, fa - 4, loc=tuple(down), sc=0.0001); key(o, fa - 3, loc=tuple(down), sc=1.0)
        key(o, fa, loc=tuple(l0 + P3i @ Vector((0, 0, 0.06)))); key(o, fa + 1, loc=tuple(l0))


# ================================================================== MCc3 Earthshaker
def build_MCc3(tag, T):
    J = {"hz": 1.9}
    root, hips, torso = mcc_body(tag, T, J, 1.9, 1.32, 1.2, 0.85, 0.95, 1.05)
    for i in range(9):                                           # hanging hex chain strips
        x = -0.8 + i * 0.2
        st = empty(f"{tag} strip pivot {i}", (x, 0.44 - 0.1 * abs(x), -0.2), hips)
        for k in range(3):
            cyl(f"{tag} chain hex {i} {k}", 0.08, 0.16, T if (i + k) % 2 else RM, 6, st, loc=(0, 0, -0.2 - k * 0.19))
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.5, 0.82, 0.82)
        plate(f"{tag} thigh {sx}", (-0.28, -0.28, -0.82), (0.28, 0.28, 0.0), T, hip)
        plate(f"{tag} knee cop {sx}", (-0.3, 0.12, -0.18), (0.3, 0.36, 0.2), RM, knee, 0.04)
        plate(f"{tag} greave {sx}", (-0.28, -0.28, -0.82), (0.28, 0.3, 0.0), T, knee)
        plate(f"{tag} boot {sx}", (-0.36, -0.42, -0.3), (0.36, 0.58, 0.0), T, ankle, 0.05)
        legs.append((hip, knee, ankle, sx))
    plate(f"{tag} roof", (-1.15, -0.68, 1.38), (1.15, 0.62, 1.58), T, torso, 0.06)
    head = empty(f"{tag} helm", (0, 0.0, 1.55), torso); J["head"] = head
    plate(f"{tag} crown helm", (-0.7, -0.5, 0.0), (0.7, 0.5, 0.35), T, head, 0.06)
    for k, xx in enumerate((-0.55, -0.2, 0.2, 0.55)):            # a crown of four horns, straight up, raked
        hn = cyl(f"{tag} crown horn {k}", 0.12, 0.6 if k in (0, 3) else 0.45, RM if k in (1, 2) else T, 8, head, loc=(xx, -0.05, 0.3), r2=0.0)
        hn.rotation_euler = (R(-15), R(xx * 30), 0)
    for sx in (-1, 1):
        sh = J["arms"][0 if sx < 0 else 1][0]
        for k in range(2):
            plate(f"{tag} pauldron {sx} {k}", (-0.5 + k * 0.08, -0.52 + k * 0.08, -0.1 + k * 0.25), (0.5 - k * 0.08, 0.52 - k * 0.08, 0.25 + k * 0.25), T if k == 0 else RM, sh, 0.06)
    make_hammer(tag, torso, J, 0.75, 1.15, "block", T)
    J["legs"] = legs
    return J


def anim_MCc3(M):
    J = M.J; hz = J["hz"]; bx = M.bx
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    # 36-76: a charging run: five fast strides, leaning in, the block hammer held low across the body
    for i in range(5):
        f0 = 36 + i * 8; sx = 1 if i % 2 == 0 else -1
        M.leg(f0, sx, -15, -5); M.leg(f0 + 4, sx, 50, -80, 25); M.leg(f0 + 8, sx, 20, -10)
        M.leg(f0, -sx, 20, -10); M.leg(f0 + 4, -sx, -20, -15); M.leg(f0 + 8, -sx, -15, -5)
        M.hips(f0, hz - 0.1, 16); M.hips(f0 + 4, hz + 0.12, 16, 0, -6 * sx); M.hips(f0 + 8, hz - 0.1, 16)
        M.root(f0 + 8, (i + 1) * 0.72)
    y = 3.6
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0)
    M.hips(76, hz)
    # 76-96: double tap: overhead, face first; it bounces up and steps in for a second blow further ahead
    M.torso(78, -10); M.torso(80, 32); M.torso(82, 10); M.torso(85, 34); M.torso(89, 32); M.torso(96)
    M.hips(78, hz + 0.08); M.hips(80, hz - 0.4); M.hips(82, hz - 0.1); M.hips(85, hz - 0.42); M.hips(89, hz - 0.4); M.hips(96, hz)
    M.root(82, y); M.root(85, y + 0.6); M.root(96, y + 0.6)
    for sx in (-1, 1):
        M.leg(80, sx, 25, -45, 20); M.leg(82, sx, 5 * sx, -10); M.leg(85, sx, 30, -50, 20); M.leg(89, sx, 30, -50, 20); M.leg(96, sx, 0, 0)
    y2 = y + 0.6
    # 96-126: the fissure: one more lift, down to one knee, the slam, and hex pillars burst up in a line ahead
    M.torso(99, -14); M.torso(103, 40); M.torso(116, 38); M.torso(124)
    M.hips(99, hz + 0.1); M.hips(103, hz - 0.75); M.hips(116, hz - 0.72); M.hips(124, hz)
    M.leg(99, 1, 0, 0); M.leg(99, -1, 0, 0)
    M.leg(103, 1, 80, -100, 20); M.leg(103, -1, -15, -110, 35); M.leg(116, 1, 80, -100, 20); M.leg(116, -1, -15, -110, 35)
    M.leg(124, 1, 0, 0); M.leg(124, -1, 0, 0)

    LOW = (Vector((0.0, 0.8, 0.35)), Vector((-0.7, 0.35, 0.5)).normalized(), Vector((0.3, 1, 0)), 0.3, -0.3)
    LOWs = lambda sx: (Vector((0.04 * sx, 0.82, 0.38)), Vector((-0.7 + 0.08 * sx, 0.35, 0.5)).normalized(), Vector((0.3, 1, 0)), 0.3, -0.3)
    keys = [(1, "T", *LOW), (36, "T", *LOW)]                   # gathers straight into its hands, held low
    for i in range(5):
        keys.append((36 + i * 8 + 4, "T", *LOWs(1 if i % 2 == 0 else -1)))
    OVER = (Vector((0, 0.3, 1.4)), Vector((0, -0.5, 1)).normalized(), Vector((0, 1, 0.5)), 0.25, -0.25)
    a1 = impact(M, 80, 1.95, 14, sR=0.25, sL=-0.25)
    a2 = impact(M, 85, 2.0, 14, sR=0.25, sL=-0.25)
    keys += [(76, "T", *LOW), (78, "T", *OVER), a1, (82, "T", Vector((0, 0.8, 1.0)), Vector((0, 0.5, 1)).normalized(), Vector((0, 1, -0.5)), 0.25, -0.25),
             a2, (89,) + a2[1:], (95, "T", *LOW), (99, "T", *OVER)]
    a3 = impact(M, 103, 1.75, 16, sR=0.25, sL=-0.25)
    keys += [a3, (116,) + a3[1:], (124, "T", *LOW), (130, "T", *LOW)]
    drive_hammer(M, keys)
    for f in (80, 85):
        h = head_world(M, f)
        cracks(f"{M.tag} tap {f}", (h.x, h.y, 0.01), f, 6, 2.0); ring_fx(f"{M.tag} tap ring {f}", (h.x, h.y, 0.04), f, 0.5, 4.5, 8)
    h = head_world(M, 103)
    hex_ring(f"{M.tag} slam hex", (h.x, h.y, 0.05), 103, 0.6, 5.0, 9)
    for k in range(8):                                           # the fissure: hex pillars erupting in a line ahead
        f = 104 + k
        px, py = h.x + rng.uniform(-0.25, 0.25), h.y + 0.6 + k * 0.62
        ht = 0.7 + k * 0.14
        pl = cyl(f"{M.tag} fissure pillar {k}", 0.32 - k * 0.012, ht, PILLAR_H1, 6, None, loc=(px, py, 0.0), r2=0.22)
        pl.rotation_euler = (R(rng.uniform(-8, 8)), R(rng.uniform(-8, 8)), R(rng.uniform(0, 60)))
        cap = cyl(f"{M.tag} fissure cap {k}", 0.24, 0.05, W, 6, pl, loc=(0, 0, ht), r2=0.2)
        key(pl, 1, sc=(1, 1, 0.0001)); key(pl, f - 1, sc=(1, 1, 0.0001)); key(pl, f + 1, sc=(1, 1, 1.15)); key(pl, f + 3, sc=(1, 1, 1.0))
        key(pl, 117, sc=(1, 1, 1.0)); key(pl, 123, sc=(1, 1, 0.0001))
        cracks(f"{M.tag} fissure {k}", (px, py, 0.01), f, 4, 0.9)
    J["rest_head"] = head_world(M, 12)


def form_MCc3(M, J, src):
    """Shatter in reverse: shards lying scattered round the mech leap up and fly together, each part appearing where
    its shards meet, in no set order; the hammer gathers last."""
    bpy.context.view_layer.update()
    pm = pixel_mesh(CM["pix"]); c0 = J["root"].matrix_world.translation
    for o in mparts(J):
        hm_ = "hammer" in o.name
        fa = int(rng.integers(17, 21)) if hm_ else int(rng.integers(5, 17))
        c = centre(o); sc0 = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 1, sc=tuple(v * 1.1 for v in sc0)); key(o, fa + 2, sc=sc0)
        for _ in range(2):
            a = rng.uniform(0, 2 * math.pi); r_ = rng.uniform(1.5, 3.2)
            s0 = Vector((c0.x + r_ * math.cos(a), c0.y + r_ * math.sin(a), 0.04))
            px = link(bpy.data.objects.new(f"{M.tag} gather shard", pm))
            fs = max(2, fa - 6)
            key(px, 1, loc=s0, sc=1.0); key(px, fs, loc=s0, sc=1.0)
            key(px, fs + 3, loc=(s0 + c) / 2 + Vector((0, 0, 0.8)), sc=1.2); key(px, fa, loc=c, sc=0.8); key(px, fa + 1, loc=c, sc=0.0001)


# ------------------------------------------------------------------ build the six takes
T_R1 = TEX["r1"]
WALL_H1 = strip_mat("M3 wall texture", strip_image("green", "h1"), 6, emit=0.9, alpha=0.8)
PILLAR_H1 = strip_mat("M3 pillar texture", strip_image("green", "h1"), 6, emit=1.0, alpha=0.9)
TAKES = [("MCb1", "Hover Tank", "r1", "villager", build_MCb1, anim_MCb1, form_MCb1, 106),
         ("MCb2", "Jump Jet", "r1", "villager", build_MCb2, anim_MCb2, form_MCb2, 109),
         ("MCb3", "Orbit Juggernaut", "r1", "villager", build_MCb3, anim_MCb3, form_MCb3, 85),
         ("MCc1", "Anvil Breaker", "h1", "zombie", build_MCc1, anim_MCc1, form_MCc1, 110),
         ("MCc2", "Ram Breaker", "h1", "zombie", build_MCc2, anim_MCc2, form_MCc2, 82),
         ("MCc3", "Earthshaker", "h1", "zombie", build_MCc3, anim_MCc3, form_MCc3, 106)]
for bi, (tk, name, look, pk, bf, af, ff, peak) in enumerate(TAKES):
    bx = bi * BAY + (18.0 if bi >= 3 else 0.0)
    tag = f"M3 {tk}"
    box(f"{tag} floor", (bx - 5, -5, -0.02), (bx + 5, 14, 0), FLOOR)
    J = bf(tag, TEX[look])
    J["root"].location = (bx, 0, 0)
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
    cam(f"Cam {tk}", (bx + 6.5, 13.5, 4.4), (bx, 3.0, 1.9), 28)
    cam(f"Cam {tk} close", (bx + 3.0, 9.5, 3.4), (bx, 3.0, 2.2), 30)
    label(f"{tk}  {name}  - pilot: {pk}", (bx, -3.5, 5.2), LBL, 0.32, rot=(R(90), 0, R(180)))
    print(tk, "built", flush=True)
cam("Cam row MCb", (BAY, 42, 10), (BAY, 3, 2.0), 30)
cam("Cam row MCc", (5 * BAY + 18.0 - 18.0, 42, 10), (5 * BAY, 3, 2.0), 30)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam MCb1", 1, (0.35, 0.45, 0.6), 3.0



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

