# Pass v2.0109: Dread Warren round 4 (Trials; PC Blender chat, 2026-10-19).
# Why: J, coordinator 3's menu: "IMPROVEs + caves". The 12 v2.0108 IMPROVEs (Matron takes W3a2c, W3a3a skipped: the
#   spider-lair hand-over, placement A, cuts her) get 3 new versions each (+1/2/3), and the v2.0106 caves come back:
#   W1a entrance ("the entrances are too obvious or unappealing"), W1b Weave Gallery, W1c Hatchery (room too dark).
# Rules held: "I would prefer you only see the webs once youre in danger" (every cave a CALM / DANGER pair side by
#   side); no columns in big caves; creatures in several poses, all turning; ceiling walking ON HOLD.
# Lights out moments use the lair's yellow construct spider (stand-in) instead of the cut Matron.
# Library below is v2.0108's (with v2.0109 options added); the round-4 section is at the end.
# Builds the whole scene from nothing (globals bpy, np, FOLDER); the renderer saves it as trials/dread_warren_r4.blend.
# Quick test: set DW_ONLY=W1a1,W3c1b2 to build only those takes.
import math
import bpy
import numpy as np

PASS = "v2.0109"
FRAMES = (1, 120)
GAP = 220.0
PX = 1.0 / 16.0

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene
scene.name = "Dread Warren"
scene.frame_start, scene.frame_end = FRAMES
scene.render.fps = 20
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        continue
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
world = bpy.data.worlds.new("DW World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.006, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

# --------------------------------------------------------------- glow (bloom from Render Layers, Standard view)
try:
    tree = bpy.data.node_groups.new("DW Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.6), ("Strength", 0.55), ("Threshold", 0.9)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)


# --------------------------------------------------------------- materials
def _bsdf(m):
    return m.node_tree.nodes.get("Principled BSDF")


def _set(p, name, val):
    if name in p.inputs:
        p.inputs[name].default_value = val


def _pixel_coords(m, scale=16.0):
    """Object coordinates snapped to the 1/16 pixel grid, so procedural textures read as pixel art."""
    N, L = m.node_tree.nodes, m.node_tree.links
    tc = N.new("ShaderNodeTexCoord")
    sn = N.new("ShaderNodeVectorMath"); sn.operation = "SNAP"
    sn.inputs[1].default_value = (1.0 / scale,) * 3
    L.new(tc.outputs["Object"], sn.inputs[0])
    return sn.outputs[0]


def mat(name, base, rough=0.6, metal=0.0, emit=None, es=0.0, alpha=1.0, veins=None, speck=0.0):
    m = bpy.data.materials.new("DW " + name)
    m.use_nodes = True
    p = _bsdf(m)
    N, L = m.node_tree.nodes, m.node_tree.links
    _set(p, "Base Color", (*base, 1)); _set(p, "Roughness", rough); _set(p, "Metallic", metal)
    if emit:
        _set(p, "Emission Color", (*emit, 1)); _set(p, "Emission Strength", es)
    if alpha < 1.0:
        _set(p, "Alpha", alpha)
        try:
            m.surface_render_method = "DITHERED"   # BLENDED writes no depth: see-through at some angles (608)
        except Exception:
            pass
    if speck > 0 or veins:
        co = _pixel_coords(m)
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0 if veins else 6.0
        nz.inputs["Detail"].default_value = 3.0
        L.new(co, nz.inputs["Vector"])
        if speck > 0:
            mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
            mix.inputs["A"].default_value = (*[c * (1 - speck) for c in base], 1)
            mix.inputs["B"].default_value = (*[min(1, c * (1 + speck)) for c in base], 1)
            L.new(nz.outputs["Fac"], mix.inputs["Factor"])
            L.new(mix.outputs["Result"], p.inputs["Base Color"])
        if veins:
            # thin ridges of a second noise = the gold-lightning veining of Dread Stone
            nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 0.35
            nz2.inputs["Detail"].default_value = 4.0; nz2.inputs["Distortion"].default_value = 0.6
            L.new(co, nz2.inputs["Vector"])
            cr = N.new("ShaderNodeValToRGB")
            e = cr.color_ramp.elements
            e[0].position, e[0].color = 0.493, (0, 0, 0, 1)
            e[1].position, e[1].color = 0.5, (1, 1, 1, 1)
            e3 = e.new(0.507); e3.color = (0, 0, 0, 1)
            L.new(nz2.outputs["Fac"], cr.inputs["Fac"])
            mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = veins
            L.new(cr.outputs["Color"], mul.inputs[0])
            _set(p, "Emission Color", (1.0, 0.6, 0.02, 1))
            L.new(mul.outputs[0], p.inputs["Emission Strength"])
    return m


YEL = (1.0, 0.62, 0.0)
M = {
    "stone": mat("dread stone", (0.03, 0.028, 0.032), 0.85, veins=0.45, speck=0.5),
    "grass": mat("dead grass", (0.13, 0.13, 0.12), 0.95, speck=0.4),
    "dirt": mat("dirt", (0.055, 0.042, 0.032), 0.95, speck=0.4),
    "log": mat("dead log", (0.045, 0.04, 0.036), 0.9, speck=0.5),
    "shell": mat("shell", (0.02, 0.017, 0.008), 0.35),
    "plate": mat("plate yellow", (0.16, 0.09, 0.005), 0.3, emit=(0.9, 0.48, 0.0), es=0.22, speck=0.7),
    "eye": mat("eye glow", (1, 0.45, 0.0), 0.2, emit=(1.0, 0.42, 0.0), es=2.0),
    "joint": mat("joint glow", (0.6, 0.3, 0.0), 0.3, emit=(1.0, 0.5, 0.0), es=0.7),
    "under": mat("underside", (0.008, 0.007, 0.005), 0.5),
    "glass": mat("fear glass", (0.6, 0.4, 0.02), 0.1, emit=YEL, es=0.35, alpha=0.38),
    "crack": mat("gold crack", (1, 0.55, 0.05), 0.3, emit=(1.0, 0.5, 0.02), es=1.5),
    "gold": mat("polished gold", (1.0, 0.68, 0.22), 0.22, metal=1.0),
    "silk": mat("hard-light silk", (0.9, 0.55, 0.02), 0.4, emit=(1.0, 0.6, 0.03), es=0.75, alpha=0.85),
    "pane": mat("web pane", (0.8, 0.55, 0.02), 0.3, emit=(1.0, 0.65, 0.04), es=0.25, alpha=0.16),
    "ghost": mat("phantom glass", (0.5, 0.35, 0.05), 0.2, emit=YEL, es=0.6, alpha=0.3),
    "static": mat("yellow static", (1, 0.6, 0.05), 0.5, emit=(1.0, 0.6, 0.04), es=0.9, alpha=0.6),
    "suit": mat("player suit", (0.03, 0.035, 0.03), 0.6),
    "skin": mat("player skin", (0.55, 0.38, 0.27), 0.7),
    "ring": mat("ring green", (0.05, 1.0, 0.15), 0.2, emit=(0.05, 1.0, 0.15), es=1.4),
    "flare": mat("will flare", (0.02, 0.6, 0.1), 0.2, emit=(0.03, 1.0, 0.18), es=0.45, alpha=0.14),
    "ash": mat("green ash", (0.03, 0.7, 0.1), 0.5, emit=(0.03, 1.0, 0.12), es=0.9),
    "red": mat("red rage", (0.9, 0.05, 0.04), 0.4, emit=(1.0, 0.04, 0.03), es=1.4),
    "blue": mat("blue hope", (0.1, 0.4, 1.0), 0.3, emit=(0.08, 0.4, 1.0), es=1.3),
    "ylring": mat("yellow ring", (1.0, 0.7, 0.05), 0.3, emit=(1.0, 0.68, 0.04), es=1.4),
    "crystal": mat("heart crystal", (1.0, 0.6, 0.02), 0.1, emit=(1.0, 0.58, 0.02), es=1.4, alpha=0.8),
    "cocoon": mat("cocoon silk", (0.07, 0.055, 0.03), 0.8, emit=(0.9, 0.5, 0.0), es=0.04, speck=0.8),
}


# --------------------------------------------------------------- voxel mesher (only exposed faces)
def grid_mesh(name, G, labels, s, loc=(0, 0, 0), center=True, trans=()):
    """G: int label grid. labels: {label: material key}. A face is drawn where the neighbour is empty, or is a
    different, translucent label (so glass shows what is inside it)."""
    keys = sorted(labels)
    lut = np.zeros(max(keys) + 1, dtype=np.int32)
    for i, k in enumerate(keys):
        lut[k] = i
    tr = np.zeros(max(keys) + 1, dtype=bool)
    for k in trans:
        if k < len(tr):
            tr[k] = True
    P = np.pad(G, 1)
    verts, faces, mids = [], [], []
    nv = 0
    for ax in range(3):
        u, v = (ax + 1) % 3, (ax + 2) % 3
        for sgn in (1, -1):
            sl = [slice(1, -1)] * 3
            sl[ax] = slice(2, None) if sgn > 0 else slice(0, -2)
            nb = P[tuple(sl)]
            vis = (G > 0) & ((nb == 0) | ((nb != G) & tr[nb]))
            idx = np.argwhere(vis)
            if not len(idx):
                continue
            n = len(idx)
            base = idx.astype(np.float64)
            if sgn > 0:
                base[:, ax] += 1
            c = np.zeros((n, 4, 3))
            quad = [(0, 0), (1, 0), (1, 1), (0, 1)] if sgn > 0 else [(0, 0), (0, 1), (1, 1), (1, 0)]
            for qi, (du, dv) in enumerate(quad):
                c[:, qi] = base
                c[:, qi, u] += du
                c[:, qi, v] += dv
            verts.append(c.reshape(-1, 3))
            faces.append(np.arange(nv, nv + 4 * n).reshape(-1, 4))
            mids.append(lut[G[tuple(idx.T)]])
            nv += 4 * n
    me = bpy.data.meshes.new(name)
    if verts:
        V = np.concatenate(verts) * s
        if center:
            sh = np.array(G.shape, dtype=np.float64) * s
            V -= np.array([sh[0] / 2, sh[1] / 2, 0.0])
        me.from_pydata(V.tolist(), [], np.concatenate(faces).tolist())
        for k in keys:
            me.materials.append(M[labels[k]])
        me.polygons.foreach_set("material_index", np.concatenate(mids).astype(np.int32))
        me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    scene.collection.objects.link(ob)
    return ob


def _box(G, a, b):
    lo = np.maximum(np.floor(np.minimum(a, b)).astype(int), 0)
    hi = np.minimum(np.ceil(np.maximum(a, b)).astype(int) + 1, G.shape)
    return lo, hi


def _pts(lo, hi):
    g = np.mgrid[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].astype(np.float64) + 0.5
    return g


def capsule(G, a, b, r, lab, only_empty=False):
    a, b = np.asarray(a, float), np.asarray(b, float)
    lo, hi = _box(G, np.minimum(a, b) - r - 1, np.maximum(a, b) + r + 1)
    if np.any(hi <= lo):
        return
    p = _pts(lo, hi)
    ab = b - a
    t = np.clip(((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1] + (p[2] - a[2]) * ab[2]) / max(ab @ ab, 1e-9), 0, 1)
    d2 = sum((p[i] - (a[i] + t * ab[i])) ** 2 for i in range(3))
    m = d2 <= r * r
    sub = G[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    if only_empty:
        m &= sub == 0
    sub[m] = lab


def ellip(G, c, rad, lab, shell=None, only_empty=False):
    c, rad = np.asarray(c, float), np.asarray(rad, float)
    lo, hi = _box(G, c - rad - 1, c + rad + 1)
    if np.any(hi <= lo):
        return
    p = _pts(lo, hi)
    q = sum(((p[i] - c[i]) / rad[i]) ** 2 for i in range(3))
    m = q <= 1.0
    if shell is not None:
        inner = sum(((p[i] - c[i]) / max(rad[i] - shell, 0.5)) ** 2 for i in range(3))
        m &= inner > 1.0
    sub = G[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    if only_empty:
        m &= sub == 0
    sub[m] = lab


def surface_mask(G):
    P = np.pad(G > 0, 1)
    inside = np.ones_like(G, dtype=bool)
    for ax in range(3):
        for sh in (2, 0):
            sl = [slice(1, -1)] * 3
            sl[ax] = slice(sh, sh + G.shape[ax]) if sh else slice(0, G.shape[ax])
            inside &= P[tuple(sl)]
    return (G > 0) & ~inside


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    scene.collection.objects.link(e)
    return e


def parent(ch, par):
    ch.parent = par


def spin(ob):
    """Turntable without keyframes: a simple driver on Z rotation, one turn per 120 frames."""
    d = ob.driver_add("rotation_euler", 2).driver
    d.type = "SCRIPTED"
    d.expression = "frame*0.05236"


# --------------------------------------------------------------- props
def player(name, loc, rot_z=0.0, ring="ring", raise_arm=True):
    """A Minecraft-sized player (1.8 blocks) in a dark suit, the ring arm raised; the ring is the lamp."""
    root = empty(name, loc); root.rotation_euler[2] = rot_z
    parts = [("legL", (-2, 0, 0), (4, 4, 12), "suit"), ("legR", (2, 0, 0), (4, 4, 12), "suit"),
             ("body", (0, 0, 12), (8, 4, 12), "suit"), ("head", (0, 0, 24), (8, 8, 8), "skin"),
             ("armL", (-6, 0, 12), (4, 4, 12), "suit")]
    for nm, (x, y, z), (sx, sy, sz), mk in parts:
        G = np.ones((sx, sy, sz), dtype=np.int16)
        o = grid_mesh(f"{name} {nm}", G, {1: mk}, PX, loc=(x * PX, y * PX, z * PX))
        parent(o, root)
    # ring arm: a pivot at the shoulder
    sh = empty(f"{name} shoulder", (6 * PX, 0, 22 * PX)); parent(sh, root)
    sh.rotation_euler[0] = math.radians(-150 if raise_arm else -80)
    G = np.ones((4, 4, 12), dtype=np.int16); G[:, :, :3] = 2
    G[1:3, 1:3, 0] = 3
    o = grid_mesh(f"{name} armR", G, {1: "suit", 2: "skin", 3: ring}, PX, loc=(0, 0, -12 * PX))
    o.rotation_euler[0] = math.pi
    o.location = (0, 0, 0)
    parent(o, sh)
    o.location = (0, 0, 0)
    G2 = np.zeros((6, 6, 3), dtype=np.int16); G2[:, :, 1] = 1; G2[1:5, 1:5, 1] = 0; G2[2:4, 2:4, :] = 1
    rg = grid_mesh(f"{name} ring", G2, {1: ring}, PX, loc=(0, 0, 12.3 * PX)); parent(rg, sh)
    hand = empty(f"{name} hand", (0, 0, 13 * PX)); parent(hand, sh)
    return root, hand


def light(name, loc, color, energy, radius=0.2, cutoff=30.0, kind="POINT", size=None, rot=None, par=None):
    ld = bpy.data.lights.new(name, kind)
    ld.color = color; ld.energy = energy
    if kind == "POINT":
        ld.shadow_soft_size = radius
    if kind == "AREA" and size:
        ld.size = size
    try:
        ld.use_custom_distance = True; ld.cutoff_distance = cutoff
    except Exception:
        pass
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    scene.collection.objects.link(ob)
    if par:
        ob.parent = par
        ob.location = loc
    return ob


def ring_light(name, hand, color=(0.08, 1.0, 0.18), energy=900.0):
    return light(name, (0, 0, 0.15), color, energy, radius=0.08, cutoff=16, par=hand)


def camera(name, loc, look, lens=30.0):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.05; cd.clip_end = 300
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    scene.collection.objects.link(ob)
    d = np.asarray(look, float) - np.asarray(loc, float)
    ob.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return ob


class Strands:
    """Hard-light silk: thin square strands (1 px, 2 px for cables) between points, one mesh per scene."""

    def __init__(self, name):
        self.name, self.V, self.F = name, [], []

    def seg(self, a, b, w=PX):
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = b - a
        n = np.linalg.norm(d)
        if n < 1e-6:
            return
        d /= n
        up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(d, up); u /= np.linalg.norm(u); v = np.cross(d, u)
        h = w / 2
        base = len(self.V)
        for p in (a, b):
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                self.V.append(p + u * su * h + v * sv * h)
        for i in range(4):
            j = (i + 1) % 4
            self.F.append((base + i, base + j, base + 4 + j, base + 4 + i))

    def poly(self, pts, w=PX):
        for a, b in zip(pts[:-1], pts[1:]):
            self.seg(a, b, w)

    def web(self, c, nrm, radius, spokes=10, rings=6, rng=None, w=PX, sag=0.0):
        c = np.asarray(c, float); nrm = np.asarray(nrm, float); nrm /= np.linalg.norm(nrm)
        up = np.array([0, 0, 1.0]) if abs(nrm[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(nrm, up); u /= np.linalg.norm(u); v = np.cross(nrm, u)
        rng = rng or np.random.default_rng(3)
        angs = np.sort(np.linspace(0, 2 * math.pi, spokes, endpoint=False) + rng.uniform(-0.15, 0.15, spokes))
        ends = []
        for a in angs:
            r = radius * rng.uniform(0.85, 1.1)
            e = c + (u * math.cos(a) + v * math.sin(a)) * r
            self.seg(c, e, w * 1.5); ends.append((a, r))
        for k in range(1, rings + 1):
            f = k / (rings + 0.6)
            pts = []
            for a, r in ends + [ends[0]]:
                pts.append(c + (u * math.cos(a) + v * math.sin(a)) * r * f * rng.uniform(0.96, 1.04)
                           - nrm * sag * f)
            self.poly(pts, w)

    def build(self, mk="silk", loc=(0, 0, 0)):
        me = bpy.data.meshes.new(self.name)
        if self.V:
            me.from_pydata(np.array(self.V).tolist(), [], self.F)
            me.materials.append(M[mk])
        ob = bpy.data.objects.new(self.name, me)
        ob.location = loc
        scene.collection.objects.link(ob)
        return ob


def blocks(name, G, loc, labels=None):
    return grid_mesh(name, G, labels or {1: "stone"}, 1.0, loc=loc, center=False)


def cave_box(nx, ny, nz, rough=0.35, seed=0):
    """A hollow room of Dread Stone: walls 2-4 blocks thick with lumpy inner faces."""
    rng = np.random.default_rng(seed)
    G = np.ones((nx, ny, nz), dtype=np.int16)
    xx, yy, zz = np.mgrid[0:nx, 0:ny, 0:nz]
    n = rng.normal(size=(nx, ny, nz))
    for _ in range(2):
        n = (n + np.roll(n, 1, 0) + np.roll(n, -1, 0) + np.roll(n, 1, 1) + np.roll(n, -1, 1) +
             np.roll(n, 1, 2) + np.roll(n, -1, 2)) / 7
    return G, xx, yy, zz, n


TAKES = []


def add_take(code, name, cam, kind, facts):
    TAKES.append((code, name, cam.name, kind, facts))



# =============================================================== v2.0107: new pieces
from mathutils import Matrix, Vector

M["stone"] = mat("dread stone r2", (0.035, 0.032, 0.036), 0.85, veins=0.22, speck=0.5)
CUR = {}      # options for the spider being built (set by build_row)
MOPT = {}     # options for the Matron being built
M.update({
    "plate_dim": mat("plate dim", (0.12, 0.07, 0.005), 0.3, emit=(0.9, 0.45, 0.0), es=0.08, speck=0.7),
    "joint_dim": mat("joint dim", (0.5, 0.25, 0.0), 0.3, emit=(1.0, 0.48, 0.0), es=0.35),
    "glass_clear": mat("fear glass clear", (0.6, 0.4, 0.02), 0.05, emit=(1.0, 0.6, 0.0), es=0.15, alpha=0.2),
    "glass_dim": mat("fear glass dim", (0.5, 0.33, 0.02), 0.1, emit=(1.0, 0.55, 0.0), es=0.12, alpha=0.32),
    "ghost_faint": mat("phantom fill", (0.5, 0.35, 0.05), 0.2, emit=(1.0, 0.6, 0.05), es=0.2, alpha=0.12),
    "deep": mat("deep stone", (0.012, 0.012, 0.016), 0.9, veins=0.25, speck=0.6),
    "silkblock": mat("silk-lined stone", (0.1, 0.07, 0.02), 0.7, emit=(1.0, 0.55, 0.02), es=0.07, speck=0.8),
    "veinblock": mat("vein stone", (0.08, 0.04, 0.0), 0.6, emit=(1.0, 0.5, 0.0), es=0.5, speck=0.9),
    "bone": mat("old bone", (0.32, 0.29, 0.22), 0.8, speck=0.5),
    "wire": mat("phantom wire", (1.0, 0.55, 0.02), 0.4, emit=(1.0, 0.55, 0.02), es=1.0),
    "greencrack": mat("green crack", (0.05, 1.0, 0.15), 0.3, emit=(0.04, 1.0, 0.16), es=1.3),
})
GLASS_LAB = {6: "glass"}
SP = {   # voxels at 1/16 block
    "broodling": dict(ceph=(3, 3.5, 2.5), abd=(4, 5, 3.5), reach=9, knee=5, zb=4, lr=(1.0, 0.8, 0.6), eyes=1.2),
    "hunter": dict(ceph=(5, 6, 4), abd=(7.5, 9, 6), reach=18, knee=9, zb=9, lr=(1.6, 1.2, 0.9), eyes=1.0),
    "weaver": dict(ceph=(4, 5, 3), abd=(5, 11, 5), reach=27, knee=15, zb=11, lr=(0.9, 0.75, 0.6), eyes=0.9),
    "phantom": dict(ceph=(4, 5, 3.5), abd=(6, 7.5, 5), reach=14, knee=8, zb=8, lr=(1.2, 1.0, 0.8), eyes=1.0),
}
LEG_ANG = (32, 68, 108, 146)     # degrees from forward (+y), per side


def octa(G, c, rad, lab, only_empty=False):
    """A faceted shard: an L1-ball, so the faces come out as flat diamond facets."""
    c, rad = np.asarray(c, float), np.asarray(rad, float)
    lo, hi = _box(G, c - rad - 1, c + rad + 1)
    if np.any(hi <= lo):
        return
    p = _pts(lo, hi)
    q = sum(np.abs(p[i] - c[i]) / rad[i] for i in range(3))
    m = q <= 1.0
    sub = G[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    if only_empty:
        m &= sub == 0
    sub[m] = lab


def orient(ob, belly, head):
    """Turn a creature so its belly faces `belly` and its head points along `head` (world directions)."""
    z = -np.asarray(belly, float); z /= np.linalg.norm(z)
    y = np.asarray(head, float); y = y - z * (y @ z); y /= np.linalg.norm(y)
    x = np.cross(y, z)
    ob.rotation_euler = Matrix(((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2]))).to_euler()


def ground(ob, z0=0.0):
    """Drop an object so its lowest point sits at z0 (in its parent's space; parents only spin about Z)."""
    bpy.context.view_layer.update()
    zs = [(ob.matrix_world @ Vector(c)).z for c in ob.bound_box]
    pz = ob.parent.matrix_world.translation.z if ob.parent else 0.0
    ob.location.z += (z0 + pz) - min(zs)


def adopt(root, before):
    for ob in scene.objects:
        if ob.name not in before and ob.parent is None and ob is not root and ob.type != "CAMERA":
            ob.parent = root


def smooth_noise(shape, rng, it=3):
    n = rng.normal(size=shape)
    for _ in range(it):
        acc = n.copy()
        for ax in range(len(shape)):
            acc += np.roll(n, 1, ax) + np.roll(n, -1, ax)
        n = acc / (1 + 2 * len(shape))
    return n / (n.std() + 1e-9)


def dilate(mask):
    out = mask.copy()
    for ax in range(3):
        out |= np.roll(mask, 1, ax) | np.roll(mask, -1, ax)
    return out


# --------------------------------------------------------------- spiders, round 2: three builds and five poses
STYLE_NOTE = {
    "plate": "Plate: a black core under separate yellow hard-light scale bands with dark gaps, small glowing joints",
    "shard": "Shard: faceted see-through fear glass round a dark core, shard spines on the back, spiked knees",
    "bristle": "Bristle: a dark furred body bristling with yellow spines, banded legs, a glowing eye mark on the abdomen",
    "shell": "Shell: a hollow see-through spider of light, sharper eyes, static clinging close",
    "wire": "Wire: only its edges, drawn in glowing lines, like a construct outline",
    "split": "Split: the head solid, the abdomen coming apart into a cloud of yellow static (mid-blink)",
}


def spider2(name, kind, style="plate", pose="stand", seed=1):
    """Fear-construct spider. pose: stand (walking, alternate feet lifted), wall, drop, rear (front legs up, fangs
    out), death (legs curled; the caller flips it onto its back). Returns (object, spinneret in object space)."""
    P = SP[kind]
    rng = np.random.default_rng(seed)
    cx_, cy_, cz_ = P["ceph"]; ax_, ay_, az_ = P["abd"]
    R, K = P["reach"], P["knee"]
    lift = 8 if pose == "death" else 0
    W = int(2 * (R + ay_ * 2 + 12))
    H = int(P["zb"] + K * 2.2 + az_ + 18 + lift)
    G = np.zeros((W, W, H), dtype=np.int16)
    ox, oy = W / 2, W / 2 + ay_ * 0.6
    zb = P["zb"] + lift + (2 if pose == "rear" else 0)
    ceph = np.array([ox, oy + cy_ * 0.6, zb + 1 + (2 if pose == "rear" else 0)])
    abd = np.array([ox, oy - cy_ * 0.4 - ay_ * 0.85, zb + az_ * 0.55])
    zz = np.arange(H)[None, None, :] + 0.5
    yy = np.arange(W)[None, :, None] + 0.5
    xx = np.arange(W)[:, None, None] + 0.5
    base_style = "plate" if kind == "phantom" else style
    opt = dict(CUR)
    if base_style == "shard":
        octa(G, ceph, np.array(P["ceph"]) * 1.25, 6)
        octa(G, abd, np.array(P["abd"]) * 1.2, 6)
        capsule(G, ceph, abd, min(cx_, ax_) * 0.5, 6)
        ellip(G, ceph, np.array(P["ceph"]) * 0.62, 1)
        ellip(G, abd, np.array(P["abd"]) * 0.6, 1)
        capsule(G, ceph, abd, min(cx_, ax_) * 0.3, 1)
        G[(G == 6) & ~surface_mask(G)] = 0
        ellip(G, abd + np.array([0, 0, az_ * 0.25]), np.array(P["abd"]) * 0.22, 4)
        nsp = opt.get("spines", 5)
        for k in range(nsp):      # shard spines along the back
            if nsp <= 5:
                b = abd + np.array([0, ay_ * (0.5 - 0.28 * k), az_ * 0.7])
                tipv = np.array([rng.uniform(-1, 1), -2.0, 3.0 + 1.2 * (k % 2)])
            else:                 # a crystal cluster bristling all over the back
                a_ = rng.uniform(0, 2 * math.pi); f_ = rng.uniform(-0.6, 0.7)
                b = abd + np.array([math.cos(a_) * ax_ * 0.55, ay_ * f_, az_ * 0.6 + abs(math.sin(a_)) * 0.5])
                tipv = np.array([math.cos(a_) * 1.6, rng.uniform(-2.2, 0.5), rng.uniform(2.0, 4.2)])
            capsule(G, b, b + tipv, 0.7 + 0.15 * (k % 2), 2)
        if opt.get("eggshell"):   # pieces of its own egg still stuck to its back
            for k in range(4):
                a_ = k / 4 * 2 * math.pi + 0.4
                c_ = abd + np.array([math.cos(a_) * ax_ * 0.7, math.sin(a_) * ay_ * 0.55, az_ * 1.05])
                octa(G, c_, (2.4, 2.2, 0.8), 6, only_empty=True)
    else:
        ellip(G, ceph, P["ceph"], 1)
        ellip(G, abd, P["abd"], 1)
        capsule(G, ceph, abd, min(cx_, ax_) * 0.55, 1)
        surf = surface_mask(G)
        up = surf & (zz > zb + 0.5)
        G[surf & (zz < zb - 0.5)] = 5
        if base_style == "plate":
            band = (np.floor((yy - abd[1]) / opt.get("band", 2.5)).astype(int) % 2 == 0) | (yy > abd[1] + ay_ * 0.95)
            G[up & band & ~((np.abs(xx - ox) < 0.8) & (yy < abd[1] + ay_ * 0.9))] = 2
            if opt.get("twotone"):  # the gaps between bands filled with gold-lit plates
                G[up & ~band & (yy < abd[1] + ay_ * 0.95) & (G == 1)] = 11
            if opt.get("glass_abd"):  # a see-through abdomen with a glowing yolk inside
                ellip(G, abd, P["abd"], 6)
                G[(G == 6) & ~surface_mask(G)] = 0
                ellip(G, abd + np.array([0, 0, -0.3]), np.array(P["abd"]) * 0.45, 4)
        else:                     # bristle
            pts = np.argwhere(up)
            if opt.get("mane"):   # a mane of spines round the waist only
                waist = (ceph + abd) / 2 + np.array([0, opt.get("mane_y", 0.0), 0])
                pts = pts[np.linalg.norm(pts + 0.5 - waist, axis=1) < max(cx_, ax_) * opt.get("mane_r", 1.1)]
            nb = opt.get("bristles", 70 if kind != "broodling" else 30)
            sweep = np.array([0, -opt.get("sweep", 0.8), opt.get("lift", 0.0)])
            for k in rng.choice(len(pts), size=min(len(pts), nb), replace=False):
                p = pts[k] + 0.5
                cc = abd if np.linalg.norm(p - abd) < np.linalg.norm(p - ceph) + 2 else ceph
                d = p - cc; d /= np.linalg.norm(d) + 1e-9
                tip_ = p + d * rng.uniform(*opt.get("blen", (1.6, 3.4))) + sweep
                if opt.get("tip_lab"):   # the last third of each spine in a second colour
                    mid_ = p + (tip_ - p) * 0.62
                    capsule(G, p, mid_, opt.get("brad", 0.45), 2, only_empty=True)
                    capsule(G, mid_, tip_, opt.get("brad", 0.45) * 0.9, opt["tip_lab"], only_empty=True)
                else:
                    capsule(G, p, tip_, opt.get("brad", 0.45), 2, only_empty=True)
            top = abd + np.array([0, 0, az_ * 0.95])
            ring = up & (np.hypot(xx - top[0], (yy - top[1]) * 0.8) > 1.8) & (np.hypot(xx - top[0], (yy - top[1]) * 0.8) < 2.9)
            G[ring] = 4
            ellip(G, top, (1.0, 1.4, 0.9), 3)
    e = P["eyes"] * (1.25 if base_style == "shard" else 1.0)
    front = ceph + np.array([0, cy_ * 0.75, cz_ * 0.45])
    for dx, dz, rr in ((-1.1, 0.4, 1.0), (1.1, 0.4, 1.0), (-2.4, 0.9, 0.6), (2.4, 0.9, 0.6),
                       (-0.6, 1.6, 0.55), (0.6, 1.6, 0.55), (-2.9, -0.4, 0.5), (2.9, -0.4, 0.5)):
        ellip(G, front + np.array([dx * e, -abs(dx) * 0.3, dz * e]), (rr * e + 0.2,) * 3, 3)
    for sx in (-1, 1):
        a = ceph + np.array([sx * 1.4, cy_ * 0.85, -cz_ * 0.3])
        spread = 1.6 if pose == "rear" else 0.3
        b = a + np.array([sx * spread, 1.2 + (1.5 if pose == "rear" else 0), -cz_ * 0.9])
        capsule(G, a, b, 1.0 * e + 0.2, 1)
        capsule(G, b, b + np.array([-sx * 0.4 * (pose == "rear"), -0.4, -1.2]), 0.6, 4)
        pa = ceph + np.array([sx * cx_ * 0.6, cy_ * 0.8, -0.5])
        pk = pa + np.array([sx * 2.5, 3.0, 2.0 + (2 if pose == "rear" else 0)])
        capsule(G, pa, pk, 0.8, 1); capsule(G, pk, pk + np.array([sx * 0.8, 2.6, -2.6]), 0.7, 1)
    r1, r2, r3 = P["lr"]
    for sx in (-1, 1):
        for li, ang in enumerate(LEG_ANG):
            a = math.radians(ang + rng.uniform(-5, 5))
            d = np.array([sx * math.sin(a), math.cos(a), 0.0])
            hip = ceph + d * np.array([cx_ * 0.8, cy_ * 0.5, 0]) + np.array([0, 0, -0.5])
            reach = R * (0.9 + 0.12 * (li in (0, 3))) * rng.uniform(0.95, 1.05)
            up = np.array([0, 0, 1.0])
            if pose == "drop":
                d = d * 0.1 + np.array([sx * math.sin(a) * 0.75, 0.55 + 0.25 * math.cos(a), 0.0]) * 0.9
                knee = hip + d * reach * 0.42 + up * K * 0.73
                ank = hip + d * reach * 0.82 + up * (K * 0.35 - zb * 0.54)
                foot = hip + d * reach + up * (-hip[2] + 0.5 - zb * 0.36)
            elif pose == "rear" and li < 2:
                knee = hip + d * reach * 0.3 + up * K * 1.25
                ank = hip + d * reach * 0.45 + np.array([0, 2.5 + li, 0]) + up * K * 1.95
                foot = ank + np.array([sx * 1.0, 2.0, -K * 0.35])
            elif pose == "death":
                knee = hip + d * reach * 0.3 - up * 2.0
                ank = hip + d * reach * 0.16 - up * (zb * 0.55)
                foot = hip + d * reach * 0.02 - up * (zb * 0.75)
            else:
                walk = pose == "stand" and (li + (sx > 0)) % 2 == 0
                knee = hip + d * reach * 0.42 + up * K * (1.12 if walk else 1.0)
                ank = hip + d * reach * 0.82 + up * K * 0.35 + (np.array([0, 1.5, K * 0.25]) if walk else 0)
                foot = hip + d * reach + up * (-hip[2] + 0.5) + (np.array([0, 2.0, K * 0.4]) if walk else 0)
            foot[2] = max(foot[2], 0.5)
            ank[2] = max(ank[2], 0.5)
            if base_style == "shard":
                capsule(G, hip, knee, r1 * 0.9, 2); capsule(G, knee, ank, r2 * 0.85, 1); capsule(G, ank, foot, r3 * 0.8, 1)
                capsule(G, knee, knee + up * 2.5 + d * 1.5, r1 * 0.55, 6)
                capsule(G, foot + up * 0.8, foot, r3 * 0.7, 4)
            elif base_style == "bristle":
                for a0, b0, rr in ((hip, knee, r1), (knee, ank, r2), (ank, foot, r3)):
                    capsule(G, a0, b0, rr, 1)
                    n = max(2, int(np.linalg.norm(b0 - a0) / 2.2))
                    for k in range(0, n, 2):
                        capsule(G, a0 + (b0 - a0) * (k / n), a0 + (b0 - a0) * ((k + 1) / n), rr + 0.12, 2)
                ellip(G, knee, (r1 + 0.35,) * 3, 4)
                if opt.get("leg_tufts"):  # tufts of spines on the legs
                    for k in range(4):
                        q_ = hip + (knee - hip) * rng.uniform(0.2, 1.0)
                        capsule(G, q_, q_ + (up * 2.2 + d * 1.0) * rng.uniform(0.8, 1.5), 0.45, 2, only_empty=True)
            else:
                capsule(G, hip, knee, r1, 2); capsule(G, knee, ank, r2, 1); capsule(G, ank, foot, r3, 1)
                ellip(G, knee, (r1 + 0.35,) * 3, 4); ellip(G, ank, (r2 + 0.25,) * 3, 4)
                capsule(G, foot + up * 0.8, foot, r3 * 0.8, 4)
    sp = abd + np.array([0, -ay_ * 0.95, -az_ * 0.2])
    capsule(G, sp, sp + np.array([0, -1.6, -0.6]), 1.1, 4)
    labels = {1: "shell", 2: "plate", 3: "eye", 4: "joint", 5: "under", 6: "glass"}
    trans = (6,)
    if kind == "phantom":
        def edges_of(solid):
            Pd = np.pad(solid, 1)
            axes_open = np.zeros(G.shape, dtype=np.int8)
            for ax in range(3):
                lo = [slice(1, -1)] * 3; hi = [slice(1, -1)] * 3
                lo[ax] = slice(0, -2); hi[ax] = slice(2, None)
                axes_open += (~Pd[tuple(lo)] | ~Pd[tuple(hi)]).astype(np.int8)
            return solid & (axes_open >= 2)
        if style.startswith("shell"):
            G[(G == 1) | (G == 2) | (G == 5)] = 6
            G[(G == 6) & ~surface_mask(G)] = 0
            labels = {6: "ghost", 3: "eye", 4: "joint"}
            if style == "shell_edge":       # its outline drawn in light over the see-through body
                G[edges_of(G > 0) & (G == 6)] = 8
                labels[8] = "wire"
            elif style == "shell_ghost":    # a dark spider shadow seen inside the light
                ellip(G, ceph, np.array(P["ceph"]) * 0.55, 1, only_empty=True)
                ellip(G, abd, np.array(P["abd"]) * 0.55, 1, only_empty=True)
                labels[1] = "shell"
            elif style == "shell_scan":     # scanlines: rows of the shell missing, like a bad signal
                G[(G == 6) & ((np.floor(zz).astype(int) % 3) == 0) & (xx > -1) & (yy > -1)] = 0
        elif style == "wire_x":            # v2.0109: the wire look built from options in CUR
            solid = G > 0
            edge = edges_of(solid)
            for _ in range(opt.get("thick", 0)):
                edge = dilate(edge) & dilate(solid)
            if opt.get("dash"):
                per, on = opt["dash"]
                ph = (xx + yy + zz) if opt.get("dash_axis") != "z" else zz + 0 * xx + 0 * yy
                edge &= (np.floor(ph).astype(int) % per) < on
            shell_ = surface_mask(G)
            keep_eye = G == 3
            G[:] = 0
            fill_ = opt.get("fill")
            if fill_:
                fm = shell_ & ~edge
                if opt.get("fill_part") == "abd":
                    fm &= (yy < (ceph[1] + abd[1]) / 2 + 0 * xx + 0 * zz)
                G[fm] = 6
            if opt.get("core"):           # a dark spider body seen through the light
                ellip(G, ceph, np.array(P["ceph"]) * opt["core"], 1, only_empty=True)
                ellip(G, abd, np.array(P["abd"]) * opt["core"], 1, only_empty=True)
                capsule(G, ceph, abd, min(cx_, ax_) * 0.3, 1, only_empty=True)
            G[edge] = 8
            if opt.get("bands"):          # the outline in alternating bands of yellow and gold light
                G[edge & ((np.floor(zz / opt["bands"] + 0 * xx + 0 * yy).astype(int) % 2) == 1)] = 11
            G[keep_eye] = 3
            labels = {8: "wire", 3: "eye", 6: fill_ or "ghost_faint", 1: "shell", 11: "gold"}
            if opt.get("wire_mat"):
                labels[8] = opt["wire_mat"]
            if opt.get("eye_big"):
                for q in np.argwhere(keep_eye):
                    ellip(G, q + 0.5, (0.9, 0.9, 0.9), 3, only_empty=True)
            trans = (6,)
        elif style.startswith("wire"):
            solid = G > 0
            edge = edges_of(solid)
            if style == "wire_thick":
                edge = dilate(edge) & dilate(solid)
            elif style == "wire_dash":
                edge &= (np.floor(xx + yy + zz).astype(int) % 4) < 2
            fill = surface_mask(G) & ~edge
            keep_eye = G == 3
            G[:] = 0
            if style == "wire_fill":
                G[fill] = 6
            G[edge] = 8
            G[keep_eye] = 3
            labels = {8: "wire", 3: "eye", 6: "ghost_faint"}
            trans = (6,)
        else:   # split: the abdomen half bursts into static
            cut = (ceph[1] + abd[1]) / 2
            back = np.argwhere((G > 0) & (G != 3) & (yy < cut + 0 * xx + 0 * zz))
            G[(G > 0) & (G != 3) & (yy < cut + 0 * xx + 0 * zz)] = 0
            keep = back[rng.random(len(back)) < 0.22].astype(float)
            off = (keep - np.array([ox, cut, zb])) * rng.uniform(0.15, 0.7, size=(len(keep), 1))
            q = np.round(keep + off + rng.normal(size=keep.shape) * 1.2).astype(int)
            ok = np.all((q >= 0) & (q < np.array(G.shape)), axis=1)
            q = q[ok]
            G[tuple(q.T)] = 9
            labels = {1: "shell", 2: "plate", 3: "eye", 4: "joint", 5: "under", 9: "static"}
            trans = ()
    if opt.get("ridge"):          # v2.0109: a spiked ridge down the back (the lair's dread-armour construct)
        for k in range(opt["ridge"]):
            f_ = k / max(opt["ridge"] - 1, 1)
            b = ceph + (abd - ceph) * (f_ * 1.25) + np.array([0, 0, (cz_ if f_ < 0.35 else az_) * 0.85])
            capsule(G, b, b + np.array([0, -1.2, 2.2 + 1.2 * math.sin(f_ * math.pi)]), 0.6, 11, only_empty=True)
    if opt.get("gcracks"):        # v2.0109: green will-light cracks running through the shell
        shell_cells = np.argwhere(surface_mask(G) & (G != 3))
        if len(shell_cells):
            sset = surface_mask(G)
            for k in range(opt["gcracks"]):
                q = shell_cells[rng.integers(len(shell_cells))].astype(float)
                dv = rng.normal(size=3); dv /= np.linalg.norm(dv)
                for step in range(opt.get("glen", 40)):
                    qi = np.round(q).astype(int)
                    if np.all(qi >= 0) and np.all(qi < G.shape) and sset[tuple(qi)]:
                        G[tuple(qi)] = 10
                    dv += rng.normal(size=3) * 0.45; dv /= np.linalg.norm(dv)
                    q = shell_cells[np.argmin(np.linalg.norm(shell_cells - (q + dv), axis=1))].astype(float)
        labels[10] = "greencrack"
    labels[11] = "gold"
    if opt.get("dim"):
        labels[2], labels[4] = "plate_dim", "joint_dim"
    if opt.get("clear") and labels.get(6) == "glass":
        labels[6] = "glass_clear"
    present = {k: v for k, v in labels.items() if np.any(G == k)}
    ob = grid_mesh(name, G, present, PX, trans=trans)
    spl = np.array([(sp[0] - W / 2) * PX, (sp[1] - W / 2) * PX, sp[2] * PX])
    return ob, spl


SPAN = {"broodling": 0.75, "hunter": 2.6, "weaver": 3.7, "phantom": 2.1}


def pose_spider(name, kind, style, pose, seed, wall=None):
    """Build one pose standing at the origin: returns the list of objects (spider, thread, wall)."""
    ob, spl = spider2(name, kind, style, pose, seed)
    out = [ob]
    s = SPAN[kind]
    if pose == "wall":
        orient(ob, belly=(0, 1, 0), head=(0, 0, 1))
        ob.location = (0, 0, 0)
        bpy.context.view_layer.update()
        ys = [(ob.matrix_world @ Vector(c)).y for c in ob.bound_box]
        zs = [(ob.matrix_world @ Vector(c)).z for c in ob.bound_box]
        ob.location = (0, -max(ys), 0.3 - min(zs) + 0.15 * s)
        n = int(s * 1.6 * 8) + 2; hgt = int(s * 1.8 * 8) + 3
        Wg = np.zeros((n, 4, hgt), dtype=np.int16)
        rng = np.random.default_rng(seed)
        bump = smooth_noise((n, hgt), rng, 2)
        for i in range(n):
            for k in range(hgt):
                Wg[i, :2 + int(bump[i, k] > 0.6) + int(bump[i, k] > 1.2), k] = 1
        Wg[rng.random(Wg.shape) < 0.03] = 0
        wo = grid_mesh(name + " wall", Wg, {1: "stone"}, 0.125, loc=(0, 0.25, 0))
        out.append(wo)
    elif pose == "drop":
        orient(ob, belly=(0, -1, 0), head=(0, 0, -1))
        bpy.context.view_layer.update()
        zs = [(ob.matrix_world @ Vector(c)).z for c in ob.bound_box]
        ob.location.z += 0.35 + 0.2 * s - min(zs)
        bpy.context.view_layer.update()
        top = ob.matrix_world @ Vector(spl)
        S = Strands(name + " thread")
        S.seg(np.array(top), np.array(top) + np.array([0, 0, 6 + 2 * s]), PX)
        out.append(S.build())
    elif pose == "death":
        orient(ob, belly=(0, 0, 1), head=(0, 1, 0))
        ground(ob, 0.25)
    else:
        ground(ob, 0.25)
    return out


def terrain_strip(name, width, depth=3.5, seed=0):
    """Rough Dread Stone ground at 1/8 block: bumps, loose rocks, a few lit veins."""
    rng = np.random.default_rng(seed)
    nx, ny = int(width * 8), int(depth * 8)
    h = smooth_noise((nx, ny), rng, 3)
    G = np.zeros((nx, ny, 8), dtype=np.int16)
    zz = np.arange(8)[None, None, :]
    G[zz < (2 + np.clip(h * 1.1, -1, 3)).astype(int)[:, :, None]] = 1
    G[:, :, 0] = 2
    top = surface_mask(G) & (np.arange(8)[None, None, :] > 0)
    G[top & (rng.random(G.shape) < 0.025)] = 3
    for k in range(int(width * 1.5)):
        c = (rng.uniform(0, nx), rng.uniform(0, ny), 2.5)
        ellip(G, c, (rng.uniform(0.8, 2), rng.uniform(0.8, 2), rng.uniform(0.8, 1.6)), 1, only_empty=True)
    ob = grid_mesh(name, G, {1: "stone", 2: "deep", 3: "veinblock"}, 0.125)
    ob.location = (0, 0, -0.05)
    return ob


def row_lights(code, X, width):
    light(f"{code} key", X + np.array([-width * 0.3, -width * 0.55, width * 0.45]), (1.0, 0.95, 0.85), 260 * width * min(1.0, width / 15),
          cutoff=width * 2, kind="AREA", size=width * 0.4, rot=(math.radians(50), 0, math.radians(-25)))
    light(f"{code} rim", X + np.array([width * 0.35, width * 0.4, width * 0.3]), (0.1, 1.0, 0.2), 120 * width * min(1.0, width / 15),
          cutoff=width * 2, kind="AREA", size=width * 0.3, rot=(math.radians(-60), 0, math.radians(150)))


POSES = ("stand", "wall", "drop", "rear", "death")
POSE_WORDS = "walking (feet lifting in turn), clinging to a wall, dropped on its thread, rearing to strike, dead on its back"


def build_row(code, name, X, kind, style, seed, facts, opt=None):
    CUR.clear(); CUR.update(opt or {})
    s = SPAN[kind]
    gap = s * 1.45
    width = gap * len(POSES) + s
    t = terrain_strip(f"{code} ground", width, 2.0 + s * 1.2, seed)
    t.location = X + np.array([0, 0.3 * s, -0.05])
    for i, pose in enumerate(POSES):
        pv = empty(f"{code} pose {i + 1} {pose}", X + np.array([(i - (len(POSES) - 1) / 2) * gap, 0, 0]))
        spin(pv)
        before = set(o.name for o in scene.objects)
        for o in pose_spider(f"{code} {pose}", kind, style, pose, seed * 10 + i):
            pass
        for o in scene.objects:
            if o.name not in before and o.parent is None and o.type != "CAMERA":
                o.parent = pv
    row_lights(code, X, width)
    dist = max(width * 0.78, 6.0)
    cam = camera(f"Cam {code} {name}", X + np.array([0, -dist, dist * 0.38]), X + np.array([0, 0, s * 0.42]),
                 lens=35)
    add_take(code, name, cam, "turntable", facts + "; every pose turns: " + POSE_WORDS)
    CUR.clear()


# --------------------------------------------------------------- the Matron, round 2: three abdomens, four poses
MATRON_NOTE = {
    "cage": "Lantern cage: fear glass inside a standing gold cage of thick bars and collars, the flaring core and "
            "broodlings inside",
    "chitin": "Cracked chitin: an opaque black-and-yellow plated shell split by deep glowing cracks, the core "
              "showing through little glass windows",
    "hourglass": "Hourglass: two glass bulbs joined at a gold waist, broodlings in both, a stream of light falling "
                 "between them",
}


def matron2(name, style="cage", pose="folded", seed=7, crack_lab=7, cracked=1.0):
    rng = np.random.default_rng(seed)
    R = 50
    W = 2 * R + 64
    H = 120
    G = np.zeros((W, W, H), dtype=np.int16)
    ox, oy = W / 2, W / 2 + 14
    zb = 26
    ceph = np.array([ox, oy + 8, zb + 2 + (5 if pose == "rear" else 0)])
    ellip(G, ceph, (12, 14, 9), 1)
    head = ceph + np.array([0, 13, 3 + (3 if pose == "rear" else 0)])
    ellip(G, head, (8, 7, 7), 1)
    surf = surface_mask(G)
    zz = np.arange(H)[None, None, :] + 0.5
    G[surf & (zz > zb + 3)] = 2
    G[surf & (zz < zb - 2)] = 5
    dark = {3, 7}
    for i in range(10):
        a = math.radians(-70 + i * (140 / 9))
        p = head + np.array([math.sin(a) * 6.5, math.cos(a) * 4.5 + 2.5, 4.5 + math.cos(a) * 1.5])
        ellip(G, p, (1.5, 1.5, 1.5), 1 if i in dark else 3)
        if i in dark:
            ellip(G, p + np.array([0, 0.6, 0.4]), (0.9, 0.9, 0.9), 0)
    for sx in (-1, 1):
        a = head + np.array([sx * 3, 6, -3])
        fang = np.array([sx * (2.5 if pose == "rear" else 0.5), 2 + (2 if pose == "rear" else 0), -6])
        capsule(G, a, a + fang, 1.8, 1)
        capsule(G, a + fang, a + fang + np.array([-sx * 0.3, -1, -3]), 1.0, 4)
    axd = math.radians(MOPT.get("axis", 28))
    axis = np.array([0, -math.cos(axd), math.sin(axd)])
    A0 = ceph + np.array([0, -10, 2])
    L, Rm = 58.0, 26.0
    lo = np.maximum((np.minimum(A0, A0 + axis * L) - Rm - 6).astype(int), 0)
    hi = np.minimum((np.maximum(A0, A0 + axis * L) + Rm + 6).astype(int), G.shape)
    p = _pts(lo, hi)
    rel = [p[i] - A0[i] for i in range(3)]
    t = (rel[0] * axis[0] + rel[1] * axis[1] + rel[2] * axis[2]) / L
    radv = [rel[i] - t * L * axis[i] for i in range(3)]
    rad = np.sqrt(sum(x * x for x in radv))
    tt = 2 * t - 1
    if style == "hourglass":
        bulb = np.sqrt(np.clip(1 - ((np.abs(tt) - 0.5) / 0.5) ** 2, 0, 1))
        prof = Rm * (0.18 + 0.82 * bulb) * np.where(tt < 0, 1.0, 0.85)
    else:
        prof = Rm * (0.32 + 0.68 * np.sqrt(np.clip(1 - tt ** 2, 0, 1)))
    inside = (t >= 0) & (t <= 1) & (rad <= prof)
    shell = inside & (rad > prof - 1.6)
    ang = np.arctan2(radv[0], radv[2] + 1e-9)
    sub = G[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    if style == "chitin":
        sub[inside & (rad > prof - 2.6)] = 1
        bands = shell & ((np.floor(tt * 9).astype(int) % 2) == 0)
        sub[bands] = 2
        win = shell & (np.abs(((ang + math.pi) % (math.pi / 2)) - math.pi / 4) < MOPT.get("win", 0.18)) & \
            (np.abs(((tt + 1) % 0.4) - 0.2) < MOPT.get("winz", 0.06))
        sub[win] = 6
        if MOPT.get("lifted"):    # the plates stand off the shell, light leaking from under them
            lift_ = (t >= 0) & (t <= 1) & (rad > prof + 0.4) & (rad <= prof + 1.8) & \
                ((np.floor(tt * 9).astype(int) % 2) == 0) & (np.abs(tt) < 0.85)
            sub[lift_] = 2
            sub[shell & ~bands & (sub == 1) & (np.abs(tt) < 0.85)] = 7
        if MOPT.get("gold_rim"):  # every plate band edged in polished gold
            sub[shell & (np.abs((tt * 9) - np.round(tt * 9)) < 0.09)] = 8
        G_inner = inside & (rad <= prof - 2.6)
        sub[G_inner] = 0
    else:
        sub[shell] = 6
    if style == "cage" or MOPT.get("caged"):
        bars = inside & (rad > prof - 1.6) & (np.abs(((ang + math.pi) % (math.pi / 4)) - math.pi / 8) > math.pi / 8 - 0.11)
        sub[bars] = 8
        outer = (t >= 0.05) & (t <= 0.95) & (rad > prof + 0.6) & (rad <= prof + 2.4) & \
            (np.abs(((ang + math.pi) % (math.pi / 4)) - math.pi / 8) > math.pi / 8 - 0.09)
        sub[outer] = 8
        collar = (t >= 0) & (t <= 1) & (rad <= prof + 2.4) & (rad > prof - 1.6) & \
            ((np.abs(tt + 0.8) < 0.06) | (np.abs(tt - 0.8) < 0.06) | (np.abs(tt) < 0.03))
        sub[collar] = 8
    if style == "hourglass":
        waist = (t >= 0) & (t <= 1) & (np.abs(tt) < 0.07) & (rad <= prof + 2.2)
        sub[waist] = 8
        sub[inside & (np.abs(tt) > 0.93)] = 8
    if style != "hourglass":
        sub[inside & (np.abs(tt) > 0.9)] = 8
    hits = np.argwhere(shell & ((sub == 6) | (sub == 2) | (sub == 1)))
    if len(hits):
        n_cr = int((14 if style == "chitin" else 8) * cracked)
        for k in range(n_cr):
            q = hits[rng.integers(len(hits))].astype(float)
            dirv = rng.normal(size=3); dirv /= np.linalg.norm(dirv)
            for step in range(80):
                qi = np.round(q).astype(int)
                if np.all(qi >= 0) and np.all(qi < sub.shape) and sub[tuple(qi)] in (6, 2, 1):
                    sub[tuple(qi)] = crack_lab
                    if style == "chitin":
                        for dd in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
                            q2 = tuple(np.clip(qi + dd, 0, np.array(sub.shape) - 1))
                            if sub[q2] in (2, 1):
                                sub[q2] = crack_lab
                dirv += rng.normal(size=3) * 0.45; dirv /= np.linalg.norm(dirv)
                q = q + dirv
                qi = np.clip(np.round(q).astype(int), 0, np.array(sub.shape) - 1)
                if not shell[tuple(qi)]:
                    q = hits[np.argmin(np.linalg.norm(hits - q, axis=1))].astype(float)
    cores = [A0 + axis * L * 0.5] if style != "hourglass" else [A0 + axis * L * 0.25, A0 + axis * L * 0.75]
    for core in cores:
        ellip(G, core, (4.5, 4.5, 4.5), 10 if MOPT.get("core_green") else 4)
        u = np.cross(axis, [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(axis, u)
        for k in range(6):
            a = rng.uniform(0, 2 * math.pi); r = rng.uniform(6, 11)
            c = core + axis * rng.uniform(-6, 6) + (u * math.cos(a) + v * math.sin(a)) * r
            ellip(G, c, (2.2, 2.6, 1.8), 1, only_empty=True)
            ellip(G, c + np.array([0, 1.8, 0.8]), (0.7, 0.7, 0.7), 3)
    if style == "hourglass":
        capsule(G, cores[0], cores[1], 1.0, 4)
    tip = A0 + axis * (L + 1.5)
    capsule(G, tip, tip + axis * 4, 2.5, 4)
    for sx in (-1, 1):
        for li, ang_d in enumerate((62, 100, 140)):
            a = math.radians(ang_d + rng.uniform(-4, 4))
            d = np.array([sx * math.sin(a), math.cos(a), 0.0])
            hip = ceph + d * np.array([10, 7, 0])
            if pose == "drop":
                d2 = np.array([sx * math.sin(a) * 0.7, 0.6, 0.0])
                knee = hip + d2 * R * 0.42 + np.array([0, 0, 22])
                ank = hip + d2 * R * 0.8 + np.array([0, 0, -6])
                foot = hip + d2 * R * 0.95 + np.array([0, 0, -18])
            else:
                knee = hip + d * R * 0.42 + np.array([0, 0, 32])
                ank = hip + d * R * 0.8 + np.array([0, 0, 10])
                foot = hip + d * R * 1.02; foot[2] = 1.0
            foot[2] = max(foot[2], 1.0); ank[2] = max(ank[2], 1.0)
            capsule(G, hip, knee, 3.0, 2); capsule(G, knee, ank, 2.3, 1); capsule(G, ank, foot, 1.5, 1)
            ellip(G, knee, (3.4,) * 3, 4); ellip(G, ank, (2.7,) * 3, 4)
            capsule(G, foot + np.array([0, 0, 2]), foot, 1.3, 4)
        hip = ceph + np.array([sx * 7, 11, 2])
        if pose == "folded":
            knee = hip + np.array([sx * 8, 14, 30]); tip = knee + np.array([sx * 2, 6, -30])
        elif pose == "strike":
            knee = hip + np.array([sx * 14, 10, 40]); tip = knee + np.array([sx * 6, 30, 6])
        elif pose == "rear":
            knee = hip + np.array([sx * 12, 4, 44]); tip = knee + np.array([sx * 10, -4, 28])
        else:   # drop: scythes reaching down at the target
            knee = hip + np.array([sx * 10, 18, 10]); tip = knee + np.array([sx * 2, 14, -24])
        tip[2] = max(tip[2], 2)
        capsule(G, hip, knee, 3.2, 2)
        ellip(G, knee, (4.0,) * 3, 4)
        capsule(G, knee, tip, 2.4, 1)
        for k in range(1, 9):
            q = knee + (tip - knee) * (k / 9)
            off = np.array([-sx * 2.2, 0, 0])
            capsule(G, q, q + off, 0.9, 4)
    labels = {1: "shell", 2: "plate", 3: "eye", 4: "joint", 5: "under", 6: "glass", 7: "crack", 8: "gold",
              10: "greencrack"}
    if MOPT.get("dim_glass"):
        labels[6] = "glass_dim"
    present = {k: v for k, v in labels.items() if np.any(G == k)}
    ob = grid_mesh(name, G, present, PX, trans=(6,))
    spl = (tip - np.array([W / 2, W / 2, 0])) * PX
    return ob, spl


MATRON_POSES = ("folded", "strike", "rear", "drop")


def build_matron_row(code, name, X, style, seed, opt=None, note=None):
    MOPT.clear(); MOPT.update(opt or {})
    gap = 9.5
    width = gap * 4 + 2
    t = terrain_strip(f"{code} ground", width, 9, seed)
    t.location = X + np.array([0, 1.0, -0.05])
    for i, pose in enumerate(MATRON_POSES):
        pv = empty(f"{code} pose {i + 1} {pose}", X + np.array([(i - 1.5) * gap, 0, 0]))
        spin(pv)
        ob, spl = matron2(f"{code} {pose}", style, pose, seed + i)
        ob.parent = pv
        if pose == "drop":
            bpy.context.view_layer.update()
            zs = [(ob.matrix_world @ Vector(c)).z for c in ob.bound_box]
            ob.location.z += 1.2 - min(zs)
            S = Strands(f"{code} drop thread")
            bpy.context.view_layer.update()
            topz = max((ob.matrix_world @ Vector(c)).z for c in ob.bound_box)
            S.seg((0, -1.2, 3.5), (0, -1.2, topz + 8), PX * 2)
            th = S.build(); th.parent = pv
        else:
            ground(ob, 0.25)
        lc = light(f"{code} core {i}", (0, -1.5, 3.0 + (1.2 if pose == "drop" else 0)), (1.0, 0.58, 0.03), 140,
                   cutoff=8)
        lc.parent = pv
    row_lights(code, X, width * 0.8)
    cam = camera(f"Cam {code} {name}", X + np.array([0, -width * 0.88, width * 0.3]), X + np.array([0, 0, 2.6]), lens=35)
    MOPT.clear()
    add_take(code, name, cam, "turntable",
             (note or MATRON_NOTE[style]) + "; four poses turning: scythes folded like a mantis, striking, rearing to scream, "
             "dropping on her thread with scythes reaching down")


# --------------------------------------------------------------- eggs (from v2.0106, smaller pods for burrows)
def egg(name, loc, rot, cracked=0, burst=False, seed=0, scale=1.0):
    rng = np.random.default_rng(seed)
    G = np.zeros((20, 20, 26), dtype=np.int16)
    c = np.array([10, 10, 12.5])
    ellip(G, c, (8, 8, 11.5), 6, shell=1.2)
    ellip(G, c + np.array([0, 1, -1]), (3.2, 3.6, 3.0), 1, only_empty=True)
    ellip(G, c + np.array([0, -2.5, 1.5]), (3.6, 3.6, 4.0), 1, only_empty=True)
    ellip(G, c + np.array([0, 4, 0]), (0.8,) * 3, 3)
    ellip(G, c + np.array([0, -1, 0]), (1.6,) * 3, 4)
    hits = np.argwhere(G == 6)
    for k in range(cracked):
        q = hits[rng.integers(len(hits))].astype(float)
        dv = rng.normal(size=3); dv /= np.linalg.norm(dv)
        for s in range(30):
            qi = np.round(q).astype(int)
            if np.all(qi >= 0) and np.all(qi < G.shape) and G[tuple(qi)] == 6:
                G[tuple(qi)] = 7
            dv += rng.normal(size=3) * 0.5; dv /= np.linalg.norm(dv)
            q = hits[np.argmin(np.linalg.norm(hits - (q + dv), axis=1))].astype(float)
    if burst:
        G[:, :, 17:] = 0
        G[G == 1] = 0
    ob = grid_mesh(name, G, {1: "shell", 3: "eye", 4: "joint", 6: "glass", 7: "crack"}, PX * scale, trans=(6,))
    ob.location = loc; ob.rotation_euler = rot
    return ob


def cocoon(name, loc, length=1.6, seed=0):
    rng = np.random.default_rng(seed)
    n = int(length * 8)
    G = np.zeros((8, 8, n + 2), dtype=np.int16)
    ellip(G, (4, 4, n / 2 + 1), (3.2, 3.0, n / 2), 1)
    G[(G == 1) & (rng.random(G.shape) < 0.15)] = 2
    ob = grid_mesh(name, G, {1: "cocoon", 2: "silkblock"}, 0.125)
    ob.location = loc
    return ob


# --------------------------------------------------------------- caves, round 2 (no columns; spider-made burrows)
CAVE_LABELS = {1: "stone", 2: "deep", 3: "silkblock", 4: "veinblock", 5: "bone"}


def chunk(R, Hh, seed):
    """A round slab of ground for a turning diorama, its underside tapering like a torn-out lump of earth."""
    rng = np.random.default_rng(seed)
    n = 2 * R + 4
    xx, yy, zz = np.mgrid[0:n, 0:n, 0:Hh]
    c = n / 2
    r = np.hypot(xx + 0.5 - c, yy + 0.5 - c)
    wob = smooth_noise((n, n, Hh), rng, 3) * 1.4
    taper = np.where(zz < Hh * 0.4, 0.55 + 0.45 * (zz / (Hh * 0.4)), 1.0)
    G = ((r + wob) < R * taper).astype(np.int16)
    G[(G == 1) & (zz < Hh * 0.45 + wob * 2)] = 2
    for _ in range(2):     # no loose floating blocks round the rim
        P = np.pad(G > 0, 1)
        cnt = sum(np.roll(P, sh, ax)[1:-1, 1:-1, 1:-1].astype(np.int8) for ax in range(3) for sh in (1, -1))
        G[(G > 0) & (cnt < 3)] = 0
    return G, xx, yy, zz, r, c, rng


def walk_tunnel(G, start, d, length, rad, rng, rise=0.0, wander=0.35):
    p = np.asarray(start, float); d = np.asarray(d, float); d /= np.linalg.norm(d)
    pts = []
    for k in range(int(length)):
        ellip(G, p, (rad, rad, rad * 0.9), 0)
        pts.append(p.copy())
        d = d + rng.normal(size=3) * wander * np.array([1, 1, 0.5]) + np.array([0, 0, rise])
        d /= np.linalg.norm(d)
        p = p + d
    return pts


def finish_cave(G, carved_before, zz, rng, mouths=(), collar=2.6):
    solid0 = carved_before
    carved = solid0 & (G == 0)
    near = dilate(dilate(carved)) & (G > 0)
    surf = surface_mask(G)
    G[surf & near & (rng.random(G.shape) < 0.035)] = 3
    for m in mouths:
        lo = np.maximum(np.floor(np.asarray(m) - collar - 1).astype(int), 0)
        hi = np.minimum(np.ceil(np.asarray(m) + collar + 1).astype(int), G.shape)
        sub = G[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        p = _pts(lo, hi)
        dd = np.sqrt(sum((p[i] - m[i]) ** 2 for i in range(3)))
        ssub = surf[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        sub[(dd < collar) & ssub & (sub > 0)] = 3
    G[surf & (G <= 2) & (rng.random(G.shape) < 0.01)] = 4
    G[surf & (G <= 2) & (rng.random(G.shape) < 0.008)] = 5


def wall_spot(G, p, d):
    """From p (block coords, inside air), walk along d to the first solid cell; return the face point."""
    p = np.asarray(p, float); d = np.asarray(d, float); d /= np.linalg.norm(d)
    for k in range(60):
        q = p + d * k * 0.25
        qi = np.floor(q).astype(int)
        if np.any(qi < 0) or np.any(qi >= G.shape):
            return None
        if G[tuple(qi)] > 0:
            return p + d * max(0, k - 1) * 0.25
    return None


def place_on(ob, spot, belly, head, s):
    orient(ob, belly, head)
    ob.location = (0, 0, 0)
    bpy.context.view_layer.update()
    b = np.asarray(belly, float); b /= np.linalg.norm(b)
    ext = max(((ob.matrix_world @ Vector(c)) @ Vector(b)) for c in ob.bound_box)
    ob.location = tuple(np.asarray(spot) - b * ext)


def cave_spiders(G, off, items, rng, code):
    """items: (kind, style, spot_air_point, belly_dir, head_dir) in block coords of G."""
    k = 0
    for kind, style, pose, p, belly, head in items:
        spot = wall_spot(G, p, belly)
        if spot is None:
            continue
        ob, spl = spider2(f"{code} {kind} {k}", kind, style, pose, 500 + k)
        place_on(ob, spot + off, belly, head, SPAN[kind])
        k += 1


def build_W4a(X):
    """Burrow warren: a bowl-shaped chamber whose walls are riddled with round spider burrows at every height."""
    code, before = "W4a", set(o.name for o in scene.objects)
    R, Hh = 17, 24
    G, xx, yy, zz, r, c, rng = chunk(R, Hh, 41)
    solid0 = G > 0
    ch = np.array([c, c, 12.0])
    ellip(G, ch, (11.5, 9.5, 7.5), 0)
    fl = smooth_noise(G.shape[:2], rng, 3)
    foot = np.hypot((xx[:, :, 0] + 0.5 - c) / 11.5, (yy[:, :, 0] + 0.5 - c) / 9.5) < 1.0
    floor_h = (6 + fl * 1.3 + np.hypot(xx[:, :, 0] - c, yy[:, :, 0] - c) * 0.18).astype(int)
    G[(zz < floor_h[:, :, None]) & foot[:, :, None] & solid0] = 1
    mouths = []
    for k in range(16):
        a = k / 16 * 2 * math.pi + rng.uniform(-0.15, 0.15)
        z0 = rng.uniform(7.5, 15)
        d = np.array([math.cos(a), math.sin(a), rng.uniform(-0.25, 0.35)])
        start = ch + np.array([math.cos(a) * 9.5, math.sin(a) * 7.8, z0 - 12])
        pts = walk_tunnel(G, start, d, rng.integers(9, 22), rng.uniform(1.15, 1.7), rng, rise=rng.uniform(-0.04, 0.06))
        mouths.append((start, d))
        if k % 3 == 0:     # side chambers off some burrows (egg nests)
            ellip(G, pts[-1], (2.6, 2.6, 2.0), 0)
    top = (15.5 + smooth_noise(G.shape[:2], rng, 4) * 1.6).astype(int)
    G[(zz >= top[:, :, None])] = 0
    for k in range(10):    # drips hanging from the overhanging lip (not columns: they stop well above the floor)
        a = rng.uniform(0, 2 * math.pi)
        p = ch + np.array([math.cos(a) * 10.2, math.sin(a) * 8.3, 2.0])
        for j in range(int(rng.integers(2, 4))):
            q = np.floor(p - np.array([0, 0, j])).astype(int)
            if np.all(q >= 0) and np.all(q < G.shape):
                G[tuple(q)] = 1
    finish_cave(G, solid0, zz, rng, [m for m, d in mouths])
    off = np.array([-c, -c, -12.0])
    blocks(f"{code} ground", G, tuple(off), CAVE_LABELS)
    S = Strands(f"{code} silk")
    for k, (m, d) in enumerate(mouths):
        mm = m + off
        if k % 2 == 0:     # trip lines fanning from the burrow mouth across the floor: funnel-web hunters
            for j in range(5):
                a = math.atan2(-d[1], -d[0]) + (j - 2) * 0.28
                e = mm + np.array([math.cos(a) * rng.uniform(3, 6), math.sin(a) * rng.uniform(3, 6), 0])
                e[2] = -12 + 6.3 + rng.uniform(-0.2, 0.4)
                S.seg(mm, e)
        if k % 4 == 1:
            S.web(mm + np.array(d) * -0.3, d, 1.5, spokes=8, rings=3, rng=np.random.default_rng(k))
    S.build()
    items = []
    for k, (m, d) in enumerate(mouths[::3]):
        items.append(("hunter", ["plate", "shard", "bristle"][k % 3], "stand", m - d * 1.5 + np.array([0, 0, 0.2]),
                      (0, 0, -1), tuple(-d[:2]) + (0,)))
    for k in range(3):
        a = rng.uniform(0, 2 * math.pi)
        items.append(("hunter", "plate", "stand", ch + np.array([math.cos(a) * 6, math.sin(a) * 5, 0]),
                      (math.cos(a), math.sin(a), 0), (0, 0, 1)))
    for k in range(5):
        a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(1, 5)
        items.append(("broodling", "plate", "stand", ch + np.array([math.cos(a) * rr, math.sin(a) * rr, -2]),
                      (0, 0, -1), (math.cos(a), math.sin(a), 0)))
    cave_spiders(G, off, items, rng, code)
    for k in range(4):
        m, d = mouths[(k * 4 + 2) % len(mouths)]
        egg(f"{code} egg {k}", tuple(m + off + d * 2.5 - np.array([0, 0, 1.0])), (0, 0, rng.uniform(0, 6)),
            cracked=k % 2 * 2, seed=k, scale=0.8)
        light(f"{code} burrow glow {k}", tuple(m + off + d * 3), (1.0, 0.55, 0.03), 30, cutoff=6)
    pr, hand = player(f"{code} player", (0.5, -2.5, -12 + float(floor_h[int(c + 0.5), int(c - 2.5)])), rot_z=0.4)
    ring_light(f"{code} ring", hand, energy=650)
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} fill", X + np.array([-20, -28, 26]), (0.55, 0.6, 0.8), 22000, cutoff=90, kind="AREA", size=18,
          rot=(math.radians(45), 0, math.radians(-35)))
    cam = camera(f"Cam {code} Burrow warren", X + np.array([0, -33, 27]), X + np.array([0, 0, -5]), lens=24)
    add_take(code, "Burrow warren", cam, "turntable",
             "a bowl-shaped chamber with no columns, its walls riddled with 16 round spider burrows at every height "
             "(silk collars, trip lines fanning across the floor from the mouths, egg nests in side pockets lit from "
             "inside); Hunters wait in the mouths and on the walls; the whole lump of ground turns")


def build_W4b(X, code="W4b", v=None):
    """Funnel hollow: terraces stepping down into a funnel web that drains into the nest hole."""
    v = v or {}
    before = set(o.name for o in scene.objects)
    R, Hh = 18, 26
    G, xx, yy, zz, r, c, rng = chunk(R, Hh, 52)
    solid0 = G > 0
    wob = smooth_noise(G.shape[:2], rng, 4)[:, :, None]
    rr = r[:, :, :1] + wob * 0.9
    tz = v.get("tz", [19, 15, 11, 7])
    trad = v.get("trad", [15.5, 11.5, 8.0, 5.0])
    if v.get("spiral"):      # v2.0109: one terrace winding down round the hollow like a ramp
        ang_ = (np.arctan2(yy[:, :, :1] + 0.5 - c, xx[:, :, :1] + 0.5 - c) + math.pi) / (2 * math.pi)
        z_top, z_bot = tz[0], tz[-1]
        turns = v["spiral"]
        for zc in range(int(z_bot), int(z_top) + 1):
            f_ = (z_top - zc) / max(z_top - z_bot, 1)
            r_here = trad[0] * (1 - f_) + trad[-1] * f_
            step_ = (np.floor(f_ * turns + ang_) % 1.0)
            G[(rr < r_here - step_ * 2.2) & (zz == zc)] = 0
        G[(rr < trad[0]) & (zz >= z_top)] = 0
        G[(rr < trad[-1]) & (zz >= z_bot)] = 0
    else:
        for k, (z0, r0) in enumerate(zip(tz, trad)):
            G[(rr < r0) & (zz >= z0)] = 0
            G[(rr >= r0) & (rr < r0 + v.get("lip", 1.6)) & (zz >= z0) & (zz < z0 + v.get("liph", 2))] = 0   # undercut lip
    G[(r < v.get("hole", 2.6) + wob[:, :, 0][:, :, None] * 0.4) & (zz >= 1)] = 0          # the nest hole
    G[zz >= 22] = 0
    mouths = []
    for k, (z0, r0) in enumerate(zip(tz, trad)):
        for j in range(v.get("mouths", 3) if k < 3 else 2):
            a = j / v.get("mouths", 3) * 2 * math.pi + k * 0.9 + rng.uniform(-0.2, 0.2)
            start = np.array([c + math.cos(a) * (r0 + 0.5), c + math.sin(a) * (r0 + 0.5), z0 + 1.3])
            d = np.array([math.cos(a), math.sin(a), 0.05])
            walk_tunnel(G, start, d, rng.integers(5, 10), rng.uniform(1.0, 1.3), rng, wander=0.25)
            mouths.append((start, d))
    finish_cave(G, solid0, zz, rng, [m for m, d in mouths])
    off = np.array([-c, -c, -12.0])
    blocks(f"{code} ground", G, tuple(off), CAVE_LABELS)
    S = Strands(f"{code} funnel web")
    nsp = v.get("spokes", 26)
    web_r = v.get("web_r", 11.0)
    for j in range(nsp):
        a = j / nsp * 2 * math.pi + rng.uniform(-0.05, 0.05)
        pts = []
        for f in np.linspace(0, 1, 9):
            rad = web_r * (1 - f) + 2.3 * f
            z = (v.get("web_z", 15.4) + 0.2) * (1 - f) + 2.5 * f - math.sin(f * math.pi) * 1.6
            pts.append(off + np.array([c + math.cos(a) * rad, c + math.sin(a) * rad, z]))
        S.poly(pts, PX * 1.5 * v.get("web_w", 1.0))
    for f in np.linspace(0.08, 0.95, v.get("rings", 9)):
        pts = []
        for j in range(nsp + 1):
            a = j / nsp * 2 * math.pi
            rad = web_r * (1 - f) + 2.3 * f
            z = (v.get("web_z", 15.4) + 0.2) * (1 - f) + 2.5 * f - math.sin(f * math.pi) * 1.6
            pts.append(off + np.array([c + math.cos(a) * rad, c + math.sin(a) * rad, z]))
        S.poly(pts, PX * v.get("web_w", 1.0))
    for m, d in mouths[::2]:
        S.web(m + off - d * 0.2, d, 1.3, spokes=7, rings=3, rng=np.random.default_rng(int(m[0] * 10)))
    if v.get("sheets"):      # sheet webs laid flat over the terrace floors
        for k, (z0, r0) in enumerate(zip(tz[:3], trad[:3])):
            for j in range(3):
                a = j / 3 * 2 * math.pi + k * 1.3 + 0.5
                rm = (r0 + (trad[k + 1] if k + 1 < len(trad) else 2.5)) / 2
                S.web(off + np.array([c + math.cos(a) * rm, c + math.sin(a) * rm, z0 + 0.15]), (0, 0, 1),
                      1.6 + 0.3 * j, spokes=9, rings=4, rng=np.random.default_rng(300 + k * 3 + j))
    S.build(v.get("web_mk", "silk"))
    items = []
    calm = v.get("calm")
    if v.get("lip_hunters"):  # Hunters clinging to the walls under the overhanging lips
        for k, (z0, r0) in enumerate(zip(tz[:3], trad[:3])):
            for j in range(2):
                a = j * math.pi + k * 0.8 + 0.3
                items.append(("hunter", ["plate", "shard", "bristle"][(k + j) % 3], "stand",
                              np.array([c + math.cos(a) * (r0 - 1.2), c + math.sin(a) * (r0 - 1.2), z0 + 0.9]),
                              (math.cos(a), math.sin(a), 0), (-math.sin(a), math.cos(a), 0)))
    for k, (m, d) in enumerate(mouths):
        if k % 2 == 0:
            items.append(("hunter", ["plate", "bristle", "shard"][k % 3], "stand", m - d * 1.4 + np.array([0, 0, 0.2]),
                          (0, 0, -1), tuple(-d[:2]) + (0,)))
    items.append(("hunter", "shard", "stand", np.array([c, c, 4.0]), (1, 0, 0), (0, 0, 1)))   # climbing out of the hole
    for k in range(6):
        a = rng.uniform(0, 2 * math.pi)
        items.append(("broodling", "bristle", "stand", np.array([c + math.cos(a) * 9.8, c + math.sin(a) * 9.8, 16.0]),
                      (0, 0, -1), (math.cos(a + 1.6), math.sin(a + 1.6), 0)))
    if calm:   # calm: nothing out; only a few eyes deep in the burrow mouths
        items = [("broodling", "plate", "stand", m - d * 0.6, (0, 0, -1), tuple(-d[:2]) + (0,)) for m, d in mouths[1::3]]
    cave_spiders(G, off, items, rng, code)
    w, spl = spider2(f"{code} weaver drop", "weaver", "bristle", "drop", 77)
    orient(w, belly=(0, -1, 0), head=(0, 0, -1)); w.location = (6.0, 5.0, -12 + 15.5)
    bpy.context.view_layer.update()
    top = w.matrix_world @ Vector(spl)
    S2 = Strands(f"{code} weaver thread"); S2.seg(np.array(top), np.array(top) + np.array([0, 0, 9]))
    S2.build(v.get("web_mk", "silk"))
    if calm:
        w.hide_render = True; w.hide_viewport = True
    light(f"{code} nest glow", (0, 0, -12 + 3.0), (1.0, 0.55, 0.03), 120 if calm else 260, cutoff=12)
    pr, hand = player(f"{code} player", (-8.5, -9.5, -12 + 19), rot_z=-0.75)
    ring_light(f"{code} ring", hand, energy=750)
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} fill", X + np.array([-20, -28, 28]), (0.55, 0.6, 0.8), 22000, cutoff=90, kind="AREA", size=18,
          rot=(math.radians(45), 0, math.radians(-35)))
    if v.get("no_take"):
        return
    nm = v.get("name", "Funnel hollow")
    cam = camera(f"Cam {code} {nm}", X + np.array([0, -33, 29]), X + np.array([0, 0, -3]), lens=24)
    add_take(code, nm, cam, "turntable", v.get("facts", "funnel hollow"))


def build_W4c(X, code="W4c", v=None):
    """Crevice: a deep, narrow, winding crack whose walls are honeycombed with burrows, laced with silk ladders."""
    v = v or {}
    before = set(o.name for o in scene.objects)
    wide = v.get("wide", 0.0)
    R, Hh = 18, 28
    G, xx, yy, zz, r, c, rng = chunk(R, Hh, 63)
    solid0 = G > 0
    wob = smooth_noise(G.shape, rng, 3)
    cx = c + np.sin((yy + 0.5) * 0.22) * 3.0 + np.sin((yy + 0.5) * 0.07 + 1) * 2
    w = 1.8 + wide + wob * 0.9 + np.clip((zz - 3) / Hh, 0, 1) * 3.6 + (np.abs(np.sin((zz + 0.5) * 0.9)) > 0.85) * 0.8
    G[(np.abs(xx + 0.5 - cx) < w) & (zz >= 3) & (np.abs(yy + 0.5 - c) < R - 2)] = 0
    for bi, (y0b, ab) in enumerate(v.get("branches", ())):   # side cracks branching off the main one
        x0b = c + math.sin(y0b * 0.22) * 3.0 + math.sin(y0b * 0.07 + 1) * 2
        for tb in np.arange(0, 13, 0.5):
            px_ = x0b + math.cos(ab) * tb; py_ = y0b + math.sin(ab) * tb
            wb = 1.4 + np.clip((zz - 4) / Hh, 0, 1) * 2.2 - tb * 0.05
            G[(np.hypot(xx + 0.5 - px_, yy + 0.5 - py_) < wb) & (zz >= 4 + tb * 0.3)] = 0
    for k in range(10):    # ledges: short shelves jutting from the walls
        y0 = rng.uniform(c - R + 6, c + R - 6); z0 = int(rng.uniform(6, 20)); side = rng.choice([-1, 1])
        x_w = c + math.sin(y0 * 0.22) * 3.0 + math.sin(y0 * 0.07 + 1) * 2
        for yy0 in range(int(y0), int(y0) + int(rng.integers(2, 4))):
            for xo in range(1, 3):
                xi = int(x_w + side * (2.2 + 3.6 * (z0 - 3) / Hh - xo + 1))
                if 0 <= xi < G.shape[0]:
                    G[xi, yy0, z0] = 1
    mouths = []
    for k in range(34):
        y0 = rng.uniform(c - R + 5, c + R - 5); z0 = rng.uniform(4, 22); side = rng.choice([-1, 1])
        x_w = c + math.sin(y0 * 0.22) * 3.0 + math.sin(y0 * 0.07 + 1) * 2
        start = np.array([x_w + side * (1.5 + 3.6 * (z0 - 3) / Hh), y0, z0])
        d = np.array([side, rng.uniform(-0.3, 0.3), rng.uniform(-0.15, 0.15)])
        walk_tunnel(G, start, d, rng.integers(3, 7), rng.uniform(0.85, 1.2), rng, wander=0.2)
        mouths.append((start, d / np.linalg.norm(d)))
    G[zz >= (24 + smooth_noise(G.shape[:2], rng, 4) * 1.5).astype(int)[:, :, None]] = 0
    finish_cave(G, solid0, zz, rng, [m for m, d in mouths], collar=1.9)
    off = np.array([-c, -c, -14.0])
    blocks(f"{code} ground", G, tuple(off), CAVE_LABELS)
    S = Strands(f"{code} silk")
    for k in range(v.get("ladders", 9)):     # silk ladders zig-zagging across the crack
        y0 = rng.uniform(c - R + 6, c + R - 6)
        pts = []
        for j in range(7):
            z = 5 + j * 2.3
            x_w = c + math.sin(y0 * 0.22) * 3.0 + math.sin(y0 * 0.07 + 1) * 2
            half = 1.8 + wide + 3.6 * (z - 3) / Hh
            pts.append(off + np.array([x_w + (half if j % 2 else -half), y0 + rng.uniform(-0.4, 0.4), z]))
        S.poly(pts, PX * 1.5)
    sheets = v.get("sheets", (8.0, 15.0))
    for k, zc in enumerate(sheets):
        y0 = c + (k - (len(sheets) - 1) / 2) * (24 / max(len(sheets), 2))
        x_w = c + math.sin(y0 * 0.22) * 3.0 + math.sin(y0 * 0.07 + 1) * 2
        S.web(off + np.array([x_w, y0, zc]), (0, 1, 0), 2.0 + wide + 3.6 * (zc - 3) / Hh, spokes=11, rings=5,
              rng=np.random.default_rng(90 + k))
    for k in range(v.get("bridges", 0)):   # thick sagging silk cables wall to wall
        y0 = c - R + 8 + k * (2 * R - 16) / max(v.get("bridges", 1) - 1, 1)
        zc = 7 + (k % 3) * 5
        x_w = c + math.sin(y0 * 0.22) * 3.0 + math.sin(y0 * 0.07 + 1) * 2
        half = 1.8 + wide + 3.6 * (zc - 3) / Hh
        pts = [off + np.array([x_w + half * (2 * f - 1), y0, zc - math.sin(f * math.pi) * 1.4]) for f in np.linspace(0, 1, 9)]
        for dy in (-0.25, 0.25):
            S.poly([q + np.array([0, dy, 0]) for q in pts], PX * 3)
    hang = []
    for k in range(6):
        y0 = rng.uniform(c - R + 6, c + R - 6)
        x_w = c + math.sin(y0 * 0.22) * 3.0 + math.sin(y0 * 0.07 + 1) * 2
        top = off + np.array([x_w, y0, 22]); low = top - np.array([0, 0, rng.uniform(4, 9)])
        S.seg(top, low)
        hang.append(low)
    S.build()
    for k, p in enumerate(hang):
        cocoon(f"{code} cocoon {k}", tuple(p - np.array([0.5, 0.5, 1.8])), 1.8, seed=k)
    items = []
    for k, (m, d) in enumerate(mouths[::3]):
        items.append(("hunter", ["shard", "plate", "bristle"][k % 3], "stand", m - d * 0.9 + np.array([0, 0, 2.0]), tuple(d), (0, 0, 1)))
    for k, (m, d) in enumerate(mouths[1::6]):
        items.append(("broodling", "shard", "stand", m - d * 0.5, tuple(d), (0, 0.4, 1)))
    cave_spiders(G, off, items, rng, code)
    for k, (m, d) in enumerate(mouths[2::7]):
        egg(f"{code} egg {k}", tuple(m + off + d * 1.2 - np.array([0, 0, 0.8])), (0, 0, 0), cracked=2, seed=20 + k,
            scale=0.7)
        light(f"{code} hole glow {k}", tuple(m + off + d * 1.8), (1.0, 0.55, 0.03), 25, cutoff=5)
    y0 = c - 4
    x_w = c + math.sin(y0 * 0.22) * 3.0 + math.sin(y0 * 0.07 + 1) * 2
    pr, hand = player(f"{code} player", (x_w - c, y0 - c, -14 + 3), rot_z=0.2)
    ring_light(f"{code} ring", hand, energy=700)
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} fill", X + np.array([-20, -28, 28]), (0.55, 0.6, 0.8), 22000, cutoff=90, kind="AREA", size=18,
          rot=(math.radians(45), 0, math.radians(-35)))
    nm = v.get("name", "Crevice")
    cam = camera(f"Cam {code} {nm}", X + np.array([0, -31, 31]), X + np.array([0, 0, -5]), lens=24)
    add_take(code, nm, cam, "turntable", v.get("facts", "crevice"))


# --------------------------------------------------------------- Lights out, round 2 (three moments, turning)
def small_arena(code, seed):
    R, Hh = 14, 10
    G, xx, yy, zz, r, c, rng = chunk(R, Hh, seed)
    solid0 = G > 0
    G[(zz >= 7 + (smooth_noise(G.shape[:2], rng, 3) * 0.8).astype(int)[:, :, None]) & (r < R - 2.5)] = 0
    G[(zz >= 9)] = 0
    mouths = []
    for k in range(8):
        a = k / 8 * 2 * math.pi
        start = np.array([c + math.cos(a) * (R - 3.2), c + math.sin(a) * (R - 3.2), 7.5])
        d = np.array([math.cos(a), math.sin(a), 0.1])
        walk_tunnel(G, start, d, 5, 1.1, rng, wander=0.2)
        mouths.append((start, d))
    finish_cave(G, solid0, zz, rng, [m for m, d in mouths], collar=1.8)
    off = np.array([-c, -c, -7.0])
    blocks(f"{code} ground", G, tuple(off), CAVE_LABELS)
    return G, off, mouths, c


def build_L(code, name, X, variant, seed, facts):
    before = set(o.name for o in scene.objects)
    G, off, mouths, c = small_arena(code, seed)
    rng = np.random.default_rng(seed)
    if variant == 1:     # the scream: all lights out; only her eyes, her abdomen and eyes in the burrows
        m, spl = matron2(f"{code} matron", "cage", "rear", seed)
        m.location = (0, 3.5, 0); ground(m, 0.0)
        light(f"{code} abdomen", (0, 1.5, 3.2), (1.0, 0.55, 0.03), 220, cutoff=9)
        for k, (mm, d) in enumerate(mouths):
            ob, _ = spider2(f"{code} eyes {k}", "hunter", "plate", "stand", 700 + k)
            place_on(ob, mm + off - d * 0.2 + np.array([0, 0, -0.4]), (0, 0, -1), tuple(-d[:2]) + (0,), 2.6)
        pr, hand = player(f"{code} player", (0, -5.5, 0), rot_z=0)
        ring_light(f"{code} guttering ring", hand, energy=25)
        fill = 600
    elif variant == 2:   # the reignite: a green burst ring sweeping the floor; spiders flipped on their backs
        m, spl = matron2(f"{code} matron", "chitin", "rear", seed)
        m.location = (0, 6.0, 0); m.rotation_euler[0] = math.radians(-8); ground(m, 0.0)
        pr, hand = player(f"{code} player", (0, -1.5, 0), rot_z=0)
        ring_light(f"{code} ring burst", hand, energy=1600)
        Rg = np.zeros((112, 112, 2), dtype=np.int16)
        xg, yg = np.mgrid[0:112, 0:112]
        rr = np.hypot(xg - 55.5, yg - 55.5)
        Rg[(rr > 50) & (rr < 54), 0] = 1
        Rg[(rr > 34) & (rr < 35.5) & (rng.random(rr.shape) < 0.6), 0] = 1
        Rg[(rr > 50) & (rr < 54) & (rng.random(rr.shape) < 0.4), 1] = 1
        ro = grid_mesh(f"{code} burst ring", Rg, {1: "ring"}, PX * 1.6); ro.location = (0, -1.5, 0.05)
        B = Strands(f"{code} dissolve")
        for k in range(160):
            a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(0.3, 4.6)
            p = np.array([math.cos(a) * r0, -1.5 + math.sin(a) * r0, rng.uniform(0.1, 3.5) * (1 - r0 / 6)])
            B.seg(p, p + np.array([0, 0, PX * 2]), PX * rng.choice([1.0, 1.5]))
        B.build("ash")
        for k in range(5):
            a = rng.uniform(0, 2 * math.pi); rr0 = rng.uniform(3.0, 5.5)
            ob, _ = spider2(f"{code} flipped {k}", "hunter" if k < 2 else "broodling", "plate", "death", 720 + k)
            orient(ob, belly=(0, 0, 1), head=(math.cos(a), math.sin(a), 0))
            ob.location = (math.cos(a) * rr0, -1.5 + math.sin(a) * rr0, 0); ground(ob, 0.0)
        fill = 1400
    else:                # the shell opens: overcharged ring, green flooding into her gold cracks
        m, spl = matron2(f"{code} matron", "chitin", "strike", seed, crack_lab=10, cracked=1.6)
        m.location = (0, 4.0, 0); ground(m, 0.0)
        pr, hand = player(f"{code} player", (0.6, -4.0, 0), rot_z=0.15)
        ring_light(f"{code} overcharge", hand, energy=2200)
        bpy.context.view_layer.update()
        hp = np.array(hand.matrix_world.translation)
        Bm = Strands(f"{code} will beam")
        tgt = np.array([0, 1.8, 3.0])
        for j in range(3):
            Bm.poly([hp, (hp + tgt) / 2 + rng.normal(size=3) * 0.15, tgt], PX * (4 - j))
        Bm.build("ring")
        light(f"{code} green in the shell", (0, 1.2, 3.0), (0.08, 1.0, 0.18), 400, cutoff=8)
        fill = 900
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} fill", X + np.array([-14, -20, 18]), (0.45, 0.5, 0.7), fill, cutoff=60, kind="AREA", size=12,
          rot=(math.radians(45), 0, math.radians(-35)))
    cam = camera(f"Cam {code} {name}", X + np.array([0, -24, 13]), X + np.array([0, 0, 2.2]), lens=35)
    add_take(code, name, cam, "turntable", facts)


# --------------------------------------------------------------- Lights out, round 3
def build_L3(code, name, X, variant, seed, facts):
    before = set(o.name for o in scene.objects)
    G, off, mouths, c = small_arena(code, seed)
    rng = np.random.default_rng(seed)
    cam_d, cam_h, look_z, fill = 24, 13, 2.2, 600
    if variant.startswith("scream"):
        m, spl = matron2(f"{code} matron", "cage", "rear", seed)
        m.location = (0, 3.5, 0); ground(m, 0.0)
        light(f"{code} abdomen", (0, 1.5, 3.2), (1.0, 0.55, 0.03), 120 if variant == "scream_dark" else 220, cutoff=9)
        pr, hand = player(f"{code} player", (0, -5.5, 0), rot_z=0)
        if variant == "scream_rings":     # the scream itself: rings of yellow sound rolling out from her head
            S = Strands(f"{code} scream rings")
            hc = np.array([0, 5.6, 4.6])
            for k, rr in enumerate((1.4, 2.4, 3.6, 5.0)):
                pts = [hc + np.array([math.cos(a) * rr, -0.6 * k, math.sin(a) * rr * 0.8])
                       for a in np.linspace(0, 2 * math.pi, 41)]
                S.poly(pts, PX * (3 - 0.5 * k))
            S.build("static")
            for k, (mm, d) in enumerate(mouths):
                ob, _ = spider2(f"{code} eyes {k}", "hunter", "plate", "stand", 700 + k)
                place_on(ob, mm + off - d * 0.2 + np.array([0, 0, -0.4]), (0, 0, -1), tuple(-d[:2]) + (0,), 2.6)
            ring_light(f"{code} guttering ring", hand, energy=25)
            cam_d, cam_h, look_z = 20, 10, 2.6
        elif variant == "scream_dark":    # true dark: only eyes and her abdomen; your ring is a single spark
            for k, (mm, d) in enumerate(mouths):
                ob, _ = spider2(f"{code} eyes {k}", "hunter", "plate", "stand", 700 + k)
                place_on(ob, mm + off - d * 0.2 + np.array([0, 0, -0.4]), (0, 0, -1), tuple(-d[:2]) + (0,), 2.6)
            ring_light(f"{code} spark", hand, energy=6)
            fill = 90
        else:                             # the brood answers: Hunters rearing half out of every burrow
            CUR.clear(); CUR.update({"dim": True})
            for k, (mm, d) in enumerate(mouths):
                ob, _ = spider2(f"{code} emerging {k}", "hunter", ["plate", "shard", "bristle"][k % 3], "rear", 740 + k)
                place_on(ob, mm + off + d * 0.6 + np.array([0, 0, -0.5]), (0, 0, -1), tuple(-d[:2]) + (0,), 2.6)
            CUR.clear()
            ring_light(f"{code} guttering ring", hand, energy=25)
            fill = 450
    else:
        MOPT.clear()
        if variant == "open_core":
            MOPT.update({"core_green": True})
        m, spl = matron2(f"{code} matron", "chitin", "strike", seed, crack_lab=10,
                         cracked=2.6 if variant == "open_beam" else 1.6)
        MOPT.clear()
        m.location = (0, 4.0, 0); ground(m, 0.0)
        pr, hand = player(f"{code} player", (0.6, -4.0, 0), rot_z=0.15)
        ring_light(f"{code} overcharge", hand, energy=2200)
        bpy.context.view_layer.update()
        hp = np.array(hand.matrix_world.translation)
        tgt = np.array([0, 1.8, 3.0])
        Bm = Strands(f"{code} will beam")
        if variant == "open_beam":        # a heavy braided will beam
            for j in range(6):
                Bm.poly([hp, (hp + tgt) / 2 + rng.normal(size=3) * 0.22, tgt], PX * (7 - j))
        else:
            for j in range(3):
                Bm.poly([hp, (hp + tgt) / 2 + rng.normal(size=3) * 0.15, tgt], PX * (4 - j))
        Bm.build("ring")
        light(f"{code} green in the shell", (0, 1.2, 3.0), (0.08, 1.0, 0.18), 700 if variant == "open_core" else 400,
              cutoff=8)
        if variant == "open_close":       # close on the abdomen: glass shards and green sparks blowing off it
            Sh = Strands(f"{code} shards")
            for k in range(70):
                d = rng.normal(size=3); d[1] = -abs(d[1]); d /= np.linalg.norm(d)
                p = tgt + d * rng.uniform(1.6, 3.8)
                Sh.seg(p, p + rng.normal(size=3) * 0.12, PX * rng.choice([2.0, 3.0]))
            Sh.build("glass")
            Sp = Strands(f"{code} sparks")
            for k in range(60):
                d = rng.normal(size=3); d /= np.linalg.norm(d)
                p = tgt + d * rng.uniform(1.2, 3.0)
                Sp.seg(p, p + d * 0.1, PX)
            Sp.build("ash")
            cam_d, cam_h, look_z = 10, 5, 3.0
        fill = 900
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} fill", X + np.array([-14, -20, 18]), (0.45, 0.5, 0.7), fill, cutoff=60, kind="AREA", size=12,
          rot=(math.radians(45), 0, math.radians(-35)))
    cam = camera(f"Cam {code} {name}", X + np.array([0, -cam_d, cam_h]), X + np.array([0, 0, look_z]), lens=35)
    add_take(code, name, cam, "turntable", facts)


# =============================================================== v2.0109 (round 4): new pieces
# J (2026-10-19, coordinator 3's menu): "IMPROVEs + caves". 3 new versions of every v2.0108 IMPROVE (Matron takes
# skipped: the spider lair, placement A, cuts her), and the v2.0106 caves again: W1a entrance ("the entrances are too
# obvious or unappealing"), W1b Weave Gallery, W1c Hatchery lit so the room's shape reads.
# Rule held everywhere: "I would prefer you only see the webs once youre in danger": every cave is a CALM / DANGER pair.
import os
PASS = "v2.0109"
M.update({
    "web_calm": mat("web hidden", (0.03, 0.025, 0.02), 0.6, emit=(1.0, 0.6, 0.03), es=0.01, alpha=0.05),
    "silk_hot": mat("silk danger", (0.95, 0.6, 0.03), 0.4, emit=(1.0, 0.62, 0.03), es=1.1, alpha=0.9),
    "grass_live": mat("grass", (0.09, 0.2, 0.05), 0.9, speck=0.5),
    "leaf": mat("leaves", (0.05, 0.15, 0.04), 0.85, speck=0.7),
    "moss": mat("mossy cobble", (0.12, 0.15, 0.09), 0.85, speck=0.8),
    "flower": mat("pale flowers", (0.55, 0.45, 0.75), 0.6, emit=(0.6, 0.5, 0.9), es=0.05),
    "lure": mat("lure gold", (1.0, 0.7, 0.2), 0.2, metal=1.0, emit=(1.0, 0.62, 0.1), es=0.5),
    "wood": mat("old wood", (0.13, 0.08, 0.045), 0.85, speck=0.5),
    "pool": mat("fear pool", (0.5, 0.3, 0.0), 0.05, emit=(1.0, 0.55, 0.0), es=0.9, alpha=0.75),
    "wire_dim": mat("phantom wire dim", (0.6, 0.33, 0.01), 0.4, emit=(1.0, 0.55, 0.02), es=0.35),
    "ghost_mid": mat("phantom fill mid", (0.5, 0.35, 0.05), 0.2, emit=(1.0, 0.6, 0.05), es=0.3, alpha=0.22),
    "label": mat("label", (0.9, 0.9, 0.9), 0.5, emit=(0.95, 0.95, 0.95), es=0.6),
    "label_hot": mat("label danger", (1.0, 0.6, 0.05), 0.5, emit=(1.0, 0.6, 0.05), es=1.0),
})
SURF_LABELS = dict(CAVE_LABELS)
SURF_LABELS.update({6: "grass_live", 7: "dirt", 8: "log", 9: "leaf", 10: "flower", 11: "moss", 12: "lure", 13: "wood",
                    14: "pool"})


def label_text(name, text, loc, size=1.4, mk="label"):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"; cu.extrude = 0.05
    ob = bpy.data.objects.new(name, cu); ob.location = loc; ob.rotation_euler = (math.radians(80), 0, 0)
    cu.materials.append(M[mk])
    scene.collection.objects.link(ob)
    return ob


def pair(code, name, X, build_one, facts, sep, cam_d, cam_h, look_z=0.0, lens=24, label_z=None, kind="turntable"):
    """A calm / danger pair: the same place built twice side by side, calm on the left, danger on the right."""
    build_one(X + np.array([-sep, 0, 0]), f"{code} calm", True)
    build_one(X + np.array([sep, 0, 0]), f"{code} danger", False)
    lz = label_z if label_z is not None else cam_h * 0.55
    label_text(f"{code} label calm", "CALM", X + np.array([-sep, -sep * 0.2, lz]), size=sep * 0.12)
    label_text(f"{code} label danger", "DANGER", X + np.array([sep, -sep * 0.2, lz]), size=sep * 0.12, mk="label_hot")
    cam = camera(f"Cam {code} {name}", X + np.array([0, -cam_d, cam_h]), X + np.array([0, 0, look_z]), lens=lens)
    add_take(code, name, cam, kind, facts + "; left CALM (webs hidden, nothing out), right DANGER (webs lit, "
             "spiders out)" + ("; both turn" if kind == "turntable" else "; cut open at the front like a doll's house"))


def surface_chunk(R, Hh, ground_z, seed, grass=6):
    """A round lump of ground for a surface diorama: stone below, dirt, a grass skin, flat-ish top at ground_z."""
    G, xx, yy, zz, r, c, rng = chunk(R, Hh, seed)
    gh = (ground_z + smooth_noise(G.shape[:2], rng, 4) * 0.7).astype(int)[:, :, None]
    G[zz >= gh] = 0
    G[(G > 0) & (zz >= gh - 3)] = 7
    G[(G > 0) & (zz == gh - 1)] = grass
    return G, xx, yy, zz, r, c, rng, gh


def flowers(G, gh, rng, n, c, R, avoid=None):
    for k in range(n):
        a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(2.5, R - 2)
        x, y = int(c + math.cos(a) * rr), int(c + math.sin(a) * rr)
        if avoid is not None and avoid(x, y):
            continue
        z = int(gh[x, y, 0])
        if 0 < z < G.shape[2] and G[x, y, z - 1] in (6, 11) and G[x, y, z] == 0:
            G[x, y, z] = 10 if k % 3 else 9


def place_eyes(G, off, spots, code, seed, kind="hunter"):
    """Spiders sitting deep in holes so only their eyes catch the light."""
    CUR.clear(); CUR.update({"dim": True})
    for k, (p, belly, head) in enumerate(spots):
        sp = wall_spot(G, p, belly)
        if sp is None:
            continue
        ob, _ = spider2(f"{code} lurker {k}", kind, "plate", "stand", seed + k)
        place_on(ob, sp + off, belly, head, SPAN[kind])
    CUR.clear()


# --------------------------------------------------------------- W1a entrances: disguised and appealing
def build_entrance(X, code, calm, kind, seed):
    before = set(o.name for o in scene.objects)
    R, Hh = 14, 30
    G, xx, yy, zz, r, c, rng, gh = surface_chunk(R, Hh, 12, seed)
    solid0 = G > 0
    g0 = int(gh[int(c), int(c), 0])
    S = Strands(f"{code} silk")
    C0 = np.array([c, c, 0.0])
    if kind == "tree":
        # a huge old oak, still in leaf; the way in is a warm-lit arch between two roots, the shaft down its heart
        tc = np.array([c, c + 1.5])
        tr = np.hypot(xx + 0.5 - tc[0], yy + 0.5 - tc[1])
        G[(tr < 2.9) & (zz >= g0 - 1) & (zz < g0 + 10)] = 8
        G[(tr < 1.5) & (zz >= 3) & (zz < g0 + 8)] = 0            # hollow heart, down into the ground
        arch = (np.abs(xx + 0.5 - tc[0]) < 1.1) & (yy + 0.5 < tc[1]) & (zz >= g0) & \
            (zz < g0 + 2.6 - np.abs(xx + 0.5 - tc[0]) * 0.5)
        G[arch & (tr < 3.2)] = 0
        for k in range(7):                                    # roots spreading over the grass
            a = k / 7 * 2 * math.pi + 0.25
            if abs(math.sin(a) + 1) < 0.25:
                continue                                      # keep the arch clear
            p0 = np.array([tc[0] + math.cos(a) * 2.4, tc[1] + math.sin(a) * 2.4, g0 + 1.2])
            p1 = np.array([tc[0] + math.cos(a) * rng.uniform(5.5, 8), tc[1] + math.sin(a) * rng.uniform(5.5, 8), g0 - 0.2])
            capsule(G, p0, p1, 0.95, 8, only_empty=True)
        for k in range(5):                                    # boughs
            a = rng.uniform(0, 2 * math.pi)
            p0 = np.array([tc[0], tc[1], g0 + 8.5 + k * 0.5])
            capsule(G, p0, p0 + np.array([math.cos(a) * 5, math.sin(a) * 5, 2.5]), 0.7, 8)
        cn = smooth_noise(G.shape, rng, 3)
        canopy = ((xx + 0.5 - tc[0]) / 8) ** 2 + ((yy + 0.5 - tc[1]) / 8) ** 2 + ((zz + 0.5 - (g0 + 13)) / 4) ** 2 < 1 + cn * 0.25
        G[canopy & (G == 0) & (rng.random(G.shape) < 0.9)] = 9
        ellip(G, (tc[0], tc[1], 3.5), (3.5, 3.5, 2.2), 0)      # a den at the bottom of the shaft
        G[int(tc[0]), int(tc[1]), 1] = 12
        lure_at = np.array([tc[0], tc[1] - 2.0, g0 + 1.0])
        if not calm:
            S.web(np.array([tc[0], tc[1] - 2.3, g0 + 1.2]) - C0, (0, -1, 0), 1.3, spokes=9, rings=4,
                  rng=np.random.default_rng(seed))
            for k in range(14):
                a = rng.uniform(0, 2 * math.pi); z = rng.uniform(g0, g0 + 9)
                S.seg(np.array([tc[0] + math.cos(a) * 3.0, tc[1] + math.sin(a) * 3.0, z]) - C0,
                      np.array([tc[0] + math.cos(a + 0.5) * 3.0, tc[1] + math.sin(a + 0.5) * 3.0,
                                z + rng.uniform(-1.5, 1.5)]) - C0)
        avoid = lambda x, y: math.hypot(x - tc[0], y - tc[1]) < 3.4
        eyes = [(np.array([tc[0], tc[1], g0 - 3.0]), (1, 0, 0), (0, 0, 1)),
                (np.array([tc[0], tc[1], g0 - 6.0]), (-1, 0, 0), (0, 0, 1))]
    elif kind == "well":
        # an old overgrown well with a little roof, flowers round it; a gold glint far down is the lure
        wc = np.array([c, c])
        wr = np.hypot(xx + 0.5 - wc[0], yy + 0.5 - wc[1])
        G[(wr < 2.4) & (wr >= 1.3) & (zz >= g0) & (zz < g0 + 1)] = 11
        G[(wr < 1.3) & (zz >= 2) & (zz < g0 + 2)] = 0
        G[(wr < 2.4) & (wr >= 1.3) & (zz >= g0 - 6) & (zz < g0) & (G > 0)] = 11
        ix, iy = int(wc[0]), int(wc[1])
        for sx in (-2, 2):
            G[ix + sx, iy, g0 + 1:g0 + 5] = 13
        for dx in range(-3, 4):
            G[ix + dx, iy, g0 + 5] = 13
            for dy in (-1, 1):
                G[ix + dx, iy + dy, g0 + 4] = 13
        G[ix, iy, 2] = 12
        ellip(G, (wc[0], wc[1] + 2, 3.0), (3.0, 3.5, 1.8), 0)
        lure_at = np.array([wc[0], wc[1], 3.0])
        for k in range(12):                                    # ivy creeping over the stones
            a = rng.uniform(0, 2 * math.pi)
            q = (int(wc[0] + math.cos(a) * 2.6), int(wc[1] + math.sin(a) * 2.6), g0)
            if G[q] == 0:
                G[q] = 9
        if not calm:
            S.web(np.array([0, 0, g0 + 0.9]), (0, 0, 1), 1.4, spokes=10, rings=4, rng=np.random.default_rng(seed))
            for k in range(8):
                a = k / 8 * 2 * math.pi
                S.poly([np.array([math.cos(a) * 1.2, math.sin(a) * 1.2, g0 - 4.0 + j * 1.0 + rng.uniform(-0.2, 0.2)])
                        for j in range(5)])
            for sx in (-2, 2):
                S.seg(np.array([sx + 0.5, 0.5, g0 + 1]), np.array([sx * 0.25, 0.2, g0 + 5]))
        avoid = lambda x, y: math.hypot(x - wc[0], y - wc[1]) < 3.6
        eyes = [(np.array([wc[0], wc[1], g0 - 2.0]), (1, 0, 0), (0, 0, 1)),
                (np.array([wc[0], wc[1], g0 - 4.5]), (0, 1, 0), (0, 0, 1))]
    else:
        # a mossy hillside; a narrow cleft behind a curtain of hanging leaves, glowing warm like a lit lantern
        rise = np.clip((yy + 0.5 - (c - 1)) * 3.0, 0, 7)       # a steep mossy bank
        hillm = (zz < g0 + rise - 0.5) & (G == 0) & (r < R - 1)
        G[hillm] = 1
        G[hillm & (zz >= g0 + rise - 1.5)] = 6
        cleft = (np.abs(xx + 0.5 - c) < 0.9 + (zz - g0) * 0.05) & (yy + 0.5 > c - 1) & (yy + 0.5 < c + 7) & \
            (zz >= g0) & (zz < g0 + 4.5)
        G[cleft] = 0
        ellip(G, (c, c + 7, g0 + 1.5), (2.8, 2.6, 2.0), 0)
        walk_tunnel(G, (c, c + 7, g0 + 0.5), (0, 1, -0.7), 9, 1.1, rng, wander=0.15)
        for dx in range(-2, 3):                               # the leaf curtain over the cleft
            for k in range(int(rng.integers(2, 5))):
                q = (int(c + dx * 0.8), int(c - 1), g0 + 4 - k)
                if G[q] == 0:
                    G[q] = 9
        for k in range(30):
            x, y = int(c + rng.uniform(-6, 6)), int(c + rng.uniform(0, 8))
            col = np.nonzero(G[x, y, :])[0]
            if len(col):
                z = col[-1]
                if z < G.shape[2] - 1 and G[x, y, z] in (6, 1):
                    G[x, y, z + 1] = 9 if k % 2 else 10
        G[int(c), int(c + 7), g0] = 12
        lure_at = np.array([c, c + 6.5, g0 + 1.5])
        if not calm:
            S.web(np.array([0, -0.5, g0 + 2.0]), (0, 1, 0), 1.5, spokes=9, rings=4, rng=np.random.default_rng(seed))
            for dx in np.linspace(-1.6, 1.6, 7):          # the "vines" were silk all along
                S.seg(np.array([dx, -0.9, g0 + 4.6]), np.array([dx + rng.uniform(-0.2, 0.2), -0.9, g0 + rng.uniform(0.5, 2.5)]))
        avoid = lambda x, y: abs(x - c) < 2 and c - 2 < y < c + 8
        eyes = [(np.array([c, c + 7, g0 + 1.2]), (0, 1, 0), (0, 0, 1)),
                (np.array([c, c + 7, g0 + 1.2]), (1, 0, 0), (0, 0, 1))]
    flowers(G, gh, rng, 22, c, R, avoid)
    finish_cave(G, solid0, zz, rng, [])
    G[(G == 3) & (zz >= g0 - 1)] = 6 if calm else 3          # no silk-lined blocks on the surface while calm
    off = np.array([-c, -c, -float(g0)])
    G[(G == 4) & (zz >= g0 - 1)] = 6
    blocks(f"{code} ground", G, tuple(off), SURF_LABELS)
    S.build("silk_hot", loc=(0, 0, -float(g0)))
    if not calm:
        place_eyes(G, off, eyes, code, seed * 3)
        ob, _ = spider2(f"{code} hunter out", "hunter", "plate", "rear", seed + 5)
        ob.location = tuple(lure_at + off + np.array([3.2, -3.5, 0])); ob.rotation_euler[2] = 0.6; ground(ob, 0.0)
    warm = (1.0, 0.72, 0.35) if calm else (1.0, 0.5, 0.03)
    light(f"{code} lure glow", tuple(lure_at + off), warm, 220 if calm else 260, cutoff=10)
    pr, hand = player(f"{code} player", (-4.5, -7.0, 0.0), rot_z=-0.5)
    ring_light(f"{code} ring", hand, energy=300)
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} moon", X + np.array([-14, -18, 22]), (0.55, 0.65, 1.0), 5000, cutoff=70, kind="AREA", size=16,
          rot=(math.radians(40), 0, math.radians(-35)))


