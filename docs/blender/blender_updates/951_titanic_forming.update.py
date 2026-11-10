# Pass 951: the Titanic construct, to replace the Anvil mode's ship (chat "titanic", 2026-11-09).
# J: "a titanic construct to replace our current one, as big as it can be, it should have random generation patterns
# instead of bottom up, it should start from random points and circles all over and connect that way, always random or
# maybe just a few repeating random patterns, give me sizes and how accurate we can make it" / "how accurate is the
# real titanic for size, use that scale" / "to replace the anvil mode we have".
# The ship: an ocean liner at the real ship's size, 1 block = 1 metre: 269 long, 28 wide, 53 keel to funnel tops,
# 63 to the mast tops. Four raked funnels, two masts, forecastle, well decks, poop, three superstructure decks with an
# open promenade, 16 lifeboats, counter stern, rudder, three propellers, lit porthole rows. Voxels, shell only.
# How it forms (frames 1-80 = 4 s, then holds to 110). Every take is one mesh; a per-face "arrive" time (0-1) is
# compared with scene["form"], so the game can do the same from one random seed:
#   F1 Seeds    : 40 random points on the hull, each starting at its own moment, spread along the surface as patches
#                 until the patches meet.
#   F2 Circles  : 26 random centres send out expanding rings; the ring lines land first, the bands between fill after.
#   F3 Web      : 34 random points first throw jagged lines to their nearest neighbours (a web over the whole ship),
#                 then the plating spreads out from the lines.
#   F4 Mix      : F2's rings at half the centres + F3's web between them.
#   B0 Bottom up: how the Anvil builds now, for comparison only.
#   SZ Sizes    : the ship at 1:1 (269), 1:2 (135) and 1:4 (67 blocks) beside the Anvil's current 48-block ship, a
#                 7 x 7 house and a 2-block player. Static.
# SEED below picks the pattern: every number gives a different one; a fixed list of 4 numbers = "a few repeating".
# Cameras are numbered and carry the option's name (J: "make the cameras named accordingly to each option"):
#   "1 F1 Seeds - bow quarter", "2 F1 Seeds - off the bow", "3 F1 Seeds - side"; 4-6 F2 Circles, 7-9 F3 Web,
#   10-12 F4 Mix, 13-15 B0 Bottom up, "16 SZ Sizes - all three".
# Builds LanternLive\constructs\951_titanic_forming.blend (was titanic_construct.blend).
SCENE_NAME = "Titanic Construct"
OUT_REL = "constructs/951_titanic_forming.blend"
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
    X, Y, Z = np.meshgrid((np.arange(nx) + 0.5) / s, (np.arange(ny) + 0.5) / s - (ny / s) / 2,
                          (np.arange(nz) + 0.5) / s, indexing="ij")
    A = np.abs(Y)
    role = np.zeros((nx, ny, nz), np.uint8)
    hb = half_beam(X, Z)
    stem = L - (19 - Z) * 0.10 - 0.5             # a near-plumb stem
    counter = np.where(X < 13, 9.0 + (13 - X) * 0.55, 0.0)   # the stern overhang rises from the rudder post
    top = np.where((X > L - 39) | (X < 32), 22.0, 19.0)      # forecastle and poop one deck higher than the wells
    hull = (A <= hb) & (Z <= top) & (X <= stem) & (Z >= counter) & (X >= 0.2)
    role[hull] = HULL
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


