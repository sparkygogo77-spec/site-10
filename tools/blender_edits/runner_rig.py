"""Builds the game's Dread Runner in Blender from its part bbmodels and rig JSON, and poses it.

Rig angles are Blender XYZ Euler degrees in the generator's frame (x right, y forward, z up). The
runner faces +Y here, so generator x is Blender -X: a pose (ax, ay, az) is Blender (ax, -ay, -az).
"""
import json
import math
import os
import shutil

import bpy

import bb_import as bb

PARTS = ["torso", "head", "arm_l", "fore_l", "arm_r", "fore_r", "thigh_l", "shin_l", "thigh_r", "shin_r"]


def bl(v):
    """Blockbench px (x, y up, z) -> Blender metres (x, z, y)."""
    return (v[0] * bb.U, v[2] * bb.U, v[1] * bb.U)


def build(assets, rig_path, name, at, tex_dir, scale=1.0):
    rig = json.load(open(rig_path))
    root = bpy.data.objects.new(f"{name} root", None)
    root.location = at
    root.scale = (scale, scale, scale)
    bpy.context.scene.collection.objects.link(root)
    objs = {}
    for i, p in enumerate(rig["parts"]):
        part = p["name"]
        src = f"{assets}/textures/entity/bb/dread_runner_{part}.png"
        dst = f"{tex_dir}/dread_runner_{part}.png"
        if not os.path.exists(dst):
            shutil.copy(src, dst)
        img = bpy.data.images.load(dst, check_existing=True)
        mats = [bb.material(f"runner {part}", img, "solid"), bb.material(f"runner {part} glow", img, "glow", 2.5)]
        ob = bb.build(f"{assets}/bbmodel/dread_runner_{part}.bbmodel", mats, f"{name} {part}", (0, 0, 0),
                      kind_of=lambda n: 1 if n.startswith("glow") else 0)
        ob.rotation_mode = "XYZ"
        parent = rig["parts"][p["parent"]] if p["parent"] >= 0 else None
        piv = p["pivot_bb"]
        if parent:
            pp = parent["pivot_bb"]
            ob.parent = objs[parent["name"]]
            ob.location = bl([piv[k] - pp[k] for k in range(3)])
        else:
            ob.parent = root
            ob.location = bl(piv)
        ob["pivot"] = ob.location[:]
        objs[part] = ob
    return root, objs, rig


def pose(objs, angles, root_offset=(0, 0, 0)):
    """angles: part -> [ax, ay, az] generator degrees. root_offset: model px (x right, y fwd, z up)."""
    for part, ob in objs.items():
        ax, ay, az = angles.get(part, [0, 0, 0])
        ob.rotation_euler = (math.radians(ax), math.radians(-ay), math.radians(-az))
    torso = objs["torso"]
    base = torso["pivot"]
    torso.location = (base[0] - root_offset[0] * bb.U, base[1] + root_offset[1] * bb.U, base[2] + root_offset[2] * bb.U)


def key(objs, frame):
    for ob in objs.values():
        ob.keyframe_insert("rotation_euler", frame=frame)
    objs["torso"].keyframe_insert("location", frame=frame)
