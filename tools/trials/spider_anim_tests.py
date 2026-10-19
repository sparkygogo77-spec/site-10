"""R2 brute animation tests (J, 2026-10-19: "do all and one more").

blender.exe -b --python spider_anim_tests.py -- <out.blend> [--video]

Three takes, each in its own area with its own camera and video:
  A1 walk test     flat floor, a 40-degree slope, then spiralling up a round column: legs plant on the blocks (each
                   foot is ray-cast onto the surface, a two-bone solve finds the knee), tetrapod gait.
  A2 burrow pop-up R2 walks to a hole, dives in with its legs tucked, scuttles through the tunnel and bursts out of a
                   second hole in a spray of dirt (shown cut open).
  A3 spike strike  R2 rears up and stabs with a front web-rock spike; you're pinned in web.
Spider: R2 brute, 36-block leg span (the lair spider), legs re-posed every frame.
"""
import math, os, sys
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_blender_kit as K

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
VIDEO = "--video" in argv
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
K.sc = sc
CM = K.cave_materials(textured=True)
FPS = 24
sc.render.fps = FPS
SPAN = 36.0
S = SPAN / 10.0


# ------------------------------------------------------------------ an animatable R2
class Spider:
    """R2 brute with legs that can be re-posed: each leg is femur (hip->knee) and a tibia+spike (knee->foot)."""

    def __init__(self, name):
        self.root = K.empty(name)
        self.name = name
        mb, hair = K._m("brute"), K._m("hair")
        self.body_h = 1.5 * S
        self.ceph_w, self.ceph_l = 2.0 * S, 2.1 * S
        ceph_c = Vector((0, 0.4 * S, self.body_h + 0.2 * S))
        abd = (2.8 * S, 3.2 * S, 2.4 * S)
        abd_c = Vector((0, -self.ceph_l * 0.5 - abd[1] * 0.45, self.body_h + abd[2] * 0.25))
        K._blob(name + " head", tuple(ceph_c), (self.ceph_w, self.ceph_l, 1.0 * S), mb, self.root)
        K._blob(name + " abdomen", tuple(abd_c), abd, mb, self.root)
        rng = np.random.default_rng(3)
        for j in range(30):   # hair on the abdomen
            off = Vector(tuple(rng.uniform(-0.5, 0.5, 3) * np.array(abd)))
            K.box(f"{name} hair{j}", tuple(abd_c + off.normalized() * abd[0] * 0.5), (0.12 * S, 0.12 * S, 0.35 * S), hair, self.root)
        for i in range(8):
            row = i // 4
            K.box(f"{name} eye{i}", tuple(ceph_c + Vector(((i % 4 - 1.5) * 0.28 * S, self.ceph_l * 0.5, 0.25 * S + row * 0.25 * S))), (0.18 * S,) * 3, K._m("eye"), self.root)
        for sx in (-1, 1):
            K._seg(f"{name} fang{sx}", ceph_c + Vector((sx * 0.3 * S, self.ceph_l * 0.5, -0.2 * S)),
                   ceph_c + Vector((sx * 0.25 * S, self.ceph_l * 0.55, -0.7 * S)), 0.25 * S, K._m("fang"), self.root)
        self.legs = []
        for sd, k, hip, knee, ankle, foot in K._legs(SPAN, self.body_h, self.ceph_w, self.ceph_l):
            L1 = (knee - hip).length
            L2 = (ankle - knee).length + (foot - ankle).length
            parts = {}
            t = 0.42 * S
            for nm, m, thick in (("femur", mb, t), ("tibia", mb, t * 0.85), ("silk", K._m("silk"), t * 1.2),
                                 ("stone0", K._m("spike"), t * 1.0), ("stone1", K._m("spike"), t * 0.66), ("stone2", K._m("spike"), t * 0.33)):
                parts[nm] = K.box(f"{name} leg{sd:+d}{k} {nm}", (0, 0, 0), (thick, 1, thick), m, None)
                parts[nm].rotation_mode = "QUATERNION"
            self.legs.append(dict(side=sd, k=k, hip=hip.copy(), rest=foot.copy(), L1=L1, L2=L2, parts=parts,
                                  group=(k + (0 if sd < 0 else 1)) % 2, planted=None, swing=None))

    @staticmethod
    def _place(ob, a, b, frame):
        v = b - a
        ob.location = (a + b) / 2
        ob.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(v.normalized())
        ob.scale = (ob.scale.x, v.length, ob.scale.z)
        ob.keyframe_insert("location", frame=frame); ob.keyframe_insert("rotation_quaternion", frame=frame)
        ob.keyframe_insert("scale", frame=frame)

    def body(self, frame, pos, forward, up):
        """Key the body: pos is the point on the ground under it, forward/up its directions."""
        up = up.normalized(); fw = (forward - up * forward.dot(up)).normalized(); rt = fw.cross(up)
        m = Matrix(((rt.x, fw.x, up.x), (rt.y, fw.y, up.y), (rt.z, fw.z, up.z)))
        self.root.rotation_mode = "QUATERNION"
        self.root.location = pos
        self.root.rotation_quaternion = m.to_quaternion()
        self.root.keyframe_insert("location", frame=frame); self.root.keyframe_insert("rotation_quaternion", frame=frame)
        self.M = Matrix.Translation(pos) @ m.to_4x4()
        self.up = up

    def leg(self, frame, L, foot):
        """Two-bone solve from the hip to the foot, the knee bending up (along the body's up)."""
        H = self.M @ L["hip"]
        d = foot - H
        dist = min(d.length, L["L1"] + L["L2"] - 0.05)
        dirn = d.normalized()
        along = (L["L1"] ** 2 - L["L2"] ** 2 + dist ** 2) / (2 * dist)
        h = math.sqrt(max(0.0, L["L1"] ** 2 - along ** 2))
        upp = (self.up - dirn * self.up.dot(dirn))
        upp = upp.normalized() if upp.length > 1e-4 else Vector((0, 0, 1))
        knee = H + dirn * along + upp * h
        F = H + dirn * dist
        p = L["parts"]
        self._place(p["femur"], H, knee, frame)
        ankle = knee + (F - knee) * 0.62
        self._place(p["tibia"], knee, ankle, frame)
        v = F - ankle
        self._place(p["silk"], ankle, ankle + v * 0.22, frame)
        for i, (t0, t1) in enumerate(((0.18, 0.55), (0.55, 0.82), (0.82, 1.0))):
            self._place(p[f"stone{i}"], ankle + v * t0, ankle + v * t1, frame)


