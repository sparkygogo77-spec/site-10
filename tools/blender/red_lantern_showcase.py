"""Renders the pixel-grid Red Lantern versions from tools/pixel_red_lantern.py in Blender: each one
at rest and charged from the same front three-quarter view on dark stone, plus a straight-on
close-up of its emblem, then lays them side by side in one sheet.

    python tools/pixel_red_lantern.py <work dir>
    python tools/blender/red_lantern_showcase.py <work dir> <out dir> [--samples 64] [--names r1,r2,r3]

Writes red_lanterns_rest.png, red_lanterns_charged.png, red_lanterns_emblems.png and
red_lanterns_sheet.png (all three rows) to <out dir>.
"""
import math, os, sys
import numpy as np
import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WORK, OUT = sys.argv[1], sys.argv[2]
SAMPLES = int(sys.argv[sys.argv.index("--samples") + 1]) if "--samples" in sys.argv else 64
NAMES = sys.argv[sys.argv.index("--names") + 1].split(",") if "--names" in sys.argv else ["r1", "r2", "r3"]
TITLES = {"r1": "R1  Barrel", "r2": "R2  Heart", "r3": "R3  Octagon"}
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name, kind):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Ln = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    col = N.new("ShaderNodeAttribute"); col.attribute_name = "col"
    emit = N.new("ShaderNodeAttribute"); emit.attribute_name = "emit"
    Ln.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    Ln.new(emit.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.0
    if kind == "metal":
        bsdf.inputs["Metallic"].default_value = 0.85
        bsdf.inputs["Roughness"].default_value = 0.38
    elif kind == "glass":
        bsdf.inputs["Roughness"].default_value = 0.1
        bsdf.inputs["Coat Weight"].default_value = 1.0
        bsdf.inputs["Coat Roughness"].default_value = 0.05
    elif kind == "glow":
        bsdf.inputs["Roughness"].default_value = 0.2
        bsdf.inputs["Coat Weight"].default_value = 0.6
    else:
        bsdf.inputs["Roughness"].default_value = 0.85
    return m


MATS = {0: material("matte", "matte"), 1: material("metal", "metal"), 4: material("glass", "glass"),
        5: material("glow", "glow")}
SLOT = {0: 0, 1: 1, 4: 2, 5: 3}

objs = {}
for name in NAMES:
    d = np.load(os.path.join(WORK, f"red_{name}.npz"))
    q, c, k, w = d["quads"], d["col"], d["kind"], d["glow"]
    verts = q.reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (c / 255.0) ** 2.2
    for attr_name, vals in (("col", lin), ("emit", lin * w[:, None])):
        a = me.color_attributes.new(attr_name, "FLOAT_COLOR", "CORNER")
        cc = np.repeat(vals, 4, axis=0)
        a.data.foreach_set("color", np.hstack([cc, np.ones((len(cc), 1))]).ravel())
    for m in MATS.values():
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.array([SLOT[int(x)] for x in k]))
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    objs[name] = (o, float(d["emblem_z"]))

# dark stone floor
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
floor = bpy.context.active_object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fb = fm.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.035, 0.032, 0.03, 1)
fb.inputs["Roughness"].default_value = 0.7
floor.data.materials.append(fm)

world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)


def area(name, loc, power, size, target=(0, 0, 12)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = power; ld.size = size
    o = bpy.data.objects.new(name, ld); scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


KEY = area("key", (-30, -42, 42), 16000, 30)
FILL = area("fill", (38, -26, 14), 4000, 30)
RIM = area("rim", (12, 42, 34), 7000, 25)
glow_lights = []
for i, (a, dist) in enumerate(((-90, 8.5), (30, 8.5), (150, 8.5))):
    ld = bpy.data.lights.new(f"red{i}", "POINT"); ld.color = (1.0, 0.12, 0.08); ld.shadow_soft_size = 2
    o = bpy.data.objects.new(f"red{i}", ld); scene.collection.objects.link(o)
    o.location = (dist * math.cos(math.radians(a)), dist * math.sin(math.radians(a)), 6)
    glow_lights.append(o)

scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam


def state(charged):
    for m, rest, lit in ((MATS[4], 0.12, 3.0), (MATS[5], 0.6, 7.0)):
        m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = lit if charged else rest
    for o in glow_lights:
        o.data.energy = 900 if charged else 60
    KEY.data.energy = 9000 if charged else 16000
    FILL.data.energy = 2000 if charged else 4000


def show_only(name):
    for n, (o, _) in objs.items():
        o.hide_render = n != name


def render(path, w, h):
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def bloom(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, float)
    lum = a.max(-1, keepdims=True)
    hot = np.clip((lum - 200) / 55, 0, 1) * a
    glow = Image.fromarray(hot.astype(np.uint8))
    b1 = np.asarray(glow.filter(ImageFilter.GaussianBlur(6)), float)
    b2 = np.asarray(glow.filter(ImageFilter.GaussianBlur(20)), float)
    Image.fromarray(np.clip(a + 0.7 * b1 + 0.6 * b2, 0, 255).astype(np.uint8)).save(path)


shots = {}
yaw, pitch = math.radians(-32), math.radians(14)
for name in NAMES:
    show_only(name)
    o, ez = objs[name]
    # front three-quarter, perspective
    cam_d.type = "PERSP"; cam_d.lens = 60
    tgt = Vector((0, 0, 13.5))
    dv = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    cam.location = tgt + dv * 78
    cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    floor.hide_render = False
    for st in (False, True):
        state(st)
        p = os.path.join(OUT, f"{name}_{'charged' if st else 'rest'}.png")
        render(p, 560, 760)
        bloom(p)
        shots[(name, "charged" if st else "rest")] = p
    # emblem close-up: straight on, orthographic, at rest lighting with a little glow
    state(False)
    for m in (MATS[5],):
        m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.2
    cam_d.type = "ORTHO"; cam_d.ortho_scale = 9.5
    cam.location = Vector((-2.5, -60, ez + 1.5))
    cam.rotation_euler = (Vector((0, 0, ez)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    p = os.path.join(OUT, f"{name}_emblem.png")
    render(p, 560, 560)
    bloom(p)
    shots[(name, "emblem")] = p


def sheet(rows, path):
    W, pad, head = 560, 12, 34
    tiles = [[Image.open(shots[(n, r)]) for n in NAMES] for r in rows]
    hgt = sum(t[0].height + head for t in tiles)
    out = Image.new("RGB", (len(NAMES) * (W + pad) + pad, hgt + pad), (20, 18, 18))
    dr = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    y = 0
    for r, row in zip(rows, tiles):
        for i, (n, t) in enumerate(zip(NAMES, row)):
            x = pad + i * (W + pad)
            dr.text((x + 6, y + 6), f"{TITLES.get(n, n)}  ·  {r}", fill=(235, 200, 190), font=font)
            out.paste(t, (x, y + head))
        y += row[0].height + head
    out.save(path)
    print("wrote", path)


sheet(["rest"], os.path.join(OUT, "red_lanterns_rest.png"))
sheet(["charged"], os.path.join(OUT, "red_lanterns_charged.png"))
sheet(["emblem"], os.path.join(OUT, "red_lanterns_emblems.png"))
sheet(["rest", "charged", "emblem"], os.path.join(OUT, "red_lanterns_sheet.png"))
