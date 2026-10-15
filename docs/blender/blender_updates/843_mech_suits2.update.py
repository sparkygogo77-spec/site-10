# Pass 843: mech suits, MA and MC variations (rings/suits chat, 2026-10-15, range 800-899). Follows 821.
# J rated 821 MA Titan frame and MC Juggernaut IMPROVE with no note: "3 new variations each", labelled, he picks.
# His MS note ("Different texture, more detailed designs for the robots") is not this pass, but it is what he values:
# more detail and better textures, so every take here has layered plates, joints, pistons or fingers, and its own look.
# J on 810 G5: "mech suit needs a few design iterations as a big robotic suit, do one other size and a few animations
# for it, this may be a feature i can give to a villager or any kind of mob potentially". MB dropped; MS is its own round.
# Every take is built a different way (shape, how it forms, how it moves). Same clock for all (20 ticks a second):
#   1-24 form, 24-30 board, 30-35 seal, 36-76 move, 76-96 attack, 96-126 finisher, 130 end.
#   MAa Plated Titan (BR1, villager; rev 2): a dark inner frame with bevel-layered brick plates over it, a sensor head, a
#       chest reactor, back exhausts, four-finger hands. Forms frame first, then the plates fly in and lock on.
#       Rev 2, J: "Give this bot the hammer and make it for the villagers": a villager pilot and a two-handed construct
#       war hammer (a solid 3D block, both fists on the haft). The head lands planted in front, the haft grows up into
#       its fists; it hefts it (no wind-up) and walks with it at port arms; attack: a fast side swing and backhand, a face
#       leading; finisher: overhead smash, the head lands face first, cracks and a ring.
#   MAb Exo Frame (V1 crystal, player standing): an open exoskeleton the pilot stands inside, a halo over the head,
#       crystal armour on struts, three-finger hands; the pilot's limbs move with the mech's. Forms as struts tracing
#       out from the ring, then the crystal plates grow on. Brisk six-step walk; left hook + right uppercut; a forward
#       leap to a one-knee landing, fist to the ground.
#   MAc Dome Titan (R2 fragments, villager): round build: a barrel body with a glass dome cockpit, ball joints, capsule
#       limbs, elephant feet, a blade on the right arm and a round shield on the left. Blooms out from the core.
#       Waddle walk; a blade slash edge-first with an arc trail; a shield slam that throws up a dome shockwave.
#   MCa Siege Ape (W1 weave, zombie): hunched, short legs, very long arms on stacked pauldrons, block fists, back
#       thrusters, hoses. A scan ring rises and builds it slice by slice. Knuckle-walks; rears up for a two-fist
#       smash; a thruster leap that lands on its fists.
#   MCb Rocket Juggernaut (R1 cells in green, villager): stubby legs on hover pads, a four-nozzle booster pack with fins,
#       big gauntlets with rocket fists. Assembles from parts that fly in from all round and spin into place. Hovers
#       and glides instead of walking; a rocket punch (the fist flies out on a tether and comes back); a spinning
#       boost jump and slam.
#   MCc Breaker (H1 hex, zombie): a horned helm, spiked pauldrons, a layered plate skirt, a slit visor, and a big
#       two-handed war hammer. Rains together from the top down, the hammer last. Plods with the hammer dragging; an
#       overhead smash with the hammer face leading; a 360 spin sweep.
# Cameras "Cam <take>" (front three-quarter), "Cam <take> close", "Cam row MA", "Cam row MC".
# Builds LanternLive\constructs\mech_suits2.blend.
SCENE_NAME = "Mech Suits 2"
OUT_REL = "constructs/mech_suits2.blend"
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
BAY = 18.0                                     # takes 18 m apart along X; the MC row starts at x = 72
FLOOR = mat("M2 floor", (0.2, 0.22, 0.2), rough=0.9)
LBL = mat("M2 label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(843)
CM = cmats("M2", "green")
RM, W, GR, GL = CM["rim"], CM["glow"], CM["grip"], CM["glass"]
FRAME = mat("M2 dark frame", (0.02, 0.12, 0.05), emit=0.35, alpha=0.9, rough=0.25)      # inner skeleton, darker
SHOCK = mat("M2 shock glass", (0.06, 0.5, 0.15), emit=1.2, alpha=0.35, rough=0.1)
TEX = {k: strip_mat(f"M2 {k} texture", strip_image("green", k), 5, emit=1.2, alpha=0.92)
       for k in ("br1", "v1", "r2", "w1", "r1", "h1")}
ROBE = mat("M2 villager robe", (0.35, 0.22, 0.12), rough=0.9)
VSKIN = mat("M2 villager skin", (0.72, 0.52, 0.4), rough=0.8)
ZSKIN = mat("M2 zombie skin", (0.3, 0.5, 0.3), rough=0.8)
ZSHIRT = mat("M2 zombie shirt", (0.1, 0.45, 0.5), rough=0.8)
BROW = mat("M2 brow", (0.15, 0.1, 0.05))


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


# ------------------------------------------------------------------ MAa Plated Titan
def build_MAa(tag, T):
    J = {"hz": 2.0}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.15), hips); J["torso"] = torso
    frame, plates = [], []
    F = lambda nm, a, c, par: frame.append(plate(f"{tag} {nm}", a, c, FRAME, par, 0.02)) or frame[-1]
    Pl = lambda nm, a, c, par, m=T, w=0.04: plates.append(plate(f"{tag} {nm}", a, c, m, par, w)) or plates[-1]
    F("pelvis frame", (-0.5, -0.32, -0.25), (0.5, 0.32, 0.15), hips)
    Pl("belt plate", (-0.62, -0.42, -0.2), (0.62, 0.42, 0.05), hips)
    for sx in (-1, 1):
        Pl(f"hip guard {sx}", (sx * 0.5 - 0.18, -0.4, -0.55), (sx * 0.5 + 0.18, 0.42, -0.05), hips)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.45, 0.85, 0.85)
        F(f"thigh bone {sx}", (-0.12, -0.12, -0.85), (0.12, 0.12, 0.0), hip)
        Pl(f"thigh plate {sx}", (-0.24, -0.08, -0.75), (0.24, 0.26, -0.1), hip)
        Pl(f"thigh back {sx}", (-0.2, -0.26, -0.7), (0.2, -0.1, -0.15), hip)
        cyl(f"{tag} knee joint {sx}", 0.15, 0.36, FRAME, 12, knee, loc=(-0.18, 0, 0), axis="X")
        Pl(f"knee cop {sx}", (-0.22, 0.12, -0.15), (0.22, 0.32, 0.18), knee, RM, 0.03)
        F(f"shin bone {sx}", (-0.11, -0.11, -0.85), (0.11, 0.11, 0.0), knee)
        Pl(f"shin plate {sx}", (-0.23, -0.02, -0.72), (0.23, 0.27, -0.12), knee)
        Pl(f"calf {sx}", (-0.21, -0.3, -0.75), (0.21, -0.02, -0.2), knee)
        cyl(f"{tag} piston {sx}", 0.045, 0.6, W, 8, knee, loc=(0, -0.33, -0.75))
        Pl(f"foot {sx}", (-0.3, -0.38, -0.3), (0.3, 0.5, 0.0), ankle)
        Pl(f"toe cap {sx}", (-0.27, 0.5, -0.27), (0.27, 0.68, -0.05), ankle, RM, 0.03)
        Pl(f"heel {sx}", (-0.22, -0.5, -0.27), (0.22, -0.38, -0.08), ankle)
        legs.append((hip, knee, ankle, sx))
    # torso: a frame cage with layered plates; the cockpit is the open front
    F("spine", (-0.25, -0.55, 0.0), (0.25, -0.35, 1.45), torso)
    F("chest floor", (-0.8, -0.5, -0.05), (0.8, 0.5, 0.1), torso)
    Pl("back plate", (-0.85, -0.62, 0.05), (0.85, -0.42, 1.4), torso)
    for sx in (-1, 1):
        Pl(f"side plate {sx}", (sx * 0.85 - 0.14, -0.55, 0.05), (sx * 0.85 + 0.14, 0.48, 1.35), torso)
        Pl(f"rib {sx} a", (sx * 0.85 - 0.18, 0.0, 0.3), (sx * 0.85 + 0.18, 0.5, 0.45), torso, RM, 0.02)
        Pl(f"rib {sx} b", (sx * 0.85 - 0.18, 0.0, 0.7), (sx * 0.85 + 0.18, 0.5, 0.85), torso, RM, 0.02)
        Pl(f"exhaust {sx}", (sx * 0.45 - 0.13, -0.85, 0.9), (sx * 0.45 + 0.13, -0.6, 1.55), torso)
        b_ = box(f"{tag} exhaust glow {sx}", (sx * 0.45 - 0.08, -0.87, 1.5), (sx * 0.45 + 0.08, -0.62, 1.58), W, torso); plates.append(b_)
    Pl("roof", (-0.92, -0.62, 1.32), (0.92, 0.55, 1.52), torso)
    Pl("collar", (-0.5, -0.5, 1.5), (0.5, 0.3, 1.62), torso)
    reactor = cyl(f"{tag} reactor", 0.17, 0.08, W, 16, torso, loc=(0, -0.43, 0.75), axis="Y"); plates.append(reactor)
    torus(f"{tag} reactor ring", 0.2, 0.03, RM, loc=(0, -0.38, 0.75), parent=torso, axis="Y")
    head = empty(f"{tag} head", (0, -0.15, 1.62), torso); J["head"] = head
    Pl("sensor head", (-0.28, -0.25, 0.0), (0.28, 0.2, 0.34), head)
    b_ = box(f"{tag} sensor visor", (-0.22, 0.2, 0.14), (0.22, 0.24, 0.24), W, head); plates.append(b_)
    Pl("head fin", (-0.03, -0.3, 0.3), (0.03, 0.05, 0.5), head, RM, 0.01)
    hatch = empty(f"{tag} canopy hinge", (0, 0.5, 1.38), torso)
    plates.append(box(f"{tag} canopy", (-0.68, 0.0, -1.28), (0.68, 0.05, 0.0), GL, hatch))
    Pl("canopy frame top", (-0.72, -0.01, -0.12), (0.72, 0.09, 0.0), hatch, RM, 0.015)
    Pl("canopy frame bottom", (-0.72, -0.01, -1.3), (0.72, 0.09, -1.18), hatch, RM, 0.015)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    arms, hands = [], {}
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.18, 0, 1.15), torso)
        cyl(f"{tag} shoulder ball {sx}", 0.2, 0.3, FRAME, 12, sh, loc=(-0.15, 0, 0), axis="X")
        Pl(f"pauldron {sx}", (-0.34, -0.4, -0.05), (0.34, 0.4, 0.42), sh)
        Pl(f"pauldron lip {sx}", (-0.38, -0.44, 0.32), (0.38, 0.44, 0.48), sh, RM, 0.02)
        b_ = box(f"{tag} vent {sx}", (sx * 0.35 - 0.02, -0.25, 0.05), (sx * 0.35 + 0.02, 0.25, 0.3), W, sh); plates.append(b_)
        F(f"upper arm bone {sx}", (-0.11, -0.11, -0.75), (0.11, 0.11, -0.05), sh)
        Pl(f"bicep plate {sx}", (-0.2, -0.2, -0.65), (0.2, 0.2, -0.2), sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.75), sh)
        cyl(f"{tag} elbow joint {sx}", 0.13, 0.3, FRAME, 12, el, loc=(-0.15, 0, 0), axis="X")
        Pl(f"forearm {sx}", (-0.22, -0.22, -0.68), (0.22, 0.22, -0.05), el)
        Pl(f"forearm guard {sx}", (sx * 0.22 - 0.05, -0.2, -0.62), (sx * 0.22 + 0.04, 0.2, -0.1), el, RM, 0.015)
        hands[sx] = hand(f"{tag} hand {sx}", el, T, -0.68)
        arms.append((sh, el, sx))
    # rev 2 (J: "Give this bot the hammer and make it for the villagers"): a two-handed construct war hammer, a solid
    # 3D block (BR1, bevelled), parented to the torso; both fists are solved onto the haft every frame (MAa_ik below).
    # Hammer space: +Z along the haft toward the head, +Y/-Y the two striking faces, origin between the hands.
    hm = empty(f"{tag} hammer", (0, 0.9, 0.5), torso); hm.rotation_mode = "QUATERNION"
    grow = empty(f"{tag} hammer grow", (0, 0, 1.85), hm)            # the haft grows out of the head
    cyl(f"{tag} hammer haft", 0.075, 2.4, FRAME, 12, grow, loc=(0, 0, -2.7))
    for k, z in enumerate((-2.15, -1.55)):
        torus(f"{tag} hammer grip wrap {k}", 0.085, 0.022, RM, loc=(0, 0, z), parent=grow, n=16, k=6)
    plate(f"{tag} hammer pommel", (-0.13, -0.13, -2.88), (0.13, 0.13, -2.66), T, grow, 0.03)
    hp = empty(f"{tag} hammer head pivot", (0, 0, 1.85), hm)
    plate(f"{tag} hammer head", (-0.36, -0.52, -0.35), (0.36, 0.52, 0.35), T, hp, 0.07)
    for sy in (-1, 1):
        lo, hi = sorted((sy * 0.5, sy * 0.63))
        plate(f"{tag} hammer face {sy}", (-0.38, lo, -0.37), (0.38, hi, 0.37), T, hp, 0.04)
        lo, hi = sorted((sy * 0.63, sy * 0.645))
        box(f"{tag} hammer face glow {sy}", (-0.22, lo, -0.21), (0.22, hi, 0.21), W, hp)
    for sx in (-1, 1):
        lo, hi = sorted((sx * 0.35, sx * 0.42))
        plate(f"{tag} hammer cheek {sx}", (lo, -0.36, -0.24), (hi, 0.36, 0.24), FRAME, hp, 0.02)
    plate(f"{tag} hammer collar", (-0.17, -0.17, -0.5), (0.17, 0.17, -0.33), T, hp, 0.03)
    torus(f"{tag} hammer collar ring", 0.13, 0.025, RM, loc=(0, 0, -0.42), parent=hp, n=16, k=6)
    J.update(legs=legs, arms=arms, hands=hands, frame=frame, plates=plates, hammer=hm, hammer_grow=grow, hammer_head=hp)
    return J


