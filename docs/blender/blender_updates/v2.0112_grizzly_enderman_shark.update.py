# Pass v2.0112: the grizzly, the Yellow Lantern enderman and the blue great white, refined (Trials; PC Blender chat,
#   2026-10-19).
# Why: J, after round 4 of the Titan bosses (tools/trials/titan_killer2_blend.py, trials\titan_killer2.blend): "I want
#   grizzly refined, shark and the other i named as well". The Titan trial is shelved ("forget the titan,"), so these
#   are standalone creature designs, not placed in a trial.
# What changed from round 4: real shapes instead of stacked boxes (voxel bodies at 1/4 block, 1/5 for the enderman),
#   real detail (dished bear face, cheek ruffs, ears, toes and curved claws, grizzled fur tips; the enderman's jointed
#   limbs, long fingers, stand-off hard-light armour; the shark's torpedo body, countershading, gill slits, toothed
#   jaws and a lunate tail) and poses that read. Every limb pair is checked numerically: legs and fins never cross each
#   other or the floor, and planted feet touch it (report in scene["v2_0112_checks"]).
# Takes (each its own camera, all turn once per 120 frames, frame 118 is the hero view):
#   G2a Grizzly swipe, G2b Grizzly charge, G2c Grizzly rearing roar (three coats: brown, silvertip, dark)
#   E2a Lantern Enderman carrying a fear block (plates), E2b scream lunge (shards, teleport afterimages),
#   E2c kneeling to charge at its lantern (lantern-cage chest)
#   S2a Great White breach, S2b banking turn with the fin cutting the water (hard-light fins), S2c lunge onto the ledge
# Glow at or under emission 1.5 (yellow and blue wash to white above that).
# Builds the whole scene from nothing (globals bpy, np, FOLDER); the renderer saves it as trials/grizzly_enderman_shark.blend.
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

PASS = "v2.0112"
FRAMES = (1, 120)
GAP = 160.0
PX = 1.0 / 16.0

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene
scene.name = "Grizzly Enderman Shark"
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


# =============================================================== the grizzly
FUR, DARK, TIP, SNOUT, NOSE, CLAW, MOUTH, TOOTH, EYE, TONGUE, EARIN = range(1, 12)
COATS = {
    "brown": dict(fur=((0.12, 0.07, 0.033), (0.23, 0.135, 0.065)), dark=((0.055, 0.032, 0.016), (0.11, 0.065, 0.032)),
                  tip=((0.36, 0.25, 0.14), (0.54, 0.41, 0.25)), snout=((0.3, 0.21, 0.13), (0.45, 0.34, 0.22))),
    "silvertip": dict(fur=((0.085, 0.055, 0.035), (0.16, 0.105, 0.065)), dark=((0.04, 0.026, 0.016), (0.085, 0.055, 0.032)),
                      tip=((0.42, 0.39, 0.35), (0.66, 0.62, 0.56)), snout=((0.28, 0.21, 0.15), (0.42, 0.34, 0.25))),
    "dark": dict(fur=((0.055, 0.036, 0.022), (0.11, 0.07, 0.042)), dark=((0.03, 0.02, 0.013), (0.06, 0.04, 0.025)),
                 tip=((0.26, 0.17, 0.09), (0.4, 0.28, 0.16)), snout=((0.22, 0.15, 0.09), (0.34, 0.25, 0.16))),
}


def bear_mats(coat):
    c = COATS[coat]
    return {FUR: pmat(f"{coat} fur", *c["fur"], 0.95), DARK: pmat(f"{coat} legs", *c["dark"], 0.95),
            TIP: pmat(f"{coat} fur tips", *c["tip"], 0.95), SNOUT: pmat(f"{coat} muzzle", *c["snout"], 0.85),
            NOSE: mat("bear nose", (0.015, 0.012, 0.012), 0.3), CLAW: pmat("bear claws", (0.55, 0.52, 0.45), (0.8, 0.77, 0.68), 0.4),
            MOUTH: pmat("bear mouth", (0.18, 0.03, 0.035), (0.3, 0.06, 0.06), 0.5), TOOTH: mat("bear teeth", (0.9, 0.87, 0.78), 0.4),
            EYE: mat("bear eye", (0.01, 0.005, 0.004), 0.12), TONGUE: pmat("bear tongue", (0.42, 0.12, 0.13), (0.55, 0.2, 0.2), 0.45),
            EARIN: mat("ear inside", (0.04, 0.025, 0.02), 0.8)}


def bear_head(V, c, fwd, k, gape):
    """Dished grizzly face: cranium, cheek ruffs, brow, round ears, tan muzzle, black nose, open jaw with canines."""
    fwd = nrm(fwd)
    x = nrm(np.cross(fwd, (0, 0, 1))); z = np.cross(x, fwd)
    R = np.column_stack([x, fwd, z])
    c = np.asarray(c, float)

    def W(p):
        return c + R @ (np.asarray(p, float) * k)
    V.ell(W((0, 0, 0.3)), np.array((2.5, 2.7, 2.3)) * k, FUR, R)
    for sx in (-1, 1):
        V.ell(W((sx * 1.9, -0.6, -0.6)), np.array((1.4, 1.8, 1.6)) * k, TIP, R)                  # cheek ruffs
        V.ell(W((sx * 1.95, -0.9, 2.35)), np.array((0.85, 0.55, 0.85)) * k, DARK, R)             # ears
        V.ell(W((sx * 1.95, -0.5, 2.4)), np.array((0.45, 0.25, 0.45)) * k, EARIN, R)
    V.ell(W((0, 1.3, 1.35)), np.array((2.0, 1.2, 0.9)) * k, FUR, R)                              # brow
    V.ell(W((0, 3.1, -0.2)), np.array((1.45, 2.0, 1.05)) * k, SNOUT, R)                          # muzzle
    V.ell(W((0, 4.9, 0.25)), np.array((0.75, 0.45, 0.55)) * k, NOSE, R)
    for sx in (-1, 1):
        V.ell(W((sx * 1.2, 2.05, 0.85)), np.array((0.33, 0.3, 0.33)) * k, EYE, R)
    # lower jaw on a hinge
    g = math.radians(gape)
    Rj = R @ Rx(-g)
    h = np.array((0, 0.6, -1.2))

    def J(p):
        return c + (R @ h + Rj @ (np.asarray(p, float))) * k
    V.ell(W((0, 2.3, -1.25)) - R @ np.array((0, 0, 0.6 * math.sin(g))) * k,
          np.array((1.0, 1.9, 0.35 + 0.9 * math.sin(g))) * k, MOUTH, R @ Rx(-g / 2), only_empty=True)
    V.ell(J((0, 2.0, -0.3)), np.array((1.25, 2.0, 0.6)) * k, SNOUT, Rj)
    V.ell(J((0, 1.9, 0.25)), np.array((0.8, 1.5, 0.28)) * k, TONGUE, Rj)
    for sx in (-1, 1):
        V.cap(W((sx * 0.8, 4.0, -1.05)), W((sx * 0.8, 4.1, -1.85)), 0.2 * k, TOOTH, 0.08 * k)  # upper canines
        V.cap(J((sx * 0.75, 3.55, 0.1)), J((sx * 0.75, 3.65, 0.85)), 0.19 * k, TOOTH, 0.07 * k)  # lower canines
    for xi in (-0.4, 0.0, 0.4):
        V.cap(W((xi, 4.55, -1.0)), W((xi, 4.6, -1.45)), 0.13 * k, TOOTH)
    V.ell(W((0, -0.4, -2.0)), np.array((2.2, 2.0, 1.4)) * k, TIP, R, only_empty=True)             # chin ruff
    return (c + R @ np.array((0, 1.0, 0)) * k, 2.7 * k)


