"""Lean Nebula lantern (J, 2026-10-14: "Nebula needs to be redone in blender with different more
efficient textures"). Blender pass 400 builds on what this writes.

The old Nebula painted every glass face uniquely from a 3D field at 4 texels per model pixel:
24 frames of 512x512, saved twice (block strip + entity frames) and again per corps, about 6.5 MB.

Here the glass and the light inside are smooth 20-sided columns of thin panels (like the light
already was). The cylinder is unrolled into one small strip: 20 panels x PP texels around, 2
texels per model pixel up its 9-pixel height. Every take's pattern is periodic around the
cylinder and loops in time, so there are no seams and no jump. Each corps is painted with its own
five-stop palette (no hue shift), and frames are palette-quantized.

    python tools/nebula_lean.py OUT_DIR [--pp 3]

writes, per take: OUT_DIR/<take>/assets/lanternring/{bbmodel,textures/block,textures/entity/bb}
(drop-in replacements for the Nebula files on main) plus preview sheets in OUT_DIR/preview/.
"""
import json
import math
import os
import sys
import uuid

import numpy as np
from PIL import Image

TAU = 2 * math.pi
# Columns of thin panels. The game's BbModel uses Minecraft box UV (integer uv_offset per cube),
# so each panel is a whole number of texels wide: its outer face, then its inner face mirrored.
COLUMNS = {
    "glass": {"panels": 21, "radius": 5.0, "width": 1.5, "step": 3},   # chord 1.49
    "light": {"panels": 24, "radius": 3.8, "width": 1.0, "step": 2},   # chord 0.99
}
Y0, Y1 = 7.0, 16.0          # both columns span y 7..16
TEX_PER_PX = 2              # texels per model pixel, vertically
FRAMES = 32                 # loop length in frames
FRAMETIME = 4               # ticks per frame: 32 x 4 = 128 ticks = 6.4 s, smooth (interpolated)

CORPS = {
    # Five stops, darkest to hottest, painted per corps (J: no hue shifts).
    "green":  [(3, 9, 8), (10, 52, 36), (26, 124, 74), (96, 220, 150), (205, 255, 228)],
    "blue":   [(3, 6, 14), (10, 30, 72), (32, 84, 176), (112, 172, 255), (218, 236, 255)],
    "red":    [(10, 2, 3), (62, 8, 14), (146, 20, 34), (232, 72, 72), (255, 204, 194)],
    "yellow": [(10, 8, 2), (72, 54, 8), (176, 134, 22), (255, 216, 72), (255, 250, 212)],
    "violet": [(7, 3, 12), (42, 14, 72), (104, 42, 164), (192, 122, 255), (242, 222, 255)],
    "orange": [(10, 5, 2), (72, 30, 6), (184, 82, 16), (255, 162, 52), (255, 236, 202)],
}
SUFFIX = {"green": "", "blue": "_blue", "red": "_red", "yellow": "_yellow", "violet": "_violet", "orange": "_orange"}


def ramp(v, stops):
    """Smoothstep blend through five colour stops; v in 0..1, any array shape."""
    v = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(v.astype(int), len(stops) - 2)
    f = v - i
    f = f * f * (3 - 2 * f)
    s = np.array(stops, float)
    return s[i] * (1 - f[..., None]) + s[i + 1] * f[..., None]


# ---- periodic noise on the cylinder -----------------------------------------------------------
def _lattice(seed, n=32):
    return np.random.default_rng(seed).random((n, n, n))


_G = [_lattice(s) for s in (11, 12, 13, 14)]


def vnoise(g, x, y, z):
    """Smooth value noise on a periodic 32^3 lattice."""
    n = g.shape[0]
    xi, yi, zi = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int)
    xf, yf, zf = x - xi, y - yi, z - zi
    u, v, w = (t * t * (3 - 2 * t) for t in (xf, yf, zf))
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                c = g[(xi + dx) % n, (yi + dy) % n, (zi + dz) % n]
                out = out + c * (u if dx else 1 - u) * (v if dy else 1 - v) * (w if dz else 1 - w)
    return out


def fbm(g, x, y, z, octaves=4):
    s, a, tot, norm = 1.0, 0.5, 0.0, 0.0
    for _ in range(octaves):
        tot = tot + a * vnoise(g, x * s, y * s, z * s)
        norm += a
        s, a = s * 2.0, a * 0.5
    return tot / norm


