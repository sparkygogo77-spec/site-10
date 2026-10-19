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

try:                      # print each line straight away: the PC script reads the log while Blender runs
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

ARGS = []          # when run from the Text Editor: e.g. ["518"] or ["--all"]

LANTERN_LIVE = os.environ.get("LANTERN_LIVE", r"C:\Users\Josh\Documents\LanternLive")
SITE = os.environ.get("LANTERN_SITE", os.path.join(LANTERN_LIVE, "review-site"))
REPO = os.environ.get("LANTERN_REPO", os.path.join(LANTERN_LIVE, "site-10"))
BUILD = os.path.join(LANTERN_LIVE, "_review_build")
DEV = "claude/lantern-redesign-pass2"   # the chats' working branch: specs + update scripts live there, not on review-site   # update scripts save their .blend here, not in the root
RES = (640, 360)
SITE_URL = os.environ.get("LANTERN_REVIEW_URL", "https://lantern-review-j.vercel.app")
TICKS = 20         # game ticks a second = one frame per tick


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ARGS)
    flags = {x for x in a if x.startswith("--")}
    return [x for x in a if not x.startswith("--")], flags


def slug(c):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", c)


# ---------------------------------------------------------------- the chats' branch
def fetch_dev():
    """Fetch the chats' branch into origin/dev (no checkout, no deploy)."""
    r = git("fetch", "-q", "origin", f"+refs/heads/{DEV}:refs/remotes/origin/dev")
    if r.returncode != 0:
        print("  (couldn't fetch the chats' branch:", r.stderr.strip()[:200], ")")
    return r.returncode == 0


def fetch_dev_file(path, outdir):
    """Copy one file from origin/dev (repo path like docs/blender/blender_updates/x.update.py) into outdir."""
    if not path or "/" not in path:
        return None
    r = subprocess.run(["git", "-C", SITE, "show", f"origin/dev:{path}"], capture_output=True)
    if r.returncode != 0:
        return None
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, os.path.basename(path))
    open(p, "wb").write(r.stdout)
    return p


def sync_specs():
    """Specs are written by the Blender chats to docs/blender/review/specs/ on their branch; copy them into the site."""
    r = git("ls-tree", "--name-only", "origin/dev", "docs/blender/review/specs/")
    n = 0
    for path in r.stdout.split():
        if path.endswith(".json") and fetch_dev_file(path, os.path.join(SITE, "specs")):
            n += 1
    print(f"  {n} specs from the chats' branch")


# ---------------------------------------------------------------- scene loading
def seed_assets():
    """Update scripts read assets under FOLDER (kl_assets: tool models, ring voxels; suit_tex: construct texture
    strips). Copy any missing ones from the site branch's assets/ folder (and J's own kl_assets) into BUILD."""
    import shutil
    root = os.path.join(SITE, "assets")
    for sub in (os.listdir(root) if os.path.isdir(root) else []):
        src, dst = os.path.join(root, sub), os.path.join(BUILD, sub)
        if not os.path.isdir(src):
            continue
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src):
            if not os.path.exists(os.path.join(dst, f)):
                shutil.copy(os.path.join(src, f), dst)
    # the texture library lives in the repo (docs/texture_library); scripts read FOLDER/texture_library/<corps>/<id>/
    # Copy every file the build folder is missing, not just the first time: strips added later (Yellow y1-y3 for 863)
    # would otherwise never reach a build folder that already holds the older library.
    r = git("ls-tree", "-r", "--name-only", "origin/dev", "docs/texture_library")
    if r.returncode == 0:
        n = 0
        for path in r.stdout.split():
            dst = os.path.join(BUILD, path.split("/", 1)[1])
            if os.path.exists(dst):
                continue
            f = subprocess.run(["git", "-C", SITE, "show", f"origin/dev:{path}"], capture_output=True)
            if f.returncode == 0:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, "wb").write(f.stdout)
                n += 1
        if n:
            print(f"  texture library: {n} new files copied from the chats' branch")
    else:
        print("  (texture library not available:", r.stderr[:200], ")")
    # J's own asset folders in LanternLive (the update scripts expect them next to FOLDER)
    for sub in ("kl_assets", "tool_tex", "texture_library", "hope_tex", "metal_tex", "red_tex", "models_glb",
                "suit_tex", "ref"):
        live = os.path.join(LANTERN_LIVE, sub)
        if not os.path.isdir(live):
            continue
        for root_, _, files in os.walk(live):
            dst = os.path.join(BUILD, sub, os.path.relpath(root_, live))
            os.makedirs(dst, exist_ok=True)
            for f in files:
                if not os.path.exists(os.path.join(dst, f)):
                    shutil.copy(os.path.join(root_, f), dst)


def script_time(spec):
    """When the pass's update script last changed on the chats' branch (unix seconds), or 0 if unknown."""
    script = spec.get("script")
    if not script:
        return 0
    r = git("log", "-1", "--format=%ct", "origin/dev", "--", script)
    return int(r.stdout.strip() or 0) if r.returncode == 0 else 0


