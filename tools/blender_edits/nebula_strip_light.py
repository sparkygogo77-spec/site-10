"""Blender pass 430: the Nebula's light source wrapped in our construct look strips (J, 2026-10-14:
"Throw it to blender and let it wrap our textures around the light source").

The light is a lathe (a profile turned round the lantern's axis) and the strip's square frame wraps
once round it, so the strip's own seamless tiling closes the wrap with no seam. The light needs no
texture of its own: in game it samples the corps' picked construct strip from the block atlas,
which already animates, so there is one strip per corps and no copies. tools/nebula_light_profiles.json
holds the takes' profiles; this scene builds the same quads and UVs the game would.

    /opt/bl/venv/bin/python tools/blender_edits/nebula_strip_light.py ASSETS GLASS_TAKE OUT
ASSETS is src/main/resources/assets/lanternring; GLASS_TAKE is a lean glass take's assets folder
(docs/handoff/2026-10-14-nebula-lean/takes/N1_smoke_ice/assets/lanternring). Writes OUT/nebula_strip_light.blend
(textures relative in OUT/textures), stills in OUT/renders and, with GIF=1, OUT/renders/gif/.
"""
import json
import math
import os
import shutil
import sys

import bpy
import numpy as np

ASSETS, GLASS, OUT = sys.argv[-3:]
HERE = os.path.dirname(os.path.abspath(__file__))
PROFILES = json.load(open(os.path.join(HERE, "..", "nebula_light_profiles.json")))
TAKES = list(PROFILES["takes"])
U = 1 / 16
SPACING = 1.6
# Each corps' default construct look in the Ring Lab (LabSettings); orange has no strip yet.
CORPS_STRIP = {"green": "w1_neon", "blue": "blue_b1", "red": "red_r1", "yellow": "yellow_y1", "violet": "violet_v1"}
SFX = {"green": "", "blue": "_blue", "red": "_red", "yellow": "_yellow", "violet": "_violet"}
GREEN_LOOKS = ["w1_neon", "h1_neon", "hw_emerald", "green_x5_emerald", "green_x5_neon", "green_x3_emerald",
               "green_x1_emerald", "green_x3d1_emerald"]
LAMP = {"green": (0.4, 1, 0.6), "blue": (0.5, 0.7, 1), "red": (1, 0.35, 0.35), "yellow": (1, 0.85, 0.4),
        "violet": (0.75, 0.5, 1)}
GIF_FRAMES = 24
TURN_PER_FRAME = 4.8   # LanternFirstPerson turns the light 1.2 degrees a tick; a GIF frame is 4 ticks