FIST_MAa = Vector((0, 0.1, -0.92))                      # fist centre in the elbow's space


def MAa_fk(sx, prm):
    """Fist point (torso space) for shoulder Euler (a, b, c) and elbow bend e, in degrees."""
    Rs = Euler((R(prm[0]), R(prm[1]), R(prm[2])), "XYZ").to_matrix()
    Re = Euler((R(prm[3]), 0, 0), "XYZ").to_matrix()
    return Vector((sx * 1.18, 0, 1.15)) + Rs @ (Vector((0, 0, -0.75)) + Re @ FIST_MAa)


def MAa_ik(sx, target, prev, _retry=False):
    """Damped least squares, warm-started from the previous frame so the arms move continuously."""
    x = np.array(prev, float); t = np.array(target, float)
    lo = np.array([-120, -70, -100, 5]); hi = np.array([200, 70, 100, 150])
    for _ in range(200):
        f0 = np.array(MAa_fk(sx, x)) - t
        if np.linalg.norm(f0) < 1e-3:
            break
        Jm = np.zeros((3, 4))
        for i in range(4):
            dx = x.copy(); dx[i] += 0.2
            Jm[:, i] = (np.array(MAa_fk(sx, dx)) - t - f0) / 0.2
        A = Jm.T @ Jm + 1e-5 * np.eye(4)
        x = np.clip(x - np.linalg.solve(A, Jm.T @ f0), lo, hi)
    err = float(np.linalg.norm(np.array(MAa_fk(sx, x)) - t))
    if err > 0.02 and not _retry:                             # stuck: restart from a few seeds, keep the closest
        for seed in ([60, 0, sx * 30, 60], [100, 0, -sx * 30, 40], [30, sx * 40, 0, 90], [140, 0, 0, 30]):
            y_, e_ = MAa_ik(sx, target, seed, True)
            if e_ < err - 0.01:
                x, err = y_, e_
    return x, err


def MAa_q(d, n):
    """Hammer orientation from the haft direction d (+Z) and the leading face normal n (+Y)."""
    d = Vector(d).normalized(); n = Vector(n); n = (n - d * n.dot(d)).normalized()
    return Matrix((n.cross(d), n, d)).transposed().to_quaternion()


def MAa_swing_n(d):
    """Flat swing (about the vertical): the face that leads is z x d."""
    d = Vector(d).normalized()
    return Vector((-d.y, d.x, 0.0))


