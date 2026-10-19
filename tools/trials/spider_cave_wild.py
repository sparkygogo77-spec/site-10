"""Giant-spider cave, round 3: a naturally shaped cavern at real world heights, different every seed (J, 2026-10-19).

J: "give me the y coordinates of the average biome surface block, then where the dome would be placed in accordance
to all of them, while being stretched to the realistic width of an expansive modern cave ... [the spider will] use
its legs to traverse angles at very low and steep degrees and around corners and round columns ... I always need it
in a differently generated (if it has to be limited multiple we can pick from a few designs of them".

So, unlike round 2 (a clean dome):
- the shape is a long, irregular cavern like the big noise ("cheese") caves of 1.18+, built from 3D noise, with side
  lobes (corners), round hourglass columns, and a floor with both gentle and steep slopes;
- it sits at absolute world heights: floor about y -24, roof about y +22, above the lava level (y -54) and below every
  land surface (see SURFACES);
- every seed gives a different cave. The datapack carries six seeds plus a random pick; the mod can later run this
  same recipe with the world seed so every cave is new.

Usage: python spider_cave_wild.py <out_dir> [seed ...]       (default seeds 1-6)
Writes <out>/V<n>.npz, <out>/V<n>_map.png and <out>/lantern-spider-cave-wild-datapack/.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Y_MIN = -64            # world bottom; grid y index 0
GRID_TOP = 72          # the grid runs up to a typical plains surface so the cutaway shows the rock overhead
FLOOR_Y = -24          # middle of the cave floor
LAVA_Y = -54           # caves below this fill with lava; the dens must stay above it
SPAN = 28              # spider leg span the cave is sized for (round 2's D2 spider)

# Typical surface heights in Java 1.18+ terrain (sea level 63). Ranges are the common spread, "avg" the usual middle.
# Read from how the generator shapes each biome, not measured in a world: check against a real seed before relying on
# them for spawning rules.
SURFACES = [
    ("Deep ocean floor", 22, 38, 30), ("Ocean floor", 38, 52, 45), ("River bed", 54, 60, 57),
    ("Swamp, mangrove, beach", 61, 66, 63), ("Mushroom fields", 63, 72, 66), ("Plains, snowy plains", 63, 78, 68),
    ("Desert", 63, 82, 70), ("Forest, birch, dark forest", 63, 90, 72), ("Taiga, jungle, savanna", 63, 95, 74),
    ("Badlands", 65, 100, 78), ("Wooded badlands, savanna plateau", 90, 130, 105), ("Windswept hills", 90, 150, 112),
    ("Meadow, cherry grove", 90, 150, 115), ("Grove, snowy slopes", 110, 190, 145),
    ("Stony, jagged, frozen peaks", 130, 260, 185),
]


def upsample(coarse, shape):
    """Trilinear upsample of a small random grid to `shape`: smooth noise without scipy."""
    out = coarse
    for ax, n in enumerate(shape):
        m = out.shape[ax]
        pos = np.linspace(0, m - 1, n)
        i0 = np.floor(pos).astype(int); i1 = np.minimum(i0 + 1, m - 1); t = pos - i0
        a = np.take(out, i0, axis=ax); b = np.take(out, i1, axis=ax)
        sh = [1] * out.ndim; sh[ax] = n
        out = a * (1 - t.reshape(sh)) + b * t.reshape(sh)
    return out


def noise3(rng, shape, cell):
    c = tuple(max(2, int(math.ceil(n / cell)) + 1) for n in shape)
    return upsample(rng.uniform(-1, 1, c), shape)


def carve_tube(air, mask, pts, rad, tag):
    X, Y, Z = air.shape
    pts = np.asarray(pts, float)
    seg = []
    for p, q in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.linalg.norm(q - p) / 0.7))
        seg += [p + (q - p) * t for t in np.linspace(0, 1, n, endpoint=False)]
    seg.append(pts[-1])
    r = int(math.ceil(rad))
    off = np.mgrid[-r:r + 1, -r:r + 1, -r:r + 1].reshape(3, -1).T
    off = off[(off ** 2).sum(1) <= rad * rad]
    for c in seg:
        idx = np.round(c).astype(int) + off
        ok = (idx[:, 0] >= 0) & (idx[:, 0] < X) & (idx[:, 1] >= 1) & (idx[:, 1] < Y) & (idx[:, 2] >= 0) & (idx[:, 2] < Z)
        idx = idx[ok]
        air[idx[:, 0], idx[:, 1], idx[:, 2]] = True
        mask[idx[:, 0], idx[:, 1], idx[:, 2]] = tag


def build(seed):
    rng = np.random.default_rng(seed)
    A = rng.uniform(62, 78)            # half length (x): 124-156 long
    C = rng.uniform(38, 48)            # half width (z): 76-96 wide
    H = rng.uniform(40, 50)            # floor-to-roof at the middle
    tw = 11                            # burrow / tunnel width
    depth = 18                         # ring tunnel this far under the edge of the floor
    X, Z = int(2 * A + 4 * tw + 30), int(2 * C + 4 * tw + 30)
    Y = GRID_TOP - Y_MIN + 1
    cx, cz = X // 2, Z // 2
    fy = FLOOR_Y - Y_MIN                # floor index
    yc = fy + H * 0.32                  # the widest level sits low, so the floor is broad and the roof arches

    xs = (np.arange(X) - cx)[:, None, None].astype(float)
    ys = (np.arange(Y) - yc)[None, :, None].astype(float)
    zs = (np.arange(Z) - cz)[None, None, :].astype(float)
    tilt = rng.uniform(-0.18, 0.18)     # the whole floor leans one way: gentle ramps across the cave
    ysl = ys - tilt * xs
    vy = np.where(ysl > 0, ysl / (H * 0.68), ysl / (H * 0.32))
    d = 1 - ((xs / A) ** 2 + vy ** 2 + (zs / C) ** 2)
    d = d + 0.32 * noise3(rng, (X, Y, Z), 28) + 0.12 * noise3(rng, (X, Y, Z), 11)
    # side lobes: smaller chambers bulging off the main one make corners to go round
    lobes = []
    for _ in range(rng.integers(2, 4)):
        a = rng.uniform(0, math.tau)
        lx, lz = math.cos(a) * A * 0.85, math.sin(a) * C * 0.85
        la, lc, lh = rng.uniform(22, 34), rng.uniform(16, 26), rng.uniform(14, 24)
        ly = rng.uniform(-2, 8)
        vl = (ysl - ly) / lh
        dl = 1 - (((xs - lx) / la) ** 2 + np.where(vl > 0, vl, vl * 2.2) ** 2 + ((zs - lz) / lc) ** 2)
        d = np.maximum(d, dl + 0.15 * noise3(rng, (X, Y, Z), 9))
        lobes.append([round(lx, 1), round(lz, 1)])
    air = d > 0
    air[:, :max(1, int(fy - 12))] = False          # no cave below the floor zone (tunnels come later)
    mask = np.where(air, 1, 0).astype(np.uint8)

    # Round columns: thick at floor and roof, pinched in the middle (hourglass), like dripstone that grew together.
    cols = []
    for _ in range(rng.integers(4, 8)):
        for _try in range(20):
            px, pz = rng.uniform(-0.7, 0.7) * A, rng.uniform(-0.6, 0.6) * C
            if all(math.hypot(px - q[0], pz - q[1]) > 22 for q in cols) and math.hypot(px + 0.45 * A, pz) > 20:
                break
        r0 = rng.uniform(2.5, 5.5)
        rad = r0 * (1 + 0.9 * ((ys - H * 0.25) / (H * 0.6)) ** 2)
        col = ((xs - px) ** 2 + (zs - pz) ** 2) < rad ** 2
        col = col & air
        air &= ~col; mask[col] = 0
        cols.append([round(px, 1), round(pz, 1), round(r0, 1)])

    # Floor height per column (lowest cave air), used for burrows and the ring tunnel.
    any_air = air.any(1)
    first = np.argmax(air, axis=1).astype(float)
    first[~any_air] = np.nan

    # Outline of the cave at floor level, angle by angle, then the ring tunnel just outside it.
    angs = np.linspace(0, math.tau, 180, endpoint=False)
    rb = np.zeros(len(angs))
    for i, a in enumerate(angs):
        last = 0
        for s in np.arange(0, max(A, C) * 1.6, 1.0):
            x, z = int(round(cx + math.cos(a) * s)), int(round(cz + math.sin(a) * s))
            if not (0 <= x < X and 0 <= z < Z):
                break
            if any_air[x, z]:
                last = s
        rb[i] = last
    rb = np.convolve(np.concatenate([rb[-6:], rb, rb[:6]]), np.ones(13) / 13, "valid")
    ring_off = tw * 0.9
    ring = []
    for a, r in zip(angs, rb):
        x, z = cx + math.cos(a) * (r + ring_off), cz + math.sin(a) * (r + ring_off)
        ring.append((x, fy - depth + 1.5 * math.sin(3 * a), z))
    ring.append(ring[0])
    carve_tube(air, mask, ring, tw / 2, 3)

    holes = []
    nb = 5
    start = rng.uniform(0, 1)
    for i in range(nb):
        k = int((start + i / nb + rng.uniform(-0.03, 0.03)) * len(angs)) % len(angs)
        a, r = angs[k], rb[k]
        in_wall = i % 2 == 1
        rr = r * (0.97 if in_wall else 0.82)
        hx, hz = cx + math.cos(a) * rr, cz + math.sin(a) * rr
        fl = first[int(round(hx)), int(round(hz))]
        fl = fy if np.isnan(fl) else fl
        k2 = (k + 3) % len(angs)
        bot = ring[k2]
        if in_wall:
            carve_tube(air, mask, [(hx, fl + tw / 2, hz), ((hx + bot[0]) / 2, (fl + bot[1]) / 2, (hz + bot[2]) / 2), bot], tw / 2, 2)
        else:
            carve_tube(air, mask, [(hx, fl + 2, hz), (hx, fl - tw * 0.8, hz), bot], tw / 2, 2)
        den = [ring[(k2 + j) % len(angs)] for j in (-3, 0, 3)]
        carve_tube(air, mask, [(p[0], p[1] + 1, p[2]) for p in den], tw * 0.85, 6)
        holes.append(dict(n=i + 1, kind="wall" if in_wall else "floor", x=round(hx - cx, 1), z=round(hz - cz, 1),
                          y=int(fl + Y_MIN)))
    # One cut-through under the long axis.
    carve_tube(air, mask, [ring[0], (cx, fy - depth - 2, cz), ring[90]], tw / 2 - 0.5, 4)

    # Entrance: a crack at the surface, a shaft winding down through the rock, breaking through the roof.
    ex, ez = cx - 0.45 * A, cz + rng.uniform(-0.2, 0.2) * C
    colair = np.flatnonzero(air[int(ex), :, int(ez)])
    roof = colair.max() if len(colair) else fy + H
    helix = []
    turns = 2.5
    for i in range(151):
        t = i / 150
        a = t * turns * math.tau
        helix.append((ex + math.cos(a) * 7, (Y - 1) - ((Y - 1) - (roof + 8)) * t, ez + math.sin(a) * 7))
    carve_tube(air, mask, helix[:14], 1.6, 5)
    carve_tube(air, mask, helix[13:], 2.6, 5)
    carve_tube(air, mask, [helix[-1], (helix[-1][0], roof - 2, helix[-1][2])], 2.6, 5)

    # Measure what we made.
    cave = mask == 1
    cx_any = cave.any(axis=(1, 2)); cz_any = cave.any(axis=(0, 1)); cy_any = cave.any(axis=(0, 2))
    ny = np.flatnonzero(cy_any)
    tun = np.isin(mask, (2, 3, 4, 6))
    meta = dict(
        take=f"V{seed}", seed=seed, span=SPAN, tw=tw, y_min=Y_MIN, floor_y=FLOOR_Y,
        length=int(cx_any.sum()), width=int(cz_any.sum()),
        cave_bottom_y=int(ny.min() + Y_MIN), cave_top_y=int(ny.max() + Y_MIN),
        tunnel_bottom_y=int(np.flatnonzero(tun.any(axis=(0, 2))).min() + Y_MIN),
        roof_at_entrance_y=int(roof + Y_MIN), drop=int(roof - (first[int(ex), int(ez)] if not np.isnan(first[int(ex), int(ez)]) else fy)),
        entrance=dict(x=round(helix[-1][0] - cx, 1), z=round(helix[-1][2] - cz, 1), top_x=round(helix[0][0] - cx, 1),
                      top_z=round(helix[0][2] - cz, 1)),
        holes=holes, columns=cols, lobes=lobes, tilt=round(float(tilt), 2), size=[X, Y, Z],
        floor_area=int((cave.any(1)).sum()),
    )
    return ~air, mask, meta


def draw_map(path, solid, mask, meta):
    X, Y, Z = solid.shape
    s = 3
    im = Image.new("RGB", (X * s, Z * s + 70), (24, 24, 26))
    d = ImageDraw.Draw(im)
    ch = (mask == 1).any(1); tun = np.isin(mask, (2, 3, 4, 6)).any(1); ent = (mask == 5).any(1)
    img = np.zeros((Z, X, 3), np.uint8) + np.array([24, 24, 26], np.uint8)
    img[tun.T] = (120, 74, 40)
    img[ch.T] = (150, 150, 140)
    img[(ch & tun).T] = (190, 130, 70)
    img[ent.T] = (80, 150, 220)
    im.paste(Image.fromarray(img).resize((X * s, Z * s), Image.NEAREST))
    cx, cz = X // 2, Z // 2
    f = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
    for px, pz, r0 in meta["columns"]:
        d.ellipse([(px + cx - r0) * s, (pz + cz - r0) * s, (px + cx + r0) * s, (pz + cz + r0) * s], fill=(70, 70, 66))
    for h in meta["holes"]:
        px, pz = (h["x"] + cx) * s, (h["z"] + cz) * s
        r = meta["tw"] / 2 * s
        d.ellipse([px - r, pz - r, px + r, pz + r], outline=(255, 210, 60), width=3)
        d.text((px - 4, pz - 9), str(h["n"]), font=f, fill=(255, 230, 120))
    sp = meta["span"] / 2 * s
    d.ellipse([cx * s - sp, cz * s - sp, cx * s + sp, cz * s + sp], outline=(230, 60, 60), width=2)
    y0 = Z * s + 6
    d.text((8, y0), f"{meta['take']}: {meta['length']} long × {meta['width']} wide, y {meta['cave_bottom_y']} to {meta['cave_top_y']}", font=f, fill=(235, 235, 235))
    d.text((8, y0 + 20), "grey cave · brown tunnels + dens · yellow holes · blue shaft · dark circles = columns · red = spider", font=f, fill=(170, 170, 170))
    im.save(path)


def runs(row):
    r = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
    return list(zip(r[::2], r[1::2] - 1))


def write_datapack(out, built):
    """Carves each cave into the real world under where you stand, at its real heights. Water and lava inside the
    cave's box are turned to tuff first so aquifers don't flood it."""
    ns = "lantern_wild"
    root = os.path.join(out, "lantern-spider-cave-wild-datapack")
    fdir = os.path.join(root, "data", ns, "function")
    if os.path.isdir(fdir):
        for f in os.listdir(fdir):
            os.remove(os.path.join(fdir, f))
    os.makedirs(fdir, exist_ok=True)
    with open(os.path.join(root, "pack.mcmeta"), "w") as fh:
        json.dump({"pack": {"description": "Lantern Ring: wild giant-spider caves (random pick or V1-V6)",
                            "pack_format": 121, "min_format": 121, "max_format": 121}}, fh)
    at = "execute at @e[type=minecraft:marker,tag=lw_origin,limit=1] run "
    PART = 20000
    names = []
    for take, (solid, mask, meta) in built.items():
        X, Y, Z = solid.shape
        ox, oz = -(X // 2), -(Z // 2)
        t = take.lower(); names.append(t)
        cave = ~solid
        ys = np.flatnonzero(np.isin(mask, (1, 2, 3, 4, 6)).any(axis=(0, 2)))
        y_lo, y_hi = int(ys.min()) - 2, min(Y - 1, int(ys.max()) + 2)
        body = []
        # 1. tuff over any water or lava in the box around the cave (not the shaft: that goes up through the surface)
        xw = 64; zw = 64; yh = max(1, 32768 // (xw * zw))
        for y0 in range(y_lo, y_hi + 1, yh):
            for x0 in range(0, X, xw):
                for z0 in range(0, Z, zw):
                    a = f"~{ox + x0} ~{y0} ~{oz + z0} ~{ox + min(X - 1, x0 + xw - 1)} ~{min(y_hi, y0 + yh - 1)} ~{oz + min(Z - 1, z0 + zw - 1)}"
                    body.append(at + f"fill {a} minecraft:tuff replace minecraft:water")
                    body.append(at + f"fill {a} minecraft:tuff replace minecraft:lava")
        # 2. carve the cave, tunnels and shaft
        for y in range(Y):
            for z in range(Z):
                for a, b in runs(cave[:, y, z]):
                    body.append(at + f"fill ~{ox + a} ~{y} ~{oz + z} ~{ox + b} ~{y} ~{oz + z} minecraft:air")
        # 3. above the grid, the shaft goes straight up to the open sky (mountains are taller than the grid)
        e = meta["entrance"]
        tx, tz = int(round(e["top_x"])), int(round(e["top_z"]))
        body.append(at + f"fill ~{tx - 1} ~{Y} ~{tz - 1} ~{tx + 1} ~{Y + 200} ~{tz + 1} minecraft:air")
        body += [at + f"execute positioned ~{tx + 4} ~ ~{tz} positioned over motion_blocking_no_leaves run tp @a[distance=..600] ~ ~1 ~",
                 "effect give @a minecraft:night_vision 1800 0 true",
                 f'tellraw @a {{"text":"{take} carved under you (cave y {meta["cave_bottom_y"]} to {meta["cave_top_y"]}). The crack next to you is the way in.","color":"green"}}']
        parts = [body[i:i + PART] for i in range(0, len(body), PART)]
        head = [f"# {take}: {meta['length']} x {meta['width']}, y {meta['cave_bottom_y']}..{meta['cave_top_y']}. Run anywhere on land; it carves into the world under you.",
                "kill @e[type=minecraft:marker,tag=lw_origin]",
                'execute align xz positioned ~0.5 -64 ~0.5 run summon minecraft:marker ~ ~ ~ {Tags:["lw_origin"]}',
                f'tellraw @s {{"text":"Carving {take}...","color":"yellow"}}']
        for i, part in enumerate(parts):
            nxt = [f"schedule function {ns}:{t}_part{i + 2} 10t"] if i + 1 < len(parts) else []
            name = t if i == 0 else f"{t}_part{i + 1}"
            with open(os.path.join(fdir, name + ".mcfunction"), "w") as fh:
                fh.write("\n".join((head if i == 0 else []) + part + nxt) + "\n")
        meta["datapack_commands"] = len(body)
    rand = ["# Picks one of the caves at random and carves it under you.",
            "scoreboard objectives add lw_pick dummy",
            f"execute store result score #pick lw_pick run random value 1..{len(names)}"]
    rand += [f"execute if score #pick lw_pick matches {i + 1} run function {ns}:{n}" for i, n in enumerate(names)]
    with open(os.path.join(fdir, "random.mcfunction"), "w") as fh:
        fh.write("\n".join(rand) + "\n")
    return root


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "spider_cave_wild"
    seeds = [int(a) for a in sys.argv[2:]] or [1, 2, 3, 4, 5, 6]
    os.makedirs(out, exist_ok=True)
    built = {}
    for sd in seeds:
        solid, mask, meta = build(sd)
        built[meta["take"]] = (solid, mask, meta)
        draw_map(os.path.join(out, meta["take"] + "_map.png"), solid, mask, meta)
    write_datapack(out, built)
    for take, (solid, mask, meta) in built.items():
        np.savez_compressed(os.path.join(out, take + ".npz"), solid=solid, mask=mask, meta=json.dumps(meta))
        print(take, f"{meta['length']}x{meta['width']}", "y", meta["cave_bottom_y"], meta["cave_top_y"],
              "tunnels down to", meta["tunnel_bottom_y"], "drop", meta["drop"], "cols", len(meta["columns"]),
              "lobes", len(meta["lobes"]), "cmds", meta["datapack_commands"])
    with open(os.path.join(out, "surfaces.json"), "w") as fh:
        json.dump(SURFACES, fh)


if __name__ == "__main__":
    main()
