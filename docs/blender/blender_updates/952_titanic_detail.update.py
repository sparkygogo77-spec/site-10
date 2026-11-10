# Pass 952: the Titanic construct at real size, with detail (chat "titanic", 2026-11-09). Follows 951.
# J on 951: "now add detail to the 1 to 1 one". Same ship, same size (1 block = 1 metre: 269 x 28 x 53, 63 to the
# mast tops); three ways to carry more detail, each built differently:
#   D1 Half-block : the whole ship re-cut at 2 voxels a block (a smoother bow, stern and funnels) + all the detail.
#   D2 Quarter    : the whole ship re-cut at 4 voxels a block (the finest hull, round funnels, thin blades) + detail.
#   D3 Overlay    : 951's 1-block ship unchanged, with the detail as a thin quarter-block layer on top (cheapest in game).
#   D4 Textured   : D1's ship wearing J's own construct textures, polished for the ship by tools/titanic_textures.py
#                   (slower, smoother, no pale mint, 12% darker): BR1 bricks on the hull, W1 weave on the decks and
#                   cabins, H1 hex on the funnels. 32 px a block, fixed in the world, playing at frametime 5.
#                   J: "add and correct and polish some of my existing textures and display it on one of them".
#                   Textures: LanternLive\constructs\titanic_textures\construct_<br1|w1|h1>_green_ship.png.
# The detail, on all three: deck railings with posts, mast stays and shrouds, the aerial between the masts, funnel stays
# and steam pipes, lifeboat davits, cargo cranes, the docking bridge on the poop, ventilators, a skylight dome, bow
# anchors, a waterline band and a thin yellow sheer line, portholes and rows of lit cabin windows, bridge windows.
# Forming: F2 circles from pass 951 (rings from random centres), frames 1-80, hold to 110. SEED picks the pattern.
# Cameras are numbered and carry the option's name (J: "make the cameras named accordingly to each option"):
#   "1 D1 Half-block - bow quarter", "2 D1 Half-block - off the bow", "3 D1 Half-block - boat deck",
#   "4 D1 Half-block - funnels", "5 D1 Half-block - stern"; 6-10 D2 Quarter-block, 11-15 D3 Overlay, 16-20 D4 Textured.
# Builds LanternLive\constructs\952_titanic_detail.blend.
SCENE_NAME = "Titanic Detail"
OUT_REL = "constructs/952_titanic_detail.blend"
SEED = 1912
import math, os
import bpy
import numpy as np

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
FORM_END, HOLD_END = 80, 110
scene.frame_start, scene.frame_end = 1, HOLD_END


def link(o):
    col.objects.link(o)
    return o


# ------------------------------------------------------------------ the ship, in metres (x from the stern, z from the keel)
L, BEAM = 269.0, 28.2
HULL, KEEL, SUPER, FUNNEL, FTOP, MAST, BOAT, DECK = range(1, 9)
FUNNELS = (113.0, 137.0, 161.0, 185.0)          # centres, stern to bow
BOATS = (62, 72, 82, 92, 164, 174, 184, 194)    # lifeboat sterns, each side


def half_beam(x, z):
    """Half breadth of the hull at x (from the stern) and height z."""
    b = np.full_like(x, BEAM / 2)
    fwd = L - x                                  # distance from the bow
    b = np.where(fwd < 62, (BEAM / 2) * np.clip(fwd / 62, 0, 1) ** 0.62, b)
    b = np.where(x < 52, (BEAM / 2) * (1 - (1 - np.clip(x / 52, 0, 1)) ** 2.2), b)
    # finer lines low down toward both ends; a rounded bilge amidships
    ends = np.clip(np.maximum((62 - fwd) / 62, (52 - x) / 52), 0, 1)
    low = np.clip(z / 13.0, 0, 1)
    b = b * (1 - ends * 0.75 * (1 - low) ** 1.3)
    bilge = np.clip((2.5 - z) / 2.5, 0, 1)
    return b - 2.5 * (1 - np.sqrt(np.clip(1 - bilge ** 2, 0, 1)))


