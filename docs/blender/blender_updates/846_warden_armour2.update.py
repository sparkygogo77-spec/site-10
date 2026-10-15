# Pass 846: Warden armour: R1b and R1h variations (rings/suits chat, 2026-10-15, range 800-899). From pass 838.
# J rated 838 R1b (H1 hex plate armour, 1.5 px off) and R1h (H1 hex heavy plate) IMPROVE with no note: 3 new
# variations each. His original note (828 R1): "covered in an armor like construct that protrudes over them not on
# their skin". R4b (W1 weave plates) is KEEP and stays in 838; the shells (R1c, R2c, R4c) and R2b were dropped, so
# every take here is plate armour standing off the skin in H1 hex, each with its own layout, silhouette and forming.
# The real warden (opaque, vanilla proportions, cyan soul spots) walks underneath; armour 80% opaque, forms in
# frames 12-32.
#   R1b1 lamellar: horizontal lames with gaps, each lower lame flares further out (skirt, stepped spaulders);
#        forms by each lame twisting round its limb into place, bottom up
#   R1b2 loose tiles: a checker of raised / set-back tiles with open seams, open visor, swept wing pauldrons;
#        forms by tiles flying in from 1.4 m out in random order and locking on
#   R1b3 exo-frame over plates: 1 px ribs, hoops, back spines, visor bars and limb rods outside narrower plates;
#        forms by the frame drawing up from its feet, then the plates rolling down over it
#   R1h1 bastion: 2 px plates 2 px off, chest boss, gorget, long tasset skirt, great helm, three-tier bell pauldrons;
#        forms by plates slamming down from above, helm first, with a bounce
#   R1h2 hunched carapace: three back layers rising over the head, peaked hood, tendril fins, huge fist cuffs;
#        forms by growing out from the sternum (hex pixels stream out, plates swell and settle)
#   R1h3 spiked heavy: chest chevrons, spine fins, horns, tendril blades, spiked pauldrons, elbow and knee spikes;
#        forms by pushing up out of the skin and standing off, from the sternum out to the limbs
# Cameras "Cam <code>", "Cam row R1b", "Cam row R1h". Builds LanternLive\constructs\warden_armour2.blend.
SCENE_NAME = "Warden Armour 2"
OUT_REL = "constructs/warden_armour2.blend"
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


FRAME_END = 160
FLOOR = mat("WA floor", (0.18, 0.2, 0.2), rough=0.9)
LBL = mat("WA label", (0.3, 1.0, 0.45), emit=2.0)
rng = np.random.default_rng(846)
CM = cmats("WA", "green")
_tm = {}


def T(look, corps="green", uvt=0.5):
    k = (look, corps)
    if k not in _tm:
        _tm[k] = strip_mat(f"WA {look} {corps}", strip_image(corps, look), 4, emit=1.2, alpha=0.88)
    return _tm[k]


def seam_mat(corps):
    return mat(f"WA seam {corps}", CORPS[corps], emit=3.0)


def turn(root, f0=1, f1=FRAME_END):
    _p = bpy.context.preferences.edit; _o = _p.keyframe_new_interpolation_type; _p.keyframe_new_interpolation_type = "LINEAR"
    key(root, f0, rot=(0, 0, R(-30))); key(root, f1, rot=(0, 0, R(-30 + 360)))
    _p.keyframe_new_interpolation_type = _o



# ------------------------------------------------------------------ 838: the warden underneath, construct armour over it
SKIN = mat("WA warden skin", (0.035, 0.09, 0.11), rough=0.7)            # vanilla warden: dark blue-teal hide
SKIN_DARK = mat("WA warden ribs", (0.02, 0.05, 0.06), rough=0.8)
SOUL = mat("WA warden souls", (0.05, 0.55, 0.6), emit=1.6)              # the cyan soul spots (not the corps green)
ARMOUR_ALPHA = 0.8


def AT(look):
    k = (look, "armour")
    if k not in _tm:
        _tm[k] = strip_mat(f"WA {look} armour", strip_image("green", look), 4, emit=1.2, alpha=ARMOUR_ALPHA)
    return _tm[k]


