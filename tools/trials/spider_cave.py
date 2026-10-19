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
TAKES = {
    "C1": dict(span=10, R=22, H=18, burrows=6, tw=5, depth=9, pillars=2, seed=11),
    "C2": dict(span=14, R=32, H=24, burrows=8, tw=6, depth=11, pillars=3, seed=12),
    "C3": dict(span=20, R=44, H=32, burrows=10, tw=8, depth=14, pillars=4, seed=13),
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
    Y = y_floor + H + 6
    cx = cz = half

    air = np.zeros((X, Y, Z), bool)
    mask = np.zeros((X, Y, Z), np.uint8)  # 1 chamber, 2 burrow shaft, 3 ring tunnel, 4 cross tunnel, 5 entrance

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
        holes.append(dict(n=i + 1, kind="wall" if in_wall else "floor", x=round(top[0] - cx, 1), z=round(top[2] - cz, 1)))

    # Two cross tunnels under the floor (cut-throughs), deeper than the ring so they pass under it at the ends.
    y_cross = y_ring - 1
    for a in (0.5, 0.5 + math.pi / 2):
        p0 = (cx + math.cos(a) * ring_r, y_ring, cz + math.sin(a) * ring_r)
        p1 = (cx + math.cos(a + math.pi) * ring_r, y_ring, cz + math.sin(a + math.pi) * ring_r)
        mid = (cx, y_cross - 1, cz)
        carve_tube(air, mask, [p0, mid, p1], tw / 2 - 0.5, 4)
    y_cross_used = y_cross - 1

    # Player entrance: a 3-wide, 4-high passage from the -x side of the box to the wall.
    ez0, ez1 = cz - 1, cz + 2
    for x in range(0, cx):
        if rn[x, cz] < 0.95:
            break
        air[x, y_floor + 1:y_floor + 5, ez0:ez1] = True
        mask[x, y_floor + 1:y_floor + 5, ez0:ez1] = 5

    solid = ~air
    floor_area = int((rn < 1).sum())
    meta = dict(take=take, **{k: v for k, v in p.items() if k != "seed"}, size=[X, Y, Z], y_floor=int(y_floor),
                y_ring=int(y_ring), y_cross=int(y_cross_used), across=int(2 * R), ring_length=int(math.tau * ring_r),
                floor_area=floor_area, holes=holes, pillar_list=pil,
                laps_note=f"a spider at 8 blocks/s crosses the floor in {2 * R / 8:.1f} s and laps the ring in {math.tau * ring_r / 8:.1f} s")
    return solid, mask, meta


def draw_map(path, solid, mask, meta):
    X, Y, Z = solid.shape
    s = max(3, 640 // X)
    im = Image.new("RGB", (X * s, Z * s + 70), (24, 24, 26))
    d = ImageDraw.Draw(im)
    tun = np.isin(mask, (2, 3, 4)).any(1)
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
    f = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
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
    d.text((8, y0), f"{meta['take']}: {meta['across']} blocks across, dome {meta['H']} high, {len(meta['holes'])} burrows {meta['tw']} wide, spider {meta['span']}-block leg span (red ring)", font=f, fill=(235, 235, 235))
    d.text((8, y0 + 22), "grey floor · brown tunnels under it · yellow holes · blue entrance · green = you", font=f, fill=(170, 170, 170))
    d.text((8, y0 + 44), meta["laps_note"], font=f, fill=(170, 170, 170))
    im.save(path)


def runs(row):
    """Start/end index pairs of True runs in a 1D bool array."""
    r = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
    return list(zip(r[::2], r[1::2] - 1))


def write_datapack(out, takes):
    ns = "lantern_cave"
    root = os.path.join(out, "lantern-spider-cave-datapack")
    fdir = os.path.join(root, "data", ns, "function")
    os.makedirs(fdir, exist_ok=True)
    with open(os.path.join(root, "pack.mcmeta"), "w") as fh:
        json.dump({"pack": {"description": "Lantern Ring: giant spider cave size test (C1, C2, C3)",
                            "pack_format": 121, "min_format": 121, "max_format": 121}}, fh)
    at = f"execute at @e[type=minecraft:marker,tag=lc_origin,limit=1] run "
    for take, (solid, mask, meta) in takes.items():
        X, Y, Z = solid.shape
        ox, oz = 6, -(Z // 2)   # the box starts 6 blocks east of you, centred on you north-south
        L = [f"# {take}: {meta['across']} across, {meta['H']} dome, {len(meta['holes'])} burrows. Stand on flat ground; builds east of you.",
             "kill @e[type=minecraft:marker,tag=lc_origin]",
             'execute align xyz run summon minecraft:marker ~ ~ ~ {Tags:["lc_origin"]}']
        # stone box in slabs under the 32768-block fill limit
        step = max(1, 32768 // (X * Z))
        for y in range(0, Y, step):
            y1 = min(Y - 1, y + step - 1)
            L.append(at + f"fill ~{ox} ~{y} ~{oz} ~{ox + X - 1} ~{y1} ~{oz + Z - 1} minecraft:deepslate")
        air = ~solid
        for y in range(Y):
            for z in range(Z):
                for a, b in runs(air[:, y, z]):
                    L.append(at + f"fill ~{ox + a} ~{y} ~{oz + z} ~{ox + b} ~{y} ~{oz + z} minecraft:air")
        yf = meta["y_floor"]
        ledge = f"fill ~{ox - 5} ~{yf} ~-2 ~{ox - 1} ~{yf} ~2"   # a ledge outside the entrance (the floor is up the box side)
        L.append(at + ledge + " minecraft:deepslate")
        L += [f"tp @s ~{ox - 3} ~{yf + 1} ~", "effect give @s minecraft:night_vision 1200 0 true",
              f'tellraw @s {{"text":"{take} built: walk east through the entrance. /function {ns}:clear_{take.lower()} removes it.","color":"green"}}']
        with open(os.path.join(fdir, take.lower() + ".mcfunction"), "w") as fh:
            fh.write("\n".join(L) + "\n")
        C = ["# Removes the last-built cave box (run it where you ran the build)."]
        C += [at + f"fill ~{ox} ~{y} ~{oz} ~{ox + X - 1} ~{min(Y - 1, y + step - 1)} ~{oz + Z - 1} minecraft:air"
              for y in range(0, Y, step)]
        C.append(at + ledge + " minecraft:air")
        with open(os.path.join(fdir, "clear_" + take.lower() + ".mcfunction"), "w") as fh:
            fh.write("\n".join(C) + "\n")
        meta["datapack_commands"] = len(L)
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