def ray_to(target, normal, reach=12.0):
    """Cast from above the target point down its normal onto the course; the hit (or the target if nothing)."""
    dg = bpy.context.evaluated_depsgraph_get()
    o = target + normal * reach
    hit, loc, nrm, *_ = sc.ray_cast(dg, o, -normal, distance=reach * 2.5)
    return (Vector(loc), Vector(nrm)) if hit else (target, normal)


def walk(sp, frames, path, period=14, lift=None):
    """Drive the body along path(t) -> (ground point, forward, up) for t in 0..1 over the frames, with a tetrapod gait:
    each half of the legs swings for half the cycle while the other half stays planted on the blocks."""
    lift = lift or 0.12 * SPAN
    f0, f1 = frames
    for f in range(f0, f1 + 1):
        t = (f - f0) / max(1, f1 - f0)
        pos, fw, up = path(t)
        sp.body(f, pos + up * 0.0, fw, up)
        phase = ((f - f0) % period) / period
        for L in sp.legs:
            desired = sp.M @ Vector((L["rest"].x, L["rest"].y + 0.08 * SPAN, 0.0))
            want, _ = ray_to(desired, up)
            swinging = (phase < 0.5) == (L["group"] == 0)
            if L["planted"] is None:
                L["planted"] = want
            if swinging:
                if L["swing"] is None:
                    L["swing"] = (L["planted"].copy(), f)
                start, fs = L["swing"]
                u = min(1.0, (f - fs) / (period * 0.5))
                foot = start.lerp(want, u) + up * (math.sin(u * math.pi) * lift)
                L["planted"] = want if u >= 1 else L["planted"]
            else:
                if L["swing"] is not None:
                    L["planted"] = want
                    L["swing"] = None
                foot = L["planted"]
            sp.leg(f, L, foot)


def camera(name, loc, target, lens=26):
    return K.camera(name, loc, target, lens)


def course_mesh(name, solid, loc, mat_idx=0, cut=None):
    s_ = solid.copy()
    if cut is not None:
        s_[:, :, cut + 1:] = False
    o = K.voxel_mesh(name, s_, lambda i, n, a, d: np.full(len(i), mat_idx), CM)
    o.location = loc
    return o


takes = []