def skin_warden(tag, loc):
    """The real warden, opaque, vanilla proportions. Returns the pivots so armour can ride on them."""
    root = empty(f"{tag} root", loc); turner = empty(f"{tag} turner", (0, 0, 0), root)
    q = P
    hips = empty(f"{tag} hips", (0, 0, 13 * q), turner)
    body = empty(f"{tag} body", (0, 0, 0), hips)
    box(f"{tag} body box", (-9 * q, -5.5 * q, 0), (9 * q, 5.5 * q, 21 * q), SKIN, body)
    for k in range(4):                                   # ribcage on the chest, souls behind it
        z = 7 + k * 2.6
        box(f"{tag} rib {k}", (-6 * q, -5.62 * q, z * q), (6 * q, -5.5 * q, (z + 1.0) * q), SKIN_DARK, body)
    for sx, z in ((-3, 9.5), (3, 12.0), (0, 14.6), (-2, 6.8)):
        box(f"{tag} soul {sx} {z}", ((sx - 1) * q, -5.64 * q, z * q), ((sx + 1) * q, -5.5 * q, (z + 1.2) * q), SOUL, body)
    head = empty(f"{tag} head", (0, 0, 21 * q), body)
    box(f"{tag} head box", (-8 * q, -5 * q, 0), (8 * q, 5 * q, 16 * q), SKIN, head)
    tendrils = []
    for sx in (-1, 1):
        td = empty(f"{tag} tendril {sx}", (sx * 8 * q, 0, 12 * q), head)
        x0, x1 = (0, 16 * q) if sx > 0 else (-16 * q, 0)
        box(f"{tag} tendril box {sx}", (x0, -0.5 * q, -2 * q), (x1, 0.5 * q, 10 * q), SKIN, td)
        box(f"{tag} tendril soul {sx}", (x0 + 2 * q, -0.52 * q, 2 * q), (x1 - 2 * q, 0.52 * q, 6 * q), SOUL, td)
        tendrils.append((td, sx))
    arms, legs = [], []
    for sx in (-1, 1):
        sh = empty(f"{tag} shoulder {sx}", (sx * 13 * q, 0, 19 * q), body)
        box(f"{tag} arm box {sx}", (-4 * q, -4 * q, -28 * q), (4 * q, 4 * q, 0), SKIN, sh)
        arms.append((sh, sx))
        lg = empty(f"{tag} leg {sx}", (sx * 5.9 * q, 0, 0), hips)
        box(f"{tag} leg box {sx}", (-3 * q, -3 * q, -13 * q), (3 * q, 3 * q, 0), SKIN, lg)
        legs.append((lg, sx))
    for f in range(1, FRAME_END + 1, 2):
        a = f * 0.18
        for sh, sx in arms:
            key(sh, f, rot=(R(18 * math.sin(a + (0 if sx > 0 else math.pi))), 0, 0))
        for lg, sx in legs:
            key(lg, f, rot=(R(20 * math.sin(a + (math.pi if sx > 0 else 0))), 0, 0))
        key(hips, f, loc=(0, 0, 13 * q + 0.03 * abs(math.sin(a))))
        for td, sx in tendrils:
            key(td, f, rot=(0, R(sx * 12 * math.sin(a * 1.3)), 0))
        key(head, f, rot=(R(3 * math.sin(a)), 0, 0))
    turn(turner)
    return {"body": body, "head": head, "tendrils": tendrils, "arms": arms, "legs": legs}


def slabs(tag, a, b, gap, t, m, parent, top=False, bottom=False, uvt=0.6):
    """Plate armour around an inner box a-b: four side plates standing `gap` px off the skin, `t` px thick.
    The +-Y plates span the full width, the +-X plates sit between them, so no two plates overlap (no z-fight)."""
    q = P; g = gap * q; tt = t * q
    a = np.array(a, float) * q; b = np.array(b, float) * q
    xo0, xo1 = a[0] - g - tt, b[0] + g + tt
    yi0, yi1 = a[1] - g, b[1] + g
    out = [box(f"{tag} front", (xo0, yi0 - tt, a[2]), (xo1, yi0, b[2]), m, parent, uvt),
           box(f"{tag} back", (xo0, yi1, a[2]), (xo1, yi1 + tt, b[2]), m, parent, uvt),
           box(f"{tag} side -", (xo0, yi0, a[2]), (a[0] - g, yi1, b[2]), m, parent, uvt),
           box(f"{tag} side +", (b[0] + g, yi0, a[2]), (xo1, yi1, b[2]), m, parent, uvt)]
    if top:
        out.append(box(f"{tag} top", (xo0, yi0 - tt, b[2] + g), (xo1, yi1 + tt, b[2] + g + tt), m, parent, uvt))
    if bottom:
        out.append(box(f"{tag} bottom", (xo0, yi0 - tt, a[2] - g - tt), (xo1, yi1 + tt, a[2] - g), m, parent, uvt))
    return out


def pb(tag, a, b, m, parent, uvt=0.6):
    """A plain plate box given in pixels."""
    return box(tag, tuple(np.array(a, float) * P), tuple(np.array(b, float) * P), m, parent, uvt)



# ------------------------------------------------------------------ 846: six new siblings of R1b and R1h (all H1 hex)
q = P
G = 1.5                                              # the stand-off J liked: 1.5 px off the skin


def recenter(o, anchor="c"):
    """Move the object's origin to its mesh centre (or the bottom / top centre) without moving the mesh."""
    vs = np.array([tuple(v.co) for v in o.data.vertices]); lo, hi = vs.min(0), vs.max(0); c = (lo + hi) / 2
    if anchor == "bottom":
        c[2] = lo[2]
    elif anchor == "top":
        c[2] = hi[2]
    c = Vector(c)
    for v in o.data.vertices:
        v.co = v.co - c
    o.location = Vector(o.location) + o.rotation_euler.to_matrix() @ c
    return o


def rbox(tag, c, s, m, parent, rot=(0, 0, 0), uvt=0.6):
    """A plate given by centre c and size s in pixels (parent space), origin at its centre, rotated rot degrees."""
    h = np.array(s, float) * q / 2
    o = box(tag, tuple(-h), tuple(h), m, parent, uvt)
    o.location = tuple(np.array(c, float) * q); o.rotation_euler = tuple(R(a) for a in rot)
    return o


def wcenter(o):
    return o.matrix_world @ Vector(np.mean([tuple(v.co) for v in o.data.vertices], axis=0))


