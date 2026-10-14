"""Lantern Ring texture library (J, 2026-10-14): every construct texture J called good, in every corps colour, in every
format the game and Blender use, in one folder.

J's must textures: BR1 bricks, W1 neon weave, H1 hex ("the hex that should be for all colours"), Red R1 magma,
Red R2 bloodfire, Violet V1 crystal, X3D1 glass aura (his pick in the lead Blender chat).
Colours: the six corps - green, blue, crimson (red), yellow, violet, orange.

Where a texture already exists in a colour (BR1 emerald, W1/H1 neon, X3D1 emerald, H1 blue, R1/R2 red, V1 violet,
and BR1 blue = BR1 jade in dark blue, J's call) that strip is used as it is. Every other colour is made from the
original's brightness: each pixel's brightness (0..1 between the strip's darkest and brightest) is mapped through the
colour's five-stop ramp, the same way the round 4-10 generators colour their designs. Alpha and animation are kept.

Per texture and colour, in OUT/<colour>/<texture>/:
  construct_<tex>_<colour>.png (+ .mcmeta)       game strip at its own size (128 px = 32 px a block, 256 = 64)
  construct_<tex>_<colour>_32px.png (+ .mcmeta)  32 px a block (only when the strip is bigger)
  barrier_<tex>_<colour>.png (+ .mcmeta)         landing barrier / shell: the light stays solid, the rest at 40 %
  particle_<tex>_<colour>_pane.png  16 px        a square of the texture with a bright rim (construct pieces)
  particle_<tex>_<colour>_shard.png  8 px        a triangle chip of it (crumbling, breaking)
  particle_<tex>_<colour>_mote.png   8 px        a soft dot in the colour's light (sparks, ribbon, smoke)
  blender_<tex>_<colour>.png                     frame 1, opaque on dark, for Blender materials
  blender_<tex>_<colour>.mp4 (with --mp4)        the loop as the game plays it, 20 fps, for Blender movie textures

    python tools/texture_library.py SRC_BLOCK_DIR OUT [--mp4 MP4_DIR]
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

SRC, OUT = sys.argv[1], sys.argv[2]
MP4 = sys.argv[sys.argv.index("--mp4") + 1] if "--mp4" in sys.argv else None
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

STOPS = (0.0, 0.25, 0.5, 0.78, 1.0)
RAMPS = {
    "green":   [(0, 12, 6), (3, 44, 22), (8, 96, 48), (34, 168, 90), (150, 240, 182)],      # emerald
    "blue":    [(0, 4, 18), (2, 16, 56), (8, 48, 128), (44, 120, 220), (180, 220, 255)],
    "crimson": [(12, 0, 3), (50, 2, 10), (124, 6, 26), (214, 34, 52), (255, 180, 176)],
    "yellow":  [(20, 10, 0), (66, 38, 0), (150, 100, 4), (236, 190, 36), (255, 246, 180)],
    "violet":  [(8, 2, 18), (36, 8, 66), (92, 26, 156), (172, 86, 244), (234, 204, 255)],
    "orange":  [(18, 5, 0), (64, 20, 0), (150, 60, 2), (248, 134, 18), (255, 220, 160)],
}
COLOURS = list(RAMPS)
# texture -> (label, J's note, {colour: existing strip (the first one is what the other colours are made from) name in SRC as construct_ripples_<name>.png, or a path})
BR1_BLUE = os.path.join(HERE, "..", "docs", "blender", "models", "br1_blue", "construct_br1_blue.png")
TEXTURES = {
    "br1":   ("BR1 bricks", "KEEP: the most construct-like", {"green": "br1_emerald", "blue": BR1_BLUE}),
    "w1":    ("W1 neon weave", "good", {"green": "w1_neon"}),
    "h1":    ("H1 hex", "the only hex, for every colour", {"blue": "h1_blue"}),   # J: H1 blue is the hex for every colour
    "r1":    ("R1 magma", "good", {"crimson": "red_r1"}),
    "r2":    ("R2 bloodfire", "good", {"crimson": "red_r2"}),
    "v1":    ("V1 crystal", "good", {"violet": "violet_v1"}),
    "x3d1":  ("X3D1 glass aura", "J's pick (lead chat): cutout like glass", {"green": "green_x3d1_emerald"}),
}


def src_path(name):
    return name if os.path.isabs(name) or os.sep in name else os.path.join(SRC, f"construct_ripples_{name}.png")


def ramp(v, pal):
    c = np.array(RAMPS[pal], float)
    v = np.clip(v, 0, 1)
    out = np.zeros(v.shape + (3,))
    for i in range(4):
        a, b = STOPS[i], STOPS[i + 1]
        u = np.clip((v - a) / (b - a), 0, 1); u = u * u * (3 - 2 * u)
        m = ((v >= a) & (v <= b))[..., None]
        out = np.where(m, c[i] + (c[i + 1] - c[i]) * u[..., None], out)
    return out


def brightness(rgba):
    rgb = rgba[..., :3].astype(float)
    lum = rgb.max(-1) * 0.6 + rgb.mean(-1) * 0.4            # hue-blind: red, green and violet lines read alike
    lit = rgba[..., 3] > 8
    lo, hi = np.percentile(lum[lit], 0.5), np.percentile(lum[lit], 99.7)
    return np.clip((lum - lo) / max(hi - lo, 1), 0, 1)


def mcmeta_of(path):
    p = path + ".mcmeta"
    return open(p).read() if os.path.exists(p) else '{"animation": {"interpolate": true, "frametime": 4}}'


def frames_of(a):
    n = a.shape[1]
    return n, a.shape[0] // n


def to_32px(a):
    n, nf = frames_of(a)
    if n <= 128:
        return None
    im = Image.fromarray(a, "RGBA")
    out = []
    for i in range(nf):
        out.append(np.asarray(im.crop((0, i * n, n, (i + 1) * n)).resize((128, 128), Image.BOX)))
    return np.concatenate(out, 0)


def barrier(a):
    v = brightness(a)
    out = a.copy()
    al = a[..., 3].astype(float)
    out[..., 3] = np.where(v > 0.55, al, al * 0.4).astype(np.uint8)
    return out


def particles(a, pal):
    n, _ = frames_of(a)
    f0 = Image.fromarray(a[:n], "RGBA")
    k = n // 4                                                  # one block of the texture
    block = f0.crop((0, 0, k, k)).resize((16, 16), Image.BOX)
    pane = np.asarray(block).copy()
    rim = np.array(RAMPS[pal][4] + (255,), np.uint8)
    pane[0, :] = pane[-1, :] = pane[:, 0] = pane[:, -1] = rim
    pane[..., 3] = np.maximum(pane[..., 3], 150)
    shard = np.asarray(f0.crop((k, k, 2 * k, 2 * k)).resize((8, 8), Image.BOX)).copy()
    yy, xx = np.mgrid[0:8, 0:8]
    shard[..., 3] = np.where(xx + yy <= 8, np.maximum(shard[..., 3], 170), 0)
    shard[(xx + yy == 8) & (xx > 0)] = rim
    d = np.hypot(xx - 3.5, yy - 3.5)
    mote = np.zeros((8, 8, 4), np.uint8)
    mote[..., :3] = np.array(RAMPS[pal][3]) * 0.5 + np.array(RAMPS[pal][4]) * 0.5
    mote[..., 3] = np.clip(255 * np.exp(-(d / 2.2) ** 2), 0, 255)
    return pane, shard, mote


def on_dark(fr):
    bg = Image.new("RGBA", (fr.shape[1], fr.shape[0]), (24, 28, 32, 255))
    bg.alpha_composite(Image.fromarray(fr, "RGBA"))
    return np.asarray(bg.convert("RGB"))


def write_mp4(a, meta, path):
    n, nf = frames_of(a)
    ft = json.loads(meta)["animation"].get("frametime", 4)
    fr = [on_dark(a[i * n:(i + 1) * n]) for i in range(nf)]
    out = []
    for k in range(nf * ft):
        i, u = divmod(k, ft)
        x, y = fr[i].astype(float), fr[(i + 1) % nf].astype(float)
        out.append((x + (y - x) * u / ft).astype(np.uint8))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{n}x{n}", "-r", "20",
                    "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", path],
                   input=b"".join(f.tobytes() for f in out), check=True)
    return nf * ft


def save(a, path, meta=None):
    im = Image.fromarray(a, "RGBA")
    if a.shape[0] > 64:                                         # strips: 256-colour palette like the game's own
        im = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    im.save(path, optimize=True)
    if meta is not None:
        open(path + ".mcmeta", "w").write(meta)


index = {"colours": COLOURS, "ramps": RAMPS, "textures": {}}
for tex, (label, note, natives) in TEXTURES.items():
    base_name = next(iter(natives.values()))
    base = np.asarray(Image.open(src_path(base_name)).convert("RGBA"))
    meta = mcmeta_of(src_path(base_name))
    v = brightness(base)
    index["textures"][tex] = {"label": label, "note": note, "made_from": os.path.basename(src_path(base_name)), "colours": {}}
    for col in COLOURS:
        if col in natives:
            a = np.asarray(Image.open(src_path(natives[col])).convert("RGBA")); m = mcmeta_of(src_path(natives[col])); how = "original"
        else:
            a = np.concatenate([ramp(v, col).round().astype(np.uint8), base[..., 3:]], -1); m = meta; how = "recoloured"
        d = os.path.join(OUT, col, tex); os.makedirs(d, exist_ok=True)
        stem = f"{tex}_{col}"
        save(a, os.path.join(d, f"construct_{stem}.png"), m)
        s32 = to_32px(a)
        if s32 is not None:
            save(s32, os.path.join(d, f"construct_{stem}_32px.png"), m)
        save(barrier(a), os.path.join(d, f"barrier_{stem}.png"), m)
        for nm, p in zip(("pane", "shard", "mote"), particles(a, col)):
            save(p, os.path.join(d, f"particle_{stem}_{nm}.png"))
        n, nf = frames_of(a)
        Image.fromarray(on_dark(a[:n])).save(os.path.join(d, f"blender_{stem}.png"))
        info = {"how": how, "size": n, "frames": nf, "mcmeta": json.loads(m)}
        if MP4:
            os.makedirs(MP4, exist_ok=True)
            info["mp4_frames"] = write_mp4(a, m, os.path.join(MP4, f"blender_{stem}.mp4"))
        index["textures"][tex]["colours"][col] = info
    print(tex, "done", flush=True)
json.dump(index, open(os.path.join(OUT, "index.json"), "w"), indent=1)

# the sheet: textures down, colours across (frame 1, 2 x 2 blocks of each)
T, P, L = 128, 8, 150
sheet = Image.new("RGB", (L + len(COLOURS) * (T + P), 40 + len(TEXTURES) * (T + P)), (16, 18, 22))
dr = ImageDraw.Draw(sheet)
for j, col in enumerate(COLOURS):
    dr.text((L + j * (T + P) + 4, 14), col.upper(), fill=tuple(RAMPS[col][3]))
for i, tex in enumerate(TEXTURES):
    y = 40 + i * (T + P)
    dr.text((6, y + 50), TEXTURES[tex][0], fill=(230, 230, 230))
    for j, col in enumerate(COLOURS):
        im = Image.open(os.path.join(OUT, col, tex, f"blender_{tex}_{col}.png"))
        sheet.paste(im.crop((0, 0, im.width // 2, im.width // 2)).resize((T, T), Image.NEAREST), (L + j * (T + P), y))
sheet.save(os.path.join(OUT, "sheet_all.png"))
print("sheet done")