ENTRANCE_NOTE = {
    "tree": "a huge old oak still in leaf; the way in is a warm-lit arch between its roots, the shaft runs down its "
            "hollow heart to a den. Calm it looks like a shelter; danger: silk across the arch and up the trunk, eyes "
            "down the shaft, a Hunter rearing by the roots",
    "well": "an old overgrown well with a little wooden roof, mossy stones and flowers round it, a gold glint far down "
            "(the lure). Calm it is just a well; danger: a web lid over the mouth, silk ladders down the shaft, eyes "
            "on the walls, a Hunter beside it",
    "cleft": "a mossy hillside with a narrow cleft behind a curtain of hanging leaves, glowing warm inside like a lit "
             "lantern. Calm it looks like a cosy hollow; danger: the vines turn out to be silk, a web across the "
             "cleft, eyes inside, a Hunter at the door",
}


# --------------------------------------------------------------- W1b the Weave Gallery: three naves, no columns
def build_gallery(X, code, calm, kind, seed):
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = (24 if kind == "tiers" else 18), 34, 17
    xx, yy, zz = np.mgrid[0:nx, 0:ny, 0:nz]
    wob = smooth_noise((nx, ny, nz), rng, 3)
    cxm = nx / 2
    outer = ((np.abs(xx + 0.5 - cxm) / (nx / 2 - 0.5)) ** 4 + (np.abs(yy + 0.5 - ny / 2) / (ny / 2 - 0.5)) ** 4) < 1 - wob * 0.05
    G = outer.astype(np.int16)
    if kind == "winding":
        path = lambda y: cxm + 3.2 * math.sin((y - 4) * 0.2)
    else:
        path = lambda y: cxm
    pcx = np.vectorize(path)(yy + 0.5)
    w0 = 5.0 if kind == "tiers" else 3.6
    spring, top = 9.0, 14.0
    arch = np.where(zz + 0.5 < spring, w0, w0 * np.sqrt(np.clip(1 - ((zz + 0.5 - spring) / (top - spring)) ** 2, 0, 1)))
    rib = ((yy + 0.5) % 4.0) < 1.1      # spider-made ribs: arches standing in from the vault, never columns
    hollow = (np.abs(xx + 0.5 - pcx) < arch - rib * 0.9 * (zz > 3) + wob * 0.35) & (zz >= 2) & (yy >= 2) & (yy < ny - 2)
    G[hollow] = 0
    G[zz >= top + 2.5] = 0
    mouths = []
    if kind == "tiers":       # two tiers of balconies carved along the walls, burrows on each
        for zl in (5, 8):
            for sx in (-1, 1):
                ledge = (np.abs(xx + 0.5 - (cxm + sx * (w0 - 0.6))) < 1.2) & (zz == zl) & (yy >= 3) & (yy < ny - 3) & outer
                G[ledge] = 1
                for k in range(5):
                    y0 = 5 + k * 6 + (zl % 2) * 2
                    start = np.array([cxm + sx * (w0 + 0.3), y0, zl + 1.2])
                    walk_tunnel(G, start, (sx, 0, 0.05), 4, 0.9, rng, wander=0.15)
                    mouths.append((start, np.array([sx, 0, 0.0])))
    else:
        for k in range(12):
            y0 = rng.uniform(4, ny - 4); sx = rng.choice([-1, 1]); z0 = rng.uniform(3, 8)
            start = np.array([path(y0) + sx * (w0 + 0.2), y0, z0])
            walk_tunnel(G, start, (sx, 0, 0.1), 5, 1.0, rng, wander=0.2)
            mouths.append((start, np.array([sx, 0, 0.0])))
    G[(G > 0) & (zz < 2)] = 2
    finish_cave(G, outer, zz, rng, [m for m, d in mouths], collar=1.6)
    G[(xx + 0.5 < pcx - w0 * 0.55) & (zz >= 3)] = 0    # the near wall cut away (doll's house view)
    if calm:
        G[G == 3] = 1
    off = np.array([-cxm, -ny / 2, -2.0])
    blocks(f"{code} gallery", G, tuple(off), CAVE_LABELS)
    S = Strands(f"{code} silk")
    if not calm:
        for k, yw in enumerate(range(6, ny - 4, 8)):   # the stained-glass webs between the ribs
            cpt = off + np.array([path(yw), yw, 7.5])
            S.web(cpt, (0, 1, 0), w0 + 1.5, spokes=12, rings=7, rng=np.random.default_rng(seed + k), sag=0.3)
        if kind == "tiers":
            for k in range(10):
                y0 = rng.uniform(4, ny - 4)
                S.seg(off + np.array([cxm - w0 + 0.6, y0, 5.5 + 3 * (k % 2)]),
                      off + np.array([cxm + w0 - 0.6, y0 + rng.uniform(-2, 2), 8.5 - 3 * (k % 2)]))
        for k in range(14):
            y0 = rng.uniform(4, ny - 4); x0 = path(y0) + rng.uniform(-w0 + 1, w0 - 1)
            S.seg(off + np.array([x0, y0, 2.1]), off + np.array([x0 + rng.uniform(-1, 1), y0, spring + 3]))
    S.build("silk_hot")
    pv = off + np.array([path(9.0), 9.0, 2.0])
    pr, hand = player(f"{code} player", tuple(pv), rot_z=0)
    ring_light(f"{code} ring", hand, energy=700)
    if not calm:
        hs, spl = spider2(f"{code} hunter drop", "hunter", "plate", "drop", seed + 2)
        orient(hs, belly=(0, -1, 0), head=(0, 0, -1)); hs.location = tuple(pv + np.array([0.3, 2.2, 3.9]))
        T = Strands(f"{code} drop thread")
        bpy.context.view_layer.update()
        tp = hs.matrix_world @ Vector(spl)
        T.seg(np.array(tp), np.array(tp) + np.array([0, 0, 8])); T.build("silk_hot")
        items = [("hunter", ["plate", "bristle", "shard"][k % 3], "stand", m - d * 0.8, tuple(d), (0, 0, 1))
                 for k, (m, d) in enumerate(mouths[::2])]
        cave_spiders(G, off, items, rng, code)
    else:
        place_eyes(G, off, [(m - d * 0.4, tuple(d), (0, 0, 1)) for m, d in mouths[::3]], code, seed * 7, "broodling")
    for k in range(3):
        y0 = 8 + k * 9
        light(f"{code} vault glow {k}", tuple(off + np.array([path(y0), y0, spring])), (1.0, 0.6, 0.06),
              60 if calm else 130, cutoff=9)
    root = empty(f"{code} turn", X); root.rotation_euler[2] = math.pi / 2; adopt(root, before)
    light(f"{code} fill", X + np.array([-8, -30, 18]), (0.55, 0.6, 0.8), 16000, cutoff=90, kind="AREA", size=16,
          rot=(math.radians(60), 0, math.radians(-15)))


