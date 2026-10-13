# Pass 75: J's pick for the gold, R2 + R3 together (R4): R3's polished gold with R2's soft green glow on the
# gold faces that face the glass, plus R3's green light pooling along the sides. Applied to the main G3
# lantern (the one the ring docks into), whose label now reads R4. R2 and R3 stay beside it to compare.
import bpy
from mathutils import Vector

scene = bpy.context.scene
src = next(o for o in scene.objects if o.name.startswith("Charge lantern F3"))
ctl = next(o for o in scene.objects if o.name.startswith("Charge control F3"))
glow_src = bpy.data.materials.get("gold R2")
m = glow_src.copy(); m.name = "gold R4"
p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
p.inputs["Roughness"].default_value = 0.12          # R3's polish
src.material_slots[1].link = "OBJECT"; src.material_slots[1].material = m
for o in list(bpy.data.objects):
    if o.name.startswith("Gold light R4"):
        bpy.data.objects.remove(o, do_unlink=True)
for sx in (-1, 1):                                    # R3's green pooling on the sides
    al = bpy.data.lights.new(f"gold R4 side {sx}", "POINT"); al.color = (0.3, 1.0, 0.4); al.use_shadow = False
    al.shadow_soft_size = 0.2
    dd = al.driver_add("energy").driver; dd.type = "SCRIPTED"
    vv = dd.variables.new(); vv.name = "c"; vv.targets[0].id = ctl; vv.targets[0].data_path = '["charge"]'
    dd.expression = "pow(min(max(c, 0), 1.4), 2) * 18"
    ao = bpy.data.objects.new(f"Gold light R4 side {sx}", al); scene.collection.objects.link(ao)
    ao.location = src.location + Vector((sx * 0.42, -0.05, 11.75 / 16))
lb = next((o for o in scene.objects if o.name.startswith("Gold label R1")), None)
if lb:
    lb.data.body = "R4  polished gold + green glow facing the glass"
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
