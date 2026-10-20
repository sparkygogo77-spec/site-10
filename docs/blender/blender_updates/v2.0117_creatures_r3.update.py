# Pass v2.0117: creatures round 3: three new versions of each creature, animated at mob size (Trials; creatures r3 chat, 2026-10-20).
# Why: J picked "New iterations" for v2.0116 without rating it, so the v2.0116 models are the base (the chat's star picks:
#   KEEP all, IMPROVE PB4 "rise a bit slower/heavier", YE4 "the fold line is thin from far away", OE3 "the standing
#   curl reads less like a prayer") and each creature gets three new versions, each built differently and shown in a move:
#   PB7 lean sloth (longest arms, heavy slow rear-up), PB8 blizzard mane (shaggy, icy fur, walk), PB9 old scarred boar
#   (shoulder hump, yellowed fur, claw scars, long claws, swipe); YE10 bold fold teleport (a thick glowing seam),
#   YE11 fear-cracked shell (black core, thin yellow cracks, lantern slam), YE12 gaunt (thin limbs, pale eyes, lava throw);
#   OE4 standing prayer with the lantern raised to its face, OE5 both knees bowed over the lantern on the ground,
#   OE6 one knee, rocking, lantern pressed to its forehead, with ember speckles; SK8 scarred great white (bite),
#   SK9 hammerhead sweeping its head as it hunts, SK10 thresher stunning a fish with a tail whip.
# Every clip runs at Minecraft's 20 ticks a second (60 frames = 3 s); rigs, IK and per-frame checks are v2.0116's
#   (scene["v2_0117_checks"]).
# Rev 2 (J's site notes, 2026-10-20): PB8 fuller face; PB9 inward-turned paws with huge anteater claws; YE12 a fist
#   and a hard-light cage round the thrown element; OE4 hugging the lantern to its chest greedily.
# Builds the whole scene from nothing (globals bpy, np, FOLDER); the renderer saves it as trials/creatures_r3.blend.

import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

PASS = "v2.0117"
FRAMES = (1, 60)
GAP = 160.0
PX = 1.0 / 16.0

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene
scene.name = "Creatures R3"
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
world = bpy.data.worlds.new("GES World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.05, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

try:   # glow: bloom fed from Render Layers, Standard view keeps the colours saturated
    tree = bpy.data.node_groups.new("GES Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.5), ("Strength", 0.45), ("Threshold", 0.9)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)


# --------------------------------------------------------------- materials
def _set(p, name, val):
    if name in p.inputs:
        p.inputs[name].default_value = val


def mat(name, base, rough=0.6, metal=0.0, emit=None, es=0.0, alpha=1.0):
    m = bpy.data.materials.new("GES " + name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    _set(p, "Base Color", (*base, 1)); _set(p, "Roughness", rough); _set(p, "Metallic", metal)
    if emit:
        _set(p, "Emission Color", (*emit, 1)); _set(p, "Emission Strength", min(es, 1.5))
    if alpha < 1.0:
        _set(p, "Alpha", alpha)
        try:
            m.surface_render_method = "DITHERED"   # BLENDED writes no depth: see-through at some angles (608)
        except Exception:
            pass
    return m


def pmat(name, lo, hi, rough=0.7, metal=0.0, cell=0.25, emit=None, es=0.0, alpha=1.0):
    """Pixel-art colour: every voxel cell gets its own shade between lo and hi (white noise on snapped coords)."""
    m = mat(name, hi, rough, metal, emit, es, alpha)
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    tc = N.new("ShaderNodeTexCoord")
    sh = N.new("ShaderNodeVectorMath"); sh.operation = "SCALE"
    L.new(tc.outputs["Normal"], sh.inputs[0]); sh.inputs["Scale"].default_value = -0.02   # step inside the face
    ad = N.new("ShaderNodeVectorMath"); ad.operation = "ADD"
    L.new(tc.outputs["Object"], ad.inputs[0]); L.new(sh.outputs["Vector"], ad.inputs[1])
    sn = N.new("ShaderNodeVectorMath"); sn.operation = "SNAP"
    sn.inputs[1].default_value = (cell,) * 3
    L.new(ad.outputs["Vector"], sn.inputs[0])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"
    L.new(sn.outputs["Vector"], wn.inputs["Vector"])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    a = [s for s in mix.inputs if s.name == "A" and s.type == "RGBA"][0]
    b = [s for s in mix.inputs if s.name == "B" and s.type == "RGBA"][0]
    a.default_value = (*lo, 1); b.default_value = (*hi, 1)
    L.new(wn.outputs["Value"], mix.inputs[0])
    L.new([o for o in mix.outputs if o.type == "RGBA"][0], p.inputs["Base Color"])
    return m


COMMON = {
    "ground": pmat("ground stone", (0.07, 0.07, 0.075), (0.13, 0.13, 0.14), 0.9, cell=0.5),
    "moss": pmat("ground moss", (0.07, 0.09, 0.05), (0.12, 0.15, 0.08), 0.95, cell=0.5),
    "suit": mat("player suit", (0.03, 0.035, 0.03), 0.6),
    "skin": mat("player skin", (0.55, 0.38, 0.27), 0.7),
    "ring": mat("ring green", (0.05, 1.0, 0.15), 0.2, emit=(0.05, 1.0, 0.15), es=1.4),
    "water": mat("water", (0.02, 0.09, 0.17), 0.04, alpha=0.45),
    "poolbed": pmat("pool bed", (0.02, 0.04, 0.06), (0.05, 0.08, 0.1), 0.9, cell=0.5),
    "foam": pmat("foam", (0.75, 0.85, 0.92), (0.95, 0.98, 1.0), 0.4, alpha=0.9),
}


# --------------------------------------------------------------- voxel grid in world blocks
class Vox:
    def __init__(self, lo, hi, step):
        self.lo = np.asarray(lo, float); self.step = step
        self.shape = tuple(int(v) for v in np.ceil((np.asarray(hi, float) - self.lo) / step))
        self.G = np.zeros(self.shape, np.int16)

    def axes(self):
        return [self.lo[i] + (np.arange(self.shape[i]) + 0.5) * self.step for i in range(3)]

    def _rng(self, a, b):
        i0 = np.floor((np.asarray(a, float) - self.lo) / self.step).astype(int) - 1
        i1 = np.ceil((np.asarray(b, float) - self.lo) / self.step).astype(int) + 1
        return np.clip(i0, 0, self.shape), np.clip(i1, 0, self.shape)

    def _pts(self, i0, i1):
        g = np.mgrid[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]].astype(np.float64)
        return (g + 0.5) * self.step + self.lo[:, None, None, None]

    def region(self, c, ext, fn, lab, only_empty=False, only_full=False):
        """fn(local points (3,...)) -> bool mask (or label array when lab is None) for the box c +- ext."""
        c = np.asarray(c, float); ext = np.broadcast_to(np.asarray(ext, float), (3,))
        i0, i1 = self._rng(c - ext, c + ext)
        if np.any(i1 <= i0):
            return
        P = self._pts(i0, i1)
        sub = self.G[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]]
        m = fn(P)
        if only_empty:
            m = m & (sub == 0)
        if only_full:
            m = m & (sub > 0)
        sub[m] = lab

    def ell(self, c, r, lab, R=None, **kw):
        c = np.asarray(c, float); r = np.asarray(r, float)
        Rt = None if R is None else np.asarray(R, float)

        def fn(P):
            d = P - c[:, None, None, None]
            if Rt is not None:
                d = np.einsum("ji,j...->i...", Rt, d)
            return (d[0] / r[0]) ** 2 + (d[1] / r[1]) ** 2 + (d[2] / r[2]) ** 2 <= 1.0
        self.region(c, r.max() if R is not None else r, fn, lab, **kw)

    def cap(self, a, b, r1, lab, r2=None, **kw):
        a, b = np.asarray(a, float), np.asarray(b, float)
        r2 = r1 if r2 is None else r2
        ab = b - a; L2 = max(ab @ ab, 1e-9)

        def fn(P):
            d = P - a[:, None, None, None]
            t = np.clip(np.einsum("i,i...->...", ab, d) / L2, 0, 1)
            q = d - ab[:, None, None, None] * t
            rr = r1 + (r2 - r1) * t
            return (q ** 2).sum(0) <= rr * rr
        rm = max(r1, r2)
        self.region((a + b) / 2, np.abs(ab) / 2 + rm, fn, lab, **kw)

    def obox(self, c, half, R, lab, rim=0.0, rim_lab=None, thin=1, **kw):
        c = np.asarray(c, float); half = np.asarray(half, float); Rt = np.asarray(R, float)

        def loc(P):
            return np.einsum("ji,j...->i...", Rt, P - c[:, None, None, None])

        def fn(P):
            d = loc(P)
            return (np.abs(d[0]) <= half[0]) & (np.abs(d[1]) <= half[1]) & (np.abs(d[2]) <= half[2])
        ext = np.linalg.norm(half)
        self.region(c, ext, fn, lab, **kw)
        if rim > 0 and rim_lab:
            def fr(P):
                d = loc(P)
                inside = (np.abs(d[0]) <= half[0]) & (np.abs(d[1]) <= half[1]) & (np.abs(d[2]) <= half[2])
                edge = np.zeros_like(inside)
                for ax in range(3):
                    if ax != thin:
                        edge |= np.abs(d[ax]) > half[ax] - rim
                return inside & edge
            self.region(c, ext, fr, rim_lab, only_full=True)

    def octa(self, c, rad, R, lab, **kw):
        c = np.asarray(c, float); rad = np.asarray(rad, float); Rt = np.asarray(R, float)

        def fn(P):
            d = np.einsum("ji,j...->i...", Rt, P - c[:, None, None, None])
            return np.abs(d[0]) / rad[0] + np.abs(d[1]) / rad[1] + np.abs(d[2]) / rad[2] <= 1.0
        self.region(c, rad.max(), fn, lab, **kw)

    def tri(self, p0, p1, p2, thick, lab, edge_lab=None, edge_w=0.3, **kw):
        """A flat fin: triangle p0-p1 (root) to p2 (tip), `thick` thick; the two outer edges glow if edge_lab."""
        p0, p1, p2 = (np.asarray(p, float) for p in (p0, p1, p2))
        n = np.cross(p1 - p0, p2 - p0); n /= np.linalg.norm(n)
        lo = np.minimum(np.minimum(p0, p1), p2) - thick; hi = np.maximum(np.maximum(p0, p1), p2) + thick
        e0, e1 = p1 - p0, p2 - p0
        d00, d01, d11 = e0 @ e0, e0 @ e1, e1 @ e1
        den = d00 * d11 - d01 * d01

        def bary(P):
            d = P - p0[:, None, None, None]
            h = np.einsum("i,i...->...", n, d)
            d20 = np.einsum("i,i...->...", e0, d); d21 = np.einsum("i,i...->...", e1, d)
            v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
            return h, v, w

        def fn(P):
            h, v, w = bary(P)
            return (np.abs(h) <= thick / 2) & (v >= 0) & (w >= 0) & (v + w <= 1)
        self.region((lo + hi) / 2, (hi - lo) / 2, fn, lab, **kw)
        if edge_lab:
            def fe(P):
                h, v, w = bary(P)
                m = (np.abs(h) <= thick / 2) & (v >= 0) & (w >= 0) & (v + w <= 1)
                # distance (in barycentric units scaled by edge length) to the outer edges p1-p2 and p0-p2
                L = max(np.linalg.norm(e0), np.linalg.norm(e1))
                return m & ((1 - v - w) * L < edge_w * 1.2)   # the trailing edge (p1-p2) only
            self.region((lo + hi) / 2, (hi - lo) / 2, fe, edge_lab, only_full=True)


def surface(G):
    P = np.pad(G > 0, 1)
    inside = np.ones(G.shape, bool)
    for ax in range(3):
        for sh in (0, 2):
            sl = [slice(1, -1)] * 3
            sl[ax] = slice(sh, sh + G.shape[ax])
            inside &= P[tuple(sl)]
    return (G > 0) & ~inside


def grid_mesh(name, V, labmats, trans=(), merge=True):
    """Only exposed faces: a face is drawn where the neighbour is empty or a different see-through label."""
    G = V.G
    keys = sorted(labmats)
    lut = np.zeros(int(G.max()) + 2, np.int32)
    for i, k in enumerate(keys):
        if k < len(lut):
            lut[k] = i
    tr = np.zeros(len(lut), bool)
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
        Vv = np.concatenate(verts) * V.step + V.lo
        me.from_pydata(Vv.tolist(), [], np.concatenate(faces).tolist())
        for k in keys:
            me.materials.append(labmats[k])
        me.polygons.foreach_set("material_index", np.concatenate(mids).astype(np.int32))
        me.update()
        if merge:   # weld and merge flat runs of faces: a 54 MB voxel .blend became 5.5 MB this way (spider lair)
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
            bmesh.ops.dissolve_limit(bm, angle_limit=0.01, verts=bm.verts, edges=bm.edges, delimit={"MATERIAL"})
            bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


# --------------------------------------------------------------- frames and small helpers
def nrm(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-9)


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def frame_fu(f, u):
    """Columns (side, f, u): f is the 'forward' axis of a part, u its 'up'."""
    f = nrm(f); u = np.asarray(u, float); u = nrm(u - f * (u @ f)); s = np.cross(f, u)
    return np.column_stack([s, f, u])


def frame_axis(z, ref=(0, -1, 0)):
    """Columns (x, y, z) with z along a limb and y toward `ref` (the limb's front)."""
    z = nrm(z); y = np.asarray(ref, float); y = y - z * (y @ z)
    if np.linalg.norm(y) < 1e-6:
        y = np.array([0, 0, 1.0]) - z * z[2]
    y = nrm(y); x = np.cross(y, z)
    return np.column_stack([x, y, z])


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    scene.collection.objects.link(e)
    return e


def spin(ob):
    """Turntable without keyframes: a simple driver on Z rotation, one turn per 120 frames."""
    d = ob.driver_add("rotation_euler", 2).driver
    d.type = "SCRIPTED"
    d.expression = "frame*0.05236"


def light(name, loc, color, energy, kind="POINT", size=None, rot=None, radius=0.2, cutoff=60.0, par=None):
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


def aim(ob, loc, look):
    d = np.asarray(look, float) - np.asarray(loc, float)
    ob.location = loc
    ob.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)


def camera(name, loc, look, lens=35.0):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.1; cd.clip_end = 400
    ob = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(ob)
    aim(ob, loc, look)
    return ob


def player(name, loc, rot_z=0.0, face=None):
    """A Minecraft-sized player (2 blocks to the top of the head) in a dark suit, the ring arm raised forward."""
    V = Vox((-0.6, -1.0, 0), (0.6, 0.6, 2.4), PX)
    I3 = np.eye(3)
    V.obox((-0.125, 0, 0.375), (0.124, 0.124, 0.374), I3, 1)
    V.obox((0.125, 0, 0.375), (0.124, 0.124, 0.374), I3, 1)
    V.obox((0, 0, 1.125), (0.249, 0.124, 0.374), I3, 1)
    V.obox((0, 0, 1.75), (0.249, 0.249, 0.249), I3, 2)
    V.obox((-0.375, 0, 1.125), (0.124, 0.124, 0.374), I3, 1)
    d = nrm((0, -0.8, 0.55)); sh = np.array([0.375, 0, 1.4])
    R = frame_axis(d, (0, 0, 1))
    V.obox(sh + d * 0.33, (0.124, 0.124, 0.37), R, 1)
    V.obox(sh + d * 0.62, (0.126, 0.126, 0.09), R, 2)
    V.obox(sh + d * 0.62, (0.15, 0.15, 0.03), R, 3, only_empty=True)
    ob = grid_mesh(name, V, {1: COMMON["suit"], 2: COMMON["skin"], 3: COMMON["ring"]})
    if face is not None:   # turn to look at a point (the model faces -y)
        rot_z = math.atan2(face[0] - loc[0], -(face[1] - loc[1]))
    ob.location = loc; ob.rotation_euler[2] = rot_z
    light(f"{name} ring light", tuple(sh + d * 0.75), (0.08, 1.0, 0.18), 60, radius=0.05, cutoff=10, par=ob)
    return ob


def ground_disc(name, radius, step=0.5, z_top=0.0, depth=2.0, seed=0, moss=True):
    """A flat round slab, top exactly at z_top (so planted feet really touch it), rough rim, a few mossy cells."""
    rng = np.random.default_rng(seed)
    V = Vox((-radius - 1, -radius - 1, z_top - depth), (radius + 1, radius + 1, z_top), step)
    x, y, z = V.axes()
    X, Y = np.meshgrid(x, y, indexing="ij")
    rr = np.hypot(X, Y) + rng.normal(0, 0.35, X.shape)
    col = rr <= radius
    zi = np.arange(V.shape[2])[None, None, :]
    dep = (rr[:, :, None] <= radius - (V.shape[2] - 1 - zi) * 0.5)
    V.G[col[:, :, None] & dep] = 1
    top = V.G[:, :, -1] > 0
    if moss:
        V.G[:, :, -1][top & (rng.random(top.shape) < 0.12)] = 2
    ob = grid_mesh(name, V, {1: COMMON["ground"], 2: COMMON["moss"]})
    return ob


# --------------------------------------------------------------- collision and contact checks
CHECKS = {}


def _seg_pts(a, b, n=24):
    t = np.linspace(0, 1, n)[:, None]
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def check(code, limbs, solids=(), floor=0.0, contacts=()):
    """limbs: {name: [(a, b, r), ...]}: no two limbs closer than their radii, nothing under the floor.
    solids: [(name, centre, r)] spheres limbs must clear. contacts: [(name, lowest z)] must sit on the floor."""
    worst, fails = 9.0, []
    names = list(limbs)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for (a, b, r) in limbs[names[i]]:
                for (c, d, s) in limbs[names[j]]:
                    A, B = _seg_pts(a, b), _seg_pts(c, d)
                    gap = np.min(np.linalg.norm(A[:, None] - B[None], axis=2)) - r - s
                    worst = min(worst, gap)
                    if gap < -0.05:
                        fails.append(f"{names[i]} x {names[j]} {gap:.2f}")
        for (a, b, r) in limbs[names[i]]:
            lowz = min(a[2], b[2]) - r
            if lowz < floor - 0.05:
                fails.append(f"{names[i]} under floor {lowz:.2f}")
            for (sn, sc_, sr) in solids:
                gap = np.min(np.linalg.norm(_seg_pts(a, b) - np.asarray(sc_, float), axis=1)) - r - sr
                if gap < -0.05:
                    fails.append(f"{names[i]} x {sn} {gap:.2f}")
    for nm, z in contacts:
        if abs(z - floor) > 0.3:
            fails.append(f"{nm} not touching ({z - floor:+.2f})")
    CHECKS[code] = {"min_gap": round(float(worst), 2), "fails": fails,
                    "contacts": [(nm, round(float(z - floor), 2)) for nm, z in contacts]}
    print(f"[{PASS}] check {code}: min limb gap {worst:.2f} blocks; {'OK' if not fails else 'FAIL ' + '; '.join(fails)}")


