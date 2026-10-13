# Pass 74: the lantern's light on the gold (J: "the light of the lantern should create a glowing or reflection
# effect on the gold along the sides"). The glass is solid geometry, so the light inside it was shadowed
# off the gold. Three takes side by side, all charging together with G3:
#   R1  reflection only: the inner light shines through the glass, so the gold catches real green highlights
#   R2  R1 plus a soft green glow on the gold faces that face the glass (collar undersides, the middle band)
#   R3  R1 with polished gold and green light pooling along the sides
import bpy
from mathutils import Vector

scene = bpy.context.scene


def find(prefix):
    for o in scene.objects:
        if o.name.startswith(prefix):
            return o
    return None


src = find("Charge lantern F3")
ctl = find("Charge control F3")
light = find("Charge inner light F3")
for o in list(bpy.data.objects):
    if o.name.startswith(("Gold take", "Gold label", "Gold light")):
        bpy.data.objects.remove(o, do_unlink=True)


def gold_mat(name, rough, glow):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    a = N.new("ShaderNodeAttribute"); a.attribute_name = "col"
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(a.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.95
    b.inputs["Roughness"].default_value = rough
    if glow:
        # faces turned toward the glass glow softly green with the charge: collar undersides, the band's edges
        geo = N.new("ShaderNodeNewGeometry")
        tc = N.new("ShaderNodeTexCoord")
        sepn = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], sepn.inputs[0])
        vt = N.new("ShaderNodeVectorTransform"); vt.vector_type = "NORMAL"; vt.convert_from = "WORLD"; vt.convert_to = "OBJECT"
        L.new(geo.outputs["Normal"], vt.inputs[0]); L.new(vt.outputs[0], sepn.inputs[0])
        sepp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sepp.inputs[0])

        def op(o, x, y=None):
            n = N.new("ShaderNodeMath"); n.operation = o
            for i, s in enumerate((x, y)):
                if s is None:
                    continue
                if isinstance(s, (int, float)):
                    n.inputs[i].default_value = s
                else:
                    L.new(s, n.inputs[i])
            return n.outputs[0]
        dz = op("SUBTRACT", sepp.outputs[2], 11.75)
        toward = op("MULTIPLY", op("MULTIPLY", sepn.outputs[2], -1.0), op("SIGN", dz))   # normal pointing back at the glass
        facing = op("MAXIMUM", op("SUBTRACT", toward, 0.4), 0.0)
        frame_only = op("LESS_THAN", sepp.outputs[2], 23.5)
        v = N.new("ShaderNodeValue")
        d = v.outputs[0].driver_add("default_value").driver
        d.type = "SCRIPTED"
        var = d.variables.new(); var.name = "c"; var.targets[0].id = ctl; var.targets[0].data_path = '["charge"]'
        d.expression = "min(max(c, 0), 1.4) * min(max(c, 0), 1.4)"
        b.inputs["Emission Color"].default_value = (0.2, 1.0, 0.32, 1)
        L.new(op("MULTIPLY", op("MULTIPLY", op("MULTIPLY", facing, v.outputs[0]), frame_only), 2.4), b.inputs["Emission Strength"])
    L.new(b.outputs[0], out.inputs["Surface"])
    return m


takes = [("R1", 0.22, False, "R1  reflection only"), ("R2", 0.22, True, "R2  + soft green glow facing the glass"),
         ("R3", 0.12, False, "R3  polished gold, green pooling on the sides")]
for i, (key, rough, glow, title) in enumerate(takes):
    if key == "R1":
        o = src
    else:
        o = src.copy(); o.animation_data_clear(); o.name = f"Gold take {key}"
        scene.collection.objects.link(o)
        o.location = src.location + Vector(((i) * 2.4, 0, 0))
    gm = gold_mat(f"gold {key}", rough, glow)
    o.material_slots[1].link = "OBJECT"; o.material_slots[1].material = gm
    # the inner light shines through the glass (no shadow from it), so the gold catches it
    li = light.data.copy() if key != "R1" else light.data
    li.use_shadow = False
    if key == "R1":
        lo = light
    else:
        lo = bpy.data.objects.new(f"Gold light {key}", li); scene.collection.objects.link(lo)
        lo.location = light.location + Vector((i * 2.4, 0, 0))
    if key == "R3":   # green light pooling along both sides, on the frame
        for sx in (-1, 1):
            al = bpy.data.lights.new(f"gold side {sx}", "POINT"); al.color = (0.3, 1.0, 0.4); al.use_shadow = False
            al.shadow_soft_size = 0.2
            dd = al.driver_add("energy").driver; dd.type = "SCRIPTED"
            vv = dd.variables.new(); vv.name = "c"; vv.targets[0].id = ctl; vv.targets[0].data_path = '["charge"]'
            dd.expression = "pow(min(max(c, 0), 1.4), 2) * 18"
            ao = bpy.data.objects.new(f"Gold light R3 side {sx}", al); scene.collection.objects.link(ao)
            ao.location = o.location + Vector((sx * 0.42, -0.05, 11.75 / 16))
    cu = bpy.data.curves.new(f"gold label {key}", "FONT"); cu.body = title; cu.size = 0.13; cu.align_x = "CENTER"
    lb = bpy.data.objects.new(f"Gold label {key}", cu); scene.collection.objects.link(lb)
    lb.location = o.location + Vector((0, 0, 2.1)); lb.rotation_euler = (1.5708, 0, 0)
    em = bpy.data.materials.new(f"gold label {key}"); em.use_nodes = True
    pp = em.node_tree.nodes.get("Principled BSDF"); pp.inputs["Emission Color"].default_value = (0.9, 1, 0.9, 1)
    pp.inputs["Emission Strength"].default_value = 2.0
    cu.materials.append(em)

cd = bpy.data.cameras.new("Cam gold takes"); cd.lens = 50
cam = bpy.data.objects.new("Cam gold takes", cd); scene.collection.objects.link(cam)
tgt = src.location + Vector((2.4, 0, 0.95))
cam.location = tgt + Vector((0.4, -10.5, 0.9))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
            a.tag_redraw()
import os
scene.frame_set(330)
scene.render.filepath = os.path.join(FOLDER, "renders", "74_gold_takes.png")
if not os.environ.get("LL_NO_RENDER"):
    bpy.ops.render.render(write_still=True)
scene.frame_set(1)
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
