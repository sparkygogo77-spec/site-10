"""Dread Runner kill takes K1-K4 in Blender (pass 420): the game's runner, keyed from the rig JSON's
"clips", plus a plain stand-in mob moved along each clip's "target" track.

    /opt/bl/venv/bin/python runner_kill_scene.py ASSETS RIG_WITH_CLIPS OUT
ASSETS is src/main/resources/assets/lanternring. Writes OUT/runner_kills.blend (textures relative,
in OUT/textures) and, unless LL_NO_RENDER=1, OUT/frames/<clip>/####.png from each take's side camera.

'target' is the victim's middle in model px (x right, y forward, z up), measured from where a
standing mob's middle would be (16 px up) at the runner's start position. After it turns null the
stand-in is let go: thrown (K2) it flies on with gravity and tumbles; otherwise it falls over.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(__file__))
import bb_import as bb  # noqa: E402
import runner_rig  # noqa: E402

ASSETS, RIG, OUT = sys.argv[-3:]
TAIL = 14          # frames after a clip ends, so the aftermath shows
MID = 16           # a standing mob's middle, model px
GRAVITY = 0.27     # model px per frame^2 (9.8 m/s^2 at 24 fps)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
os.makedirs(f"{OUT}/textures", exist_ok=True)
import json  # noqa: E402
rig = json.load(open(RIG))
clips = rig["clips"]
U = bb.U


def dummy(name):
    """A plain 2-block mob, tan cloth and grey skin, pivoting at its middle."""
    root = bpy.data.objects.new(name, None)
    scene.collection.objects.link(root)
    cloth = bpy.data.materials.new(name + " cloth")
    cloth.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.24, 0.14, 1)
    skin = bpy.data.materials.new(name + " skin")
    skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.45, 0.40, 1)
    # (size x, y, z), (centre x, y, z) in px, relative to the middle; the mob faces -Y (the runner)
    for part, size, at, mat in [("legs", (8, 4, 12), (0, 0, -10), cloth), ("body", (8, 4, 12), (0, 0, 2), cloth),
                                ("head", (8, 8, 8), (0, 0, 12), skin), ("arm_l", (4, 4, 12), (-6, 0, 2), skin),
                                ("arm_r", (4, 4, 12), (6, 0, 2), skin)]:
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.object
        ob.name = f"{name} {part}"
        ob.scale = [s * U for s in size]
        ob.location = [c * U for c in at]
        ob.data.materials.append(mat)
        ob.parent = root
    return root


def victim_track(clip):
    """Per frame: (x, y, z) px from the runner's start, lie angle (deg), tumble (deg)."""
    n = len(clip["frames"]) + TAIL
    out, last, vel, lie, tumble, thrown = [], None, (0, 0, 0), 0.0, 0.0, False
    for f in range(n):
        t = clip["target"][f] if f < len(clip["frames"]) else None
        if t is not None:
            p = (t[0], t[1], MID + t[2])
            if last is not None:
                vel = tuple(p[i] - last[i] for i in range(3))
            lie = min(1.0, max(0.0, (-t[2] - 4) / 8.0)) * 90
            last = p
        else:
            if last is None:
                continue
            if not thrown and math.hypot(*vel) > 1.5:
                thrown = True
            if thrown and last[2] > 4:
                vel = (vel[0] * 0.98, vel[1] * 0.98, vel[2] - GRAVITY)
                p = (last[0] + vel[0], last[1] + vel[1], max(4.0, last[2] + vel[2]))
                tumble += 24
            else:
                p = (last[0], last[1], max(4.0, last[2] - 1.5))
                tumble = round(tumble / 360) * 360 if thrown else tumble
            lie = min(90.0, lie + 11)
            last = p
        out.append((f, p, lie, tumble))
    return out


TAKES = list(clips)
for i, name in enumerate(TAKES):
    clip = clips[name]
    x0, y0 = i * 30.0, -i * 60.0
    label = name.split("_")[1].upper()
    root, objs, _ = runner_rig.build(ASSETS, RIG, f"{label} runner", (x0, y0, 0), f"{OUT}/textures")
    vic = dummy(f"{label} mob")
    n = len(clip["frames"])
    for f in range(n + TAIL):
        k = min(f, n - 1)
        runner_rig.pose(objs, clip["frames"][k], clip["root"][k])
        runner_rig.key(objs, f + 1)
    for f, p, lie, tumble in victim_track(clip):
        vic.location = (x0 - p[0] * U, y0 + p[1] * U, p[2] * U)
        vic.rotation_euler = (math.radians(-lie - tumble), 0, 0)
        vic.keyframe_insert("location", frame=f + 1)
        vic.keyframe_insert("rotation_euler", frame=f + 1)
    bb.camera(f"Cam {label} side", (x0 + 6.5, y0 + 1.6, 1.4), (x0, y0 + 1.4, 0.9), 30)
    bb.camera(f"Cam {label} front", (x0 - 3.5, y0 + 5.5, 1.6), (x0, y0 + 1.0, 0.9), 30)
    scene[f"{label}_hit"] = clip["hit"] + 1

bpy.ops.mesh.primitive_plane_add(size=600, location=(45, -90, 0))
fm = bpy.data.materials.new("ground")
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.07, 0.04, 1)
bpy.context.object.data.materials.append(fm)
sun = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN"))
sun.data.energy = 1.6
sun.rotation_euler = (math.radians(50), 0, math.radians(60))
scene.collection.objects.link(sun)
bb.night(scene, 0.7)
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, max(len(c["frames"]) for c in clips.values()) + TAIL
scene.cycles.samples = int(os.environ.get("SAMPLES", "12"))
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 560, 350
scene.camera = bpy.data.objects["Cam K1 side"]

bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/runner_kills.blend")
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_mainfile()

if os.environ.get("LL_NO_RENDER") != "1":
    only = os.environ.get("FRAMES")  # e.g. "1,18" for a quick check
    for i, name in enumerate(TAKES):
        label = name.split("_")[1].upper()
        if os.environ.get("ONLY") and os.environ["ONLY"] != label:
            continue
        scene.camera = bpy.data.objects[f"Cam {label} side"]
        frames = [int(v) for v in only.split(",")] if only else range(1, len(clips[name]["frames"]) + TAIL + 1)
        os.makedirs(f"{OUT}/frames/{name}", exist_ok=True)
        for f in frames:
            scene.frame_set(f)
            scene.render.filepath = f"{OUT}/frames/{name}/{f:04d}.png"
            bpy.ops.render.render(write_still=True)
    print("RENDER_DONE")
