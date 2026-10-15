"""python3 export_glb.py UPDATE.py LLDIR OUTDIR INPLACE(xy|xyz) 'TAG:f0:f1' ..."""
import os, sys
import bpy
import numpy as np
from mathutils import Vector
src, folder, out, inplace = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
import json, struct
def merge(path, tag):
    b = open(path, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); rest = b[20 + n:]
    ch, sm = [], []
    for a in j.get("animations", []):
        off = len(sm); sm += a["samplers"]
        for c in a["channels"]: c = dict(c); c["sampler"] += off; ch.append(c)
    j["animations"] = [{"name": tag, "channels": ch, "samplers": sm}]
    bn = struct.unpack("<I", rest[:4])[0]; bin_ = rest[8:8 + bn]
    for c in ch:  # rest pose = first keyframe, so bounds and framing match the animation
        acc = j["accessors"][sm[c["sampler"]]["output"]]; bv = j["bufferViews"][acc["bufferView"]]
        k = 4 if c["target"]["path"] == "rotation" else 3
        o = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        j["nodes"][c["target"]["node"]][c["target"]["path"]] = list(struct.unpack("<%df" % k, bin_[o:o + 4 * k]))
    js = json.dumps(j, separators=(",", ":")).encode(); js += b" " * (-len(js) % 4)
    body = struct.pack("<II", len(js), 0x4E4F534A) + js + rest
    open(path, "wb").write(b[:8] + struct.pack("<I", 12 + len(body)) + body)
os.environ["LL_NO_RENDER"] = "1"
exec(compile(open(src).read(), src, "exec"), {"bpy": bpy, "np": np, "FOLDER": folder, "__name__": "__ll__"})
sc = max(bpy.data.scenes, key=lambda s: len(s.objects))
bpy.context.window_manager.windows[0].scene = sc if bpy.context.window_manager.windows else None
os.makedirs(out, exist_ok=True)
for o in list(bpy.data.objects):
    if o.name == "Cube": bpy.data.objects.remove(o)
for spec in sys.argv[5:]:
    tag, f0, f1 = spec.rsplit(":", 2); f0, f1 = int(f0), int(f1)
    parts = [o for o in sc.objects if o.name.startswith(f"KL {tag} ")]
    roots = [o for o in parts if o.parent is None]
    body = next(o for o in roots if o.name.endswith(" body"))
    root = bpy.data.objects.new(f"root {tag}", None); sc.collection.objects.link(root)
    sc.frame_set(f0); base = body.matrix_world.translation.copy()
    for f in range(f0, f1 + 1):
        sc.frame_set(f); p = body.matrix_world.translation
        off = Vector((p.x, p.y, p.z if inplace == "xyz" else base.z))
        root.location = -off; root.keyframe_insert("location", frame=f)
    for o in roots:
        o.parent = root  # matrix_parent_inverse stays identity: world = root * local
    for o in sc.objects: o.select_set(False)
    root.select_set(True)
    for o in parts: o.select_set(True)
    sc.frame_start, sc.frame_end = f0, f1; sc.frame_set(f0)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, f"{tag}.glb"), use_selection=True, export_animations=True,
                              export_animation_mode="SCENE", export_frame_range=True, export_force_sampling=True,
                              export_yup=True, export_apply=False, export_cameras=False, export_lights=False)
    for o in roots: o.parent = None
    merge(os.path.join(out, f"{tag}.glb"), tag)
    print("GLB", tag, os.path.getsize(os.path.join(out, f"{tag}.glb")), flush=True)
