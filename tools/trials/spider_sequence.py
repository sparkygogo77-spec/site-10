"""Block-out of the three-part giant-spider fight (docs/plans/trials/2026-10-19-spider-boss-sequence.md).

  1. The run      a wild cave (round 3 recipe) with the yellow construct spider; its entrance shaft comes down from
                  the surface.
  2. Funnel trap  a small silk-walled room (24 across) above the edge of the lair. Its floor is a 3-block layer of
                  webbed dirt hanging over a drop; one escape burrow climbs up to it from cave 1.
  3. The lair     the W1 cave J liked (seed 11, 1.6x), lowered so it keeps its full height, with no shaft of its own:
                  the only way in is falling through the trap floor into the cobweb net.

Cave 1 and the lair sit side by side (cave 1 to the west) on one grid, world y -64 to 72.

Usage: python spider_sequence.py <out_dir>
Writes <out>/sequence.npz (solid, mask, dirt, net, meta) and a datapack.
"""
import json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spider_cave_wild as W

GAP = 50                     # rock between cave 1 and the lair
TRAP_R = 12                  # funnel trap: radius (24 across)
TRAP_FLOOR_Y = 18            # top of the webbed dirt floor
TRAP_H = 14                  # floor to roof
DIRT = 3                     # floor thickness
SHAFT_R = 10                 # the drop under the trap floor
NET_BELOW = 12               # the net hangs this far under the trap floor


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "spider_sequence"
    os.makedirs(out, exist_ok=True)
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

    # Funnel trap above the lair's west edge, where its roof is still high enough to drop through.
    lair_cave = mask == 1
    lair_cave[:o3[0]] = False
    tx = o3[0] + int(meta3["length"] * 0.18) + 40
    col = np.flatnonzero(lair_cave[tx, :, zc])
    while not len(col):
        tx += 4
        col = np.flatnonzero(lair_cave[tx, :, zc])
    lair_roof = int(col.max())
    fy = TRAP_FLOOR_Y - ymin                       # trap floor index (top of the dirt)
    xs = (np.arange(X) - tx)[:, None, None]
    zs = (np.arange(Z) - zc)[None, None, :]
    ys = np.arange(Y)[None, :, None]
    rr = np.sqrt(xs ** 2 + zs ** 2)
    # room: straight-ish silk walls that lean in toward the roof (a funnel turned upside down)
    t = np.clip((ys - fy) / TRAP_H, 0, 1)
    room = (ys > fy) & (ys <= fy + TRAP_H) & (rr <= TRAP_R * (1 - 0.45 * t ** 2))
    air |= room; mask[room] = 7
    # webbed dirt floor (solid, its own material) and the drop under it down into the lair roof
    dirt = (ys > fy - DIRT) & (ys <= fy) & (rr <= TRAP_R + 0.5)
    drop = (ys <= fy - DIRT) & (ys > lair_roof - 2) & (rr <= SHAFT_R * (1 + 0.25 * (fy - DIRT - ys) / max(1, fy - lair_roof)))
    air |= drop; mask[drop & (mask == 0)] = 9
    air &= ~dirt
    # the cobweb net: one layer across the drop
    net_y = fy - NET_BELOW
    net = np.zeros_like(air)
    net[:, net_y, :] = (rr[:, 0, :] <= SHAFT_R * 1.1) & air[:, net_y, :]

    # Escape burrow: from a floor hole near cave 1's east end up into the trap's west wall.
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

    solid = ~air
    meta = dict(
        y_min=ymin, size=[X, Y, Z], cave1=dict(meta1, offset=o1), lair=dict(meta3, offset=o3),
        trap=dict(x=int(tx), z=int(zc), floor_y=TRAP_FLOOR_Y, radius=TRAP_R, height=TRAP_H, dirt=DIRT,
                  net_y=int(net_y + ymin), lair_roof_y=int(lair_roof + ymin),
                  lair_floor_y=int(np.flatnonzero(lair_cave[tx, :, zc]).min() + ymin)),
        burrow=dict(start=[int(start[0]), int(start[1] + ymin), int(start[2])], end=[int(end[0]), int(end[1] + ymin), int(end[2])]),
        construct_span=20, real_span=36,
    )
    np.savez_compressed(os.path.join(out, "sequence.npz"), solid=solid, mask=mask, dirt=dirt, net=net, meta=json.dumps(meta))
    write_datapack(out, solid, mask, dirt, net, meta)
    t_ = meta["trap"]
    print("grid", meta["size"], "| cave1", meta1["length"], "x", meta1["width"], "y", meta1["cave_bottom_y"], meta1["cave_top_y"],
          "| lair", meta3["length"], "x", meta3["width"], "y", meta3["cave_bottom_y"], meta3["cave_top_y"],
          "| trap floor y", t_["floor_y"], "net y", t_["net_y"], "lair roof y", t_["lair_roof_y"], "lair floor y", t_["lair_floor_y"],
          "| burrow", meta["burrow"])


