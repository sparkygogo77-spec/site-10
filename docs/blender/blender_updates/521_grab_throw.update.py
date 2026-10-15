# Pass 521: grab and throw (Chat C, combat, 2026-10-15). J (503): "grab-throw later" -> picked now: a construct hand forms
# from the ring, grabs the mob, and flings it where you look; what it hits craters (D0 rule on the wall face).
#   G1 reach and fling: the hand shoots out on a tether (6 blocks), grabs, yanks the mob up in front of you, winds back
#      over your right shoulder and flings it along your crosshair.
#   G2 overhead whip: grabs, swings the mob up over your head and behind, then whips it over and down the crosshair.
#   G3 spin throw: grabs, pulls it in, you spin once with it held at arm's length, release facing the crosshair.
# The crosshair is 12 degrees right of the mob, so the throw visibly goes where you look, not back where it came from.
# Mob flight: 1.9-2.2 blocks a tick along the look (+ a little lift), gravity 0.08, drag 0.98, tumbling; it hits a stone
# wall 16 blocks out, craters a 3x3 in its face (centre lit on impact, gone 4 ticks later; the ring of 8 lit at once and
# gone at 6) and sticks in the hole. The hand closes on the grab, opens on release and dissolves to pixels.
# Cameras "NN <take> - 3rd person", "NN <take> - side", "NN <take> - 1st person". Builds LanternLive\combat\grab_throw.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

_src = os.path.join(os.environ.get("KL_REPO", "/home/claude/site-10"), "docs", "blender", "blender_updates",
                    "518_primed_slam.update.py")
_txt = open(_src).read()
exec(compile(_txt[:_txt.index("rng = np.random.default_rng(518)")], _src, "exec"), globals())
scene.name = "Grab Throw"
OUT = os.path.join(FOLDER, "grab_throw.blend")
TOP = 0.0
rng = np.random.default_rng(521)
EYE_PX = np.array([0.0, -5.0, -4.3])
FPX = 1000.0
LOOK = -R(12)                                  # body yaw: the crosshair 12 deg to the right of the mob
LOOKV = np.array([math.sin(LOOK), -math.cos(LOOK), 0.0])
MOB_AT = np.array([0.0, -6.0, 0.0])
WALL_Y = -16.0                                 # the wall's front face
END = 110

THRUST = dict(body=(0.15, 0, 0), head=(0.0, 0, 0), ring=(-1.57, 0, 0.05), free=(0.3, 0, -0.25),
              ringleg=(-0.25, 0, 0.03), freeleg=(0.3, 0, -0.03))
LIFT = dict(body=(-0.05, 0, 0), head=(-0.2, 0, 0), ring=(-2.2, 0, 0.08), free=(0.2, 0, -0.25),
            ringleg=(-0.15, 0, 0.03), freeleg=(0.2, 0, -0.03))
COCK = dict(body=(-0.18, 0, 0), head=(-0.1, 0, 0), ring=(-2.9, 0, 0.35), free=(-0.6, 0, -0.3),
            ringleg=(0.25, 0, 0.03), freeleg=(-0.3, 0, -0.03))
WHIP = dict(body=(0.38, 0, 0), head=(0.1, 0, 0), ring=(-1.3, 0, 0.05), free=(0.7, 0, -0.2),
            ringleg=(-0.45, 0, 0.03), freeleg=(0.5, 0, -0.03))
OVER = dict(body=(-0.22, 0, 0), head=(-0.35, 0, 0), ring=(-3.05, 0, 0.05), free=(0.1, 0, -0.3),
            ringleg=(0.1, 0, 0.03), freeleg=(-0.1, 0, -0.03))
HOLD_OUT = dict(body=(0.05, 0, 0), head=(0.0, 0, 0), ring=(-1.57, 0, 0.12), free=(-0.4, 0, -0.5),
                ringleg=(-0.15, 0, 0.03), freeleg=(0.15, 0, -0.03))