def bear_leg(V, name, joints, radii, paw, nclaw, Lc, rc, limbs, contacts):
    segs = []
    for i in range(len(joints) - 1):
        lab = FUR if i == 0 else DARK
        V.cap(joints[i], joints[i + 1], radii[i], lab, radii[i + 1])
        segs.append((np.asarray(joints[i], float), np.asarray(joints[i + 1], float), max(radii[i], radii[i + 1])))
    c, f, u, rad = paw
    c = np.asarray(c, float)
    R = frame_fu(f, u); side, fv, uv = R[:, 0], R[:, 1], R[:, 2]
    V.ell(c, rad, DARK, R)
    segs.append((c - fv * rad[1] * 0.6, c + fv * rad[1] * 0.6, rad[2]))
    for i in range(nclaw):
        o = (i - (nclaw - 1) / 2) * rad[0] * 0.38
        toe = c + fv * rad[1] * 0.78 + side * o + uv * rad[2] * 0.05
        V.ell(toe, (0.38, 0.42, 0.4), DARK, R)
        base = toe + fv * 0.3
        mid = base + fv * Lc * 0.6
        tip = mid + fv * Lc * 0.4 - uv * Lc * 0.45
        for p in (mid, tip):          # claws never dig into the floor: they lie on it
            p[2] = max(p[2], rc)
        V.cap(base, mid, rc, CLAW, rc * 0.9); V.cap(mid, tip, rc * 0.9, CLAW, rc * 0.55)
        segs.append((base, tip, rc * 0.8))
    limbs[name] = segs
    return c[2] - rad[2]