def order_frames(parts, f0, f1, val, jitter=1):
    bpy.context.view_layer.update()
    vals = [val(o) for o in parts]; lo, hi = min(vals), max(vals) + 1e-6
    return [int(round(f0 + (v - lo) / (hi - lo) * (f1 - f0))) + int(rng.integers(0, jitter + 1)) for v in vals]


def base(o):
    return Vector(o.location), Euler(o.rotation_euler), tuple(o.scale)


def to_local(o, w):
    """A world direction into the object's parent space (parents carry no scale)."""
    return o.parent.matrix_world.to_3x3().inverted() @ w if o.parent else w


# --- six ways of forming (each take forms differently)
def form_wrap(parts, f0, f1):
    """R1b1: each lame twists round its limb into place, rising a little, bottom up."""
    for o, fa in zip(parts, order_frames(parts, f0 + 4, f1 - 1, lambda o: wcenter(o).z)):
        L, E, S = base(o)
        tw = Euler((E.x, E.y, E.z + R(120))); mid = Euler((E.x, E.y, E.z + R(35)))
        key(o, 1, loc=L - Vector((0, 0, 0.12)), rot=tw, sc=0.0001); key(o, fa - 6, loc=L - Vector((0, 0, 0.12)), rot=tw, sc=0.0001)
        key(o, fa - 3, loc=L - Vector((0, 0, 0.04)), rot=mid, sc=S); key(o, fa, loc=L, rot=E, sc=S)


def form_fly(parts, root, f0, f1):
    """R1b2: loose tiles fly in from 1.4 m out in random order and lock on with a small kick."""
    bpy.context.view_layer.update()
    rp = root.matrix_world.translation
    for o, fa in zip(parts, order_frames(parts, f0 + 5, f1, lambda o: rng.random())):
        recenter(o); bpy.context.view_layer.update()
        L, E, S = base(o)
        d = wcenter(o) - rp; d.z = 0
        d = (d.normalized() if d.length > 1e-4 else Vector((0, -1, 0))) * 1.4 + Vector((0, 0, 0.35))
        off = to_local(o, d)
        key(o, 1, loc=L + off, sc=0.0001); key(o, fa - 5, loc=L + off, sc=0.0001); key(o, fa - 4, loc=L + off, sc=S)
        key(o, fa - 1, loc=L - off * 0.03, sc=S); key(o, fa + 1, loc=L, sc=S)


def form_frame(struts, plates, f0, f1):
    """R1b3: the frame draws first (each strut grows from its foot), then the plates roll down over it from the top."""
    for o, fa in zip(struts, order_frames(struts, f0 + 3, f0 + 10, lambda o: wcenter(o).z)):
        recenter(o, "bottom"); S = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, fa - 3, sc=0.0001); key(o, fa - 2, sc=(1, 1, 0.03)); key(o, fa, sc=S)
    for o, fa in zip(plates, order_frames(plates, f0 + 9, f1, lambda o: -wcenter(o).z)):
        recenter(o, "top"); S = tuple(o.scale)
        key(o, 1, sc=0.0001); key(o, fa - 4, sc=0.0001); key(o, fa - 3, sc=(1, 1, 0.03)); key(o, fa, sc=(1, 1, 1.06))
        key(o, fa + 2, sc=S)


def form_slam(parts, f0, f1):
    """R1h1: plates drop from a block above and slam on, helm first, with a small bounce."""
    for o, fa in zip(parts, order_frames(parts, f0 + 5, f1 - 2, lambda o: -wcenter(o).z)):
        recenter(o); bpy.context.view_layer.update()
        L, E, S = base(o); up = to_local(o, Vector((0, 0, 1.0)))
        key(o, 1, loc=L + up, sc=0.0001); key(o, fa - 5, loc=L + up, sc=0.0001); key(o, fa - 4, loc=L + up, sc=S)
        key(o, fa - 1, loc=L + up * 0.25, sc=S); key(o, fa, loc=L, sc=(S[0] * 1.06, S[1] * 1.06, S[2] * 0.9))
        key(o, fa + 1, loc=L + up * 0.025, sc=S); key(o, fa + 3, loc=L, sc=S)


def form_radial(parts, chest, f0, f1, pixm, tag):
    """R1h2: armour grows out from the chest: hex pixels stream from the sternum and each plate swells in, overshooting."""
    bpy.context.view_layer.update()
    c0 = chest.matrix_world.translation.copy(); pm = pixel_mesh(pixm)
    for o, fa in zip(parts, order_frames(parts, f0 + 4, f1 - 2, lambda o: (wcenter(o) - c0).length)):
        recenter(o); S = tuple(o.scale); p = wcenter(o)
        key(o, 1, sc=0.0001); key(o, fa - 3, sc=0.0001); key(o, fa, sc=tuple(s * 1.18 for s in S)); key(o, fa + 2, sc=S)
        if rng.random() < 0.45:
            px = link(bpy.data.objects.new(f"{tag} pixel", pm)); fs = max(2, fa - 6)
            key(px, 1, loc=c0, sc=0.0001); key(px, fs, loc=c0, sc=0.0001); key(px, fs + 1, loc=c0, sc=1.0)
            key(px, fa - 2, loc=p, sc=0.8); key(px, fa - 1, loc=p, sc=0.0001)


