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


def burrow_web(air, mask, lair, cave1, cx, cz, lair_roof, c1_floor, ymin, tw=9):
    """J (2026-10-19, drawing on the stacked cutaway): "lets make the burrow system more complex like this".
    From the lair's ring tunnel, burrows climb up round the outside of the lair, branch through the rock between the
    two caves with den chambers where they meet, and join cave 1's ring tunnel. Built all the way round (n_spokes),
    and linked spoke to spoke, so the spider can run between the caves without the funnel. Tunnels keep at least 4
    blocks of rock from both caves and the funnel except where they join a tunnel on purpose.
    Tags: 11 web tunnel, 12 den chamber."""
    X, Y, Z = air.shape
    rng = np.random.default_rng(404)
    # keep-out zone: the two caves and the funnel, grown by 4 blocks
    keep = lair | cave1 | (mask == 10)
    for _ in range(4):
        g = keep.copy()
        for ax in range(3):
            g |= np.roll(keep, 1, ax) | np.roll(keep, -1, ax)
        keep = g
    ring3 = np.argwhere((mask == 3) & (np.arange(Y)[None, :, None] < lair_roof))
    ring1 = np.argwhere((mask == 3) & (np.arange(Y)[None, :, None] > c1_floor - 30))

    def nearest_on(cells, a):
        ang = np.arctan2(cells[:, 2] - cz, cells[:, 0] - cx)
        d = np.abs((ang - a + math.pi) % math.tau - math.pi)
        best = cells[d < d.min() + 0.02]
        return best[np.argmax(np.hypot(best[:, 0] - cx, best[:, 2] - cz))].astype(float)

    def clear(p, r):
        """Lift a point until a ball of radius r round it is outside the keep-out zone."""
        p = np.array(p, float)
        for _ in range(60):
            q = np.round(p).astype(int)
            lo = np.maximum(q - int(r), 0); hi = np.minimum(q + int(r) + 1, [X, Y, Z])
            if not keep[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].any():
                return p
            p[1] += 1
            if p[1] > c1_floor - 8:
                # no room going up: push outward instead
                p[1] -= 1
                d = np.array([p[0] - cx, 0, p[2] - cz]); d /= np.linalg.norm(d) + 1e-9
                p += d * 2
        return p

    lair_r = max(np.ptp(np.argwhere(lair.any(1))[:, 0]), 1) / 2
    gap_lo, gap_hi = lair_roof + 6, c1_floor - 10
    # Round 2 of the web (J: "bigger dens and denser spokes, have the system connect the dens properly I guess 5 is
    # cool but with much more spokes for connectivity"): 5 big den rooms round the lair, each with 3 burrows down to
    # the lair's ring tunnel, 2 up to cave 1's ring tunnel, links to both neighbours and across to the dens two over
    # (a star), so every den reaches every other den in one or two tunnels.
    n_dens = 5
    starts = rng.uniform(0, math.tau)
    dens_p, dens = [], []
    for k in range(n_dens):
        a = starts + k / n_dens * math.tau + rng.uniform(-0.1, 0.1)
        p = clear([cx + math.cos(a) * lair_r * 0.78, (gap_lo + gap_hi) / 2 + rng.uniform(-3, 3), cz + math.sin(a) * lair_r * 0.78], 12)
        tang = np.array([-math.sin(a), 0, math.cos(a)])
        # the room: three overlapping balls along the wall, about 30 long, 24 deep, 14 high
        for off, rad in ((-9, 7.5), (0, 8.5), (9, 7.5)):
            W.carve_tube(air, mask, [p + tang * off - [0, 2, 0], p + tang * off + [0, 2, 0]], rad, 12)
        dens_p.append((a, p)); dens.append([int(p[0]), int(p[1] + ymin), int(p[2])])
    n_tunnels = 0
    for k, (a, p) in enumerate(dens_p):
        out = np.array([math.cos(a), 0, math.sin(a)])
        for da in (-0.35, 0.0, 0.35):                                        # down to the lair's ring tunnel
            s0 = nearest_on(ring3, a + da)
            climb = clear(s0 + out * 6 + [0, 12, 0], tw / 2)
            W.carve_tube(air, mask, [s0, s0 + out * 3 + [0, 4, 0], climb, p], tw / 2, 11); n_tunnels += 1
        for da in (-0.2, 0.2):                                               # up to cave 1's ring tunnel
            e1 = nearest_on(ring1, a + da)
            W.carve_tube(air, mask, [p, clear((p + e1) / 2, tw / 2), e1], tw / 2, 11); n_tunnels += 1
        for step in (1, 2):                                                  # to the next den, and across to the one two over
            q = dens_p[(k + step) % n_dens][1]
            mid = clear((p + q) / 2 + [0, rng.uniform(-4, 4), 0], tw / 2)
            W.carve_tube(air, mask, [p, mid, q], tw / 2, 11); n_tunnels += 1
    return dict(dens=dens, den_count=n_dens, tunnels=n_tunnels, tunnel_width=tw)


