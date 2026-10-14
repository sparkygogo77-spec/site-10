# Pass 98: corps metals (J, 2026-10-14: "create colours of every metal like diamond in the hue of every lantern corps,
# do black as a metal"). The shiny vanilla blocks - diamond, emerald, iron, gold, netherite, copper - recoloured into
# crimson, green, blue, yellow, violet, orange and black (tools/corps_metal_recolour.py; preview copies from J's game in
# LanternLive\metal_tex). Each is a 2-block cube shaded as polished metal, the way the diamond ID shines under J's
# shaders, on a dark floor with a soft sky and three lights so the reflections show.
# Rows: blocks (front diamond ... back copper). Columns: colours. Cameras: Cam all, Cam diamond (close on the front row).
# Builds LanternLive\corps_metals.blend.
import math, os
import bpy
from mathutils import Vector

R = math.radians
TEX = os.path.join(FOLDER, "metal_tex")
OUT = os.path.join(FOLDER, "corps_metals.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Corps Metals")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Corps Metals")
col = scene.collection
win = bpy.context.window
if win:
    win.scene = scene
COLOURS = ["crimson", "green", "blue", "yellow", "violet", "orange", "black"]
BLOCKS = ["diamond_block", "emerald_block", "iron_block", "gold_block", "netherite_block", "copper_block"]


def link(o):
    col.objects.link(o)
    return o


def metal(block, colour):
    m = bpy.data.materials.new(f"CM {block} {colour}"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.interpolation = "Closest"
    t.image = bpy.data.images.load(os.path.join(TEX, f"{block}_{colour}.png"))
    L.new(t.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Metallic"].default_value = 0.85 if colour != "black" else 0.95
    p.inputs["Roughness"].default_value = 0.16 if colour != "black" else 0.12
    for nm, v in (("Coat Weight", 0.35), ("Coat Roughness", 0.05)):
        if nm in p.inputs:
            p.inputs[nm].default_value = v
    return m


def cube(name, loc, mat):
    me = bpy.data.meshes.new(name)
    v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(v, [], f)
    uv = me.uv_layers.new()
    for poly in me.polygons:
        for li, c in zip(poly.loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            uv.data[li].uv = c
    me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    return o


for j, colour in enumerate(COLOURS):
    for i, block in enumerate(BLOCKS):
        cube(f"CM {block} {colour}", ((j - 3) * 3.0, i * 3.0, 1.0), metal(block, colour))
    cu = bpy.data.curves.new("CM label " + colour, "FONT"); cu.body = colour; cu.size = 0.6; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("CM label " + colour, cu)); t.location = ((j - 3) * 3.0, -2.2, 0.01)
for i, block in enumerate(BLOCKS):
    cu = bpy.data.curves.new("CM row " + block, "FONT"); cu.body = block.replace("_block", ""); cu.size = 0.6; cu.align_x = "RIGHT"
    t = link(bpy.data.objects.new("CM row " + block, cu)); t.location = (-11.2, i * 3.0 - 0.2, 0.01)
fm = bpy.data.materials.new("CM floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.25
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 8, 0))
fl = bpy.context.active_object
for c in fl.users_collection:
    c.objects.unlink(fl)
link(fl); fl.name = "CM floor"; fl.data.materials.append(fm)
world = bpy.data.worlds.new("CM sky"); world.use_nodes = True
N, L = world.node_tree.nodes, world.node_tree.links
sky = N.new("ShaderNodeTexSky")
try:
    sky.sky_type = "NISHITA"; sky.sun_elevation = R(25); sky.sun_rotation = R(140)
except Exception:
    pass
L.new(sky.outputs["Color"], N["Background"].inputs["Color"]); N["Background"].inputs["Strength"].default_value = 0.06
scene.world = world
for nm, loc, e, c in (("key", (-12, -10, 14), 420, (1, 0.95, 0.9)), ("rim", (14, 22, 10), 380, (0.8, 0.85, 1)),
                      ("fill", (0, -16, 4), 90, (1, 1, 1))):
    ld = bpy.data.lights.new("CM " + nm, "AREA"); ld.size = 8; ld.energy = e; ld.color = c
    lo = link(bpy.data.objects.new("CM " + nm, ld)); lo.location = loc
    lo.rotation_euler = (Vector((0, 8, 1)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def cam(name, eye, tgt, lens):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = eye; c.data.lens = lens
    c.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    return c


cams = {"all": cam("Cam all", (0, -22, 15), (0, 7, 0), 32), "diamond": cam("Cam diamond", (0, -11, 4.5), (0, 1, 1), 32)}
scene.camera = cams["all"]
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass
try:
    scene.eevee.use_raytracing = True
except Exception:
    pass
rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for k, c in cams.items():
        scene.camera = c
        scene.render.filepath = os.path.join(rdir, f"98_metals_{k}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["all"]
for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
