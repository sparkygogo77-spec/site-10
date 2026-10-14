"""Blender pass 410: ram barrier takes R1-R4 in front of a flying stand-in.

    /opt/bl/venv/bin/python tools/blender_edits/ram_barrier_scene.py TAKES_DIR OUT_DIR

Cameras per take: "Cam <R> side", "Cam <R> front", "Cam <R> own" (the flyer's view from behind);
"Cam corps" shows R1-R4 in six corps colours is not built (colour is a texture swap).
"""
import math
import os
import shutil
import sys

import bpy

sys.path.insert(0, os.path.dirname(__file__))
import bb_import as bb

TAKES_DIR, OUT = sys.argv[-2:]
TAKES = ["R1_glass_shell", "R2_lattice", "R3_particle_field", "R4_pressure_rings"]
os.makedirs(f"{OUT}/textures", exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def stand_in(at):
    """A Steve-sized figure flying flat, head first toward -Y (north), arm forward with the ring."""
    mat = bpy.data.materials.new("flyer")
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.09, 0.1, 1)
    parts = [((0, -0.05, 0), (0.5, 0.75, 0.25)),   # torso (flat: length along y)
             ((0, -0.62, 0), (0.5, 0.5, 0.5)),     # head
             ((0.12, 0.72, 0), (0.25, 0.75, 0.25)), ((-0.12, 0.72, 0), (0.25, 0.75, 0.25)),  # legs
             ((0.37, -0.75, 0), (0.25, 0.75, 0.25)), ((-0.37, 0.3, 0), (0.25, 0.75, 0.25))]  # arms
    for (x, y, z), (sx, sy, sz) in parts:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(at[0] + x, at[1] + y, at[2] + z))
        o = bpy.context.object
        o.scale = (sx, sy, sz)
        o.data.materials.append(mat)
    ring = bpy.data.materials.new("ring")
    ring.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.3, 1, 0.5, 1)
    ring.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 6
    bpy.ops.mesh.primitive_cube_add(size=0.12, location=(at[0] + 0.37, at[1] - 1.12, at[2] + 0.05))
    bpy.context.object.data.materials.append(ring)


for i, take in enumerate(TAKES):
    x0 = i * 200      # far apart: no camera sees another take
    root = f"{TAKES_DIR}/{take}/assets/lanternring"
    src = f"{root}/textures/entity/bb/ram_barrier.png"
    dst = f"{OUT}/textures/{take}_ram_barrier.png"
    shutil.copy(src, dst)
    img = bpy.data.images.load(dst)
    mats = [bb.material(f"{take} glass", img, "glass", 1.0), bb.material(f"{take} glow", img, "glow", 2.4)]
    centre = (x0, 0, 2.0)                 # the flyer's middle, two blocks up
    bb.build(f"{root}/bbmodel/ram_barrier.bbmodel", mats, f"ram {take}", centre,
             kind_of=lambda n: 1 if n.startswith("glow") else 0)
    stand_in(centre)
    bb.camera(f"Cam {take[:2]} side", (x0 + 11, -1.5, 3.2), (x0, -2.5, 2.0), 32)
    bb.camera(f"Cam {take[:2]} front", (x0 - 7, -11, 4.0), (x0, -2.5, 2.0), 32)
    bb.camera(f"Cam {take[:2]} own", (x0 + 0.4, 2.6, 2.7), (x0, -6, 2.0), 22)

bpy.ops.mesh.primitive_plane_add(size=1600, location=(300, 0, -2))
fm = bpy.data.materials.new("ground")
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.04, 0.03, 1)
bpy.context.object.data.materials.append(fm)
sun = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN"))
sun.data.energy = 0.5
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun)
bb.night(scene)
scene.cycles.samples = int(os.environ.get("SAMPLES", "20"))
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 960, 600

bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/ram_barrier.blend")
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_mainfile()

if os.environ.get("LL_NO_RENDER") != "1":
    os.makedirs(f"{OUT}/renders", exist_ok=True)
    for take in TAKES:
        for view in ("side", "front", "own"):
            scene.camera = bpy.data.objects[f"Cam {take[:2]} {view}"]
            scene.render.filepath = f"{OUT}/renders/{take}_{view}.png"
            bpy.ops.render.render(write_still=True)