def form_extrude(parts, root, f0, f1):
    """R1h3: plates push up out of the skin and stand off, splitting open from the sternum out to the limbs."""
    bpy.context.view_layer.update()
    r0 = root.matrix_world.translation.copy()
    for o, fa in zip(parts, order_frames(parts, f0 + 4, f1 - 2, lambda o: (wcenter(o) - r0).xy.length + 0.3 * abs(wcenter(o).z - 1.3))):
        recenter(o)
        L, E, S = base(o); d = Vector((L.x, L.y, 0))
        d = d.normalized() if d.length > 1e-4 else Vector((0, -1, 0))
        key(o, 1, loc=L - d * 0.09, sc=0.0001); key(o, fa - 4, loc=L - d * 0.09, sc=0.0001)
        key(o, fa - 3, loc=L - d * 0.09, sc=tuple(s * 0.6 for s in S)); key(o, fa - 1, loc=L + d * 0.035, sc=tuple(s * 1.05 for s in S))
        key(o, fa + 1, loc=L, sc=S)


# --- the six armours (front of the warden is -Y)
def tendril_x(sx, a, b):
    return (a, b) if sx > 0 else (-b, -a)


def lamellar(tag, rig, m):
    """R1b1: horizontal lames, each 3 px tall with 0.5 px gaps; every lower lame flares 0.4 px further out, so the
    torso flares into a skirt and the shoulders step outward. Tendril guards split into three upright strips."""
    parts, body, head = [], rig["body"], rig["head"]
    for i, (z0, z1) in enumerate(((18, 21), (14.5, 17.5), (11, 14), (7.5, 10.5), (4, 7))):
        parts += slabs(f"{tag} lame {i}", (-9, -5.5, z0), (9, 5.5, z1), G + 0.4 * i, 1.0, m, body)
    parts += slabs(f"{tag} fauld 0", (-9, -5.5, 0.5), (9, 5.5, 3.5), G + 2.4, 1.0, m, body)
    parts += slabs(f"{tag} fauld 1", (-9, -5.5, -3), (9, 5.5, 0), G + 3.0, 1.0, m, body)
    parts += slabs(f"{tag} collar", (-7.5, -5.5, 21.5), (7.5, 5.5, 23.5), G, 1.0, m, body)
    for i, (z0, z1, top) in enumerate(((12.5, 16, True), (8.5, 12, False), (4.5, 8, False))):
        parts += slabs(f"{tag} helm lame {i}", (-8, -5, z0), (8, 5, z1), G + 0.4 * i, 1.0, m, head, top=top)
    for td, sx in rig["tendrils"]:
        for j, (a, b) in enumerate(((1.5, 5.5), (6, 10), (10.5, 14.5))):
            x0, x1 = tendril_x(sx, a, b); h = 9 - j * 0.8
            parts.append(pb(f"{tag} tendril strip f {sx} {j}", (x0, -0.5 - G - 1, -1), (x1, -0.5 - G, h), m, td))
            parts.append(pb(f"{tag} tendril strip b {sx} {j}", (x0, 0.5 + G, -1), (x1, 0.5 + G + 1, h), m, td))
    for sh, sx in rig["arms"]:
        for i, (z0, z1) in enumerate(((-1, 2.5), (-4.5, -1.5), (-8, -5))):
            parts += slabs(f"{tag} spaulder {sx} {i}", (-4, -4, z0), (4, 4, z1), G + 0.6 * i, 1.0, m, sh, top=(i == 0))
        for i, (z0, z1) in enumerate(((-12, -9), (-15.5, -12.5), (-19, -16))):
            parts += slabs(f"{tag} vambrace {sx} {i}", (-4, -4, z0), (4, 4, z1), G + 0.3 * i, 1.0, m, sh)
        parts += slabs(f"{tag} gauntlet {sx}", (-4, -4, -28), (4, 4, -20), G + 0.6, 1.5, m, sh, bottom=True)
    for lg, sx in rig["legs"]:
        for i, (z0, z1) in enumerate(((-5, -2), (-9, -5.5), (-13, -9.5))):
            parts += slabs(f"{tag} leg lame {sx} {i}", (-3, -3, z0), (3, 3, z1), G + 0.3 * i, 1.0, m, lg)
    return parts


def tile_wall(tag, par, face, a, b, nu, nv, m, gap=G, t=1.0, relief=0.7, sp=0.8, skip=()):
    """Loose square tiles over one face of an inner box (pixels): nu x nv tiles, sp px apart, standing gap px off,
    every other tile raised `relief` px more (checker relief). Corners stay open."""
    a = np.array(a, float); b = np.array(b, float); out = []
    ax = 1 if face[1] == "y" else 0; sg = -1 if face[0] == "-" else 1; ua = 1 - ax
    du = (b[ua] - a[ua] - sp * (nu - 1)) / nu; dv = (b[2] - a[2] - sp * (nv - 1)) / nv
    for i in range(nu):
        for j in range(nv):
            if (i, j) in skip:
                continue
            r = relief if (i + j) % 2 else 0.0
            s0 = (a[ax] if sg < 0 else b[ax]) + sg * (gap + r); s1 = s0 + sg * t
            lo, hi = np.zeros(3), np.zeros(3)
            lo[ua] = a[ua] + i * (du + sp); hi[ua] = lo[ua] + du
            lo[2] = a[2] + j * (dv + sp); hi[2] = lo[2] + dv
            lo[ax], hi[ax] = min(s0, s1), max(s0, s1)
            out.append(pb(f"{tag} tile {face} {i} {j}", lo, hi, m, par))
    return out


