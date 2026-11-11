"""One-process self-check for a pass: build once, render a few key frames from every camera.

    python3 tools/blender_pipeline/check_pass.py UPDATE.py LLDIR "Cam A,Cam B" [FRAMES]

FRAMES is a comma list (default: 5 frames spread over the scene's frame range). Needs LIBGL_ALWAYS_SOFTWARE=1 and libegl1 in the container. Env: ENGINE (EEVEE default, matching
lantern_review.py; CYCLES if EEVEE fails headless), SAMPLES (default 8), W/H (default 800x450), OUT (default LLDIR/renders).
Stills land in OUT/check_<camera>_f<frame>.png. Denoising is on, so 8 samples stays readable.
"""
import os, sys, time
import bpy
import numpy as np

src, folder = sys.argv[1], sys.argv[2]
cams = [c for c in sys.argv[3].split(",") if c]
os.environ["LL_NO_RENDER"] = "1"
t = time.time()
exec(compile(open(src).read(), src, "exec"), {"bpy": bpy, "np": np, "FOLDER": folder, "__name__": "__ll__"})
print("built in %.1fs" % (time.time() - t), flush=True)
sc = max(bpy.data.scenes, key=lambda s: len(s.objects))
f0, f1 = sc.frame_start, sc.frame_end
frames = [int(f) for f in sys.argv[4].split(",")] if len(sys.argv) > 4 else sorted({round(f0 + (f1 - f0) * i / 4) for i in range(5)})
samples = int(os.environ.get("SAMPLES", 8))

want = os.environ.get("ENGINE", "EEVEE").upper()
if want == "CYCLES":
    sc.render.engine = "CYCLES"; sc.cycles.samples = samples; sc.cycles.device = "CPU"
    sc.cycles.use_denoising = True
else:
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng; break
        except TypeError:
            continue
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass
sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get("W", 800)), int(os.environ.get("H", 450))
sc.render.resolution_percentage = 100
out = os.environ.get("OUT", os.path.join(folder, "renders")); os.makedirs(out, exist_ok=True)
for cam in cams:
    sc.camera = bpy.data.objects[cam]
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, "check_%s_f%03d.png" % (cam.replace(" ", "_"), f))
        t = time.time(); bpy.ops.render.render(write_still=True, scene=sc.name)
        print(cam, f, "%.1fs" % (time.time() - t), flush=True)
