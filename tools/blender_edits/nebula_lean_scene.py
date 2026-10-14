"""Blender pass 400: the lean Nebula lantern takes side by side (J judges by eye).

    /opt/bl/venv/bin/python tools/blender_edits/nebula_lean_scene.py TAKES_DIR BODY_DIR OUT_DIR

TAKES_DIR is what tools/nebula_lean.py wrote; BODY_DIR holds main's nebula_lantern.bbmodel and its
body textures. Writes OUT_DIR/nebula_lean.blend (textures alongside, paths relative), stills of
every take and every corps, and frames for GIFs. Cameras: "Cam takes", "Cam N1".."Cam N4",
"Cam corps <take>".
"""
import json
import math
import os
import shutil
import sys

import bpy

TAKES_DIR, BODY_DIR, OUT = sys.argv[-3:]
TAKES = ["N1_smoke_ice", "N2_spiral_arms", "N3_aurora", "N4_deep_stars"]
CORPS = ["green", "blue", "red", "yellow", "violet", "orange"]
SFX = {"green": "", "blue": "_blue", "red": "_red", "yellow": "_yellow", "violet": "_violet", "orange": "_orange"}
U = 1 / 16  # one model pixel in Blender units (1 block = 1 m)
SPACING = 1.6

os.makedirs(f"{OUT}/textures", exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def image(path, sequence=False):
    """Copies the texture next to the .blend and loads it with a relative path."""
    name = os.path.basename(path)
    dst = f"{OUT}/textures/{os.path.relpath(os.path.dirname(path), TAKES_DIR).replace(os.sep, '_')}_{name}" if sequence else f"{OUT}/textures/{name}"
    if not os.path.exists(dst):
        shutil.copy(path, dst)
    img = bpy.data.images.load(dst, check_existing=True)
    if sequence:
        img.source = "SEQUENCE"
    return img


def material(name, img, kind, sequence_len=0):
    """kind: 'body' (lit, cutout), 'glass' (full-bright see-through), 'light' (solid glow)."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    if sequence_len:
        tex.image_user.frame_duration = sequence_len
        tex.image_user.use_cyclic = True
        tex.image_user.use_auto_refresh = True
        tex.image_user.frame_start = 0
    mix = nt.nodes.new("ShaderNodeMixShader")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    if kind == "body":
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 0.45
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs[0], mix.inputs[2])
    else:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.6 if kind == "glass" else 1.05
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.blend_method = "BLEND" if kind == "glass" else "CLIP"
    return m


def build_bbmodel(path, mats_by_texture, name, offset, skip_prefixes=()):
    """Every bbmodel cube as a box mesh with its faces' UVs (Blockbench units -> 0..1)."""
    d = json.load(open(path))
    rw, rh = d["resolution"]["width"], d["resolution"]["height"]
    verts, faces, uvs, mats = [], [], [], []
    order = {  # face name -> corner indices of the box (x0/x1, y0/y1, z0/z1), counter-clockwise from outside
        "north": [(1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)],
        "south": [(0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)],
        "east": [(1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)],
        "west": [(0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)],
        "up": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
        "down": [(0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)],
    }
    for e in d["elements"]:
        if any(e["name"].startswith(p) for p in skip_prefixes):
            continue
        f, t, inf = e["from"], e["to"], e.get("inflate", 0)
        f = [f[i] - inf for i in range(3)]
        t = [t[i] + inf for i in range(3)]
        rot = e.get("rotation") or [0, 0, 0]
        org = e.get("origin") or [0, 0, 0]
        for fname, corners in order.items():
            fc = e["faces"].get(fname)
            if not fc or fc.get("texture") is None:
                continue
            u0, v0, u1, v1 = fc["uv"]
            if u0 == u1 or v0 == v1:
                continue
            idx = []
            for cx, cy, cz in corners:
                p = [t[0] if cx else f[0], t[1] if cy else f[1], t[2] if cz else f[2]]
                # rotate round the origin (Blockbench degrees, X then Y then Z)
                x, y, z = p[0] - org[0], p[1] - org[1], p[2] - org[2]
                rx, ry, rz = (math.radians(a) for a in rot)
                y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
                x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
                x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
                x, y, z = x + org[0], y + org[1], z + org[2]
                # Blockbench (+Y up, -Z north) -> Blender (+Z up, -Y north... keep north facing -Y)
                verts.append((x * U, z * U, y * U))
                idx.append(len(verts) - 1)
            faces.append(idx)
            uvs.append([(u0 / rw, 1 - v0 / rh), (u1 / rw, 1 - v0 / rh), (u1 / rw, 1 - v1 / rh), (u0 / rw, 1 - v1 / rh)])
            mats.append(0)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly, quad in zip(me.polygons, uvs):
        for li, uv in zip(poly.loop_indices, quad):
            uvl.data[li].uv = uv
    for m in mats_by_texture:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = offset
    scene.collection.objects.link(ob)
    return ob


def lantern(take, corps, at):
    sfx = SFX[corps]
    body_tex = image(f"{BODY_DIR}/nebula_lantern{sfx}.png")
    body = material(f"body{sfx}", body_tex, "body")
    root = f"{TAKES_DIR}/{take}/assets/lanternring"
    gl = image(f"{root}/textures/entity/bb/nebula_glass_f0{sfx}.png", sequence=True) if not sfx else None
    # Blender reads numbered sequences; corps frames end in a suffix, so give them plain numbering.
    seq_dir = f"{OUT}/textures/{take}_{corps}"
    os.makedirs(seq_dir, exist_ok=True)
    for kind in ("glass", "light"):
        for i in range(32):
            src = f"{root}/textures/entity/bb/nebula_{kind}_f{i}{sfx}.png"
            dst = f"{seq_dir}/{kind}_{i:02d}.png"
            if not os.path.exists(dst):
                shutil.copy(src, dst)
    gimg = bpy.data.images.load(f"{seq_dir}/glass_00.png", check_existing=True)
    gimg.source = "SEQUENCE"
    limg = bpy.data.images.load(f"{seq_dir}/light_00.png", check_existing=True)
    limg.source = "SEQUENCE"
    gm = material(f"glass {take} {corps}", gimg, "glass", 32)
    lm = material(f"light {take} {corps}", limg, "light", 32)
    objs = [build_bbmodel(f"{BODY_DIR}/nebula_lantern.bbmodel", [body], f"body {take} {corps}", at, ("glass", "light", "orb")),
            build_bbmodel(f"{root}/bbmodel/nebula_light.bbmodel", [lm], f"light {take} {corps}", at, ("glow_",)),
            build_bbmodel(f"{root}/bbmodel/nebula_glass.bbmodel", [gm], f"glass {take} {corps}", at)]
    lamp = bpy.data.lights.new(f"glow {take} {corps}", "POINT")
    lamp.energy = 3
    lamp.color = {"green": (0.4, 1, 0.6), "blue": (0.5, 0.7, 1), "red": (1, 0.35, 0.35), "yellow": (1, 0.85, 0.4),
                  "violet": (0.75, 0.5, 1), "orange": (1, 0.6, 0.3)}[corps]
    lo = bpy.data.objects.new(f"glow {take} {corps}", lamp)
    lo.location = (at[0], at[1], at[2] + 11.5 * U)
    scene.collection.objects.link(lo)
    return objs


def camera(name, target, dist, height=0.75, lens=50):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    ob = bpy.data.objects.new(name, cam)
    ob.location = (target[0], target[1] - dist, target[2] + height)
    scene.collection.objects.link(ob)
    c = ob.constraints.new("TRACK_TO")
    empty = bpy.data.objects.new(name + " aim", None)
    empty.location = target
    scene.collection.objects.link(empty)
    c.target = empty
    return ob


# Row 1: the four takes in green. Rows 2-5: every corps for each take (behind, far apart).
for i, take in enumerate(TAKES):
    lantern(take, "green", (i * SPACING, 0, 0))
    camera(f"Cam {take[:2]}", (i * SPACING, 0, 0.66), 2.3, 0.3)
camera("Cam takes", ((len(TAKES) - 1) * SPACING / 2, 0, 0.6), 7.5, 0.6, 40)
for r, take in enumerate(TAKES):
    x0 = 30 + r * 30   # rows far to the side, so no camera sees another row
    for c, corps in enumerate(CORPS):
        lantern(take, corps, (x0 + c * SPACING, 0, 0))
    camera(f"Cam corps {take[:2]}", (x0 + (len(CORPS) - 1) * SPACING / 2, 0, 0.6), 10.5, 0.6, 40)

# Floor and a dark night world.
bpy.ops.mesh.primitive_plane_add(size=300, location=(60, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new("floor")
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.035, 0.04, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
floor.data.materials.append(fm)
world = bpy.data.worlds.new("night")
world.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.005, 0.008, 1)
scene.world = world
key = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN"))
key.data.energy = 0.6
key.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(key)

# Render: Cycles, Standard view (AgX washes saturated greens to white), compositor bloom.
scene.render.engine = "CYCLES"
scene.cycles.samples = int(os.environ.get("SAMPLES", "20"))
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x, scene.render.resolution_y = 960, 640
scene.frame_start, scene.frame_end = 0, 31
scene.render.fps = 24
scene.render.film_transparent = False
def bloom():
    """Compositor bloom fed from Render Layers (Blender 5: settings are node inputs)."""
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
    gl.inputs["Threshold"].default_value = 0.55
    gl.inputs["Strength"].default_value = 0.9
    gl.inputs["Size"].default_value = 0.6
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], out.inputs[0])


bloom()

bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/nebula_lean.blend", relative_remap=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_mainfile()

if os.environ.get("LL_NO_RENDER") != "1":
    os.makedirs(f"{OUT}/renders", exist_ok=True)
    shots = [("Cam takes", "takes")] + [(f"Cam {t[:2]}", t) for t in TAKES] + [(f"Cam corps {t[:2]}", f"corps_{t}") for t in TAKES]
    for cam, label in shots:
        scene.camera = bpy.data.objects[cam]
        scene.frame_set(8)
        scene.render.filepath = f"{OUT}/renders/{label}.png"
        bpy.ops.render.render(write_still=True)
    if os.environ.get("GIF") == "1":
        scene.camera = bpy.data.objects["Cam takes"]
        scene.render.resolution_x, scene.render.resolution_y = 720, 480
        scene.cycles.samples = 10
        for f in range(0, 32, 2):
            scene.frame_set(f)
            scene.render.filepath = f"{OUT}/renders/gif/takes_{f:02d}.png"
            bpy.ops.render.render(write_still=True)