def bear_fur(V, rng):
    G = V.G
    z = V.axes()[2][None, None, :]
    surf = surface(G)
    zn = np.clip((z - 3.0) / 12.0, 0, 1)
    # grizzled tips come in soft patches (coarse noise, 2-block cells), more of them up on the back and hump
    cs = tuple(s // 8 + 2 for s in G.shape)
    n = rng.normal(size=cs)
    for _ in range(2):
        n = (n + np.roll(n, 1, 0) + np.roll(n, -1, 0) + np.roll(n, 1, 1) + np.roll(n, -1, 1)) / 5
    n = np.repeat(np.repeat(np.repeat(n, 8, 0), 8, 1), 8, 2)[:G.shape[0], :G.shape[1], :G.shape[2]]
    n /= n.std() + 1e-9
    rnd = rng.random(G.shape)
    G[surf & (G == FUR) & (n > 0.9 - 1.6 * zn) & (rnd < 0.75)] = TIP                              # grizzled tips
    furry = (G == FUR) | (G == TIP)
    up_free = np.zeros(G.shape, bool); up_free[:, :, :-1] = G[:, :, 1:] == 0
    tuft = surf & furry & up_free & (rng.random(G.shape) < 0.07) & (z > 3.0)
    G[:, :, 1:][tuft[:, :, :-1]] = TIP                                                            # shaggy tufts
    dn_free = np.zeros(G.shape, bool); dn_free[:, :, 1:] = G[:, :, :-1] == 0
    fr = surface(G) & (G == FUR) & dn_free & (rng.random(G.shape) < 0.35) & (z > 3.2)
    G[:, :, :-1][fr[:, :, 1:]] = FUR                                                              # belly fringe


def mirror(p, sx):
    return (p[0] * sx, p[1], p[2])


def grizzly(code, pose, coat, X, facts, name):
    rng = np.random.default_rng(len(code) * 7 + ord(code[-1]))
    V = Vox((-11, -17.5, 0), (11, 17, 23.5), 0.25)
    limbs, contacts = {}, []
    if pose == "swipe":
        torso = [((0, -3.8, 7.6), (4.1, 4.6, 3.6)), ((0, 1.5, 7.4), (3.8, 5.4, 3.3)), ((0, 6.2, 7.9), (3.7, 3.6, 3.4)),
                 ((0, -3.0, 10.1), (3.0, 3.4, 2.1)), ((0, -7.8, 7.8), (2.9, 3.0, 2.8)), ((0, -7.0, 5.6), (2.4, 2.0, 1.8))]
        tail = (0, 9.6, 8.3)
        head = ((0, -11.2, 7.0), (0, -0.95, -0.3), 1.15, 32)
        legs = {
            "front R (swiping)": ([(2.9, -5.0, 7.2), (4.6, -7.8, 6.6), (5.6, -10.2, 5.0)], [1.6, 1.35, 1.15],
                                  ((5.9, -11.0, 4.4), (0.2, -0.75, -0.6), (0.1, -0.6, 0.8), (1.25, 1.5, 0.6)), False),
            "front L": ([(-2.9, -5.0, 7.0), (-3.2, -5.6, 4.2), (-3.3, -6.0, 1.4)], [1.6, 1.35, 1.15],
                        ((-3.3, -6.9, 0.55), (0, -1, 0), (0, 0, 1), (1.3, 1.7, 0.55)), True),
        }
        for sx, nm in ((1, "hind R"), (-1, "hind L")):
            legs[nm] = ([mirror((3.0, 6.5, 7.2), sx), mirror((3.3, 4.8, 4.2), sx), mirror((3.35, 7.4, 1.5), sx)],
                        [1.9, 1.4, 1.0], (mirror((3.35, 6.0, 0.5), sx), (0, -1, 0), (0, 0, 1), (1.2, 2.1, 0.5)), True)
    elif pose == "charge":
        torso = [((0, -4.4, 7.7), (4.0, 4.8, 3.5)), ((0, 1.0, 7.7), (3.6, 5.6, 3.1)), ((0, 6.0, 8.5), (3.7, 3.6, 3.4)),
                 ((0, -3.6, 10.0), (3.0, 3.4, 2.0)), ((0, -8.4, 8.4), (2.8, 3.0, 2.7)), ((0, -7.6, 6.3), (2.3, 2.0, 1.7))]
        tail = (0, 9.4, 9.3)
        head = ((0, -11.8, 8.6), (0, -1, 0.05), 1.15, 24)
        legs = {
            "front R (landing)": ([(2.8, -5.4, 7.2), (3.1, -8.4, 5.8), (3.2, -10.6, 3.6)], [1.6, 1.35, 1.15],
                                  ((3.2, -11.4, 3.0), (0, -0.6, -0.8), (0, -0.8, 0.6), (1.25, 1.6, 0.55)), False),
            "front L": ([(-2.8, -5.6, 7.2), (-3.0, -8.4, 4.6), (-3.1, -10.0, 1.4)], [1.6, 1.35, 1.15],
                        ((-3.1, -10.9, 0.55), (0, -1, 0), (0, 0, 1), (1.3, 1.7, 0.55)), True),
            "hind R": ([(3.0, 6.4, 7.8), (3.3, 4.6, 4.8), (3.4, 7.0, 1.5)], [1.9, 1.4, 1.0],
                       ((3.4, 5.6, 0.5), (0, -1, 0), (0, 0, 1), (1.2, 2.1, 0.5)), True),
            "hind L (pushing off)": ([(-3.0, 6.4, 7.8), (-3.2, 8.6, 5.6), (-3.3, 11.6, 4.0)], [1.9, 1.4, 1.0],
                                     ((-3.3, 12.4, 2.6), (0, 0.45, -0.9), (0, -0.9, -0.45), (1.2, 2.0, 0.5)), False),
        }
    else:   # rear: up on the hind legs, roaring, arms spread
        torso = [((0, 1.9, 6.9), (3.9, 3.6, 3.8)), ((0, 0.7, 10.0), (3.7, 3.4, 4.0)), ((0, -0.4, 13.3), (4.1, 3.4, 3.5)),
                 ((0, 2.0, 14.6), (3.0, 2.2, 2.5)), ((0, -1.4, 15.8), (2.8, 2.6, 2.6)), ((0, -2.6, 14.2), (2.3, 1.6, 1.8))]
        tail = (0, 4.9, 5.0)
        head = ((0, -3.0, 17.9), (0, -0.7, 0.7), 1.15, 46)
        legs = {}
        for sx, side in ((1, "R"), (-1, "L")):
            legs[f"hind {side}"] = ([mirror((3.0, 1.6, 6.6), sx), mirror((3.4, -0.3, 3.7), sx), mirror((3.4, 1.8, 1.55), sx)],
                                    [2.0, 1.45, 1.05], (mirror((3.4, 0.3, 0.5), sx), (0, -1, 0), (0, 0, 1), (1.3, 2.3, 0.5)), True)
            legs[f"arm {side}"] = ([mirror((3.5, -0.6, 14.0), sx), mirror((6.4, -3.0, 15.0), sx), mirror((7.6, -5.0, 16.8), sx)],
                                   [1.6, 1.35, 1.15],
                                   (mirror((7.8, -5.9, 17.6), sx), (0, -0.85, -0.5), (0, -0.5, 0.85), (1.25, 1.5, 0.6)), False)
    for c, r in torso:
        V.ell(c, r, FUR)
    V.ell(tail, (0.75, 0.8, 0.65), FUR)
    hc, hr = bear_head(V, *head)
    for nm, (joints, radii, paw, planted) in legs.items():
        front = nm.startswith("front") or nm.startswith("arm")
        lowz = bear_leg(V, nm, joints, radii, paw, 5, 2.1 if front else 1.3, 0.21, limbs, contacts)
        if planted:
            contacts.append((nm + " paw", lowz))
    bear_fur(V, rng)
    contacts = [(nm, z) for nm, z in contacts]
    check(code, limbs, solids=[("head", hc, hr)], contacts=contacts)
    ob = grid_mesh(f"{code} grizzly", V, bear_mats(coat))
    gd = ground_disc(f"{code} ground", 17, seed=len(code))
    pl = player(f"{code} player", (-8.5, -9.5, 0), face=(0, -4))
    tall = pose == "rear"
    cam = stage(code, X, [ob, gd, pl], (0, -1.5, 9.5 if tall else 6.5), 46 if tall else 44, elev=0.3)
    add_take(code, name, cam, facts)


# =============================================================== the Yellow Lantern enderman
BODY, PLATE, EDGE, EYEG, CORE, GOLD, STATIC, BGLASS, MOUTHG, RINGY = range(1, 11)
EM = {BODY: pmat("ender black", (0.012, 0.01, 0.016), (0.045, 0.035, 0.055), 0.55, cell=0.2),
      PLATE: mat("fear plate", (0.3, 0.17, 0.0), 0.25, emit=(1.0, 0.6, 0.02), es=0.3, alpha=0.72),
      EDGE: mat("fear edge", (1.0, 0.68, 0.08), 0.3, emit=(1.0, 0.64, 0.04), es=1.0),
      EYEG: mat("fear eyes", (1.0, 0.72, 0.1), 0.2, emit=(1.0, 0.7, 0.06), es=1.5),
      CORE: mat("lantern core", (1.0, 0.7, 0.1), 0.2, emit=(1.0, 0.66, 0.05), es=1.4),
      GOLD: pmat("lantern gold", (0.5, 0.33, 0.06), (0.95, 0.7, 0.25), 0.28, metal=1.0, cell=0.2),
      STATIC: mat("fear static", (1.0, 0.62, 0.05), 0.5, emit=(1.0, 0.6, 0.04), es=1.0),
      BGLASS: mat("fear glass", (0.45, 0.28, 0.02), 0.1, emit=(1.0, 0.62, 0.03), es=0.35, alpha=0.5),
      MOUTHG: mat("mouth glow", (1.0, 0.55, 0.05), 0.4, emit=(1.0, 0.5, 0.03), es=1.3),
      RINGY: mat("yellow ring", (1.0, 0.7, 0.05), 0.3, emit=(1.0, 0.68, 0.04), es=1.4)}
GHOST = mat("teleport afterimage", (0.03, 0.02, 0.01), 0.5, emit=(1.0, 0.55, 0.03), es=0.18, alpha=0.32)
LW = 0.6   # limb width (blocks)


def limb(V, a, b, w=LW, ref=(0, -1, 0), lab=BODY):
    a, b = np.asarray(a, float), np.asarray(b, float)
    R = frame_axis(b - a, ref)
    V.obox((a + b) / 2, (w / 2, w / 2, np.linalg.norm(b - a) / 2 + w * 0.3), R, lab)
    return R


def fingers(V, wrist, d, side, n=3, L=1.1, spread=0.22, curl=0.0, ring=False):
    d = nrm(d); side = nrm(side); up = np.cross(side, d)
    out = []
    for i in range(n):
        o = (i - (n - 1) / 2) * spread
        a = np.asarray(wrist, float) + side * o + d * 0.15
        m = a + d * L * 0.55 + side * o * 0.6
        t = m + nrm(d - up * curl) * L * 0.45 + side * o * 0.3
        limb(V, a, m, 0.24, up); limb(V, m, t, 0.2, up)
        V.obox(t, (0.11, 0.11, 0.12), frame_axis(t - m, up), EDGE)        # hard-light claw tips
        out.append((a, t, 0.13))
        if ring and i == n // 2:
            V.obox(a + (m - a) * 0.35, (0.2, 0.2, 0.07), frame_axis(m - a, up), RINGY)
    return out


def halo(V, c, R, r=1.45, spikes=8):
    c = np.asarray(c, float); Rt = np.asarray(R, float)

    def fn(P):
        d = np.einsum("ji,j...->i...", Rt, P - c[:, None, None, None])
        rr = np.hypot(d[0], d[1])
        return (np.abs(rr - r) < 0.17) & (np.abs(d[2]) < 0.12)
    V.region(c, r + 0.5, fn, GOLD)
    for k in range(spikes):
        a = k / spikes * math.tau
        p = c + Rt @ np.array((math.cos(a) * r, math.sin(a) * r, 0.0))
        tip = p + Rt @ np.array((0, 0, 0.55 if k % 2 else 0.85))
        V.cap(p, tip, 0.12, GOLD, 0.06)
        V.ell(tip, (0.12, 0.12, 0.12), EDGE)


def fear_block(V, c, half, R, core=True):
    V.obox(c, (half,) * 3, R, BGLASS, rim=half * 0.18, rim_lab=EDGE, thin=-1)
    if core:
        V.obox(c, (half * 0.5,) * 3, R, BODY)
        V.obox(c, (half * 0.38, half * 0.56, half * 0.09), R, CORE, only_full=True)   # the fear eye slit


def enderman_head(V, c, R, open_mouth=0.0, style="plate"):
    c = np.asarray(c, float); R = np.asarray(R, float)

    def W(p):
        return c + R @ np.asarray(p, float)
    if open_mouth > 0:
        V.obox(W((0, 0, 0.3)), (1.2, 1.2, 0.9), R, BODY)
        V.obox(W((0, 0, -0.85 - open_mouth)), (1.15, 1.15, 0.35), R, BODY)
        V.obox(W((0, -0.05, -0.55 - open_mouth / 2)), (1.0, 1.0, 0.1 + open_mouth / 2), R, MOUTHG)
        for xi in (-0.75, -0.25, 0.25, 0.75):
            V.obox(W((xi, -1.05, -0.62)), (0.08, 0.08, 0.16), R, EDGE)
    else:
        V.obox(W((0, 0, 0)), (1.2, 1.2, 1.2), R, BODY)
        V.obox(W((0, -1.15, -0.55)), (0.75, 0.1, 0.06), R, MOUTHG, only_full=True)
    for sx in (-1, 1):
        V.obox(W((sx * 0.55, -1.12, 0.32)), (0.42, 0.12, 0.13), R, EYEG, only_full=True)
    if style == "shard":
        for k, a in enumerate((-0.9, -0.3, 0.3, 0.9)):
            V.octa(W((a, 0.1, 1.85 + (0.25 if abs(a) < 0.5 else 0))), (0.22, 0.22, 0.6), R @ Ry(a * 0.4), PLATE)
    else:
        halo(V, W((0, 0.1, 2.0)), R)


def armour(V, style, T, Rt, sh, legs, arms):
    """Hard-light armour standing off the body (the 838 stand-off rule): plates, shards, or a lantern cage."""
    def TW(p):
        return T + Rt @ np.asarray(p, float)
    if style == "plate":
        for sx in (-1, 1):
            for k in range(3):
                Rp = Rt @ Ry(sx * math.radians(-22 - k * 8))
                V.obox(TW((sx * (1.55 + k * 0.12), 0, 1.95 + 0.55 - k * 0.42)), (0.95 - k * 0.1, 0.85 - k * 0.08, 0.08), Rp,
                       PLATE, rim=0.13, rim_lab=EDGE, thin=2)
        V.obox(TW((0, -0.98, 0.15)), (1.05, 0.08, 1.35), Rt, PLATE, rim=0.13, rim_lab=EDGE)
        V.obox(TW((0, -0.98, 0.0)), (0.55, 0.2, 0.7), Rt, 0, only_full=True)      # window onto the lantern core
        for k in range(4):
            V.obox(TW((0, 0.98, -1.2 + k * 0.85)), (0.55 - k * 0.05, 0.08, 0.3), Rt @ Rx(math.radians(-18)), PLATE,
                   rim=0.1, rim_lab=EDGE)
    elif style == "shard":
        for sx in (-1, 1):
            for k, (dx, dz, tilt) in enumerate(((0.2, 0.9, 0.2), (0.7, 0.5, 0.7), (0.0, 0.5, -0.3))):
                V.octa(TW((sx * (1.55 + dx), 0.05 * k, 1.9 + dz)), (0.28, 0.28, 0.85), Rt @ Ry(sx * tilt), PLATE)
                V.octa(TW((sx * (1.55 + dx), 0.05 * k, 1.9 + dz)), (0.12, 0.12, 0.5), Rt @ Ry(sx * tilt), EDGE)
        for k in range(5):
            V.octa(TW((0, 0.95, -1.4 + k * 0.75)), (0.18, 0.55, 0.3), Rt @ Rx(math.radians(25)), PLATE)
        V.octa(TW((0, -0.95, 0.0)), (0.9, 0.12, 1.2), Rt, PLATE)
        V.octa(TW((0, -0.95, 0.0)), (0.5, 0.25, 0.7), Rt, 0, only_full=True)
    else:   # cage: gold bars round a glass lantern set into the chest
        for sx in (-1, 1):
            V.ell(TW((sx * 1.55, 0, 2.15)), (0.95, 0.85, 0.45), PLATE, Rt)
        cagec = TW((0, -0.95, 0.0))
        for xi in (-0.85, -0.3, 0.3, 0.85):
            V.obox(cagec + Rt @ np.array((xi, -0.12, 0)), (0.07, 0.07, 1.3), Rt, GOLD)
        for zi in (-1.3, 0.0, 1.3):
            V.obox(cagec + Rt @ np.array((0, -0.12, zi)), (0.95, 0.09, 0.08), Rt, GOLD)
    # lantern core in the chest (every style): gold frame, glowing heart
    V.obox(TW((0, -0.55, 0.0)), (0.45, 0.15, 0.6), Rt, GOLD)
    V.obox(TW((0, -0.6, 0.0)), (0.3, 0.15, 0.45), Rt, CORE)
    # greaves and bracers (plates, or shards along the back of the limb)
    for (a, b, R) in legs:
        mid = (np.asarray(a) + np.asarray(b)) / 2
        if style == "shard":
            V.octa(np.asarray(a) + R[:, 1] * 0.55, (0.2, 0.55, 0.2), R, PLATE)            # knee spike
        else:
            V.obox(mid + R[:, 1] * 0.58, (0.4, 0.08, np.linalg.norm(np.asarray(b) - a) * 0.36), R, PLATE)
            V.obox(np.asarray(a) + R[:, 1] * 0.58, (0.32, 0.1, 0.1), R, EDGE)                       # a lit knee cap
    for (a, b, R) in arms:
        mid = (np.asarray(a) + np.asarray(b)) / 2
        if style == "shard":
            for t in (0.3, 0.6):
                p = np.asarray(a) + (np.asarray(b) - a) * t
                V.octa(p - R[:, 1] * 0.5, (0.16, 0.45, 0.3), R, PLATE)
        else:
            V.obox(mid - R[:, 1] * 0.0 + R[:, 0] * 0.0 + R[:, 1] * -0.55, (0.38, 0.08, np.linalg.norm(np.asarray(b) - a) * 0.3),
                   R, PLATE)


def static_specks(V, rng, centre, rad, n):
    for _ in range(n):
        p = np.asarray(centre, float) + rng.uniform(-1, 1, 3) * rad
        if p[2] < 0.6:
            continue
        V.obox(p, (0.09, 0.09, 0.09), np.eye(3), STATIC, only_empty=True)


def lantern(V, c, h=2.0, w=0.75):
    """A small Yellow Lantern of our own: gold base and cap, four posts, fear glass round a glowing heart."""
    c = np.asarray(c, float); I3 = np.eye(3)
    V.obox(c + (0, 0, 0.15), (w + 0.15, w + 0.15, 0.15), I3, GOLD)
    V.obox(c + (0, 0, h / 2), (w - 0.05, w - 0.05, h / 2 - 0.3), I3, BGLASS)
    V.ell(c + (0, 0, h / 2), (0.38, 0.38, 0.5), CORE)
    for sx in (-1, 1):
        for sy in (-1, 1):
            V.obox(c + (sx * w, sy * w, h / 2), (0.1, 0.1, h / 2 - 0.1), I3, GOLD)
    V.obox(c + (0, 0, h - 0.15), (w + 0.1, w + 0.1, 0.15), I3, GOLD)
    V.obox(c + (0, 0, h + 0.05), (0.32, 0.32, 0.08), I3, EDGE)          # the charging port


def lantern_enderman(code, pose, style, X, facts, name):
    rng = np.random.default_rng(50 + ord(code[-1]))
    V = Vox((-7.5, -9, 0), (7.5, 9.5, 17.5), 0.2)
    limbs, contacts, legs_r, arms_r, extra = {}, {}, [], [], []
    I3 = np.eye(3)
    if pose == "carry":
        legdef = {"leg R": [(0.8, 0, 8.0), (0.85, -0.2, 4.2), (0.85, 0, 0.55)],
                  "leg L": [(-0.8, 0, 8.0), (-0.85, -0.2, 4.2), (-0.85, 0, 0.55)]}
        feet = {"leg R": ((0.85, -0.3, 0.25), I3), "leg L": ((-0.85, -0.3, 0.25), I3)}
        T, Rt = np.array((0, 0, 9.9)), I3
        hc, Rh, mouth = np.array((0, -0.1, 13.0)), Ry(math.radians(8)), 0.0
        armdef = {"arm R": [(1.55, 0, 11.3), (1.95, -1.0, 7.4), (1.35, -3.5, 9.5)],
                  "arm L": [(-1.55, 0, 11.3), (-1.95, -1.0, 7.4), (-1.35, -3.5, 9.5)]}
    elif pose == "lunge":
        legdef = {"leg L (front)": [(-0.8, 0.3, 6.0), (-0.9, -3.0, 4.4), (-0.9, -3.4, 0.55)],
                  "leg R (back)": [(0.8, 0.3, 6.0), (0.9, 2.6, 3.0), (0.9, 5.6, 0.6)]}
        feet = {"leg L (front)": ((-0.9, -3.75, 0.25), I3), "leg R (back)": ((0.9, 5.45, 0.25), Rx(math.radians(-12)))}
        lean = math.radians(32)
        Rt = Rx(lean); T = np.array((0, 0.3, 6.2)) + Rt @ np.array((0, 0, 1.9))
        hc, Rh, mouth = T + Rt @ np.array((0, -0.5, 3.2)), Rx(math.radians(12)), 0.55
        sh = lambda sx: T + Rt @ np.array((sx * 1.55, 0, 1.45))
        armdef = {"arm R": [tuple(sh(1)), (3.7, 0.4, 7.4), (5.3, 2.6, 6.6)],
                  "arm L": [tuple(sh(-1)), (-3.7, 0.4, 7.4), (-5.3, 2.6, 6.6)]}
    else:   # kneel at its lantern
        legdef = {"leg R (kneeling)": [(0.8, 0.4, 4.4), (0.85, 0.0, 0.32), (0.85, 3.9, 0.32)],
                  "leg L (knee up)": [(-0.8, 0.4, 4.4), (-0.85, -3.6, 4.5), (-0.85, -3.3, 0.55)]}
        feet = {"leg R (kneeling)": ((0.85, 4.35, 0.25), Rx(math.radians(90))),
                "leg L (knee up)": ((-0.85, -3.6, 0.25), I3)}
        lean = math.radians(20)
        Rt = Rx(lean); T = np.array((0, 0.4, 4.6)) + Rt @ np.array((0, 0, 1.9))
        hc, Rh, mouth = T + Rt @ np.array((0, -0.4, 3.2)) + np.array((0, -0.3, 0)), Rx(math.radians(28)), 0.0
        sh = lambda sx: T + Rt @ np.array((sx * 1.55, 0, 1.45))
        armdef = {"arm R (ring hand)": [tuple(sh(1)), (1.9, -3.4, 5.7), (0.55, -5.7, 3.15)],
                  "arm L": [tuple(sh(-1)), (-1.65, -2.0, 5.15), (-1.1, -5.4, 5.05)]}
    # legs and feet
    for nm, (hip, knee, ankle) in legdef.items():
        R1 = limb(V, hip, knee); R2 = limb(V, knee, ankle)
        fc, fR = feet[nm]
        fh = np.array((0.36, 0.55, 0.25))
        fc = np.array((fc[0], fc[1], (np.abs(fR[2, :]) * fh).sum()))   # sole exactly on the ground
        V.obox(fc, fh, fR, BODY)
        limbs[nm] = [(np.array(hip), np.array(knee), 0.32), (np.array(knee), np.array(ankle), 0.32)]
        legs_r.append((knee, ankle, R2))
        contacts[nm] = fc[2] - (np.abs(fR[2, :]) * fh).sum()
    if pose == "kneel":
        contacts["knee R"] = 0.32 - 0.3
    # torso and head
    V.obox(T, (1.2, 0.6, 1.9), Rt, BODY)
    enderman_head(V, hc, Rh, mouth, style)
    # arms and hands
    for nm, (s0, el, wr) in armdef.items():
        limb(V, s0, el, 0.55); R2 = limb(V, el, wr, 0.55)
        limbs[nm] = [(np.array(s0), np.array(el), 0.3), (np.array(el), np.array(wr), 0.3)]
        arms_r.append((el, wr, R2))
    armour(V, style, T, Rt, None, legs_r, arms_r)
    if pose == "carry":
        bc = np.array((0, -3.6, 9.6))
        fear_block(V, bc, 1.0, I3)
        for sx in (-1, 1):
            V.obox((sx * 1.15, -3.6, 9.6), (0.15, 0.5, 0.45), I3, BODY)                       # palms on the block
            for k, dy in enumerate((-0.32, 0.0, 0.32)):
                a = np.array((sx * 1.15, -3.6 + dy, 10.1)); b = np.array((sx * 0.55, -3.6 + dy, 10.75))
                limb(V, a, b, 0.22, (0, 0, 1)); V.obox(b, (0.1, 0.1, 0.1), I3, EDGE)
        V.obox((1.15, -3.6, 9.6), (0.18, 0.12, 0.07), I3, RINGY, only_empty=False)
        for k in range(4):
            a = k / 4 * math.tau + 0.4
            p = np.array((math.cos(a) * 3.6, math.sin(a) * 3.2, 7.0 + 2.5 * math.sin(a * 2)))
            fear_block(V, p, 0.32, Rz(a) @ Rx(0.5 + k * 0.3), core=True)
        static_specks(V, rng, (0, 0, 9), (4, 4, 5), 40)
    elif pose == "lunge":
        for nm, (s0, el, wr) in armdef.items():
            sx = 1 if "R" in nm else -1
            f = fingers(V, wr, np.asarray(wr) - el, (0, 0, 1), n=3, L=1.2, spread=0.28, curl=0.4, ring=sx > 0)
            limbs[nm] += f
        static_specks(V, rng, (0, 3.5, 7), (3, 5, 6), 70)
    else:
        lantern(V, (0.55, -5.7, 0.0), h=2.0)
        f = fingers(V, armdef["arm R (ring hand)"][2], (0, -0.2, -1), (1, 0, 0), n=3, L=0.75, spread=0.26, ring=True)
        limbs["arm R (ring hand)"] += f
        f = fingers(V, armdef["arm L"][2], (0.1, -1, -0.3), (1, 0, 0), n=3, L=1.0, spread=0.24, curl=0.5)
        limbs["arm L"] += f
        static_specks(V, rng, (0.5, -3, 5), (3, 4, 5), 35)
    solids = [("lantern", (0.55, -5.7, 1.0), 0.75)] if pose == "kneel" else []
    if pose == "kneel":   # the ring hand rests on the lantern's port: contact, not a clip
        solids = [("lantern", (0.55, -5.7, 0.9), 0.7)]
    check(code, {k: v for k, v in limbs.items()}, solids=solids,
          contacts=list(contacts.items()))
    ob = grid_mesh(f"{code} lantern enderman", V, EM, trans=(PLATE, BGLASS))
    objs = [ob]
    if pose == "lunge":   # teleport afterimages: the black body only, left behind in yellow static
        GB = V.G.copy(); V.G[(V.G != BODY)] = 0
        for k, off in enumerate((3.4, 6.8)):
            g = grid_mesh(f"{code} afterimage {k + 1}", V, {BODY: GHOST})
            g.location = (0.6 * (k + 1), off, 0); objs.append(g)
        V.G = GB
    lt = light(f"{code} lantern glow", (0, -1.5, 10.0) if pose != "kneel" else (0.55, -5.7, 1.0), (1.0, 0.65, 0.1), 220,
               radius=0.3, cutoff=14)
    objs.append(lt)
    objs.append(ground_disc(f"{code} ground", 12, seed=3 + len(code)))
    objs.append(player(f"{code} player", (5.2, -7.0, 0), face=(0, 0)))
    look = {"carry": (0, -1.2, 8.2), "lunge": (0, 0.5, 6.0), "kneel": (0, -2.6, 5.4)}[pose]
    cam = stage(code, X, objs, look, 29, elev=0.16, key=7000)
    add_take(code, name, cam, facts)


# =============================================================== the blue great white
BACK, BELLY, BGLOW, SMOUTH, STOOTH, SEYE, HFIN, FINTIP, SCAR, FINC = range(1, 11)
SM = {BACK: pmat("shark back", (0.055, 0.12, 0.21), (0.12, 0.23, 0.37), 0.35),
      BELLY: pmat("shark belly", (0.72, 0.74, 0.77), (0.9, 0.91, 0.93), 0.4),
      BGLOW: mat("blue hard light", (0.2, 0.55, 1.0), 0.3, emit=(0.15, 0.5, 1.0), es=1.4),
      SMOUTH: pmat("shark mouth", (0.2, 0.03, 0.04), (0.34, 0.07, 0.08), 0.5),
      STOOTH: mat("shark teeth", (0.92, 0.9, 0.84), 0.35),
      SEYE: mat("shark eye", (0.005, 0.005, 0.01), 0.08),
      HFIN: mat("hard-light fin", (0.2, 0.45, 0.9), 0.2, emit=(0.15, 0.48, 1.0), es=0.45, alpha=0.55),
      FINTIP: pmat("fin tips", (0.02, 0.035, 0.06), (0.05, 0.08, 0.12), 0.4),
      SCAR: pmat("old scars", (0.3, 0.37, 0.45), (0.45, 0.52, 0.6), 0.5),
      FINC: pmat("shark fins", (0.1, 0.19, 0.3), (0.18, 0.3, 0.45), 0.35)}
SL = 23.5   # spine length, blocks (body 0.93 of it: a 22-block shark)


def bezier(P, n=400):
    P = np.asarray(P, float); t = np.linspace(0, 1, n)[:, None]
    B = ((1 - t) ** 3) * P[0] + 3 * ((1 - t) ** 2) * t * P[1] + 3 * (1 - t) * t * t * P[2] + t ** 3 * P[3]
    seg = np.linalg.norm(np.diff(B, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    return B, cum


def spine(P, back_ref):
    """Scale the control points about the snout to SL blocks; return s -> (centre, X side, T tailward, U back)."""
    P = np.asarray(P, float)
    B, cum = bezier(P)
    P = P[0] + (P - P[0]) * (SL / cum[-1])
    B, cum = bezier(P)
    s_of = cum / cum[-1]
    br = np.asarray(back_ref, float)

    def at(s):
        i = int(np.clip(np.searchsorted(s_of, s), 1, len(B) - 1))
        c = B[i - 1] + (B[i] - B[i - 1]) * ((s - s_of[i - 1]) / max(s_of[i] - s_of[i - 1], 1e-9))
        T = nrm(B[min(i + 2, len(B) - 1)] - B[max(i - 3, 0)])
        U = nrm(br - T * (br @ T)); Xs = np.cross(T, U)
        return c, Xs, T, U
    return at


def girth(s):
    f = math.sin(math.pi / 2 * s / 0.32) ** 0.55 if s < 0.32 else max(math.cos(math.pi / 2 * min(1, (s - 0.32) / 0.62)) ** 1.2, 0.13)
    w, h = 2.2 * f, 2.75 * f
    if s > 0.84:
        w = max(w, 0.6)   # caudal keel
    return max(w, 0.25), max(h, 0.3)


def great_white(code, pose, look, X, facts, name):
    rng = np.random.default_rng(90 + ord(code[-1]))
    V = Vox((-15, -18, -10), (15, 18, 19.5), 0.25)
    hard = look == "hardlight"
    if pose == "breach":
        at = spine([(-3.5, -2.0, 15.0), (-1.5, -1.0, 9.5), (0.5, 0.3, 4.5), (2.5, 1.5, -4.5)], (0.85, 0.5, 0.0))
        gape, ledge = 34, None
    elif pose == "bank":
        at = spine([(-9.5, -3.0, -1.2), (-3.0, -10.0, -1.2), (6.0, -8.5, -1.5), (8.0, 3.0, -2.0)], (0.25, 0.25, 1.0))
        gape, ledge = 10, None
    else:
        at = spine([(0, -12.8, 3.0), (0, -6.5, 2.4), (0, 0.5, 0.4), (0, 7.5, -3.0)], (0, 0.15, 1.0))
        gape, ledge = 52, dict(x=(-9, 9), y=(-18, -6.0), top=1.0)
    S = np.linspace(0, 0.93, 150)
    fr = [at(s) for s in S]
    ds = SL * 0.93 / len(S)
    for s, (c, Xs, T, U) in zip(S, fr):
        w, h = girth(s)
        V.ell(c, (w, ds * 1.6, h), BACK, np.column_stack([Xs, T, U]))
    # label pass: nearest spine sample gives (s, side, height) for every body voxel
    idx = np.argwhere(V.G > 0)
    P = idx * V.step + V.lo + V.step / 2
    C = np.array([f[0] for f in fr])
    best = np.zeros(len(P), int); bd = np.full(len(P), 1e9)
    for j in range(len(C)):
        d = ((P - C[j]) ** 2).sum(1)
        m = d < bd; bd[m] = d[m]; best[m] = j
    Cs = C[best]
    Xa = np.array([f[1] for f in fr])[best]; Ua = np.array([f[3] for f in fr])[best]
    GW = np.array([girth(s) for s in S])[best]
    sv = S[best]
    lx = ((P - Cs) * Xa).sum(1) / GW[:, 0]; lz = ((P - Cs) * Ua).sum(1) / GW[:, 1]
    lab = np.full(len(P), BACK, np.int16)
    line = -0.08 + 0.13 * np.sin(sv * 57 + lx * 2.0) + 0.06 * np.sin(sv * 151)
    lab[lz < line] = BELLY
    gill = (sv > 0.2) & (sv < 0.29) & (((sv - 0.2) / 0.018) % 1 < 0.38) & (np.abs(lx) > 0.5) & (lz > -0.55) & (lz < 0.4)
    lab[gill] = BGLOW
    if look == "scarred":
        lat = (sv > 0.27) & (sv < 0.86) & (np.abs(lz - 0.05) < 0.07) & (np.abs(lx) > 0.45)
        lab[lat] = BGLOW
        scar = (lz > 0.1) & (np.abs(np.sin(sv * 40 + lz * 9 + lx * 4)) < 0.05) & (sv > 0.12) & (sv < 0.6)
        lab[scar & (lab == BACK)] = SCAR
    V.G[tuple(idx.T)] = lab
    # open mouth: cut away the head below the upper jaw line, hang a lower jaw on a hinge
    head_cut = (sv < 0.15) & (lz < -0.28)
    V.G[tuple(idx[head_cut].T)] = 0
    roof = (sv < 0.15) & (lz >= -0.28) & (lz < -0.05) & (np.abs(lx) < 0.75)
    V.G[tuple(idx[roof].T)] = np.where(V.G[tuple(idx[roof].T)] > 0, SMOUTH, 0)
    ch, Xh, Th, Uh = at(0.15)
    wh, hh = girth(0.15)
    hinge = ch - Uh * hh * 0.35
    g = math.radians(gape)

    def rot(p):   # rotate about the hinge axis (X): the jaw's front swings down
        v = np.asarray(p, float) - hinge
        return hinge + v * math.cos(g) + np.cross(Xh, v) * math.sin(g) + Xh * (Xh @ v) * (1 - math.cos(g))
    Rjaw = np.column_stack([Xh, Th * math.cos(g) + Uh * math.sin(g), -Th * math.sin(g) + Uh * math.cos(g)])
    for s in np.linspace(0.02, 0.16, 18):
        c, Xs, T, U = at(s)
        w, h = girth(s)
        ctr = c - U * h * 0.55
        V.ell(rot(ctr), (w * 0.82, ds * 1.8, h * 0.32), BELLY, np.column_stack(
            [Xs, rot(ctr + T) - rot(ctr), rot(ctr + U) - rot(ctr)]))
        V.ell(rot(ctr + U * h * 0.2), (w * 0.62, ds * 1.8, h * 0.12), SMOUTH,
              np.column_stack([Xs, rot(ctr + T) - rot(ctr), rot(ctr + U) - rot(ctr)]))
    for s in np.linspace(0.03, 0.14, 9):   # teeth: upper row points down, lower row up
        c, Xs, T, U = at(s)
        w, h = girth(s)
        for sx in (-1, 1):
            top = c + Xs * sx * w * 0.72 - U * h * 0.27
            V.cap(top, top - U * 0.7, 0.16, STOOTH, 0.05)
            low = c + Xs * sx * w * 0.66 - U * h * 0.42
            V.cap(rot(low), rot(low + U * 0.6), 0.15, STOOTH, 0.05)
    c0, X0, T0, U0 = at(0.0)
    V.cap(c0 - U0 * 0.5, c0 - U0 * 0.5 + T0 * 0.3 - U0 * 0.55, 0.16, STOOTH, 0.05)
    # eyes: black with a blue hard-light ring
    c, Xs, T, U = at(0.085)
    w, h = girth(0.085)
    for sx in (-1, 1):
        e = c + Xs * sx * w * 0.86 + U * h * 0.22
        V.ell(e, (0.5, 0.5, 0.5), BGLOW, only_full=True)
        V.ell(e + Xs * sx * 0.1, (0.3, 0.3, 0.3), SEYE)
    # fins
    finlab = HFIN if hard else FINC
    edge = BGLOW

    def fin(s0, s1, lx, lz, tip, thick=0.45, lab=None, edge_lab=edge):
        a0, Xa_, Ta_, Ua_ = at(s0); a1, Xb_, Tb_, Ub_ = at(s1)
        w0, h0 = girth(s0); w1, h1 = girth(s1)
        r0 = a0 + Xa_ * lx * w0 + Ua_ * lz * h0
        r1 = a1 + Xb_ * lx * w1 + Ub_ * lz * h1
        cm, Xm, Tm, Um = at((s0 + s1) / 2)
        p2 = (r0 + r1) / 2 + Xm * tip[0] + Tm * tip[1] + Um * tip[2]
        V.tri(r0, r1, p2, thick, lab or finlab, edge_lab=edge_lab, edge_w=0.32)
        return [(r0, p2, thick), (r1, p2, thick)]
    fins = {}
    for sx in (-1, 1):
        fins[f"pectoral {'R' if sx > 0 else 'L'}"] = fin(0.26, 0.36, sx * 0.7, -0.45, (sx * 5.2, 2.6, -2.2))
        fins[f"pelvic {'R' if sx > 0 else 'L'}"] = fin(0.6, 0.66, sx * 0.4, -0.75, (sx * 1.2, 1.2, -1.0), 0.35)
    fins["dorsal"] = fin(0.36, 0.52, 0, 0.92, (0, 2.0, 4.0), 0.5)
    fins["second dorsal"] = fin(0.8, 0.84, 0, 0.9, (0, 0.6, 0.8), 0.35, edge_lab=None)
    fins["anal"] = fin(0.81, 0.85, 0, -0.9, (0, 0.6, -0.8), 0.35, edge_lab=None)
    ce, Xe, Te, Ue = at(0.93)
    up_tip = ce + Te * 3.6 + Ue * 4.9; lo_tip = ce + Te * 2.0 - Ue * 3.5
    V.tri(ce - Te * 0.9 + Ue * 0.2, ce + Te * 0.6 + Ue * 0.1, up_tip, 0.5, finlab, edge_lab=edge, edge_w=0.32)
    V.tri(ce - Te * 0.6 - Ue * 0.2, ce + Te * 0.6 - Ue * 0.1, lo_tip, 0.5, finlab, edge_lab=edge, edge_w=0.32)
    fins["tail"] = [(ce, up_tip, 0.5), (ce, lo_tip, 0.5)]
    if not hard:   # dark pectoral tips underneath, like a real great white
        for sx in (-1, 1):
            a, Xs, T, U = at(0.31)
            V.ell(a + Xs * sx * 5.8 + T * 2.4 - U * 2.4, (1.2, 1.2, 0.6), FINTIP, only_full=True)
    # contact: lift the shark until it rests on the ledge (belly and fins on top, never through it)
    dz = 0.0
    objs = []
    x, y, z = V.axes()
    if ledge:
        reg = ((x[:, None, None] > ledge["x"][0]) & (x[:, None, None] < ledge["x"][1]) &
               (y[None, :, None] > ledge["y"][0]) & (y[None, :, None] < ledge["y"][1]))
        reg = np.broadcast_to(reg, V.G.shape)
        low = lowest_z(V, region=reg)
        dz = ledge["top"] - low
        LV = Vox((ledge["x"][0], ledge["y"][0], -9.0), (ledge["x"][1], ledge["y"][1], ledge["top"]), 0.5)
        lx_, ly_, lz_ = LV.axes()
        edge_noise = rng.normal(0, 0.4, (len(lx_), 1, 1))
        LV.G[np.broadcast_to(ly_[None, :, None] < ledge["y"][1] - 0.2 - np.abs(edge_noise), LV.G.shape)] = 1
        LV.G[:, :, -1][(LV.G[:, :, -1] > 0) & (rng.random(LV.G.shape[:2]) < 0.15)] = 2
        objs.append(grid_mesh(f"{code} ledge", LV, {1: COMMON["ground"], 2: COMMON["moss"]}))
        pl_at = (-2.8, -15.2, ledge["top"])
    else:
        rx, ry = ((-12, -5), (-17, -10)) if pose == "breach" else ((-15, -9), (6, 13))
        LV = Vox((rx[0], ry[0], -9.0), (rx[1], ry[1], 1.0), 0.5)
        LV.G[:] = 1
        LV.G[:, :, -1][rng.random(LV.G.shape[:2]) < 0.15] = 2
        objs.append(grid_mesh(f"{code} rock", LV, {1: COMMON["ground"], 2: COMMON["moss"]}))
        pl_at = ((rx[0] + rx[1]) / 2, (ry[0] + ry[1]) / 2, 1.0)
    # foam where the body meets the water, spray above it
    zi = int(round((0.0 - dz - V.lo[2]) / V.step))
    if 0 < zi < V.shape[2] - 12:
        body2d = (V.G[:, :, zi - 1:zi + 2] > 0).any(2)
        ring = body2d.copy()
        for k in range(4):
            ring = ring | np.roll(ring, 1, 0) | np.roll(ring, -1, 0) | np.roll(ring, 1, 1) | np.roll(ring, -1, 1)
            if k == 1:
                inner = ring.copy()
        near = ring & ~body2d
        X2 = x[:, None]; Y2 = y[None, :]
        if ledge:
            near &= ~((X2 > ledge["x"][0]) & (X2 < ledge["x"][1]) & (Y2 < ledge["y"][1]))
        foam = near & ((rng.random(near.shape) < 0.35) | inner)
        V.G[:, :, zi][foam & (V.G[:, :, zi] == 0)] = 20
        top_n = 34 if pose == "breach" else (14 if pose == "lunge" else 8)
        cand = np.argwhere(near)
        for k in rng.choice(len(cand), min(len(cand), 220 if pose == "breach" else 90), replace=False):
            hgt = rng.exponential(0.25) * top_n / 10
            kz = zi + 1 + int(hgt / V.step)
            if kz < V.shape[2]:
                i, j = cand[k]
                if V.G[i, j, kz] == 0:
                    V.G[i, j, kz] = 20
        if False:   # (wake: read as a white snake in the check render; the foam ring is enough)
            for s in np.linspace(0.45, 0.93, 40):
                c, Xs, T, U = at(s)
                for sx in (-1, 1):
                    p = c + Xs * sx * (1.5 + (s - 0.45) * 7) + T * 1.5
                    for _ in range(4):
                        q = p + rng.normal(0, 0.35, 3)
                        i, j = int((q[0] - V.lo[0]) / V.step), int((q[1] - V.lo[1]) / V.step)
                        if 0 <= i < V.shape[0] and 0 <= j < V.shape[1] and V.G[i, j, zi] == 0:
                            V.G[i, j, zi] = 20
    mats = dict(SM); mats[20] = COMMON["foam"]
    check(code, fins, floor=-9.0)
    if ledge:
        CHECKS[code]["contacts"] = [("belly/fins on the ledge", round(float(low + dz - ledge["top"]), 2))]
    ob = grid_mesh(f"{code} great white", V, mats, trans=(HFIN,))
    ob.location = (0, 0, dz)
    objs.append(ob)
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=21, fill_type="NGON", location=(0, 0, 0))
    w = bpy.context.object; w.name = f"{code} water"; w.data.materials.append(COMMON["water"])
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=21, fill_type="NGON", location=(0, 0, -9))
    b = bpy.context.object; b.name = f"{code} pool bed"; b.data.materials.append(COMMON["poolbed"])
    objs += [w, b]
    objs.append(player(f"{code} player", pl_at, face=(0, -6 if ledge else 0)))
    objs.append(light(f"{code} blue under", (0, 0, -3.0), (0.2, 0.5, 1.0), 900, radius=2, cutoff=25))
    look_at = {"breach": (0, -1.5, 6.0), "bank": (0, -3, 0.5), "lunge": (0, -6, 2.5)}[pose]
    cam = stage(code, X, objs, look_at, {"breach": 40, "bank": 40, "lunge": 34}[pose],
                elev={"breach": 0.22, "bank": 0.55, "lunge": 0.35}[pose], key=9000)
    add_take(code, name, cam, facts)


# =============================================================== the takes
BUILDS = [
    lambda X: grizzly("G2a", "swipe", "brown", X,
                      "brown coat; on all fours, head low and roaring, the near front paw mid-swipe with five long pale "
                      "claws out; three paws planted flat on the ground; shoulder hump, dished face, cheek ruffs, round "
                      "ears, grizzled tips and shaggy tufts down the back; about 18 blocks long, 10 at the shoulder",
                      "Grizzly: swipe"),
    lambda X: grizzly("G2b", "charge", "silvertip", X,
                      "silvertip coat (dark brown, silver-tipped fur); mid-gallop: one front paw landing, the other just "
                      "touching down ahead, a hind foot planted under it, the other pushing off; mouth open, ears back",
                      "Grizzly: charge"),
    lambda X: grizzly("G2c", "rear", "dark", X,
                      "dark coat; up on the hind legs (about 21 blocks to the ears), both hind feet flat on the ground, "
                      "arms spread with claws out, head thrown back in a roar",
                      "Grizzly: rearing roar"),
    lambda X: lantern_enderman("E2a", "carry", "plate", X,
                               "plates: a black enderman (14 tall) under stand-off yellow hard-light armour (stacked "
                               "pauldrons, a chest plate with a window onto its gold-framed lantern heart, greaves, "
                               "bracers, floating back plates), a gold halo; it carries a big fear block (glass, glowing "
                               "edges, a dark core with a fear-eye slit) in both hands, four small ones orbiting",
                               "Lantern Enderman: block carrier"),
    lambda X: lantern_enderman("E2b", "lunge", "shard", X,
                               "shards: armour of faceted fear glass (shoulder spikes, barbs down the forearms and spine, "
                               "knee spikes, a shard crown); a screaming lunge out of a teleport, jaw open on its glow, "
                               "clawed hands flung back (the ring on its right hand); two black afterimages behind it in "
                               "yellow static; both feet on the ground",
                               "Lantern Enderman: scream lunge"),
    lambda X: lantern_enderman("E2c", "kneel", "cage", X,
                               "lantern cage: gold bars over a glowing heart in its chest, rounded glass pauldrons; it kneels "
                               "(one knee on the ground) to charge its ring at its own Yellow Lantern, the ring hand resting "
                               "on the lantern's port, the other forearm on its raised knee",
                               "Lantern Enderman: kneels to charge"),
    lambda X: great_white("S2a", "breach", "natural", X,
                          "a 22-block great white breaching straight up out of the flooded room, jaws open on rows of "
                          "teeth; steel blue over a ragged white belly line, blue hard-light gill slits, eye rings and fin "
                          "edges; a ring of foam and spray where it leaves the water",
                          "Great White: breach"),
    lambda X: great_white("S2b", "bank", "hardlight", X,
                          "hard-light fins: see-through blue fins and tail with glowing edges; banking hard just under the "
                          "surface, only the back and the dorsal fin cutting the water, a foam wake behind",
                          "Great White: banking hunt"),
    lambda X: great_white("S2c", "lunge", "scarred", X,
                          "scarred: pale old scars on the back and a glowing blue line down each side; it hurls itself "
                          "onto the ledge at you, belly and fins resting on the stone, jaws wide, the tail still in the "
                          "water",
                          "Great White: ledge lunge"),
]
for i, b in enumerate(BUILDS):
    b(np.array([i * GAP, 0.0, 0.0]))

scene.camera = bpy.data.objects[TAKES[0][2]]
scene["ges_takes"] = repr(TAKES)
scene["v2_0112_checks"] = repr(CHECKS)
bad = [c for c, r in CHECKS.items() if r["fails"]]
print(f"[{PASS}] built {len(TAKES)} takes, {len(scene.objects)} objects; checks {'all OK' if not bad else 'FAIL in ' + ', '.join(bad)}")