def tiles(tag, rig, m):
    """R1b2: loose tiles, a checker of raised and set-back hex tiles with open seams, and tall swept wing pauldrons
    angled out over the shoulders. Lighter, spikier silhouette than R1b."""
    parts, body, head = [], rig["body"], rig["head"]
    parts += tile_wall(f"{tag} chest", body, "-y", (-9, -5.5, 5), (9, 5.5, 21), 3, 4, m)
    parts += tile_wall(f"{tag} back", body, "+y", (-9, -5.5, 5), (9, 5.5, 21), 3, 4, m)
    parts += tile_wall(f"{tag} hip", body, "-y", (-9, -5.5, 0), (9, 5.5, 4), 4, 1, m, gap=G + 1.0)
    parts += tile_wall(f"{tag} hip back", body, "+y", (-9, -5.5, 0), (9, 5.5, 4), 4, 1, m, gap=G + 1.0)
    parts += tile_wall(f"{tag} face", head, "-y", (-8, -5, 1), (8, 5, 16), 3, 3, m, skip=((1, 1),))   # open visor
    parts += tile_wall(f"{tag} nape", head, "+y", (-8, -5, 1), (8, 5, 16), 3, 3, m)
    for sx in (-1, 1):
        parts += tile_wall(f"{tag} cheek {sx}", head, "+x" if sx > 0 else "-x", (-8, -5, 0), (8, 5, 9), 2, 2, m)
    for k, x in enumerate((-5, 0, 5)):                    # a row of crown tiles
        parts.append(rbox(f"{tag} crown {k}", (x, 0, 16 + G + 0.6 + (0.6 if k == 1 else 0)), (4.2, 9, 1.2), m, head))
    for td, sx in rig["tendrils"]:
        for side in ("-y", "+y"):
            a = (1.5, -0.5, -1) if sx > 0 else (-15.5, -0.5, -1); b = (15.5, 0.5, 9) if sx > 0 else (-1.5, 0.5, 9)
            parts += tile_wall(f"{tag} tendril {sx}", td, side, a, b, 3, 2, m, relief=0.5)
    for sh, sx in rig["arms"]:
        so = "+x" if sx > 0 else "-x"
        parts.append(rbox(f"{tag} wing {sx}", (sx * 7.2, 0, 0.5), (1.2, 10, 11), m, sh, rot=(0, sx * 22, 0)))
        parts.append(rbox(f"{tag} wing tip {sx}", (sx * 10.2, 0, 7.2), (1.0, 7, 5.5), m, sh, rot=(0, sx * 42, 0)))
        for face in ("-y", "+y"):
            parts += tile_wall(f"{tag} upper arm {sx}", sh, face, (-4, -4, -10), (4, 4, -5), 2, 1, m)
            parts += tile_wall(f"{tag} forearm {sx}", sh, face, (-4, -4, -27), (4, 4, -12), 2, 3, m)
        parts += tile_wall(f"{tag} forearm out {sx}", sh, so, (-4, -4, -27), (4, 4, -12), 2, 3, m)
        parts.append(pb(f"{tag} fist cap {sx}", (-4.5, -4.5, -28 - G - 1), (4.5, 4.5, -28 - G), m, sh))
    for lg, sx in rig["legs"]:
        so = "+x" if sx > 0 else "-x"
        for face in ("-y", "+y", so):
            parts += tile_wall(f"{tag} leg {sx} {face}", lg, face, (-3, -3, -12.5), (3, 3, -1), 1, 2, m, relief=0.0)
        parts.append(pb(f"{tag} knee tile {sx}", (-2, -3 - G - 2.2, -7), (2, -3 - G - 1.2, -4), m, lg))
    return parts