def ship_roles(s):
    """Role grid for the ship at s voxels per metre. Axes: x along, y across, z up."""
    nx, ny, nz = int(math.ceil(L * s)) + 1, int(math.ceil(BEAM * s)) + 2, int(math.ceil(64 * s)) + 1
    X, Y, Z = np.meshgrid(((np.arange(nx) + 0.5) / s).astype(np.float32),
                          ((np.arange(ny) + 0.5) / s - (ny / s) / 2).astype(np.float32),
                          ((np.arange(nz) + 0.5) / s).astype(np.float32), indexing="ij", sparse=True)
    A = np.abs(Y)
    role = np.zeros((nx, ny, nz), np.uint8)
    hb = half_beam(X, Z)
    stem = L - (19 - Z) * 0.10 - 0.5             # a near-plumb stem
    counter = np.where(X < 13, 9.0 + (13 - X) * 0.55, 0.0)   # the stern overhang rises from the rudder post
    top = np.where((X > L - 39) | (X < 32), 22.0, 19.0)      # forecastle and poop one deck higher than the wells
    hull = (A <= hb) & (Z <= top) & (X <= stem) & (Z >= counter) & (X >= 0.2)
    role[np.broadcast_to(hull, role.shape)] = HULL
    role[hull & (Z < 10.5)] = KEEL               # below the waterline
    role[hull & (Z > top - 1.0 / s) & (A < hb - 1.0 / s)] = DECK

    def box(x0, x1, hw, z0, z1, r=SUPER):
        m = (X >= x0) & (X < x1) & (A <= np.minimum(hw, hb + 0 * A if z0 < 22 else hw)) & (Z >= z0) & (Z < z1)
        role[m & (role == 0)] = r
        return m

    box(47, L - 54, 14.1, 19, 22)                # B deck, flush with the hull side
    a = box(55, L - 62, 13.2, 22, 25)            # A deck with the open promenade
    prom = a & (A > 12.0) & (Z > 22.9) & (Z < 24.6) & ((np.floor(X * s) % 3) != 0) & (X > 60) & (X < L - 70)
    role[prom] = 0
    box(62, L - 66, 12.0, 25, 28)                # boat deck house
    role[(X >= 62) & (X < L - 66) & (A <= 13.2) & (Z >= 27.2) & (Z < 28) & (role == 0)] = DECK
    box(L - 74, L - 66, 10.0, 28, 31)            # wheelhouse and bridge
    box(L - 92, L - 74, 6.0, 28, 30.5)           # officers' quarters
    for fx in FUNNELS:
        box(fx - 9, fx + 7, 5.5, 28, 30)         # the casing round each funnel
        cx = fx - (Z - 28) / 6.0                 # raked aft
        f = (((X - cx) / 3.9) ** 2 + (Y / 3.1) ** 2 <= 1) & (Z >= 28) & (Z < 52.5)
        role[f] = FUNNEL
        role[f & (Z > 46.5)] = FTOP
        role[(((X - cx) / 2.4) ** 2 + (Y / 1.7) ** 2 <= 1) & (Z >= 50) & (Z < 52.5)] = 0   # open tops
    box(70, 100, 6.5, 28, 30)                    # aft deck houses
    for bx in BOATS:                             # lifeboats on the boat deck edge
        role[(X >= bx) & (X < bx + 9) & (A > 10.3) & (A <= 13.2) & (Z >= 28) & (Z < 30) & (role == 0)] = BOAT
    w = max(0.5, 0.5 / s) if s >= 1 else 0.5 / s  # masts: one voxel thick at any scale
    for mx, z0, z1 in ((L - 47, 19, 63.0), (58, 22, 61.0)):
        cx = mx - (Z - z0) / 11.0
        role[(np.abs(X - cx) <= w) & (A <= w) & (Z >= z0) & (Z < z1)] = MAST
    role[(np.abs(X - (L - 47 - 2.0)) <= 1.2) & (A <= 1.2) & (Z >= 40) & (Z < 42)] = MAST     # crow's nest
    for hx0, hx1 in ((L - 53, L - 46), (38, 45), (L - 30, L - 24)):                           # cargo hatches
        role[(X >= hx0) & (X < hx1) & (A <= 3.5) & (Z >= np.where(hx0 > L - 39, 22.0, 19.0)) &
             (Z < np.where(hx0 > L - 39, 23.0, 20.0)) & (role == 0)] = SUPER
    role[(X >= 5.5) & (X < 12.5) & (A <= w) & (Z >= 1.5) & (Z < 10.5)] = KEEL                # rudder
    for px, py, pz, pr in ((14.5, 0, 4.0, 2.6), (22.0, 8.5, 4.5, 3.4), (22.0, -8.5, 4.5, 3.4)):   # propellers
        d = np.hypot(Y - py, Z - pz)
        ang = np.arctan2(Z - pz, Y - py)
        role[(np.abs(X - px) <= w) & (d <= pr) & ((np.cos(3 * ang) > 0.2) | (d < 1.0))] = KEEL
    return role


def shell_of(solid):
    p = np.pad(solid, 1)
    inner = (p[2:, 1:-1, 1:-1] & p[:-2, 1:-1, 1:-1] & p[1:-1, 2:, 1:-1] & p[1:-1, :-2, 1:-1] &
             p[1:-1, 1:-1, 2:] & p[1:-1, 1:-1, :-2])
    return solid & ~inner


def dilate(m):
    p = np.pad(m, 1)
    out = np.zeros_like(m)
    n = m.shape
    for dx in (0, 1, 2):
        for dy in (0, 1, 2):
            for dz in (0, 1, 2):
                out |= p[dx:dx + n[0], dy:dy + n[1], dz:dz + n[2]]
    return out


def grow(shell, start):
    """Spread over the shell from every voxel with start >= 0 (its own starting step). Returns the arrival step."""
    T = np.full(shell.shape, -1, np.int32)
    reached = np.zeros(shell.shape, bool)
    last = int(start.max())
    k = 0
    left = int(shell.sum())
    while left > 0 and k < 4000:
        new = (start == k) & shell & ~reached
        if reached.any():
            new |= dilate(reached) & shell & ~reached
        if new.any():
            T[new] = k
            reached |= new
            left -= int(new.sum())
        elif k > last:
            T[shell & ~reached] = k              # cut-off islands (a propeller blade) land with the last step
            break
        k += 1
    return T


def pick(rng, pts, n, min_gap):
    """n random shell points, none closer than min_gap to another."""
    out = []
    for i in rng.permutation(len(pts)):
        p = pts[i]
        if all(np.abs(p - q).max() >= min_gap or np.linalg.norm(p - q) >= min_gap for q in out):
            out.append(p)
            if len(out) == n:
                break
    return np.array(out)


