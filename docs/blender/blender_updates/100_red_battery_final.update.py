# Pass 100 (battery range 100-199): the final Red corps battery, exactly as handed to the game
# (docs/handoff/2026-10-13-red-battery-final/): the game's Blockbench models turned into glb, the battery with its
# smooth crimson stone and glowing parts, and the port cover next to it. Builds LanternLive\red_battery_final.blend.
import os, math
import bpy
from mathutils import Vector
SRC = os.path.join(FOLDER, "red_battery_final")
OUT = os.path.join(FOLDER, "red_battery_final.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
scene = bpy.data.scenes.new("Red Battery Final"); col = scene.collection
win = bpy.context.window
if win:
    win.scene = scene


def imp(name, at, rz):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    h = bpy.data.objects.new(name, None); col.objects.link(h)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        if o.parent is None:
            o.parent = h
        if o.type == "MESH":
            for m in o.data.materials:
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE":
                        n.interpolation = "Closest"
                p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                if p:
                    p.inputs["Roughness"].default_value = 0.12; p.inputs["Coat Weight"].default_value = 0.6
                if "_glow" in m.name and p:
                    t = next(n for n in m.node_tree.nodes if n.type == "TEX_IMAGE")
                    m.node_tree.links.new(t.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = 4
    h.location = at; h.rotation_euler = (0, 0, rz)


imp("red_battery", Vector((0, 0, 0)), math.radians(180))
imp("red_battery_cover", Vector((0, 0, 0)), math.radians(180))
imp("red_battery", Vector((3.5, 0, 0)), 0)
w = bpy.data.worlds.new("w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.015, 0.015, 1); scene.world = w
cd = bpy.data.cameras.new("Cam battery"); c = bpy.data.objects.new("Cam battery", cd); col.objects.link(c)
c.location = (1.75, -8.5, 2.2); c.rotation_euler = (Vector((1.75, 0, 1.6)) - c.location).to_track_quat("-Z", "Y").to_euler(); scene.camera = c
k = bpy.data.lights.new("key", "AREA"); k.energy = 500; k.size = 6
ko = bpy.data.objects.new("key", k); ko.location = (2, -6, 6); ko.rotation_euler = (math.radians(45), 0, 0); col.objects.link(ko)
scene.render.engine = "BLENDER_EEVEE"
for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def _after():
    sc = bpy.context.scene
    if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
        sc.lantern_live_watch = True
    return None


bpy.app.timers.register(_after, first_interval=3.0)
print("saved", OUT)