GALLERY_NOTE = {
    "ribs": "a straight nave 7 wide and 12 tall, its vault held by spider-made ribs arching overhead every 4 blocks "
            "(no columns; the ceiling between the ribs is cut away so you can see in); burrows in both walls. Danger: "
            "the webs between the ribs light up like stained glass, a Hunter drops on its thread over you",
    "winding": "the nave winds in an S so you never see far ahead, the ribs follow the bends, burrows in the walls. "
               "Danger: webs light across the bends, Hunters in the burrows, one drops on you",
    "tiers": "a wider nave with two tiers of balconies carved along the walls, five burrows on each balcony. Danger: "
             "threads strung balcony to balcony, webs between the ribs, Hunters on the balconies, one drops on you",
}


# --------------------------------------------------------------- W1c the Hatchery: lit so the room reads
def build_hatchery(X, code, calm, kind, seed):
    before = set(o.name for o in scene.objects)
    R, Hh = 13, 13
    G, xx, yy, zz, r, c, rng = chunk(R, Hh, seed)
    solid0 = G > 0
    ch = np.array([c, c, 3.0])
    dome = ((xx + 0.5 - c) / 10) ** 2 + ((yy + 0.5 - c) / 8.5) ** 2 + ((zz + 0.5 - 3) / 6.5) ** 2 < 1
    G[dome & (zz >= 3)] = 0
    G[(yy + 0.5 < c - 1.5) & (zz >= 3)] = 0              # the front cut open (doll's house view), the dome kept
    niches = []
    for row, zc in enumerate((4.0, 6.0)):              # a honeycomb of egg niches all round the wall
        nk = 16 if row == 0 else 12
        f_ = math.sqrt(max(1 - ((zc - 3) / 6.5) ** 2, 0))
        for k in range(nk):
            a = (k + 0.5 * row) / nk * 2 * math.pi
            p = np.array([c + math.cos(a) * (10 * f_ - 0.2), c + math.sin(a) * (8.5 * f_ - 0.2), zc])
            d = np.array([math.cos(a), math.sin(a), 0.0])
            ellip(G, p + d * 0.6, (1.0, 1.0, 0.9), 0)
            niches.append((p, d, a))
            if kind == "veins":                         # glowing vein rims round every niche
                u = np.array([-math.sin(a), math.cos(a), 0])
                for t_ in np.linspace(0, 2 * math.pi, 12, endpoint=False):
                    q = np.floor(p + d * 1.0 + u * math.cos(t_) * 1.4 + np.array([0, 0, math.sin(t_) * 1.3])).astype(int)
                    if np.all(q >= 0) and np.all(q < G.shape) and G[tuple(q)] > 0:
                        G[tuple(q)] = 4
    if kind == "veins":                                 # vein ribs running up the dome from the floor
        for k in range(10):
            a = k / 10 * 2 * math.pi
            for zc in np.arange(3, 8, 0.5):
                f_ = math.sqrt(max(1 - ((zc - 3) / 6.5) ** 2, 0))
                q = np.floor(np.array([c + math.cos(a) * (10 * f_ + 0.4), c + math.sin(a) * (8.5 * f_ + 0.4), zc])).astype(int)
                if np.all(q >= 0) and np.all(q < G.shape) and G[tuple(q)] > 0:
                    G[tuple(q)] = 4
    if kind == "pools":                                 # shallow pools of fear-light on the floor
        for k in range(5):
            a = k / 5 * 2 * math.pi + 0.4; rr = 4.5 if k else 0
            pc = np.array([c + math.cos(a) * rr, c + math.sin(a) * rr * 0.8])
            pm = (np.hypot(xx + 0.5 - pc[0], yy + 0.5 - pc[1]) < rng.uniform(1.6, 2.4)) & (zz == 2)
            G[pm & (G > 0)] = 14
    veins_keep = G == 4
    finish_cave(G, solid0, zz, rng, [])
    if kind != "veins":
        G[(G == 4) & (zz >= 3) & ~veins_keep] = 1
    if calm:
        G[G == 3] = 1
    off = np.array([-c, -c, -3.0])
    blocks(f"{code} hatchery", G, tuple(off), {**CAVE_LABELS, 14: "pool"})
    S = Strands(f"{code} silk")
    for i, (p, d, a) in enumerate(niches):
        if p[1] < c - 1.0:
            continue                                    # that niche was in the cut-away front
        loc = p + off + d * 0.15 - np.array([0, 0, 0.9])
        burst = (not calm) and i in (3, 11, 20)
        egg(f"{code} egg {i}", tuple(loc), (0, 0, a + math.pi / 2), cracked=0 if calm else 3 + (i % 3 == 0) * 2,
            burst=burst, seed=seed + i, scale=1.2)
        if kind == "sacs":
            light(f"{code} sac {i}", tuple(loc + np.array([0, 0, 0.75]) - d * 0.6), (1.0, 0.6, 0.06),
                  14 if calm else 22, cutoff=4)
        if not calm:
            S.seg(loc + np.array([0, 0, 1.3]), off + ch + np.array([0, 0, 4.6]) + rng.normal(size=3) * 1.2)
    if not calm:
        for k in range(4):
            S.web(off + ch + np.array([math.cos(k * 1.6) * 5, math.sin(k * 1.6) * 4, 3.4]),
                  (math.cos(k * 1.6), math.sin(k * 1.6), 0.2), 1.6, spokes=8, rings=4,
                  rng=np.random.default_rng(seed + 40 + k))
        for b in range(9):
            a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(2, 6.5)
            bs, _ = spider2(f"{code} broodling {b}", "broodling", "plate", "stand", seed + 60 + b)
            bs.location = (math.cos(a) * rr, math.sin(a) * rr * 0.8, 0); bs.rotation_euler[2] = rng.uniform(0, 6.3)
            ground(bs, 0.0)
    S.build("silk_hot")
    pr, hand = player(f"{code} player", (-3.0, -1.5, 0), rot_z=-0.3)
    ring_light(f"{code} ring", hand, energy=450)
    if kind == "sacs":
        light(f"{code} bounce", (0, 0, 1.0), (1.0, 0.6, 0.1), 160, cutoff=12)
    elif kind == "veins":
        light(f"{code} vein glow", (0, 0, 2.5), (1.0, 0.55, 0.05), 220, cutoff=12)
    else:
        for k in range(5):
            a = k / 5 * 2 * math.pi + 0.4; rr = 4.5 if k else 0
            light(f"{code} pool {k}", (math.cos(a) * rr, math.sin(a) * rr * 0.8, 0.4), (1.0, 0.55, 0.03), 90, cutoff=8)
    root = empty(f"{code} turn", X); adopt(root, before)
    light(f"{code} fill", X + np.array([-6, -22, 12]), (0.55, 0.6, 0.8), 1500, cutoff=70, kind="AREA", size=14,
          rot=(math.radians(65), 0, math.radians(-15)))


