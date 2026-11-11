"""(Older check; prefer check_pass.py: builds once, EEVEE like the site render, denoised, few key frames.)
Render a strip of frames from one camera for a contact sheet or GIF.

    python3 tools/blender_pipeline/render_frames.py UPDATE.py LLDIR "Cam X" FIRST LAST STEP OUTDIR
"""
import os, sys
import bpy
import numpy as np

src, folder, camname, f0, f1, step, out = sys.argv[1], sys.argv[2], sys.argv[3], *map(int, sys.argv[4:7]), sys.argv[7]
os.environ["LL_NO_RENDER"] = "1"
exec(compile(open(src).read(), src, "exec"), {"bpy": bpy, "np": np, "FOLDER": folder, "__name__": "__ll__"})
sc = max(bpy.data.scenes, key=lambda s: len(s.objects))
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.device = "CPU"; sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = 480, 270
sc.camera = bpy.data.objects[camname]
os.makedirs(out, exist_ok=True)
for f in range(f0, f1 + 1, step):
    sc.frame_set(f); sc.render.filepath = os.path.join(out, "f%03d.png" % f)
    bpy.ops.render.render(write_still=True, scene=sc.name)
