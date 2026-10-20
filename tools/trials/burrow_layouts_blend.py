"""3D x-ray of burrow web layouts side by side (J's lair note 4).

blender.exe -b --python burrow_layouts_blend.py -- <out.blend> <code>=<sequence dir> [...] [--stills]
Each layout: the burrows, dens and the lair's ring tunnel as solid shapes, the lair and cave 1 as faint ghosts, one
camera ("<code> x-ray") looking down at an angle, the code burnt into the view. --stills renders
renders_web/<code>.png next to the .blend.
"""
import json, math, os, sys
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_blender_kit as K

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
items = [a.split("=", 1) for a in argv[1:] if "=" in a]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
K.sc = sc
M = K.cave_materials(textured=False)
ghost = K.mat("cave ghost", (0.55, 0.65, 0.9), 0.5, alpha=0.10)
ring_m = K.mat("ring tunnel", (0.35, 0.5, 0.7), 0.6)
label_m = K.mat("label", (1, 1, 1), 0.5, (1, 1, 1), 1.2)
cams = []
x_off = 0.0
for code, d in items:
    z = np.load(os.path.join(d, "sequence.npz"))
    mask, solid = z["mask"], z["solid"]
    meta = json.loads(str(z["meta"]))
    X, Y, Z = mask.shape
    tun = np.isin(mask, (3, 11, 12))
    mats = [M[1], M[10], ring_m]

    def fm(idx, nidx, ax, d_, mask=mask):
        t = mask[idx[:, 0], idx[:, 1], idx[:, 2]]
        return np.where(t == 12, 1, np.where(t == 3, 2, 0))
    o = K.voxel_mesh(f"{code} burrows", tun, fm, mats)
    o.location.x = x_off
    caves = ((~solid) & np.isin(mask, (1, 10)))
    g = K.voxel_mesh(f"{code} caves ghost", caves, lambda i, n, a, d_: np.zeros(len(i), int), [ghost])
    g.location.x = x_off
    c = Vector((x_off + X * 0.5, -Z * 0.5, Y * 0.35))
    cam = K.camera(f"{code} x-ray", tuple(c + Vector((X * 0.05, -Z * 1.25, Y * 1.55))), tuple(c + Vector((0, 0, -Y * 0.1))), 30)
    cu = bpy.data.curves.new(code + " label", "FONT"); cu.body = code; cu.size = 0.055
    lb = bpy.data.objects.new(code + " label", cu); sc.collection.objects.link(lb); lb.data.materials.append(label_m)
    lb.parent = cam; lb.location = (-0.33, 0.17, -1.0)
    K.light(f"{code} key", tuple(c + Vector((0, -Z * 0.4, Y * 2))), 3000000, (1, 0.95, 0.9), "AREA", 400)
    cams.append((code, cam))
    x_off += X + 300
w = bpy.data.worlds.new("World"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.04, 0.045, 0.06, 1)
sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.use_denoising = True
prefs = bpy.context.preferences.addons["cycles"].preferences
for dt in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dt; prefs.get_devices()
        if any(dv.type == dt for dv in prefs.devices):
            for dv in prefs.devices:
                dv.use = dv.type == dt
            sc.cycles.device = "GPU"; break
    except TypeError:
        continue
sc.view_settings.view_transform = "Standard"
sc.camera = cams[0][1]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
if "--stills" in argv:
    rdir = os.path.join(os.path.dirname(OUT), "renders_web")
    os.makedirs(rdir, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.image_settings.file_format = "PNG"
    for code, cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, code.split()[0] + ".png")
        bpy.ops.render.render(write_still=True)
        print("still", sc.render.filepath)
    sc.camera = cams[0][1]
print("done", OUT)
