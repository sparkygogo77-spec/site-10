# Pass v2.0115: Dread Warren round 8, more scenarios on existing generations, textured, a modern shaft (Trials; PC chat).
# Why: J on v2.0114 W1a7a-c: "all three are good, more scenarios like this, perfect utilization of existing
#   generations, it will be textured naturally or can you attempt updated themed modern looking shafts ... the cave
#   would need texturing, prepare to retire soon". Last pass of this chat.
# Library below is v2.0114's (mineshaft builders included); the round-8 section is at the end.
# Builds the whole scene from nothing (globals bpy, np, FOLDER); the renderer saves it as trials/dread_warren_r8.blend.
# Quick test: set DW_ONLY=W1a8c,W1a9a to build only those takes.
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


# =============================================================== v2.0111 (round 5): new pieces
# J rated v2.0109 on the site. KEEP W2d2b1 ("too much yellow"), W3c1c1, W3c1c2, W3c3c1. IMPROVE (no note) W3c1a1-a3,
# W3c1b1, W3c1b3, W3c3a1-a3, W3c3c2 -> 3 new versions each (+a/b/c). Every entrance and hall he rated was dropped
# ("these were all scrappable"); then he picked "Hidden in the world" (ordinary Minecraft spots, from eye height) and
# "Yes, from inside" (galleries shot from where you stand).
# Less yellow everywhere ("too much yellow", "pure yellow i cant see the detail"): quiet stone, a cool rim light on the
# construct spider so its black body reads, yellow kept to accents.
# Entrances and galleries are short clips: CALM for the first 3 seconds, then DANGER (webs fade in and glow, spiders
# come out): "I would prefer you only see the webs once youre in danger".
PASS = "v2.0111"
DANGER_AT = 60          # frame where calm turns to danger (3 s at 20 fps)
M.update({
    "stone_quiet": mat("dread stone quiet", (0.035, 0.032, 0.036), 0.85, veins=0.07, speck=0.5),
    "rock": mat("plain stone", (0.16, 0.16, 0.17), 0.9, speck=0.5),
    "gravel": mat("gravel", (0.2, 0.19, 0.18), 0.95, speck=0.9),
    "water": mat("river water", (0.05, 0.12, 0.2), 0.05, alpha=0.55),
    "sand": mat("river sand", (0.35, 0.32, 0.22), 0.95, speck=0.5),
    "reed": mat("reeds", (0.18, 0.35, 0.1), 0.8, speck=0.4),
    "rail": mat("old rail", (0.25, 0.22, 0.2), 0.4, metal=0.8),
})
QUIET_LABELS = {1: "stone_quiet", 2: "deep", 3: "silkblock", 4: "veinblock", 5: "bone"}
WORLD_LABELS = {1: "rock", 2: "deep", 3: "dirt", 4: "grass_live", 5: "log", 6: "leaf", 7: "wood", 8: "gravel",
                9: "water", 10: "sand", 11: "reed", 12: "flower", 13: "rail", 14: "stone_quiet"}


def web_fade_mat():
    """Silk that is all but invisible until DANGER_AT, then fades in and glows over 0.6 s."""
    if "web_fade" in M:
        return M["web_fade"]
    m = mat("web fade", (0.95, 0.6, 0.03), 0.4, emit=(1.0, 0.62, 0.03), es=1.0, alpha=0.9)
    p = _bsdf(m)
    for f, a, e in ((1, 0.0, 0.0), (DANGER_AT, 0.0, 0.0), (DANGER_AT + 12, 0.9, 1.0)):   # v2.0114: truly hidden while calm
        p.inputs["Alpha"].default_value = a; p.inputs["Alpha"].keyframe_insert("default_value", frame=f)
        p.inputs["Emission Strength"].default_value = e
        p.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    M["web_fade"] = m
    return m


def appear(ob, hidden_loc, frame_in=DANGER_AT, dur=14):
    """Keyframe an object from a hidden spot (inside a hole, up in the dark) to where it was placed."""
    final = tuple(ob.location)
    ob.location = hidden_loc
    ob.keyframe_insert("location", frame=1); ob.keyframe_insert("location", frame=frame_in)
    ob.location = final
    ob.keyframe_insert("location", frame=frame_in + dur)


def light_ramp(lt, calm_e, danger_e, frame_in=DANGER_AT, dur=12):
    lt.data.energy = calm_e
    lt.data.keyframe_insert("energy", frame=1); lt.data.keyframe_insert("energy", frame=frame_in)
    lt.data.energy = danger_e
    lt.data.keyframe_insert("energy", frame=frame_in + dur)


def eye_pair(name, loc, facing, size=1.0):
    """Two glowing eyes and two small ones, nothing else (a spider too deep in the dark to see)."""
    G = np.zeros((10, 4, 6), dtype=np.int16)
    for x, z, r in ((3.0, 3.0, 1.0), (7.0, 3.0, 1.0), (1.6, 4.4, 0.6), (8.4, 4.4, 0.6)):
        ellip(G, (x, 2, z), (r, r, r), 3)
    ob = grid_mesh(name, G, {3: "eye"}, PX * 1.4 * size)
    ob.location = loc
    ob.rotation_euler[2] = math.atan2(facing[1], facing[0]) - math.pi / 2 + math.pi
    return ob


def rim_lights(code, at, span=4.0, energy=260):
    """Cool rim light behind the construct spider: its black body reads as a silhouette, not a yellow blur."""
    at = np.asarray(at, float)
    for k, sx in enumerate((-1, 1)):
        light(f"{code} rim {k}", tuple(at + np.array([sx * span * 0.9, span * 1.2, span * 0.9])), (0.55, 0.7, 1.0),
              energy, cutoff=span * 4, kind="AREA", size=span * 0.6,
              rot=(math.radians(-55), 0, math.radians(180 + sx * 35)))


def arena5(code, seed):
    """small_arena with quiet stone: no yellow vein blocks, the gold veins faint."""
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
    G[G == 4] = 1
    off = np.array([-c, -c, -7.0])
    blocks(f"{code} ground", G, tuple(off), QUIET_LABELS)
    return G, off, mouths, c


def ring_set(S, centre, radii, mode, rng, width=3.0):
    """The scream drawn as rings of static. mode: vertical, flat, broken, thick, cone (rings growing toward you)."""
    centre = np.asarray(centre, float)
    for k, rr in enumerate(radii):
        if mode in ("vertical", "broken", "thick"):
            pts = [centre + np.array([math.cos(a) * rr, -0.7 * k, math.sin(a) * rr * 0.8])
                   for a in np.linspace(0, 2 * math.pi, 61)]
        elif mode == "flat":
            pts = [np.array([centre[0] + math.cos(a) * rr, centre[1] + math.sin(a) * rr, 0.08])
                   for a in np.linspace(0, 2 * math.pi, 73)]
        else:   # cone: each ring further toward the player and wider
            pts = [centre + np.array([math.cos(a) * rr * 0.6, -1.3 * (k + 1), math.sin(a) * rr * 0.45])
                   for a in np.linspace(0, 2 * math.pi, 49)]
        w = PX * (width - 0.4 * k if mode != "thick" else 6 - k)
        if mode == "broken":
            for j in range(0, 60, 6):
                S.poly(pts[j:j + 4], PX * width)
        else:
            S.poly(pts, max(w, PX))


