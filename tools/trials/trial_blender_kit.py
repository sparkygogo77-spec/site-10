"""Shared Blender helpers for the spider trial block-outs (import from a script run with blender -b --python).

- textured materials: 16-pixel-per-block noise like Minecraft textures (stone above y 4, deepslate below, dripstone,
  dirt, silk, webbed dirt, yellow hard light)
- voxel_mesh(): one mesh from a solid grid, flat runs of faces merged
- spider(): the six spider takes (J, 2026-10-19: real spider with "spiked web rock points" on its legs, yellow
  fear construct spider). Real: R1 hunter, R2 brute, R3 funnel-web. Construct: C1 solid light, C2 lattice, C3 shards.
- player(), camera(), light()

Grid convention: grid (x, y up, z) -> Blender (x, -z, y); grid y index 0 is world y -64.
"""
import math
import bpy, bmesh
import numpy as np
from mathutils import Vector

sc = bpy.context.scene
DEEP_Z = 68          # grid index of world y 4: deepslate below


# ---------------------------------------------------------------- materials
def _bsdf(m):
    if m.node_tree is None:
        m.use_nodes = True
    return m.node_tree.nodes["Principled BSDF"]


def mat(name, rgb, rough=0.9, emit=None, strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    b = _bsdf(m)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def _pixels(nt, lo, hi, per_block=16, seed=0.0):
    """Colour from a 16 px per block white noise between lo and hi, plus a per-block tint."""
    n = nt.nodes
    tc = n.new("ShaderNodeTexCoord")
    sc_ = n.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs[3].default_value = per_block
    fl = n.new("ShaderNodeVectorMath"); fl.operation = "FLOOR"
    add = n.new("ShaderNodeVectorMath"); add.operation = "ADD"; add.inputs[1].default_value = (seed, seed * 2, seed * 3)
    wn = n.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"
    blk = n.new("ShaderNodeVectorMath"); blk.operation = "FLOOR"
    wn2 = n.new("ShaderNodeTexWhiteNoise"); wn2.noise_dimensions = "3D"
    mix = n.new("ShaderNodeMath"); mix.operation = "MULTIPLY_ADD"
    mix.inputs[1].default_value = 0.7
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*lo, 1); ramp.color_ramp.elements[1].color = (*hi, 1)
    l = nt.links
    l.new(tc.outputs["Object"], sc_.inputs[0]); l.new(sc_.outputs[0], fl.inputs[0]); l.new(fl.outputs[0], add.inputs[0])
    l.new(add.outputs[0], wn.inputs["Vector"])
    l.new(tc.outputs["Object"], blk.inputs[0]); l.new(blk.outputs[0], wn2.inputs["Vector"])
    l.new(wn.outputs["Value"], mix.inputs[0])
    w2 = n.new("ShaderNodeMath"); w2.operation = "MULTIPLY"; w2.inputs[1].default_value = 0.3
    l.new(wn2.outputs["Value"], w2.inputs[0]); l.new(w2.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], ramp.inputs["Fac"])
    return ramp.outputs["Color"]


def pixel_mat(name, lo, hi, rough=0.95, lo2=None, hi2=None):
    """Pixel-noise material; with lo2/hi2 it switches to that palette below world y 4 (deepslate)."""
    m = bpy.data.materials.new(name)
    b = _bsdf(m); nt = m.node_tree
    c1 = _pixels(nt, lo, hi)
    if lo2 is None:
        nt.links.new(c1, b.inputs["Base Color"])
    else:
        c2 = _pixels(nt, lo2, hi2, seed=7.0)
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = DEEP_Z
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        nt.links.new(tc.outputs["Object"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], lt.inputs[0])
        nt.links.new(lt.outputs[0], mx.inputs[0]); nt.links.new(c1, mx.inputs[6]); nt.links.new(c2, mx.inputs[7])
        nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m