def looped(fn, t):
    """Cross-fades two copies one loop apart, so any drifting field loops seamlessly."""
    return fn(t) * (1 - t) + fn(t - 1) * t


# ---- the glass designs: each returns (value 0..1, alpha 0..255) on the unrolled cylinder ------
# th: angle round the column (0..2pi), y: model px up the glass (0..9), t: loop time 0..1.
def n1_smoke_ice(th, y, t):
    """N1 Smoke & ice: the Nebula as J knows it. Slow smoke drifting up, pale ice veins, far stars."""
    cx, cz = np.cos(th) * 2.2 + 8, np.sin(th) * 2.2 + 8   # a circle in noise space: periodic round the glass

    def at(tt):
        Y = y * 0.42 - tt * 3.0
        smoke = fbm(_G[0], cx, Y, cz, 4)
        warp = fbm(_G[1], cx * 1.3, Y * 1.3 + 5, cz * 1.3, 3)
        ice = 1 - np.abs(fbm(_G[2], cx * 1.6 + warp * 1.4, Y * 0.9 + warp, cz * 1.6, 4) * 2 - 1)
        return np.stack([smoke, ice])
    smoke, ice = looped(at, t)
    cloud = np.clip((smoke - 0.42) * 2.6, 0, 1) ** 1.3
    veins = np.clip((ice - 0.9) * 10, 0, 1) ** 1.5
    v = 0.08 + 0.4 * cloud + 0.6 * veins
    a = 150 + 50 * cloud + 50 * veins
    return v, a


def n2_spiral(th, y, t):
    """N2 Spiral arms: two galaxy arms winding round the glass, gliding sideways, with dust lanes."""
    warp = fbm(_G[3], np.cos(th) * 1.8 + 4, y * 0.3, np.sin(th) * 1.8 + 4, 3)
    phase = 2 * th + y * 0.55 - TAU * t + warp * 2.2      # whole turns per loop: seamless
    arm = (np.cos(phase) * 0.5 + 0.5) ** 3
    dust = (np.cos(2 * phase + 1.3) * 0.5 + 0.5) ** 6
    v = 0.06 + 0.66 * arm - 0.25 * dust * arm
    a = 150 + 85 * arm - 40 * dust * arm
    return v, a


def n3_aurora(th, y, t):
    """N3 Aurora curtains: soft upright veils swaying round the glass, brightest in the middle band."""
    sway = 0.6 * np.sin(3 * th + TAU * t) + 0.4 * np.sin(5 * th - TAU * 2 * t + 1.1)
    curtain = (np.sin(7 * th + sway * 1.6 + TAU * t) * 0.5 + 0.5) ** 2
    band = np.exp(-((y - 4.5 - 1.2 * np.sin(2 * th + TAU * t)) / 2.6) ** 2)
    v = 0.06 + 0.72 * curtain * band
    a = 150 + 85 * curtain * band
    return v, a


def n4_deep_stars(th, y, t, w, h):
    """N4 Deep stars: dark gas with two layers of pixel stars rising at different speeds."""
    gas = fbm(_G[0], np.cos(th) * 1.5 + 2, y * 0.2 - TAU * 0, np.sin(th) * 1.5 + 2, 3)
    v = 0.05 + 0.3 * np.clip((gas - 0.45) * 2.5, 0, 1)
    a = 160 + 50 * np.clip((gas - 0.45) * 2.5, 0, 1)
    rng = np.random.default_rng(7)
    for layer, (count, speed, bright) in enumerate(((10, 1, 0.75), (6, 2, 1.0))):
        xs = rng.integers(0, w, count)
        ys = rng.random(count) * h
        tw = rng.random(count)
        for sx, sy, ph in zip(xs, ys, tw):
            yy = int((sy - t * speed * h) % h)          # whole laps per loop: seamless
            glow = bright * (0.7 + 0.3 * math.sin(TAU * (t * 2 + ph)))
            v[yy, sx] = max(v[yy, sx], glow)
            a[yy, sx] = 230
    return v, a


GLASS_TAKES = {
    "N1_smoke_ice": n1_smoke_ice,
    "N2_spiral_arms": n2_spiral,
    "N3_aurora": n3_aurora,
    "N4_deep_stars": n4_deep_stars,
}