def build_L5(code, name, X, o, seed, facts):
    """Lights out with the lair's construct spider, round 5. o: options (see the take list)."""
    before = set(o_.name for o_ in scene.objects)
    G, off, mouths, c = arena5(code, seed)
    rng = np.random.default_rng(seed)
    fill = o.get("fill", 300)
    if o["base"] == "scream":
        sp = construct_spider(f"{code} construct", "rear", seed)
        sp.location = (0, o.get("sp_y", 4.5), 0); ground(sp, 0.0)
        lo, hi = bbox_w(sp)
        hc = np.array([0, lo[1] + 1.2, hi[2] * 0.62])
        light(f"{code} eyes", tuple(hc - np.array([0, 1.0, 0])), (1.0, 0.55, 0.03), 60, cutoff=5)
        if o.get("boss_eyes"):        # the construct spider's own eyes, big and bright enough to find in the dark
            be = eye_pair(f"{code} boss eyes", tuple(hc + np.array([0, -0.9, 0.1])), (0, -1, 0), o["boss_eyes"])
            light(f"{code} boss eye glow", tuple(hc + np.array([0, -1.2, 0.2])), (1.0, 0.5, 0.02), 35, radius=0.3, cutoff=3)
        pr, hand = player(f"{code} player", (0, -5.5, 0), rot_z=0)
        if o.get("rings"):
            S = Strands(f"{code} scream")
            for mode, radii, w in o["rings"]:
                ring_set(S, hc if mode != "flat" else np.array([0, 4.5, 0]), radii, mode, rng, w)
            S.build("static")
        if o.get("streaks"):          # the scream as streaks of static flying at you
            S = Strands(f"{code} streaks")
            mode = o.get("streak_mode", "long")
            for k in range(o["streaks"]):
                a = rng.uniform(0, 2 * math.pi); f_ = rng.uniform(0.1, 0.9)
                spread = 3.4 if mode != "long" else 2.2
                p = hc + np.array([math.cos(a) * f_ * spread, -f_ * 8.5, math.sin(a) * f_ * spread * 0.7])
                if mode == "short":
                    S.seg(p, p + np.array([math.cos(a) * 0.08, -0.45, math.sin(a) * 0.05]), PX * 2)
                elif mode == "wavy":
                    S.poly([p + np.array([math.sin(j * 1.3 + a) * 0.12, -0.3 * j, math.cos(j * 1.3 + a) * 0.08])
                            for j in range(6)], PX * 1.5)
                else:
                    S.seg(p, p + np.array([math.cos(a) * 0.15, -1.4, math.sin(a) * 0.1]), PX * 1.5)
            S.build("static")
        if o.get("wrap"):             # the static wrapping round you: loops of it round the player
            S = Strands(f"{code} wrap")
            for k in range(5):
                z0 = 0.3 + k * 0.35
                S.poly([np.array([math.cos(a) * (0.9 + 0.1 * k), -5.5 + math.sin(a) * (0.9 + 0.1 * k), z0 + math.sin(a * 3) * 0.1])
                        for a in np.linspace(0, 2 * math.pi, 37)], PX * 2)
            S.build("static")
        if o.get("dust"):             # dust thrown up off the floor by the shockwave
            Dd = Strands(f"{code} dust")
            nd, ds, dh = (160, 2, 0.6) if o["dust"] is True else o["dust"]
            for k in range(nd):
                a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(1.5, 8.5)
                p = np.array([math.cos(a) * rr, 4.5 + math.sin(a) * rr, rng.uniform(0.05, dh)])
                Dd.seg(p, p + np.array([0, 0, PX * ds]), PX * ds)
            Dd.build("gravel")
        if o.get("floor_cracks"):     # the floor cracking under the rings
            Fc = Strands(f"{code} floor cracks")
            for k in range(o["floor_cracks"]):
                a = rng.uniform(0, 2 * math.pi); p = np.array([math.cos(a) * 1.5, 4.5 + math.sin(a) * 1.5, 0.04])
                d_ = np.array([math.cos(a), math.sin(a), 0.0])
                pts = [p.copy()]
                for j in range(14):
                    d_ = d_ + np.array([rng.normal() * 0.35, rng.normal() * 0.35, 0]); d_ /= np.linalg.norm(d_)
                    p = p + d_ * 0.5; pts.append(p.copy())
                Fc.poly(pts, PX * 1.5)
            Fc.build("crack")
        if o.get("sparks"):           # your ring guttering: green sparks dropping off it
            bpy.context.view_layer.update()
            hp = np.array(hand.matrix_world.translation)
            Sp = Strands(f"{code} sparks")
            for k in range(o["sparks"]):
                p = hp + rng.normal(size=3) * 0.3 - np.array([0, 0, rng.uniform(0, 1.6)])
                Sp.seg(p, p + np.array([0, 0, PX * 3]), PX * 2.5)
            Sp.build("ash")
            light(f"{code} flicker", tuple(hp - np.array([0, 0, 0.5])), (0.08, 1.0, 0.18), 60, cutoff=4)
        # eyes in the burrows and round the walls
        if o.get("eyes", "burrows") != "none":
            spots = list(mouths)
            for k in range(o.get("wall_eyes", 0)):
                a = rng.uniform(0, 2 * math.pi)
                spots.append((np.array([c + math.cos(a) * 10.5, c + math.sin(a) * 10.5, 7.6]),
                              np.array([math.cos(a), math.sin(a), 0.0])))
            for k, (mm, d) in enumerate(spots):
                p = mm + off - d * 0.2 + np.array([0, 0, -0.4])
                if o.get("eyes") == "only":
                    eye_pair(f"{code} eyes {k}", tuple(p), -d, o.get("eye_size", 1.6))
                else:
                    ob, _ = spider2(f"{code} lurker {k}", "hunter", "plate", "stand", 700 + k)
                    place_on(ob, p, (0, 0, -1), tuple(-d[:2]) + (0,), 2.6)
        if o.get("eye_ring"):         # eyes closing in round you on the floor
            for k in range(o["eye_ring"]):
                a = k / o["eye_ring"] * 2 * math.pi
                eye_pair(f"{code} close eyes {k}", (math.cos(a) * 3.2, -5.5 + math.sin(a) * 3.2, 0.25),
                         (-math.cos(a), -math.sin(a), 0), 1.4)
        if o.get("scream_light"):
            light(f"{code} scream light", tuple(hc + np.array([0, -2.5, 0])), (1.0, 0.6, 0.05), o["scream_light"],
                  cutoff=o.get("scream_cut", 10))
        if o.get("ring_e", 25):
            ring_light(f"{code} ring", hand, energy=o.get("ring_e", 25))
        rim_lights(code, (0, 4.5, 1.5), 4.0, 260 if fill >= 300 else 45)   # true dark stays dark
        look_default = hc
    else:
        sp = construct_spider(f"{code} construct", "stand", seed, cracks=o.get("cracks", 12), glen=o.get("glen", 25))
        sp.location = (0, 4.0, 0); ground(sp, 0.0)
        lo, hi = bbox_w(sp)
        tgt = np.array([0, lo[1] + (hi[1] - lo[1]) * 0.42, hi[2] * 0.5])
        pr, hand = player(f"{code} player", (0.6, -4.0, 0), rot_z=0.15)
        ring_light(f"{code} overcharge", hand, energy=1600)
        bpy.context.view_layer.update()
        hp = np.array(hand.matrix_world.translation)
        Bm = Strands(f"{code} will beam")
        axis_ = tgt - hp; L_ = np.linalg.norm(axis_); axis_ /= L_
        u_ = np.cross(axis_, (0, 0, 1)); u_ /= np.linalg.norm(u_); v_ = np.cross(axis_, u_)
        beam = o["beam"]
        if beam.startswith("rod"):
            n_ = o.get("rod_n", 4); half = o.get("rod_r", 1.5)
            for du in np.linspace(-half, half, n_):
                for dv in np.linspace(-half, half, n_):
                    Bm.seg(hp + (u_ * du + v_ * dv) * PX, tgt + (u_ * du + v_ * dv) * PX * 1.4, PX * 1.3)
            if beam == "rod_collars":       # hard-light collars ringing the rod
                for f_ in np.linspace(0.15, 0.85, 5):
                    cpt = hp + axis_ * L_ * f_
                    Bm.poly([cpt + (u_ * math.cos(a) + v_ * math.sin(a)) * 0.32 for a in np.linspace(0, 2 * math.pi, 17)], PX * 2)
        elif beam.startswith("braid"):
            ns, rad = o.get("strands", 3), o.get("braid_r", 0.16)
            for j in range(ns):
                pts = []
                for f_ in np.linspace(0, 1, 50):
                    a = f_ * 6 * math.pi + j * 2 * math.pi / ns
                    pts.append(hp + axis_ * L_ * f_ + (u_ * math.cos(a) + v_ * math.sin(a)) * rad)
                Bm.poly(pts, PX * 2.5)
            Bm.seg(hp, tgt, PX * 2)
            if beam == "braid_sparks":     # sparks spiralling off the braid
                Sp = Strands(f"{code} braid sparks")
                for k in range(80):
                    f_ = rng.uniform(0, 1); a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.3, 0.8)
                    p = hp + axis_ * L_ * f_ + (u_ * math.cos(a) + v_ * math.sin(a)) * rr
                    Sp.seg(p, p + (u_ * -math.sin(a) + v_ * math.cos(a)) * 0.12, PX)
                Sp.build("ash")
        else:                               # heavy: several rough strands
            for j in range(6):
                Bm.poly([hp, (hp + tgt) / 2 + rng.normal(size=3) * 0.22, tgt], PX * (7 - j))
        Bm.build("ring")
        light(f"{code} green in the shell", tuple(tgt), (0.08, 1.0, 0.18), o.get("green", 380), cutoff=8)
        for k in range(o.get("blaze_lights", 0)):
            light(f"{code} crack blaze {k}", tuple(tgt + rng.normal(size=3) * np.array([1.4, 1.4, 0.9])),
                  (0.08, 1.0, 0.18), 140, cutoff=5)
        if o.get("chunks"):                # pieces of the shell lifting off round the hit
            Ch = Strands(f"{code} shell chunks")
            for k in range(o["chunks"]):
                d = rng.normal(size=3); d[1] = -abs(d[1]) * 0.5; d /= np.linalg.norm(d)
                p = tgt + d * rng.uniform(1.0, 2.6)
                Ch.seg(p, p + rng.normal(size=3) * 0.18, PX * rng.choice([3.0, 4.0, 5.0]))
            Ch.build("shell")
        if o.get("shards"):
            Sh = Strands(f"{code} shards")
            for k in range(o["shards"]):
                d = rng.normal(size=3); d /= np.linalg.norm(d)
                p = tgt + d * rng.uniform(1.6, 4.2)
                Sh.seg(p, p + rng.normal(size=3) * 0.14, PX * rng.choice([2.0, 3.0]))
            Sh.build("glass")
        rim_lights(code, (0, 4.0, 1.5), 4.0)
        look_default = tgt
    root = empty(f"{code} turn", X)
    kind = "turntable" if o.get("spin", True) else "static"
    if kind == "turntable":
        spin(root)
    adopt(root, before)
    light(f"{code} fill", X + np.array([-14, -20, 18]), (0.45, 0.5, 0.7), fill, cutoff=60, kind="AREA", size=12,
          rot=(math.radians(45), 0, math.radians(-35)))
    cl, lk, lens = o.get("cam", ((0, -20, 10), None, 35))
    look = np.asarray(lk, float) if lk is not None else look_default
    cam = camera(f"Cam {code} {name}", X + np.asarray(cl, float), X + look, lens=lens)
    add_take(code, name, cam, kind, facts)


# --------------------------------------------------------------- W1a entrances, hidden in the world (eye height)
def world_block(code, G, off):
    return blocks(f"{code} world", G, tuple(off), WORLD_LABELS)


def grass_skin(G, ground):
    """Fill rock under a height map, dirt 3 deep, grass on top. ground: (nx, ny) int heights."""
    nx, ny, nz = G.shape
    zz = np.arange(nz)[None, None, :]
    h = ground[:, :, None]
    G[zz < h] = 1
    G[(zz < h) & (zz >= h - 3)] = 3
    G[zz == h - 1] = 4
    G[:, :, 0] = 2


def plants(G, rng, n, mask_fn, lab_choices=(12, 6, 11)):
    nx, ny, nz = G.shape
    for k in range(n):
        x, y = int(rng.integers(1, nx - 1)), int(rng.integers(1, ny - 1))
        if not mask_fn(x, y):
            continue
        col = np.nonzero(G[x, y, :])[0]
        if len(col) and G[x, y, col[-1]] == 4 and col[-1] + 1 < nz:
            lab = lab_choices[k % len(lab_choices)]
            G[x, y, col[-1] + 1] = lab
            if lab == 11 and col[-1] + 3 < nz:
                G[x, y, col[-1] + 2] = 11


def tree(G, x, y, z0, h, rng, lean=0):
    G[x, y, z0:z0 + h] = 5
    c = np.array([x + 0.5, y + 0.5, z0 + h])
    ellip(G, c, (2.6, 2.6, 2.0), 6, only_empty=True)
    G[(G == 6) & (rng.random(G.shape) < 0.12)] = 0


