"""R2 brute animation tests, round 2: J's lair notes 1-3 (2026-10-19).

J: "the legs should never collide, the bury animation should be a quick one instead of that one that isnt animated,
the strike is only okay making no contact if its using the yellow constructs and sending webs that way, otherwise i
want a contacting strike".

blender.exe -b --python spider_anim_tests.py -- <out.blend> [--video] [--only W1,D2,...] [--check]

Every take sits in its own area along x (400 blocks apart) with its own camera, and every leg of every frame goes
through check_legs(): segment-to-segment distance between every pair of legs (femur and tibia+spike as capsules of
their own thickness) and every leg against the body boxes. The counts are printed and burnt into each video's label.

Note 1, legs never collide (floor, 40-degree slope, then spiralling up a round column):
  W1 wide stance   foot rests fanned wider per leg pair, knees bend up AND out (no two femurs share a plane)
  W2 outward arcs  W1 plus every swing lifts outward in an arc, away from the neighbouring legs
  W3 wave gait     W2 plus a wave gait (two legs move at a time, back to front), the slowest and calmest
  (before: the round-1 A1 gait is measured, not rendered; its count is printed as "A1 before")
  Column fix for all three: a foot that misses the surface below it is cast round toward the column, so legs wrap the
  column instead of bunching in the air.
Note 2, the burrow dive is a quick animated dig (each: walk up, dig in under a second, scrabble along the tunnel with
the legs planted on the walls, and the same pop-up out of the far hole):
  D1 head-first    front legs claw the rim, nose drops, it pours in head first; dirt thrown back over it
  D2 corkscrew     it spins once as it drills down the hole, legs braced on the walls, dirt spiralling out
  D3 digs its own  no hole: it tears a new one in the ground, the dirt flying off in chunks as it sinks
Note 3, strikes:
  S1 rear and stab R2 rears, lunges and the right spike hits your chest; you're thrown back and webbed
  S2 lunge pin     R2 charges, both spikes come down: one pins you to the floor, the other stabs the ground beside you
  S3 double jab    left spike, then right spike: two hits, the second launches you
  C1b webs         the yellow construct spider (C1b dread armour) stops short and shoots three hard-light webs at you
                   from range: the only strike that doesn't touch you
"""
import math, os, sys
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_blender_kit as K

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
VIDEO = "--video" in argv
ONLY = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
CHECK_ONLY = "--check" in argv
RESOLVE = "--no-resolve" not in argv
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
K.sc = sc
CM = K.cave_materials(textured=True)
FPS = 24
sc.render.fps = FPS
SPAN = 36.0
S = SPAN / 10.0
AREA = 400.0
rng = np.random.default_rng(8)
REPORT = {}


def want(code):
    return ONLY is None or code in ONLY


# ------------------------------------------------------------------ gait settings
class Gait:
    def __init__(self, spread=0.0, knee_out=0.0, arc_out=0.0, wave=False, period=14, lift=0.12, wrap=True):
        self.spread, self.knee_out, self.arc_out, self.wave = spread, knee_out, arc_out, wave
        self.period, self.lift, self.wrap = period, lift * SPAN, wrap


OLD = Gait(wrap=False)                                         # round 1, for the "before" count


def leg_layout(spread):
    """Hip, rest foot (local, +Y forward) for 8 legs. spread 0 = round 1 (52/18/-16/-50 degrees, hips in two straight
    rows 1.7 blocks apart). spread 1 = the fix: legs fanned to 60/22/-16/-48, hips spaced round the edge of the head
    (each leg leaves the body pointing the way it goes), feet a little further out."""
    out = []
    R = SPAN / 2
    body_h, ceph_w, ceph_l = 1.5 * S, 2.0 * S, 2.1 * S
    base = (52, 18, -16, -50)
    wide = (60, 22, -16, -48)
    ceph_y = 0.4 * S
    for s in (-1, 1):
        for k in range(4):
            phi = math.radians(base[k] + (wide[k] - base[k]) * spread)
            dvec = Vector((s * math.cos(phi), math.sin(phi), 0))
            row = Vector((s * ceph_w * 0.45, ceph_l * (0.35 - k * 0.22), body_h))
            arc = Vector((s * math.cos(phi) * ceph_w * 0.44, ceph_y + math.sin(phi) * ceph_l * 0.5, body_h))
            hip = row.lerp(arc, spread)
            reach = (R - row.length * 0.5) * (1 + 0.06 * spread)
            foot = hip + dvec * reach; foot.z = 0.0
            knee = hip + dvec * (R * 0.40) + Vector((0, 0, body_h * 0.95))
            ankle = knee + (foot - knee) * 0.6 + dvec * R * 0.05
            out.append((s, k, hip, knee, ankle, foot))
    return out


