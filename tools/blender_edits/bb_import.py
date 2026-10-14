"""Shared helpers for building game bbmodels in Blender (headless)."""
import json
import math

import bpy

U = 1 / 16  # one model pixel in Blender units (1 block = 1 m)
ORDER = {  # face -> box corners (x, y, z picks of from/to), counter-clockwise seen from outside
    "north": [(1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)],
    "south": [(0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)],
    "east": [(1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)],
    "west": [(0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)],
    "up": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
    "down": [(0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)],
}


def box_uv(e):
    """Per-face UVs of Minecraft box UV from uv_offset (what the game's BbModel uses)."""
    f, t = e["from"], e["to"]
    w, h, d = (t[i] - f[i] for i in range(3))
    u, v = e.get("uv_offset", [0, 0])
    return {
        "east": [u, v + d, u + d, v + d + h], "north": [u + d, v + d, u + d + w, v + d + h],
        "west": [u + d + w, v + d, u + 2 * d + w, v + d + h], "south": [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h],
        "up": [u + d, v, u + d + w, v + d], "down": [u + d + w, v, u + d + 2 * w, v + d],
    }


def material(name, img, kind, strength=None):
    """kind: 'solid' (lit cutout), 'glass' (full-bright see-through), 'glow' (emissive)."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    mix = nt.nodes.new("ShaderNodeMixShader")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    if kind == "solid":
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 0.5
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs[0], mix.inputs[2])
    else:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = strength if strength is not None else (1.0 if kind == "glass" else 3.0)
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def build(path, mats, name, location, kind_of=lambda n: 0, scene=None, use_box_uv=True):
    """Every cube of a bbmodel as quads. mats: material list; kind_of(cube name) -> material index."""
    scene = scene or bpy.context.scene
    d = json.load(open(path))
    rw, rh = d["resolution"]["width"], d["resolution"]["height"]
    verts, faces, uvs, mi = [], [], [], []
    for e in d["elements"]:
        if e.get("type", "cube") != "cube":
            continue
        f, t, inf = e["from"], e["to"], e.get("inflate", 0)
        f = [f[i] - inf for i in range(3)]
        t = [t[i] + inf for i in range(3)]
        rot = e.get("rotation") or [0, 0, 0]
        org = e.get("origin") or [0, 0, 0]
        uvmap = box_uv(e) if (use_box_uv and e.get("box_uv", True)) else {k: v["uv"] for k, v in e.get("faces", {}).items()}
        for fname, corners in ORDER.items():
            if fname not in uvmap:
                continue
            u0, v0, u1, v1 = uvmap[fname]
            if u0 == u1 or v0 == v1:
                continue
            idx = []
            for cx, cy, cz in corners:
                x, y, z = (t[0] if cx else f[0]) - org[0], (t[1] if cy else f[1]) - org[1], (t[2] if cz else f[2]) - org[2]
                rx, ry, rz = (math.radians(a) for a in rot)
                y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
                x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
                x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
                verts.append(((x + org[0]) * U, (z + org[2]) * U, (y + org[1]) * U))
                idx.append(len(verts) - 1)
            faces.append(idx)
            uvs.append([(u0 / rw, 1 - v0 / rh), (u1 / rw, 1 - v0 / rh), (u1 / rw, 1 - v1 / rh), (u0 / rw, 1 - v1 / rh)])
            mi.append(kind_of(e.get("name", "")))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly, quad, m in zip(me.polygons, uvs, mi):
        poly.material_index = m
        for li, uv in zip(poly.loop_indices, quad):
            uvl.data[li].uv = uv
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    scene.collection.objects.link(ob)
    return ob


def camera(name, location, target, lens=40, scene=None):
    scene = scene or bpy.context.scene
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.data.lens = lens
    cam.location = location
    scene.collection.objects.link(cam)
    aim = bpy.data.objects.new(name + " aim", None)
    aim.location = target
    scene.collection.objects.link(aim)
    c = cam.constraints.new("TRACK_TO")
    c.target = aim
    return cam


def night(scene=None, bloom_threshold=0.55):
    """Dark world, Standard view (AgX washes greens out), Cycles, compositor bloom."""
    scene = scene or bpy.context.scene
    world = bpy.data.worlds.new("night")
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.005, 0.008, 1)
    scene.world = world
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = "Standard"
    if hasattr(scene, "compositing_node_group"):
        ng = bpy.data.node_groups.new("bloom", "CompositorNodeTree")
        scene.compositing_node_group = ng
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        out = ng.nodes.new("NodeGroupOutput")
    else:
        scene.use_nodes = True
        ng = scene.node_tree
        for n in list(ng.nodes):
            ng.nodes.remove(n)
        out = ng.nodes.new("CompositorNodeComposite")
    rl = ng.nodes.new("CompositorNodeRLayers")
    gl = ng.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Bloom"
    gl.inputs["Threshold"].default_value = bloom_threshold
    gl.inputs["Strength"].default_value = 0.9
    gl.inputs["Size"].default_value = 0.6
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], out.inputs[0])