HATCH_NOTE = {
    "sacs": "a low dome with two rows of egg niches all round its wall (28 sacs); every sac has its own soft light and a "
            "warm bounce off the floor shows the dome's curve. Danger: the sacs crack and burst, silk strung niche to "
            "niche, broodlings on the floor",
    "veins": "the same dome traced in glowing gold veins: a rim round every niche and ribs running up from the floor, "
             "so the honeycomb's shape reads even far off. Danger: sacs crack, webs, broodlings out",
    "pools": "shallow pools of yellow fear-light on the floor light the honeycomb from below, five pools spread round "
             "the dome. Danger: sacs crack, webs over the room, broodlings out",
}


# --------------------------------------------------------------- Lights out, round 4: the lair's construct spider
CONSTRUCT_SCALE = 2.5


def construct_spider(name, pose, seed, cracks=0, glen=40):
    """The yellow fear construct spider from the spider lair (stand-in: the Hunter build at 3x with a spiked
    dread-armour ridge), turned to face the player (head toward -y)."""
    CUR.clear(); CUR.update({"dim": True, "ridge": 7, "gcracks": cracks, "glen": glen})
    ob, spl = spider2(name, "hunter", "plate", pose, seed)
    CUR.clear()
    ob.scale = (CONSTRUCT_SCALE,) * 3
    ob.rotation_euler[2] = math.pi
    return ob