def construct_mat(name="yellow hard light", strength=3.0, alpha=0.7):
    """Yellow fear construct: emissive, see-through, with slow bands (like the Y textures)."""
    m = bpy.data.materials.new(name)
    b = _bsdf(m); nt = m.node_tree
    col = _pixels(nt, (1.0, 0.62, 0.05), (1.0, 0.9, 0.35), per_block=4)
    nt.links.new(col, b.inputs["Base Color"]); nt.links.new(col, b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Roughness"].default_value = 0.3
    return m


def cave_materials(textured=True):
    """Index order used by voxel_mesh: 0 cave rock, 1 burrow earth, 2 cut rock, 3 shaft, 4 cut deepslate, 5 grass,
    6 silk, 7 webbed dirt, 8 dripstone, 9 construct tip."""
    if not textured:
        return [mat("cave wall", (0.17, 0.16, 0.14)), mat("burrow earth", (0.20, 0.12, 0.07)), mat("cut stone", (0.2, 0.2, 0.21)),
                mat("entrance shaft", (0.25, 0.32, 0.42)), mat("cut deepslate", (0.06, 0.06, 0.07)), mat("grass", (0.18, 0.35, 0.1)),
                mat("silk", (0.75, 0.74, 0.7), 0.6), mat("webbed dirt", (0.3, 0.2, 0.12)), mat("dripstone", (0.35, 0.27, 0.2)),
                construct_mat()]
    rock = pixel_mat("rock (stone / deepslate)", (0.22, 0.22, 0.22), (0.42, 0.42, 0.41), lo2=(0.07, 0.07, 0.09), hi2=(0.19, 0.19, 0.22))
    return [rock, pixel_mat("burrow dirt", (0.16, 0.10, 0.06), (0.32, 0.21, 0.12)), rock,
            pixel_mat("shaft rock", (0.20, 0.20, 0.21), (0.36, 0.36, 0.37)), rock, pixel_mat("grass", (0.15, 0.32, 0.08), (0.30, 0.52, 0.16)),
            pixel_mat("silk", (0.70, 0.70, 0.68), (0.95, 0.95, 0.93), 0.6), pixel_mat("webbed dirt", (0.22, 0.15, 0.09), (0.80, 0.78, 0.74)),
            pixel_mat("dripstone", (0.30, 0.22, 0.16), (0.52, 0.40, 0.30)), construct_mat("construct spike tip", 4.0, 0.85)]


# ---------------------------------------------------------------- voxels
CORNERS = {
    (0, 1): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (0, -1): [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
    (1, 1): [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], (1, -1): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
    (2, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (2, -1): [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
}


def voxel_mesh(name, solid, face_mat, mats, keep=None):
    """Quads on every solid face that meets a non-solid cell. face_mat(idx, nidx, axis, d) -> material index array,
    with idx/nidx the solid and neighbour cells (grid coords, may be -1 or size for outside). keep(idx, nidx) -> bool
    array filters faces. Vertices are in grid coords mapped to Blender (x, -z, y)."""
    X, Y, Z = solid.shape
    pad = np.zeros((X + 2, Y + 2, Z + 2), bool); pad[1:-1, 1:-1, 1:-1] = solid
    verts, faces, ms = [], [], []
    for (ax, d), cs in CORNERS.items():
        hit = pad & ~np.roll(pad, -d, axis=ax)
        idx = np.argwhere(hit) - 1
        if not len(idx):
            continue
        nidx = idx.copy(); nidx[:, ax] += d
        if keep is not None:
            k_ = keep(idx, nidx)
            idx, nidx = idx[k_], nidx[k_]
        m = face_mat(idx, nidx, ax, d)
        quad = np.stack([idx + np.array(c) for c in cs], 1).reshape(-1, 3)
        k = np.arange(len(idx)) * 4 + len(verts)
        verts.extend(quad.tolist()); faces.extend(np.stack([k, k + 1, k + 2, k + 3], 1).tolist()); ms.extend(np.asarray(m).tolist())
    me = bpy.data.meshes.new(name)
    v = np.asarray(verts, float)
    me.from_pydata(np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1).tolist(), [], faces)
    for m_ in mats:
        me.materials.append(m_)
    me.polygons.foreach_set("material_index", np.asarray(ms, np.int32))
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.001, verts=bm.verts, edges=bm.edges, delimit={"MATERIAL"})
    bm.to_mesh(me); bm.free(); me.update()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


def safe_get(arr, idx, default=0):
    X, Y, Z = arr.shape
    ok = (idx[:, 0] >= 0) & (idx[:, 0] < X) & (idx[:, 1] >= 0) & (idx[:, 1] < Y) & (idx[:, 2] >= 0) & (idx[:, 2] < Z)
    out = np.full(len(idx), default, dtype=arr.dtype)
    i = idx[ok]
    out[ok] = arr[i[:, 0], i[:, 1], i[:, 2]]
    return out, ok


# ---------------------------------------------------------------- small helpers
def camera(name, loc, target, lens=24):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 3000
    c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c)
    c.location = loc; c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return c


def light(name, loc, energy, color, kind="POINT", size=1.0):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = color
    if kind == "AREA":
        lt.size = size
    o = bpy.data.objects.new(name, lt); sc.collection.objects.link(o); o.location = loc
    return o


def empty(name, loc=(0, 0, 0), yaw=0.0):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.location = loc; e.rotation_euler = (0, 0, yaw)
    return e


def box(name, center, size, m, parent, along=None, wire=None):
    """A cuboid; with `along` its local Y axis points along that vector (a leg segment)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.object; o.name = name; o.scale = size; o.data.materials.append(m)
    if along is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(Vector(along).normalized())
    if wire:
        w = o.modifiers.new("lattice", "WIREFRAME"); w.thickness = wire; w.use_replace = True
    o.parent = parent
    return o


M_PLAYER = None


def player(name, loc):
    global M_PLAYER
    if M_PLAYER is None:
        M_PLAYER = mat("player", (0.15, 0.3, 0.6), 0.6)
    root = empty(name, loc)
    for nm, l, dim in [("legs", (0, 0, 0.375), (0.5, 0.25, 0.75)), ("body", (0, 0, 1.125), (0.5, 0.25, 0.75)), ("head", (0, 0, 1.75), (0.5, 0.5, 0.5))]:
        box(f"{name} {nm}", l, dim, M_PLAYER, root)
    ring = mat("ring", (0.2, 1, 0.4), 0.3, (0.2, 1, 0.4), 12)
    box(f"{name} ring", (0.45, 0.3, 1.1), (0.15, 0.15, 0.15), ring, root)
    lt = bpy.data.lights.new(name + " ring light", "POINT"); lt.energy = 300; lt.color = (0.3, 1, 0.45)
    lo = bpy.data.objects.new(name + " ring light", lt); sc.collection.objects.link(lo); lo.parent = root; lo.location = (0.5, 0.3, 1.3)
    return root


# ---------------------------------------------------------------- spiders
_MATS = {}


def _m(key):
    if key in _MATS:
        return _MATS[key]
    table = {
        "hunter": lambda: pixel_mat("spider hunter", (0.10, 0.07, 0.05), (0.24, 0.17, 0.11), 0.7),
        "hunter_band": lambda: pixel_mat("spider hunter bands", (0.32, 0.25, 0.17), (0.48, 0.38, 0.26), 0.7),
        "brute": lambda: pixel_mat("spider brute", (0.05, 0.04, 0.035), (0.14, 0.11, 0.09), 0.9),
        "hair": lambda: mat("spider hair", (0.30, 0.24, 0.18), 0.9),
        "funnel": lambda: pixel_mat("spider funnel-web", (0.015, 0.015, 0.02), (0.07, 0.07, 0.09), 0.18),
        "fang": lambda: mat("fangs", (0.03, 0.02, 0.02), 0.15),
        "spike": lambda: pixel_mat("web-rock spike", (0.30, 0.30, 0.29), (0.55, 0.54, 0.52), 0.8),
        "silk": lambda: pixel_mat("silk binding", (0.75, 0.75, 0.72), (0.98, 0.98, 0.96), 0.6),
        "eye": lambda: mat("spider eyes", (1, 0.8, 0.1), 0.3, (1, 0.75, 0.05), 10),
        "c_solid": lambda: construct_mat("construct solid", 1.2, 0.6),
        "c_edge": lambda: mat("construct edge", (1, 0.85, 0.3), 0.3, (1, 0.8, 0.2), 4),
        "c_lattice": lambda: construct_mat("construct lattice", 3.0, 1.0),
        "c_shard": lambda: construct_mat("construct shards", 2.0, 0.85),
    }
    _MATS[key] = table[key]()
    return _MATS[key]


def _legs(span, body_h, ceph_w, ceph_l, raised_front=False):
    """Hip, knee, ankle, foot points (local, +Y forward) for 8 legs."""
    out = []
    R = span / 2
    for s in (-1, 1):
        for k in range(4):
            phi = math.radians(52 - k * 34)
            dvec = Vector((s * math.cos(phi), math.sin(phi), 0))
            hip = Vector((s * ceph_w * 0.45, ceph_l * (0.35 - k * 0.22), body_h))
            foot = hip + dvec * (R - hip.length * 0.5); foot.z = 0.0
            knee = hip + dvec * (R * 0.40) + Vector((0, 0, body_h * 0.95))
            ankle = knee + (foot - knee) * 0.6 + dvec * R * 0.05
            if raised_front and k == 0:
                knee.z += body_h * 0.6; ankle = knee + dvec * R * 0.25 + Vector((0, 0, body_h * 0.3))
                foot = ankle + dvec * R * 0.2 + Vector((0, 0, -body_h * 0.4))
            out.append((s, k, hip, knee, ankle, foot))
    return out


def _seg(name, a, b, thick, m, parent, wire=None):
    v = b - a
    return box(name, tuple((a + b) / 2), (thick, v.length, thick), m, parent, along=v, wire=wire)


def _spike(name, a, b, thick, parent):
    """Silk-bound stone spike: a silk band, then three stepped stone blocks narrowing to a point."""
    v = b - a
    _seg(name + " silk", a, a + v * 0.22, thick * 1.35, _m("silk"), parent)
    steps = [(0.18, 0.55, 1.0), (0.55, 0.82, 0.65), (0.82, 1.0, 0.32)]
    for i, (t0, t1, w) in enumerate(steps):
        _seg(f"{name} stone{i}", a + v * t0, a + v * t1, thick * w * 1.15, _m("spike"), parent)


def _blob(name, center, size, m, parent, wire=None):
    """A rounded voxel lump: a core box plus three slightly smaller boxes poking out of its faces."""
    c = Vector(center); sx, sy, sz = size
    box(name, center, (sx * 0.8, sy * 0.8, sz * 0.8), m, parent, wire=wire)
    box(name + " x", center, (sx, sy * 0.6, sz * 0.6), m, parent, wire=wire)
    box(name + " y", center, (sx * 0.6, sy, sz * 0.6), m, parent, wire=wire)
    box(name + " z", center, (sx * 0.6, sy * 0.6, sz), m, parent, wire=wire)


def spider(take, name, loc, span, yaw=0.0):
    """Build one spider take at loc. Real takes: R1 hunter, R2 brute, R3 funnel-web. Construct: C1, C2, C3."""
    root = empty(name, loc, yaw)
    s = span / 10.0
    construct = take.startswith("C")
    body_h = 1.5 * s if take != "R1" else 1.8 * s
    ceph_w, ceph_l = (1.6 * s, 1.9 * s) if take != "R1" else (1.2 * s, 1.6 * s)
    if take == "R2":
        ceph_w, ceph_l = 2.0 * s, 2.1 * s
    abd = {"R1": (1.4, 3.0, 1.3), "R2": (2.8, 3.2, 2.4), "R3": (2.2, 2.8, 1.7)}.get(take, (2.0, 2.8, 1.8))
    abd = tuple(a * s for a in abd)
    wire = 0.18 * s if take == "C2" else None
    body_m = {"R1": "hunter", "R2": "brute", "R3": "funnel", "C1": "c_solid", "C2": "c_lattice", "C3": "c_shard"}[take]
    mb = _m(body_m)
    ceph_c = Vector((0, 0.4 * s, body_h + 0.2 * s))
    abd_c = Vector((0, -ceph_l * 0.5 - abd[1] * 0.45, body_h + abd[2] * 0.25))
    if take == "C3":
        # shards: the body is a cloud of separate cubes filling its shape, with gaps between them
        rng = np.random.default_rng(len(name))
        for part_c, part_s in ((ceph_c, (ceph_w, ceph_l, 1.0 * s)), (abd_c, abd)):
            n = 40
            for i in range(n):
                off = Vector(((rng.random() - 0.5) * part_s[0], (rng.random() - 0.5) * part_s[1], (rng.random() - 0.5) * part_s[2]))
                if (off.x / part_s[0]) ** 2 + (off.y / part_s[1]) ** 2 + (off.z / part_s[2]) ** 2 > 0.25:
                    continue
                q = rng.uniform(0.25, 0.45) * s
                box(f"{name} shard{i}", tuple(part_c + off), (q, q, q), mb, root).rotation_euler = tuple(rng.uniform(0, 1, 3))
    else:
        _blob(name + " head", tuple(ceph_c), (ceph_w, ceph_l, 1.0 * s), mb, root, wire)
        _blob(name + " abdomen", tuple(abd_c), abd, mb, root, wire)
        if take == "R3":   # raised armour plate on the head
            box(name + " plate", tuple(ceph_c + Vector((0, 0, 0.55 * s))), (ceph_w * 0.85, ceph_l * 0.8, 0.25 * s), mb, root)
        if take == "C1":   # bright edges along the hard light
            for nm_, c_, sz in (("head", ceph_c, (ceph_w, ceph_l, 1.0 * s)), ("abdomen", abd_c, abd)):
                box(f"{name} {nm_} edge", tuple(c_), tuple(x * 1.02 for x in sz), _m("c_edge"), root, wire=0.06 * s)
    # eyes: two rows on the front of the head
    for i in range(8):
        row = i // 4
        ex = (i % 4 - 1.5) * 0.28 * s
        box(f"{name} eye{i}", tuple(ceph_c + Vector((ex, ceph_l * 0.5, 0.25 * s + row * 0.25 * s))), (0.18 * s,) * 3, _m("eye"), root)
    # fangs
    fang_l = (0.9 if take == "R3" else 0.5) * s
    for sx in (-1, 1):
        _seg(f"{name} fang{sx}", ceph_c + Vector((sx * 0.3 * s, ceph_l * 0.5, -0.2 * s)),
             ceph_c + Vector((sx * 0.25 * s, ceph_l * 0.55, -0.2 * s - fang_l)), 0.25 * s, _m("fang") if not construct else mb, root, wire)
    leg_t = {"R1": 0.22, "R2": 0.42, "R3": 0.32}.get(take, 0.3) * s
    rng = np.random.default_rng(span)
    for sd, k, hip, knee, ankle, foot in _legs(span, body_h, ceph_w, ceph_l, raised_front=take == "R3"):
        n_ = f"{name} leg{sd:+d}{k}"
        if take == "C3":
            for seg, (a, b) in enumerate(((hip, knee), (knee, ankle), (ankle, foot))):
                v = b - a; m_ = int(v.length / (0.7 * s)) + 1
                for j in range(m_):
                    q = 0.32 * s * (1 - 0.25 * seg)
                    box(f"{n_} chain{seg}{j}", tuple(a + v * ((j + 0.5) / m_)), (q, q, q), mb, root)
            continue
        band = _m("hunter_band") if take == "R1" else mb
        _seg(n_ + " femur", hip, knee, leg_t, mb, root, wire)
        _seg(n_ + " tibia", knee, ankle, leg_t * 0.85, band, root, wire)
        if construct:
            _seg(n_ + " tarsus", ankle, foot, leg_t * 0.6, mb, root, wire)
        else:
            _spike(n_ + " spike", ankle, foot, leg_t * 0.9, root)
        if take == "R2":   # hair: short stubs along the femur and tibia
            for seg_a, seg_b in ((hip, knee), (knee, ankle)):
                v = seg_b - seg_a
                for j in range(5):
                    p = seg_a + v * rng.uniform(0.1, 0.9)
                    off = Vector(tuple(rng.uniform(-1, 1, 3))).normalized() * leg_t * 0.6
                    box(f"{n_} hair{j}", tuple(p + off), (0.12 * s, 0.12 * s, 0.35 * s), _m("hair"), root)
    return root


# ---------------------------------------------------------------- construct spiders, round 2
# J on C1-C3 (2026-10-19): "Discard the third one on the right unless you think itd look cool in game which im not
# sure, massive improvements on the others needed". C1 -> C1a scale shell, C1b dread armour; C2 -> C2a lightning
# lattice. Built from his yellow fear construct picks (Y1 scales, Y2 lightning, Y3 dread); plates stand off the body
# (838 R4b) and shells stay see-through. Emission stays at or under ~1.5 so the yellow stays saturated (it clips
# to pale white above that under the Standard view, the 864 lesson).

def _surface(center, axes, u, v):
    """Point and outward normal on an ellipsoid (u = latitude, 0 top .. pi bottom; v = longitude)."""
    ax, ay, az = axes
    n = Vector((math.sin(u) * math.cos(v), math.sin(u) * math.sin(v), math.cos(u)))
    p = Vector((n.x * ax, n.y * ay, n.z * az))
    nn = Vector((n.x / ax, n.y / ay, n.z / az)).normalized()
    return Vector(center) + p, nn


def _plate(name, p, normal, size, m, parent, lift=0.0, wire=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(p + normal * lift))
    o = bpy.context.object; o.name = name; o.scale = size; o.data.materials.append(m)
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(normal)
    if wire:
        w = o.modifiers.new("edge", "WIREFRAME"); w.thickness = wire
    o.parent = parent
    return o


def _zigzag(name, a, b, n, amp, m, parent, rng, thick):
    pts = [a + (b - a) * (i / n) for i in range(n + 1)]
    for i in range(1, n):
        pts[i] = pts[i] + Vector(tuple(rng.uniform(-amp, amp, 3)))
    for i in range(n):
        _seg(f"{name}{i}", pts[i], pts[i + 1], thick, m, parent)


def construct_spider(take, name, loc, span, yaw=0.0):
    """C1a scale shell, C1b dread armour, C2a lightning lattice (20-block leg span in the fight)."""
    if "c_core" not in _MATS:
        _MATS["c_core"] = mat("construct core", (0.30, 0.16, 0.01), 0.4, (0.85, 0.42, 0.0), 0.6, alpha=0.95)
        _MATS["c_plate"] = construct_mat("construct plates", 1.0, 0.55)
        _MATS["c_bright"] = mat("construct seams", (1, 0.78, 0.2), 0.3, (1, 0.72, 0.1), 1.4)
        _MATS["c_dread"] = construct_mat("dread plates", 1.3, 0.75)
        _MATS["c_bolt"] = mat("construct lightning", (1, 0.9, 0.5), 0.2, (1, 0.85, 0.35), 2.0)
    root = empty(name, loc, yaw)
    s = span / 10.0
    rng = np.random.default_rng(sum(map(ord, take)))
    body_h = 1.6 * s
    ceph_w, ceph_l = 1.7 * s, 2.0 * s
    ceph_c = Vector((0, 0.5 * s, body_h + 0.3 * s))
    abd_ax = (1.15 * s, 1.6 * s, 1.0 * s)
    abd_c = Vector((0, -ceph_l * 0.5 - abd_ax[1] * 0.85, body_h + 0.7 * s))
    head_ax = (ceph_w * 0.5, ceph_l * 0.5, 0.55 * s)
    core, plate, bright = _MATS["c_core"], _MATS["c_plate"], _MATS["c_bright"]

    # every take: a dark amber core you can see through the shell, glowing eyes, fangs
    _blob(name + " core abdomen", tuple(abd_c), tuple(a * 1.5 for a in abd_ax), core, root)
    _blob(name + " core head", tuple(ceph_c), (ceph_w * 0.85, ceph_l * 0.85, 0.9 * s), core, root)
    for i in range(8):
        row = i // 4
        box(f"{name} eye{i}", tuple(ceph_c + Vector(((i % 4 - 1.5) * 0.3 * s, ceph_l * 0.48, 0.3 * s + row * 0.28 * s))),
            (0.2 * s,) * 3, _m("eye"), root)
    for sx in (-1, 1):
        a_ = ceph_c + Vector((sx * 0.32 * s, ceph_l * 0.5, -0.25 * s))
        _seg(f"{name} fang{sx}", a_, a_ + Vector((-sx * 0.1 * s, 0.25 * s, -0.8 * s)), 0.26 * s, bright, root)

    if take == "C1a":
        # Y1 scales: overlapping plates in rows over the abdomen and head, each tilted to the surface, glowing seams
        for part, c_, ax_, rows, per in (("abd", abd_c, abd_ax, 7, 12), ("head", ceph_c, head_ax, 4, 9)):
            for r_ in range(rows):
                u = 0.25 + (math.pi * 0.72) * r_ / (rows - 1)
                n_ = max(4, int(per * math.sin(u)) + 2)
                for k in range(n_):
                    v = (k + 0.5 * (r_ % 2)) / n_ * math.tau
                    p, nn = _surface(c_, ax_, u, v)
                    w_ = 0.75 * s * (1.4 if part == "abd" else 1.0)
                    _plate(f"{name} {part} scale {r_}-{k}", p, nn, (w_, w_ * 0.8, 0.12 * s), plate, root, lift=0.05 * s)
            box(f"{name} {part} seam", tuple(c_), tuple(a * 2.08 for a in ax_), bright, root, wire=0.035 * s)
    elif take == "C1b":
        # Y3 dread: big plates standing off the core with a visible gap, a ridge of spikes down the back
        dread = _MATS["c_dread"]
        spots = [(0.35, math.pi / 2), (0.75, 0.2), (0.75, math.pi - 0.2), (1.0, math.pi / 2 + 0.9), (1.0, math.pi / 2 - 0.9),
                 (0.55, -math.pi / 2), (1.25, 0.6), (1.25, math.pi - 0.6)]
        for part, c_, ax_ in (("abd", abd_c, abd_ax), ("head", ceph_c, head_ax)):
            for k, (u, v) in enumerate(spots):
                p, nn = _surface(c_, ax_, u, v)
                _plate(f"{name} {part} plate {k}", p, nn, (1.5 * s, 1.1 * s, 0.18 * s), dread, root, lift=0.45 * s)
                _plate(f"{name} {part} plate edge {k}", p, nn, (1.52 * s, 1.12 * s, 0.2 * s), bright, root, lift=0.45 * s, wire=0.05 * s)
        for k in range(6):
            t = k / 5
            base = abd_c + Vector((0, abd_ax[1] * (0.8 - 1.6 * t), abd_ax[2] * (1.05 - 0.3 * abs(t - 0.4))))
            h_ = (1.1 - 0.5 * abs(t - 0.3)) * s
            for j, w_ in enumerate((0.45, 0.3, 0.15)):
                box(f"{name} ridge {k}-{j}", tuple(base + Vector((0, 0, h_ * (j + 0.5) / 3))), (w_ * s, w_ * s, h_ / 3), dread, root)
    elif take == "C2a":
        # Y2 lightning: a frame shell with lightning crackling through the core and down every leg
        for part, c_, ax_ in (("abd", abd_c, abd_ax), ("head", ceph_c, head_ax)):
            _blob(f"{name} {part} frame", tuple(c_), tuple(a * 2.1 for a in ax_), bright, root, wire=0.07 * s)
            for k in range(5):
                a_ = Vector(c_) + Vector(tuple(rng.uniform(-1, 1, 3) * np.array(ax_) * 0.8))
                b_ = Vector(c_) + Vector(tuple(rng.uniform(-1, 1, 3) * np.array(ax_) * 0.8))
                _zigzag(f"{name} {part} bolt{k}-", a_, b_, 4, 0.25 * s, _MATS["c_bolt"], root, rng, 0.07 * s)

    leg_t = 0.34 * s
    for sd, k, hip, knee, ankle, foot in _legs(span, body_h, ceph_w, ceph_l):
        n_ = f"{name} leg{sd:+d}{k}"
        segs = ((hip, knee, leg_t), (knee, ankle, leg_t * 0.8), (ankle, foot, leg_t * 0.55))
        for j, (a, b, t_) in enumerate(segs):
            mid = a + (b - a) * 0.55
            if take == "C2a":
                _seg(f"{n_} frame{j}", a, b, t_ * 1.3, bright, root, wire=0.05 * s)
                _zigzag(f"{n_} bolt{j}-", a, b, 3, t_ * 0.35, _MATS["c_bolt"], root, rng, 0.06 * s)
            else:
                body_m = plate if take == "C1a" else core
                _seg(f"{n_} seg{j}a", a, mid, t_, body_m, root)
                _seg(f"{n_} seg{j}b", mid, b, t_ * 0.82, body_m, root)
                if take == "C1b" and j < 2:   # stand-off guard plate over the femur and tibia
                    side = Vector((sd, 0, 0.6)).normalized()
                    _seg(f"{n_} guard{j}", a + side * t_ * 1.4, b + side * t_ * 1.4, t_ * 1.5, _MATS["c_dread"], root)
            box(f"{n_} joint{j}", tuple(a), (t_ * 1.35,) * 3, bright, root)
        _seg(f"{n_} claw", foot + Vector((0, 0, 0.6 * s)), foot - Vector((0, 0, 0.15 * s)), leg_t * 0.4, bright, root)
    return root
