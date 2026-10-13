# Pass 36: save the lantern models (J: "most efficiently and optimally").
#  1. Purge unused data (old meshes and materials left behind by earlier passes).
#  2. Save the whole scene, compressed, as LanternLive\lantern_live.blend. That becomes the file Blender
#     works on, so the watcher also falls back to this folder.
#  3. Write lantern_models.blend: only the pixel models (every mesh with the "col" colour attribute)
#     with their materials and the "Lantern Controls" driver object, compressed. It is small, and other
#     scenes can File > Append or Link from it.
# Results and sizes go to renders/save_report.txt.
import os
import bpy

scene = bpy.context.scene
report = []

before = len(bpy.data.meshes), len(bpy.data.materials), len(bpy.data.images)
try:
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
except Exception as e:
    report.append(f"purge skipped: {e}")
after = len(bpy.data.meshes), len(bpy.data.materials), len(bpy.data.images)
report.append(f"purged meshes/materials/images: {before} -> {after}")

models = [o for o in bpy.data.objects if o.type == "MESH" and o.data and "col" in o.data.color_attributes]
report.append("pixel models: " + ", ".join(sorted(o.name for o in models)))
ids = set(models)
for o in models:
    ids.add(o.data)
    ids.update(m for m in o.data.materials if m)
ctl = bpy.data.objects.get("Lantern Controls")
if ctl:
    ids.add(ctl)

lib = os.path.join(FOLDER, "lantern_models.blend")
bpy.data.libraries.write(lib, ids, fake_user=True, compress=True)
report.append(f"lantern_models.blend: {os.path.getsize(lib):,} bytes")

main = os.path.join(FOLDER, "lantern_live.blend")
bpy.ops.wm.save_as_mainfile(filepath=main, compress=True)
report.append(f"lantern_live.blend (whole scene, compressed): {os.path.getsize(main):,} bytes")

os.makedirs(os.path.join(FOLDER, "renders"), exist_ok=True)
with open(os.path.join(FOLDER, "renders", "save_report.txt"), "w") as fh:
    fh.write("\n".join(report) + "\n")