def bbox_w(ob):
    bpy.context.view_layer.update()
    P = np.array([list(ob.matrix_world @ Vector(c)) for c in ob.bound_box])
    return P.min(0), P.max(0)


def build_L4(code, name, X, variant, seed, facts):
    before = set(o.name for o in scene.objects)
    G, off, mouths, c = small_arena(code, seed)
    rng = np.random.default_rng(seed)
    cam_d, cam_h, look_z, fill, kind, spin_it = 24, 13, 2.2, 600, "turntable", True
    if variant.startswith("beam"):
        cam_d, cam_h, look_z = 15, 7.5, 2.4
    cam_loc = look = None
    if not variant.startswith(("beam", "close")):
        sp = construct_spider(f"{code} construct", "rear", seed)
        sp.location = (0, 4.5 if variant != "dark_bubble" else 1.4, 0); ground(sp, 0.0)
        lo, hi = bbox_w(sp)
        hc = np.array([0, lo[1] + 1.2, hi[2] * 0.62])      # its head, facing the player
        light(f"{code} eyes", tuple(hc - np.array([0, 1.0, 0])), (1.0, 0.55, 0.03), 90, cutoff=6)
        pr, hand = player(f"{code} player", (0, -5.5, 0), rot_z=0)
        ring_e = 25
        if variant in ("scream_flat", "scream_broken", "scream_lit"):
            S = Strands(f"{code} scream rings")
            radii = (1.0, 1.8, 2.7, 3.7, 4.8, 6.0) if variant == "scream_broken" else (1.4, 2.4, 3.6, 5.0)
            for k, rr in enumerate(radii):
                pts = [hc + np.array([math.cos(a) * rr, -0.7 * k, math.sin(a) * rr * 0.8]) for a in np.linspace(0, 2 * math.pi, 49)]
                if variant == "scream_broken":
                    for j in range(0, 48, 4):
                        S.poly(pts[j:j + 3], PX * 3)
                else:
                    S.poly(pts, PX * (3.5 - 0.5 * k))
            if variant == "scream_flat":                  # the same scream rolling across the floor as a shockwave
                for k, rr in enumerate((2.0, 3.8, 5.8, 8.0)):
                    S.poly([np.array([math.cos(a) * rr, 4.5 + math.sin(a) * rr, 0.08]) for a in np.linspace(0, 2 * math.pi, 61)],
                           PX * (3 - 0.5 * k))
            S.build("static")
            if variant == "scream_broken":                # your ring guttering: green sparks dropping off it
                bpy.context.view_layer.update()
                hp = np.array(hand.matrix_world.translation)
                Sp = Strands(f"{code} guttering sparks")
                for k in range(30):
                    p = hp + rng.normal(size=3) * 0.25 - np.array([0, 0, rng.uniform(0, 1.6)])
                    Sp.seg(p, p + np.array([0, 0, PX * 2]), PX * 1.5)
                Sp.build("ash")
            if variant == "scream_lit":
                fill, ring_e = 15, 4
                light(f"{code} scream light", tuple(hc + np.array([0, -2.5, 0])), (1.0, 0.6, 0.05), 160, cutoff=10)
            cam_d, cam_h, look_z = 20, 10, 2.6
        if variant == "scream_cone":                      # the scream thrown at you as a cone of static
            S = Strands(f"{code} scream cone")
            for k in range(240):
                f_ = rng.uniform(0.05, 1.0); a = rng.uniform(0, 2 * math.pi)
                p = hc + np.array([math.cos(a) * f_ * 2.6, -f_ * 9.0, math.sin(a) * f_ * 1.8])
                S.seg(p, p + np.array([0, -0.2, 0]), PX * rng.choice([1.5, 2.5]))
            S.build("static")
            cam_d, cam_h, look_z = 20, 10, 2.6
        if variant.startswith(("scream", "dark")):
            spots = list(mouths)
            if variant == "dark_eyes":                    # eyes in every burrow and all round the walls too
                for k in range(10):
                    a = rng.uniform(0, 2 * math.pi)
                    spots.append((np.array([c + math.cos(a) * 10.5, c + math.sin(a) * 10.5, 7.6]),
                                  np.array([math.cos(a), math.sin(a), 0.0])))
            for k, (mm, d) in enumerate(spots):
                ob, _ = spider2(f"{code} eyes {k}", "hunter", "plate", "stand", 700 + k)
                place_on(ob, mm + off - d * 0.2 + np.array([0, 0, -0.4]), (0, 0, -1), tuple(-d[:2]) + (0,), 2.6)
        if variant == "dark_eyes":
            fill, ring_e = 40, 6
        elif variant == "dark_bubble":                  # the ring a spark: it lights a 2-block bubble, and a leg is in it
            fill, ring_e = 30, 0
            light(f"{code} spark bubble", (0.25, -5.2, 1.9), (0.08, 1.0, 0.18), 45, cutoff=2.6)
        elif variant.startswith("brood"):
            CUR.clear(); CUR.update({"dim": True})
            if variant == "brood_spill":               # Hunters rear out of the burrows, broodlings pour across the floor
                for k, (mm, d) in enumerate(mouths):
                    ob, _ = spider2(f"{code} emerging {k}", "hunter", ["plate", "shard", "bristle"][k % 3], "rear", 740 + k)
                    place_on(ob, mm + off + d * 0.6 + np.array([0, 0, -0.5]), (0, 0, -1), tuple(-d[:2]) + (0,), 2.6)
                for k in range(12):
                    a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(3, 8)
                    ob, _ = spider2(f"{code} broodling {k}", "broodling", "plate", "stand", 760 + k)
                    ob.location = (math.cos(a) * rr, -1 + math.sin(a) * rr, 0)
                    ob.rotation_euler[2] = math.atan2(-5.5 - ob.location.y, -ob.location.x) - math.pi / 2
                    ground(ob, 0.0)
            elif variant == "brood_drop":              # they answer from above: Hunters dropping on threads round you
                T = Strands(f"{code} threads")
                for k in range(8):
                    a = k / 8 * 2 * math.pi
                    ob, spl = spider2(f"{code} dropper {k}", "hunter", ["plate", "shard", "bristle"][k % 3], "drop", 780 + k)
                    orient(ob, belly=(-math.cos(a), -math.sin(a), 0), head=(0, 0, -1))
                    ob.location = (math.cos(a) * 3.2, -5.5 + math.sin(a) * 3.2, 2.2 + (k % 3) * 0.6)
                    bpy.context.view_layer.update()
                    tp = ob.matrix_world @ Vector(spl)
                    T.seg(np.array(tp), np.array(tp) + np.array([0, 0, 9]))
                T.build("silk_hot")
            else:                                      # a closing ring: Hunters out and walking in on you
                for k in range(9):
                    a = k / 9 * 2 * math.pi
                    ob, _ = spider2(f"{code} closer {k}", "hunter", ["plate", "shard", "bristle"][k % 3], "stand", 800 + k)
                    ob.location = (math.cos(a) * 4.4, -5.5 + math.sin(a) * 4.4, 0)
                    ob.rotation_euler[2] = a + math.pi / 2
                    ground(ob, 0.0)
            CUR.clear()
        if ring_e:
            ring_light(f"{code} guttering ring", hand, energy=ring_e)
    else:
        cracks = {"beam_rod": 12, "beam_helix": 10, "beam_blaze": 22}.get(variant, 16)
        sp = construct_spider(f"{code} construct", "rear" if variant == "close_low" else "stand", seed, cracks=cracks,
                              glen=45 if variant == "beam_blaze" else 25)
        sp.location = (0, 4.0, 0); ground(sp, 0.0)
        lo, hi = bbox_w(sp)
        tgt = np.array([0, lo[1] + (hi[1] - lo[1]) * 0.42, hi[2] * 0.5])
        pr, hand = player(f"{code} player", (0.6, -4.0, 0), rot_z=0.15)
        ring_light(f"{code} overcharge", hand, energy=2200)
        bpy.context.view_layer.update()
        hp = np.array(hand.matrix_world.translation)
        Bm = Strands(f"{code} will beam")
        axis_ = tgt - hp; L_ = np.linalg.norm(axis_); axis_ /= L_
        u_ = np.cross(axis_, (0, 0, 1)); u_ /= np.linalg.norm(u_); v_ = np.cross(axis_, u_)
        if variant == "beam_rod":                      # one fat straight rod of will
            for du in np.linspace(-1.5, 1.5, 4):
                for dv in np.linspace(-1.5, 1.5, 4):
                    Bm.seg(hp + (u_ * du + v_ * dv) * PX, tgt + (u_ * du + v_ * dv) * PX * 1.6, PX * 1.2)
        elif variant == "beam_blaze":                  # heavy braided beam, the cracks blazing
            for j in range(6):
                Bm.poly([hp, (hp + tgt) / 2 + rng.normal(size=3) * 0.22, tgt], PX * (7 - j))
            for k in range(3):
                light(f"{code} crack blaze {k}", tuple(tgt + rng.normal(size=3) * np.array([1.4, 1.4, 0.9])),
                      (0.08, 1.0, 0.18), 160, cutoff=5)
        else:                                          # three strands braided round each other
            for j in range(3):
                pts = []
                for f_ in np.linspace(0, 1, 40):
                    a = f_ * 6 * math.pi + j * 2 * math.pi / 3
                    pts.append(hp + axis_ * L_ * f_ + (u_ * math.cos(a) + v_ * math.sin(a)) * 0.16)
                Bm.poly(pts, PX * 2.5)
            Bm.seg(hp, tgt, PX * 2)
        Bm.build("ring")
        light(f"{code} green in the shell", tuple(tgt), (0.08, 1.0, 0.18), 450, cutoff=8)
        if variant.startswith("close"):                # shards and green sparks blowing off the shell
            Sh = Strands(f"{code} shards")
            for k in range(90):
                d = rng.normal(size=3); d /= np.linalg.norm(d)
                p = tgt + d * rng.uniform(1.6, 4.5)
                if variant == "close_low":
                    p[2] = rng.uniform(0.2, hi[2] + 2)
                Sh.seg(p, p + rng.normal(size=3) * 0.14, PX * rng.choice([2.0, 3.0]))
            Sh.build("glass")
            Sp = Strands(f"{code} sparks")
            for k in range(70):
                d = rng.normal(size=3); d /= np.linalg.norm(d)
                p = tgt + d * rng.uniform(1.2, 3.4)
                Sp.seg(p, p + d * 0.1, PX)
            Sp.build("ash")
            if variant == "close_side":
                cam_loc, look = np.array([10.5, 0.5, 4.0]), tgt
            elif variant == "close_shoulder":
                cam_loc, look = np.array([1.6, -6.6, 2.6]), tgt
                spin_it, kind = False, "static"
            else:
                cam_loc, look = np.array([2.5, -3.5, 0.35]), tgt + np.array([0, 0, 1.5])
        fill = 900
    root = empty(f"{code} turn", X)
    if spin_it:
        spin(root)
    adopt(root, before)
    light(f"{code} fill", X + np.array([-14, -20, 18]), (0.45, 0.5, 0.7), fill, cutoff=60, kind="AREA", size=12,
          rot=(math.radians(45), 0, math.radians(-35)))
    if cam_loc is not None:
        cam = camera(f"Cam {code} {name}", X + cam_loc, X + look, lens=30)
    else:
        cam = camera(f"Cam {code} {name}", X + np.array([0, -cam_d, cam_h]), X + np.array([0, 0, look_z]), lens=35)
    add_take(code, name, cam, kind, facts)