def blend_is_stale(spec, path):
    """True when the .blend in J's area folder is older than its script, so the pass must be rebuilt from the script.
    Rebuilding replaces the file (the old one goes to _to_delete), so a file J edited by hand must not count as stale."""
    changed = script_time(spec)
    if not changed or not spec.get("script"):          # can't tell: keep J's file
        return False
    return changed > os.path.getmtime(path) + 60       # a minute's slack for the chats' clocks


def save_built_blend(spec):
    """Keep the scene a script just built as J's .blend in the area folder (spec "blend"), textures packed, so the file
    he opens is the one the site's clips came from. A file already there moves to _to_delete first."""
    blend = spec.get("blend")
    if not blend:
        return
    p = blend if os.path.isabs(blend) else os.path.join(LANTERN_LIVE, blend)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            old = os.path.join(LANTERN_LIVE, "_to_delete", time.strftime("%Y%m%d-%H%M%S-") + os.path.basename(p))
            os.makedirs(os.path.dirname(old), exist_ok=True)
            os.replace(p, old)
        try:
            bpy.ops.file.pack_all()
        except Exception as e:
            print("  (couldn't pack every texture:", str(e)[:120], ")")
        bpy.ops.wm.save_as_mainfile(filepath=p, copy=True, compress=True)
        print(f"  saved {blend} ({os.path.getsize(p) / 1e6:.1f} MB)")
    except Exception as e:                                # never lose the render over the file
        print(f"  (couldn't save {blend}:", str(e)[:200], ")")


def load_pass(spec):
    """Open the pass's packed .blend; if there isn't one (or it's older than its script), build it by running its
    update script and save the result as the .blend."""
    blend = spec.get("blend")
    if blend:
        p = blend if os.path.isabs(blend) else os.path.join(LANTERN_LIVE, blend)
        if os.path.exists(p) and not blend_is_stale(spec, p):
            bpy.ops.wm.open_mainfile(filepath=p)
            return max(bpy.data.scenes, key=lambda s: len(s.objects))
    script = spec.get("script")
    if script:
        seed_assets()
        dev_copy = fetch_dev_file(script, os.path.join(BUILD, "scripts"))
        if dev_copy:
            # A pass script may build on another pass's script (855 runs 603's) through KL_REPO/docs/blender/...:
            # mirror every update script it names into BUILD/repo and point KL_REPO there.
            mirror = os.path.join(BUILD, "repo", "docs", "blender", "blender_updates")
            todo, seen = [os.path.basename(script)], set()
            while todo:                                   # follow chains: 855 -> 603 -> 827
                dep = todo.pop()
                if dep in seen:
                    continue
                seen.add(dep)
                got = fetch_dev_file("docs/blender/blender_updates/" + dep, mirror)
                if got:
                    text = open(got, encoding="utf-8", errors="replace").read()
                    todo += re.findall(r"[0-9]{2,3}_[A-Za-z0-9_]+\.update\.py", text)
            os.environ["KL_REPO"] = os.path.join(BUILD, "repo")
        for d in ((os.path.dirname(dev_copy),) if dev_copy else ()) + (
                os.path.join(SITE, "scripts"), os.path.join(REPO, "docs", "blender", "blender_updates"), LANTERN_LIVE):
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
                save_built_blend(spec)                    # before setup() switches it to the review render settings
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
        sc.eevee.taa_render_samples = 8
    except Exception:
        pass


# ---------------------------------------------------------------- rendering
def _retry_file(fn, *a, tries=20, wait=0.5):
    """Windows keeps a fresh video locked for a moment (Blender's writer closing, antivirus scanning it): WinError 32.
    Retry for up to 10 s instead of failing the take."""
    for i in range(tries):
        try:
            return fn(*a)
        except PermissionError:
            if i == tries - 1:
                raise
            time.sleep(wait)


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
    # render to "<name>.part.mp4" and rename when finished, so a stopped run never leaves a half clip as done
    d, base = os.path.split(out)
    stem = os.path.splitext(base)[0] + ".part"
    for f in os.listdir(d):
        if f.startswith(stem):
            _retry_file(os.remove, os.path.join(d, f))
    sc.render.filepath = os.path.join(d, stem + ".mp4")
    bpy.ops.render.render(animation=True, scene=sc.name)
    for f in os.listdir(d):        # Blender may append the frame range to the name
        if f.startswith(stem) and f.endswith(".mp4"):
            _retry_file(os.replace, os.path.join(d, f), out)
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


FP_FOV = 120   # J: "120 deg is standard" -- horizontal field of view of every first-person clip
FP_V = 4       # bump when first-person framing changes; older first-person clips re-render (1st person only) once
FP_BLANK = 12000   # v3: a v2 clip this small is an empty view (the old hide also hid the floor, beam and ring)


def set_fp_fov(sc, cam_name):
    c = sc.objects.get(cam_name) or bpy.data.objects.get(cam_name)
    if c and c.type == "CAMERA":
        c.data.sensor_fit = "HORIZONTAL"; c.data.angle_x = math.radians(FP_FOV); c.data.clip_start = min(c.data.clip_start, 0.05)


