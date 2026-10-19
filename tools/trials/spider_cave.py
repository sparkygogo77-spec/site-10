"""Giant-spider arena cave: block layout study (J, 2026-10-19).

"a large generated cave meant for a very large spider to have enough space to move quickly within, with burrows
around the edge giving it tunnels to escape through and pop back up through another hole".
Size first, no models or animations yet.

Makes three takes (C1, C2, C3) at different spider sizes. For each take it writes:
  <out>/<take>.npz         solid grid (1 = stone) + tunnel/burrow mask + metadata, read by spider_cave_blend.py
  <out>/<take>_map.png     top-down map: floor, burrow holes, tunnels under the floor
  <out>/datapack/...       /function lantern_cave:<take>  builds it in a test world, east of where you stand

Usage: python spider_cave.py <out_dir>
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# span = spider leg span in blocks. R = chamber floor radius. H = dome height above the floor.
# tw = burrow / tunnel width. depth = how far the ring tunnel runs under the floor.
# cover = solid rock over the top of the dome. Round 1 (C1-C3: 44/64/88 across, 6-10 burrows, side entrance) was
# "go even bigger", entrance from above, larger den tunnels, fewer wider holes, buried deep (J, 2026-10-19).
TAKES = {
    "D1": dict(span=24, R=55, H=40, burrows=5, tw=10, depth=18, cover=30, pillars=3, seed=21),
    "D2": dict(span=28, R=65, H=46, burrows=5, tw=11, depth=20, cover=32, pillars=4, seed=22),
    "D3": dict(span=32, R=75, H=52, burrows=6, tw=12, depth=22, cover=34, pillars=4, seed=23),
}


def value_noise(rng, n):
    """Smooth periodic 1D noise over an angle, n samples, roughly -1..1."""
    k = rng.normal(size=6)
    ph = rng.uniform(0, math.tau, 6)
    a = np.linspace(0, math.tau, n, endpoint=False)
    return sum(k[i] * np.sin((i + 2) * a + ph[i]) / (i + 2) for i in range(6)) / 1.2


def carve_tube(air, mask, pts, rad, tag):
    """Carve spheres of radius rad along a polyline of (x, y, z) points; mark them in mask with tag."""
    X, Y, Z = air.shape
    pts = np.asarray(pts, float)
    seg = []
    for p, q in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.linalg.norm(q - p) / 0.7))
        for t in np.linspace(0, 1, n, endpoint=False):
            seg.append(p + (q - p) * t)
    seg.append(pts[-1])
    r = int(math.ceil(rad))
    off = np.mgrid[-r:r + 1, -r:r + 1, -r:r + 1].reshape(3, -1).T
    off = off[(off ** 2).sum(1) <= rad * rad]
    for c in seg:
        idx = np.round(c).astype(int) + off
        ok = (idx[:, 0] >= 0) & (idx[:, 0] < X) & (idx[:, 1] >= 1) & (idx[:, 1] < Y - 1) & (idx[:, 2] >= 0) & (idx[:, 2] < Z)
        idx = idx[ok]
        air[idx[:, 0], idx[:, 1], idx[:, 2]] = True
        mask[idx[:, 0], idx[:, 1], idx[:, 2]] = tag


def build(take, p):
    rng = np.random.default_rng(p["seed"])
    R, H, tw, depth = p["R"], p["H"], p["tw"], p["depth"]
    ring_r = R + tw * 0.9          # the escape ring runs just outside the chamber wall, under the floor
    half = int(ring_r + tw + 6)
    X = Z = 2 * half + 1
    y_floor = depth + tw + 3       # floor level (blocks of rock under the ring tunnel)
    Y = y_floor + H + p["cover"]
    cx = cz = half

    air = np.zeros((X, Y, Z), bool)
    mask = np.zeros((X, Y, Z), np.uint8)  # 1 chamber, 2 burrow, 3 ring tunnel, 4 cross tunnel, 5 entrance, 6 den

    # Chamber: a wide, low dome. Wall radius wobbles with the angle so it reads as a cave, not a bowl.
    xs, zs = np.meshgrid(np.arange(X) - cx, np.arange(Z) - cz, indexing="ij")
    ang = (np.arctan2(zs, xs) % math.tau)
    wob = value_noise(rng, 360)
    wall = R * (1 + 0.10 * wob[(ang / math.tau * 360).astype(int) % 360])
    rn = np.sqrt(xs ** 2 + zs ** 2) / wall
    bump = rng.normal(size=(X, Z))
    from_noise = np.real(np.fft.ifft2(np.fft.fft2(bump) * np.exp(-((np.fft.fftfreq(X)[:, None] ** 2 + np.fft.fftfreq(Z)[None] ** 2) * 900))))
    from_noise /= np.abs(from_noise).max() + 1e-9
    floor_h = y_floor + 1.5 * rn ** 2 + 1.0 * from_noise          # nearly flat: room to run
    ceil_h = y_floor + H * np.sqrt(np.clip(1 - rn ** 2.2, 0, 1)) + 2.5 * from_noise
    ceil_h = np.maximum(ceil_h, y_floor + 5) * (rn < 1)          # walls stay at least 5 high at the edge
    yy = np.arange(Y)[None, :, None]
    ch = (rn[:, None, :] < 1) & (yy > floor_h[:, None, :]) & (yy < ceil_h[:, None, :])
    air |= ch
    mask[ch] = 1

    # Pillars of rock for cover (few, so the spider can still sprint).
    pil = []
    for i in range(p["pillars"]):
        a = i / p["pillars"] * math.tau + rng.uniform(-0.3, 0.3)
        d = R * rng.uniform(0.38, 0.55)
        px, pz = cx + math.cos(a) * d, cz + math.sin(a) * d
        pr = rng.uniform(2.0, 3.2) * (R / 32) ** 0.5 + 1
        if math.hypot(px - (cx - 0.55 * R), pz - cz) < pr + 12:   # keep the drop from the entrance shaft clear
            continue
        col = (xs - px) ** 2 + (zs - pz) ** 2 < pr ** 2
        col3 = col[:, None, :] & (mask == 1)
        air[col3] = False
        mask[col3] = 0
        pil.append([round(px - cx, 1), round(pz - cz, 1), round(pr, 1)])

    # Ring tunnel: a loop under the edge of the floor, gently rising and falling.
    y_ring = y_floor - depth
    ring = []
    for i in range(181):
        a = i / 180 * math.tau
        ring.append((cx + math.cos(a) * ring_r, y_ring + 1.5 * math.sin(3 * a), cz + math.sin(a) * ring_r))
    carve_tube(air, mask, ring, tw / 2, 3)

    # Burrows: holes in the floor near the wall (even) and in the wall base (odd), each a sloped shaft to the ring.
    holes = []
    nb = p["burrows"]
    for i in range(nb):
        a = i / nb * math.tau + rng.uniform(-0.15, 0.15)
        in_wall = i % 2 == 1
        rr = R * (0.98 if in_wall else 0.80)
        top = (cx + math.cos(a) * rr, y_floor + (tw / 2 if in_wall else 0.5), cz + math.sin(a) * rr)
        mid = (cx + math.cos(a + 0.08) * (rr + ring_r) / 2, (top[1] + y_ring) / 2, cz + math.sin(a + 0.08) * (rr + ring_r) / 2)
        bot = (cx + math.cos(a + 0.16) * ring_r, y_ring + 1.5 * math.sin(3 * (a + 0.16)), cz + math.sin(a + 0.16) * ring_r)
        if not in_wall:   # floor holes drop straight down first so they read as pits
            carve_tube(air, mask, [(top[0], y_floor + 1, top[2]), (top[0], y_floor - tw * 0.8, top[2]), bot], tw / 2, 2)
        else:
            carve_tube(air, mask, [top, mid, bot], tw / 2, 2)
        # a den where the burrow meets the ring: a wide pocket for the spider to sit in
        den = [(cx + math.cos(a + 0.16 + t) * ring_r, y_ring + 1, cz + math.sin(a + 0.16 + t) * ring_r) for t in (-0.07, 0, 0.07)]
        carve_tube(air, mask, den, tw * 0.85, 6)
        holes.append(dict(n=i + 1, kind="wall" if in_wall else "floor", x=round(top[0] - cx, 1), z=round(top[2] - cz, 1)))

    # Two cross tunnels under the floor (cut-throughs), deeper than the ring so they pass under it at the ends.
    y_cross = y_ring - 1
    for a in (0.5, 0.5 + math.pi / 2):
        p0 = (cx + math.cos(a) * ring_r, y_ring, cz + math.sin(a) * ring_r)
        p1 = (cx + math.cos(a + math.pi) * ring_r, y_ring, cz + math.sin(a + math.pi) * ring_r)
        mid = (cx, y_cross - 1, cz)
        carve_tube(air, mask, [p0, mid, p1], tw / 2 - 0.5, 4)
    y_cross_used = y_cross - 1

    # Player entrance from above: a narrow crack at the surface (no other sign of the dome), a shaft that winds
    # down through the cover, then breaks through the dome roof. You drop (or fly) the rest of the way.
    ex, ez = cx - 0.55 * R, cz          # on the cut line, so the cutaway slices through the shaft
    roof = y_floor + H * math.sqrt(max(0.0, 1 - 0.57 ** 2.2))
    y_top, y_low = Y - 1, roof + 8
    turns = 2.0
    helix = []
    for i in range(121):
        t = i / 120
        a = t * turns * math.tau
        helix.append((ex + math.cos(a) * 7, y_top - (y_top - y_low) * t, ez + math.sin(a) * 7))
    carve_tube(air, mask, helix[:12], 1.6, 5)                       # 3-wide crack at the top
    carve_tube(air, mask, helix[11:], 2.6, 5)                       # 5-wide shaft lower down
    carve_tube(air, mask, [helix[-1], (helix[-1][0], roof - 3, helix[-1][2])], 2.6, 5)
    entrance = dict(x=round(helix[-1][0] - cx, 1), z=round(helix[-1][2] - cz, 1), roof=int(roof),
                    drop=int(roof - y_floor), top_x=round(helix[0][0] - cx, 1), top_z=round(helix[0][2] - cz, 1))

    solid = ~air
    floor_area = int((rn < 1).sum())
    meta = dict(take=take, **{k: v for k, v in p.items() if k != "seed"}, size=[X, Y, Z], y_floor=int(y_floor),
                y_ring=int(y_ring), y_cross=int(y_cross_used), across=int(2 * R), ring_length=int(math.tau * ring_r),
                floor_area=floor_area, holes=holes, pillar_list=pil, entrance=entrance,
                laps_note=f"a spider at 8 blocks/s crosses the floor in {2 * R / 8:.1f} s and laps the ring in {math.tau * ring_r / 8:.1f} s")
    return solid, mask, meta


def draw_map(path, solid, mask, meta):
    X, Y, Z = solid.shape
    s = max(3, 640 // X)
    im = Image.new("RGB", (X * s, Z * s + 90), (24, 24, 26))
    d = ImageDraw.Draw(im)
    tun = np.isin(mask, (2, 3, 4, 6)).any(1)
    ch = (mask == 1).any(1)
    ent = (mask == 5).any(1)
    for x in range(X):
        for z in range(Z):
            c = None
            if tun[x, z]:
                c = (120, 74, 40)
            if ch[x, z]:
                c = (150, 150, 140) if not tun[x, z] else (190, 130, 70)
            if ent[x, z]:
                c = (80, 170, 220)
            if c:
                d.rectangle([x * s, z * s, x * s + s - 1, z * s + s - 1], fill=c)
    cx = cz = X // 2
    f = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
    for h in meta["holes"]:
        px, pz = (h["x"] + cx) * s, (h["z"] + cz) * s
        r = meta["tw"] / 2 * s
        d.ellipse([px - r, pz - r, px + r, pz + r], outline=(255, 210, 60), width=3)
        d.text((px - 5, pz - 9), str(h["n"]), font=f, fill=(255, 230, 120))
    for px, pz, pr in meta["pillar_list"]:
        d.ellipse([(px + cx - pr) * s, (pz + cz - pr) * s, (px + cx + pr) * s, (pz + cz + pr) * s], fill=(70, 70, 66))
    # spider and player to scale, centre
    sp = meta["span"] / 2 * s
    d.ellipse([cx * s - sp, cz * s - sp, cx * s + sp, cz * s + sp], outline=(230, 60, 60), width=2)
    d.rectangle([cx * s + sp + 6, cz * s - 1, cx * s + sp + 6 + max(2, int(0.6 * s)), cz * s + max(2, int(0.6 * s))], fill=(60, 230, 110))
    y0 = Z * s + 6
    lines = [(f"{meta['take']}: {meta['across']} across, dome {meta['H']} high, {meta['cover']} rock on top", (235, 235, 235)),
             (f"{len(meta['holes'])} burrows {meta['tw']} wide · spider {meta['span']}-block leg span (red)", (235, 235, 235)),
             ("brown: tunnels + dens under the floor · blue: shaft from the surface", (170, 170, 170)),
             (meta["laps_note"], (170, 170, 170))]
    for k, (txt, col) in enumerate(lines):
        d.text((8, y0 + k * 20), txt, font=f, fill=col)
    im.save(path)


def runs(row):
    """Start/end index pairs of True runs in a 1D bool array."""
    r = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
    return list(zip(r[::2], r[1::2] - 1))


def write_datapack(out, takes):
    """One build per take, centred on where you stand. Big takes pass the 65,536-command limit for one function
    call, so the build is split into parts chained with /schedule; every command runs at a marker, so parts don't
    depend on who runs them."""
    ns = "lantern_cave"
    root = os.path.join(out, "lantern-spider-cave-datapack")
    fdir = os.path.join(root, "data", ns, "function")
    if os.path.isdir(fdir):
        for f in os.listdir(fdir):
            os.remove(os.path.join(fdir, f))
    os.makedirs(fdir, exist_ok=True)
    names = ", ".join(takes)
    with open(os.path.join(root, "pack.mcmeta"), "w") as fh:
        json.dump({"pack": {"description": f"Lantern Ring: giant spider cave size test ({names})",
                            "pack_format": 121, "min_format": 121, "max_format": 121}}, fh)
    at = "execute at @e[type=minecraft:marker,tag=lc_origin,limit=1] run "
    PART = 20000
    for take, (solid, mask, meta) in takes.items():
        X, Y, Z = solid.shape
        o = -(X // 2)   # the box is centred on you; it rises from your feet
        t = take.lower()
        body = []
        xs_ = max(1, -(-X * Z // 32768))           # rock box in slabs (and x strips) under the 32,768-block fill limit
        xw = -(-X // xs_)
        step = max(1, 32768 // (xw * Z))
        slabs = [(x0, min(X - 1, x0 + xw - 1), y, min(Y - 1, y + step - 1)) for y in range(0, Y, step) for x0 in range(0, X, xw)]
        for x0, x1, y0, y1 in slabs:
            body.append(at + f"fill ~{o + x0} ~{y0} ~{o} ~{o + x1} ~{y1} ~{o + Z - 1} minecraft:deepslate")
        air = ~solid
        for y in range(Y):
            for z in range(Z):
                for a, b in runs(air[:, y, z]):
                    body.append(at + f"fill ~{o + a} ~{y} ~{o + z} ~{o + b} ~{y} ~{o + z} minecraft:air")
        e = meta["entrance"]
        body += [at + f"tp @a[distance=..300] ~{e['top_x']} ~{Y + 1} ~{e['top_z']}",
                 "effect give @a minecraft:night_vision 1800 0 true",
                 f'tellraw @a {{"text":"{take} built. The crack under you is the only way in: follow the shaft down and drop into the dome. /function {ns}:clear_{t} removes it.","color":"green"}}']
        parts = [body[i:i + PART] for i in range(0, len(body), PART)]
        head = [f"# {take}: {meta['across']} across, dome {meta['H']}, {len(meta['holes'])} burrows {meta['tw']} wide, "
                f"{meta['cover']} blocks of rock on top. Run on flat ground in creative; it builds round and above you.",
                "kill @e[type=minecraft:marker,tag=lc_origin]",
                'execute align xyz run summon minecraft:marker ~ ~ ~ {Tags:["lc_origin"]}',
                f"tp @s ~ ~{Y + 3} ~",
                f'tellraw @s {{"text":"Building {take}...","color":"yellow"}}']
        for i, part in enumerate(parts):
            nxt = [f"schedule function {ns}:{t}_part{i + 2} 10t"] if i + 1 < len(parts) else []
            lines = (head if i == 0 else []) + part + nxt
            name = t if i == 0 else f"{t}_part{i + 1}"
            with open(os.path.join(fdir, name + ".mcfunction"), "w") as fh:
                fh.write("\n".join(lines) + "\n")
        C = ["# Removes the cave box (the marker remembers where it was built)."]
        C += [at + f"fill ~{o + x0} ~{y0} ~{o} ~{o + x1} ~{y1} ~{o + Z - 1} minecraft:air" for x0, x1, y0, y1 in slabs]
        with open(os.path.join(fdir, "clear_" + t + ".mcfunction"), "w") as fh:
            fh.write("\n".join(C) + "\n")
        meta["datapack_commands"] = len(body)
        meta["datapack_parts"] = len(parts)
    return root


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "spider_cave_out"
    os.makedirs(out, exist_ok=True)
    built = {}
    for take, p in TAKES.items():
        solid, mask, meta = build(take, p)
        np.savez_compressed(os.path.join(out, take + ".npz"), solid=solid, mask=mask, meta=json.dumps(meta))
        draw_map(os.path.join(out, take + "_map.png"), solid, mask, meta)
        built[take] = (solid, mask, meta)
    write_datapack(out, built)
    for take, (_, _, m) in built.items():
        print(take, m["size"], "across", m["across"], "ring", m["ring_length"], "cmds", m["datapack_commands"], "|", m["laps_note"])


if __name__ == "__main__":
    main()
