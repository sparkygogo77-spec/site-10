# Pass 862: first-person tools, round 6 variations (rings/suits chat, 2026-10-16, range 800-899). Built from 852's
# script (rev 2); 852 and 861 are untouched. Only the 15 new takes are here.
# J's 852 ratings: no-note IMPROVEs S4b1, H1b1, H2a1, H2a2, C1d1 -> "3 new variations each" (codes +1/2/3).
# Dropped siblings (their ideas are not reused): S4b3 (two-step lunge, blade turns over), H1b2 (windmill smash),
# H1b3 (jumping smash), H2a3 (step in 3 blocks). The ten C1e combos of pass 859 are not repeated either.
# Carried rules: swords heavy and slow with a short charge, none faster than 852 S2c1 (each thrust takes 3-4 ticks after
# a charge, as S2c1's cuts do); hammers are solid 3D constructs, the head lands face first; mobs react on contact.
# J's words: H1b "More variations, keep this one"; H2a "This is good for variations of when i swing and i hit a mob
# further than my crosshair"; C1a "make a few variations of the mix up between cross cross DASH strike like 12 blocks
# forward? but the charge up for the dash final hit is like .7s and I need the sword to prime upword and be held at 20
# degree angle from pointed at them".
#
# Each new take keeps its parent's construction family and forms a different way from its siblings:
#   extrude (S4b1, H1b1): b1 behind a scan plate (as the parent), b4 the plate sweeps from the tip back to the grip,
#     b5 two plates start at both ends and meet in the middle
#   pixel stream (H2a1 a1 / C1d1 a1): a1 grip first (as the parent), a4 a pixel ribbon winds round the tool grip to tip,
#     a5 pixels gather in from a cloud round the fist
#   spiral (H2a2 a2): a2 up the forearm (as the parent), a6 two counter-spirals, a7 down from the shoulder, each section
#     flashes in
#
#   S4b11 high guard, long charge, deep stepping lunge (0.7 block), hold, pull out                         (b1)
#   S4b12 hanging guard high by the right ear, point down at the mob, descending lunge, edge vertical      (b4)
#   S4b13 high guard lunge, then you sink and drive on: the mob rides the point back, then slides off   (b5)
#   H1b11 longer charged hang, smash, the head rebounds once and settles; two shockwaves; the mob is crushed (b1)
#   H1b12 hang high over the right shoulder, diagonal smash; one shockwave and a crack runs out ahead       (b4)
#   H1b13 hang, smash and sink with it (knees bend); three shockwave pulses, growing                         (b5)
#   H2a11 level backhand, the haft clicks out 2 blocks in three steps on the swing                         (a1)
#   H2a12 rising backhand from low left, the haft slides out 2 blocks on the way up                        (a4)
#   H2a13 the haft runs out 2 blocks on the wind-up, a long waist-high sweep, snaps back after the hit     (a5)
#   H2a21 backhand throw: the head arcs out wide 4 blocks on the chain, comes back the other side, caught  (a2)
#   H2a22 whirl the head on a short chain overhead, then backhand it out 4 blocks                          (a6)
#   H2a23 the head flies 4 blocks, hooks the mob and yanks it 2.5 blocks toward you                        (a7)
#   C1d11 charged crosses (a short charge before each), overhead prime, low skimming dash (you drop 0.3 m),
#         thrust; the mob skids 3 blocks back                                                               (a1)
#   C1d12 crosses (the second quick), overhead prime, the dash comes in two bursts with a ring re-flare between,
#         thrust                                                                                            (a4)
#   C1d13 crosses, overhead prime, a slow first step then an explosive dash, thrust spins the mob round    (a5)
#   Every C1d1x: high-right then high-left crosses, primed overhead for 0.7 s (14 ticks) with the blade solved to
#   20.0 deg above the fist-to-mob line, ~12-block dash (the point meets the mob 12 m out), thrust.
#
# Cameras: "Cam <take>" first person (120 deg, crosshair; on the C1d takes it rides the dash), "Cam <take> side" third
# person from the right. Bays 80 m apart. Every take forms over ticks 0-14 (20 ticks a second), then swings twice with a
# 6-tick rest (once for the C1d dash takes). Writes LanternLive\combat\fp_tools6_poses.json, builds
# LanternLive\combat\fp_tools6.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector

R = math.radians
OUT = os.path.join(FOLDER, "combat", "fp_tools6.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
BB = None
for d_ in (os.path.join(FOLDER, "kl_assets"), os.path.join(os.getcwd(), "src", "main", "resources", "assets", "lanternring", "bbmodel")):
    if os.path.exists(os.path.join(d_, "construct_sword_green.bbmodel")):
        BB = d_; break
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
SCENE_NAME = "FP Tools 6"
old = bpy.data.scenes.get(SCENE_NAME)
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(SCENE_NAME)
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
FORM = 14                 # forming ticks
GAP = 6                   # rest ticks between the two swings
P = 1 / 16
PX = P * 1.05             # first-person pixel (as 803/844)


def link(o):
    col.objects.link(o)
    return o


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_start = 0.02
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


def mat(name, rgb, emit=0.0, alpha=1.0, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


SKIN = mat("FT6 skin", (0.62, 0.42, 0.3)); SLEEVE = mat("FT6 sleeve", (0.04, 0.28, 0.12))
RINGM = mat("FT6 ring face", (0.02, 0.85, 0.15), emit=2.0); GOLDM = mat("FT6 ring gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0)
GLASS = mat("FT6 hard-light glass", (0.03, 0.45, 0.16), emit=0.8, alpha=0.62, rough=0.15)
GLOW = mat("FT6 construct glow", (0.05, 0.9, 0.22), emit=3.5)
RIM = mat("FT6 construct rim", (0.08, 1.0, 0.28), emit=4.5)
GRIP = mat("FT6 construct grip", (0.02, 0.2, 0.08), emit=0.6, rough=0.3)
PIX = mat("FT6 forming pixel", (0.06, 1.0, 0.28), emit=4.0)
SCAN = mat("FT6 scan plate", (0.05, 0.95, 0.25), emit=3.0, alpha=0.45)
BEAM = mat("FT6 guide beam", (0.04, 0.95, 0.22), emit=5.0, alpha=0.7)
CHG = mat("FT6 charge shell", (0.03, 0.8, 0.2), emit=2.2, alpha=0.28, rough=0.2)
WAVE = mat("FT6 shockwave", (0.04, 0.85, 0.2), emit=3.0, alpha=0.6)
XH = mat("FT6 crosshair", (0.85, 0.85, 0.85), emit=1.0)
FLOOR = mat("FT6 floor", (0.18, 0.2, 0.22), rough=0.9)
WALL = mat("FT6 backdrop", (0.24, 0.26, 0.3), rough=0.95)
STONE = mat("FT6 block", (0.32, 0.33, 0.35), rough=0.9)
DIRT = mat("FT6 dirt", (0.35, 0.24, 0.15), rough=0.95)
DUMMY = mat("FT6 dummy", (0.07, 0.11, 0.08), rough=0.85)
DUMMYH = mat("FT6 dummy head", (0.1, 0.16, 0.1), rough=0.85)
HIT = mat("FT6 hit flash", (0.04, 0.7, 0.18), emit=1.6, alpha=0.8)
BOXF = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]


def box(name, a, b, m, parent=None, loc=None):
    a = np.array(a, float); b = np.array(b, float)
    v = [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], BOXF); me.update(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me))
    if parent is not None:
        o.parent = parent
    if loc is not None:
        o.location = loc
    return o