def construct_material():
    m = bpy.data.materials.new("Titanic construct")
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
    since = mth("SUBTRACT", form.outputs[0], arr.outputs["Fac"])           # how long this face has been there
    shown = mth("GREATER_THAN", since, 0.0)
    fresh = mth("SUBTRACT", 1.0, mth("DIVIDE", since, 0.07), clamp=True)   # 1 on the leading edge, 0 once settled
    fresh = mth("MULTIPLY", fresh, shown)
    edge = N("ShaderNodeRGB"); edge.outputs[0].default_value = (0.10, 1.0, 0.22, 1)
    bsdf = N("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.35
    K(tone.outputs["Color"], bsdf.inputs["Base Color"])
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
    K(fresh, mix.inputs["Factor"]); K(tone.outputs["Color"], mix.inputs["A"]); K(edge.outputs[0], mix.inputs["B"])
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


# ------------------------------------------------------------------ build
scene["form"] = 0.0
scene.keyframe_insert('["form"]', frame=1)
scene["form"] = 1.0
scene.keyframe_insert('["form"]', frame=FORM_END)
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
GREY = flat_material("Reference", (0.25, 0.27, 0.30), 0.25)
TEXT = flat_material("Label", (0.20, 0.95, 0.35), 0.9)
DARK = flat_material("Ground", (0.030, 0.034, 0.040), 0.0)
ROLE1 = ship_roles(1.0)
SHELL1 = shell_of(ROLE1 > 0)
ROW = 1600.0                                             # rows far apart so no take hides another
TAKES = [("F1", "Seeds"), ("F2", "Circles"), ("F3", "Web"), ("F4", "Mix"), ("B0", "Bottom up")]
STATS = {}
for i, (code, nm) in enumerate(TAKES):
    arr = arrive_for(code, SHELL1, SEED + i)
    y0 = i * ROW
    o, nf = ship_mesh(f"{code} {nm}", ROLE1, arr, 1.0, (0, y0, 40), MAT)     # forming 40 blocks up, as the Anvil does
    STATS[code] = nf
    camera(f"{3 * i + 1} {code} {nm} - bow quarter", (L + 75, y0 - 205, 96), (L * 0.47, y0 + 14, 64), 26)
    camera(f"{3 * i + 2} {code} {nm} - off the bow", (L + 38, y0 - 30, 46), (L - 60, y0 + 14, 66), 20)
    camera(f"{3 * i + 3} {code} {nm} - side", (L / 2, y0 - 330, 70), (L / 2, y0 + 14, 66), 40)
    cube(f"{code} ground", (L + 400, 300, 1), (-200, y0 - 140, -1), DARK)
    cube(f"{code} player", (0.6, 0.6, 1.8), (L + 20, y0 - 12, 0), TEXT)
    print(code, "faces", nf, flush=True)

# SZ: the three sizes, the Anvil's current ship, a house and a player
y0 = len(TAKES) * ROW
x = 0.0
for sc, nm in ((1.0, "1:1  269 blocks"), (0.5, "1:2  135 blocks"), (0.25, "1:4  67 blocks")):
    r = ROLE1 if sc == 1.0 else ship_roles(sc)
    o, nf = ship_mesh("SZ " + nm, r, np.full(r.shape, -1.0, np.float32), 1.0, (x, y0, 0), MAT)   # 1 voxel = 1 block
    STATS["SZ " + nm] = (nf, int(shell_of(r > 0).sum()))
    label(nm, (x + r.shape[0] / 2, y0 - 2, r.shape[2] + 8), 14, TEXT)
    x += r.shape[0] + 30
cube("SZ current Anvil ship (48 x 12 x 21)", (48, 12, 21), (x, y0 + 8, 0), GREY)
label("Anvil ship now  48", (x + 24, y0 - 2, 29), 9, TEXT)
cube("SZ house 7 x 7 x 6", (7, 7, 6), (x + 62, y0 + 10, 0), GREY)
cube("SZ player 2 blocks", (0.6, 0.6, 1.8), (x + 76, y0 + 10, 0), TEXT)
label("house, player", (x + 70, y0 - 2, 14), 7, TEXT)
cube("SZ ground", (x + 300, 300, 1), (-100, y0 - 140, -1), DARK)
camera("16 SZ Sizes - all three", ((x + 90) / 2, y0 - 520, 150), ((x + 90) / 2, y0, 25), 24)
print("STATS", STATS, flush=True)

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

scene.camera = bpy.data.objects["1 F1 Seeds - bow quarter"]
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
