"""Lantern Review: render Blender takes on J's PC and publish them to the review site.

Run with Blender (uses the graphics card through EEVEE, about 20x faster than the cloud renders):

    blender -b --python lantern_review.py -- 518 803            # these passes
    blender -b --python lantern_review.py -- --all              # every spec not yet rendered
    blender -b --python lantern_review.py -- 518 --force        # render again even if the clips exist
    blender -b --python lantern_review.py -- 518 --no-push      # render only, don't git push

Or paste it into Blender's Text Editor, set ARGS below, and press Run Script.

Folders (on J's PC):
    LANTERN_LIVE  C:\\Users\\Josh\\Documents\\LanternLive          the packed .blend files (area folders)
    SITE          LANTERN_LIVE\\review-site                       a git clone of branch `review-site`
    REPO          LANTERN_LIVE\\site-10 (optional)                a clone of the main repo, for update scripts

What it reads: one review spec per pass, `review.json`, from
    SITE\\specs\\<key>.json  (the Blender chats write these; see tools/review_site/README.md)

What it writes, in SITE:
    media/<key>/<take>-3p.mp4   third-person clip      media/<key>/<take>-fp.mp4   first-person (eye camera)
    media/<key>/<take>.jpg      still (static takes)   media/<key>/<take>.gltf.json  3D model, player held in place
    data/site.json              the page's list of passes and takes (rebuilt by tools/gen_site.py)
then `git add / commit / push` on branch review-site; Vercel redeploys https://lantern-review-j.vercel.app.
"""
import base64, json, math, os, re, struct, subprocess, sys, time, traceback

import bpy

ARGS = []          # when run from the Text Editor: e.g. ["518"] or ["--all"]

LANTERN_LIVE = os.environ.get("LANTERN_LIVE", r"C:\Users\Josh\Documents\LanternLive")
SITE = os.environ.get("LANTERN_SITE", os.path.join(LANTERN_LIVE, "review-site"))
REPO = os.environ.get("LANTERN_REPO", os.path.join(LANTERN_LIVE, "site-10"))
BUILD = os.path.join(LANTERN_LIVE, "_review_build")   # update scripts save their .blend here, not in the root
RES = (640, 360)
TICKS = 20         # game ticks a second = one frame per tick


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ARGS)
    flags = {x for x in a if x.startswith("--")}
    return [x for x in a if not x.startswith("--")], flags


def slug(c):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", c)


# ---------------------------------------------------------------- scene loading
def seed_assets():
    """Update scripts read FOLDER/kl_assets (tool models, ring voxels); copy any missing ones from the site branch."""
    import shutil
    src, dst = os.path.join(SITE, "assets", "kl_assets"), os.path.join(BUILD, "kl_assets")
    os.makedirs(dst, exist_ok=True)
    live = os.path.join(LANTERN_LIVE, "kl_assets")
    if os.path.isdir(live):
        for f in os.listdir(live):
            if not os.path.exists(os.path.join(dst, f)):
                shutil.copy(os.path.join(live, f), dst)
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src):
            if not os.path.exists(os.path.join(dst, f)):
                shutil.copy(os.path.join(src, f), dst)


def load_pass(spec):
    """Open the pass's packed .blend; if there isn't one, build it by running its update script."""
    blend = spec.get("blend")
    if blend:
        p = blend if os.path.isabs(blend) else os.path.join(LANTERN_LIVE, blend)
        if os.path.exists(p):
            bpy.ops.wm.open_mainfile(filepath=p)
            return max(bpy.data.scenes, key=lambda s: len(s.objects))
    script = spec.get("script")
    if script:
        seed_assets()
        for d in (os.path.join(SITE, "scripts"), os.path.join(REPO, "docs", "blender", "blender_updates"), LANTERN_LIVE):
            p = os.path.join(d, os.path.basename(script))
            if os.path.exists(p):
                bpy.ops.wm.read_homefile(use_empty=True)
                os.environ["LL_NO_RENDER"] = "1"
                import numpy as np
                cwd = os.getcwd(); os.chdir(os.path.dirname(p))
                try:
                    exec(compile(open(p, encoding="utf-8").read(), p, "exec"),
                         {"bpy": bpy, "np": np, "FOLDER": BUILD, "__name__": "__ll__", "__file__": p})
                finally:
                    os.chdir(cwd)
                return max(bpy.data.scenes, key=lambda s: len(s.objects))
    raise FileNotFoundError(f"pass {spec['key']}: no blend ({blend}) and no update script ({script}) found")


def setup(sc):
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng; break
        except TypeError:
            continue
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.fps = TICKS
    try:
        sc.eevee.taa_render_samples = 16
    except Exception:
        pass