# ------------------------------------------------------------------ an animatable R2
class Spider:
    """R2 brute with legs that can be re-posed: each leg is femur (hip->knee) and a tibia+spike (knee->foot).
    ghost=True builds nothing (used to measure the round-1 gait)."""

    def __init__(self, name, gait, ghost=False):
        self.name, self.gait, self.ghost = name, gait, ghost
        self.body_h = 1.5 * S
        self.ceph_w, self.ceph_l = 2.0 * S, 2.1 * S
        ceph_c = Vector((0, 0.4 * S, self.body_h + 0.2 * S))
        abd = (2.8 * S, 3.2 * S, 2.4 * S)
        waist = 0.75 * S if gait.spread else 0.0          # the fix: a short waist (pedicel) so the rear thighs clear the abdomen
        abd_c = Vector((0, -self.ceph_l * 0.5 - abd[1] * 0.45 - waist, self.body_h + abd[2] * 0.25))
        # body boxes (centre, half size) for the collision check: the _blob core + its three cross boxes
        self.body_boxes = []
        for c_, sz in ((ceph_c, (self.ceph_w, self.ceph_l, 1.0 * S)), (abd_c, abd)):
            sx, sy, sz_ = sz
            for hs in ((sx * .4, sy * .4, sz_ * .4), (sx * .5, sy * .3, sz_ * .3), (sx * .3, sy * .5, sz_ * .3), (sx * .3, sy * .3, sz_ * .5)):
                self.body_boxes.append((c_.copy(), Vector(hs)))
        self.abd_boxes = self.body_boxes[4:]
        self.rec = {}
        self.legs = []
        t = 0.42 * S
        self.r_fem, self.r_tib = t * 0.5, t * 0.85 * 0.5
        if not ghost:
            self.root = K.empty(name)
            mb, hair = K._m("brute"), K._m("hair")
            K._blob(name + " head", tuple(ceph_c), (self.ceph_w, self.ceph_l, 1.0 * S), mb, self.root)
            K._blob(name + " abdomen", tuple(abd_c), abd, mb, self.root)
            if waist:
                K.box(name + " waist", (0, -self.ceph_l * 0.5 - waist * 0.4, self.body_h + 0.3 * S), (0.9 * S, waist * 1.6, 0.8 * S), mb, self.root)
            r_ = np.random.default_rng(3)
            for j in range(30):
                off = Vector(tuple(r_.uniform(-0.5, 0.5, 3) * np.array(abd)))
                K.box(f"{name} hair{j}", tuple(abd_c + off.normalized() * abd[0] * 0.5), (0.12 * S, 0.12 * S, 0.35 * S), hair, self.root)
            for i in range(8):
                row = i // 4
                K.box(f"{name} eye{i}", tuple(ceph_c + Vector(((i % 4 - 1.5) * 0.28 * S, self.ceph_l * 0.5, 0.25 * S + row * 0.25 * S))), (0.18 * S,) * 3, K._m("eye"), self.root)
            for sx in (-1, 1):
                K._seg(f"{name} fang{sx}", ceph_c + Vector((sx * 0.3 * S, self.ceph_l * 0.5, -0.2 * S)),
                       ceph_c + Vector((sx * 0.25 * S, self.ceph_l * 0.55, -0.7 * S)), 0.25 * S, K._m("fang"), self.root)
        for sd, k, hip, knee, ankle, foot in leg_layout(gait.spread):
            L1 = (knee - hip).length
            L2 = (ankle - knee).length + (foot - ankle).length
            parts = {}
            if not ghost:
                for nm, m, thick in (("femur", K._m("brute"), t), ("tibia", K._m("brute"), t * 0.85), ("silk", K._m("silk"), t * 1.2),
                                     ("stone0", K._m("spike"), t * 1.0), ("stone1", K._m("spike"), t * 0.66), ("stone2", K._m("spike"), t * 0.33)):
                    parts[nm] = K.box(f"{name} leg{sd:+d}{k} {nm}", (0, 0, 0), (thick, 1, thick), m, None)
                    parts[nm].rotation_mode = "QUATERNION"
            # wave gait: back to front on each side, the two sides half a cycle apart; tetrapod: alternate groups
            off = (((3 - k) / 4.0) + (0.0 if sd < 0 else 0.5)) % 1.0 if gait.wave else (0.0 if (k + (0 if sd < 0 else 1)) % 2 == 0 else 0.5)
            self.legs.append(dict(side=sd, k=k, hip=hip.copy(), rest=foot.copy(), L1=L1, L2=L2, parts=parts,
                                  off=off, planted=None, swing=None))

    def _place(self, ob, a, b, frame):
        v = b - a
        ob.location = (a + b) / 2
        ob.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(v.normalized())
        ob.scale = (ob.scale.x, max(v.length, 0.01), ob.scale.z)
        ob.keyframe_insert("location", frame=frame); ob.keyframe_insert("rotation_quaternion", frame=frame)
        ob.keyframe_insert("scale", frame=frame)

    def body(self, frame, pos, forward, up):
        """Key the body: pos is the point on the surface under it, forward/up its directions."""
        up = up.normalized(); fw = (forward - up * forward.dot(up)).normalized(); rt = fw.cross(up)
        m = Matrix(((rt.x, fw.x, up.x), (rt.y, fw.y, up.y), (rt.z, fw.z, up.z)))
        self.M = Matrix.Translation(pos) @ m.to_4x4()
        self.Mi = self.M.inverted()
        self.up, self.fw, self.pos = up, fw, pos.copy()
        if not self.ghost:
            self.root.rotation_mode = "QUATERNION"
            self.root.location = pos
            self.root.rotation_quaternion = m.to_quaternion()
            self.root.keyframe_insert("location", frame=frame); self.root.keyframe_insert("rotation_quaternion", frame=frame)

    def centre(self):
        return self.M @ Vector((0, 0, self.body_h))

    def solve(self, L, foot):
        """Two-bone solve from the hip to the foot. The knee bends along the body's up, tilted outward by knee_out
        (W gaits), so neighbouring femurs fan apart instead of sharing one vertical plane."""
        H = self.M @ L["hip"]
        d = foot - H
        dist = max(0.5, min(d.length, L["L1"] + L["L2"] - 0.05))
        dirn = d.normalized()
        along = (L["L1"] ** 2 - L["L2"] ** 2 + dist ** 2) / (2 * dist)
        h = math.sqrt(max(0.0, L["L1"] ** 2 - along ** 2))
        outw = (self.M.to_3x3() @ Vector((L["side"], 0, 0)))
        bend = (self.up + outw * (self.gait.knee_out + L.get("kb", 0.0)) + self.fw * L.get("kf", 0.0)).normalized()
        upp = (bend - dirn * bend.dot(dirn))
        upp = upp.normalized() if upp.length > 1e-4 else self.up
        knee = H + dirn * along + upp * h
        F = H + dirn * dist
        return H, knee, F

    def leg(self, frame, L, foot):
        H, knee, F = self.solve(L, foot)
        self.rec.setdefault(frame, {})[id(L)] = (H.copy(), knee.copy(), F.copy())
        self.recM = getattr(self, "recM", {}); self.recM[frame] = self.Mi.copy()
        if self.ghost:
            return F
        p = L["parts"]
        self._place(p["femur"], H, knee, frame)
        ankle = knee + (F - knee) * 0.62
        self._place(p["tibia"], knee, ankle, frame)
        v = F - ankle
        self._place(p["silk"], ankle, ankle + v * 0.22, frame)
        for i, (t0, t1) in enumerate(((0.18, 0.55), (0.55, 0.82), (0.82, 1.0))):
            self._place(p[f"stone{i}"], ankle + v * t0, ankle + v * t1, frame)
        return F


# ------------------------------------------------------------------ the collision check (J: "the legs should never collide")
def seg_dist(p1, q1, p2, q2):
    """Closest distance between segments p1q1 and p2q2 (Ericson, Real-Time Collision Detection 5.1.9)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1.dot(d1), d2.dot(d2), d2.dot(r)
    if a <= 1e-9 and e <= 1e-9:
        return r.length
    if a <= 1e-9:
        s, t = 0.0, min(1, max(0, f / e))
    else:
        c = d1.dot(r)
        if e <= 1e-9:
            t, s = 0.0, min(1, max(0, -c / a))
        else:
            b = d1.dot(d2); den = a * e - b * b
            s = min(1, max(0, (b * f - c * e) / den)) if den > 1e-9 else 0.0
            t = (b * s + f) / e
            if t < 0:
                t, s = 0.0, min(1, max(0, -c / a))
            elif t > 1:
                t, s = 1.0, min(1, max(0, (b - c) / a))
    return ((p1 + d1 * s) - (p2 + d2 * t)).length


def box_dist(p, c, h):
    q = Vector((max(abs(p.x - c.x) - h.x, 0), max(abs(p.y - c.y) - h.y, 0), max(abs(p.z - c.z) - h.z, 0)))
    return q.length


def frame_hits(sp, chains, margin=0.05):
    """chains: per leg (H, knee, F). Returns {leg index: push kind} for legs touching a neighbour or the body."""
    segs = []
    for (H, kn, F) in chains:
        Ht = H + (kn - H).normalized() * min(1.2, (kn - H).length * 0.5)
        segs.append(((Ht, kn, sp.r_fem), (kn, F, sp.r_tib)))
    hits = {}
    for i in range(8):
        for j in range(i + 1, 8):
            if any(seg_dist(a[0], a[1], b[0], b[1]) - a[2] - b[2] < -margin for a in segs[i] for b in segs[j]):
                hits.setdefault(i, []).append(j); hits.setdefault(j, []).append(i)
    for i in range(8):
        for n_, (p, q, r) in enumerate(segs[i]):
            boxes = sp.abd_boxes if n_ == 0 else sp.body_boxes
            if any(any(box_dist(sp.Mi @ (p + (q - p) * float(t)), c, h) < r - margin for c, h in boxes) for t in np.linspace(0.08 if n_ else 0.0, 1, 12)):
                hits.setdefault(i, []).append("body")
                break
    return hits


def resolve(sp, feet, swinging, iters=40, locked=()):
    """Nudge feet until no leg touches another leg or the body on this frame: a swinging foot moves first (planted
    feet only if both legs are planted). Away from the neighbour's foot sideways, or straight out from the body."""
    up = sp.up
    C = sp.pos
    for it in range(iters):
        chains = [sp.solve(L, feet[i]) for i, L in enumerate(sp.legs)]
        hits = frame_hits(sp, chains, margin=-0.1)         # aim for a 0.1-block gap, stricter than the check
        if not hits:
            return feet, True
        for i, others in hits.items():
            if i in locked:
                continue
            push = Vector((0, 0, 0))
            L = sp.legs[i]
            L["kb"] = min(2.5, L.get("kb", 0.0) + 0.3)     # swing this knee further out
            for o in others:
                if o == "body":
                    v = feet[i] - C
                    push += (v - up * v.dot(up)).normalized() * 1.2
                    if L["k"] >= 2:
                        L["kf"] = min(1.5, L.get("kf", 0.0) + 0.25)     # rear thigh: knee forward, off the abdomen
                else:
                    Lo = sp.legs[o]
                    if Lo["side"] == L["side"]:                          # same side: knees part fore and aft
                        L["kf"] = max(-1.5, min(1.5, L.get("kf", 0.0) + (0.25 if L["k"] < Lo["k"] else -0.25)))
                    if swinging[o] and not swinging[i] and it < iters // 2 and o not in locked:
                        continue                       # the swinging neighbour gives way (both, if that isn't enough)
                    v = feet[i] - feet[o]
                    v = v - up * v.dot(up)
                    if v.length < 1e-3:
                        v = sp.M.to_3x3() @ Vector((sp.legs[i]["side"], 0, 0))
                    push += v.normalized() * 0.9
            if push.length > 0:
                f2 = feet[i] + push
                h = _ray(f2 + up * 6, -up, 14, front_only=True)
                feet[i] = h if h is not None else f2
    chains = [sp.solve(L, feet[i]) for i, L in enumerate(sp.legs)]
    return feet, not frame_hits(sp, chains)


