"""Pack a built .blend for J: pack all images, keep one scene, set its start camera, save compressed.

    python3 tools/blender_pipeline/pack_blend.py IN.blend OUT.blend "Scene Name" "Cam X"

Then deliver OUT.blend into C:\\Users\\Josh\\Documents\\LanternLive\\ with the device bridge (device_commit_files,
stagedPath under /mnt/user-data/outputs/) when the session is linked to J's computer.
"""
import os, sys
import bpy

src, dst, scene_name, cam = sys.argv[1:5]
bpy.ops.wm.open_mainfile(filepath=src)
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("pack:", e)
sc = bpy.data.scenes.get(scene_name)
for s in list(bpy.data.scenes):
    if s != sc:
        bpy.data.scenes.remove(s)
sc.camera = bpy.data.objects.get(cam) or sc.camera
bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True)
print("saved", os.path.getsize(dst), "bytes; unpacked:", [i.name for i in bpy.data.images if not i.packed_file and i.source == "FILE"])