def frame_armour(tag, rig, m):
    """R1b3: an exo-frame of 1 px rods standing outside narrower plates: three ribs and two hoops on the chest, a high
    collar and three swept spines on the back, visor bars, rods down the shoulders, forearms and shins.
    Returns (struts, plates)."""
    st, pl, body, head = [], [], rig["body"], rig["head"]
    yf = -5.5 - G - 1                                    # outer face of the chest plate
    pl.append(pb(f"{tag} chest plate", (-7.5, yf, 6), (7.5, -5.5 - G, 20), m, body))
    pl.append(pb(f"{tag} back plate", (-7.5, 5.5 + G, 6), (7.5, 5.5 + G + 1, 17.5), m, body))
    pl.append(pb(f"{tag} collar", (-8, 5.5 + G, 18), (8, 5.5 + G + 1, 29), m, body))
    pl += slabs(f"{tag} fauld", (-9, -5.5, 0), (9, 5.5, 4.5), G + 0.5, 1.0, m, body)
    for x in (-7, 0, 7):
        st.append(pb(f"{tag} rib {x}", (x - 0.5, yf - 1.5, 4.5), (x + 0.5, yf - 0.5, 22), m, body))
    for z in (9, 16):
        st.append(pb(f"{tag} hoop {z}", (-8.5, yf - 2.6, z), (8.5, yf - 1.6, z + 1), m, body))
    for x in (-5, 0, 5):
        st.append(rbox(f"{tag} spine {x}", (x, 9.8, 24), (1.2, 1.2, 14), m, body, rot=(-28, 0, 0)))
    pl += slabs(f"{tag} helm", (-8, -5, 3), (8, 5, 16), G, 1.0, m, head, top=True)
    for z in (7, 10):
        st.append(pb(f"{tag} visor bar {z}", (-7, -5 - G - 2, z), (7, -5 - G - 1.2, z + 0.8), m, head))
    st.append(pb(f"{tag} crest rod", (-0.5, -5, 16 + G + 1.4), (0.5, 5, 16 + G + 2.4), m, head))
    for td, sx in rig["tendrils"]:
        x0, x1 = tendril_x(sx, 1.5, 15.5)
        pl.append(pb(f"{tag} tendril guard f {sx}", (x0, -0.5 - G - 1, -1), (x1, -0.5 - G, 9), m, td))
        pl.append(pb(f"{tag} tendril guard b {sx}", (x0, 0.5 + G, -1), (x1, 0.5 + G + 1, 9), m, td))
        st.append(pb(f"{tag} tendril rod {sx}", (x0, -0.5, 9 + G), (x1, 0.5, 9 + G + 1), m, td))
    for sh, sx in rig["arms"]:
        pl += slabs(f"{tag} pauldron {sx}", (-4, -4, -6), (4, 4, 1), G, 1.0, m, sh, top=True)
        xo = (4 + G + 1.6, 4 + G + 2.6) if sx > 0 else (-(4 + G + 2.6), -(4 + G + 1.6))
        for y in (-3, 3):
            st.append(pb(f"{tag} shoulder rod {sx} {y}", (xo[0], y - 0.5, -9), (xo[1], y + 0.5, 3.5), m, sh))
            st.append(pb(f"{tag} forearm rod {sx} {y}", (xo[0], y - 0.5, -27), (xo[1], y + 0.5, -11), m, sh))
        pl += slabs(f"{tag} bracer {sx}", (-4, -4, -21), (4, 4, -12), G, 1.0, m, sh)
        pl += slabs(f"{tag} gauntlet {sx}", (-4, -4, -28), (4, 4, -23), G + 0.5, 1.2, m, sh, bottom=True)
    for lg, sx in rig["legs"]:
        pl += slabs(f"{tag} greave {sx}", (-3, -3, -12), (3, 3, -6), G, 1.0, m, lg)
        st.append(pb(f"{tag} shin rod {sx}", (-0.5, -3 - G - 2.2, -13), (0.5, -3 - G - 1.2, -1), m, lg))
    return st, pl


def bastion(tag, rig, m):
    """R1h1: a bastion: 2 px thick plates 2 px off, a chest boss, a tall gorget, a long tasset skirt, a great helm with
    three visor bars, three-tier bell pauldrons flaring out as they go down, big gauntlets."""
    parts, body, head = [], rig["body"], rig["head"]
    parts += slabs(f"{tag} cuirass", (-9, -5.5, 4), (9, 5.5, 21), 2, 2, m, body)
    parts.append(pb(f"{tag} boss", (-5, -5.5 - 4 - 2, 9), (5, -5.5 - 4, 17), m, body))
    parts += slabs(f"{tag} gorget", (-7.5, -5.5, 21), (7.5, 5.5, 24), G, 1.5, m, body)
    parts += slabs(f"{tag} tasset", (-9, -5.5, -7), (9, 5.5, 3.5), 3, 1.5, m, body)
    parts += slabs(f"{tag} great helm", (-8, -5, 3.5), (8, 5, 16), 2, 2, m, head, top=True)
    for z in (7, 9.4, 11.8):
        parts.append(pb(f"{tag} visor bar {z}", (-7, -5 - 4 - 1.3, z), (7, -5 - 4, z + 0.9), m, head))
    for td, sx in rig["tendrils"]:
        x0, x1 = tendril_x(sx, 1.5, 15.5)
        parts.append(pb(f"{tag} tendril guard f {sx}", (x0, -0.5 - G - 2, -1.5), (x1, -0.5 - G, 9), m, td))
        parts.append(pb(f"{tag} tendril guard b {sx}", (x0, 0.5 + G, -1.5), (x1, 0.5 + G + 2, 9), m, td))
        parts.append(pb(f"{tag} tendril cap {sx}", (x0, -0.5 - G - 2, 9 + G), (x1, 0.5 + G + 2, 9 + G + 1.5), m, td))
    for sh, sx in rig["arms"]:
        parts += slabs(f"{tag} pauldron 0 {sx}", (-4, -4, -3), (4, 4, 2), 2, 2, m, sh, top=True)
        parts += slabs(f"{tag} pauldron 1 {sx}", (-4, -4, -6.5), (4, 4, -3.5), 4, 1.5, m, sh)
        parts += slabs(f"{tag} pauldron 2 {sx}", (-4, -4, -10), (4, 4, -7), 5.5, 1.5, m, sh)
        parts += slabs(f"{tag} bracer {sx}", (-4, -4, -20.5), (4, 4, -12), 2, 1.5, m, sh)
        parts += slabs(f"{tag} gauntlet {sx}", (-4, -4, -28), (4, 4, -22), 2.5, 2.5, m, sh, bottom=True)
        parts.append(pb(f"{tag} knuckles {sx}", (-4.5, -4 - 5 - 1.5, -27), (4.5, -4 - 5, -24), m, sh))
    for lg, sx in rig["legs"]:
        parts += slabs(f"{tag} greave {sx}", (-3, -3, -13), (3, 3, -6), G, 1.2, m, lg)
        parts.append(pb(f"{tag} knee cop {sx}", (-3, -3 - G - 1.2 - 2.5, -6.5), (3, -3 - G - 1.2, -2.5), m, lg))
    return parts


