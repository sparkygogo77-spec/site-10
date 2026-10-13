# Pass 36b: smaller lantern files. Every pixel face had its own four corners; neighbouring faces share
# corners, so merging them loses nothing (colours are stored per face corner) and cuts the vertex count
# several times over. Then both files are saved again, compressed. Sizes go to renders/save_report.txt.
import os
import bmesh
import bpy

lines = []
for o in bpy.data.objects:
    if o.type != "MESH" or not o.data or "col" not in o.data.color_attributes:
        continue
    me = o.data
    before = len(me.vertices)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(me)
    bm.free()
    me.update()
    lines.append(f"{o.name}: {before:,} -> {len(me.vertices):,} vertices")

models = [o for o in bpy.data.objects if o.type == "MESH" and o.data and "col" in o.data.color_attributes
          and not o.name.startswith("Runner")]
ids = set(models)
for o in models:
    ids.add(o.data)
    ids.update(m for m in o.data.materials if m)
ctl = bpy.data.objects.get("Lantern Controls")
if ctl:
    ids.add(ctl)
lib = os.path.join(FOLDER, "lantern_models.blend")
bpy.data.libraries.write(lib, ids, fake_user=True, compress=True)
lines.append(f"lantern_models.blend: {os.path.getsize(lib):,} bytes")
main = os.path.join(FOLDER, "lantern_live.blend")
bpy.ops.wm.save_as_mainfile(filepath=main, compress=True)
lines.append(f"lantern_live.blend: {os.path.getsize(main):,} bytes")
with open(os.path.join(FOLDER, "renders", "save_report.txt"), "a") as fh:
    fh.write("\n-- 36b merge --\n" + "\n".join(lines) + "\n")