def anim_MAa(M):
    """rev 2: the villager's hammer mech. Rests on the planted hammer, hefts it (no wind-up), walks with it at port
    arms, a fast side swing and backhand (from the side, a face leading), then the overhead smash: the head lands face
    first, cracks and a ring, held, then back up."""
    J = M.J; hz = J["hz"]; hm = J["hammer"]; tor = J["torso"]
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0)
    M.fists(1, 0.3); M.fists(19, 0.3); M.fists(22, 1.0)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    # 36-76: four heavy steps, a hip roll and a shoulder sway into each one (the hammer rides at port arms)
    for i in range(4):
        f0 = 36 + i * 10; sx = 1 if i % 2 == 0 else -1
        M.leg(f0, sx, 0, 0); M.leg(f0 + 4, sx, 32, -50, 12); M.leg(f0 + 10, sx, 0, 0)
        M.leg(f0, -sx, 0, 0); M.leg(f0 + 5, -sx, -14, -5); M.leg(f0 + 10, -sx, 0, 0)
        M.root(f0 + 10, (i + 1) * 0.9)
        M.hips(f0, hz, 0, 0, 0); M.hips(f0 + 5, hz + 0.07, 0, 4 * sx, -5 * sx); M.hips(f0 + 10, hz - 0.08, 0, 0, 0)
        M.torso(f0 + 5, 0, -2 * sx, 6 * sx); M.torso(f0 + 10)
        ring_fx(f"{M.tag} step ring {i}", (M.bx + sx * 0.45, (i + 1) * 0.9 + 0.3, 0.04), f0 + 10, 0.35, 3.0, 6, th=0.03)
    y = 3.6
    M.hips(76, hz); M.torso(76)
    # 76-96: side swing right to left straight from the carry, then the backhand back; the torso uncoils into each
    M.torso(78, 0, 0, 14); M.torso(79, 0, 0, 26); M.torso(81, 0, 0, 34); M.torso(83, 0, 0, 12)
    M.torso(85, 0, 0, -22); M.torso(87, 0, 0, -30); M.torso(92); M.torso(96)
    M.leg(76, -1, 0, 0); M.leg(78, -1, 20, -24, 4); M.leg(87, -1, 20, -24, 4); M.leg(92, -1, 0, 0)
    M.hips(79, hz - 0.12); M.hips(82, hz - 0.04); M.hips(85, hz - 0.12); M.hips(92, hz)
    # 96-126: overhead smash: up in two ticks, down in three, face first into the ground, held, then back up
    M.hips(96, hz); M.hips(98, hz + 0.12); M.hips(101, hz - 0.85); M.hips(110, hz - 0.85); M.hips(118, hz - 0.1); M.hips(122, hz)
    M.torso(96); M.torso(98, -12); M.torso(101, 42); M.torso(110, 42); M.torso(118, 8); M.torso(122)
    for sx in (-1, 1):
        M.leg(96, sx, 0, 0); M.leg(98, sx, -4, 0); M.leg(101, sx, 60, -116, 56); M.leg(110, sx, 60, -116, 56)
        M.leg(118, sx, 10, -16, 6); M.leg(122, sx, 0, 0)
    M.root(126, y)

    # ---- the hammer's path (torso space): (frame, pivot, haft dir, face normal, right grip s, left grip s)
    REST_D = Vector((0, 0.12, -1)).normalized()
    rest_pz = 0.4 - (hz + 0.15) + 1.85 * abs(REST_D.z)                   # head resting on the ground
    REST = (Vector((0, 0.95, rest_pz)), REST_D, Vector((0, 1, 0.12)), -0.3, -0.75)
    CD = Vector((0.5, 0.12, 1)).normalized()
    CARRY = (Vector((-0.02, 0.8, 0.62)), CD, Vector((0, 1, 0)), 0.3, -0.3)
    SWAY = lambda sx: (Vector((-0.02 + 0.04 * sx, 0.82, 0.65)), Vector((0.5 + 0.08 * sx, 0.2, 1)).normalized(), Vector((0, 1, 0)), 0.3, -0.3)

    def flat(p, d, sR=0.3, sL=-0.3):
        d = Vector(d).normalized()
        return (Vector(p), d, MAa_swing_n(d), sR, sL)

    def over(p, d, sR=0.3, sL=-0.3):
        d = Vector(d).normalized()
        return (Vector(p), d, Vector((0, d.z, -d.y)), sR, sL)

    keys = [(1, REST), (31, REST), (33, (Vector((0.05, 0.75, 0.3)), Vector((1, 0.3, -0.1)).normalized(), Vector((0, 1, 0)), 0.0, -0.4)), (36, CARRY)]
    for i in range(4):
        keys += [(36 + i * 10 + 5, SWAY(1 if i % 2 == 0 else -1)), (36 + i * 10 + 10, CARRY)]
    keys += [(78, flat((0.1, 0.78, 0.5), (0.7, 1, 0.12), 0.05, -0.35)), (79, flat((0.0, 0.8, 0.5), (0.0, 1, 0.04), 0.05, -0.35)),
             (81, flat((-0.1, 0.75, 0.5), (-0.6, 1, 0.1), 0.05, -0.35)), (83, flat((-0.05, 0.78, 0.5), (-0.35, 1, 0.08), 0.05, -0.35)),
             (85, flat((0.05, 0.8, 0.5), (0.25, 1, 0.04), 0.05, -0.35)), (87, flat((0.12, 0.76, 0.5), (0.65, 1, 0.12), 0.05, -0.35)),
             (92, CARRY), (96, CARRY), (98, over((0.0, 0.4, 1.4), (0, -0.3, 1), 0.15, -0.25))]
    # the impact pose is set in world space: haft 12 degrees below level, the lower face flat on the ground
    scene.frame_set(101); bpy.context.view_layer.update()
    TW = tor.matrix_world.copy(); TWi = TW.inverted(); T3i = TW.to_3x3().inverted()
    sh_mid = TW @ Vector((0, 0, 1.15))
    dW = Vector((0, math.cos(R(12)), -math.sin(R(12))))
    nW = Vector((0, -math.sin(R(12)), -math.cos(R(12))))
    headW = Vector((M.bx, sh_mid.y + 0.3 + 1.85 * dW.y, 0.0))
    headW.z = 0.66 * math.cos(R(12)) + 0.37 * math.sin(R(12)) + 0.01
    pivW = headW - dW * 1.85
    IMP = ((TWi @ pivW), (T3i @ dW).normalized(), (T3i @ nW).normalized(), 0.15, -0.3)
    keys += [(101, IMP), (110, IMP), (116, over((0.0, 0.95, 0.6), (0.3, 0.5, 1))), (122, CARRY), (130, CARRY)]
    poses = [(f, P_, MAa_q(d, n), sR, sL) for f, (P_, d, n, sR, sL) in keys]

    def at(f):
        for (f0, p0, q0, r0, l0), (f1, p1, q1, r1, l1) in zip(poses, poses[1:]):
            if f0 <= f <= f1:
                t = smooth((f - f0) / max(1, f1 - f0))
                if q0.dot(q1) < 0:
                    q1 = -q1
                return p0.lerp(p1, t), q0.slerp(q1, t), r0 + (r1 - r0) * t, l0 + (l1 - l0) * t
        f_, p_, q_, r_, l_ = poses[-1]
        return p_, q_, r_, l_

    prev = {1: [30, 0, 30, 60], -1: [30, 0, -30, 60]}
    worst = 0.0; qp = None
    for f in range(1, FRAME_END + 1):
        p_, q_, sR, sL = at(f)
        if qp is not None and qp.dot(q_) < 0:
            q_ = -q_
        qp = q_
        hm.location = p_; hm.rotation_quaternion = q_
        hm.keyframe_insert("location", frame=f); hm.keyframe_insert("rotation_quaternion", frame=f)
        for sx, s_ in ((1, sR), (-1, sL)):
            tgt = p_ + q_ @ Vector((0, 0, s_))
            x, err = MAa_ik(sx, tgt, prev[sx]); prev[sx] = list(x)
            if f > 14:
                worst = max(worst, err)
            for sh, el, sx_ in J["arms"]:
                if sx_ == sx:
                    key(sh, f, rot=(R(x[0]), R(x[1]), R(x[2]))); key(el, f, rot=(R(x[3]), 0, 0))
    for fc in (hm.animation_data.action.fcurves if hasattr(hm.animation_data.action, "fcurves") else []):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    print(M.tag, "hammer grip worst miss %.3f m" % worst, flush=True)
    # impacts: where the head really is
    hp = J["hammer_head"]

    def head_at(f):
        scene.frame_set(f); bpy.context.view_layer.update()
        return hp.matrix_world.translation.copy()
    for f in (79, 85):
        h = head_at(f)
        ring_fx(f"{M.tag} swing ring {f}", tuple(h), f, 0.3, 3.2, 6, axis="X", th=0.03)
    h = head_at(101)
    cracks(M.tag, (h.x, h.y, 0.01), 101, 8, 2.6)
    ring_fx(f"{M.tag} smash ring", (h.x, h.y, 0.04), 101, 0.7, 6.5, 10)
    ring_fx(f"{M.tag} smash ring 2", (h.x, h.y, 0.06), 103, 0.5, 4.0, 8, th=0.03)
    J["head_rest"] = head_at(17)
    scene.frame_set(1)


def form_MAa(M, J, src):
    """Frame first (feet up, pixels from the ring), then the plates fly in from outside and lock on; the hammer head
    lands planted in front, then the haft grows up out of it into the fists."""
    form_in(J["frame"], 2, 13, src, CM["pix"], rng, M.tag, 2, 0.6)
    bpy.context.view_layer.update()
    centre = J["torso"].matrix_world.translation
    others = [o for o in mparts(J) if o not in J["frame"] and o not in J["plates"] and " hammer" not in o.name]
    for o in J["plates"] + others:
        c = o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))
        d = (c - centre); d.z *= 0.4
        d = d.normalized() * 1.4 if d.length > 1e-3 else Vector((0, 0, 1.4))
        l0 = Vector(o.location); off = l0 + o.parent.matrix_world.to_3x3().inverted() @ d
        fa = 12 + int((c.z / 4.0) * 9) + int(rng.integers(0, 3))
        key(o, 1, loc=tuple(off), sc=0.0001); key(o, fa - 5, loc=tuple(off), sc=0.0001)
        key(o, fa - 4, loc=tuple(off), sc=1.0); key(o, fa, loc=tuple(l0), sc=1.0)
    hp, gr = J["hammer_head"], J["hammer_grow"]
    key(hp, 1, sc=0.0001); key(hp, 15, sc=0.0001); key(hp, 17, sc=1.15); key(hp, 19, sc=1.0)
    key(gr, 1, sc=(1, 1, 0.0001)); key(gr, 18, sc=(1, 1, 0.0001)); key(gr, 22, sc=(1, 1, 1))
    h = J.get("head_rest")
    if h is not None:
        ring_fx(f"{M.tag} hammer land ring", (h.x, h.y, 0.04), 17, 0.5, 4.0, 7, th=0.03)


# ------------------------------------------------------------------ MAb Exo Frame (pilot stands inside, arms mirrored)
def build_MAb(tag, T):
    J = {"hz": 1.75}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.1), hips); J["torso"] = torso
    struts, crystals = [], []
    S_ = lambda nm, a, c, par: struts.append(plate(f"{tag} {nm}", a, c, FRAME, par, 0.015)) or struts[-1]
    C_ = lambda nm, a, c, par, m=T: crystals.append(plate(f"{tag} {nm}", a, c, m, par, 0.05)) or crystals[-1]
    S_("hip bar", (-0.55, -0.1, -0.12), (0.55, 0.1, 0.05), hips)
    C_("hip crystal", (-0.3, -0.25, -0.3), (0.3, -0.05, 0.05), hips)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.5, 0.78, 0.75)
        S_(f"thigh strut {sx} a", (-0.05, -0.12, -0.78), (0.05, -0.04, 0.0), hip)
        S_(f"thigh strut {sx} b", (-0.05, 0.04, -0.78), (0.05, 0.12, 0.0), hip)
        C_(f"thigh crystal {sx}", (-0.17, 0.1, -0.6), (0.17, 0.3, -0.12), hip)
        torus(f"{tag} knee ring {sx}", 0.13, 0.035, RM, loc=(0, 0, 0), parent=knee, axis="X")
        S_(f"shin strut {sx}", (-0.06, -0.06, -0.75), (0.06, 0.06, 0.0), knee)
        C_(f"shin crystal {sx}", (-0.15, 0.04, -0.65), (0.15, 0.24, -0.1), knee)
        cyl(f"{tag} shin spring {sx}", 0.035, 0.55, W, 8, knee, loc=(0, -0.15, -0.68))
        S_(f"foot frame {sx}", (-0.22, -0.3, -0.2), (0.22, 0.45, -0.1), ankle)
        for k, xx in enumerate((-0.16, 0.0, 0.16)):
            C_(f"toe claw {sx} {k}", (xx - 0.05, 0.4, -0.22), (xx + 0.05, 0.65, -0.12), ankle, RM)
        C_(f"heel spur {sx}", (-0.05, -0.5, -0.22), (0.05, -0.3, -0.12), ankle, RM)
        legs.append((hip, knee, ankle, sx))
    # an open cage: the pilot stands on the chest plate, the frame rises round him
    S_("stand plate", (-0.45, -0.35, -0.04), (0.45, 0.35, 0.06), torso)
    for sx in (-1, 1):
        for sy in (-1, 1):
            S_(f"cage post {sx} {sy}", (sx * 0.55 - 0.04, sy * 0.35 - 0.04, 0.0), (sx * 0.55 + 0.04, sy * 0.35 + 0.04, 2.2), torso)
        S_(f"cage rail {sx}", (sx * 0.55 - 0.04, -0.38, 1.1), (sx * 0.55 + 0.04, 0.38, 1.18), torso)
        C_(f"flank crystal {sx}", (sx * 0.62 - 0.08, -0.3, 0.2), (sx * 0.62 + 0.08, 0.3, 0.95), torso)
    S_("spine bar", (-0.06, -0.45, 0.0), (0.06, -0.37, 2.25), torso)
    C_("back crystal", (-0.4, -0.55, 0.4), (0.4, -0.42, 1.6), torso)
    S_("top bar", (-0.6, -0.4, 2.2), (0.6, 0.4, 2.27), torso)
    halo = torus(f"{tag} halo", 0.3, 0.03, W, loc=(0, 0, 2.5), parent=torso); crystals.append(halo)
    hatch = empty(f"{tag} chest guard hinge", (0, 0.4, 0.95), torso)
    C_("chest guard", (-0.45, 0.0, -0.75), (0.45, 0.06, 0.0), hatch, GL)
    J["hatch"] = hatch; J["hatch_open"] = (R(170), 0, 0); J["seat"] = (0, -0.05, 0.06)
    arms, hands = [], {}
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 0.85, 0, 1.55), torso)
        torus(f"{tag} shoulder ring {sx}", 0.16, 0.035, RM, parent=sh, axis="X")
        C_(f"shoulder crystal {sx}", (-0.22, -0.28, 0.05), (0.22, 0.28, 0.4), sh)
        S_(f"upper strut {sx}", (-0.05, -0.05, -0.85), (0.05, 0.05, 0.0), sh)
        C_(f"upper crystal {sx}", (sx * 0.05, -0.14, -0.7), (sx * 0.2, 0.14, -0.15), sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.85), sh)
        torus(f"{tag} elbow ring {sx}", 0.12, 0.03, RM, parent=el, axis="X")
        S_(f"fore strut {sx}", (-0.05, -0.05, -0.75), (0.05, 0.05, 0.0), el)
        C_(f"fore crystal {sx}", (-0.17, -0.17, -0.65), (0.17, 0.17, -0.2), el)
        hands[sx] = hand(f"{tag} claw {sx}", el, T, -0.75, n=3, flen=0.3, pw=0.2, thumb=True)
        arms.append((sh, el, sx))
    J.update(legs=legs, arms=arms, hands=hands, struts=struts, crystals=crystals)
    return J


