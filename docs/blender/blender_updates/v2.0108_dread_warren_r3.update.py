# Pass v2.0108: Dread Warren round 3 (Trials; PC Blender chat, 2026-10-19).
# Why: J rated v2.0107 on the site: Hunter W2b1-3 and Weaver W2c1-3 KEEP (handed off:
#   docs/handoff/2026-10-19-dread-warren-spiders/), W2d3 W3c2 W4a DROP, and 11 IMPROVE with no notes; then
#   "Hand off + improve all" (star). An IMPROVE with no note = 3 new labelled variations, built differently (a/b/c).
# Takes (each its own camera, 220 blocks apart; all turn):
#   W2a1a-c, W2a2a-c, W2a3a-c Broodlings; W2d1a-c, W2d2a-c Dread Phantom (five poses each);
#   W3a2a-c, W3a3a-c the Matron (four poses each); W3c1a-c, W3c3a-c Lights out; W4ba-c funnel hollow, W4ca-c crevice.
# Rule held: ceiling walking is ON HOLD (Stormie's Spiders test first): walls and drops only.
# Builds the whole scene from nothing (globals bpy, np, FOLDER); the renderer saves it as trials/dread_warren_r3.blend.
import math
import bpy
import numpy as np

PASS = "v2.0108"
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
                waist = (ceph + abd) / 2
                pts = pts[np.linalg.norm(pts + 0.5 - waist, axis=1) < max(cx_, ax_) * 1.1]
            nb = opt.get("bristles", 70 if kind != "broodling" else 30)
            for k in rng.choice(len(pts), size=min(len(pts), nb), replace=False):
                p = pts[k] + 0.5
                cc = abd if np.linalg.norm(p - abd) < np.linalg.norm(p - ceph) + 2 else ceph
                d = p - cc; d /= np.linalg.norm(d) + 1e-9
                capsule(G, p, p + d * rng.uniform(*opt.get("blen", (1.6, 3.4))) + np.array([0, -0.8, 0]),
                        opt.get("brad", 0.45), 2, only_empty=True)
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
    for k, (z0, r0) in enumerate(zip(tz, trad)):
        G[(rr < r0) & (zz >= z0)] = 0
        G[(rr >= r0) & (rr < r0 + v.get("lip", 1.6)) & (zz >= z0) & (zz < z0 + v.get("liph", 2))] = 0   # undercut lip
    G[(r < 2.6 + wob[:, :, 0][:, :, None] * 0.4) & (zz >= 1)] = 0          # the nest hole
    G[zz >= 22] = 0
    mouths = []
    for k, (z0, r0) in enumerate(zip(tz, trad)):
        for j in range(3 if k < 3 else 2):
            a = j / 3 * 2 * math.pi + k * 0.9 + rng.uniform(-0.2, 0.2)
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
            z = (15.4 + 0.2) * (1 - f) + 2.5 * f - math.sin(f * math.pi) * 1.6
            pts.append(off + np.array([c + math.cos(a) * rad, c + math.sin(a) * rad, z]))
        S.poly(pts, PX * 1.5)
    for f in np.linspace(0.08, 0.95, v.get("rings", 9)):
        pts = []
        for j in range(nsp + 1):
            a = j / nsp * 2 * math.pi
            rad = web_r * (1 - f) + 2.3 * f
            z = 15.6 * (1 - f) + 2.5 * f - math.sin(f * math.pi) * 1.6
            pts.append(off + np.array([c + math.cos(a) * rad, c + math.sin(a) * rad, z]))
        S.poly(pts, PX)
    for m, d in mouths[::2]:
        S.web(m + off - d * 0.2, d, 1.3, spokes=7, rings=3, rng=np.random.default_rng(int(m[0] * 10)))
    if v.get("sheets"):      # sheet webs laid flat over the terrace floors
        for k, (z0, r0) in enumerate(zip(tz[:3], trad[:3])):
            for j in range(3):
                a = j / 3 * 2 * math.pi + k * 1.3 + 0.5
                rm = (r0 + (trad[k + 1] if k + 1 < len(trad) else 2.5)) / 2
                S.web(off + np.array([c + math.cos(a) * rm, c + math.sin(a) * rm, z0 + 0.15]), (0, 0, 1),
                      1.6 + 0.3 * j, spokes=9, rings=4, rng=np.random.default_rng(300 + k * 3 + j))
    S.build()
    items = []
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
    cave_spiders(G, off, items, rng, code)
    w, spl = spider2(f"{code} weaver drop", "weaver", "bristle", "drop", 77)
    orient(w, belly=(0, -1, 0), head=(0, 0, -1)); w.location = (6.0, 5.0, -12 + 15.5)
    bpy.context.view_layer.update()
    top = w.matrix_world @ Vector(spl)
    S2 = Strands(f"{code} weaver thread"); S2.seg(np.array(top), np.array(top) + np.array([0, 0, 9])); S2.build()
    light(f"{code} nest glow", (0, 0, -12 + 3.0), (1.0, 0.55, 0.03), 260, cutoff=12)
    pr, hand = player(f"{code} player", (-8.5, -9.5, -12 + 19), rot_z=-0.75)
    ring_light(f"{code} ring", hand, energy=750)
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} fill", X + np.array([-20, -28, 28]), (0.55, 0.6, 0.8), 22000, cutoff=90, kind="AREA", size=18,
          rot=(math.radians(45), 0, math.radians(-35)))
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
            cam_d, cam_h, look_z = 17, 8, 3.0
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


