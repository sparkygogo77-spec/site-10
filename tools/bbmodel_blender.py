"""Imports the mod's Blockbench models straight into Blender (no Pillow or trimesh needed: J's PC has neither).

    import bbmodel_blender as bb
    obj = bb.import_bbmodel("dark_lantern.bbmodel", texture="dark_lantern.png", glow=False)

One mesh per model, 1 block = 1 Blender unit, Blockbench Y-up -> Blender Z-up, each cube's own per-face UVs, nearest-
pixel texture, alpha clip. glow=True makes the material emissive (the game draws "_glow" models full-bright).
Preview from the command line (front, three-quarter, top on a dark backdrop with bloom):

    blender -b --python tools/bbmodel_blender.py -- OUTDIR model.bbmodel tex.png [glow.bbmodel glow.png]
"""
import json, math, os, sys
import bpy

# Corner order per face matches Blockbench's uv rectangle: (u0,v0) (u1,v0) (u1,v1) (u0,v1).
FACE_CORNERS = {
    "north": lambda x0, y0, z0, x1, y1, z1: [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
    "south": lambda x0, y0, z0, x1, y1, z1: [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
    "east": lambda x0, y0, z0, x1, y1, z1: [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
    "west": lambda x0, y0, z0, x1, y1, z1: [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
    "up": lambda x0, y0, z0, x1, y1, z1: [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
    "down": lambda x0, y0, z0, x1, y1, z1: [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
}


def _rot(r, origin, p):
    """Blockbench cube rotation (X, then Y, then Z, degrees) about the cube's origin."""
    x, y, z = (p[i] - origin[i] for i in range(3))
    rx, ry, rz = (math.radians(a) for a in r)
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    return (x + origin[0], y + origin[1], z + origin[2])


def _material(name, tex_path, glow, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.abspath(tex_path), check_existing=True)
    img.interpolation = "Closest"
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.35
    if glow:
        nt.links.new(img.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = strength
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    try:
        mat.surface_render_method = "DITHERED"
    except Exception:
        pass
    return mat


def import_bbmodel(path, texture, glow=False, strength=1.0, name=None):
    d = json.load(open(path, encoding="utf-8"))
    tw = d["textures"][0].get("uv_width") or d["resolution"]["width"]
    th = d["textures"][0].get("uv_height") or d["resolution"]["height"]
    verts, faces, uvs = [], [], []
    for el in d["elements"]:
        if el.get("type", "cube") != "cube" or el.get("visibility") is False:
            continue
        inf = el.get("inflate", 0) or 0
        f = [el["from"][i] - inf for i in range(3)]
        t = [el["to"][i] + inf for i in range(3)]
        rot, org = el.get("rotation", [0, 0, 0]), el.get("origin", [0, 0, 0])
        for fname, face in el.get("faces", {}).items():
            if face.get("texture") is None or "uv" not in face:
                continue
            u0, v0, u1, v1 = face["uv"]
            if u0 == u1 or v0 == v1:
                continue
            base = len(verts)
            for p in FACE_CORNERS[fname](*f, *t):
                if any(rot):
                    p = _rot(rot, org, p)
                verts.append((p[0] / 16, -p[2] / 16, p[1] / 16))      # bb (x, y up, z) -> Blender (x, -z, y)
            faces.append((base, base + 1, base + 2, base + 3))
            uvs += [(u0 / tw, 1 - v0 / th), (u1 / tw, 1 - v0 / th), (u1 / tw, 1 - v1 / th), (u0 / tw, 1 - v1 / th)]
    name = name or os.path.splitext(os.path.basename(path))[0]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UV")
    for i, uv in enumerate(uvs):
        uvl.data[i].uv = uv
    me.validate()
    me.materials.append(_material(name, texture, glow, strength))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def preview_scene(scene, res=900):
    """Dark backdrop, Standard view (AgX washes greens white), EEVEE on the GPU, Glare bloom."""
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    w = scene.world or bpy.data.worlds.new("W")
    scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.014, 0.016, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    for nm, loc, energy in (("Key", (2.5, -3, 3.5), 220), ("Rim", (-3, 2.5, 2.5), 120)):
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = energy; ld.size = 2.5
        lo = bpy.data.objects.new(nm, ld); lo.location = loc
        scene.collection.objects.link(lo)
        lo.rotation_euler = (lo.location * -1).to_track_quat("-Z", "Y").to_euler()
    tree = bpy.data.node_groups.new("bb bloom", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); rl.scene = scene
    gl = tree.nodes.new("CompositorNodeGlare")
    try:
        gl.inputs["Type"].default_value = "Bloom"
    except Exception:
        gl.glare_type = "BLOOM"
    for nm, v in (("Threshold", 0.7), ("Strength", 0.6), ("Size", 0.5)):
        try:
            gl.inputs[nm].default_value = v
        except Exception:
            pass
    go = tree.nodes.new("NodeGroupOutput")
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree


def camera(scene, name, target, yaw, elev, dist, lens=60):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name); cd.lens = lens
    co = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(co)
    y, e = math.radians(yaw), math.radians(elev)
    # yaw 0 = looking at the model's front (Blockbench north = Blender +Y... front faces -Y here)
    co.location = Vector(target) + Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e))) * dist
    co.rotation_euler = (Vector(target) - co.location).to_track_quat("-Z", "Y").to_euler()
    return co


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    outdir = os.path.abspath(a[0])                       # Blender resolves a relative render path elsewhere
    os.makedirs(outdir, exist_ok=True)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    scene = bpy.context.scene
    body = import_bbmodel(a[1], a[2], glow=False)
    if len(a) >= 5:
        import_bbmodel(a[3], a[4], glow=True, strength=1.2)
    zs = [v.co.z for v in body.data.vertices]
    h = max(zs) - min(zs)
    target = (0, 0, min(zs) + h / 2)
    preview_scene(scene)
    stem = os.path.splitext(os.path.basename(a[1]))[0]
    for label, yaw, elev in (("front", 0, 6), ("threequarter", 40, 18), ("top", 0, 85)):
        scene.camera = camera(scene, "Cam " + label, target, yaw, elev, h * 2.6)
        scene.render.filepath = os.path.join(outdir, f"{stem}_{label}.png")
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)
