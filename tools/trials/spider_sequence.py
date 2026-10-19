"""Block-out of the three-part giant-spider fight (docs/plans/trials/2026-10-19-spider-boss-sequence.md).

Two layouts:

trap (default, rounds 1-2)
  1. The run      a wild cave (round 3 recipe) with the yellow construct spider; its entrance shaft comes down from
                  the surface.
  2. Funnel trap  a small silk-walled room (24 across) above the edge of the lair, its floor a 3-block layer of
                  webbed dirt over a drop; one escape burrow climbs up to it from cave 1.
  3. The lair     the W1 cave J liked (seed 11, 1.6x), with no shaft of its own.
  Cave 1 and the lair side by side on one grid, world y -64 to 72.

--collapse (J's pick, 2026-10-19: "maybe the original cave could be destroyed falling through a hollow funnel of
spikes on the sides into the dungeon?" -> "Cave collapse")
  Cave 1 (30 high) sits over the lair's west end. Its floor over the drop is a disc of webbed dirt that breaks; under
  it a hollow funnel with spikes pointing in from every side drops you onto the net at the lair roof. No trap room,
  no escape burrow. The grid runs to y 100: this version only fits under hills and mountains (surface y 85+).

Both: hanging dripstone spikes, about a quarter with yellow hard-light tips (J: "constructed tip ones that should be
apart of the spiders arsenal, they will hang from the ceiling").

Usage: python spider_sequence.py <out_dir> [--collapse]
Writes <out>/sequence.npz (solid, mask, dirt, net, drip, meta) and a datapack.
"""
import json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spider_cave_wild as W

GAP = 50                     # rock between cave 1 and the lair (trap layout)
TRAP_R = 12                  # funnel trap: radius (24 across)
TRAP_FLOOR_Y = 18            # top of the webbed dirt floor
TRAP_H = 14                  # floor to roof
DIRT = 3                     # floor thickness
SHAFT_R = 10                 # the drop under the trap floor
NET_BELOW = 12               # the net hangs this far under the trap floor


def _placed(X, Y, Z, s_, m_, o, only_cave=True):
    a = np.zeros((X, Y, Z), bool)
    a[o[0]:o[0] + s_.shape[0], :, o[1]:o[1] + s_.shape[2]] = (~s_) & (m_ == 1) if only_cave else ~s_
    return a