def anim_MAb(M):
    hz = M.J["hz"]
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0); M.arm(1, sx, 0, 10)
    M.fists(1, 0.1); M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    # 36-72: six brisk steps, 6 ticks each, a forward lean and a big arm swing
    for i in range(6):
        f0 = 36 + i * 6; sx = 1 if i % 2 == 0 else -1
        M.leg(f0, sx, -10, -5); M.leg(f0 + 3, sx, 35, -55, 10); M.leg(f0 + 6, sx, 15, -10)
        M.leg(f0, -sx, 15, -10); M.leg(f0 + 3, -sx, 0, -5); M.leg(f0 + 6, -sx, -10, -5)
        M.arm(f0 + 3, sx, -30, 30); M.arm(f0 + 3, -sx, 35, 40)
        M.root(f0 + 6, (i + 1) * 0.6)
        M.hips(f0, hz - 0.04, 6); M.hips(f0 + 3, hz + 0.05, 6, 0, -6 * sx); M.hips(f0 + 6, hz - 0.04, 6)
    y = 3.6
    for sx in (-1, 1):
        M.leg(74, sx, 0, 0); M.arm(74, sx, 15, 60)
    M.hips(74, hz); M.root(76, y)
    # 76-96: guard up, a left hook (swung across), then a right uppercut lifting the whole frame
    M.fists(76, 1.0)
    M.arm(78, -1, 60, 90, 40); M.arm(81, -1, 80, 80, -35); M.torso(78, 0, 0, -15); M.torso(81, 0, 0, 25)
    M.arm(84, -1, 20, 70); M.arm(84, 1, -10, 120); M.torso(84, 0, 0, -10)
    M.hips(84, hz - 0.25); M.leg(84, 1, 25, -45, 20); M.leg(84, -1, 25, -45, 20)
    M.arm(88, 1, 150, 40); M.torso(88, -8, 0, 15); M.hips(88, hz + 0.25)
    M.leg(88, 1, 0, 0); M.leg(88, -1, 0, 0)
    M.arm(96, 1, 15, 60); M.arm(96, -1, 15, 60); M.torso(96); M.hips(96, hz)
    ring_fx(f"{M.tag} hook ring", (M.bx - 0.3, y + 1.3, 3.0), 81, 0.2, 3.0, 5, axis="Y", th=0.025)
    ring_fx(f"{M.tag} uppercut ring", (M.bx + 0.8, y + 0.9, 4.2), 88, 0.3, 3.0, 6, th=0.03)
    # 96-126: crouch, leap forward 2.2 m, land on one knee with the right fist planted, ring
    for sx in (-1, 1):
        M.leg(96, sx, 0, 0); M.leg(100, sx, 40, -80, 40); M.leg(104, sx, -15, 0, 0)
        M.arm(100, sx, -35, 30); M.arm(104, sx, 120, 20)
    M.hips(100, hz - 0.5); M.hips(104, hz + 0.3); M.hips(109, hz + 1.0); M.hips(114, hz - 0.7); M.hips(120, hz - 0.7); M.hips(126, hz)
    M.root(100, y); M.root(114, y + 2.2)
    M.leg(114, 1, 80, -95, 15); M.leg(114, -1, -20, -110, 40); M.leg(120, 1, 80, -95, 15); M.leg(120, -1, -20, -110, 40)
    M.arm(114, 1, 35, 0); M.arm(114, -1, -30, 40, 25); M.arm(120, 1, 35, 0); M.arm(120, -1, -30, 40, 25)
    M.torso(114, 25); M.torso(120, 25)
    for sx in (-1, 1):
        M.leg(126, sx, 0, 0); M.arm(126, sx, 0, 10)
    M.torso(126); M.fists(126, 0.1)
    ring_fx(f"{M.tag} land ring", (M.bx + 0.8, y + 3.0, 0.04), 114, 0.5, 5.0, 9)
    cracks(M.tag, (M.bx + 0.8, y + 3.0, 0.01), 114, 5, 1.6)


def form_MAb(M, J, src):
    """The struts trace out joint by joint from the ring (each grows out of its pivot), then the crystals grow on."""
    bpy.context.view_layer.update()
    s_ = Vector(src)
    def order(objs, f0, f1, over=1.0):
        pos = [(o, (o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0)) - s_).length) for o in objs]
        lo = min(p for _, p in pos); hi = max(p for _, p in pos) + 1e-6
        for o, d in pos:
            fa = int(f0 + (d - lo) / (hi - lo) * (f1 - f0))
            key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 2, sc=over); key(o, fa + 3, sc=1.0)
    rest = [o for o in mparts(J) if o not in J["struts"] and o not in J["crystals"]]
    order(J["struts"] + rest, 2, 14)
    order(J["crystals"], 13, 22, 1.12)


# ------------------------------------------------------------------ MAc Dome Titan (round, blade + shield)
def build_MAc(tag, T):
    J = {"hz": 1.55}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.2), hips); J["torso"] = torso
    cyl(f"{tag} pelvis drum", 0.55, 0.4, T, 20, hips, loc=(0, 0, -0.3))
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.42, 0.6, 0.55)
        ball(f"{tag} hip ball {sx}", 0.2, FRAME, parent=hip)
        cyl(f"{tag} thigh {sx}", 0.2, 0.5, T, 14, hip, loc=(0, 0, -0.55), r2=0.24)
        ball(f"{tag} knee ball {sx}", 0.19, RM, parent=knee)
        cyl(f"{tag} shin {sx}", 0.24, 0.45, T, 14, knee, loc=(0, 0, -0.5), r2=0.2)
        cyl(f"{tag} foot {sx}", 0.36, 0.25, T, 18, ankle, loc=(0, 0.05, -0.32), r2=0.3)
        torus(f"{tag} foot band {sx}", 0.34, 0.03, RM, loc=(0, 0.05, -0.2), parent=ankle)
        legs.append((hip, knee, ankle, sx))
    cyl(f"{tag} barrel", 0.85, 1.1, T, 24, torso, loc=(0, 0, 0.0), r2=0.95)
    for k, z in enumerate((0.25, 0.75)):
        torus(f"{tag} barrel band {k}", 0.9 + z * 0.08, 0.04, RM, loc=(0, 0, z), parent=torso)
    torus(f"{tag} dome seat", 0.82, 0.05, RM, loc=(0, 0, 1.12), parent=torso)
    hatch = empty(f"{tag} dome hinge", (0, -0.8, 1.12), torso)
    dome = ball(f"{tag} dome", 0.78, GL, loc=(0, 0.8, 0.0), parent=hatch, seg=20); dome.scale = (1, 1, 0.85)
    for k in range(4):
        rib = box(f"{tag} dome rib {k}", (-0.025, -0.02, 0.0), (0.025, 0.02, 0.68), RM, hatch)
        rib.location = (0, 0.8, 0); rib.rotation_euler = (R(-55 + 37 * k), 0, 0)
    J["hatch"] = hatch; J["hatch_open"] = (R(110), 0, 0); J["seat"] = (0, 0.0, -0.1)
    J["core"] = cyl(f"{tag} core lens", 0.2, 0.06, W, 16, torso, loc=(0, 0.92, 0.5), axis="Y")
    arms, hands = [], {}
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.05, 0, 0.85), torso)
        ball(f"{tag} shoulder ball {sx}", 0.3, T, parent=sh)
        torus(f"{tag} shoulder band {sx}", 0.3, 0.035, RM, parent=sh, axis="X")
        cyl(f"{tag} upper arm {sx}", 0.14, 0.65, T, 12, sh, loc=(0, 0, -0.7))
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.75), sh)
        ball(f"{tag} elbow ball {sx}", 0.17, FRAME, parent=el)
        cyl(f"{tag} forearm {sx}", 0.2, 0.6, T, 14, el, loc=(0, 0, -0.65), r2=0.16)
        arms.append((sh, el, sx))
    el_r = arms[1][1]; el_l = arms[0][1]
    # right: a blade along the forearm, flat so its edge leads in a sideways slash
    bl = bev(box(f"{tag} blade", (-0.22, -0.03, -2.0), (0.22, 0.03, -0.55), T, el_r), 0.03)
    box(f"{tag} blade edge out", (0.2, -0.035, -1.95), (0.26, 0.035, -0.6), W, el_r)
    box(f"{tag} blade edge in", (-0.26, -0.035, -1.95), (-0.2, 0.035, -0.6), W, el_r)
    cyl(f"{tag} blade tip", 0.22, 0.25, T, 4, el_r, loc=(0, 0, -2.0), r2=0.01).rotation_euler = (R(180), 0, R(45))
    # left: a round shield on the forearm, facing out front when the arm is raised
    cyl(f"{tag} shield", 0.75, 0.08, T, 24, el_l, loc=(0, 0.18, -0.4), axis="Y")
    torus(f"{tag} shield rim", 0.75, 0.05, RM, loc=(0, 0.24, -0.4), parent=el_l, axis="Y")
    cyl(f"{tag} shield boss", 0.2, 0.12, W, 16, el_l, loc=(0, 0.24, -0.4), axis="Y")
    J.update(legs=legs, arms=arms, hands=hands)
    return J


