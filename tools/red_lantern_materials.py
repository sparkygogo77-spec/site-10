"""J (2026-10-16, in game with Complementary): the Red Lantern is shiny all over ("it looks very weird with 100% of it
being this way, this is closer to reflective like i was looking for, i need multiple material iterations").

Makes material takes M1-M4 of the Red battery: each part of the stone body gets its own colour and its own LabPBR
material, so only some of it is mirror-like. For every take it writes, next to the model's own texture,
    textures/entity/bb/red_battery_<take>.png      the base colour (the original's shading kept)
    textures/entity/bb/red_battery_<take>_s.png    the material: R smoothness, G reflectance (230+ metal),
                                                   B 253 = Lantern Ring material map (ShaderPackPatcher reads only
                                                   maps carrying that mark), A emission (255 = none)
and the same pair for the crumbling front cover (red_battery_cover_<take>). LanternFirstPerson draws the take picked in
the Ring Lab ("Red Lantern material"); M0 keeps today's texture and look.

Parts, from the model's cubes (model px, y up, the front is -z):
    pedestal  below 8          neck  8-16           drum  16-40          handle  above 40
    bezel     the drum's front ring round the port (z < -11, within 10 px of the port's centre at y 24)
    glow_*    the runes, veins, blood, port and side rings: kept as they are, just lightly polished

    python3 tools/red_lantern_materials.py
"""
import colorsys
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "src/main/resources/assets/lanternring")
TEX = os.path.join(ROOT, "textures/entity/bb")
REF = np.array([172, 27, 43], float)          # the body's main crimson: its shading is kept relative to this
PORT = (0.0, 24.0)                             # the port's centre (x, y) on the front

# take: {part: (base colour, smoothness 0-1, reflectance G (0-229 dielectric F0, 230 iron, 231 gold), name)}
GEM, IRON, GOLD = 18, 230, 231
TAKES = {
    "m1": ("Ruby and gold", {
        "drum": ((188, 30, 47), 0.90, GEM), "bezel": ((205, 34, 52), 0.96, GEM),
        "pedestal": ((226, 176, 72), 0.80, GOLD), "neck": ((226, 176, 72), 0.80, GOLD), "handle": ((226, 176, 72), 0.80, GOLD)}),
    "m2": ("Obsidian and ruby", {
        "drum": ((58, 15, 22), 0.55, 12), "bezel": ((200, 30, 48), 0.97, GEM),
        "pedestal": ((44, 12, 18), 0.45, 12), "neck": ((44, 12, 18), 0.45, 12), "handle": ((50, 14, 20), 0.50, 12)}),
    "m3": ("Crimson lacquer and black steel", {
        "drum": ((172, 27, 43), 0.62, 14), "bezel": ((190, 30, 48), 0.90, GEM),
        "pedestal": ((62, 62, 70), 0.82, IRON), "neck": ((214, 166, 70), 0.78, GOLD), "handle": ((62, 62, 70), 0.82, IRON)}),
    "m4": ("Matte stone, polished lens", {
        "drum": ((160, 26, 40), 0.18, 6), "bezel": ((200, 32, 50), 0.95, GEM),
        "pedestal": ((140, 22, 36), 0.15, 5), "neck": ((150, 24, 38), 0.18, 6), "handle": ((150, 24, 38), 0.20, 6)}),
}
GLOW_SPEC = (0.80, 14)                         # the glowing parts: lightly polished, no emission from the map


def part_of(e):
    if not e["name"].startswith("stone") and not e["name"].startswith("cover"):
        return "glow"
    a, b = np.array(e["from"], float), np.array(e["to"], float)
    c = (a + b) / 2
    if c[1] < 8:
        return "pedestal"
    if c[1] < 16:
        return "neck"
    if c[1] >= 40:
        return "handle"
    if c[2] < -11 and np.hypot(c[0] - PORT[0], c[1] - PORT[1]) < 10:
        return "bezel"
    return "drum"


def lum(rgb):
    return rgb @ np.array([0.2126, 0.7152, 0.0722])


def make(model, take, parts):
    d = json.load(open(os.path.join(ROOT, "bbmodel", model + ".bbmodel")))
    src = Image.open(os.path.join(TEX, model + ".png")).convert("RGBA")
    base = np.asarray(src).astype(float)
    k = src.size[0] / d["resolution"]["width"]          # texture px per model-texture unit
    col = base.copy()
    spec = np.zeros_like(base)
    spec[..., 3] = 255
    ref = lum(REF)
    for e in d["elements"]:
        part = part_of(e)
        for face in e["faces"].values():
            if face.get("texture") is None or "uv" not in face:
                continue
            u0, v0, u1, v1 = face["uv"]
            x0, x1 = sorted((int(round(u0 * k)), int(round(u1 * k))))
            y0, y1 = sorted((int(round(v0 * k)), int(round(v1 * k))))
            if x1 <= x0 or y1 <= y0:
                continue
            region = base[y0:y1, x0:x1]
            solid = region[..., 3] > 0
            if part == "glow":
                s, g = GLOW_SPEC
                spec[y0:y1, x0:x1][solid] = (round(s * 255), g, 253, 255)
                continue
            rgb, s, g = parts[part]
            shade = np.clip(lum(region[..., :3]) / ref, 0.35, 1.6)[..., None]
            out = np.clip(np.array(rgb, float) * shade, 0, 255)
            col[y0:y1, x0:x1][solid, :3] = out[solid]
            spec[y0:y1, x0:x1][solid] = (round(s * 255), g, 253, 255)
    Image.fromarray(col.astype(np.uint8), "RGBA").save(os.path.join(TEX, f"{model}_{take}.png"), optimize=True)
    Image.fromarray(spec.astype(np.uint8), "RGBA").save(os.path.join(TEX, f"{model}_{take}_s.png"), optimize=True)


for take, (name, parts) in TAKES.items():
    for model in ("red_battery", "red_battery_cover"):
        make(model, take, parts)
    print(take, name)