def multibox(name, boxes, parent, origin):
    """One mesh from many (a, b, material) boxes, origin at `origin` (parent space)."""
    mats = []; verts = []; faces = []; fm = []
    for a, b, m in boxes:
        if m not in mats:
            mats.append(m)
        a = np.array(a, float) - origin; b = np.array(b, float) - origin
        base = len(verts)
        verts += [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
        faces += [tuple(base + i for i in f) for f in BOXF]; fm += [mats.index(m)] * 6
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for m in mats:
        me.materials.append(m)
    for p, i in zip(me.polygons, fm):
        p.material_index = i
    o = link(bpy.data.objects.new(name, me)); o.parent = parent; o.location = tuple(origin)
    return o


def key(o, f, loc=None, rot=None, sc=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if sc is not None:
        o.scale = (sc,) * 3 if np.isscalar(sc) else sc; o.keyframe_insert("scale", frame=f)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def curve_at(pts, t):
    """[(tick, value)] -> value at tick t (smooth between points, held outside)."""
    if not pts:
        return 0.0
    if t <= pts[0][0]:
        return pts[0][1]
    for (ta, a), (tb, b) in zip(pts, pts[1:]):
        if ta <= t <= tb:
            return a + (b - a) * smooth((t - ta) / (tb - ta))
    return pts[-1][1]


# ------------------------------------------------------------------ swings
# (tick, arm pitch, yaw, roll, tool tilt, reach m). Pitch 90 = straight ahead, >90 raised; yaw + = toward the left
# (- = right); roll twists the forearm; tilt leans the tool forward in the fist; reach moves the shoulder (+ forward).
# With roll 0 and yaw 0 the tool points (pitch - tilt) degrees above level: the C1d prime uses that for its 20 deg.
REST = (96, 14, 0, 22, 0.0)
T = {}


def take(code, name, tool, build, keys, hits, fixed=(), charge=(), main=None, plays=2, knock=0.6, ext=(), body=(),
         hop=(), parent=None, note="", extra=None):
    T[code] = dict(name=name, tool=tool, build=build, keys=[(0, *REST)] + keys, hits=hits, fixed=list(fixed),
                   charge=list(charge), main=hits[0] if main is None else main, plays=plays, knock=knock, ext=list(ext),
                   body=list(body), hop=list(hop), parent=parent, note=note, extra=extra or {})


NN = "no note: 3 new variations (J's standing rule)"
# ---- S4b1 sword lunge from a high guard (extrude family; b1 scan plate, b4 scan plate tip to grip, b5 two plates)
# Thrusts take 4 ticks (no faster than S2c1's cuts), a charge before each, the mob reacts on contact.
take("S4b11", "Sword: high guard, long charge, deep stepping lunge, hold and pull out", "sword", "b1",
     [(4, 120, 4, 0, 100, -0.28), (10, 122, 4, 0, 102, -0.32), (14, 86, 7, 0, 72, 0.5), (17, 86, 7, 0, 72, 0.48),
      (22, *REST)], [14], fixed=[(2, 19, 90)], charge=[(4, 10)], knock=1.3,
     body=[(0, 0.0), (10, 0.0), (14, 0.7), (18, 0.7), (22, 0.0)], parent="S4b1", note=NN)
take("S4b12", "Sword: hanging guard high by the right ear, descending lunge, edge vertical", "sword", "b4",
     [(5, 146, -22, 0, 138, -0.2), (11, 148, -24, 0, 140, -0.24), (15, 94, 4, 0, 98, 0.46), (18, 92, 4, 0, 98, 0.44),
      (23, *REST)], [15], fixed=[(2, 20, 0)], charge=[(5, 11)], knock=1.0, parent="S4b1", note=NN)
take("S4b13", "Sword: high guard, lunge, then sink and drive the mob back on the point", "sword", "b5",
     [(3, 118, 4, 0, 98, -0.26), (10, 120, 4, 0, 100, -0.3), (14, 88, 6, 0, 74, 0.44), (17, 86, 6, 0, 72, 0.64),
      (20, 86, 6, 0, 72, 0.64), (25, *REST)], [14], fixed=[(2, 22, 90)], charge=[(3, 10)], knock=1.1,
     hop=[(0, 0.0), (10, 0.0), (14, -0.1), (18, -0.18), (23, 0.0)], parent="S4b1", note=NN,
     extra={"react": "push", "push_to": 17})
# ---- H1b1 heavy hammer: long wind-up, charged hang, crushing smash, shockwave (extrude family)
H1B = "More variations, keep this one"
take("H1b11", "Heavy hammer: longer hang, smash, the head rebounds once, double shockwave", "hammer_big", "b1",
     [(8, 150, -8, 0, -50, -0.08), (15, 154, -8, 0, -58, -0.1), (18, 54, 4, 0, 88, 0.1), (19, 62, 4, 0, 80, 0.08),
      (21, 55, 4, 0, 87, 0.09), (23, 57, 4, 0, 85, 0.09), (27, *REST)], [18], charge=[(8, 15)], knock=1.0,
     parent="H1b1", note=H1B, extra={"wave": "double", "react": "crush"})
take("H1b12", "Heavy hammer: hang high over the right shoulder, diagonal smash, a crack runs out ahead", "hammer_big",
     "b4", [(7, 146, -30, -20, -46, -0.08), (12, 150, -32, -22, -54, -0.1), (15, 58, 6, 10, 86, 0.1),
            (17, 60, 6, 10, 84, 0.08), (20, 58, 4, 0, 84, 0.08), (24, *REST)], [15], charge=[(7, 12)], knock=1.1,
     parent="H1b1", note=H1B, extra={"wave": "line", "react": "crush"})
take("H1b13", "Heavy hammer: hang, smash and sink into it, three shockwave pulses", "hammer_big", "b5",
     [(6, 148, -8, 0, -48, -0.06), (13, 152, -6, 0, -56, -0.1), (16, 52, 4, 0, 90, 0.12), (19, 50, 4, 0, 92, 0.12),
      (21, 56, 4, 0, 86, 0.1), (25, *REST)], [16], charge=[(6, 13)], knock=1.2,
     hop=[(0, 0.0), (16, 0.0), (18, -0.16), (20, -0.2), (23, 0.0)], parent="H1b1", note=H1B,
     extra={"wave": "pulse", "react": "crush"})
# ---- H2a1 hammer backhand, the haft telescopes 2 blocks to reach a mob past the crosshair (pixel stream family)
H2A = "This is good for variations of when i swing and i hit a mob further than my crosshair"
take("H2a11", "Hammer: level backhand, haft clicks out 2 blocks in three steps", "hammer3d", "a1",
     [(5, 98, 50, 90, 30, 0.0), (8, 98, 52, 90, 30, -0.02), (11, 95, -26, 90, 60, 0.05), (13, 95, -38, 90, 58, 0.04),
      (17, *REST)], [11], knock=1.0, ext=[(0, 0.0), (7, 0.0), (8, 0.67), (9, 1.33), (10, 2.0), (13, 2.0), (16, 0.0)],
     parent="H2a1", note=H2A, extra={"reach": "telescope", "clicks": [8, 9, 10]})
take("H2a12", "Hammer: rising backhand from low left, haft slides out 2 blocks on the way up", "hammer3d", "a4",
     [(5, 74, 46, 60, 40, 0.0), (8, 72, 48, 60, 40, -0.02), (12, 118, -24, 110, 40, 0.06), (14, 124, -34, 110, 36, 0.04),
      (18, *REST)], [12], knock=1.0, ext=[(0, 0.0), (7, 0.0), (12, 2.0), (14, 2.0), (17, 0.0)], parent="H2a1", note=H2A,
     extra={"reach": "telescope"})
take("H2a13", "Hammer: haft out 2 blocks on the wind-up, long waist-high sweep, snaps back", "hammer3d", "a5",
     [(6, 86, 56, 90, 34, -0.02), (9, 86, 58, 90, 34, -0.02), (13, 84, -24, 90, 62, 0.04), (15, 84, -40, 90, 60, 0.02),
      (18, *REST)], [13], knock=1.0, ext=[(0, 0.0), (3, 0.0), (6, 2.0), (14, 2.0), (15, 0.0)], parent="H2a1", note=H2A,
     extra={"reach": "telescope"})
# ---- H2a2 hammer backhand, the head flies 4 blocks on a chain of light (spiral family)
take("H2a21", "Hammer: backhand throw, the head arcs out 4 blocks, comes back and is caught", "hammer3d", "a2",
     [(4, 104, 50, 90, 24, 0.0), (8, 106, 54, 90, 22, -0.04), (11, 98, -12, 90, 58, 0.06), (12, 96, -26, 90, 60, 0.06),
      (15, 96, -30, 90, 60, 0.04), (16, 100, -20, 90, 50, -0.04), (20, *REST)], [12], knock=1.0,
     ext=[(0, 0.0), (9, 0.0), (12, 4.0), (13, 4.0), (15, 0.0)], parent="H2a2", note=H2A,
     extra={"reach": "chain", "arc": 1.0})
take("H2a22", "Hammer: whirl the head round on a short chain, then backhand it out 4 blocks", "hammer3d", "a6",
     [(3, 112, 30, 90, 20, 0.0), (5, 124, -6, 90, 8, 0.0), (7, 112, -40, 90, 18, 0.0), (10, 100, 46, 90, 26, -0.02),
      (12, 97, -14, 90, 56, 0.06), (13, 95, -28, 90, 62, 0.06), (16, 95, -30, 90, 60, 0.04), (20, *REST)], [13],
     knock=1.0, ext=[(0, 0.0), (2, 0.0), (3, 0.8), (10, 0.8), (13, 4.0), (14, 4.0), (17, 0.0)], parent="H2a2", note=H2A,
     extra={"reach": "chain"})
take("H2a23", "Hammer: backhand, the head flies 4 blocks, hooks the mob and yanks it 2.5 blocks back", "hammer3d", "a7",
     [(4, 100, 52, 90, 26, 0.0), (7, 100, 54, 90, 26, -0.02), (10, 96, -24, 90, 60, 0.06), (12, 96, -28, 90, 60, 0.04),
      (14, 106, -10, 90, 30, -0.1), (18, *REST)], [10], knock=1.0,
     ext=[(0, 0.0), (7, 0.0), (10, 4.0), (11, 4.0), (14, 1.5), (16, 0.0)], parent="H2a2", note=H2A,
     extra={"reach": "chain", "react": "pull", "pull_to": 14})
# ---- C1d1 dash combo: high-right then high-left crosses, primed overhead 0.7 s (14 ticks) held 20 deg above pointing at
#      the mob, ~12-block dash, thrust (pixel stream family). The prime tilt is solved so it is 20.0 deg in the build.
C1A = ("make a few variations of the mix up between cross cross DASH strike like 12 blocks forward? but the charge up for "
       "the dash final hit is like .7s and I need the sword to prime upword and be held at 20 degree angle from pointed "
       "at them")
DASH = 12.0
take("C1d11", "Dash combo: charged crosses, overhead prime, low skimming dash, thrust skids the mob 3 blocks", "sword",
     "a1", [(3, 136, -26, -34, -12, -0.04), (5, 137, -27, -35, -14, -0.05), (9, 64, 30, 30, 78, 0.08),
            (12, 138, 30, 35, -18, -0.04), (16, 139, 31, 36, -20, -0.05), (20, 62, -28, -30, 80, 0.08),
            (23, 152, 0, 0, 132, -0.1), (37, 152, 0, 0, 132, -0.1), (38, 152, 0, 0, 132, -0.08), (42, 90, 7, 0, 72, 0.42),
            (45, 90, 7, 0, 72, 0.4), (51, *REST)], [42], main=42, fixed=[(22, 47, 90)],
     charge=[(3, 5), (12, 16), (23, 37)], plays=1, knock=2.6, body=[(0, 0.0), (37, 0.0), (42, None)],
     hop=[(0, 0.0), (37, 0.0), (39, -0.28), (41, -0.28), (44, 0.0)], parent="C1d1", note=C1A,
     extra={"react": "skid", "prime": (23, 37)})
take("C1d12", "Dash combo: crosses, overhead prime, dash in two bursts with a ring re-flare, thrust", "sword", "a4",
     [(3, 136, -26, -34, -12, -0.04), (7, 64, 30, 30, 78, 0.08), (11, 138, 30, 35, -18, -0.04),
      (12, 139, 31, 36, -20, -0.05), (16, 62, -28, -30, 80, 0.08), (19, 152, 0, 0, 132, -0.1), (33, 152, 0, 0, 132, -0.1),
      (36, 152, 0, 0, 132, -0.08), (40, 90, 7, 0, 72, 0.42), (43, 90, 7, 0, 72, 0.4), (49, *REST)], [40], main=40,
     fixed=[(18, 45, 90)], charge=[(19, 33), (35, 37)], plays=1, knock=2.6,
     body=[(0, 0.0), (33, 0.0), (35, 5.5), (37, 5.5), (40, None)], parent="C1d1", note=C1A,
     extra={"prime": (19, 33)})
take("C1d13", "Dash combo: crosses, overhead prime, slow first step then explosive dash, thrust spins the mob round",
     "sword", "a5",
     [(4, 134, -24, -32, -10, -0.04), (8, 64, 30, 30, 78, 0.08), (12, 140, 30, 35, -20, -0.04), (16, 62, -28, -30, 80, 0.08),
      (18, 152, 0, 0, 132, -0.1), (32, 152, 0, 0, 132, -0.1), (34, 154, 0, 0, 134, -0.12), (38, 90, 7, 0, 72, 0.42),
      (41, 90, 7, 0, 72, 0.4), (47, *REST)], [38], main=38, fixed=[(17, 43, 90)], charge=[(18, 32)], plays=1, knock=2.6,
     body=[(0, 0.0), (32, 0.0), (35, 1.0), (38, None)], parent="C1d1", note=C1A,
     extra={"react": "spin", "prime": (18, 32)})
# Shovels: dug straight ahead the flat blade hides under the forearm in first person, so the dig keys swing the arm
# 14 deg in toward the crosshair and 5 deg up (as 844).
for _tk, _v in T.items():
    if _v["tool"] == "shovel":
        _v["keys"][:] = [k if k[1:] == REST else (k[0], k[1] + 5, k[2] + 14, k[3], k[4], k[5]) for k in _v["keys"]]
BUILD_NAME = {"a1": "pixel stream, grip first", "a2": "pixels spiral up the forearm", "a3": "pixel jet, tip first",
              "b1": "extrudes behind a scan plate", "b2": "guide beam, then extrudes behind a bright edge with sparks",
              "b3": "ratchets out in four clicks", "c1": "sections fly in and lock", "c2": "sections unfold out of the grip",
              "c3": "sections orbit the fist and spiral in",
              "a4": "pixel ribbon winds round the tool, grip to tip", "a5": "pixels gather in from a cloud round the fist",
              "a6": "two counter-spirals up the forearm", "a7": "pixels spiral down from the shoulder, each section flashes in",
              "b4": "scan plate sweeps from the tip back to the grip", "b5": "two scan plates start at both ends and meet"}


def pose_at(keys, t):
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = smooth((t - ta) / (tb - ta))
            return [x + (y - x) * w for x, y in zip(a, b)]
    return list(keys[-1][1:])


# ------------------------------------------------------------------ tool models -> (a, b, material) boxes, tool space
def tool_boxes(tool):
    out = []
    if tool.startswith("hammer"):
        def hb(a, b, m):
            out.append((np.array(a, float), np.array(b, float), m))
        if tool == "hammer3d":                     # 803's construct block hammer
            hb((-0.03, 0.0, -0.03), (0.03, 0.62, 0.03), GRIP)
            for y in (0.08, 0.2, 0.32, 0.44):
                hb((-0.04, y, -0.04), (0.04, y + 0.03, 0.04), GLOW)
            hb((-0.2, 0.58, -0.12), (0.2, 0.82, 0.12), GLASS); hb((-0.12, 0.64, -0.06), (0.12, 0.76, 0.06), GLOW)
            for sx in (-1, 1):
                hb((sx * 0.2 - 0.015, 0.57, -0.13), (sx * 0.2 + 0.015, 0.83, 0.13), RIM)
                hb((sx * 0.23 - 0.02, 0.6, -0.1), (sx * 0.23 + 0.02, 0.8, 0.1), GLASS)
            hb((-0.2, 0.82, -0.12), (0.2, 0.84, 0.12), RIM)
        else:                                      # heavy (844 H1b): long haft, wide deep head, stepped faces, collar
            hb((-0.035, 0.0, -0.035), (0.035, 0.8, 0.035), GRIP)
            for y in (0.06, 0.18, 0.3, 0.42, 0.54):
                hb((-0.045, y, -0.045), (0.045, y + 0.03, 0.045), GLOW)
            hb((-0.07, 0.66, -0.07), (0.07, 0.72, 0.07), RIM)
            hb((-0.26, 0.72, -0.16), (0.26, 1.04, 0.16), GLASS); hb((-0.16, 0.8, -0.08), (0.16, 0.96, 0.08), GLOW)
            for sx in (-1, 1):
                hb((sx * 0.26 - 0.015, 0.71, -0.17), (sx * 0.26 + 0.015, 1.05, 0.17), RIM)
                hb((sx * 0.29 - 0.03, 0.75, -0.13), (sx * 0.29 + 0.03, 1.01, 0.13), GLASS)
                hb((sx * 0.32 - 0.01, 0.78, -0.1), (sx * 0.32 + 0.01, 0.98, 0.1), RIM)
        return out
    d = json.load(open(os.path.join(BB, f"construct_{tool}_green.bbmodel")))
    for e in d["elements"]:
        nm = e["name"]
        m = GRIP if nm.startswith("handle") else RIM if nm.startswith("glow_rim") else GLOW if nm.startswith("glow") else GLASS
        inf = float(e.get("inflate", 0) or 0) / 32.0
        out.append((np.array(e["from"], float) / 32.0 - inf, np.array(e["to"], float) / 32.0 + inf, m))
    return out


def ring_on_fist(tag, parent, end_z, px):
    """The jar's placement: on the punching face, 1 px in from the back of the hand, over the middle finger."""
    mt = link(bpy.data.objects.new(f"{tag} ring mount", None)); mt.parent = parent
    mt.location = (0, 0, end_z); mt.rotation_euler = (0, 0, R(90))
    c = 0.6 * px
    box(f"{tag} ring band", (1.95 * px, -0.55 * px, 0), (2.25 * px, 0.55 * px, 1.4 * px), GOLDM, mt)
    box(f"{tag} ring frame", (c - 1.25 * px, -1.25 * px, -0.45 * px), (c + 1.25 * px, 1.25 * px, 0), GOLDM, mt)
    box(f"{tag} ring face", (c - 0.95 * px, -0.95 * px, -1.0 * px), (c + 0.95 * px, 0.95 * px, -0.4 * px), RINGM, mt)
    return Vector((0, c, end_z - 1.0 * px))


GRIP_LOC = Vector((0, -1.1 * PX, -10.6 * PX))
SH_LOCAL = Vector((0.36, 0.12, -0.42))          # shoulder from the eye


def make_arm(tag, parent):
    sh = link(bpy.data.objects.new(f"{tag} shoulder", None)); sh.parent = parent; sh.location = SH_LOCAL
    sh.rotation_mode = "XYZ"
    box(f"{tag} sleeve", (-2 * PX, -2 * PX, -8 * PX), (2 * PX, 2 * PX, 0), SLEEVE, sh)
    box(f"{tag} hand", (-2 * PX, -2 * PX, -12 * PX), (2 * PX, 2 * PX, -8 * PX), SKIN, sh)
    box(f"{tag} knuckles", (-2.05 * PX, 1.2 * PX, -12.05 * PX), (2.05 * PX, 2.05 * PX, -11.1 * PX), SKIN, sh)
    ring_pt = ring_on_fist(tag, sh, -12 * PX, PX)
    grip = link(bpy.data.objects.new(f"{tag} grip", None)); grip.parent = sh
    grip.location = tuple(GRIP_LOC); grip.rotation_mode = "XYZ"
    return sh, grip, ring_pt


def arm_matrix(p):
    pitch, yaw, roll, tilt, reach = p
    e_ = Euler((R(pitch), 0, R(yaw)), "XYZ"); e_.rotate_axis("Z", R(roll))
    return e_, Matrix.Translation(SH_LOCAL + Vector((0, reach, 0))) @ e_.to_matrix().to_4x4()


def grip_matrix(tilt):
    return Matrix.Translation(GRIP_LOC) @ Matrix.Rotation(R(-tilt), 4, "X")


def eye_angles(v):
    """eye-space vector -> (deg right of the crosshair, deg above it); the eye camera looks 4.8 deg down."""
    h = math.degrees(math.atan2(v.x, v.y))
    vv = math.degrees(math.atan2(v.z, math.hypot(v.x, v.y))) + 4.76
    return round(h, 1), round(vv, 1)


dump = {"format": "per take: per tick right-arm rotation (pitch, yaw, roll in degrees, pitch 90 = ahead), shoulder reach "
                  "(m, + forward), tool tilt and twist, body offset (m: forward, up), reach extension (m); 'hit' = the "
                  "tick the tool connects; forming ticks 0-14 come first. 20 ticks a second.", "takes": {}}
BAY = 80.0
ORDER = list(T)
MODEL_AT = {}
AIM_TIP = (0.275, 0.66, 0.008)                     # the pick's tip corner (tool space, x mirrored for the other tip)
AIM_PT = {}
for bi, tk in enumerate(ORDER):
    S = T[tk]
    name, tool, build, keys, hits = S["name"], S["tool"], S["build"], S["keys"], S["hits"]
    fixed, plays = S["fixed"], S["plays"]
    tag = f"FT6 {tk} fp"
    wtag = f"FT6 {tk} world"
    bx = bi * BAY
    eye0 = Vector((bx, 0.0, 1.62))
    swing = keys[-1][0]
    total = FORM + plays * swing + (plays - 1) * GAP + 10
    long_bay = bool(S["body"])

    def kk_of(t):
        """tick t -> tick within the swing being played (None while forming or resting)."""
        if t < FORM:
            return None
        k = t - FORM
        for pl in range(plays):
            s0 = pl * (swing + GAP)
            if s0 <= k <= s0 + swing:
                return k - s0
        return None

    poses = []
    for t in range(total + 1):
        k = kk_of(t)
        poses.append(list(REST) if k is None else pose_at(keys, k))
    mats_ = [arm_matrix(p)[1] @ grip_matrix(p[3]) for p in poses]       # tool space -> eye (body) space
    bxs = tool_boxes(tool)
    span = max(float(b[1]) for _, b, _ in bxs)
    ext_t = [0.0 if kk_of(t) is None else curve_at(S["ext"], kk_of(t)) for t in range(total + 1)]
    # body travel (dash / step) and hop. A body point with value None is solved so the tool's far end lands DASH m out.
    bpts = list(S["body"])
    if bpts and bpts[-1][1] is None:
        hk = S["main"]
        loc_tip = mats_[FORM + hk] @ Vector((0, span, 0))
        bpts[-1] = (bpts[-1][0], DASH - loc_tip.y)
    S["body_pts"] = bpts
    if S["extra"].get("prime"):                      # C1d1x: solve the prime hold so the blade is 20 deg above the fist-mob line
        pa, pb = S["extra"]["prime"]
        hk = S["main"]
        mob_eye = (Vector((0, bpts[-1][1] if bpts else 0.0, curve_at(S["hop"], hk) if S["hop"] else 0.0))
                   + mats_[FORM + hk] @ Vector((0, span, 0)))   # the hit point (eye space at the start)
        def prime_err(yaw_, tilt_, pitch_):
            pz = (pitch_, yaw_, 0.0, tilt_, keys_p[4])
            m_ = arm_matrix(pz)[1] @ grip_matrix(tilt_)
            fist = m_ @ Vector((0, 0, 0)); bd = (m_ @ Vector((0, 1, 0)) - fist).normalized()
            to = (mob_eye - fist).normalized()
            eb = math.degrees(math.asin(bd.z)); et = math.degrees(math.asin(to.z))
            hb_ = math.degrees(math.atan2(bd.x, bd.y)); ht = math.degrees(math.atan2(to.x, to.y))
            return hb_ - ht, eb - et - 20.0, math.degrees(bd.angle(to))
        keys_p = next(k for k in S["keys"] if k[0] == pa)[1:]
        yaw_, tilt_ = keys_p[1], keys_p[3]
        for _ in range(30):
            e1, e2, _a = prime_err(yaw_, tilt_, keys_p[0])
            if abs(e1) < 0.01 and abs(e2) < 0.01:
                break
            d = 0.01
            j11 = (prime_err(yaw_ + d, tilt_, keys_p[0])[0] - e1) / d; j12 = (prime_err(yaw_, tilt_ + d, keys_p[0])[0] - e1) / d
            j21 = (prime_err(yaw_ + d, tilt_, keys_p[0])[1] - e2) / d; j22 = (prime_err(yaw_, tilt_ + d, keys_p[0])[1] - e2) / d
            det = j11 * j22 - j12 * j21
            yaw_ -= (j22 * e1 - j12 * e2) / det; tilt_ -= (-j21 * e1 + j11 * e2) / det
        S["keys"] = [(k[0], k[1], yaw_, k[3], tilt_, k[5]) if pa <= k[0] <= pb else k for k in S["keys"]]
        keys = S["keys"]
        S["prime_deg"] = round(prime_err(yaw_, tilt_, keys_p[0])[1] + 20.0, 2)
        S["prime_pose"] = (round(keys_p[0], 1), round(yaw_, 2), round(tilt_, 2))
        poses = []
        for t in range(total + 1):
            k = kk_of(t)
            poses.append(list(REST) if k is None else pose_at(keys, k))
        mats_ = [arm_matrix(p)[1] @ grip_matrix(p[3]) for p in poses]

    def body_off(t):
        k = kk_of(t)
        if k is None:
            k = 0 if t < FORM else swing
        fwd = curve_at(bpts, k) if bpts else 0.0
        up = curve_at(S["hop"], k) if S["hop"] else 0.0
        return Vector((0, fwd, up))

    offs = [body_off(t) for t in range(total + 1)]
    tips_local = [m_ @ Vector((0, 0.75, 0)) for m_ in mats_]
    far_world = [eye0 + offs[t] + mats_[t] @ Vector((0, span + ext_t[t], 0)) for t in range(total + 1)]
    # ---- the working edge leads: turn the tool about its length to face the tip's motion
    phis = []
    phi_prev = 0.0
    for t in range(total + 1):
        k_ = kk_of(t)
        fx = None if k_ is None else next((dd for a_, b_, dd in fixed if a_ <= k_ <= b_), None)
        if fx is not None:
            phi = R(fx)
        else:
            v = (tips_local[min(total, t + 1)] + offs[min(total, t + 1)]) - (tips_local[max(0, t - 1)] + offs[max(0, t - 1)])
            v = v - (offs[min(total, t + 1)] - offs[max(0, t - 1)])            # body travel doesn't turn the blade
            vg = mats_[t].to_3x3().inverted() @ v
            if math.hypot(vg.x, vg.z) > 0.004:
                phi = math.atan2(-vg.z, vg.x)
                alt = phi + math.pi
                phi = min((phi, alt), key=lambda a: abs((a - phi_prev + math.pi) % (2 * math.pi) - math.pi))
            else:
                phi = phi_prev
        phi = phi_prev + ((phi - phi_prev + math.pi) % (2 * math.pi) - math.pi)
        phi = phi_prev + (phi - phi_prev) * 0.65 if fx is None else phi
        phi_prev = phi
        phis.append(phi)
    if S["extra"].get("twist_add"):                  # S2a2 rev 2: extra turn about the length on top of the edge lead
        phis = [ph + (0.0 if kk_of(t) is None else R(curve_at(S["extra"]["twist_add"], kk_of(t)))) for t, ph in
                enumerate(phis)]
    # ---- world: floor, backdrop, the mob (or block) that meets the tool's far end at the main hit
    yfar = 26 if long_bay else 11
    box(f"{wtag} floor", (bx - 6, -6, -0.02), (bx + 3.5 if not long_bay else bx + 12, yfar, 0), FLOOR)
    box(f"{wtag} backdrop", (bx - 6.2, -8, 0), (bx - 6, yfar + 2, 7), WALL)
    t_main = FORM + S["main"]
    tip_hit = far_world[t_main]
    blocky = tool in ("pickaxe", "shovel")
    aim = S["extra"].get("aim")
    if aim:                                          # P1c2/P1c3 rev 2: the leading pick tip is the hit point
        tm_ = mats_[t_main] @ Matrix.Rotation(phis[t_main], 4, "Y")
        cands = [tm_ @ Vector((sx_ * AIM_TIP[0], AIM_TIP[1], AIM_TIP[2])) for sx_ in (1, -1)]
        tip_hit = eye0 + offs[t_main] + max(cands, key=lambda c_: c_.y)
        AIM_PT[tk] = tuple(tip_hit)
    if blocky and aim:                               # a stack of blocks; the one under the crosshair takes the hit
        face_y = tip_hit.y - 0.04
        tz = tip_hit.z + 0.45
        tgt = link(bpy.data.objects.new(f"{wtag} block pivot", None)); tgt.location = (tip_hit.x, face_y, 0)
        box(f"{wtag} block", (-0.45, 0, 0), (0.45, 0.9, tz), STONE, tgt)
        box(f"{wtag} block seam", (-0.46, -0.004, tip_hit.z - 0.46), (0.46, 0.0, tip_hit.z - 0.44), DUMMY, tgt)
        flash = box(f"{wtag} hit", (-0.12, -0.01, -0.12), (0.12, 0.0, 0.12), HIT, loc=(tip_hit.x, face_y - 0.002, tip_hit.z))
    elif blocky:
        tz = max(0.25, tip_hit.z - 0.03)
        tgt = link(bpy.data.objects.new(f"{wtag} block pivot", None)); tgt.location = (tip_hit.x, tip_hit.y - 0.12, 0)
        box(f"{wtag} block", (-0.45, 0, 0), (0.45, 0.9, tz), DIRT if tool == "shovel" else STONE, tgt)
        flash = box(f"{wtag} hit", (-0.12, -0.12, 0.0), (0.12, 0.12, 0.01), HIT, loc=(tip_hit.x, tip_hit.y, tz))
    else:
        ty = tip_hit.y + 0.03
        top = min(1.8, max(0.6, tip_hit.z + 0.2))
        tgt = link(bpy.data.objects.new(f"{wtag} mob pivot", None)); tgt.location = (tip_hit.x, ty, 0)
        hb_ = [((-0.22, 0, 0), (0.22, 0.35, top - 0.3), DUMMY), ((-0.15, 0.03, top - 0.3), (0.15, 0.33, top), DUMMYH)]
        multibox(f"{wtag} mob", hb_, tgt, np.array((0.0, 0.17, 0.0)))
        flash = box(f"{wtag} hit", (-0.18, -0.03, -0.18), (0.18, 0.0, 0.18), HIT,
                    loc=(tip_hit.x, ty, min(top - 0.2, max(0.25, tip_hit.z))))
    tgt.rotation_mode = "XYZ"
    tgt_home = Vector(tgt.location)
    # ---- rig: body (eye) -> camera + shoulder -> grip -> tool root
    body = link(bpy.data.objects.new(f"{tag} body", None)); body.location = eye0
    sh, grip, ring_pt = make_arm(tag, body)
    root = link(bpy.data.objects.new(f"{tag} tool", None)); root.parent = grip; root.rotation_mode = "XYZ"
    reach_kind = S["extra"].get("reach")
    head = None
    if reach_kind:
        head = link(bpy.data.objects.new(f"{tag} tool head", None)); head.parent = root
    ticks = []
    hit_frames = []
    for t, p in enumerate(poses):
        pitch, yaw, roll, tilt, reach = p
        e_, _ = arm_matrix(p)
        sh.rotation_euler = e_; sh.keyframe_insert("rotation_euler", frame=t + 1)
        key(sh, t + 1, loc=tuple(SH_LOCAL + Vector((0, reach, 0))))
        key(grip, t + 1, rot=(R(-tilt), 0, 0))
        if bpts or S["hop"]:
            key(body, t + 1, loc=tuple(eye0 + offs[t]))
        k_ = kk_of(t)
        hit_now = k_ is not None and k_ in hits
        if hit_now:
            hit_frames.append(t + 1)
        ticks.append({"arm": [round(pitch, 2), round(yaw, 2), round(roll, 2)], "tool_tilt": round(tilt, 2),
                      "reach": round(reach, 3), "hit": hit_now, "body": [round(offs[t].y, 3), round(offs[t].z, 3)],
                      "extend": round(ext_t[t], 3)})
        if t == 0 or hit_now or ticks[t - 1]["hit"]:
            flash.hide_render = not hit_now; flash.keyframe_insert("hide_render", frame=t + 1)
            flash.hide_viewport = not hit_now; flash.keyframe_insert("hide_viewport", frame=t + 1)
    # ---- the mob / block reacts on contact: knocked back along the swing and tilted, back on its feet after
    for hi_, f in enumerate(hit_frames):
        t = f - 1
        gap = (hit_frames[hi_ + 1] - f) if hi_ + 1 < len(hit_frames) else 99
        v = far_world[min(total, t + 1)] - far_world[max(0, t - 1)]
        d = Vector((v.x, max(v.y, 0.0) + 0.6 * v.length + 0.3, 0))
        d.normalize()
        if blocky:
            key(tgt, f - 1, sc=1.0); key(tgt, f + 1, sc=(1.04, 1.04, 0.94)); key(tgt, f + 3, sc=1.0)
            continue
        kn = S["knock"]
        react = S["extra"].get("react")
        ax = Vector((0, 0, 1)).cross(d)
        e_tilt = Matrix.Rotation(R(22), 3, ax).to_euler("XYZ")
        nxt = f + swing + GAP - 2 if plays > 1 else total + 1   # back on its feet before the next play's hit
        if react in ("push", "pull"):                # the mob rides the point / is hooked by the head
            t_end = FORM + (t - FORM) // (swing + GAP) * (swing + GAP) + S["extra"][react + "_to"]
            key(tgt, f - 1, loc=tuple(tgt_home), rot=(0, 0, 0))
            for t_ in range(t, t_end + 1):
                dv = far_world[t_] - tip_hit
                dv.z = 0.0
                w = min(1.0, (t_ - t + 1) / 2)
                key(tgt, t_ + 1, loc=tuple(tgt_home + dv), rot=tuple(Matrix.Rotation(R(22) * w, 3, ax).to_euler("XYZ")))
            dv = far_world[t_end] - tip_hit; dv.z = 0.0
            last = tgt_home + dv
            fling = (dv.normalized() if dv.length > 0.05 else d) * (0.6 if react == "push" else 0.4)
            key(tgt, t_end + 4, loc=tuple(last + fling), rot=tuple(Matrix.Rotation(R(12), 3, ax).to_euler("XYZ")))
            key(tgt, min(nxt, t_end + 10), loc=tuple(tgt_home), rot=(0, 0, 0))
            continue
        if react == "crush":                         # squashed under the head, knocked back, springs up
            key(tgt, f - 1, loc=tuple(tgt_home), rot=(0, 0, 0), sc=1.0)
            key(tgt, f + 1, loc=tuple(tgt_home + d * 0.25), rot=tuple(e_tilt), sc=(1.18, 1.18, 0.55))
            key(tgt, f + 4, loc=tuple(tgt_home + d * kn * 0.8), rot=tuple(e_tilt), sc=(1.06, 1.06, 0.82))
            key(tgt, f + 8, loc=tuple(tgt_home + d * kn), rot=(0, 0, 0), sc=1.0)
            key(tgt, min(nxt, f + 13), loc=tuple(tgt_home), rot=(0, 0, 0), sc=1.0)
            continue
        if react == "skid":                          # driven back 3 blocks, feet skidding, leaning back
            key(tgt, f - 1, loc=tuple(tgt_home), rot=(0, 0, 0))
            for q, (dd, ang) in enumerate(((0.9, 26), (1.8, 24), (2.5, 18), (2.85, 10), (3.0, 4))):
                key(tgt, f + 1 + 2 * q, loc=tuple(tgt_home + Vector((0, 1, 0)) * dd),
                    rot=tuple(Matrix.Rotation(R(ang), 3, Vector((1, 0, 0))).to_euler("XYZ")))
            key(tgt, f + 14, loc=tuple(tgt_home + Vector((0, 3.0, 0))), rot=(0, 0, 0))
            continue
        if react == "spin":                          # spun round once and knocked back
            key(tgt, f - 1, loc=tuple(tgt_home), rot=(0, 0, 0))
            for q in range(1, 6):
                w = q / 5
                key(tgt, f + 2 * q - 1, loc=tuple(tgt_home + Vector((0.4 * w, 2.2 * math.sqrt(w), 0))),
                    rot=(R(14 * (1 - w)), 0, R(-360 * math.sqrt(w))))
            key(tgt, f + 14, loc=tuple(tgt_home + Vector((0.45, 2.3, 0))), rot=(0, 0, R(-360)))
            continue
        ax = Vector((0, 0, 1)).cross(d)
        tilt_r = R(28 if kn > 1.5 else 18)
        e_tilt = Matrix.Rotation(tilt_r, 3, ax).to_euler("XYZ")
        e_half = Matrix.Rotation(tilt_r * 0.35, 3, ax).to_euler("XYZ")
        key(tgt, f - 1, loc=tuple(tgt_home), rot=(0, 0, 0))
        key(tgt, f + 1, loc=tuple(tgt_home + d * kn * 0.7), rot=tuple(e_tilt))
        if gap < 7:                                    # the next hit comes quickly: back on its feet just before it
            key(tgt, f + gap - 1, loc=tuple(tgt_home), rot=(0, 0, 0))
            continue
        key(tgt, f + 3, loc=tuple(tgt_home + d * kn), rot=tuple(e_half))
        back = f + (6 if plays > 1 else 12)
        if plays > 1 or kn < 2:
            key(tgt, back, loc=tuple(tgt_home), rot=(0, 0, 0))
        else:
            key(tgt, back, loc=tuple(tgt_home + d * kn * 1.05), rot=(0, 0, 0))
    # ---- the working edge leads (twist solved above, before the world)
    for t in range(total + 1):
        key(root, t + 1, rot=(0, phis[t], 0))
        ticks[t]["tool_twist"] = round(math.degrees(phis[t]), 2)
    # ---- the tool, in sections along its length (grip first); hammer heads ride a slider when the take reaches out
    NB = 7
    bands = [[] for _ in range(NB)]
    for a, b, m in bxs:
        bands[min(NB - 1, int(((a[1] + b[1]) / 2) / span * NB))].append((a, b, m))
    parts = []
    for k, bl in enumerate(bands):
        if not bl:
            continue
        lo = np.min([a for a, _, _ in bl], 0); hi = np.max([b for _, b, _ in bl], 0)
        c = (lo + hi) / 2
        par = head if (head is not None and c[1] > 0.5) else root
        parts.append((multibox(f"{tag} tool part {k}", bl, par, c), c))
    lo_x = min(float(a[0]) for a, _, _ in bxs); hi_x = max(float(b[0]) for _, b, _ in bxs)
    lo_z = min(float(a[2]) for a, _, _ in bxs); hi_z = max(float(b[2]) for _, b, _ in bxs)
    # reach-out pieces (H2a1 telescope, H2a2 chain)
    if head is not None:
        arc = S["extra"].get("arc", 0.0)          # H2a21: the thrown head swings wide on the way out and back
        head_x = [0.0] * (total + 1)
        if arc:
            emax = max(ext_t) or 1.0
            for t in range(1, total + 1):
                out_ = ext_t[t] >= ext_t[t - 1]
                head_x[t] = arc * math.sin(math.pi * ext_t[t] / emax) * (1 if out_ else -0.6)
        for t in range(total + 1):
            key(head, t + 1, loc=(head_x[t], ext_t[t], 0))
        if reach_kind == "telescope":
            sleeves = []
            for i, (w_, m_) in enumerate(((0.045, GLASS), (0.037, GLOW), (0.03, GRIP))):
                s_ = box(f"{tag} tool sleeve {i}", (-w_, 0, -w_), (w_, 1.0, w_), m_, root, loc=(0, 0.56, 0))
                sleeves.append(s_)
            for t in range(total + 1):
                e = ext_t[t]
                for i, s_ in enumerate(sleeves):                 # nested sleeves, thinner ones reach further
                    key(s_, t + 1, sc=(1, e * (i + 1) / 3 + 0.04, 1) if e > 0.01 else 0.0001)
        else:
            NL = 14
            lk = [box(f"{tag} tool chain {i}", (-0.025, -0.025, -0.025), (0.025, 0.025, 0.025), RIM if i % 2 else GLOW, root)
                  for i in range(NL)]
            for t in range(total + 1):
                e = ext_t[t]
                hx = head_x[t]
                for i, o in enumerate(lk):
                    fr = (i + 0.5) / NL
                    sag = -math.sin(fr * math.pi) * 0.12 * e / 4
                    key(o, t + 1, loc=(sag * 0.4 + hx * math.sin(fr * math.pi / 2), 0.6 + e * fr, sag),
                        sc=1.0 if e > 0.08 else 0.0001)
    # ---- charge before the big swings: a green shell over the tool and a ring flare
    if S["charge"]:
        shell = box(f"{tag} charge shell", (lo_x - 0.02, -0.02, lo_z - 0.02), (hi_x + 0.02, span + 0.03, hi_z + 0.02), CHG, root)
        flare = box(f"{tag} ring flare", (-0.025, -0.025, -0.025), (0.025, 0.025, 0.025), PIX, sh, loc=tuple(ring_pt))
        rng_c = np.random.default_rng(852 + bi * 7)
        motes = [box(f"{tag} charge mote {i}", (-0.012, -0.012, -0.012), (0.012, 0.012, 0.012), PIX, root) for i in range(6)]
        for t in range(total + 1):
            k_ = kk_of(t)
            on = k_ is not None and any(a_ <= k_ <= b_ for a_, b_ in S["charge"])
            if on:
                a_, b_ = next((a_, b_) for a_, b_ in S["charge"] if a_ <= k_ <= b_)
                w = (k_ - a_) / max(1, b_ - a_)
                s_ = 0.85 + 0.15 * w + (0.03 if t % 2 else -0.03)
                key(shell, t + 1, sc=(s_, 1.0, s_)); key(flare, t + 1, sc=1.0 + 1.2 * w)
            else:
                key(shell, t + 1, sc=0.0001); key(flare, t + 1, sc=0.0001)
            for i, o in enumerate(motes):
                if on:
                    ph = (t * 0.45 + i * 1.05)
                    r_ = 0.16 * (1 - ((t + i) % 4) / 4)
                    key(o, t + 1, loc=(r_ * math.cos(ph), span * (0.35 + 0.1 * i), r_ * math.sin(ph)), sc=1.0)
                else:
                    key(o, t + 1, loc=(0, span * 0.5, 0), sc=0.0001)
    # ---- impact extras: hammer shockwave ring, chips / dirt for blocks, a dirt load that flies on the toss
    if S["extra"].get("wave"):
        ring_boxes = []
        for i in range(20):
            a = 2 * math.pi * i / 20
            cx, cy = math.cos(a), math.sin(a)
            ring_boxes.append(((cx - 0.09, cy - 0.09, 0.0), (cx + 0.09, cy + 0.09, 0.05), WAVE))
        wv = multibox(f"{wtag} shockwave", ring_boxes, None, np.zeros(3))
        wv.location = (tip_hit.x, tip_hit.y + 0.15, 0.01)
        key(wv, 1, sc=0.0001)
        wmode = S["extra"]["wave"]
        rings = [wv]
        offs_w = [0] if wmode in (True, "line") else [0, 3] if wmode == "double" else [0, 3, 6]
        for i in range(1, len(offs_w)):
            w2 = multibox(f"{wtag} shockwave {i}", ring_boxes, None, np.zeros(3)); w2.location = wv.location
            key(w2, 1, sc=0.0001); rings.append(w2)
        for f in hit_frames:
            for w_o, o_ in zip(offs_w, rings):
                g = f + w_o; sz = 1.0 + 0.35 * (w_o // 3)
                key(o_, g - 1, sc=0.0001); key(o_, g, sc=(0.25 * sz, 0.25 * sz, 1)); key(o_, g + 3, sc=(1.2 * sz, 1.2 * sz, 1))
                key(o_, g + 5, sc=(1.7 * sz, 1.7 * sz, 0.4)); key(o_, g + 6, sc=0.0001)
        if wmode == "line":                          # a crack runs out ahead from the impact, a segment a tick
            fwd_ = Vector((tip_hit.x - eye0.x, tip_hit.y - eye0.y, 0)).normalized()
            segs = []
            for i in range(10):
                c_ = Vector((tip_hit.x, tip_hit.y + 0.15, 0.012)) + fwd_ * (0.35 * i + 0.2)
                sg = box(f"{wtag} crack {i}", (-0.06, -0.18, 0), (0.06, 0.18, 0.02), WAVE, loc=tuple(c_))
                sg.rotation_euler = (0, 0, math.atan2(-fwd_.x, fwd_.y) + R(18 if i % 2 else -18))
                segs.append(sg)
                key(sg, 1, sc=0.0001)
            for f in hit_frames:
                for i, sg in enumerate(segs):
                    g = f + i // 2
                    key(sg, g - 1, sc=0.0001); key(sg, g, sc=1.0)
                    key(sg, f + 9, sc=1.0); key(sg, f + 11, sc=0.0001)
    if blocky:
        rng_d = np.random.default_rng(900 + bi)
        top_z = tgt.children[0].dimensions.z if tgt.children else 0.5
        for hf_i, f in enumerate(hit_frames):
            for j in range(5):
                ch = box(f"{wtag} chip {hf_i}.{j}", (-0.035, -0.035, -0.035), (0.035, 0.035, 0.035),
                         DIRT if tool == "shovel" else STONE)
                p0 = Vector((tip_hit.x, tip_hit.y, max(0.25, tip_hit.z - (0.0 if aim else 0.03)))) + Vector(rng_d.uniform(-0.06, 0.06, 3))
                vel = Vector((rng_d.uniform(-1.4, 1.4), rng_d.uniform(-1.6, -0.4), rng_d.uniform(1.6, 2.8)))
                key(ch, 1, loc=tuple(p0), sc=0.0001); key(ch, f - 1, loc=tuple(p0), sc=0.0001)
                for s in range(0, 9):
                    tt = s / 20.0
                    pp = p0 + vel * tt + Vector((0, 0, -9.8 * tt * tt / 2))
                    pp.z = max(0.03, pp.z)
                    key(ch, f + s, loc=tuple(pp), sc=1.0 if s < 8 else 0.0001)
        if S["extra"].get("chunk") or S["extra"].get("toss"):
            kt = S["extra"].get("chunk") or S["extra"].get("toss")
            lump = box(f"{wtag} load", (-0.08, -0.08, -0.05), (0.08, 0.08, 0.06), DIRT if tool == "shovel" else STONE)
            key(lump, 1, loc=tuple(tip_hit), sc=0.0001)
            for pl in range(plays):
                base_t = FORM + pl * (swing + GAP)
                h0 = base_t + S["main"]
                key(lump, h0, loc=tuple(far_world[h0] + Vector((0, -0.05, 0.02))), sc=0.0001)
                for t in range(h0, base_t + kt + 1):
                    p_ = eye0 + offs[t] + mats_[t] @ Vector((0, span * 0.8, 0.05))
                    key(lump, t + 1, loc=tuple(p_), sc=1.0)
                t0 = base_t + kt
                p0 = eye0 + offs[t0] + mats_[t0] @ Vector((0, span * 0.8, 0.05))
                vth = (far_world[t0] - far_world[t0 - 1]) * 20 * 0.6 + Vector((0, 0, 1.0))
                for s in range(1, 8):
                    tt = s / 20.0
                    pp = p0 + vth * tt + Vector((0, 0, -9.8 * tt * tt / 2))
                    pp.z = max(0.04, pp.z)
                    key(lump, t0 + 1 + s, loc=tuple(pp), sc=1.0 if s < 7 else 0.0001)
    # ---- forming (ticks 0-14), nine ways
    rng = np.random.default_rng(852 + bi)
    m_rest = grip_matrix(REST[3])                     # tool space -> shoulder space during forming (twist 0)
    fam, var = build[0], build[1]
    if fam == "a":
        pm = bpy.data.meshes.new(f"{tag} px"); s_ = 0.022
        pm.from_pydata([(x, y, z) for x in (-s_, s_) for y in (-s_, s_) for z in (-s_, s_)], [], BOXF)
        pm.materials.append(PIX)
        for o, c in parts:
            frac = c[1] / span
            if var == "3":
                frac = 1 - frac                       # tip first
            f_arrive = 3 + int(round(frac * (FORM - 5)))
            if var == "5":                            # a5: the cloud gathers, then every section pops in close together
                f_arrive = 9 + int(round(frac * 3))
            if var in "37":
                key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive, sc=1.35); key(o, f_arrive + 2, sc=1.0)
            else:
                key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive + 1, sc=1.0)
            for j in range(3):
                px_ = link(bpy.data.objects.new(f"{tag} pixel", pm)); px_.parent = sh
                end = m_rest @ Vector(c + rng.uniform(-0.03, 0.03, 3))
                if var == "4":                        # a4: a ribbon winds round the tool's length from the grip to the part
                    hel = [m_rest @ Vector((0.07 * math.cos(q * 2.4 + j * 2.1), c[1] * q / 3, 0.07 * math.sin(q * 2.4 + j * 2.1)))
                           for q in range(4)]
                    f0 = max(1, f_arrive - 5 + j)
                    key(px_, 1, loc=hel[0], sc=0.0001); key(px_, f0, loc=hel[0], sc=0.0001)
                    for q in range(1, 4):
                        key(px_, f0 + q, loc=hel[q], sc=1.0)
                    key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
                elif var == "5":                      # a5: a loose cloud round the fist drifts in
                    dv = Vector(rng.normal(0, 1, 3)).normalized() * rng.uniform(0.22, 0.34)
                    st = ring_pt + dv
                    key(px_, 1, loc=st, sc=0.0001); key(px_, 2 + j, loc=st, sc=0.0001); key(px_, 3 + j, loc=st, sc=0.8)
                    key(px_, 6 + j, loc=st * 0.7 + end * 0.3 + Vector((0, 0, 0.02)), sc=1.0)
                    key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
                elif var == "6":                      # a6: two strands spiral up the forearm the opposite ways
                    sg = 1 if j % 2 == 0 else -1
                    th = rng.uniform(0, 2 * math.pi)
                    hel = [Vector((0.08 * math.cos(th + sg * q * 2.1), 0.08 * math.sin(th + sg * q * 2.1), -0.08 - 0.12 * q))
                           for q in range(4)]
                    f0 = max(1, f_arrive - 6 + j)
                    key(px_, 1, loc=hel[0], sc=0.0001); key(px_, f0, loc=hel[0], sc=0.0001)
                    for q in range(4):
                        key(px_, f0 + 1 + q, loc=hel[q], sc=1.0)
                    key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
                elif var == "7":                      # a7: from the shoulder down the arm, the section flashes in on arrival
                    th = rng.uniform(0, 2 * math.pi)
                    hel = [Vector((0.07 * math.cos(th - q * 2.0), 0.07 * math.sin(th - q * 2.0), 0.02 - 0.22 * q)) for q in range(4)]
                    f0 = max(1, f_arrive - 6 + j)
                    key(px_, 1, loc=hel[0], sc=0.0001); key(px_, f0, loc=hel[0], sc=0.0001)
                    for q in range(4):
                        key(px_, f0 + 1 + q, loc=hel[q], sc=1.0)
                    key(px_, f_arrive, loc=end, sc=0.5); key(px_, f_arrive + 1, loc=end, sc=0.0001)
                elif var == "2":                      # spiral up the forearm from the elbow, then out to the part
                    th = rng.uniform(0, 2 * math.pi)
                    hel = [Vector((0.08 * math.cos(th + q * 2.1), 0.08 * math.sin(th + q * 2.1), -0.12 - 0.2 * q)) for q in range(3)]
                    f0 = max(1, f_arrive - 6 + j)
                    key(px_, 1, loc=hel[0], sc=0.0001); key(px_, f0, loc=hel[0], sc=0.0001)
                    key(px_, f0 + 1, loc=hel[0], sc=1.0); key(px_, f0 + 2, loc=hel[1], sc=1.0); key(px_, f0 + 3, loc=hel[2], sc=1.0)
                    key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
                else:
                    start = ring_pt + Vector(rng.uniform(-0.015, 0.015, 3))
                    f0 = max(1, f_arrive - (2 if var == "3" else 4) + j - 1)
                    key(px_, 1, loc=start, sc=0.0001); key(px_, f0, loc=start, sc=0.0001); key(px_, f0 + 1, loc=start, sc=1.0)
                    if var == "1":
                        key(px_, f0 + 3, loc=(start + end) / 2 + Vector((0, 0.03, -0.03)), sc=1.0)
                    key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
    elif fam == "b":
        if var == "1":                                # 844: behind a scan plate
            key(root, 1, sc=(1, 0.001, 1)); key(root, 3, sc=(1, 0.001, 1)); key(root, FORM, sc=(1, 1, 1))
            sp = box(f"{tag} scan plate", (-0.11, -0.006, -0.06), (0.11, 0.006, 0.06), SCAN, root)
            sw = (hi_x - lo_x) / 0.22 + 0.2
            sp.location = ((hi_x + lo_x) / 2, span, 0)
            key(sp, 1, sc=0.0001); key(sp, 3, sc=(sw, 1, 1)); key(sp, FORM, sc=(sw, 1, 1)); key(sp, FORM + 2, sc=0.0001)
        elif var == "2":                              # guide beam first, then the tool grows behind a bright edge
            gb = box(f"{tag} guide beam", (-0.007, 0, -0.007), (0.007, span, 0.007), BEAM, grip)
            key(gb, 1, sc=(1, 0.001, 1)); key(gb, 4, sc=(1, 1, 1)); key(gb, FORM, sc=(1, 1, 1)); key(gb, FORM + 1, sc=0.0001)
            key(root, 1, sc=(1, 0.001, 1)); key(root, 5, sc=(1, 0.001, 1)); key(root, FORM, sc=(1, 1, 1))
            ew = 0.012
            edge = [((lo_x - ew, -0.004, lo_z - ew), (hi_x + ew, 0.004, lo_z)), ((lo_x - ew, -0.004, hi_z), (hi_x + ew, 0.004, hi_z + ew)),
                    ((lo_x - ew, -0.004, lo_z), (lo_x, 0.004, hi_z)), ((hi_x, -0.004, lo_z), (hi_x + ew, 0.004, hi_z))]
            eo = multibox(f"{tag} build edge", [(a, b, BEAM) for a, b in edge], grip, np.zeros(3))
            for t in range(1, FORM + 3):
                s = 0.0 if t <= 5 else min(1.0, smooth((t - 5) / (FORM - 5)))
                key(eo, t, loc=(0, span * max(s, 0.001), 0), sc=1.0 if 5 <= t <= FORM else 0.0001)
            for j in range(6):
                spk = box(f"{tag} spark {j}", (-0.01, -0.01, -0.01), (0.01, 0.01, 0.01), PIX, grip)
                f0 = 6 + j
                s = smooth((f0 - 5) / (FORM - 5)); p0 = Vector((rng.uniform(lo_x, hi_x), span * s, 0))
                dv = Vector((rng.uniform(-1, 1), rng.uniform(-0.3, 0.6), rng.uniform(-1, 1))).normalized() * 0.18
                key(spk, 1, loc=p0, sc=0.0001); key(spk, f0, loc=p0, sc=0.0001); key(spk, f0 + 1, loc=p0, sc=1.0)
                key(spk, f0 + 3, loc=p0 + dv, sc=0.6); key(spk, f0 + 4, loc=p0 + dv * 1.2, sc=0.0001)
        elif var in "45":                             # b4: one plate sweeps tip to grip; b5: two plates meet in the middle
            sw = (hi_x - lo_x) / 0.22 + 0.2
            plates = []
            for pi_ in range(1 if var == "4" else 2):
                sp = box(f"{tag} scan plate {pi_}", (-0.11, -0.006, -0.06), (0.11, 0.006, 0.06), SCAN, root)
                plates.append(sp)
            def plate_y(pi_, fr_):
                if var == "4":
                    return span * (1 - fr_)
                return span * 0.5 * fr_ if pi_ == 0 else span * (1 - 0.5 * fr_)
            for t in range(1, FORM + 3):
                fr_ = 0.0 if t <= 3 else min(1.0, (t - 3) / (FORM - 3))
                for pi_, sp in enumerate(plates):
                    key(sp, t, loc=((hi_x + lo_x) / 2, plate_y(pi_, fr_), 0), sc=(sw, 1, 1) if 3 <= t <= FORM else 0.0001)
            for o, c in parts:
                cy = c[1] / span
                if var == "4":
                    fr_ = 1 - cy
                else:
                    fr_ = (cy / 0.5) if cy < 0.5 else ((1 - cy) / 0.5)
                f_on = 3 + int(round(fr_ * (FORM - 3)))
                key(o, 1, sc=0.0001); key(o, max(2, f_on - 1), sc=0.0001); key(o, f_on, sc=(1, 0.5, 1)); key(o, f_on + 1, sc=1.0)
        else:                                         # four clicks
            steps = [(1, 0.001), (3, 0.001), (4, 0.28), (6, 0.28), (7, 0.52), (9, 0.52), (10, 0.76), (12, 0.76), (13, 1.0)]
            for f, s in steps:
                key(root, f, sc=(1, s, 1))
            for i, (f, s) in enumerate(steps[2::2]):
                cl = box(f"{tag} click {i}", (lo_x - 0.02, -0.006, lo_z - 0.02), (hi_x + 0.02, 0.006, hi_z + 0.02), RIM, grip,
                         loc=(0, span * s, 0))
                key(cl, 1, sc=0.0001); key(cl, f - 1, sc=0.0001); key(cl, f, sc=1.0); key(cl, f + 1, sc=0.0001)
    else:
        homes = []
        for i, (o, c) in enumerate(parts):
            f_lock = 4 + int(round((c[1] / span) * (FORM - 6)))
            home = Vector(c); o.rotation_mode = "XYZ"
            if var == "1":                            # 844: fly in and snap
                off = Vector(rng.uniform(-1, 1, 3)); off.y = abs(off.y) * 0.5; off = off.normalized() * 0.35
                key(o, 1, loc=home + off, sc=0.0001); key(o, max(2, f_lock - 4), loc=home + off, sc=0.0001)
                key(o, max(3, f_lock - 3), loc=home + off, sc=0.6); key(o, f_lock, loc=home, sc=1.0)
                key(o, max(3, f_lock - 3), rot=(R(rng.uniform(-60, 60)), R(rng.uniform(-60, 60)), R(rng.uniform(-60, 60))))
                key(o, f_lock, rot=(0, 0, 0))
            elif var == "2":                          # unfold out of the grip, one after another
                start = Vector((home.x, 0.05, home.z))
                key(o, 1, loc=start, sc=0.0001, rot=(R(180), 0, 0)); key(o, max(2, f_lock - 3), loc=start, sc=0.0001, rot=(R(180), 0, 0))
                key(o, max(3, f_lock - 2), loc=start, sc=0.8, rot=(R(160), 0, 0))
                key(o, f_lock, loc=home, sc=1.0, rot=(0, 0, 0))
            else:                                     # orbit the fist, spiral in
                th0 = 2 * math.pi * i / max(1, len(parts))
                orb = [Vector((0.34 * math.cos(th0 + q), home.y * 0.6, 0.34 * math.sin(th0 + q))) for q in (0, 1.6, 3.2)]
                f0 = max(2, f_lock - 5)
                key(o, 1, loc=orb[0], sc=0.0001); key(o, f0, loc=orb[0], sc=0.0001)
                key(o, f0 + 1, loc=orb[0], sc=0.7); key(o, f0 + 2, loc=orb[1], sc=0.8)
                key(o, f0 + 3, loc=orb[2] * 0.6 + home * 0.4, sc=0.9); key(o, f_lock, loc=home, sc=1.0)
    # ---- record
    t_main = FORM + S["main"]
    MODEL_AT[tk] = t_main + 1
    vis_far = eye_angles(mats_[t_main] @ Vector((0, span, 0)))
    vis_grip = eye_angles(mats_[t_main] @ Vector((0, 0.1, 0)))
    dump["takes"][tk] = {"name": name, "tool": tool, "build": BUILD_NAME[build], "forming_ticks": FORM, "swing_ticks": swing,
                         "plays": plays, "hit_ticks": hits, "charge_ticks": S["charge"], "keys": [list(k) for k in keys],
                         "ticks": ticks}
    # ---- cameras: the eye (moves with the body), and from the right
    c = cam(f"Cam {tk}", (0, 0, 0), (0, 3, -0.25), 10.4)
    c.parent = body
    c.data.sensor_fit = "HORIZONTAL"; c.data.sensor_width = 36.0
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        box(f"FT6 {tk} crosshair {nm_}", a_, b_, XH, c)
    if long_bay and DASH > 0 and bpts and bpts[-1][1] > 5:
        cam(f"Cam {tk} side", (bx + 11.0, 5.5, 3.0), (bx, 6.5, 0.9), 18)
    elif long_bay or S["ext"]:
        cam(f"Cam {tk} side", (bx + 5.5, 2.0, 2.2), (bx + 0.2, 2.2, 0.9), 24)
    else:
        cam(f"Cam {tk} side", tuple(eye0 + Vector((3.2, 0.9, 0.2))), tuple(eye0 + Vector((0.3, 0.6, -0.3))), 35)
    cu = bpy.data.curves.new("FT6 label " + tk, "FONT"); cu.body = f"{tk}  {name}  ({BUILD_NAME[build]})"
    cu.size = 0.11; cu.align_x = "RIGHT"
    tl = link(bpy.data.objects.new("FT6 label " + tk, cu)); tl.location = (bx - 5.95, -0.3, 2.3); tl.rotation_euler = (R(90), 0, R(90))   # behind the eye: side camera only
    tl.data.materials.append(GLOW)
    S["total"] = total
    print(tk, name, "| build", build, "| frames 1 -", total + 1, "| main hit frame", t_main + 1, "| far end at",
          tuple(round(x - y, 2) for x, y in zip(tip_hit, (bx, 0, 0))), "| far end / grip in view (deg right, up)", vis_far,
          vis_grip, "| aim point" if tk in AIM_PT else "", AIM_PT.get(tk, ""), flush=True)

with open(os.path.join(FOLDER, "combat", "fp_tools6_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
with open(os.path.join(FOLDER, "combat", "fp_tools6_takes.json"), "w") as fh:
    json.dump({tk: {"frames": [1, T[tk]["total"] + 1], "model_at": MODEL_AT[tk], "hits": T[tk]["hits"],
                    "plays": T[tk]["plays"], "build": T[tk]["build"], "name": T[tk]["name"], "parent": T[tk]["parent"],
                    "note": T[tk]["note"], "swing": T[tk]["keys"][-1][0], "charge": T[tk]["charge"],
                    "tool": T[tk]["tool"], "prime_deg": T[tk].get("prime_deg"), "prime_pose": T[tk].get("prime_pose")} for tk in ORDER}, fh, indent=1)

scene.frame_start, scene.frame_end = 1, max(T[t]["total"] + 1 for t in ORDER)
world = bpy.data.worlds.new("FT6 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.42, 0.55, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("FT6 sun", bpy.data.lights.new("FT6 sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(45), R(-10), R(-30))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("FT6 Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm_, val in (("Size", 0.5), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm_ in gl.inputs:
            gl.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects["Cam S4b11"]
scene.frame_set(MODEL_AT["S4b11"])
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