def anim_MAc(M):
    hz = M.J["hz"]
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0); M.arm(1, sx, 0, 20, sx * 8)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    # 36-76: a waddle: the whole round body rocks side to side over each short step
    for i in range(5):
        f0 = 36 + i * 8; sx = 1 if i % 2 == 0 else -1
        M.leg(f0, sx, 0, 0); M.leg(f0 + 4, sx, 25, -35, 10, hip_z=-sx * 6); M.leg(f0 + 8, sx, 0, 0)
        M.leg(f0 + 4, -sx, -8, 0)
        M.hips(f0, hz, 0, 0, 0); M.hips(f0 + 4, hz + 0.06, 0, -9 * sx, 4 * sx); M.hips(f0 + 8, hz - 0.03, 0, 0, 0)
        M.arm(f0 + 4, sx, -10, 25, sx * 18); M.arm(f0 + 4, -sx, 15, 25, -sx * 12)
        M.root(f0 + 8, (i + 1) * 0.72)
    y = 3.6
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0)
    M.hips(76, hz)
    # 76-96: the blade slash, edge first: blade drawn back across the body, then swept out wide, a trail arc
    M.arm(76, 1, 0, 20, 8); M.arm(80, 1, 90, 30, 70); M.torso(80, 0, 0, 30)
    M.arm(83, 1, 90, 10, -10); M.arm(86, 1, 88, 10, -75); M.torso(83, 0, 0, -5); M.torso(86, 0, 0, -35)
    M.arm(90, 1, 80, 15, -70); M.arm(96, 1, 0, 20, 8); M.torso(96)
    M.arm(76, -1, 0, 20, -8); M.arm(80, -1, 60, 70, 0); M.arm(90, -1, 60, 70, 0)
    tr = arc(f"{M.tag} slash trail", 2.3, 0.06, R(10), R(170), W, (M.bx, y, 2.6))
    tr.rotation_euler = (0, 0, R(-10))
    key(tr, 1, sc=0.0001); key(tr, 81, sc=0.0001); key(tr, 83, sc=(1, 1, 1)); key(tr, 88, sc=(1.05, 1.05, 0.6)); key(tr, 90, sc=0.0001)
    # 96-126: shield slam: shield raised overhead, driven into the ground, a dome shockwave
    M.arm(98, -1, 140, 40, 0); M.arm(103, -1, 165, 20, 0); M.arm(107, -1, 50, 10, 0); M.arm(116, -1, 52, 10, 0); M.arm(126, -1, 0, 20, -8)
    M.arm(98, 1, -20, 30, 15); M.arm(116, 1, -15, 30, 15); M.arm(126, 1, 0, 20, 8)
    M.hips(98, hz + 0.1); M.hips(103, hz + 0.15); M.hips(107, hz - 0.35); M.hips(116, hz - 0.33); M.hips(126, hz)
    for sx in (-1, 1):
        M.leg(103, sx, 0, 0); M.leg(107, sx, 35, -60, 25); M.leg(116, sx, 35, -60, 25); M.leg(126, sx, 0, 0)
    M.torso(103, -8, 0, 15); M.torso(107, 28, 0, 10); M.torso(116, 26, 0, 10); M.torso(126)
    dm = ball(f"{M.tag} shock dome", 1.0, SHOCK, loc=(M.bx - 0.4, y + 1.4, 0.0), seg=24)
    key(dm, 1, sc=0.0001); key(dm, 106, sc=0.0001); key(dm, 107, sc=(0.4, 0.4, 0.3)); key(dm, 113, sc=(3.4, 3.4, 1.8))
    key(dm, 116, sc=(3.8, 3.8, 1.7)); key(dm, 117, sc=0.0001)
    ring_fx(f"{M.tag} slam ring", (M.bx - 0.4, y + 1.4, 0.04), 107, 0.6, 6.5, 9)


def form_MAc(M, J, src):
    """Blooms out from the core: nearest parts first, each overshoots a little and settles."""
    bpy.context.view_layer.update()
    c0 = J["core"].matrix_world @ Vector((0, 0, 0))
    parts = mparts(J)
    ds = [(o, (o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0)) - c0).length) for o in parts]
    hi = max(d for _, d in ds) + 1e-6
    for o, d in ds:
        fa = int(3 + d / hi * 17) + int(rng.integers(0, 2)); sc0 = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 2, sc=tuple(v * 1.15 for v in sc0)); key(o, fa + 4, sc=sc0)
    pulse = ball(f"{M.tag} bloom pulse", 0.4, SHOCK, loc=tuple(c0))
    key(pulse, 1, sc=0.0001); key(pulse, 2, sc=0.2); key(pulse, 16, sc=6.0); key(pulse, 17, sc=0.0001)


# ------------------------------------------------------------------ MCa Siege Ape (hunched, long arms, knuckle walk)
def build_MCa(tag, T):
    J = {"hz": 1.35}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, -0.1, 0.15), hips); J["torso"] = torso
    plate(f"{tag} pelvis", (-0.65, -0.45, -0.3), (0.65, 0.45, 0.15), T, hips)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.55, 0.5, 0.5)
        plate(f"{tag} thigh {sx}", (-0.3, -0.3, -0.55), (0.3, 0.3, 0.0), T, hip)
        plate(f"{tag} knee pad {sx}", (-0.28, 0.2, -0.65), (0.28, 0.4, -0.3), RM, hip, 0.03)
        plate(f"{tag} shin {sx}", (-0.27, -0.27, -0.5), (0.27, 0.27, 0.0), T, knee)
        plate(f"{tag} foot {sx}", (-0.38, -0.4, -0.25), (0.38, 0.55, 0.0), T, ankle)
        for k, xx in enumerate((-0.24, 0.0, 0.24)):
            box(f"{tag} foot claw {sx} {k}", (xx - 0.07, 0.55, -0.22), (xx + 0.07, 0.72, -0.06), RM, ankle)
        legs.append((hip, knee, ankle, sx))
    plate(f"{tag} back hump", (-1.0, -0.75, 0.2), (1.0, -0.3, 1.55), T, torso, 0.06)
    for sx in (-1, 1):
        plate(f"{tag} chest side {sx}", (sx * 1.0 - 0.15, -0.6, 0.0), (sx * 1.0 + 0.15, 0.55, 1.45), T, torso)
        cyl(f"{tag} hose {sx}", 0.06, 1.0, W, 8, torso, loc=(sx * 0.75, -0.72, 0.4)).rotation_euler = (R(-20), R(sx * 10), 0)
        nz = empty(f"{tag} thruster {sx}", (sx * 0.5, -0.85, 0.7), torso)
        plate(f"{tag} thruster body {sx}", (-0.22, -0.28, -0.25), (0.22, 0.18, 0.55), T, nz)
        torus(f"{tag} thruster lip {sx}", 0.16, 0.035, RM, loc=(0, -0.05, -0.27), parent=nz)
        J[f"flame {sx}"] = cyl(f"{tag} thruster flame {sx}", 0.14, -0.8, W, 10, nz, loc=(0, -0.05, -0.27), r2=0.02)
    plate(f"{tag} chest floor", (-1.0, -0.6, -0.05), (1.0, 0.55, 0.1), T, torso)
    plate(f"{tag} roof", (-1.05, -0.7, 1.4), (1.05, 0.6, 1.62), T, torso, 0.05)
    plate(f"{tag} brow ridge", (-0.9, 0.45, 1.25), (0.9, 0.75, 1.5), RM, torso, 0.04)
    hatch = empty(f"{tag} canopy hinge", (0, 0.55, 1.4), torso)
    box(f"{tag} canopy", (-0.82, 0.0, -1.35), (0.82, 0.06, 0.0), GL, hatch)
    for k in range(4):
        box(f"{tag} canopy grille {k}", (-0.84 + k * 0.56, 0.0, -1.35), (-0.78 + k * 0.56, 0.1, 0.0), RM, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    arms = []
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.45, 0, 1.15), torso)
        for k in range(3):                                    # stacked pauldron plates
            plate(f"{tag} pauldron {sx} {k}", (-0.55 + k * 0.06, -0.55 + k * 0.05, 0.05 + k * 0.17),
                  (0.55 - k * 0.06, 0.55 - k * 0.05, 0.3 + k * 0.17), T if k != 1 else RM, sh, 0.04)
        plate(f"{tag} upper arm {sx}", (-0.25, -0.25, -1.05), (0.25, 0.25, -0.05), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -1.1), sh)
        cyl(f"{tag} elbow joint {sx}", 0.2, 0.44, FRAME, 12, el, loc=(-0.22, 0, 0), axis="X")
        plate(f"{tag} forearm {sx}", (-0.3, -0.3, -0.9), (0.3, 0.3, -0.05), T, el)
        cyl(f"{tag} forearm piston {sx}", 0.05, 0.7, W, 8, el, loc=(sx * 0.33, 0, -0.85))
        plate(f"{tag} fist {sx}", (-0.4, -0.38, -1.4), (0.4, 0.38, -0.9), T, el, 0.05)
        for k in range(4):
            box(f"{tag} knuckle {sx} {k}", (-0.38 + k * 0.2, 0.3, -1.38), (-0.22 + k * 0.2, 0.42, -1.18), RM, el)
        arms.append((sh, el, sx))
    J.update(legs=legs, arms=arms, hands={})
    return J