def layout_trap():
    s1, m1, meta1 = W.build(seed=21, scale=1.0, H=44, floor_y=-20, depth=12, name="cave1", shaft=True, shaft_on_cut=True)
    s3, m3, meta3 = W.build(seed=11, scale=1.6, H=56, floor_y=-46, depth=8, name="lair", shaft=False)
    X1, Y, Z1 = s1.shape
    X3, _, Z3 = s3.shape
    X, Z = X1 + GAP + X3, max(Z1, Z3)
    o1 = (0, (Z - Z1) // 2)
    o3 = (X1 + GAP, (Z - Z3) // 2)
    air = np.zeros((X, Y, Z), bool)
    mask = np.zeros((X, Y, Z), np.uint8)
    for s_, m_, (ox, oz) in ((s1, m1, o1), (s3, m3, o3)):
        sl = (slice(ox, ox + s_.shape[0]), slice(None), slice(oz, oz + s_.shape[2]))
        air[sl] |= ~s_
        mask[sl] = np.maximum(mask[sl], m_)
    ymin = W.Y_MIN
    zc = Z // 2
    lair_cave = mask == 1
    lair_cave[:o3[0]] = False
    tx = o3[0] + int(meta3["length"] * 0.18) + 40
    col = np.flatnonzero(lair_cave[tx, :, zc])
    while not len(col):
        tx += 4
        col = np.flatnonzero(lair_cave[tx, :, zc])
    lair_roof = int(col.max())
    fy = TRAP_FLOOR_Y - ymin
    xs = (np.arange(X) - tx)[:, None, None]; zs = (np.arange(Z) - zc)[None, None, :]; ys = np.arange(Y)[None, :, None]
    rr = np.sqrt(xs ** 2 + zs ** 2)
    t = np.clip((ys - fy) / TRAP_H, 0, 1)
    room = (ys > fy) & (ys <= fy + TRAP_H) & (rr <= TRAP_R * (1 - 0.45 * t ** 2))
    air |= room; mask[room] = 7
    dirt = (ys > fy - DIRT) & (ys <= fy) & (rr <= TRAP_R + 0.5)
    drop = (ys <= fy - DIRT) & (ys > lair_roof - 2) & (rr <= SHAFT_R * (1 + 0.25 * (fy - DIRT - ys) / max(1, fy - lair_roof)))
    air |= drop; mask[drop & (mask == 0)] = 9
    air &= ~dirt
    net_y = fy - NET_BELOW
    net = np.zeros_like(air)
    net[:, net_y, :] = (rr[:, 0, :] <= SHAFT_R * 1.1) & air[:, net_y, :]
    # escape burrow from cave 1's east end up into the trap's west wall
    cave1 = mask == 1
    cave1[o1[0] + X1:] = False
    hx = o1[0] + X1 // 2 + int(meta1["length"] * 0.36)
    cols = np.flatnonzero(cave1[hx, :, zc])
    while not len(cols):
        hx -= 3
        cols = np.flatnonzero(cave1[hx, :, zc])
    h_floor = int(cols.min())
    start = (hx, h_floor + 2, zc)
    end = (tx - TRAP_R + 1, fy + 3, zc)
    mid1 = (hx + 25, h_floor - 6, zc + 6)
    mid2 = ((hx + end[0]) / 2 + 10, (h_floor + fy) / 2, zc - 6)
    W.carve_tube(air, mask, [start, (hx, h_floor - 4, zc), mid1, mid2, (end[0] - 8, fy + 3, zc), end], 5.5, 8)
    trap = dict(x=int(tx), z=int(zc), floor_y=TRAP_FLOOR_Y, radius=TRAP_R, height=TRAP_H, dirt=DIRT,
                net_y=int(net_y + ymin), lair_roof_y=int(lair_roof + ymin),
                lair_floor_y=int(np.flatnonzero(lair_cave[tx, :, zc]).min() + ymin), kind="trap room")
    burrow = dict(start=[int(start[0]), int(start[1] + ymin), int(start[2])], end=[int(end[0]), int(end[1] + ymin), int(end[2])])
    space_air = {"cave1": _placed(X, Y, Z, s1, m1, o1), "lair": _placed(X, Y, Z, s3, m3, o3)}
    keep_clear = (tx, zc, SHAFT_R + 14)
    return dict(air=air, mask=mask, dirt=dirt, net=net, o1=o1, o3=o3, meta1=meta1, meta3=meta3, trap=trap,
                burrow=burrow, space_air=space_air, keep_clear=keep_clear, wall_spikes=[])


def layout_collapse():
    W.GRID_TOP = 100
    s1, m1, meta1 = W.build(seed=21, scale=1.0, H=30, floor_y=26, depth=6, name="cave1", shaft=True, shaft_on_cut=True)
    s3, m3, meta3 = W.build(seed=11, scale=1.6, H=56, floor_y=-46, depth=8, name="lair", shaft=False)
    X1, Y, Z1 = s1.shape
    X3, _, Z3 = s3.shape
    o3x = int(X1 * 0.45)
    X, Z = max(X1, o3x + X3), max(Z1, Z3)
    o1 = (0, (Z - Z1) // 2)
    o3 = (o3x, (Z - Z3) // 2)
    c1 = _placed(X, Y, Z, s1, m1, o1)
    c1_all = _placed(X, Y, Z, s1, m1, o1, only_cave=False)
    l3 = _placed(X, Y, Z, s3, m3, o3)
    l3_all = _placed(X, Y, Z, s3, m3, o3, only_cave=False)
    # keep cave 1's tunnels out of the lair: drop cave-1 tunnel cells within 3 blocks of any lair air
    near = l3_all.copy()
    for _ in range(3):
        grown = near.copy()
        for ax in range(3):
            grown |= np.roll(near, 1, ax) | np.roll(near, -1, ax)
        near = grown
    c1_all &= ~(near & ~c1)
    air = c1_all | l3_all
    mask = np.zeros((X, Y, Z), np.uint8)
    for s_, m_, (ox, oz) in ((s3, m3, o3), (s1, m1, o1)):
        sl = (slice(ox, ox + s_.shape[0]), slice(None), slice(oz, oz + s_.shape[2]))
        mask[sl] = np.maximum(mask[sl], m_)
    mask[~air] = 0
    ymin = W.Y_MIN
    zc = Z // 2
    # the drop: where cave 1's floor sits over the lair roof with rock between, toward cave 1's east end
    best = None
    for x in range(o1[0] + 20, o1[0] + X1 - 20):
        a_ = np.flatnonzero(c1[x, :, zc]); b_ = np.flatnonzero(l3[x, :, zc])
        if len(a_) and len(b_) and a_.min() - b_.max() > 10 and len(np.flatnonzero(c1[x - 16:x + 17, :, zc].any(1))) > 30:
            h = b_.max() - b_.min()                       # pick the tallest part of the lair under cave 1
            if best is None or h > best[0]:
                best = (h, x)
    tx = best[1]
    fy = int(np.flatnonzero(c1[tx, :, zc]).min())          # lowest cave-1 air: just above the floor
    lair_roof = int(np.flatnonzero(l3[tx, :, zc]).max())
    xs = (np.arange(X) - tx)[:, None, None]; zs = (np.arange(Z) - zc)[None, None, :]; ys = np.arange(Y)[None, :, None]
    rr = np.sqrt(xs ** 2 + zs ** 2)
    R_TOP, R_BOT = 16, 9
    dirt = (ys >= fy - 3) & (ys < fy) & (rr <= R_TOP + 0.5)
    span = max(1, fy - 3 - lair_roof)
    rad = R_BOT + (R_TOP - R_BOT) * np.clip((ys - lair_roof) / span, 0, 1)
    funnel = (ys < fy - 3) & (ys > lair_roof - 2) & (rr <= rad)
    air |= funnel; mask[funnel & (mask == 0)] = 10
    air &= ~dirt
    net_y = lair_roof - 1
    net = np.zeros_like(air)
    net[:, net_y, :] = (rr[:, 0, :] <= R_BOT * 1.4) & air[:, net_y, :]
    # spikes on the funnel walls, pointing in and slightly down
    rng = np.random.default_rng(91)
    wall_spikes = []
    for k in range(70):
        y0 = rng.uniform(lair_roof + 2, fy - 5)
        a = rng.uniform(0, math.tau)
        r0 = R_BOT + (R_TOP - R_BOT) * (y0 - lair_roof) / span + 0.8
        d = np.array([-math.cos(a), -0.35, -math.sin(a)]); d /= np.linalg.norm(d)
        p0 = np.array([tx + math.cos(a) * r0, y0, zc + math.sin(a) * r0])
        wall_spikes.append((p0, d, rng.uniform(3, 8), rng.uniform(0.8, 1.8), rng.random() < 0.3))
    trap = dict(x=int(tx), z=int(zc), floor_y=int(fy + ymin), radius=R_TOP, r_bottom=R_BOT, height=int(fy - lair_roof),
                dirt=3, net_y=int(net_y + ymin), lair_roof_y=int(lair_roof + ymin),
                lair_floor_y=int(np.flatnonzero(l3[tx, :, zc]).min() + ymin), kind="cave collapse")
    return dict(air=air, mask=mask, dirt=dirt, net=net, o1=o1, o3=o3, meta1=meta1, meta3=meta3, trap=trap,
                burrow=None, space_air={"cave1": c1, "lair": l3}, keep_clear=(tx, zc, R_TOP + 6), wall_spikes=wall_spikes)


def _clear_columns(air, mask, cave, cx, cz, radius):
    """Open every column of a cave inside `radius` of (cx, cz) from its floor to its roof (removes rock columns)."""
    X, Y, Z = air.shape
    for x in range(max(0, int(cx - radius)), min(X, int(cx + radius) + 1)):
        for z in range(max(0, int(cz - radius)), min(Z, int(cz + radius) + 1)):
            if math.hypot(x - cx, z - cz) <= radius:
                ys_ = np.flatnonzero(cave[x, :, z])
                if len(ys_):
                    lo, hi = ys_.min(), ys_.max()
                    fill = ~air[x, lo:hi + 1, z]
                    air[x, lo:hi + 1, z] = True
                    mask[x, lo:hi + 1, z][fill] = 1
                    cave[x, lo:hi + 1, z] = True


def layout_stack():
    """J (2026-10-19): "I need better positioning, it should be straight over the larger one and the funnel should be a
    great distance but maybe theres water in some way always in the center of this larger arena below".
    Cave 1 is centred straight over the lair; its floor disc breaks into a long spiked funnel that opens through the
    middle of the lair roof, and you land in a pool in the centre of the lair floor (water: no fall damage). No net.
    Cave 1's floor is at about y 60, so this needs mountains above it (surface about y 120+)."""
    W.GRID_TOP = 130
    s1, m1, meta1 = W.build(seed=21, scale=1.0, H=30, floor_y=60, depth=6, name="cave1", shaft=True, shaft_on_cut=True)
    s3, m3, meta3 = W.build(seed=11, scale=1.6, H=56, floor_y=-46, depth=8, name="lair", shaft=False)
    X1, Y, Z1 = s1.shape
    X3, _, Z3 = s3.shape
    X, Z = max(X1, X3), max(Z1, Z3)
    o1 = ((X - X1) // 2, (Z - Z1) // 2)
    o3 = ((X - X3) // 2, (Z - Z3) // 2)
    c1 = _placed(X, Y, Z, s1, m1, o1)
    l3 = _placed(X, Y, Z, s3, m3, o3)
    air = _placed(X, Y, Z, s1, m1, o1, only_cave=False) | _placed(X, Y, Z, s3, m3, o3, only_cave=False)
    mask = np.zeros((X, Y, Z), np.uint8)
    for s_, m_, (ox, oz) in ((s3, m3, o3), (s1, m1, o1)):
        sl = (slice(ox, ox + s_.shape[0]), slice(None), slice(oz, oz + s_.shape[2]))
        mask[sl] = np.maximum(mask[sl], m_)
    mask[~air] = 0
    ymin = W.Y_MIN
    tx, zc = X // 2, Z // 2
    R_TOP, R_BOT, POOL_R = 16, 10, 15
    # nothing in the way of the fall: open any rock columns round the drop in both caves
    _clear_columns(air, mask, c1, tx, zc, R_TOP + 4)
    _clear_columns(air, mask, l3, tx, zc, POOL_R + 4)
    fy = int(np.flatnonzero(c1[tx, :, zc]).min())
    lair_roof = int(np.flatnonzero(l3[tx, :, zc]).max())
    lair_floor = int(np.flatnonzero(l3[tx, :, zc]).min())
    xs = (np.arange(X) - tx)[:, None, None]; zs = (np.arange(Z) - zc)[None, None, :]; ys = np.arange(Y)[None, :, None]
    rr = np.sqrt(xs ** 2 + zs ** 2)
    dirt = (ys >= fy - 3) & (ys < fy) & (rr <= R_TOP + 0.5)
    span = max(1, fy - 3 - lair_roof)
    rad = R_BOT + (R_TOP - R_BOT) * np.clip((ys - lair_roof) / span, 0, 1)
    funnel = (ys < fy - 3) & (ys > lair_roof - 2) & (rr <= rad)
    air |= funnel; mask[funnel & (mask == 0)] = 10
    air &= ~dirt
    # the pool: a bowl 4 deep in the middle of the lair floor
    depth = 4 * np.clip(1 - (rr / POOL_R) ** 2, 0, 1)
    water = (ys < lair_floor) & (ys >= lair_floor - np.ceil(depth)) & (rr <= POOL_R)
    air |= water
    net = np.zeros_like(air)
    rng = np.random.default_rng(91)
    wall_spikes = []
    for k in range(int(70 * span / 39)):
        y0 = rng.uniform(lair_roof + 2, fy - 5)
        a = rng.uniform(0, math.tau)
        r0 = R_BOT + (R_TOP - R_BOT) * (y0 - lair_roof) / span + 0.8
        d = np.array([-math.cos(a), -0.35, -math.sin(a)]); d /= np.linalg.norm(d)
        p0 = np.array([tx + math.cos(a) * r0, y0, zc + math.sin(a) * r0])
        wall_spikes.append((p0, d, rng.uniform(3, 8), rng.uniform(0.8, 1.8), rng.random() < 0.3))
    trap = dict(x=int(tx), z=int(zc), floor_y=int(fy + ymin), radius=R_TOP, r_bottom=R_BOT, height=int(fy - lair_roof),
                dirt=3, net_y=int(lair_roof + ymin), lair_roof_y=int(lair_roof + ymin), lair_floor_y=int(lair_floor + ymin),
                fall=int(fy - lair_floor), pool=dict(radius=POOL_R, depth=4), kind="stacked collapse")
    return dict(air=air, mask=mask, dirt=dirt, net=net, water=water, o1=o1, o3=o3, meta1=meta1, meta3=meta3, trap=trap,
                burrow=None, space_air={"cave1": c1, "lair": l3}, keep_clear=(tx, zc, R_TOP + 8), wall_spikes=wall_spikes)


def add_spikes(air, mask, drip, space_air, keep_clear, wall_spikes, ymin):
    """Hanging dripstone from each space's ceiling (lots of small drips, fewer big spikes, about a quarter with yellow
    hard-light tips), plus the funnel's wall spikes. Cells: drip 1 dripstone, 2 hard-light tip."""
    X, Y, Z = air.shape
    rng = np.random.default_rng(77)
    spikes = []
    kx, kz, kr = keep_clear
    for name, n_small, n_big in (("cave1", 140, 26), ("lair", 320, 60)):
        cave = space_air[name] & air
        top = np.where(cave.any(1), Y - 1 - np.argmax(cave[:, ::-1, :], axis=1), -1)
        bot = np.where(cave.any(1), np.argmax(cave, axis=1), -1)
        cand = np.argwhere((top - bot) > 14)
        cand = cand[np.hypot(cand[:, 0] - kx, cand[:, 1] - kz) > kr]
        for k in range(n_small + n_big):
            x, z = cand[rng.integers(len(cand))]
            big = k >= n_small
            L = int(rng.uniform(8, 22) if big else rng.uniform(2, 6)) * (1.3 if name == "lair" and big else 1)
            rb = rng.uniform(2.0, 4.0) if big else rng.uniform(0.5, 1.2)
            construct = big and rng.random() < 0.3 or (not big and rng.random() < 0.12)
            t0 = top[x, z]
            r = int(math.ceil(rb))
            for dy in range(int(L)):
                rad = rb * (1 - dy / L) ** 1.2
                tip = dy >= 0.7 * L
                for ix in range(-r, r + 1):
                    for iz in range(-r, r + 1):
                        if ix * ix + iz * iz <= max(rad, 0.45) ** 2:
                            cx_, cy_, cz_ = x + ix, t0 - dy, z + iz
                            if 0 <= cx_ < X and 0 <= cz_ < Z and cave[cx_, cy_, cz_]:
                                air[cx_, cy_, cz_] = False
                                drip[cx_, cy_, cz_] = 2 if construct and tip else 1
            spikes.append(dict(space=name, big=bool(big), construct=bool(construct)))
    for p0, d, Ls, rb, construct in wall_spikes:
        for step in np.arange(0, Ls, 0.5):
            rad = rb * (1 - step / Ls) ** 1.1
            c = p0 + d * step
            r = int(math.ceil(rad))
            for ix in range(-r, r + 1):
                for iy in range(-r, r + 1):
                    for iz in range(-r, r + 1):
                        if ix * ix + iy * iy + iz * iz <= max(rad, 0.5) ** 2:
                            q = np.round(c + [ix, iy, iz]).astype(int)
                            if 0 <= q[0] < X and 0 <= q[1] < Y and 0 <= q[2] < Z and air[q[0], q[1], q[2]] and mask[q[0], q[1], q[2]] == 10:
                                air[q[0], q[1], q[2]] = False
                                drip[q[0], q[1], q[2]] = 2 if construct and step >= 0.65 * Ls else 1
        spikes.append(dict(space="funnel", big=False, construct=bool(construct)))
    return spikes


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "spider_sequence"
    os.makedirs(out, exist_ok=True)
    layout = "stack" if "--stack" in sys.argv else "collapse" if "--collapse" in sys.argv else "trap"
    Lo = {"stack": layout_stack, "collapse": layout_collapse, "trap": layout_trap}[layout]()
    air, mask, dirt, net = Lo["air"], Lo["mask"], Lo["dirt"], Lo["net"]
    water = Lo.get("water", np.zeros_like(air))
    ymin = W.Y_MIN
    drip = np.zeros(air.shape, np.uint8)
    spikes = add_spikes(air, mask, drip, Lo["space_air"], Lo["keep_clear"], Lo["wall_spikes"], ymin)
    solid = ~air
    X, Y, Z = solid.shape
    meta1, meta3 = Lo["meta1"], Lo["meta3"]
    meta = dict(
        layout=layout, y_min=ymin, size=[X, Y, Z],
        cave1=dict(meta1, offset=Lo["o1"]), lair=dict(meta3, offset=Lo["o3"]), trap=Lo["trap"], burrow=Lo["burrow"],
        construct_span=20, real_span=36,
        spikes=dict(total=len(spikes), big=sum(sp["big"] for sp in spikes), construct=sum(sp["construct"] for sp in spikes),
                    funnel=sum(sp["space"] == "funnel" for sp in spikes)),
    )
    np.savez_compressed(os.path.join(out, "sequence.npz"), solid=solid, mask=mask, dirt=dirt, net=net, drip=drip, water=water,
                        meta=json.dumps(meta))
    write_datapack(out, solid, mask, dirt, net, meta, drip, water)
    t_ = meta["trap"]
    print(meta["layout"], "grid", meta["size"], "| cave1", meta1["length"], "x", meta1["width"], "y", meta1["cave_bottom_y"], meta1["cave_top_y"],
          "| lair", meta3["length"], "x", meta3["width"], "y", meta3["cave_bottom_y"], meta3["cave_top_y"],
          "| fall", t_.get("fall"), "| drop floor y", t_["floor_y"], "net y", t_["net_y"], "lair roof y", t_["lair_roof_y"], "lair floor y", t_["lair_floor_y"],
          "| spikes", meta["spikes"])


def write_datapack(out, solid, mask, dirt, net, meta, drip, water=None):
    ns = "lantern_seq"
    root = os.path.join(out, "lantern-spider-sequence-datapack")
    fdir = os.path.join(root, "data", ns, "function")
    if os.path.isdir(fdir):
        for f in os.listdir(fdir):
            os.remove(os.path.join(fdir, f))
    os.makedirs(fdir, exist_ok=True)
    with open(os.path.join(root, "pack.mcmeta"), "w") as fh:
        json.dump({"pack": {"description": f"Lantern Ring: three-part giant spider fight, block-out ({meta['layout']})",
                            "pack_format": 121, "min_format": 121, "max_format": 121}}, fh)
    at = "execute at @e[type=minecraft:marker,tag=ls_origin,limit=1] run "
    X, Y, Z = solid.shape
    ox, oz = -(X // 2), -(Z // 2)
    body = []
    ys = np.flatnonzero((~solid).any(axis=(0, 2)))
    y_lo, y_hi = int(ys.min()) - 2, min(Y - 1, int(np.flatnonzero(np.isin(mask, (1, 2, 3, 4, 6, 7, 8, 9, 10)).any(axis=(0, 2))).max()) + 2)
    xw = zw = 64; yh = max(1, 32768 // (xw * zw))
    for y0 in range(y_lo, y_hi + 1, yh):
        for x0 in range(0, X, xw):
            for z0 in range(0, Z, zw):
                a = f"~{ox + x0} ~{y0} ~{oz + z0} ~{ox + min(X - 1, x0 + xw - 1)} ~{min(y_hi, y0 + yh - 1)} ~{oz + min(Z - 1, z0 + zw - 1)}"
                body.append(at + f"fill {a} minecraft:tuff replace minecraft:water")
                body.append(at + f"fill {a} minecraft:tuff replace minecraft:lava")
    # spikes: dripstone blocks, a pointed dripstone on each bottom tip, yellow stained glass for hard-light tips
    # (a stand-in until the mod has its own construct-spike block)
    below_air = np.zeros_like(solid); below_air[:, 1:, :] = ~solid[:, :-1, :]
    rock = (drip == 1) & ~below_air
    tipd = (drip == 1) & below_air
    for grid, block in ((~solid, "minecraft:air"), (dirt, "minecraft:coarse_dirt"), (net, "minecraft:cobweb"),
                        (rock, "minecraft:dripstone_block"), (tipd, "minecraft:pointed_dripstone[vertical_direction=down,thickness=tip]"),
                        (drip == 2, "minecraft:yellow_stained_glass"),
                        (water if water is not None else np.zeros_like(solid), "minecraft:water")):
        for y in range(Y):
            for z in range(Z):
                for a, b in W.runs(grid[:, y, z]):
                    body.append(at + f"fill ~{ox + a} ~{y} ~{oz + z} ~{ox + b} ~{y} ~{oz + z} {block}")
    e = meta["cave1"]["entrance"]; o1 = meta["cave1"]["offset"]; s1 = meta["cave1"]["size"]
    tx = o1[0] + s1[0] // 2 + int(round(e["top_x"])) + ox
    tz = o1[1] + s1[2] // 2 + int(round(e["top_z"])) + oz
    body.append(at + f"fill ~{tx - 1} ~{Y} ~{tz - 1} ~{tx + 1} ~{min(Y + 200, 383)} ~{tz + 1} minecraft:air")
    fl = [f"~{ox + x0} ~{oz + z0} ~{ox + min(X + 15, x0 + 199)} ~{oz + min(Z + 15, z0 + 199)}"
          for x0 in range(0, X + 16, 200) for z0 in range(0, Z + 16, 200)]
    body += [at + f"forceload remove {r}" for r in fl]
    how = ("the floor disc over the funnel breaks into the lair" if meta["layout"] in ("collapse", "stack")
           else "the escape burrow at its east end climbs to the funnel trap")
    body += [at + f"execute positioned ~{tx + 4} ~ ~{tz} positioned over motion_blocking_no_leaves run tp @a[distance=..800] ~ ~1 ~",
             "effect give @a minecraft:night_vision 1800 0 true",
             f'tellraw @a {{"text":"Spider sequence carved. The crack next to you leads to cave 1; {how}.","color":"green"}}']
    PART = 20000
    parts = [body[i:i + PART] for i in range(0, len(body), PART)]
    head = ["# Three-part giant spider fight, block-out. Run on land in a normal creative world; it carves under you.",
            "kill @e[type=minecraft:marker,tag=ls_origin]",
            'execute align xz positioned ~0.5 -64 ~0.5 run summon minecraft:marker ~ ~ ~ {Tags:["ls_origin"]}']
    head += [at + f"forceload add {r}" for r in fl]
    head += [f'tellraw @s {{"text":"Carving the spider sequence in {len(parts)} steps...","color":"yellow"}}',
             f"schedule function {ns}:build_part1 40t"]
    with open(os.path.join(fdir, "build.mcfunction"), "w") as fh:
        fh.write("\n".join(head) + "\n")
    for i, part in enumerate(parts):
        nxt = [f"schedule function {ns}:build_part{i + 2} 10t"] if i + 1 < len(parts) else []
        with open(os.path.join(fdir, f"build_part{i + 1}.mcfunction"), "w") as fh:
            fh.write("\n".join(part + nxt) + "\n")


if __name__ == "__main__":
    main()