def light_field(th, y, t):
    """The solid light column inside (shared by every take): waves rising, a spiral winding round,
    brightest at a beating heart mid-height. Every time term turns whole times per loop."""
    rise = np.sin(TAU * (y / 4.5 - 2 * t) + 1.8 * np.sin(2 * th + TAU * t))
    spiral = np.sin(3 * th + TAU * (y / 7 - t))
    v = (rise + spiral) / 4 + 0.55
    rings = np.clip(1 - np.abs(rise) * 5, 0, 1) ** 2
    heart = np.exp(-((y - 4.5) / 3.2) ** 2) * (0.6 + 0.4 * np.sin(TAU * 2 * t))
    return np.clip(0.35 + 0.4 * v + 0.25 * rings + 0.25 * heart, 0, 1)


# ---- textures ---------------------------------------------------------------------------------
def grid(kind):
    c = COLUMNS[kind]
    w, h = int(c["panels"] * c["width"] * TEX_PER_PX), int((Y1 - Y0) * TEX_PER_PX)
    th = (np.arange(w) + 0.5) / w * TAU
    y = (Y1 - Y0) - (np.arange(h) + 0.5) / TEX_PER_PX     # row 0 is the top
    TH, YY = np.meshgrid(th, y)
    return w, h, TH, YY


def glass_frame(take, corps, t, pp=None):
    """The glass, unrolled: one continuous strip round the column."""
    w, h, TH, YY = grid("glass")
    fn = GLASS_TAKES[take]
    v, a = fn(TH, YY, t, w, h) if take == "N4_deep_stars" else fn(TH, YY, t)
    # The glass darkens toward its top and bottom ends (J: ends fade to near-black).
    ends = np.clip(np.minimum(YY, (Y1 - Y0) - YY) / 2.2, 0, 1) ** 0.6
    v = v * (0.45 + 0.55 * ends)
    rgb = ramp(v, CORPS[corps])
    return Image.fromarray(np.dstack([rgb, np.clip(a, 0, 255)]).astype(np.uint8), "RGBA")


def light_frame(corps, t, pp=None):
    w, h, TH, YY = grid("light")
    v = light_field(TH, YY, t)
    # Rich, saturated corps colour through the body; the hottest stop only in rings and the heart.
    rgb = ramp(0.4 + 0.5 * v, CORPS[corps])
    return Image.fromarray(np.dstack([rgb, np.full(v.shape, 255)]).astype(np.uint8), "RGBA")


def to_layout(strip, kind):
    """Unrolled strip -> the model texture: per panel, its outer face slice then the same slice
    mirrored for the inner face (seen through the glass from the far side)."""
    c = COLUMNS[kind]
    pw, sw = int(c["width"] * TEX_PER_PX), c["step"] * TEX_PER_PX
    out = Image.new("RGBA", (c["panels"] * sw, strip.height), (0, 0, 0, 0))
    for k in range(c["panels"]):
        sl = strip.crop((k * pw, 0, (k + 1) * pw, strip.height))
        out.paste(sl, (k * sw, 0))
        out.paste(sl.transpose(Image.FLIP_LEFT_RIGHT), (k * sw + pw, 0))
    return out


def quantize(im, colors):
    """Palette PNG (keeps alpha). Small strips quantize losslessly enough at 64 colours."""
    return im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)


