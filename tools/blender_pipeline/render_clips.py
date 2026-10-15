"""python3 render_clips.py UPDATE.py LLDIR OUTDIR STEP 'Cam A:f0:f1' 'Cam B:f0:f1' ..."""
import os, sys, time
import bpy
import numpy as np
src, folder, out, step = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
specs = sys.argv[5:]
os.environ["LL_NO_RENDER"] = "1"
exec(compile(open(src).read(), src, "exec"), {"bpy": bpy, "np": np, "FOLDER": folder, "__name__": "__ll__"})
sc = max(bpy.data.scenes, key=lambda s: len(s.objects))
sc.render.engine = "CYCLES"; sc.cycles.samples = int(os.environ.get("SAMPLES", 8)); sc.cycles.device = "CPU"
sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get("W", 640)), int(os.environ.get("H", 360))
for spec in specs:
    cam, f0, f1 = spec.rsplit(":", 2)
    sc.camera = bpy.data.objects[cam]
    d = os.path.join(out, cam.replace(" ", "_")); os.makedirs(d, exist_ok=True)
    t = time.time()
    for i, f in enumerate(range(int(f0), int(f1) + 1, step)):
        p = os.path.join(d, "f%03d.png" % i)
        if os.path.exists(p): continue
        sc.frame_set(f); sc.render.filepath = p
        bpy.ops.render.render(write_still=True, scene=sc.name)
    print("DONE", cam, round(time.time() - t, 1), flush=True)