def web_lines(rng, shell, seeds, links=2):
    """Jagged lines along the shell from each seed toward its nearest seeds. Returns [(voxel, step)]."""
    out = {}
    n = shell.shape
    offs = np.array([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)])
    for i, p in enumerate(seeds):
        d = np.linalg.norm(seeds - p, axis=1)
        for j in np.argsort(d)[1:1 + links]:
            cur, tgt, seen = p.copy(), seeds[j], set()
            for step in range(600):
                out.setdefault(tuple(cur), step)
                seen.add(tuple(cur))
                if np.abs(cur - tgt).max() <= 1:
                    break
                c = cur + offs
                ok = ((c >= 0) & (c < n)).all(1)
                c = c[ok]
                c = c[shell[c[:, 0], c[:, 1], c[:, 2]]]
                c = np.array([q for q in c if tuple(q) not in seen])
                if not len(c):
                    break
                cost = np.linalg.norm(c - tgt, axis=1) + rng.random(len(c)) * 2.2      # the jitter makes it jagged
                cur = c[int(np.argmin(cost))]
    return out


def arrive_for(kind, shell, seed):
    """Per-voxel arrival, 0-1, for one forming pattern."""
    rng = np.random.default_rng(seed)
    pts = np.argwhere(shell)
    span = max(shell.shape)
    if kind == "B0":
        T = np.broadcast_to(np.arange(shell.shape[2])[None, None, :], shell.shape).astype(np.float32)
    elif kind == "F1":
        seeds = pick(rng, pts, 40, span * 0.07)
        start = np.full(shell.shape, -1, np.int32)
        for p in seeds:
            start[tuple(p)] = int(rng.integers(0, max(2, span // 9)))
        T = grow(shell, start).astype(np.float32)
    elif kind in ("F2", "F4"):
        cents = pick(rng, pts, 26 if kind == "F2" else 13, span * 0.09)
        delay = rng.random(len(cents)) * span * 0.10
        band = max(3.0, span / 55.0)
        T = np.full(shell.shape, 1e9, np.float32)
        ii, jj, kk = np.indices(shell.shape, sparse=True)
        for c, dl in zip(cents, delay):
            d = np.sqrt(((ii - c[0]) ** 2 + (jj - c[1]) ** 2 + (kk - c[2]) ** 2).astype(np.float32))
            fill_late = (np.floor(d / band) % 2) * band * 2.2          # every other band waits: rings first
            T = np.minimum(T, dl + d + fill_late)
        if kind == "F4":
            seeds = np.vstack([cents, pick(rng, pts, 22, span * 0.06)])
            start = np.full(shell.shape, -1, np.int32)
            for v, st in web_lines(rng, shell, seeds).items():
                start[v] = st // 3
            W = grow(shell, start).astype(np.float32) * 1.6
            T = np.minimum(T, W)
    elif kind == "F3":
        seeds = pick(rng, pts, 34, span * 0.07)
        start = np.full(shell.shape, -1, np.int32)
        for v, st in web_lines(rng, shell, seeds, links=3).items():
            start[v] = st // 3                                         # lines run 3 voxels a step, plating 1
        T = grow(shell, start).astype(np.float32)
    else:
        return np.full(shell.shape, -1.0, np.float32)
    lo, hi = float(T[shell].min()), float(T[shell].max())
    lin = np.clip((T - lo) / max(1e-6, hi - lo), 0, 1)
    # even pacing: mostly by rank (the same share of the ship lands every tick), so no pattern ends on a long tail
    vals = np.sort(T[shell])
    rank = np.searchsorted(vals, T, side="left").astype(np.float32) / max(1, len(vals))
    return np.clip(0.3 * lin + 0.7 * rank, 0, 1) * 0.94               # everything is in by form = 0.94


# colours: linear, saturated greens, never white (emission stays under 1.5)
PAL = {HULL: (0.020, 0.300, 0.085), KEEL: (0.008, 0.120, 0.045), SUPER: (0.060, 0.620, 0.160),
       FUNNEL: (0.300, 0.720, 0.050), FTOP: (0.006, 0.070, 0.030), MAST: (0.100, 0.800, 0.200),
       BOAT: (0.140, 0.900, 0.260), DECK: (0.030, 0.400, 0.110)}
DIRS = (((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))), ((-1, 0, 0), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0))),
        ((0, 1, 0), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0))), ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))),
        ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))), ((0, 0, -1), ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0))))