WEB = "star"                 # burrow web layout: star (round 2), orb, lattice, natural (J's lair note 4)


def _grow(m, n):
    m = m.copy()
    for _ in range(n):
        g = m.copy()
        for ax in range(3):
            g |= np.roll(m, 1, ax) | np.roll(m, -1, ax)
        m = g
    return m


def burrow_grid(air, mask, lair, cave1, cx, cz, lair_roof, c1_floor, ymin, style, tw=9):
    """J's lair note 4 (2026-10-19): "a more maybe organized or natural grid system for the tunnels all around".
    Every layout drapes over the lair's dome: a tunnel point above the lair sits 9 blocks over its roof, one beside it
    sits partway up its wall, so the network wraps the whole lair instead of a flat star in the rock above it.
      orb      a spider's orb web: 10 spokes from the funnel out and down the dome, crossed by 3 rings; 5 dens where
               the middle ring meets every other spoke
      lattice  a planned square grid, 34 blocks apart, inside a ring round the lair's edge; dens at 5 crossings
      natural  scattered chambers joined to their natural neighbours (a relative-neighbourhood graph) by winding,
               uneven tunnels, like an ant nest; dens at the 5 busiest junctions
    All of them drop burrows to the lair's ring tunnel all the way round and climb to cave 1's ring tunnel.
    Tunnels keep 4 blocks of rock from both caves and the funnel except where they join on purpose.
    Tags: 11 web tunnel, 12 den chamber."""
    X, Y, Z = air.shape
    rng = np.random.default_rng({"orb": 501, "lattice": 502, "natural": 503}[style])
    keep = _grow(lair | cave1 | (mask == 10), 4)
    keep_c = _grow(keep, int(math.ceil(tw / 2)))           # centre-line keep-out: the whole tube stays clear
    ring3 = np.argwhere((mask == 3) & (np.arange(Y)[None, :, None] < lair_roof))
    ring1 = np.argwhere((mask == 3) & (np.arange(Y)[None, :, None] > c1_floor - 30))
    foot = lair.any(1)
    fx, fz = np.nonzero(foot)
    A = (fx.max() - fx.min()) / 2
    C = (fz.max() - fz.min()) / 2
    ys_ = np.arange(Y)[None, :, None]
    top = np.where(foot, (lair * ys_).max(1), -1)
    bot_ = np.where(foot, np.where(lair, ys_, 10 ** 6).min(1), -1)
    mid_y = float(np.median(bot_[foot]) + 0.45 * (np.median(top[foot]) - np.median(bot_[foot])))
    gap_hi = c1_floor - 10
    LIM = np.array([X - 1, Y - 1, Z - 1])

    def blocked(c):
        ci = np.clip(np.round(c).astype(int), 0, LIM)
        return bool(keep_c[ci[0], ci[1], ci[2]])

    def shell(x, z, lift=9.0):
        """Height of the web at (x, z): over the dome, or partway up the wall beside it."""
        xi, zi = int(round(min(X - 1, max(0, x)))), int(round(min(Z - 1, max(0, z))))
        r = 3
        win = top[max(0, xi - r):xi + r + 1, max(0, zi - r):zi + r + 1]
        h = win.max()
        if h < 0:
            return mid_y
        return min(gap_hi, max(mid_y, h + lift))

    def ell(a, s_):
        return cx + math.cos(a) * A * s_, cz + math.sin(a) * C * s_

    def P(x, z, lift=9.0):
        return np.array([x, shell(x, z, lift), z], float)

    stats = {"tunnels": 0, "length": 0.0}

    def carve_safe(pts, rad):
        """Carve a polyline, skipping any stretch whose centre would bring the tube within 4 blocks of a cave."""
        pts = np.asarray(pts, float)
        run = []
        for p_, q_ in zip(pts[:-1], pts[1:]):
            n = max(1, int(np.linalg.norm(q_ - p_) / 1.5))
            for t in np.linspace(0, 1, n, endpoint=False):
                c = p_ + (q_ - p_) * t
                if blocked(c):
                    if len(run) > 1:
                        W.carve_tube(air, mask, run, rad, 11)
                    run = []
                else:
                    run.append(c)
        if not blocked(pts[-1]):
            run.append(pts[-1])
        if len(run) > 1:
            W.carve_tube(air, mask, run, rad, 11)
        stats["tunnels"] += 1
        stats["length"] += float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())

    def nearest_on(cells, a):
        ang = np.arctan2(cells[:, 2] - cz, cells[:, 0] - cx)
        d = np.abs((ang - a + math.pi) % math.tau - math.pi)
        best = cells[d < d.min() + 0.02]
        return best[np.argmax(np.hypot(best[:, 0] - cx, best[:, 2] - cz))].astype(float)

    def drop_to_lair(p_):
        """A burrow from a web point down to the lair's ring tunnel below it."""
        a = math.atan2(p_[2] - cz, p_[0] - cx)
        s0 = nearest_on(ring3, a)
        out = np.array([math.cos(a), 0, math.sin(a)])
        W.carve_tube(air, mask, [p_, p_ + out * 6 - np.array([0, 6, 0]), s0 + out * 4 + np.array([0, 6, 0]), s0], tw / 2, 11)
        stats["tunnels"] += 1

    def climb_to_cave1(p_):
        a = math.atan2(p_[2] - cz, p_[0] - cx)
        e1 = nearest_on(ring1, a)
        W.carve_tube(air, mask, [p_, (p_ + e1) / 2 + np.array([0, 4, 0]), e1], tw / 2, 11)
        stats["tunnels"] += 1

    dens = []

    def den(p_, a):
        tang = np.array([-math.sin(a), 0, math.cos(a)])
        for off, rad in ((-9, 7.5), (0, 8.5), (9, 7.5)):
            W.carve_tube(air, mask, [p_ + tang * off - np.array([0, 2, 0]), p_ + tang * off + np.array([0, 2, 0])], rad, 12)
        dens.append([int(p_[0]), int(p_[1] + ymin), int(p_[2])])

    if style == "orb":
        n_sp, rings = 10, (0.42, 0.72, 1.06)
        a0 = rng.uniform(0, math.tau)
        for k in range(n_sp):                                         # spokes, out and down the dome
            a = a0 + k / n_sp * math.tau
            carve_safe([P(*ell(a, s_)) for s_ in np.linspace(0.3, 1.18, 14)], tw / 2)
            drop_to_lair(P(*ell(a, 1.18)))
            if k % 2 == 1:
                climb_to_cave1(P(*ell(a, 0.42)))
        for s_ in rings:                                              # rings, each a loop round the whole lair
            carve_safe([P(*ell(a0 + j / 72 * math.tau, s_)) for j in range(73)], tw / 2 - (0.5 if s_ < 0.5 else 0))
        for k in range(0, n_sp, 2):
            a = a0 + k / n_sp * math.tau
            den(P(*ell(a, 0.72)), a)
    elif style == "lattice":
        sp_, lim = 34, 1.1
        rot = rng.uniform(-0.3, 0.3)
        ca, sa = math.cos(rot), math.sin(rot)
        n_ = int(max(A, C) * lim / sp_) + 1

        def to_w(u, v):
            return cx + u * ca - v * sa, cz + u * sa + v * ca

        def inside(u, v):
            x, z = to_w(u, v)
            return ((x - cx) / (A * lim)) ** 2 + ((z - cz) / (C * lim)) ** 2 <= 1
        for axis in (0, 1):
            for k in range(-n_, n_ + 1):
                line = []
                for t in np.arange(-n_ * sp_, n_ * sp_ + 1, 3.0):
                    u, v = (k * sp_, t) if axis == 0 else (t, k * sp_)
                    if inside(u, v):
                        line.append(P(*to_w(u, v)))
                    else:
                        if len(line) > 1:
                            carve_safe(line, tw / 2)
                        line = []
                if len(line) > 1:
                    carve_safe(line, tw / 2)
        carve_safe([P(*ell(j / 72 * math.tau, lim)) for j in range(73)], tw / 2)   # the edge ring closing the grid
        for k in range(12):
            a = k / 12 * math.tau + 0.13
            drop_to_lair(P(*ell(a, lim)))
            if k % 3 == 0:
                climb_to_cave1(P(*ell(a, 0.55)))
        cand = []
        for u in range(-n_, n_ + 1):
            for v in range(-n_, n_ + 1):
                if not inside(u * sp_, v * sp_):
                    continue
                x, z = to_w(u * sp_, v * sp_)
                rr = math.hypot((x - cx) / A, (z - cz) / C)
                if 0.45 <= rr <= 0.9:
                    cand.append((math.atan2(z - cz, x - cx), x, z))
        cand.sort()
        for j in range(5):
            a, x, z = cand[int(j * len(cand) / 5)]
            den(P(x, z), a)
    else:   # natural
        nodes = []
        for _ in range(4000):
            if len(nodes) >= 34:
                break
            a = rng.uniform(0, math.tau)
            r = math.sqrt(rng.uniform(0.16, 1.32))
            x, z = ell(a, r)
            p_ = P(x, z, lift=rng.uniform(7, 14))
            if all(np.linalg.norm(p_ - q) >= 30 for q in nodes) and not blocked(p_):
                nodes.append(p_)
        nodes = np.array(nodes)
        n_ = len(nodes)
        D = np.linalg.norm(nodes[:, None] - nodes[None], axis=2)
        edges = []
        for i in range(n_):                                           # relative neighbourhood graph
            for j in range(i + 1, n_):
                if not any(max(D[i, k], D[j, k]) < D[i, j] for k in range(n_) if k not in (i, j)):
                    edges.append((i, j))
        deg = np.zeros(n_, int)
        for i, j in edges:
            p_, q_ = nodes[i], nodes[j]
            side = np.cross(q_ - p_, [0, 1, 0])
            side /= np.linalg.norm(side) + 1e-9
            pts = [p_]
            for t in (0.25, 0.5, 0.75):                               # a winding line, not a straight bore
                pts.append(p_ + (q_ - p_) * t + side * rng.normal(0, 4.5) + np.array([0, rng.normal(0, 2), 0]))
            pts.append(q_)
            carve_safe(pts, rng.uniform(3.6, 5.0))
            deg[i] += 1
            deg[j] += 1
        r_of = np.hypot((nodes[:, 0] - cx) / A, (nodes[:, 2] - cz) / C)
        for i in np.argsort(-r_of)[:9]:
            drop_to_lair(nodes[i])
        for i in np.argsort(r_of)[:4]:
            climb_to_cave1(nodes[i])
        chosen = []
        for i in np.argsort(-deg):
            if all(np.linalg.norm(nodes[i] - nodes[c]) > 60 for c in chosen):
                chosen.append(i)
            if len(chosen) == 5:
                break
        for i in chosen:
            den(nodes[i], math.atan2(nodes[i][2] - cz, nodes[i][0] - cx))
        stats["nodes"] = int(n_)
        stats["edges"] = len(edges)
    out = dict(style=style, dens=dens, den_count=len(dens), tunnels=stats["tunnels"], tunnel_length=int(stats["length"]), tunnel_width=tw)
    for k in ("nodes", "edges"):
        if k in stats:
            out[k] = stats[k]
    return out


