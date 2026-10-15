# Pass 520: first-person versions of the moves (Chat C, 2026-10-15). The catalogue (519) showed that from your eyes the
# arms never come into view for the flurries, slams, take-off, double jump, sprint and flight. J picked all four groups
# and "Show me both" styles:
#   V  vanilla-like: the arms come in from the lower corners at Minecraft's own first-person size, then punch, reach
#      and swing through the view.
#   B  bigger and closer: the same motion with the arms 1.3x bigger and a quarter closer, filling more of the screen.
# The camera rides the eyes of the picked 3rd-person take (same timings as the catalogue), so the view rises, dives
# and flies exactly as in 3rd person; the arms are keyed in view space and exported in the same terms as the mod's
# RingFirstPerson (fist point, elbow point, back-of-hand direction; blocks; x right, y up, -z forward).
# Moves: flurry F2, flying flurry, big slam S3, primed slams P1/P2, slide U1, take-off F2, double jump S1, running
# dart (A2 arm), sprint with the lantern S5a, ring arm leading flight D1.
# Cameras "NN <move> - vanilla" and "NN <move> - bigger". Builds LanternLive\first_person_moves.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

_src = os.path.join(os.environ.get("KL_REPO", "/home/claude/site-10"), "docs", "blender", "blender_updates",
                    "519_animation_catalogue.update.py")
_txt = open(_src).read()
exec(compile(_txt[:_txt.index("NAMES = {")], _src, "exec"), globals())     # rig, loaders, lantern, keyer from 519
scene.name = "First Person Moves"
OUT = os.path.join(FOLDER, "first_person_moves.blend")
ENT = {e[1]: e for e in ENTRIES}
EYE_PX = np.array([0.0, -5.0, -4.3])


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ view-space poses: (fist, elbow, back-of-hand)
def P(f, e, b=(0, 1, 0)):
    return (np.array(f, float), np.array(e, float), np.array(b, float))


def mirror(p):
    f, e, b = p
    m = np.array([-1, 1, 1.0])
    return (f * m, e * m, b * m)


R_REST = P((.40, -.42, -.72), (.70, -.95, -.35))
R_OFF = P((.55, -1.15, -.55), (.75, -1.70, -.30))
R_GUARD = P((.22, -.30, -.70), (.50, -.80, -.40))
R_CROSS = P((.04, -.08, -1.10), (.32, -.42, -.55))
R_WIND = P((-.30, -.16, -.58), (.22, -.50, -.45), (0, 0, 1))         # backfist wound across the chest
R_BACKFIST = P((.32, -.05, -1.00), (.10, -.45, -.50), (1, 0, 0))     # back of the hand leads to the right
R_FWD = P((.14, -.16, -1.00), (.36, -.58, -.52))                     # ring fist leading flight / dive
R_PULL = P((.30, -.10, -.66), (.56, -.42, -.28))                     # slam wind-up
R_SLAM = P((.05, -.30, -.80), (.35, -.95, -.45), (0, 0, -1))         # fist driven down into the ground
R_PUSH = P((.48, -.78, -.62), (.52, -.35, -.40), (0, 0, -1))         # pushing down (jump puff / crouch)
R_LAUNCH = P((.16, .18, -1.00), (.38, -.38, -.62))
R_SPRINT = P((.24, -.30, -.88), (.48, -.75, -.48))
R_HOVER = P((.20, -.25, -.85), (.45, -.70, -.45))
R_AIM = P((.12, -.25, -.95), (.38, -.65, -.50))                      # looking at the crater, left click
R_LOW = P((.20, -.32, -.95), (.42, -.75, -.50))
L_REST, L_OFF, L_GUARD, L_PUSH = mirror(R_REST), mirror(R_OFF), mirror(R_GUARD), mirror(R_PUSH)
L_JAB = P((-.06, -.10, -1.05), (-.30, -.42, -.55))
L_TOUCH = P((-.30, -.38, -.80), (-.50, -1.00, -.45), (0, 0, -1))      # free hand bracing on the ground
L_CARRY = P((-.38, -.40, -.70), (-.60, -1.00, -.40))                  # holding the lantern's handle, low left