# ---- models -----------------------------------------------------------------------------------
def lathe_bbmodel(name, kind, prefix, glow_copies):
    """A smooth column of thin panels; each panel's faces sit at its own box-UV slot."""
    c = COLUMNS[kind]
    n, radius, width, step = c["panels"], c["radius"], c["width"], c["step"]
    ang_step = TAU / n
    a = radius * math.cos(ang_step / 2)
    h = Y1 - Y0
    elements = []
    for k in range(n):
        ang = (k + 0.5) * ang_step                  # panel centre angle (0 = north, -z)
        cx, cz = a * math.sin(ang), -a * math.cos(ang)
        u = k * step
        faces = {
            "north": {"uv": [u, 0, u + width, h], "texture": 0},
            "south": {"uv": [u + width, 0, u + 2 * width, h], "texture": 0},
            "east": {"uv": [u, 0, u, h], "texture": None},
            "west": {"uv": [u + width, 0, u + width, h], "texture": None},
            "up": {"uv": [u, 0, u + width, 0], "texture": None},
            "down": {"uv": [u + width, 0, u + 2 * width, 0], "texture": None},
        }
        for pre in [prefix] + (["glow_" + prefix] if glow_copies else []):
            elements.append({
                "name": f"{pre}_{k}", "box_uv": True, "rescale": False, "locked": False,
                "render_order": "default", "allow_mirror_modeling": True,
                "from": [cx - width / 2, Y0, cz], "to": [cx + width / 2, Y1, cz],
                "autouv": 0, "color": 0, "inflate": 0.0, "origin": [cx, (Y0 + Y1) / 2, cz],
                "rotation": [0.0, -math.degrees(ang), 0.0], "uv_offset": [u, 0],
                "faces": faces, "type": "cube", "uuid": str(uuid.uuid4()),
            })
    rw, rh = n * step, int(math.ceil(h))
    return {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": True},
        "name": name, "model_identifier": name, "visible_box": [1, 1, 0],
        "resolution": {"width": rw, "height": rh},
        "elements": elements,
        "outliner": [e["uuid"] for e in elements],
        "textures": [{"name": f"{name}.png", "width": rw * TEX_PER_PX, "height": rh * TEX_PER_PX,
                      "uv_width": rw, "uv_height": rh, "id": "0", "uuid": str(uuid.uuid4())}],
    }


def write_take(out, take, pp, colors=64):
    root = f"{out}/{take}/assets/lanternring"
    for d in ("bbmodel", "textures/block", "textures/entity/bb"):
        os.makedirs(f"{root}/{d}", exist_ok=True)
    json.dump(lathe_bbmodel("nebula_glass", "glass", "glass", False),
              open(f"{root}/bbmodel/nebula_glass.bbmodel", "w"), indent=1)
    json.dump(lathe_bbmodel("nebula_light", "light", "light", True),
              open(f"{root}/bbmodel/nebula_light.bbmodel", "w"), indent=1)
    for corps, sfx in SUFFIX.items():
        for kind, make in (("glass", lambda t: glass_frame(take, corps, t, pp)),
                           ("light", lambda t: light_frame(corps, t, pp))):
            frames = [to_layout(make(i / FRAMES), kind) for i in range(FRAMES)]
            w, h = frames[0].size
            meta = {"animation": {"frametime": FRAMETIME, "interpolate": True, "width": w, "height": h}}
            strip = Image.new("RGBA", (w, h * FRAMES))
            for i, im in enumerate(frames):
                strip.paste(im, (0, i * h))
                quantize(im, colors).save(f"{root}/textures/entity/bb/nebula_{kind}_f{i}{sfx}.png", optimize=True)
            quantize(strip, colors).save(f"{root}/textures/block/nebula_{kind}{sfx}.png", optimize=True)
            json.dump(meta, open(f"{root}/textures/block/nebula_{kind}{sfx}.png.mcmeta", "w"), indent="\t")
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(root) for f in fs)
    return total


def preview(out, pp):
    """One sheet per take: the unrolled glass over the light for every corps, frames 0/8/16/24."""
    os.makedirs(f"{out}/preview", exist_ok=True)
    w, h, _, _ = grid("glass")
    s = 6
    for take in GLASS_TAKES:
        sheet = Image.new("RGBA", (4 * (w * s + 8), len(CORPS) * (h * s + 8)), (24, 24, 28, 255))
        for r, corps in enumerate(CORPS):
            for c, f in enumerate((0, 8, 16, 24)):
                t = f / FRAMES
                im = light_frame(corps, t).resize((w, h), Image.NEAREST)
                im = Image.blend(Image.new("RGBA", im.size, (0, 0, 0, 255)), im, 0.55)  # light seen dimmed, as behind dark glass
                im.alpha_composite(glass_frame(take, corps, t))
                sheet.paste(im.resize((w * s, h * s), Image.NEAREST), (c * (w * s + 8), r * (h * s + 8)))
        sheet.save(f"{out}/preview/{take}_unrolled.png")


if __name__ == "__main__":
    out = sys.argv[1]
    pp = int(sys.argv[sys.argv.index("--pp") + 1]) if "--pp" in sys.argv else 3
    for take in GLASS_TAKES:
        kb = write_take(out, take, pp) / 1024
        print(f"{take}: {kb:.0f} KB for all six corps (glass + light, block strips + entity frames + models)")
    preview(out, pp)
