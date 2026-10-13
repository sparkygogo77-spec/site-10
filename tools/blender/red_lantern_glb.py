"""Exports the Red Lantern versions from tools/pixel_red_lantern.py as .glb files that import
straight into J's Lantern Live scene: 1 unit = 1 block, per-face colour attributes `col` (sRGB
colour) and `glow` (the charge weight, grey), one material per kind.

    python tools/blender/red_lantern_glb.py <work dir> <out dir> [r1 r2 r3]
"""
import os, sys
import numpy as np
import bpy

WORK, OUT = sys.argv[1], sys.argv[2]
NAMES = sys.argv[3:] or ["r1", "r2", "r3"]
os.makedirs(OUT, exist_ok=True)
KINDS = {0: "matte", 1: "metal", 4: "glass", 5: "vein"}

for name in NAMES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    d = np.load(os.path.join(WORK, f"red_{name}.npz"))
    q, c, k, w = d["quads"], d["col"], d["kind"], d["glow"]
    verts = q.reshape(-1, 3) / 16.0
    me = bpy.data.meshes.new(f"red_lantern_{name}")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    for attr, vals in (("col", c / 255.0), ("glow", np.repeat(w[:, None], 3, 1))):
        a = me.color_attributes.new(attr, "BYTE_COLOR", "CORNER")
        cc = np.repeat(vals, 4, axis=0)
        a.data.foreach_set("color_srgb", np.hstack([cc, np.ones((len(cc), 1))]).ravel())
    slots = {}
    for kind, label in KINDS.items():
        m = bpy.data.materials.new(label)
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        at = m.node_tree.nodes.new("ShaderNodeVertexColor"); at.layer_name = "col"
        m.node_tree.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Metallic"].default_value = 0.8 if kind == 1 else 0.0
        bsdf.inputs["Roughness"].default_value = {1: 0.3, 4: 0.1, 5: 0.2}.get(kind, 0.85)
        slots[kind] = len(me.materials)
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.array([slots[int(x)] for x in k]))
    o = bpy.data.objects.new(f"red_lantern_{name}", me)
    bpy.context.scene.collection.objects.link(o)
    path = os.path.join(OUT, f"red_lantern_{name}.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_vertex_color="ACTIVE",
                              export_all_vertex_colors=True)
    print(name, path, os.path.getsize(path))
