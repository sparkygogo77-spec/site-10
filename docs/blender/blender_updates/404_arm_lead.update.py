# Pass 404: the ring arm leads where you fly (Blender designer chat, 2026-10-14). J on 403 (screenshot of the dart with
# the ring arm up past the head): "arm should be animated in the directions a player could move with the arm leading
# the body by like .08s". Also: "L2 for the ease landing" (soft landing pick, pass 403).
# The ring arm now aims along the way you are actually moving (velocity): flat ahead when level (-90 deg, not up past
# the head), raised into a climb, lowered into a dive, swung left/right into turns. The body follows the same path
# 0.08 s (1.6 ticks) later. One course flies every direction: straight, hard right 60, hard left 90, climb 30, dive 30,
# level. Free arm A2 (slightly forward of the body line) until J picks.
#   D1 pure lead: arm = where you move now, body = where you moved 0.08 s ago.
#   D2 lead + anticipation: the arm also overshoots the turn by 25% of its rate, then settles.
#   D3 lead + bank: D1 plus the body banking into turns (up to 35 deg, J's earlier pick).
# Cameras "Cam D1".."Cam D3" (chase, behind and above, turning with the body), "Cam D1 close" (side, following, for the
# arm), "Cam D1 top" (overhead), "Cam all". Writes LanternLive\arm_lead_poses.json, builds LanternLive\arm_lead.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "arm_lead.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Arm Lead")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Arm Lead")
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


def euler_of(Rm):
    """XYZ euler (x, y, z) of R = Rz @ Ry @ Rx, the inverse of rot()."""
    y = math.asin(max(-1.0, min(1.0, -Rm[2, 0])))
    return (math.atan2(Rm[2, 1], Rm[2, 2]), y, math.atan2(Rm[1, 0], Rm[0, 0]))
GROUND = 24.0
A = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # MC model axes -> Blender axes (x, z, -y)


def rot(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def corners(part, pivot, r):
    a, b = BOX[part]
    pts = np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])], float)
    return pts @ rot(*r).T + np.asarray(pivot, float)


def solve(p):
    """Pose (ring = right side) -> per part rotation and pivot. The body turns about the hips, the legs hang from the
    hips, grounded poses drop the hips until the lowest foot touches, `sink` lowers the torso into the legs."""
    rot_ = {"body": p.get("body", (0, 0, 0)), "head": p.get("head", (0, 0, 0))}
    # the neck bends at most ~57 degrees back from the body, so a flat flyer looks ahead instead of folding the head
    # back into his own chest (J, F3)
    hb = rot_["head"]; rot_["head"] = (max(hb[0], rot_["body"][0] - 1.0), hb[1], hb[2])
    for k, part, sgn in (("ring", "rarm", 1), ("free", "larm", -1), ("ringleg", "rleg", 1), ("freeleg", "lleg", -1)):
        x, y, z = p.get(k, (0, 0, 0))
        rot_[part] = (x, sgn * y, sgn * z)
    Rb = rot(*rot_["body"])
    sink = float(p.get("sink", 0.0))
    piv = {}

    def place(d):
        hip = np.array([0.0, 12.0 + d, -float(p.get("fwd", 0.0))])
        neck = hip + Rb @ np.array([0.0, -12.0, 0.0]) + np.array([0.0, sink, 0.0])
        piv["body"] = neck; piv["head"] = neck.copy()
        piv["rarm"] = neck + Rb @ np.array([-5.0, 2.0, 0.0]); piv["larm"] = neck + Rb @ np.array([5.0, 2.0, 0.0])
        piv["rleg"] = hip + Rb @ np.array([-1.9, 0.0, 0.0]) * np.array([1, 0, 1]) + np.array([0, 0, 0])
        piv["lleg"] = hip + Rb @ np.array([1.9, 0.0, 0.0]) * np.array([1, 0, 1])
        for leg, shin in (("rleg", "rshin"), ("lleg", "lshin")):
            piv[shin] = piv[leg] + rot(*rot_[leg]) @ np.array([0.0, 6.0, 0.0])

    for leg, shin, kk in (("rleg", "rshin", "ringknee"), ("lleg", "lshin", "freeknee")):
        k = float(p.get(kk, 0.0))
        rot_[shin] = euler_of(rot(*rot_[leg]) @ rot(k, 0, 0))
    place(0.0)
    d = 0.0
    if p.get("grounded", True):
        low = max(corners(k, piv[k], rot_[k])[:, 1].max() for k in ("rleg", "lleg", "rshin", "lshin"))
        d = GROUND - low
        place(d)
    return {k: (np.asarray(rot_[k], float), piv[k]) for k in PARTS}


