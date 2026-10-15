"""python3 render_manifest.py KEY [KEY...]  (run inside the bpy python)
Renders every take of the given manifest pass keys: frames to FR/<key>/<code>-3p|-fp/, stills, glTF to MD/<key>/."""
import os, sys, json, time, struct, base64, re, traceback
import bpy
import numpy as np
from mathutils import Vector
R = "/tmp/claude-0/-home-claude-site-10/339d885c-9635-527f-8aeb-f861000ea518/scratchpad/review"
REPO = "/home/claude/site-10"
LL = "/tmp/claude-0/-home-claude-site-10/339d885c-9635-527f-8aeb-f861000ea518/scratchpad/LL2"
FR, MD = os.environ.get("FR_OVERRIDE", f"{R}/frames2"), os.environ.get("MD_OVERRIDE", f"{R}/models2")
man = json.load(open(f"{R}/manifest.json"))
man["passes"] += json.load(open("/home/claude/review-tools/movement_manifest.json"))["passes"]
def key_of(p): return p["pass"] + ("cps" if p.get("entry") == "combat pick sheet" else "")
def slug(c): return re.sub(r"[^A-Za-z0-9_.-]+", "_", c)
os.environ["LL_NO_RENDER"] = "1"

def glb_to_gltf_json(path, out, tag):
    b = open(path, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); rest = b[20 + n:]
    bn = struct.unpack("<I", rest[:4])[0]; bin_ = rest[8:8 + bn]
    ch, sm = [], []
    for a in j.get("animations", []):
        off = len(sm); sm += a["samplers"]
        for c in a["channels"]: c = dict(c); c["sampler"] += off; ch.append(c)
    if ch:
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
    if not roots: return False
    body = next((o for o in roots if o.name.endswith("body")), roots[0])
    saved = {o.name: (o.parent, o.matrix_parent_inverse.copy()) for o in roots}
    root = bpy.data.objects.new(f"root {prefix}", None); sc.collection.objects.link(root)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); p = body.matrix_world.translation.copy()
        root.location = -p; root.keyframe_insert("location", frame=f)
    for o in roots:
        if o.parent is None: o.parent = root
    for o in sc.objects: o.select_set(False)
    root.select_set(True)
    for o in parts: o.select_set(True)
    fs, fe = sc.frame_start, sc.frame_end
    sc.frame_start, sc.frame_end = f0, f1; sc.frame_set(f0)
    bpy.context.window.scene = sc
    tmp = out + ".glb"
    bpy.ops.export_scene.gltf(filepath=tmp, use_selection=True, export_animations=True, export_animation_mode="SCENE",
                              export_frame_range=True, export_force_sampling=True, export_yup=True, export_cameras=False,
                              export_lights=False)
    sc.frame_start, sc.frame_end = fs, fe
    for o in roots:
        if o.parent is root: o.parent = None
    bpy.data.objects.remove(root)
    glb_to_gltf_json(tmp, out, prefix); os.remove(tmp)
    return True

def render_cam(sc, cam, f0, f1, step, d):
    if cam not in bpy.data.objects: print("MISSING CAM", cam, flush=True); return False
    sc.camera = bpy.data.objects[cam]; os.makedirs(d, exist_ok=True)
    for i, f in enumerate(range(f0, f1 + 1, step)):
        p = os.path.join(d, "f%03d.png" % i)
        if os.path.exists(p): continue
        sc.frame_set(f); sc.render.filepath = p
        bpy.ops.render.render(write_still=True, scene=sc.name)
    open(os.path.join(d, "done"), "w").write(str(20 / step))
    return True

def fp_cam(sc, prefix):
    """Minecraft-style eye camera on the player's head (70 deg vertical FOV)."""
    import math
    head = bpy.data.objects.get(f"{prefix} head")
    if head is None: return None
    name = f"FPEYE {prefix}"
    if name in bpy.data.objects: return name
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.sensor_fit = "VERTICAL"; c.data.angle_y = math.radians(70); c.data.clip_start = 0.05
    c.parent = head; c.matrix_parent_inverse.identity()
    c.location = (0.0, -0.27, 0.27); c.rotation_euler = (math.radians(90), 0, math.radians(180))
    return name

def render_fp(sc, prefix, cam, f0, f1, step, d):
    hidden = [o for o in sc.objects if o.name.startswith(prefix + " ") and "arm" not in o.name and o.type == "MESH"]
    for o in hidden: o.visible_camera = False
    try: return render_cam(sc, cam, f0, f1, step, d)
    finally:
        for o in hidden: o.visible_camera = True

def setup(sc):
    sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 480, 270, 100
    sc.render.image_settings.file_format = "PNG"

def load(script):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for s in list(bpy.data.scenes)[1:]: bpy.data.scenes.remove(s)
    src = os.path.join(REPO, script)
    cwd = os.getcwd(); os.chdir(os.path.dirname(src))
    try:
        exec(compile(open(src).read(), src, "exec"), {"bpy": bpy, "np": np, "FOLDER": LL, "__name__": "__ll__", "__file__": src})
    finally:
        os.chdir(cwd)
    return max(bpy.data.scenes, key=lambda s: len(s.objects))

for key in sys.argv[1:]:
    p = next(x for x in man["passes"] if key_of(x) == key)
    sup = bool(p.get("superseded_by"))
    groups = {}
    for t in p["takes"]:
        groups.setdefault(t.get("script") or p["script"], []).append(t)
    for script, takes in groups.items():
        t0 = time.time()
        try:
            sc = load(script); setup(sc)
        except Exception:
            print("LOAD FAIL", key, script, traceback.format_exc()[-800:], flush=True); continue
        print("LOADED", key, script, round(time.time() - t0), flush=True)
        for t in takes:
            try:
                kind = t.get("kind", p["kind"]); f0, f1 = t.get("frames") or [sc.frame_start, sc.frame_end]
                base = f"{FR}/{key}/{slug(t['code'])}"
                if kind == "static":
                    fm = min(f1, f0 + 60)
                    render_cam(sc, t["cam3p"], fm, fm, 1, base + "-still")
                    continue
                step = 4 if kind == "turntable" else (2 if sup or key == "519" else 1)
                if t.get("cam3p"): render_cam(sc, t["cam3p"], f0, f1, step, base + "-3p")
                if t.get("camfp"): render_cam(sc, t["camfp"], f0, f1, step, base + "-fp")
                elif t.get("fp_head"):
                    cn = fp_cam(sc, t["fp_head"])
                    if cn: render_fp(sc, t["fp_head"], cn, f0, f1, step, base + "-fp")
                pl = t.get("player")
                if pl and kind == "animation":
                    os.makedirs(f"{MD}/{key}", exist_ok=True)
                    out = f"{MD}/{key}/{slug(t['code'])}.gltf.json"
                    if not os.path.exists(out):
                        try: export_player(sc, pl, f0, f1, out)
                        except Exception: print("GLTF FAIL", key, t["code"], traceback.format_exc()[-400:], flush=True)
                print("TAKE", key, t["code"], round(time.time() - t0), flush=True)
            except Exception:
                print("TAKE FAIL", key, t["code"], traceback.format_exc()[-600:], flush=True)
    print("PASS DONE", key, flush=True)