def check_legs(sp, label, margin=0.05):
    """Per frame: every pair of legs (femur minus the 1.2 blocks inside the head, tibia+spike) as capsules of their
    own half-thickness, and every leg against the body boxes (femurs against the abdomen only: they start in the head).
    Returns (frames with a hit, total frames, smallest leg-to-leg clearance in blocks)."""
    bad, worst, nfr = [], 1e9, 0
    why = {}
    for f, legs in sorted(sp.rec.items()):
        nfr += 1
        Mi = sp.recM[f]
        segs = []
        for L in sp.legs:
            H, kn, F = legs[id(L)]
            Ht = H + (kn - H).normalized() * min(1.2, (kn - H).length * 0.5)
            segs.append(((Ht, kn, sp.r_fem), (kn, F, sp.r_tib)))
        hit = False
        for i in range(8):
            for j in range(i + 1, 8):
                for a in segs[i]:
                    for b in segs[j]:
                        d = seg_dist(a[0], a[1], b[0], b[1]) - a[2] - b[2]
                        worst = min(worst, d)
                        if d < -margin:
                            hit = True
                            kk = f"leg{sp.legs[i]['side']:+d}{sp.legs[i]['k']}-{'ft'[segs[i].index(a)]} x leg{sp.legs[j]['side']:+d}{sp.legs[j]['k']}-{'ft'[segs[j].index(b)]}"
                            why[kk] = why.get(kk, 0) + 1
        for i in range(8):
            for n_, (p, q, r) in enumerate(segs[i]):
                boxes = sp.abd_boxes if n_ == 0 else sp.body_boxes
                for t in np.linspace(0.08 if n_ else 0.0, 1, 12):
                    lp = Mi @ (p + (q - p) * float(t))
                    if any(box_dist(lp, c, h) < r - margin for c, h in boxes):
                        hit = True
                        kk = f"leg{sp.legs[i]['side']:+d}{sp.legs[i]['k']}-{'ft'[n_]} x body"
                        why[kk] = why.get(kk, 0) + 1
                        break
        if hit:
            bad.append(f)
    if os.environ.get("LEGDUMP") and label != "A1 before":
        fd = int(os.environ["LEGDUMP"]); Mi = sp.recM[fd]
        for L in sp.legs:
            H, kn, F = sp.rec[fd][id(L)]
            print(f"  dump {label} f{fd} leg{L['side']:+d}{L['k']} hip {tuple(round(c,1) for c in Mi@H)} knee {tuple(round(c,1) for c in Mi@kn)} foot {tuple(round(c,1) for c in Mi@F)} reach {L['L1']+L['L2']:.1f} d {(F-H).length:.1f}")
        print("  abd boxes", [(tuple(round(c,1) for c in c_), tuple(round(c,1) for c in h)) for c_, h in sp.abd_boxes])
    REPORT[label] = dict(bad=len(bad), frames=nfr, clearance=round(worst, 2), first=bad[:6])
    if os.environ.get("LEGDEBUG"):
        print("  frames", bad)
        print("  why", sorted(why.items(), key=lambda kv: -kv[1])[:12])
    print(f"LEGCHECK {label}: {len(bad)}/{nfr} frames with legs touching, closest leg-to-leg gap {worst:.2f} blocks, first {bad[:6]}")
    return len(bad), nfr, worst


# ------------------------------------------------------------------ casting feet onto the course
COURSES = []                                           # BVH trees of the ground meshes only (feet never land on spiders)


def _ray(o, d, dist, front_only=False):
    """Nearest hit on a ground mesh. front_only: a ray that starts inside rock first meets a face from behind
    (its normal along the ray); count that as a miss instead of landing the foot deep in the stone."""
    best = None
    d = d.normalized()
    for t in COURSES:
        loc, nrm, idx, dd = t.ray_cast(o, d, dist)
        if loc is not None and (best is None or dd < best[1]):
            best = (loc, dd, nrm)
    if best is None or (front_only and best[2].dot(d) > 0):
        return None
    return Vector(best[0])


def _rayn(o, d, dist):
    """Front-face hit and its normal, or (None, None)."""
    best = None
    d = d.normalized()
    for t in COURSES:
        loc, nrm, idx, dd = t.ray_cast(o, d, dist)
        if loc is not None and (best is None or dd < best[1]):
            best = (loc, dd, nrm)
    if best is None or best[2].dot(d) > 0:
        return None, None
    return Vector(best[0]), Vector(best[2]).normalized()


def march_foot(sp, P, step=1.5):
    """Walk from the point under the body toward the aim along the surface itself, so a foot lands as far away as it
    was aimed measured over the ground: round a column, up a wall, over a ledge. (A straight cast bunched all the
    fore and aft feet into one strip down the column's sides.)"""
    up = sp.up
    q, n = _rayn(sp.pos + up * 3, -up, 8)
    if q is None:
        return None
    D0 = P - sp.pos
    D0 = D0 - up * D0.dot(up)
    remaining = D0.length
    if remaining < 1e-3:
        return q
    D0.normalize()
    n_prev = up
    for _ in range(int(remaining / step) + 6):
        if remaining <= 1e-3:
            break
        d = D0 - n * D0.dot(n)
        if d.length < 0.25:
            d = n_prev - n * n_prev.dot(n)
        d.normalize()
        st = min(step, remaining)
        h, hn = _rayn(q + n * 0.05, d, st)                 # a wall in the way: climb onto it
        if h is not None:
            remaining -= (h - q).length
            q, n_prev, n = h, n, hn
            continue
        q2 = q + d * st
        h, hn = _rayn(q2 + n * 1.5, -n, 3.5)               # follow the surface down
        if h is None:                                     # fell off an edge: wrap round it
            h, hn = _rayn(q2 - n * 1.2, -d, st * 1.5)
        if h is None:
            break
        remaining -= st
        if (hn - n).length > 1e-3:
            n_prev = n
        q, n = h, hn
    return q