# ------------------------------------------------------------------ A1 walk test: floor, slope, column spiral
X, Y, Z = 170, 80, 90
g = np.zeros((X, Y, Z), bool)
g[:, :4, :] = True                                  # floor, top at z 4
xs = np.arange(X)[:, None, None]; ys = np.arange(Y)[None, :, None]; zs = np.arange(Z)[None, None, :]
SLOPE0, SLOPE1, TOP = 50, 80, 4 + 25                # a 40-degree slope from x 50 to 80, plateau at 29
h = np.clip((xs - SLOPE0) * math.tan(math.radians(40)), 0, TOP - 4) + 4
g |= ys < h
COLX, COLZ, COLR = 125, 45, 14                      # the round column on the plateau
g |= ((xs - COLX) ** 2 + (zs - COLZ) ** 2 <= COLR ** 2) & (ys < 75)
course = course_mesh("A1 course", g, (0, 0, 0))
A1_OFF = Vector((0, 0, 0))


def B1(x, y, z):   # grid -> Blender, like the kit: (x, -z, y)
    return Vector((x, -z, y))


def path_a1(t):
    """0-0.25 floor, 0.25-0.45 slope, 0.45-0.55 plateau to the column, 0.55-1 spiral up the column."""
    z0 = 45
    if t < 0.25:
        u = t / 0.25; x = 10 + u * (SLOPE0 - 10)
        return B1(x, 4, z0), Vector((1, 0, 0)), Vector((0, 0, 1))
    if t < 0.45:
        u = (t - 0.25) / 0.2; x = SLOPE0 + u * (SLOPE1 - SLOPE0 - 6)
        yy = 4 + (x - SLOPE0) * math.tan(math.radians(40))
        n = Vector((-math.sin(math.radians(40)), 0, math.cos(math.radians(40))))
        n = Vector((0, 0, 1)).lerp(n, min(1, u * 4)).normalized()
        return B1(x, min(yy, TOP), z0), Vector((1, 0, math.tan(math.radians(40)) * (1 - min(1, max(0, u - 0.8) * 5)))), n
    if t < 0.55:
        u = (t - 0.45) / 0.1; x = SLOPE1 - 6 + u * (COLX - COLR - (SLOPE1 - 6) - 2)
        return B1(x, TOP, z0), Vector((1, 0, 0)), Vector((0, 0, 1))
    u = (t - 0.55) / 0.45
    ang = math.pi + u * math.pi * 1.6                 # round the column, climbing
    yy = TOP + u * 32
    radial = Vector((math.cos(ang), -math.sin(ang), 0))
    p = B1(COLX + math.cos(ang) * COLR, yy, COLZ + math.sin(ang) * COLR)
    tang = Vector((-math.sin(ang), -math.cos(ang), 0)) * (COLR * math.pi * 1.6) + Vector((0, 0, 32))
    up = Vector((0, 0, 1)).lerp(radial, min(1, u * 5)).normalized()
    return p, tang.normalized(), up


r2a = Spider("A1 R2")
walk(r2a, (1, 220), path_a1)
K.player("A1 player", tuple(B1(30, 4, 30)))
takes.append(("A1 walk test", camera("01 A1 walk test", tuple(B1(70, 70, -150)), tuple(B1(95, 25, 45)), 30), (1, 220)))
K.light("A1 key", tuple(B1(80, 140, -60)), 450000, (1, 0.95, 0.9), "AREA", 200)

# ------------------------------------------------------------------ A2 burrow pop-up (cut open)
OX = 0; OY = -400
X2, Y2, Z2 = 150, 50, 80
g2 = np.zeros((X2, Y2, Z2), bool)
g2[:, :34, :] = True                                 # ground, top at 34
H1, H2, HZ, HR = 35, 115, 40, 9
xs2 = np.arange(X2)[:, None, None]; ys2 = np.arange(Y2)[None, :, None]; zs2 = np.arange(Z2)[None, None, :]
for hx in (H1, H2):
    g2 &= ~(((xs2 - hx) ** 2 + (zs2 - HZ) ** 2 <= HR ** 2) & (ys2 >= 14))
tun = (((ys2 - 14) ** 2 + (zs2 - HZ) ** 2) <= 8.5 ** 2) & (xs2 >= H1) & (xs2 <= H2)
g2 &= ~tun
course_mesh("A2 ground", g2, Vector((OX, OY, 0)), 0, cut=HZ)


def B2(x, y, z):
    return Vector((OX + x, OY - z, y))


r2b = Spider("A2 R2")
F_DIVE, F_OUT, F_END2 = 40, 100, 150


def path_a2_walk(t):
    x = 5 + t * (H1 - 12 - 5)
    return B2(x, 34, HZ), Vector((1, 0, 0)), Vector((0, 0, 1))


