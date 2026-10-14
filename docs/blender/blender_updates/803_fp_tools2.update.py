# Pass 803: first-person construct tool animations, round 2 (Chat C, 2026-10-14, range 800-899).
# J on 802: "A1 axe chop is not very controlled and it hits at an angle inconsistent with the blade; the hammer is also
# not the construct version, its also facing the wrong way and is flat which doesnt work as a hammer ... hammer from the
# side might be closer when the hammer is no longer 2d; pickaxe is also used incorrectly; the sword slash is almost fine
# but i need a combination / mix up; the sword heavy chop S2 should also be a diagonal swing more than straight down ...
# if the blade was held properly instead of hiding with the side of the blade instead of the edge; S3 is closer to good
# the sweep pair; sword thrust is a poor thrust animation it needs to be brought back then forward not pressed down not
# on the blade edge even; shovel also done poorly. generate new animations per in this format."
# The fix that runs through every take: the working edge LEADS. Each tick the tool turns about its own length so its
# edge (sword), point (pickaxe), blade (axe, hoe) or striking face (hammer) faces the way the tool is moving (computed
# from the tool tip's actual motion); the thrust and the shovel hold a fixed turn (edge upright / blade flat).
# The hammer is the construct hammer now: a solid block head with depth (as in Hammer mode, pass 503), glowing faces.
# Arms can reach: the shoulder moves forward and back (pull back, then drive forward).
#   S1 sword slash (kept, edge-true)            S2 sword diagonal chop, upper right to lower left
#   S3 sword sweep pair (kept, edge-true)        S4 sword thrust: drawn back, then a straight stab, edge upright
#   C1 sword combo: slash, backhand, diagonal chop (three hits)
#   C2 sword combo: sweep, then draw back and thrust (two hits)
#   P1 pickaxe: raised, point-first strike into the block, bounce
#   A1 axe: a controlled diagonal chop, blade leading, a short recoil
#   V1 shovel: blade flat, drive into the ground ahead, lever back, lift and flick
#   O1 hoe: raise, hook the blade into the ground ahead, drag it back toward you
#   H1 hammer overhead: raised high, held, face-first smash   H2 hammer from the side: flat swing into a wall
# Cameras "Cam <take>" (first person), "Cam <take> side", "Cam all". Writes LanternLive\combat\fp_tools2_poses.json
# and builds LanternLive\combat\fp_tools2.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector

R = math.radians
OUT = os.path.join(FOLDER, "combat", "fp_tools2.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
BB = os.path.join(FOLDER, "kl_assets")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("FP Tools 2")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("FP Tools 2")
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
FORM = 14                 # forming ticks
GAP = 6                   # rest ticks between the two swings


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


SKIN = mat("FP skin", (0.62, 0.42, 0.3)); SLEEVE = mat("FP sleeve", (0.04, 0.28, 0.12))
RINGM = mat("FP ring", (0.12, 1.0, 0.3), emit=4.0); GOLDM = mat("FP ring gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0)
GLASS = mat("FP hard-light glass", (0.05, 0.55, 0.22), emit=0.9, alpha=0.62, rough=0.15)
GLOW = mat("FP construct glow", (0.12, 1.0, 0.35), emit=4.5)
RIM = mat("FP construct rim", (0.25, 1.0, 0.45), emit=6.0)
GRIP = mat("FP construct grip", (0.02, 0.2, 0.08), emit=0.6, rough=0.3)
PIX = mat("FP forming pixel", (0.2, 1.0, 0.4), emit=5.0)
FLOOR = mat("FP floor", (0.18, 0.2, 0.22), rough=0.9)
STONE = mat("FP block", (0.32, 0.33, 0.35), rough=0.9)
DUMMY = mat("FP dummy", (0.25, 0.45, 0.25), rough=0.8)
HIT = mat("FP hit flash", (1.0, 0.25, 0.2), emit=3.0)


def box(name, a, b, m, parent=None):
    a = np.array(a, float); b = np.array(b, float)
    v = [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me))
    if parent is not None:
        o.parent = parent
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


# ------------------------------------------------------------------ swings: (tick, arm pitch, yaw, roll, tool tilt)
# Arm angles in degrees: pitch 90 = straight ahead, >90 raised, <90 lowered; yaw + = toward the left; roll twists the
# forearm; tool tilt leans the tool forward (+) or back (-) in the fist. Ease between keys.
REST = (96, 14, 0, 22, 0.0)
# (tick, arm pitch, yaw, roll, tool tilt, reach m); take: (name, tool, keys, hit ticks, blade side, fixed twists)
# blade side: +1 the working edge is on the tool's +X, -1 on -X, 0 both (sword, pickaxe, hammer)
# fixed twists: [(from tick, to tick, degrees)] where the turn is held instead of following the motion
SWINGS = {
    "S1": ("Sword slash", "sword", [(0, *REST), (2, 125, -18, -25, 40, 0), (5, 70, 32, 35, 70, 0.05), (8, *REST)], [4], 0, []),
    "S2": ("Sword diagonal chop", "sword", [(0, *REST), (5, 140, -30, -35, -20, -0.05), (8, 144, -32, -38, -28, -0.06),
                                            (11, 60, 30, 30, 80, 0.08), (13, 55, 34, 32, 85, 0.08), (16, *REST)], [11], 0, []),
    "S3": ("Sword sweep pair", "sword", [(0, *REST), (3, 96, -45, -80, 60, 0), (6, 92, 50, -80, 60, 0.04), (8, 94, 52, 100, 60, 0),
                                         (11, 94, -40, 100, 60, 0.04), (14, *REST)], [5, 10], 0, []),
    "S4": ("Sword thrust", "sword", [(0, *REST), (4, 92, 8, 0, 88, -0.22), (6, 95, 2, 0, 90, -0.24), (8, 93, 0, 0, 90, 0.34),
                                     (10, 93, 0, 0, 90, 0.32), (14, *REST)], [8], 0, [(2, 12, 90)]),
    "C1": ("Sword combo: slash, backhand, chop", "sword", [(0, *REST), (2, 125, -18, -25, 40, 0), (5, 72, 32, 35, 70, 0.05),
                                                           (7, 80, 40, 30, 60, 0), (10, 128, -25, -30, 45, 0.04),
                                                           (12, 140, -28, -35, -20, -0.04), (16, 58, 28, 30, 82, 0.08),
                                                           (20, *REST)], [4, 9, 15], 0, []),
    "C2": ("Sword combo: sweep, thrust", "sword", [(0, *REST), (3, 96, -45, -80, 60, 0), (6, 92, 50, -80, 60, 0.05),
                                                   (9, 92, 8, 0, 88, -0.22), (11, 94, 2, 0, 90, -0.24), (13, 93, 0, 0, 90, 0.34),
                                                   (17, *REST)], [5, 13], 0, [(8, 15, 90)]),
    "P1": ("Pickaxe", "pickaxe", [(0, *REST), (4, 135, -6, 0, -15, -0.04), (6, 138, -6, 0, -18, -0.05), (9, 72, 4, 0, 78, 0.06),
                                  (10, 78, 4, 0, 70, 0.04), (13, *REST)], [9], 0, []),
    "A1": ("Axe", "axe", [(0, *REST), (4, 132, -26, -30, -10, -0.03), (6, 134, -28, -32, -14, -0.04), (9, 70, 22, 28, 75, 0.06),
                          (10, 74, 20, 26, 70, 0.05), (14, *REST)], [9], -1, []),
    "V1": ("Shovel", "shovel", [(0, *REST), (3, 88, 4, 0, 92, 0.02), (6, 82, 4, 0, 104, 0.26), (9, 86, 4, 0, 72, 0.2),
                                (11, 106, 0, 0, 40, 0.06), (12, 110, -10, 0, 22, 0.06), (15, *REST)], [6], 0, [(0, 15, 90)]),
    "O1": ("Hoe", "hoe", [(0, *REST), (3, 120, 2, 0, 10, 0.05), (6, 70, 2, 0, 95, 0.18), (10, 66, 0, 0, 90, -0.12), (13, *REST)],
           [6], -1, []),
    "H1": ("Hammer overhead", "hammer3d", [(0, *REST), (6, 140, -6, 0, -35, -0.06), (10, 144, -6, 0, -42, -0.07),
                                           (13, 58, 4, 0, 85, 0.08), (15, 56, 4, 0, 86, 0.08), (19, *REST)], [13], 0, []),
    "H2": ("Hammer from the side", "hammer3d", [(0, *REST), (5, 98, -60, -90, 30, 0), (8, 95, 40, -90, 60, 0.05),
                                                (9, 95, 36, -90, 58, 0.04), (13, *REST)], [8], 0, []),
}


def pose_at(keys, t):
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = smooth((t - ta) / (tb - ta))
            return [x + (y - x) * w for x, y in zip(a, b)]
    return list(keys[-1][1:])


# ------------------------------------------------------------------ tool models from the jar's bbmodels
def load_tool(tool, parent, tag):
    """Each bbmodel element becomes a box (1 unit = 1/32 m, held size), material by name; returns (obj, centre)."""
    if tool == "hammer3d":
        # J: the construct hammer, not a flat item: a solid block head with depth, striking faces at +-X, glowing rims
        root = link(bpy.data.objects.new(f"{tag} tool", None)); root.parent = parent
        parts = []
        def hb(nm, a, b, m):
            o = box(f"{tag} {nm}", a, b, m, root); parts.append((o, (np.array(a) + np.array(b)) / 2))
        hb("handle", (-0.03, 0.0, -0.03), (0.03, 0.62, 0.03), GRIP)
        for k, y in enumerate((0.08, 0.2, 0.32, 0.44)):
            hb(f"glow_band {k}", (-0.04, y, -0.04), (0.04, y + 0.03, 0.04), GLOW)
        hb("glass_hardlight head", (-0.2, 0.58, -0.12), (0.2, 0.82, 0.12), GLASS)
        hb("glow_core", (-0.12, 0.64, -0.06), (0.12, 0.76, 0.06), GLOW)
        for sx in (-1, 1):
            hb(f"glow_rim face {sx}", (sx * 0.2 - 0.015, 0.57, -0.13), (sx * 0.2 + 0.015, 0.83, 0.13), RIM)
            hb(f"glow_rim plate {sx}", (sx * 0.23 - 0.02, 0.6, -0.1), (sx * 0.23 + 0.02, 0.8, 0.1), GLASS)
        hb("glow_rim top", (-0.2, 0.82, -0.12), (0.2, 0.84, 0.12), RIM)
        return root, parts
    path = os.path.join(BB, f"construct_{tool}_green.bbmodel")
    d = json.load(open(path))
    root = link(bpy.data.objects.new(f"{tag} tool", None)); root.parent = parent
    parts = []
    for e in d["elements"]:
        nm = e["name"]
        m = GRIP if nm.startswith("handle") else RIM if nm.startswith("glow_rim") else GLOW if nm.startswith("glow") else GLASS
        a = np.array(e["from"], float) / 32.0; b = np.array(e["to"], float) / 32.0
        inf = float(e.get("inflate", 0)) / 32.0
        a -= inf; b += inf
        # bb y is the tool's length (grip at 0); in the fist: along the tool's local +Y, flat across X
        o = box(f"{tag} {nm}", (a[0], a[1], a[2]), (b[0], b[1], b[2]), m, root)
        parts.append((o, (a + b) / 2))
    return root, parts


def make_arm(tag, base):
    """Minecraft right arm in first person: a 4x12x4 px box from the shoulder, sleeve then skin, ring on the hand."""
    sh = link(bpy.data.objects.new(f"{tag} shoulder", None)); sh.location = base; sh.rotation_mode = "XYZ"
    px = 1 / 16 * 1.05                                        # one skin pixel, a touch larger in first person
    box(f"{tag} sleeve", (-2 * px, -2 * px, -8 * px), (2 * px, 2 * px, 0), SLEEVE, sh)
    box(f"{tag} hand", (-2 * px, -2 * px, -12 * px), (2 * px, 2 * px, -8 * px), SKIN, sh)
    # the ring stays on (J): a gold band round the hand with the green face on the knuckle side
    box(f"{tag} ring band", (-2.2 * px, -2.2 * px, -10.6 * px), (2.2 * px, 2.2 * px, -9.6 * px), GOLDM, sh)
    box(f"{tag} ring face", (-1.0 * px, 2.2 * px, -11.0 * px), (1.0 * px, 2.9 * px, -9.2 * px), RINGM, sh)
    grip = link(bpy.data.objects.new(f"{tag} grip", None)); grip.parent = sh
    grip.location = (0, 0, -11 * px); grip.rotation_mode = "XYZ"
    return sh, grip, Vector((0, 2.6 * px, -10.1 * px))       # ring face point (shoulder space)


dump = {"format": "per take: per tick right-arm rotation (pitch, yaw, roll in degrees, pitch 90 = ahead), shoulder reach (m, + forward), tool tilt in the fist and tool twist about its length (the edge leads); 'hit' = the tick the tool connects; forming ticks 0-14 come first. 20 ticks a second.",
        "takes": {}}
BAY = 6.0
ORDER = list(SWINGS)
for bi, tk in enumerate(ORDER):
    name, tool, keys, hits, side, fixed = SWINGS[tk]
    bx = bi * BAY
    eye = Vector((bx, 0.0, 1.62))
    # the world ahead: floor, a block, a dummy target
    box(f"FP {tk} floor", (bx - 2.5, -1, -0.02), (bx + 2.5, 6, 0), FLOOR)
    box(f"FP {tk} block", (bx - 0.5, 2.0, 0.0), (bx + 0.5, 3.0, 1.0), STONE)
    dm = box(f"FP {tk} dummy", (bx + 0.6, 2.4, 0.0), (bx + 1.1, 2.8, 1.8), DUMMY)
    flash = box(f"FP {tk} hit", (bx + 0.62, 2.36, 1.0), (bx + 1.08, 2.39, 1.6), HIT)
    shoulder0 = eye + Vector((0.36, 0.12, -0.42))
    sh, grip, ring_pt = make_arm(f"FP {tk}", shoulder0)
    root, parts = load_tool(tool, grip, f"FP {tk}")
    swing = keys[-1][0]
    total = FORM + 2 * swing + GAP + 10
    ticks = []
    for t in range(total + 1):
        if t < FORM:
            p = list(REST)
        else:
            k = t - FORM
            if k <= swing:
                p = pose_at(keys, k)
            elif k <= swing + GAP:
                p = list(REST)
            elif k <= 2 * swing + GAP:
                p = pose_at(keys, k - swing - GAP)
            else:
                p = list(REST)
        pitch, yaw, roll, tilt, reach = p
        e_ = Euler((R(pitch), 0, R(yaw)), "XYZ"); e_.rotate_axis("Z", R(roll))
        sh.rotation_euler = e_; sh.keyframe_insert("rotation_euler", frame=t + 1)
        key(sh, t + 1, loc=tuple(shoulder0 + Vector((0, reach, 0))))
        key(grip, t + 1, rot=(R(-tilt), 0, 0))           # the tool stands up out of the fist, leaning forward by tilt
        k_ = t - FORM
        hit_now = t >= FORM and (k_ in hits or (k_ - swing - GAP) in hits)
        ticks.append({"arm": [round(pitch, 2), round(yaw, 2), round(roll, 2)], "tool_tilt": round(tilt, 2),
                      "reach": round(reach, 3), "hit": hit_now})
        flash.hide_render = not hit_now; flash.keyframe_insert("hide_render", frame=t + 1)
        flash.hide_viewport = not hit_now; flash.keyframe_insert("hide_viewport", frame=t + 1)
        if hit_now:
            key(dm, t + 1, rot=(R(-12), 0, 0)); key(dm, t + 4, rot=(0, 0, 0))
    # the working edge leads: sample the tool tip each tick, turn the tool about its length to face its motion
    L_tip = 0.75
    tips = []
    for t in range(total + 1):
        scene.frame_set(t + 1)
        tips.append((grip.matrix_world.copy(), grip.matrix_world @ Vector((0, L_tip, 0))))
    phi_prev = 0.0; twists = []
    for t in range(total + 1):
        k_ = t - FORM
        kk = k_ if k_ <= swing else k_ - swing - GAP
        fx = next((d for a_, b_, d in fixed if a_ <= kk <= b_ and t >= FORM), None)
        if fx is not None:
            phi = R(fx)
        else:
            v = tips[min(total, t + 1)][1] - tips[max(0, t - 1)][1]
            vg = tips[t][0].to_3x3().inverted() @ v
            if math.hypot(vg.x, vg.z) > 0.004:
                phi = math.atan2(-vg.z, vg.x) if side >= 0 else math.atan2(vg.z, -vg.x)
                if side == 0:                                  # two-edged: pick the turn closest to the last one
                    alt = phi + math.pi
                    phi = min((phi, alt), key=lambda a: abs((a - phi_prev + math.pi) % (2 * math.pi) - math.pi))
            else:
                phi = phi_prev
        phi = phi_prev + ((phi - phi_prev + math.pi) % (2 * math.pi) - math.pi)   # unwrap
        phi = phi_prev + (phi - phi_prev) * 0.65 if fx is None else phi           # ease
        twists.append(phi); phi_prev = phi
        key(root, t + 1, rot=(0, phi, 0))
        ticks[t]["tool_twist"] = round(math.degrees(phi), 2)
    # forming: every tool box grows in from nothing, grip first and tip last, a pixel flying from the ring to it
    bpy.context.view_layer.update()
    span = max(c[1] for _, c in parts) or 1.0
    rng = np.random.default_rng(802 + bi)
    pm = bpy.data.meshes.new(f"FP {tk} px"); s_ = 0.025
    pm.from_pydata([(x, y, z) for x in (-s_, s_) for y in (-s_, s_) for z in (-s_, s_)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    pm.materials.append(PIX)
    for o, c in parts:
        f_arrive = 2 + int(round((c[1] / span) * (FORM - 4))) + int(rng.integers(0, 2))
        key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive + 1, sc=1.0)
        if rng.random() < 0.55:                                    # a pixel streams out of the ring to it
            px = link(bpy.data.objects.new(f"FP {tk} pixel", pm)); px.parent = sh
            start = ring_pt + Vector(rng.uniform(-0.02, 0.02, 3))
            ends = sh.matrix_world.inverted() @ root.matrix_world @ Vector(c)
            f0 = max(1, f_arrive - 5)
            key(px, 1, loc=start, sc=0.0001); key(px, f0, loc=start, sc=0.0001)
            key(px, f0 + 1, loc=start, sc=1.0)
            mid = (start + ends) / 2 + Vector((0, 0.04, 0.03))
            key(px, f0 + 3, loc=mid, sc=1.0); key(px, f_arrive, loc=ends, sc=0.6); key(px, f_arrive + 1, loc=ends, sc=0.0001)
    dump["takes"][tk] = {"name": name, "tool": tool, "forming_ticks": FORM, "swing_ticks": swing, "hit_ticks": hits,
                         "keys": [list(k) for k in keys], "ticks": ticks}
    # cameras: the eye (first person), and from the right to read the arc
    c = cam(f"Cam {tk}", tuple(eye), tuple(eye + Vector((0, 3, -0.25))), 26)
    cam(f"Cam {tk} side", tuple(eye + Vector((3.2, 0.9, 0.2))), tuple(eye + Vector((0.3, 0.6, -0.3))), 35)
    cu = bpy.data.curves.new("FP label " + tk, "FONT"); cu.body = f"{tk}  {name}"; cu.size = 0.2; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("FP label " + tk, cu)); tl.location = (bx, 3.6, 2.4); tl.rotation_euler = (R(90), 0, 0)
    tl.data.materials.append(GLOW)
    print(tk, name, "built:", total, "ticks", flush=True)

with open(os.path.join(FOLDER, "combat", "fp_tools2_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

scene.frame_start, scene.frame_end = 1, max(FORM + 2 * SWINGS[t][2][-1][0] + GAP + 11 for t in ORDER)
world = bpy.data.worlds.new("FP world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.42, 0.55, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("FP sun", bpy.data.lights.new("FP sun", "SUN")))
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
    tree = bpy.data.node_groups.new("FP Glow", "CompositorNodeTree")
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
cam("Cam all", ((len(ORDER) - 1) * BAY / 2, -9.0, 6.0), ((len(ORDER) - 1) * BAY / 2, 2.0, 1.0), 30)
scene.camera = bpy.data.objects["Cam S1"]
scene.frame_set(FORM + 3)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