def cast_foot(sp, P, wrap=True, reach=12.0):
    """Where a foot aimed at P lands. Round 1 cast only straight down the body's up (misses = feet in the air, which
    bunched the legs on the column). Now, keeping only spots a leg can really reach (in front of the spider's back
    plane, within reach): open ground casts down from high above P, then into a wall ahead, then round a column;
    holes and tunnels ("enclosed") cast from the body centre out toward P first."""
    up = sp.up
    if not wrap:
        h = _ray(P + up * reach, -up, reach * 2.5)
        return h if h is not None else P
    C = sp.centre()

    def ok(h):
        return h is not None and (sp.Mi @ h).z <= 2.5 and (h - C).length <= 0.62 * SPAN
    tries = []
    if wrap == "enclosed":
        tries.append(lambda: _ray(C, P - C, (P - C).length * 1.35))
    tries.append(lambda: _ray(P + up * 40, -up, 70, front_only=True))
    tries.append(lambda: _ray(C, P - C, (P - C).length * 1.35, front_only=True))
    tgt = sp.pos - up * 25
    tries.append(lambda: _ray(P + up * 2, tgt - P, (tgt - P).length, front_only=True))
    for t in tries:
        h = t()
        if ok(h):
            return h
    return P


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def animate(sp, frames, pose, rest_fn=None, period=None, lift=None, arc=None, wrap=None, foot_hook=None, sf=None, enclosed=None, fix=True):
    """Drive the body by pose(f) -> (ground point, forward, up) and step the legs. rest_fn(L, f) gives each foot's
    aim in body space (default: the rest pose a little forward). Each leg swings for sf of the cycle (0.5 tetrapod,
    0.25 wave) from where it was planted to its new aim, lifted along up and arced outward by arc_out."""
    g = sp.gait
    period = period or g.period
    lift = g.lift if lift is None else lift
    arc = g.arc_out if arc is None else arc
    wrap = g.wrap if wrap is None else wrap
    sf = sf or (0.25 if g.wave else 0.5)
    f0, f1 = frames
    for f in range(f0, f1 + 1):
        pos, fw, up = pose(f)
        sp.body(f, pos, fw, up)
        # put each step's middle on the rest spot: lead the aim by half the distance the body covers while planted
        vel = sp.Mi.to_3x3() @ (pose(f + 1)[0] - pos)
        lead = Vector((vel.x, vel.y, 0)) * (period * (1 - sf) * 0.5)
        phase = ((f - f0) % period) / period
        feet, swinging = [], []
        for L in sp.legs:
            aim = (rest_fn(L, f) if rest_fn else Vector((L["rest"].x, L["rest"].y, 0.0))) + lead
            tgt = cast_foot(sp, sp.M @ aim, "enclosed" if (enclosed and enclosed(f)) else wrap)
            if L["planted"] is None:
                L["planted"] = tgt
            ph = (phase - L["off"]) % 1.0
            dur = max(2, int(round(period * sf)))
            # catch-up step: a planted foot left far from its aim (the body turned or rolled) steps now, off-cycle
            if fix and RESOLVE and ph >= sf and L.get("fs") is None and L["swing"] is None:
                if (sp.Mi @ L["planted"] - aim).length > 0.25 * SPAN:
                    L["fs"] = f
            forced = L.get("fs") is not None and f - L["fs"] <= dur
            if not forced:
                L["fs"] = None
            sw = ph < sf or forced
            if sw:
                if L["swing"] is None:
                    L["swing"] = L["planted"].copy()
                u = (f - L["fs"]) / dur if forced else ph / sf
                outw = sp.M.to_3x3() @ Vector((L["side"], 0, 0))
                foot = L["swing"].lerp(tgt, smooth(u)) + up * (math.sin(u * math.pi) * lift) + outw * (math.sin(u * math.pi) * arc)
                if foot_hook:
                    foot_hook(sp, L, f, foot, True)
                if forced and u >= 1:
                    L["planted"] = tgt; L["swing"] = None; L["fs"] = None; sw = False; foot = tgt
            else:
                if L["swing"] is not None:
                    L["planted"] = tgt
                    L["swing"] = None
                foot = L["planted"]
            feet.append(foot); swinging.append(sw)
        if RESOLVE and fix:
            for L in sp.legs:
                L["kb"] = max(0.0, L.get("kb", 0.0) - 0.15)   # knees relax back over a few frames
                L["kf"] = L.get("kf", 0.0) * 0.85
            feet, ok = resolve(sp, feet, swinging)
            for i, L in enumerate(sp.legs):
                if not swinging[i]:
                    L["planted"] = feet[i]         # a nudged planted foot stays where it was moved
        for i, L in enumerate(sp.legs):
            sp.leg(f, L, feet[i])


def reset(sp):
    for L in sp.legs:
        L["planted"] = None; L["swing"] = None; L["fs"] = None


def keyed_pose(keys):
    """keys: [(frame, pos, fw, up)], smooth in between (positions eased, orientation slerped)."""
    def mat_of(fw, up):
        up = up.normalized(); fw = (fw - up * fw.dot(up)).normalized(); rt = fw.cross(up)
        return Matrix(((rt.x, fw.x, up.x), (rt.y, fw.y, up.y), (rt.z, fw.z, up.z))).to_quaternion()
    qs = [mat_of(k[2], k[3]) for k in keys]

    def pose(f):
        if f <= keys[0][0]:
            i, u = 0, 0.0
        elif f >= keys[-1][0]:
            i, u = len(keys) - 2, 1.0
        else:
            i = max(j for j in range(len(keys) - 1) if keys[j][0] <= f)
            u = (f - keys[i][0]) / (keys[i + 1][0] - keys[i][0])
        u2 = smooth(u)
        p = keys[i][1].lerp(keys[i + 1][1], u2)
        q = qs[i].slerp(qs[i + 1], u2)
        m = q.to_matrix()
        return p, m.col[1].copy(), m.col[2].copy()
    return pose


def smoothed(pose, half=8, f_lo=1, f_hi=10 ** 6):
    """Average a path's position and turn over +-half frames. Round 1's course path turned the spider 90 degrees in a
    single frame where it stepped from the plateau onto the column, so its planted feet ended up crossed."""
    def mat_q(fw, up):
        up = up.normalized(); fw = (fw - up * fw.dot(up)).normalized(); rt = fw.cross(up)
        return Matrix(((rt.x, fw.x, up.x), (rt.y, fw.y, up.y), (rt.z, fw.z, up.z))).to_quaternion()

    def p2(f):
        acc_p, acc_q, n, q0 = Vector((0, 0, 0)), Vector((0, 0, 0, 0)), 0, None
        for g_ in range(f - half, f + half + 1):
            g_ = min(f_hi, max(f_lo, g_))
            p, fw, up = pose(g_)
            q = mat_q(fw, up)
            if q0 is None:
                q0 = q
            if q.dot(q0) < 0:
                q.negate()
            acc_p += p; acc_q += Vector(q); n += 1
        q = Quaternion(acc_q / n).normalized()
        m = q.to_matrix()
        return acc_p / n, m.col[1].copy(), m.col[2].copy()
    return p2


# ------------------------------------------------------------------ scene helpers
def course_mesh(name, solid, loc, mat_idx=0, cut=None):
    s_ = solid.copy()
    if cut is not None:
        s_[:, :, cut + 1:] = False
    o = K.voxel_mesh(name, s_, lambda i, n, a, d: np.full(len(i), mat_idx), CM)
    o.location = loc
    mw = Matrix.Translation(Vector(loc))
    COURSES.append(BVHTree.FromPolygons([mw @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons]))
    return o


LABEL_M = None


def follow(cam, target):
    """Keep the spider in frame: the camera stays put and turns to follow it."""
    c = cam.constraints.new("TRACK_TO")
    c.target = target; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    return cam


def label(cam, text, sub=""):
    """Take name burnt into the top-left of the camera's view."""
    global LABEL_M
    if LABEL_M is None:
        LABEL_M = K.mat("label", (1, 1, 1), 0.5, (1, 1, 1), 1.2)
    for i, (t, sz) in enumerate(((text, 0.055), (sub, 0.032))):
        if not t:
            continue
        cu = bpy.data.curves.new(cam.name + f" label{i}", "FONT"); cu.body = t; cu.size = sz
        ob = bpy.data.objects.new(cam.name + f" label{i}", cu); sc.collection.objects.link(ob)
        ob.data.materials.append(LABEL_M)
        ob.parent = cam
        ob.location = (-0.33, 0.17 - i * 0.05, -1.0)
    return cam


def dirt_cube(origin, vel, f0, life=18, size=None, m=None):
    size = size or rng.uniform(0.5, 1.0)
    q = K.box("dirt", tuple(origin), (size,) * 3, m or CM[1], None)
    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=max(1, f0 - 1))
    q.scale = (size,) * 3; q.keyframe_insert("scale", frame=f0)
    q.rotation_euler = (0, 0, 0); q.keyframe_insert("rotation_euler", frame=f0)
    for k in range(0, life + 1, 2):
        tt = k / FPS
        q.location = origin + vel * tt + Vector((0, 0, -20 * tt * tt))
        q.keyframe_insert("location", frame=f0 + k)
    q.rotation_euler = tuple(rng.uniform(-4, 4, 3)); q.keyframe_insert("rotation_euler", frame=f0 + life)
    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=f0 + life + 1)
    return q


