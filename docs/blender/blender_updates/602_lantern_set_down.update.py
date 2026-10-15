# Pass 602: lantern set-down (Chat D, 2026-10-15). J picked "Kneel and place": drop to one knee and set the Dark Lantern
# on the ground in front, deliberate, the way K3c picks it up (the catalogue only had K3c played backwards as a stand-in).
# Same rig, poses and Dark Lantern (16 px tall with the handle, its true size) as pass 601 / K3c. The lantern hangs from
# the ring hand by its handle and swings as you move; it touches down when its base reaches the ground, rights itself
# and stands; then you let go.
#   D1 deliberate: carry, kneel, lower, touch down at 1.3 s, let go at 1.8 s, stand by 3.2 s.
#   D2 quick: the same in 1.8 s (touch down 0.75 s, let go 0.95 s).
#   D3 seal: D1, then the ring hand rests over the lantern a moment and the lantern lights (a pulse that settles to its
#      idle glow) before you stand.
# Cameras "NN <take> - 3rd person" (over the right shoulder), "NN <take> - side", "NN <take> - 1st person" (eyes; arms,
# ring and lantern only, as Minecraft draws first person). Builds LanternLive\lanterns\lantern_set_down.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

_src = os.path.join(os.environ.get("KL_REPO", "/home/claude/site-10"), "docs", "blender", "blender_updates",
                    "601_lantern_charge6.update.py")
_txt = open(_src).read()
exec(compile(_txt[:_txt.index("# ------------------------------------------------------------------ build the takes")],
             _src, "exec"), globals())                      # rig, K3 poses, fit_reach, Dark Lantern, charge light
scene.name = "Lantern Set Down"
OUT = os.path.join(FOLDER, "lantern_set_down.blend")
EYE_PX = np.array([0.0, -5.0, -4.3])
FPX = 1000.0

P["K3_seal"] = dict(P["K3_vow"]); P["K3_seal"]["ring"] = (P["K3_vow"]["ring"][0] - 0.22, P["K3_vow"]["ring"][1],
                                                          P["K3_vow"]["ring"][2])
P["K3_seal"]["head"] = (0.85, 0, 0)
P["K3_seal2"] = dict(P["K3_seal"])                 # the free hand comes over too, resting beside the ring hand
P["K3_seal2"]["free"] = (P["K3_seal"]["ring"][0] + 0.1, 0.55, 0.0)
P["K3_seal2"]["body"] = (P["K3_seal"].get("body", (0, 0, 0))[0] + 0.08, 0, 0)

TAKES = {
    "D1": dict(name="Set down deliberate", release=36, end=64,
               keys=[("K3_stand", 0), ("K3_stand", 8), ("K3_raise", 18), ("K3_vow", 28), ("K3_vow", 38),
                     ("K3_kneel", 44), ("K3_kneel", 48), ("idle", 64)]),
    "D2": dict(name="Set down quick", release=21, end=36,
               keys=[("K3_stand", 0), ("K3_stand", 4), ("K3_raise", 10), ("K3_vow", 16), ("K3_vow", 20),
                     ("K3_kneel", 24), ("idle", 36)]),
    "D3": dict(name="Set down and seal", release=34, end=76, seal=(38, 54),
               keys=[("K3_stand", 0), ("K3_stand", 8), ("K3_raise", 18), ("K3_vow", 28), ("K3_vow", 36),
                     ("K3_seal", 42), ("K3_seal", 52), ("K3_kneel", 58), ("idle", 76)]),
    # J (site): D1, D2 KEEP; D3 IMPROVE (no note) -> three labelled variations
    "D3a": dict(name="Seal quick", release=28, end=58, seal=(31, 41),
                keys=[("K3_stand", 0), ("K3_stand", 6), ("K3_raise", 14), ("K3_vow", 22), ("K3_vow", 28),
                      ("K3_seal", 32), ("K3_seal", 40), ("K3_kneel", 45), ("idle", 58)]),
    "D3b": dict(name="Seal with both hands", release=34, end=78, seal=(38, 56),
                keys=[("K3_stand", 0), ("K3_stand", 8), ("K3_raise", 18), ("K3_vow", 28), ("K3_vow", 36),
                      ("K3_seal2", 43), ("K3_seal2", 54), ("K3_kneel", 60), ("idle", 78)]),
    "D3c": dict(name="Seal and blaze", release=34, end=86, seal=(38, 64), seal_peak=0.85, seal_flare=10.0,
                keys=[("K3_stand", 0), ("K3_stand", 8), ("K3_raise", 18), ("K3_vow", 28), ("K3_vow", 36),
                      ("K3_seal", 42), ("K3_seal", 62), ("K3_kneel", 68), ("idle", 86)]),
}