def hand_point(sol, part="rarm"):
    r, pv = sol[part]
    return np.array([-1.0 if part == "rarm" else 1.0, 10.0, 0.0]) @ rot(*r).T + pv


def to_bl(v):
    v = np.asarray(v, float)
    return A @ np.array([v[0], v[1] - GROUND, v[2]]) / 16.0


def mat(name, rgb, emit=0.0, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
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


SKIN = mat("KL skin", (0.62, 0.42, 0.3)); SHIRT = mat("KL shirt", (0.04, 0.28, 0.12))
PANTS = mat("KL pants", (0.03, 0.05, 0.09)); HAIR = mat("KL hair", (0.08, 0.05, 0.03))
RINGM = mat("KL ring", (0.1, 1.0, 0.25), emit=3.0)
SHOES = mat("KL shoes", (0.12, 0.12, 0.13))
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


def make_player(tag):
    objs = {}
    for k in PARTS:
        a, b = BOX[k]
        o = link(bpy.data.objects.new(f"KL {tag} {k}", box_mesh(f"KL {tag} {k}", a, b, PART_MAT[k])))
        o.rotation_mode = "XYZ"
        objs[k] = o
    # details as children: hair cap, hands, ring
    for k, (a, b), m in (("head", ((-4.05, -8.05, -4.05), (4.05, -6.5, 4.05)), HAIR),
                         ("rarm", ((-3.02, 7, -2.02), (1.02, 10.02, 2.02)), SKIN),
                         ("larm", ((-1.02, 7, -2.02), (3.02, 10.02, 2.02)), SKIN),
                         ("rarm", ((-3.4, 6.2, -2.4), (1.4, 7.4, 2.4)), RINGM),
                         ("rshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES),
                         ("lshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES)):
        c = link(bpy.data.objects.new(f"KL {tag} {k} detail", box_mesh(f"KL {tag} {k} d", a, b, m)))
        c.parent = objs[k]
        if m is RINGM:
            objs["ring"] = c
    return objs


def set_pose(objs, sol, origin, frame, side=0.0):
    rs = np.array([[math.cos(side), -math.sin(side), 0], [math.sin(side), math.cos(side), 0], [0, 0, 1]])
    for k in PARTS:
        r, pv = sol[k]
        Rb = rs @ (A @ rot(*r) @ A.T)
        loc = rs @ to_bl(pv) + np.asarray(origin)
        o = objs[k]
        M = np.eye(4); M[:3, :3] = Rb; M[:3, 3] = loc
        from mathutils import Matrix
        o.matrix_world = Matrix(M.tolist())
        o.keyframe_insert("location", frame=frame); o.keyframe_insert("rotation_euler", frame=frame)


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c



def smooth(t):
    return t * t * (3 - 2 * t)


def mixp(a, b, w):
    keys = set(a) | set(b)
    out = {}
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if k in ("grounded",):
            continue
        if isinstance(va, tuple) or isinstance(vb, tuple):
            va = np.array(va if va is not None else (0, 0, 0), float); vb = np.array(vb if vb is not None else (0, 0, 0), float)
            out[k] = tuple(va + (vb - va) * w)
        else:
            va = 0.0 if va is None else va; vb = 0.0 if vb is None else vb
            out[k] = va + (vb - va) * w
    return out

def set_pose_w(objs, sol, origin, frame, byaw, phi, roll):
    """Like set_pose, plus a bank: roll about the travel direction, so the top of the body tips into the turn."""
    def Rz(a):
        return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Ry = np.array([[math.cos(roll), 0, math.sin(roll)], [0, 1, 0], [-math.sin(roll), 0, math.cos(roll)]])
    W = Rz(phi) @ Ry @ Rz(byaw - phi)
    chest = np.array([0, 0, 1.0])
    for k in PARTS:
        r, pv = sol[k]
        Rb = W @ (A @ rot(*r) @ A.T)
        loc = W @ (to_bl(pv) - chest) + chest + np.asarray(origin)
        M = np.eye(4); M[:3, :3] = Rb; M[:3, 3] = loc
        objs[k].matrix_world = Matrix(M.tolist())
        objs[k].keyframe_insert("location", frame=frame); objs[k].keyframe_insert("rotation_euler", frame=frame)



# ================================================================== pass 404
T_END = 130
V = 0.7                      # blocks a tick, cruise
LEAD = 1.6                   # ticks: 0.08 s
# the course: (tick, heading deg clockwise from the start, climb deg)
KEYS = [(0, 0, 0), (14, 0, 0), (26, 60, 0), (36, 60, 0), (52, -30, 0), (62, -30, 0), (72, -30, 30), (82, -30, 30),
        (94, -30, -30), (104, -30, -30), (114, -30, 0), (130, -30, 0)]
TAKES = ["D1", "D2", "D3"]
NAMES = {"D1": "arm leads 0.08 s", "D2": "arm leads + anticipates", "D3": "arm leads + bank"}
BANK = R(35.0)


def course(t):
    """Heading (deg clockwise) and climb (deg) at fractional tick t, smoothstep between keys."""
    t = max(0.0, min(KEYS[-1][0], t))
    for (t0, h0, c0), (t1, h1, c1) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1:
            w = smooth((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return h0 + (h1 - h0) * w, c0 + (c1 - c0) * w
    return KEYS[-1][1], KEYS[-1][2]


FLYB = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03),
            freeknee=0.4, grounded=False)


def pose_at(take, t):
    """Returns pose, body heading/climb (deg), arm heading/climb (deg), roll (rad)."""
    hb, cb = course(t - LEAD)                    # the body follows the path 0.08 s late
    ha, ca = course(t)                           # the arm points where you are moving now
    if take == "D2":
        h1, c1 = course(t - 2.0)
        ha += 0.25 * (ha - h1) * 2.0; ca += 0.25 * (ca - c1) * 2.0
    roll = 0.0
    if take == "D3":
        h_prev, _ = course(t - LEAD - 1.0)
        rate = hb - h_prev                        # deg a tick, + = turning right
        roll = -BANK * max(-1.0, min(1.0, rate / 6.0))
    c = R(cb)
    p = dict(FLYB)
    p["body"] = (1.42 - c, 0, 0)
    p["head"] = (-1.25 - c, 0, 0)
    p["ringleg"] = (1.38 - c, 0, 0.03); p["freeleg"] = (1.3 - c, 0, -0.03)
    dyaw = R(ha - hb)                            # arm yaw relative to the body (+ = to the right)
    p["ring"] = (-(math.pi / 2) - R(ca), dyaw, 0.02)
    p["free"] = (1.42 - c - 0.3, 0, -0.08)       # free arm A2
    return p, hb, cb, ha, ca, roll


try:
    tree = bpy.data.node_groups.new("AL Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.6), ("Strength", 0.5), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
TRAIL = mat("AL trail", (0.1, 1.0, 0.3), emit=3.0)
LABEL = mat("AL label", (0.85, 1.0, 0.9), emit=2.0)

dump = {"format": "per take, per tick: part rot (xRot,yRot,zRot rad, model space before the body yaw/roll), offset_px, "
                  "pos [right, forward, up] blocks, body_heading/body_climb and arm_heading/arm_climb (deg; heading "
                  "clockwise), roll_deg (+ = right side down). 20 ticks a second.",
        "rule": "ring arm: xRot = -(90 deg + arm_climb), yRot = arm_heading - body_heading; the arm follows the player's "
                "movement input/velocity now, the body follows the same direction 1.6 ticks (0.08 s) later",
        "lead_ticks": LEAD, "takes": {}}
LANE = 90.0
for li, take in enumerate(TAKES):
    ox = li * LANE
    objs = make_player(take)
    rm = mat(f"AL ring {take}", (0.1, 1.0, 0.25), emit=6.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"AL {take} mover", None)); mover.empty_display_size = 0.1
    mover.rotation_mode = "XYZ"
    pos = np.array([ox, 0.0, 8.0]); ticks = []; trail = []
    for t in range(T_END + 1):
        ha_now, ca_now = course(t)                # velocity = the movement direction now
        phi_v = -R(ha_now)
        vel = V * np.array([-math.sin(phi_v) * math.cos(R(ca_now)), -math.cos(phi_v) * math.cos(R(ca_now)), math.sin(R(ca_now))])
        if t > 0:
            pos = pos + vel
        p, hb, cb, ha, ca, roll = pose_at(take, t)
        sol = solve(p)
        phi_b = -R(hb)
        set_pose_w(objs, sol, pos, t + 1, phi_b, phi_b, roll)
        mover.location = tuple(pos); mover.rotation_euler = (0, 0, phi_b)
        mover.keyframe_insert("location", frame=t + 1); mover.keyframe_insert("rotation_euler", frame=t + 1)
        if t % 2 == 0:
            trail.append((pos[0], pos[1], 0.05))
        ticks.append({"pos": [round(float(-(pos[0] - ox)), 3), round(float(-pos[1]), 3), round(float(pos[2]), 3)],
                      "body_heading": round(hb, 2), "body_climb": round(cb, 2), "arm_heading": round(ha, 2),
                      "arm_climb": round(ca, 2), "roll_deg": round(-math.degrees(roll), 1),
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    dump["takes"][take] = {"name": NAMES[take], "ticks": ticks}
    cu = bpy.data.curves.new(f"AL {take} path", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.08
    sp = cu.splines.new("POLY"); sp.points.add(len(trail) - 1)
    for i, q in enumerate(trail):
        sp.points[i].co = (*q, 1)
    po = link(bpy.data.objects.new(f"AL {take} ground track", cu)); po.data.materials.append(TRAIL)
    lb = bpy.data.curves.new(f"AL label {take}", "FONT"); lb.body = f"{take}  {NAMES[take]}"; lb.size = 1.2
    lb.align_x = "CENTER"
    tl = link(bpy.data.objects.new(f"AL label {take}", lb)); tl.location = (ox, 6.0, 0.05); tl.data.materials.append(LABEL)
    # chase camera: behind and above, turning with the body (like the game's third-person camera)
    scene.frame_set(1); bpy.context.view_layer.update()
    st = np.array([ox, 0.0, 8.0])
    c = cam(f"Cam {take}", tuple(st + np.array([-0.8, 5.5, 1.8])), tuple(st + np.array([0.2, -6.0, 0.6])), 30)
    c.parent = mover; c.matrix_parent_inverse = mover.matrix_world.inverted()
    cc = cam(f"Cam {take} close", tuple(st + np.array([6.0, -0.5, 0.6])), tuple(st + np.array([0, -0.6, 0.3])), 35)
    cc.parent = mover; cc.matrix_parent_inverse = mover.matrix_world.inverted()
    cam(f"Cam {take} top", (ox + 10, -30, 95), (ox + 10, -30.5, 0), 35)
    print(take, "built", flush=True)

with open(os.path.join(FOLDER, "arm_lead_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

for o in scene.objects:
    ad = o.animation_data
    if ad and ad.action:
        try:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        except Exception:
            pass

scene.frame_start, scene.frame_end = 1, T_END
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE, -30, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "AL ground"; g.scale = (400, 400, 1)
gm = bpy.data.materials.new("AL ground"); gm.use_nodes = True
N, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 400
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("AL world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("AL sun", bpy.data.lights.new("AL sun", "SUN")))
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
cam("Cam all", (LANE, 60, 80), (LANE, -30, 0), 30)
scene.camera = bpy.data.objects["Cam D1"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def _after():
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    for sp in a.spaces:
                        if sp.type == "VIEW_3D":
                            sp.region_3d.view_perspective = "CAMERA"
                            sp.shading.type = "MATERIAL"
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