takes = []


def take(code, title, cam, frames):
    takes.append((code, title, cam, frames))


def area(i):
    return Vector((i * AREA, 0, 0))


# ------------------------------------------------------------------ note 1: the walk course
X, Y, Z = 170, 80, 90
g = np.zeros((X, Y, Z), bool)
g[:, :4, :] = True
xs = np.arange(X)[:, None, None]; ys = np.arange(Y)[None, :, None]; zs = np.arange(Z)[None, None, :]
SLOPE0, SLOPE1, TOP = 50, 80, 4 + 25
h_ = np.clip((xs - SLOPE0) * math.tan(math.radians(40)), 0, TOP - 4) + 4
g |= ys < h_
COLX, COLZ, COLR = 125, 45, 14
g |= ((xs - COLX) ** 2 + (zs - COLZ) ** 2 <= COLR ** 2) & (ys < 75)


def make_path_a1(O):
    def B1(x, y, z):
        return O + Vector((x, -z, y))

    def path(f, f0=1, f1=200, roll=True):
        """0-0.25 floor, 0.25-0.45 slope, 0.45-0.55 plateau, 0.55-1 spiral up the column. roll=True (the fix): the
        spider walks past the column's side and rolls onto it, heading on; round 1 (roll=False) walked at the
        column's middle and turned 90 degrees on the spot at its foot."""
        t = (f - f0) / (f1 - f0)
        z0 = COLZ - COLR - 5 if roll else 45
        if t < 0.25:
            u = t / 0.25; x = 10 + u * (SLOPE0 - 10)
            return B1(x, 4, z0), Vector((1, 0, 0)), Vector((0, 0, 1))
        if t < 0.45:
            u = (t - 0.25) / 0.2; x = SLOPE0 + u * (SLOPE1 - SLOPE0 - 6)
            yy = 4 + (x - SLOPE0) * math.tan(math.radians(40))
            n = Vector((-math.sin(math.radians(40)), 0, math.cos(math.radians(40))))
            n = Vector((0, 0, 1)).lerp(n, min(1, u * 4)).normalized()
            return B1(x, min(yy, TOP), z0), Vector((1, 0, math.tan(math.radians(40)) * (1 - min(1, max(0, u - 0.8) * 5)))), n
        x_end = COLX - 3 if roll else COLX - COLR - 2
        if t < 0.55:
            u = (t - 0.45) / 0.1; x = SLOPE1 - 6 + u * (x_end - (SLOPE1 - 6))
            return B1(x, TOP, z0 + (COLZ - COLR - z0) * smooth(u) * 0.6 if roll else z0), Vector((1, 0, 0)), Vector((0, 0, 1))
        u = (t - 0.55) / 0.45
        a0 = 1.5 * math.pi - 0.2 if roll else math.pi
        ang = a0 + u * math.pi * (1.2 if roll else 1.6)
        yy = TOP + u * 32
        radial = Vector((math.cos(ang), -math.sin(ang), 0))
        p = B1(COLX + math.cos(ang) * COLR, yy, COLZ + math.sin(ang) * COLR)
        tang = Vector((-math.sin(ang), -math.cos(ang), 0)) * (COLR * math.pi * (1.2 if roll else 1.6)) + Vector((0, 0, 32))
        up = Vector((0, 0, 1)).lerp(radial, min(1, u * 5)).normalized()
        return p, tang.normalized(), up
    return B1, path


F_WALK = 200
walk_takes = [("W1", "W1 wide stance", Gait(spread=1.0, knee_out=0.45)),
              ("W2", "W2 outward arcs", Gait(spread=1.0, knee_out=0.45, arc_out=0.07 * SPAN)),
              ("W3", "W3 wave gait", Gait(spread=1.0, knee_out=0.45, arc_out=0.07 * SPAN, wave=True, period=16, lift=0.09))]
ai = 0
need_course = any(want(c) for c, _, _ in walk_takes) or want("A1")
if need_course:
    O = area(ai)
    course_mesh("W course", g, O)
    B1, path_raw = make_path_a1(O)
    path = smoothed(path_raw, 8, 1, F_WALK)
    # the round-1 gait, measured on the same course (not rendered)
    old = Spider("A1 before", OLD, ghost=True)
    animate(old, (1, F_WALK), lambda f: path_raw(f, roll=False), fix=False)
    check_legs(old, "A1 before")
    K.light("W key", tuple(B1(80, 140, -60)), 450000, (1, 0.95, 0.9), "AREA", 200)
    K.player("W player", tuple(B1(30, 4, 20)))
    for code, title, gt in walk_takes:
        if not want(code):
            continue
        sp = Spider(code + " R2", gt)
        # each take on its own copy of the course: shift the spider sideways in z by 0 (same course, own spider),
        # so render the takes one at a time (only one spider visible per camera: hide the others per take)
        animate(sp, (1, F_WALK), path)
        n, nf, gap = check_legs(sp, code)
        cam = follow(K.camera(f"{code} cam", tuple(B1(100, 62, -75)), tuple(B1(95, 25, 45)), 24), sp.root)
        label(cam, title, f"legs touching: {n} of {nf} frames  (round 1: {REPORT['A1 before']['bad']})")
        take(code, title, cam, (1, F_WALK))
        sp.objs = [o for o in bpy.data.objects if o.name.startswith(code + " R2")]
    ai += 1


# ------------------------------------------------------------------ note 2: quick animated digs
X2, Y2, Z2 = 160, 50, 80
H1, H2, HZ, HR = 35, 112, 40, 9
TY, TR = 14, 8.5                                       # tunnel centre height and radius
xs2 = np.arange(X2)[:, None, None]; ys2 = np.arange(Y2)[None, :, None]; zs2 = np.arange(Z2)[None, None, :]


def dig_course(own_hole):
    g2 = np.zeros((X2, Y2, Z2), bool)
    g2[:, :34, :] = True
    for hx in (H1, H2):
        g2 &= ~(((xs2 - hx) ** 2 + (zs2 - HZ) ** 2 <= HR ** 2) & (ys2 >= TY))
    g2 &= ~((((ys2 - TY) ** 2 + (zs2 - HZ) ** 2) <= TR ** 2) & (xs2 >= H1) & (xs2 <= H2))
    return g2


F_RIM, F_DUG, F_TEND, F_TOP, F_END = 24, 44, 84, 100, 128


def tunnel_rest(L, f):
    """In the hole and tunnel the legs reach fore and aft along the walls, like a spider in its burrow."""
    k, s = L["k"], L["side"]
    fwd = (0.85, 0.45, -0.35, -0.8)[k]
    return Vector((s * 0.42 * SPAN * (0.55 if abs(fwd) > 0.6 else 0.9), fwd * 0.5 * SPAN, 0.15 * S))