def needs_fp(t, base):
    """Re-render the first-person clip once when it was made with an older field of view (v1), came out blank (v2: the
    old body-hiding also hid the floor, beam and ring) or looked backwards (v2-3: rigs facing +Y), unless J dropped it.
    v1 also skips KEEP takes."""
    if not (t.get("camfp") or t.get("fp_head")):
        return False
    stamp = base + ".fpv"
    v = int(open(stamp).read().strip() or 0) if os.path.exists(stamp) else 0
    if v >= FP_V or not (os.path.exists(base + "-fp.mp4") or os.path.exists(base + "-fp.skip")):
        return False
    rating = (RATINGS.get(t["_id"]) or {}).get("rating", "")
    if rating == "DROP":
        return False
    if t.get("fp_head"):                   # eye-camera bugs: fix these even on KEEP takes
        mp4 = base + "-fp.mp4"
        if (os.path.exists(mp4) and os.path.getsize(mp4) < FP_BLANK) or faces_plus_y(base):
            return True
    return v < 2 and rating != "KEEP"


def fp_cam(sc, prefix):
    """Minecraft-style eye camera on the player's head (field of view set by set_fp_fov). It sits at the eyes and looks
    the way they face: older rigs face -Y, newer ones (eye l / eye r meshes at +Y) face +Y."""
    from mathutils import Vector
    head = bpy.data.objects.get(f"{prefix} head")
    if head is None:
        return None
    name = f"FPEYE {prefix}"
    if name in bpy.data.objects:
        return name
    sign, ez = -1.0, 0.27
    eyes = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(prefix + " eye")]
    if eyes:
        pts = [o.matrix_world @ Vector(c) for o in eyes for c in o.bound_box]
        local = head.matrix_world.inverted() @ (sum(pts, Vector()) / len(pts))
        sign, ez = (1.0 if local.y > 0 else -1.0), local.z
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.sensor_fit = "VERTICAL"; c.data.angle_y = math.radians(70); c.data.clip_start = 0.05
    c.parent = head; c.matrix_parent_inverse.identity()
    c.location = (0.0, sign * 0.27, ez)
    c.rotation_euler = (math.radians(90), 0, 0 if sign > 0 else math.radians(180))
    return name