# ---------------------------------------------------------------- rendering
def render_clip(sc, cam, f0, f1, step, out):
    if cam not in bpy.data.objects:
        print("  missing camera:", cam); return False
    sc.camera = bpy.data.objects[cam]
    sc.frame_start, sc.frame_end, sc.frame_step = f0, f1, step
    sc.render.fps = max(1, round(TICKS / step))
    im = sc.render.image_settings
    if hasattr(im, "media_type"):          # Blender 5: video is a media type, then FFMPEG
        im.media_type = "VIDEO"
    im.file_format = "FFMPEG"
    ff = sc.render.ffmpeg
    ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "MEDIUM"; ff.ffmpeg_preset = "GOOD"
    ff.audio_codec = "NONE"
    sc.render.filepath = out
    bpy.ops.render.render(animation=True, scene=sc.name)
    # Blender appends the frame range to the name; move it to the exact path
    d, base = os.path.split(out)
    for f in os.listdir(d):
        if f.startswith(os.path.splitext(base)[0]) and f.endswith(".mp4") and f != base:
            os.replace(os.path.join(d, f), out)
    return os.path.exists(out)


def render_still(sc, cam, frame, out):
    if cam not in bpy.data.objects:
        print("  missing camera:", cam); return False
    sc.camera = bpy.data.objects[cam]
    sc.frame_set(frame)
    im = sc.render.image_settings
    if hasattr(im, "media_type"):
        im.media_type = "IMAGE"
    im.file_format = "JPEG"; im.quality = 88
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True, scene=sc.name)
    return True


def fp_cam(sc, prefix):
    """Minecraft-style eye camera on the player's head: 70 deg vertical field of view."""
    head = bpy.data.objects.get(f"{prefix} head")
    if head is None:
        return None
    name = f"FPEYE {prefix}"
    if name in bpy.data.objects:
        return name
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.sensor_fit = "VERTICAL"; c.data.angle_y = math.radians(70); c.data.clip_start = 0.05
    c.parent = head; c.matrix_parent_inverse.identity()
    c.location = (0.0, -0.27, 0.27); c.rotation_euler = (math.radians(90), 0, math.radians(180))
    return name


def hide_body_for_fp(sc, prefix, hide):
    """In first person Minecraft draws no head or body; keep the arms (and what they hold)."""
    for o in sc.objects:
        if o.name.startswith(prefix + " ") and "arm" not in o.name and o.type == "MESH":
            o.visible_camera = not hide


# ---------------------------------------------------------------- 3D export
def gltf_json(glb_path, out, tag):
    b = open(glb_path, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n])
    rest = b[20 + n:]; bn = struct.unpack("<I", rest[:4])[0]; bin_ = rest[8:8 + bn]
    ch, sm = [], []
    for a in j.get("animations", []):
        off = len(sm); sm += a["samplers"]
        for c in a["channels"]:
            c = dict(c); c["sampler"] += off; ch.append(c)
    if ch:   # one animation for the viewer; rest pose = first keyframe so the framing matches
        j["animations"] = [{"name": tag, "channels": ch, "samplers": sm}]
        for c in ch:
            acc = j["accessors"][sm[c["sampler"]]["output"]]; bv = j["bufferViews"][acc["bufferView"]]
            k = 4 if c["target"]["path"] == "rotation" else 3
            o = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            j["nodes"][c["target"]["node"]][c["target"]["path"]] = list(struct.unpack("<%df" % k, bin_[o:o + 4 * k]))
    for m in j.get("materials", []):
        if "ring" in m.get("name", "").lower():
            m.setdefault("pbrMetallicRoughness", {})["baseColorFactor"] = [0.05, 0.75, 0.3, 1]
            m["emissiveFactor"] = [0.1, 1.0, 0.4]
            m.setdefault("extensions", {})["KHR_materials_emissive_strength"] = {"emissiveStrength": 0.8}
    j["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(bin_).decode()
    open(out, "w").write(json.dumps(j, separators=(",", ":")))


def export_player(sc, prefix, f0, f1, out):
    parts = [o for o in sc.objects if o.name.startswith(prefix + " ") and o.type in ("MESH", "EMPTY")]
    roots = [o for o in parts if o.parent is None or o.parent not in parts]
    if not roots:
        return False
    body = next((o for o in roots if o.name.endswith("body")), roots[0])
    root = bpy.data.objects.new(f"root {prefix}", None); sc.collection.objects.link(root)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); root.location = -body.matrix_world.translation.copy()
        root.keyframe_insert("location", frame=f)
    for o in roots:
        if o.parent is None:
            o.parent = root
    for o in sc.objects:
        o.select_set(False)
    root.select_set(True)
    for o in parts:
        o.select_set(True)
    sc.frame_start, sc.frame_end, sc.frame_step = f0, f1, 1; sc.frame_set(f0)
    tmp = out + ".glb"
    bpy.ops.export_scene.gltf(filepath=tmp, use_selection=True, export_animations=True, export_animation_mode="SCENE",
                              export_frame_range=True, export_force_sampling=True, export_yup=True,
                              export_cameras=False, export_lights=False)
    for o in roots:
        if o.parent is root:
            o.parent = None
    bpy.data.objects.remove(root)
    gltf_json(tmp, out, prefix); os.remove(tmp)
    return True