def anim_MCa(M):
    hz = M.J["hz"]
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0); M.arm(1, sx, 0, 0)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.torso(30); M.root(36, 0)
    for sx in (-1, 1):
        M.arm(34, sx, 15, -10)
    M.torso(36, 32)
    # 36-76: knuckle-walks: an arm and the opposite leg swing together, the fists plant, the body rolls over them
    for i in range(4):
        f0 = 36 + i * 10; sx = 1 if i % 2 == 0 else -1
        M.arm(f0, sx, 5, -5); M.arm(f0 + 5, sx, 45, 20, -sx * 5); M.arm(f0 + 10, sx, 30, -15)
        M.arm(f0, -sx, 30, -15); M.arm(f0 + 5, -sx, 10, -10); M.arm(f0 + 10, -sx, 5, -5)
        M.leg(f0, -sx, -10, 0); M.leg(f0 + 5, -sx, 30, -45, 10); M.leg(f0 + 10, -sx, 10, -5)
        M.leg(f0 + 5, sx, -12, 0)
        M.hips(f0, hz, 0, 0, 0); M.hips(f0 + 5, hz + 0.1, 0, 5 * sx, 8 * sx); M.hips(f0 + 10, hz - 0.05, 0, 0, 0)
        M.torso(f0 + 5, 30, 0, -8 * sx); M.torso(f0 + 10, 34)
        M.root(f0 + 10, (i + 1) * 0.9)
        ring_fx(f"{M.tag} knuckle ring {i}", (M.bx + sx * 1.6, (i + 1) * 0.9 + 1.7, 0.04), f0 + 10, 0.3, 3.0, 6, th=0.03)
    y = 3.6
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0); M.arm(76, sx, 30, -15)
    M.hips(76, hz); M.torso(76, 34)
    # 76-96: rears up, both fists high, then a two-fist smash in front
    M.torso(83, -15); M.hips(83, hz + 0.35)
    for sx in (-1, 1):
        M.arm(83, sx, 170, 30, -sx * 12); M.arm(87, sx, 80, 0, sx * 5); M.arm(93, sx, 80, 0, sx * 5); M.arm(96, sx, 30, -15)
        M.leg(83, sx, -5, 0); M.leg(87, sx, 30, -50, 20); M.leg(93, sx, 30, -50, 20); M.leg(96, sx, 0, 0)
    M.torso(87, 50); M.hips(87, hz - 0.3); M.torso(93, 48); M.hips(93, hz - 0.3); M.torso(96, 34); M.hips(96, hz)
    cracks(M.tag, (M.bx, y + 2.6, 0.01), 87, 8, 2.6)
    ring_fx(f"{M.tag} smash ring", (M.bx, y + 2.6, 0.04), 87, 0.6, 6.0, 9)
    # 96-126: thruster leap: crouch, thrusters blast, it arcs forward and lands on its fists and feet
    for sx in (-1, 1):
        M.leg(100, sx, 40, -80, 40); M.leg(104, sx, -10, 0); M.leg(112, sx, 20, -40, 15); M.leg(116, sx, 35, -70, 35); M.leg(126, sx, 0, 0)
        M.arm(100, sx, -30, 0); M.arm(104, sx, -40, 10); M.arm(112, sx, 60, -10); M.arm(116, sx, 55, -20); M.arm(120, sx, 55, -20); M.arm(126, sx, 30, -15)
        fl = M.J[f"flame {sx}"]
        key(fl, 1, sc=(1, 1, 0.0001)); key(fl, 101, sc=(1, 1, 0.0001)); key(fl, 103, sc=(1.3, 1.3, 2.0)); key(fl, 110, sc=(1, 1, 1.4))
        key(fl, 113, sc=(1, 1, 0.0001))
    M.hips(100, hz - 0.35); M.hips(104, hz + 0.2); M.hips(109, hz + 1.8); M.hips(116, hz - 0.35); M.hips(120, hz - 0.35); M.hips(126, hz)
    M.torso(100, 40); M.torso(104, 10); M.torso(112, 35); M.torso(116, 55); M.torso(120, 52); M.torso(126, 34)
    M.root(100, y); M.root(116, y + 2.0)
    ring_fx(f"{M.tag} land ring", (M.bx, y + 3.6, 0.04), 116, 0.7, 6.0, 10)
    cracks(M.tag + " land", (M.bx, y + 3.6, 0.01), 116, 6, 2.0)


def form_MCa(M, J, src):
    """A scan ring rises from the ground; each slice appears as the ring passes it."""
    bpy.context.view_layer.update()
    parts = mparts(J, ("flame",))
    zs = [(o, (o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))).z) for o in parts]
    top = max(z for _, z in zs) + 0.2
    for o, z in zs:
        fa = int(3 + z / top * 18); sc0 = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, fa, sc=0.0001); key(o, fa + 1, sc=sc0)
    sc_ = torus(f"{M.tag} scan ring", 1.7, 0.05, W, loc=(M.bx, 0, 0.0))
    sc2 = torus(f"{M.tag} scan ring inner", 1.6, 0.025, RM, loc=(M.bx, 0, 0.0))
    for o in (sc_, sc2):
        key(o, 1, loc=(M.bx, 0, 0.0), sc=0.0001); key(o, 2, loc=(M.bx, 0, 0.0), sc=1.0)
        key(o, 21, loc=(M.bx, 0, top), sc=1.0); key(o, 23, loc=(M.bx, 0, top + 0.1), sc=0.0001)


# ------------------------------------------------------------------ MCb Rocket Juggernaut (hovers, rocket fist)
def build_MCb(tag, T):
    J = {"hz": 1.4}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.15), hips); J["torso"] = torso
    plate(f"{tag} pelvis", (-0.6, -0.45, -0.3), (0.6, 0.45, 0.15), T, hips)
    legs, pads = [], []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.5, 0.55, 0.5)
        plate(f"{tag} thigh {sx}", (-0.25, -0.25, -0.55), (0.25, 0.25, 0.0), T, hip)
        plate(f"{tag} shin {sx}", (-0.3, -0.3, -0.5), (0.3, 0.3, 0.0), T, knee)
        torus(f"{tag} shin band {sx}", 0.3, 0.035, RM, loc=(0, 0, -0.25), parent=knee)
        cyl(f"{tag} hover pad {sx}", 0.42, 0.18, T, 20, ankle, loc=(0, 0.05, -0.2))
        cyl(f"{tag} pad glow {sx}", 0.3, 0.03, W, 20, ankle, loc=(0, 0.05, -0.23))
        fl = cyl(f"{tag} pad jet {sx}", 0.28, -0.5, W, 14, ankle, loc=(0, 0.05, -0.23), r2=0.02); pads.append(fl)
        legs.append((hip, knee, ankle, sx))
    plate(f"{tag} chest back", (-1.0, -0.6, 0.0), (1.0, -0.3, 1.5), T, torso)
    for sx in (-1, 1):
        plate(f"{tag} chest side {sx}", (sx * 1.0 - 0.15, -0.6, 0.0), (sx * 1.0 + 0.15, 0.55, 1.45), T, torso)
    plate(f"{tag} chest floor", (-1.0, -0.6, -0.05), (1.0, 0.55, 0.1), T, torso)
    plate(f"{tag} roof", (-1.05, -0.65, 1.4), (1.05, 0.6, 1.6), T, torso, 0.05)
    plate(f"{tag} chin", (-0.7, 0.3, -0.15), (0.7, 0.62, 0.15), RM, torso, 0.03)
    # booster pack: four nozzles and two fins
    pack = empty(f"{tag} booster pack", (0, -0.75, 0.8), torso)
    plate(f"{tag} pack body", (-0.7, -0.35, -0.6), (0.7, 0.15, 0.7), T, pack, 0.05)
    jets = []
    for i, (xx, zz) in enumerate(((-0.4, 0.2), (0.4, 0.2), (-0.4, -0.35), (0.4, -0.35))):
        cyl(f"{tag} nozzle {i}", 0.15, 0.25, FRAME, 12, pack, loc=(xx, -0.35, zz), axis="Y", r2=0.2).rotation_euler = (0, 0, R(180))
        jets.append(cyl(f"{tag} jet {i}", 0.15, 0.9, W, 10, pack, loc=(xx, -0.6, zz), axis="Y", r2=0.02))
        jets[-1].rotation_euler = (0, 0, R(180))
    for sx in (-1, 1):
        plate(f"{tag} fin {sx}", (sx * 0.7, -0.4, 0.1), (sx * 1.0, 0.0, 0.9), RM, pack, 0.02)
    hatch = empty(f"{tag} canopy hinge", (0, 0.55, 1.45), torso)
    box(f"{tag} canopy", (-0.85, 0.0, -1.4), (0.85, 0.06, 0.0), GL, hatch)
    box(f"{tag} canopy bar", (-0.87, 0.0, -0.75), (0.87, 0.1, -0.65), RM, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    arms, fists = [], {}
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.4, 0, 1.15), torso)
        plate(f"{tag} pauldron {sx}", (-0.48, -0.48, -0.15), (0.48, 0.48, 0.5), T, sh, 0.06)
        torus(f"{tag} pauldron band {sx}", 0.45, 0.04, RM, loc=(0, 0, 0.2), parent=sh)
        plate(f"{tag} upper arm {sx}", (-0.2, -0.2, -0.75), (0.2, 0.2, -0.1), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.8), sh)
        plate(f"{tag} gauntlet {sx}", (-0.34, -0.34, -0.65), (0.34, 0.34, 0.0), T, el, 0.05)
        torus(f"{tag} gauntlet ring {sx}", 0.33, 0.035, RM, loc=(0, 0, -0.62), parent=el)
        rf = empty(f"{tag} rocket fist {sx}", (0, 0, -0.65), el)
        plate(f"{tag} fist {sx}", (-0.33, -0.33, -0.55), (0.33, 0.33, 0.0), T, rf, 0.06)
        for k in range(4):
            box(f"{tag} fist knuckle {sx} {k}", (-0.3 + k * 0.155, 0.28, -0.53), (-0.18 + k * 0.155, 0.37, -0.3), RM, rf)
        fists[sx] = (rf, cyl(f"{tag} fist jet {sx}", 0.18, 0.7, W, 10, rf, loc=(0, 0, -0.0), r2=0.02))
        teth = empty(f"{tag} tether {sx}", (0, 0, -0.65), el)
        box(f"{tag} tether line {sx}", (-0.035, -0.035, -1.0), (0.035, 0.035, 0.0), W, teth)
        fists[sx] = fists[sx] + (teth,)
        arms.append((sh, el, sx))
    J.update(legs=legs, arms=arms, hands={}, pads=pads, jets=jets, fists=fists)
    return J