def faces_plus_y(base):
    """From the take's exported 3D model: does the rig's face point +Y (eye meshes in front)? glTF z = -Blender y."""
    try:
        j = json.load(open(base + ".gltf.json", encoding="utf-8"))
    except Exception:
        return False
    for n in j.get("nodes", []):
        if "mesh" in n and n.get("name", "").endswith((" eye l", " eye r")):
            try:
                a = j["accessors"][j["meshes"][n["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
                return a["max"][2] < 0
            except Exception:
                return False
    return False


# Body parts Minecraft doesn't draw in first person (first word after the player prefix). Rigs name props with the same
# prefix ("RB4 T1a beam", "... floor", "... ring band"), so only these words are hidden -- never the arms or what they hold.
FP_BODY = {"head", "eye", "eyes", "pupil", "mouth", "hat", "hair", "helmet", "visor", "neck", "torso", "body", "chest",
           "hip", "hips", "thigh", "shin", "leg", "legs", "lleg", "rleg", "lshin", "rshin", "pelvis", "waist", "belt", "cape"}
FP_ARM = {"arm", "larm", "rarm", "forearm", "upper", "elbow", "shoulder", "hand", "wrist", "finger", "fingers", "thumb"}


def _fp_word(o, prefix):
    return o.name[len(prefix) + 1:].split(" ")[0].split(".")[0].lower() if o.name.startswith(prefix + " ") else None


def fp_body_parts(sc, prefix):
    """Meshes to hide in first person: the player's body words, plus anything parented to them (eyes on the head),
    but nothing on the arm chain."""
    out = []
    for o in sc.objects:
        if o.type != "MESH":
            continue
        hide, k = False, o
        while k is not None:
            w = _fp_word(k, prefix)
            if w in FP_ARM:
                hide = False; break
            if w in FP_BODY:
                hide = True
            k = k.parent
        if hide:
            out.append(o)
    return out


def fp_arm_parts(sc, prefix):
    """The arms and what they hold (ring, tools): what first person should show."""
    out = []
    for o in sc.objects:
        if o.type != "MESH":
            continue
        k = o
        while k is not None:
            if _fp_word(k, prefix) in FP_ARM:
                out.append(o); break
            k = k.parent
    return out


def hide_body_for_fp(sc, prefix, hide):
    """In first person Minecraft draws no head or body; keep the arms, what they hold, and the world."""
    for o in fp_body_parts(sc, prefix):
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
    if ch:   # one animation for the viewer; rest pose = LAST keyframe: the finished look shows before you press play
        j["animations"] = [{"name": tag, "channels": ch, "samplers": sm}]
        for c in ch:
            acc = j["accessors"][sm[c["sampler"]]["output"]]; bv = j["bufferViews"][acc["bufferView"]]
            k = 4 if c["target"]["path"] == "rotation" else 3
            o = bv.get("byteOffset", 0) + acc.get("byteOffset", 0) + 4 * k * (acc["count"] - 1)
            j["nodes"][c["target"]["node"]][c["target"]["path"]] = list(struct.unpack("<%df" % k, bin_[o:o + 4 * k]))
    for m in j.get("materials", []):
        if "ring" in m.get("name", "").lower():
            m.setdefault("pbrMetallicRoughness", {})["baseColorFactor"] = [0.05, 0.75, 0.3, 1]
            m["emissiveFactor"] = [0.1, 1.0, 0.4]
            m.setdefault("extensions", {})["KHR_materials_emissive_strength"] = {"emissiveStrength": 0.8}
    j["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(bin_).decode()
    open(out, "w").write(json.dumps(j, separators=(",", ":")))


MODEL_V = 2   # bump when the 3D export changes; older models re-export (3D only) on the next run
BAKE_PX = 1024


def _descendants(o):
    out = []
    for c in o.children:
        out.append(c); out += _descendants(c)
    return out


def _procedural(mat):
    """True when a material's look comes from nodes glTF can't carry (noise, gradients, drivers...)."""
    if not mat or not mat.use_nodes:
        return False
    simple = {"BSDF_PRINCIPLED", "OUTPUT_MATERIAL", "TEX_IMAGE", "EMISSION", "BSDF_DIFFUSE"}
    return any(n.type not in simple for n in mat.node_tree.nodes)


_GPU = None


def use_gpu_for_cycles(sc):
    """Bakes use Cycles, which runs on the CPU unless told otherwise: switch it to the graphics card once per run."""
    global _GPU
    if _GPU is None:
        _GPU = False
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
                try:
                    prefs.compute_device_type = kind
                except Exception:
                    continue
                prefs.get_devices()
                gpus = [d for d in prefs.devices if d.type != "CPU"]
                if gpus:
                    for d in prefs.devices:
                        d.use = d.type != "CPU"
                    _GPU = True
                    print(f"  bakes on the graphics card ({kind}: {', '.join(d.name for d in gpus)})")
                    break
        except Exception as e:
            print("  (bakes stay on the CPU:", str(e)[:120], ")")
    if _GPU:
        sc.cycles.device = "GPU"


def bake_suit(sc, owner, pieces, f1, tag):
    """Join the pieces under one moving body part into a copy, give it one UV atlas, bake its colour and glow at the
    last frame (the finished look) and return the copy with a plain image material. Returns None when nothing needs it."""
    pieces = [o for o in pieces if o.type == "MESH" and any(_procedural(m) for m in o.data.materials)]
    if not pieces:
        return None
    sc.frame_set(f1)
    dg = bpy.context.evaluated_depsgraph_get()
    import bmesh
    bm = bmesh.new()
    mats = []
    for o in pieces:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(owner.matrix_world.inverted() @ o.matrix_world)
        remap = []
        for m in me.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        for poly in me.polygons:
            poly.material_index = remap[poly.material_index] if remap else 0
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(f"bake {tag}"); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(f"{owner.name} suit", me); sc.collection.objects.link(ob)
    ob.parent = owner; ob.matrix_parent_inverse.identity()
    for o in sc.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    uv = me.uv_layers.new(name="bake"); me.uv_layers.active = uv
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=0.5, island_margin=0.004, area_weight=1.0, correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    imgs = {}
    for kind in ("DIFFUSE", "EMIT"):
        img = bpy.data.images.new(f"{tag} {kind}", BAKE_PX, BAKE_PX, alpha=False)
        added = []
        for m in mats:
            n = m.node_tree.nodes.new("ShaderNodeTexImage"); n.image = img
            m.node_tree.nodes.active = n; added.append((m, n))
        old = sc.render.engine; sc.render.engine = "CYCLES"; use_gpu_for_cycles(sc)
        sc.cycles.samples = 2          # colour and glow bakes need no lighting samples
        try:
            if kind == "DIFFUSE":
                bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, margin=4, uv_layer="bake")
            else:
                bpy.ops.object.bake(type="EMIT", margin=4, uv_layer="bake")
        finally:
            sc.render.engine = old
            for m, n in added:
                m.node_tree.nodes.remove(n)
        imgs[kind] = img
    # one plain material the glTF exporter understands: baked colour + baked glow
    mat = bpy.data.materials.new(f"{tag} baked"); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexImage"); tc.image = imgs["DIFFUSE"]; tc.interpolation = "Closest"
    te = nt.nodes.new("ShaderNodeTexImage"); te.image = imgs["EMIT"]; te.interpolation = "Closest"
    nt.links.new(tc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.45
    me.materials.clear(); me.materials.append(mat)
    for p in me.polygons:
        p.material_index = 0
    for name in [l.name for l in me.uv_layers if l.name != "bake"]:
        me.uv_layers.remove(me.uv_layers[name])
    return ob


def export_player(sc, prefix, f0, f1, out):
    tops = [o for o in sc.objects if o.name.startswith(prefix + " ") and o.type in ("MESH", "EMPTY")]
    if not tops:
        return False
    # everything parented under the player's parts (suit pieces, gauntlets, the ring) belongs to the model
    extra = [d for o in tops for d in _descendants(o) if d not in tops and d.type in ("MESH", "EMPTY")]
    baked, hidden = [], []
    for o in [t for t in tops if t.parent is None or t.parent not in tops] + [t for t in tops if t.parent in tops]:
        try:
            b = bake_suit(sc, o, [d for d in _descendants(o) if d in extra and _owner(d, tops) is o], f1, f"{prefix} {o.name[len(prefix)+1:]}")
        except Exception:
            print("  bake failed for", o.name, traceback.format_exc()[-300:]); b = None
        if b:
            baked.append(b)
            hidden += [d for d in _descendants(o) if d in extra and _owner(d, tops) is o and d.type == "MESH" and any(_procedural(m) for m in d.data.materials)]
    parts = tops + [d for d in extra if d not in hidden] + baked
    roots = [o for o in parts if o.parent is None or o.parent not in parts]
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
    sc.frame_start, sc.frame_end, sc.frame_step = f0, f1, 1; sc.frame_set(f1)
    tmp = out + ".glb"
    bpy.ops.export_scene.gltf(filepath=tmp, use_selection=True, export_animations=True, export_animation_mode="SCENE",
                              export_frame_range=True, export_force_sampling=True, export_yup=True,
                              export_cameras=False, export_lights=False)
    for o in roots:
        if o.parent is root:
            o.parent = None
    bpy.data.objects.remove(root)
    for b in baked:   # drop the temporary copies; their images are left for Blender to discard (removing them
        try:          # by hand crashed Blender once on J's PC, mid-run)
            mats = list(b.data.materials); me = b.data
            bpy.data.objects.remove(b)
            bpy.data.meshes.remove(me)
            for m in mats:
                if m and m.users == 0:
                    bpy.data.materials.remove(m)
        except Exception:
            pass
    gltf_json(tmp, out, prefix); _retry_file(os.remove, tmp)
    open(out[:-len(".gltf.json")] + ".model", "w").write(str(MODEL_V))
    return True


def _ancestors(o):
    out = []
    while o.parent:
        o = o.parent; out.append(o)
    return out


def _owner(d, tops):
    """The player part a piece moves with: its nearest ancestor that is a player part."""
    return next((a for a in _ancestors(d) if a in tops), None)


# ---------------------------------------------------------------- site.json
def rebuild_site():
    """data/site.json is rebuilt from specs/*.json + media by the shared gen_site.py (same as the cloud chats use)."""
    import runpy
    saved = sys.argv
    sys.argv = ["gen_site.py", SITE]
    try:
        runpy.run_path(os.path.join(SITE, "tools", "gen_site.py"), run_name="__main__")
        st = os.path.join(SITE, "tools", "gen_status.py")
        if os.path.exists(st):          # "In the game" panel: jar contents + what isn't on the site yet
            sys.argv = ["gen_status.py", SITE, "--fetch"]
            try:
                runpy.run_path(st, run_name="__main__")
            except Exception as e:
                print("  (status panel not updated:", e, ")")
        ctl = os.path.join(SITE, "tools", "gen_control.py")
        if os.path.exists(ctl):         # Control tab: waiting passes, jar models, .blend files, textures, prompts
            sys.argv = ["gen_control.py", SITE]
            try:
                runpy.run_path(ctl, run_name="__main__")
            except Exception as e:
                print("  (control tab not updated:", e, ")")
    finally:
        sys.argv = saved


# ---------------------------------------------------------------- what to render (J: "optimize the amount rendered")
FP_MIN = 0.05          # skip a first-person clip when the arms/ring are in view in under 5% of its frames
HALF_RATE_OVER = 100   # clips longer than this many frames render every 2nd frame (10 a second)
RATINGS = {}           # J's ratings from the site; KEEP / DROP takes are decided and not re-rendered


def load_ratings():
    import urllib.request
    try:
        with urllib.request.urlopen(SITE_URL + "/api/reviews", timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print("  (couldn't read ratings, rendering as if none:", e, ")")
        return {}


def fp_visibility(sc, cam_name, prefixes, f0, f1, objs=None):
    """Share of frames (sampled every 3rd) where any arm/ring/tool mesh is inside the eye camera's view."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    cam = bpy.data.objects.get(cam_name)
    if objs is None:
        objs = [o for o in sc.objects if o.type == "MESH" and any(o.name.startswith(p) for p in prefixes)]
    if cam is None or not objs:
        return None
    frames = list(range(f0, f1 + 1, 3)); seen = 0
    for f in frames:
        sc.frame_set(f)
        hit = False
        for o in objs:
            for c in o.bound_box:
                v = world_to_camera_view(sc, cam, o.matrix_world @ Vector(c))
                if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1:
                    hit = True; break
            if hit:
                break
        seen += hit
    return seen / max(1, len(frames))


def rev_path(base):
    return base + ".rev"


def needs_render(t, base, force):
    """New takes always render. A take with media re-renders only when its spec `rev` went up
    (a Blender chat changed it) and J hasn't already decided it (KEEP or DROP)."""
    if force:
        return True
    have = any(os.path.exists(base + x) for x in ("-3p.mp4", "-fp.mp4", ".jpg"))
    if not have:
        return True
    old = int(open(rev_path(base)).read().strip() or 0) if os.path.exists(rev_path(base)) else 0
    if int(t.get("rev", 0)) <= old:
        return False
    rating = (RATINGS.get(t["_id"]) or {}).get("rating", "")
    if rating in ("KEEP", "DROP"):
        print(f"  {t['code']}: changed (rev {t.get('rev')}) but you rated it {rating}; skipped (use --force)")
        return False
    return True


def needs_model(t, base):
    """The 3D model is older than the current exporter (finished pose, baked suits): re-export it, 3D only.
    Skipped for takes J already decided (KEEP / DROP)."""
    if not t.get("player"):
        return False
    stamp = base + ".model"
    v = int(open(stamp).read().strip() or 0) if os.path.exists(stamp) else 0
    if os.path.exists(base + ".gltf.json") and v >= MODEL_V:
        return False
    return (RATINGS.get(t["_id"]) or {}).get("rating", "") not in ("KEEP", "DROP")


# ---------------------------------------------------------------- live progress on the site (/api/render)
PROG = {"running": True, "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "done": 0, "total": 0,
        "pass": "", "take": "", "etaSec": 0, "uploaded": 0, "failures": [], "note": ""}
_t_start = time.time()
_post_url = None


def report(**kw):
    """Tell the site how far the render is (shown as a banner on lantern-review-j.vercel.app). Never stops the run."""
    global _post_url
    PROG.update(kw)
    if PROG["done"] and PROG["total"]:
        per = (time.time() - _t_start) / PROG["done"]
        PROG["etaSec"] = int(per * max(0, PROG["total"] - PROG["done"]))
    try:
        import urllib.request
        if _post_url is None:      # the short address redirects to the branch address; POSTs must go to the final one
            with urllib.request.urlopen(urllib.request.Request(SITE_URL + "/api/render", headers={"User-Agent": "lantern-render"}), timeout=15) as r:
                _post_url = r.geturl()
        req = urllib.request.Request(_post_url, data=json.dumps(PROG).encode(), method="POST",
                                     headers={"content-type": "application/json", "User-Agent": "lantern-render"})
        urllib.request.urlopen(req, timeout=15).read()
    except Exception as e:
        _post_url = _post_url or ""
        if not PROG.get("_warned"):
            print("  (couldn't update the site's progress banner:", str(e)[:120], ")"); PROG["_warned"] = True


def skipped_takes():
    """Takes the PC script found hanging in this run ("<pass> <take>" lines in review-site\\SKIPPED): leave them out."""
    p = os.path.join(SITE, "SKIPPED")
    return set(open(p).read().split("\n")) if os.path.exists(p) else set()


def plan_pass(spec, force):
    """The takes of a pass that need any work (clips, 3D or first person), without opening Blender files."""
    key = spec["key"]; outdir = os.path.join(SITE, "media", key)
    todo = []
    skip = skipped_takes()
    for t in spec["takes"]:
        t["_id"] = f"{key}_{t['code']}"
        if f"{key} {t['code']}" in skip:
            PROG["failures"].append(f"{key} {t['code']}: hung last time, skipped this run") if f"{key} {t['code']}: hung last time, skipped this run" not in PROG["failures"] else None
            continue
        base = os.path.join(outdir, slug(t["code"]))
        t["_clips"] = needs_render(t, base, force)
        if t["_clips"] or needs_model(t, base) or needs_fp(t, base):
            todo.append(t)
    return todo


# ---------------------------------------------------------------- one pass
def do_pass(spec, force):
    key = spec["key"]; outdir = os.path.join(SITE, "media", key); os.makedirs(outdir, exist_ok=True)
    todo = plan_pass(spec, force)
    if not todo:
        print(f"[{key}] nothing new"); return False
    t0 = time.time()
    sc = load_pass(spec); setup(sc)
    print(f"[{key}] loaded in {time.time() - t0:.0f}s; rendering {len(todo)} of {len(spec['takes'])} takes")
    stamps = {}
    rerender = force or any(os.path.exists(rev_path(os.path.join(outdir, slug(t["code"])))) for t in todo)
    for t in todo:
        report(**{"pass": key, "take": t["code"]})
        open(os.path.join(SITE, "CURRENT"), "w").write(f"{key} {t['code']}")   # the PC script's watchdog reads this
        if stop_requested():
            print(f"[{key}] STOP file found: stopping after the takes done so far"); break
        code = t["code"]; base = os.path.join(outdir, slug(code))
        kind = t.get("kind", spec.get("kind", "animation"))
        f0, f1 = t.get("frames") or [sc.frame_start, sc.frame_end]
        step = t.get("step", 4 if kind == "turntable" else (2 if f1 - f0 + 1 > HALF_RATE_OVER else 1))
        redo = t["_clips"]                 # clips only when new / changed; otherwise this take only needs its 3D
        try:
            did = False
            if kind == "static":
                if redo or not os.path.exists(base + ".jpg"):
                    did |= render_still(sc, t["cam3p"], t.get("still_frame", min(f1, f0 + 60)), base + ".jpg")
            else:
                if t.get("cam3p") and (redo or not os.path.exists(base + "-3p.mp4")):
                    did |= render_clip(sc, t["cam3p"], f0, f1, step, base + "-3p.mp4")
                fp = t.get("camfp")
                if not fp and t.get("fp_head"):
                    fp = fp_cam(sc, t["fp_head"])
                fp_again = needs_fp(t, base)
                if fp and (redo or fp_again or not os.path.exists(base + "-fp.mp4")):
                    set_fp_fov(sc, fp)
                    for old in (base + "-fp.mp4", base + "-fp.skip"):
                        if fp_again and os.path.exists(old):
                            _retry_file(os.remove, old)
                    prefixes = [t["fp_prefix"] + " "] if t.get("fp_prefix") else \
                               ([t["fp_head"] + " "] if t.get("fp_head") else [])
                    if t.get("fp_head"):
                        hide_body_for_fp(sc, t["fp_head"], True)
                    vis = fp_visibility(sc, fp, [p for p in prefixes], f0, f1) if prefixes else None
                    if t.get("fp_head") and vis is not None:
                        # only the arms count for a real-body eye camera
                        vis = fp_visibility(sc, fp, [], f0, f1, objs=fp_arm_parts(sc, t["fp_head"]))
                    if vis is not None and vis < FP_MIN:
                        open(base + "-fp.skip", "w").write(f"{vis:.3f}")
                        print(f"  {code}: first person skipped, arms in view {vis:.0%} of frames")
                    else:
                        did |= render_clip(sc, fp, f0, f1, step, base + "-fp.mp4")
                    if t.get("fp_head"):
                        hide_body_for_fp(sc, t["fp_head"], False)
                    open(base + ".fpv", "w").write(str(FP_V))
                if t.get("player") and (redo or needs_model(t, base)):
                    try:
                        did |= export_player(sc, t["player"], f0, f1, base + ".gltf.json")
                    except Exception:
                        print("  3D export failed:", code, traceback.format_exc()[-300:])
            open(rev_path(base), "w").write(str(int(t.get("rev", 0))))
            if did:
                stamps[code] = True
            print(f"[{key}] {code} done ({time.time() - t0:.0f}s)")
            report(done=PROG["done"] + 1)
        except Exception:
            err = traceback.format_exc()
            print(f"[{key}] {code} FAILED:", err[-600:])
            PROG["failures"].append(f"{key} {code}: {err.strip().splitlines()[-1][:120]}")
            report(done=PROG["done"] + 1)
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


STOP_FILE = os.path.join(SITE, "STOP")
UPLOAD_EVERY = 15 * 60   # long runs upload what's done every 15 min (one Vercel deploy each) so the site fills as it goes


def stop_requested():
    """J can end a run cleanly: create review-site\\STOP (PowerShell: ni review-site\\STOP). The run finishes the take
    it's on, uploads everything done so far, deletes STOP and quits."""
    return os.path.exists(STOP_FILE)


def sync_with_site(msg):
    """Put this clone on top of the site as it is online, keeping every render made here. Never rebases (a stuck
    rebase once left the clone off its branch and every push failed): the site's own files (page, tools, specs)
    come from online, media/ comes from here, data/ is rebuilt from both."""
    for st in ("rebase-merge", "rebase-apply"):
        if os.path.exists(os.path.join(SITE, ".git", st)):
            git("rebase", "--quit")
    if os.path.exists(os.path.join(SITE, ".git", "MERGE_HEAD")):
        git("merge", "--quit")
    git("checkout", "-q", "-B", "review-site")               # back on the branch, keeping whatever HEAD has
    if git("fetch", "-q", "origin", "review-site").returncode != 0:
        return False
    git("reset", "-q", "--mixed", "origin/review-site")
    git("checkout", "origin/review-site", "--", ".", ":(exclude)media", ":(exclude)data")
    git("branch", "-q", "--set-upstream-to=origin/review-site")
    rebuild_site()
    ensure_identity(); git("add", "-A")
    if git("status", "--porcelain").stdout.strip():
        git("commit", "-q", "-m", msg)
    return True


def publish(msg):
    ensure_identity()
    git("add", "-A")
    if git("status", "--porcelain").stdout.strip():
        r = git("commit", "-q", "-m", msg)
        if r.returncode != 0:
            print("COMMIT FAILED:", r.stdout.strip(), r.stderr.strip()); return
    r = git("push", "-q", "origin", "HEAD:review-site")
    if r.returncode != 0:   # the site moved on (or the clone got stuck): line up with it and try once more
        sync_with_site(msg)
        r = git("push", "-q", "origin", "HEAD:review-site")
    print("pushed: " + msg if r.returncode == 0 else "PUSH FAILED: " + r.stderr.strip())


# ---------------------------------------------------------------- one render at a time
# RENDER.ps1 has its own lock, but a chat can start Blender with this script directly; two runs on the same pass
# fight over the same files (WinError 32, 2026-10-15: runs at 18:51 and 18:55 both rendered 702).
BLENDER_LOCK = "BLENDER.lock"


def _pid_alive(pid):
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong(); ok = k.GetExitCodeProcess(h, ctypes.byref(code)); k.CloseHandle(h)
        return bool(ok) and code.value == 259           # STILL_ACTIVE
    try:
        os.kill(pid, 0); return True
    except OSError:
        return False


def take_lock():
    path = os.path.join(SITE, BLENDER_LOCK)
    try:
        other = int(open(path).read().strip() or 0)
    except Exception:
        other = 0
    if other and other != os.getpid() and _pid_alive(other):
        print(f"Another render (process {other}) is already running here. Nothing started; it will pick up this work.")
        return False
    open(path, "w").write(str(os.getpid()))
    import atexit
    atexit.register(lambda: os.path.exists(path) and open(path).read().strip() == str(os.getpid()) and os.remove(path))
    return True


def main():
    names, flags = args()
    if not take_lock():
        return
    specdir = os.path.join(SITE, "specs")
    if "--no-pull" not in flags and os.path.isdir(os.path.join(SITE, ".git")) and not os.environ.get("LR_RELOADED"):
        if git("status", "--porcelain").stdout.strip():      # renders left from a run that couldn't commit
            ensure_identity(); git("add", "-A"); git("commit", "-q", "-m", "Review renders from J's PC (left over)")
        me = os.path.join(SITE, "tools", "lantern_review.py")
        before = open(me, "rb").read() if os.path.exists(me) else b""
        sync_with_site("Review renders from J's PC (left over)")   # no rebase: can't get stuck
        if os.path.exists(me) and open(me, "rb").read() != before:
            # the pull brought a newer renderer: run that one now, not the copy already loaded
            print("Renderer updated; restarting with the new version")
            import runpy
            os.environ["LR_RELOADED"] = "1"
            runpy.run_path(me, run_name="__main__")
            return
    if fetch_dev():
        sync_specs()
    global RATINGS
    RATINGS = load_ratings()
    keys = names or sorted(f[:-5] for f in os.listdir(specdir) if f.endswith(".json"))
    done = []
    push = "--no-push" not in flags and os.path.isdir(os.path.join(SITE, ".git"))
    # plan first, so the site can show "12 of 48 takes, about 9 min left"
    plan = {}
    for k in keys:
        p = os.path.join(specdir, f"{k}.json")
        if not os.path.exists(p):
            continue
        sp = json.load(open(p, encoding="utf-8"))
        if (sp.get("superseded_by") or (RATINGS.get(f"pass_{k}") or {}).get("scrapped")) and not names:
            continue
        plan[k] = plan_pass(sp, "--force" in flags)
    report(total=sum(len(v) for v in plan.values()), note="")
    print(f"  {sum(len(v) for v in plan.values())} takes to render across {sum(1 for v in plan.values() if v)} passes")
    last_push, pushed = time.time(), []
    for k in keys:
        p = os.path.join(specdir, f"{k}.json")
        if not os.path.exists(p):
            print("no spec:", p); continue
        spec = json.load(open(p, encoding="utf-8"))
        if spec.get("superseded_by") and not names:
            continue
        if (RATINGS.get(f"pass_{k}") or {}).get("scrapped") and not names:
            print(f"[{k}] scrapped on the site; skipped"); continue
        try:
            if do_pass(spec, "--force" in flags):
                done.append(k)
                ensure_identity(); git("add", "-A"); git("commit", "-q", "-m", f"Review renders from J's PC: {k}")
                if push and "--push-each" in flags:      # one deploy per pass only when asked
                    publish(f"Review renders from J's PC: {k}")
                elif push and time.time() - last_push > UPLOAD_EVERY:   # long runs: the site fills as it goes
                    publish("Review renders from J's PC: " + ", ".join(d for d in done if d not in pushed))
                    pushed += done; last_push = time.time(); report(uploaded=PROG["uploaded"] + 1)
        except KeyboardInterrupt:
            print("Ctrl+C: uploading what's done so far")
            rebuild_site()
            if push:
                publish(f"Review renders from J's PC: {', '.join(done + [k + ' (part)'])}")
            return
        except Exception:
            err = traceback.format_exc()
            print(f"[{k}] FAILED:", err[-800:])
            PROG["failures"].append(f"{k}: {err.strip().splitlines()[-1][:140]}")
            report(done=PROG["done"] + len(plan.get(k, [])))
        if stop_requested():
            os.remove(STOP_FILE)
            if push and done:
                publish("Review renders from J's PC: " + ", ".join(done))
            print("Stopped by the STOP file. Run the same command again to carry on where it left off.")
            report(running=False, finishedAt=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), note="Stopped early (STOP file)")
            return
    rest = [d for d in done if d not in pushed]
    if push and rest and "--push-each" not in flags:
        publish("Review renders from J's PC: " + ", ".join(rest))   # one deploy for the rest of the run
    print("Rendered:", ", ".join(done) or "nothing new")
    report(running=False, finishedAt=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), done=PROG["total"],
           note=("Rendered " + ", ".join(done)) if done else "Nothing new to render")
    open(os.path.join(SITE, "last_render_summary.txt"), "w").write(
        f"{PROG['total']} takes, {len(PROG['failures'])} failed\n" + "\n".join(PROG["failures"]))


main()
