# Pass 823: modern construct bows and arrows, and a bigger shield (Chat C, 2026-10-15, range 800-899).
# J on 808: "the shield is too small and the bow and arrow is broken and out of place it needs to shoot like an actual
# bow we will just make VERY in depth bow and arrow models, think modern day bow and arrows", then "there is also
# already a spear in the game we should just use that new one, scrap the rest of construct weapons".
# The shot, like a real archer (right-handed, ring on the draw hand):
#   1-14   the bow forms in the left hand from the ring's pixels; the arrow forms on the string at the ring hand
#   14-18  side-on stance, left shoulder to the target, head turned to it; bow arm comes up straight
#   18-32  draw: the right hand pulls the string straight back to the anchor under the jaw, elbow up behind,
#          the string bends to a V at the nock, the limbs flex
#   32-42  hold and aim (a little settle)
#   42     release: the string snaps forward and shivers, the arrow leaves at 5 blocks a tick and flies flat to a
#          target 18 blocks out (a slight drop), sticks; the draw hand follows through back along the jaw
#   42-60  follow-through, then the bow comes down
#   B1 compound bow: machined riser with cut-outs, split limbs, two cams with cables and a cable guard, a 3-pin sight,
#      whisker-biscuit rest, a front stabiliser with weights, a peep sight and D-loop on the string; carbon arrow with
#      three vanes, nock and field point
#   B2 Olympic recurve: long riser, limbs that curve forward and recurve back at the tips, a long front rod and a V-bar
#      with side rods, clicker, plunger, a sight on an extension bar; target arrow with spin vanes
#   B3 hunting compound: short and compact, 5-pin sight, a bow quiver with four broadhead arrows, short stabiliser,
#      wrist sling; arrow with a three-blade broadhead
# Shields (bigger, J: "too small"), each blocks a shot that breaks on it:
#   H1 big hex (1.1 blocks across, twice 808's)    H2 tower shield (0.9 x 1.6 blocks, covers the body)
#   H3 dome wall (a curved hex wall, 1.6 blocks, held out in front)
# Cameras "Cam <take>", "Cam <take> close" (bows), "Cam all". Builds LanternLive\combat\bows_shields.blend.
SCENE_NAME = "Bows and Shields"
OUT_REL = "combat/bows_shields.blend"
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
FLOOR = mat("BW floor", (0.2, 0.22, 0.24), rough=0.9)
STRAW = mat("BW target straw", (0.75, 0.62, 0.35), rough=0.9)
RINGS = [mat(f"BW target ring {i}", c, rough=0.7) for i, c in enumerate(((0.9, 0.9, 0.85), (0.08, 0.08, 0.1), (0.1, 0.3, 0.9), (0.9, 0.1, 0.1), (1.0, 0.85, 0.1)))]
SHOT = mat("BW shot", (0.6, 0.15, 0.1), emit=1.0)
BOARD = mat("BW board", (0.04, 0.05, 0.05), rough=0.8)
TXT = mat("BW text", (0.75, 1.0, 0.8), emit=1.2)
TXTH = mat("BW heading", (0.2, 1.0, 0.4), emit=2.2)
rng = np.random.default_rng(823)
CM = cmats("BW", "green")
G, W, RM, GR = CM["glass"], CM["glow"], CM["rim"], CM["grip"]
STR = mat("BW string", (0.1, 1.0, 0.3), emit=2.0)
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