def anim_MCb(M):
    hz = M.J["hz"]; lift = 0.45
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0); M.arm(1, sx, 0, 15)
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    for o in M.J["pads"]:
        key(o, 1, sc=(1, 1, 0.0001)); key(o, 34, sc=(1, 1, 0.0001)); key(o, 37, sc=(1, 1, 1.0)); key(o, 74, sc=(1, 1, 1.0))
        key(o, 77, sc=(1, 1, 0.0001)); key(o, 99, sc=(1, 1, 0.0001)); key(o, 102, sc=(1, 1, 1.4)); key(o, 113, sc=(1, 1, 1.4)); key(o, 116, sc=(1, 1, 0.0001))
    for o in M.J["jets"]:
        key(o, 1, sc=(1, 0.0001, 1)); key(o, 99, sc=(1, 0.0001, 1)); key(o, 101, sc=(1.3, 1.6, 1.3)); key(o, 112, sc=(1, 1.0, 1)); key(o, 114, sc=(1, 0.0001, 1))
        key(o, 38, sc=(1, 0.0001, 1)); key(o, 40, sc=(0.8, 0.6, 0.8)); key(o, 70, sc=(0.8, 0.6, 0.8)); key(o, 72, sc=(1, 0.0001, 1))
    for sx in (-1, 1):
        rf, jet, teth = M.J["fists"][sx]
        key(jet, 1, sc=(1, 1, 0.0001)); key(teth, 1, sc=(1, 1, 0.0001))
    # 36-76: lifts off its pads and glides forward, legs trailing, a slow bob; no steps
    M.hips(36, hz); M.hips(40, hz + lift, 8)
    for k, f in enumerate(range(44, 76, 8)):
        M.hips(f, hz + lift + (0.08 if k % 2 == 0 else -0.04), 10, 0, 4 if k % 2 == 0 else -4)
    for sx in (-1, 1):
        M.leg(40, sx, -15, -30, -10); M.leg(72, sx, -15, -30, -10); M.arm(40, sx, -20, 30, sx * 10); M.arm(72, sx, -15, 30, sx * 10)
    M.root(40, 0.2); M.root(72, 3.4); M.root(76, 3.6)
    M.hips(76, hz, 0)
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0); M.arm(76, sx, 0, 15)
    y = 3.6
    # 76-96: rocket punch: the right arm aims, the fist fires out 4 m on a tether, hits, and reels back in
    M.arm(80, 1, 90, 0); M.torso(80, 0, 0, -15); M.arm(80, -1, 30, 60)
    rf, jet, teth = M.J["fists"][1]
    key(rf, 1, loc=(0, 0, -0.65)); key(rf, 82, loc=(0, 0, -0.65)); key(rf, 86, loc=(0, 0, -4.6)); key(rf, 89, loc=(0, 0, -4.6))
    key(rf, 94, loc=(0, 0, -0.65))
    key(teth, 82, sc=(1, 1, 0.0001)); key(teth, 86, sc=(1, 1, 3.95)); key(teth, 89, sc=(1, 1, 3.95)); key(teth, 94, sc=(1, 1, 0.0001))
    key(jet, 81, sc=(1, 1, 0.0001)); key(jet, 82, sc=(1.2, 1.2, 1.8)); key(jet, 86, sc=(1, 1, 1.0)); key(jet, 87, sc=(1, 1, 0.0001))
    M.arm(94, 1, 90, 0); M.arm(96, 1, 0, 15); M.torso(94, 0, 0, -10); M.torso(96); M.arm(96, -1, 0, 15)
    M.hips(82, hz - 0.08, -4); M.hips(88, hz)
    ring_fx(f"{M.tag} rocket ring", (M.bx + 1.4, y + 5.8, 2.75), 86, 0.3, 4.0, 6, axis="Y")
    # 96-126: spinning boost jump: the pack fires, one full turn in the air, slam down, ring
    for sx in (-1, 1):
        M.leg(98, sx, 35, -70, 35); M.leg(102, sx, -5, 0); M.leg(112, sx, -10, -20); M.leg(116, sx, 35, -70, 35); M.leg(126, sx, 0, 0)
        M.arm(98, sx, -20, 30); M.arm(102, sx, 10, 20, sx * 70); M.arm(112, sx, 10, 20, sx * 70); M.arm(116, sx, 120, 30); M.arm(120, sx, 70, 10)
        M.arm(126, sx, 0, 15)
    M.hips(98, hz - 0.35); M.hips(102, hz + 0.4); M.hips(108, hz + 2.2); M.hips(116, hz - 0.4); M.hips(120, hz - 0.38); M.hips(126, hz)
    M.root(98, y, 0, 0); M.root(102, y, 0, 0); M.root(112, y, 0, 360); M.root(126, y, 0, 360)
    M.torso(116, 25); M.torso(120, 22); M.torso(126)
    ring_fx(f"{M.tag} slam ring", (M.bx, y, 0.04), 116, 0.7, 6.5, 10)
    cracks(M.tag, (M.bx, y + 0.8, 0.01), 116, 7, 2.0)


def form_MCb(M, J, src):
    """Assembles from parts flying in from all round, spinning into place, the pack and fists last."""
    bpy.context.view_layer.update()
    parts = mparts(J, ("jet", "tether"))
    for o in parts:
        c = o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))
        a = rng.uniform(0, 2 * math.pi); d = Vector((math.cos(a) * 3.2, math.sin(a) * 3.2, rng.uniform(0.5, 2.5)))
        local = o.parent.matrix_world.to_3x3().inverted() @ d
        last = any(s in o.name for s in ("pack", "nozzle", "jet", "fin", "fist", "knuckle"))
        fa = int(rng.integers(16, 22)) if last else int(4 + c.z / 3.6 * 11 + rng.integers(0, 3))
        r0 = tuple(o.rotation_euler); sp = Euler((r0[0] + rng.uniform(-3, 3), r0[1] + rng.uniform(-3, 3), r0[2] + rng.uniform(-3, 3)))
        l0 = tuple(o.location)
        key(o, 1, loc=tuple(Vector(l0) + local), rot=tuple(sp), sc=0.0001); key(o, fa - 6, loc=tuple(Vector(l0) + local), rot=tuple(sp), sc=0.0001)
        key(o, fa - 5, sc=1.0); key(o, fa, loc=l0, rot=r0, sc=1.0)


# ------------------------------------------------------------------ MCc Breaker (horned, plate skirt, war hammer)
def build_MCc(tag, T):
    J = {"hz": 1.95}
    root = empty(f"{tag} mech"); J["root"] = root
    hips = empty(f"{tag} hips", (0, 0, J["hz"]), root); J["hips"] = hips
    torso = empty(f"{tag} torso", (0, 0, 0.15), hips); J["torso"] = torso
    plate(f"{tag} pelvis", (-0.65, -0.45, -0.25), (0.65, 0.45, 0.15), T, hips)
    for i in range(7):                                       # a layered plate skirt, each plate over the next
        a = -math.pi * 0.9 + i * (math.pi * 1.8 / 6)
        pv = empty(f"{tag} skirt pivot {i}", (0.7 * math.sin(a), 0.5 * math.cos(a), -0.05), hips); pv.rotation_euler = (0, 0, -a)
        pv.rotation_euler = (R(12), 0, -a)
        plate(f"{tag} skirt plate {i}", (-0.24, -0.04, -0.6), (0.24, 0.05, 0.0), T if i % 2 else RM, pv, 0.02)
    legs = []
    for sx in (-1, 1):
        hip, knee, ankle = leg_pivots(tag, hips, sx, 0.45, 0.82, 0.82)
        plate(f"{tag} thigh {sx}", (-0.23, -0.23, -0.82), (0.23, 0.23, 0.0), T, hip)
        plate(f"{tag} knee cop {sx}", (-0.25, 0.1, -0.18), (0.25, 0.33, 0.2), RM, knee, 0.04)
        box(f"{tag} knee spike {sx}", (-0.05, 0.3, -0.05), (0.05, 0.5, 0.06), RM, knee)
        plate(f"{tag} greave {sx}", (-0.24, -0.24, -0.82), (0.24, 0.26, 0.0), T, knee)
        plate(f"{tag} boot {sx}", (-0.32, -0.4, -0.3), (0.32, 0.55, 0.0), T, ankle, 0.05)
        legs.append((hip, knee, ankle, sx))
    plate(f"{tag} chest back", (-0.95, -0.6, 0.0), (0.95, -0.3, 1.5), T, torso)
    for sx in (-1, 1):
        plate(f"{tag} chest side {sx}", (sx * 0.95 - 0.15, -0.6, 0.0), (sx * 0.95 + 0.15, 0.55, 1.45), T, torso)
    plate(f"{tag} chest floor", (-0.95, -0.6, -0.05), (0.95, 0.55, 0.1), T, torso)
    head = empty(f"{tag} helm", (0, 0, 1.4), torso); J["head"] = head
    plate(f"{tag} helm crown", (-1.0, -0.66, 0.0), (1.0, 0.62, 0.28), T, head, 0.06)
    plate(f"{tag} helm crest", (-0.08, -0.6, 0.25), (0.08, 0.55, 0.55), RM, head, 0.02)
    for sx in (-1, 1):                                       # two horns that sweep out and up
        h1 = cyl(f"{tag} horn {sx} a", 0.14, 0.55, T, 8, head, loc=(sx * 0.85, 0.2, 0.15), r2=0.09); h1.rotation_euler = (R(-10), R(sx * 60), 0)
        h2 = cyl(f"{tag} horn {sx} b", 0.09, 0.45, RM, 8, head, loc=(sx * 1.32, 0.13, 0.42), r2=0.01); h2.rotation_euler = (R(-15), R(sx * 15), 0)
    hatch = empty(f"{tag} visor hinge", (0, 0.55, 1.4), torso)
    box(f"{tag} visor", (-0.8, 0.0, -1.35), (0.8, 0.06, 0.0), GL, hatch)
    plate(f"{tag} visor plate", (-0.82, 0.0, -0.7), (0.82, 0.12, 0.0), T, hatch, 0.02)
    box(f"{tag} visor slit", (-0.6, 0.12, -0.45), (0.6, 0.15, -0.36), W, hatch)
    J["hatch"] = hatch; J["seat"] = (0, -0.05, -0.62)
    arms = []
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 1.3, 0, 1.15), torso)
        plate(f"{tag} pauldron {sx}", (-0.45, -0.5, -0.2), (0.45, 0.5, 0.45), T, sh, 0.06)
        for k in range(3):
            sp = cyl(f"{tag} pauldron spike {sx} {k}", 0.09, 0.35, RM, 6, sh, loc=(sx * 0.15, -0.3 + k * 0.3, 0.42), r2=0.0)
            sp.rotation_euler = (0, R(sx * 25), 0)
        plate(f"{tag} upper arm {sx}", (-0.2, -0.2, -0.75), (0.2, 0.2, -0.1), T, sh)
        el = empty(f"{tag} elbow {sx}", (0, 0, -0.8), sh)
        plate(f"{tag} vambrace {sx}", (-0.25, -0.25, -0.65), (0.25, 0.25, 0.0), T, el, 0.04)
        plate(f"{tag} gauntlet {sx}", (-0.28, -0.28, -0.98), (0.28, 0.28, -0.62), T, el, 0.05)
        arms.append((sh, el, sx))
    # the war hammer, in the right fist: handle along the arm, head across it, faces on +/-Y (leading on an overhead smash)
    el_r = arms[1][1]
    hm = empty(f"{tag} hammer", (0, 0, -0.85), el_r); J["hammer"] = hm
    cyl(f"{tag} hammer haft", 0.07, 2.0, FRAME, 10, hm, loc=(0, 0, -2.0))
    torus(f"{tag} haft grip", 0.08, 0.03, RM, loc=(0, 0, -0.3), parent=hm)
    hd = plate(f"{tag} hammer head", (-0.32, -0.55, -2.35), (0.32, 0.55, -1.75), T, hm, 0.06)
    cyl(f"{tag} hammer face front", 0.28, 0.08, RM, 14, hm, loc=(0, 0.55, -2.05), axis="Y")
    cyl(f"{tag} hammer face back", 0.28, 0.08, W, 14, hm, loc=(0, -0.63, -2.05), axis="Y")
    J.update(legs=legs, arms=arms, hands={})
    return J