# --------------------------------------------------------------- the takes (33: three new versions of each IMPROVE)
SPIDER_ROWS = [   # (code, name, kind, style, opt, facts)
    ("W2a1a", "Broodlings: plate, dimmed", "broodling", "plate", {"dim": True},
     "from W2a1; the same plate build with the glow turned right down, so the black core leads and only eyes burn"),
    ("W2a1b", "Broodlings: plate, glass belly", "broodling", "plate", {"glass_abd": True, "dim": True},
     "from W2a1; a see-through glass abdomen with a glowing yolk inside, dim plates on the head"),
    ("W2a1c", "Broodlings: plate, two-tone", "broodling", "plate", {"twotone": True, "band": 3.5, "dim": True},
     "from W2a1; wider dim yellow bands alternating with polished gold plates"),
    ("W2a2a", "Broodlings: shard, clear glass", "broodling", "shard", {"clear": True},
     "from W2a2; clearer, thinner glass so the dark core inside shows"),
    ("W2a2b", "Broodlings: shard, crystal cluster", "broodling", "shard", {"spines": 12},
     "from W2a2; a cluster of crystal spines all over the back"),
    ("W2a2c", "Broodlings: shard, eggshell", "broodling", "shard", {"eggshell": True, "clear": True},
     "from W2a2; fresh out of the egg, pieces of the glass eggshell still stuck to its back"),
    ("W2a3a", "Broodlings: bristle, few long spines", "broodling", "bristle",
     {"bristles": 9, "blen": (3.0, 5.0), "brad": 0.5}, "from W2a3; nine long spines instead of fuzz"),
    ("W2a3b", "Broodlings: bristle, leg tufts", "broodling", "bristle", {"bristles": 0, "leg_tufts": True},
     "from W2a3; a smooth body, the spines only in tufts on the legs"),
    ("W2a3c", "Broodlings: bristle, mane", "broodling", "bristle", {"mane": True, "bristles": 18, "blen": (2.0, 3.5)},
     "from W2a3; a mane of spines round the waist only"),
    ("W2d1a", "Dread Phantom: shell, outlined", "phantom", "shell_edge", {},
     "from W2d1; the see-through shell with its outline drawn in light"),
    ("W2d1b", "Dread Phantom: shell, shadow inside", "phantom", "shell_ghost", {},
     "from W2d1; a dark spider shadow seen inside the shell of light"),
    ("W2d1c", "Dread Phantom: shell, scanlines", "phantom", "shell_scan", {},
     "from W2d1; rows of the shell missing like a bad signal, mid-teleport"),
    ("W2d2a", "Dread Phantom: wire, heavy", "phantom", "wire_thick", {},
     "from W2d2; the edge-only outline drawn twice as thick"),
    ("W2d2b", "Dread Phantom: wire, faint fill", "phantom", "wire_fill", {},
     "from W2d2; the glowing outline over a barely-there see-through body"),
    ("W2d2c", "Dread Phantom: wire, dashed", "phantom", "wire_dash", {},
     "from W2d2; the outline broken into dashes, like a construct still drawing itself"),
]
MATRON_ROWS = [   # (code, name, style, opt, note)
    ("W3a2a", "The Matron: chitin, big windows", "chitin", {"win": 0.34, "winz": 0.11},
     "from W3a2; cracked black-and-yellow chitin with windows three times bigger, the core and broodlings showing"),
    ("W3a2b", "The Matron: chitin, lifted plates", "chitin", {"lifted": True},
     "from W3a2; the plates stand off the shell, light leaking from the cracks under them"),
    ("W3a2c", "The Matron: chitin, gold-rimmed", "chitin", {"gold_rim": True},
     "from W3a2; every plate band edged in polished gold, like the lantern frames"),
    ("W3a3a", "The Matron: hourglass, dimmed", "hourglass", {"dim_glass": True},
     "from W3a3; darker glass so the gold waist and the falling stream of light read"),
    ("W3a3b", "The Matron: hourglass, caged", "hourglass", {"caged": True, "dim_glass": True},
     "from W3a3; the two glass bulbs held in a standing gold cage"),
    ("W3a3c", "The Matron: hourglass, upright", "hourglass", {"axis": 62, "dim_glass": True},
     "from W3a3; the hourglass carried upright over her back like a lantern on a pole"),
]
BUILDS = []
for i, (code, name, kind, style, opt, facts) in enumerate(SPIDER_ROWS):
    BUILDS.append(lambda X, a=(code, name, kind, style, opt, facts), i=i:
                  build_row(a[0], a[1], X, a[2], a[3], 11 + i, a[5], a[4]))