def arrow(tag, par, broad=False, spin=False):
    """A modern arrow along local -Z (point forward): carbon shaft, insert, point, three vanes, nock. Nock at z=0."""
    root = empty(f"{tag} arrow", (0, 0, 0), par)
    cyl(f"{tag} shaft", 0.0065, 0.74, G, 8, root, loc=(0, 0, -0.74), axis="Z")
    cyl(f"{tag} wrap", 0.0075, 0.12, W, 8, root, loc=(0, 0, -0.14), axis="Z")
    cyl(f"{tag} insert", 0.0072, 0.03, RM, 8, root, loc=(0, 0, -0.77), axis="Z")
    if broad:
        cyl(f"{tag} ferrule", 0.009, 0.05, RM, 8, root, loc=(0, 0, -0.82), axis="Z", r2=0.004)
        for k in range(3):
            bl = box(f"{tag} blade {k}", (0, -0.0015, -0.87), (0.022, 0.0015, -0.79), RM, root)
            bl.rotation_euler = (0, 0, k * 2 * math.pi / 3)
    else:
        cyl(f"{tag} point", 0.0075, 0.035, RM, 8, root, loc=(0, 0, -0.81), axis="Z", r2=0.001)
    for k in range(3):                                       # three vanes, 120 deg apart (a slight helix on spin vanes)
        v = box(f"{tag} vane {k}", (0.006, -0.0008, -0.12), (0.02 if not spin else 0.016, 0.0008, -0.03), RM, root)
        v.rotation_euler = (0, R(3) if spin else 0, k * 2 * math.pi / 3)
    box(f"{tag} nock", (-0.006, -0.006, -0.012), (0.006, 0.006, 0.006), W, root)
    box(f"{tag} nock throat", (-0.0065, -0.0015, -0.002), (0.0065, 0.0015, 0.0065), GR, root)
    return root