def layout_stack(short=False):
    """J (2026-10-19): "I need better positioning, it should be straight over the larger one and the funnel should be a
    great distance but maybe theres water in some way always in the center of this larger arena below".
    Cave 1 is centred straight over the lair; its floor disc breaks into a long spiked funnel that opens through the
    middle of the lair roof, and you land in a pool in the centre of the lair floor (water: no fall damage). No net.
    Cave 1's floor is at about y 60, so this needs mountains above it (surface about y 120+).
    short=True (J: "Both, by terrain"): cave 1's floor at about y 35 for an ~80-block fall, which fits under hills and
    plateaus (surface about y 100+). The mod picks long or short from the height of the ground above."""
    W.GRID_TOP = 105 if short else 130
    s1, m1, meta1 = W.build(seed=21, scale=1.0, H=30, floor_y=35 if short else 60, depth=6, name="cave1", shaft=True, shaft_on_cut=True)
    s3, m3, meta3 = W.build(seed=11, scale=1.6, H=56, floor_y=-46, depth=8, name="lair", shaft=False)
    X1, Y, Z1 = s1.shape
    X3, _, Z3 = s3.shape
    X, Z = max(X1, X3) + 80, max(Z1, Z3) + 80          # room round the lair for the burrow web
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
    nest = (burrow_web(air, mask, l3, c1, tx, zc, lair_roof, fy, ymin) if WEB == "star" else
            burrow_grid(air, mask, l3, c1, tx, zc, lair_roof, fy, ymin, WEB))
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
                fall=int(fy - lair_floor), pool=dict(radius=POOL_R, depth=4), kind="stacked collapse (short)" if short else "stacked collapse",
                needs_surface_y=int(meta1["cave_top_y"] + 30), burrow_web=nest)
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
    short = "--short" in sys.argv
    global WEB
    if "--web" in sys.argv:
        WEB = sys.argv[sys.argv.index("--web") + 1]
    Lo = {"stack": lambda: layout_stack(short), "collapse": layout_collapse, "trap": layout_trap}[layout]()
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
    y_lo, y_hi = int(ys.min()) - 2, min(Y - 1, int(np.flatnonzero(np.isin(mask, (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12)).any(axis=(0, 2))).max()) + 2)
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