def carapace(tag, rig, m):
    """R1h2: a hunched juggernaut: a three-layer carapace stepping out from the back and rising over the head, a hood
    with a peak, swept tendril fins, huge fist cuffs and thick knee cops. Lighter chest, all the weight on the back."""
    parts, body, head = [], rig["body"], rig["head"]
    parts.append(pb(f"{tag} chest", (-9 - G - 1.5, -5.5 - G - 1.5, 6), (9 + G + 1.5, -5.5 - G, 21), m, body))
    for sx in (-1, 1):
        x0, x1 = (9 + G, 9 + G + 1.5) if sx > 0 else (-9 - G - 1.5, -9 - G)
        parts.append(pb(f"{tag} flank {sx}", (x0, -5.5 - G, 6), (x1, 5.5 + G, 21), m, body))
    for i, (x, y0, y1, z0, z1) in enumerate(((9, 5.5 + G, 5.5 + G + 2.5, 2, 33), (8, 9.4, 11.6, 6, 38.5), (5, 12, 14, 13, 33))):
        parts.append(pb(f"{tag} carapace {i}", (-x, y0, z0), (x, y1, z1), m, body))
    parts += slabs(f"{tag} fauld", (-9, -5.5, 0), (9, 5.5, 5), G + 0.5, 1.2, m, body)
    parts += slabs(f"{tag} hood", (-8, -5, 2), (8, 5, 16), G, 1.5, m, head, top=True)
    parts.append(pb(f"{tag} hood peak", (-9, -5 - G - 1.5 - 4, 14.5), (9, -5 - G - 1.5, 16.5), m, head))
    for td, sx in rig["tendrils"]:
        x0, x1 = tendril_x(sx, 1.5, 15.5)
        parts.append(pb(f"{tag} tendril guard f {sx}", (x0, -0.5 - G - 1.2, -1), (x1, -0.5 - G, 8.5), m, td))
        parts.append(pb(f"{tag} tendril guard b {sx}", (x0, 0.5 + G, -1), (x1, 0.5 + G + 1.2, 8.5), m, td))
        parts.append(rbox(f"{tag} tendril fin {sx}", (sx * 9.5, 1.5, 11.5), (15, 4, 1.4), m, td, rot=(0, -sx * 10, 0)))
    for sh, sx in rig["arms"]:
        parts += slabs(f"{tag} pauldron {sx}", (-4, -4, -6), (4, 4, 1), 2, 1.5, m, sh, top=True)
        parts += slabs(f"{tag} bracer {sx}", (-4, -4, -19), (4, 4, -11), G, 1.2, m, sh)
        parts += slabs(f"{tag} fist cuff {sx}", (-4, -4, -28), (4, 4, -20), 2.5, 3, m, sh, bottom=True)
    for lg, sx in rig["legs"]:
        parts += slabs(f"{tag} greave {sx}", (-3, -3, -12.5), (3, 3, -7.5), G, 1.0, m, lg)
        parts.append(pb(f"{tag} knee cop {sx}", (-3.5, -3 - G - 1 - 3, -7.5), (3.5, -3 - G - 1, -2), m, lg))
    return parts