walk(r2b, (1, F_DIVE), path_a2_walk)
# dive: down the hole, along the tunnel, up and out; legs tucked against the body while underground
pts = [B2(H1 - 12, 34, HZ), B2(H1, 30, HZ), B2(H1, 14 - 3, HZ), B2((H1 + H2) / 2, 14 - 4, HZ), B2(H2, 14 - 3, HZ),
       B2(H2, 30, HZ), B2(H2 + 14, 34, HZ)]


def along(points, u):
    seg = [(points[i + 1] - points[i]).length for i in range(len(points) - 1)]
    tot = sum(seg); d = u * tot
    for i, L_ in enumerate(seg):
        if d <= L_ or i == len(seg) - 1:
            w = d / L_ if L_ else 0
            return points[i].lerp(points[i + 1], min(1, w)), (points[i + 1] - points[i]).normalized()
        d -= L_


for f in range(F_DIVE, F_OUT + 1):
    u = (f - F_DIVE) / (F_OUT - F_DIVE)
    u = u * u * (3 - 2 * u)
    p, fw = along(pts, u)
    up = Vector((0, 0, 1))
    if abs(fw.z) > 0.6:   # going down or up the hole: belly to the wall
        up = Vector((-fw.x, 0, 0)).normalized() if abs(fw.x) > 0.01 else Vector((-1, 0, 0))
    r2b.body(f, p - up * r2b.body_h * 0.5, fw, up)
    for L in r2b.legs:   # tucked: feet pulled in under the body
        foot = r2b.M @ Vector((L["rest"].x * 0.35, L["rest"].y * 0.45 + 0.1 * SPAN, 0.2 * S))
        r2b.leg(f, L, foot)
for L in r2b.legs:
    L["planted"] = None; L["swing"] = None


def path_a2_out(t):
    x = H2 + 14 + t * 12
    return B2(x, 34, HZ), Vector((1, 0, 0)), Vector((0, 0, 1))


walk(r2b, (F_OUT + 1, F_END2), path_a2_out)
rng = np.random.default_rng(8)
dirt_m = CM[1]
for j in range(26):   # the burst: dirt thrown up out of the second hole
    c0 = B2(H2 + rng.uniform(-5, 5), 34, HZ + rng.uniform(-5, 5))
    q = K.box(f"A2 dirt {j}", tuple(c0), (1, 1, 1), dirt_m, None)
    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=1); q.keyframe_insert("scale", frame=F_OUT - 8)
    q.scale = (1, 1, 1); q.keyframe_insert("scale", frame=F_OUT - 7)
    v = Vector((rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(14, 26)))
    for k in range(0, 34, 2):
        tt = k / FPS
        q.location = c0 + v * tt + Vector((0, 0, -16 * tt * tt))
        q.keyframe_insert("location", frame=F_OUT - 7 + k)
    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=F_OUT + 28)
takes.append(("A2 burrow pop-up", camera("02 A2 burrow pop-up", tuple(B2(75, 40, HZ + 150)), tuple(B2(75, 22, HZ)), 30), (1, F_END2)))
K.light("A2 key", tuple(B2(75, 120, HZ + 80)), 300000, (1, 0.95, 0.9), "AREA", 160)
K.light("A2 tunnel glow", tuple(B2(75, 14, HZ - 2)), 6000, (1, 0.85, 0.6))

# ------------------------------------------------------------------ A3 spike strike
OY3 = -800
g3 = np.zeros((120, 20, 80), bool); g3[:, :4, :] = True
course_mesh("A3 floor", g3, Vector((0, OY3, 0)))


def B3(x, y, z):
    return Vector((x, OY3 - z, y))