# --------------------------------------------------------------- the takes (39)
SPIDER_ROWS = [   # (code, name, kind, style, opt, facts)
    ("W2a3c1", "Broodlings: mane, thick collar", "broodling", "bristle",
     {"mane": True, "bristles": 40, "blen": (1.2, 2.2), "brad": 0.4, "mane_r": 0.9},
     "from W2a3c; a dense short collar of spines round the waist, like a ruff"),
    ("W2a3c2", "Broodlings: mane, swept back", "broodling", "bristle",
     {"mane": True, "bristles": 12, "blen": (3.5, 5.5), "sweep": 2.6, "lift": 0.8},
     "from W2a3c; a dozen long spines swept back over the abdomen like a crest"),
    ("W2a3c3", "Broodlings: mane, gold tips", "broodling", "bristle",
     {"mane": True, "bristles": 18, "blen": (2.0, 3.5), "tip_lab": 11, "dim": True},
     "from W2a3c; the same mane with polished-gold tips and a dimmed body, so the ring of tips reads"),
    ("W2d2a1", "Dread Phantom: heavy wire, dark core", "phantom", "wire_x", {"thick": 1, "core": 0.6},
     "from W2d2a; the heavy outline round a dark spider body you can just see inside"),
    ("W2d2a2", "Dread Phantom: heavy wire, gold bands", "phantom", "wire_x", {"thick": 1, "bands": 2.0},
     "from W2d2a; the heavy outline in alternating bands of yellow and gold light"),
    # rev 2 (J on rev 1: "pure yellow i cant see the detail"): the wire dimmed to a third and a dark body inside it,
    # so the legs and joints read against black instead of one glow
    ("W2d2a3", "Dread Phantom: heavier wire, big eyes", "phantom", "wire_x",
     {"thick": 1, "eye_big": True, "core": 0.6, "wire_mat": "wire_dim"},
     "from W2d2a; rev 2: the heavy outline dimmed to a third, a dark body inside it, the swollen eyes the brightest thing"),
    ("W2d2b1", "Dread Phantom: faint fill, stronger", "phantom", "wire_x", {"fill": "ghost_mid"},
     "from W2d2b; the fill a little stronger so the body's shape reads between the lines"),
    ("W2d2b2", "Dread Phantom: fill in the abdomen", "phantom", "wire_x", {"fill": "ghost_mid", "fill_part": "abd"},
     "from W2d2b; only the abdomen filled with light, the head and legs outline only"),
    ("W2d2b3", "Dread Phantom: faint fill, shadow inside", "phantom", "wire_x", {"fill": "ghost_faint", "core": 0.55},
     "from W2d2b; the faint fill with a dark spider shadow inside it"),
    ("W2d2c1", "Dread Phantom: long dashes", "phantom", "wire_x", {"dash": (6, 4)},
     "from W2d2c; longer dashes with short gaps, still drawing itself"),
    ("W2d2c2", "Dread Phantom: heavy dashes", "phantom", "wire_x", {"dash": (4, 2), "thick": 1},
     "from W2d2c; the dashed outline drawn heavy"),
    ("W2d2c3", "Dread Phantom: scan dashes, faint fill", "phantom", "wire_x",
     {"dash": (3, 2), "dash_axis": "z", "fill": "ghost_faint"},
     "from W2d2c; the outline broken into level rows like a scan, over a faint body"),
]
L_ROWS = [
    ("W3c1a1", "Lights out: scream, floor shockwave", "scream_flat",
     "from W3c1a; the lair's yellow construct spider screams (the Matron is cut): rings of static from its head and "
     "the same rings rolling out across the floor; eyes in every burrow"),
    ("W3c1a2", "Lights out: scream, broken rings", "scream_broken",
     "from W3c1a; six broken rings of static, and your ring guttering, green sparks dropping off it"),
    ("W3c1a3", "Lights out: scream, cone of static", "scream_cone",
     "from W3c1a; the scream thrown at you as a cone of yellow static"),
    ("W3c1b1", "Lights out: true dark, eyes everywhere", "dark_eyes",
     "from W3c1b; almost no light: eyes in every burrow and all round the walls, the construct spider's eyes, your "
     "ring a spark"),
    ("W3c1b2", "Lights out: true dark, the spark's bubble", "dark_bubble",
     "from W3c1b; your ring lights a 2-block bubble round you, and the construct spider is right at its edge"),
    ("W3c1b3", "Lights out: true dark, lit by the scream", "scream_lit",
     "from W3c1b; the only light is its scream: rings of static lighting the floor and its face"),
    ("W3c1c1", "Lights out: the brood answers, spilling out", "brood_spill",
     "from W3c1c; Hunters rear out of every burrow and broodlings pour across the floor toward you"),
    ("W3c1c2", "Lights out: the brood answers from above", "brood_drop",
     "from W3c1c; eight Hunters drop on their threads all round you"),
    ("W3c1c3", "Lights out: the brood answers, closing in", "brood_ring",
     "from W3c1c; nine Hunters out of the burrows, walking in on you in a ring"),
    ("W3c3a1", "Lights out: shell opens, solid rod", "beam_rod",
     "from W3c3a; one fat straight rod of will light into the construct spider, green cracks spreading through its shell"),
    ("W3c3a2", "Lights out: shell opens, braided beam", "beam_helix",
     "from W3c3a; three beams braided round each other, green cracks through the shell"),
    ("W3c3a3", "Lights out: shell opens, cracks blazing", "beam_blaze",
     "from W3c3a; the heavy braided beam, long green cracks blazing all over the shell, green light spilling out"),
    ("W3c3c1", "Lights out: shell opens, close from the side", "close_side",
     "from W3c3c; close from the side as shards and green sparks blow off the shell"),
    ("W3c3c2", "Lights out: shell opens, over your shoulder", "close_shoulder",
     "from W3c3c; from over your shoulder, down the braided beam into the cracking shell (one still)"),
    ("W3c3c3", "Lights out: shell opens, low from the floor", "close_low",
     "from W3c3c; low from the floor looking up at it rearing, shards raining down"),
]
FUNNEL_ROWS = [
    ("W4ba1", "Funnel hollow: spiral ramp", {"spiral": 2.0, "tz": [20, 15, 10, 5], "trad": [16.0, 12.5, 9.0, 5.5],
                                             "web_r": 12.5, "spokes": 36, "rings": 13},
     "from W4ba; one terrace winding down round the hollow twice like a ramp, the deep funnel web over it"),
    ("W4ba2", "Funnel hollow: deep shaft", {"tz": [21, 17, 13, 9, 5], "trad": [16.0, 12.0, 8.5, 6.0, 4.0],
                                            "web_r": 11.6, "web_z": 17.3, "spokes": 36, "rings": 15, "hole": 3.2},
     "from W4ba; five steps narrowing fast into a wide, deep nest shaft"),
    ("W4ba3", "Funnel hollow: burrowed terraces", {"tz": [20, 15, 10, 5], "trad": [16.0, 12.5, 9.0, 5.5],
                                                   "web_r": 12.5, "spokes": 36, "rings": 13, "mouths": 6},
     "from W4ba; the deep hollow with twice the burrows, six on every terrace"),
]