def anim_MCc(M):
    hz = M.J["hz"]; hm = M.J["hammer"]
    M.hatch()
    for sx in (-1, 1):
        M.leg(1, sx, 0, 0)
    M.arm(1, 1, -10, 10); M.arm(1, -1, 0, 10)
    key(hm, 1, rot=(R(-80), 0, 0))                        # hammer trailing down and back
    M.hips(1, hz); M.torso(1); M.root(1, 0); M.root(36, 0)
    # 36-76: four slow plodding steps, the hammer head dragging behind, the body leaning into each
    for i in range(4):
        f0 = 36 + i * 10; sx = 1 if i % 2 == 0 else -1
        M.leg(f0, sx, 0, 0); M.leg(f0 + 5, sx, 30, -45, 12); M.leg(f0 + 10, sx, 0, 0)
        M.leg(f0 + 5, -sx, -12, 0)
        M.hips(f0, hz - 0.05, 4, 0, 0); M.hips(f0 + 5, hz + 0.05, 4, 3 * sx, -4 * sx); M.hips(f0 + 10, hz - 0.08, 4, 0, 0)
        M.arm(f0 + 5, -1, 20 if sx == 1 else -15, 25)
        M.arm(f0 + 5, 1, -14, 8)
        M.root(f0 + 10, (i + 1) * 0.8)
    key(hm, 74, rot=(R(-80), 0, 0)); M.arm(74, 1, -10, 10)
    y = 3.2
    for sx in (-1, 1):
        M.leg(76, sx, 0, 0)
    M.hips(76, hz)
    # 76-96: the overhead smash: hammer swung up behind, then down in front, the face leading, cracks and ring
    key(hm, 76, rot=(R(-80), 0, 0)); key(hm, 82, rot=(R(-10), 0, 0)); key(hm, 88, rot=(R(40), 0, 0)); key(hm, 93, rot=(R(40), 0, 0))
    key(hm, 96, rot=(R(-80), 0, 0))                                        # the head lands face-first ahead, not in the floor
    M.arm(76, 1, -10, 10); M.arm(82, 1, 185, 20); M.arm(85, 1, 120, 10); M.arm(88, 1, 55, 0); M.arm(93, 1, 55, 0); M.arm(96, 1, -10, 10)
    M.arm(76, -1, 0, 10); M.arm(82, -1, 175, 30, 25); M.arm(88, -1, 50, 20, 20); M.arm(93, -1, 50, 20, 20); M.arm(96, -1, 0, 10)
    M.torso(82, -14); M.torso(88, 30); M.torso(93, 28); M.torso(96)
    M.hips(82, hz + 0.1); M.hips(88, hz - 0.4); M.hips(93, hz - 0.4); M.hips(96, hz)
    for sx in (-1, 1):
        M.leg(88, sx, 30, -55, 25); M.leg(93, sx, 30, -55, 25); M.leg(96, sx, 0, 0)
    cracks(M.tag, (M.bx + 1.2, y + 3.0, 0.01), 88, 8, 2.8)
    ring_fx(f"{M.tag} smash ring", (M.bx + 1.2, y + 3.0, 0.04), 88, 0.6, 6.0, 9)
    # 96-126: a full-turn sweep: hammer out level, the head rolled so a face leads, one 360 turn, a ring of wind
    M.arm(100, 1, 90, 0, -30); key(hm, 100, rot=(0, 0, R(90)))
    M.arm(100, -1, 30, 60)
    M.root(100, y, 0, 0); M.root(103, y, 0, -30); M.root(113, y, 0, 330); M.root(116, y, 0, 360); M.root(126, y, 0, 360)
    M.hips(100, hz - 0.15, 0, 0); M.hips(113, hz - 0.15); M.hips(126, hz)
    key(hm, 116, rot=(0, 0, R(90))); key(hm, 126, rot=(R(-80), 0, 0)); M.arm(116, 1, 85, 0, -20); M.arm(126, 1, -10, 10); M.arm(126, -1, 0, 10)
    sw = torus(f"{M.tag} sweep ring", 3.3, 0.06, RM, loc=(M.bx, y, 1.9))
    key(sw, 1, sc=0.0001); key(sw, 104, sc=0.0001); key(sw, 106, sc=(0.85, 0.85, 1)); key(sw, 114, sc=(1.1, 1.1, 1)); key(sw, 118, sc=(1.4, 1.4, 1))
    key(sw, 119, sc=0.0001)


def form_MCc(M, J, src):
    """Rains together from the top down: each plate drops in from above and bounces into place, the hammer last."""
    bpy.context.view_layer.update()
    parts = mparts(J)
    zs = [(o, (o.matrix_world @ Vector(np.mean([v.co for v in o.data.vertices], axis=0))).z) for o in parts]
    top = max(z for _, z in zs) + 1e-6
    for o, z in zs:
        hammer = "hammer" in o.name or "haft" in o.name
        fa = int(rng.integers(19, 22)) if hammer else int(4 + (1 - z / top) * 13) + int(rng.integers(0, 2))
        up = o.parent.matrix_world.to_3x3().inverted() @ Vector((0, 0, 3.5))
        l0 = Vector(o.location)
        key(o, 1, loc=tuple(l0 + up), sc=0.0001); key(o, fa - 4, loc=tuple(l0 + up), sc=0.0001); key(o, fa - 3, sc=1.0)
        key(o, fa, loc=tuple(l0)); key(o, fa + 1, loc=tuple(l0 + up * 0.03)); key(o, fa + 2, loc=tuple(l0))


# ------------------------------------------------------------------ build the six takes
TAKES = [("MAa", "Plated Titan", "br1", "villager", build_MAa, anim_MAa, form_MAa, 104),
         ("MAb", "Exo Frame", "v1", "player", build_MAb, anim_MAb, form_MAb, 88),
         ("MAc", "Dome Titan", "r2", "villager", build_MAc, anim_MAc, form_MAc, 85),
         ("MCa", "Siege Ape", "w1", "zombie", build_MCa, anim_MCa, form_MCa, 87),
         ("MCb", "Rocket Juggernaut", "r1", "villager", build_MCb, anim_MCb, form_MCb, 87),
         ("MCc", "Breaker", "h1", "zombie", build_MCc, anim_MCc, form_MCc, 88)]
for bi, (tk, name, look, pk, bf, af, ff, peak) in enumerate(TAKES):
    bx = bi * BAY + (18.0 if bi >= 3 else 0.0)
    tag = f"M2 {tk}"
    box(f"{tag} floor", (bx - 5, -5, -0.02), (bx + 5, 13, 0), FLOOR)
    J = bf(tag, TEX[look])
    J["root"].location = (bx, 0, 0)
    M = Mech(tag, J, bx)
    standing = tk == "MAb"
    seat_parent = J["torso"]
    prig, PM = pilot(f"{tag} pilot", pk, seat_parent, J["seat"])
    if standing:
        J["mirror"] = prig
    af(M)
    pr = prig["root"]
    scene.frame_set(1); bpy.context.view_layer.update()
    stand_local = seat_parent.matrix_world.inverted() @ Vector((bx, 0.0, 0.0))
    key(pr, 1, loc=tuple(stand_local)); key(pr, 24, loc=tuple(stand_local)); key(pr, 30, loc=J["seat"])
    if standing:                                              # stands on the plate, legs follow the stance only lightly
        pose(prig, 1, leg_r=(0, 0, 0), leg_l=(0, 0, 0), shin_r=(0, 0, 0), shin_l=(0, 0, 0), body=(0, 0, 0))
        pose(prig, 30, leg_r=(0, 0, 4), leg_l=(0, 0, -4))
    else:
        pose(prig, 1, leg_r=(0, 0, 0), leg_l=(0, 0, 0), shin_r=(0, 0, 0), shin_l=(0, 0, 0), arm_r=(0, 0, 0), arm_l=(0, 0, 0), body=(0, 0, 0))
        pose(prig, 24, leg_r=(0, 0, 0), leg_l=(0, 0, 0), shin_r=(0, 0, 0), shin_l=(0, 0, 0), arm_r=(40, 0, 0), arm_l=(40, 0, 0))
        pose(prig, 30, leg_r=(90, 0, 6), leg_l=(90, 0, -6), shin_r=(-90, 0, 0), shin_l=(-90, 0, 0), arm_r=(60, 0, 0), arm_l=(60, 0, 0),
             fore_r=(20, 0, 0), fore_l=(20, 0, 0))
    if pk == "villager" and tk == "MAc":                      # the dome is round and low: the villager sits a little smaller
        pr.scale = (0.85, 0.85, 0.85)
    scene.frame_set(1); bpy.context.view_layer.update()
    ring_world = prig["ring_pt"].matrix_world.translation.copy()
    ff(M, J, tuple(ring_world))
    cam(f"Cam {tk}", (bx + 6.5, 12.5, 4.2), (bx, 2.4, 1.9), 30)
    cam(f"Cam {tk} close", (bx + 3.0, 8.5, 3.4), (bx, 2.0, 2.2), 30)
    label(f"{tk}  {name}  - pilot: {pk}", (bx, -3.5, 5.2), LBL, 0.32, rot=(R(90), 0, R(180)))
    print(tk, "built", flush=True)
cam("Cam row MA", (BAY, 40, 10), (BAY, 2, 2.0), 30)
cam("Cam row MC", (5 * BAY, 40, 10), (5 * BAY, 2, 2.0), 30)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam MAa", 1, (0.35, 0.45, 0.6), 3.0



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