def build_entrance5(X, code, name, kind, seed, facts, v=None):
    v = v or {}
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = 64, 48, 34
    G = np.zeros((nx, ny, nz), dtype=np.int16)
    xx, yy, zz = np.mgrid[0:nx, 0:ny, 0:nz]
    n2 = smooth_noise((nx, ny), rng, 4)
    web = web_fade_mat()
    S = Strands(f"{code} silk")
    spiders = []      # (object, hidden location offset)
    eyes_at = []
    if kind == "ravine":
        gnd = (20 + n2 * 0.6).astype(int)
        grass_skin(G, gnd)
        cy = 15.5 + np.sin((xx[:, :, 0] + 0.5) * 0.12) * 1.2                 # a ravine running across your view
        for z in range(4, nz):
            half = 1.2 + max(0, z - 4) * 0.16 + n2 * 0.25
            G[:, :, z][np.abs(yy[:, :, 0] + 0.5 - cy) < half] = 0
        cyv = float(cy[32, 0])
        hx, hz = 32, 15
        ws = cyv + 1.2 + (hz - 4) * 0.16                                     # the far wall's face at the hole
        hy = int(ws)
        G[hx - 3:hx + 3, hy - 1:hy + 1, hz - 1] = 1                          # a ledge under it
        ellip(G, (hx, ws + 1.5, hz + 1.0), (1.2, 2.0, 1.4), 0)
        walk_tunnel(G, (hx, ws + 3.0, hz + 0.8), (0, 1, 0.1), 8, 1.1, rng, wander=0.15)
        for k, x in enumerate((hx - 2.6, hx - 1.9, hx + 1.9, hx + 2.6)):  # roots hanging beside the hole
            for z in range(hz + 3, hz + 3 - int(rng.integers(2, 4)), -1):
                if G[int(x), hy - 1, z] == 0:
                    G[int(x), hy - 1, z] = 5 if k % 2 else 6
        tree(G, 18, 34, int(gnd[18, 34]), 6, rng); tree(G, 45, 38, int(gnd[45, 38]), 5, rng)
        tree(G, 10, 4, int(gnd[10, 4]), 6, rng)
        plants(G, rng, 220, lambda x, y: abs(y - cy[x, 0]) > 5)
        mouth = np.array([hx + 0.5, ws - 0.2, hz + 1.0])
        S.web(mouth, (0, -1, 0), 1.5, spokes=9, rings=4, rng=np.random.default_rng(seed))
        for k in range(9):                                                  # threads strung across the ravine
            x0 = hx + rng.uniform(-10, 10)
            S.seg(np.array([x0, cy[int(x0), 0] - 3.0, 20.2]), np.array([x0 + rng.uniform(-2, 2), cy[int(x0), 0] + 3.0, rng.uniform(12, 20)]))
        eyes_at = [(mouth + np.array([-0.5, 2.2, 0]), (0, -1, 0)), (mouth + np.array([0.6, 3.6, 0.2]), (0, -1, 0))]
        cam_g, look_g = np.array([32.5, cyv - 5.0, 21.6]), mouth + np.array([0, 0, -0.8])
        climb = (mouth + np.array([1.4, 0.4, -1.0]), (0, -1, 0), (0, 0, 1))
        lure_g = mouth + np.array([0, 2.5, 0])
    elif kind == "mineshaft":
        hill = np.clip((yy[:, :, 0] + 0.5 - 14) * 1.1, 0, 9)
        gnd = (20 + hill + n2 * 0.5).astype(int)
        grass_skin(G, gnd)
        x0, x1 = 30, 33
        G[x0:x1, 13:44, 20:23] = 0                                          # the old tunnel into the hill
        for yb in (14, 18, 22, 26, 30):                                      # timber frames
            G[x0 - 1, yb, 20:23] = 7; G[x1, yb, 20:23] = 7; G[x0 - 1:x1 + 1, yb, 23] = 7
            G[x0:x1, yb, 22] = 7 if yb == 14 else G[x0:x1, yb, 22]
        G[x0 - 1, 14, 20:24] = 7; G[x1, 14, 20:24] = 7; G[x0 - 1:x1 + 1, 14, 23] = 7
        G[x0:x1, 14, 22] = 0
        G[x0 + 1, 13:44, 19] = 13                                            # a rail line
        if v.get("gravel", True):
            for k in range(12):                                             # a little gravel slide at the mouth
                G[int(rng.integers(x0 - 1, x1 + 1)), int(rng.integers(11, 15)), 20 + int(rng.integers(0, 2))] = 8
            G[x0:x1, 13:16, 20][rng.random((3, 3)) < 0.35] = 8
        if v.get("rails_out"):                                              # the rails run out of the mine toward you
            G[x0 + 1, 5:13, 19] = 13
        if v.get("cart"):                                                   # an old minecart left on the rails
            G[x0:x1, 10:12, 20] = 7                                         # low, so you see over it into the mine
        if v.get("collapse"):                                               # the hill fallen in over the first frames
            G[x0 - 1:x1 + 1, 15:19, 23:30] = 0
            G[x0:x1, 16:18, 20] = 8
            capsule(G, (x0 - 0.5, 14.5, 23.5), (x1 + 0.5, 15.5, 20.5), 0.5, 7)
        tree(G, 22, 9, int(gnd[22, 9]), 6, rng); tree(G, 42, 7, int(gnd[42, 7]), 5, rng)
        tree(G, 38, 30, int(gnd[38, 30]), 6, rng)
        plants(G, rng, 220, lambda x, y: not (x0 - 2 <= x <= x1 + 1 and y < 16))
        mouth = np.array([31.5, 15.0, 21.5])
        for yb in (18, 22, 26):                                             # silk wound round the timbers (danger)
            for side in (x0 - 0.5, x1 + 0.5):
                S.poly([np.array([side + math.cos(a) * 0.6, yb + 0.5 + math.sin(a) * 0.6, 20 + a / (2 * math.pi) * 0.5])
                        for a in np.linspace(0, 2 * math.pi * 6, 60)], PX * 1.5)
        S.web(np.array([31.5, 24.0, 21.5]), (0, 1, 0), 1.7, spokes=10, rings=5, rng=np.random.default_rng(seed))
        S.web(np.array([31.5, 30.0, 21.5]), (0, 1, 0), 1.7, spokes=10, rings=5, rng=np.random.default_rng(seed + 1))
        eyes_at = [(np.array([31.0, 33.0, 21.3]), (0, -1, 0)), (np.array([32.2, 36.0, 21.6]), (0, -1, 0)),
                   (np.array([31.5, 40.0, 22.0]), (0, -1, 0))]
        cam_g, look_g = np.array([31.5, 3.0, 21.6]), np.array([31.5, 18.0, 21.2])
        climb = (np.array([31.5, 20.5, 20.0]), (0, 0, -1), (0, -1, 0))
        lure_g = np.array([31.5, 28.0, 21.5])
        if v.get("lantern"):                                                # a lantern still hanging in the first frame
            G[31, 18, 22] = 12
            lure_g = np.array([31.5, 18.5, 22.0])
    else:   # river bank
        gnd = np.where(yy[:, :, 0] < 9, 19, np.where(yy[:, :, 0] > 17, 21, 16)) + (n2 * 0.5).astype(int)
        grass_skin(G, gnd)
        river = (yy[:, :, 0] >= 9) & (yy[:, :, 0] <= 17)
        for z in range(15, 18):
            G[:, :, z][river & (G[:, :, z] == 0)] = 9
        G[:, :, 15][river] = 10
        G[:, 17:19, 19:21] = 4                                              # the grassy lip hanging over the water
        G[:, 18, 19] = 3
        gh_ = v.get("gap_h", 2)
        if gh_ > 2:                                                          # a higher lip over a taller gap
            G[:, 17:19, 19:21] = 0
            G[:, 17:19, 17 + gh_:19 + gh_] = 4
            G[:, 19:24, 19:17 + gh_ + 2] = 3
            G[:, 19:24, 17 + gh_ + 1] = 4
        G[26:38, 17, 17:17 + gh_] = 0                                       # the gap under it
        G[26:38, 18:21, 17:17 + gh_] = 0
        walk_tunnel(G, (32, 20, 17.6), (0, 1, 0.05), 10, 1.1, rng, wander=0.15)
        if v.get("steps"):                                                  # stepping stones across the river to it
            for k, y in enumerate(range(9, 17, 2)):
                G[31 + (k % 2), y, 15:18] = 1
        if v.get("falls"):                                                  # a little waterfall over the gap
            G[26:38, 16, 17:17 + gh_ + 1] = 9
        if v.get("log"):                                                    # a fallen log across the river
            capsule(G, (27.0, 7.5, 18.5), (29.5, 17.0, 18.0), 0.7, 5)
        for x in range(22, 42):                                             # reeds along the far bank hiding the gap
            if v.get("falls") or (v.get("steps") and 30 <= x <= 33):
                continue
            if rng.random() < v.get("reeds", 0.55):
                h = int(rng.integers(2, 4))
                G[x, 16, 18:18 + h] = 11
        tree(G, 14, 30, int(gnd[14, 30]), 6, rng); tree(G, 48, 28, int(gnd[48, 28]), 5, rng)
        tree(G, 40, 3, int(gnd[40, 3]), 6, rng)
        plants(G, rng, 200, lambda x, y: y < 8 or y > 21)
        mouth = np.array([32.0, 17.2, 17.9])
        S.web(mouth, (0, -1, 0), 1.0, spokes=8, rings=3, rng=np.random.default_rng(seed))
        for dx in np.linspace(-7, 7, 15):                                   # the "reeds" have silk running through them
            S.seg(np.array([32 + dx, 16.5, 18.2]), np.array([32 + dx + rng.uniform(-0.8, 0.8), 16.5, 20.4]))
        eyes_at = [(mouth + np.array([-2.5, 1.4, 0]), (0, -1, 0)), (mouth + np.array([2.0, 1.6, 0.1]), (0, -1, 0)),
                   (mouth + np.array([0.0, 3.0, 0.0]), (0, -1, 0))]
        cam_g, look_g = np.array([32.0, 4.0, 20.6]), mouth + np.array([0, 0, 0.3])
        climb = (mouth + np.array([0.5, 0.2, -0.6]), (0, 0, -1), (0, -1, 0))
        lure_g = mouth + np.array([0, 2.0, 0])
    near = (np.hypot(xx + 0.5 - cam_g[0], yy + 0.5 - cam_g[1]) < 4.5) & (zz >= cam_g[2] - 2.0)
    G[near & np.isin(G, (5, 6, 11, 12))] = 0          # nothing tall right in front of your eyes
    off = np.array([-cam_g[0], -cam_g[1], -(cam_g[2] - 1.6)])
    world_block(code, G, off)
    S.build("web_fade", loc=tuple(off))
    for k, (p, facing) in enumerate(eyes_at):
        eo = eye_pair(f"{code} eyes {k}", tuple(p + off), facing, 1.0)
        appear(eo, tuple(p + off + np.array([0, 4, -3.0])))     # shut away in the rock while calm
    CUR.clear(); CUR.update({"dim": True})
    ob, _ = spider2(f"{code} hunter", "hunter", ["plate", "bristle", "shard"][seed % 3], "rear", seed + 3)
    CUR.clear()
    pos, belly, head = climb
    place_on(ob, pos + off, belly, head, 2.6) if kind != "ravine" else None
    if kind == "ravine":
        ob.location = tuple(pos + off); ground(ob, (pos + off)[2] - 0.6)
    appear(ob, tuple(np.asarray(ob.location) + np.array([0, 9.0, -3.0])), DANGER_AT + 6, 18)   # hidden in the rock while calm
    lg = light(f"{code} inside glow", tuple(lure_g + off), (1.0, 0.55, 0.03), 10, cutoff=8)
    light_ramp(lg, 10, 120)
    # moonlight from behind you (an area light, not a sun: a sun would light every take in the file)
    light(f"{code} moon", (-6, -10, 22), (0.55, 0.65, 1.0), 9000, cutoff=70, kind="AREA", size=30,
          rot=(math.radians(-40), 0, math.radians(-20)))
    lr = light(f"{code} ring", (0.35, 0.4, 1.35), (0.08, 1.0, 0.18), 120, radius=0.05, cutoff=12)
    root = empty(f"{code} place", X); adopt(root, before)
    cam = camera(f"Cam {code} {name}", X + np.array([0, 0, 1.6]), X + (look_g + off), lens=28)
    add_take(code, name, cam, "turntable", facts + "; from eye height where you'd stand. The clip runs CALM for 3 "
             "seconds, then DANGER: the webs fade in and glow, eyes open, a Hunter comes out")