def funnel_pair(X, code, name, v, facts):
    def one(Xp, nm, calm):
        vv = dict(v); vv.update({"no_take": True, "calm": calm, "web_mk": "web_calm" if calm else "silk_hot", "web_w": 1.0 if calm else 2.5})
        build_W4b(Xp, nm, vv)
    pair(code, name, X, one, facts, 20.0, 56, 34, -4, label_z=14)


BUILDS = []   # (code, builder)
for i, (code, name, kind, style, opt, facts) in enumerate(SPIDER_ROWS):
    BUILDS.append((code, lambda X, a=(code, name, kind, style, opt, facts), i=i:
                   build_row(a[0], a[1], X, a[2], a[3], 11 + i, a[5], a[4])))
for i, (code, name, variant, facts) in enumerate(L_ROWS):
    BUILDS.append((code, lambda X, a=(code, name, variant, facts), i=i: build_L4(a[0], a[1], X, a[2], 91 + i, a[3])))
for code, name, v, facts in FUNNEL_ROWS:
    BUILDS.append((code, lambda X, a=(code, name, v, facts): funnel_pair(X, *a)))
ENT_NAMES = {"tree": "Entrance: the hollow oak", "well": "Entrance: the old well", "cleft": "Entrance: the lit cleft"}
for k, kind in enumerate(("tree", "well", "cleft")):
    code = f"W1a{k + 1}"
    BUILDS.append((code, lambda X, code=code, kind=kind, k=k: pair(
        code, ENT_NAMES[kind], X, lambda Xp, n_, calm: build_entrance(Xp, n_, calm, kind, 120 + k * 10),
        "from W1a (\"the entrances are too obvious or unappealing\"): " + ENTRANCE_NOTE[kind], 16.0, 54, 22, 2.0,
        label_z=21)))