for i, (code, name, style, opt, note) in enumerate(MATRON_ROWS):
    BUILDS.append(lambda X, a=(code, name, style, opt, note), i=i:
                  build_matron_row(a[0], a[1], X, a[2], 30 + i * 4, a[3], a[4]))
L_ROWS = [
    ("W3c1a", "Lights out: the scream, sound rings", "scream_rings",
     "from W3c1; closer, her scream drawn as rings of yellow static rolling out from her head; eyes in every burrow"),
    ("W3c1b", "Lights out: the scream, true dark", "scream_dark",
     "from W3c1; almost no light at all: her eyes, her lantern abdomen and eight pairs of eyes; your ring a spark"),
    ("W3c1c", "Lights out: the scream, the brood answers", "scream_emerge",
     "from W3c1; Hunters rear half out of every burrow as she screams"),
    ("W3c3a", "Lights out: shell opens, heavy beam", "open_beam",
     "from W3c3; a heavy braided will beam and green cracks spread across her whole shell"),
    ("W3c3b", "Lights out: shell opens, green core", "open_core",
     "from W3c3; the green reaches her core: the nest's lantern turning green from the inside"),
    ("W3c3c", "Lights out: shell opens, close", "open_close",
     "from W3c3; close on her abdomen as glass shards and green sparks blow off it"),
]
for i, (code, name, variant, facts) in enumerate(L_ROWS):
    BUILDS.append(lambda X, a=(code, name, variant, facts), i=i: build_L3(a[0], a[1], X, a[2], 91 + i, a[3]))
BUILDS += [
    lambda X: build_W4b(X, "W4ba", {"name": "Funnel hollow: deep", "tz": [20, 15, 10, 5], "trad": [16.0, 12.5, 9.0, 5.5],
                                    "web_r": 12.5, "spokes": 36, "rings": 13,
                                    "facts": "from W4b; one more step down, a bigger and denser funnel web (36 spokes) "
                                             "into a deeper nest hole"}),
    lambda X: build_W4b(X, "W4bb", {"name": "Funnel hollow: deep lips", "lip": 2.8, "liph": 3, "lip_hunters": True,
                                    "facts": "from W4b; overhangs undercut twice as deep, Hunters clinging to the "
                                             "walls under every lip"}),
    lambda X: build_W4b(X, "W4bc", {"name": "Funnel hollow: sheet webs", "sheets": True,
                                    "trad": [14.0, 10.5, 7.5, 4.8],
                                    "facts": "from W4b; a tighter hollow, flat sheet webs laid over the terraces like "
                                             "tripwires"}),
    lambda X: build_W4c(X, "W4ca", {"name": "Crevice: sheet webs", "ladders": 3, "sheets": (6.0, 10.0, 14.0, 18.0, 21.0),
                                    "facts": "from W4c; fewer silk ladders, five sheet webs stacked down the crack"}),
    lambda X: build_W4c(X, "W4cb", {"name": "Crevice: wide with cable bridges", "wide": 1.8, "ladders": 4, "bridges": 6,
                                    "facts": "from W4c; a wider crack crossed by thick sagging silk cables"}),
    lambda X: build_W4c(X, "W4cc", {"name": "Crevice: branching", "ladders": 5, "branches": ((10.0, 0.6), (26.0, 3.6)),
                                    "facts": "from W4c; two side cracks branch off the main one, more burrows to hide in"}),
]
for i, b in enumerate(BUILDS):
    b(np.array([i * GAP, 0.0, 0.0]))

scene.camera = bpy.data.objects[TAKES[0][2]]
scene["dw_takes"] = repr(TAKES)
print(f"[{PASS}] built {len(TAKES)} takes, {len(scene.objects)} objects")
