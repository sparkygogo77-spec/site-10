# Pass v2.0106: Dread Warren look (Trials; PC Blender chat, 2026-10-19).
# Why: J: "Dread Warren build", then "Look first (Blender) ★": the trial's look before any game code
#   (docs/plans/trials/2026-10-19-trials-concept.md, Part 1). Any corps can enter, each with its own counter to Dread.
# Rule held: ceiling walking is ON HOLD until J watches the Stormie's Spiders test world, so spiders stand on floors,
#   cling to walls or drop on a thread; nothing walks upside-down on a ceiling.
# Takes (each row its own camera, 220 blocks apart):
#   W1a Maw, W1b Weave Gallery, W1c Hatchery, W1d four corps counters   (cave and fear-light, static stills)
#   W2a Broodlings, W2b Hunter, W2c Weaver on a drop thread, W2d Dread Phantom   (fear spiders, turntables)
#   W3a the Matron, W3b Brood Heart arena, W3c Lights out   (the Matron)
# Voxel pixel art: creatures at 1/16 block, cave at 1 block with 1/16-pixel snapped textures. Yellow = them, green = you.
# Builds the whole scene from nothing (globals bpy, np, FOLDER); the renderer saves it as trials/dread_warren.blend.
import math
import bpy
import numpy as np

PASS = "v2.0106"
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


# --------------------------------------------------------------- spiders
SP = {   # voxels at 1/16 block
    "broodling": dict(ceph=(3, 3.5, 2.5), abd=(4, 5, 3.5), reach=9, knee=5, zb=4, lr=(1.0, 0.8, 0.6), eyes=1.2),
    "hunter": dict(ceph=(5, 6, 4), abd=(7.5, 9, 6), reach=18, knee=9, zb=9, lr=(1.6, 1.2, 0.9), eyes=1.0),
    "weaver": dict(ceph=(4, 5, 3), abd=(5, 11, 5), reach=27, knee=15, zb=11, lr=(0.9, 0.75, 0.6), eyes=0.9),
    "phantom": dict(ceph=(4, 5, 3.5), abd=(6, 7.5, 5), reach=14, knee=8, zb=8, lr=(1.2, 1.0, 0.8), eyes=1.0),
}
LEG_ANG = (32, 68, 108, 146)     # degrees from forward (+y), per side


def spider(name, kind, seed=1, curl=0.0):
    """A fear-construct spider: dark core under yellow hard-light plates, glowing eyes and joints.
    curl 0 = standing, 1 = legs reaching forward and down (the drop)."""
    P = SP[kind]
    rng = np.random.default_rng(seed)
    cx_, cy_, cz_ = P["ceph"]; ax_, ay_, az_ = P["abd"]
    R = P["reach"]
    W = int(2 * (R + ay_ * 2 + 10))
    H = int(P["zb"] + P["knee"] + az_ + 12)
    G = np.zeros((W, W, H), dtype=np.int16)
    ox, oy = W / 2, W / 2 + ay_ * 0.6
    zb = P["zb"]
    ceph = np.array([ox, oy + cy_ * 0.6, zb + 1])
    abd = np.array([ox, oy - cy_ * 0.4 - ay_ * 0.85, zb + az_ * 0.55])
    ellip(G, ceph, P["ceph"], 1)
    ellip(G, abd, P["abd"], 1)
    capsule(G, ceph, abd, min(cx_, ax_) * 0.55, 1)
    # plates on the upper surface, dark grooves between them, darker undersides
    surf = surface_mask(G)
    zz = np.arange(H)[None, None, :] + 0.5
    yy = np.arange(W)[None, :, None] + 0.5
    xx = np.arange(W)[:, None, None] + 0.5
    up = surf & (zz > zb + 0.5)
    groove = (np.floor(yy - abd[1]).astype(int) % 4 == 0) & (yy < abd[1] + ay_ * 0.6)
    G[up & ~groove] = 2
    G[surf & (zz < zb - 0.5)] = 5
    # dorsal chevrons of glow on the abdomen (the abdomen "breathes light")
    for k in range(3):
        yk = abd[1] + ay_ * (0.35 - 0.3 * k)
        for dx in (-2, -1, 0, 1, 2):
            capsule(G, (ox + dx * 1.2, yk - abs(dx) * 0.9, abd[2] + az_ - 0.6 - abs(dx) * 0.3),
                    (ox + dx * 1.2, yk - abs(dx) * 0.9 + 0.1, abd[2] + az_ - 0.6 - abs(dx) * 0.3), 0.7, 4)
    # eyes: two big, six small, on the front top of the head
    e = P["eyes"]
    front = ceph + np.array([0, cy_ * 0.75, cz_ * 0.45])
    for dx, dz, rr in ((-1.1, 0.4, 1.0), (1.1, 0.4, 1.0), (-2.4, 0.9, 0.6), (2.4, 0.9, 0.6),
                       (-0.6, 1.6, 0.55), (0.6, 1.6, 0.55), (-2.9, -0.4, 0.5), (2.9, -0.4, 0.5)):
        ellip(G, front + np.array([dx * e, -abs(dx) * 0.3, dz * e]), (rr * e + 0.2,) * 3, 3)
    # chelicerae with glowing fang tips, pedipalps
    for sx in (-1, 1):
        a = ceph + np.array([sx * 1.4, cy_ * 0.85, -cz_ * 0.3])
        b = a + np.array([sx * 0.3, 1.2, -cz_ * 0.9])
        capsule(G, a, b, 1.0 * e + 0.2, 1)
        capsule(G, b, b + np.array([0, -0.4, -1.2]), 0.6, 4)
        pa = ceph + np.array([sx * cx_ * 0.6, cy_ * 0.8, -0.5])
        pk = pa + np.array([sx * 2.5, 3.0, 2.0])
        capsule(G, pa, pk, 0.8, 1); capsule(G, pk, pk + np.array([sx * 0.8, 2.6, -2.6]), 0.7, 1)
    # legs: femur yellow plates, tibia + tarsus dark, glowing knees and ankles
    r1, r2, r3 = P["lr"]
    for sx in (-1, 1):
        for li, ang in enumerate(LEG_ANG):
            a = math.radians(ang + rng.uniform(-5, 5))
            d = np.array([sx * math.sin(a), math.cos(a), 0.0])
            hip = ceph + d * np.array([cx_ * 0.8, cy_ * 0.5, 0]) + np.array([0, 0, -0.5])
            reach = R * (0.9 + 0.12 * (li in (0, 3))) * rng.uniform(0.95, 1.05)
            if curl:
                # the drop: every leg reaches forward and down to grab the target
                d2 = np.array([sx * math.sin(a) * 0.75, 0.55 + 0.25 * math.cos(a), 0.0])
                d = d * (1 - curl) + d2 * curl
            knee = hip + d * reach * 0.42 + np.array([0, 0, P["knee"] * (1 - 0.3 * curl)])
            ank = hip + d * reach * 0.82 + np.array([0, 0, P["knee"] * 0.35 - curl * zb * 0.6])
            foot = hip + d * reach + np.array([0, 0, -hip[2] + 0.5 - curl * zb * 0.4])
            foot[2] = max(foot[2], 0.5)
            capsule(G, hip, knee, r1, 2)
            capsule(G, knee, ank, r2, 1)
            capsule(G, ank, foot, r3, 1)
            ellip(G, knee, (r1 + 0.7,) * 3, 4)
            ellip(G, ank, (r2 + 0.5,) * 3, 4)
            capsule(G, foot + np.array([0, 0, 0.8]), foot, r3 * 0.8, 4)
    # spinnerets
    sp = abd + np.array([0, -ay_ * 0.95, -az_ * 0.2])
    capsule(G, sp, sp + np.array([0, -1.6, -0.6]), 1.1, 4)
    labels = {1: "shell", 2: "plate", 3: "eye", 4: "joint", 5: "under"}
    if kind == "phantom":
        G[(G == 1) | (G == 2) | (G == 5)] = 6
        labels = {6: "ghost", 3: "eye", 4: "joint"}
        surf = surface_mask(G)
        G[(G == 6) & ~surf] = 0     # hollow: phantoms are shells of light
    ob = grid_mesh(name, G, labels, PX, trans=(6,))
    return ob, float(sp[1] - W / 2) * PX, float(sp[2]) * PX