def dig_take(code, title, idx, kind):
    O = area(idx)

    def B2(x, y, z):
        return O + Vector((x, -z, y))
    g2 = dig_course(kind == "own")
    course_mesh(f"{code} ground", g2, O, 0, cut=HZ)
    sp = Spider(code + " R2", Gait(spread=1.0, knee_out=0.45, arc_out=0.05 * SPAN))
    Z_, X_ = Vector((0, 0, 1)), Vector((1, 0, 0))
    rim_x = H1 - HR - 6
    walk_pose = lambda f: (B2(5 + (rim_x - 5) * (f - 1) / (F_RIM - 1), 34, HZ), X_, Z_)
    animate(sp, (1, F_RIM), walk_pose)
    reset(sp)
    dirt_from = []

    def hook(sp_, L, f, foot, swinging):
        if L["k"] <= 1 and swinging and rng.random() < 0.55:
            dirt_from.append((f, foot.copy(), sp_.fw.copy(), sp_.up.copy()))
    if kind == "head":
        keys = [(F_RIM, B2(rim_x, 34, HZ), X_, Z_),
                (F_RIM + 5, B2(H1 - HR - 1, 33, HZ), Vector((1, 0, -0.7)), Vector((0.7, 0, 1))),     # claw the rim, nose drops
                (F_RIM + 10, B2(H1 - HR + 0.5, 25, HZ), -Z_, X_),                                   # pours in head first
                (F_RIM + 16, B2(H1 - HR + 0.5, TY + 2, HZ), -Z_, X_),
                (F_DUG, B2(H1 + 4, TY - TR, HZ), X_, Z_)]
        rest = lambda L, f: (Vector((L["rest"].x, L["rest"].y + 0.08 * SPAN, 0)) if f < F_RIM + 4 else tunnel_rest(L, f))
        animate(sp, (F_RIM, F_DUG), keyed_pose(keys), rest, period=4, lift=0.05 * SPAN, foot_hook=hook)
    elif kind == "cork":
        keys = [(F_RIM, B2(rim_x, 34, HZ), X_, Z_), (F_RIM + 4, B2(H1 - 4, 34, HZ), X_, Z_)]
        n = 10
        for j in range(n + 1):
            a = j / n * math.tau
            upv = Vector((math.cos(a), math.sin(a), 0))
            centre = B2(H1, 31 - (31 - TY - 1) * j / n, HZ)
            keys.append((F_RIM + 6 + j * 1.2, centre - upv * sp.body_h * 0.8, -Z_, upv))
        keys.append((F_DUG, B2(H1 + 4, TY - TR, HZ), X_, Z_))
        rest = lambda L, f: (Vector((L["rest"].x, L["rest"].y + 0.08 * SPAN, 0)) if f < F_RIM + 4 else tunnel_rest(L, f))
        animate(sp, (F_RIM, F_DUG), keyed_pose(keys), rest, period=4, lift=0.04 * SPAN, foot_hook=hook)
    else:   # digs its own hole: it sinks as the dirt goes
        F_D2 = F_DUG + 6
        keys = [(F_RIM, B2(H1 - 4, 34, HZ), X_, Z_),
                (F_RIM + 8, B2(H1 - 2, 30, HZ), Vector((1, 0, -0.5)), Vector((0.5, 0, 1))),
                (F_RIM + 16, B2(H1 - HR + 1.5, 24, HZ), -Z_, X_),
                (F_RIM + 22, B2(H1 - HR + 1.5, TY + 2, HZ), -Z_, X_),
                (F_D2, B2(H1 + 4, TY - TR, HZ), X_, Z_)]
        keys[0] = (F_RIM, B2(rim_x + 8, 34, HZ), X_, Z_)
        surf = lambda f: 34 - max(0, (f - F_RIM)) * (34 - TY) / (F_D2 - 6 - F_RIM)

        def own_hook(sp_, L, f, foot, swinging):
            hook(sp_, L, f, foot, swinging)
        def rest(L, f):
            return Vector((L["rest"].x, L["rest"].y + 0.08 * SPAN, 0)) if f < F_RIM + 10 else tunnel_rest(L, f)
        # walk the extra few blocks first
        animate(sp, (F_RIM, F_D2), keyed_pose(keys), rest, period=4, lift=0.04 * SPAN, foot_hook=own_hook)
        # the dirt plug: 2-block chunks filling the near half of the hole, each flies off as the dig passes it
        for cy in range(TY, 34, 2):
            for cx in range(H1 - HR, H1 + HR + 1, 2):
                for cz in range(HZ - HR, HZ + 1, 2):
                    if (cx - H1) ** 2 + (cz - HZ) ** 2 > HR ** 2:
                        continue
                    fgo = int(F_RIM + (34 - cy) / (34 - TY) * (F_D2 - 6 - F_RIM))
                    q = K.box(f"{code} plug", tuple(B2(cx + 0.5, cy + 1, cz)), (2, 2, 2), CM[1], None)
                    q.keyframe_insert("scale", frame=fgo)
                    q.keyframe_insert("location", frame=fgo)
                    v = Vector((rng.uniform(-6, 2), rng.uniform(-5, 5), rng.uniform(10, 20)))
                    for k in range(2, 13, 2):
                        tt = k / FPS
                        q.location = B2(cx + 0.5, cy + 1, cz) + v * tt + Vector((0, 0, -20 * tt * tt))
                        q.keyframe_insert("location", frame=fgo + k)
                    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=fgo + 13)
    reset(sp)
    t0 = F_DUG + (6 if kind == "own" else 0)
    tun_pose = lambda f: (B2(H1 + 4 + (H2 - HR - 2 - H1 - 4) * (f - t0) / (F_TEND - t0), TY - TR, HZ), X_, Z_)
    animate(sp, (t0, F_TEND), tun_pose, tunnel_rest, period=6, lift=0.03 * SPAN, sf=0.5)
    reset(sp)
    keys = [(F_TEND, B2(H2 - HR - 2, TY - TR, HZ), X_, Z_),
            (F_TEND + 5, B2(H2 + HR - 0.5, TY + 3, HZ), Z_, -X_),
            (F_TOP - 4, B2(H2 + HR - 0.5, 29, HZ), Z_, -X_),
            (F_TOP, B2(H2 + HR + 6, 34, HZ), X_, Z_)]
    rest_up = lambda L, f: tunnel_rest(L, f) if f < F_TOP - 3 else Vector((L["rest"].x, L["rest"].y + 0.08 * SPAN, 0))
    animate(sp, (F_TEND, F_TOP), keyed_pose(keys), rest_up, period=5, lift=0.06 * SPAN)
    reset(sp)
    animate(sp, (F_TOP, F_END), lambda f: (B2(H2 + HR + 6 + 14 * (f - F_TOP) / (F_END - F_TOP), 34, HZ), X_, Z_))
    # dirt thrown back by the scrabbling front legs, and the burst out of the far hole
    for f, foot, fw, up in dirt_from:
        for _ in range(2):
            v = -fw * rng.uniform(4, 10) + up * rng.uniform(6, 14) + Vector(tuple(rng.uniform(-3, 3, 3)))
            if kind == "cork":
                v += fw.cross(up) * rng.uniform(4, 9)
            dirt_cube(foot, v, f, 16)
    for j in range(30):
        c0 = B2(H2 + rng.uniform(-5, 5), 34, HZ + rng.uniform(-5, 2))
        dirt_cube(c0, Vector((rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(14, 26))), F_TOP - 6, 28, 1.0)
    check_legs(sp, code)
    n = REPORT[code]["bad"]
    cam = follow(K.camera(f"{code} cam", tuple(B2(72, 42, HZ + 82)), tuple(B2(75, 22, HZ)), 28), sp.root)
    label(cam, title, f"dig in: {(F_DUG - F_RIM + (6 if kind == 'own' else 0)) / FPS:.1f} s   legs touching: {n} of {REPORT[code]['frames']} frames")
    K.light(f"{code} key", tuple(B2(75, 120, HZ + 80)), 300000, (1, 0.95, 0.9), "AREA", 160)
    K.light(f"{code} tunnel glow", tuple(B2(75, TY, HZ - 2)), 6000, (1, 0.85, 0.6))
    take(code, title, cam, (1, F_END))


for code, title, kind in (("D1", "D1 head-first dig", "head"), ("D2", "D2 corkscrew dig", "cork"), ("D3", "D3 digs its own hole", "own")):
    if want(code):
        dig_take(code, title, ai, kind)
    ai += 1


# ------------------------------------------------------------------ note 3: strikes that land
PLAYER_BOXES = [((0, 0, 0.375), (0.25, 0.125, 0.375)), ((0, 0, 1.125), (0.25, 0.125, 0.375)), ((0, 0, 1.75), (0.25, 0.25, 0.25))]