def lowest_z(V, lab_mask=None, region=None):
    G = V.G > 0 if lab_mask is None else lab_mask
    if region is not None:
        G = G & region
    idx = np.argwhere(G.any(axis=(0, 1)))
    return V.lo[2] + idx.min() * V.step if len(idx) else 99.0


TAKES = []


def add_take(code, name, cam, facts):
    TAKES.append((code, name, cam.name, "turntable", facts))


def stage(code, X, objs, look, dist, elev=0.32, side=0.62, lens=35.0, key=9000.0, size=None):
    """Parent the take to one spinning root at X, light it and aim its camera from the front-right (3/4 hero view)."""
    root = empty(f"{code} turn", tuple(X)); spin(root)
    for o in objs:
        o.parent = root
    s = size or dist * 0.5
    light(f"{code} key", tuple(X + np.array([dist * 0.45, -dist * 0.75, dist * 0.8])), (1.0, 0.95, 0.88), key * 1.8,
          kind="AREA", size=s, rot=(math.radians(42), 0, math.radians(30)), cutoff=dist * 4)
    light(f"{code} rim", tuple(X + np.array([-dist * 0.6, dist * 0.6, dist * 0.55])), (0.55, 0.7, 1.0), key * 0.55,
          kind="AREA", size=s, rot=(math.radians(-50), 0, math.radians(215)), cutoff=dist * 4)
    light(f"{code} fill", tuple(X + np.array([-dist * 0.8, -dist * 0.5, dist * 0.25])), (0.6, 0.62, 0.7), key * 0.35,
          kind="AREA", size=s, rot=(math.radians(70), 0, math.radians(-55)), cutoff=dist * 4)
    look = np.asarray(look, float)
    d = nrm((side, -1.0, 0))
    cam_at = X + look + np.array([d[0] * dist, d[1] * dist, dist * elev])
    return camera(f"Cam {code}", tuple(cam_at), tuple(X + look), lens)



# =============================================================== v2.0116: rigs, IK and clips
F0, F1 = FRAMES
TPS = 20.0                 # Minecraft ticks a second: every clip is timed in ticks
ALLF = range(F0, F1 + 1)


def add_hurt(m):
    """Minecraft's hurt flash: the object's "hurt" property (0-1) tints the colour red."""
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    bc = p.inputs["Base Color"]
    src = bc.links[0].from_socket if bc.is_linked else None
    at = N.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = "hurt"
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    a = [s for s in mix.inputs if s.name == "A" and s.type == "RGBA"][0]
    b = [s for s in mix.inputs if s.name == "B" and s.type == "RGBA"][0]
    if src is not None:
        L.new(src, a)
    else:
        a.default_value = tuple(bc.default_value)
    b.default_value = (0.85, 0.06, 0.04, 1)
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.6
    L.new(at.outputs["Fac"], mul.inputs[0]); L.new(mul.outputs[0], mix.inputs[0])
    L.new([o for o in mix.outputs if o.type == "RGBA"][0], bc)
    return m


for _k in ("suit", "skin"):
    add_hurt(COMMON[_k])


def T4(v):
    M = np.eye(4); M[:3, 3] = v
    return M


def R4(e):
    M = np.eye(4); M[:3, :3] = Rz(e[2]) @ Ry(e[1]) @ Rx(e[0])
    return M


def S4(s):
    s = np.broadcast_to(np.asarray(s, float), (3,))
    return np.diag([s[0], s[1], s[2], 1.0])


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ramp(f, a, b):
    """0 before frame a, 1 after frame b, smooth in between."""
    return ease((f - a) / max(b - a, 1e-6))


