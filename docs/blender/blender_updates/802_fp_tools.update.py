# Pass 802: first-person construct tool animations (Chat C, 2026-10-14, range 800-899).
# J: "i need the tool animations 1st person reworked and i need them to fill up my item bar instead of forcing me to
# use them". Picks: sword, pickaxe and axe, shovel and hoe, hammer; show 3+ sword takes; the tool forms pixel by pixel;
# "the ring should stay on when wearing it, make a ring slot in the inventory for your right hand" (the slot and the
# hotbar behaviour are game code, sent to the mc chat; here the ring stays on the right hand in every take).
# First person, Minecraft style: the camera is the eye, the right arm (ring on it) comes in from the lower right.
# Every take starts with the tool FORMING pixel by pixel: construct pixels stream out of the ring and lock into the
# tool from the grip to the tip (ticks 0-14), then the swing plays twice. The tools are the jar's construct tool models
# (assets/lanternring/bbmodel/construct_<tool>_green.bbmodel), glass see-through, glowing parts lit.
#   S1 sword fast slash   : a quick diagonal cut, high right to low left, snaps back (8 ticks)
#   S2 sword heavy chop   : raised high behind, a wind-up, a big downward chop with follow-through (16 ticks)
#   S3 sword sweep pair   : a flat sweep right to left, then a backhand return (14 ticks)
#   S4 sword thrust       : pulled back, a straight stab forward, drawn back (9 ticks)
#   P1 pickaxe            : overhead strike into the block ahead, a small bounce on impact (10 ticks)
#   A1 axe                : a slanted chop from the right with a recoil (12 ticks)
#   V1 shovel             : a forward-down scoop, lift and flick (11 ticks)
#   O1 hoe                : reach out, hook down, drag back toward you (11 ticks)
#   H1 hammer overhead    : raised over the head, held, smashed down (18 ticks)  (J's default: overhead)
#   H2 hammer from the side: a flat side swing into a wall (13 ticks)            (J: from the side on walls)
# Each take sits in its own bay with a dummy target and a block ahead; the hit tick flashes the target.
# Cameras "Cam <take>" (first person, the eye), "Cam <take> side" (from the right, to read the arc), "Cam all".
# Writes LanternLive\combat\fp_tools_poses.json (per tick arm and tool rotations) and builds
# LanternLive\combat\fp_tools.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector

R = math.radians
OUT = os.path.join(FOLDER, "combat", "fp_tools.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
BB = os.path.join(FOLDER, "kl_assets")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("FP Tools")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("FP Tools")
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
REST = (96, 14, 0, 22)
SWINGS = {
    "S1": ("Sword fast slash", "sword", [(0, *REST), (2, 125, -18, -25, 40), (5, 70, 32, 35, 70), (8, *REST)], 4),
    "S2": ("Sword heavy chop", "sword", [(0, *REST), (5, 138, -6, -10, -25), (8, 142, -4, -12, -35), (11, 55, 6, 5, 80),
                                         (13, 50, 8, 5, 85), (16, *REST)], 11),
    "S3": ("Sword sweep pair", "sword", [(0, *REST), (3, 96, -45, -80, 60), (6, 92, 50, -80, 60), (8, 94, 52, 100, 60),
                                        (11, 94, -40, 100, 60), (14, *REST)], 6),
    "S4": ("Sword thrust", "sword", [(0, *REST), (3, 84, 4, 0, 82), (5, 92, 2, 0, 90), (9, *REST)], 5),
    "P1": ("Pickaxe", "pickaxe", [(0, *REST), (4, 132, -2, 0, -10), (7, 82, 4, 0, 70), (8, 88, 4, 0, 62), (10, *REST)], 7),
    "A1": ("Axe", "axe", [(0, *REST), (4, 135, -30, -40, -5), (8, 75, 22, 30, 70), (9, 80, 18, 25, 60), (12, *REST)], 8),
    "V1": ("Shovel", "shovel", [(0, *REST), (3, 70, 2, 0, 95), (6, 62, 0, 0, 115), (9, 100, 0, 0, 40), (11, *REST)], 6),
    "O1": ("Hoe", "hoe", [(0, *REST), (3, 98, 2, 0, 20), (6, 70, 2, 0, 95), (9, 60, 0, 0, 80), (11, *REST)], 6),
    "H1": ("Hammer overhead", "hammer", [(0, *REST), (6, 140, -4, 0, -40), (10, 144, -4, 0, -45), (13, 58, 4, 0, 85),
                                          (15, 56, 4, 0, 86), (18, *REST)], 13),
    "H2": ("Hammer from the side", "hammer", [(0, *REST), (5, 100, -70, -90, 30), (8, 95, 45, -90, 60), (9, 95, 40, -90, 58),
                                               (13, *REST)], 8),
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


dump = {"format": "per take: per tick right-arm rotation (pitch, yaw, roll in degrees, pitch 90 = ahead) and tool tilt "
                  "in the fist; 'hit' = the tick the tool connects; forming ticks 0-14 come first. 20 ticks a second.",
        "takes": {}}
BAY = 6.0
ORDER = list(SWINGS)
for bi, tk in enumerate(ORDER):
    name, tool, keys, hit = SWINGS[tk]
    bx = bi * BAY
    eye = Vector((bx, 0.0, 1.62))
    # the world ahead: floor, a block, a dummy target
    box(f"FP {tk} floor", (bx - 2.5, -1, -0.02), (bx + 2.5, 6, 0), FLOOR)
    box(f"FP {tk} block", (bx - 0.5, 2.0, 0.0), (bx + 0.5, 3.0, 1.0), STONE)
    dm = box(f"FP {tk} dummy", (bx + 0.6, 2.4, 0.0), (bx + 1.1, 2.8, 1.8), DUMMY)
    flash = box(f"FP {tk} hit", (bx + 0.62, 2.36, 1.0), (bx + 1.08, 2.39, 1.6), HIT)
    sh, grip, ring_pt = make_arm(f"FP {tk}", eye + Vector((0.36, 0.12, -0.42)))
    root, parts = load_tool(tool, grip, f"FP {tk}")
    swing = len(keys) and keys[-1][0]
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
        pitch, yaw, roll, tilt = p
        e_ = Euler((R(pitch), 0, R(yaw)), "XYZ"); e_.rotate_axis("Z", R(roll))
        sh.rotation_euler = e_; sh.keyframe_insert("rotation_euler", frame=t + 1)
        key(grip, t + 1, rot=(R(-tilt), 0, 0))           # the tool stands up out of the fist, leaning forward by tilt
        hit_now = t >= FORM and ((t - FORM) == hit or (t - FORM) == hit + swing + GAP)
        ticks.append({"arm": [round(pitch, 2), round(yaw, 2), round(roll, 2)], "tool_tilt": round(tilt, 2), "hit": hit_now})
        flash.hide_render = not hit_now; flash.keyframe_insert("hide_render", frame=t + 1)
        flash.hide_viewport = not hit_now; flash.keyframe_insert("hide_viewport", frame=t + 1)
        if hit_now:
            key(dm, t + 1, rot=(R(-12), 0, 0)); key(dm, t + 4, rot=(0, 0, 0))
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
    dump["takes"][tk] = {"name": name, "tool": tool, "forming_ticks": FORM, "swing_ticks": swing, "hit_tick": hit,
                         "keys": [list(k) for k in keys], "ticks": ticks}
    # cameras: the eye (first person), and from the right to read the arc
    c = cam(f"Cam {tk}", tuple(eye), tuple(eye + Vector((0, 3, -0.25))), 26)
    cam(f"Cam {tk} side", tuple(eye + Vector((3.2, 0.9, 0.2))), tuple(eye + Vector((0.3, 0.6, -0.3))), 35)
    cu = bpy.data.curves.new("FP label " + tk, "FONT"); cu.body = f"{tk}  {name}"; cu.size = 0.2; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("FP label " + tk, cu)); tl.location = (bx, 3.6, 2.4); tl.rotation_euler = (R(90), 0, 0)
    tl.data.materials.append(GLOW)
    print(tk, name, "built:", total, "ticks", flush=True)

with open(os.path.join(FOLDER, "combat", "fp_tools_poses.json"), "w") as fh:
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