r2c = Spider("A3 R2")
PX = 80
pl = K.player("A3 player", tuple(B3(PX, 4, 40)))
F_REAR, F_STAB, F_HIT, F_BACK, F_END3 = 20, 34, 38, 60, 90
base = B3(40, 4, 40)
for f in range(1, F_END3 + 1):
    # rear up before the stab, drop back after
    if f < F_REAR:
        pitch = 0
    elif f < F_STAB:
        pitch = 28 * (f - F_REAR) / (F_STAB - F_REAR)
    elif f < F_BACK:
        pitch = 28 - 18 * (f - F_STAB) / (F_BACK - F_STAB)
    else:
        pitch = 10 - 10 * min(1, (f - F_BACK) / 12)
    fw = Vector((1, 0, math.tan(math.radians(pitch)))).normalized()
    up = Vector((-math.sin(math.radians(pitch)), 0, math.cos(math.radians(pitch))))
    r2c.body(f, base + Vector((0, 0, pitch * 0.12)), fw, up)
    for L in r2c.legs:
        rest = r2c.M @ Vector((L["rest"].x, L["rest"].y, 0))
        if f == 1 or L["planted"] is None:
            L["planted"], _ = ray_to(Vector((rest.x, rest.y, 4)), Vector((0, 0, 1)))
        foot = L["planted"]
        if L["k"] == 0 and L["side"] > 0 and f >= F_REAR:      # the right front leg strikes
            target = B3(PX - 1.5, 5.5, 40)
            raised = r2c.M @ Vector((L["rest"].x * 0.6, L["rest"].y * 0.5, 0.5 * SPAN))
            if f < F_STAB:
                foot = L["planted"].lerp(raised, (f - F_REAR) / (F_STAB - F_REAR))
            elif f <= F_HIT:
                foot = raised.lerp(target, (f - F_STAB) / (F_HIT - F_STAB))
            elif f < F_BACK:
                foot = target
            else:
                foot = target.lerp(L["planted"], min(1, (f - F_BACK) / 14))
        elif L["k"] == 0 and L["side"] < 0 and F_REAR <= f < F_BACK + 10:   # the other front leg lifts, threatening
            up_ = r2c.M @ Vector((L["rest"].x * 0.7, L["rest"].y * 0.6, 0.35 * SPAN))
            u = min(1, (f - F_REAR) / 10) if f < F_BACK else 1 - (f - F_BACK) / 10
            foot = L["planted"].lerp(up_, u)
        r2c.leg(f, L, foot)
web_m = K._m("silk")
for j in range(22):   # pinned: web strands wrap you on the hit
    a = j / 22 * math.tau
    c0 = B3(PX, 4 + (j % 5) * 0.4, 40)
    q = K.box(f"A3 web {j}", tuple(c0 + Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 0))), (0.12, 1.6, 0.12), web_m, None)
    q.rotation_euler = (rng.uniform(-1, 1), rng.uniform(-1, 1), a)
    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=1); q.keyframe_insert("scale", frame=F_HIT - 1)
    q.scale = (1, 1, 1); q.keyframe_insert("scale", frame=F_HIT + 2)
for j in range(14):   # stone chips off the spike on the hit
    c0 = B3(PX - 1.5, 5.5, 40)
    q = K.box(f"A3 chip {j}", tuple(c0), (0.35, 0.35, 0.35), K._m("spike"), None)
    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=1); q.keyframe_insert("scale", frame=F_HIT - 1)
    q.scale = (1, 1, 1); q.keyframe_insert("scale", frame=F_HIT)
    v = Vector((rng.uniform(-8, 2), rng.uniform(-6, 6), rng.uniform(4, 12)))
    for k in range(0, 20, 2):
        tt = k / FPS
        q.location = c0 + v * tt + Vector((0, 0, -16 * tt * tt)); q.keyframe_insert("location", frame=F_HIT + k)
    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=F_HIT + 20)
takes.append(("A3 spike strike", camera("03 A3 spike strike", tuple(B3(62, 22, -48)), tuple(B3(62, 12, 40)), 28), (1, F_END3)))
K.light("A3 key", tuple(B3(60, 80, -20)), 180000, (1, 0.95, 0.9), "AREA", 120)

# ------------------------------------------------------------------ render setup
w = bpy.data.worlds.new("World"); sc.world = w
try:
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.3, 0.42, 0.6, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
except Exception as e:
    print("world", e)
sc.render.engine = "CYCLES"; sc.cycles.samples = 64; sc.cycles.use_denoising = True; sc.cycles.use_preview_denoising = True
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
sc.frame_start, sc.frame_end = 1, 220
sc.camera = takes[0][1]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
if VIDEO:
    rdir = os.path.join(os.path.dirname(OUT), "renders_anim")
    os.makedirs(rdir, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.cycles.samples = 16
    sc.render.image_settings.media_type = "VIDEO"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"; sc.render.ffmpeg.constant_rate_factor = "MEDIUM"
    for nm, cam, (f0, f1) in takes:
        sc.camera = cam; sc.frame_start, sc.frame_end = f0, f1
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".mp4")
        bpy.ops.render.render(animation=True)
        print("video", sc.render.filepath)
    sc.camera = takes[0][1]; sc.frame_start, sc.frame_end = 1, 220
print("done", OUT)
