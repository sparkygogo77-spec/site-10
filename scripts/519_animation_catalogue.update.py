# Pass 519: the animation catalogue (Chats C/D, 2026-10-14). J: "some third person animations dont have 1st person and
# vice versa, i need them all in a blender file but ill make a report here" -> "All picked so far".
# Every picked (or in-game) animation replayed from its hand-off poses JSON, each one twice:
#   3p lane (x = lane * 14):         the full player, camera "NN <name> - 3rd person" over the right shoulder, following.
#   fp lane (same lane, x + 1000):   arms + ring (+ lantern) only, as Minecraft draws first person, camera
#                                    "NN <name> - 1st person" riding the eyes (70 deg vertical field of view).
# Effects (craters, beams, puffs, domes) are NOT here: they live in each take's own .blend (listed in the README).
# The lantern is the real Dark Lantern at its true size: 16 px (one block) tall with the handle, 6.2 px wide.
# Reads the poses from the repo (KL_REPO, default /home/claude/site-10). Builds LanternLive\animation_catalogue.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler

R = math.radians
REPO = os.environ.get("KL_REPO", "/home/claude/site-10")
HO = os.path.join(REPO, "docs", "handoff")
RV = os.path.join(REPO, "docs", "blender", "review")
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "animation_catalogue.blend")
old = bpy.data.scenes.get("Animation Catalogue")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Animation Catalogue")
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


# ------------------------------------------------------------------ rig (Minecraft model space: px, y down, -z forward)
PIVOT = {"head": (0, 0, 0), "body": (0, 0, 0), "rarm": (-5, 2, 0), "larm": (5, 2, 0),
         "rleg": (-1.9, 12, 0), "lleg": (1.9, 12, 0), "rshin": (-1.9, 18, 0), "lshin": (1.9, 18, 0)}
BOX = {"head": ((-4, -8, -4), (4, 0, 4)), "body": ((-4, 0, -2), (4, 12, 2)), "rarm": ((-3, -2, -2), (1, 10, 2)),
       "larm": ((-1, -2, -2), (3, 10, 2)), "rleg": ((-2, 0, -2), (2, 6, 2)), "lleg": ((-2, 0, -2), (2, 6, 2)),
       "rshin": ((-2, 0, -2), (2, 6, 2)), "lshin": ((-2, 0, -2), (2, 6, 2))}
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")
FP_PARTS = ("rarm", "larm")
GROUND = 24.0
A = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # MC model axes -> Blender axes (x, z, -y)
FPX = 1000.0                                                 # the first-person lanes sit this far along x
LANE = 14.0