# ---------------------------------------------------------------- site.json
def rebuild_site():
    """data/site.json is rebuilt from specs/*.json + media by the shared gen_site.py (same as the cloud chats use)."""
    import runpy
    saved = sys.argv
    sys.argv = ["gen_site.py", SITE]
    try:
        runpy.run_path(os.path.join(SITE, "tools", "gen_site.py"), run_name="__main__")
    finally:
        sys.argv = saved


# ---------------------------------------------------------------- one pass
def do_pass(spec, force):
    key = spec["key"]; outdir = os.path.join(SITE, "media", key); os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    sc = load_pass(spec); setup(sc)
    print(f"[{key}] loaded in {time.time() - t0:.0f}s")
    stamps = {}
    for t in spec["takes"]:
        code = t["code"]; base = os.path.join(outdir, slug(code))
        kind = t.get("kind", spec.get("kind", "animation"))
        f0, f1 = t.get("frames") or [sc.frame_start, sc.frame_end]
        step = t.get("step", 4 if kind == "turntable" else 1)
        try:
            did = False
            if kind == "static":
                if force or not os.path.exists(base + ".jpg"):
                    did |= render_still(sc, t["cam3p"], t.get("still_frame", min(f1, f0 + 60)), base + ".jpg")
            else:
                if t.get("cam3p") and (force or not os.path.exists(base + "-3p.mp4")):
                    did |= render_clip(sc, t["cam3p"], f0, f1, step, base + "-3p.mp4")
                fp = t.get("camfp")
                if not fp and t.get("fp_head"):
                    fp = fp_cam(sc, t["fp_head"])
                if fp and (force or not os.path.exists(base + "-fp.mp4")):
                    if t.get("fp_head"):
                        hide_body_for_fp(sc, t["fp_head"], True)
                    did |= render_clip(sc, fp, f0, f1, step, base + "-fp.mp4")
                    if t.get("fp_head"):
                        hide_body_for_fp(sc, t["fp_head"], False)
                if t.get("player") and (force or not os.path.exists(base + ".gltf.json")):
                    try:
                        did |= export_player(sc, t["player"], f0, f1, base + ".gltf.json")
                    except Exception:
                        print("  3D export failed:", code, traceback.format_exc()[-300:])
            if did:
                stamps[code] = True
            print(f"[{key}] {code} done ({time.time() - t0:.0f}s)")
        except Exception:
            print(f"[{key}] {code} FAILED:", traceback.format_exc()[-600:])
    rebuild_site()
    return bool(stamps)


def git(*a):
    return subprocess.run(["git", "-C", SITE] + list(a), capture_output=True, text=True)


def ensure_identity():
    """Commits need a name and email; set them for this clone only if git has none."""
    if not git("config", "user.email").stdout.strip():
        git("config", "user.email", "sparkygogo77@gmail.com")
    if not git("config", "user.name").stdout.strip():
        git("config", "user.name", "J (Lantern review PC)")


def main():
    names, flags = args()
    specdir = os.path.join(SITE, "specs")
    if "--no-pull" not in flags and os.path.isdir(os.path.join(SITE, ".git")):
        if git("status", "--porcelain").stdout.strip():      # renders left from a run that couldn't commit
            ensure_identity(); git("add", "-A"); git("commit", "-q", "-m", "Review renders from J's PC (left over)")
        print(git("pull", "--rebase", "-q", "-X", "theirs").stderr.strip())
    keys = names or sorted(f[:-5] for f in os.listdir(specdir) if f.endswith(".json"))
    done = []
    for k in keys:
        p = os.path.join(specdir, f"{k}.json")
        if not os.path.exists(p):
            print("no spec:", p); continue
        spec = json.load(open(p, encoding="utf-8"))
        if spec.get("superseded_by") and not names:
            continue
        try:
            if do_pass(spec, "--force" in flags):
                done.append(k)
        except Exception:
            print(f"[{k}] FAILED:", traceback.format_exc()[-800:])
    if done and "--no-push" not in flags and os.path.isdir(os.path.join(SITE, ".git")):
        ensure_identity()
        git("add", "-A")
        r = git("commit", "-q", "-m", "Review renders from J's PC: " + ", ".join(done))
        if r.returncode != 0:
            print("COMMIT FAILED:", r.stdout.strip(), r.stderr.strip())
        else:
            r = git("push", "-q")
            if r.returncode != 0:   # someone pushed meanwhile: rebase onto it and try once more
                git("pull", "--rebase", "-q", "-X", "theirs")
                r = git("push", "-q")
            print("pushed" if r.returncode == 0 else "PUSH FAILED: " + r.stderr.strip())
    print("Rendered:", ", ".join(done) or "nothing new")


main()