GAL_NAMES = {"ribs": "Weave Gallery: ribbed nave", "winding": "Weave Gallery: winding nave", "tiers": "Weave Gallery: balconies"}
for k, kind in enumerate(("ribs", "winding", "tiers")):
    code = f"W1b{k + 1}"
    BUILDS.append((code, lambda X, code=code, kind=kind, k=k: pair(
        code, GAL_NAMES[kind], X, lambda Xp, n_, calm: build_gallery(Xp, n_, calm, kind, 150 + k * 10),
        "from W1b: " + GALLERY_NOTE[kind], 19.0, 62, 20, 6.0, label_z=19, kind="static")))
HAT_NAMES = {"sacs": "Hatchery: lit by the sacs", "veins": "Hatchery: vein-traced dome", "pools": "Hatchery: fear-light pools"}
for k, kind in enumerate(("sacs", "veins", "pools")):
    code = f"W1c{k + 1}"
    BUILDS.append((code, lambda X, code=code, kind=kind, k=k: pair(
        code, HAT_NAMES[kind], X, lambda Xp, n_, calm: build_hatchery(Xp, n_, calm, kind, 180 + k * 10),
        "from W1c (the egg sacs glow nicely, the room was too dark to read): " + HATCH_NOTE[kind], 14.5, 44, 13, 2.0,
        label_z=11, kind="static")))
ONLY = [s for s in os.environ.get("DW_ONLY", "").split(",") if s]    # quick tests: DW_ONLY=W1a1,W3c1b2
for i, (code, b) in enumerate(BUILDS):
    if ONLY and code not in ONLY:
        continue
    b(np.array([i * GAP, 0.0, 0.0]))

scene.camera = bpy.data.objects[TAKES[0][2]]
scene["dw_takes"] = repr(TAKES)
print(f"[{PASS}] built {len(TAKES)} takes, {len(scene.objects)} objects")