def rot(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def to_bl(v):
    v = np.asarray(v, float)
    return A @ np.array([v[0], v[1] - GROUND, v[2]]) / 16.0


def Rz(a):
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def world_of(M_rig_R, M_rig_t, origin, side, roll):
    """Rig-space rotation/point -> Blender world 4x4, with the body yaw (side) and bank (roll, about the chest)."""
    Ry = np.array([[math.cos(roll), 0, math.sin(roll)], [0, 1, 0], [-math.sin(roll), 0, math.cos(roll)]])
    W = Rz(side) @ Ry
    chest = np.array([0, 0, 1.0])
    M = np.eye(4)
    M[:3, :3] = W @ (A @ M_rig_R @ A.T)
    M[:3, 3] = W @ (to_bl(M_rig_t) - chest) + chest + np.asarray(origin)
    return Matrix(M.tolist())


def hand_point(parts, part="rarm"):
    r, pv = parts[part]
    return np.array([-1.0 if part == "rarm" else 1.0, 10.0, 0.0]) @ rot(*r).T + pv


# ------------------------------------------------------------------ fast keying (one action per object)
class Keys:
    def __init__(self):
        self.d = {}

    def add(self, o, frame, M):
        lst = self.d.setdefault(o, [])
        loc, q, _ = M.decompose()
        e = q.to_euler("XYZ", lst[-1][2]) if lst else q.to_euler("XYZ")
        lst.append((frame, tuple(loc), e.copy()))

    def flush(self):
        for o, lst in self.d.items():
            o.rotation_mode = "XYZ"
            o.location = lst[0][1]; o.rotation_euler = lst[0][2]
            o.animation_data_create()
            act = bpy.data.actions.new(o.name + " act")
            o.animation_data.action = act
            for path, j in (("location", 1), ("rotation_euler", 2)):
                for i in range(3):
                    fc = act.fcurve_ensure_for_datablock(o, path, index=i)
                    fc.keyframe_points.add(len(lst))
                    fc.keyframe_points.foreach_set("co", [v for r in lst for v in (r[0], r[j][i])])
                    fc.update()


KEYS = Keys()


# ------------------------------------------------------------------ materials and meshes
def mat(name, rgb, emit=0.0, rough=0.6, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    return m


SKIN = mat("KL skin", (0.62, 0.42, 0.3)); SHIRT = mat("KL shirt", (0.04, 0.28, 0.12))
PANTS = mat("KL pants", (0.03, 0.05, 0.09)); HAIR = mat("KL hair", (0.08, 0.05, 0.03))
SHOES = mat("KL shoes", (0.12, 0.12, 0.13)); STONE = mat("KL block", (0.45, 0.45, 0.47))
LABEL = mat("KL label", (0.8, 1.0, 0.85), emit=2.0)
AREA_LABEL = mat("KL area label", (1.0, 0.85, 0.3), emit=2.5)
PART_MAT = {"head": SKIN, "body": SHIRT, "rarm": SHIRT, "larm": SHIRT, "rleg": PANTS, "lleg": PANTS,
            "rshin": PANTS, "lshin": PANTS}


def box_mesh(name, a, b, m):
    a = np.array(a, float); b = np.array(b, float)
    pts = [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    verts = [tuple(A @ p / 16.0) for p in pts]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.materials.append(m)
    return me


def make_player(tag, parts, ringm):
    objs = {}
    for k in parts:
        a, b = BOX[k]
        objs[k] = link(bpy.data.objects.new(f"AC {tag} {k}", box_mesh(f"AC {tag} {k}", a, b, PART_MAT[k])))
    for k, (a, b), m in (("head", ((-4.05, -8.05, -4.05), (4.05, -6.5, 4.05)), HAIR),
                         ("rarm", ((-3.02, 7, -2.02), (1.02, 10.02, 2.02)), SKIN),
                         ("larm", ((-1.02, 7, -2.02), (3.02, 10.02, 2.02)), SKIN),
                         ("rarm", ((-3.4, 6.2, -2.4), (1.4, 7.4, 2.4)), ringm),
                         ("rshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES),
                         ("lshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES)):
        if k not in objs:
            continue
        c = link(bpy.data.objects.new(f"AC {tag} {k} detail", box_mesh(f"AC {tag} {k} d", a, b, m)))
        c.parent = objs[k]
    return objs


# ------------------------------------------------------------------ the Dark Lantern (true size)
LH = 16.0                                   # placed height with the handle (one block)
DL_H, DL_W, DL_BODY = 28.5, 11.0, 21.0      # dark_lantern.bbmodel: height, width, top of the body
S_DL = LH / DL_H
HW = DL_W * S_DL / 2                        # 3.09 px: the body is 6.2 px wide
BODY_H = DL_BODY * S_DL
BLOCK_TOP = GROUND - 16.0
LANTERN_BLOCK = (0.0, -15.0)                # L1c: the lantern stands on a block one block in front (rig x, z)


def import_lantern(tag):
    root = link(bpy.data.objects.new(f"AC {tag} lantern", None)); root.empty_display_size = 0.05
    glow_mats = []
    for name in ("dark_lantern", "dark_lantern_glow"):
        path = os.path.join(ASSETS, name + ".glb")
        if not os.path.exists(path):
            print("missing", path); continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            o.name = f"AC {tag} {o.name}"
            if o.type == "MESH":
                for i, m in enumerate(o.data.materials):
                    if m is None:
                        continue
                    for n in m.node_tree.nodes:
                        if n.type == "TEX_IMAGE":
                            n.interpolation = "Closest"
                    if "glow" in m.name.lower() or name.endswith("glow"):
                        m2 = m.copy(); m2.name = f"AC {tag} {m.name}"; o.data.materials[i] = m2
                        bsdf = next((n for n in m2.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                        if bsdf is not None:
                            bsdf.inputs["Emission Color"].default_value = (0.2, 1.0, 0.3, 1)
                            glow_mats.append(bsdf)
        for o in new:
            if o.parent is None:
                o.parent = root
    bpy.context.view_layer.update()
    from mathutils import Vector
    pts = [o.matrix_world @ Vector(c) for o in root.children_recursive if o.type == "MESH" for c in o.bound_box]
    if pts:
        P_ = np.array([tuple(p) for p in pts]); lo, hi = P_.min(0), P_.max(0)
        s = (LH / 16.0) / max(hi[2] - lo[2], 1e-6)
        for o in root.children:
            o.matrix_world = Matrix.Scale(s, 4) @ Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])) @ o.matrix_world
    lamp = link(bpy.data.objects.new(f"AC {tag} lantern lamp", bpy.data.lights.new(f"AC {tag} lamp", "POINT")))
    lamp.data.color = (0.55, 1.0, 0.6); lamp.data.energy = 0.0; lamp.data.shadow_soft_size = 0.2
    lamp.parent = root; lamp.location = (0, 0, LH / 32.0)
    return root, glow_mats, lamp


def lantern_on_block(tilt):
    x0, z0 = LANTERN_BLOCK
    a = tilt
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    piv = np.array([x0, BLOCK_TOP, z0 - HW]); base = np.array([x0, BLOCK_TOP, z0])
    return Rx, Rx @ (base - piv) + piv


def lantern_hung(grip, phx, phz):
    cz, sz_, cx, sx = math.cos(phx), math.sin(phx), math.cos(phz), math.sin(phz)
    Rr = np.array([[cz, -sz_, 0], [sz_, cz, 0], [0, 0, 1]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    return Rr, grip + Rr @ np.array([0.0, LH - 0.5, 0.0])


# ------------------------------------------------------------------ the catalogue: what, where from, how it moves
J = lambda *p: os.path.join(*p)
MF = J(HO, "2026-10-14-movement-flight", "poses")
BJ = J(HO, "2026-10-14-bundle-jar", "poses")
PL = J(HO, "2026-10-14-power-landing", "poses")
ENTRIES = [
    # (area, id, label, file, take key or None, root rule, source .blend)
    ("Movement", "F2", "F2 flight take-off", J(MF, "flight_takeoff_poses.json"), "F2", "fu_neg", "flight_takeoff.blend"),
    ("Movement", "S5a", "S5a sprint, lantern 43 deg", J(MF, "sprint_run2_poses.json"), "S5a", "sprint", "sprint_run2.blend"),
    ("Movement", "S5b", "S5b sprint, lantern 57 deg", J(MF, "sprint_run2_poses.json"), "S5b", "sprint", "sprint_run2.blend"),
    ("Movement", "H1", "H1 ground flight stop", J(MF, "ground_flight_poses.json"), "H1", "fu_neg", "ground_flight.blend"),
    ("Movement", "H2", "H2 ground flight stop", J(MF, "ground_flight_poses.json"), "H2", "fu_neg", "ground_flight.blend"),
    ("Movement", "H3", "H3 ground flight stop", J(MF, "ground_flight_poses.json"), "H3", "fu_neg", "ground_flight.blend"),
    ("Movement", "S1", "S1 double jump, standing", J(BJ, "403_S1.json"), None, "pos", "movement\\takeoff_small2.blend"),
    ("Movement", "S2a", "S2a double jump, spring", J(BJ, "403_S2a.json"), None, "pos", "movement\\takeoff_small2.blend"),
    ("Movement", "S2b", "S2b double jump, fastest", J(BJ, "403_S2b.json"), None, "pos", "movement\\takeoff_small2.blend"),
    ("Movement", "R3A1", "R3A1 running dart, arm side", J(BJ, "403_R3A1.json"), None, "pos", "movement\\takeoff_small2.blend"),
    ("Movement", "R3A2", "R3A2 running dart, arm fwd", J(BJ, "403_R3A2.json"), None, "pos", "movement\\takeoff_small2.blend"),
    ("Movement", "R3A3", "R3A3 running dart, arm out", J(BJ, "403_R3A3.json"), None, "pos", "movement\\takeoff_small2.blend"),
    ("Movement", "L4", "L4 double-tap landing", J(BJ, "405_L4.json"), None, "pos", "movement\\land_tight.blend"),
    ("Movement", "L5", "L5 double-tap landing (default)", J(BJ, "405_L5.json"), None, "pos", "movement\\land_tight.blend"),
    ("Movement", "L6", "L6 double-tap landing", J(BJ, "405_L6.json"), None, "pos", "movement\\land_tight.blend"),
    ("Movement", "D1", "D1 ring arm leads", J(BJ, "404_arm_lead_D1-D3.json"), "D1", "pos404", "movement\\arm_lead.blend"),
    ("Movement", "D2", "D2 arm leads + anticipation", J(BJ, "404_arm_lead_D1-D3.json"), "D2", "pos404", "movement\\arm_lead.blend"),
    ("Movement", "D3", "D3 arm leads + bank", J(BJ, "404_arm_lead_D1-D3.json"), "D3", "pos404", "movement\\arm_lead.blend"),
    ("Movement", "D0", "D0 power landing, stop dead", J(PL, "D0_stop_dead.json"), None, "fu_neg", "power_slide.blend"),
    ("Movement", "A3", "A3 power landing, dissolve", J(PL, "A3_dissolve.json"), None, "fu_neg", "power_slide.blend"),
    ("Movement", "B2", "B2 power landing, plough", J(PL, "B2_plough.json"), None, "fu_neg", "power_slide.blend"),
    ("Lantern", "K3c", "K3c kneel, pick the lantern up", J(HO, "2026-10-14-lantern-charge", "poses", "kneel_lean4_poses.json"), "K3c", "carry", "kneel_lean4.blend"),
    ("Lantern", "K3cR", "set down (K3c backwards)", J(HO, "2026-10-14-lantern-charge", "poses", "kneel_lean4_poses.json"), "K3c", "carry_rev", "none yet"),
    ("Lantern", "C6a", "L1c charge in 6 s (C6a timing)", J(RV, "601_lantern_charge6", "lantern_charge6_poses.json"), "C6a", "block", "lanterns\\lantern_charge6.blend"),
    ("Combat", "R2a", "R2a hammer overhead", J(HO, "2026-10-14-construct-hammer", "poses", "combat_round4_poses.json"), "R2a", "fwdb", "combat\\combat_round4.blend"),
    ("Combat", "R2b", "R2b hammer from the side", J(HO, "2026-10-14-construct-hammer", "poses", "combat_round4_poses.json"), "R2b", "fwdb", "combat\\combat_round4.blend"),
    ("Combat", "R3a", "R3a dash strike (4-tick dash)", J(RV, "505_dash_strike5", "dash_strike5_poses.json"), "R3a-4", "fwdb", "combat\\dash_strike5.blend"),
    ("Combat", "R4b", "R4b absorb and fire back", J(RV, "503_combat_round4", "combat_round4_poses.json"), "R4b", "fwdb", "combat\\combat_round4.blend"),
    ("Combat", "F2f", "F2 flurry jab-cross-backfist", J(RV, "507_flurry5", "flurry5_poses.json"), "F2", "side", "combat\\flurry5.blend"),
    ("Combat", "A1", "A1 flying flurry, crater ahead", J(RV, "509_flying_flurry", "flying_flurry_poses.json"), "A1", "fu_neg", "combat\\flying_flurry.blend"),
    ("Combat", "A2", "A2 flying flurry, 50 blocks", J(RV, "509_flying_flurry", "flying_flurry_poses.json"), "A2", "fu_neg", "combat\\flying_flurry.blend"),
    ("Combat", "A3f", "A3 flying flurry, crater below", J(RV, "509_flying_flurry", "flying_flurry_poses.json"), "A3", "fu_neg", "combat\\flying_flurry.blend"),
    ("Combat", "S3H5", "S3 big slam (in game now)", J(RV, "510_flight_slam4", "flight_slam4_poses.json"), "S3 H5", "fu_pos", "combat\\flight_slam4.blend"),
    ("Combat", "P1", "P1 primed slam (shift)", J(RV, "518_primed_slam", "primed_slam_poses.json"), "P1", "fu_pos", "combat\\primed_slam.blend"),
    ("Combat", "P2", "P2 primed super-jump slam", J(RV, "518_primed_slam", "primed_slam_poses.json"), "P2", "fu_pos", "combat\\primed_slam.blend"),
    ("Combat", "U1", "U1 unprimed slide", J(RV, "518_primed_slam", "primed_slam_poses.json"), "U1", "fu_pos", "combat\\primed_slam.blend"),
]

_cache = {}


def load(path):
    if path not in _cache:
        with open(path) as fh:
            _cache[path] = json.load(fh)
    return _cache[path]


def frames_of(entry):
    """-> list of dict(parts={k: (rot, pivot)}, origin(xyz rel), side, roll, glow, lantern=(R, t) or None), meta"""
    area, tid, label, path, key, rule, src = entry
    d = load(path)
    tk = d if key is None else d["takes"][key]
    ticks = tk["ticks"]
    out = []
    if rule == "sprint":
        loop = ticks[:-1] if len(ticks) > 1 else ticks
        ticks = loop * 3
    if rule == "carry_rev":
        ticks = list(reversed(ticks))
    for t, k in enumerate(ticks):
        P = k["parts"] if "parts" in k else {kk: k[kk] for kk in PARTS}
        parts = {kk: (np.array(P[kk]["rot"], float), np.array(PIVOT[kk], float) + np.array(P[kk]["offset_px"], float))
                 for kk in PARTS}
        o = np.zeros(3); side = 0.0; roll = 0.0; cam_yaw = False
        if rule in ("fu_neg", "fu_pos"):
            o = np.array([0.0, (-1 if rule == "fu_neg" else 1) * k.get("forward", 0.0), k.get("up", 0.0)])
            side = k.get("spin_yaw", 0.0)
        elif rule == "sprint":
            o = np.array([0.0, -tk.get("blocks_per_tick", 0.28) * t, 0.0])
        elif rule == "fwdb":
            o = np.array([0.0, -k.get("fwd_blocks", 0.0), 0.0])
        elif rule == "side":
            side = k.get("side_yaw", 0.0)
        elif rule == "pos":
            p = k["pos"]; o = np.array([-p[0], -p[1], p[2]])
            if tk.get("run_deg") is not None:
                side = -R(tk["heading_deg"][min(t, len(tk["heading_deg"]) - 1)]); cam_yaw = True
        elif rule == "pos404":
            p = k["pos"]; o = np.array([-p[0], -p[1], p[2]])
            side = -R(k["body_heading"]); roll = -R(k.get("roll_deg", 0.0)); cam_yaw = True
        g = float(k.get("glow", 3.0))
        out.append(dict(parts=parts, origin=o, side=side, roll=roll, glow=g, cam_yaw=cam_yaw, tilt=k.get("tilt"),
                        swing=k.get("swing")))
    meta = {"lantern": None}
    if rule in ("carry", "carry_rev"):
        meta["lantern"] = "carry"
        carry = tk.get("carry_from_tick", 30)
        # forward-time lantern path, then reversed for the set-down
        fwd = ticks if rule == "carry" else list(reversed(ticks))
        sols = [{kk: (np.array(f["parts"][kk]["rot"], float), np.array(PIVOT[kk], float) + np.array(f["parts"][kk]["offset_px"], float))
                 for kk in ("rarm",)} for f in fwd]
        hp0 = hand_point(sols[carry], "rarm"); spot = np.array([hp0[0], GROUND, hp0[2]])
        lan = []
        for t, f in enumerate(fwd):
            if t >= carry:
                sw = f.get("swing") or [0.0, 0.0]
                lan.append(lantern_hung(hand_point(sols[t], "rarm"), sw[0], sw[1]))
            else:
                lan.append((np.eye(3), spot))
        if rule == "carry_rev":
            lan = list(reversed(lan))
        for fr, l_ in zip(out, lan):
            fr["lantern"] = l_
            fr["glow01"] = fr["glow"]
    elif rule == "block":
        meta["lantern"] = "block"
        for fr in out:
            fr["lantern"] = lantern_on_block(fr["tilt"] or 0.0)
            fr["glow01"] = fr["glow"]
    elif tid in ("S5a", "S5b"):
        meta["lantern"] = "hand"                   # carried in the free hand by the handle (no swing here)
        for fr in out:
            fr["lantern"] = lantern_hung(hand_point(fr["parts"], "larm"), 0.0, 0.0)
            fr["glow01"] = 0.12
    return out, meta


def cam(name, loc, look, lens=40, parent=None):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_start = 0.05
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


def label(text, loc, size, m):
    cu = bpy.data.curves.new("AC label " + text, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("AC label " + text, cu)); tl.location = loc
    tl.data.materials.append(m)
    return tl


NAMES = {  # plain camera names (J: "I need the cameras named for each properly")
    "F2": "Flight take-off F2", "S5a": "Sprint with lantern S5a", "S5b": "Sprint with lantern S5b",
    "H1": "Ground flight wall stop H1", "H2": "Ground flight wall stop H2", "H3": "Ground flight wall stop H3",
    "S1": "Double jump standing S1", "S2a": "Double jump standing S2a", "S2b": "Double jump standing S2b",
    "R3A1": "Double jump running A1", "R3A2": "Double jump running A2", "R3A3": "Double jump running A3",
    "L4": "Soft landing L4", "L5": "Soft landing L5", "L6": "Soft landing L6",
    "D1": "Ring arm leads flight D1", "D2": "Ring arm leads flight D2", "D3": "Ring arm leads flight D3",
    "D0": "Power landing stop dead D0", "A3": "Power landing dissolve A3", "B2": "Power landing plough B2",
    "K3c": "Lantern pick up K3c", "K3cR": "Lantern set down (stand-in)", "C6a": "Lantern charge L1c",
    "R2a": "Hammer overhead R2a", "R2b": "Hammer from the side R2b", "R3a": "Dash strike R3a",
    "R4b": "Absorb and fire back R4b", "F2f": "Flurry F2", "A1": "Flying flurry down A1",
    "A2": "Flying flurry level A2", "A3f": "Flying flurry steep A3", "S3H5": "Big flight slam S3",
    "P1": "Primed flight slam P1", "P2": "Primed super-jump slam P2", "U1": "Unprimed slide U1",
}
EYE_PX = np.array([0.0, -5.0, -4.3])          # eye height in the head (1.62 of 1.8 blocks), just in front of the face
END = 0
lanes = []
area_prev = None
li = 0
for entry in ENTRIES:
    area, tid, lab, path, key, rule, src = entry
    try:
        frames, meta = frames_of(entry)
    except Exception as e:
        print("SKIP", tid, e); continue
    if area != area_prev:
        if area_prev is not None:
            li += 1                                   # a gap between areas
        label(area.upper(), (li * LANE, 6.0, 0.02), 1.2, AREA_LABEL)
        label(area.upper(), (FPX + li * LANE, 6.0, 0.02), 1.2, AREA_LABEL)
        area_prev = area
    ox = li * LANE
    END = max(END, len(frames))
    ringm = mat(f"AC ring {tid}", (0.1, 1.0, 0.25), emit=3.0)
    tp = make_player(tid + " 3p", PARTS, ringm)
    fp = make_player(tid + " fp", FP_PARTS, ringm)
    eye = link(bpy.data.objects.new(f"AC {tid} fp eye", None)); eye.empty_display_size = 0.08
    mover = link(bpy.data.objects.new(f"AC {tid} mover", None)); mover.empty_display_size = 0.1
    lan3 = lanf = None
    if meta["lantern"]:
        lan3 = import_lantern(tid + " 3p"); lanf = import_lantern(tid + " fp")
        if meta["lantern"] == "block":
            for base_x, tag in ((ox, "3p"), (FPX + ox, "fp")):
                bx, bz = LANTERN_BLOCK
                blk = link(bpy.data.objects.new(f"AC {tid} {tag} block", box_mesh(f"AC {tid} {tag} block",
                                                (bx - 8, BLOCK_TOP, bz - 8), (bx + 8, GROUND, bz + 8), STONE)))
                blk.location = (base_x, 0, GROUND / 16.0)
    sock = ringm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for t, fr in enumerate(frames):
        f = t + 1
        for base_x, objs, lan in ((ox, tp, lan3), (FPX + ox, fp, lanf)):
            origin = np.array([base_x, 0.0, 0.0]) + fr["origin"]
            for k, o in objs.items():
                r, pv = fr["parts"][k]
                KEYS.add(o, f, world_of(rot(*r), pv, origin, fr["side"], fr["roll"]))
            if lan is not None:
                Rl, tl_ = fr["lantern"]
                KEYS.add(lan[0], f, world_of(Rl, tl_, origin, fr["side"], fr["roll"]))
            if base_x != ox:
                r, pv = fr["parts"]["head"]
                Mh = world_of(rot(*r), pv + rot(*r) @ EYE_PX, origin, fr["side"], fr["roll"])
                KEYS.add(eye, f, Mh)
            else:
                yaw = fr["side"] if fr["cam_yaw"] else 0.0
                M = np.eye(4); M[:3, :3] = Rz(yaw); M[:3, 3] = origin
                KEYS.add(mover, f, Matrix(M.tolist()))
        if "glow01" in fr:
            e = 2.0 + 10.0 * min(1.25, fr["glow01"]) if meta["lantern"] != "hand" else 3.0
            for lan in (lan3, lanf):
                for bsdf in lan[1]:
                    s = bsdf.inputs["Emission Strength"]; s.default_value = 1.0 + 5.0 * min(1.3, fr["glow01"])
                    s.keyframe_insert("default_value", frame=f)
                lan[2].data.energy = 25.0 * fr["glow01"]; lan[2].data.keyframe_insert("energy", frame=f)
        else:
            e = fr["glow"]
        sock.default_value = e; sock.keyframe_insert("default_value", frame=f)
    # cameras: over the right shoulder (following) and the eyes
    st = np.array([ox, 0.0, 0.0]) + frames[0]["origin"]
    nm = f"{len(lanes) + 1:02d} {NAMES.get(tid, tid)}"
    c3 = cam(f"{nm} - 3rd person", tuple(st + np.array([-1.5, 4.0, 2.7])), tuple(st + np.array([0.3, -4.0, 0.8])), 28)
    c3.parent = mover; c3.matrix_parent_inverse = Matrix.Translation(tuple(st)).inverted()
    cf = link(bpy.data.objects.new(f"{nm} - 1st person", bpy.data.cameras.new(f"{nm} - 1st person")))
    cf.data.sensor_fit = "VERTICAL"; cf.data.angle = R(70); cf.data.clip_start = 0.02
    cf.parent = eye; cf.location = (0, 0, 0); cf.rotation_euler = (R(90), 0, R(180))
    label(nm, (ox, 3.0, 0.02), 0.32, LABEL)
    label(nm, (FPX + ox, 3.0, 0.02), 0.32, LABEL)
    lanes.append(dict(id=tid, camera=nm, area=area, label=lab, lane_x=ox, ticks=len(frames), source=src,
                      lantern=meta["lantern"]))
    print(tid, "built", len(frames), flush=True)
    li += 1

KEYS.flush()
scene.frame_start, scene.frame_end = 1, END

# ground: a one-block checker under both halves
gm = bpy.data.materials.new("AC ground"); gm.use_nodes = True
N, L = gm.node_tree.nodes, gm.node_tree.links
bs = N["Principled BSDF"]; bs.inputs["Roughness"].default_value = 0.95
geo = N.new("ShaderNodeNewGeometry"); ck = N.new("ShaderNodeTexChecker")
ck.inputs["Scale"].default_value = 1.0
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.16, 0.3, 0.1, 1)
L.new(geo.outputs["Position"], ck.inputs["Vector"]); L.new(ck.outputs["Color"], bs.inputs["Base Color"])
span = li * LANE
for gx, nm in ((span / 2, "AC ground 3p"), (FPX + span / 2, "AC ground fp")):
    me = bpy.data.meshes.new(nm)
    hx, hy = span / 2 + 20, 160
    me.from_pydata([(-hx, -hy, 0), (hx, -hy, 0), (hx, 40, 0), (-hx, 40, 0)], [], [(0, 1, 2, 3)]); me.update()
    me.materials.append(gm)
    g = link(bpy.data.objects.new(nm, me)); g.location = (gx - 7, 0, 0)

world = bpy.data.worlds.new("AC world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("AC sun", bpy.data.lights.new("AC sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(50), R(-10), R(-35))
ov = cam("00 Overview of all lanes", (span / 2, 30.0, 26.0), (span / 2, -6.0, 0.0), 24)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects.get("01 Flight take-off F2 - 3rd person") or ov
with open(os.path.join(FOLDER, "animation_catalogue_lanes.json"), "w") as fh:
    json.dump({"fp_offset_x": FPX, "lane_width": LANE, "frames": END, "lanes": lanes}, fh, indent=1)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT, "takes", len(lanes), "frames", END)