def spiked(tag, rig, m):
    """R1h3: heavy plate with points: chevrons on the chest, a row of spine fins, two-segment horns on the helm,
    tendril guards running out into stepped blades, spiked pauldrons, elbow and knee spikes."""
    parts, body, head = [], rig["body"], rig["head"]
    parts += slabs(f"{tag} cuirass", (-9, -5.5, 5), (9, 5.5, 21), G, 1.5, m, body)
    yf = -5.5 - G - 1.5
    for z in (13, 17.5):
        for sx in (-1, 1):
            parts.append(rbox(f"{tag} chevron {z} {sx}", (sx * 4.3, yf - 0.7, z), (9, 1.2, 2.4), m, body, rot=(0, -sx * 28, 0)))
    for k, (z, h) in enumerate(((6, 2.5), (10, 3.5), (14, 4.2), (18, 3.5))):
        parts.append(pb(f"{tag} spine fin {k}", (-0.6, 5.5 + G + 1.5, z), (0.6, 5.5 + G + 1.5 + h, z + 3), m, body))
    parts += slabs(f"{tag} fauld", (-9, -5.5, 0), (9, 5.5, 4.5), G + 0.5, 1.2, m, body)
    parts += slabs(f"{tag} helm", (-8, -5, 2), (8, 5, 16), G, 1.5, m, head, top=True)
    parts.append(pb(f"{tag} brow", (-9.5, -5 - G - 1.5 - 1.6, 9), (9.5, -5 - G - 1.5, 11), m, head))
    for sx in (-1, 1):
        parts.append(rbox(f"{tag} horn {sx}", (sx * 6.5, -1, 22.4), (1.8, 1.8, 7), m, head, rot=(0, sx * 30, 0)))
        parts.append(rbox(f"{tag} horn tip {sx}", (sx * 9.9, -1, 26.6), (1.2, 1.2, 4), m, head, rot=(0, sx * 55, 0)))
    for td, sx in rig["tendrils"]:
        x0, x1 = tendril_x(sx, 1.5, 15.5)
        parts.append(pb(f"{tag} tendril guard f {sx}", (x0, -0.5 - G - 1, -1), (x1, -0.5 - G, 9), m, td))
        parts.append(pb(f"{tag} tendril guard b {sx}", (x0, 0.5 + G, -1), (x1, 0.5 + G + 1, 9), m, td))
        b0, b1 = tendril_x(sx, 16.5, 19.5); c0, c1 = tendril_x(sx, 19.5, 22)
        parts.append(pb(f"{tag} tendril blade {sx}", (b0, -0.5, 0.5), (b1, 0.5, 8), m, td))
        parts.append(pb(f"{tag} tendril blade tip {sx}", (c0, -0.5, 2.5), (c1, 0.5, 6), m, td))
    for sh, sx in rig["arms"]:
        parts += slabs(f"{tag} pauldron {sx}", (-4, -4, -6), (4, 4, 1), 2, 2, m, sh, top=True)
        for y, h in ((-3.5, 5), (0, 6.5), (3.5, 5)):
            parts.append(rbox(f"{tag} pauldron spike {sx} {y}", (sx * (3 + h * 0.17), y, 5 + h / 2), (1.4, 1.4, h), m, sh, rot=(0, sx * 20, 0)))
        parts += slabs(f"{tag} bracer {sx}", (-4, -4, -21), (4, 4, -11), G, 1.5, m, sh)
        parts.append(rbox(f"{tag} elbow spike {sx}", (0, 4 + G + 1.5 + 2, -12), (1.2, 4, 1.2), m, sh, rot=(15, 0, 0)))
        parts += slabs(f"{tag} gauntlet {sx}", (-4, -4, -28), (4, 4, -22), 2, 2, m, sh, bottom=True)
    for lg, sx in rig["legs"]:
        parts += slabs(f"{tag} greave {sx}", (-3, -3, -12.5), (3, 3, -7), G, 1.2, m, lg)
        parts.append(pb(f"{tag} knee cop {sx}", (-3, -3 - G - 1.2 - 2, -7), (3, -3 - G - 1.2, -2.5), m, lg))
        parts.append(rbox(f"{tag} knee spike {sx}", (0, -3 - G - 1.2 - 2 - 1.8, -4.8), (1.2, 4, 1.2), m, lg, rot=(-20, 0, 0)))
    return parts


# The armour forms over the bare warden in 1 s (frames 12-32), each take a different way, then it walks and turns.
FORM0, FORM1 = 12, 32
TAKES = [("R1b1", "H1 hex lamellar: flaring lames, twists on", "b"),
         ("R1b2", "H1 hex loose tiles + wing pauldrons, fly in", "b"),
         ("R1b3", "H1 hex exo-frame over plates: frame draws, plates roll down", "b"),
         ("R1h1", "H1 hex bastion: tiered pauldrons, skirt, great helm, slam on", "h"),
         ("R1h2", "H1 hex hunched carapace + hood, grows from the chest", "h"),
         ("R1h3", "H1 hex spiked heavy plate, pushes out of the skin", "h")]
ROWS = {"b": 0.0, "h": 60.0}                         # far apart, so see-through armour never hides another row
SPACE = 10.0
_col = {"b": 0, "h": 0}
m = AT("h1")
for k, nm, row in TAKES:
    i = _col[row]; _col[row] += 1
    x = ROWS[row] + i * SPACE; y = 0.0
    box(f"WA {k} pad", (x - 2.6, y - 2.2, -0.02), (x + 2.6, y + 2.2, 0), FLOOR)
    rig = skin_warden(f"WA {k}", (x, y, 0))
    t = f"WA {k}"
    bpy.context.view_layer.update()
    if k == "R1b1":
        form_wrap(lamellar(t, rig, m), FORM0, FORM1)
    elif k == "R1b2":
        form_fly(tiles(t, rig, m), bpy.data.objects[f"{t} root"], FORM0, FORM1)
    elif k == "R1b3":
        st, pl = frame_armour(t, rig, m); form_frame(st, pl, FORM0, FORM1)
    elif k == "R1h1":
        form_slam(bastion(t, rig, m), FORM0, FORM1)
    elif k == "R1h2":
        chest = empty(f"{t} sternum", (0, -5.5 * q, 14 * q), rig["body"])
        form_radial(carapace(t, rig, m), chest, FORM0, FORM1, CM["pix"], t)
    else:
        form_extrude(spiked(t, rig, m), bpy.data.objects[f"{t} root"], FORM0, FORM1)
    label(f"{k}  {nm}", (x, y - 2.5, 4.1), LBL, 0.12)
    cam(f"Cam {k}", (x + 4.6, y - 8.0, 3.2), (x, y, 1.7), 35)
cam("Cam row R1b", (10.0, -30.0, 4.6), (10.0, 0, 1.7), 40)
cam("Cam row R1h", (70.0, -30.0, 4.6), (70.0, 0, 1.7), 40)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam row R1b", 60, (0.3, 0.38, 0.5), 3.0



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
