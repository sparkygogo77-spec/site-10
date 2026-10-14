"""Build a Lantern Live pass headless and (optionally) render spot checks.

    pip install bpy --break-system-packages          # once per container (bpy 5.2 wheel)
    python3 tools/blender_pipeline/build_pass.py docs/blender/blender_updates/NNN_name.update.py LLDIR ["Cam A,Cam B"]

LLDIR is a local copy of J's LanternLive folder (the scripts read assets such as LLDIR/kl_assets/*.glb and write
LLDIR/<name>.blend and LLDIR/<name>_poses.json). Env: FRAME (default 60) and SAMPLES (default 12) for the check renders,
which land in LLDIR/renders/test_<camera>.png at 800x450 in Cycles (headless EEVEE can time out).
"""
import os, sys, time
import bpy
import numpy as np

src, folder = sys.argv[1], sys.argv[2]
cams = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else []
os.environ["LL_NO_RENDER"] = "1"
t = time.time()
exec(compile(open(src).read(), src, "exec"), {"bpy": bpy, "np": np, "FOLDER": folder, "__name__": "__ll__"})
print("built in %.1fs" % (time.time() - t))
sc = max(bpy.data.scenes, key=lambda s: len(s.objects))
sc.render.engine = "CYCLES"; sc.cycles.samples = int(os.environ.get("SAMPLES", "12")); sc.cycles.device = "CPU"
sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = 800, 450
for c in cams:
    sc.camera = bpy.data.objects[c]; sc.frame_set(int(os.environ.get("FRAME", "60")))
    sc.render.filepath = os.path.join(folder, "renders", "test_" + c.replace(" ", "_") + ".png")
    t = time.time(); bpy.ops.render.render(write_still=True, scene=sc.name); print(c, "%.1fs" % (time.time() - t))
