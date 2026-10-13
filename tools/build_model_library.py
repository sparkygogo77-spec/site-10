"""Builds LanternRing_SAFE_library.blend: one self-contained Blender file holding every Lantern Ring model.

  "Game models (jar)"    every .bbmodel the mod ships (assets/lanternring/bbmodel), converted with
                         tools/bbmodel_to_glb.py: one object per model, its own texture, glow cubes in a
                         separate glow material; laid out in a grid by family and marked as Blender assets.
  "Blender picks"        J's picked Blender-only builds (not bbmodels): A3 Hope sanctuary + turbine, C3 Red tower +
                         steak farms + rage orb, Deluge water G1 and R2, the L3 lean rig.
  "Pending picks"        round-2 work still waiting on J's pick: kneel K4-K7, suits S2a-S2c with masks M1-M3.

Every texture is packed into the file, so it opens on any machine with nothing else beside it, and it is
saved compressed. It is a normal openable file with a scene (not a library-only file).

    python tools/build_model_library.py OUT.blend LL_FOLDER
LL_FOLDER holds the Blender pass outputs (hope_sanctuary.blend, red_tower.blend, deluge_water.blend,
kneel_lean.blend, kneel2.blend, lantern_suit2.blend), as built by the update scripts in docs/blender/blender_updates.
"""
import os, sys, subprocess, math
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = sys.argv[1]
LL = sys.argv[2]
GLB = os.path.join(ROOT, "build", "glb_all")

# ------------------------------------------------------------------ 1. every game model -> .glb
os.makedirs(GLB, exist_ok=True)
subprocess.run([sys.executable, os.path.join(HERE, "bbmodel_to_glb.py"), GLB], check=True,
               stdout=subprocess.DEVNULL)
names = sorted(f[:-4] for f in os.listdir(GLB) if f.endswith(".glb"))

bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.name = "Lantern Ring library"


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c


def family(n):
    for key, label in (("lantern", "Lanterns"), ("battery", "Lanterns"), ("ring", "Rings"),
                       ("construct_", "Construct tools"), ("squad", "Blue squad"), ("ravager", "Blue squad"),
                       ("dread", "Dread Runner"), ("suit", "Suits"), ("drill", "Weapons"), ("pistol", "Weapons"),
                       ("nuke", "Weapons"), ("bull", "Creatures"), ("golem", "Creatures")):
        if key in n:
            return label
    return "Other"


game = coll("Game models (jar)")
fams = {}
placed = {}
for n in names:
    f = family(n)
    if f not in fams:
        fams[f] = coll(f, game)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(GLB, n + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    i = placed.get(f, 0); placed[f] = i + 1
    row = list(fams).index(f)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        fams[f].objects.link(o)
    for r in roots:
        r.location = (i * 3.0, row * 4.0, 0)
        r.name = n
        try:
            r.asset_mark()
        except Exception:
            pass

# ------------------------------------------------------------------ 2. Blender-only picks + pending work
SOURCES = [
    ("Blender picks", "hope_sanctuary.blend", ("HS A3",), (0, -120, 0)),
    ("Blender picks", "red_tower.blend", ("RT C3", "RT farms 110"), (120, -120, 0)),
    ("Blender picks", "deluge_water.blend", ("DW G1", "DW R2"), (240, -120, 0)),
    ("Blender picks", "kneel_lean.blend", ("KL L3",), (320, -120, 0)),
    ("Pending picks", "kneel2.blend", ("KL K",), (0, -60, 0)),
    ("Pending picks", "lantern_suit2.blend", ("LS S2", "LS M"), (40, -60, 0)),
]
groups = {}
for group, fname, prefixes, offset in SOURCES:
    path = os.path.join(LL, fname)
    if not os.path.exists(path):
        print("missing", path)
        continue
    if group not in groups:
        groups[group] = coll(group)
    sub = coll(fname[:-6], groups[group])
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(prefixes) and "(plan)" not in n]
    for o in dst.objects:
        if o is None:
            continue
        sub.objects.link(o)
    tops = [o for o in dst.objects if o is not None and (o.parent is None or o.parent.name not in sub.objects)]
    if tops:
        mx = min(o.location.x for o in tops); my = min(o.location.y for o in tops)
        for o in tops:
            o.location.x += offset[0] - mx
            o.location.y += offset[1] - my
            try:
                o.asset_mark()
            except Exception:
                pass

# ------------------------------------------------------------------ 3. light, camera, pack, save
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (20, -30, 25); cam.rotation_euler = (math.radians(60), 0, 0)
scene.collection.objects.link(cam); scene.camera = cam
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("pack:", e)
for _ in range(3):
    bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("objects:", len(bpy.data.objects), "game models:", len(names), "saved", OUT, os.path.getsize(OUT))