def bow(tag, par, kind):
    """In the bow hand's frame: Y up, -Z toward the target, +Z toward the archer, X out to the side.
    Returns (root, top tip, bottom tip, brace z of the string, limb pivots)."""
    root = empty(f"{tag} bow", (0, 0, -0.02), par)
    flex = []
    if kind in ("B1", "B3"):
        H = 0.36 if kind == "B1" else 0.3                    # riser half-height
        bx_(tag, "grip", (-0.017, -0.05, -0.02), (0.017, 0.05, 0.03), GR, root)
        for sy in (-1, 1):                                   # riser: two rails with cut-outs and braces (a truss)
            bx_(tag, f"riser rail front {sy}", (-0.012, sy * 0.05, -0.06), (0.012, sy * H, -0.04), G, root) if sy > 0 else \
                bx_(tag, f"riser rail front {sy}", (-0.012, -H, -0.06), (0.012, -0.05, -0.04), G, root)
            ys = sorted((sy * 0.05, sy * H))
            bx_(tag, f"riser rail back {sy}", (-0.012, ys[0], 0.0), (0.012, ys[1], 0.02), G, root)
            for k in range(3):
                y = sy * (0.1 + k * (H - 0.12) / 3)
                bx_(tag, f"riser brace {sy} {k}", (-0.011, y - 0.008, -0.05), (0.011, y + 0.008, 0.01), RM if k == 1 else G, root)
            bx_(tag, f"limb pocket {sy}", (-0.022, min(sy * H, sy * (H + 0.04)), -0.06), (0.022, max(sy * H, sy * (H + 0.04)), 0.02), RM, root)
        # arrow rest (whisker biscuit ring), sight with pins, stabiliser, cable guard
        torus(f"{tag} rest", 0.022, 0.005, RM, parent=root, loc=(0, 0.075, -0.02), axis="Z")
        sb = empty(f"{tag} sight", (0.04, 0.13, -0.05), root)
        bx_(tag, "sight bracket", (-0.03, -0.01, 0.0), (0.0, 0.01, 0.08), G, sb)
        torus(f"{tag} sight housing", 0.03, 0.006, RM, parent=sb, loc=(0, 0, -0.03), axis="Z")
        for k in range(3 if kind == "B1" else 5):
            pin = bx_(tag, f"sight pin {k}", (0.0, 0.0, 0.0), (0.02, 0.003, 0.003), W, sb)
            pin.location = (-0.02, 0.016 - k * (0.032 / (2 if kind == "B1" else 4)), -0.032)
        L_st = 0.42 if kind == "B1" else 0.2
        cyl(f"{tag} stabiliser", 0.011, L_st, G, 10, root, loc=(0, -0.08, -0.06 - L_st), axis="Z")
        for k in range(3 if kind == "B1" else 2):
            cyl(f"{tag} stab weight {k}", 0.02, 0.018, RM, 12, root, loc=(0, -0.08, -0.06 - L_st - 0.02 - k * 0.022), axis="Z")
        cyl(f"{tag} cable guard", 0.004, 0.16, G, 6, root, loc=(0.02, -0.12, 0.02), axis="Z")
        if kind == "B3":                                     # a bow quiver with four broadhead arrows, and a wrist sling
            q = empty(f"{tag} quiver", (0.05, 0.0, 0.0), root)
            bx_(tag, "quiver hood", (-0.01, 0.2, -0.05), (0.03, 0.3, 0.03), G, q)
            bx_(tag, "quiver gripper", (-0.01, -0.2, -0.04), (0.03, -0.17, 0.02), RM, q)
            for k in range(4):
                a_ = arrow(f"{tag} quiver {k}", q, broad=True); a_.location = (0.012, 0.36, -0.03 + k * 0.012)
                a_.rotation_euler = (R(-90), 0, 0)
            torus(f"{tag} wrist sling", 0.04, 0.005, RM, parent=root, loc=(0, 0, 0.0), axis="Y")
        # split limbs to cams; each limb pair is a pivot so it can flex on the draw
        tips = []
        for sy in (-1, 1):
            lp = empty(f"{tag} limb {sy}", (0, sy * (H + 0.02), -0.02), root); flex.append((lp, sy))
            Ll = 0.26 if kind == "B1" else 0.22
            for sx in (-1, 1):
                y0, y1 = (0.0, Ll) if sy > 0 else (-Ll, 0.0)
                bx_(tag, f"limb {sy} {sx}", (sx * 0.014 - 0.006, y0, -0.008), (sx * 0.014 + 0.006, y1, 0.008), G, lp)
            lp.rotation_euler = (R(-sy * 28), 0, 0)              # limbs swept back toward the archer
            cam_ = empty(f"{tag} cam {sy}", (0, sy * Ll, 0), lp)
            cyl(f"{tag} cam wheel {sy}", 0.038, 0.016, RM, 16, cam_, loc=(-0.008, 0, 0), axis="X")
            cyl(f"{tag} cam module {sy}", 0.02, 0.018, W, 10, cam_, loc=(-0.009, 0.0, 0.01), axis="X")
            tips.append(cam_)
        brace = 0.17
    else:                                                    # B2 Olympic recurve
        H = 0.32
        bx_(tag, "grip", (-0.016, -0.06, -0.015), (0.016, 0.06, 0.035), GR, root)
        bx_(tag, "riser", (-0.013, -H, -0.05), (0.013, H, -0.01), G, root)
        bx_(tag, "riser window", (-0.014, 0.06, -0.012), (0.004, 0.2, 0.0), RM, root)
        bx_(tag, "plunger", (-0.03, 0.075, -0.035), (-0.012, 0.085, -0.02), W, root)
        bx_(tag, "clicker", (-0.016, 0.07, -0.13), (-0.013, 0.074, -0.03), RM, root)
        sb = empty(f"{tag} sight", (0.03, 0.15, -0.05), root)
        bx_(tag, "sight bar", (-0.006, -0.006, -0.3), (0.006, 0.006, 0.0), G, sb)
        torus(f"{tag} sight aperture", 0.012, 0.003, RM, parent=sb, loc=(0, 0.0, -0.3), axis="Z")
        cyl(f"{tag} long rod", 0.008, 0.7, G, 10, root, loc=(0, -0.08, -0.76), axis="Z")
        cyl(f"{tag} long rod weight", 0.018, 0.04, RM, 12, root, loc=(0, -0.08, -0.8), axis="Z")
        for sx in (-1, 1):                                   # V-bar and side rods
            sr = empty(f"{tag} side rod {sx}", (0, -0.1, -0.03), root); sr.rotation_euler = (R(-20), R(sx * 35), 0)
            cyl(f"{tag} side rod bar {sx}", 0.007, 0.3, G, 8, sr, loc=(0, 0, 0), axis="Z")
            cyl(f"{tag} side rod weight {sx}", 0.016, 0.03, RM, 10, sr, loc=(0, 0, 0.3), axis="Z")
        tips = []
        for sy in (-1, 1):
            lp = empty(f"{tag} limb {sy}", (0, sy * H, -0.03), root); flex.append((lp, sy))
            prev = lp; pos = (0, 0, 0)
            # four segments: out and forward, then recurving back at the tip
            for k, (ln, ang) in enumerate(((0.12, -12), (0.12, -10), (0.1, 6), (0.08, 28))):
                sgm = empty(f"{tag} limb seg {sy} {k}", pos, prev); sgm.rotation_euler = (R(sy * ang), 0, 0)
                bx_(tag, f"limb blade {sy} {k}", (-0.02 + 0.003 * k, min(0, sy * ln), -0.006), (0.02 - 0.003 * k, max(0, sy * ln), 0.006), G if k < 3 else RM, sgm)
                prev = sgm; pos = (0, sy * ln, 0)
            tip = empty(f"{tag} tip {sy}", pos, prev); tips.append(tip)
        brace = 0.21
    return root, tips, brace, flex