# --------------------------------------------------------------- the Matron
def matron(name, pose="folded", seed=7, cracked=1.0):
    """7-block leg span; a swollen lantern-shaped abdomen of fear glass crazed with gold lightning, broodlings moving
    inside it round a flaring core; a crown of ten eyes (eight lit, two dark); mantis scythes."""
    rng = np.random.default_rng(seed)
    R = 50
    W = 2 * R + 60
    H = 96
    G = np.zeros((W, W, H), dtype=np.int16)
    ox, oy = W / 2, W / 2 + 14
    zb = 26
    ceph = np.array([ox, oy + 8, zb + 2])
    ellip(G, ceph, (12, 14, 9), 1)
    head = ceph + np.array([0, 13, 3])
    ellip(G, head, (8, 7, 7), 1)
    surf = surface_mask(G)
    zz = np.arange(H)[None, None, :] + 0.5
    G[surf & (zz > zb + 3)] = 2
    G[surf & (zz < zb - 2)] = 5
    # crown of ten eyes on the head's top-front arc; two are dark and empty
    dark = {3, 7}
    for i in range(10):
        a = math.radians(-70 + i * (140 / 9))
        p = head + np.array([math.sin(a) * 6.5, math.cos(a) * 4.5 + 2.5, 4.5 + math.cos(a) * 1.5])
        ellip(G, p, (1.5, 1.5, 1.5), 1 if i in dark else 3)
        if i in dark:
            ellip(G, p + np.array([0, 0.6, 0.4]), (0.9, 0.9, 0.9), 0)
    for sx in (-1, 1):   # fangs
        a = head + np.array([sx * 3, 6, -3])
        capsule(G, a, a + np.array([sx * 0.5, 2, -6]), 1.8, 1)
        capsule(G, a + np.array([sx * 0.5, 2, -6]), a + np.array([sx * 0.2, 1, -9]), 1.0, 4)
    # abdomen: a lantern lying back and up from the body
    axis = np.array([0, -math.cos(math.radians(28)), math.sin(math.radians(28))])
    A0 = ceph + np.array([0, -10, 2])
    L = 58.0
    Rm = 26.0
    lo = np.maximum((np.minimum(A0, A0 + axis * L) - Rm - 4).astype(int), 0)
    hi = np.minimum((np.maximum(A0, A0 + axis * L) + Rm + 4).astype(int), G.shape)
    p = _pts(lo, hi)
    rel = [p[i] - A0[i] for i in range(3)]
    t = (rel[0] * axis[0] + rel[1] * axis[1] + rel[2] * axis[2]) / L       # 0..1 along the abdomen
    radv = [rel[i] - t * L * axis[i] for i in range(3)]
    rad = np.sqrt(sum(x * x for x in radv))
    tt = 2 * t - 1
    prof = Rm * (0.32 + 0.68 * np.sqrt(np.clip(1 - tt ** 2, 0, 1)))       # pinched ends, swollen middle
    inside = (t >= 0) & (t <= 1) & (rad <= prof)
    shell = inside & (rad > prof - 1.6)
    ang = np.arctan2(radv[0], radv[2] + 1e-9)
    sub = G[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    sub[shell] = 6
    collar = shell & ((np.abs(tt + 0.78) < 0.07) | (np.abs(tt - 0.78) < 0.07) | (np.abs(tt) < 0.025))
    ribs = shell & (np.abs(((ang + math.pi) % (math.pi / 3)) - math.pi / 6) > math.pi / 6 - 0.07) & (np.abs(tt) < 0.8)
    sub[collar | ribs] = 8
    ends = inside & (np.abs(tt) > 0.9)
    sub[ends] = 8
    # gold lightning: random walks over the glass, branching
    hits = np.argwhere(shell & (sub == 6))
    if len(hits):
        for k in range(int(9 * cracked)):
            q = hits[rng.integers(len(hits))].astype(float)
            dirv = rng.normal(size=3); dirv /= np.linalg.norm(dirv)
            for step in range(70):
                qi = np.round(q).astype(int)
                if np.all(qi >= 0) and np.all(qi < sub.shape) and sub[tuple(qi)] in (6,):
                    sub[tuple(qi)] = 7
                dirv += rng.normal(size=3) * 0.45; dirv /= np.linalg.norm(dirv)
                q = q + dirv
                # stay on the shell: pull toward the nearest shell cell
                qi = np.clip(np.round(q).astype(int), 0, np.array(sub.shape) - 1)
                if not shell[tuple(qi)]:
                    d = np.linalg.norm(hits - q, axis=1)
                    q = hits[np.argmin(d)].astype(float)
    # inside: the flaring core and broodlings moving round it
    core = A0 + axis * L * 0.5
    ellip(G, core, (5, 5, 5), 4)
    for k in range(9):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(7, 13)
        u = np.cross(axis, [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(axis, u)
        c = core + axis * rng.uniform(-12, 12) + (u * math.cos(a) + v * math.sin(a)) * r
        ellip(G, c, (2.2, 2.6, 1.8), 1, only_empty=True)
        ellip(G, c + np.array([0, 1.8, 0.8]), (0.7, 0.7, 0.7), 3)
    # spinneret
    tip = A0 + axis * (L + 1.5)
    capsule(G, tip, tip + axis * 4, 2.5, 4)
    # six walking legs (thick, yellow-plated femurs) + the two mantis scythes in front
    for sx in (-1, 1):
        for li, ang_d in enumerate((62, 100, 140)):
            a = math.radians(ang_d + rng.uniform(-4, 4))
            d = np.array([sx * math.sin(a), math.cos(a), 0.0])
            hip = ceph + d * np.array([10, 7, 0])
            knee = hip + d * R * 0.42 + np.array([0, 0, 32])
            ank = hip + d * R * 0.8 + np.array([0, 0, 10])
            foot = hip + d * R * 1.02; foot[2] = 1.0
            capsule(G, hip, knee, 3.0, 2); capsule(G, knee, ank, 2.3, 1); capsule(G, ank, foot, 1.5, 1)
            ellip(G, knee, (3.8,) * 3, 4); ellip(G, ank, (3.0,) * 3, 4)
            capsule(G, foot + np.array([0, 0, 2]), foot, 1.3, 4)
        hip = ceph + np.array([sx * 7, 11, 2])
        if pose == "folded":      # held folded like a mantis until she strikes
            knee = hip + np.array([sx * 8, 14, 30])
            tip = knee + np.array([sx * 2, 6, -30])
        else:                     # raised to strike
            knee = hip + np.array([sx * 14, 10, 40])
            tip = knee + np.array([sx * 6, 30, 6])
        capsule(G, hip, knee, 3.2, 2)
        ellip(G, knee, (4.0,) * 3, 4)
        capsule(G, knee, tip, 2.4, 1)
        # the blade's inner edge: serrations of glow
        for k in range(1, 9):
            q = knee + (tip - knee) * (k / 9)
            off = np.array([-sx * 2.2, 0, 0]) + (np.array([0, -2.5, 0]) if pose == "folded" else np.array([0, 0, -2.5]))
            capsule(G, q, q + off, 0.9, 4)
    labels = {1: "shell", 2: "plate", 3: "eye", 4: "joint", 5: "under", 6: "glass", 7: "crack", 8: "gold"}
    ob = grid_mesh(name, G, labels, PX, trans=(6,))
    return ob, (core - np.array([W / 2, W / 2, 0])) * PX


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


# =============================================================== W1a the Maw (surface, night)
def build_W1a(X):
    rng = np.random.default_rng(11)
    n = 32; depth = 16
    G = np.zeros((n, n, depth + 1), dtype=np.int16)
    xx, yy, zz = np.mgrid[0:n, 0:n, 0:depth + 1]
    G[:] = 1
    G[zz >= depth - 3] = 4
    G[zz == depth] = 3
    c = n / 2
    r = np.hypot(xx + 0.5 - c, yy + 0.5 - c)
    wob = rng.normal(size=(n, n, depth + 1)) * 0.35
    shaft = (r + wob < 2.6 + np.clip((depth - 3 - zz) * 0.35, 0, 3.2))
    G[shaft] = 0
    # spiral ledges on the shaft wall
    ang = np.arctan2(yy + 0.5 - c, xx + 0.5 - c)
    ledge_z = ((ang + math.pi) / (2 * math.pi) * 7 + 0) % 7
    for turn in range(3):
        ledge = (~(r + wob < 2.4)) & (np.abs((depth - 4 - turn * 7) - zz - ledge_z) < 0.6) & (r < 5.4) & (zz < depth - 3)
        G[ledge & shaft] = 1
    G[:, :, 0] = 1
    root = X + np.array([-c, -c, -depth])
    blocks("W1a ground", G, root, {1: "stone", 3: "grass", 4: "dirt"})
    S = Strands("W1a silk")
    # eyelash silk curling inward round the rim
    for k in range(30):
        a = k / 30 * 2 * math.pi + rng.uniform(-0.05, 0.05)
        r0 = 2.8 + rng.uniform(0, 0.6)
        pts = []
        for j in range(9):
            f = j / 8
            rr = r0 + 0.7 * math.sin(f * 2.4) - f * 1.6
            pts.append(X + np.array([math.cos(a) * rr, math.sin(a) * rr, 0.05 + math.sin(f * math.pi) * 0.9 - f * 1.1]))
        S.poly(pts, PX * 1.5)
    # web curtains across the shaft below the rim
    for k, zc in enumerate((-3.5, -7.5, -11.5)):
        S.web(X + np.array([0, 0, zc]), (0, 0, 1), 3.4 + k * 0.6, spokes=9, rings=4, rng=np.random.default_rng(20 + k))
    # dead grove with threads strung between the trunks
    trunks = []
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.3
        p = np.array([c + math.cos(a) * 10.5, c + math.sin(a) * 10.5])
        h = int(rng.integers(5, 8))
        T = np.zeros((3, 3, h + 3), dtype=np.int16)
        T[1, 1, :h] = 1
        T[0, 1, h - 2] = T[2, 1, h - 1] = T[1, 0, h - 3] = T[1, 2, h] = 1
        T[0, 1, h - 1] = T[2, 1, h] = T[1, 2, h + 1] = 1
        blocks(f"W1a tree {k}", T, X + np.array([p[0] - c - 1, p[1] - c - 1, 0]), {1: "log"})
        trunks.append(X + np.array([p[0] - c - 0.5 + 0.5, p[1] - c + 0.5 - 0.5, 0]))
    for k in range(6):
        a, b = trunks[k], trunks[(k + 1) % 6]
        for hgt in (1.5, 2.6, 3.4):
            mid = (a + b) / 2 + np.array([0, 0, hgt - 0.5])
            S.poly([a + np.array([0, 0, hgt]), mid, b + np.array([0, 0, hgt + 0.2])])
        S.seg(a + np.array([0, 0, 3.0]), X + np.array([0, 0, 0.3]))
    S.build()
    # wall-watchers across the shaft: eyes only, waiting at the edge of the light
    for k in range(5):
        a = rng.uniform(0, 2 * math.pi); zc = -rng.uniform(3, 12); rr = 4.8
        sp, _, _ = spider(f"W1a watcher {k}", "hunter", seed=40 + k)
        sp.location = X + np.array([math.cos(a) * rr, math.sin(a) * rr, zc])
        sp.rotation_euler = (math.pi / 2, 0, a + math.pi / 2)     # on the wall, belly to the stone, head down
    light("W1a moon", X + np.array([-14, -10, 22]), (0.55, 0.65, 1.0), 9000, cutoff=80, kind="AREA", size=20,
          rot=(math.radians(35), 0, math.radians(-50)))
    light("W1a shaft glow", X + np.array([0, 0, -9]), (1.0, 0.6, 0.05), 180, cutoff=14)
    cam = camera("Cam W1a Maw", X + np.array([8.0, -11.5, 7.5]), X + np.array([0, 0, -1.5]), lens=24)
    add_take("W1a", "The Maw", cam, "static",
             "the one true entrance: a 5-wide sinkhole in a dead grey grove, hard-light silk curling inward round the "
             "rim like eyelashes, web curtains down the shaft, threads strung between the dead trunks, wall-watchers "
             "lit only by their eyes")


# =============================================================== W1b the Weave Gallery
def build_W1b(X):
    nx, ny, nz = 15, 34, 18
    G, xx, yy, zz, n = cave_box(nx, ny, nz, seed=5)
    cxm = nx / 2
    width = 4.2 + 1.6 * np.sin(yy * 0.35) + n * 3.0
    ceiling = 13 + n * 4 + np.sin(yy * 0.5) * 1.2
    hollow = (np.abs(xx + 0.5 - cxm) < width + (zz - 2) * 0.12) & (zz >= 1) & (zz < ceiling) & (yy > 0) & (yy < ny - 1)
    G[hollow] = 0
    G[:, :, 0] = 1
    root = X + np.array([-cxm, -4, 0])
    blocks("W1b gallery", G, root)
    S = Strands("W1b silk")
    rng = np.random.default_rng(8)
    panes = []
    for k, yw in enumerate((9, 17, 25)):
        cpt = X + np.array([rng.uniform(-0.6, 0.6), yw - 4, 7.5])
        S.web(cpt, (0, 1, 0), 6.5, spokes=12, rings=7, rng=np.random.default_rng(30 + k), sag=0.4)
        panes.append(cpt)
    # loose strands floor to ceiling
    for k in range(18):
        x0 = rng.uniform(-4, 4); y0 = rng.uniform(9, 28)
        S.seg(X + np.array([x0, y0 - 4, 0.9]), X + np.array([x0 + rng.uniform(-1, 1), y0 - 4 + rng.uniform(-1, 1), 13]))
    # the drop: a Hunter on its thread, stopped 2 blocks above the player's head, hanging for one beat
    hp = X + np.array([0.4, 4.2, 4.0])
    hs, sy, sz = spider("W1b hunter drop", "hunter", seed=3, curl=0.8)
    hs.rotation_euler = (-math.pi / 2, 0, 0.2)
    hs.location = hp
    S.seg(hp + np.array([0, 0, 0.9]), hp + np.array([0, 0, 12]), PX)
    # a Hunter on the left wall watching, one on the right wall turning away from the light
    for k, (xw, yw, zw, rz) in enumerate(((-4.4, 7.5, 6.0, -math.pi / 2), (4.6, 13.0, 8.5, math.pi / 2))):
        w, _, _ = spider(f"W1b hunter wall {k}", "hunter", seed=12 + k)
        w.location = X + np.array([xw, yw, zw])
        w.rotation_euler = (0, -math.pi / 2 if xw < 0 else math.pi / 2, 0)
        w.rotation_euler[0] = 0.3 * (k + 1)
    S.build()
    panes_ob = Strands("W1b panes")
    pm = bpy.data.meshes.new("W1b pane mesh")
    pv, pf = [], []
    for c in panes:
        b = len(pv)
        for dx, dz in ((-5.5, -5.5), (5.5, -5.5), (5.5, 5.5), (-5.5, 5.5)):
            pv.append(tuple(c + np.array([dx, 0.02, dz])))
        pf.append((b, b + 1, b + 2, b + 3))
    pm.from_pydata(pv, [], pf); pm.materials.append(M["pane"])
    po = bpy.data.objects.new("W1b panes", pm); scene.collection.objects.link(po)
    pr, hand = player("W1b player", X + np.array([0, 0.5, 1]), rot_z=0)
    ring_light("W1b ring light", hand)
    light("W1b far fear", X + np.array([0, 26, 6]), (1.0, 0.55, 0.03), 220, cutoff=16)
    cam = camera("Cam W1b Weave Gallery", X + np.array([1.4, -1.6, 3.4]), X + np.array([0, 10, 4.8]), lens=22)
    add_take("W1b", "Weave Gallery", cam, "static",
             "a tall nave strung floor to ceiling with yellow silk like stained glass; your green ring is the only "
             "lamp and throws the spiders' leg shadows across the webs; a Hunter has dropped on its thread and hangs "
             "2 blocks over your head for one beat; two more cling to the walls")


# =============================================================== W1c the Hatchery
def egg(name, loc, rot, cracked=0, burst=False, seed=0):
    rng = np.random.default_rng(seed)
    G = np.zeros((20, 20, 26), dtype=np.int16)
    c = np.array([10, 10, 12.5])
    ellip(G, c, (8, 8, 11.5), 6, shell=1.2)
    # a curled spiderling silhouette inside
    ellip(G, c + np.array([0, 1, -1]), (3.2, 3.6, 3.0), 1, only_empty=True)
    ellip(G, c + np.array([0, -2.5, 1.5]), (3.6, 3.6, 4.0), 1, only_empty=True)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        capsule(G, c + np.array([0, 0.5, -1]), c + np.array([math.cos(a) * 5, math.sin(a) * 4, 1.5 + math.sin(a * 2) * 2]),
                0.8, 1, only_empty=True)
    ellip(G, c + np.array([0, 4, 0]), (0.8,) * 3, 3)
    ellip(G, c + np.array([0, -1, 0]), (1.6,) * 3, 4)
    shell = (G == 6)
    hits = np.argwhere(shell)
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
        top = (G[:, :, 16] == 6)
        G[:, :, 16][top & (np.random.default_rng(seed).random(top.shape) < 0.5)] = 7
        G[G == 1] = 0
    ob = grid_mesh(name, G, {1: "shell", 3: "eye", 4: "joint", 6: "glass", 7: "crack"}, PX, trans=(6,))
    ob.location = loc; ob.rotation_euler = rot
    return ob


def build_W1c(X):
    nx, ny, nz = 26, 14, 8
    G, xx, yy, zz, n = cave_box(nx, ny, nz, seed=9)
    hollow = (xx > 0) & (xx < nx - 1) & (yy < 9 + n * 2) & (zz >= 1) & (zz < 5 + n * 1.5)
    G[hollow] = 0
    G[:, :2, 1:] = 0               # cutaway: no front wall
    root = X + np.array([-nx / 2, -2, 0])
    rng = np.random.default_rng(4)
    # honeycomb niches in the back wall
    niches = []
    for row, zc in enumerate((1.6, 3.2)):
        for k in range(10):
            xc = 2.5 + k * 2.1 + (row % 2) * 1.05
            if xc > nx - 2:
                continue
            yb = int(np.argmax(G[int(xc), 1:, int(zc)] > 0)) + 1
            G[int(xc) - 0:int(xc) + 1, yb:yb + 1, int(zc):int(zc) + 1] = 0
            niches.append((xc, yb, zc))
    blocks("W1c hatchery", G, root)
    S = Strands("W1c silk")
    for i, (xc, yb, zc) in enumerate(niches):
        loc = root + np.array([xc + 0.5, yb + 0.15, zc - 0.2])
        burst = i == 5
        egg(f"W1c egg {i}", loc, (math.radians(-12), rng.uniform(-0.2, 0.2), 0),
            cracked=(0 if i % 3 else 3) + (2 if i in (4, 6) else 0), burst=burst, seed=i)
        S.seg(loc + np.array([0, 0, 1.2]), loc + np.array([rng.uniform(-0.6, 0.6), 0.4, 2.0]))
        if burst:
            light("W1c burst glow", loc + np.array([0, -0.4, 1.0]), (1.0, 0.55, 0.03), 40, cutoff=6)
            for b in range(7):
                bs, _, _ = spider(f"W1c broodling {b}", "broodling", seed=60 + b)
                a = rng.uniform(-1.3, 1.3)
                bs.location = loc + np.array([math.sin(a) * rng.uniform(0.6, 2.4), -rng.uniform(0.5, 2.8), -zc + 1.0])
                bs.rotation_euler[2] = math.pi + a + rng.uniform(-0.5, 0.5)
    for k in range(14):
        a = root + np.array([rng.uniform(1, nx - 1), rng.uniform(5, 8), 1.0])
        S.seg(a, a + np.array([rng.uniform(-2, 2), rng.uniform(-1, 1), 3.5]))
    S.build()
    pr, hand = player("W1c player", X + np.array([-8.5, 1.2, 1]), rot_z=-0.9)
    ring_light("W1c ring light", hand, energy=500)
    light("W1c eggs", X + np.array([3, 3.5, 3.4]), (1.0, 0.6, 0.05), 60, cutoff=10)
    cam = camera("Cam W1c Hatchery", X + np.array([1.5, -5.5, 2.6]), X + np.array([0, 5.5, 2.2]), lens=22)
    add_take("W1c", "Hatchery", cam, "static",
             "a low room, ceiling 4 blocks; the walls honeycombed with translucent yellow egg sacs, a curled "
             "spiderling in each; your Dread has cracked the nearest (gold-crack light leaking first) and one has "
             "burst, broodlings pouring out toward your green light")


# =============================================================== W1d four corps counters
def build_W1d(X):
    nx, ny, nz = 44, 12, 9
    G, xx, yy, zz, n = cave_box(nx, ny, nz, seed=13)
    G[(xx > 0) & (xx < nx - 1) & (yy < 9 + n * 2) & (zz >= 1) & (zz < 7 + n * 2)] = 0
    G[:, :2, 1:] = 0               # cutaway: no front wall
    for k in (11, 22, 33):     # stone ribs between the four bays
        G[k - 1:k + 1, 5:, :] = 1
    root = X + np.array([-nx / 2, -3, 0])
    blocks("W1d threshold", G, root)
    S = Strands("W1d silk")
    rng = np.random.default_rng(21)
    bays = [-16.5, -5.5, 5.5, 16.5]
    # each bay: webs behind, a player, their corps' counter
    for bi, bx in enumerate(bays):
        c = X + np.array([bx, 4.2, 3.5])
        S.web(c, (0, 1, 0), 3.6, spokes=9, rings=5, rng=np.random.default_rng(70 + bi))
    S.build()
    # GREEN: the Will Flare, a green sphere pulsing out, webs burning to green ash
    pr, hand = player("W1d green", X + np.array([bays[0], 1.2, 1]), raise_arm=True)
    ring_light("W1d green light", hand, energy=1100)
    F = np.zeros((96, 96, 96), dtype=np.int16)
    ellip(F, (48, 48, 48), (47, 47, 47), 1, shell=1.0)
    fo = grid_mesh("W1d will flare", F, {1: "flare"}, PX)
    fo.location = X + np.array([bays[0], 1.2, 0.2])
    A = Strands("W1d ash")
    for k in range(80):
        p = X + np.array([bays[0] + rng.uniform(-3.5, 3.5), 4.0 + rng.uniform(-0.3, 0.3), rng.uniform(0.3, 6.5)])
        A.seg(p, p + np.array([0, 0, -PX * 2]), PX * 1.5)
    A.build("ash")
    # RED: rage; burns while attacking, can't flare. Ember fists and slash marks of red light
    pr, hand = player("W1d red", X + np.array([bays[1], 1.2, 1]), ring="red", raise_arm=False)
    ring_light("W1d red light", hand, color=(1.0, 0.05, 0.03), energy=500)
    Rr = Strands("W1d rage")
    for k in range(3):
        a = X + np.array([bays[1] - 1.8 + k * 1.2, 2.6, 3.8])
        Rr.poly([a, a + np.array([0.6, 0.05, -1.0]), a + np.array([1.0, 0.1, -2.2])], PX * 2.5)
    for k in range(30):
        p = X + np.array([bays[1] + rng.uniform(-1.4, 1.4), 1.2 + rng.uniform(-0.8, 1.2), rng.uniform(1.0, 3.2)])
        Rr.seg(p, p + np.array([0, 0, PX * 1.5]), PX * 1.5)
    Rr.build("red")
    sp, _, _ = spider("W1d red hunter", "hunter", seed=81)
    sp.location = X + np.array([bays[1] + 0.8, 3.2, 1]); sp.rotation_euler = (0.25, 0, math.pi + 0.3)
    # BLUE: hope; a slow passive drain. A calm halo overhead, the silk near it greying
    pr, hand = player("W1d blue", X + np.array([bays[2], 1.2, 1]), ring="blue", raise_arm=False)
    ring_light("W1d blue light", hand, color=(0.1, 0.4, 1.0), energy=500)
    Hh = np.zeros((60, 60, 2), dtype=np.int16)
    xh, yh = np.mgrid[0:60, 0:60]
    rr = np.hypot(xh - 29.5, yh - 29.5)
    Hh[(rr > 25) & (rr < 28), 0] = 1
    Hh[(rr > 17) & (rr < 18.4) & ((np.arctan2(yh - 29.5, xh - 29.5) * 4) % 2 < 1), 1] = 1
    ho = grid_mesh("W1d hope halo", Hh, {1: "blue"}, PX); ho.location = X + np.array([bays[2], 1.2, 3.3])
    light("W1d blue halo light", X + np.array([bays[2], 1.2, 3.6]), (0.1, 0.4, 1.0), 300, cutoff=8)
    # YELLOW: the brood is wary of you; broodlings stopped in a half ring, hesitating
    pr, hand = player("W1d yellow", X + np.array([bays[3], 1.0, 1]), ring="ylring", raise_arm=False)
    ring_light("W1d yellow light", hand, color=(1.0, 0.62, 0.04), energy=420)
    for k in range(6):
        a = math.radians(-70 + k * 28)
        b, _, _ = spider(f"W1d wary {k}", "broodling", seed=90 + k)
        b.location = X + np.array([bays[3] + math.sin(a) * 2.6, 1.0 + math.cos(a) * 2.6, 1])
        b.rotation_euler[2] = math.pi + a + 0.0
    cam = camera("Cam W1d Corps counters", X + np.array([0, -27, 7.0]), X + np.array([0, 2.5, 3.0]), lens=24)
    add_take("W1d", "Four corps counters", cam, "static",
             "any corps can enter; four bays at the threshold, each player's counter to Dread: GREEN Will Flare (a "
             "green sphere, webs burning to green ash), RED rage (ember fists, slashes; Dread rises slower while "
             "attacking, no flare), BLUE hope (a calm halo, a slow passive Dread drain), YELLOW kin (the brood "
             "hesitates in a half ring)")


# =============================================================== W2 fear spiders (turntables on plinths)
def plinth(name, X, r=2.2):
    n = int(r * 2 * 4)
    G = np.zeros((n, n, 2), dtype=np.int16)
    xg, yg = np.mgrid[0:n, 0:n]
    rr = np.hypot(xg + 0.5 - n / 2, yg + 0.5 - n / 2)
    G[rr < n / 2, 0] = 1
    G[(rr < n / 2 - 1.5), 1] = 1
    o = grid_mesh(name, G, {1: "stone"}, 0.25, loc=X + np.array([0, 0, -0.5]))
    return o


def stage_lights(code, X, dist=6.0, key=900):
    light(f"{code} key", X + np.array([-dist * 0.7, -dist, dist * 0.9]), (1.0, 0.95, 0.85), key, cutoff=30,
          kind="AREA", size=4, rot=(math.radians(50), 0, math.radians(-35)))
    light(f"{code} rim", X + np.array([dist * 0.8, dist * 0.7, dist * 0.5]), (0.1, 1.0, 0.2), key * 0.5, cutoff=30,
          kind="AREA", size=3, rot=(math.radians(-60), 0, math.radians(140)))


def build_W2a(X):
    plinth("W2a plinth", X, 2.0)
    root = empty("W2a turn", X); spin(root)
    rng = np.random.default_rng(31)
    # an empty burst egg in the middle, broodlings streaming off it in step-step-freeze
    e = egg("W2a egg", (0, 0, 0), (0, 0, 0), cracked=3, burst=True, seed=5); parent(e, root)
    for k in range(9):
        b, _, _ = spider(f"W2a broodling {k}", "broodling", seed=100 + k)
        a = k / 9 * 2 * math.pi + rng.uniform(-0.2, 0.2); r = rng.uniform(0.7, 1.7)
        b.location = (math.cos(a) * r, math.sin(a) * r, 0)
        b.rotation_euler[2] = a - math.pi / 2 + rng.uniform(-0.6, 0.6)
        parent(b, root)
    stage_lights("W2a", X, 4.0, 400)
    cam = camera("Cam W2a Broodlings", X + np.array([0, -5.6, 3.4]), X + np.array([0, 0, 0.2]), lens=40)
    add_take("W2a", "Broodlings", cam, "turntable",
             "0.5x spiders that pour out of the eggs in 6-12s: bright plates, oversized eyes, fast twitchy bursts "
             "then freeze; weak alone, they raise Dread fast")


def build_W2b(X):
    plinth("W2b plinth", X, 2.6)
    root = empty("W2b turn", X); spin(root)
    h, _, _ = spider("W2b hunter", "hunter", seed=3); parent(h, root)
    stage_lights("W2b", X, 5.0, 700)
    cam = camera("Cam W2b Hunter", X + np.array([-3.4, -4.4, 3.2]), X + np.array([0, 0, 0.5]), lens=40)
    add_take("W2b", "Hunter", cam, "turntable",
             "the main fighter at 1.6x (2.2 blocks across): black core under yellow hard-light plates with dark "
             "grooves, glowing knees and ankles, eight eyes, chevrons breathing light on the abdomen")


def build_W2c(X):
    plinth("W2c plinth", X, 2.6)
    root = empty("W2c turn", X); spin(root)
    w, sy, sz = spider("W2c weaver", "weaver", seed=5, curl=0.9)
    w.rotation_euler = (-math.pi / 2, 0, 0)
    w.location = (0, 0, 2.1)
    parent(w, root)
    S = Strands("W2c thread")
    S.seg((0, 0, 2.1 + 1.1), (0, 0, 9.0), PX)
    # the strand it is paying out under itself (spits silk that slows you)
    S.poly([(0, 0.25, 1.4), (0.3, 0.6, 0.8), (0.8, 1.2, 0.05)], PX)
    th = S.build(); parent(th, root)
    stage_lights("W2c", X, 5.5, 700)
    cam = camera("Cam W2c Weaver", X + np.array([0, -6.2, 2.2]), X + np.array([0, 0, 1.6]), lens=38)
    add_take("W2c", "Weaver on a drop thread", cam, "turntable",
             "the support spider at 1.3x with long thin legs; shown the way the trial uses it (a drop, not ceiling "
             "walking): hanging on its own hard-light thread, legs reaching down, paying out a slowing strand")


def build_W2d(X):
    plinth("W2d plinth", X, 2.2)
    root = empty("W2d turn", X); spin(root)
    p, _, _ = spider("W2d phantom", "phantom", seed=9); parent(p, root)
    rng = np.random.default_rng(91)
    S = Strands("W2d static")
    for k in range(140):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 1.6) ** 1.2; z = rng.uniform(0.1, 2.6) ** 1.3
        q = np.array([math.cos(a) * r, math.sin(a) * r, z])
        S.seg(q, q + rng.normal(size=3) * PX, PX * rng.choice([0.6, 1.0]))
    st = S.build("static"); parent(st, root)
    light("W2d inner", X + np.array([0, 0, 0.6]), (1.0, 0.6, 0.05), 60, cutoff=6)
    stage_lights("W2d", X, 4.5, 250)
    cam = camera("Cam W2d Dread Phantom", X + np.array([0, -4.4, 2.4]), X + np.array([0, 0, 0.6]), lens=40)
    add_take("W2d", "Dread Phantom", cam, "turntable",
             "J's 'yellow Ender spiders teleporting in from above': a hollow, see-through spider of light blinking "
             "in behind you in a puff of yellow static; spawns only over Dread 60")


# =============================================================== W3 the Matron
def build_W3a(X):
    plinth("W3a plinth", X, 6.0)
    root = empty("W3a turn", X); spin(root)
    m, core = matron("W3a matron", "folded"); parent(m, root)
    lc = light("W3a core light", tuple(core), (1.0, 0.58, 0.03), 260, cutoff=12); parent(lc, root)
    lc.location = tuple(core)
    stage_lights("W3a", X, 11.0, 3500)
    cam = camera("Cam W3a Matron", X + np.array([-9.0, -10.0, 7.0]), X + np.array([0, 0, 2.2]), lens=32)
    add_take("W3a", "The Matron", cam, "turntable",
             "a 7-block leg span, body the size of a horse; a swollen lantern-shaped abdomen of fear glass in a "
             "polished gold frame, crazed with gold lightning, broodlings moving inside round a flaring core; a crown "
             "of ten eyes (eight lit, two dark and empty); mantis scythes held folded")


def build_W3b(X):
    rng = np.random.default_rng(55)
    R = 15
    n = 2 * R + 4
    G = np.zeros((n, n, 3), dtype=np.int16)
    xg, yg = np.mgrid[0:n, 0:n]
    rr = np.hypot(xg + 0.5 - n / 2, yg + 0.5 - n / 2)
    G[rr < R + 1.5, 0] = 1
    G[(rr > R - 0.5) & (rr < R + 1.5), 1:] = 1
    blocks("W3b floor", G, X + np.array([-n / 2, -n / 2, -1]))
    S = Strands("W3b dome")
    apex = X + np.array([0, 0, 17])
    pillars = []
    for k in range(8):
        a = k / 8 * 2 * math.pi + math.pi / 8
        p = X + np.array([math.cos(a) * (R - 2), math.sin(a) * (R - 2), 0])
        pillars.append((p, a))
        P = np.zeros((10, 10, 64), dtype=np.int16)
        for j in range(5):
            capsule(P, (5 + rng.uniform(-1, 1), 5 + rng.uniform(-1, 1), 0),
                    (5 + rng.uniform(-2, 2), 5 + rng.uniform(-2, 2), 64), 2.4 + rng.uniform(0, 0.8), 1)
        # an old cocoon fused into the pillar (a shape you can just make out)
        ellip(P, (5, 3.0, 18 + k % 3 * 6), (3.6, 3.0, 9), 2)
        po = grid_mesh(f"W3b pillar {k}", P, {1: "cocoon", 2: "cocoon"}, 0.25)
        po.location = p; po.rotation_euler[2] = a
        top = p + np.array([0, 0, 15.5])
        # the sagging dome web: from the apex to each pillar top, then rings between
        mid = (apex + top) / 2 + np.array([0, 0, -2.5])
        S.poly([apex, mid, top], PX * 3)
    for ring_k in range(1, 6):
        f = ring_k / 6
        pts = []
        for k in range(9):
            p, a = pillars[k % 8]
            top = p + np.array([0, 0, 15.5])
            mid = apex * (1 - f) + top * f + np.array([0, 0, -2.5 * math.sin(f * math.pi)])
            pts.append(mid)
        S.poly(pts, PX * 2)
    # burnt sections hang in shreds (where Will Flares have burned the dome)
    for k in range(20):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(3, 12)
        q = X + np.array([math.cos(a) * r, math.sin(a) * r, 16 - r * 0.6])
        S.seg(q, q + np.array([0, 0, -rng.uniform(1, 4)]), PX)
    S.build()
    # the heart-crystal, half buried in the floor
    C = np.zeros((40, 40, 56), dtype=np.int16)
    for k in range(7):
        a = k / 7 * 2 * math.pi
        tip = np.array([20 + math.cos(a) * 9 * (k > 0), 20 + math.sin(a) * 9 * (k > 0), 52 - 18 * (k > 0)])
        capsule(C, (20, 20, 0), tip, 6 - 2 * (k > 0), 1)
    co = grid_mesh("W3b heart-crystal", C, {1: "crystal"}, PX * 1.5)
    co.location = X + np.array([0, 0, -0.4])
    light("W3b crystal light", X + np.array([0, 0, 2.2]), (1.0, 0.58, 0.03), 900, cutoff=24)
    # phase 2: she has come down, scythes raised to strike
    m, core = matron("W3b matron", "raised", seed=8)
    m.location = X + np.array([3.5, 5.5, 0]); m.rotation_euler[2] = math.radians(200)
    pr, hand = player("W3b player", X + np.array([-3.5, -7.5, 0]), rot_z=math.radians(-25))
    ring_light("W3b ring light", hand, energy=1200)
    for k in range(4):
        b, _, _ = spider(f"W3b broodling {k}", "broodling", seed=140 + k)
        b.location = X + np.array([rng.uniform(-6, 6), rng.uniform(-3, 4), 0]); b.rotation_euler[2] = rng.uniform(0, 6)
    cam = camera("Cam W3b Brood Heart", X + np.array([-11.0, -9.0, 4.0]), X + np.array([2.5, 4.0, 6.0]), lens=18)
    add_take("W3b", "Brood Heart arena", cam, "static",
             "the boss dome, 30 blocks across: a sagging web ceiling half burnt to shreds, eight pillars of fused silk "
             "with old cocoons in them, the yellow heart-crystal half buried in the floor; phase 2, she has come "
             "down and raises her scythes at your green light")


def build_W3c(X):
    G = np.zeros((40, 40, 1), dtype=np.int16); G[:] = 1
    blocks("W3c floor", G, X + np.array([-20, -20, -1]))
    m, core = matron("W3c matron", "raised", seed=9, cracked=2.2)
    m.location = X + np.array([0, 4, 0]); m.rotation_euler[2] = math.radians(185)
    light("W3c abdomen glow", X + np.array([0, 4, 0]) + np.array([-core[0], -core[1], core[2]]),
          (1.0, 0.55, 0.03), 300, cutoff=12)
    # the will to relight: you hold use for 3 s and the ring reignites by force in a green burst
    pr, hand = player("W3c player", X + np.array([0, -4.5, 0]), rot_z=0)
    ring_light("W3c reignite", hand, energy=650)
    B = Strands("W3c burst")
    rng = np.random.default_rng(66)
    for k in range(90):
        d = rng.normal(size=3); d /= np.linalg.norm(d)
        c = X + np.array([0, -4.5, 0]) + np.array([0.37, 0.0, 2.25])
        r0 = rng.uniform(0.15, 0.35)
        B.seg(c + d * r0, c + d * (r0 + rng.uniform(0.15, 0.5)), PX)
    B.build("ash")
    cam = camera("Cam W3c Lights out", X + np.array([-3.2, -9.5, 2.2]), X + np.array([0, 2, 2.8]), lens=26)
    add_take("W3c", "Lights out", cam, "static",
             "phase 3: her scream puts out every light; all you see is her cracked glowing abdomen, her eyes and the "
             "first green burst of your ring reigniting by force, the moment her shell opens where the gold "
             "lightning is")


BUILDERS = [build_W1a, build_W1b, build_W1c, build_W1d, build_W2a, build_W2b, build_W2c, build_W2d,
            build_W3a, build_W3b, build_W3c]
for i, b in enumerate(BUILDERS):
    b(np.array([i * GAP, 0.0, 0.0]))

scene.camera = bpy.data.objects[TAKES[0][2]]
scene["dw_takes"] = repr(TAKES)
print(f"[{PASS}] built {len(TAKES)} takes, {len(scene.objects)} objects")