ENT5 = [
    ("W1a4", "Entrance: ravine ledge", "ravine",
     "an ordinary ravine in a grass plain; on the far wall, a few blocks down, a ledge and a dark hole half-hidden by "
     "hanging roots, the kind of spot you'd climb down to for ore"),
    ("W1a5", "Entrance: old mineshaft", "mineshaft",
     "an abandoned mineshaft in a hillside: timber frames, a rail line, a little gravel slide at the mouth. It looks "
     "like any old mine until the timbers turn out to be wound in silk"),
    ("W1a6", "Entrance: river bank", "river",
     "a quiet river; under the grassy lip of the far bank, behind the reeds, a low dark gap just above the water"),
]


# --------------------------------------------------------------- W1b Weave Gallery, from inside
def build_gallery5(X, code, name, kind, seed, facts, v=None):
    v = v or {}
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    if kind == "cathedral":
        nx, ny, nz, w0, spring, top = 17, 46, 20, 4.6, 10.0, 17.0
    elif kind == "winding":
        nx, ny, nz, w0, spring, top = 24, 40, v.get("nz", 13), v.get("w0", 3.0), v.get("spring", 6.0), v.get("top", 10.0)
    else:
        nx, ny, nz, w0, spring, top = 20, 40, 30, 6.0, 20.0, 27.0
    G = np.ones((nx, ny, nz), dtype=np.int16)
    xx, yy, zz = np.mgrid[0:nx, 0:ny, 0:nz]
    wob = smooth_noise((nx, ny, nz), rng, 3)
    cxm = nx / 2
    if kind == "winding":
        path = lambda y: cxm + 4.5 * math.sin((y - 3) * 0.16)
    else:
        path = lambda y: cxm
    pcx = np.vectorize(path)(yy + 0.5)
    floor = 2 if kind != "ledge" else 12
    arch = np.where(zz + 0.5 < spring, w0, w0 * np.sqrt(np.clip(1 - ((zz + 0.5 - spring) / (top - spring)) ** 2, 0, 1)))
    rib = ((yy + 0.5) % 4.0) < 1.1
    hollow = (np.abs(xx + 0.5 - pcx) < arch - rib * 0.8 * (zz > floor + 1) + wob * 0.3) & (zz >= floor) & (yy >= 1) & (yy < ny - 1)
    if kind == "ledge":       # the floor drops away into a pit; a ledge runs along the left wall
        hollow |= (np.abs(xx + 0.5 - pcx) < w0 - 0.5) & (zz >= 2) & (zz < floor) & (yy >= 1) & (yy < ny - 1)
        hollow &= ~((xx + 0.5 < cxm - w0 + 2.6) & (zz < floor) & (zz >= floor - 1))
    G[hollow] = 0
    G[:, 0, :] = 1
    mouths = []
    for k in range(14):
        y0 = rng.uniform(4, ny - 4); sx = rng.choice([-1, 1]); z0 = rng.uniform(floor + 1, floor + spring * 0.6)
        start = np.array([path(y0) + sx * (w0 + 0.2), y0, z0])
        walk_tunnel(G, start, (sx, 0, 0.1), 5, 1.0, rng, wander=0.2)
        mouths.append((start, np.array([sx, 0, 0.0])))
    finish_cave(G, G > 0, zz, rng, [], collar=1.4)
    G[G == 3] = 1
    G[G == 4] = 1
    cam_x = path(1.5) if kind != "ledge" else cxm - w0 + 1.3
    off = np.array([-cam_x, -1.5, -(floor + 1.6)])
    blocks(f"{code} gallery", G, tuple(off), QUIET_LABELS)
    web = web_fade_mat()
    S = Strands(f"{code} silk")
    if v.get("wall_webs"):   # rev 2 (J: "THE WEBBING ON THE INSIDE SHOULDNTBE HERE"): webs only on the walls and
        # up in the vault between the ribs, nothing across the walkway
        for k, yw in enumerate(range(6, ny - 4, 4)):
            for sx in (-1, 1):
                S.web(np.array([path(yw + 2) + sx * (w0 - 0.3), yw + 2, floor + 4.0 + (k % 2) * 2.5]), (sx, 0, 0),
                      1.6, spokes=9, rings=5, rng=np.random.default_rng(seed + 50 + 2 * k + (sx > 0)))
            S.web(np.array([path(yw + 2), yw + 2, top - 1.2]), (0, 0, -1), w0 * 0.6, spokes=10, rings=5,
                  rng=np.random.default_rng(seed + 90 + k))
    elif kind == "cathedral":
        for k, yw in enumerate((12, 20, 28, 36)):
            S.web(np.array([path(yw), yw, floor + 8.0]), (0, 1, 0), w0 + 3.5, spokes=14, rings=8,
                  rng=np.random.default_rng(seed + k), sag=0.3)
        for k in range(20):
            y0 = rng.uniform(6, ny - 4); x0 = path(y0) + rng.uniform(-w0 + 0.8, w0 - 0.8)
            S.seg(np.array([x0, y0, floor + 0.1]), np.array([x0 + rng.uniform(-1, 1), y0, top - 1]))
    elif kind == "winding":
        for k, yw in enumerate((11, 17, 24, 31)):
            S.web(np.array([path(yw), yw, floor + 3.0]), (0, 1, 0), w0 + 2.0, spokes=11, rings=6,
                  rng=np.random.default_rng(seed + k), sag=0.2)
    else:
        for k, (zn, yw) in enumerate(((floor - 3, 0), (floor - 7, 0))):   # nets across the pit
            for j in range(4):
                S.web(np.array([cxm + 1.0, 8 + j * 8 + k * 3, zn]), (0, 0, 1), w0 + 0.5, spokes=12, rings=6,
                      rng=np.random.default_rng(seed + 10 * k + j))
        for k in range(16):
            y0 = rng.uniform(5, ny - 4)
            S.seg(np.array([cxm - w0 + 2.6, y0, floor]), np.array([cxm + w0 - 0.5, y0 + rng.uniform(-2, 2), floor - rng.uniform(2, 9)]))
    S.build("web_fade", loc=tuple(off))
    for k, (m, d) in enumerate(mouths[::2]):
        eo = eye_pair(f"{code} eyes {k}", tuple(m + off - d * 0.5), -d, 1.0)
        appear(eo, tuple(m + off + d * 3.0))
        if v.get("burrow_lights"):         # each burrow glowing warm from deep inside once it is danger
            bl = light(f"{code} burrow glow {k}", tuple(m + off + d * 2.5), (1.0, 0.55, 0.05), 0, cutoff=5)
            light_ramp(bl, 0, 40)
    CUR.clear(); CUR.update({"dim": True})
    if kind != "ledge":   # a Hunter drops on its thread in front of you
        hs, spl = spider2(f"{code} hunter drop", "hunter", "plate", "drop", seed + 2)
        orient(hs, belly=(0, -1, 0), head=(0, 0, -1))
        dy = 6.5 if kind == "cathedral" else 5.0
        hs.location = tuple(np.array([path(dy), dy, floor + 2.6]) + off)
        bpy.context.view_layer.update()
        tp = np.array(hs.matrix_world @ Vector(spl))
        T = Strands(f"{code} drop thread"); T.seg(tp, tp + np.array([0, 0, top])); T.build("web_fade")
        appear(hs, tuple(np.asarray(hs.location) + np.array([0, 0, top - floor - 2.5])), DANGER_AT + 4, 10)
    else:                 # Hunters climbing up the nets out of the pit
        for k in range(4):
            ob, _ = spider2(f"{code} climber {k}", "hunter", ["plate", "bristle", "shard"][k % 3], "stand", seed + 20 + k)
            orient(ob, belly=(0, 0, -1), head=(rng.uniform(-0.4, 0.4), -1, 0))
            ob.location = tuple(np.array([cxm + rng.uniform(-1.5, 3.5), 10 + k * 7, floor - 2.8]) + off)
            appear(ob, tuple(np.asarray(ob.location) + np.array([0, 0, -6])), DANGER_AT + 4 + k * 3, 16)
    CUR.clear()
    lights_ = []
    for k in range(3):
        y0 = 14 + k * 10
        lights_.append(light(f"{code} deep glow {k}", tuple(np.array([path(y0), y0, floor + (spring if kind != "ledge" else -6)]) + off),
                             (1.0, 0.6, 0.06), 30, cutoff=14))
    for lt in lights_:
        light_ramp(lt, v.get("glow_calm", 30), v.get("glow_danger", 110))
    light(f"{code} ring", (0.35, 0.5, -0.3), (0.08, 1.0, 0.18), v.get("ring_e", 160), radius=0.05, cutoff=16)
    light(f"{code} cave fill", (0, 4, 3), (0.5, 0.55, 0.75), 60, radius=2.0, cutoff=40)
    root = empty(f"{code} place", X); adopt(root, before)
    look = np.array([path(14) if kind != "ledge" else cam_x + 2.0, 14, floor + (3.5 if kind == "cathedral" else (2.0 if kind == "winding" else -2.5))]) + off
    cam = camera(f"Cam {code} {name}", X + np.array([0, 0, 0]), X + look, lens=22)
    add_take(code, name, cam, "turntable", facts + "; from inside, standing where you would, your ring the only lamp. "
             "The clip runs CALM for 3 seconds, then DANGER: the webs fade in and glow, eyes open in the burrows")


GAL5_OPT = {"W1b4": {"wall_webs": True}}   # rev 2 of W1b4
GAL5 = [
    ("W1b4", "Weave Gallery inside: silk cathedral", "cathedral",
     "a tall nave, 9 wide and 15 high, ribs arching over you every 4 blocks (no columns), burrows in both walls; rev 2 "
     "(J: \"THE WEBBING ON THE INSIDE SHOULDNTBE HERE\"): in danger the webs light up only on the walls and up in the "
     "vault between the ribs, the walkway stays clear, and a Hunter drops on its thread in front of you"),
    ("W1b5", "Weave Gallery inside: winding hall", "winding",
     "a lower hall that winds left and right so you only see to the next bend; in danger webs light up across every "
     "bend and a Hunter drops just ahead"),
    ("W1b6", "Weave Gallery inside: ledge over the pit", "ledge",
     "you walk a narrow ledge along the left wall over a deep dark pit; in danger nets of silk across the pit light up "
     "below you and Hunters climb them toward you"),
]


