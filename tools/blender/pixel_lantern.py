"""The Blue Lantern built straight on Minecraft's pixel grid from measurements of J's sheet: cubes on
a GRID (0.5 = 32 per block, 0.25 = 64 per block), every cube face painted as pixel art at 4 pixels
per unit (64 per block). The emblem is authored pixel by pixel, not shrunk from a picture. Renders
the sheet's nine views in Blender beside the sheet and scores the silhouette against it.

    python tools/blender/pixel_lantern.py <sheet.jpg> <out.png> [--grid 0.5] [--fast]

Units are the mod's (1 = 1/16 block). Measured from the sheet's front and side views at 12 px per
unit: body 13.3 wide and 13.6 tall on a 4.6 tall stepped foot, windows a 5.5 octagon frame round a
4.75 domed glass, bronze collar 4.35 round, stone handle loop to 26.7.
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pixel_blue_lantern as L
from pixel_blue_lantern import *

SHEET, OUT = sys.argv[1], sys.argv[2]
FAST = "--fast" in sys.argv
L.build(float(sys.argv[sys.argv.index("--grid") + 1]) if "--grid" in sys.argv else 0.5)
if "--emblem-res" in sys.argv:
    L.TG = 1 / (float(sys.argv[sys.argv.index("--emblem-res") + 1]) / 16)
G, TG, xs, zs, part, occ = L.G, L.TG, L.xs, L.zs, L.part, L.occ

quads, qcol, qkind = L.pixel_quads()
print(f"grid {G} ({int(round(16 / G))} per block): {int(occ.sum()):,} cubes, "
      f"{len(quads):,} pixel quads")

# ---- export for the Lantern Model Bench viewer: quad count, corner positions, colour + kind -----------
if "--export" in sys.argv:
    path = sys.argv[sys.argv.index("--export") + 1]
    with open(path, "wb") as f:
        f.write(np.uint32(len(quads)).tobytes())
        f.write(np.asarray(quads, np.float32).tobytes())
        f.write(np.hstack([np.clip(np.round(qcol), 0, 255), np.array(qkind)[:, None]]).astype(np.uint8).tobytes())
    print("exported", path, os.path.getsize(path), "bytes")

# ---- Blender ---------------------------------------------------------------------------------------
import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
verts = np.array(quads).reshape(-1, 3)
faces = np.arange(len(verts)).reshape(-1, 4)
me = bpy.data.meshes.new("lantern")
me.from_pydata(verts.tolist(), [], faces.tolist())
lin = (np.array(qcol) / 255) ** 2.2
attr = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
cols = np.repeat(lin, 4, axis=0)
attr.data.foreach_set("color", np.hstack([cols, np.ones((len(cols), 1))]).ravel())


def mat(name, metal, glow):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute")
    at.attribute_name = "col"
    L.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.45 if metal else 0.9
    bsdf.inputs["Metallic"].default_value = 0.75 if metal else 0.0
    if glow:
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        for l in list(bsdf.inputs["Base Color"].links):
            L.remove(l)
        L.new(at.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.2
    return m


for m in (mat("stone", False, False), mat("metal", True, False), mat("glow", False, True)):
    me.materials.append(m)
me.polygons.foreach_set("material_index", qkind)
obj = bpy.data.objects.new("lantern", me)
scene.collection.objects.link(obj)

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.43, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5


def area(name, loc, power, size):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.size = size
    o = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 12)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("key", (-28, -40, 40), 14000, 30)
area("fill", (35, -25, 12), 3500, 30)
area("rim", (10, 40, 30), 6000, 25)
scene.render.engine = "CYCLES"
scene.cycles.samples = 12 if FAST else 32
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam = bpy.data.objects.new("cam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
SIZE = 341
scene.render.resolution_x = scene.render.resolution_y = SIZE
# the sheet's tiles are 341 px at 12 px per unit with the ground at 332 px: match that framing
cam_d.ortho_scale = SIZE / 12.0
TARGET = Vector((0, 0, (332.5 - SIZE / 2) / 12.0))
VIEWS = [("FRONT", 0, 0), ("BACK", 180, 0), ("TOP", 0, 90), ("LEFT", -90, 0), ("RIGHT", 90, 0),
         ("BOTTOM", 0, -90), ("FRONT LEFT", -40, 14), ("FRONT RIGHT", 40, 14), ("BACK RIGHT", 140, 14)]
work = os.path.dirname(OUT)
TAG = os.path.splitext(os.path.basename(OUT))[0]
tiles = []
for label, yaw, pitch in VIEWS:
    y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    tgt = TARGET if abs(pitch) < 80 else Vector((0, 0, 12))
    cam.location = tgt + d * 80
    if abs(pitch) >= 80:
        cam.rotation_euler = (0, 0, 0) if pitch > 0 else (math.pi, 0, 0)
    else:
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    scene.render.film_transparent = label in ("FRONT", "LEFT")
    path = os.path.join(work, f"{TAG}_{label.replace(' ', '_')}.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    tiles.append((label, path))

# a close-up of the front window
cam_d.ortho_scale = 11
cam.location = Vector((0, -80, CZ))
cam.rotation_euler = (Vector((0, 1, 0))).to_track_quat("-Z", "Y").to_euler()
scene.render.film_transparent = False
scene.render.resolution_x = scene.render.resolution_y = 480
scene.render.filepath = os.path.join(work, f"{TAG}_closeup.png")
bpy.ops.render.render(write_still=True)
scene.render.resolution_x = scene.render.resolution_y = SIZE

# ---- compare with the sheet ------------------------------------------------------------------------
from PIL import Image, ImageDraw

sheet = Image.open(SHEET).convert("RGB")


def sheet_mask(tile_rc):
    r, c = tile_rc
    t = np.asarray(sheet.crop((c * SIZE, r * SIZE, (c + 1) * SIZE, (r + 1) * SIZE))).astype(int)
    chroma = t.max(2) - t.min(2)
    m = (chroma > 14) | (t.mean(2) < 80)
    m[:40] = False
    return m


scores = []
for (label, path), rc in (((tiles[0]), (0, 0)), ((tiles[3]), (1, 0))):
    ours = np.asarray(Image.open(path).convert("RGBA"))[..., 3] > 128
    theirs = sheet_mask(rc)
    iou = (ours & theirs).sum() / max(1, (ours | theirs).sum())
    scores.append((label, iou))
    print(f"{label} silhouette match (intersection over union): {iou:.1%}")

grid = Image.new("RGB", (SIZE * 3, SIZE * 3), (107, 109, 115))
for i, (label, path) in enumerate(tiles):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (107, 109, 115, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    if label in ("FRONT", "LEFT"):
        # the sheet's outline in red over our render
        rc = (0, 0) if label == "FRONT" else (1, 0)
        m = sheet_mask(rc)
        edge = m ^ np.roll(m, 1, 0) | m ^ np.roll(m, 1, 1)
        a = np.asarray(im).copy()
        a[edge] = (255, 40, 40)
        im = Image.fromarray(a)
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), label + (f"  match {dict(scores)[label]:.0%}" if label in dict(scores) else ""), fill=(255, 255, 255))
    grid.paste(im, ((i % 3) * SIZE, (i // 3) * SIZE))
sh = sheet.resize((int(sheet.width * SIZE * 3 / sheet.height), SIZE * 3))
both = Image.new("RGB", (sh.width + grid.width, SIZE * 3))
both.paste(sh, (0, 0))
both.paste(grid, (sh.width, 0))
both.save(OUT)
print("wrote", OUT)