TAKES = [("B1", "compound bow", "B1"), ("B2", "Olympic recurve", "B2"), ("B3", "hunting compound", "B3"),
         ("H1", "big hex shield", "H1"), ("H2", "tower shield", "H2"), ("H3", "dome wall", "H3")]
dump = {"takes": {}}
for bi, (tk, name, kind) in enumerate(TAKES):
    bx = bi * BAY
    tag = f"BW {tk}"
    box(f"{tag} floor", (bx - 2.6, -3, -0.02), (bx + 2.6, 21, 0), FLOOR)
    M = player_mats(tag)
    M["ring"] = mat(f"{tag} ring face", (0.02, 0.85, 0.15), emit=1.6)
    if tk.startswith("B"):
        # side-on: the root turns so the left shoulder points down +Y at the target
        rig = make_player(tag, (bx, 0, 0), M, face=-math.pi / 2)
        aim_l = dict(arm_l=(90, 0, 90), fore_l=(0, 0, 0))
        HEAD = (-4, 0, 82)
        brace_pt = Vector((-18 * P + 0.22, -0.02, 22 * P + 0.02))
        anchor = Vector((-0.27, -0.03, 1.47))
        keys = [(1, {}),
                (F_UP, dict(head=(0, 0, 40), arm_l=(60, 0, 60), fore_l=(20, 0, 0), ik_r=(Vector((0.1, 0.25, 1.1)), "hand", [60, 0, 30, 60]))),
                (F_DRAW, dict(head=HEAD, **aim_l, ik_r=(brace_pt, "hand", [90, 0, 80, 20]))),
                (F_DRAW + 8, dict(head=HEAD, **aim_l, ik_r=(brace_pt.lerp(anchor, 0.75), "hand", [100, 0, 100, 90]))),
                (F_FULL, dict(head=HEAD, **aim_l, ik_r=(anchor, "hand", [100, 0, 100, 120]))),
                (F_REL, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.01, 0, 0)), "hand", [100, 0, 100, 120]))),
                (F_REL + 2, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.12, -0.02, 0.0)), "hand", [100, 0, 100, 120]))),
                (F_REL + 10, dict(head=HEAD, **aim_l, ik_r=(anchor + Vector((0.14, -0.03, -0.02)), "hand", [100, 0, 100, 120]))),
                (F_REL + 20, dict(head=(0, 0, 30), arm_l=(20, 0, 20), fore_l=(10, 0, 0)))]
        solved, errs = build_keys(keys)
        for f, p in solved:
            pp = dict(p); pp["root_loc"] = (bx, 0, 0); pose(rig, f, **pp)
        hl = empty(f"{tag} bow hand", (0, 0, -6 * P), rig["fore_l"])
        broot, tips, brace, flex = bow(tag, hl, kind)
        # the arrow: parented to nothing, keyed per tick (on the string at the nock, then flying)
        ar = arrow(tag, None, broad=kind == "B3", spin=kind == "B2")
        ar.rotation_mode = "QUATERNION"
        nock_obj = empty(f"{tag} nock point", (0, 0.075, 0), broot)
        string_parts = []
        for sy in (-1, 1):
            s_ = cyl(f"{tag} string {sy}", 0.0025, 1.0, STR, 6, None, axis="Z"); s_.rotation_mode = "QUATERNION"; string_parts.append((s_, sy))
            c_ = cyl(f"{tag} cable {sy}", 0.0018, 1.0, G, 5, None, axis="Z"); c_.rotation_mode = "QUATERNION"; string_parts.append((c_, sy * 2))
        peep = torus(f"{tag} peep", 0.008, 0.002, RM, axis="Z"); peep.rotation_mode = "QUATERNION"
        target = Vector((bx + 0.0, 18.0, 1.36))
        flight = None
        for f in range(1, FRAME_END + 1):
            scene.frame_set(f); bpy.context.view_layer.update()
            Mb = broot.matrix_world
            fwd = (Mb.to_3x3() @ Vector((0, 0, -1))).normalized(); up = (Mb.to_3x3() @ Vector((0, 1, 0))).normalized()
            tipw = [t.matrix_world.translation.copy() for t in tips]
            rest_nock = Mb @ Vector((0, 0.075, brace))
            hand = rig["hand_pt"].matrix_world.translation.copy()
            if F_DRAW <= f < F_REL:
                u = smooth((f - F_DRAW) / (F_FULL - F_DRAW))
                nock = rest_nock.lerp(hand + Vector((0, 0, 0.02)), u)
                draw = u
            elif F_REL <= f < F_REL + 5:                     # the string snaps forward and shivers
                k = f - F_REL
                nock = rest_nock + fwd * (0.03 * math.cos(k * 2.4) * math.exp(-k * 0.6)); draw = 0.0
            else:
                nock = rest_nock; draw = 0.0
            for lp, sy in flex:                              # limbs flex in as the string comes back
                key(lp, f, rot=(R(-sy * (28 if kind != "B2" else 0) - sy * 14 * draw), 0, 0))
            for s_, sy in string_parts:
                if abs(sy) == 1:
                    a = tipw[0] if sy < 0 else tipw[1]; b = nock
                else:
                    a = tipw[0] if sy < 0 else tipw[1]; b = Mb @ Vector((0.016, (0.2 if sy > 0 else -0.2), brace - 0.01))
                    if kind == "B2":
                        b = a
                d = b - a; L = max(1e-4, d.length)
                s_.location = a; s_.rotation_quaternion = d.to_track_quat("Z", "Y"); s_.scale = (1, 1, L)
                for path in ("location", "rotation_quaternion", "scale"):
                    s_.keyframe_insert(path, frame=f)
            if kind != "B2":
                peep.location = nock + up * 0.11; peep.rotation_quaternion = fwd.to_track_quat("Z", "Y")
                peep.keyframe_insert("location", frame=f); peep.keyframe_insert("rotation_quaternion", frame=f)
            # arrow: forms on the string (10-16), rides the nock, flies at release
            if f < F_REL:
                ar.location = nock; ar.rotation_quaternion = fwd.to_track_quat("-Z", "Y")
                ar.keyframe_insert("location", frame=f); ar.keyframe_insert("rotation_quaternion", frame=f)
            elif flight is None:
                flight = (nock.copy(), fwd.copy())
            if f >= F_REL:
                p0, d0 = flight
                k = f - F_REL
                dist = min(5.0 * k, (target - p0).length - 0.55)
                p = p0 + (target - p0).normalized() * dist + Vector((0, 0, -0.0004 * dist * dist))
                ar.location = p; ar.keyframe_insert("location", frame=f)
                ar.rotation_quaternion = (target - p0).normalized().to_track_quat("-Z", "Y"); ar.keyframe_insert("rotation_quaternion", frame=f)
        form_in([o for o in broot.children_recursive if o.type == "MESH"], 2, F_UP, None, CM["pix"], rng, tag, order_axis=2)
        for o in ar.children_recursive:
            if o.type == "MESH":
                key(o, 1, sc=0.0001); key(o, 10, sc=0.0001); key(o, 14, sc=1.0)
        for s_, sy in string_parts:
            s_.hide_render = True; s_.keyframe_insert("hide_render", frame=1); s_.hide_render = False; s_.keyframe_insert("hide_render", frame=12)
        # the target: a straw boss with coloured rings, 18 blocks out
        tg = empty(f"{tag} target", (bx, 18.3, 1.36)); tg.rotation_euler = (R(90), 0, 0)
        cyl(f"{tag} boss", 0.6, 0.3, STRAW, 24, tg, loc=(0, 0, -0.15))
        for i, m in enumerate(RINGS):
            cyl(f"{tag} face {i}", 0.55 - i * 0.11, 0.01, m, 24, tg, loc=(0, 0, 0.15 + i * 0.003))
        box(f"{tag} target stand", (bx - 0.05, 18.4, 0), (bx + 0.05, 18.5, 0.9), STRAW)
        cam(f"Cam {tk}", (bx + 3.6, -1.0, 2.0), (bx - 0.2, 1.2, 1.3), 32)
        cam(f"Cam {tk} close", (bx + 2.3, 1.2, 1.75), (bx - 0.1, 0.45, 1.4), 32)
        cam(f"Cam {tk} target", (bx + 1.5, 16.0, 1.8), (bx, 18.2, 1.35), 30)
        dump["takes"][tk] = {"solver_error_m": errs}
        lines = {"B1": ["Compound: machined riser, split limbs, two cams with", "cables, 3-pin sight, biscuit rest, front stabiliser,",
                        "peep + D-loop. Carbon arrow, 3 vanes, field point."],
                 "B2": ["Olympic recurve: long riser, limbs recurve at the tips,", "long rod + V-bar, clicker, plunger, extension sight.",
                        "Target arrow with spin vanes."],
                 "B3": ["Hunting compound: compact, 5-pin sight, bow quiver with", "4 broadhead arrows, short stabiliser, wrist sling.",
                        "Arrow with a 3-blade broadhead."]}[tk]
        board(tag, (bx, 3.0, 3.0), f"{tk}  {name.upper()}", lines + ["Draw 18-32, anchor under the jaw; release 42;", "arrow 5 blocks a tick to the target at 18 blocks."])
    else:
        rig = make_player(tag, (bx, 0, 0), M)
        keys = [(1, {}), (8, dict(arm_r=(80, 0, 10), fore_r=(85, 0, 0), arm_l=(70, 0, -20), fore_l=(70, 0, 0), leg_l=(18, 0, 0), shin_l=(-14, 0, 0), leg_r=(-10, 0, 0), body=(-4, 0, 0))),
                (28, dict(arm_r=(80, 0, 10), fore_r=(85, 0, 0), arm_l=(70, 0, -20), fore_l=(70, 0, 0), leg_l=(18, 0, 0), shin_l=(-14, 0, 0), leg_r=(-10, 0, 0), body=(-4, 0, 0))),
                (31, dict(arm_r=(72, 0, 10), fore_r=(95, 0, 0), arm_l=(64, 0, -20), fore_l=(78, 0, 0), leg_l=(14, 0, 0), shin_l=(-10, 0, 0), leg_r=(-14, 0, 0), body=(4, 0, 0), root_loc=(0, -0.1, 0))),
                (40, dict(arm_r=(80, 0, 10), fore_r=(85, 0, 0), arm_l=(70, 0, -20), fore_l=(70, 0, 0), leg_l=(18, 0, 0), shin_l=(-14, 0, 0), leg_r=(-10, 0, 0), body=(-4, 0, 0), root_loc=(0, -0.1, 0))),
                (56, dict(root_loc=(0, -0.1, 0)))]
        for f, d in keys:
            pp = dict(IDLE); pp.update(d); rl = pp.pop("root_loc", (0, 0, 0)); pp["root_loc"] = (bx + rl[0], rl[1], rl[2]); pose(rig, f, **pp)
        sroot = empty(f"{tag} shield", (0, -3.5 * P, -3 * P), rig["fore_r"])
        parts = []
        if tk == "H1":
            for q in range(-4, 5):
                for r in range(-4, 5):
                    if abs(q) + abs(r) + abs(-q - r) > 8:
                        continue
                    x = 0.13 * (q + r / 2); z = 0.113 * r
                    edge = abs(q) + abs(r) + abs(-q - r) == 8
                    parts.append(box(f"{tag} tile {q} {r}", (x - 0.063, -0.025, z - 0.054), (x + 0.063, 0.02 if edge else 0.0, z + 0.054), RM if edge else G, sroot))
            parts.append(box(f"{tag} boss", (-0.07, -0.06, -0.07), (0.07, 0.0, 0.07), W, sroot))
        elif tk == "H2":
            for i in range(8):
                for j in range(5):
                    x = -0.45 + j * 0.18; z = -0.95 + i * 0.2
                    parts.append(box(f"{tag} plate {i} {j}", (x, -0.03, z), (x + 0.17, 0.0, z + 0.19), G, sroot))
            for x in (-0.47, 0.46):
                parts.append(box(f"{tag} rim side {x}", (x, -0.05, -0.97), (x + 0.03, 0.01, 0.67), RM, sroot))
            for z in (-0.97, 0.64):
                parts.append(box(f"{tag} rim end {z}", (-0.47, -0.05, z), (0.49, 0.01, z + 0.03), RM, sroot))
            parts.append(box(f"{tag} spine", (-0.03, -0.06, -0.9), (0.03, -0.03, 0.6), W, sroot))
            parts.append(box(f"{tag} viewport", (-0.2, -0.04, 0.35), (0.2, -0.02, 0.42), W, sroot))
        else:
            for i in range(9):
                for j in range(7):
                    a = (j - 3) * 0.17; z = -0.6 + i * 0.17
                    x = 0.8 * math.sin(a); y = -0.8 * math.cos(a) + 0.8
                    t_ = box(f"{tag} cell {i} {j}", (-0.075, -0.012, -0.075), (0.075, 0.012, 0.075), RM if (i in (0, 8) or j in (0, 6)) else G, sroot)
                    t_.location = (x, -y - 0.2, z + 0.3 * math.sin(i / 8 * math.pi) * 0); t_.rotation_euler = (0, 0, -a)
                    parts.append(t_)
        form_in(parts, 2, 8, None, CM["pix"], rng, tag, order_axis=2, stream=0.0)
        sb = box(f"{tag} incoming shot", (-0.1, -0.1, -0.1), (0.1, 0.1, 0.1), SHOT)
        scene.frame_set(30); bpy.context.view_layer.update()
        guard = sroot.matrix_world.translation.copy()
        key(sb, 1, loc=(bx, 7.0, 1.4), sc=0.0001); key(sb, 20, loc=(bx, 7.0, 1.4), sc=1.0); key(sb, 30, loc=tuple(guard + Vector((0, 0.3, 0))), sc=1.0)
        sb.scale = (1, 1, 1); shatter([sb], 31, SHOT, rng, tag, n=8, speed=0.08)
        SG = parts[0].data.materials[0]
        cam(f"Cam {tk}", (bx + 2.6, 4.2, 1.8), (bx, 0.2, 1.2), 35)
        cam(f"Cam {tk} back", (bx + 2.4, -3.2, 1.8), (bx, 0.3, 1.2), 35)
        size = {"H1": "big hex, 1.2 blocks across (twice 808)", "H2": "tower, 0.9 x 1.6 blocks, covers the body",
                "H3": "dome wall, a curved hex wall 1.2 x 1.6 blocks"}[tk]
        board(tag, (bx, 3.0, 3.0), f"{tk}  {name.upper()}", [size, "forms on the ring forearm 2-8, guard up,",
                                                              "a shot breaks on it at 30, the arm gives a little."])
    print(tk, "built", flush=True)
with open(os.path.join(FOLDER, "combat", "bows_poses.json"), "w") as fh:
    json.dump(dump, fh, indent=1)
cam("Cam all", (2.5 * BAY, -14.0, 6.0), (2.5 * BAY, 2.0, 1.2), 26)
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam B1", 1, (0.3, 0.38, 0.5), 3.0


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