def write_datapack(out, solid, mask, dirt, net, meta):
    ns = "lantern_seq"
    root = os.path.join(out, "lantern-spider-sequence-datapack")
    fdir = os.path.join(root, "data", ns, "function")
    if os.path.isdir(fdir):
        for f in os.listdir(fdir):
            os.remove(os.path.join(fdir, f))
    os.makedirs(fdir, exist_ok=True)
    with open(os.path.join(root, "pack.mcmeta"), "w") as fh:
        json.dump({"pack": {"description": "Lantern Ring: three-part giant spider fight, block-out",
                            "pack_format": 121, "min_format": 121, "max_format": 121}}, fh)
    at = "execute at @e[type=minecraft:marker,tag=ls_origin,limit=1] run "
    X, Y, Z = solid.shape
    ox, oz = -(X // 2), -(Z // 2)
    body = []
    ys = np.flatnonzero((~solid).any(axis=(0, 2)))
    y_lo, y_hi = int(ys.min()) - 2, min(Y - 1, int(np.flatnonzero(np.isin(mask, (1, 2, 3, 4, 6, 7, 8, 9)).any(axis=(0, 2))).max()) + 2)
    xw = zw = 64; yh = max(1, 32768 // (xw * zw))
    for y0 in range(y_lo, y_hi + 1, yh):
        for x0 in range(0, X, xw):
            for z0 in range(0, Z, zw):
                a = f"~{ox + x0} ~{y0} ~{oz + z0} ~{ox + min(X - 1, x0 + xw - 1)} ~{min(y_hi, y0 + yh - 1)} ~{oz + min(Z - 1, z0 + zw - 1)}"
                body.append(at + f"fill {a} minecraft:tuff replace minecraft:water")
                body.append(at + f"fill {a} minecraft:tuff replace minecraft:lava")
    for grid, block in ((~solid, "minecraft:air"), (dirt, "minecraft:coarse_dirt"), (net, "minecraft:cobweb")):
        for y in range(Y):
            for z in range(Z):
                for a, b in W.runs(grid[:, y, z]):
                    body.append(at + f"fill ~{ox + a} ~{y} ~{oz + z} ~{ox + b} ~{y} ~{oz + z} {block}")
    e = meta["cave1"]["entrance"]; o1 = meta["cave1"]["offset"]; s1 = meta["cave1"]["size"]
    tx = o1[0] + s1[0] // 2 + int(round(e["top_x"])) + ox
    tz = o1[1] + s1[2] // 2 + int(round(e["top_z"])) + oz
    body.append(at + f"fill ~{tx - 1} ~{Y} ~{tz - 1} ~{tx + 1} ~{Y + 200} ~{tz + 1} minecraft:air")
    fl = [f"~{ox + x0} ~{oz + z0} ~{ox + min(X + 15, x0 + 199)} ~{oz + min(Z + 15, z0 + 199)}"
          for x0 in range(0, X + 16, 200) for z0 in range(0, Z + 16, 200)]
    body += [at + f"forceload remove {r}" for r in fl]
    body += [at + f"execute positioned ~{tx + 4} ~ ~{tz} positioned over motion_blocking_no_leaves run tp @a[distance=..800] ~ ~1 ~",
             "effect give @a minecraft:night_vision 1800 0 true",
             'tellraw @a {"text":"Spider sequence carved. The crack next to you leads to cave 1; the escape burrow at its east end climbs to the funnel trap.","color":"green"}']
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
