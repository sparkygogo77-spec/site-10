# Pass 863: Fear-consumed mobs: Yellow construct armour and tools (rings/suits chat, 2026-10-18, range 800-899).
# J (2026-10-16, handoff docs/handoff/2026-10-16-fear-consumed-gear/): "things consumed by fear need better light
# construct armor and tools nearly like mine". In game a fear-consumed zombie villager holds a flat yellow sword sprite
# and wears nothing (now.png). Here: Yellow hard-light construct armour and solid 3D construct tools on a vanilla
# zombie villager, built like J's own gear (855 C8b Crest Knight suit language and 603 suits; the 838/846 warden plate
# armour that stands off the body; the 852/861 solid construct tools; the 842/850 modern construct bows), a little
# rougher and crueller so they read as the enemy: jagged edges, spikes, uneven plates, cracks. Original designs only.
# Looks: the Yellow corps strips J has (Ring Lab): Y1 scales, Y2 lightning, Y3 dread (texture_library/yellow/y1-y3,
# 256x8192, 32 frames). Shells at most 90% opaque, darker cores, saturated yellow glow (never white).
# Rig: vanilla zombie villager (head 8x10x8 px with the 2x4x2 nose, body 8x12x6 with the ragged robe, arms 4x12x4 held
# forward, legs 4x12x4), zombie-green skin. Every piece stands 1-1.25 px off the body like J's.
# Every take: the mob walks zombie-style toward the camera (frames 1-46), then acts once (46-80): armour takes lunge and
# grab, melee takes wind up with a short charge (the edge flares), cut edge-first and recover, bow takes draw (52-60),
# hold, loose (64) and recover. 20 fps.
# Armour (full set: helmet, chest, legs, boots):
#   A1 Y1 scales "Scale Reaver": overlapping pointed scale rows on the chest, lower rows further out; tiered pauldrons
#      with saw edges and two spikes; helm with a saw-toothed brow, five swept crown spikes, nose guard; scale tassets,
#      greaves with knee spikes, clawed boots
#   A2 Y2 lightning "Storm-split": the breastplate split down the middle by a jagged lightning gap that glows, the two
#      halves uneven; branching cracks; one huge stepped bolt-finned pauldron (weapon arm), one small; wedge helm with a
#      chevron slit and zigzag bolt horns; uneven blade tassets, zigzag-finned greaves, wedge boots
#   A3 Y3 dread "Hollow Dread": ribcage bars over the robe, a three-layer cowl rising behind the head, drooping hooked
#      pauldrons, a hooded helm with a hollow face and hanging fangs, long ragged strip tassets, spurred greaves
#   A4 mix "Fear Knight": Y3 breastplate and great helm, Y1 scale tiers, waist band and crest, Y2 boss, cracks and the
#      spiked gorget ring; horned scale pauldrons; Y2 knee spikes
# Tools (solid 3D constructs in the zombie's right hand: see-through shell, dark core, bright leading edge):
#   S1 Y1 sword: straight blade, barbed saw back, hooked guard, scale-cut ricasso
#   S2 Y2 sword: zigzag lightning blade in offset sections, forked tip, branching cracks, one-sided spike guard
#   S3 Y3 sword: dread falchion widening to a clipped point, a back hook, a claw guard over the hand
#   X1 Y2 axe: bearded bit with a sawtooth edge, back spike, top spike, crack lines
#   X2 Y3 axe: big crescent bit with hooked horns, back hook, ribbed haft
#   X3 Y1 axe: three overlapping scale plates stepping out to the edge, spiked butt
#   P1 Y3 pick: long front spike curving down, short spiked hammer back, collar ribs
#   P2 Y1 pick: front spike and a back adze blade, scale collar plates
#   P3 Y2 pick: split twin head (two plates with a gap), zigzag bolt prongs front and back
#   B1 Y1 bow: modern compound, a swept riser of stacked scale plates, saw-edged split limbs, twin cams, single pin
#   B2 Y2 bow: zigzag bolt riser and limbs, star cams, long stabiliser with bolt fins
#   B3 Y3 bow: hollow ribbed riser (two rails and rib bars), hooked limbs ending in claws, thorn stabiliser
# Cameras: "Cam <code>" third person per take (frames 1-80); "Cam lineup": every take side by side for a still
# (orthographic, three tiers: armour, swords and axes, picks and bows; static copies, nothing animated).
# Builds LanternLive\suit\fear_gear.blend.
SCENE_NAME = "Fear Gear"
OUT_REL = "suit/fear_gear.blend"
import math, os
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Euler, Vector
from mathutils.geometry import tessellate_polygon

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
bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
P = 1 / 16                                     # one Minecraft pixel in metres
FRAME_END = 80
WALK_END = 46
rng = np.random.default_rng(863)


def link(o):
    col.objects.link(o)
    return o


def empty(name, loc=(0, 0, 0), parent=None, rot=None):
    o = link(bpy.data.objects.new(name, None)); o.location = loc; o.rotation_mode = "XYZ"
    o.empty_display_size = 0.05
    if parent is not None:
        o.parent = parent
    if rot is not None:
        o.rotation_euler = tuple(R(a) for a in rot)
    return o


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_start = 0.05
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


def _blend(m):
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass


def mat(name, rgb, emit=0.0, alpha=1.0, rough=0.5, metal=0.0, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*(ecol or rgb), 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = min(0.99, alpha); _blend(m)
    return m


def key(o, f, loc=None, rot=None, sc=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if sc is not None:
        o.scale = (sc,) * 3 if np.isscalar(sc) else sc; o.keyframe_insert("scale", frame=f)


def keyd(o, f, deg):
    key(o, f, rot=tuple(R(a) for a in deg))


# ------------------------------------------------------------------ meshes
def mesh_obj(name, vs, fs, m, parent=None, uvt=0.5, loc=(0, 0, 0), smooth=False):
    """A mesh (metres) with outward normals and per-face projected UVs (one texture tile per `uvt` metres)."""
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


BOXF = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]


def box(name, a, b, m, parent=None, uvt=0.5):
    a = np.array(a, float); b = np.array(b, float); lo = np.minimum(a, b); hi = np.maximum(a, b)
    v = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    return mesh_obj(name, v, BOXF, m, parent, uvt)


def pbox(name, a, b, m, parent=None, uvt=0.5):
    return box(name, tuple(np.array(a, float) * P), tuple(np.array(b, float) * P), m, parent, uvt)


def _to3(axis, u, v, t):
    return {"x": (t, u, v), "y": (u, t, v), "z": (u, v, t)}[axis]


def prism_m(name, poly, axis, t0, t1, m, parent=None, uvt=0.5):
    """A flat plate: a 2D outline (metres) in the plane across `axis`, extruded from t0 to t1 along it.
    axis 'x': poly is (y, z); 'y': (x, z); 'z': (x, y). Concave outlines are fine."""
    poly = [tuple(p) for p in poly]
    tris = tessellate_polygon([[Vector((p[0], p[1], 0)) for p in poly]])
    n = len(poly)
    vs = [_to3(axis, p[0], p[1], t0) for p in poly] + [_to3(axis, p[0], p[1], t1) for p in poly]
    fs = [tuple(t) for t in tris] + [tuple(i + n for i in t) for t in tris]
    fs += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return mesh_obj(name, vs, fs, m, parent, uvt)


def prism(name, poly, axis, t0, t1, m, parent=None, uvt=0.9):
    """prism_m in pixels."""
    return prism_m(name, [(a * P, b * P) for a, b in poly], axis, min(t0, t1) * P, max(t0, t1) * P, m, parent, uvt)


def spike_m(name, base, tip, r, m, parent=None, n=4, rot=45):
    """A pyramid spike (metres): n-gon base of radius r round `base`, pointing at `tip`."""
    b = Vector(base); t = Vector(tip); ax = t - b
    q = ax.normalized().to_track_quat("Z", "Y")
    vs = [b + q @ Vector((r * math.cos(R(rot) + 2 * math.pi * k / n), r * math.sin(R(rot) + 2 * math.pi * k / n), 0)) for k in range(n)]
    vs.append(t)
    fs = [(k, (k + 1) % n, n) for k in range(n)] + [tuple(range(n))[::-1]]
    return mesh_obj(name, vs, fs, m, parent, 0.3)


def spike(name, base, tip, r, m, parent=None, n=4):
    return spike_m(name, tuple(np.array(base) * P), tuple(np.array(tip) * P), r * P, m, parent, n)


def sweep_m(name, pts, ws, ts, m, parent=None, side=(1, 0, 0)):
    """A rectangular section swept along pts (metres): width along `side`, thickness across the path."""
    pts = [Vector(p) for p in pts]; sd = Vector(side).normalized(); vs = []; n_ = len(pts)
    for i, p in enumerate(pts):
        t = (pts[min(n_ - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
        nn = sd.cross(t)
        if nn.length < 1e-6:
            nn = Vector((0, 0, 1)).cross(t)
        nn.normalize()
        w = ws[i] if hasattr(ws, "__len__") else ws; th = ts[i] if hasattr(ts, "__len__") else ts
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            vs.append(p + sd * (a * w / 2) + nn * (b * th / 2))
    fs = []
    for i in range(n_ - 1):
        for k in range(4):
            fs.append((i * 4 + k, i * 4 + (k + 1) % 4, (i + 1) * 4 + (k + 1) % 4, (i + 1) * 4 + k))
    fs += [(3, 2, 1, 0), tuple((n_ - 1) * 4 + k for k in range(4))]
    return mesh_obj(name, vs, fs, m, parent, 0.3)


def sweep(name, pts, ws, ts, m, parent=None, side=(1, 0, 0)):
    """sweep_m in pixels."""
    sc = lambda v: [x * P for x in v] if hasattr(v, "__len__") else v * P
    return sweep_m(name, [tuple(np.array(p) * P) for p in pts], sc(ws), sc(ts), m, parent, side)


def horn(name, pts, r0, m, parent=None, side=(1, 0, 0)):
    """A tapering curved spike along pts (pixels), square section from r0 to a point."""
    n = len(pts); ws = [max(0.02, 2 * r0 * (1 - i / (n - 1)) ** 0.9) for i in range(n)]
    return sweep(name, pts, ws, ws, m, parent, side)


def rod_m(name, a, b, r, m, parent=None, n=6):
    a = Vector(a); b = Vector(b); d = b - a; L = max(1e-5, d.length); q = d.to_track_quat("Z", "Y")
    vs = []
    for k in range(n):
        an = 2 * math.pi * k / n
        for z in (0, L):
            vs.append(a + q @ Vector((r * math.cos(an), r * math.sin(an), z)))
    fs = [(2 * k, 2 * ((k + 1) % n), 2 * ((k + 1) % n) + 1, 2 * k + 1) for k in range(n)]
    fs += [tuple(2 * k for k in range(n))[::-1], tuple(2 * k + 1 for k in range(n))]
    return mesh_obj(name, vs, fs, m, parent, 0.3, smooth=True)


def saw(p0, p1, n, depth, out=None, jit=0.35, skew=0.5):
    """Jagged edge from p0 toward p1 (p1 itself not included): n teeth of uneven depth on the `out` side
    (2D unit vector; default the right of travel, outward for a counter-clockwise outline)."""
    p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0
    nrm = np.array(out, float) if out is not None else np.array([d[1], -d[0]]) / max(1e-9, np.linalg.norm(d))
    pts = []
    for i in range(n):
        a = p0 + d * i / n; mid = p0 + d * (i + skew + rng.uniform(-0.12, 0.12)) / n
        pts += [tuple(a), tuple(mid + nrm * depth * (1 + rng.uniform(-jit, jit)))]
    return pts


def zigzag(p0, p1, n, amp, start=1):
    """Lightning: points from p0 to p1 (both included), alternating amp across the line."""
    p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0
    nrm = np.array([-d[1], d[0]]) / max(1e-9, np.linalg.norm(d)); out = []
    for i in range(n + 1):
        s = 0 if i in (0, n) else (start if i % 2 else -start) * amp * (1 + rng.uniform(-0.3, 0.3))
        out.append(tuple(p0 + d * i / n + nrm * s))
    return out


# ------------------------------------------------------------------ the Yellow construct looks
TEXLIB = os.path.join(FOLDER, "texture_library")
if not os.path.isdir(os.path.join(TEXLIB, "yellow")):
    _here = os.path.dirname(os.path.abspath(bpy.data.filepath)) if bpy.data.filepath else ""
    for cand in (os.path.join(os.getcwd(), "docs", "texture_library"), os.path.join(_here, "texture_library")):
        if os.path.isdir(os.path.join(cand, "yellow")):
            TEXLIB = cand
            break


def strip_image(look):
    p = os.path.join(TEXLIB, "yellow", look, f"construct_{look}_yellow.png")
    im = bpy.data.images.get(os.path.basename(p))
    if im is None:
        im = bpy.data.images.load(p)
        try:
            im.pack()
        except Exception:
            pass
    return im


YGLOW = (1.0, 0.6, 0.0)          # the saturated yellow every glow is (no blue: it can't wash to white)
YBASE = (0.42, 0.22, 0.0)


def ystrip(name, look, ft=4, emit=1.5, alpha=0.86, gamma=1.6):
    """Animated Yellow strip (32 frames, frame k = floor(frame/ft) mod n, two samples crossfaded like the game's
    interpolate). The strip's brightness drives a saturated yellow (emission) and a dark amber (base), so the texture's
    pale highlights never come out white; darker cores stay dark. Opacity 50-`alpha` from the strip's alpha (<= 0.99)."""
    im = strip_image(look)
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.35
    if "Specular Tint" in p.inputs:                       # reflections of the white sun come out yellow, never white
        p.inputs["Specular Tint"].default_value = (*YGLOW, 1)
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
    bw = N.new("ShaderNodeRGBToBW"); L.new(mc.outputs[2], bw.inputs["Color"])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = gamma; L.new(bw.outputs["Val"], pw.inputs[0])
    ec = N.new("ShaderNodeVectorMath"); ec.operation = "SCALE"; ec.inputs[0].default_value = YGLOW
    L.new(pw.outputs[0], ec.inputs["Scale"]); L.new(ec.outputs[0], p.inputs["Emission Color"])
    bc = N.new("ShaderNodeVectorMath"); bc.operation = "SCALE"; bc.inputs[0].default_value = YBASE
    L.new(bw.outputs["Val"], bc.inputs["Scale"]); L.new(bc.outputs[0], p.inputs["Base Color"])
    p.inputs["Emission Strength"].default_value = emit
    ma = N.new("ShaderNodeMix"); ma.data_type = "FLOAT"; L.new(wv.outputs[0], ma.inputs["Factor"])
    L.new(outs[0].outputs["Alpha"], ma.inputs[2]); L.new(outs[1].outputs["Alpha"], ma.inputs[3])
    am = N.new("ShaderNodeMapRange"); am.clamp = True
    am.inputs["From Min"].default_value = 0.0; am.inputs["From Max"].default_value = 1.0
    am.inputs["To Min"].default_value = 0.5; am.inputs["To Max"].default_value = min(0.99, alpha)
    L.new(ma.outputs[0], am.inputs["Value"]); L.new(am.outputs["Result"], p.inputs["Alpha"])
    _blend(m)
    return m


LOOKS = {"y1": dict(ft=4, emit=0.95, gamma=2.0), "y2": dict(ft=4, emit=1.5, gamma=1.6), "y3": dict(ft=5, emit=1.4, gamma=1.5)}
SHELL = {k: ystrip(f"FG {k} shell", k, alpha=0.88, **v) for k, v in LOOKS.items()}
TSHELL = {k: ystrip(f"FG {k} tool shell", k, alpha=0.9, **{**v, "emit": v["emit"] * 1.6, "gamma": 1.25}) for k, v in LOOKS.items()}
CORE = mat("FG dark core", (0.05, 0.022, 0.0), emit=0.6, alpha=0.95, rough=0.3, ecol=(0.55, 0.2, 0.0))
RIM = mat("FG edge", (0.9, 0.5, 0.0), emit=2.6, alpha=0.97, rough=0.2, ecol=YGLOW)
CRACK = mat("FG crack", (0.6, 0.2, 0.0), emit=2.4, alpha=0.97, ecol=(1.0, 0.42, 0.0))
SLIT = mat("FG eye glow", (0.6, 0.3, 0.0), emit=3.5, ecol=(1.0, 0.5, 0.0))
TRIM = mat("FG trim", (0.8, 0.42, 0.0), emit=1.9, alpha=0.97, rough=0.25, ecol=YGLOW)
GRIPM = mat("FG grip", (0.06, 0.03, 0.0), emit=0.4, alpha=0.97, rough=0.35, ecol=(0.5, 0.22, 0.0))

# vanilla zombie villager colours (linear)
SKIN = mat("FG zombie skin", (0.075, 0.17, 0.05), rough=0.85)
SKIN_D = mat("FG zombie skin dark", (0.045, 0.1, 0.03), rough=0.85)
ROBE = mat("FG robe", (0.13, 0.06, 0.025), rough=0.95)
ROBE_D = mat("FG robe torn", (0.06, 0.028, 0.012), rough=0.95)
PANTS = mat("FG trousers", (0.09, 0.075, 0.06), rough=0.95)
EYE = mat("FG zombie eyes", (0.4, 0.2, 0.0), emit=1.6, ecol=(1.0, 0.45, 0.0))     # fear: a dull yellow
FLOOR = mat("FG floor", (0.035, 0.037, 0.042), rough=0.92)
WALL = mat("FG backdrop", (0.03, 0.032, 0.04), rough=0.95)
LBL = mat("FG label", (0.5, 0.3, 0.02), emit=1.2, ecol=(1.0, 0.6, 0.0))


# ------------------------------------------------------------------ the zombie villager (faces -Y; its right is -X)
def zombie(tag, loc):
    """Pivots: root (ground), body (hips, 12 px up), head (neck), arm_r/arm_l (shoulders, rest -90 = forward),
    leg_r/leg_l (hips). Gear mounts: grip_r/grip_l (tool frame = world frame when the arm points forward),
    hand_r/hand_l (hand points)."""
    root = empty(f"{tag} root", loc)
    body = empty(f"{tag} body", (0, 0, 12 * P), root)
    pbox(f"{tag} robe", (-4.5, -3.5, -6), (4.5, 3.5, 12.5), ROBE, body)
    for k, (x0, x1, l) in enumerate(((-4.5, -3.2, 1.6), (-2.4, -1.0, 0.9), (0.2, 1.6, 2.0), (2.6, 4.5, 1.2))):
        pbox(f"{tag} robe rag {k}", (x0, -3.5, -6 - l), (x1, 3.5, -6), ROBE, body)          # torn hem
    for k, (x0, z0, w, h) in enumerate(((-3.6, 3.0, 1.4, 1.2), (1.2, -3.4, 1.8, 1.0), (2.2, 7.2, 1.0, 1.6))):
        pbox(f"{tag} robe tear {k}", (x0, -3.56, z0), (x0 + w, -3.4, z0 + h), ROBE_D, body)
    head = empty(f"{tag} head", (0, 0, 12 * P), body)
    pbox(f"{tag} skull", (-4, -4, 0), (4, 4, 10), SKIN, head)
    pbox(f"{tag} nose", (-1, -6, 1), (1, -4, 5), SKIN_D, head)
    pbox(f"{tag} brow", (-4, -4.06, 6), (4, -3.9, 7), SKIN_D, head)
    for sx in (-1, 1):
        pbox(f"{tag} eye {sx}", (sx * 1.0, -4.07, 5), (sx * 3.0, -3.9, 6), EYE, head)
    pbox(f"{tag} rot patch", (1.5, -4.05, 1.0), (3.5, -3.9, 3.0), SKIN_D, head)
    rig = {"root": root, "body": body, "head": head}
    for side, sx in (("r", -1), ("l", 1)):
        arm = empty(f"{tag} arm {side}", (sx * 6 * P, 0, 10 * P), body, rot=(-90, 0, 0))
        pbox(f"{tag} arm box {side}", (-2, -2, -10), (2, 2, 2), SKIN, arm)
        pbox(f"{tag} sleeve {side}", (-2.12, -2.12, -4), (2.12, 2.12, 2.12), ROBE, arm)
        rig["arm_" + side] = arm
        rig["hand_" + side] = empty(f"{tag} hand {side}", (0, 0, -9 * P), arm)
        rig["grip_" + side] = empty(f"{tag} grip {side}", (0, 0, -9 * P), arm, rot=(90, 0, 0))
        leg = empty(f"{tag} leg {side}", (sx * 2 * P, 0, 0), body)
        pbox(f"{tag} leg box {side}", (-2, -2, -12), (2, 2, 0), PANTS, leg)
        pbox(f"{tag} foot {side}", (-2.05, -2.05, -12), (2.05, 2.05, -10.5), SKIN_D, leg)
        rig["leg_" + side] = leg
    return rig


# Gear helpers. Body frame (px): x across (the zombie's right is -x), y front (-), z up from the hips.
# Arm frame: u outward from the arm's centre, w up (when the arm points forward), a along the arm toward the hand
# (0 = shoulder pivot, 10 = the hand end; arm box u, w in -2..2, a in -2..10). Leg frame: leg local px (u outward).
def AL(s, u, w, a):
    return (s * u, -w, -a)


def abox(nm, rig, side, u, w, a, m):
    s = -1 if side == "r" else 1
    return pbox(nm, AL(s, u[0], w[0], a[0]), AL(s, u[1], w[1], a[1]), m, rig["arm_" + side])


def aprism_top(nm, rig, side, poly_ua, w0, w1, m, trim_pts=None):
    """A plate lying over the arm (normal = up): outline in (u, a)."""
    s = -1 if side == "r" else 1
    o = prism(nm, [(s * u, -a) for u, a in poly_ua], "y", -w0, -w1, m, rig["arm_" + side])
    if trim_pts:
        trim(nm + " trim", [(s * u, -a) for u, a in trim_pts], "y", -(w1 + 0.12), rig["arm_" + side])
    return o


def aprism_side(nm, rig, side, poly_wa, u0, u1, m, trim_pts=None):
    """A plate on the arm's outer (or inner) side: outline in (w, a), thickness u0..u1."""
    s = -1 if side == "r" else 1
    o = prism(nm, [(-w, -a) for w, a in poly_wa], "x", s * u0, s * u1, m, rig["arm_" + side])
    if trim_pts:
        trim(nm + " trim", [(-w, -a) for w, a in trim_pts], "x", s * (u1 + 0.12), rig["arm_" + side])
    return o


def aspike(nm, rig, side, b, t, r, m, n=4):
    s = -1 if side == "r" else 1
    return spike(nm, AL(s, *b), AL(s, *t), r, m, rig["arm_" + side], n)


def gauntlet(tag, rig, side, m, a0=7.0, a1=10.3, g=1.25, t=0.5):
    """Four plates round the forearm, `g` px off (top spans the full width, the sides sit between)."""
    o = 2 + g; out = []
    out.append(abox(f"{tag} gauntlet top {side}", rig, side, (-o - t, o + t), (o, o + t), (a0, a1), m))
    out.append(abox(f"{tag} gauntlet under {side}", rig, side, (-o - t, o + t), (-o - t, -o), (a0, a1), m))
    out.append(abox(f"{tag} gauntlet outer {side}", rig, side, (o, o + t), (-o, o), (a0, a1), m))
    out.append(abox(f"{tag} gauntlet inner {side}", rig, side, (-o - t, -o), (-o, o), (a0, a1), m))
    return out


def trim(nm, pts, axis, t, par, m=None, w=0.32, d=0.3):
    """A lit trim just proud of a plate's outer face, along some of its (jagged) edge points (2D, pixels)."""
    if not pts or len(pts) < 2:
        return None
    side = {"y": (0, 1, 0), "x": (1, 0, 0), "z": (0, 0, 1)}[axis]
    return sweep(nm, [_to3(axis, u, v, t) for u, v in pts], d, w, m or TRIM, par, side)


def fplate(nm, poly, m, par, y=-4.75, t=0.5, trim_pts=None):
    o = prism(nm, poly, "y", y - t, y, m, par)
    trim(nm + " trim", trim_pts, "y", y - t - 0.12, par)
    return o


def bplate(nm, poly, m, par, y=4.75, t=0.5, trim_pts=None):
    o = prism(nm, poly, "y", y, y + t, m, par)
    trim(nm + " trim", trim_pts, "y", y + t + 0.12, par)
    return o


def splate(nm, s, poly_yz, m, par, x=5.75, t=0.5, trim_pts=None):
    o = prism(nm, poly_yz, "x", s * x, s * (x + t), m, par)
    trim(nm + " trim", trim_pts, "x", s * (x + t + 0.12), par)
    return o


def crack(nm, pts, par, axis="y", m=None, w=0.28, d=0.16):
    side = {"y": (0, 1, 0), "x": (1, 0, 0), "z": (0, 0, 1)}[axis]
    return sweep(nm, pts, d, w, m or CRACK, par, side)


# --- helmet frame: head local px (x -4..4, y -4..4, z 0..10), nose x -1..1, y -6..-4, z 1..5.
HF, HS, HB, HT = -5.25, 5.0, 5.25, 11.25          # inner faces: front, sides (x), back, top (1-1.25 px off)


def helm_shell(tag, head, m, brow, cheek_bot=0.5, side_bot=0.5, nose=True, slit=(4.8, 6.2), back_bot=0.5):
    """The common helm: top, back, sides, a brow plate (outline given), cheeks, the nose guard and the eye-slit glow
    behind. `brow`: outline (x, z) of the front plate above the slit; returns the parts."""
    T = 0.5; out = []
    out.append(prism(f"{tag} helm top", [(-HS - T, HF - T), (HS + T, HF - T), (HS + T, HB + T), (-HS - T, HB + T)], "z", HT, HT + T, m, head))
    out.append(prism(f"{tag} helm back", [(-HS - T, back_bot), (HS + T, back_bot), (HS + T, HT), (-HS - T, HT)], "y", HB, HB + T, m, head))
    for sx in (-1, 1):
        sp = saw((HF - T, side_bot), (HB, side_bot), 3, 0.9, out=(0, -1)) + [(HB, side_bot), (HB, HT), (HF - T, HT)]
        out.append(prism(f"{tag} helm side {sx}", sp, "x", sx * HS, sx * (HS + T), m, head))
    out.append(prism(f"{tag} helm brow", brow, "y", HF - T, HF, m, head))
    trim(f"{tag} helm brow trim", brow[:-2], "y", HF - T - 0.12, head)
    for sx in (-1, 1):
        x0, x1 = (2.25, HS + T) if sx > 0 else (-(HS + T), -2.25)
        cp = [(x0, slit[0]), (x1, slit[0]), (x1, cheek_bot)] + saw((x1, cheek_bot), (x0, cheek_bot), 2, 0.9, out=(0, -1))[1:] + [(x0, cheek_bot)]
        out.append(prism(f"{tag} helm cheek {sx}", cp, "y", HF - T, HF, m, head))
    if nose:
        out.append(prism(f"{tag} helm nose front", [(-2.25, 0.25), (2.25, 0.25), (2.25, slit[1]), (0, slit[1] + 0.8), (-2.25, slit[1])],
                         "y", -7.25, -6.75, m, head))
        for sx in (-1, 1):
            out.append(prism(f"{tag} helm nose side {sx}", [(-6.75, 0.25), (HF - T, 0.25), (HF - T, slit[1]), (-6.75, slit[1])],
                             "x", sx * 1.75, sx * 2.25, m, head))
    out.append(pbox(f"{tag} helm slit glow", (-HS, -4.75, slit[0] + 0.1), (HS, -4.55, slit[1] - 0.1), SLIT, head))
    return out


# ------------------------------------------------------------------ armour sets
def armour_A1(tag, rig):
    """Y1 scales, Scale Reaver."""
    m = SHELL["y1"]; body, head = rig["body"], rig["head"]
    for r in range(5):                                       # pointed scale rows, each lower row further out
        zt = 12.2 - r * 2.45; h = 3.3; y = -4.75 - 0.28 * r
        n = 3 if r % 2 == 0 else 4; w = 7.6 / 3 if n == 3 else 7.6 / 3.4
        x0 = -3.8 if n == 3 else -3.8 - w * 0.2
        for c in range(n):
            a = max(-3.8, x0 + c * w); b = min(3.8, x0 + (c + 1) * w + 0.15)
            if b - a < 0.8:
                continue
            tip = (a + b) / 2 + rng.uniform(-0.3, 0.3)
            poly = [(a, zt), (b, zt), (b, zt - h * 0.55), (tip, zt - h - rng.uniform(0, 0.5)), (a, zt - h * 0.55)]
            fplate(f"{tag} chest scale {r} {c}", poly, m, body, y=y, t=0.4, trim_pts=poly[2:])
    for s in (-1, 1):
        splate(f"{tag} chest side {s}", s, [(-3.6, 6.5), (3.6, 6.5), (3.6, -0.5)] + saw((3.6, -0.5), (-3.6, -0.5), 3, 1.1, out=(0, -1))[1:] + [(-3.6, -0.5)], m, body)
    bplate(f"{tag} back", [(-4.6, -0.5), (4.6, -0.5), (4.6, 12), (-4.6, 12)], m, body)
    for k in range(4):                                       # backbone spikes
        z = 1.5 + k * 2.8
        spike(f"{tag} back spike {k}", (0, 5.2, z), (0, 7.4 + 0.3 * (k % 2), z + 1.6), 0.7, m, body)
    for k, x in enumerate((-3.2, -2.6, 2.6, 3.2)):           # gorget spikes, forward and down, clear of the nose guard
        spike(f"{tag} gorget spike {k}", (x, -5.0, 11.4), (x * 1.15, -7.0, 10.0), 0.55, m, body)
    crack(f"{tag} chest crack", [(1.2, -5.62, 9.5), (1.8, -5.62, 8.2), (1.1, -5.62, 7.3), (2.0, -5.62, 6.0)], body)
    for s in (-1, 1):                                        # scale tassets, front pair and sides
        x0, x1 = (0.2, 4.2) if s > 0 else (-4.2, -0.2)
        for r in range(2):
            pts = [(x0, -0.2 - r * 1.8), (x1, -0.2 - r * 1.8)]
            nn = 2; w = (x1 - x0) / nn
            for c in range(nn):
                a, b = x0 + c * w, x0 + (c + 1) * w + 0.1
                tq = [(b, -1.6 - r * 1.8), ((a + b) / 2, -2.4 - r * 1.8), (a, -1.6 - r * 1.8)]
                fplate(f"{tag} tasset {s} {r} {c}", [(a, -0.2 - r * 1.8), (b, -0.2 - r * 1.8)] + tq, m, body, y=-4.75 - 0.3 * r, t=0.4, trim_pts=tq)
        splate(f"{tag} side tasset {s}", s, [(-3.2, 0.0), (3.2, 0.0), (3.2, -2.6), (0.0, -4.0), (-3.2, -2.6)], m, body)
    for side in ("r", "l"):                                  # tiered saw-edged pauldrons, two spikes
        for k, (u1, a1, w0) in enumerate(((4.2, 4.0, 3.25), (3.6, 2.8, 3.8), (3.0, 1.6, 4.35))):
            poly = [(0.2, -2.6), (u1, -2.6)] + saw((u1, -2.0), (u1, a1), 3, 0.7, out=(1, 0)) + [(u1, a1), (0.2, a1)]
            aprism_top(f"{tag} pauldron {k} {side}", rig, side, poly, w0, w0 + 0.45, m, trim_pts=poly[1:-1])
        aprism_side(f"{tag} pauldron side {side}", rig, side,
                    [(3.25, -2.6), (3.25, 4.0)] + saw((-1.2, 4.0), (-1.2, -2.6), 3, 0.9, out=(-1, 0)) + [(-1.2, -2.6)], 3.25, 3.75, m)
        aspike(f"{tag} pauldron spike a {side}", rig, side, (1.6, 4.6, -0.6), (2.6, 7.4, -1.6), 0.7, m)
        aspike(f"{tag} pauldron spike b {side}", rig, side, (2.8, 4.4, 1.0), (4.6, 6.4, 0.6), 0.55, m)
        gauntlet(f"{tag}", rig, side, m)
        for k, w in enumerate((-1.2, 0.0, 1.2)):             # knuckle claws
            aspike(f"{tag} claw {k} {side}", rig, side, (0.5 * (k - 1), w, 10.2), (0.6 * (k - 1), w + 0.3, 12.0), 0.45, m)
    brow = saw((-HS - 0.5, 6.2), (HS + 0.5, 6.2), 6, 0.9, out=(0, -1)) + [(HS + 0.5, 6.2), (HS + 0.5, HT + 0.5), (-HS - 0.5, HT + 0.5)]
    helm_shell(f"{tag}", head, m, brow)
    for k, (x, l) in enumerate(((-3.6, 2.2), (-1.8, 3.0), (0.0, 3.8), (1.8, 2.6), (3.6, 1.8))):     # swept crown spikes
        spike(f"{tag} crown spike {k}", (x, -1.5 + abs(x) * 0.3, HT + 0.5), (x * 1.1, 2.0 + l * 0.6, HT + 0.5 + l), 0.75, m, head)
    for sx in (-1, 1):
        for r in range(2):
            x0, x1 = (2.5, 4.9) if sx > 0 else (-4.9, -2.5)
            prism(f"{tag} cheek scale {sx} {r}", [(x0, 4.4 - r * 1.9), (x1, 4.4 - r * 1.9), (x1, 3.2 - r * 1.9), ((x0 + x1) / 2, 2.4 - r * 1.9), (x0, 3.2 - r * 1.9)],
                  "y", HF - 0.9, HF - 0.5, m, head)
    crack(f"{tag} helm crack", [(-3.0, HF - 0.58, 10.6), (-2.2, HF - 0.58, 9.3), (-3.1, HF - 0.58, 8.2), (-2.4, HF - 0.58, 7.2)], head)
    legs_common(tag, rig, m, knee="spike", toe="claws")


def legs_common(tag, rig, m, knee="spike", toe="claws", fin=False, spur=False, knee_m=None):
    """Greaves (front, outer, back) on the visible shin under the robe, and boots; the inner side stays open so the
    two legs never touch."""
    for side in ("r", "l"):
        s = -1 if side == "r" else 1; leg = rig["leg_" + side]
        u0, u1 = -1.6, 2.75                              # inner edge 0.4 px from the middle
        xs = sorted((s * u0, s * u1))
        prism(f"{tag} greave front {side}", [(xs[0], -9.4), (xs[1], -9.4), (xs[1], -7.4), ((xs[0] + xs[1]) / 2, -6.9), (xs[0], -7.4)], "y", -3.75, -3.25, m, leg)
        prism(f"{tag} greave outer {side}", [(-3.25, -9.4), (3.25, -9.4), (3.25, -7.2), (-3.25, -7.2)], "x", s * 3.25, s * 3.75, m, leg)
        prism(f"{tag} greave back {side}", [(xs[0], -9.4), (xs[1], -9.4), (xs[1], -7.2), (xs[0], -7.2)], "y", 3.25, 3.75, m, leg)
        if knee == "spike":
            spike(f"{tag} knee spike {side}", (s * 0.6, -3.7, -7.9), (s * 0.7, -5.6, -7.6), 0.6, knee_m or m, leg)
        elif knee == "plate":
            prism(f"{tag} knee plate {side}", [(xs[0] + 0.4, -8.6), (xs[1] - 0.4, -8.6), ((xs[0] + xs[1]) / 2, -7.0)], "y", -4.25, -3.75, knee_m or m, leg)
        if fin:
            pts = zigzag((-2.6, -9.0), (2.4, -7.6), 4, 0.5)
            prism(f"{tag} greave fin {side}", pts + [(2.4, -7.0), (-2.6, -8.4)], "x", s * 3.75, s * 4.15, m, leg)
        if spur:
            spike(f"{tag} heel spur {side}", (s * 0.6, 3.6, -8.4), (s * 0.6, 6.0, -9.6), 0.6, m, leg)
        # boots: toe cap, outer and back plates, sole stays on the ground
        prism(f"{tag} boot toe {side}", [(xs[0], -12), (xs[1], -12), (xs[1], -10.2), (xs[0], -10.2)], "y", -3.75, -3.25, m, leg)
        prism(f"{tag} boot outer {side}", [(-3.25, -12), (3.25, -12), (3.25, -9.8), (-3.25, -9.8)], "x", s * 3.25, s * 3.75, m, leg)
        prism(f"{tag} boot back {side}", [(xs[0], -12), (xs[1], -12), (xs[1], -9.8), (xs[0], -9.8)], "y", 3.25, 3.75, m, leg)
        prism(f"{tag} boot top {side}", [(xs[0], -3.75), (xs[1], -3.75), (xs[1], -2.4), (xs[0], -2.4)], "z", -10.2, -9.8, m, leg)
        if toe == "claws":
            for k, x in enumerate((-0.9, 0.9)):
                spike(f"{tag} toe claw {k} {side}", (s * 0.6 + x, -3.7, -11.4), (s * 0.6 + x * 1.2, -5.4, -11.9), 0.45, m, leg)
        elif toe == "wedge":
            prism(f"{tag} boot wedge {side}", [(-3.75, -12), (-5.6, -12), (-3.75, -10.2)], "x", xs[0] + 0.3, xs[1] - 0.3, m, leg)


def armour_A2(tag, rig):
    """Y2 lightning, Storm-split."""
    m = SHELL["y2"]; body, head = rig["body"], rig["head"]
    split = zigzag((0.0, 12.0), (0.3, -0.8), 6, 0.7)
    left = [(-3.8, 12.0)] + [(x - 0.3, z) for x, z in split] + [(-3.8, 0.6)]
    right = [(x + 0.3, z) for x, z in split] + [(3.8, -0.2), (3.8, 12.0)]
    fplate(f"{tag} breast left", left[::-1], m, body, y=-4.75, t=0.55, trim_pts=[(-3.8, 0.6), left[-2]])
    fplate(f"{tag} breast right", right, m, body, y=-5.15, t=0.55, trim_pts=[right[-3], (3.8, -0.2)])            # uneven: the right half stands further out
    crack(f"{tag} split light", [(x, -4.55, z) for x, z in split], body, w=0.5, d=0.2)
    for k, pts in enumerate(([(-0.4, 9.2), (-1.6, 8.6), (-2.2, 9.4), (-3.3, 8.8)], [(0.5, 4.2), (1.7, 3.4), (2.4, 4.0), (3.4, 2.9)],
                             [(-0.2, 2.2), (-1.4, 1.2), (-2.8, 1.6)])):
        yy = -5.33 if k == 0 else -5.73
        crack(f"{tag} chest crack {k}", [(x, yy, z) for x, z in pts], body)
    for s in (-1, 1):
        zb = 0.0 if s < 0 else -0.8
        splate(f"{tag} chest side {s}", s, [(-3.6, 6.4), (3.6, 5.6), (3.6, zb), (0.4, zb - 1.2), (-3.6, zb + 0.4)], m, body)
    bplate(f"{tag} back", [(-4.6, -0.6), (4.6, -0.6), (4.6, 12.0), (-4.6, 12.0)], m, body)
    crack(f"{tag} back crack", [(x, 5.33, z) for x, z in zigzag((-3.0, 11.0), (2.5, 0.6), 5, 0.8)], body)
    for k, (x0, x1, zb) in enumerate(((-4.2, -1.6, -3.9), (-1.4, 1.0, -2.4), (1.2, 4.2, -3.4))):       # uneven blade tassets
        tq = [(x1, zb + 1.0), (x0 + (x1 - x0) * (0.2 + 0.6 * (k % 2)), zb), (x0, zb + 0.6)]
        fplate(f"{tag} tasset blade {k}", [(x0, 0.0), (x1, 0.0)] + tq, m, body, y=-4.75 - 0.25 * k, t=0.45, trim_pts=tq)
    for s in (-1, 1):
        splate(f"{tag} side tasset {s}", s, [(-3.0, 0.0), (3.0, 0.0), (3.0, -2.2 - (s > 0)), (-3.0, -3.6)], m, body)
    # pauldrons: the weapon arm's (right) huge, stepped, bolt-finned; the left small and plain
    for k in range(3):
        u1 = 4.6 - 0.5 * k; a1 = 4.6 - 1.3 * k; w0 = 3.25 + 0.6 * k
        aprism_top(f"{tag} pauldron r {k}", rig, "r", [(0.2, -2.8), (u1, -2.2 + 0.4 * k), (u1 + 0.4, a1), (0.2, a1 + 0.6)], w0, w0 + 0.5, m)
    aprism_side(f"{tag} pauldron side r", rig, "r", [(4.25, -2.8), (4.25, 4.6), (0.6, 5.0), (-1.8, 3.4), (-0.4, 1.0), (-2.2, -1.4), (-0.8, -2.8)], 3.25, 3.75, m)
    for k, (a, l) in enumerate(((-1.6, 3.4), (0.6, 4.2), (2.6, 2.8))):
        zz = zigzag((a, 5.0), (a - 0.8, 5.0 + l), 3, 0.5)
        poly = zz + [(zz[-1][0] - 0.6, zz[-1][1] - 0.6)] + [(p[0] - 0.9, p[1]) for p in zz[::-1][1:]]
        prism(f"{tag} bolt fin {k}", [(-(w), -aa) for aa, w in poly], "x", -(1.2 + 0.4 * k) - 0.2, -(1.2 + 0.4 * k) + 0.2, m, rig["arm_r"])
        trim(f"{tag} bolt fin trim {k}", [(-(w), -aa) for aa, w in zz], "x", -(1.2 + 0.4 * k) - 0.3, rig["arm_r"])
    aprism_top(f"{tag} pauldron l", rig, "l", [(0.2, -2.4), (3.6, -2.0), (3.9, 2.4), (0.2, 3.0)], 3.25, 3.75, m)
    aprism_side(f"{tag} pauldron side l", rig, "l", [(3.25, -2.4), (3.25, 2.6), (0.0, 2.0), (-0.6, -2.0)], 3.25, 3.75, m)
    for side in ("r", "l"):
        gauntlet(f"{tag}", rig, side, m)
        aspike(f"{tag} elbow fin {side}", rig, side, (3.0, 3.6, 8.0), (4.4, 6.0, 6.6), 0.55, m)
    # wedge helm: chevron slit, zigzag bolt horns from the temples going back
    brow = [(-HS - 0.5, 6.4), (0.0, 5.4 + 0.0), (HS + 0.5, 6.4), (HS + 0.5, HT + 0.5), (-HS - 0.5, HT + 0.5)]
    helm_shell(f"{tag}", head, m, brow, slit=(4.6, 6.4))
    prism(f"{tag} helm ridge", [(-6.0, HT + 0.5), (5.0, HT + 0.5), (2.0, HT + 2.2), (-3.5, HT + 1.6)], "x", -0.4, 0.4, m, head)
    for sx in (-1, 1):
        zz = zigzag((1.0, 8.0), (6.4, 14.8), 4, 0.7, start=sx)
        poly = zz + [(p[0] - 0.8, p[1] + 0.65) for p in zz[::-1]]
        prism(f"{tag} bolt horn {sx}", poly, "x", sx * 5.5, sx * 6.1, m, head)
        trim(f"{tag} bolt horn trim {sx}", zz, "x", sx * 6.22, head)
    crack(f"{tag} helm crack", [(x, HF - 0.58, z) for x, z in zigzag((2.6, 10.8), (3.6, 7.0), 3, 0.5)], head)
    legs_common(tag, rig, m, knee="plate", toe="wedge", fin=True)


def armour_A3(tag, rig):
    """Y3 dread, Hollow Dread."""
    m = SHELL["y3"]; body, head = rig["body"], rig["head"]
    fplate(f"{tag} sternum", [(-0.7, 11.6), (0.7, 11.6), (0.6, 1.0), (0.0, 0.0), (-0.6, 1.0)], m, body, y=-4.9, t=0.55)
    for k in range(5):                                       # ribcage bars curving down at the ends, gaps between
        z = 10.6 - k * 2.2; w = 3.8 - 0.15 * k; sag = 0.9 + 0.15 * k
        poly = [(-w, z - sag), (-w * 0.6, z - 0.2), (-0.7, z), (0.7, z), (w * 0.6, z - 0.2), (w, z - sag),
                (w, z - sag - 0.9), (w * 0.6, z - 1.15), (0.7, z - 1.0), (-0.7, z - 1.0), (-w * 0.6, z - 1.15), (-w, z - sag - 0.9)]
        fplate(f"{tag} rib {k}", poly[::-1], m, body, y=-4.75, t=0.45, trim_pts=poly[6:])
    fplate(f"{tag} belly plate", [(-3.6, 0.0), (3.6, 0.0), (3.0, -0.9), (-3.0, -0.9)], m, body, y=-4.75)
    for s in (-1, 1):
        for k in range(3):
            z = 5.6 - k * 2.4
            splate(f"{tag} side rib {s} {k}", s, [(-3.4, z), (3.4, z - 0.6), (3.4, z - 1.6), (-3.4, z - 1.0)], m, body)
    bplate(f"{tag} back", [(-4.6, -0.8), (4.6, -0.8), (4.6, 12.0), (-4.6, 12.0)], m, body)
    for k in range(3):                                       # the cowl: three layered back plates rising over the head
        y = 6.3 + 0.7 * k; top = 26.0 - 2.2 * k; w = 5.6 - 0.6 * k
        poly = [(-w + 0.4, 9.0 - k * 2.5), (w - 0.4, 9.0 - k * 2.5)] + saw((w, top - 4.0), (-w, top - 4.0), 3, 2.4, out=(0, 1)) + [(-w, top - 4.0)]
        bplate(f"{tag} cowl {k}", poly, m, body, y=y, t=0.5, trim_pts=poly[2:])
    crack(f"{tag} cowl crack", [(x, 6.24, z) for x, z in ((-1.0, 20.6), (-1.6, 18.8), (-0.6, 17.4), (-1.4, 15.6))], body)
    for k, (x0, w, l) in enumerate(((-4.2, 1.3, 5.2), (-2.8, 1.1, 3.6), (-1.6, 1.4, 4.4), (-0.1, 1.2, 3.0), (1.2, 1.3, 4.8), (2.6, 1.6, 3.9))):
        l = min(l, 4.0)                                      # long ragged strips, but end above the shin guards' swing
        tq = [(x0 + w, -l + 0.8), (x0 + w * 0.4, -l), (x0, -l + 0.5)]
        fplate(f"{tag} strip {k}", [(x0, 0.0), (x0 + w, 0.0)] + tq, m, body, y=-4.75 - 0.3 * (k % 2), t=0.4, trim_pts=tq)
    for s in (-1, 1):
        for k, (y0, w, l) in enumerate(((-3.4, 2.0, 3.8), (-1.2, 2.2, 3.0), (1.2, 2.2, 3.6))):
            splate(f"{tag} side strip {s} {k}", s, [(y0, 0.0), (y0 + w, 0.0), (y0 + w, -l + 0.7), (y0 + w * 0.5, -l), (y0, -l + 0.6)], m, body,
                   x=5.75 + 0.3 * (k % 2), t=0.4)
    for side in ("r", "l"):                                  # drooping hooked pauldrons
        aprism_top(f"{tag} pauldron {side}", rig, side, [(0.2, -2.6), (4.0, -2.0), (4.4, 3.6), (0.2, 4.2)], 3.25, 3.8, m)
        aprism_side(f"{tag} pauldron drape {side}", rig, side, [(3.25, -2.6), (3.25, 4.2), (-3.4, 3.6), (-2.2, 1.4), (-4.2, 0.0), (-2.4, -2.0)], 3.8, 4.3, m)
        horn(f"{tag} pauldron hook {side}", [AL(-1 if side == "r" else 1, *p) for p in ((4.0, -0.5, 1.0), (4.6, -2.2, 1.6), (4.4, -3.8, 2.6), (3.6, -4.6, 3.6))], 0.6, m,
             rig["arm_" + side], side=(0, 0, 1))
        gauntlet(f"{tag}", rig, side, m)
        for k, w in enumerate((-1.4, 0.0, 1.4)):            # long curved claws
            s = -1 if side == "r" else 1
            horn(f"{tag} claw {k} {side}", [AL(s, *p) for p in ((0.6 * (k - 1), w, 10.0), (0.7 * (k - 1), w - 0.2, 11.6), (0.8 * (k - 1), w - 1.2, 13.0))],
                 0.42, m, rig["arm_" + side], side=(1, 0, 0))
    # hooded helm: the hood overhangs the brow, a hollow dark face, fangs hanging in front
    brow = [(-HS - 0.5, 7.0), (HS + 0.5, 7.0), (HS + 0.5, HT + 0.5), (-HS - 0.5, HT + 0.5)]
    helm_shell(f"{tag}", head, m, brow, slit=(5.0, 6.8))
    prism(f"{tag} hood peak", [(-HS - 0.9, HF - 2.4), (HS + 0.9, HF - 2.4), (HS + 0.9, HB + 0.5), (-HS - 0.9, HB + 0.5)], "z", HT + 0.5, HT + 1.0, m, head)
    brim = saw((-HS - 0.9, 8.2), (HS + 0.9, 8.2), 5, 0.8, out=(0, -1)) + [(HS + 0.9, 8.2)]
    prism(f"{tag} hood brim", brim + [(HS + 0.9, HT + 1.0), (-HS - 0.9, HT + 1.0)], "y", HF - 2.4, HF - 1.9, m, head)
    trim(f"{tag} hood brim trim", brim, "y", HF - 2.52, head)
    pbox(f"{tag} hollow face", (-HS, -5.0, 0.6), (HS, -4.8, 4.8), CORE, head)
    for k, (x, l) in enumerate(((-4.0, 2.2), (-3.0, 2.8), (3.0, 2.6), (4.0, 2.0))):
        spike(f"{tag} fang {k}", (x, -6.4, 8.0), (x * 0.98, -6.6, 8.0 - l), 0.5, m, head)
    crack(f"{tag} helm crack", [(-1.2, HF - 2.48, 10.8), (-0.4, HF - 2.48, 9.8), (-1.0, HF - 2.48, 8.8)], head)
    legs_common(tag, rig, m, knee="spike", toe="claws", spur=True)


def armour_A4(tag, rig):
    """Mix, Fear Knight: Y3 plates, Y1 scales, Y2 boss, cracks and spikes."""
    m3, m1, m2 = SHELL["y3"], SHELL["y1"], SHELL["y2"]; body, head = rig["body"], rig["head"]
    bp = [(-3.8, 12.0), (3.8, 12.0), (3.8, 3.6), (2.6, 2.4), (0.0, 1.6), (-2.6, 2.4), (-3.8, 3.6)]
    fplate(f"{tag} breastplate", bp, m3, body, trim_pts=bp[2:])
    boss = [(0.0, 9.6), (1.8, 7.0), (0.0, 4.4), (-1.8, 7.0)]
    fplate(f"{tag} boss", boss, m2, body, y=-5.25, t=0.6, trim_pts=boss + [boss[0]])
    spike(f"{tag} boss spike", (0, -5.8, 7.0), (0, -7.6, 6.6), 0.7, m2, body)
    for r in range(2):                                       # Y1 scale waist band
        n = 4
        for c in range(n):
            a = -3.8 + c * 1.9 + (0.95 if r else 0); b = a + 1.95
            if b > 3.9:
                continue
            tq = [(b, 2.0 - r * 1.6), ((a + b) / 2, 1.2 - r * 1.6), (a, 2.0 - r * 1.6)]
            fplate(f"{tag} waist scale {r} {c}", [(a, 3.0 - r * 1.6), (b, 3.0 - r * 1.6)] + tq, m1, body, y=-5.0 - 0.3 * r, t=0.4, trim_pts=tq)
    for k, pts in enumerate(([(-3.0, 11.4), (-2.2, 10.2), (-2.9, 9.0), (-2.0, 7.6)], [(2.2, 4.2), (3.0, 5.2), (2.4, 6.4)])):
        crack(f"{tag} chest crack {k}", [(x, -5.33, z) for x, z in pts], body)
    for k, x in enumerate((-3.4, -2.8, 2.8, 3.4)):           # spiked gorget: front pair each side (clear of nose and arms)
        spike(f"{tag} gorget front {k}", (x, -4.6, 11.0), (x * 1.05, -6.0, 12.4), 0.5, m2, body)
    for k, x in enumerate((-3.2, -1.6, 0.0, 1.6, 3.2)):      # and a fan behind the neck, under the helm's back
        spike(f"{tag} gorget back {k}", (x, 4.4, 11.0), (x * 1.1, 6.9, 12.8 + 0.4 * (k % 2)), 0.55, m2, body)
    for s in (-1, 1):
        splate(f"{tag} chest side {s}", s, [(-3.6, 6.4), (3.6, 6.4), (3.6, -0.4), (-3.6, -0.4)], m3, body)
        splate(f"{tag} side tasset {s}", s, [(-3.0, -0.6), (3.0, -0.6), (3.0, -2.4), (0.0, -3.8), (-3.0, -2.4)], m1, body)
    bplate(f"{tag} back", [(-4.6, -0.6), (4.6, -0.6), (4.6, 12.0), (-4.6, 12.0)], m3, body)
    for s in (-1, 1):                                        # Y1 scale tassets
        for c in range(2):
            a = 0.2 + c * 2.0 if s > 0 else -0.2 - (c + 1) * 2.0; b = a + 2.0
            fplate(f"{tag} tasset {s} {c}", [(a, -0.3), (b, -0.3), (b, -2.6), ((a + b) / 2, -3.8), (a, -2.6)], m1, body, y=-4.75,
                   trim_pts=[(b, -2.6), ((a + b) / 2, -3.8), (a, -2.6)])
    for side in ("r", "l"):                                  # Y1 scale tiers capped by a Y3 dome plate and a horn
        s = -1 if side == "r" else 1
        for k in range(3):
            a0 = -2.4 + k * 1.9
            aprism_side(f"{tag} pauldron scale {k} {side}", rig, side, [(3.5, a0), (3.5, a0 + 2.2), (0.0, a0 + 2.2), (-1.4, a0 + 1.1), (0.0, a0)],
                        3.25 + 0.2 * k, 3.65 + 0.2 * k, m1, trim_pts=[(0.0, a0 + 2.2), (-1.4, a0 + 1.1), (0.0, a0)])
        aprism_top(f"{tag} pauldron cap {side}", rig, side, [(0.2, -2.6), (4.3, -2.6), (4.3, 4.0), (0.2, 4.0)], 3.5, 4.0, m3)
        horn(f"{tag} pauldron horn {side}", [AL(s, *p) for p in ((2.6, 4.0, 0.6), (3.6, 5.8, 0.2), (4.0, 7.6, -1.0), (3.6, 8.8, -2.4))], 0.75, m2,
             rig["arm_" + side], side=(0, 0, 1))
        gauntlet(f"{tag}", rig, side, m3)
        crack(f"{tag} gauntlet crack {side}", [AL(s, *p) for p in ((3.8, 0.5, 7.4), (3.8, -0.6, 8.4), (3.8, 0.4, 9.6))], rig["arm_" + side], axis="x")
    # great helm in Y3, a Y1 serrated crest front to back, Y2 cracks, a narrow slit
    brow = [(-HS - 0.5, 5.8), (HS + 0.5, 5.8), (HS + 0.5, HT + 0.5), (-HS - 0.5, HT + 0.5)]
    helm_shell(f"{tag}", head, m3, brow, slit=(4.9, 5.8))
    for k in range(5):
        y = -4.4 + k * 2.2
        prism(f"{tag} crest {k}", [(y - 1.0, HT + 0.5), (y + 1.2, HT + 0.5), (y + 0.9, HT + 2.0 + 0.5 * (k % 2)), (y - 0.6, HT + 3.0 - 0.3 * k)], "x", -0.35, 0.35, m1, head)
    for k, pts in enumerate(([(-3.4, 10.8), (-2.6, 9.4), (-3.3, 8.2), (-2.4, 7.0)], [(3.0, 3.9), (3.8, 2.8), (3.2, 1.6)])):
        crack(f"{tag} helm crack {k}", [(x, HF - 0.58, z) for x, z in pts], head)
    legs_common(tag, rig, m3, knee="spike", toe="claws", knee_m=m2)


ARMOUR = {"A1": armour_A1, "A2": armour_A2, "A3": armour_A3, "A4": armour_A4}


# ------------------------------------------------------------------ tools (built in the grip frame, metres; blade in
# the YZ plane, thickness along X; the edge / spike / bit that works is on -Y, the side that leads when the arm swings)
def tp(nm, poly, hw, m, par):
    return prism_m(nm, poly, "x", -hw, hw, m, par, 0.25)


def edge(nm, pts, par, w=0.032, t=0.012):
    return sweep_m(nm, [(0, y, z) for y, z in pts], w, t, RIM, par, (1, 0, 0))


def tcrack(nm, pts, par, hw):
    out = []
    for sx in (-1, 1):
        out.append(sweep_m(f"{nm} {sx}", [(sx * (hw + 0.002), y, z) for y, z in pts], 0.004, 0.008, CRACK, par, (1, 0, 0)))
    return out


def handle(tag, par, z0=-0.13, z1=0.1, r=0.022, bands=3):
    box(f"{tag} grip core", (-r, -r, z0), (r, r, z1), GRIPM, par)
    for k in range(bands):
        z = z0 + 0.02 + k * (z1 - z0 - 0.04) / max(1, bands - 1)
        box(f"{tag} grip band {k}", (-r - 0.004, -r - 0.004, z - 0.006), (r + 0.004, r + 0.004, z + 0.006), RIM, par)


def haft(tag, par, z0, z1, m, r=0.024):
    box(f"{tag} haft shell", (-r, -r, z0), (r, r, z1), m, par, 0.25)
    box(f"{tag} haft core", (-r * 0.5, -r * 0.5, z0 + 0.01), (r * 0.5, r * 0.5, z1 - 0.01), CORE, par)


def sword_S1(tag, par, look):
    m = TSHELL[look]; handle(tag, par)
    spike_m(f"{tag} pommel", (0, 0, -0.13), (0, 0, -0.21), 0.03, m, par)
    guard = [(-0.13, 0.17), (-0.1, 0.11), (0.1, 0.11), (0.14, 0.18), (0.08, 0.15), (-0.07, 0.15)]
    tp(f"{tag} guard", guard, 0.034, m, par)
    front = [(-0.05, 0.15), (-0.049, 0.45), (-0.046, 0.72), (-0.04, 0.86), (-0.008, 0.995)]
    back = saw((0.05, 0.84), (0.05, 0.2), 7, 0.026, out=(1, 0), skew=0.2)
    blade = front + [(0.03, 0.9)] + back + [(0.05, 0.2), (0.05, 0.15)]
    tp(f"{tag} blade", blade, 0.02, m, par)
    tp(f"{tag} blade core", [(-0.03, 0.2), (-0.026, 0.82), (-0.004, 0.9), (0.026, 0.8), (0.03, 0.2)], 0.009, CORE, par)
    edge(f"{tag} edge", [(y - 0.004, z) for y, z in front], par)
    for k in range(2):                                       # scale-cut ricasso plates
        tp(f"{tag} ricasso scale {k}", [(-0.055, 0.15 + k * 0.06), (0.055, 0.15 + k * 0.06), (0.055, 0.2 + k * 0.06), (0.0, 0.23 + k * 0.06), (-0.055, 0.2 + k * 0.06)],
           0.026, m, par)
    tcrack(f"{tag} crack", [(0.012, 0.36), (0.002, 0.46), (0.014, 0.56), (0.0, 0.68)], par, 0.02)


def sword_S2(tag, par, look):
    m = TSHELL[look]; handle(tag, par)
    box(f"{tag} pommel", (-0.03, -0.03, -0.17), (0.03, 0.03, -0.13), m, par, 0.25)
    tp(f"{tag} guard", [(-0.07, 0.11), (0.08, 0.11), (0.08, 0.15), (0.0, 0.15), (-0.16, 0.24), (-0.09, 0.15), (-0.07, 0.15)], 0.032, m, par)
    secs = 6; outline_f, outline_b = [], []
    for i in range(secs + 1):                               # zigzag sections shifting alternately
        z = 0.15 + i * 0.12; off = (0.022 if i % 2 else -0.012) if 0 < i < secs else 0.0
        w = 0.05 - 0.004 * i
        outline_f.append((-w + off, z)); outline_b.append((w * 0.85 + off, z + 0.03))
    tipf = (-0.03, 0.99); tipb = (0.03, 0.96)
    blade = outline_f[:-1] + [tipf, (0.0, 0.9), tipb] + outline_b[:-1][::-1]
    blade = [outline_f[0]] + blade[1:] + [(outline_b[0][0], 0.15)]
    tp(f"{tag} blade", blade, 0.02, m, par)
    tp(f"{tag} blade core", [(p[0] * 0.45, p[1]) for p in blade if p[1] < 0.9], 0.009, CORE, par)
    edge(f"{tag} edge", [(y - 0.004, z) for y, z in outline_f[:-1]] + [tipf], par)
    tcrack(f"{tag} crack a", zigzag((0.01, 0.3), (0.0, 0.78), 5, 0.012), par, 0.02)
    tcrack(f"{tag} crack b", [(0.0, 0.52), (0.024, 0.58), (0.016, 0.64)], par, 0.02)


def sword_S3(tag, par, look):
    m = TSHELL[look]; handle(tag, par)
    spike_m(f"{tag} pommel", (0, 0, -0.13), (0, 0.02, -0.2), 0.032, m, par)
    for k, (y, l) in enumerate(((-0.06, 0.13), (0.0, 0.16), (0.06, 0.12))):          # claw guard curling over the hand
        sweep_m(f"{tag} claw {k}", [(0, y * 0.4, 0.13), (0, y - 0.03, 0.1), (0, y - 0.07, 0.13 - l * 0.5), (0, y - 0.09, 0.13 - l)],
                [0.03, 0.026, 0.016, 0.004], [0.026, 0.022, 0.014, 0.004], m, par, (1, 0, 0))
    tp(f"{tag} guard", [(-0.08, 0.11), (0.08, 0.11), (0.06, 0.15), (-0.06, 0.15)], 0.03, m, par)
    front = [(-0.04, 0.15), (-0.05, 0.4), (-0.075, 0.62), (-0.1, 0.8), (-0.09, 0.9), (-0.03, 0.98)]
    back = [(0.035, 0.84), (0.09, 0.8), (0.05, 0.76), (0.035, 0.6), (0.035, 0.15)]       # the back hook near the tip
    blade = front + [(0.0, 0.93)] + back
    tp(f"{tag} blade", blade, 0.02, m, par)
    tp(f"{tag} blade core", [(-0.02, 0.2), (-0.03, 0.42), (-0.055, 0.64), (-0.065, 0.82), (-0.02, 0.88), (0.02, 0.76), (0.018, 0.2)], 0.009, CORE, par)
    edge(f"{tag} edge", [(y - 0.004, z) for y, z in front], par)
    tcrack(f"{tag} crack", [(-0.01, 0.32), (-0.03, 0.44), (-0.012, 0.52), (-0.04, 0.66)], par, 0.02)


def axe_X1(tag, par, look):
    m = TSHELL[look]; haft(tag, par, -0.2, 0.7, m); handle(tag, par, -0.2, 0.06, 0.026, 2)
    bit = [(-0.03, 0.47), (-0.1, 0.5)] + saw((-0.2, 0.42), (-0.2, 0.78), 5, 0.03, out=(-1, 0)) + [(-0.2, 0.78), (-0.1, 0.72), (-0.03, 0.74)]
    bit = [(-0.03, 0.47), (-0.1, 0.5), (-0.2, 0.42)] + saw((-0.2, 0.42), (-0.2, 0.78), 5, 0.03, out=(-1, 0))[1:] + [(-0.2, 0.78), (-0.1, 0.72), (-0.03, 0.74)]
    tp(f"{tag} bit", bit, 0.018, m, par)
    tp(f"{tag} bit core", [(-0.035, 0.53), (-0.15, 0.5), (-0.16, 0.7), (-0.035, 0.69)], 0.008, CORE, par)
    edge(f"{tag} edge", [(-0.206, 0.42), (-0.206, 0.6), (-0.206, 0.78)], par, w=0.026)
    box(f"{tag} socket", (-0.04, -0.04, 0.5), (0.04, 0.04, 0.74), m, par, 0.25)
    spike_m(f"{tag} back spike", (0, 0.04, 0.62), (0, 0.17, 0.6), 0.035, m, par)
    spike_m(f"{tag} top spike", (0, 0, 0.74), (0, -0.01, 0.86), 0.03, m, par)
    tcrack(f"{tag} crack", zigzag((-0.06, 0.66), (-0.16, 0.56), 3, 0.012), par, 0.018)


def axe_X2(tag, par, look):
    m = TSHELL[look]; haft(tag, par, -0.22, 0.76, m); handle(tag, par, -0.22, 0.04, 0.026, 2)
    for k in range(5):
        z = 0.1 + k * 0.1
        box(f"{tag} haft rib {k}", (-0.03, -0.03, z), (0.03, 0.03, z + 0.018), m, par, 0.25)
    arc = [(-0.03 - 0.2 * math.sin(math.pi * t) - 0.04 * t, 0.36 + 0.5 * t) for t in np.linspace(0, 1, 9)]
    inner = [(-0.05 - 0.09 * math.sin(math.pi * t), 0.47 + 0.28 * t) for t in np.linspace(1, 0, 7)]
    crescent = [(-0.03, 0.36)] + [(-0.09, 0.32)] + arc[1:] + [(-0.11, 0.9), (-0.04, 0.8)] + inner
    tp(f"{tag} crescent", crescent, 0.016, m, par)
    tp(f"{tag} crescent core", [(p[0] * 0.75 - 0.01, p[1]) for p in arc[2:-2]] + [(-0.07, 0.62)], 0.007, CORE, par)
    edge(f"{tag} edge", [(y - 0.004, z) for y, z in arc[1:-1]], par, w=0.024)
    box(f"{tag} socket", (-0.04, -0.04, 0.45), (0.04, 0.04, 0.78), m, par, 0.25)
    sweep_m(f"{tag} back hook", [(0, 0.04, 0.66), (0, 0.12, 0.66), (0, 0.18, 0.6), (0, 0.19, 0.52)], [0.03, 0.026, 0.018, 0.004], [0.04, 0.03, 0.02, 0.004],
            m, par, (1, 0, 0))
    tcrack(f"{tag} crack", [(-0.12, 0.7), (-0.16, 0.64), (-0.14, 0.56)], par, 0.016)


def axe_X3(tag, par, look):
    m = TSHELL[look]; haft(tag, par, -0.2, 0.72, m); handle(tag, par, -0.2, 0.06, 0.026, 2)
    for k in range(3):                                       # overlapping scale plates stepping out to the edge
        y0 = -0.03 - k * 0.055; y1 = y0 - 0.09; zc = 0.6; h = 0.15 + 0.03 * k
        tp(f"{tag} scale {k}", [(y0, zc - h), (y1, zc - h - 0.05), (y1 - 0.02, zc), (y1, zc + h), (y0, zc + h * 0.8)], 0.02 - 0.004 * k, m, par)
    tp(f"{tag} bit core", [(-0.04, 0.5), (-0.17, 0.46), (-0.17, 0.72), (-0.04, 0.7)], 0.006, CORE, par)
    edge(f"{tag} edge", [(-0.235, 0.39), (-0.255, 0.6), (-0.235, 0.81)], par, w=0.016)
    box(f"{tag} socket", (-0.04, -0.04, 0.48), (0.04, 0.04, 0.73), m, par, 0.25)
    tp(f"{tag} cleaver back", [(0.04, 0.5), (0.1, 0.52), (0.12, 0.66), (0.04, 0.7)], 0.016, m, par)
    spike_m(f"{tag} butt spike", (0, 0, -0.2), (0, 0.02, -0.3), 0.03, m, par)
    tcrack(f"{tag} crack", [(-0.07, 0.7), (-0.1, 0.64), (-0.08, 0.58)], par, 0.014)


def pick_P1(tag, par, look):
    m = TSHELL[look]; haft(tag, par, -0.2, 0.74, m); handle(tag, par, -0.2, 0.06, 0.026, 2)
    top = [(0.0, 0.72), (-0.1, 0.72), (-0.2, 0.69), (-0.3, 0.62), (-0.37, 0.52)]
    bot = [(-0.36, 0.53), (-0.27, 0.6), (-0.18, 0.64), (-0.08, 0.66), (0.0, 0.66)]
    tp(f"{tag} spike", top + bot, 0.024, m, par)
    tp(f"{tag} spike core", [(-0.02, 0.705), (-0.2, 0.675), (-0.28, 0.62), (-0.18, 0.655), (-0.02, 0.675)], 0.01, CORE, par)
    edge(f"{tag} edge", [(-0.27, 0.6), (-0.33, 0.55), (-0.375, 0.515)], par, w=0.03)
    box(f"{tag} head", (-0.045, -0.045, 0.62), (0.045, 0.1, 0.76), m, par, 0.25)
    for k, (y, z) in enumerate(((0.08, 0.74), (0.08, 0.66), (0.08, 0.7))):
        spike_m(f"{tag} hammer spike {k}", (0.0 + 0.02 * (k - 1), 0.1, z), (0.0 + 0.03 * (k - 1), 0.16, z + 0.01), 0.02, m, par)
    for k in range(2):
        box(f"{tag} collar rib {k}", (-0.032, -0.032, 0.5 + k * 0.05), (0.032, 0.032, 0.52 + k * 0.05), m, par, 0.25)
    tcrack(f"{tag} crack", [(-0.1, 0.69), (-0.16, 0.675), (-0.22, 0.66)], par, 0.024)


def pick_P2(tag, par, look):
    m = TSHELL[look]; haft(tag, par, -0.2, 0.74, m); handle(tag, par, -0.2, 0.06, 0.026, 2)
    tp(f"{tag} spike", [(0.0, 0.73), (-0.16, 0.7), (-0.31, 0.64), (-0.18, 0.66), (0.0, 0.66)], 0.02, m, par)
    edge(f"{tag} edge", [(-0.22, 0.665), (-0.29, 0.645), (-0.315, 0.638)], par, w=0.026)
    tp(f"{tag} adze", [(0.0, 0.73), (0.12, 0.72), (0.2, 0.66), (0.22, 0.56), (0.17, 0.6), (0.1, 0.65), (0.0, 0.66)], 0.03, m, par)
    edge(f"{tag} adze edge", [(0.2, 0.655), (0.222, 0.6), (0.223, 0.56)], par, w=0.05)
    tp(f"{tag} core", [(-0.2, 0.68), (0.14, 0.69), (0.16, 0.67), (-0.2, 0.67)], 0.008, CORE, par)
    for k in range(3):                                       # scale collar
        z = 0.6 - k * 0.05
        tp(f"{tag} collar scale {k}", [(-0.05, z + 0.05), (0.05, z + 0.05), (0.05, z + 0.01), (0.0, z - 0.02), (-0.05, z + 0.01)], 0.04, m, par)
    box(f"{tag} head", (-0.04, -0.045, 0.64), (0.04, 0.045, 0.75), m, par, 0.25)


def pick_P3(tag, par, look):
    m = TSHELL[look]; haft(tag, par, -0.2, 0.74, m); handle(tag, par, -0.2, 0.06, 0.026, 2)
    for sx in (-1, 1):                                      # split twin head with a gap down the middle
        x0, x1 = sorted((sx * 0.008, sx * 0.03))
        zz = zigzag((-0.02, 0.7), (-0.34, 0.6), 4, 0.025)
        prong = zz + [(-0.31, 0.63)] + [(y + 0.015, z + 0.05) for y, z in zz[::-1][1:]]
        prism_m(f"{tag} front prong {sx}", prong, "x", x0, x1, m, par, 0.25)
        zb = zigzag((0.02, 0.72), (0.22, 0.66), 3, 0.02)
        back = zb + [(0.2, 0.7)] + [(y - 0.01, z + 0.04) for y, z in zb[::-1][1:]]
        prism_m(f"{tag} back prong {sx}", back, "x", x0, x1, m, par, 0.25)
        sweep_m(f"{tag} edge {sx}", [(sx * 0.019, y - 0.003, z - 0.004) for y, z in zz[-2:]], 0.022, 0.01, RIM, par, (1, 0, 0))
    box(f"{tag} gap glow", (-0.008, -0.2, 0.64), (0.008, 0.12, 0.72), CRACK, par)
    box(f"{tag} head", (-0.045, -0.045, 0.64), (0.045, 0.045, 0.77), m, par, 0.25)
    spike_m(f"{tag} top spike", (0, 0, 0.77), (0, 0, 0.85), 0.03, m, par)


# --- bows: riser along Z in the grip frame, the arrow flies along -Y, the string on +Y; the draw moves the nock
def bow_common(tag, par, look, H, L, riser_build, limb_build, cam_build, stab_build):
    m = TSHELL[look]
    root = empty(f"{tag} bow", (0, 0, 0), par)
    riser_build(tag, root, m, H)
    tips, limbs = [], []
    for sy in (-1, 1):
        lp = empty(f"{tag} limb {sy}", (0, 0.0, sy * H), root)
        limb_build(tag, lp, m, sy, L)
        tip = empty(f"{tag} tip {sy}", (0, 0.1, sy * L), lp)
        cam_build(tag, tip, m, sy)
        sa = empty(f"{tag} string anchor {sy}", (0, 0.03, 0), tip)
        tips.append(sa); limbs.append((lp, sy))
    stab_build(tag, root, m)
    box(f"{tag} grip", (-0.02, -0.02, -0.06), (0.02, 0.03, 0.06), GRIPM, root)
    box(f"{tag} rest", (0.016, -0.03, 0.06), (0.04, 0.0, 0.07), RIM, root)
    nock = empty(f"{tag} nock", (0, 0.13 + 0.03, 0), root)
    strings = []
    for k, sa in enumerate(tips):                            # the string: two lit rods stretched from each cam to the nock
        me = bpy.data.meshes.new(f"{tag} string {k}")
        r = 0.004
        vs = [(x, y, z) for x in (-r, r) for y in (0, 1) for z in (-r, r)]
        me.from_pydata(vs, [], BOXF); me.update(); me.materials.append(RIM)
        so = link(bpy.data.objects.new(f"{tag} string {k}", me)); so.parent = sa
        c = so.constraints.new("STRETCH_TO"); c.target = nock; c.rest_length = 1.0; c.volume = "NO_VOLUME"; c.keep_axis = "PLANE_Z"
        strings.append(so)
    return dict(root=root, nock=nock, limbs=limbs, tips=tips, m=m)


def arrow(tag, par, m):
    """A construct arrow from the nock (y 0) to the head (y -0.62)."""
    a = empty(f"{tag} arrow", (0, 0, 0), par)
    box(f"{tag} arrow shaft", (-0.006, -0.56, -0.006), (0.006, 0.0, 0.006), m, a, 0.2)
    box(f"{tag} arrow core", (-0.003, -0.55, -0.003), (0.003, -0.01, 0.003), RIM, a)
    spike_m(f"{tag} arrow head", (0, -0.56, 0), (0, -0.64, 0), 0.016, RIM, a)
    for k in range(3):
        an = 2 * math.pi * k / 3
        d = Vector((math.cos(an), 0, math.sin(an)))
        pts = [(0.0, 0.0), (0.0, -0.09), (0.022, -0.06), (0.022, -0.01)]
        prism_m(f"{tag} vane {k}", [(p[1], p[0]) for p in pts], "x", -0.0015, 0.0015, CORE, empty(f"{tag} vane pivot {k}", (0, 0, 0), a, rot=(0, -math.degrees(an) + 90, 0)), 0.2)
    return a


def b1_riser(tag, root, m, H):
    for k in range(7):                                       # swept riser of stacked scale plates
        z = -H + k * (2 * H / 7); off = -0.05 * math.cos(math.pi * (z + H / 7) / (2 * H))
        tp(f"{tag} riser scale {k}", [(off - 0.045, z), (off + 0.05, z), (off + 0.05, z + 2 * H / 7 * 0.8), (off, z + 2 * H / 7 * 1.2), (off - 0.045, z + 2 * H / 7 * 0.8)],
           0.024, m, root)
        edge(f"{tag} riser edge {k}", [(off - 0.05, z + 0.005), (off - 0.05, z + 2 * H / 7 * 0.78)], root, w=0.03, t=0.008)
    tp(f"{tag} riser core", [(-0.06, -H * 0.6), (-0.04, -H * 0.6), (-0.04, H * 0.6), (-0.06, H * 0.6)], 0.006, CORE, root)
    rod_m(f"{tag} sight bar", (0.03, -0.03, 0.1), (0.03, -0.13, 0.1), 0.006, m, root)
    box(f"{tag} sight pin", (0.024, -0.14, 0.09), (0.036, -0.13, 0.11), RIM, root)


def b1_limb(tag, lp, m, sy, L):
    for sx in (-1, 1):
        pts = [(0.0, 0.0), (0.05, sy * L * 0.5), (0.1, sy * L)]
        poly = [(y, z) for y, z in pts] + saw((0.135, sy * L), (0.045, 0.0), 4, 0.02, out=(1, 0))[1:] + [(0.045, 0.0)]
        prism_m(f"{tag} limb {sy} {sx}", poly if sy > 0 else poly[::-1], "x", min(sx * 0.01, sx * 0.032), max(sx * 0.01, sx * 0.032), m, lp, 0.25)
        sweep_m(f"{tag} limb edge {sy} {sx}", [(sx * 0.021, y - 0.004, z) for y, z in pts], 0.022, 0.008, RIM, lp, (1, 0, 0))


def b1_cam(tag, tip, m, sy):
    prof = [(math.cos(t) * 0.055 * (1 + 0.25 * math.cos(t)), math.sin(t) * 0.055) for t in np.linspace(0, 2 * math.pi, 14, endpoint=False)]
    prism_m(f"{tag} cam {sy}", prof, "x", -0.008, 0.008, m, tip, 0.2)
    box(f"{tag} cam axle {sy}", (-0.016, -0.006, -0.006), (0.016, 0.006, 0.006), RIM, tip)


def b1_stab(tag, root, m):
    rod_m(f"{tag} stabiliser", (0, -0.03, -0.08), (0, -0.4, -0.1), 0.012, m, root)
    box(f"{tag} stab weight", (-0.02, -0.44, -0.12), (0.02, -0.4, -0.08), RIM, root)


def b2_riser(tag, root, m, H):
    zz = zigzag((0.0, -H), (0.0, H), 6, 0.035)
    poly = [(y - 0.04, z) for y, z in zz] + [(y + 0.045, z) for y, z in zz[::-1]]
    tp(f"{tag} riser", poly, 0.024, m, root)
    tp(f"{tag} riser core", [(y - 0.012, z) for y, z in zz[1:-1]] + [(y + 0.018, z) for y, z in zz[1:-1][::-1]], 0.01, CORE, root)
    edge(f"{tag} riser edge", [(y - 0.044, z) for y, z in zz], root, w=0.034, t=0.008)
    tcrack(f"{tag} riser crack", [(y, z) for y, z in zz[1:-1]], root, 0.024)


def b2_limb(tag, lp, m, sy, L):
    zz = zigzag((0.0, 0.0), (0.1, sy * L), 4, 0.018)
    poly = [(y - 0.02, z) for y, z in zz] + [(y + 0.022, z) for y, z in zz[::-1]]
    prism_m(f"{tag} limb {sy}", poly, "x", -0.02, 0.02, m, lp, 0.25)
    edge(f"{tag} limb edge {sy}", [(y - 0.023, z) for y, z in zz], lp, w=0.03, t=0.008)


def b2_cam(tag, tip, m, sy):
    star = []
    for k in range(10):
        r = 0.064 if k % 2 == 0 else 0.034
        star.append((r * math.cos(2 * math.pi * k / 10), r * math.sin(2 * math.pi * k / 10)))
    prism_m(f"{tag} cam {sy}", star, "x", -0.008, 0.008, m, tip, 0.2)
    box(f"{tag} cam axle {sy}", (-0.016, -0.006, -0.006), (0.016, 0.006, 0.006), RIM, tip)


def b2_stab(tag, root, m):
    rod_m(f"{tag} stabiliser", (0, -0.03, -0.08), (0, -0.5, -0.12), 0.011, m, root)
    for k in range(3):
        y = -0.18 - k * 0.11
        tp(f"{tag} stab fin {k}", zigzag((y, -0.1), (y - 0.04, -0.2), 2, 0.012) + [(y - 0.06, -0.18)], 0.004, m, root)
    box(f"{tag} stab tip", (-0.018, -0.54, -0.14), (0.018, -0.5, -0.1), RIM, root)


def b3_riser(tag, root, m, H):
    for sy_, y in ((0, -0.05), (1, 0.03)):
        pts = [(0, y - 0.03 * math.cos(math.pi * z / (2 * H)), z) for z in np.linspace(-H, H, 9)]
        sweep_m(f"{tag} riser rail {sy_}", pts, 0.036, 0.024, m, root, (1, 0, 0))
        if sy_ == 0:
            sweep_m(f"{tag} riser edge", [(0, y_ - 0.014, z_) for _x, y_, z_ in pts], 0.026, 0.008, RIM, root, (1, 0, 0))
    for k in range(6):
        z = -H * 0.8 + k * (1.6 * H / 5)
        box(f"{tag} riser rib {k}", (-0.012, -0.08 + 0.03 * (1 - math.cos(math.pi * z / (2 * H))), z - 0.008), (0.012, 0.03, z + 0.008), CORE if k % 2 else m, root, 0.2)


def b3_limb(tag, lp, m, sy, L):
    pts = [(0, 0.0, 0.0), (0, 0.04, sy * L * 0.45), (0, 0.04, sy * L * 0.85), (0, 0.1, sy * L), (0, 0.06, sy * L * 1.12)]
    sweep_m(f"{tag} limb {sy}", pts, [0.042, 0.036, 0.03, 0.024, 0.005], [0.034, 0.028, 0.022, 0.018, 0.005], m, lp, (1, 0, 0))
    sweep_m(f"{tag} limb edge {sy}", [(0, y - 0.016, z) for _x, y, z in pts[:4]], 0.024, 0.007, RIM, lp, (1, 0, 0))
    spike_m(f"{tag} limb claw {sy}", (0, 0.06, sy * L * 0.7), (0, -0.04, sy * L * 0.78), 0.012, m, lp)


def b3_cam(tag, tip, m, sy):
    prism_m(f"{tag} cam {sy}", [(-0.05, -0.03), (0.055, -0.04), (0.045, 0.04), (-0.015, 0.055), (-0.07, 0.08)], "x", -0.01, 0.01, m, tip, 0.2)
    box(f"{tag} cam axle {sy}", (-0.016, -0.006, -0.006), (0.016, 0.006, 0.006), RIM, tip)


def b3_stab(tag, root, m):
    rod_m(f"{tag} stabiliser", (0, -0.05, -0.08), (0, -0.42, -0.1), 0.012, m, root)
    for k in range(4):
        y = -0.12 - k * 0.08; sx = 1 if k % 2 else -1
        spike_m(f"{tag} thorn {k}", (0, y, -0.09), (sx * 0.05, y + 0.03, -0.06), 0.008, m, root)


BOWS = {"B1": (0.17, 0.42, b1_riser, b1_limb, b1_cam, b1_stab), "B2": (0.17, 0.41, b2_riser, b2_limb, b2_cam, b2_stab),
        "B3": (0.18, 0.42, b3_riser, b3_limb, b3_cam, b3_stab)}
TOOLS = {"S1": sword_S1, "S2": sword_S2, "S3": sword_S3, "X1": axe_X1, "X2": axe_X2, "X3": axe_X3,
         "P1": pick_P1, "P2": pick_P2, "P3": pick_P3}


# ------------------------------------------------------------------ the takes
TAKES = [
    ("A1", "armour", "y1", "Y1 scales: Scale Reaver", "pointed scale rows (lower rows further out), saw-edged tiered pauldrons with spikes, saw-brow helm with five swept crown spikes, nose guard, scale tassets, knee spikes, clawed boots"),
    ("A2", "armour", "y2", "Y2 lightning: Storm-split", "breastplate split by a glowing lightning gap, halves uneven, branching cracks; one huge bolt-finned pauldron, one small; wedge helm, chevron slit, zigzag bolt horns; uneven blade tassets, finned greaves, wedge boots"),
    ("A3", "armour", "y3", "Y3 dread: Hollow Dread", "ribcage bars over the robe, a three-layer saw-topped cowl rising behind the head, drooping hooked pauldrons, long curved claws, hooded helm with a hollow face and fangs, ragged strip tassets, heel spurs"),
    ("A4", "armour", "mix", "Mix: Fear Knight", "Y3 breastplate and great helm, Y2 boss spike and spiked gorget ring, Y1 scale waist, pauldron tiers, crest and tassets, Y2 pauldron horns and knee spikes, cracks"),
    ("S1", "sword", "y1", "Sword, Y1: barbed saw-back", "straight blade, barbed saw back, hooked guard, scale-cut ricasso, dark core, lit cutting edge"),
    ("S2", "sword", "y2", "Sword, Y2: lightning blade", "zigzag blade in offset sections, forked tip, cracks, one-sided spike guard"),
    ("S3", "sword", "y3", "Sword, Y3: dread falchion", "blade widening to a clipped point, back hook, claw guard curling over the hand"),
    ("X1", "axe", "y2", "Axe, Y2: saw-bearded", "bearded bit with a sawtooth edge, back spike, top spike, zigzag crack"),
    ("X2", "axe", "y3", "Axe, Y3: crescent hook", "big crescent bit with hooked horns, back hook, ribbed haft"),
    ("X3", "axe", "y1", "Axe, Y1: scale cleaver", "three overlapping scale plates stepping out to the edge, cleaver back, spiked butt"),
    ("P1", "pick", "y3", "Pick, Y3: drooping horn", "long front spike curving down, short spiked hammer back, collar ribs"),
    ("P2", "pick", "y1", "Pick, Y1: spike and adze", "front spike, back adze blade, scale collar plates"),
    ("P3", "pick", "y2", "Pick, Y2: split bolt", "split twin head with a glowing gap, zigzag bolt prongs front and back"),
    ("B1", "bow", "y1", "Bow, Y1: scale compound", "swept riser of stacked scale plates, saw-edged split limbs, twin cams, sight pin, stabiliser"),
    ("B2", "bow", "y2", "Bow, Y2: bolt compound", "zigzag bolt riser and limbs with lit edges, star cams, long stabiliser with bolt fins"),
    ("B3", "bow", "y3", "Bow, Y3: hooked dread bow", "hollow ribbed riser (two rails, rib bars), hooked limbs with claws, thorn stabiliser"),
]
SPACE = 20.0
HOLD = 125                                           # rest hold: the tool tipped 35 deg forward


def build_gear(tag, rig, code, kind, look, static=False):
    out = {}
    if kind == "armour":
        ARMOUR[code](tag, rig)
    elif kind == "bow":
        H, L, rb, lb, cb, sb = BOWS[code]
        out["bow"] = bow_common(tag, rig["grip_l"], look, H, L, rb, lb, cb, sb)
        if not static:
            out["arrow"] = arrow(tag, out["bow"]["nock"], TSHELL[look])
    else:
        rig["grip_r"].rotation_euler = (R(HOLD), 0, 0)               # held tipped forward, the working edge ahead
        tr = empty(f"{tag} tool", (0, 0, 0), rig["grip_r"]); tr.scale = (1.25, 1.45, 1.25)
        TOOLS[code](tag, tr, look)
    return out


def walk(rig, y0):
    """Zombie walk toward the camera (-Y): 1.8 m in 45 frames, legs 20 deg, arms forward with a little sway."""
    for f in range(1, WALK_END + 1, 2):
        t = (f - 1) / (WALK_END - 1); ph = 2 * math.pi * (f - 1) / 22.0
        key(rig["root"], f, loc=(rig["root"].location.x, y0 + 1.6 - 1.8 * t, 0))
        sw = 20 * math.sin(ph)
        keyd(rig["leg_r"], f, (-sw, 0, 0)); keyd(rig["leg_l"], f, (sw, 0, 0))
        keyd(rig["arm_r"], f, (-90 + 4 * math.sin(ph), 0, 2 * math.sin(ph))); keyd(rig["arm_l"], f, (-90 - 4 * math.sin(ph), 0, 2 * math.sin(ph)))
        key(rig["body"], f, loc=(0, 0, 12 * P + 0.025 * abs(math.sin(ph))), rot=(R(2), R(3 * math.sin(ph)), R(4 * math.sin(ph))))
        keyd(rig["head"], f, (3 * math.sin(ph * 0.5), 4 * math.sin(ph * 0.5 + 1), 6 * math.sin(ph * 0.5)))
    return y0 + 1.6 - 1.8


def settle_legs(rig, f, stance=(0, 0)):
    keyd(rig["leg_r"], f, (stance[0], 0, 0)); keyd(rig["leg_l"], f, (stance[1], 0, 0))


def act_melee(rig, yend, rim):
    """Heavy cut: wind up overhead (46-54), short charge with the edge flaring (54-57), cut edge-first (57-61),
    recover (61-72). The wrist cocks back on the wind-up and snaps through on the cut."""
    ro, b, ar, g = rig["root"], rig["body"], rig["arm_r"], rig["grip_r"]
    x = ro.location.x
    settle_legs(rig, 50, (-12, 8))
    keyd(ar, WALK_END, (-90, 0, 0)); keyd(g, WALK_END, (HOLD, 0, 0))
    keyd(ar, 54, (-160, 0, -8)); keyd(g, 54, (75, 0, 0))
    key(b, 54, loc=(0, 0, 12 * P), rot=(R(-6), 0, R(-14)))
    keyd(ar, 57, (-166, 0, -8)); keyd(g, 57, (72, 0, 0)); key(b, 57, loc=(0, 0, 12 * P), rot=(R(-8), 0, R(-16)))
    key(ro, 57, loc=(x, yend, 0))
    keyd(ar, 60, (-46, 0, 6)); keyd(g, 60, (120, 0, 0)); key(b, 60, loc=(0, 0, 11.6 * P), rot=(R(14), 0, R(12)))
    key(ro, 60, loc=(x, yend - 0.3, 0)); settle_legs(rig, 60, (-22, 14))
    keyd(ar, 62, (-41, 0, 6)); keyd(g, 62, (123, 0, 0))
    keyd(ar, 72, (-90, 0, 0)); keyd(g, 72, (HOLD, 0, 0)); key(b, 72, loc=(0, 0, 12 * P), rot=(R(2), 0, 0))
    settle_legs(rig, 72, (-6, 4)); key(ro, 72, loc=(x, yend - 0.3, 0))
    keyd(ar, FRAME_END, (-90, 0, 0)); keyd(rig["arm_l"], 54, (-96, 0, 6)); keyd(rig["arm_l"], 60, (-80, 0, -4)); keyd(rig["arm_l"], 72, (-90, 0, 0))
    s = rim.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, v in ((1, 2.6), (52, 2.6), (55, 4.0), (57, 5.0), (60, 4.0), (64, 2.6)):
        s.default_value = v; s.keyframe_insert("default_value", frame=f)


def act_lunge(rig, yend):
    """Armour takes: rear back, lunge and grab (arms stay forward so no plate clips), recover."""
    ro, b = rig["root"], rig["body"]; x = ro.location.x
    for side in ("r", "l"):
        keyd(rig["arm_" + side], WALK_END, (-90, 0, 0)); keyd(rig["arm_" + side], 54, (-104, 0, 8 if side == "r" else -8))
        keyd(rig["arm_" + side], 59, (-80, 0, -6 if side == "r" else 6)); keyd(rig["arm_" + side], 72, (-90, 0, 0))
    key(b, 54, loc=(0, 0, 12 * P), rot=(R(-6), 0, 0)); key(b, 59, loc=(0, 0, 11.6 * P), rot=(R(12), 0, 0)); key(b, 72, loc=(0, 0, 12 * P), rot=(R(2), 0, 0))
    keyd(rig["head"], 54, (-8, 0, 0)); keyd(rig["head"], 59, (10, 0, 0)); keyd(rig["head"], 72, (0, 0, 0))
    settle_legs(rig, 52, (6, -6)); settle_legs(rig, 59, (-22, 14)); settle_legs(rig, 72, (-6, 4))
    key(ro, 54, loc=(x, yend + 0.05, 0)); key(ro, 59, loc=(x, yend - 0.35, 0)); key(ro, 72, loc=(x, yend - 0.35, 0))


def act_bow(rig, yend, gear, tag, look):
    """Turn side-on, draw (52-60), hold, loose at 64 (string snaps back, the arrow flies), recover."""
    ro, b, al, ar, gl = rig["root"], rig["body"], rig["arm_l"], rig["arm_r"], rig["grip_l"]
    bw = gear["bow"]; nock, arr = bw["nock"], gear["arrow"]; x = ro.location.x
    settle_legs(rig, 50, (-10, 10))
    keyd(al, WALK_END, (-90, 0, 0)); keyd(ar, WALK_END, (-90, 0, 0))
    key(b, WALK_END, loc=(0, 0, 12 * P), rot=(R(2), 0, 0))
    key(b, 52, loc=(0, 0, 12 * P), rot=(0, 0, R(-25))); keyd(al, 52, (-93, 0, -10)); keyd(ar, 52, (-93, 0, 30))
    keyd(ar, 60, (-93, 0, 56)); keyd(ar, 64, (-93, 0, 57))
    keyd(ar, 66, (-84, 0, 70)); keyd(ar, 76, (-90, 0, 0)); keyd(al, 64, (-93, 0, -10)); keyd(al, 66, (-88, 0, -10)); keyd(al, 76, (-90, 0, 0))
    key(b, 64, loc=(0, 0, 12 * P), rot=(0, 0, R(-25))); key(b, 76, loc=(0, 0, 12 * P), rot=(R(2), 0, 0))
    key(ro, 52, loc=(x, yend, 0)); key(ro, 76, loc=(x, yend, 0))
    # the nock follows the drawing hand
    c = nock.constraints.new("COPY_LOCATION"); c.target = rig["hand_r"]
    for f, v in ((1, 0.0), (51, 0.0), (53, 1.0), (64, 1.0), (65, 0.0)):
        c.influence = v; c.keyframe_insert("influence", frame=f)
    key(arr, 1, sc=0.0001); key(arr, 49, sc=0.0001); key(arr, 51, sc=1.0); key(arr, 64, sc=1.0); key(arr, 65, sc=0.0001)
    # limbs flex toward the string at full draw and shiver after the loose
    for lp, sy in bw["limbs"]:
        a = -sy * 9
        for f, v in ((1, 0), (53, 0), (60, a), (64, a), (65, -a * 0.35), (67, a * 0.2), (69, 0)):
            keyd(lp, f, (v, 0, 0))
    # keep the bow upright and aimed along the draw line while the body turns (solved once at full draw)
    for f in (1, WALK_END):
        keyd(gl, f, (90, 0, 0))
    bpy.context.view_layer.update(); scene.frame_set(60)
    d = gl.matrix_world.translation - rig["hand_r"].matrix_world.translation; d.z = 0
    yaw = math.atan2(d.x, -d.y)                                    # Rz(yaw) @ (0, -1, 0) is along d
    want = Matrix.Rotation(yaw, 4, "Z")
    for f in (52, 56, 60, 64, 66, 70, 76):
        scene.frame_set(f)
        par = gl.parent.matrix_world.to_3x3().normalized()
        loc = (par.inverted() @ want.to_3x3()).to_euler("XYZ", gl.rotation_euler)
        gl.rotation_euler = loc; gl.keyframe_insert("rotation_euler", frame=f)
    scene.frame_set(76)
    keyd(gl, 80, (90, 0, 0))
    # the flying arrow: a copy launched from the nocked arrow's place at the loose
    scene.frame_set(64); bpy.context.view_layer.update()
    mw = arr.matrix_world.copy()
    fly = empty(f"{tag} arrow flight", (0, 0, 0))
    arrow(f"{tag} flying", fly, TSHELL[look])
    fly.matrix_world = mw; fly.scale = (1, 1, 1)
    p0 = mw.translation.copy(); dirn = (mw.to_3x3() @ Vector((0, -1, 0))).normalized()
    fly.rotation_mode = "XYZ"
    key(fly, 1, loc=p0, sc=0.0001); key(fly, 63, loc=p0, sc=0.0001); key(fly, 64, loc=p0, sc=1.0)
    _p = bpy.context.preferences.edit; _p.keyframe_new_interpolation_type = "LINEAR"
    key(fly, 70, loc=p0 + dirn * 14.0, sc=1.0); key(fly, 71, loc=p0 + dirn * 14.0, sc=0.0001)
    _p.keyframe_new_interpolation_type = "BEZIER"
    fly.keyframe_insert("rotation_euler", frame=64)
    sc_ = TSHELL[look]


for i, (code, kind, look, nm, desc) in enumerate(TAKES):
    x = i * SPACE; y0 = 0.0; tag = f"ZV {code}"
    box(f"FG pad {code}", (x - 2.4, y0 - 2.6, -0.02), (x + 2.4, y0 + 3.2, 0.0), FLOOR)
    rig = zombie(tag, (x, y0 + 1.6, 0))
    gear = build_gear(tag, rig, code, kind, look)
    yend = walk(rig, y0)
    if kind == "armour":
        act_lunge(rig, yend)
    elif kind == "bow":
        act_bow(rig, yend, gear, tag, look)
    else:
        rimc = RIM.copy(); rimc.name = f"FG edge {code}"
        for o in list(bpy.data.objects):
            if o.name.startswith(tag + " ") and o.type == "MESH":
                for k_, mm in enumerate(o.data.materials):
                    if mm == RIM:
                        o.data.materials[k_] = rimc
        act_melee(rig, yend, rimc)
    if kind == "armour":
        cp, lk = (x - 4.7, y0 - 5.6, 2.0), (x, y0 + 0.1, 1.3)
    elif kind == "bow":                              # bows from the bow side
        cp, lk = (x + 5.6, y0 - 4.4, 1.9), (x, y0 - 0.5, 1.3)
    else:                                            # tools from the weapon side, so their flats show
        cp, lk = (x - 5.9, y0 - 4.1, 2.0), (x, y0 + 0.0, 1.3)
    cam(f"Cam {code}", cp, lk, 38)
    # a dark backdrop behind each take (so no other take shows in its clip), with the take's name on it
    d = Vector((lk[0] - cp[0], lk[1] - cp[1], 0)).normalized(); wc = Vector(lk) + d * 4.2
    ang = math.atan2(d.y, d.x) - math.pi / 2
    wall = mesh_obj(f"FG backdrop {code}", [(-6.0, 0, -0.1), (6.0, 0, -0.1), (6.0, 0, 6.0), (-6.0, 0, 6.0)], [(0, 1, 2, 3)], WALL)
    wall.location = (wc.x, wc.y, 0); wall.rotation_euler = (0, 0, ang)
    lb = bpy.data.curves.new(f"FG label {code}", "FONT"); lb.body = f"{code}  {nm}"; lb.size = 0.2; lb.align_x = "CENTER"
    lo = link(bpy.data.objects.new(f"FG label {code}", lb)); lo.parent = wall; lo.location = (0, -0.02, 3.3); lo.rotation_euler = (R(90), 0, 0)
    lo.data.materials.append(LBL)

# ------------------------------------------------------------------ the lineup: static copies, three tiers, orthographic
LX = -70.0
TIERS = [["A1", "A2", "A3", "A4"], ["S1", "S2", "S3", "X1", "X2", "X3"], ["P1", "P2", "P3", "B1", "B2", "B3"]]
TIER_H, TIER_D = 2.85, 3.0
INFO = {t[0]: t for t in TAKES}
for ti, row in enumerate(TIERS):
    sp = 2.6 if ti == 0 else 1.75
    z0 = 0.6 + ti * TIER_H; y = ti * TIER_D
    box(f"FG lineup step {ti}", (LX - 7.9, y - 1.3, -0.02), (LX + 7.9, y + 1.3, z0), FLOOR)
    for j, code in enumerate(row):
        x = LX + (j - (len(row) - 1) / 2) * sp
        _, kind, look, nm, _d = INFO[code]
        rig = zombie(f"ZL {code}", (x, y, z0))
        rig["root"].rotation_euler = (0, 0, R({"armour": -22, "bow": -62}.get(kind, 62)))      # tools turned to show their flats
        build_gear(f"ZL {code}", rig, code, kind, look, static=True)
        lb = bpy.data.curves.new(f"FG lineup label {code}", "FONT"); lb.body = code; lb.size = 0.26; lb.align_x = "CENTER"
        lo = link(bpy.data.objects.new(f"FG lineup label {code}", lb)); lo.location = (x, y - 1.32, z0 - 0.3); lo.rotation_euler = (R(90), 0, 0)
        lo.data.materials.append(LBL)
lc = cam("Cam lineup", (LX, -40.0, 4.45), (LX, 0.0, 4.45), 50)
lc.data.type = "ORTHO"; lc.data.ortho_scale = 15.6; lc.data.clip_end = 200

# ------------------------------------------------------------------ stage, light, bloom, save
scene.frame_start, scene.frame_end = 1, FRAME_END
bpy.ops.mesh.primitive_plane_add(size=800, location=(140, 0, -0.03))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "FG ground"; g.data.materials.append(FLOOR)
world = bpy.data.worlds.new(SCENE_NAME + " world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.035, 0.04, 0.055, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
scene.world = world
for nm_, e, loc, rot in (("key", 2.6, (0, 0, 0), (R(48), R(0), R(-28))), ("rim", 1.2, (0, 0, 0), (R(-55), R(0), R(160)))):
    sun = link(bpy.data.objects.new(f"FG {nm_}", bpy.data.lights.new(f"FG {nm_}", "SUN")))
    sun.data.energy = e; sun.rotation_euler = rot
    sun.data.color = (1.0, 0.95, 0.88) if nm_ == "key" else (0.6, 0.7, 1.0)
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
    for nm_, val in (("Size", 0.5), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm_ in gl.inputs:
            gl.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
START_CAM = "Cam lineup"
scene.camera = bpy.data.objects[START_CAM]
scene.frame_set(30)
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
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