os.makedirs(f"{OUT}/textures", exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def copy_tex(src):
    dst = f"{OUT}/textures/{os.path.basename(src)}"
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    return bpy.data.images.load(dst, check_existing=True)


def strip_material(strip):
    """The strip's current frame as solid light: its colour where opaque, over a dark core of its own darkest tone."""
    name = f"strip {strip}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    path = f"{ASSETS}/textures/block/construct_ripples_{strip}.png"
    img = copy_tex(path)
    w, h = img.size
    n = h // w
    px = np.array(img.pixels[:]).reshape(h, w, 4)[h - w:]   # the top frame (Blender rows run bottom up)
    solid = px[px[:, :, 3] > 0.8][:, :3]
    solid = solid[np.argsort(solid.sum(1))] if len(solid) else np.array([[0.015, 0.03, 0.02]])
    dark = solid[len(solid) // 10]   # already linear
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    uv = nt.nodes.new("ShaderNodeUVMap")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 1 / n, 1)
    nt.links.new(uv.outputs[0], mp.inputs[0])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    tex.extension = "REPEAT"
    nt.links.new(mp.outputs[0], tex.inputs[0])
    core = nt.nodes.new("ShaderNodeEmission")
    core.inputs["Color"].default_value = (float(dark[0]), float(dark[1]), float(dark[2]), 1)
    core.inputs["Strength"].default_value = 1.0
    lit = nt.nodes.new("ShaderNodeEmission")
    lit.inputs["Strength"].default_value = float(os.environ.get("LIGHT", "2.6"))
    nt.links.new(tex.outputs["Color"], lit.inputs["Color"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
    nt.links.new(core.outputs[0], mix.inputs[1])
    nt.links.new(lit.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    # Step through the strip's frames (one per GIF frame), top frame first.
    for f in range(GIF_FRAMES + 1):
        k = f % n
        mp.inputs["Location"].default_value = (0, (n - 1 - k) / n, 0)
        mp.inputs["Location"].keyframe_insert("default_value", frame=f)
    for fc in (nt.animation_data.action.fcurves if hasattr(nt.animation_data.action, "fcurves") else []):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    return m


def lathe(take, name, at, mat):
    """The take's light: each profile turned round the axis; u wraps once, v runs down the profile."""
    t = PROFILES["takes"][take]
    verts, faces, uvs = [], [], []
    for part in t["parts"]:
        seg, prof = part["segments"], part["profile"]
        rmax = max(r for _, r in prof)
        circ = 2 * math.pi * rmax
        s, vs = 0.0, [0.0]
        for (y0, r0), (y1, r1) in zip(prof, prof[1:]):
            s += math.hypot(y1 - y0, r1 - r0)
            vs.append(s / circ)
        keep = part.get("every", 1)
        for k in range(seg):
            if k % keep:
                continue
            a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            for j in range(len(prof) - 1):
                (y0, r0), (y1, r1) = prof[j], prof[j + 1]
                base = len(verts)
                for (a, y, r) in ((a0, y0, r0), (a1, y0, r0), (a1, y1, r1), (a0, y1, r1)):
                    verts.append((r * math.sin(a) * U, -r * math.cos(a) * U, y * U))
                faces.append([base, base + 3, base + 2, base + 1])
                u0, u1 = 1 - k / seg, 1 - (k + 1) / seg   # left to right seen from outside
                uvs.append([(u0, 1 - vs[j]), (u0, 1 - vs[j + 1]), (u1, 1 - vs[j + 1]), (u1, 1 - vs[j])])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly, quad in zip(me.polygons, uvs):
        for li, uv in zip(poly.loop_indices, quad):
            uvl.data[li].uv = uv
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = at
    scene.collection.objects.link(ob)
    for f in range(GIF_FRAMES + 1):
        ob.rotation_euler = (0, 0, math.radians(-TURN_PER_FRAME * f))
        ob.keyframe_insert("rotation_euler", frame=f)
    return ob


def plain_material(name, img, kind):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    mix = nt.nodes.new("ShaderNodeMixShader")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    fade = nt.nodes.new("ShaderNodeMath")
    fade.operation = "MULTIPLY"
    # The glass is thinned here so the wrapped light reads (GLASS_ALPHA; 1 = the lean take as shipped).
    fade.inputs[1].default_value = 1.0 if kind == "body" else float(os.environ.get("GLASS_ALPHA", "0.55"))
    nt.links.new(tex.outputs["Alpha"], fade.inputs[0])
    nt.links.new(fade.outputs[0], mix.inputs[0])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    if kind == "body":
        sh = nt.nodes.new("ShaderNodeBsdfPrincipled")
        sh.inputs["Roughness"].default_value = 0.45
        nt.links.new(tex.outputs["Color"], sh.inputs["Base Color"])
    else:
        sh = nt.nodes.new("ShaderNodeEmission")
        sh.inputs["Strength"].default_value = 1.6
        nt.links.new(tex.outputs["Color"], sh.inputs["Color"])
    nt.links.new(sh.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def bbmodel(path, mat, name, at, skip=()):
    """Every cube face of a bbmodel with its per-face UVs (Blockbench +Y up -> Blender +Z up)."""
    d = json.load(open(path))
    rw, rh = d["resolution"]["width"], d["resolution"]["height"]
    order = {"north": [(1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)], "south": [(0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)],
             "east": [(1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)], "west": [(0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)],
             "up": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)], "down": [(0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)]}
    verts, faces, uvs = [], [], []
    for e in d["elements"]:
        if any(e["name"].startswith(p) for p in skip):
            continue
        inf = e.get("inflate", 0)
        f = [v - inf for v in e["from"]]
        t = [v + inf for v in e["to"]]
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
                x, y, z = (t[0] if cx else f[0]) - org[0], (t[1] if cy else f[1]) - org[1], (t[2] if cz else f[2]) - org[2]
                rx, ry, rz = (math.radians(a) for a in rot)
                y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
                x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
                x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
                verts.append(((x + org[0]) * U, (z + org[2]) * U, (y + org[1]) * U))
                idx.append(len(verts) - 1)
            faces.append(idx)
            uvs.append([(u0 / rw, 1 - v0 / rh), (u1 / rw, 1 - v0 / rh), (u1 / rw, 1 - v1 / rh), (u0 / rw, 1 - v1 / rh)])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly, quad in zip(me.polygons, uvs):
        for li, uv in zip(poly.loop_indices, quad):
            uvl.data[li].uv = uv
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = at
    scene.collection.objects.link(ob)
    return ob


def lantern(take, corps, strip, at, label):
    sfx = SFX[corps]
    body = plain_material(f"body{sfx}", copy_tex(f"{ASSETS}/textures/entity/bb/nebula_lantern{sfx}.png"), "body")
    bbmodel(f"{ASSETS}/bbmodel/nebula_lantern.bbmodel", body, f"body {label}", at, ("glass", "light", "orb"))
    gm_name = f"glass{sfx}"
    gm = bpy.data.materials.get(gm_name) or plain_material(
        gm_name, copy_tex(f"{GLASS}/textures/entity/bb/nebula_glass_f0{sfx}.png"), "glass")
    bbmodel(f"{GLASS}/bbmodel/nebula_glass.bbmodel", gm, f"glass {label}", at)
    lathe(take, f"light {label}", at, strip_material(strip))
    lamp = bpy.data.lights.new(f"glow {label}", "POINT")
    lamp.energy = 3
    lamp.color = LAMP[corps]
    lo = bpy.data.objects.new(f"glow {label}", lamp)
    lo.location = (at[0], at[1], at[2] + 11.5 * U)
    scene.collection.objects.link(lo)


def camera(name, target, dist, height=0.75, lens=50):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.data.lens = lens
    cam.location = (target[0], target[1] - dist, target[2] + height)
    scene.collection.objects.link(cam)
    aim = bpy.data.objects.new(name + " aim", None)
    aim.location = target
    scene.collection.objects.link(aim)
    cam.constraints.new("TRACK_TO").target = aim
    return cam


# Row 1: the four takes in green (W1 neon). Then each take in every corps, then the green looks on L1,
# each row far to the side so no camera sees another row.
for i, take in enumerate(TAKES):
    lantern(take, "green", "w1_neon", (i * SPACING, 0, 0), f"{take} green")
    camera(f"Cam {take[:2]}", (i * SPACING, 0, 0.72), 2.6, 0.25)
camera("Cam takes", ((len(TAKES) - 1) * SPACING / 2, 0, 0.6), 7.5, 0.6, 40)
for r, take in enumerate(TAKES):
    x0 = 30 + r * 30
    for c, (corps, strip) in enumerate(CORPS_STRIP.items()):
        lantern(take, corps, strip, (x0 + c * SPACING, 0, 0), f"{take} {corps}")
    camera(f"Cam corps {take[:2]}", (x0 + (len(CORPS_STRIP) - 1) * SPACING / 2, 0, 0.6), 9.0, 0.6, 40)
x0 = 160
for c, strip in enumerate(GREEN_LOOKS):
    lantern(TAKES[0], "green", strip, (x0 + c * SPACING, 0, 0), f"look {strip}")
camera("Cam green looks", (x0 + (len(GREEN_LOOKS) - 1) * SPACING / 2, 0, 0.6), 14.0, 0.6, 40)

bpy.ops.mesh.primitive_plane_add(size=400, location=(90, 0, 0))
fm = bpy.data.materials.new("floor")
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.035, 0.04, 1)
bpy.context.object.data.materials.append(fm)
world = bpy.data.worlds.new("night")
world.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.005, 0.008, 1)
scene.world = world
moon = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN"))
moon.data.energy = 0.6
moon.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(moon)

scene.render.engine = "CYCLES"
scene.cycles.samples = int(os.environ.get("SAMPLES", "20"))
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x, scene.render.resolution_y = 960, 640
scene.frame_start, scene.frame_end = 0, GIF_FRAMES - 1
scene.render.fps = 5
if hasattr(scene, "compositing_node_group"):
    ng = bpy.data.node_groups.new("bloom", "CompositorNodeTree")
    scene.compositing_node_group = ng
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    out = ng.nodes.new("NodeGroupOutput")
else:
    scene.use_nodes = True
    ng = scene.node_tree
    for node in list(ng.nodes):
        ng.nodes.remove(node)
    out = ng.nodes.new("CompositorNodeComposite")
rl = ng.nodes.new("CompositorNodeRLayers")
gl = ng.nodes.new("CompositorNodeGlare")
gl.inputs["Type"].default_value = "Bloom"
gl.inputs["Threshold"].default_value = 0.55
gl.inputs["Strength"].default_value = 0.9
gl.inputs["Size"].default_value = 0.6
ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
ng.links.new(gl.outputs["Image"], out.inputs[0])
scene.camera = bpy.data.objects["Cam takes"]

bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/nebula_strip_light.blend")
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_mainfile()

if os.environ.get("LL_NO_RENDER") != "1":
    os.makedirs(f"{OUT}/renders/gif", exist_ok=True)
    shots = ([("Cam takes", "takes")] + [(f"Cam {t[:2]}", t) for t in TAKES]
             + [(f"Cam corps {t[:2]}", f"corps_{t}") for t in TAKES] + [("Cam green looks", "green_looks")])
    for cam, label in shots:
        scene.camera = bpy.data.objects[cam]
        scene.frame_set(3)
        scene.render.filepath = f"{OUT}/renders/{label}.png"
        bpy.ops.render.render(write_still=True)
    if os.environ.get("GIF") == "1":
        scene.camera = bpy.data.objects["Cam takes"]
        scene.render.resolution_x, scene.render.resolution_y = 720, 480
        scene.cycles.samples = 10
        for f in range(GIF_FRAMES):
            scene.frame_set(f)
            scene.render.filepath = f"{OUT}/renders/gif/takes_{f:02d}.png"
            bpy.ops.render.render(write_still=True)
    print("RENDER_DONE")