def player_hit_dist(tip, ploc, tilt):
    R = Matrix.Rotation(tilt, 3, "Y")
    lp = R.inverted() @ (tip - ploc)
    return min(box_dist(lp, Vector(c), Vector(h)) for c, h in PLAYER_BOXES)


def strike_take(code, title, idx, kind):
    O = area(idx)

    def B3(x, y, z):
        return O + Vector((x, -z, y))
    g3 = np.zeros((140, 20, 80), bool); g3[:, :4, :] = True
    course_mesh(f"{code} floor", g3, O)
    sp = Spider(code + " R2", Gait(spread=1.0, knee_out=0.45))
    PX = 70
    F_END3 = 90
    # the player's pose per frame: (location, backward tilt); knocked back on each hit
    if kind == "stab":
        hits = [(34, "R")]
    elif kind == "pin":
        hits = [(30, "R")]
    else:
        hits = [(26, "L"), (38, "R")]

    def ppose(f):
        x, tilt, y = PX, 0.0, 4.0
        if kind == "stab":
            if f > 34:
                u = smooth((f - 34) / 8); x += 3.5 * u; tilt = 1.45 * smooth((f - 36) / 8)
        elif kind == "pin":
            if f > 30:
                tilt = 1.5 * smooth((f - 30) / 5); x += 0.8 * smooth((f - 30) / 5)
        else:
            if f > 26:
                x += 1.0 * smooth((f - 26) / 4); tilt = 0.25 * smooth((f - 26) / 4) * (1 - smooth((f - 32) / 5))
            if f > 38:
                x += 5.0 * smooth((f - 38) / 7); tilt = 1.45 * smooth((f - 39) / 8)
        return B3(x, y, 40), tilt

    def chest(f):
        loc, tilt = ppose(f)
        return loc + Matrix.Rotation(tilt, 3, "Y") @ Vector((0, 0, 1.05))

    lunge = {"stab": (20, 32, 4.0), "pin": (16, 28, 9.0), "jab": (18, 26, 3.0)}[kind]

    def body_pose(f, bx):
        a0, a1, dx = lunge
        x = bx + dx * smooth((f - a0) / (a1 - a0)) - (dx * 0.4 * smooth((f - 56) / 16) if f > 56 else 0)
        if kind == "stab":
            pitch = 26 * smooth((f - 18) / 12) - 18 * smooth((f - 34) / 20) - 8 * smooth((f - 56) / 12)
        elif kind == "pin":
            pitch = 22 * smooth((f - 14) / 10) - 30 * smooth((f - 25) / 6) + 8 * smooth((f - 50) / 14)
        else:
            pitch = 14 * smooth((f - 14) / 8) - 14 * smooth((f - 48) / 14)
        pr = math.radians(pitch)
        fw = Vector((math.cos(pr), 0, math.sin(pr)))
        up = Vector((-math.sin(pr), 0, math.cos(pr)))
        return B3(x, 4, 40) + Vector((0, 0, max(0, pitch) * 0.12)), fw, up

    # place the spider so the striking hip is 88% of a leg's reach from the target at the hit
    bx = 30.0
    L_hit = [L for L in sp.legs if L["k"] == 0 and L["side"] > 0][0]
    for _ in range(4):
        fh, side = hits[-1]
        p, fw, up = body_pose(fh, bx)
        sp.body(fh, p, fw, up)
        Lh = [L for L in sp.legs if L["k"] == 0 and L["side"] == (1 if side == "R" else -1)][0]
        H = sp.M @ Lh["hip"]
        bx += ((chest(fh) - H).length - 0.86 * (Lh["L1"] + Lh["L2"]))
    planted = {}
    contact = []
    for f in range(1, F_END3 + 1):
        p, fw, up = body_pose(f, bx)
        sp.body(f, p, fw, up)
        feet = []
        for L in sp.legs:
            if id(L) not in planted or (L["k"] >= 1 and (sp.M.inverted() @ planted[id(L)] - Vector((L["rest"].x, L["rest"].y, 0))).length > 0.3 * SPAN):
                rest = sp.M @ Vector((L["rest"].x, L["rest"].y + 0.05 * SPAN, 0))
                planted[id(L)] = cast_foot(sp, Vector((rest.x, rest.y, O.z + 4 + 0.0)) + up * 0)
            foot = planted[id(L)]
            if L["k"] == 0:
                sd = "R" if L["side"] > 0 else "L"
                mine = [fh for fh, s_ in hits if s_ == sd]
                raised = sp.M @ Vector((L["rest"].x * 0.55, L["rest"].y * 0.55, 0.5 * SPAN))
                if mine:
                    fh = mine[0]
                    wind = fh - 10
                    tip_in = chest(fh) + (chest(fh) - (sp.M @ L["hip"])).normalized() * 0.25   # 0.25 blocks into you
                    if f < wind:
                        foot = foot.lerp(raised, smooth((f - (wind - 12)) / 12))
                    elif f < fh - 3:
                        foot = raised
                    elif f <= fh:
                        foot = raised.lerp(tip_in, (f - (fh - 3)) / 3)          # the stab: 3 frames
                    elif f <= fh + 3:
                        foot = chest(f) + (chest(f) - (sp.M @ L["hip"])).normalized() * 0.25   # rides the hit
                    elif kind == "pin" and f < 62:
                        foot = chest(f) + Vector((0, 0, 0.1))                    # pinning you to the floor
                    else:
                        back = fh + 3 if kind != "pin" else 62
                        foot = (chest(back)).lerp(planted[id(L)], smooth((f - back) / 12))
                elif kind == "pin":   # the other spike stabs the floor beside you
                    side_pt = B3(PX + 0.5, 4.0, 40 - 2.2)
                    if f < 18:
                        foot = foot.lerp(raised, smooth((f - 6) / 12))
                    elif f <= 30:
                        foot = raised.lerp(side_pt, smooth((f - 27) / 3))
                    elif f < 62:
                        foot = side_pt
                    else:
                        foot = side_pt.lerp(planted[id(L)], smooth((f - 62) / 12))
                else:                 # the free front leg lifts, threatening
                    foot = foot.lerp(raised * 0.6 + foot * 0.4, smooth((f - 14) / 10) * (1 - smooth((f - 58) / 10)))
            feet.append(foot)
        locked = [i for i, L in enumerate(sp.legs) if L["k"] == 0]
        for L in sp.legs:
            L["kb"] = max(0.0, L.get("kb", 0.0) - 0.15); L["kf"] = L.get("kf", 0.0) * 0.85
        feet, _ = resolve(sp, feet, [L["k"] != 0 for L in sp.legs], locked=locked)
        for i, L in enumerate(sp.legs):
            if L["k"] != 0:
                planted[id(L)] = feet[i]
            F = sp.leg(f, L, feet[i])
            sd = "R" if L["side"] > 0 else "L"
            if L["k"] == 0 and (f, sd) in hits:
                loc, tilt = ppose(f)
                contact.append(round(player_hit_dist(F, loc, tilt), 2))
    pl = K.player(f"{code} player", tuple(B3(PX, 4, 40)))
    for f in range(1, F_END3 + 1):
        loc, tilt = ppose(f)
        pl.location = loc; pl.rotation_euler = (0, tilt, 0)
        pl.keyframe_insert("location", frame=f); pl.keyframe_insert("rotation_euler", frame=f)
    # web on the hit, stone chips off the spike
    web_m = K._m("silk")
    fh = hits[-1][0]
    for j in range(18):
        a = j / 18 * math.tau
        q = K.box(f"{code} web {j}", (math.cos(a) * 0.6, math.sin(a) * 0.6, 0.4 + (j % 5) * 0.35), (0.1, 1.5, 0.1), web_m, pl)
        q.rotation_euler = (rng.uniform(-1, 1), rng.uniform(-1, 1), a)
        q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=1); q.keyframe_insert("scale", frame=fh)
        q.scale = (1, 1, 1); q.keyframe_insert("scale", frame=fh + 3)
    for fh_, _ in hits:
        for j in range(10):
            dirt_cube(chest(fh_), Vector((rng.uniform(-8, 2), rng.uniform(-6, 6), rng.uniform(4, 12))), fh_, 18, 0.35, K._m("spike"))
    real = [c for c in contact if c is not None]
    REPORT[code + " contact"] = real
    print(f"CONTACT {code}: spike-tip distance to your body at each hit frame {real} (0 = touching)")
    check_legs(sp, code)
    cam = K.camera(f"{code} cam", tuple(B3(PX - 9, 13, 40 - 30)), tuple(B3(PX - 7, 5, 40)), 28)
    label(cam, title, f"spike hits you: {'yes' if real and max(real) <= 0.01 else 'NO'}   legs touching: {REPORT[code]['bad']} of {REPORT[code]['frames']} frames")
    K.light(f"{code} key", tuple(B3(PX - 20, 80, -20)), 180000, (1, 0.95, 0.9), "AREA", 120)
    take(code, title, cam, (1, F_END3))