def lerp(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


class Rig:
    """Voxel parts on a joint hierarchy. Keys are stored per frame and baked once; FK in numpy mirrors Blender's
    parenting (parent world @ translate(location) @ rotate(XYZ euler) @ scale) so checks see exactly what renders."""

    def __init__(self, code, X):
        self.code, self.X = code, np.asarray(X, float)
        self.J, self.meshes, self.hurt, self._cache = {}, [], {}, {}
        self.add("root", None, (0, 0, 0))

    def add(self, name, parent, offset):
        e = empty(f"{self.code} {name}")
        if parent:
            e.parent = self.J[parent]["obj"]
            e.location = tuple(offset)
        else:
            e.location = tuple(self.X + np.asarray(offset, float))
        self.J[name] = dict(parent=parent, off=np.asarray(offset, float), obj=e, rot={}, loc={}, scl={})
        return e

    def part(self, joint, V, mats, trans=(), name=None):
        ob = grid_mesh(f"{self.code} {name or joint}", V, mats, trans)
        ob.parent = self.J[joint]["obj"]
        ob["hurt"] = 0.0
        self.meshes.append(ob)
        return ob

    def rot(self, f, j, e):
        self.J[j]["rot"][f] = np.asarray(e, float); self._cache.pop(f, None)

    def loc(self, f, j, v):
        self.J[j]["loc"][f] = np.asarray(v, float); self._cache.pop(f, None)

    def scl(self, f, j, s):
        self.J[j]["scl"][f] = np.broadcast_to(np.asarray(s, float), (3,)).copy(); self._cache.pop(f, None)

    def _get(self, d, f, default):
        return d[f] if f in d else default

    def M(self, f, j):
        c = self._cache.setdefault(f, {})
        if j in c:
            return c[j]
        jt = self.J[j]
        loc = self._get(jt["loc"], f, jt["off"])
        if jt["parent"]:
            P = self.M(f, jt["parent"])
        else:
            P = np.eye(4); loc = self.X + loc
        m = P @ T4(loc) @ R4(self._get(jt["rot"], f, np.zeros(3))) @ S4(self._get(jt["scl"], f, 1.0))
        c[j] = m
        return m

    def wp(self, f, j, p=(0, 0, 0)):
        return (self.M(f, j) @ np.array([*p, 1.0]))[:3]

    def pitch(self, f, j):
        m = self.M(f, j)
        return math.atan2(m[2, 1], m[1, 1])

    def ik(self, f, upper, lower, end, target, knee_fwd=True, flat=0.0, ay=0.0, az=0.0):
        """Two bones in the limb's own side plane: put joint `end` on world point `target`; the end part is turned so
        it lies flat (world pitch `flat`). Bones point down (-z) at rest; the body faces -y."""
        jp = self.J[upper]["parent"]
        Pi = np.linalg.inv(self.M(f, jp))
        tl = (Pi @ np.array([*target, 1.0]))[:3] - self.J[upper]["off"]
        if ay == 0.0:   # swing the limb out (about y) so its plane passes through the target
            rho = math.hypot(tl[0], tl[2])
            ay = math.atan2(-tl[0], -tl[2])
            tl = np.array([0.0, tl[1], -rho])
        a = np.linalg.norm(self.J[lower]["off"]); b = np.linalg.norm(self.J[end]["off"])
        D = min(max(math.hypot(tl[1], tl[2]), 1e-3), a + b - 1e-4)
        phi = math.atan2(tl[1], -tl[2])
        al = math.acos(min(max((a * a + D * D - b * b) / (2 * a * D), -1), 1))
        be = math.pi - math.acos(min(max((a * a + b * b - D * D) / (2 * a * b), -1), 1))
        t1, t2 = (phi - al, be) if knee_fwd else (phi + al, -be)
        self.rot(f, upper, (t1, ay, az)); self.rot(f, lower, (t2, 0, 0))
        self.rot(f, end, (flat - self.pitch(f, jp) - t1 - t2, 0, 0))

    def elbows_out(self, f, upper, end, side_sign, psi=1.0):
        """Roll the arm about the shoulder-to-hand line (the hand stays put) so the elbow points outward."""
        jp = self.J[upper]["parent"]
        Pi = np.linalg.inv(self.M(f, jp))
        s0 = self.J[upper]["off"]
        h = (Pi @ np.array([*self.wp(f, end), 1.0]))[:3]
        ax_ = nrm(h - s0)
        Ru = R4(self.J[upper]["rot"].get(f, np.zeros(3)))[:3, :3]
        lower = [j for j, v in self.J.items() if v["parent"] == upper][0]
        best = None
        for sg in (1, -1):
            a = sg * psi
            K = np.array([[0, -ax_[2], ax_[1]], [ax_[2], 0, -ax_[0]], [-ax_[1], ax_[0], 0]])
            Rr = np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K
            e = Matrix((Rr @ Ru).tolist()).to_euler("XYZ")
            self.rot(f, upper, (e.x, e.y, e.z))
            ex = self.wp(f, lower)[0] - self.X[0]
            if best is None or ex * side_sign > best[0]:
                best = (ex * side_sign, (e.x, e.y, e.z))
        self.rot(f, upper, best[1])
    def key_hurt(self, spans):
        """spans: [(first, last)] frames the red flash shows (Minecraft: 10 ticks)."""
        for ob in self.meshes:
            for f in ALLF:
                v = 1.0 if any(a <= f <= b for a, b in spans) else 0.0
                prev = 1.0 if any(a <= f - 1 <= b for a, b in spans) else 0.0
                if f == F0 or v != prev:
                    ob["hurt"] = v
                    ob.keyframe_insert('["hurt"]', frame=f)
                    if f > F0:
                        ob["hurt"] = prev
                        ob.keyframe_insert('["hurt"]', frame=f - 1)

    def bake(self):
        for name, jt in self.J.items():
            o = jt["obj"]
            for f, v in jt["rot"].items():
                o.rotation_euler = tuple(v); o.keyframe_insert("rotation_euler", frame=f)
            for f, v in jt["loc"].items():
                o.location = tuple(v + (self.X if not jt["parent"] else 0)); o.keyframe_insert("location", frame=f)
            for f, v in jt["scl"].items():
                o.scale = tuple(v); o.keyframe_insert("scale", frame=f)


def keyed_obj(ob, f, loc=None, rot=None, scale=None):
    if loc is not None:
        ob.location = tuple(loc); ob.keyframe_insert("location", frame=f)
    if rot is not None:
        ob.rotation_euler = tuple(rot); ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        ob.scale = tuple(np.broadcast_to(np.asarray(scale, float), (3,))); ob.keyframe_insert("scale", frame=f)


def rig_check(code, rig, segs, contacts=(), floor=0.0, frames=ALLF, tol=0.06):
    """segs: [(limb, joint, a, b, r)]: different limbs never closer than their radii, nothing under the floor.
    contacts: [(name, joint, point, frames)]: that point sits on the floor on those frames."""
    worst, fails, cmax = 9.0, {}, {}
    for f in frames:
        W = [(lm, rig.wp(f, j, a), rig.wp(f, j, b), r) for lm, j, a, b, r in segs]
        for i in range(len(W)):
            lm, A, B, r = W[i]
            low = min(A[2], B[2]) - r
            if low < floor - tol:
                fails.setdefault(f"{lm} under the floor", (f, low - floor))
            Pa = _seg_pts(A, B, 12)
            for k in range(i + 1, len(W)):
                lm2, C, D, s = W[k]
                if lm2 == lm or lm == "torso" or lm2 == "torso":
                    continue
                gap = np.min(np.linalg.norm(Pa[:, None] - _seg_pts(C, D, 12)[None], axis=2)) - r - s
                worst = min(worst, gap)
                if gap < -tol:
                    if gap < fails.get(f"{lm} x {lm2}", (0, 0))[1]:
                        fails[f"{lm} x {lm2}"] = (f, gap)
        for nm, j, p, fr, *dz in contacts:
            if f in fr:
                z = rig.wp(f, j, p)[2] + (dz[0] if dz else 0.0) - floor
                cmax[nm] = max(cmax.get(nm, 0.0), abs(z))
    for nm, z in cmax.items():
        if z > 0.08:
            fails.setdefault(f"{nm} not touching", (None, z))
    CHECKS[code] = {"min_gap": round(float(worst), 2),
                    "fails": [f"{k} (frame {v[0]}, {v[1]:+.2f})" for k, v in fails.items()],
                    "contacts": {k: round(float(v), 3) for k, v in cmax.items()}}
    print(f"[{PASS}] check {code}: min limb gap {worst:.2f}; contacts {CHECKS[code]['contacts']}; "
          f"{'OK' if not fails else 'FAIL ' + '; '.join(CHECKS[code]['fails'])}")


def add_take(code, name, cam, facts, kind="animation"):
    TAKES.append((code, name, cam.name, kind, facts))


def stage2(code, X, look, dist, elev=0.32, side=0.62, lens=35.0, key=900.0, spin_objs=()):
    """Light a take and aim its camera from the front-right 3/4 (no turning: the clip itself moves)."""
    X = np.asarray(X, float)
    s = dist * 0.5
    light(f"{code} key", tuple(X + np.array([dist * 0.45, -dist * 0.75, dist * 0.8])), (1.0, 0.95, 0.88), key * 1.8,
          kind="AREA", size=s, rot=(math.radians(42), 0, math.radians(30)), cutoff=dist * 4)
    light(f"{code} rim", tuple(X + np.array([-dist * 0.6, dist * 0.6, dist * 0.55])), (0.55, 0.7, 1.0), key * 0.55,
          kind="AREA", size=s, rot=(math.radians(-50), 0, math.radians(215)), cutoff=dist * 4)
    light(f"{code} fill", tuple(X + np.array([-dist * 0.8, -dist * 0.5, dist * 0.25])), (0.6, 0.62, 0.7), key * 0.35,
          kind="AREA", size=s, rot=(math.radians(70), 0, math.radians(-55)), cutoff=dist * 4)
    look = np.asarray(look, float)
    d = nrm((side, -1.0, 0))
    cam = camera(f"Cam {code}", tuple(X + look + np.array([d[0] * dist, d[1] * dist, dist * elev])), tuple(X + look), lens)
    cam.data.clip_end = dist * 2.5        # never see the neighbouring takes
    return cam


class Puffs:
    """Little cubes keyed over time: Minecraft death poofs, teleport static, splashes."""

    def __init__(self, name, n, size, mat, parent=None):
        V = Vox((-size / 2,) * 3, (size / 2,) * 3, size)
        V.G[:] = 1
        me_ob = grid_mesh(f"{name} cube", V, {1: mat}, merge=False)
        self.me = me_ob.data
        bpy.data.objects.remove(me_ob)
        self.obs = []
        for i in range(n):
            o = bpy.data.objects.new(f"{name} {i}", self.me)
            scene.collection.objects.link(o)
            if parent is not None:
                o.parent = parent
            o.scale = (0, 0, 0)
            self.obs.append(o)

    def key(self, i, f, loc, s):
        keyed_obj(self.obs[i], f, loc=loc, scale=s)


def player_rig(code, X, at, face):
    """The player model as a keyable object (a hit sends it flying back, Minecraft knockback)."""
    pl = player(f"{code} player", tuple(np.asarray(X, float) + np.asarray(at, float)), face=tuple(np.asarray(X, float)[:2] + np.asarray(face, float)[:2]))
    pl["hurt"] = 0.0
    return pl


def knockback(pl, X, at, f_hit, push, up=0.9):
    base = np.asarray(X, float) + np.asarray(at, float)
    push = np.asarray(push, float)
    for f in ALLF:
        t = (f - f_hit) / TPS
        if t < 0:
            p = base
        else:
            k = min(t / 0.45, 1.0)
            p = base + push * ease(k) + np.array([0, 0, up * 4 * k * (1 - k)])
        keyed_obj(pl, f, loc=p) if (f % 2 == 1 or abs(f - f_hit) < 3) else None
    for f, v in ((F0, 0.0), (f_hit - 1, 0.0), (f_hit, 1.0), (f_hit + 9, 1.0), (f_hit + 10, 0.0)):
        if F0 <= f <= F1:
            pl["hurt"] = v; pl.keyframe_insert('["hurt"]', frame=f)


# =============================================================== the polar bear (5 tall, skinny, sloth arms)
PS = 0.125   # bear voxels: 1/8 block
F1_, F2_, F3_, F4_, F5_, CLAWB, NOSEB, EYEB, MOUTHB, TOOTHB, TONGB = range(1, 12)
BEARM = {k: add_hurt(v) for k, v in {
    F1_: mat("polar ivory", (0.86, 0.84, 0.76), 0.95), F2_: mat("polar cream", (0.8, 0.75, 0.6), 0.95),
    F3_: mat("polar warm", (0.71, 0.65, 0.5), 0.95), F4_: mat("polar shadow", (0.5, 0.49, 0.46), 0.95),
    F5_: mat("polar bright", (0.95, 0.95, 0.91), 0.95), CLAWB: mat("sloth claws", (0.1, 0.085, 0.075), 0.35),
    NOSEB: mat("polar nose", (0.02, 0.02, 0.022), 0.3), EYEB: mat("polar eye", (0.01, 0.01, 0.012), 0.1),
    MOUTHB: mat("polar mouth", (0.22, 0.05, 0.07), 0.5), TOOTHB: mat("polar teeth", (0.93, 0.9, 0.8), 0.35),
    TONGB: mat("polar tongue", (0.5, 0.18, 0.22), 0.45)}.items()}


def fur_paint(V, rng, shag_down=0.0, shag_up=0.0):
    """Hand-picked polar colours: shadow underneath, cream and warm patches, bright and ivory sprinkled on top."""
    G = V.G
    fur = G == F1_
    x, y, z = V.axes()
    Z = np.broadcast_to(z[None, None, :], G.shape)
    zn = (Z - z.min()) / max(z.max() - z.min(), 1e-6)
    n = smooth3(G.shape, rng)
    lab = np.full(G.shape, F1_, np.int16)
    lab[n > 0.55] = F2_
    lab[n > 1.2] = F3_
    lab[(zn < 0.3) & (rng.random(G.shape) < 0.75)] = F4_
    lab[(zn > 0.55) & (rng.random(G.shape) < 0.22)] = F5_
    lab[(rng.random(G.shape) < 0.08)] = F2_
    G[fur] = lab[fur]
    furry = (G >= F1_) & (G <= F5_)
    surf = surface(G)
    if shag_down:
        dn = np.zeros(G.shape, bool); dn[:, :, 1:] = G[:, :, :-1] == 0
        hang = surf & furry & dn & (rng.random(G.shape) < shag_down)
        G[:, :, :-1][hang[:, :, 1:]] = F3_
        hang2 = np.zeros(G.shape, bool); hang2[:, :, 1:] = hang[:, :, 1:] & (rng.random(G.shape)[:, :, 1:] < 0.5)
        sub = G[:, :, :-2]
        m2 = hang2[:, :, 2:] & (sub == 0)
        sub[m2] = F4_
    if shag_up:
        up = np.zeros(G.shape, bool); up[:, :, :-1] = G[:, :, 1:] == 0
        tuft = surf & furry & up & (rng.random(G.shape) < shag_up)
        G[:, :, 1:][tuft[:, :, :-1]] = F5_


def smooth3(shape, rng, cell=4):
    cs = tuple(s // cell + 2 for s in shape)
    n = rng.normal(size=cs)
    for _ in range(2):
        n = (n + np.roll(n, 1, 0) + np.roll(n, -1, 0) + np.roll(n, 1, 1) + np.roll(n, -1, 1)
             + np.roll(n, 1, 2) + np.roll(n, -1, 2)) / 7
    n = np.repeat(np.repeat(np.repeat(n, cell, 0), cell, 1), cell, 2)[:shape[0], :shape[1], :shape[2]]
    return n / (n.std() + 1e-9)


BEAR = dict(body_z=3.05, sh=(0.62, -1.5, -0.2), hip=(0.58, 2.0, -0.55), ua=1.55, fa=1.45, th=1.3, sn=1.2,
            neck=(0, -2.45, 0.45), neck_len=(0, -1.05, 0.5), paw_h=0.24)


def bear_rig(code, X, seed):
    rng = np.random.default_rng(seed)
    B = BEAR
    R = Rig(code, X)
    R.add("body", "root", (0, 0, B["body_z"]))
    V = Vox((-1.2, -3.1, -1.4), (1.2, 3.4, 1.7), PS)
    for c, r in (((0, -1.3, 0.2), (0.95, 1.4, 1.05)), ((0, 0.4, -0.05), (0.82, 1.6, 0.88)), ((0, 1.9, -0.2), (0.85, 1.0, 0.88)),
                 ((0, -1.4, 0.8), (0.72, 1.0, 0.6)), ((0, -2.4, 0.45), (0.6, 0.62, 0.62)), ((0, 2.95, 0.05), (0.22, 0.25, 0.2))):
        V.ell(c, (r[0] * BV['girth'], r[1], r[2] * BV['girth']), F1_)
    for sx in (-1, 1):
        V.ell((sx * B["sh"][0], B["sh"][1], B["sh"][2]), (0.42, 0.45, 0.45), F1_)
        V.ell((sx * B["hip"][0], B["hip"][1], B["hip"][2]), (0.46, 0.5, 0.5), F1_)
    bear_extra_body(V)
    fur_paint(V, rng, shag_down=0.35 * BV['shag'], shag_up=0.06 * BV['shag'])
    bear_scars(V)
    R.part("body", V, BEARM)
    R.add("neck", "body", B["neck"])
    V = Vox((-0.8, -1.6, -0.7), (0.8, 0.5, 1.2), PS)
    V.cap((0, 0, 0), B["neck_len"], 0.56, F1_, 0.48)
    V.ell((0, -0.45, -0.25), (0.5, 0.55, 0.45), F1_)       # throat ruff
    if BV['mane']:
        V.ell((0, -0.25, 0.1), (0.74 * BV['mane'], 0.75, 0.62 * BV['mane']), F1_)
    fur_paint(V, rng, shag_down=0.4 * BV['shag'])
    R.part("neck", V, BEARM)
    R.add("head", "neck", B["neck_len"])
    V = Vox((-0.8, -1.8, -0.6), (0.8, 0.6, 0.9), PS)
    fw = BV['face']
    V.ell((0, -0.3, 0.15), (0.5 * fw, 0.62, 0.48 * (0.5 + 0.5 * fw)), F1_)
    V.ell((0, -0.95, -0.05), (0.32 * fw, 0.55, 0.28 * (0.6 + 0.4 * fw)), F1_)
    for sx in (-1, 1):
        V.ell((sx * 0.34 * fw, 0.0, 0.55), (0.15, 0.1, 0.15), F1_)
        V.ell((sx * 0.29 * fw, -0.6, 0.3), (0.08, 0.07, 0.08), EYEB)
    fur_paint(V, rng)
    V.ell((0, -1.47, 0.04), (0.17, 0.1, 0.13), NOSEB)
    V.ell((0, -0.95, -0.3), (0.26 * BV['face'], 0.48, 0.1), MOUTHB)
    for sx in (-1, 1):
        V.cap((sx * 0.18, -1.22, -0.25), (sx * 0.18, -1.24, -0.42), 0.06, TOOTHB)
    R.part("head", V, BEARM)
    R.add("jaw", "head", (0, -0.45, -0.18))
    V = Vox((-0.5, -1.2, -0.45), (0.5, 0.3, 0.2), PS)
    V.ell((0, -0.5, -0.1), (0.27 * BV['face'], 0.52, 0.14), F1_)
    fur_paint(V, rng)
    V.ell((0, -0.45, 0.02), (0.18, 0.4, 0.06), TONGB)
    for sx in (-1, 1):
        V.cap((sx * 0.17, -0.85, -0.02), (sx * 0.17, -0.87, 0.15), 0.06, TOOTHB)
    R.part("jaw", V, BEARM)
    segs = [("torso", "body", (0, -2.2, 0.2), (0, 2.6, -0.1), 0.85), ("head", "head", (0, -0.2, 0.15), (0, -1.3, 0.0), 0.45)]
    for side, sx in (("R", 1), ("L", -1)):
        # front: long sloth arm, elbow pointing back
        R.add(f"sh{side}", "body", (sx * B["sh"][0], B["sh"][1], B["sh"][2]))
        V = Vox((-0.6, -0.6, -B['ua'] - 0.45), (0.6, 0.6, 0.5), PS)
        V.cap((0, 0, 0), (0, 0, -B["ua"]), 0.38, F1_, 0.3)
        fur_paint(V, rng, shag_down=0.25)
        R.part(f"sh{side}", V, BEARM, name=f"upper arm {side}")
        R.add(f"el{side}", f"sh{side}", (0, 0, -B["ua"]))
        V = Vox((-0.5, -0.5, -B['fa'] - 0.35), (0.5, 0.6, 0.4), PS)
        V.cap((0, 0, 0.05), (0, 0, -B["fa"]), 0.31, F1_, 0.22)
        fur_paint(V, rng, shag_down=0.2 * BV['shag'])
        for k in range(10):     # long shaggy guard hair down the back of the forearm (sloth)
            zz = -0.1 - k * 0.13
            V.cap((0, 0.2, zz), (0, 0.42, zz - 0.18), 0.07, F3_ if k % 3 else F2_)
        R.part(f"el{side}", V, BEARM, name=f"forearm {side}")
        R.add(f"wr{side}", f"el{side}", (0, 0, -B["fa"]))
        V = Vox((-0.55 - 0.95 * BV['claw'] * math.sin(BV['claw_in']), -0.7 - 0.9 * BV['claw'], -0.45), (0.55 + 0.95 * BV['claw'] * math.sin(BV['claw_in']), 0.5, 0.35), PS)
        V.ell((0, -0.15, -0.08), (0.3, 0.42, 0.16), F1_)
        fur_paint(V, rng)
        for xi in (-0.15, 0.0, 0.15):   # three long hooked sloth claws
            bear_claw(V, xi, sx)
        R.part(f"wr{side}", V, BEARM, name=f"front paw {side}")
        segs += [(f"front {side}", f"sh{side}", (0, 0, 0), (0, 0, -B["ua"]), 0.36),
                 (f"front {side}", f"el{side}", (0, 0, 0), (0, 0, -B["fa"] / 2), 0.3),
                 (f"front {side}", f"el{side}", (0, 0, -B["fa"] / 2), (0, 0, -B["fa"]), 0.22),
                 (f"front {side}", f"wr{side}", (0, 0.15, -0.08), (0, -1.15, -0.12), 0.12)]
        # hind
        R.add(f"hp{side}", "body", (sx * B["hip"][0], B["hip"][1], B["hip"][2]))
        V = Vox((-0.7, -0.7, -1.7), (0.7, 0.7, 0.5), PS)
        V.cap((0, 0, 0), (0, 0, -B["th"]), 0.48, F1_, 0.32)
        fur_paint(V, rng, shag_down=0.2)
        R.part(f"hp{side}", V, BEARM, name=f"thigh {side}")
        R.add(f"kn{side}", f"hp{side}", (0, 0, -B["th"]))
        V = Vox((-0.5, -0.5, -1.5), (0.5, 0.5, 0.4), PS)
        V.cap((0, 0, 0.05), (0, 0, -B["sn"]), 0.31, F1_, 0.22)
        fur_paint(V, rng, shag_down=0.15)
        R.part(f"kn{side}", V, BEARM, name=f"shin {side}")
        R.add(f"an{side}", f"kn{side}", (0, 0, -B["sn"]))
        V = Vox((-0.5, -1.1, -0.35), (0.5, 0.5, 0.35), PS)
        V.ell((0, -0.2, -0.08), (0.28, 0.45, 0.16), F1_)
        fur_paint(V, rng)
        for xi in (-0.16, -0.05, 0.05, 0.16):
            V.cap((xi, -0.6, -0.12), (xi, -0.85, -0.18), 0.055, CLAWB, 0.045)
        R.part(f"an{side}", V, BEARM, name=f"hind paw {side}")
        segs += [(f"hind {side}", f"hp{side}", (0, 0, 0), (0, 0, -B["th"]), 0.44),
                 (f"hind {side}", f"kn{side}", (0, 0, 0), (0, 0, -B["sn"] / 2), 0.3),
                 (f"hind {side}", f"kn{side}", (0, 0, -B["sn"] / 2), (0, 0, -B["sn"]), 0.22),
                 (f"hind {side}", f"an{side}", (0, 0.2, -0.08), (0, -0.85, -0.12), 0.12)]
    return R, segs


def bear_rest_targets(R, f, by=0.0):
    """Where the paws stand at rest (world), body at y=by."""
    B = BEAR
    out = {}
    for side, sx in (("R", 1), ("L", -1)):
        out[f"wr{side}"] = R.X + np.array([sx * B["sh"][0], by + B["sh"][1] - 0.05, B["paw_h"]])
        out[f"an{side}"] = R.X + np.array([sx * B["hip"][0], by + B["hip"][1] + 0.1, B["paw_h"]])
    return out


def bear_leg(R, f, foot, target):
    side = foot[-1]
    if foot.startswith("wr"):
        R.ik(f, f"sh{side}", f"el{side}", foot, target, knee_fwd=False)
    else:
        R.ik(f, f"hp{side}", f"kn{side}", foot, target, knee_fwd=True)


def bear_take(code, name, X, clip, facts, seed):
    R, segs = bear_rig(code, X, seed)
    B = BEAR
    pl = None
    contacts = []
    hurt = []
    puff = None
    feet = ("wrR", "wrL", "anR", "anL")
    paw_pt = (0, 0, -B["paw_h"])
    if clip in ("idle", "hurt", "death", "swipe", "rear"):
        rest = bear_rest_targets(R, F0)
    if clip == "walk":
        T, S, duty = 30.0, 1.3, 0.65
        v = S / (duty * T / TPS)
        ph = {"anL": 0.0, "wrL": 0.25, "anR": 0.5, "wrR": 0.75}
        y0 = 2.0
        for f in ALLF:
            t = (f - F0) / TPS
            by = y0 - v * t
            R.loc(f, "root", (0, by, 0))
            cyc = (f - F0) / T
            R.loc(f, "body", (0, 0, B["body_z"] + 0.05 * math.sin(4 * math.pi * cyc)))
            R.rot(f, "body", (0.02 * math.sin(4 * math.pi * cyc), 0, 0.03 * math.sin(2 * math.pi * cyc)))
            R.rot(f, "neck", (-0.1 + 0.06 * math.sin(4 * math.pi * cyc + 1), 0, -0.04 * math.sin(2 * math.pi * cyc)))
            R.rot(f, "head", (0.15, 0, 0))
            for foot, p0 in ph.items():
                p = (cyc + p0) % 1.0
                base = bear_rest_targets(R, f, by)[foot]
                if p < duty:
                    yr = -S / 2 + S * p / duty; lift = 0.0
                else:
                    q = (p - duty) / (1 - duty)
                    yr = S / 2 - S * ease(q); lift = 0.35 * math.sin(math.pi * q)
                tgt = base + np.array([0, yr, lift])
                bear_leg(R, f, foot, tgt)
                if p < duty - 0.02:
                    contacts.append((f"{foot} paw", foot, paw_pt, {f}))
        look, dist = (0, 0, 2.3), 14
    else:
        for f in ALLF:
            t = (f - F0) / TPS
            br = 0.03 * math.sin(2 * math.pi * t / 2.2)
            R.loc(f, "body", (0, 0, B["body_z"] + br))
            R.rot(f, "neck", (-0.08 + 0.05 * math.sin(2 * math.pi * t / 3.0), 0, 0.18 * math.sin(2 * math.pi * t / 3.0)))
            R.rot(f, "head", (0.12, 0, 0))
        look, dist = (0, -0.6, 2.3), 13
        if clip == "idle":
            for f in ALLF:
                t = (f - F0) / TPS
                sniff = max(0.0, math.sin(2 * math.pi * (t - 1.4) / 0.8)) if 1.4 < t < 2.2 else 0.0
                R.rot(f, "head", (0.12 - 0.25 * sniff, 0, 0))
                R.rot(f, "jaw", (0.08 * sniff, 0, 0))
                for foot in feet:
                    bear_leg(R, f, foot, rest[foot])
                    contacts.append((f"{foot} paw", foot, paw_pt, {f}))
        elif clip == "swipe":
            pl = player_rig(code, X, (0.9, -4.6, 0), (0, 0))
            f_hit = 27
            for f in ALLF:
                a = ramp(f, 6, 20) * (1 - ramp(f, 22, 30))        # raise
                s = ramp(f, 21, 28)                                 # strike
                back = ramp(f, 34, 52)                              # return
                R.rot(f, "body", (0.06 * a - 0.08 * s * (1 - back), 0, -0.12 * a + 0.1 * s * (1 - back)))
                R.rot(f, "neck", (-0.08, 0, -0.35 * (a + s) * (1 - back)))
                R.rot(f, "jaw", (0.5 * ramp(f, 14, 20) * (1 - back), 0, 0))
                for foot in ("wrL", "anR", "anL"):
                    bear_leg(R, f, foot, rest[foot])
                    contacts.append((f"{foot} paw", foot, paw_pt, {f}))
                # the swiping right arm: raised out to the side of the head, then down across the player, then back
                bear_leg(R, f, "wrR", rest["wrR"])
                ik = [R.J[j]["rot"][f].copy() for j in ("shR", "elR", "wrR")]
                raised = [np.array([-2.5, 0.45, 0.0]), np.array([-0.6, 0, 0]), np.array([0.9, 0, 0])]
                struck = [np.array([-0.25, 0.3, 0.15]), np.array([-0.4, 0, 0]), np.array([0.5, 0, 0])]
                for jn, i_, r_, s_ in zip(("shR", "elR", "wrR"), ik, raised, struck):
                    pose = lerp(i_, r_, ramp(f, 6, 20))
                    pose = lerp(pose, s_, s)
                    R.rot(f, jn, lerp(pose, i_, back))
                if f <= 6 or back >= 1:
                    contacts.append(("wrR paw", "wrR", paw_pt, {f}))
            knockback(pl, X, (0.9, -4.6, 0), f_hit, (0.6, -2.6, 0))
            look, dist = (0, -1.8, 2.3), 14
        elif clip == "rear":
            hipw = {s_: R.wp(F0, "body", (sx * B["hip"][0], B["hip"][1], B["hip"][2])) for s_, sx in (("R", 1), ("L", -1))}
            pivot = R.X + np.array([0, B["hip"][1], B["body_z"] + B["hip"][2]])
            for f in ALLF:
                up = ramp(f, BV['rear'][0], BV['rear'][1]) * (1 - ramp(f, BV['rear'][2], BV['rear'][3]))
                pitch = -0.95 * up
                Rb = Rx(pitch)
                body_c = pivot - Rb @ np.array([0, B["hip"][1], B["hip"][2]])
                R.loc(f, "body", body_c - R.X - np.array([0, 0, bear_heavy(f)]))
                R.rot(f, "body", (pitch, bear_rear_roll(f, up), 0))
                roar = ramp(f, 18, 24) * (1 - ramp(f, 38, 44))
                R.rot(f, "neck", (0.5 * up, 0, 0))
                R.rot(f, "head", (0.12 - 0.35 * roar + 0.4 * up, 0, 0))
                R.rot(f, "jaw", (0.75 * roar, 0, 0))
                for foot in ("anR", "anL"):
                    bear_leg(R, f, foot, rest[foot])
                    contacts.append((f"{foot} paw", foot, paw_pt, {f}))
                for side, sx in (("R", 1), ("L", -1)):
                    foot = f"wr{side}"
                    bear_leg(R, f, foot, rest[foot])
                    ik = [R.J[j]["rot"][f].copy() for j in (f"sh{side}", f"el{side}", foot)]
                    sway = 0.15 * math.sin((f - 20) * 0.35) * roar
                    # the upper arm swings along the shortest way between its standing direction and up-and-out
                    w = min(up * 1.6, 1.0)
                    d_ik = limb_dir(*R.J[f"sh{side}"]["rot"][f][:2])
                    d_up = Rx(pitch).T @ nrm(bear_rear_dir(f, sx, sway))
                    ax, ay_ = aim_limb(nrm(lerp(d_ik, d_up, w)))
                    R.rot(f, f"sh{side}", (ax, ay_, 0))
                    R.rot(f, f"el{side}", lerp(ik[1], (BV["rear_elbow"], 0, 0), w))
                    R.rot(f, foot, lerp(ik[2], (BV['wrist'], 0, 0), w))
                    if w <= 0:
                        contacts.append((f"{foot} paw", foot, paw_pt, {f}))
            look, dist = (0, -0.5, 3.4), 16
        elif clip == "hurt":
            pl = player_rig(code, X, (2.8, -4.5, 0), (0, 0))
            hits = (14, 38)
            hurt = [(h, h + 9) for h in hits]
            for f in ALLF:
                k = sum(math.exp(-((f - h) / 4.0) ** 2) * (1 if f >= h else 0.3) for h in hits)
                R.loc(f, "body", (0.25 * k, 0.15 * k, B["body_z"] - 0.12 * k))
                R.rot(f, "body", (0.05 * k, -0.15 * k, -0.1 * k))
                R.rot(f, "neck", (0.2 * k - 0.08, 0, 0.35 * k))
                R.rot(f, "jaw", (0.45 * k, 0, 0))
                for foot in feet:
                    bear_leg(R, f, foot, rest[foot])
                    contacts.append((f"{foot} paw", foot, paw_pt, {f}))
        elif clip == "death":
            hurt = [(10, F1)]
            puff = Puffs(f"{code} poof", 24, 0.22, mat("death poof", (0.85, 0.85, 0.85), 0.8))
            for f in ALLF:
                fall = ramp(f, 12, 30)
                stiff = ramp(f, 10, 22)
                for foot in feet:
                    bear_leg(R, f, foot, rest[foot])
                    side = foot[-1]
                    for j in ((f"sh{side}", f"el{side}", foot) if foot.startswith("wr") else (f"hp{side}", f"kn{side}", foot)):
                        R.rot(f, j, lerp(R.J[j]["rot"][f], (0, 0, 0), stiff))
                    if stiff <= 0:
                        contacts.append((f"{foot} paw", foot, paw_pt, {f}))
                R.rot(f, "root", (0, 1.5708 * fall, 0))     # Minecraft death: tips onto its side
                R.loc(f, "root", (0, 0, 0))
                R.rot(f, "jaw", (0.4 * stiff, 0, 0))
                # keep everything above the ground and, once over, lying on it
                low = min(min(R.wp(f, j, a)[2], R.wp(f, j, b)[2]) - r for _, j, a, b, r in segs)
                lift = -low if (low < 0 or fall >= 1) else 0.0
                R.loc(f, "root", (0, 0, lift))
                if fall >= 1:
                    contacts.append(("lying on its side", "body", (0, 0, 0), set()))
            ctr = R.wp(F1, "body")
            for i in range(24):
                d = rng_dir(i)
                for f in range(42, F1 + 1, 2):
                    k = (f - 42) / 18
                    R_ = 0.22 * (1 - k) + 0.02
                    puff.key(i, f, ctr + d * (0.6 + 1.6 * k) + np.array([0, 0, 0.8 * k]), R_ / 0.22)
                puff.key(i, 41, ctr, 0.0)
            for f in ALLF:
                R.scl(f, "root", 1.0 if f < 46 else max(0.001, 1 - (f - 46) / 4))
    if clip == "death":
        rig_check(code, R, segs, contacts=[c for c in contacts if c[3]], frames=range(F0, 45))
    else:
        rig_check(code, R, segs, contacts=contacts)
    R.bake()
    if hurt:
        R.key_hurt(hurt)
    gd = ground_disc(f"{code} ground", 9, seed=seed)
    gd.location = tuple(R.X)
    if pl is None:
        player(f"{code} player", tuple(R.X + np.array([-3.4, -3.2, 0])), face=tuple(R.X[:2]))
    cam = stage2(code, R.X, np.asarray(look, float) + np.array([0, 0, BV['cam_up']]), dist * BV['cam_d'], elev=0.28, key=700)
    add_take(code, name, cam, facts)


def limb_dir(ax, ay):
    """Direction of a limb (rest: straight down) after Blender XYZ euler (ax, ay, 0)."""
    return np.array([-math.sin(ay) * math.cos(ax), math.sin(ax), -math.cos(ay) * math.cos(ax)])


def aim_limb(d):
    return math.asin(min(max(d[1], -1.0), 1.0)), math.atan2(-d[0], -d[2])


def rng_dir(i):
    r = np.random.default_rng(1000 + i)
    v = r.normal(size=3); v[2] = abs(v[2]) * 0.6
    return nrm(v)


# =============================================================== the Lantern endermen (7 tall, Minecraft proportions)
P = 7.0 / 50.0     # one enderman pixel: the vanilla model is 50 px tall
EB1, EB2, EB3, EEYE, LGOLD, LGLASS, LCORE, LAVA, WATER, ELIT = range(1, 11)


def ender_mats(corps):
    eye = (1.0, 0.72, 0.08) if corps == "yellow" else (1.0, 0.42, 0.04)
    eye = EV.get("eye") or eye
    return {EB1: add_hurt(mat("ender black", EV["skin"][0], 0.6)), EB2: add_hurt(mat("ender grey", EV["skin"][1], 0.6)),
            EB3: add_hurt(mat("ender dark violet", EV["skin"][2], 0.6)),
            EEYE: mat(f"{corps} ender eyes", eye, 0.2, emit=eye, es=1.5),
            LGOLD: pmat(f"{corps} lantern gold", (0.5, 0.33, 0.06), (0.95, 0.7, 0.25), 0.28, metal=1.0, cell=P / 2),
            LGLASS: mat(f"{corps} lantern glass", tuple(c * 0.55 for c in eye), 0.1, emit=eye, es=0.35, alpha=0.5),
            LCORE: mat(f"{corps} lantern heart", eye, 0.2, emit=eye, es=1.4),
            LAVA: pmat("lava block", (0.75, 0.18, 0.02), (1.0, 0.55, 0.06), 0.5, cell=0.0625, emit=(1.0, 0.32, 0.02), es=1.2),
            WATER: mat("water construct", (0.1, 0.35, 0.85), 0.05, emit=(0.1, 0.4, 1.0), es=0.25, alpha=0.6),
            ELIT: mat(f"{corps} construct glow", eye, 0.3, emit=eye, es=1.2)}


def ebox(V, lo, hi, rng):
    """A box in enderman pixels, speckled black / grey / violet like the vanilla skin."""
    def fn(Pt):
        return ((Pt[0] >= lo[0] * P) & (Pt[0] <= hi[0] * P) & (Pt[1] >= lo[1] * P) & (Pt[1] <= hi[1] * P)
                & (Pt[2] >= lo[2] * P) & (Pt[2] <= hi[2] * P))
    V.region(((np.array(lo) + hi) / 2) * P, ((np.array(hi) - lo) / 2) * P + P, fn, EB1)
    m = V.G == EB1
    r = rng.random(V.G.shape)
    V.G[m & (r < 0.22)] = EB2
    V.G[m & (r > 0.86)] = EB3
    ender_cracks(V, m, r)


def lantern_vox(origin_top=True):
    """The Lantern in enderman pixels: bail, cap, glass round a heart, corner posts, base (9.5 px tall)."""
    V = Vox((-3.6 * P, -3.6 * P, -10 * P), (3.6 * P, 3.6 * P, 0.6 * P), P / 2)
    I3 = np.eye(3)
    V.cap((-1.5 * P, 0, -1.6 * P), (0, 0, 0), P * 0.35, LGOLD); V.cap((0, 0, 0), (1.5 * P, 0, -1.6 * P), P * 0.35, LGOLD)
    V.obox((0, 0, -2.0 * P), (3 * P, 3 * P, 0.5 * P), I3, LGOLD)
    V.obox((0, 0, -5.5 * P), (2.2 * P, 2.2 * P, 3 * P), I3, LGLASS)
    V.obox((0, 0, -5.5 * P), (1.0 * P, 1.0 * P, 1.5 * P), I3, LCORE)
    for sx in (-1, 1):
        for sy in (-1, 1):
            V.obox((sx * 2.5 * P, sy * 2.5 * P, -5.5 * P), (0.5 * P, 0.5 * P, 3 * P), I3, LGOLD)
    V.obox((0, 0, -9.0 * P), (3 * P, 3 * P, 0.5 * P), I3, LGOLD)
    return V


LANT_H = 9.5 * P          # lantern height below its bail top
LANT_HALF = 3.0 * P


def cube_vox(lab, size=0.45, step=0.0625):
    V = Vox((-size / 2,) * 3, (size / 2,) * 3, step)
    V.G[:] = lab
    return V


def torus_vox(lab, r=1.0, t=0.12, step=0.0625):
    V = Vox((-r - t, -r - t, -t), (r + t, r + t, t), step)
    x, y, z = V.axes()
    X_, Y_, Z_ = np.meshgrid(x, y, z, indexing="ij")
    V.G[(np.abs(np.hypot(X_, Y_) - r) < t) & (np.abs(Z_) < t)] = lab
    return V


def ender_rig(code, X, corps, seed, lantern_on="haR"):
    rng = np.random.default_rng(seed)
    EM2 = ender_mats(corps)
    R = Rig(code, X)
    R.add("pelvis", "root", (0, 0, 30 * P))
    R.add("spine", "pelvis", (0, 0, 0))
    V = Vox((-4.5 * P, -2.5 * P, -0.5 * P), (4.5 * P, 2.5 * P, 12.5 * P), P); ebox(V, (-4, -2, 0), (4, 2, 12), rng)
    R.part("spine", V, EM2, name="body")
    R.add("neck", "spine", (0, 0, 12 * P))
    V = Vox((-4.5 * P, -4.5 * P, -0.5 * P), (4.5 * P, 4.5 * P, 8.5 * P), P); ebox(V, (-4, -4, 0), (4, 4, 8), rng)
    R.part("neck", V, EM2, name="head")
    R.add("eyes", "neck", (0, -4 * P, 3.5 * P))
    V = Vox((-4 * P, -0.6 * P, -0.6 * P), (4 * P, 0.1 * P, 0.6 * P), P / 2)
    for sx in (-1, 1):
        V.obox((sx * 2.0 * P, -0.25 * P, 0), (1.5 * P, 0.3 * P, 0.5 * P), np.eye(3), EEYE)
    R.part("eyes", V, EM2)
    segs = [("torso", "spine", (0, 0, 1 * P), (0, 0, 11 * P), 4 * P), ("head", "neck", (0, 0, 2.5 * P), (0, 0, 5.5 * P), 3.9 * P)]
    for side, sx in (("R", 1), ("L", -1)):
        R.add(f"hp{side}", "pelvis", (sx * 2 * P, 0, 0))
        V = Vox((-1.5 * P, -1.5 * P, -15.5 * P), (1.5 * P, 1.5 * P, 1.5 * P), P); ebox(V, (-1, -1, -15), (1, 1, 1), rng)
        R.part(f"hp{side}", V, EM2, name=f"thigh {side}")
        R.add(f"kn{side}", f"hp{side}", (0, 0, -15 * P))
        V = Vox((-1.5 * P, -1.5 * P, -15.5 * P), (1.5 * P, 1.5 * P, 1 * P), P); ebox(V, (-1, -1, -15), (1, 1, 0.5), rng)
        R.part(f"kn{side}", V, EM2, name=f"shin {side}")
        R.add(f"ft{side}", f"kn{side}", (0, 0, -15 * P))
        R.add(f"sh{side}", "spine", (sx * 5 * P, 0, 11 * P))
        V = Vox((-1.5 * P, -1.5 * P, -15.5 * P), (1.5 * P, 1.5 * P, 1.5 * P), P); ebox(V, (-1, -1, -15), (1, 1, 1), rng)
        R.part(f"sh{side}", V, EM2, name=f"upper arm {side}")
        R.add(f"el{side}", f"sh{side}", (0, 0, -15 * P))
        V = Vox((-1.5 * P, -1.5 * P, -15.5 * P), (1.5 * P, 1.5 * P, 1 * P), P); ebox(V, (-1, -1, -15), (1, 1, 0.5), rng)
        R.part(f"el{side}", V, EM2, name=f"forearm {side}")
        R.add(f"ha{side}", f"el{side}", (0, 0, -15 * P))
        segs += [(f"leg {side}", f"hp{side}", (0, 0, 0), (0, 0, -15 * P), 1.15 * P),
                 (f"leg {side}", f"kn{side}", (0, 0, 0), (0, 0, -14 * P), 1.15 * P),
                 (f"arm {side}", f"sh{side}", (0, 0, 0), (0, 0, -15 * P), 1.15 * P),
                 (f"arm {side}", f"el{side}", (0, 0, 0), (0, 0, -14 * P), 1.15 * P)]
    if lantern_on == "haR":
        R.add("lan", "haR", (0, 0, -0.5 * P))
        R.part("lan", lantern_vox(), EM2, trans=(LGLASS,), name="lantern")
        segs.append(("arm R", "lan", (0, 0, -4.5 * P), (0, 0, -6.5 * P), 3.0 * P))    # held: part of the arm
    else:
        R.add("lan", lantern_on, (0, 0, 0))
        R.part("lan", lantern_vox(), EM2, trans=(LGLASS,), name="lantern")
        segs.append(("lantern", "lan", (0, 0, -4.5 * P), (0, 0, -6.5 * P), 3.0 * P))
    R.add("core", "lan", (0, 0, -5.5 * P))
    for ob in R.meshes:     # gaunt versions: thinner limbs (the joints, so the checks, are unchanged)
        if any(k in ob.name for k in ("thigh", "shin", "arm")):
            ob.scale = (EV["limb"], EV["limb"], 1.0)
    return R, segs, EM2, rng


def settle(R, f, pts):
    """Move the whole rig up or down so the lowest of these points sits exactly on the ground."""
    zs = [R.wp(f, j, p)[2] + (q[0] if q else 0.0) for j, p, *q in pts]
    cur = R._get(R.J["root"]["loc"], f, np.zeros(3))
    R.loc(f, "root", cur - np.array([0, 0, min(zs)]))


def hang_lantern(R, f, swing=0.0):
    R.rot(f, "lan", (-R.pitch(f, "haR") + swing, 0, 0))


def ender_stand(R, f, t, crouch=0.0, ftgt=None):
    """Both feet planted (IK), pelvis lowered by `crouch` blocks."""
    R.loc(f, "pelvis", (0, 0, 30 * P - crouch))
    for side, sx in (("R", 1), ("L", -1)):
        tgt = R.X + R._get(R.J["root"]["loc"], f, np.zeros(3)) + np.array([sx * 2 * P, 0.0, 0.0]) if ftgt is None else ftgt[side]
        R.ik(f, f"hp{side}", f"kn{side}", f"ft{side}", tgt, knee_fwd=True)


def ender_carry_arms(R, f, t, sway=0.0):
    R.rot(f, "shR", (-0.12 + sway * 0.3, -0.3, 0)); R.rot(f, "elR", (-1.35, 0, 0))
    R.rot(f, "shL", (0.05 - sway * 0.3, 0.1, 0)); R.rot(f, "elL", (-0.15, 0, 0))


class Orbit:
    """Constructs the enderman has taken: lava and water blocks circling it at chest height."""

    def __init__(self, code, R, EM2, kinds=("lava", "water", "lava", "water")):
        self.obs = []
        for i, k in enumerate(kinds):
            lab = LAVA if k == "lava" else WATER
            o = grid_mesh(f"{code} {k} block {i}", cube_vox(lab), {lab: EM2[lab]}, trans=(WATER,))
            o.parent = R.J["root"]["obj"]
            self.obs.append((k, o))
        self.R = R

    def pos(self, i, f):
        t = (f - F0) / TPS
        a = t * 0.9 + i / len(self.obs) * math.tau
        return np.array([math.cos(a) * 1.7, math.sin(a) * 1.7, 4.6 + 0.35 * math.sin(t * 1.7 + i)])

    def key_all(self, skip=(), until=None):
        for i, (k, o) in enumerate(self.obs):
            if i in skip:
                continue
            for f in ALLF:
                keyed_obj(o, f, loc=self.pos(i, f), rot=(f * 0.05 + i, f * 0.03, 0))


def ender_take(code, name, X, corps, clip, facts, seed):
    lantern_on = "spine" if clip.startswith("pray") else "haR"
    R, segs, EM2, rng = ender_rig(code, X, corps, seed, lantern_on)
    hurt, contacts = [], []
    feet = [("ftR", (0, 0, 0)), ("ftL", (0, 0, 0))]
    orbit = Orbit(code, R, EM2) if corps == "yellow" else None
    look, dist = (0, -0.5, 3.6), 13.5
    extra = []

    def idle_body(f, t):
        R.rot(f, "spine", (0.03 * math.sin(t * 2.1), 0, 0.02 * math.sin(t * 1.3)))
        R.rot(f, "neck", (0.05 * math.sin(t * 1.1), 0, 0.12 * math.sin(t * 0.7)))

    if clip in ("idle", "hurt", "death"):
        for f in ALLF:
            t = (f - F0) / TPS
            idle_body(f, t)
            ender_carry_arms(R, f, t, 0.05 * math.sin(t * 2))
            k = 0.0
            if clip == "hurt":
                k = sum(math.exp(-((f - h) / 3.5) ** 2) * (1 if f >= h else 0.3) for h in (14, 38))
                R.rot(f, "spine", (-0.2 * k, 0, 0.12 * k)); R.rot(f, "neck", (-0.3 * k, 0, -0.3 * k))
            ender_stand(R, f, t, crouch=0.25 * k)
            hang_lantern(R, f, 0.15 * math.sin(t * 2.4) + 0.4 * k)
            settle(R, f, feet)
            if clip == "death":
                fall = ramp(f, 12, 30)
                R.rot(f, "root", (0, -1.5708 * fall, 0))
                low = min(min(R.wp(f, j, a)[2], R.wp(f, j, b)[2]) - r for _, j, a, b, r in segs)
                cur = R._get(R.J["root"]["loc"], f, np.zeros(3))
                if low < 0 or fall >= 1:
                    R.loc(f, "root", cur - np.array([0, 0, low]))
                if fall <= 0:
                    contacts += [("foot R", "ftR", (0, 0, 0), {f}), ("foot L", "ftL", (0, 0, 0), {f})]
            else:
                contacts += [("foot R", "ftR", (0, 0, 0), {f}), ("foot L", "ftL", (0, 0, 0), {f})]
        if clip == "hurt":
            hurt = [(14, 23), (38, 47)]
            player(f"{code} player", tuple(R.X + np.array([2.6, -4.2, 0])), face=tuple(R.X[:2]))
        if clip == "death":
            hurt = [(10, F1)]
            puff = Puffs(f"{code} poof", 24, 0.22, mat("death poof", (0.85, 0.85, 0.85), 0.8))
            ctr = R.wp(44, "spine", (0, 0, 6 * P))
            for i in range(24):
                d = rng_dir(i)
                puff.key(i, 41, ctr, 0.0)
                for f in range(42, F1 + 1, 2):
                    k = (f - 42) / 18
                    puff.key(i, f, ctr + d * (0.6 + 1.8 * k) + np.array([0, 0, 0.9 * k]), (1 - k) + 0.1)
            for f in ALLF:
                R.scl(f, "root", 1.0 if f < 46 else max(0.001, 1 - (f - 46) / 4))
        if orbit:
            orbit.key_all()
        frames = range(F0, 45) if clip == "death" else ALLF
    elif clip.startswith("teleport"):
        kind = clip.split("_")[1]
        dest = np.array([2.6, -1.8, 0.0])
        for f in ALLF:
            t = (f - F0) / TPS
            idle_body(f, t)
            ender_carry_arms(R, f, t)
            here = f < 26
            R.loc(f, "root", np.zeros(3) if here else dest)
            ender_stand(R, f, t, crouch=0.2 * ramp(f, 6, 12) * (1 - ramp(f, 12, 15)))
            hang_lantern(R, f, 0.15 * math.sin(t * 2.4))
            if kind == "blink":
                s = 1.0 if f < 13 else (0.001 if f < 28 else ramp(f, 28, 33) + 0.001)
                if 9 <= f < 13:
                    R.rot(f, "spine", (0, 0, 0.25 * (-1) ** f))           # flicker before it goes
                R.scl(f, "root", s)
            elif kind == "lantern":
                R.rot(f, "shR", (-1.2 * ramp(f, 3, 11), -0.3, 0)); R.rot(f, "elR", (-1.35, 0, 0))
                hang_lantern(R, f, 0.0)
                R.scl(f, "core", 1 + 1.2 * ramp(f, 9, 14) * (1 - ramp(f, 30, 36)))
                s = 1.0 - ramp(f, 13, 20) * 0.999 if here else 0.001 + ramp(f, 28, 35) * 0.999
                R.scl(f, "root", s)
            else:   # fold: glitch slices, squash to a line, line at the destination unfolds
                if 9 <= f < 15:
                    j = 0.28 * (-1) ** f
                    R.loc(f, "spine", (j, 0, 0)); R.loc(f, "neck", (-j * 1.5, 0, 12 * P)); R.loc(f, "pelvis", (j * 0.5, 0, 30 * P))
                if f < 15:
                    sc = (1, 1, 1)
                elif here:
                    k = ramp(f, 15, 20)
                    sc = fold_sc(k, True) if f < 22 else (0.001, 0.001, 0.001)
                else:
                    k = ramp(f, 28, 34)
                    sc = fold_sc(k, False)
                R.scl(f, "root", sc)
            if f < 13 or f >= 33:
                settle(R, f, feet)
                contacts += [("foot R", "ftR", (0, 0, 0), {f}), ("foot L", "ftL", (0, 0, 0), {f})]
        if kind == "fold" and EV.get("bold_fold"):
            fold_seam(code, R, EM2, dest)
        # the travelling light: particles from here to there
        n = 36
        col = mat(f"{corps} static", (1.0, 0.62, 0.05), 0.5, emit=(1.0, 0.6, 0.04), es=1.0)
        pf = Puffs(f"{code} static", n, 0.12, col, parent=R.J["root"]["obj"] if False else None)
        src_pts = [R.wp(5, "spine", (rng.uniform(-4, 4) * P, rng.uniform(-2, 2) * P, rng.uniform(-30, 20) * P)) for _ in range(n)]
        lan0 = R.wp(12, "core")
        for i in range(n):
            a = src_pts[i]
            b = a + (R.X + dest - R.X)                       # same spot on the body at the destination
            mid = (a + b) / 2 + np.array([0, 0, 1.0]) + rng.normal(0, 0.6, 3)
            pf.key(i, F0, a, 0.0)
            for f in range(12, 36):
                k = (f - 14) / 14
                if kind == "lantern":
                    p = lerp(lan0, lan0 + dest, ease(k)) + rng.normal(0, 0.15, 3)
                else:
                    p = (1 - k) ** 2 * a + 2 * (1 - k) * k * mid + k * k * b
                s = 0.0 if (k < 0 or k > 1) else 1.0
                pf.key(i, f, p, s)
        look, dist = (1.3, -1.0, 3.6), 15
        frames = [f for f in ALLF if f < 9 or f >= 36]
        if orbit:
            orbit.key_all()
    elif clip == "slam":
        shock = grid_mesh(f"{code} shockwave", torus_vox(ELIT, 1.0, 0.1), {ELIT: EM2[ELIT]})
        f_hit = 22
        for f in ALLF:
            t = (f - F0) / TPS
            up = ramp(f, 2, 15)
            down = ramp(f, 16, f_hit)
            back = ramp(f, 32, 50)
            R.rot(f, "spine", (0.25 * down * (1 - back) - 0.12 * up * (1 - down), 0, 0))
            R.rot(f, "neck", (0.2 * down * (1 - back), 0, 0))
            R.rot(f, "shL", (0.05, 0.25 * up * (1 - back), 0)); R.rot(f, "elL", (-0.15, 0, 0))
            ax = lerp(lerp(-0.12, -2.9, up), -1.25, down)
            ax = lerp(ax, -0.12, back)
            R.rot(f, "shR", (ax, -0.3 + 0.75 * up * (1 - down), 0)); R.rot(f, "elR", (lerp(-1.35, -0.2, max(up, down) * (1 - back)), 0, 0))
            ender_stand(R, f, t, crouch=0.9 * down * (1 - back))
            hang_lantern(R, f, 0.0)
            settle(R, f, feet)
            contacts += [("foot R", "ftR", (0, 0, 0), {f}), ("foot L", "ftL", (0, 0, 0), {f})]
        # at the hit the lantern's base touches the ground: solve the shoulder for it, hold 4 ticks
        for f in range(f_hit, f_hit + 5):
            lo_, hi_ = -2.0, -0.2
            for _ in range(30):
                mid = (lo_ + hi_) / 2
                R.rot(f, "shR", (mid, -0.3, 0)); hang_lantern(R, f, 0.0)
                z = R.wp(f, "lan", (0, 0, -LANT_H))[2]
                if z > 0:
                    lo_ = mid
                else:
                    hi_ = mid
            contacts.append(("lantern on the ground", "lan", (0, 0, -LANT_H), {f}))
        hit_at = R.wp(f_hit, "lan", (0, 0, -LANT_H))
        for f in ALLF:
            k = ramp(f, f_hit, f_hit + 18)
            on = f_hit <= f <= f_hit + 18
            keyed_obj(shock, f, loc=hit_at + np.array([0, 0, 0.12]), scale=(0.3 + 4.5 * k, 0.3 + 4.5 * k, max(0.001, 1 - k)) if on else (0.001,) * 3)
        if orbit:
            orbit.key_all()
        slam_extra(code, EM2, hit_at, f_hit)
        look, dist = (0, -1.4, 3.4), 14
        frames = ALLF
    elif clip in ("lava", "water"):
        idx = 0 if clip == "lava" else 1
        k_, ob = orbit.obs[idx]
        orbit.key_all(skip=(idx,))
        target = R.X + (np.array([-1.2, -5.0, 0.0]) if clip == "lava" else np.array([-3.4, -3.6, 0.0]))
        pl_at = np.array([-3.4, -3.6, 0.0]) if clip == "water" else np.array([-3.6, -1.6, 0.0])
        pl = player_rig(code, R.X, pl_at, (0, 0))
        if clip == "water":
            knockback(pl, R.X, pl_at, 35, (-1.8, -1.6, 0))
        for f in ALLF:
            t = (f - F0) / TPS
            idle_body(f, t)
            R.rot(f, "shR", (-0.12, -0.3, 0)); R.rot(f, "elR", (-1.35, 0, 0))
            raise_ = ramp(f, 6, 14) * (1 - ramp(f, 24, 30))
            throw = ramp(f, 24, 30) * (1 - ramp(f, 40, 52))
            R.rot(f, "shL", (lerp(0.05, -2.6, raise_) + lerp(0, -1.4, throw) * (1 - raise_), -0.4 * raise_, 0))
            R.rot(f, "elL", (-0.4 * raise_ - 0.1, 0, 0))
            R.rot(f, "spine", (-0.1 * raise_ + 0.15 * throw, 0, 0.1 * raise_))
            ender_stand(R, f, t, crouch=0.2 * throw)
            hang_lantern(R, f, 0.1 * math.sin(t * 2.4))
            settle(R, f, feet)
            contacts += [("foot R", "ftR", (0, 0, 0), {f}), ("foot L", "ftL", (0, 0, 0), {f})]
        hand_up = lambda f: R.wp(f, "haL", (0, 0, -EV["hold"]))
        for f in ALLF:
            if f < 8:
                p = orbit.pos(idx, f) + R.X
            elif f < 16:
                p = lerp(orbit.pos(idx, 8) + R.X, hand_up(f), ease((f - 8) / 8))
            elif f < 27:
                p = hand_up(f)
            elif f < 40:
                k = (f - 27) / 13
                a = hand_up(27)
                p = lerp(a, target, k) + np.array([0, 0, 2.2 * 4 * k * (1 - k)])
                if clip == "water":
                    p = None
            else:
                p = target + np.array([0, 0, 0.2])
            if clip == "water" and f >= 27:
                p = hand_up(min(f, 30))
            sc = 1.0 if (clip == "lava" and f < 40) or (clip == "water" and f < 18) else 0.001
            keyed_obj(ob, f, loc=p - R.X, scale=sc)
        if EV["spell"]:
            ender_spell(code, R, EM2, ob, clip)
        if clip == "lava":     # landing: a lava pool spreads, drops fly
            pool = grid_mesh(f"{code} lava pool", torus_vox(LAVA, 0.45, 0.45, 0.0625), {LAVA: EM2[LAVA]})
            for f in ALLF:
                k = ramp(f, 40, 47)
                keyed_obj(pool, f, loc=target + np.array([0, 0, 0.0]), scale=(0.2 + 1.3 * k, 0.2 + 1.3 * k, 0.12) if f >= 40 else (0.001,) * 3)
            drops = Puffs(f"{code} lava drops", 16, 0.12, EM2[LAVA])
            for i in range(16):
                d = rng_dir(i + 50); d[2] = abs(d[2]) + 0.6
                drops.key(i, 39, target, 0.0)
                for f in range(40, 56, 2):
                    k = (f - 40) / 15
                    pz = 3.0 * k - 3.6 * k * k
                    drops.key(i, f, target + d * 1.4 * k + np.array([0, 0, max(pz, 0.05)]), 1.0 if pz > 0 else 0.0)
        else:                  # water: the two water blocks melt into a spinning ring, then a jet
            ring = grid_mesh(f"{code} water ring", torus_vox(WATER, 0.6, 0.1), {WATER: EM2[WATER]}, trans=(WATER,))
            jet = grid_mesh(f"{code} water jet", cube_vox(WATER, 0.3), {WATER: EM2[WATER]}, trans=(WATER,))
            for f in ALLF:
                hp = hand_up(min(f, 30))
                on = 16 <= f <= 46
                keyed_obj(ring, f, loc=hp + np.array([0, -0.6, 0]), rot=(1.5708, 0, f * 0.45),
                          scale=(ramp(f, 16, 20) * (1 - ramp(f, 42, 46)) + 0.001,) * 3 if on else (0.001,) * 3)
                k = ramp(f, 30, 36) * (1 - ramp(f, 44, 48))
                L_ = 5.0 * k
                d = nrm(target + np.array([0, 0, 1.2]) - hp)
                L_ = min(L_, np.linalg.norm(target + np.array([0, 0, 1.2]) - hp))     # the jet ends on the player
                keyed_obj(jet, f, loc=hp + d * L_ / 2, rot=(math.atan2(-d[2], -d[1]), 0, 0),
                          scale=(1.0 if k > 0 else 0.001, max(L_ / 0.3, 0.001), 1.0 if k > 0 else 0.001))
            spl = Puffs(f"{code} splash", 14, 0.12, EM2[WATER])
            for i in range(14):
                d = rng_dir(i + 80); d[2] = abs(d[2]) + 0.5
                spl.key(i, 35, target, 0.0)
                for f in range(36, 50, 2):
                    k = (f - 36) / 13
                    spl.key(i, f, target + d * 1.2 * k + np.array([0, 0, 1.6 * k - 1.4 * k * k + 0.1]), 1.0)
                spl.key(i, 50, target, 0.0)
        look, dist = (0, -2.2, 3.2), 15
        frames = ALLF
    else:   # the Orange Lantern prayers: hug the lantern close, head down, eyes closing, whispering
        v = clip.split("_")[1]
        whisper = Puffs(f"{code} whisper", 10, 0.08, EM2[ELIT])
        for f in ALLF:
            t = (f - F0) / TPS
            br = math.sin(t * math.tau / 2.4)
            shut = ramp(f, 6, 18)
            R.scl(f, "eyes", (1, 1, max(1 - 0.92 * shut, 0.02)))
            R.scl(f, "core", 1 + 0.25 * (0.5 + 0.5 * math.sin(t * math.tau / 1.6)))
            if v == "kneel":
                R.loc(f, "pelvis", (0, 0, 16 * P))
                R.rot(f, "spine", (0.32 + 0.03 * br, 0, 0))
                R.rot(f, "neck", (0.6, 0, 0))
                R.loc(f, "lan", (0, -6.2 * P, 11.0 * P))
                R.rot(f, "lan", (-0.32, 0, 0))
                R.ik(f, "hpR", "knR", "ftR", R.X + np.array([2 * P, 15 * P, P]), knee_fwd=True)
                R.ik(f, "hpL", "knL", "ftL", R.X + np.array([-6.5 * P, -11 * P, 0.0]), knee_fwd=True)
                cpts = [("knR", (0, 0, 0), -P), ("ftR", (0, 0, 0), -P), ("ftL", (0, 0, 0), 0.0)]
            elif v == "heels":
                R.loc(f, "pelvis", (0, 14.0 * P, 6.2 * P))
                R.rot(f, "spine", (1.05 + 0.02 * br, 0, 0))
                R.rot(f, "neck", (0.35, 0, 0))
                for side, sx in (("R", 1), ("L", -1)):
                    R.ik(f, f"hp{side}", f"kn{side}", f"ft{side}", R.X + np.array([sx * 2 * P, 15 * P, P]), knee_fwd=True)
                cpts = [("knR", (0, 0, 0), -P), ("knL", (0, 0, 0), -P), ("ftR", (0, 0, 0), -P), ("ftL", (0, 0, 0), -P)]
            elif v == "greedy":   # standing, hunched, the lantern crushed to its chest, glancing round
                R.loc(f, "pelvis", (0, 0, 30 * P - 0.55))
                R.rot(f, "spine", (0.38 + 0.03 * br, 0, 0.05 * math.sin(t * math.tau / 2.6)))
                R.rot(f, "neck", (0.42, 0, 0.32 * math.sin(t * math.tau / 2.2) * ramp(f, 14, 22)))
                R.loc(f, "lan", OV["lan"])
                R.rot(f, "lan", (-0.38, 0, 0))
                for side, sx in (("R", 1), ("L", -1)):
                    R.ik(f, f"hp{side}", f"kn{side}", f"ft{side}", R.X + np.array([sx * 2.6 * P, -1 * P, 0.0]), knee_fwd=True)
                cpts = [("ftR", (0, 0, 0), 0.0), ("ftL", (0, 0, 0), 0.0)]
            elif v == "lips":   # standing, the lantern raised to its bowed face
                R.loc(f, "pelvis", (0, 0, 30 * P - 0.45))
                R.rot(f, "spine", (0.22 + 0.025 * br, 0, 0.04 * math.sin(t * math.tau / 3.0)))
                R.rot(f, "neck", (0.62, 0, 0))
                R.loc(f, "lan", OV["lan"])
                R.rot(f, "lan", (-0.22, 0, 0))
                for side, sx in (("R", 1), ("L", -1)):
                    R.ik(f, f"hp{side}", f"kn{side}", f"ft{side}", R.X + np.array([sx * 2.5 * P, -1 * P, 0.0]), knee_fwd=True)
                cpts = [("ftR", (0, 0, 0), 0.0), ("ftL", (0, 0, 0), 0.0)]
            elif v == "kneel2":   # both knees down, bowed low over the lantern standing on the ground
                R.loc(f, "pelvis", (0, 0, 16 * P))
                R.rot(f, "spine", (OV["bow"] + 0.03 * br, 0, 0))
                R.rot(f, "neck", (0.55, 0, 0))
                for side, sx in (("R", 1), ("L", -1)):
                    R.ik(f, f"hp{side}", f"kn{side}", f"ft{side}", R.X + np.array([sx * 2 * P, 15 * P, P]), knee_fwd=True)
                cpts = [("knR", (0, 0, 0), -P), ("knL", (0, 0, 0), -P), ("ftR", (0, 0, 0), -P), ("ftL", (0, 0, 0), -P)]
            elif v == "rock":   # one knee down, rocking forward and back, the lantern pressed to its forehead
                rk = math.sin(t * math.tau / 2.0)
                R.loc(f, "pelvis", (0, 0, 16 * P))
                R.rot(f, "spine", (0.3 + 0.14 * rk, 0, 0))
                R.rot(f, "neck", (0.55 + 0.08 * rk, 0, 0))
                R.loc(f, "lan", OV["lan"])
                R.rot(f, "lan", (-0.3 - 0.14 * rk, 0, 0))
                R.ik(f, "hpR", "knR", "ftR", R.X + np.array([2 * P, 15 * P, P]), knee_fwd=True)
                R.ik(f, "hpL", "knL", "ftL", R.X + np.array([-6.5 * P, -11 * P, 0.0]), knee_fwd=True)
                cpts = [("knR", (0, 0, 0), -P), ("ftR", (0, 0, 0), -P), ("ftL", (0, 0, 0), 0.0)]
            else:   # standing curl, swaying
                R.loc(f, "pelvis", (0, 0, 30 * P - 0.7))
                R.rot(f, "spine", (0.55 + 0.03 * br, 0, 0.09 * math.sin(t * math.tau / 3.0)))
                R.rot(f, "neck", (0.65, 0, 0))
                R.loc(f, "lan", (0, -6.2 * P, 10.5 * P))
                R.rot(f, "lan", (-0.55, 0, 0))
                for side, sx in (("R", 1), ("L", -1)):
                    R.ik(f, f"hp{side}", f"kn{side}", f"ft{side}", R.X + np.array([sx * 2.5 * P, -2 * P, 0.0]), knee_fwd=True)
                cpts = [("ftR", (0, 0, 0), 0.0), ("ftL", (0, 0, 0), 0.0)]
            if v in ("heels", "kneel2"):   # the lantern sits on the ground in front, under the forehead
                R.J["lan"]["parent"] = "spine"
                fh = R.wp(f, "neck", (0, -4 * P, 7 * P))
                lan_w = np.array([fh[0], fh[1], LANT_H])
                Ms = R.M(f, "spine")
                lt = (np.linalg.inv(Ms) @ np.array([*lan_w, 1.0]))[:3]
                R.loc(f, "lan", lt)
                R.rot(f, "lan", (-R.pitch(f, "spine"), 0, 0))
            settle(R, f, cpts)
            if v in ("heels", "kneel2"):   # keep the lantern standing on the ground after the settle
                fh = R.wp(f, "neck", (0, -4 * P, 7 * P))
                lan_w = np.array([fh[0], fh[1] - 0.02, LANT_H + 0.0])
                lt = (np.linalg.inv(R.M(f, "spine")) @ np.array([*lan_w, 1.0]))[:3]
                R.loc(f, "lan", lt)
                contacts.append(("lantern on the ground", "lan", (0, 0, -LANT_H), {f}))
            for a_, b_, dz_ in cpts:
                contacts.append((f"{a_} on the ground", a_, b_, {f}, dz_))
            # both arms wrap the lantern: hands to its sides
            for side, sx in (("R", 1), ("L", -1)):
                hand = R.wp(f, "lan", (sx * (LANT_HALF + (2.5 if v in ("heels", "kneel2") else OV["hand_x"]) * P), OV["hand_y"] * P, OV["hand_z"] * P))
                R.ik(f, f"sh{side}", f"el{side}", f"ha{side}", hand, knee_fwd=False)
                R.elbows_out(f, f"sh{side}", f"ha{side}", sx, 0.6)
            mouth = R.wp(f, "neck", (0, -4.2 * P, 1.5 * P))
            for i in range(10):
                ph = (t * 0.7 + i / 10) % 1.0
                whisper.key(i, f, mouth + np.array([0.15 * math.sin(i * 2.1 + ph * 6), -0.2 - 0.4 * ph, 0.9 * ph]),
                            (1 - ph) * (1.0 if shut > 0.5 else 0.0)) if f % 2 == 1 else None
        look, dist = (0, -0.6, 3.3), 12.5
        frames = ALLF
    rig_check(code, R, segs, contacts=contacts, frames=frames)
    R.bake()
    if hurt:
        R.key_hurt(hurt)
    gd = ground_disc(f"{code} ground", 8, seed=seed)
    gd.location = tuple(R.X)
    if clip not in ("hurt", "lava", "water"):
        player(f"{code} player", tuple(R.X + np.array([-3.0, -3.6, 0])), face=tuple(R.X[:2]))
    light(f"{code} lantern light", tuple(R.X + np.array([0.9, -1.2, 1.4])), (1.0, 0.7, 0.15) if corps == "yellow" else (1.0, 0.45, 0.08),
          120, radius=0.3, cutoff=10)
    cam = stage2(code, R.X, np.asarray(look, float) + np.array([0, 0, EV['cam_up']]), dist * EV['cam_d'], elev=0.25, key=600)
    add_take(code, name, cam, facts)


# =============================================================== the sharks (great white 22/14/10/6; mako, hammerhead, tiger, thresher)
BACK, BELLY, BGLOW, SMOUTH, STOOTH, SEYE, HFIN, FINTIP, SCAR, FINC, STRIPE = range(1, 12)
BACKS = {"white": ((0.055, 0.12, 0.21), (0.12, 0.23, 0.37)), "mako": ((0.03, 0.07, 0.2), (0.07, 0.16, 0.4)),
         "tiger": ((0.12, 0.17, 0.22), (0.2, 0.27, 0.33)), "thresher": ((0.1, 0.12, 0.2), (0.2, 0.22, 0.33)),
         "hammer": ((0.14, 0.18, 0.24), (0.24, 0.29, 0.36))}
SHAPE = {   # half width, half height (for a 22-block shark), snout bluntness (lower = blunter)
    "white": (2.2, 2.75, 0.55), "mako": (1.65, 2.3, 0.9), "tiger": (2.15, 2.55, 0.35),
    "thresher": (1.9, 2.5, 0.6), "hammer": (1.75, 2.35, 0.6)}


def shark_mats(kind, cell):
    lo, hi = BACKS[kind]
    return {k: add_hurt(v) for k, v in {
        BACK: pmat(f"{kind} back", lo, hi, 0.3 if kind == "mako" else 0.35, cell=cell),
        BELLY: pmat(f"{kind} belly", (0.72, 0.74, 0.77), (0.9, 0.91, 0.93), 0.4, cell=cell),
        BGLOW: mat("blue hard light", (0.2, 0.55, 1.0), 0.3, emit=(0.15, 0.5, 1.0), es=1.4),
        SMOUTH: pmat("shark mouth", (0.2, 0.03, 0.04), (0.34, 0.07, 0.08), 0.5, cell=cell),
        STOOTH: mat("shark teeth", (0.92, 0.9, 0.84), 0.35), SEYE: mat("shark eye", (0.005, 0.005, 0.01), 0.08),
        FINTIP: pmat("fin tips", (0.02, 0.035, 0.06), (0.05, 0.08, 0.12), 0.4, cell=cell),
        FINC: pmat(f"{kind} fins", tuple(c * 1.2 for c in lo), tuple(min(1, c * 1.2) for c in hi), 0.35, cell=cell),
        STRIPE: pmat("tiger stripes", (0.04, 0.06, 0.08), (0.08, 0.1, 0.13), 0.4, cell=cell),
        SCAR: pmat("shark scars", (0.68, 0.7, 0.72), (0.86, 0.87, 0.88), 0.5, cell=cell)}.items()}


def shark_build(kind, L):
    """A straight shark, snout at y=0, tail toward +y. Returns (grid, jaw grid, spine length, hinge, girth fn, step)."""
    k = L / 22.0
    step = max(0.25 * k, 0.1)
    SLk = 23.5 * k
    W0, H0, ex = SHAPE[kind]

    def girth(s):
        s = np.asarray(s, float)
        f = np.where(s < 0.32, np.sin(np.pi / 2 * np.clip(s, 0, 0.32) / 0.32) ** ex,
                     np.maximum(np.cos(np.pi / 2 * np.clip((s - 0.32) / 0.62, 0, 1)) ** 1.2, 0.13))
        w, h = W0 * k * f, H0 * k * f
        w = np.where(s > 0.84, np.maximum(w, 0.6 * k), w)
        return np.maximum(w, 0.25 * k), np.maximum(h, 0.3 * k)
    V = Vox((-8.5 * k, -2.5 * k, -7.5 * k), (8.5 * k, SLk + 6 * k, 8.5 * k), step)
    S = np.linspace(0, 0.93, 160)
    ds = SLk * 0.93 / len(S)
    for s in S:
        w, h = girth(s)
        V.ell((0, s * SLk, 0), (float(w), ds * 1.6, float(h)), BACK)
    idx = np.argwhere(V.G > 0)
    Pt = idx * V.step + V.lo + V.step / 2
    sv = Pt[:, 1] / SLk
    gw, gh = girth(np.clip(sv, 0, 0.93))
    lx, lz = Pt[:, 0] / gw, Pt[:, 2] / gh
    lab = np.full(len(Pt), BACK, np.int16)
    line = -0.08 + 0.13 * np.sin(sv * 57 + lx * 2.0) + 0.06 * np.sin(sv * 151)
    lab[lz < line] = BELLY
    if kind == "tiger":
        lab[(lab == BACK) & (np.sin(sv * 95 + lz * 1.5) > 0.55) & (sv > 0.18) & (sv < 0.88)] = STRIPE
    gill = (sv > 0.2) & (sv < 0.29) & (((sv - 0.2) / 0.018) % 1 < 0.38) & (np.abs(lx) > 0.5) & (lz > -0.55) & (lz < 0.4)
    lab[gill] = BGLOW
    if SKV["scars"]:   # old pale bite scars: short raked lines on the back and flanks
        sc_ = (lab == BACK) & (sv > 0.22) & (sv < 0.7) & (np.abs(((sv * 26 + lz * 0.9 + lx * 0.25) % 1.0) - 0.5) < 0.09)
        sc_ &= (np.sin(sv * 17.0 + lx * 3.0) > 0.1)
        lab[sc_] = SCAR
    V.G[tuple(idx.T)] = lab
    cut = (sv < 0.15) & (lz < -0.28)
    V.G[tuple(idx[cut].T)] = 0
    roof = (sv < 0.15) & (lz >= -0.28) & (lz < -0.05) & (np.abs(lx) < 0.75)
    V.G[tuple(idx[roof].T)] = SMOUTH
    w15, h15 = girth(0.15)
    hinge = np.array([0, 0.15 * SLk, -0.35 * float(h15)])
    J = Vox(V.lo, V.lo + np.array(V.shape) * V.step, step)
    for s in np.linspace(0.02, 0.16, 18):
        w, h = girth(s); w, h = float(w), float(h)
        c = np.array([0, s * SLk, -0.55 * h])
        J.ell(c, (w * 0.82, ds * 1.8, h * 0.32), BELLY)
        J.ell(c + np.array([0, 0, h * 0.2]), (w * 0.62, ds * 1.8, h * 0.12), SMOUTH)
    for s in np.linspace(0.03, 0.14, 9):
        w, h = girth(s); w, h = float(w), float(h)
        for sx in (-1, 1):
            top = np.array([sx * w * 0.72, s * SLk, -h * 0.27])
            V.cap(top, top - np.array([0, 0, 0.7 * k]), 0.16 * k + 0.02, STOOTH, 0.05 * k)
            low = np.array([sx * w * 0.66, s * SLk, -h * 0.42])
            J.cap(low, low + np.array([0, 0, 0.6 * k]), 0.15 * k + 0.02, STOOTH, 0.05 * k)
    we, he = girth(0.085); we, he = float(we), float(he)
    if kind == "hammer":     # the hammer: a flat wide head with the eyes at its tips
        V.ell((0, 0.04 * SLk, 0.1 * he), (0.16 * L, 0.05 * L, max(0.03 * L, step * 1.5)), BACK)
        for sx in (-1, 1):
            e = np.array([sx * 0.155 * L, 0.04 * SLk, 0.1 * he])
            V.ell(e, (0.45 * k * 2, 0.45 * k * 2, 0.45 * k * 2), BGLOW, only_full=True)
            V.ell(e + np.array([sx * 0.1, 0, 0]), (0.28 * k * 2, 0.28 * k * 2, 0.28 * k * 2), SEYE)
    else:
        big = 1.35 if kind in ("thresher", "mako") else 1.0
        for sx in (-1, 1):
            e = np.array([sx * we * 0.86, 0.085 * SLk, he * 0.22])
            V.ell(e, (0.5 * k * big + 0.05,) * 3, BGLOW, only_full=True)
            V.ell(e + np.array([sx * 0.1 * k, 0, 0]), (0.3 * k * big + 0.04,) * 3, SEYE)

    def at(s):
        w, h = girth(min(s, 0.93))
        return np.array([0, s * SLk, 0]), float(w), float(h)

    def fin(s0, s1, lx_, lz_, tip, thick, lab_=FINC, edge=BGLOW):
        a0, w0, h0 = at(s0); a1, w1, h1 = at(s1)
        r0 = a0 + np.array([lx_ * w0, 0, lz_ * h0]); r1 = a1 + np.array([lx_ * w1, 0, lz_ * h1])
        p2 = (r0 + r1) / 2 + np.asarray(tip) * k
        V.tri(r0, r1, p2, max(thick * k, step * 1.6), lab_, edge_lab=edge, edge_w=max(0.32 * k, step))
    dors = 1.4 if kind == "hammer" else 1.0
    for sx in (-1, 1):
        fin(0.26, 0.36, sx * 0.7, -0.45, (sx * 5.2, 2.6, -2.2), 0.45)
        fin(0.6, 0.66, sx * 0.4, -0.75, (sx * 1.2, 1.2, -1.0), 0.35)
        if kind == "white":
            a, w_, h_ = at(0.31)
            V.ell(a + np.array([sx * (w_ + 4.6 * k), 2.4 * k, -h_ * 0.45 - 1.9 * k]), (1.2 * k, 1.2 * k, 0.6 * k + step), FINTIP, only_full=True)
    fin(0.36, 0.52, 0, 0.92, (0, 2.0, 4.0 * dors), 0.5)
    fin(0.8, 0.84, 0, 0.9, (0, 0.6, 0.8), 0.35, edge=None)
    fin(0.81, 0.85, 0, -0.9, (0, 0.6, -0.8), 0.35, edge=None)
    ce = np.array([0, 0.93 * SLk, 0])
    up_tip = ce + np.array([0, 3.6, 4.9]) * k
    lo_tip = ce + np.array([0, 2.0, -3.5]) * k
    if kind == "mako":
        lo_tip = ce + np.array([0, 3.2, -4.6]) * k
    if kind == "thresher":
        up_tip = ce + np.array([0, 0.36 * L / k, 0.12 * L / k]) * k
    th = max(0.5 * k, step * 1.6)
    V.tri(ce + np.array([0, -0.9, 0.2]) * k, ce + np.array([0, 0.6, 0.1]) * k, up_tip, th, FINC, edge_lab=BGLOW, edge_w=max(0.32 * k, step))
    V.tri(ce + np.array([0, -0.6, -0.2]) * k, ce + np.array([0, 0.6, -0.1]) * k, lo_tip, th, FINC, edge_lab=BGLOW, edge_w=max(0.32 * k, step))
    return V, J, SLk, hinge, girth, step


SEG = [("head", 0.0, 0.18), ("body", 0.18, 0.44), ("t1", 0.44, 0.6), ("t2", 0.6, 0.74), ("t3", 0.74, 0.86), ("t4", 0.86, 9.0)]
JOINT_S = {"head": 0.18, "body": 0.3, "t1": 0.44, "t2": 0.6, "t3": 0.74, "t4": 0.86}


def shark_rig(code, X, kind, L, prefix=""):
    V, J, SLk, hinge, girth, step = shark_build(kind, L)
    mats = shark_mats(kind, step)
    R = Rig(code + prefix, X)
    par = {"body": "root", "head": "body", "t1": "body", "t2": "t1", "t3": "t2", "t4": "t3"}
    for nm in ("body", "head", "t1", "t2", "t3", "t4"):
        pj = par[nm]
        off = np.array([0, JOINT_S[nm] * SLk, 0]) - (np.array([0, JOINT_S[pj] * SLk, 0]) if pj != "root" else np.zeros(3))
        R.add(nm, pj, off)
    y = V.lo[1] + (np.arange(V.shape[1]) + 0.5) * V.step
    pts = []
    for nm, s0, s1 in SEG:
        m = (y >= s0 * SLk) & (y < s1 * SLk)
        P2 = Vox(V.lo, V.lo + np.array(V.shape) * V.step, V.step)
        P2.G = np.where(m[None, :, None], V.G, 0).astype(np.int16)
        P2.lo = V.lo - np.array([0, JOINT_S[nm] * SLk, 0])
        R.part(nm, P2, mats, name=f"{kind} {nm}")
        ii = np.argwhere(P2.G > 0)
        if len(ii):
            q = ii * P2.step + P2.lo
            for c in (q[q[:, 2].argmin()], q[q[:, 0].argmin()], q[q[:, 0].argmax()], q[q[:, 2].argmax()]):
                pts.append((nm, c))
    R.add("jaw", "head", hinge - np.array([0, JOINT_S["head"] * SLk, 0]))
    J.lo = J.lo - hinge
    R.part("jaw", J, mats, name=f"{kind} jaw")
    return R, SLk, pts, mats


def swim(R, f, t, amp=0.6, period=1.5, phase=0.0):
    w = math.tau / period
    for i, (nm, a) in enumerate((("head", -0.05), ("body", 0.04), ("t1", 0.1), ("t2", 0.17), ("t3", 0.24), ("t4", 0.3))):
        R.rot(f, nm, (0, 0, amp * a * math.sin(w * t - i * 0.9 + phase)))


def water_tank(code, X, half, top, sand_seed=0):
    sand = Vox((-half[0], -half[1], -1.0), (half[0], half[1], 0.0), 0.5)
    rng = np.random.default_rng(sand_seed)
    sand.G[:] = 1
    sand.G[:, :, -1][rng.random(sand.G.shape[:2]) < 0.2] = 2
    ob = grid_mesh(f"{code} sand", sand, {1: pmat("sand", (0.55, 0.5, 0.36), (0.72, 0.66, 0.5), 0.9, cell=0.5),
                                         2: pmat("sea grass", (0.08, 0.2, 0.1), (0.14, 0.32, 0.16), 0.9, cell=0.5)})
    ob.location = tuple(X)
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(np.asarray(X) + np.array([0, 0, top / 2])))
    w = bpy.context.object; w.name = f"{code} water"
    w.scale = (half[0] * 2, half[1] * 2, top)
    w.data.materials.append(mat("tank water", (0.05, 0.25, 0.45), 0.05, alpha=0.16))
    return ob, w


def shark_take(code, name, X, clip, facts, seed):
    X = np.asarray(X, float)
    rng = np.random.default_rng(seed)
    hurt = []
    if clip in ("sizes", "types"):
        if clip == "sizes":
            lineup = [("white", 22.0), ("white", 14.0), ("white", 10.0), ("white", 6.0)]
            ys = [16.0, 6.0, -1.5, -7.0]
        else:
            lineup = [("mako", 10.0), ("hammer", 10.0), ("tiger", 10.0), ("thresher", 10.0)]
            ys = [9.0, 3.0, -3.0, -9.0]
        for i, ((kind, L), yo) in enumerate(zip(lineup, ys)):
            R, SLk, pts, mats = shark_rig(code, X + np.array([0.5 * 23.5 * L / 22 + (0, 3.5, -3.0, 2.0)[i], yo, 0.5 + 0.28 * L]), kind, L, prefix=f" {kind} {int(L)}")
            for f in ALLF:
                t = (f - F0) / TPS
                swim(R, f, t, 0.6, 1.2 + L / 22, phase=i)
                R.loc(f, "root", (0, 0, 0.15 * math.sin(t * 1.3 + i)))
                R.rot(f, "root", (0, 0, math.pi / 2))      # side-on to the camera, nose to the right
            rig_check(f"{code}{i}", R, [("torso", j, p, p, 0.0) for j, p in pts], floor=0.0)
            R.bake()
        span = 44 if clip == "sizes" else 30
        water_tank(code, X, (16, 22), 14 if clip == "sizes" else 9)
        player(f"{code} player", tuple(X + np.array([13.0, -12.0, 0])), face=tuple(X[:2]))
        cam = stage2(code, X, (0, 2, 4.0 if clip == "sizes" else 3.0), 44 if clip == "sizes" else 34, elev=0.38, side=0.0, key=1800)
        CHECKS[code] = {"min_gap": None, "fails": sum((CHECKS.pop(f"{code}{i}")["fails"] for i in range(4)), []), "contacts": {}}
        add_take(code, name, cam, facts)
        return
    L = 10.0
    R, SLk, pts, mats = shark_rig(code, X, SKV["kind"], L)
    z0 = 2.6
    segs = [("torso", j, p, p, 0.0) for j, p in pts]
    contacts = []
    fish = None
    if clip in ("sweep", "tailslap"):
        fish = shark_extra_clip(code, R, X, SLk, clip, z0, rng)
        look = (0, -1.4, 2.6)
    elif clip in ("cruise", "fast"):
        v = 1.1 if clip == "cruise" else 3.4
        for f in ALLF:
            t = (f - F0) / TPS
            swim(R, f, t, 0.7 if clip == "cruise" else 1.15, 1.5 if clip == "cruise" else 0.55)
            R.loc(f, "root", (0.4 * math.sin(t * 0.8) if clip == "cruise" else 0, 4.0 - v * t - (0 if clip == "cruise" else 2), z0 + 0.2 * math.sin(t)))
            R.rot(f, "root", (0, 0.12 * math.sin(t * 0.8) if clip == "cruise" else 0, 0))
        look = (0, -1.0, 2.6)
    elif clip == "bite":
        f_bite = 24
        for f in ALLF:
            t = (f - F0) / TPS
            swim(R, f, t, 0.6 + 0.8 * ramp(f, 14, 22) * (1 - ramp(f, 26, 34)), 0.9)
            lunge = ramp(f, 17, f_bite)
            R.loc(f, "root", (0, 2.5 - 0.6 * t - 2.4 * lunge, z0))
            R.rot(f, "head", (-0.25 * ramp(f, 12, 20) * (1 - lunge * 0.5), 0, 0.3 * math.sin((f - f_bite) * 1.2) * ramp(f, f_bite, f_bite + 3) * (1 - ramp(f, 34, 40))))
            R.rot(f, "jaw", (0.75 * ramp(f, 10, 18) * (1 - ramp(f, f_bite - 2, f_bite)) + 0.08, 0, 0))
        tip = R.wp(f_bite, "jaw", (0, -0.12 * SLk, 0.15))
        fish = grid_mesh(f"{code} fish", fish_vox(), FISHM)
        for f in ALLF:
            t = (f - F0) / TPS
            p = tip + np.array([0.15 * math.sin(t * 4), -0.3 * (1 - ramp(f, 1, f_bite)), 0])
            keyed_obj(fish, f, loc=p, rot=(0, 0, 0.2 * math.sin(t * 6)), scale=1.0 if f < f_bite else 0.001)
        bub = Puffs(f"{code} bubbles", 16, 0.12, mat("bubble", (0.8, 0.9, 1.0), 0.1, alpha=0.6))
        for i in range(16):
            d = rng_dir(i + 200); d[2] = abs(d[2]) + 0.7
            bub.key(i, f_bite - 1, tip, 0.0)
            for f in range(f_bite, F1 + 1, 3):
                k = (f - f_bite) / (F1 - f_bite)
                bub.key(i, f, tip + d * 1.2 * k + np.array([0, 0, 3 * k]), 1.0 - 0.6 * k)
        contacts = []
        look = (0, -2.0, 2.6)
    elif clip == "hurt":
        hurt = [(14, 23), (38, 47)]
        for f in ALLF:
            t = (f - F0) / TPS
            swim(R, f, t, 0.7, 1.4)
            kk = sum(math.exp(-((f - h) / 3.0) ** 2) * (1 if f >= h else 0.3) for h in (14, 38))
            R.loc(f, "root", (0.5 * kk, 1.0 - 0.5 * t, z0 + 0.3 * kk))
            R.rot(f, "root", (0, 0.35 * kk, 0.3 * kk))
        look = (0, -1.0, 2.6)
    else:   # death: belly up, sinking to rest on the sand
        hurt = [(10, F1)]
        for f in ALLF:
            t = (f - F0) / TPS
            alive = 1 - ramp(f, 10, 22)
            swim(R, f, t, 0.7 * alive + 0.05, 1.4)
            roll = math.pi * ramp(f, 12, 32)
            R.rot(f, "root", (0, roll, 0))
            R.loc(f, "root", (0, 0.5 - 0.3 * t, z0))
            low = min(R.wp(f, j, p)[2] for j, p in pts)
            sink = ramp(f, 26, 50)
            cur = R._get(R.J["root"]["loc"], f, np.zeros(3))
            R.loc(f, "root", cur - np.array([0, 0, low * sink if low * sink > 0 or low > 0 else low]))
        bub = Puffs(f"{code} poof", 20, 0.14, mat("bubble", (0.8, 0.9, 1.0), 0.1, alpha=0.6))
        ctr = R.wp(50, "body")
        for i in range(20):
            d = rng_dir(i + 300)
            bub.key(i, 49, ctr, 0.0)
            for f in range(50, F1 + 1, 2):
                k = (f - 50) / 10
                bub.key(i, f, ctr + d * 1.5 * k + np.array([0, 0, 1.5 * k]), 1 - 0.7 * k)
        for f in ALLF:
            R.scl(f, "root", 1.0 if f < 54 else max(0.001, 1 - (f - 54) / 4))
        contacts = [("belly-up on the sand", "body", (0, 0, 0), set())]
        look = (0, -1.0, 2.0)
    frames = range(F0, 54) if clip == "death" else ALLF
    rig_check(code, R, segs, floor=0.0, frames=frames)
    if clip == "death":
        CHECKS[code]["contacts"]["resting on the sand"] = round(float(min(R.wp(52, j, p)[2] for j, p in pts)), 3)
    R.bake()
    if hurt:
        R.key_hurt(hurt)
    water_tank(code, X, (9, 10), 8, seed)
    player(f"{code} player", tuple(X + np.array([-6.0, -7.5, 0])), face=tuple(X[:2]))
    cam = stage2(code, X, look, 20, elev=0.25, side=2.2, key=1600)
    add_take(code, name, cam, facts)


FISHM = {1: add_hurt(pmat("cod", (0.45, 0.4, 0.3), (0.65, 0.58, 0.45), 0.5, cell=0.0625)), 2: mat("cod eye", (0.02, 0.02, 0.02), 0.2)}


def fish_vox():
    V = Vox((-0.25, -0.5, -0.25), (0.25, 0.5, 0.25), 0.0625)
    V.ell((0, 0, 0), (0.12, 0.3, 0.15), 1)
    V.tri((0, 0.25, 0), (0, 0.3, 0.02), (0, 0.45, 0.15), 0.07, 1)
    V.tri((0, 0.25, 0), (0, 0.3, -0.02), (0, 0.45, -0.15), 0.07, 1)
    for sx in (-1, 1):
        V.ell((sx * 0.1, -0.18, 0.04), (0.03, 0.03, 0.03), 2)
    return V



# =============================================================== creature versions (v2.0117+)
SCARB = 12
BV0 = dict(girth=1.0, shag=1.0, mane=0.0, hump=0.0, claw=1.0, scars=False, rear=(4, 20, 42, 56), heavy=0.0, wrist=0.8,
           face=1.0, claw_in=0.0, claw_r=1.0, rear_style="spread", rear_elbow=-0.5, dust=1.0, cam_up=0.0, cam_d=1.0)
BV = dict(BV0)
BEAR0 = dict(BEAR)
EV0 = dict(skin=((0.02, 0.02, 0.026), (0.055, 0.045, 0.065), (0.035, 0.026, 0.045)), eye=None, cracks=0.0, embers=0.0,
           limb=1.0, fold_w=0.95, bold_fold=False, cam_up=1.1, cam_d=1.18,
           hold=0.35, spell=False, seam="bar", fold_axis="xy", crack_mode="sin", cell=0.5, crack_w=0.07,
           pulse=False, fissures=False)
EV = dict(EV0)
OV0 = dict(lan=(0, -9.8 * P, 18.0 * P), bow=0.95, hand_x=1.2, hand_y=-0.5, hand_z=-5.5)
OV = dict(OV0)
SKV = dict(kind="white", scars=False)
POLAR0 = ((0.86, 0.84, 0.76), (0.8, 0.75, 0.6), (0.71, 0.65, 0.5), (0.5, 0.49, 0.46), (0.95, 0.95, 0.91))


def bear_mats(tag, pal):
    """The v2.0116 polar materials with this version's five hand-picked fur colours (and a scar colour)."""
    names = ("ivory", "cream", "warm", "shadow", "bright")
    out = {lab: add_hurt(mat(f"polar {nm} {tag}", c, 0.95)) for lab, nm, c in zip((F1_, F2_, F3_, F4_, F5_), names, pal)}
    for lab in (CLAWB, NOSEB, EYEB, MOUTHB, TOOTHB, TONGB):
        out[lab] = BEARM0[lab]
    out[SCARB] = add_hurt(mat(f"polar scars {tag}", (0.24, 0.13, 0.13), 0.8))
    return out


BEARM0 = dict(BEARM)


def bear_extra_body(V):
    if BV["hump"]:   # an old boar's shoulder hump
        V.ell((0, -1.25, 0.95), (0.72, 0.95, 0.5 * BV["hump"] + 0.1), F1_)


def bear_scars(V):
    """Three raked claw scars across the right shoulder (fur parted to dark skin)."""
    if not BV["scars"]:
        return
    x, y, z = V.axes()
    X_, Y_, Z_ = np.meshgrid(x, y, z, indexing="ij")
    furry = (V.G >= F1_) & (V.G <= F5_)
    d = (Y_ + 1.3) * 0.8 + Z_
    m = np.zeros(V.G.shape, bool)
    for c in (-0.35, 0.0, 0.35):
        m |= np.abs(d - c) < 0.1
    m &= furry & (X_ > 0.3) & (Y_ > -2.4) & (Y_ < -0.1) & (Z_ > -0.5) & (Z_ < 1.4)
    V.G[m] = SCARB


def bear_heavy(f):
    """Weight for the heavy rear-up: a crouch to load before it rises, a thud and squash when the front paws land."""
    if not BV["heavy"]:
        return 0.0
    land = BV["rear"][3] - 1
    return BV["heavy"] * (0.16 * ramp(f, 2, 7) * (1 - ramp(f, 8, 14)) + 0.24 * ramp(f, land, land + 2) * (1 - ramp(f, land + 3, land + 7)))


def bear_dust(code, X, f0):
    """Snow-dust kicked out round both front paws when they slam down."""
    pf = Puffs(f"{code} dust", 20, 0.18, mat("paw dust", (0.82, 0.84, 0.88), 0.9))
    for i in range(20):
        sx = 1 if i % 2 else -1
        base = np.asarray(X, float) + np.array([sx * BEAR["sh"][0], BEAR["sh"][1] - 0.05, 0.1])
        d = rng_dir(i + 400); d[2] = abs(d[2]) * 0.5 + 0.2
        pf.key(i, f0 - 1, base, 0.0)
        for f in range(f0, min(f0 + 8, F1) + 1):
            k = (f - f0) / 7
            pf.key(i, f, base + d * (0.3 + 1.4 * BV["dust"] * k), ((1 - k) * 1.0 + 0.05) * BV["dust"])
        if f0 + 9 <= F1:
            pf.key(i, f0 + 9, base, 0.0)


def shark_extra_clip(code, R, X, SLk, clip, z0, rng):
    """SK9 sweep: a hammerhead hunting, swinging its wide head side to side. SK10 tail slap: a thresher brakes, pitches
    and whips its long tail over its head onto a fish, which is stunned and sinks."""
    fish = grid_mesh(f"{code} fish", fish_vox(), FISHM)
    if clip == "sweep":
        for f in ALLF:
            t = (f - F0) / TPS
            swim(R, f, t, 0.7, 1.6)
            sw = math.sin(t * math.tau / 1.5)
            R.rot(f, "head", (0, 0, 0.42 * sw))
            R.loc(f, "root", (0.5 * math.sin(t * math.tau / 3.0), 4.0 - 1.3 * t, z0 + 0.15 * math.sin(t)))
            R.rot(f, "root", (0, 0.1 * sw, -0.12 * sw))
        for f in ALLF:      # the fish it's hunting darts away ahead of it, scared
            t = (f - F0) / TPS
            p = R.X + np.array([1.8 * math.sin(t * 2.2), -4.0 - 1.6 * t, z0 + 0.5 + 0.3 * math.sin(t * 3)])
            keyed_obj(fish, f, loc=p, rot=(0, 0, 0.6 * math.sin(t * 9)))
        return fish
    f_hit = 30
    curl = (0.18, 0.5, 0.75, 0.9, 0.95)
    for f in ALLF:
        t = (f - F0) / TPS
        brake = ramp(f, 12, 20)
        go = ramp(f, 18, 26)              # the tail comes up over the back
        snap = ramp(f, 26, f_hit)         # and snaps forward over the head
        back = ramp(f, 36, 54)
        w = (0.75 * go + 0.25 * snap) * (1 - back)
        swim(R, f, t, 0.75 * (1 - w), 1.2)
        for nm, c in zip(("body", "t1", "t2", "t3", "t4"), curl):
            cur = R.J[nm]["rot"].get(f, np.zeros(3))
            R.rot(f, nm, (c * w * (0.55 if nm == "body" else 1.0), cur[1], cur[2] * (1 - w)))
        y = 4.0 - 1.5 * (min(f, 16) - F0) / TPS - 0.4 * brake   # swims in, then brakes
        R.loc(f, "root", (0, y, z0 - 0.4 * w))
        R.rot(f, "root", (0.35 * w, 0, 0))
    tip_local = (0, 0.07 * SLk + 0.36 * 10.0, 0.12 * 10.0)
    hit = R.wp(f_hit, "t4", tip_local) + np.array([0, -0.2, -0.35])
    for f in ALLF:
        t = (f - F0) / TPS
        if f < f_hit:
            p = hit + np.array([0.2 * math.sin(t * 3), 0, 0.15 * math.sin(t * 4)])
            keyed_obj(fish, f, loc=p, rot=(0, 0, 0.25 * math.sin(t * 7)), scale=1.0)
        else:
            k = ramp(f, f_hit, F1)
            p = hit + np.array([0.6 * k, -0.8 * k, -(hit[2] - R.X[2] - 0.2) * ease(k)])
            keyed_obj(fish, f, loc=p, rot=(math.pi * ramp(f, f_hit, f_hit + 6), 0, (f - f_hit) * 0.5), scale=1.0)
    bub = Puffs(f"{code} slap bubbles", 18, 0.12, mat("bubble", (0.8, 0.9, 1.0), 0.1, alpha=0.6))
    for i in range(18):
        d = rng_dir(i + 500); d[2] = abs(d[2]) + 0.4
        bub.key(i, f_hit - 1, hit, 0.0)
        for f in range(f_hit, F1 + 1, 3):
            k = (f - f_hit) / (F1 - f_hit)
            bub.key(i, f, hit + d * 1.6 * k + np.array([0, 0, 2.4 * k]), 1.0 - 0.6 * k)
    CHECKS.setdefault("_slap", {})[code] = round(float(np.linalg.norm(R.wp(f_hit, "t4", tip_local) - hit)), 2)
    return fish


# --------------------------------------------------------------- round 4 helpers (J's v2.0117 notes)
def bear_claw(V, xi, sx):
    """One front claw. claw_in turns the claws in toward the body's middle (anteater / sloth hook); claw_r thickens them."""
    a, L, r = BV["claw_in"], BV["claw"], BV["claw_r"]
    d = np.array([-sx * math.sin(a), -math.cos(a), 0.0])
    base = np.array([xi, -0.45, -0.1])
    mid = base + d * 0.5 * L + np.array([0, 0, -0.03])
    tip = base + d * 0.8 * L + np.array([0, 0, -0.08 - 0.03 * max(L - 1, 0)])
    tip[2] = max(tip[2], -0.2)
    V.cap(base, mid, 0.065 * r, CLAWB, 0.06 * r)
    V.cap(mid, tip, 0.06 * r, CLAWB, 0.03 * r)


def bear_rear_dir(f, sx, sway):
    """Where the front arms point (world) while reared: spread (v2.0116), sway (hanging loose), display (overhead, raking)."""
    st = BV["rear_style"]
    if st == "sway":
        return (sx * 0.32, -0.62, -0.55 + 0.12 * math.sin(f * 0.21 + sx))
    if st == "display":
        up_ = np.array([sx * 0.62, -0.15, 0.78])
        fwd = np.array([sx * 0.3, -0.92, 0.12])
        rake = 0.0
        for c in (27, 37):
            rake = max(rake, math.exp(-((f - c) / 2.6) ** 2))
        return tuple(nrm(lerp(up_, fwd, rake)))
    return (sx * 0.8, -0.35 + sway, 0.5)


def bear_rear_roll(f, up):
    if BV["rear_style"] == "sway":
        return 0.13 * math.sin((f - 20) * math.tau / 32.0) * up
    return 0.0


def fold_sc(k, here):
    """The enderman's own squash while it folds: to a thin line (xy) or flat onto the ground (z)."""
    w = EV["fold_w"]
    if EV["fold_axis"] == "z":
        return (1 + 0.25 * k, 1 + 0.25 * k, 1 - 0.97 * k) if here else (1.25 - 0.25 * k, 1.25 - 0.25 * k, 0.03 + 0.97 * k)
    return (1 - w * k, 1 - w * k, 1 + 0.3 * k) if here else (1 - w + w * k, 1 - w + w * k, 1.3 - 0.3 * k)


def _seam_mesh(name, EM2, style, H):
    """A seam mesh with its origin at the ground: bar, zigzag (a jagged crack of light), disc (a pool of light)."""
    if style == "zigzag":
        V = Vox((-0.6, -0.3, 0), (0.6, 0.3, H + 0.2), 0.0625)
        pts = [np.array([0.3 * (-1) ** i if 0 < i < 8 else 0.0, 0.0, H * i / 8]) for i in range(9)]
        for a, b in zip(pts, pts[1:]):
            V.cap(a, b, 0.2, ELIT)
    elif style == "disc":
        V = Vox((-1.3, -1.3, 0), (1.3, 1.3, 0.12), 0.0625)
        V.ell((0, 0, 0.0), (1.2, 1.2, 0.1), ELIT)
    else:
        V = Vox((-0.5, -0.5, 0), (0.5, 0.5, 1.0), 0.125)
        V.G[:] = ELIT
    return grid_mesh(name, V, {ELIT: EM2[ELIT]})


def fold_seam(code, R, EM2, dest):
    """The bold fold: as it folds, a glowing seam stands where it was, snaps shut, and opens at the new spot.
    Styles: bar (v2.0117 YE10), zigzag (a jagged crack), door (two bars part like a doorway), disc (a pool of light)."""
    H = 7.6
    st = EV["seam"]
    for nm, at, a, b, c in (("here", np.zeros(3), 14, 19, 24), ("there", dest, 25, 28, 35)):
        parts = [("", 0.0)] if st != "door" else [(" L", -1.0), (" R", 1.0)]
        lt = light(f"{code} fold light {nm}", tuple(R.X + at + np.array([0, -0.6, 0.6 if st == "disc" else 3.6])),
                   (1.0, 0.7, 0.12), 0.0, radius=0.3, cutoff=14)
        for suf, side in parts:
            ob = _seam_mesh(f"{code} fold seam {nm}{suf}", EM2, "bar" if st == "door" else st, H)
            for f in ALLF:
                if f < a or f > c:
                    w, h, op = 0.001, 0.001, 0.0
                elif f <= b:
                    k = ramp(f, a, b); w, h, op = 0.45 + 0.15 * k, H * (0.35 + 0.65 * k), k
                else:
                    k = ramp(f, b, c); w, h, op = 0.6 * (1 - k) + 0.001, H * (1 - 0.3 * k), 1 - k
                if st == "zigzag":
                    s = (w / 0.6, w / 0.6, max(h / H, 0.001))
                    loc = R.X + at
                elif st == "disc":
                    s = (max(op, 0.001),) * 2 + (1.0 if op > 0 else 0.001,)
                    loc = R.X + at + np.array([0, 0, 0.01])
                elif st == "door":
                    s = (0.22 if op > 0 else 0.001, 0.22 if op > 0 else 0.001, max(h, 0.001))
                    loc = R.X + at + np.array([side * 0.62 * math.sin(math.pi * min(op, 1.0)) * (1 if op > 0 else 0), 0, 0])
                else:
                    s = (w, w, max(h, 0.001))
                    loc = R.X + at
                keyed_obj(ob, f, loc=loc, scale=s)
        for f in ALLF:
            k = ramp(f, a, b) * (1 - ramp(f, b, c)) if a <= f <= c else 0.0
            lt.data.energy = 500.0 * k
            lt.data.keyframe_insert("energy", frame=f)


def ender_cracks(V, m, r):
    """Glowing marks over the black skin. cracks: sin bands (v2.0117), voronoi: a shattered-shell web of cracks,
    veins: lightning running down the limbs; embers: a sprinkle of glowing pixels."""
    mode = EV["crack_mode"]
    if EV["cracks"] and mode == "sin":
        x, y, z = V.axes()
        X_, Y_, Z_ = np.meshgrid(x, y, z, indexing="ij")
        q = np.abs(np.sin(X_ * 7.0 + Z_ * 4.1 + np.sin(Y_ * 5.0)) + np.sin(Y_ * 8.3 - Z_ * 5.7)) < EV["cracks"]
        V.G[m & q] = ELIT
    elif mode == "voronoi":
        idx = np.argwhere(m)
        if len(idx):
            Pt = idx * V.step + V.lo + V.step / 2
            lo_, hi_ = Pt.min(0) - 0.2, Pt.max(0) + 0.2
            rng_ = np.random.default_rng(int(V.G.size) + len(idx))
            n = max(4, int(np.prod(hi_ - lo_) / EV["cell"] ** 3))
            seeds = lo_ + rng_.random((n, 3)) * (hi_ - lo_)
            d = np.sort(np.linalg.norm(Pt[:, None] - seeds[None], axis=2), axis=1)
            hit = (d[:, 1] - d[:, 0]) < EV["crack_w"]
            V.G[tuple(idx[hit].T)] = ELIT
    elif mode == "veins":
        x, y, z = V.axes()
        X_, Y_, Z_ = np.meshgrid(x, y, z, indexing="ij")
        q = (np.abs(np.sin(X_ * 9.0 + 2.2 * np.sin(Z_ * 2.7 + Y_ * 3.0))) < 0.16) & (np.sin(Z_ * 4.3 + X_ * 5.0) > -0.1)
        V.G[m & q] = ELIT
    if EV["embers"]:
        V.G[m & (r > 1 - EV["embers"])] = ELIT


def ender_spell(code, R, EM2, ob, clip):
    """J: "make a fist ... and construct around the element ... like casting spells": the casting hand clenches into a
    fist, and a yellow hard-light cage of two spinning rings and sparks builds round the element it throws."""
    V = Vox((-2.0 * P, -2.0 * P, -1.8 * P), (2.0 * P, 2.0 * P, 1.8 * P), P / 2)
    V.obox((0, 0, 0), (1.8 * P, 1.8 * P, 1.6 * P), np.eye(3), EB1)
    for xi in (-1.2, -0.4, 0.4, 1.2):    # knuckles
        V.obox((xi * P, -1.9 * P, -1.0 * P), (0.35 * P, 0.25 * P, 0.4 * P), np.eye(3), EB2)
    fist = grid_mesh(f"{code} fist", V, EM2)
    fist.parent = R.J["haL"]["obj"]
    end = 27 if clip == "lava" else 32
    for f in ALLF:
        on = 6 <= f <= end
        keyed_obj(fist, f, loc=(0, 0, -1.3 * P), scale=ramp(f, 6, 9) + 0.001 if on else 0.001)
    rings = []
    for i, (r_, t_) in enumerate(((0.42, 0.04), (0.36, 0.035))):
        o = grid_mesh(f"{code} spell ring {i}", torus_vox(ELIT, r_, t_, 0.03125), {ELIT: EM2[ELIT]})
        o.parent = ob
        rings.append(o)
    sparks = Puffs(f"{code} spell sparks", 8, 0.06, EM2[ELIT], parent=ob)
    for f in ALLF:
        g = ramp(f, 8, 14)
        keyed_obj(rings[0], f, loc=(0, 0, 0), rot=(f * 0.32, 0.4, f * 0.18), scale=g + 0.001)
        keyed_obj(rings[1], f, loc=(0, 0, 0), rot=(1.2, f * 0.27, f * 0.35), scale=g + 0.001)
        if f % 2 == 1:
            for i in range(8):
                a = f * 0.4 + i * math.tau / 8
                sparks.key(i, f, (0.55 * math.cos(a), 0.55 * math.sin(a), 0.2 * math.sin(a * 2 + i)), g)


def slam_extra(code, EM2, hit_at, f_hit):
    """Fear-crack versions: the cracks flare as the lantern hits (pulse), glowing fissures run out over the ground."""
    if EV["pulse"]:
        p = EM2[ELIT].node_tree.nodes.get("Principled BSDF")
        es = p.inputs["Emission Strength"]
        for f, v in ((F0, 0.55), (f_hit - 1, 0.65), (f_hit, 1.5), (f_hit + 4, 1.4), (f_hit + 16, 0.55)):
            es.default_value = v
            es.keyframe_insert("default_value", frame=f)
    if EV["fissures"]:
        rng_ = np.random.default_rng(len(code) * 7 + 3)
        for i in range(7):
            ang = i / 7 * math.tau + rng_.uniform(-0.3, 0.3)
            L = rng_.uniform(1.8, 3.2)
            o = grid_mesh(f"{code} fissure {i}", cube_vox(ELIT, 1.0, 0.125), {ELIT: EM2[ELIT]})
            for f in ALLF:
                k = ramp(f, f_hit, f_hit + 6)
                fade = 1 - ramp(f, f_hit + 18, f_hit + 32)
                on = f >= f_hit and fade > 0
                ln = max(L * k, 0.001)
                c_ = np.asarray(hit_at) + np.array([math.cos(ang) * ln / 2, math.sin(ang) * ln / 2, 0.0])
                c_[2] = 0.015
                keyed_obj(o, f, loc=c_, rot=(0, 0, ang),
                          scale=(ln, 0.09 * fade + 0.001, 0.03) if on else (0.001,) * 3)


# =============================================================== the takes
BEAR_TAKES = [
    ("PB7", "Polar bear version 1: lean sloth, heavy rear-up", "rear",
     dict(girth=0.88, claw=1.25, rear=(13, 34, 46, 54), heavy=1.0, wrist=-0.15), dict(ua=1.85, fa=1.75, body_z=3.17), POLAR0,
     "the leanest bear: a narrower body and the longest sloth arms (3.6 blocks shoulder to wrist) with longer hooked claws, "
     "v2.0116's hand-picked fur kept as it was; the rear-up made slower and heavier: it crouches to load, rises over "
     "1.05 s, roars, and drops onto its front paws with a thud, a squash and snow dust"),
    ("PB8", "Polar bear version 2: blizzard mane, walk", "walk",
     dict(shag=1.8, mane=1.0, face=1.3), dict(), ((0.84, 0.87, 0.9), (0.74, 0.79, 0.84), (0.62, 0.68, 0.75), (0.4, 0.45, 0.52), (0.97, 0.98, 1.0)),
     "a shaggy arctic coat: a thick mane over the neck and shoulders, nearly twice the guard-hair fringe, and icy fur "
     "picked in five cool colours (snow, frost, glacier, blue shadow, bright); walking 4 blocks in 3 s, paws planted (IK). "
     "Rev 2 (J: \"The polar besrs face doesnt need to be as skinny\"): a fuller face, 30% wider head, muzzle and jaw"),
    ("PB9", "Polar bear version 3: old scarred boar, swipe", "swipe",
     dict(girth=1.06, hump=1.0, claw=1.8, claw_in=0.5, claw_r=1.45, scars=True), dict(), ((0.82, 0.76, 0.6), (0.74, 0.66, 0.48), (0.62, 0.52, 0.36), (0.42, 0.38, 0.32), (0.9, 0.87, 0.76)),
     "an old male: a heavy shoulder hump, yellowed old fur, three raked claw scars across the right shoulder; the sloth "
     "swipe: rises on three legs and rakes you on tick 27 (red flash, knockback). Rev 2 (J: \"arms turned inward and it "
     "to swipe you with big sharp sloth like claws/anteater\"): the front paws turn in, with three huge thick hooked "
     "claws (1.45 blocks) curving in toward the body like an anteater's"),
]
ENDER_TAKES = [
    ("YE10", "Yellow Lantern Enderman version 1: bold fold teleport", "yellow", "teleport_fold",
     dict(bold_fold=True, fold_w=0.85), dict(),
     "the v2.0116 enderman with the fold teleport made readable from far away: it glitches, folds into a thick glowing "
     "yellow seam as tall as itself (lit, so it shows across a cave), the seam snaps shut, opens 3 blocks away and "
     "unfolds it"),
    ("YE11", "Yellow Lantern Enderman version 2: fear-cracked shell, lantern slam", "yellow", "slam",
     dict(cracks=0.035, skin=((0.012, 0.012, 0.016), (0.03, 0.028, 0.036), (0.02, 0.018, 0.026))), dict(),
     "a blacker skin split by thin glowing yellow fear cracks (black core first, yellow only in the cracks, like the "
     "Warren's fear spiders); slams its lantern into the ground on tick 22, a shockwave ring runs out"),
    ("YE12", "Yellow Lantern Enderman version 3: gaunt, lava throw", "yellow", "lava",
     dict(limb=0.72, eye=(1.0, 0.86, 0.4), skin=((0.035, 0.03, 0.045), (0.075, 0.06, 0.09), (0.05, 0.035, 0.07)),
          spell=True, hold=0.75, cam_up=2.2, cam_d=1.4), dict(),
     "stick-thin arms and legs (72% as thick), a violet-grey skin and pale gold eyes; pulls a lava block out of its "
     "orbit and lobs it into a spreading lava pool. Rev 2 (J: \"make a fist ... and construct around the element ... like "
     "casting spells\"): the casting hand clenches into a fist (knuckles out) and a yellow hard-light cage of two "
     "spinning rings and sparks builds round the lava block, held above the fist and thrown with it"),
    ("OE4", "Orange Lantern Enderman version 1: standing, hugging the lantern greedily", "orange", "pray_greedy",
     dict(), dict(lan=(0, -5.6 * P, 7.4 * P), hand_x=0.4, hand_y=-2.4),
     "the charging pause standing up. Rev 2 (J: \"i want arms hugging it to the chest greedily\"): hunched, the Orange "
     "Lantern crushed against its chest, both arms wrapped round the front of it, head down over it, eyes closing, "
     "then glancing side to side as if someone might take it"),
    ("OE5", "Orange Lantern Enderman version 2: both knees, bowed over the lantern", "orange", "pray_kneel2",
     dict(embers=0.025), dict(bow=0.95, ),
     "down on both knees, the lantern standing on the ground in front, arms round it, bowed low over it, eyes shut, "
     "whispering; orange ember pixels in its skin"),
    ("OE6", "Orange Lantern Enderman version 3: rocking, lantern to the forehead", "orange", "pray_rock",
     dict(embers=0.025, limb=0.8), dict(lan=(0, -10.6 * P, 21.0 * P)),
     "one knee down, rocking slowly forward and back with the lantern pressed to its forehead in both hands, eyes "
     "shut, whispering; thinner limbs and ember pixels"),
]
SHARK_TAKES = [
    ("SK8", "Shark version 1: scarred great white, bite", "bite", dict(kind="white", scars=True),
     "the kept 10-block great white with old pale bite scars raked over its back and flanks; jaws open, it lunges and "
     "the jaws close on the fish exactly at tick 24, then a head shake"),
    ("SK9", "Shark version 2: hammerhead hunting", "sweep", dict(kind="hammer"),
     "a 10-block hammerhead cruising after a fleeing fish, swinging its wide head side to side as it hunts (eyes and "
     "fin edges in blue hard light)"),
    ("SK10", "Shark version 3: thresher tail slap", "tailslap", dict(kind="thresher"),
     "a 10-block thresher swims in, brakes, pitches nose-down and whips its long tail over its head: the tail tip "
     "strikes the fish on tick 30, the fish flips over stunned and sinks in a burst of bubbles"),
]
for i, (c, n, clip, bv, bear, pal, facts) in enumerate(BEAR_TAKES):
    BV = dict(BV0, **bv)
    BEAR.clear(); BEAR.update(BEAR0, **bear)
    BEARM = bear_mats(c, pal)
    X_ = np.array([i * 90.0, 0.0, 0.0])
    bear_take(c, n, X_, clip, facts, 70 + i)
    if BV["heavy"]:
        bear_dust(c, X_, BV["rear"][3])
BV = dict(BV0); BEAR.clear(); BEAR.update(BEAR0); BEARM = BEARM0
for i, (c, n, corps, clip, ev, ov, facts) in enumerate(ENDER_TAKES):
    EV = dict(EV0, **ev)
    if corps == "orange":
        EV.update(cam_up=1.9, cam_d=1.3)
    OV = {**OV0, **ov}
    ender_take(c, n, np.array([i * 90.0, 250.0, 0.0]), corps, clip, facts, 90 + i)
EV = dict(EV0)
for i, (c, n, clip, skv, facts) in enumerate(SHARK_TAKES):
    SKV = {**dict(kind="white", scars=False), **skv}
    shark_take(c, n, np.array([i * 120.0, 500.0, 0.0]), clip, facts, 110 + i)

scene.camera = bpy.data.objects[TAKES[0][2]]
scene["creature_takes"] = repr(TAKES)
scene["v2_0117_checks"] = repr(CHECKS)
scene.frame_set(F0)
bad = [c for c, r in CHECKS.items() if not c.startswith("_") and r["fails"]]
print(f"[{PASS}] built {len(TAKES)} takes, {len(scene.objects)} objects; checks {'all OK' if not bad else 'FAIL in ' + ', '.join(bad)}")
print(f"[{PASS}] tail slap tip-to-fish: {CHECKS.get('_slap')}")
