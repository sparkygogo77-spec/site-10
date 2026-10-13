# Pass 73: the gold frame back to real metal (J: "the entirety of the yellow became brighter... will it look
# cheap in game?"). Take 2 gave the gold its own faint green glow, which flattens metal into a pale matte
# shape. Now the gold has no glow of its own: it only reflects the lantern's light, from a stronger inner
# light, so the frame catches green on the sides facing the glass and stays dark gold elsewhere.
import bpy
for m in bpy.data.materials:
    if m.name.startswith("charge gold lit"):
        p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if p:
            for l in list(p.inputs["Emission Strength"].links):
                m.node_tree.links.remove(l)
            p.inputs["Emission Strength"].default_value = 0.0
            p.inputs["Metallic"].default_value = 0.95
            p.inputs["Roughness"].default_value = 0.22
for o in bpy.context.scene.objects:
    if o.type == "LIGHT" and o.name.startswith("Charge inner light"):
        d = o.data.animation_data.drivers[0].driver if o.data.animation_data and o.data.animation_data.drivers else None
        if d:
            d.expression = "pow(max(c, 0), 2) * 110 + max(c - 1, 0) * 350 + 6 * min(c * 1000, 1)"
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