def set_down_physics(hands, release, zeta=0.12, sub=20):
    """Hanging from the grip (pendulum, lags the hand) until the base reaches the ground; then it stands where it
    touched and rights itself over 4 ticks. Returns per tick (R (3x3 rig), base point, grounded)."""
    Lg = LH - 0.5
    Lc = Lg - BODY_H / 2
    g = 9.81 * 16
    w0 = math.sqrt(g / Lc)
    hands = np.asarray(hands, float)
    acc = np.gradient(np.gradient(hands, 1 / 20, axis=0), 1 / 20, axis=0)
    phi = np.zeros(2); om = np.zeros(2)
    out = []; touched = None
    dt = 1 / 20 / sub
    for t in range(len(hands)):
        grip = hands[t]
        if touched is None:
            a = np.array([acc[t, 0], -acc[t, 2]])
            for _ in range(sub):
                al = -(g / Lc) * np.sin(phi) + (a / Lc) * np.cos(phi) - 2 * zeta * w0 * om
                om = om + al * dt; phi = phi + om * dt
            cz, sz_, cx, sx = math.cos(phi[0]), math.sin(phi[0]), math.cos(phi[1]), math.sin(phi[1])
            Rr = np.array([[cz, -sz_, 0], [sz_, cz, 0], [0, 0, 1]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
            base = grip + Rr @ np.array([0.0, Lg, 0.0])
            if base[1] >= GROUND - 0.05:
                touched = (t, Rr, np.array([base[0], GROUND, base[2]]))
            else:
                out.append((Rr, base, False)); continue
        t0, R0, spot = touched
        w = smooth(min(1.0, (t - t0) / 4.0))
        Rm = R0 * (1 - w) + np.eye(3) * w
        u, _, vt = np.linalg.svd(Rm); Rm = u @ vt                   # back to a rotation
        out.append((Rm, spot, True))
    return out, (touched[0] if touched else None)


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


def hide_body(objs):
    for k, o in objs.items():
        if k in ("rarm", "larm", "ring"):
            continue
        for c in [o] + list(o.children_recursive):
            c.hide_render = True; c.hide_viewport = True


dump = {"format": "per take: per tick solved pose (part rot rad, offset_px from the vanilla pivot), lantern: rig-space "
                  "rotation (3x3 rows) and base point (px, y down) while hanging from the ring hand, 'grounded' once it "
                  "stands; glow 0..1; ring = right arm; 20 ticks a second", "takes": {}}
END = 0
for i, (take, spec) in enumerate(TAKES.items()):
    ox = i * 14.0                       # far enough apart that a side camera does not catch the next lane
    nm = f"{i + 1:02d} {spec['name']}"
    last = spec["end"] + 10
    END = max(END, last)
    sols = [solve(pose_at(t, spec["keys"])) for t in range(last + 1)]
    hands = [hand_point(s, "rarm") for s in sols]
    phys, t_touch = set_down_physics(hands, spec["release"])
    rigs = []
    for base_x, tag in ((ox, "3p"), (FPX + ox, "fp")):
        objs = make_player(f"{take} {tag}")
        rm = mat(f"SD ring {take} {tag}", (0.04, 0.85, 0.15), emit=2.0); objs["ring"].data.materials[0] = rm
        if tag == "fp":
            hide_body(objs)
        root, glows, (charges, lamp) = import_lantern(f"{take} {tag}")
        rigs.append((base_x, tag, objs, rm, root, glows, charges, lamp))
    eye = link(bpy.data.objects.new(f"SD {take} eye", None)); eye.empty_display_size = 0.05
    ticks = []
    for t in range(last + 1):
        sol = sols[t]
        Rl, base, grounded = phys[t]
        M = np.eye(4); M[:3, :3] = Rl; M[:3, 3] = base
        # glow: idle 0.12 once it stands; D3 lights up under the resting hand, then settles
        glow = 0.0 if not grounded else 0.12 * smooth(min(1, (t - t_touch) / 6))
        if spec.get("seal"):
            a, b = spec["seal"]
            if a <= t <= b + 12:
                glow = max(glow, spec.get("seal_peak", 0.55) * math.sin(math.pi * min(1.0, (t - a) / (b - a + 12))) ** 0.7)
        ring_e = 2.0 + (10.0 * math.exp(-((t - spec["release"]) / 3.0) ** 2))      # a small flare as you let go
        if spec.get("seal"):
            a, b = spec["seal"]
            if a <= t <= b:
                ring_e = max(ring_e, 2.0 + spec.get("seal_flare", 6.0) * math.sin(math.pi * (t - a) / (b - a)))
        for base_x, tag, objs, rm, root, glows, charges, lamp in rigs:
            origin = np.array([base_x, 0.0, 0.0])
            set_pose(objs, sol, origin, t + 1)
            key_root(root, bl_matrix(M, origin, 0.0), t + 1)
            s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
            s.default_value = min(12.0, ring_e); s.keyframe_insert("default_value", frame=t + 1)
            for bsdf in glows:
                q = bsdf.inputs["Emission Strength"]; q.default_value = 1.0 + 5.0 * glow
                q.keyframe_insert("default_value", frame=t + 1)
            for cv in charges:
                cv.outputs[0].default_value = glow; cv.outputs[0].keyframe_insert("default_value", frame=t + 1)
            lamp.data.energy = 25.0 * glow; lamp.data.keyframe_insert("energy", frame=t + 1)
        r, pv = sol["head"]
        Me = np.eye(4); Me[:3, :3] = A @ rot(*r) @ A.T
        Me[:3, 3] = to_bl(pv + rot(*r) @ EYE_PX) + np.array([FPX + ox, 0.0, 0.0])
        eye.matrix_world = Matrix(Me.tolist())
        eye.keyframe_insert("location", frame=t + 1); eye.keyframe_insert("rotation_euler", frame=t + 1)
        ticks.append({"glow": round(float(glow), 3), "grounded": bool(grounded),
                      "lantern": {"rot": [[round(float(v), 4) for v in row] for row in Rl],
                                  "base_px": [round(float(v), 3) for v in base]},
                      "parts": {k: {"rot": [round(float(v), 4) for v in sol[k][0]],
                                    "offset_px": [round(float(v), 3) for v in sol[k][1] - np.array(PIVOT[k], float)]}
                                for k in PARTS}})
    dump["takes"][take] = {"name": spec["name"], "touchdown_tick": t_touch, "release_tick": spec["release"],
                           "seal_ticks": spec.get("seal"), "end_tick": spec["end"], "ticks": ticks}
    # cameras
    c3 = cam(f"{nm} - 3rd person", (ox - 1.4, 3.6, 2.3), (ox + 0.2, -1.5, 0.5), 30)
    cs = cam(f"{nm} - side", (ox + 4.4, -0.7, 1.0), (ox, -0.7, 0.6), 35)
    cf = link(bpy.data.objects.new(f"{nm} - 1st person", bpy.data.cameras.new(f"{nm} - 1st person")))
    cf.data.sensor_fit = "VERTICAL"; cf.data.angle = R(70); cf.data.clip_start = 0.02
    cf.parent = eye; cf.rotation_euler = (R(90), 0, R(180))
    for bx in (ox, FPX + ox):
        cu = bpy.data.curves.new("SD label " + nm + str(bx), "FONT"); cu.body = nm; cu.size = 0.3; cu.align_x = "CENTER"
        tl = link(bpy.data.objects.new("SD label " + nm + str(bx), cu)); tl.location = (bx, 1.8, 0.01)
        tl.data.materials.append(mat("KL label", (0.8, 1.0, 0.85), emit=2.0))
    print(take, "built; touchdown", t_touch, "release", spec["release"], flush=True)

with open(os.path.join(FOLDER, "lantern_set_down_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
scene.frame_start, scene.frame_end = 1, END + 1
for gx in (35.0, FPX + 35.0):
    bpy.ops.mesh.primitive_plane_add(size=140, location=(gx, 0, 0))
    g = bpy.context.active_object
    for c in g.users_collection:
        c.objects.unlink(g)
    link(g); g.name = "SD floor"; g.data.materials.append(mat("KL grass", (0.22, 0.4, 0.15)))
world = bpy.data.worlds.get("KL world") or bpy.data.worlds.new("KL world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("SD sun", bpy.data.lights.new("SD sun", "SUN")))
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
scene.camera = bpy.data.objects.get("01 Set down deliberate - 3rd person")
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
