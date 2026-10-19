"""Pictures for the decision manager: one sheet per pass (a frame of each take's clip, labelled) for SendUserFile.

    python decision_stills.py DECISIONS_JSON SITE_DIR OUT_DIR [--blender PATH] [--only 606,864]

For every "rate" / "improve" card (and questions that name a pass) it takes each listed take's third-person clip
(first-person if there's no 3p) from SITE_DIR\\media, grabs the frame at the take's poseFrac with Blender's video
reader (no ffmpeg on J's PC), and lays them out in OUT_DIR\\<pass>.jpg with Pillow. Cached: a sheet is only redrawn
when a clip is newer than it. Prints one line per sheet.
"""
import json, os, subprocess, sys, tempfile

if "bpy" in sys.modules or os.path.basename(sys.executable).lower().startswith("blender"):
    # ---- inside Blender: argv after "--" is a job file [[clip, frac, png], ...]
    import bpy
    jobs = json.load(open(sys.argv[sys.argv.index("--") + 1]))
    for clip, frac, png in jobs:
        sc = bpy.context.scene
        sc.sequence_editor_create()
        for old in list(sc.sequence_editor.strips):
            sc.sequence_editor.strips.remove(old)
        strip = sc.sequence_editor.strips.new_movie("m", clip, 1, 1)
        el = strip.elements[0]
        # the scene runs at the clip's own rate (the site's clips are 5-10 fps) so the frame number lands on the pose
        sc.render.fps, sc.render.fps_base = max(1, round(strip.fps)), 1
        sc.render.resolution_x, sc.render.resolution_y = el.orig_width or 640, el.orig_height or 360
        sc.render.resolution_percentage = 100
        n = strip.duration
        sc.frame_start, sc.frame_end = 1, n
        sc.frame_set(max(1, min(n, round(frac * n))))
        sc.render.use_sequencer = True
        sc.render.image_settings.file_format = "PNG"
        sc.render.filepath = png
        bpy.ops.render.render(write_still=True)
    sys.exit(0)

from PIL import Image, ImageDraw, ImageFont

ARGS = [a for a in sys.argv[1:]]
def opt(name, default=None):
    if name in ARGS:
        i = ARGS.index(name); v = ARGS[i + 1]; del ARGS[i:i + 2]; return v
    return default
BLENDER = opt("--blender", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
ONLY = set((opt("--only", "") or "").split(",")) - {""}
DEC, SITE, OUT = ARGS[:3]   # clip paths must be absolute: Blender reads a relative one as a black frame
os.makedirs(OUT, exist_ok=True)

cards = json.load(open(DEC, encoding="utf-8"))["cards"]
site = {p["key"]: p for p in json.load(open(os.path.join(SITE, "data", "site.json"), encoding="utf-8"))["passes"]}
want = {}
for c in cards:
    k = c.get("pass")
    if k in site and (not ONLY or k in ONLY):
        want.setdefault(k, [])
        for code in c.get("takes") or [t["code"] for t in site[k]["takes"]]:
            if code not in want[k]:
                want[k].append(code)

jobs, sheets = [], []
tmp = os.path.join(tempfile.gettempdir(), "lr_stills")
os.makedirs(tmp, exist_ok=True)
for k, codes in want.items():
    takes = [t for t in site[k]["takes"] if t["code"] in codes and (t.get("clip3p") or t.get("clipfp"))][:12]
    # first-person passes (ring glow, held tools) read only in the first-person clip; everything else in third person
    fp = "first person" in site[k]["title"].lower() or "first-person" in site[k]["title"].lower()
    pick = lambda t: (t.get("clipfp") or t.get("clip3p")) if fp else (t.get("clip3p") or t.get("clipfp"))
    clips = [(t, os.path.join(os.path.abspath(SITE), *pick(t).split("/"))) for t in takes]
    clips = [(t, c) for t, c in clips if os.path.exists(c)]
    if not clips:
        continue
    sheet = os.path.join(OUT, f"{k}.jpg")
    if os.path.exists(sheet) and os.path.getmtime(sheet) > max(os.path.getmtime(c) for _, c in clips):
        print(f"  {k}: cached {sheet}")
        continue
    frames = []
    for t, c in clips:
        png = os.path.join(tmp, f"{k}_{t['code']}.png")
        jobs.append([c, t.get("poseFrac") or 0.6, png])
        frames.append((t, png))
    sheets.append((k, sheet, frames))

if jobs:
    job = os.path.join(tmp, "jobs.json")
    json.dump(jobs, open(job, "w"))
    subprocess.run([BLENDER, "-b", "--factory-startup", "--python", os.path.abspath(__file__), "--", job],
                   capture_output=True, text=True)

try:
    font = ImageFont.truetype("segoeuib.ttf", 26)
except OSError:
    font = ImageFont.load_default()
for k, sheet, frames in sheets:
    ims = [(t, Image.open(p).convert("RGB")) for t, p in frames if os.path.exists(p)]
    if not ims:
        print(f"  {k}: no frames (Blender couldn't read the clips)")
        continue
    w, h = ims[0][1].size
    cols = 1 if len(ims) == 1 else 2 if len(ims) <= 4 else 3
    rows = -(-len(ims) // cols)
    pad = 6
    out = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad) + pad), (18, 20, 19))
    d = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(ims):
        x, y = pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad)
        out.paste(im.resize((w, h)), (x, y))
        d.rectangle([x, y, x + 14 + d.textlength(t["code"], font=font), y + 36], fill=(0, 0, 0))
        d.text((x + 7, y + 4), t["code"], font=font, fill=(120, 240, 170))
    scale = min(1.0, 1800 / out.width)
    if scale < 1:
        out = out.resize((round(out.width * scale), round(out.height * scale)))
    out.save(sheet, quality=85)
    print(f"  {k}: {len(ims)} takes -> {sheet}")
