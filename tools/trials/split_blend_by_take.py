# Split a big pass .blend into smaller ones for SendUserFile (30 MB cap): keeps only the objects whose top-level
# parent's name (or camera name after "Cam ") starts with one of the given take-code prefixes.
# blender -b <pass>.blend --python tools/trials/split_blend_by_take.py -- W2a,W2d <out>.blend
import bpy, sys
keep = sys.argv[sys.argv.index("--") + 1].split(",")
out = sys.argv[sys.argv.index("--") + 2]
def ok(name):
    n = name[4:] if name.startswith("Cam ") else name
    return any(n.startswith(k) for k in keep)
for ob in list(bpy.data.objects):
    root = ob
    while root.parent:
        root = root.parent
    if not ok(root.name):
        bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
sc = bpy.context.scene
cams = [o for o in sc.objects if o.type == "CAMERA"]
sc.camera = sorted(cams, key=lambda o: o.name)[0]
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("kept", len(sc.objects), "objects")