def ship_mesh(name, role, arrive, s, origin, mat):
    """One mesh of the ship's outside faces, with per-face 'arrive', 'glow' and colour."""
    solid = role > 0
    p = np.pad(solid, 1)
    n = solid.shape
    verts, cols, arr, glow = [], [], [], []
    rng = np.random.default_rng(7)
    shade = 0.86 + 0.28 * rng.random(n).astype(np.float32)
    zi = np.arange(n[2])[None, None, :]
    xi = np.arange(n[0])[:, None, None]
    strake = np.where((zi // max(1, int(round(3 * s)))) % 2 == 0, 1.0, 0.82)          # hull plating bands
    port_rows = np.isin(zi, [int(round(z * s)) for z in (12.5, 15.5, 18.0, 20.5, 23.5, 26.0)])
    ports = port_rows & ((xi % max(2, int(round(3 * s)))) == 0)                         # lit portholes
    for (dx, dy, dz), corners in DIRS:
        face = solid & ~p[1 + dx:1 + dx + n[0], 1 + dy:1 + dy + n[1], 1 + dz:1 + dz + n[2]]
        idx = np.argwhere(face)
        if not len(idx):
            continue
        quad = idx[:, None, :] + np.array(corners)[None, :, :]
        verts.append(quad.reshape(-1, 3))
        r = role[face]
        c = np.array([PAL.get(i, (0, 0, 0)) for i in range(9)], np.float32)[r]
        light = (1.0, 0.80, 0.90, 0.70, 1.12, 0.50)[[d[0] for d in DIRS].index((dx, dy, dz))]
        k = shade[face] * light * np.where(np.isin(r, (HULL, KEEL)), np.broadcast_to(strake, n)[face], 1.0)
        c = c * k[:, None]
        g = np.zeros(len(idx), np.float32)
        side = (dy != 0) & np.broadcast_to(ports, n)[face] & np.isin(r, (HULL, SUPER))
        g[side] = 1.0
        g[r == BOAT] = 0.35
        cols.append(c); arr.append(arrive[face]); glow.append(g)
    V = np.vstack(verts).astype(np.float32) / s
    nf = len(V) // 4
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.loops.add(nf * 4); me.polygons.add(nf)
    me.vertices.foreach_set("co", V.ravel())
    me.loops.foreach_set("vertex_index", np.arange(nf * 4, dtype=np.int32))
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 4, 4, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(nf, 4, np.int32))
    me.update()
    me.attributes.new("arrive", "FLOAT", "FACE").data.foreach_set("value", np.concatenate(arr))
    me.attributes.new("glow", "FLOAT", "FACE").data.foreach_set("value", np.concatenate(glow))
    C = np.concatenate(cols)
    me.attributes.new("tone", "FLOAT_COLOR", "FACE").data.foreach_set(
        "color", np.hstack([C, np.ones((nf, 1), np.float32)]).ravel())
    me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me))
    o.location = origin
    return o, nf