# =============================================================== v2.0114 (round 7): natural entrances, one at a time
# J on v2.0113 W1a5a (IMPROVE): "try to make it look natural, it should be calculated to be as common as a certain
# rivine is mountain is, it should be random though It shouldnt be obvious that whatever it is associated with spawns
# the tunnel systems". Then "3 new versions, one by one": each version is shown to J on its own and steers the next.
# Rule: an entrance is an ordinary natural feature (as common as a ravine or mountain type, placed at random), with
# nothing that always marks a Warren or the spider lair. Only DANGER gives it away.
PASS = "v2.0114"
M.update({
    "coal_ore": mat("coal ore", (0.16, 0.16, 0.17), 0.9, speck=1.0),
    "iron_ore": mat("iron ore", (0.3, 0.24, 0.19), 0.85, speck=0.9),
    "moss_rock": mat("mossy stone", (0.12, 0.16, 0.1), 0.9, speck=0.8),
})
WORLD_LABELS.update({15: "coal_ore", 16: "iron_ore", 17: "moss_rock"})


def mine_corridor(G, x_c, y0, y1, z_floor, rng, drop_every=7, frames_every=4, broken=(), rails=True, hw=2, h=4):
    """An old mineshaft corridor along +y (2*hw+1 wide, h tall), stepping down a block every drop_every; timber frames
    (two posts against the walls and a beam under the roof) every frames_every blocks, a rail line on the floor."""
    floors = {}
    zf = z_floor
    for y in range(int(y0), int(y1)):
        if drop_every and y > y0 and (y - y0) % drop_every == 0:
            zf -= 1
        floors[y] = zf
        G[x_c - hw:x_c + hw + 1, y, zf:zf + h] = 0
        if rails:
            G[x_c, y, zf - 1] = 13
        if (y - int(y0)) % frames_every == 2:
            if y in broken:                              # a broken frame: one post left, the beam gone
                G[x_c - hw, y, zf:zf + h - 1] = 7
            else:
                G[x_c - hw, y, zf:zf + h - 1] = 7; G[x_c + hw, y, zf:zf + h - 1] = 7
                G[x_c - hw:x_c + hw + 1, y, zf + h - 1] = 7
    return floors