def lerp_pose(a, b, w):
    return tuple(a[i] + (b[i] - a[i]) * w for i in range(3))


def keyed(keys, t):
    """keys: [(tick, pose)] -> pose at t (smooth between keys)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return lerp_pose(pa, pb, smooth((t - ta) / max(1e-6, tb - ta)))
    return keys[-1][1]


def shake_at(t, events):
    """events: [(tick, amp, len)] -> camera offset (x, y) that decays."""
    x = y = 0.0
    for t0, amp, ln in events:
        if t0 <= t < t0 + ln:
            k = amp * (1 - (t - t0) / ln)
            x += k * math.sin(t * 2.7 + t0); y += k * math.cos(t * 3.3 + t0)
    return x, y


# ------------------------------------------------------------------ the moves: which 3p take drives the camera, keys
MOVES = []


def move(name, entry, R, L, shake=(), extra=None):
    MOVES.append(dict(name=name, entry=entry, R=R, L=L, shake=list(shake), extra=extra or {}))


move("Flurry F2", "F2f",
     [(0, R_GUARD), (6, R_GUARD), (11, R_CROSS), (14, R_WIND), (18, R_BACKFIST), (24, R_BACKFIST), (34, R_REST)],
     [(0, L_GUARD), (3, P((-.30, -.36, -.62), (-.55, -.80, -.38))), (6, L_JAB), (9, L_GUARD), (18, L_GUARD), (34, L_OFF)],
     shake=[(6, .008, 3), (11, .010, 3), (18, .022, 5)], extra={"mob": "ground"})
move("Flying flurry", "A2",
     [(0, R_FWD), (8, R_FWD), (11, R_GUARD), (12, R_GUARD), (17, R_CROSS), (20, R_WIND), (24, R_BACKFIST),
      (30, R_BACKFIST), (40, R_FWD)],
     [(0, L_OFF), (8, L_OFF), (11, L_GUARD), (12, L_JAB), (15, L_GUARD), (24, L_GUARD), (40, L_OFF)],
     shake=[(12, .008, 3), (17, .010, 3), (24, .022, 5)], extra={"mob": "carried"})
move("Big flight slam S3", "S3H5",
     [(0, R_FWD), (31, R_FWD), (33, R_PULL), (34, R_SLAM), (48, R_SLAM), (56, R_REST)],
     [(0, L_OFF), (32, L_OFF), (34, L_TOUCH), (48, L_TOUCH), (56, L_OFF)],
     shake=[(34, .06, 10)])
move("Primed flight slam P1", "P1",
     [(0, R_FWD), (27, R_FWD), (29, R_PULL), (30, R_SLAM), (44, R_SLAM), (52, R_REST), (66, R_REST), (70, R_AIM),
      (90, R_AIM), (96, R_REST)],
     [(0, L_OFF), (28, L_OFF), (30, L_TOUCH), (44, L_TOUCH), (52, L_OFF)],
     shake=[(30, .06, 10), (70, .006, 4)])
move("Primed super-jump slam P2", "P2",
     [(0, R_REST), (6, R_PUSH), (12, R_REST), (40, R_FWD), (53, R_FWD), (55, R_PULL), (56, R_SLAM), (70, R_SLAM),
      (78, R_REST), (92, R_REST), (96, P((-.18, -.25, -.95), (.20, -.65, -.50))),
      (114, P((.32, -.25, -.95), (.58, -.65, -.50))), (120, R_REST)],
     [(0, L_OFF), (6, L_PUSH), (12, L_OFF), (54, L_OFF), (56, L_TOUCH), (70, L_TOUCH), (78, L_OFF)],
     shake=[(6, .01, 4), (56, .08, 12), (96, .006, 4)])
move("Unprimed slide U1", "U1",
     [(0, R_FWD), (24, R_LOW), (42, R_LOW), (52, R_REST)],
     [(0, L_OFF), (26, L_OFF), (30, L_TOUCH), (42, L_TOUCH), (52, L_OFF)],
     shake=[(30, .02, 12)])
move("Flight take-off F2", "F2",
     [(0, R_SPRINT), (22, R_SPRINT), (26, R_PUSH), (29, R_LAUNCH), (45, R_LAUNCH), (54, R_FWD)],
     [(0, L_OFF), (22, L_OFF), (26, L_PUSH), (30, L_OFF)],
     shake=[(28, .02, 6)], extra={"bob": (0, 24)})
move("Double jump standing S1", "S1",
     [(0, R_REST), (9, R_REST), (12, R_PUSH), (16, R_PUSH), (24, R_HOVER)],
     [(0, L_OFF), (9, L_OFF), (12, L_PUSH), (16, L_PUSH), (24, L_OFF)],
     shake=[(12, .015, 5)])
move("Double jump running A2", "R3A2",
     [(0, R_SPRINT), (16, R_SPRINT), (19, R_PUSH), (23, R_FWD)],
     [(0, L_OFF), (16, L_OFF), (19, L_PUSH), (24, L_OFF)],
     shake=[(19, .015, 5)], extra={"bob": (0, 18)})
move("Sprint with lantern S5a", "S5a", [(0, R_SPRINT)], [(0, L_CARRY)], extra={"bob": (0, 999), "lantern": True})
move("Ring arm leads flight D1", "D1", [(0, R_FWD)], [(0, L_OFF)], extra={"lead": True})

STYLES = (("vanilla", 1.0, 1.0), ("bigger", 1.3, 0.75))      # name, arm size, distance scale


def styled(p, size, dist):
    f, e, b = p
    k = np.array([1.08, 1.04, dist]) if size > 1 else np.ones(3)
    return (f * k, e * k, b)


# ------------------------------------------------------------------ arms in camera space
def arm_mesh(name, size, ring):
    w, L = 4 / 16 * size, 12 / 16 * size
    parts = [((0, 0), (3, SKIN)), ((3, 12), (None, SHIRT))]
    verts, faces, mats = [], [], []
    me = bpy.data.meshes.new(name)

    def box(a, b, mi):
        n = len(verts)
        for x in (a[0], b[0]):
            for y in (a[1], b[1]):
                for z in (a[2], b[2]):
                    verts.append((x, y, z))
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            faces.append(tuple(n + i for i in f)); mats.append(mi)

    px = 1 / 16 * size
    box((-w / 2, 0, -w / 2), (w / 2, 3 * px, w / 2), 0)                  # hand
    box((-w / 2, 3 * px, -w / 2), (w / 2, L, w / 2), 1)                   # sleeve
    if ring:
        box((-w / 2 - .4 * px, 2.6 * px, -w / 2 - .4 * px), (w / 2 + .4 * px, 3.8 * px, w / 2 + .4 * px), 2)
    me.from_pydata(verts, [], faces); me.update()
    for m in (SKIN, SHIRT, ring or SKIN):
        me.materials.append(m)
    for poly, mi in zip(me.polygons, mats):
        poly.material_index = mi
    return me


def arm_matrix(p, shake):
    f, e, b = p
    y = e - f; y = y / np.linalg.norm(y)
    z = b - np.dot(b, y) * y
    if np.linalg.norm(z) < 1e-4:
        z = np.array([0, 0, 1.0]) - y[2] * y
    z = z / np.linalg.norm(z); x = np.cross(y, z)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2] = x, y, z; M[:3, 3] = f + np.array([shake[0], shake[1], 0])
    return Matrix(M.tolist())


PINK = mat("FP dummy", (0.55, 0.42, 0.3)); PINK2 = mat("FP dummy head", (0.7, 0.55, 0.38))


def mob(tag):
    me = box_mesh(tag, (-4, -24, -2), (4, 0, 2), PINK)               # a 2-block training dummy facing you
    o = link(bpy.data.objects.new(tag, me))
    h = link(bpy.data.objects.new(tag + " head", box_mesh(tag + " head", (-4, -32, -4), (4, -24, 4), PINK2)))
    h.parent = o
    return o


def mob_path(kind, frames, hits, launch, n):
    """World positions of the target: held 1.7 blocks in front, nudged by each punch, launched by the backfist."""
    out = []
    pos = vel = None
    for t in range(n):
        fr = frames[min(t, len(frames) - 1)]
        base = fr["origin"]
        if t <= hits[-1]:
            nudge = 0.25 * sum(1 for h in hits[:-1] if t >= h)
            ahead = 0.0 if kind == "ground" else 0.7 * max(0, hits[0] - t)     # flying: you close in on it first
            pos = base + np.array([0.0, -1.7 - nudge - ahead, 0.0 if kind == "ground" else -0.6])
            if t == hits[-1]:
                vel = np.array(launch, float)
        else:
            g, drag = (0.08, 0.98) if kind == "ground" else (0.03, 0.99)
            pos = pos + vel; vel = vel * drag; vel[2] -= g
            if pos[2] < 0:
                pos[2] = 0.0; vel[:] = 0
        out.append(pos.copy())
    return out


dump = {"format": "per move and style: per tick right/left arm in view space (blocks; x right, y up, -z forward): "
                  "fist point, elbow point (the arm runs fist -> elbow), back-of-hand direction; arm_scale; ring glow; "
                  "camera shake (x, y blocks). The camera rides the eyes of the 3rd-person take named in 'third_person'. "
                  "20 ticks a second.", "moves": {}}
END = 0
lane = 0
for mv in MOVES:
    frames, meta = frames_of(ENT[mv["entry"]])
    n = len(frames)
    END = max(END, n)
    for sname, size, dist in STYLES:
        ox = lane * 20.0
        tag = f"{lane // 2 + 1:02d} {mv['name']} - {sname}"
        ringm = mat(f"FP ring {tag}", (0.04, 0.85, 0.15), emit=2.0)
        eye = link(bpy.data.objects.new(f"FP {tag} eye", None)); eye.empty_display_size = 0.05
        c = link(bpy.data.objects.new(tag, bpy.data.cameras.new(tag)))
        c.data.sensor_fit = "VERTICAL"; c.data.angle = R(70); c.data.clip_start = 0.02
        c.parent = eye; c.rotation_euler = (R(90), 0, R(180))
        rarm = link(bpy.data.objects.new(f"FP {tag} ring arm", arm_mesh(f"FP {tag} ring arm", size, ringm)))
        larm = link(bpy.data.objects.new(f"FP {tag} free arm", arm_mesh(f"FP {tag} free arm", size, None)))
        rarm.parent = c; larm.parent = c
        lan = None
        if mv["extra"].get("lantern"):
            lan = import_lantern(f"FP {tag}")
            lan[0].parent = c
        target = mob(f"FP {tag} target") if mv["extra"].get("mob") else None
        if target is not None:
            src = load(ENT[mv["entry"]][3])["takes"][ENT[mv["entry"]][4]]
            hits = src["hits"]
            launch = src.get("launch_bpt") or list(np.array(src["launch_dir"]) * src["launch_speed_bpt"])
            path = mob_path(mv["extra"]["mob"], frames, hits, launch, n)
        sock = ringm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        ticks = []
        for t, fr in enumerate(frames):
            f_ = t + 1
            origin = np.array([ox, 0.0, 0.0]) + fr["origin"]
            r, pv = fr["parts"]["head"]
            yaw = fr["side"] if fr["cam_yaw"] else 0.0
            KEYS.add(eye, f_, world_of(rot(*r), pv + rot(*r) @ EYE_PX, origin, yaw, 0.0))
            Rp, Lp = keyed(mv["R"], t), keyed(mv["L"], t)
            bob = mv["extra"].get("bob")
            if bob and bob[0] <= t <= bob[1]:
                ph = 2 * math.pi * t / 12.0
                Rp = (Rp[0] + np.array([.015 * math.cos(ph), .035 * math.sin(ph), 0]), Rp[1], Rp[2])
                Lp = (Lp[0] + np.array([.015 * math.cos(ph), -.035 * math.sin(ph), 0]), Lp[1], Lp[2])
            if mv["extra"].get("lead"):
                k = load(ENT["D1"][3])["takes"]["D1"]["ticks"][t]
                d = math.radians(k["arm_heading"] - k["body_heading"])
                dx = 0.9 * math.tan(max(-0.6, min(0.6, d)))
                Rp = (Rp[0] + np.array([dx, 0, 0]), Rp[1] + np.array([dx * 0.5, 0, 0]), Rp[2])
            Rs, Ls = styled(Rp, size, dist), styled(Lp, size, dist)
            sh = shake_at(t, mv["shake"])
            KEYS.add(rarm, f_, arm_matrix(Rs, sh))
            KEYS.add(larm, f_, arm_matrix(Ls, sh))
            if lan is not None:
                M = np.eye(4); M[:3, 3] = Ls[0] + np.array([sh[0], sh[1] - (LH - 0.5) / 16.0, 0.0])
                M[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])      # lantern upright in view (z up -> y up)
                KEYS.add(lan[0], f_, Matrix(M.tolist()))
            if target is not None:
                Mt = np.eye(4); Mt[:3, 3] = path[t] + np.array([ox, 0.0, 0.0])
                KEYS.add(target, f_, Matrix(Mt.tolist()))
            glow = fr["glow"]
            sock.default_value = min(4.0, 1.2 + 0.2 * glow)      # close to the eye: saturated, never white; sock.keyframe_insert("default_value", frame=f_)
            ticks.append({"right": {"fist": [round(float(v), 3) for v in Rs[0]], "elbow": [round(float(v), 3) for v in Rs[1]],
                                    "back": [round(float(v), 3) for v in Rs[2]]},
                          "left": {"fist": [round(float(v), 3) for v in Ls[0]], "elbow": [round(float(v), 3) for v in Ls[1]],
                                   "back": [round(float(v), 3) for v in Ls[2]]},
                          "glow": round(float(glow), 2), "shake": [round(sh[0], 4), round(sh[1], 4)]})
        dump["moves"][tag] = {"move": mv["name"], "style": sname, "arm_scale": size, "third_person": mv["entry"],
                              "ticks": ticks}
        label(tag, (ox, 3.0, 0.02), 0.3, LABEL)
        print(tag, "built", n, flush=True)
        lane += 1

KEYS.flush()
scene.frame_start, scene.frame_end = 1, END
gm = bpy.data.materials.new("FP ground"); gm.use_nodes = True
N_, L_ = gm.node_tree.nodes, gm.node_tree.links
bs = N_["Principled BSDF"]; bs.inputs["Roughness"].default_value = 0.95
geo = N_.new("ShaderNodeNewGeometry"); ck = N_.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 1.0
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.16, 0.3, 0.1, 1)
L_.new(geo.outputs["Position"], ck.inputs["Vector"]); L_.new(ck.outputs["Color"], bs.inputs["Base Color"])
span = lane * 20.0
me = bpy.data.meshes.new("FP ground")
me.from_pydata([(-40, -200, 0), (span + 40, -200, 0), (span + 40, 60, 0), (-40, 60, 0)], [], [(0, 1, 2, 3)]); me.update()
me.materials.append(gm); link(bpy.data.objects.new("FP ground", me))
world = bpy.data.worlds.new("FP world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("FP sun", bpy.data.lights.new("FP sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(50), R(-10), R(-35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects.get("01 Flurry F2 - vanilla")
with open(os.path.join(FOLDER, "first_person_moves_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT, "lanes", lane, "frames", END)