def keyed_pose(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            q = mixp(pa, pb, smooth((t - ta) / max(1e-6, tb - ta)))
            q["grounded"] = True
            return q
    return keys[-1][1]


def Rz(a):
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def world_pt(p_rig, origin, side):
    return Rz(side) @ to_bl(p_rig) + origin


# ------------------------------------------------------------------ the construct hand (palm + fingers + thumb)
HANDM = bpy.data.materials.new("GT hand"); HANDM.use_nodes = True
_N, _L = HANDM.node_tree.nodes, HANDM.node_tree.links
_out = _N.get("Material Output"); _N.remove(_N.get("Principled BSDF"))
_con = construct_nodes(HANDM, _N, _L)
_em = _N.new("ShaderNodeEmission"); _L.new(_con, _em.inputs["Color"]); _em.inputs["Strength"].default_value = 2.4
_tr = _N.new("ShaderNodeBsdfTransparent")
_fa = obj_attr(_N, "fade")
_mul = _N.new("ShaderNodeMath"); _mul.operation = "MULTIPLY"; _mul.inputs[1].default_value = 0.92
_L.new(_fa, _mul.inputs[0])
_ms = _N.new("ShaderNodeMixShader"); _L.new(_mul.outputs[0], _ms.inputs[0])
_L.new(_tr.outputs[0], _ms.inputs[1]); _L.new(_em.outputs[0], _ms.inputs[2]); _L.new(_ms.outputs[0], _out.inputs["Surface"])
try:
    HANDM.surface_render_method = "BLENDED"
except Exception:
    pass


def box(name, a, b, m):
    a = np.array(a, float); b = np.array(b, float)
    verts = [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.materials.append(m)
    return me


def make_hand(tag):
    """Local frame: wrist at the origin, fingers along +z, palm facing -y. Finger pivots at the knuckles (z 0.9)."""
    palm = link(bpy.data.objects.new(f"{tag} palm", box(f"{tag} palm", (-0.5, -0.17, 0), (0.5, 0.17, 0.9), HANDM)))
    palm["fade"] = 0.0
    fingers = []
    for i, x in enumerate((-0.375, -0.125, 0.125, 0.375)):
        piv = link(bpy.data.objects.new(f"{tag} knuckle {i}", None)); piv.parent = palm
        piv.location = (x, -0.05, 0.9); piv.rotation_mode = "XYZ"
        f = link(bpy.data.objects.new(f"{tag} finger {i}", box(f"{tag} finger {i}", (-0.11, -0.11, 0),
                                                                (0.11, 0.11, 0.75 - 0.08 * abs(i - 1.5)), HANDM)))
        f.parent = piv; f["fade"] = 0.0
        fingers.append((piv, f))
    piv = link(bpy.data.objects.new(f"{tag} thumb knuckle", None)); piv.parent = palm
    piv.location = (0.5, -0.1, 0.35); piv.rotation_mode = "XYZ"
    th = link(bpy.data.objects.new(f"{tag} thumb", box(f"{tag} thumb", (0, -0.11, -0.11), (0.55, 0.11, 0.11), HANDM)))
    th.parent = piv; th["fade"] = 0.0
    return palm, fingers, (piv, th)


def look_matrix(pos, fwd, up=(0, 0, 1)):
    """Hand frame: +z (fingers) along fwd, -y (palm) toward the ground side."""
    z = np.asarray(fwd, float); z = z / np.linalg.norm(z)
    upv = np.asarray(up, float)
    x = np.cross(upv, z)
    if np.linalg.norm(x) < 1e-4:
        x = np.array([1.0, 0, 0])
    x = x / np.linalg.norm(x); y = np.cross(z, x)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2] = x, y, z; M[:3, 3] = pos
    return Matrix(M.tolist())


TETHER = cube_mesh("GT tether"); TETHER.materials.append(FX)
STONEM = mat("GT stone", (0.42, 0.42, 0.44), rough=0.9)


def wall(tag, ox):
    """A stone wall 9 wide, 5 tall, 2 thick, its front face at WALL_Y, centred on the crosshair line."""
    cx0 = ox + LOOKV[0] * (WALL_Y / LOOKV[1])          # where the crosshair line meets the wall
    cells = {}
    for ix in range(-4, 5):
        for iz in range(5):
            for layer in (0, 1):
                o = link(bpy.data.objects.new(f"{tag} wall {ix} {iz} {layer}", UNIT)); o["cx"] = 0.0
                o.location = (round(cx0) + ix, WALL_Y - 0.5 - layer, iz + 0.5)
                o.scale = (0.999, 0.999, 0.999)
                if layer == 0:
                    cells[(round(cx0) + ix, iz)] = o
    return cells


def crater(cells, hit_x, hit_z, t_hit):
    """3x3 in the wall face: the centre lit at the hit and gone 4 ticks later, the ring of 8 lit at once, gone at 6."""
    log = []
    cxi, czi = int(round(hit_x)), int(round(hit_z - 0.5))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            o = cells.get((cxi + dx, czi + dz))
            if o is None:
                continue
            d = max(abs(dx), abs(dz))
            gone = t_hit + 4 + 2 * d
            key_prop(o, "cx", 0.0, 1); key_prop(o, "cx", 0.0, t_hit - 1); key_prop(o, "cx", 1.0, t_hit)
            key_obj(o, 1, sc=0.999); key_obj(o, gone - 1, sc=0.999); key_obj(o, gone, sc=0.0001)
            pixel_burst(f"{o.name} px", tuple(o.location), gone, rng, n=5, drift=(0, 0.08, 0))
            log.append({"dx": dx, "dz": dz, "lit": 0, "gone": gone - t_hit})
    return log


# ------------------------------------------------------------------ the takes
TAKES = {
    "G1": dict(name="Reach and fling", throw_speed=1.9, lift=0.18,
               keys=[(0, STAND), (8, STAND), (12, THRUST), (18, THRUST), (28, LIFT), (34, COCK), (37, WHIP),
                     (44, WHIP), (58, STAND)], release=36),
    "G2": dict(name="Overhead whip", throw_speed=2.2, lift=-0.05,
               keys=[(0, STAND), (8, STAND), (12, THRUST), (18, THRUST), (30, OVER), (34, OVER), (38, WHIP),
                     (46, WHIP), (60, STAND)], release=38),
    "G3": dict(name="Spin throw", throw_speed=2.0, lift=0.15,
               keys=[(0, STAND), (8, STAND), (12, THRUST), (18, THRUST), (24, HOLD_OUT), (44, HOLD_OUT), (47, WHIP),
                     (52, WHIP), (66, STAND)], release=44, spin=(24, 44)),
    # J (site): G1 IMPROVE (no note) -> three labelled variations; G2, G3 dropped
    "G1a": dict(name="Reach and fling - snappy", base="G1", speed=1.35, throw_speed=2.3, lift=0.15,
                keys=[(0, STAND), (8, STAND), (12, THRUST), (18, THRUST), (28, LIFT), (34, COCK), (37, WHIP),
                      (44, WHIP), (58, STAND)], release=36),
    "G1b": dict(name="Reach and fling - big hand", base="G1", hand_scale=1.6, arc=1.35, throw_speed=2.0,
                lift=0.05, keys=[(0, STAND), (8, STAND), (12, THRUST), (18, THRUST), (28, LIFT), (34, COCK), (37, WHIP),
                                 (44, WHIP), (58, STAND)], release=36),
    "G1c": dict(name="Reach and fling - yank", base="G1", nowind=True, throw_speed=2.1, lift=0.2,
                keys=[(0, STAND), (8, STAND), (12, THRUST), (18, THRUST), (24, LIFT), (27, WHIP), (34, WHIP),
                      (48, STAND)], release=28),
}
TAKES = {k: v for k, v in TAKES.items() if k in ("G1", "G1a", "G1b", "G1c")}     # G2, G3 dropped (J)


def body_side(spec, t):
    s = LOOK
    if spec.get("spin"):
        a, b = spec["spin"]
        if a <= t <= b:
            s = LOOK - 2 * math.pi * smooth((t - a) / (b - a))
    return s


def hand_target(take, spec, t, ring_pt, origin, side):
    """Where the construct hand is (and which way its fingers point) while it forms, reaches, carries and throws."""
    grab = origin + MOB_AT + np.array([0, 0.25, 1.35])
    fwd_dir = LOOKV
    start = ring_pt + LOOKV * 1.0                     # it forms a block out in front of the ring fist
    if t < 12:
        return start, (grab - ring_pt)
    if t < 18:
        w = smooth((t - 12) / 6)
        return start + (grab - start) * w, (grab - ring_pt)
    rel = spec["release"]
    if spec.get("base", take) == "G1":
        arc = spec.get("arc", 1.0)
        front = origin + LOOKV * 3.0 + np.array([0, 0, 2.6 * arc])
        back = origin + Rz(side) @ np.array([-1.0 * arc, 1.2 * arc, 0]) + np.array([0, 0, 3.6 * arc])   # over the right shoulder
        out = origin + LOOKV * 3.6 + np.array([0, 0, 2.1])
        if spec.get("nowind"):
            p = grab + (front - grab) * smooth((t - 18) / 8) if t < 26 else front + (out - front) * smooth(min(1, (t - 26) / 2.0))
            return p, (fwd_dir + np.array([0, 0, 0.6]))
        if t < 28:
            p = grab + (front - grab) * smooth((t - 18) / 10)
        elif t < 34:
            p = front + (back - front) * smooth((t - 28) / 6)
        else:
            p = back + (out - back) * smooth(min(1, (t - 34) / 2.5))
        return p, (fwd_dir + np.array([0, 0, 0.6]))
    if take == "G2":
        # an arc over the head: from in front (low) up through overhead to behind, then whip back over to the front
        def arc(theta):
            return origin + LOOKV * (3.2 * math.cos(theta)) + np.array([0, 0, 1.9 + 3.0 * math.sin(theta)])
        if t < 30:
            p0 = grab
            th = math.pi * 0.05 + (math.pi * 0.95) * smooth((t - 18) / 12)
            p = p0 + (arc(th) - p0) * smooth(min(1, (t - 18) / 4))
        elif t < 34:
            p = arc(math.pi)
        else:
            th = math.pi - (math.pi * 1.15) * smooth(min(1, (t - 34) / 4.0))
            p = arc(th)
        return p, (p - (origin + np.array([0, 0, 1.6])))
    # G3: pulled in to arm's length, then carried round the spin
    r = 3.4
    held = lambda s: origin + Rz(s) @ np.array([0.0, -r, 0.0]) + np.array([0, 0, 1.4])
    if t < 24:
        return grab + (held(side) - grab) * smooth((t - 18) / 6), (held(side) - origin)
    return held(side), (held(side) - origin)


dump = {"format": "per take: per tick part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, body yaw (rad, "
                  "+ = left), construct hand position (blocks from the player's feet) and grip 0..1, mob position, ring "
                  "glow; plus the grab, release and hit ticks and the wall crater cells. 20 ticks a second.",
        "look_yaw_deg": -12, "wall_distance_blocks": 16, "takes": {}}
for i, (take, spec) in enumerate(TAKES.items()):
    ox = i * 200.0                      # far apart: the side cameras don't see the next lane
    nm = f"{i + 1:02d} {spec['name']}"
    origin = np.array([ox, 0.0, 0.0])
    objs = make_player(take + " 3p")
    fpo = make_player(take + " fp")
    for k, o in fpo.items():
        if k not in ("rarm", "larm", "ring"):
            for c in [o] + list(o.children_recursive):
                c.hide_render = True; c.hide_viewport = True
    ringm = mat(f"GT ring {take}", (0.04, 0.85, 0.15), emit=2.0)
    objs["ring"].data.materials[0] = ringm; fpo["ring"].data.materials[0] = ringm
    hands = [make_hand(f"GT {take} hand {tag}") for tag in ("3p", "fp")]
    tethers = []
    for tag in ("3p", "fp"):
        tt = link(bpy.data.objects.new(f"GT {take} tether {tag}", TETHER)); tt["fade"] = 0.0
        tethers.append(tt)
    mobs = []
    for tag in ("3p", "fp"):
        mo = link(bpy.data.objects.new(f"GT {take} mob {tag}", MOBME)); mo["hurt"] = 0.0; mo.rotation_mode = "XYZ"
        mobs.append(mo)
    walls = [wall(f"GT {take} 3p", ox), wall(f"GT {take} fp", FPX + ox)]
    eye = link(bpy.data.objects.new(f"GT {take} eye", None)); eye.empty_display_size = 0.05
    rel = spec["release"]
    mob_pos = origin + MOB_AT; vel = None; t_hit = None; tumble = 0.0; hit_at = None
    ticks = []
    SPD = spec.get("speed", 1.0)
    burst_done = False
    for t_real in range(END + 1):
        f_ = t_real + 1
        t = t_real * SPD                    # animation time (a variation can run quicker); physics stays per real tick
        side = body_side(spec, t)
        p = keyed_pose(spec["keys"], t)
        sol = solve(p)
        for base, rig in ((origin, objs), (origin + np.array([FPX, 0, 0]), fpo)):
            set_pose(rig, sol, base, f_, side=side)
        ring_pt = world_pt(hand_point(sol, "rarm"), origin, side)
        hp, hdir = hand_target(take, spec, t, ring_pt, origin, side)
        # the hand: forms 9-12, full size from 12, dissolves from the release + 2
        if t < 9:
            sc, fade = 0.0001, 0.0
        elif t < 12:
            sc, fade = spec.get("hand_scale", 1.0) * (0.2 + 0.8 * smooth((t - 9) / 3)), 0.6 + 0.4 * (t - 9) / 3
        elif t <= rel + 2:
            sc, fade = spec.get("hand_scale", 1.0), 1.0
        elif t <= rel + 8:
            u = (t - rel - 2) / 6; sc, fade = spec.get("hand_scale", 1.0) * (1.0 - 0.3 * u), 1.0 - u
        else:
            sc, fade = 0.0001, 0.0
        grip = 0.0
        if 17 <= t <= rel:
            grip = smooth(min(1, (t - 17) / 2))
        if rel < t <= rel + 3:
            grip = 1 - (t - rel) / 3
        if t >= rel + 3 and not burst_done:
            burst_done = True
            pixel_burst(f"GT {take} hand px", tuple(hp), f_, rng, n=14, drift=tuple(LOOKV * 0.08))
        # the mob: stands, is grabbed (18), hangs from the hand, flies from the release, hits the wall
        if t < 18:
            pass
        elif t <= rel:
            mob_pos = hp - np.array([0, 0.25, 1.35]) * np.array([1, 1, 1])
        else:
            if vel is None:
                vel = LOOKV * spec["throw_speed"] + np.array([0, 0, spec["lift"]])
            if t_hit is None:
                mob_pos = mob_pos + vel; vel = vel * 0.98; vel[2] -= 0.08; tumble += 0.45
                if mob_pos[1] - origin[1] <= WALL_Y + 0.3:
                    mob_pos[1] = origin[1] + WALL_Y + 0.6
                    t_hit = t_real; hit_at = mob_pos.copy()
                if mob_pos[2] < 0:
                    mob_pos[2] = 0.0
        for k, (palm, fingers, (tp, th)) in enumerate(hands):
            off = np.array([FPX * k, 0, 0])
            M = look_matrix(hp + off, hdir)
            palm.matrix_world = M @ Matrix.Scale(sc, 4)
            palm.keyframe_insert("location", frame=f_); palm.keyframe_insert("rotation_euler", frame=f_)
            palm.keyframe_insert("scale", frame=f_)
            for piv, fo in fingers:
                piv.rotation_euler = (-1.45 * grip, 0, 0); piv.keyframe_insert("rotation_euler", frame=f_)
                key_prop(fo, "fade", fade, f_)
            tp.rotation_euler = (0, 0.0, -1.2 * grip); tp.keyframe_insert("rotation_euler", frame=f_)
            key_prop(th, "fade", fade, f_); key_prop(palm, "fade", fade, f_)
            # tether from the ring to the wrist while reaching and holding
            tt = tethers[k]
            a_, b_ = ring_pt + off, hp + off
            d = b_ - a_; L_ = float(np.linalg.norm(d))
            tfade = 0.8 * fade if t <= rel else 0.0
            if L_ > 1e-3:
                z = d / L_
                x = np.cross([0, 0, 1.0], z); x = x / (np.linalg.norm(x) + 1e-9); y = np.cross(z, x)
                Mt = np.eye(4); Mt[:3, 0], Mt[:3, 1], Mt[:3, 2] = x * 0.07, y * 0.07, z * L_
                Mt[:3, 3] = (a_ + b_) / 2
                tt.matrix_world = Matrix(Mt.tolist())
                tt.keyframe_insert("location", frame=f_); tt.keyframe_insert("rotation_euler", frame=f_)
                tt.keyframe_insert("scale", frame=f_)
            key_prop(tt, "fade", tfade, f_)
            mo = mobs[k]
            mo.location = tuple(mob_pos + off)
            if t_hit is None:
                mo.rotation_euler = (tumble if t > rel else 0.0, 0, side if t >= 18 else 0.0)
            mo.keyframe_insert("location", frame=f_); mo.keyframe_insert("rotation_euler", frame=f_)
            hurt = 1.0 if (17 <= t <= 22) or (t_hit is not None and t_real - t_hit <= 8) else 0.0
            key_prop(mo, "hurt", hurt, f_)
        r_, pv = sol["head"]
        Me = np.eye(4)
        cam_side = LOOK if spec.get("spin") else side
        Me[:3, :3] = Rz(cam_side) @ (A @ rot(*r_) @ A.T)
        Me[:3, 3] = Rz(cam_side) @ to_bl(pv + rot(*r_) @ EYE_PX) + origin + np.array([FPX, 0, 0])
        eye.matrix_world = Matrix(Me.tolist())
        eye.keyframe_insert("location", frame=f_); eye.keyframe_insert("rotation_euler", frame=f_)
        glow = 3.0 if t < 9 else (6.0 if t < 18 else (9.0 if t < rel else (16.0 if t <= rel + 2 else 4.0)))
        sk = ringm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        sk.default_value = min(6.0, 1.2 + 0.3 * glow); sk.keyframe_insert("default_value", frame=f_)
        ticks.append({"body_yaw": round(float(side), 4), "glow": glow, "grip": round(float(grip), 3),
                      "hand": [round(float(v), 3) for v in (hp - origin)], "hand_scale": round(float(sc), 3),
                      "mob": [round(float(v), 3) for v in (mob_pos - origin)],
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    cells_log = []
    if t_hit is not None:
        for k, cells in enumerate(walls):
            lg = crater(cells, hit_at[0] + FPX * k, hit_at[2] + 0.7, t_hit + 1)
            if k == 0:
                cells_log = lg
    dump["takes"][take] = {"name": spec["name"], "grab_tick": 18, "release_tick": rel, "hit_tick": t_hit,
                           "throw_speed_bpt": spec["throw_speed"], "spin_ticks": spec.get("spin"),
                           "crater": cells_log, "ticks": ticks}
    c3 = cam(f"{nm} - 3rd person", tuple(origin + Rz(LOOK) @ np.array([-1.6, 4.4, 0]) + np.array([0, 0, 2.8])),
             tuple(origin + LOOKV * 7 + np.array([0, 0, 1.2])), 26)
    cs = cam(f"{nm} - side", tuple(origin + np.array([16.0, -7.0, 3.5])), tuple(origin + np.array([0, -7.0, 2.0])), 22)
    cf = link(bpy.data.objects.new(f"{nm} - 1st person", bpy.data.cameras.new(f"{nm} - 1st person")))
    cf.data.sensor_fit = "VERTICAL"; cf.data.angle = R(70); cf.data.clip_start = 0.02
    cf.parent = eye; cf.rotation_euler = (R(90), 0, R(180))
    for bx in (ox, FPX + ox):
        cu = bpy.data.curves.new(f"GT label {nm} {bx}", "FONT"); cu.body = nm; cu.size = 0.4; cu.align_x = "CENTER"
        tl = link(bpy.data.objects.new(f"GT label {nm} {bx}", cu)); tl.location = (bx, 2.2, 0.01)
        tl.data.materials.append(LABEL)
    print(take, "built; release", rel, "hit", t_hit, flush=True)

with open(os.path.join(FOLDER, "grab_throw_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
scene.frame_start, scene.frame_end = 1, END
gm = bpy.data.materials.new("GT ground"); gm.use_nodes = True
N_, L_ = gm.node_tree.nodes, gm.node_tree.links
bs = N_["Principled BSDF"]; bs.inputs["Roughness"].default_value = 0.95
geo = N_.new("ShaderNodeNewGeometry"); ck = N_.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 1.0
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.16, 0.3, 0.1, 1)
L_.new(geo.outputs["Position"], ck.inputs["Vector"]); L_.new(ck.outputs["Color"], bs.inputs["Base Color"])
for gx in (200.0, FPX + 200.0):
    me = bpy.data.meshes.new("GT ground")
    me.from_pydata([(-300, -80, 0), (300, -80, 0), (300, 40, 0), (-300, 40, 0)], [], [(0, 1, 2, 3)]); me.update()
    me.materials.append(gm); g = link(bpy.data.objects.new("GT ground", me)); g.location = (gx, 0, 0)
world = bpy.data.worlds.new("GT world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("GT sun", bpy.data.lights.new("GT sun", "SUN")))
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
scene.camera = bpy.data.objects.get("01 Reach and fling - 3rd person")
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