def construct_material(texs=None):
    m = bpy.data.materials.new("Titanic construct textured" if texs else "Titanic construct")
    m.use_nodes = True
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    N, K = nt.nodes.new, nt.links.new

    def attr(nm):
        a = N("ShaderNodeAttribute"); a.attribute_name = nm
        return a

    def mth(op, a, b=None, clamp=False):
        x = N("ShaderNodeMath"); x.operation = op; x.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                x.inputs[i].default_value = v
            else:
                K(v, x.inputs[i])
        return x.outputs[0]

    form = N("ShaderNodeValue"); form.label = "form (scene['form'])"
    d = form.outputs[0].driver_add("default_value").driver
    d.type = "AVERAGE"
    v = d.variables.new(); v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = '["form"]'
    arr, glow, tone = attr("arrive"), attr("glow"), attr("tone")
    base = texture_base(nt, N, K, mth, attr, tone, texs) if texs else tone.outputs["Color"]
    since = mth("SUBTRACT", form.outputs[0], arr.outputs["Fac"])           # how long this face has been there
    shown = mth("GREATER_THAN", since, 0.0)
    fresh = mth("SUBTRACT", 1.0, mth("DIVIDE", since, 0.07), clamp=True)   # 1 on the leading edge, 0 once settled
    fresh = mth("MULTIPLY", fresh, shown)
    edge = N("ShaderNodeRGB"); edge.outputs[0].default_value = (0.10, 1.0, 0.22, 1)
    bsdf = N("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.35
    K(base, bsdf.inputs["Base Color"])
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
    K(fresh, mix.inputs["Factor"]); K(base, mix.inputs["A"]); K(edge.outputs[0], mix.inputs["B"])
    K(mix.outputs["Result"], bsdf.inputs["Emission Color"])
    strength = mth("ADD", mth("ADD", 0.55, mth("MULTIPLY", fresh, 0.9)), mth("MULTIPLY", glow.outputs["Fac"], 0.8))
    K(mth("MINIMUM", strength, 1.45), bsdf.inputs["Emission Strength"])
    K(mth("MULTIPLY", shown, 0.96), bsdf.inputs["Alpha"])                  # constructs stay see-through
    out = N("ShaderNodeOutputMaterial")
    K(bsdf.outputs[0], out.inputs["Surface"])
    return m


def flat_material(name, rgb, emit=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Emission Color"].default_value = (*rgb, 1)
    b.inputs["Emission Strength"].default_value = emit
    return m


def cube(name, size, loc, mat):
    me = bpy.data.meshes.new(name)
    sx, sy, sz = size
    v = [(x, y, z) for x in (0, sx) for y in (0, sy) for z in (0, sz)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(v, [], f); me.update(); me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    return o


def camera(name, loc, target, lens=35):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.data.lens = lens; c.data.clip_start = 0.5; c.data.clip_end = 1200
    c.location = loc
    dx, dy, dz = (target[i] - loc[i] for i in range(3))
    c.rotation_euler = (math.atan2(math.hypot(dx, dy), -dz), 0, math.atan2(dy, dx) - math.pi / 2)
    return c


def label(text, loc, size, mat):
    cu = bpy.data.curves.new("Label " + text, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = link(bpy.data.objects.new("Label " + text, cu)); o.location = loc
    o.rotation_euler = (math.radians(90), 0, 0); cu.materials.append(mat)
    return o


# ------------------------------------------------------------------ detail (pass 952)
RAIL, RIG, STRIPE, GOLD, GLASS = 9, 10, 11, 12, 13
PAL.update({RAIL: (0.090, 0.780, 0.200), RIG: (0.060, 0.560, 0.150), STRIPE: (0.050, 0.520, 0.130),
            GOLD: (0.420, 0.800, 0.040), GLASS: (0.120, 0.950, 0.300)})
DETAIL = (RAIL, RIG, GLASS)


def upsample(role, k):
    return role if k == 1 else np.repeat(np.repeat(np.repeat(role, k, 0), k, 1), k, 2)


def add_detail(role, s):
    """Thin detail on a role grid at s voxels per metre (s = 2 or 4). Changes role in place."""
    nx, ny, nz = role.shape
    yc = (ny / s) / 2

    def vox(p):
        return (int(p[0] * s), int((p[1] + yc) * s), int(p[2] * s))

    def put(i, j, k, r, over=False):
        if 0 <= i < nx and 0 <= j < ny and 0 <= k < nz and (over or role[i, j, k] == 0):
            role[i, j, k] = r

    def line(p0, p1, r=RIG):
        n = int(max(2, math.dist(p0, p1) * s * 2))
        for t in np.linspace(0, 1, n):
            put(*vox([p0[a] + (p1[a] - p0[a]) * t for a in range(3)]), r)

    def fill(x0, x1, y0, y1, z0, z1, r, over=False):
        i0, j0, k0 = vox((x0, y0, z0)); i1, j1, k1 = vox((x1, y1, z1))
        sl = role[max(0, i0):max(i0 + 1, i1), max(0, j0):max(j0 + 1, j1), max(0, k0):max(k0 + 1, k1)]
        if over:
            sl[...] = r
        else:
            sl[sl == 0] = r

    # paint on the hull: waterline band, thin sheer line, bow anchors
    Xm = ((np.arange(nx) + 0.5) / s)[:, None, None]
    Zm = ((np.arange(nz) + 0.5) / s)[None, None, :]
    hullm = (role == HULL) | (role == KEEL)
    top = np.where((Xm > L - 39) | (Xm < 32), 22.0, 19.0)
    role[hullm & (Zm >= 10.5) & (Zm < 11.5)] = STRIPE
    role[hullm & (Zm >= top - 3.5) & (Zm < top - 3.5 + max(0.5, 1.0 / s))] = GOLD
    anchor = ((np.abs(Xm - (L - 13)) < 0.5) & (Zm > 14.5) & (Zm < 18.5)) | \
             ((np.abs(Zm - 15.2) < 0.5) & (np.abs(Xm - (L - 13)) < 1.8))
    role[(role == HULL) & anchor] = MAST

    # railings: on every deck edge that drops 2 m or more
    walk = np.isin(role, (HULL, KEEL, SUPER, DECK, STRIPE, GOLD))
    zidx = np.arange(nz)[None, None, :]
    H = np.where(walk, zidx, -1).max(2)                           # top walkable voxel of each column
    clear = (np.where(role > 0, zidx, -1).max(2) == H) & (H > int(18 * s))
    P = np.pad(H, 1, constant_values=-1)
    lowest = np.minimum(np.minimum(P[2:, 1:-1], P[:-2, 1:-1]), np.minimum(P[1:-1, 2:], P[1:-1, :-2]))
    edge = clear & (H - lowest >= int(2 * s))
    ii, jj = np.nonzero(edge)
    hh = H[ii, jj]
    rail_h = int(round(1.0 * s))
    ok = hh + rail_h < nz
    ii, jj, hh = ii[ok], jj[ok], hh[ok]
    role[ii, jj, hh + rail_h] = RAIL                              # the top rail
    mid = max(1, rail_h // 2)
    if s >= 4:
        role[ii, jj, hh + mid] = RAIL                             # a middle rail at quarter-block
    post = ((ii % int(2 * s)) == 0) & ((jj % int(2 * s)) == 0) | ((ii % int(2 * s)) == 0) & (np.abs(jj - ny / 2) > 4 * s)
    for dz in range(1, rail_h):
        role[ii[post], jj[post], hh[post] + dz] = RAIL

    # masts: stays, shrouds and the aerial
    fm = lambda z: (L - 47 - (z - 19) / 11.0, 0.0, z)
    mm = lambda z: (58 - (z - 22) / 11.0, 0.0, z)
    line(fm(62.5), (L - 2.5, 0, 23.2))
    line(mm(60.5), (5.0, 0, 23.2))
    for sy in (-1, 1):
        for dx in (-9, -5, -1):
            line(fm(50), (L - 47 + dx, sy * 12.2, 19.5))
            line(mm(50), (58 + dx + 4, sy * 12.8, 22.5))
        line((fm(61)[0], sy * 1.5, 61), (mm(59.5)[0], sy * 1.5, 59.5))        # the aerial, two wires
        line(fm(61), (fm(61)[0], sy * 1.5, 61)); line(mm(59.5), (mm(59.5)[0], sy * 1.5, 59.5))
    line((fm(41)[0] + 0.6, 0, 41.5), (fm(41)[0] + 2.0, 0, 41.5), MAST)
    # funnels: four stays each, a steam pipe up the front, a lip
    for fx in FUNNELS:
        cx = lambda z: fx - (z - 28) / 6.0
        for sx in (-1, 1):
            for sy in (-1, 1):
                line((cx(44) + sx * 2.6, sy * 2.3, 44), (fx + sx * 8.0, sy * 11.3, 28.3))
        line((cx(29) + 4.1, 0, 29), (cx(51) + 4.1, 0, 51), MAST)
        for a in np.linspace(0, 2 * math.pi, int(40 * s)):
            put(*vox((cx(46.5) + 4.1 * math.cos(a), 3.3 * math.sin(a), 46.5)), FTOP)
    # lifeboat davits
    for bx in BOATS:
        for sy in (-1, 1):
            for px in (bx + 0.6, bx + 8.4):
                line((px, sy * 13.1, 28), (px, sy * 13.1, 31.6), MAST)
                line((px, sy * 13.1, 31.6), (px, sy * 11.6, 31.9), MAST)
                line((px, sy * 11.6, 31.9), (px, sy * 11.6, 30.2), RIG)
    # cargo cranes on the well decks
    for cxp, zb, d in ((L - 58, 19, 1), (L - 58, 19, -1), (41, 19, 1), (41, 19, -1), (36, 22, 1), (36, 22, -1)):
        line((cxp, d * 8.5, zb), (cxp, d * 8.5, zb + 4.5), MAST)
        line((cxp, d * 8.5, zb + 4.5), (cxp + 7.5, d * 4.0, zb + 7.5), MAST)
        line((cxp + 7.5, d * 4.0, zb + 7.5), (cxp, d * 8.5, zb + 6.5))
    # the docking bridge across the poop
    fill(14.0, 15.6, -13.0, 13.0, 25.0, 25.0 + 1.0 / s, DECK)
    for y in (-13.0, -6.0, 6.0, 13.0 - 1.0 / s):
        fill(14.6, 14.6 + 1.0 / s, y, y + 1.0 / s, 22.0, 25.0, MAST)
    fill(14.0, 14.0 + 1.0 / s, -13.0, 13.0, 26.0, 26.0 + 1.0 / s, RAIL)
    fill(15.6 - 1.0 / s, 15.6, -13.0, 13.0, 26.0, 26.0 + 1.0 / s, RAIL)
    # ventilators and the skylight dome
    rngv = np.random.default_rng(52)
    for _ in range(26):
        vx = float(rngv.uniform(66, L - 96)); vy = float(rngv.choice((-1, 1)) * rngv.uniform(7.2, 9.4))
        fill(vx, vx + 0.5, vy, vy + 0.5, 28.0, 30.0, MAST)
        fill(vx, vx + 1.2, vy - 0.3, vy + 0.8, 30.0, 30.9, FUNNEL)
    i0, j0, k0 = vox((173.0 - 4, -3.5, 30.0)); i1, j1, k1 = vox((173.0 + 4, 3.5, 33.0))
    gi, gj, gk = np.meshgrid(np.arange(i0, i1), np.arange(j0, j1), np.arange(k0, k1), indexing="ij")
    dome = (((gi + 0.5) / s - 173.0) / 3.8) ** 2 + (((gj + 0.5) / s - yc) / 3.3) ** 2 + (((gk + 0.5) / s - 30.0) / 2.6) ** 2 <= 1
    sl = role[i0:i1, j0:j1, k0:k1]
    sl[dome] = GLASS
    return role


def circles_arrive(shape, pts, seed):
    """F2 circles from pass 951, worked out on the shell voxels only (fast at any resolution)."""
    rng = np.random.default_rng(seed)
    span = max(shape)
    cents = pick(rng, pts[rng.permutation(len(pts))[:4000]], 26, span * 0.09)
    delay = rng.random(len(cents)) * span * 0.10
    band = max(3.0, span / 55.0)
    T = np.full(len(pts), 1e9, np.float32)
    P = pts.astype(np.float32)
    for c, dl in zip(cents, delay):
        d = np.sqrt(((P - c) ** 2).sum(1))
        T = np.minimum(T, dl + d + (np.floor(d / band) % 2) * band * 2.2)
    lin = (T - T.min()) / max(1e-6, float(T.max() - T.min()))
    rank = np.argsort(np.argsort(T)).astype(np.float32) / len(T)
    out = np.full(shape, -1.0, np.float32)
    out[pts[:, 0], pts[:, 1], pts[:, 2]] = (0.3 * lin + 0.7 * rank) * 0.94
    return out


TEX_OF = {HULL: 1, KEEL: 1, SUPER: 2, DECK: 2, FUNNEL: 3}        # role -> texture slot (BR1, W1, H1); the rest stay plain


def ship_mesh(name, role, arrive, vpm, origin, mat, mask=None, tex=False):
    """One mesh of the outside faces. vpm = voxels per block. mask = draw only these voxels (the overlay).
    tex = also write the UV map (32 px a block, fixed in the world) and which texture each face wears."""
    solid = role > 0
    draw = solid if mask is None else mask
    p = np.pad(solid, 1)
    n = solid.shape
    verts, cols, arr, glow, uvs, tid, lit = [], [], [], [], [], [], []
    texlut = np.zeros(14, np.float32)
    for r_, s_ in TEX_OF.items():
        texlut[r_] = s_
    rng = np.random.default_rng(7)
    cell = max(1, int(vpm))
    coarse = (n[0] // cell + 1, n[1] // cell + 1, n[2] // cell + 1)
    shade = upsample(0.86 + 0.28 * rng.random(coarse).astype(np.float32), cell)[:n[0], :n[1], :n[2]]   # one tone a block
    zm = ((np.arange(n[2]) + 0.5) / vpm)[None, None, :]
    xm = ((np.arange(n[0]) + 0.5) / vpm)[:, None, None]
    ym = ((np.arange(n[1]) + 0.5) / vpm)[None, :, None]
    strake = np.where(np.floor(zm / 3.0) % 2 == 0, 1.0, 0.84)
    w = 1.0 if vpm == 1 else 0.5
    port = np.zeros((1, 1, n[2]), bool)
    for zr in (12.5, 14.5, 16.5):
        port |= (zm >= zr) & (zm < zr + w)
    ports = port & ((xm % (3.0 if vpm == 1 else 2.5)) < w)                    # portholes in the hull
    win = np.zeros((1, 1, n[2]), bool)
    for zr in (19.9, 22.9, 25.9):
        win |= (zm >= zr) & (zm < zr + (1.0 if vpm == 1 else 1.25))
    wins = win & ((xm % (3.0 if vpm == 1 else 2.0)) < 1.0)                    # cabin windows
    bridge = (zm >= 29.0) & (zm < 30.3) & ((ym % (2.0 if vpm > 1 else 3.0)) < 1.0) & (xm > L - 80)
    for (dx, dy, dz), corners in DIRS:
        face = draw & ~p[1 + dx:1 + dx + n[0], 1 + dy:1 + dy + n[1], 1 + dz:1 + dz + n[2]]
        idx = np.argwhere(face)
        if not len(idx):
            continue
        quad = (idx[:, None, :] + np.array(corners)[None, :, :]).reshape(-1, 3)
        verts.append(quad)
        r = role[face]
        if tex:
            ax = (1, 2) if dx else ((0, 2) if dy else (0, 1))
            uvs.append(quad[:, ax].astype(np.float32) / vpm / 4.0)          # one tile = 4 blocks = 128 px
            tid.append(texlut[r])
        c = np.array([PAL.get(i, (0, 0, 0)) for i in range(14)], np.float32)[r]
        light = (1.0, 0.80, 0.90, 0.70, 1.12, 0.50)[[d[0] for d in DIRS].index((dx, dy, dz))]
        k = shade[face] * light * np.where(np.isin(r, (HULL, KEEL)), np.broadcast_to(strake, n)[face], 1.0)
        c = c * k[:, None]
        if tex:
            lit.append((light * np.where(np.isin(r, (HULL, KEEL)), np.broadcast_to(strake, n)[face], 1.0)
                        * np.where(r == KEEL, 0.55, 1.0) * np.where(r == FUNNEL, 1.5, 1.0)).astype(np.float32))
        g = np.zeros(len(idx), np.float32)
        if dy != 0:
            g[np.broadcast_to(ports, n)[face] & (r == HULL)] = 1.0
            g[np.broadcast_to(wins, n)[face] & (r == SUPER)] = 1.0
        if dx > 0:
            g[np.broadcast_to(bridge, n)[face] & (r == SUPER)] = 1.0
        g[r == BOAT] = 0.35
        g[r == GLASS] = 0.9
        g[r == GOLD] = 0.5
        cols.append(c); arr.append(arrive[face]); glow.append(g)
    V = np.vstack(verts).astype(np.float32) / vpm
    nf = len(V) // 4
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.loops.add(nf * 4); me.polygons.add(nf)
    me.vertices.foreach_set("co", V.ravel())
    me.loops.foreach_set("vertex_index", np.arange(nf * 4, dtype=np.int32))
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 4, 4, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(nf, 4, np.int32))
    me.update()
    me.attributes.new("arrive", "FLOAT", "FACE").data.foreach_set("value", np.concatenate(arr))
    me.attributes.new("glow", "FLOAT", "FACE").data.foreach_set("value", np.concatenate(glow))
    C = np.concatenate(cols)
    me.attributes.new("tone", "FLOAT_COLOR", "FACE").data.foreach_set(
        "color", np.hstack([C, np.ones((nf, 1), np.float32)]).ravel())
    if tex:
        me.attributes.new("texid", "FLOAT", "FACE").data.foreach_set("value", np.concatenate(tid))
        me.attributes.new("lit", "FLOAT", "FACE").data.foreach_set("value", np.concatenate(lit))
        me.uv_layers.new(name="UVMap").data.foreach_set("uv", np.vstack(uvs).ravel())
    me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me))
    o.location = origin
    return o, nf


TEXDIR = os.path.join(FOLDER, "constructs", "titanic_textures")
TEX_FRAMES = 24


def texture_base(nt, N, K, mth, attr, tone, texs):
    """Base colour from J's animated strips: UV wrapped inside one frame, the frame picked by scene['tex']."""
    uv = N("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    sep = N("ShaderNodeSeparateXYZ"); K(uv.outputs[0], sep.inputs[0])
    fu = mth("FRACT", sep.outputs[0]); fv = mth("FRACT", sep.outputs[1])
    tv = N("ShaderNodeValue"); tv.label = "texture frame (scene['tex'])"
    d = tv.outputs[0].driver_add("default_value").driver
    d.type = "AVERAGE"
    v = d.variables.new(); v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = '["tex"]'
    idx = mth("FLOOR", mth("MODULO", tv.outputs[0], float(TEX_FRAMES)))
    vv = mth("SUBTRACT", 1.0, mth("DIVIDE", mth("SUBTRACT", mth("ADD", idx, 1.0), fv), float(TEX_FRAMES)))
    comb = N("ShaderNodeCombineXYZ"); K(fu, comb.inputs[0]); K(vv, comb.inputs[1])
    tid, lit = attr("texid"), attr("lit")
    col_out = tone.outputs["Color"]
    for i, path in enumerate(texs):
        img = N("ShaderNodeTexImage"); img.interpolation = "Closest"; img.extension = "EXTEND"
        img.image = bpy.data.images.load(path, check_existing=True)
        K(comb.outputs[0], img.inputs["Vector"])
        sc = N("ShaderNodeVectorMath"); sc.operation = "SCALE"
        K(img.outputs["Color"], sc.inputs[0]); K(lit.outputs["Fac"], sc.inputs["Scale"])
        mx = N("ShaderNodeMix"); mx.data_type = "RGBA"
        K(mth("COMPARE", tid.outputs["Fac"], float(i + 1)), mx.inputs["Factor"])
        K(col_out, mx.inputs["A"]); K(sc.outputs[0], mx.inputs["B"])
        col_out = mx.outputs["Result"]
    return col_out


# ------------------------------------------------------------------ build
scene["form"] = 0.0
scene.keyframe_insert('["form"]', frame=1)
scene["form"] = 1.0
scene.keyframe_insert('["form"]', frame=FORM_END)
scene["tex"] = 0.0
scene.keyframe_insert('["tex"]', frame=1)
scene["tex"] = (HOLD_END - 1) / 5.0                                 # frametime 5: one texture frame every 5 ticks
scene.keyframe_insert('["tex"]', frame=HOLD_END)
try:
    for fc in scene.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
except Exception:
    try:
        for layer in scene.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
    except Exception as e:
        print("linear keys:", e)

MAT = construct_material()
TEX_PATHS = [os.path.join(TEXDIR, f"construct_{k}_green_ship.png") for k in ("br1", "w1", "h1")]
HAVE_TEX = all(os.path.exists(q) for q in TEX_PATHS)
if not HAVE_TEX:
    print("D4: textures not found in", TEXDIR, "- D4 is drawn plain", flush=True)
MAT_TEX = construct_material(TEX_PATHS) if HAVE_TEX else MAT
DARK = flat_material("Ground", (0.030, 0.034, 0.040), 0.0)
TEXT = flat_material("Label", (0.20, 0.95, 0.35), 0.9)
ROW = 1600.0
STATS = {}
CAMS = []
TAKES = [("D1", "Half-block", 2, 2), ("D2", "Quarter-block", 4, 4), ("D3", "Overlay", 1, 4), ("D4", "Textured", 2, 2)]
VIEWS = (("bow quarter", (L + 75, -219, 96), (L * 0.47, 0, 64), 26), ("off the bow", (L + 30, -34, 52), (L - 55, 0, 70), 22),
         ("boat deck", (112, -8.6, 71.5), (L - 70, -7.0, 71.0), 20), ("funnels", (L - 40, -62, 98), (L - 110, 0, 78), 35),
         ("stern", (-42, -46, 60), (60, 0, 64), 24))
for i, (code, nm, hull_v, det_v) in enumerate(TAKES):
    yc = i * ROW + 14
    k = det_v // hull_v
    base = ship_roles(float(hull_v))
    plain = upsample(base, k)
    role = add_detail(plain.copy(), det_v)
    pts = np.argwhere(shell_of(role > 0))
    arr = circles_arrive(role.shape, pts, SEED + 1)
    origin = (0, yc - (role.shape[1] / det_v) / 2, 40)                 # centre line on yc, forming 40 blocks up
    if code == "D3":
        a = np.where(arr < 0, 0, arr)                                  # each block lands when its last voxel does
        for axis in range(3):
            a = np.maximum.reduceat(a, np.arange(0, a.shape[axis], k), axis)
        o, nf = ship_mesh(f"{code} {nm} ship (1-block)", base, a, hull_v, origin, MAT)
        o2, nf2 = ship_mesh(f"{code} {nm} detail layer", role, arr, det_v, origin, MAT, mask=(role != plain) & (role > 0))
        nf = (nf, nf2)
    else:
        o, nf = ship_mesh(f"{code} {nm}", role, arr, det_v, origin, MAT_TEX if code == "D4" else MAT, tex=(code == "D4"))
    STATS[code] = (role.shape, nf, len(pts))
    for view, loc, tgt, lens in VIEWS:
        name = f"{len(CAMS) + 1} {code} {nm} - {view}"
        camera(name, (loc[0], yc + loc[1], loc[2]), (tgt[0], yc + tgt[1], tgt[2]), lens)
        CAMS.append(name)
    cube(f"{code} ground", (L + 400, 300, 1), (-200, yc - 154, -1), DARK)
    cube(f"{code} player (2 blocks) on the boat deck", (0.6, 0.6, 1.8), (130, yc - 9.5, 68), TEXT)
    print(code, STATS[code], flush=True)
    del base, plain, role, arr, pts
print("CAMS", CAMS, flush=True)
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("pack:", e)

# ------------------------------------------------------------------ light, world, glow
world = bpy.data.worlds.new("Titanic night"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.016, 0.024, 1)
scene.world = world
sun = link(bpy.data.objects.new("Moonlight", bpy.data.lights.new("Moonlight", "SUN")))
sun.data.energy = 1.6; sun.rotation_euler = (math.radians(52), 0, math.radians(-35))
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
try:
    tree = bpy.data.node_groups.new("Titanic Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.5), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)

scene.camera = bpy.data.objects[CAMS[0]]
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