def build_natural(X, code, name, seed, facts, v):
    """A hillside with an ordinary cave mouth, the kind the game makes everywhere. kind = v["kind"]."""
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = 64, 56, 40
    G = np.zeros((nx, ny, nz), dtype=np.int16)
    xx, yy, zz = np.mgrid[0:nx, 0:ny, 0:nz]
    n2 = smooth_noise((nx, ny), rng, 12)
    kind = v.get("kind", "hillside")
    # rolling ground rising into a hill in front of you
    mx, my = v.get("mouth", (31.0, 19.0))
    hill = np.clip((yy[:, :, 0] + 0.5 - (my - 1.0)) * v.get("slope", 1.4), 0, 16) * (1 + n2 * 0.15) + n2 * 0.45
    if kind == "sinkhole":
        hill = n2 * 0.0 + 0.4
    gnd = (20 + hill).astype(int)
    grass_skin(G, gnd)
    G[(G == 1) & (rng.random(G.shape) < 0.012)] = 15                       # coal and iron in the stone, as anywhere
    G[(G == 1) & (rng.random(G.shape) < 0.006)] = 16
    # the cave mouth: an irregular hole in the hill face that turns downward out of sight
    mz = float(gnd[int(mx), int(my) - 2])
    if kind == "cliff":   # a bare stone cliff face with grass only on top, scree at its foot, a tall crack in it
        top_ = gnd[:, :, None]
        face = (yy >= my - 1) & (zz < top_ - 1) & (zz >= mz)
        G[face & (G > 0)] = 1
        G[(G == 1) & face & (rng.random(G.shape) < 0.02)] = 15
        for k in range(70):
            x_, y_ = int(rng.normal(mx, 7)), int(rng.uniform(my - 4.5, my - 1))
            if 0 <= x_ < nx and abs(x_ - mx) > 1.4:
                G[x_, y_, int(mz) + (1 if rng.random() < 0.3 else 0)] = 8 if rng.random() < 0.6 else 1
        for t in range(7):    # the crack: narrow and tall, jagged, zig-zagging and pinching as it goes up and in
            hgt = 5.5 - t * 0.4
            zig = np.sin((zz + 0.5 - mz) * 1.1 + t) * 0.35 + np.sin((zz + 0.5) * 2.3) * 0.15
            wid = 0.9 - t * 0.05 - np.clip((zz + 0.5 - mz - 2.5) * 0.12, 0, 0.5)
            G[(np.abs(xx + 0.5 - mx - zig) < wid) & (yy == int(my) - 1 + t) & (zz >= mz) & (zz < mz + hgt)] = 0
        for k in range(14):   # a few stones broken out of the crack's lips
            q = (int(mx + rng.choice([-1, 1]) * rng.uniform(0.8, 1.6)), int(my) - 1, int(mz + rng.uniform(0, 4)))
            if 0 <= q[0] < nx and rng.random() < 0.5:
                G[q] = 0
        if v.get("deeper"):   # behind the crack it opens onto a dark slope going down
            ellip(G, (mx, my + 6.5, mz + 1.2), (2.2, 3.0, 2.4), 0)
            walk_tunnel(G, (mx, my + 8.5, mz + 0.5), (0.2, 1, -0.55), 10, 1.9, rng, wander=0.15)
            for t in range(4):
                G[(np.abs(xx + 0.5 - mx) < 1.3) & (yy == int(my) - 1 + t) & (zz >= mz) & (zz < mz + 2.2)] = 0
        pts = walk_tunnel(G, (mx, my + 6, mz + 0.8), (0, 1, -0.3), 7, 1.3, rng, wander=0.2)
        pts = [np.array([mx, my - 0.5, mz + 1.4]), np.array([mx, my + 2, mz + 1.2]), np.array([mx, my + 4, mz + 1.0])] + pts
    elif kind == "underground":   # you stand inside an old mineshaft deep in the hill
        G[:, :, :] = np.where(zz < 38, 1, 0)
        G[(G == 1) & (rng.random(G.shape) < 0.012)] = 15
        G[(G == 1) & (rng.random(G.shape) < 0.006)] = 16
        mz = 14.0
        xc = int(mx)
        floors = mine_corridor(G, xc, 1, 34, int(mz), rng, drop_every=0, broken=(26,))
        # the right wall broken through into a natural crack that drops away
        cy = 22
        ellip(G, (xc + 3.2, cy + 0.5, mz + 1.4), (1.3, 1.8, 1.8), 0)
        crack = walk_tunnel(G, (xc + 4.0, cy + 0.5, mz + 0.8), (1, 0.3, -0.5), 12, 1.4, rng, wander=0.3)
        G[xc, cy - 1:cy + 2, int(mz) - 1] = 1                     # the rail stops short of the break
        G[xc - 2:xc + 3, 31:34, int(mz):int(mz) + 4] = 8          # the far end collapsed in gravel
        G[xc - 2:xc + 3, 30, int(mz)] = 8
        pts = [np.array([xc + 0.5, 2.5, mz + 0.0])] + [np.array([xc + 0.5, y + 0.5, mz]) for y in range(4, cy)] + crack
    elif kind == "sinkhole":   # a ragged pit in a flat forest floor, dropping straight down
        mz = float(gnd[int(mx), int(my)])
        wob3 = smooth_noise(G.shape, rng, 3) * 0.45
        shaft = (np.hypot(xx + 0.5 - mx, yy + 0.5 - my) + wob3 < 2.4) & (zz < mz) & (zz >= mz - 13)
        G[shaft] = 0                                                       # a straight ragged shaft, 13 deep
        pts = [np.array([mx, my, mz - k]) for k in range(13)]
        pts += walk_tunnel(G, pts[-1], (0.3, 1, -0.4), 8, 1.6, rng, wander=0.3)
        pts = [pts[0] + np.array([0, 0, -0.5])] + pts
    else:
        pts = walk_tunnel(G, (mx, my - 0.5, mz + 1.4), (0, 1, v.get("dip", -0.2)), 9, v.get("mouth_r", 2.4), rng,
                          wander=0.2)
    if kind != "underground":
        pts += walk_tunnel(G, pts[-1], (0.3, 1, -0.6), 12, 1.5, rng, wander=0.3)
    if v.get("mine") == "cave_then_mine":      # a few blocks into the natural cave, an old mine runs on
        p3 = pts[3]
        mine_corridor(G, int(round(p3[0])), int(p3[1]), int(p3[1]) + 18, int(p3[2] - 1.0), rng, drop_every=6,
                      broken=(int(p3[1]) + 2,))
    if v.get("mine") == "crack_cross":         # behind the crack, an old mine corridor crosses left to right
        yc = int(my + 6)
        for x in range(int(mx) - 12, int(mx) + 12):
            G[x, yc - 1:yc + 2, int(mz):int(mz) + 3] = 0
            G[x, yc, int(mz) - 1] = 13
            if x % 4 == 0:
                G[x, yc - 1, int(mz):int(mz) + 2] = 7; G[x, yc + 1, int(mz):int(mz) + 2] = 7
                G[x, yc - 1:yc + 2, int(mz) + 2] = 7
    for p in (pts[:4] if kind != "cliff" else []):                        # a ragged rim
        for k in range(v.get("rough", 10)):
            q = np.floor(p + rng.normal(size=3) * np.array([1.6, 0.8, 1.2])).astype(int)
            if np.all(q >= 0) and np.all(q < G.shape) and rng.random() < 0.45:
                G[tuple(q)] = 0
    rim = dilate(G == 0) & (G > 0) & (np.hypot(xx + 0.5 - mx, yy + 0.5 - my) < 4.5) & (zz > mz - 3)
    G[rim & (G == 1) & (rng.random(G.shape) < (0.5 if kind != "cliff" else 0.15))] = 17   # moss round the mouth
    G[rim & (G == 1) & (rng.random(G.shape) < 0.08)] = 15
    # trees, grass and flowers like any hillside; nothing that marks the place
    trees_ = ((14, 30, 6), (46, 34, 5), (22, 44, 6), (52, 14, 5), (9, 10, 6), (40, 46, 6))
    if kind == "sinkhole":   # a forest: trees all round, the pit among them
        trees_ = tuple((int(rng.integers(3, nx - 3)), int(rng.integers(3, ny - 3)), int(rng.integers(5, 8))) for _ in range(30))
        trees_ = tuple(t for t in trees_ if not (abs(t[0] - mx) < 6 and t[1] < my + 4))   # keep your view of the pit open
    for (tx, ty, h) in trees_:
        if math.hypot(tx - mx, ty - my) > 7:
            tree(G, tx, ty, int(gnd[tx, ty]), h, rng)
    plants(G, rng, v.get("plants", 0), lambda x, y: math.hypot(x - mx, y - my) > 6.0, (11,))   # a few tufts only
    cam_g = np.array([mx + v.get("cam_dx", 1.5), my - v.get("cam_back", 14.0), 0.0])
    cam_g[2] = float(gnd[int(cam_g[0]), int(cam_g[1])]) + 1.6
    if kind == "underground":
        cam_g = np.array([int(mx) - 0.5, 4.6, mz + 1.6])         # between two frames, a little left
    near = (np.hypot(xx + 0.5 - cam_g[0], yy + 0.5 - cam_g[1]) < 4.5) & (zz >= cam_g[2] - 2.0)
    G[near & np.isin(G, (5, 6, 11, 12))] = 0
    off = np.array([-cam_g[0], -cam_g[1], -(cam_g[2] - 1.6)])
    world_block(code, G, off)
    calm_only = v.get("calm_only")
    # danger only: webs deep inside the mouth (never at the rim), eyes, a Hunter climbing out
    S = Strands(f"{code} silk")
    deep = pts[6:]
    for k, p in enumerate(deep[::3]):
        S.web(p, (0, 1, -0.3), 1.4, spokes=9, rings=4, rng=np.random.default_rng(seed + k))
    for k in range(10):
        a, b = deep[rng.integers(len(deep))], deep[rng.integers(len(deep))]
        S.seg(a + rng.normal(size=3) * 0.8, b + rng.normal(size=3) * 0.8)
    web_fade_mat()
    S.build("web_fade", loc=tuple(off))
    for k, p in enumerate([] if calm_only else deep[2::4][:3]):
        eo = eye_pair(f"{code} eyes {k}", tuple(p + off), (0, -1, 0), 1.0)
        appear(eo, tuple(p + off + np.array([0, 6, -6.0])))
    CUR.clear(); CUR.update({"dim": True})
    ob, _ = spider2(f"{code} hunter", "hunter", "plate", "rear", seed + 3)
    CUR.clear()
    if calm_only:
        bpy.data.objects.remove(ob, do_unlink=True)
    elif kind == "sinkhole":   # clinging to the pit wall, climbing up toward you
        orient(ob, belly=(0, 1, 0), head=(0, 0, 1)); ob.location = tuple(pts[3] + off + np.array([0, 1.7, 0]))
    else:
        place_on(ob, pts[2 if kind != "cliff" else 0] + off - np.array([0, 0, 1.2]), (0, 0, -1), (0, -1, 0), 2.6)
    if not calm_only:
        appear(ob, tuple(np.asarray(ob.location) + np.array([0, 10.0, -6.0])), DANGER_AT + 6, 18)
    lg = light(f"{code} deep glow", tuple(deep[len(deep) // 2] + off), (1.0, 0.55, 0.03), 0, cutoff=10)
    light_ramp(lg, 0, 140)
    light(f"{code} moon", (-6, -14, 20), (0.6, 0.7, 1.0), v.get("moon", 14000), cutoff=80, kind="AREA", size=34,
          rot=(math.radians(50), 0, math.radians(-15)))      # from behind you, shining onto the hill
    light(f"{code} ring", (0.35, 0.4, 1.35), (0.08, 1.0, 0.18), v.get("ring_e", 120), radius=0.05, cutoff=12)
    if v.get("inner"):          # a faint cold light a few blocks in, so the timbers inside just read
        light(f"{code} inner", tuple((pts[4] if kind != "cliff" else np.array([mx, my + 6.0, mz + 1.5])) + off),
              (0.6, 0.65, 0.8), v["inner"], radius=0.8, cutoff=10)
    if kind == "underground":   # a cold dim fill so the timbers read; the crack stays dark
        light(f"{code} mine fill", (0, 6, 2.2), (0.6, 0.65, 0.8), 260, radius=1.5, cutoff=30)
        light(f"{code} mine far", (0, 15, 2.2), (0.6, 0.65, 0.8), 160, radius=1.5, cutoff=20)
        light(f"{code} crack draught", (4.2, 17.9, 0.2), (0.55, 0.6, 0.75), 90, radius=0.6, cutoff=6)   # the break reads
    root = empty(f"{code} place", X); adopt(root, before)
    look = pts[0] + off + np.array([0, 0, {"cliff": 2.2, "sinkhole": -2.5}.get(kind, 0.6)]) + np.array([0, 1.6 if kind == "sinkhole" else 0, 0])
    if kind == "underground":
        look = np.array([0.4, 16.0, 1.0])
    cam = camera(f"Cam {code} {name}", X + np.array([0, 0, 1.6]), X + look, lens=v.get("lens", 32))
    if calm_only:
        add_take(code, name, cam, "static", facts + "; from eye height, just as you'd find it")
    else:
        add_take(code, name, cam, "turntable", facts + "; from eye height. The clip runs CALM for 3 seconds, then "
                 "DANGER: webs fade in deep inside (never at the rim), eyes open, a Hunter climbs out")


# --------------------------------------------------------------- the mineshaft design (J: "natural mineshafts that have the
# additional portion of ours attached to it ... preferredly in caves as usual under and maybe appearing on the walls of
# rivines"). Ordinary mineshaft corridors (3 wide, 3 tall, timber frames every 4, rails, crossings); one dead end carries
# our section: the timbers go on a few frames, then the tunnel turns round and dark and drops toward the Warren.
M.update({
    "old_wood": mat("old dark timber", (0.07, 0.045, 0.028), 0.9, speck=0.6),
    "ours_label": mat("label ours", (1.0, 0.6, 0.05), 0.5, emit=(1.0, 0.6, 0.05), es=0.8),
})
WORLD_LABELS.update({18: "old_wood"})
AX = {"+x": (0, 1), "-x": (0, -1), "+y": (1, 1), "-y": (1, -1)}


def mine_seg(G, start, axis, length, rng, frame_lab=7, frames=True, rails=True):
    """One straight corridor from start (x, y, floor z) along axis; returns the end cell."""
    ai, sg = AX[axis]
    p = list(map(int, start))
    for k in range(length):
        c = list(p)
        c[ai] += sg * k
        x, y, z = c
        if not (2 <= x < G.shape[0] - 2 and 2 <= y < G.shape[1] - 2):
            return c
        if ai == 0:                                   # 5 wide, 4 tall, so the frames read as frames, not doorways
            G[x, y - 2:y + 3, z:z + 4] = 0
        else:
            G[x - 2:x + 3, y, z:z + 4] = 0
        if rails and rng.random() < 0.8:
            G[x, y, z - 1] = 13
        if frames and k % 4 == 2:
            if ai == 0:
                G[x, y - 2, z:z + 3] = frame_lab; G[x, y + 2, z:z + 3] = frame_lab; G[x, y - 2:y + 3, z + 3] = frame_lab
            else:
                G[x - 2, y, z:z + 3] = frame_lab; G[x + 2, y, z:z + 3] = frame_lab; G[x - 2:x + 3, y, z + 3] = frame_lab
    c = list(p); c[ai] += sg * (length - 1)
    return c


def mine_network(G, centre, rng, depth=3):
    """A vanilla-like mineshaft: a central room, corridors branching at crossings. Returns the dead ends."""
    cx, cy, cz = map(int, centre)
    G[cx - 3:cx + 4, cy - 3:cy + 4, cz:cz + 4] = 0                        # the central room
    G[cx - 3:cx + 4, cy - 3:cy + 4, cz - 1] = 8
    ends = []

    def grow(p, axis, d):
        end = mine_seg(G, p, axis, int(rng.integers(9, 17)), rng)
        if d <= 0 or rng.random() < 0.2:
            ends.append((end, axis)); return
        x, y, z = end
        G[x - 2:x + 3, y - 2:y + 3, z:z + 4] = 0                          # a crossing
        turns = [a for a in AX if a[1] != axis[1]] + [axis]
        rng.shuffle(turns)
        for a in turns[:int(rng.integers(1, 3))]:
            grow(end, a, d - 1)

    for a in AX:
        start = [cx, cy, cz]
        start[AX[a][0]] += AX[a][1] * 4
        grow(start, a, depth)
    return ends


def our_section(G, end, axis, rng, n_frames=3):
    """Our part, attached to a mine's dead end: a few more frames in darker old timber, then the tunnel goes round,
    narrower and dark, and drops away toward the Warren."""
    e2 = mine_seg(G, end, axis, 4 * n_frames, rng, frame_lab=18, rails=False)
    ai, sg = AX[axis]
    d = np.zeros(3); d[ai] = sg; d[2] = -0.55
    pts = walk_tunnel(G, np.array(e2, float) + np.array([0.5, 0.5, 1.4]), d, 16, 1.6, rng, wander=0.15)
    for p in pts:   # the round tunnel lined in quiet dread stone
        lo = np.maximum(np.floor(p - 2.6).astype(int), 0); hi = np.minimum(np.ceil(p + 2.6).astype(int), G.shape)
        sub = G[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        sub[(sub == 1) | (sub == 15) | (sub == 16)] = 14
    return e2, pts


def mine_cave_ground(R, Hh, seed):
    G, xx, yy, zz, r, c, rng = chunk(R, Hh, seed)
    G[G > 0] = 1
    G[(G == 1) & (rng.random(G.shape) < 0.012)] = 15
    G[(G == 1) & (rng.random(G.shape) < 0.006)] = 16
    return G, xx, yy, zz, r, c, rng


def build_mine_overview(X, code, name, seed, facts):
    """A cutaway lump of underground: natural caves, an ordinary mineshaft in them, and our section on one dead end."""
    before = set(o.name for o in scene.objects)
    R, Hh = 34, 22
    G, xx, yy, zz, r, c, rng = mine_cave_ground(R, Hh, seed)
    for k in range(5):                                   # natural caves winding through, as anywhere underground
        a = rng.uniform(0, 2 * math.pi)
        walk_tunnel(G, (c + math.cos(a) * 20, c + math.sin(a) * 20, rng.uniform(8, 14)),
                    (-math.cos(a), -math.sin(a), 0.05), 40, rng.uniform(1.8, 2.8), rng, wander=0.35)
    mz = 12
    ends = mine_network(G, (c, c, mz), rng, depth=2)
    far = max(ends, key=lambda e: math.hypot(e[0][0] - c, e[0][1] - c))
    e2, pts = our_section(G, far[0], far[1], rng)
    G[zz >= mz + 4] = 0                                  # the roof cut away so the corridors read like a map
    G[(r > R - 1)] = 0
    off = np.array([-c, -c, -float(mz)])
    blocks(f"{code} ground", G, tuple(off), WORLD_LABELS)
    lt = label_text(f"{code} label ours", "OUR SECTION", tuple(np.array(e2, float) + off + np.array([0, 0, 6.0])),
                    size=2.2, mk="ours_label")
    root = empty(f"{code} turn", X); spin(root); adopt(root, before)
    light(f"{code} fill", X + np.array([-20, -30, 40]), (0.75, 0.78, 0.9), 30000, cutoff=120, kind="AREA", size=40,
          rot=(math.radians(40), 0, math.radians(-30)))
    cam = camera(f"Cam {code} {name}", X + np.array([0, -58, 52]), X + np.array([0, 0, -3]), lens=30)
    add_take(code, name, cam, "turntable", facts)


def build_mine_ravine(X, code, name, seed, facts):
    """A ravine whose walls cut through an ordinary mineshaft: corridor mouths in both walls, a plank bridge across,
    and one corridor on the far wall that is ours."""
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = 64, 48, 34
    G = np.zeros((nx, ny, nz), dtype=np.int16)
    xx, yy, zz = np.mgrid[0:nx, 0:ny, 0:nz]
    n2 = smooth_noise((nx, ny), rng, 6)
    gnd = (24 + n2 * 0.6).astype(int)
    grass_skin(G, gnd)
    G[(G == 1) & (rng.random(G.shape) < 0.012)] = 15
    cy = 22.0
    for z in range(3, nz):
        half = 1.6 + max(0, z - 3) * 0.17
        G[:, :, z][np.abs(yy[:, :, 0] + 0.5 - cy) < half + n2 * 0.3] = 0
    mz = 13
    # mineshaft corridors running along both walls just behind the face, cut open where the ravine crosses them
    near_w = int(cy - (1.6 + (mz - 3) * 0.17)) - 2
    far_w = int(cy + (1.6 + (mz - 3) * 0.17)) + 2
    mine_seg(G, (8, near_w, mz), "+x", 48, rng)
    mine_seg(G, (8, far_w, mz), "+x", 48, rng)
    mine_seg(G, (30, far_w, mz), "+y", 14, rng)                 # an ordinary corridor going on into the far wall
    G[29:32, int(cy) - 4:int(cy) + 5, mz - 1] = 7               # the plank bridge the mine built across the ravine
    e2, pts = our_section(G, (44, far_w, mz), "+y", rng, n_frames=2)
    for (tx, ty, h) in ((12, 6, 6), (50, 8, 5), (20, 40, 6), (46, 42, 5)):
        tree(G, tx, ty, int(gnd[tx, ty]), h, rng)
    cam_g = np.array([30.5, cy, mz + 1.6])                      # standing on the mine's plank bridge
    off = np.array([-cam_g[0], -cam_g[1], -(cam_g[2] - 1.6)])
    world_block(code, G, off)
    light(f"{code} moon", (-6, -14, 20), (0.6, 0.7, 1.0), 14000, cutoff=80, kind="AREA", size=34,
          rot=(math.radians(50), 0, math.radians(-15)))
    light(f"{code} ravine fill", tuple(np.array([36, cy, 16]) + off), (0.6, 0.65, 0.8), 600, radius=3, cutoff=30)
    root = empty(f"{code} place", X); adopt(root, before)
    look = np.array([52.0, cy + 1.0, mz + 1.4]) + off
    cam = camera(f"Cam {code} {name}", X + np.array([0, 0, 1.6]), X + look, lens=24)
    add_take(code, name, cam, "static", facts)


def build_mine_inside(X, code, name, seed, facts):
    """Inside an ordinary mineshaft corridor, looking down it to where it becomes ours."""
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = 24, 44, 24
    G = np.ones((nx, ny, nz), dtype=np.int16)
    G[(G == 1) & (rng.random(G.shape) < 0.012)] = 15
    G[(G == 1) & (rng.random(G.shape) < 0.006)] = 16
    xc, mz = 12, 12
    end = mine_seg(G, (xc, 2, mz), "+y", 13, rng)
    G[xc - 1:xc + 2, 7:10, mz:mz + 3] = 0
    walk_tunnel(G, (xc - 2, 8.5, mz + 1.2), (-1, 0.2, 0), 8, 1.4, rng, wander=0.2)   # a side cave, as mines have
    e2, pts = our_section(G, (xc, 15, mz), "+y", rng, n_frames=2)
    off = np.array([-(xc + 0.5), -4.5, -float(mz)])
    blocks(f"{code} mine", G, tuple(off), WORLD_LABELS)
    light(f"{code} fill", (0, 4, 2.2), (0.6, 0.65, 0.8), 220, radius=1.5, cutoff=30)
    light(f"{code} far", (0, 14, 2.2), (0.6, 0.65, 0.8), 140, radius=1.5, cutoff=14)
    light(f"{code} ring", (0.35, 0.4, 1.35), (0.08, 1.0, 0.18), 8, radius=0.05, cutoff=12)
    root = empty(f"{code} place", X); adopt(root, before)
    cam = camera(f"Cam {code} {name}", X + np.array([0, 0, 1.6]), X + np.array([0, 18, 0.6]), lens=24)
    add_take(code, name, cam, "static", facts)


MINES = [
    ("W1a7a", "Mineshaft entrance: the whole mine, ours on one end", build_mine_overview, 401,
     "J: \"natural mineshafts that have the additional portion of ours attached to it\": a cutaway of underground with "
     "natural caves and an ordinary mineshaft (a central room, corridors 3 wide with timber frames every 4 blocks and "
     "rails, crossings, dead ends). On one dead end (labelled) our section carries on: a few more frames in old dark "
     "timber, then the tunnel goes round and narrow, lined in dark stone, and drops toward the Warren. In the game, any "
     "mineshaft within the Warren's own radius (about 200 blocks) has a chance to carry it; turns"),
    ("W1a7b", "Mineshaft entrance: cut open on a ravine wall", build_mine_ravine, 402,
     "\"maybe appearing on the walls of rivines\": a ravine that cuts through an ordinary mineshaft, corridor mouths "
     "open in both walls with their timbers, the plank bridge the mine built across; one corridor on the far wall is "
     "ours (it looks the same from here); standing on the mine's plank bridge looking along the ravine at the corridor mouths in both walls"),
    ("W1a7c", "Mineshaft entrance: inside, where it becomes ours", build_mine_inside, 403,
     "inside an ordinary mineshaft corridor with a side cave off it; ahead the timbers turn old and dark for two frames, "
     "then the corridor ends in a round, narrow tunnel dropping away: the only sign it isn't just a mine"),
]


# =============================================================== v2.0115 (round 8): more scenarios, textured, a modern shaft
# J on v2.0114 W1a7a-c: "all three are good, more scenarios like this, perfect utilization of existing generations,it
# will be textured naturally or can you attempt updated themed modern looking shafts even though naturally generated
# modern ones would be perfect, the cave would need texturing". In the game these are the game's own blocks, so they
# take Minecraft's textures (and J's pack and shaders); here the stand-ins get pixel textures so they read closer.
PASS = "v2.0115"


def tex_mat(name, kind, c1, c2, rough=0.85, metal=0.0, emit=None, es=0.0, scale=1.0):
    """A 16-pixels-per-block procedural texture between two colours: noise (stone, dirt), cobble (cells with dark
    joints), planks (boards), panel (steel plates with seams)."""
    m = mat(name, c1, rough, metal, emit, es)
    N, L = m.node_tree.nodes, m.node_tree.links
    p = _bsdf(m)
    co = _pixel_coords(m)
    ramp = N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].color = (*c1, 1); e[1].color = (*c2, 1)
    if kind == "cobble":
        t = N.new("ShaderNodeTexVoronoi"); t.inputs["Scale"].default_value = 2.2 * scale
        L.new(co, t.inputs["Vector"]); L.new(t.outputs["Distance"], ramp.inputs["Fac"])
        e[0].position, e[1].position = 0.05, 0.55
        e[0].color = (*[x * 0.45 for x in c1], 1)
    elif kind == "planks":
        t = N.new("ShaderNodeTexWave"); t.wave_type = "BANDS"; t.bands_direction = "Z"
        t.inputs["Scale"].default_value = 1.6 * scale; t.inputs["Distortion"].default_value = 1.5
        L.new(co, t.inputs["Vector"]); L.new(t.outputs["Fac"], ramp.inputs["Fac"])
    elif kind == "panel":
        t = N.new("ShaderNodeTexWave"); t.wave_type = "BANDS"; t.bands_direction = "X"
        t.inputs["Scale"].default_value = 0.9 * scale; t.inputs["Distortion"].default_value = 0.0
        L.new(co, t.inputs["Vector"]); L.new(t.outputs["Fac"], ramp.inputs["Fac"])
        e[0].position, e[1].position = 0.02, 0.12
    else:
        t = N.new("ShaderNodeTexNoise"); t.inputs["Scale"].default_value = 3.5 * scale
        t.inputs["Detail"].default_value = 2.0
        L.new(co, t.inputs["Vector"]); L.new(t.outputs["Fac"], ramp.inputs["Fac"])
        e[0].position, e[1].position = 0.35, 0.65
    L.new(ramp.outputs["Color"], p.inputs["Base Color"])
    return m


M.update({
    "tx_stone": tex_mat("tex stone", "noise", (0.26, 0.26, 0.27), (0.42, 0.42, 0.43)),
    "tx_deep": tex_mat("tex deepslate", "noise", (0.1, 0.1, 0.12), (0.2, 0.2, 0.22)),
    "tx_dirt": tex_mat("tex dirt", "noise", (0.2, 0.13, 0.08), (0.32, 0.22, 0.14)),
    "tx_grass": tex_mat("tex grass", "noise", (0.15, 0.3, 0.09), (0.26, 0.45, 0.14)),
    "tx_log": tex_mat("tex log", "planks", (0.18, 0.12, 0.07), (0.3, 0.21, 0.12), scale=2.0),
    "tx_leaf": tex_mat("tex leaves", "noise", (0.05, 0.16, 0.04), (0.12, 0.3, 0.08), scale=2.0),
    "tx_plank": tex_mat("tex oak planks", "planks", (0.36, 0.26, 0.14), (0.5, 0.38, 0.22)),
    "tx_gravel": tex_mat("tex gravel", "cobble", (0.36, 0.34, 0.33), (0.5, 0.48, 0.46), scale=2.0),
    "tx_rail": tex_mat("tex rail", "panel", (0.18, 0.16, 0.15), (0.45, 0.42, 0.4), rough=0.4, metal=0.7),
    "tx_dread": tex_mat("tex dread stone", "noise", (0.03, 0.028, 0.034), (0.08, 0.07, 0.06)),
    "tx_oldwood": tex_mat("tex old dark timber", "planks", (0.06, 0.04, 0.025), (0.12, 0.08, 0.05)),
    "tx_coal": tex_mat("tex coal ore", "cobble", (0.04, 0.04, 0.04), (0.38, 0.38, 0.39), scale=1.6),
    "tx_iron": tex_mat("tex iron ore", "cobble", (0.55, 0.42, 0.32), (0.4, 0.4, 0.41), scale=1.6),
    "tx_cobble": tex_mat("tex cobblestone", "cobble", (0.2, 0.2, 0.2), (0.34, 0.34, 0.34)),
    "tx_mossy": tex_mat("tex mossy cobblestone", "cobble", (0.14, 0.22, 0.11), (0.3, 0.34, 0.27)),
    "tx_drip": tex_mat("tex dripstone", "noise", (0.3, 0.24, 0.2), (0.45, 0.37, 0.3), scale=1.5),
    "tx_steel": tex_mat("tex steel beam", "panel", (0.08, 0.09, 0.1), (0.28, 0.3, 0.32), rough=0.35, metal=0.9),
    "tx_concrete": tex_mat("tex shaft concrete", "noise", (0.4, 0.4, 0.39), (0.55, 0.55, 0.53), scale=2.0),
    "tx_lamp": mat("dead shaft lamp", (0.7, 0.68, 0.6), 0.2, emit=(1.0, 0.9, 0.7), es=0.35, alpha=0.9),
    "tx_spawner": tex_mat("tex spawner cage", "panel", (0.05, 0.06, 0.08), (0.2, 0.22, 0.26), rough=0.4, metal=0.8, scale=3.0),
    "tx_chest": tex_mat("tex chest", "planks", (0.4, 0.26, 0.1), (0.55, 0.38, 0.16)),
})
TEX = {1: "tx_stone", 2: "tx_deep", 3: "tx_dirt", 4: "tx_grass", 5: "tx_log", 6: "tx_leaf", 7: "tx_plank",
       8: "tx_gravel", 13: "tx_rail", 14: "tx_dread", 15: "tx_coal", 16: "tx_iron", 17: "tx_mossy", 18: "tx_oldwood",
       19: "tx_steel", 20: "tx_concrete", 21: "tx_lamp", 22: "tx_cobble", 23: "tx_mossy", 24: "tx_spawner",
       25: "tx_chest", 26: "tx_drip"}


def textured(fn):
    """Run a v2.0114 builder with the textured materials swapped in."""
    def run(*a):
        saved = dict(WORLD_LABELS)
        WORLD_LABELS.update(TEX)
        try:
            fn(*a)
        finally:
            WORLD_LABELS.clear(); WORLD_LABELS.update(saved)
    return run


def build_modern_shaft(X, code, name, seed, facts):
    """A modern mine shaft: steel frames, concrete lining, a cable run, dead lamps; at the end, our round tunnel."""
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = 24, 44, 24
    G = np.ones((nx, ny, nz), dtype=np.int16)
    G[(G == 1) & (rng.random(G.shape) < 0.012)] = 15
    xc, mz = 12, 12
    yy = np.arange(ny)[None, :, None] + 0 * np.zeros((nx, 1, nz))
    mine_seg(G, (xc, 2, mz), "+y", 13, rng, frame_lab=19)
    lining = dilate(G == 0) & (G > 0) & (G != 19) & (yy < 15)
    G[lining] = 20                                                       # a concrete lining round the shaft
    for y in range(2, 15):
        if (y - 2) % 4 == 2:
            G[xc, y, mz + 3] = 21                                       # a lamp in every frame, all but dead
        G[xc, y, mz - 1] = 13 if rng.random() < 0.9 else 20
    e2, pts = our_section(G, (xc, 15, mz), "+y", rng, n_frames=0)
    off = np.array([-(xc + 0.5), -4.5, -float(mz)])
    blocks(f"{code} shaft", G, tuple(off), TEX)
    C = Strands(f"{code} cable")
    C.poly([np.array([1.6, y, 3.6 - 0.15 * math.sin(y * 0.8)]) for y in np.linspace(-2.5, 10.4, 24)], PX * 2)
    C.build("shell")
    light(f"{code} fill", (0, 4, 2.6), (0.75, 0.75, 0.72), 200, radius=1.5, cutoff=30)
    light(f"{code} last lamp", (0, 9.5, 3.4), (1.0, 0.9, 0.7), 60, radius=0.3, cutoff=10)
    light(f"{code} ring", (0.35, 0.4, 1.35), (0.08, 1.0, 0.18), 8, radius=0.05, cutoff=12)
    root = empty(f"{code} place", X); adopt(root, before)
    cam = camera(f"Cam {code} {name}", X + np.array([0, 0, 1.6]), X + np.array([0, 18, 0.6]), lens=24)
    add_take(code, name, cam, "static", facts)


def build_dungeon(X, code, name, seed, facts):
    """A plain dungeon (cobblestone room, spawner, chest); one wall has cracked into our tunnel behind it."""
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = 26, 34, 22
    G = np.ones((nx, ny, nz), dtype=np.int16)
    G[(G == 1) & (rng.random(G.shape) < 0.012)] = 15
    x0, x1, y0, y1, z0, z1 = 9, 16, 3, 10, 10, 14
    G[x0 - 1:x1 + 1, y0 - 1:y1 + 1, z0 - 1:z1 + 1] = 22                 # the dungeon's cobblestone shell
    G[x0 - 1:x1 + 1, y0 - 1:y1 + 1, z0 - 1][rng.random((x1 - x0 + 2, y1 - y0 + 2)) < 0.6] = 23
    shell = G == 22
    G[shell & (rng.random(G.shape) < 0.3)] = 23
    G[x0:x1, y0:y1, z0:z1] = 0
    G[12, 6, z0] = 24                                                    # the spawner
    G[x0, y0 + 2, z0] = 25; G[x1 - 1, y1 - 2, z0] = 25                   # two chests against the walls
    # the far wall has cracked through into our round tunnel
    for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (-1, 1), (2, 1), (1, 2)):
        G[12 + dx, y1, z0 + dz] = 0
    G[13, y1, z0 + 3] = 0
    e2, pts = our_section(G, (12, y1 + 1, z0), "+y", rng, n_frames=0)
    for k in range(6):                                                  # rubble from the broken wall on the floor
        G[int(rng.integers(11, 15)), y1 - 1 - int(rng.integers(0, 2)), z0] = 22 if k % 2 else 23
    off = np.array([-12.5, -(y0 + 0.6), -float(z0)])
    blocks(f"{code} dungeon", G, tuple(off), TEX)
    light(f"{code} fill", (0, 2.5, 2.4), (0.7, 0.72, 0.8), 140, radius=1.2, cutoff=20)
    light(f"{code} ring", (0.35, 0.4, 1.35), (0.08, 1.0, 0.18), 3, radius=0.05, cutoff=12)
    root = empty(f"{code} place", X); adopt(root, before)
    cam = camera(f"Cam {code} {name}", X + np.array([-1.6, 0, 1.6]), X + np.array([0.4, 7.0, 1.0]), lens=22)
    add_take(code, name, cam, "static", facts)


def build_dripstone(X, code, name, seed, facts):
    """A dripstone cave as the game makes them; behind the stalagmites at the foot of the far wall, our tunnel."""
    before = set(o.name for o in scene.objects)
    rng = np.random.default_rng(seed)
    nx, ny, nz = 40, 40, 26
    G = np.ones((nx, ny, nz), dtype=np.int16)
    xx, yy, zz = np.mgrid[0:nx, 0:ny, 0:nz]
    wob = smooth_noise(G.shape, rng, 3) * 1.2
    cave = ((xx + 0.5 - 20) / 15) ** 2 + ((yy + 0.5 - 20) / 15) ** 2 + ((zz + 0.5 - 11) / 8) ** 2 + wob * 0.08 < 1
    G[cave] = 0
    G[(G == 1) & dilate(cave) & (rng.random(G.shape) < 0.55)] = 26      # dripstone blocks on the cave's skin
    for k in range(70):                                                 # pointed dripstone, down and up
        x, y = rng.uniform(7, 33), rng.uniform(7, 33)
        col = np.nonzero(G[int(x), int(y), :] == 0)[0]
        if not len(col):
            continue
        lo_, hi_ = col[0], col[-1]
        ln = rng.uniform(1.5, 5.5)
        if k % 2:
            capsule(G, (x, y, hi_ + 0.9), (x, y, hi_ + 0.9 - ln), 0.35 + ln * 0.08, 26, only_empty=True)
        else:
            capsule(G, (x, y, lo_), (x, y, lo_ + ln * 0.8), 0.35 + ln * 0.08, 26, only_empty=True)
    # our tunnel at the foot of the far wall
    wy = int(np.max(np.nonzero(G[20, :, 6] == 0)[0])) + 1
    e2, pts = our_section(G, (20, wy - 1, 5), "+y", rng, n_frames=0)
    G[19:22, wy - 2:wy, 5:8][G[19:22, wy - 2:wy, 5:8] == 26] = 0
    floor_z = int(np.nonzero(G[20, 8, :] == 0)[0][0])
    off = np.array([-20.5, -8.0, -float(floor_z)])
    blocks(f"{code} cave", G, tuple(off), TEX)
    light(f"{code} fill", (0, 10, 6), (0.75, 0.72, 0.68), 900, radius=4, cutoff=40)
    light(f"{code} ring", (0.35, 0.4, 1.35), (0.08, 1.0, 0.18), 3, radius=0.05, cutoff=12)
    root = empty(f"{code} place", X); adopt(root, before)
    look = np.array([20.5, wy - 1.0, 6.5]) + off
    cam = camera(f"Cam {code} {name}", X + np.array([0, 0, 1.6]), X + look, lens=24)
    add_take(code, name, cam, "static", facts)


R8 = [
    ("W1a8a", "Textured: inside a mine, where it becomes ours", textured(build_mine_inside), 403,
     "W1a7c with pixel textures (oak planks, stone with ore, rails, gravel); ours in dark textured stone. In the game "
     "these are the game's own blocks, so they take Minecraft's textures and your pack"),
    ("W1a8b", "Textured: a ravine through a mineshaft", textured(build_mine_ravine), 402,
     "W1a7b with pixel textures: grass, dirt, stone, the mine's planks and rails, from the plank bridge"),
    ("W1a8c", "Modern shaft", build_modern_shaft, 404,
     "J: \"can you attempt updated themed modern looking shafts\": a modern mine shaft (steel frames, a concrete lining, "
     "a cable run along the roof, a rail, lamps all but dead); at its end the concrete stops and our round dark tunnel "
     "goes on down"),
    ("W1a9a", "Dungeon broken into ours", build_dungeon, 405,
     "more scenarios on what the game already makes: a plain dungeon (cobblestone and mossy cobblestone, a spawner, two "
     "chests) whose far wall has cracked open, rubble on the floor, onto our round tunnel"),
    ("W1a9b", "Dripstone cave, ours behind the stalagmites", build_dripstone, 406,
     "a dripstone cave as the game makes them, pointed dripstone hanging and rising; at the foot of the far wall, "
     "behind the stalagmites, our round tunnel"),
]
BUILDS = []
for code, name, fn, seed, facts in R8:
    BUILDS.append((code, lambda X, a=(code, name, fn, seed, facts): a[2](X, a[0], a[1], a[3], a[4])))
ONLY = [s for s in os.environ.get("DW_ONLY", "").split(",") if s]
for i, (code, b) in enumerate(BUILDS):
    if ONLY and code not in ONLY:
        continue
    b(np.array([i * GAP, 0.0, 0.0]))

scene.camera = bpy.data.objects[TAKES[0][2]]
scene["dw_takes"] = repr(TAKES)
print(f"[{PASS}] built {len(TAKES)} takes, {len(scene.objects)} objects")