for code, title, kind in (("S1", "S1 rear and stab", "stab"), ("S2", "S2 lunge pin", "pin"), ("S3", "S3 double jab", "jab")):
    if want(code):
        strike_take(code, title, ai, kind)
    ai += 1


# ------------------------------------------------------------------ C1b: the yellow construct stops short and shoots webs
def c1b_take(code, title, idx):
    O = area(idx)

    def B4(x, y, z):
        return O + Vector((x, -z, y))
    g4 = np.zeros((140, 20, 80), bool); g4[:, :4, :] = True
    course_mesh(f"{code} floor", g4, O)
    PX = 70
    span_c = 20.0
    start, stop = B4(PX - 45, 4, 40), B4(PX - 20, 4, 40)
    cs = K.construct_spider("C1b", f"{code} construct", tuple(start), span_c, -math.pi / 2)
    cs.rotation_mode = "XYZ"
    for f in range(1, 91):
        u = smooth((f - 1) / 18)
        loc = start.lerp(stop, u) + Vector((0, 0, abs(math.sin(f * 0.9)) * 0.3 * (1 - u)))   # a skitter, then stop
        rear = math.radians(14) * smooth((f - 18) / 6) * (1 - smooth((f - 64) / 10))
        recoil = sum(math.radians(5) * max(0, 1 - abs(f - fs) / 3) for fs in (26, 36, 46))
        cs.location = loc + Vector((0, 0, math.sin(rear) * 4))
        cs.rotation_euler = (rear - recoil, 0, -math.pi / 2)
        cs.keyframe_insert("location", frame=f); cs.keyframe_insert("rotation_euler", frame=f)
    web = K.mat("hard-light web", (1, 0.8, 0.25), 0.3, (1, 0.72, 0.12), 1.4, alpha=0.85)
    pl = K.player(f"{code} player", tuple(B4(PX, 4, 40)))
    s = span_c / 10
    for j, fs in enumerate((26, 36, 46)):
        mouth = stop + Vector((2.0 * s, 0, 2.2 * s + math.sin(math.radians(14)) * 4))
        tgt = B4(PX, 4 + 0.7 + j * 0.45, 40 + (j - 1) * 0.3)
        ob = K.box(f"{code} web shot {j}", tuple(mouth), (0.16, 1, 0.16), web, None)
        ob.rotation_mode = "QUATERNION"
        for f in range(fs - 1, fs + 30):
            u = min(1.0, max(0.0, (f - fs) / 4))
            end = mouth.lerp(tgt, u)
            v = end - mouth
            ob.location = (mouth + end) / 2
            ob.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(v.normalized() if v.length > 1e-3 else Vector((1, 0, 0)))
            fade = 1.0 if f < fs + 18 else max(0.0, 1 - (f - fs - 18) / 10)
            ob.scale = (0.16 * fade if f >= fs else 0, max(v.length, 0.01), 0.16 * fade if f >= fs else 0)
            for dp in ("location", "rotation_quaternion", "scale"):
                ob.keyframe_insert(dp, frame=f)
        for k in range(10):   # the web opening round you as each shot lands
            a = k / 10 * math.tau
            q = K.box(f"{code} wrap {j}-{k}", (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.5 + j * 0.45), (0.08, 1.3, 0.08), web, pl)
            q.rotation_euler = (0.3 * (k % 3 - 1), 0.6, a)
            q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=1); q.keyframe_insert("scale", frame=fs + 3)
            q.scale = (1, 1, 1); q.keyframe_insert("scale", frame=fs + 6)
    for f in range(1, 91):   # pushed back a little by each shot, then stuck
        x = PX + sum(0.4 * smooth((f - fs - 4) / 3) for fs in (26, 36, 46))
        pl.location = B4(x, 4, 40); pl.keyframe_insert("location", frame=f)
    gap = (B4(PX, 4, 40) - stop).length
    REPORT[code] = dict(range_blocks=round(gap - span_c / 2, 1))
    cam = K.camera(f"{code} cam", tuple(B4(PX - 13, 12, 40 - 36)), tuple(B4(PX - 12, 5, 40)), 28)
    label(cam, title, f"stops {gap - span_c / 2:.0f} blocks short (leg tips to you) and webs you from range")
    K.light(f"{code} key", tuple(B4(PX - 20, 80, -20)), 180000, (1, 0.95, 0.9), "AREA", 120)
    take(code, title, cam, (1, 90))


if want("C1b"):
    c1b_take("C1b", "C1b construct webs (range)", ai)
ai += 1

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
print("REPORT", REPORT)
with open(os.path.splitext(OUT)[0] + "_report.json", "w", encoding="utf-8") as fh_:
    import json
    json.dump(REPORT, fh_, indent=1)
if CHECK_ONLY:
    sys.exit(0)


def show_only(code):
    """The walk takes share one course: hide the other walk spiders, and every other take's label."""
    for c, _, _ in walk_takes:
        for o in bpy.data.objects:
            if o.name.startswith(c + " R2"):
                o.hide_render = c != code and code in ("W1", "W2", "W3")
                o.hide_viewport = o.hide_render
    for o in bpy.data.objects:
        if " label" in o.name and o.parent is not None:
            o.hide_render = not o.parent.name.startswith(code + " cam")
            o.hide_viewport = o.hide_render


sc.frame_start, sc.frame_end = 1, F_WALK
sc.camera = takes[0][2]
if takes and takes[0][0] in ("W1", "W2", "W3"):
    show_only(takes[0][0])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
MODEL_AT = {"W1": 135, "W2": 135, "W3": 135, "D1": 33, "D2": 36, "D3": 40, "S1": 35, "S2": 31, "S3": 38, "C1b": 38}
if "--stills" in argv:
    sdir = os.path.join(os.path.dirname(OUT), "renders_anim2", "stills")
    os.makedirs(sdir, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.cycles.samples = 24
    sc.render.image_settings.file_format = "PNG"
    for code, title, cam, (f0, f1) in takes:
        show_only(code)
        sc.camera = cam
        sc.frame_set(MODEL_AT.get(code, (f0 + f1) // 2))
        sc.render.filepath = os.path.join(sdir, code + ".png")
        bpy.ops.render.render(write_still=True)
        print("still", sc.render.filepath)
if VIDEO:
    rdir = os.path.join(os.path.dirname(OUT), "renders_anim2")
    os.makedirs(rdir, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.cycles.samples = 16
    sc.render.image_settings.media_type = "VIDEO"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"; sc.render.ffmpeg.constant_rate_factor = "MEDIUM"
    for code, title, cam, (f0, f1) in takes:
        show_only(code)
        sc.camera = cam; sc.frame_start, sc.frame_end = f0, f1
        sc.render.filepath = os.path.join(rdir, title.replace(" ", "_").replace("(", "").replace(")", "") + ".mp4")
        bpy.ops.render.render(animation=True)
        print("video", sc.render.filepath)
print("done", OUT)
