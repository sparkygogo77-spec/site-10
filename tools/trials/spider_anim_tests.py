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
GROUND_ON = "--no-ground" not in argv
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
            # wave: legs step 4-2-3-1 on each side, the two sides half a cycle apart (Cupiennius and tarantula
            # studies, docs/findings/2026-10-19-spider-leg-movement.md); tetrapod: L1 R2 L3 R4 against R1 L2 R3 L4
            off = (({3: 0.0, 1: 0.25, 2: 0.5, 0: 0.75}[k]) + (0.0 if sd < 0 else 0.5)) % 1.0 if gait.wave else (0.0 if (k + (0 if sd < 0 else 1)) % 2 == 0 else 0.5)
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
        bend = (self.up * (1 + L.get("kg", 0.0)) + outw * (self.gait.knee_out + L.get("kb", 0.0)) + self.fw * L.get("kf", 0.0)).normalized()
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
    if GROUND_ON:
        for i in range(8):
            if leg_in_ground(sp, chains[i], 0.5 - margin * 4):
                hits.setdefault(i, []).append("ground")
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


KNEE_GRID = [(kb, kf, kg) for kb in (0.0, 0.5, 1.0, 1.8, 3.0) for kf in (-1.0, -0.5, 0.0, 0.5, 1.0) for kg in (-0.6, 0.0, 0.6, 1.4, 2.4)]


def leg_penalty(sp, i, chains, gap=0.1):
    """How far leg i overlaps the other legs, the body and the ground on this frame, in blocks (0 = clear by gap)."""
    H, kn, F = chains[i]
    Ht = H + (kn - H).normalized() * min(1.2, (kn - H).length * 0.5)
    mine = ((Ht, kn, sp.r_fem), (kn, F, sp.r_tib))
    pen = 0.0
    for j, ch in enumerate(chains):
        if j == i:
            continue
        H2, kn2, F2 = ch
        Ht2 = H2 + (kn2 - H2).normalized() * min(1.2, (kn2 - H2).length * 0.5)
        for a in mine:
            for b in ((Ht2, kn2, sp.r_fem), (kn2, F2, sp.r_tib)):
                pen += max(0.0, a[2] + b[2] + gap - seg_dist(a[0], a[1], b[0], b[1]))
    for n_, (p, q, r) in enumerate(mine):
        boxes = sp.abd_boxes if n_ == 0 else sp.body_boxes
        for t in np.linspace(0.08 if n_ else 0.0, 1, 8):
            lp = sp.Mi @ (p + (q - p) * float(t))
            pen += max(0.0, max(r + gap - box_dist(lp, c, h) for c, h in boxes))
    if GROUND_ON:
        for (a, b, r, t0, t1) in ((H, kn, sp.r_fem, 0.15, 1.0), (kn, F, sp.r_tib, 0.0, GROUND_TIP)):
            for t in np.linspace(t0, t1, 9):
                pen += max(0.0, r * 0.5 + gap - ground_sd(a + (b - a) * float(t)))
    return pen


def resolve(sp, feet, swinging, iters=8, locked=()):
    """Clear every leg off the other legs, the body and the floor on this frame. For each leg still touching
    something: try a grid of knee directions (out, fore/aft, up) with the foot kept where it is, and keep the least
    overlap (a small cost for changing from last frame keeps knees from popping); only if no knee works does the foot
    move, to the best of 8 spots 1.5 blocks around it on real, reachable ground."""
    up = sp.up
    for it in range(iters):
        chains = [sp.solve(L, feet[i]) for i, L in enumerate(sp.legs)]
        if not frame_hits(sp, chains, margin=-0.1):
            return feet, True
        for i, L in enumerate(sp.legs):
            base = leg_penalty(sp, i, chains)
            if base <= 1e-6:
                continue
            prev = (L.get("kb", 0.0), L.get("kf", 0.0), L.get("kg", 0.0))
            best = (base + 0.0, prev)
            for kb, kf, kg in KNEE_GRID:
                L["kb"], L["kf"], L["kg"] = kb, kf, kg
                chains[i] = sp.solve(L, feet[i])
                cost = leg_penalty(sp, i, chains) + 0.02 * (abs(kb - prev[0]) + abs(kf - prev[1]) + abs(kg - prev[2]))
                if cost < best[0]:
                    best = (cost, (kb, kf, kg))
            L["kb"], L["kf"], L["kg"] = best[1]
            chains[i] = sp.solve(L, feet[i])
            if i not in locked and leg_penalty(sp, i, chains) > 1e-6 and (swinging[i] or it >= 1):   # locked feet stay on target
                Hh = sp.M @ L["hip"]
                lim = 0.95 * (L["L1"] + L["L2"])
                rt = sp.M.to_3x3() @ Vector((1, 0, 0)); fw = sp.M.to_3x3() @ Vector((0, 1, 0))
                cur = leg_penalty(sp, i, chains)
                for k in range(16):
                    a = k / 8 * math.tau
                    f2 = feet[i] + (rt * math.cos(a) + fw * math.sin(a)) * (1.5 if k < 8 else 3.0)
                    h = _ray(f2 + up * 6, -up, 14, front_only=True)
                    if h is None or (h - Hh).length > lim:
                        continue
                    old = feet[i]
                    feet[i] = h
                    chains[i] = sp.solve(L, h)
                    c2 = leg_penalty(sp, i, chains)
                    if c2 < cur:
                        cur = c2
                    else:
                        feet[i] = old
                        chains[i] = sp.solve(L, old)
    chains = [sp.solve(L, feet[i]) for i, L in enumerate(sp.legs)]
    return feet, not frame_hits(sp, chains)


def check_legs(sp, label, margin=0.05):
    """Per frame: every pair of legs (femur minus the 1.2 blocks inside the head, tibia+spike) as capsules of their
    own half-thickness, and every leg against the body boxes (femurs against the abdomen only: they start in the head).
    Returns (frames with a hit, total frames, smallest leg-to-leg clearance in blocks)."""
    bad, worst, nfr, gbad = [], 1e9, 0, []
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
        if any(leg_in_ground(sp, legs[id(L)]) for L in sp.legs):
            gbad.append(f)
            if os.environ.get("GDUMP") and f in (int(x) for x in os.environ["GDUMP"].split(",")) and label != "A1 before":
                for L in sp.legs:
                    H, kn, F = legs[id(L)]
                    worst_ = min((ground_sd(aa + (bb - aa) * float(t)) - rr, nm, round(float(t), 2)) for aa, bb, rr, nm in ((H, kn, sp.r_fem, "thigh"), (kn, F, sp.r_tib, "shin")) for t in np.linspace(0, 0.85, 9))
                    print(f"  gdump {label} f{f} leg{L['side']:+d}{L['k']} worst {worst_} hip_sd {ground_sd(H):.1f} knee_sd {ground_sd(kn):.1f} foot_sd {ground_sd(F):.1f} reach {(F-H).length:.1f}/{L['L1']+L['L2']:.1f}")
    if os.environ.get("LEGDUMP") and label != "A1 before":
        fd = int(os.environ["LEGDUMP"]); Mi = sp.recM[fd]
        for L in sp.legs:
            H, kn, F = sp.rec[fd][id(L)]
            print(f"  dump {label} f{fd} leg{L['side']:+d}{L['k']} hip {tuple(round(c,1) for c in Mi@H)} knee {tuple(round(c,1) for c in Mi@kn)} foot {tuple(round(c,1) for c in Mi@F)} reach {L['L1']+L['L2']:.1f} d {(F-H).length:.1f}")
        print("  abd boxes", [(tuple(round(c,1) for c in c_), tuple(round(c,1) for c in h)) for c_, h in sp.abd_boxes])
    REPORT[label] = dict(bad=len(bad), frames=nfr, clearance=round(worst, 2), first=bad[:6], ground=len(gbad), ground_first=gbad[:8])
    print(f"GROUNDCHECK {label}: {len(gbad)}/{nfr} frames with a leg through the floor, first {gbad[:8]}")
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


def ground_sd(p):
    """Signed distance from p to the nearest ground surface: positive in the open, negative inside rock."""
    best = None
    for t in COURSES:
        loc, nrm, idx, dd = t.find_nearest(p, 40.0)
        if loc is not None and (best is None or dd < best[0]):
            best = (dd, loc, nrm)
    if best is None:
        return 99.0
    dd, loc, nrm = best
    return dd if (p - loc).dot(nrm) >= 0 else -dd


GROUND_TIP = 0.75                                      # the spike end of the shin (its last quarter) may touch or dig into the ground


def leg_in_ground(sp, chain, frac=0.5):
    """True if any part of this leg (thigh, shin above the spike) sinks more than frac of its thickness into rock."""
    H, kn, F = chain
    for (a, b, r, t0, t1) in ((H, kn, sp.r_fem, 0.15, 1.0), (kn, F, sp.r_tib, 0.0, GROUND_TIP)):
        for t in np.linspace(t0, t1, 9):
            if ground_sd(a + (b - a) * float(t)) < r * frac:
                return True
    return False


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


def cast_foot(sp, P, wrap=True, reach=12.0, L=None):
    """Where a foot aimed at P lands. Round 1 cast only straight down the body's up (misses = feet in the air, which
    bunched the legs on the column). Now, keeping only spots a leg can really reach (in front of the spider's back
    plane, within reach): open ground casts down from high above P, then into a wall ahead, then round a column;
    holes and tunnels ("enclosed") cast from the body centre out toward P first."""
    up = sp.up
    if not wrap:
        h = _ray(P + up * reach, -up, reach * 2.5)
        return h if h is not None else P
    C = sp.centre()
    H = sp.M @ L["hip"] if L is not None else C
    lim = 0.97 * (L["L1"] + L["L2"]) if L is not None else 0.62 * SPAN

    def ok(h):
        return h is not None and (sp.Mi @ h).z <= (22.0 if wrap == "enclosed" else 2.5) and lim * 0.36 <= (h - H).length <= lim
    tries = []
    if wrap == "enclosed":
        tries.append(lambda: _ray(C, P - C, (P - C).length * 1.35))
    def down_on_ledge():
        """Straight down from above the aim; if that is a drop of more than 4 blocks below the body (over a hole's rim),
        pull the aim back toward the body until the foot stays on the ledge."""
        first = None
        for k in (1.0, 0.85, 0.7, 0.55, 0.4):
            Pk = H + (P - H) * k if L is not None else P
            h = _ray(Pk + up * (40 if up.z > -0.5 else 14), -up, 70, front_only=True)   # upside down: start below the ceiling, above the floor
            if h is None:
                continue
            if first is None or (sp.Mi @ h).z > (sp.Mi @ first).z:
                first = h                               # keep the shallowest drop seen
            if ((sp.Mi @ h).z >= -2.5 and (h - H).length <= lim) or wrap == "enclosed":
                return h
        return first
    tries.append(down_on_ledge)
    tries.append(lambda: _ray(C, P - C, (P - C).length * 1.35, front_only=True))
    tgt = sp.pos - up * 25
    tries.append(lambda: _ray(P + up * 2, tgt - P, (tgt - P).length, front_only=True))
    seen = []
    for t in tries:
        h = t()
        if ok(h):
            return h
        if h is not None:
            seen.append(h)
    # nothing ideal: the nearest real surface spot, never the aim point inside the rock (round 8 left feet in the slope)
    if seen:
        near = [h for h in seen if lim * 0.36 <= (h - H).length <= lim]
        return min(near or seen, key=lambda h: (h - P).length)
    return P


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def animate(sp, frames, pose, rest_fn=None, period=None, lift=None, arc=None, wrap=None, foot_hook=None, sf=None, enclosed=None, fix=True, tgt_fn=None, override=None, locked_fn=None):
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
        if g.wave and fix:
            BL = 19.0                                   # R2's body length in blocks
            ph_ = ((f - f0) % period) / period * math.tau
            rt_ = fw.cross(up).normalized()
            pos = pos + up * (0.05 * BL * 0.5 * (1 - math.cos(2 * ph_))) + rt_ * (0.065 * BL * math.sin(ph_))
            q_ = Quaternion(fw, math.radians(6.6) * math.sin(ph_)) @ Quaternion(up, math.radians(5.4) * math.sin(ph_ + 1.2))
            fw, up = q_ @ fw, q_ @ up
        sp.body(f, pos, fw, up)
        if fix and GROUND_ON:                       # body clearance: lift until every hip is 1.5 blocks clear of rock
            for _ in range(24):
                if min(ground_sd(sp.M @ L["hip"]) for L in sp.legs) >= 1.5:
                    break
                pos = pos + up * 0.5
                sp.body(f, pos, fw, up)
        # put each step's middle on the rest spot: lead the aim by half the distance the body covers while planted
        vel = sp.Mi.to_3x3() @ (pose(f + 1)[0] - pos)
        lead = Vector((vel.x, vel.y, 0)) * (period * (1 - sf) * 0.5)
        phase = ((f - f0) % period) / period
        feet, swinging = [], []
        for L in sp.legs:
            aim = (rest_fn(L, f) if rest_fn else Vector((L["rest"].x, L["rest"].y, 0.0))) + lead
            Pw, Hw = sp.M @ aim, sp.M @ L["hip"]
            rmax = 0.88 * (L["L1"] + L["L2"])
            if (Pw - Hw).length > rmax:                  # aim within reach, or the straight leg cuts through edges
                Pw = Hw + (Pw - Hw).normalized() * rmax
            tgt = cast_foot(sp, Pw, "enclosed" if (enclosed and enclosed(f)) else wrap, L=L)
            if tgt_fn:
                tgt = tgt_fn(L, f, tgt)
            if L["planted"] is None:
                L["planted"] = tgt
            ph = (phase - L["off"]) % 1.0
            dur = max(2, int(round(period * sf)))
            # catch-up step: a planted foot left far from its aim (the body turned or rolled) steps now, off-cycle
            if fix and RESOLVE and ph >= sf and L.get("fs") is None and L["swing"] is None:
                stretched = (L["planted"] - sp.M @ L["hip"]).length > 0.88 * (L["L1"] + L["L2"])
                if (sp.Mi @ L["planted"] - aim).length > 0.25 * SPAN or stretched:
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
                lift_k = lift * (1.5 if (L["k"] == 0 and g.wave) else 1.0)   # front legs lift high, feeling ahead
                foot = L["swing"].lerp(tgt, smooth(u)) + up * (math.sin(u * math.pi) * lift_k) + outw * (math.sin(u * math.pi) * arc)
                if foot_hook:
                    foot_hook(sp, L, f, foot, True)
                if forced and u >= 1:
                    L["planted"] = tgt; L["swing"] = None; L["fs"] = None; sw = False; foot = tgt
            else:
                if L["swing"] is not None:
                    L["planted"] = tgt
                    L["swing"] = None
                foot = L["planted"]
            if override is not None:                       # a strike drives this leg: it follows the script, not the gait
                o_ = override(L, f)
                if o_ is not None:
                    foot, sw = o_, False
                    L["planted"], L["swing"], L["fs"] = o_.copy(), None, None
            feet.append(foot); swinging.append(sw)
        if RESOLVE and fix:
            for L in sp.legs:
                L["kb"] = L.get("kb", 0.0) * 0.8           # knees relax back toward the plain pose over a few frames
                L["kf"] = L.get("kf", 0.0) * 0.8
                L["kg"] = L.get("kg", 0.0) * 0.8
            feet, ok = resolve(sp, feet, swinging, locked=locked_fn(f) if locked_fn else ())
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
def course_mesh(name, solid, loc, mat_idx=0, cut=None, pad=30):
    # 30 more blocks of the end slabs on both ends: round 8's spiders started so near an end that back feet hung off it
    solid = np.concatenate([np.repeat(solid[:1], pad, 0), solid, np.repeat(solid[-1:], pad, 0)], 0)
    loc = Vector(loc) - Vector((pad, 0, 0))
    s_ = solid.copy()
    if cut is not None:
        s_[:, :, cut + 1:] = False
    o = K.voxel_mesh(name, s_, lambda i, n, a, d: np.full(len(i), mat_idx), CM)
    o.location = loc
    mw = Matrix.Translation(Vector(loc))
    # feet and the floor check use the whole ground; only the picture is cut open (round 8 planted the near legs on
    # the cut face)
    src = o if cut is None else K.voxel_mesh(name + " full", solid, lambda i, n, a, d: np.zeros(len(i), int), CM[:1])
    COURSES.append(BVHTree.FromPolygons([mw @ v.co for v in src.data.vertices], [tuple(p.vertices) for p in src.data.polygons]))
    if src is not o:
        me = src.data; bpy.data.objects.remove(src); bpy.data.meshes.remove(me)
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
COLX, COLZ, COLR = 125, 45, 14         # round 8's column (climbing is on hold: round 9 walks the lair floor instead)
# round 9: lair floor after the slope: a 5-block ledge and boulders 2-5 high, the ground R2 actually crosses
LEDGE_X = 128
g |= (xs >= LEDGE_X) & (ys < TOP + 5)
_rb = np.random.default_rng(12)
for _k in range(16):
    bx_, bz_ = _rb.integers(84, 166), _rb.integers(6, 64)
    bw, bd, bh = _rb.integers(3, 8), _rb.integers(3, 8), _rb.integers(2, 6)
    base_ = TOP + (5 if bx_ >= LEDGE_X else 0)
    g |= (np.abs(xs - bx_) <= bw // 2) & (np.abs(zs - bz_) <= bd // 2) & (ys < base_ + bh)
HGT = np.where(g.any(1), Y - np.argmax(g[:, ::-1, :], axis=1), 0).astype(float)   # top of the ground per column


def ground_h(x, z, r=4):
    xi, zi = int(round(x)), int(round(z))
    return float(HGT[max(0, xi - r):xi + r + 1, max(0, zi - r):zi + r + 1].max())


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
            n = Vector((0, 0, 1)).lerp(n, min(1, u * 4) * (1 - (min(1, max(0, u - 0.8) * 5) if roll else 0))).normalized()
            return B1(x, min(yy, TOP), z0), Vector((1, 0, math.tan(math.radians(40)) * (1 - min(1, max(0, u - 0.8) * 5)))), n
        if roll and t >= 0.45:                      # round 9: over boulders and up the ledge
            u = (t - 0.45) / 0.55
            x = SLOPE1 - 6 + u * (170 - 12 - (SLOPE1 - 6))
            hx = (ground_h(x + 9, z0, 3) - ground_h(x - 9, z0, 3)) / 18
            hz = (ground_h(x, z0 + 9, 3) - ground_h(x, z0 - 9, 3)) / 18
            up = Vector((-hx * 0.6, hz * 0.6, 1)).normalized()
            return B1(x, ground_h(x, z0), z0), Vector((1, 0, hx * 0.6)), up
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
    REPORT["A1 before"] = dict(bad=194, ground=81, frames=200, note="round 1 gait, measured in round 8 on its own course")
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
        label(cam, title, f"legs through the floor: {REPORT[code]['ground']} of {nf} frames (round 1: 81)   legs touching each other: {n}")
        take(code, title, cam, (1, F_WALK))
        sp.objs = [o for o in bpy.data.objects if o.name.startswith(code + " R2")]
    ai += 1


# ------------------------------------------------------------------ note 2: quick animated digs
# Round 9 (J: "D2 and 3"): both rebuilt round a cone-shaped pit, room for a 36-block spider. Round 10 (J: "make sure
# the burrows are accessing part of the pipeline instead of making short new ones, the corkscrew ... the angle needs
# to be better slower and the spider needs a digging arm animation and to smoothly settle into the blocks on all sides
# and ceilings"): the tunnel runs the whole scene (a stretch of the orb-web network) and both pits break into it; the
# pit wall is gentler (42 degrees, 60 across at the top); D2 turns half a circle in 1.8 s while its front legs dig in
# strokes; in the tunnel every foot settles onto the walls and the ceiling, all round.
X2, Y2, Z2 = 170, 50, 80
H1, H2, HZ = 42, 120, 40
TY, TR = 18, 15.0                       # tunnel centre height and radius (30 wide: what R2 needs)
RT, RB, YB = 32.0, 15.0, 18             # pit radius at the top (y 34) and bottom (y YB)
xs2 = np.arange(X2)[:, None, None]; ys2 = np.arange(Y2)[None, :, None]; zs2 = np.arange(Z2)[None, None, :]


def pit_r(y):
    return RB + (RT - RB) * min(1.0, max(0.0, (y - YB) / (34 - YB)))


def dig_course():
    g2 = np.zeros((X2, Y2, Z2), bool)
    g2[:, :34, :] = True
    rr = RB + (RT - RB) * np.clip((ys2 - YB) / (34 - YB), 0, 1)
    for hx in (H1, H2):
        g2 &= ~((((xs2 - hx) ** 2 + (zs2 - HZ) ** 2) <= rr ** 2) & (ys2 >= YB))
    g2 &= ~((((ys2 - TY) ** 2 + (zs2 - HZ) ** 2) <= TR ** 2) & (xs2 >= 0))     # the network tunnel, end to end
    return g2


def tunnel_rest(L, f):
    """Settled in the tunnel: feet spread round the whole bore. Front legs reach ahead high on the walls, the second
    pair up onto the ceiling, the third out to the sides, the back legs low behind (round 9 kept every foot low)."""
    k, s = L["k"], L["side"]
    fwd = (0.75, 0.3, -0.25, -0.6)[k]
    lat = (0.62, 0.42, 0.9, 0.8)[k]
    hi = (1.6, 3.6, 0.9, 0.4)[k]
    return Vector((s * 0.42 * SPAN * lat, fwd * 0.5 * SPAN, hi * S))


def dig_take(code, title, idx, kind):
    O = area(idx)

    def B2(x, y, z):
        return O + Vector((x, -z, y))

    def G(v):
        return Vector((v[0], -v[2], v[1]))

    def wall(hx, a, y):
        r = pit_r(y)
        p = B2(hx + math.cos(a) * r, y, HZ + math.sin(a) * r)
        n = G((-math.cos(a), (RT - RB) / (34 - YB), -math.sin(a))).normalized()
        return p, n
    g2 = dig_course()
    course_mesh(f"{code} ground", g2, O, 0, cut=HZ)
    sp = Spider(code + " R2", Gait(spread=1.0, knee_out=0.45, arc_out=0.07 * SPAN, wave=True, period=16, lift=0.09))
    Z_, X_ = Vector((0, 0, 1)), Vector((1, 0, 0))
    rest0 = lambda L, f: Vector((L["rest"].x, L["rest"].y, 0))
    dirt_from = []

    def hook(sp_, L, f, foot, swinging):
        if L["k"] <= 1 and swinging and rng.random() < 0.55:
            dirt_from.append((f, foot.copy(), sp_.fw.copy(), sp_.up.copy()))
    F_RIM = 20
    if kind == "cork":
        F_DUG = 64                                            # 1.8 s down the pit (round 9: 1.0 s)
        rim_x = H1 - RT - 12
        animate(sp, (1, F_RIM), lambda f: (B2(rim_x - 14 + 14 * (f - 1) / (F_RIM - 1), 34, HZ), X_, Z_))
        reset(sp)
        keys = [(F_RIM, B2(rim_x, 34, HZ), X_, Z_)]
        a0, turns = math.pi - 0.3, 0.55
        for f in range(F_RIM + 4, F_DUG - 7, 2):              # half a turn down the gentler wall
            u = (f - F_RIM - 4) / (F_DUG - 9 - F_RIM - 4)
            a = a0 + u * turns * math.tau
            y = 32.5 - u * (32.5 - YB - 1)
            p, n = wall(H1, a, y)
            tang = G((-math.sin(a), -(32.5 - YB - 1) / (turns * math.tau * pit_r(y)), math.cos(a)))
            keys.append((f, p, tang, n))
        keys.append((F_DUG, B2(H1 + 6, TY - TR, HZ), X_, Z_))

        def dig_strokes(L, f):
            """The digging legs: the front pair rake the wall ahead in turns, 8-frame strokes: reach, bite, pull."""
            if L["k"] != 0 or not (F_RIM + 4 <= f <= F_DUG - 6):
                return None
            ph = ((f - F_RIM - 4) / 8.0 + (0.0 if L["side"] < 0 else 0.5)) % 1.0
            s = L["side"]
            reach_ = sp.M @ Vector((s * 4.5, 15.0, -2.5))
            bite = cast_foot(sp, reach_, "enclosed", L=L)
            pull = sp.M @ Vector((s * 6.5, 6.0, 3.0))
            if ph < 0.35:
                return pull.lerp(bite, smooth(ph / 0.35))
            if ph < 0.55:
                return bite
            if ph < 0.6 and rng.random() < 0.9:
                for _ in range(3):
                    dirt_from.append((f, bite.copy(), sp.fw.copy(), sp.up.copy()))
            return bite.lerp(pull, smooth((ph - 0.55) / 0.45))

        def locked_dig(f):
            return {i for i, L in enumerate(sp.legs) if dig_strokes(L, f) is not None}
        settle = lambda L, f: rest0(L, f) if f < F_DUG - 6 else tunnel_rest(L, f)
        animate(sp, (F_RIM, F_DUG + 10), keyed_pose(keys + [(F_DUG + 10, B2(H1 + 14, TY - TR, HZ), X_, Z_)]), settle,
                period=12, lift=0.04 * SPAN, foot_hook=hook, enclosed=lambda f: f >= F_RIM + 5,
                override=dig_strokes, locked_fn=locked_dig)
        dig_s = (F_DUG - F_RIM) / FPS
        t0 = F_DUG + 10
    else:   # digs its own pit, straight down into the network tunnel below
        F_DUG = 50
        animate(sp, (1, F_RIM), lambda f: (B2(H1 - 22 + 16 * (f - 1) / (F_RIM - 1), 34, HZ), X_, Z_))
        reset(sp)
        depth_at = lambda f: 34.0 - (34.0 - (TY - TR)) * smooth((f - F_RIM) / (F_DUG - F_RIM))

        def own_pose(f):
            y = depth_at(f)
            u = (f - F_RIM) / (F_DUG - F_RIM)
            pitch = math.radians(24) * math.sin(math.pi * min(1, u * 1.2))
            fw = Vector((math.cos(pitch), 0, -math.sin(pitch)))
            up = Vector((math.sin(pitch), 0, math.cos(pitch)))
            return B2(H1 - 6 + 8 * min(1, u), y, HZ), fw, up

        def on_dirt(L, f, tgt):
            floor_ = O.z + depth_at(f)
            gx, gz = tgt.x - O.x, -(tgt.y - O.y)
            if (gx - H1) ** 2 + (gz - HZ) ** 2 <= pit_r(tgt.z - O.z) ** 2 and tgt.z < floor_:
                tgt = tgt.copy(); tgt.z = floor_
            return tgt
        settle = lambda L, f: rest0(L, f) if f < F_DUG else tunnel_rest(L, f)
        animate(sp, (F_RIM, F_DUG + 10), lambda f: own_pose(f) if f <= F_DUG else (B2(H1 + 2 + 12 * (f - F_DUG) / 10, TY - TR, HZ), X_, Z_),
                settle, period=12, lift=0.04 * SPAN, foot_hook=hook, enclosed=lambda f: depth_at(f) < 30, tgt_fn=on_dirt)
        for cy in range(YB - 1, 34, 3):
            r = pit_r(cy + 1.5)
            for cx in range(int(H1 - r), int(H1 + r) + 1, 3):
                for cz in range(int(HZ - r), HZ + 1, 3):
                    if (cx + 1.5 - H1) ** 2 + (cz + 1.5 - HZ) ** 2 > r ** 2:
                        continue
                    fgo = next((f for f in range(F_RIM, F_DUG + 1) if depth_at(f) < cy + 1.5), F_DUG)
                    c0 = B2(cx + 1.5, cy + 1.5, cz + 1.5)
                    q = K.box(f"{code} plug", tuple(c0), (3, 3, 3), CM[1], None)
                    q.keyframe_insert("scale", frame=fgo); q.keyframe_insert("location", frame=fgo)
                    v = Vector((rng.uniform(-7, 3), rng.uniform(-6, 6), rng.uniform(12, 22)))
                    for k in range(2, 15, 2):
                        tt = k / FPS
                        q.location = c0 + v * tt + Vector((0, 0, -20 * tt * tt))
                        q.keyframe_insert("location", frame=fgo + k)
                    q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=fgo + 15)
        dig_s = (F_DUG - F_RIM) / FPS
        t0 = F_DUG + 10
    F_TEND = t0 + 36
    F_TOP = F_TEND + 18
    F_END = F_TOP + 26
    x_t0 = H1 + 14
    tun_pose = lambda f: (B2(x_t0 + (H2 - 4 - x_t0) * (f - t0) / (F_TEND - t0), TY - TR, HZ), X_, Z_)
    animate(sp, (t0, F_TEND), tun_pose, tunnel_rest, period=12, lift=0.03 * SPAN, enclosed=lambda f: True)
    reset(sp)
    keys = [(F_TEND, B2(H2 - 4, TY - TR, HZ), X_, Z_)]
    for f in range(F_TEND + 4, F_TOP - 2, 2):
        u = (f - F_TEND - 4) / max(1, (F_TOP - 4 - F_TEND - 4))
        y = YB + 1 + u * (32 - YB - 1)
        p, n = wall(H2, 0.0, y)
        keys.append((f, p, G(((RT - RB) / (34 - YB), 1, 0)).normalized(), n))
    keys.append((F_TOP, B2(H2 + RT + 5, 34, HZ), X_, Z_))
    animate(sp, (F_TEND, F_TOP), keyed_pose(keys), rest0, period=10, lift=0.05 * SPAN, enclosed=lambda f: f < F_TOP - 2)
    reset(sp)
    animate(sp, (F_TOP, F_END), lambda f: (B2(H2 + RT + 5 + 12 * (f - F_TOP) / (F_END - F_TOP), 34, HZ), X_, Z_))
    for f, foot, fw, up in dirt_from:
        for _ in range(2):
            v = -fw * rng.uniform(4, 10) + up * rng.uniform(6, 14) + Vector(tuple(rng.uniform(-3, 3, 3)))
            if kind == "cork":
                v += fw.cross(up) * rng.uniform(3, 7)
            dirt_cube(foot, v, f, 16)
    for j in range(30):
        c0 = B2(H2 + RT * 0.6 + rng.uniform(-4, 4), 34, HZ + rng.uniform(-8, 2))
        dirt_cube(c0, Vector((rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(14, 26))), F_TOP - 6, 28, 1.0)
    check_legs(sp, code)
    r_ = REPORT[code]
    cam = follow(K.camera(f"{code} cam", tuple(B2(80, 46, HZ + 100)), tuple(B2(80, 22, HZ)), 28), sp.root)
    label(cam, title, f"dig in: {dig_s:.1f} s   legs through the floor: {r_['ground']} of {r_['frames']} frames   touching each other: {r_['bad']}")
    K.light(f"{code} key", tuple(B2(80, 120, HZ + 80)), 300000, (1, 0.95, 0.9), "AREA", 160)
    K.light(f"{code} tunnel glow", tuple(B2(80, TY, HZ - 2)), 6000, (1, 0.85, 0.6))
    take(code, title, cam, (1, F_END))


for code, title, kind in (("D2", "D2 corkscrew dig", "cork"), ("D3", "D3 digs its own pit", "own")):
    if want(code):
        dig_take(code, title, ai, kind)
    ai += 1


# ------------------------------------------------------------------ P1: slow patrol in a network tunnel
def patrol_take(code, title, idx):
    """J: "while im flying or in the tunnels (it needs to be able to patrol it slowly)". W3's wave gait at walking
    pace along a 24-wide web tunnel, feet settled all round the bore, ceiling included."""
    O = area(idx)

    def B2(x, y, z):
        return O + Vector((x, -z, y))
    PR = 15.0                                                       # 30 wide: R2's patrol tunnels (24 was too tight)
    PY = 3 + PR
    g2 = np.zeros((X2, Y2, Z2), bool)
    g2[:, :42, :] = True
    g2 &= ~((((ys2 - PY) ** 2 + (zs2 - HZ) ** 2) <= PR ** 2) & (xs2 >= 0))
    course_mesh(f"{code} rock", g2, O, 0, cut=HZ)
    sp = Spider(code + " R2", Gait(spread=1.0, knee_out=0.45, arc_out=0.07 * SPAN, wave=True, period=22, lift=0.07))
    X_, Z_ = Vector((1, 0, 0)), Vector((0, 0, 1))
    F_P = 168                                                       # 7 s for 34 blocks: about 5 blocks a second
    sway = lambda f: 1.2 * math.sin(f / F_P * math.tau * 1.5)       # it drifts side to side, sensing
    animate(sp, (1, F_P), lambda f: (B2(50 + 34 * f / F_P, PY - PR, HZ + sway(f)),
                                     Vector((1, -0.08 * math.cos(f / F_P * math.tau * 1.5), 0)), Z_),
            tunnel_rest, period=22, lift=0.025 * SPAN, enclosed=lambda f: True)
    check_legs(sp, code)
    r_ = REPORT[code]
    cam = follow(K.camera(f"{code} cam", tuple(B2(70, 30, HZ + 70)), tuple(B2(70, 16, HZ)), 26), sp.root)
    label(cam, title, f"5 blocks a second, feet on walls and ceiling   through the floor: {r_['ground']}   touching each other: {r_['bad']}")
    K.light(f"{code} key", tuple(B2(70, 60, HZ + 60)), 200000, (1, 0.95, 0.9), "AREA", 120)
    K.light(f"{code} tunnel glow", tuple(B2(70, TY, HZ - 2)), 8000, (1, 0.85, 0.6))
    take(code, title, cam, (1, F_P))


if want("P1"):
    patrol_take("P1", "P1 tunnel patrol", ai)
ai += 1


# ------------------------------------------------------------------ C1: web shot, zip up, upside-down patrol
def ceiling_take(code, title, idx):
    """J: "if im far or very close or on the ceiling I think it should shoot slow projectile spreading web that
    captures me on the ceiling and it zips up and patrols upside down with the same leg rules all the time".
    You hover 26 blocks up; R2 tips its abdomen up and fires a slow web ball from its spinnerets that opens into a
    net, sticks you to the ceiling, then it fires a dragline, climbs it hand over hand, flips onto the ceiling and
    walks to you upside down with the same wave gait and leg rules."""
    O = area(idx)

    def B5(x, y, z):
        return O + Vector((x, -z, y))
    CEIL = 44
    g5 = np.zeros((170, 52, 80), bool)
    g5[:, :4, :] = True
    g5[:, CEIL:50, :] = True
    course_mesh(f"{code} cave", g5, O, 0, cut=46)
    sp = Spider(code + " R2", Gait(spread=1.0, knee_out=0.45, arc_out=0.07 * SPAN, wave=True, period=16, lift=0.09))
    X_, Z_ = Vector((1, 0, 0)), Vector((0, 0, 1))
    PXc, PZc = 96, 40
    F_IN, F_TIP, F_FIRE, F_HIT, F_LINE, F_TOPC, F_FLIP, F_ENDC = 24, 34, 36, 66, 72, 102, 116, 216
    tip_ang = lambda f: math.radians(-22) * smooth((f - F_IN) / (F_TIP - F_IN)) * (1 - smooth((f - F_HIT) / 6))
    ground_pose = lambda f: (B5(30 + 14 * min(1, f / F_IN), 4, PZc),
                             Vector((math.cos(tip_ang(f)), 0, math.sin(tip_ang(f)))),
                             Vector((-math.sin(tip_ang(f)), 0, math.cos(tip_ang(f)))))
    animate(sp, (1, F_LINE), ground_pose, period=16)
    reset(sp)
    # the climb: body upright on the thread, head to the ceiling; then it flips onto the ceiling
    x_line = 44 + 2
    keys = [(F_LINE, B5(44, 4, PZc), X_, Z_), (F_LINE + 6, B5(x_line, 9, PZc), Z_, -X_)]
    keys += [(F_TOPC - 4, B5(x_line, CEIL - 12, PZc), Z_, -X_),
             (F_TOPC + 6, B5(x_line + 3, CEIL - 6, PZc), Vector((1, 0, 1)).normalized(), Vector((-1, 0, -1)).normalized()),   # halfway over
             (F_FLIP, B5(x_line + 8, CEIL, PZc), X_, -Z_)]
    climb = keyed_pose(keys)
    thread_pt = lambda y: B5(x_line + 1.5, y, PZc)

    def on_thread(L, f):
        """Hand over hand: the front two pairs grab the dragline above in turns, the back pairs pull below."""
        if not (F_LINE + 6 <= f <= F_TOPC - 2):
            return None
        p, fw, up = climb(f)
        by = p.z - O.z
        ph = ((f - F_LINE) / 6.0 + (0.5 if L["side"] > 0 else 0.0) + 0.25 * L["k"]) % 1.0
        lo, hi_ = ((7.5, 12.5), (2.5, 6.0), (-5.0, -1.5), (-11.5, -7.5))[L["k"]]   # each pair keeps its own stretch of thread
        off = lo + (hi_ - lo) * 0.5 * (1 + math.sin(ph * math.tau))
        y_ = min(CEIL - 1.5, max(5.5, by + off))                      # never below the floor or into the ceiling
        return thread_pt(y_) + Vector((0, -L["side"] * (0.9 + 0.6 * (L["k"] % 2)), 0))
    animate(sp, (F_LINE, F_FLIP), climb, rest_fn=lambda L, f: Vector((L["rest"].x, L["rest"].y, 0)), period=12,
            override=on_thread, locked_fn=lambda f: set(range(8)) if F_LINE + 6 <= f <= F_TOPC - 2 else set())
    reset(sp)
    walk_ceiling = lambda f: (B5(x_line + 6 + (PXc - 20 - x_line - 6) * smooth((f - F_FLIP) / (F_ENDC - 20 - F_FLIP)), CEIL, PZc), X_, -Z_)
    animate(sp, (F_FLIP, F_ENDC), walk_ceiling, period=16)
    # you: hovering, then the net carries you up and sticks you to the ceiling
    pl = K.player(f"{code} player", tuple(B5(PXc, 26, PZc)))
    for f in range(1, F_ENDC + 1):
        y = 26 + 0.5 * math.sin(f * 0.15) if f < F_HIT else 26 + (CEIL - 2.0 - 26) * smooth((f - F_HIT) / 8)
        pl.location = B5(PXc, y, PZc); pl.keyframe_insert("location", frame=f)
    silk = K._m("silk")
    spin = lambda f: sp.rec[f][id(sp.legs[3])][0] if False else None
    src = B5(30 + 14 - 13.5, 4 + 9.5, PZc)                        # the spinnerets, abdomen tipped up
    tgt = B5(PXc, 27, PZc)
    ball = K.box(f"{code} web ball", tuple(src), (1, 1, 1), silk, None)
    w = ball.modifiers.new("net", "WIREFRAME"); w.thickness = 0.06; w.use_replace = True
    sub = ball.modifiers.new("round", "SUBSURF"); sub.levels = 2; ball.modifiers.move(1, 0)
    for f in range(1, F_HIT + 12):
        u = min(1.0, max(0.0, (f - F_FIRE) / (F_HIT - F_FIRE)))
        p = src.lerp(tgt, u) + Vector((0, 0, 8 * math.sin(u * math.pi)))    # a slow lob
        r = 0.0 if f < F_FIRE else 1.0 + 5.0 * u                          # spreading as it flies
        if f > F_HIT:
            p = B5(PXc, CEIL - 0.6, PZc); r = 6.0
        ball.location = p
        ball.scale = (r, r, r if f <= F_HIT else 0.3)
        ball.keyframe_insert("location", frame=f); ball.keyframe_insert("scale", frame=f)
    for j in range(14):                                              # the net, glued flat to the ceiling round you
        a = j / 14 * math.tau
        q = K.box(f"{code} net {j}", tuple(B5(PXc + math.cos(a) * 3.5, CEIL - 0.3, PZc + math.sin(a) * 3.5)), (0.12, 7.5, 0.12), silk, None)
        q.rotation_euler = (0, 0, a + 1.4)
        q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=1); q.keyframe_insert("scale", frame=F_HIT + 4)
        q.scale = (1, 1, 1); q.keyframe_insert("scale", frame=F_HIT + 8)
    line = K.box(f"{code} dragline", tuple(B5(x_line + 1.5, (4 + CEIL) / 2, PZc)), (0.1, 1, 0.1), silk, None)
    line.rotation_mode = "QUATERNION"
    for f in range(1, F_ENDC + 1):                                  # the dragline shoots up, then stays
        u = min(1.0, max(0.0, (f - (F_LINE - 4)) / 4))
        top_y = 9 + (CEIL - 9) * u
        line.location = B5(x_line + 1.5, (9 + top_y) / 2, PZc)
        line.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(Vector((0, 0, 1)))
        line.scale = (0.1 if u > 0 else 0, max(0.01, top_y - 9), 0.1 if u > 0 else 0)
        for dp in ("location", "rotation_quaternion", "scale"):
            line.keyframe_insert(dp, frame=f)
    check_legs(sp, code)
    r_ = REPORT[code]
    cam = K.camera(f"{code} cam", tuple(B5(66, 24, PZc - 92)), tuple(B5(66, 24, PZc)), 24)
    label(cam, title, f"web shot, zip up, upside-down patrol   through the floor or ceiling: {r_['ground']}   touching each other: {r_['bad']}")
    K.light(f"{code} key", tuple(B5(66, 24, PZc - 70)), 260000, (1, 0.95, 0.9), "AREA", 120)
    K.light(f"{code} fill", tuple(B5(66, 10, PZc - 10)), 30000, (0.9, 0.9, 1), "AREA", 60)
    take(code, title, cam, (1, F_ENDC))


if want("C1"):
    ceiling_take("C1", "C1 web shot and ceiling patrol", ai)
ai += 1


# ------------------------------------------------------------------ note 3: strikes that land
PLAYER_BOXES = [((0, 0, 0.375), (0.25, 0.125, 0.375)), ((0, 0, 1.125), (0.25, 0.125, 0.375)), ((0, 0, 1.75), (0.25, 0.25, 0.25))]


def player_hit_dist(tip, ploc, tilt):
    R = Matrix.Rotation(tilt, 3, "Y")
    lp = R.inverted() @ (tip - ploc)
    return min(box_dist(lp, Vector(c), Vector(h)) for c, h in PLAYER_BOXES)


PART_Z = {"legs": 0.5, "chest": 1.05, "head": 1.72}


def ease_keys(keys, f):
    """keys: [(frame, value tuple)]; smooth between them, held at the ends."""
    if f <= keys[0][0]:
        return keys[0][1]
    if f >= keys[-1][0]:
        return keys[-1][1]
    i = max(j for j in range(len(keys) - 1) if keys[j][0] <= f)
    u = smooth((f - keys[i][0]) / (keys[i + 1][0] - keys[i][0]))
    return tuple(a + (b - a) * u for a, b in zip(keys[i][1], keys[i + 1][1]))


# Round 9 (J: "Find a way to utilize all 3, more motion and points on each"): every strike stays in R2's moveset, each
# with more body motion (steps in, strafes, sways, turns to face you) and more contact points; S4 chains them.
#   body:   (frame, forward, sideways, pitch degrees, yaw degrees)    player: (frame, pushed back, tilt, sideways)
#   hits:   (frame, "L"/"R", part, kind) kind "stab" rides the hit 3 frames, "pin" holds until the next key, "drag"
#           slides down from the last hit to this part in 4 frames
STRIKES = {
    "S1": dict(title="S1 rear, stab and rip", end=96,
               body=[(1, -6, 0, 0, 0), (16, 0, 0, 6, 0), (28, 3, 0, 32, -8), (34, 4.5, 0, 34, -10), (44, 4.5, 0, 26, -6),
                     (60, 2, 0, 8, 0), (80, 0, 0, 0, 0)],
               player=[(1, 0, 0, 0), (34, 0, 0, 0), (38, 0.6, 0.15, 0), (44, 1.2, 0.35, 0), (48, 4.0, 1.45, 0)],
               hits=[(34, "R", "chest", "stab"), (42, "R", "legs", "drag")], web=44),
    "S2": dict(title="S2 strafe, lunge and pin", end=104,
               body=[(1, -8, -6, 0, 18), (14, -6, 5, 4, -16), (22, -6, 6, 20, -12), (30, 4, 0, -6, 0), (52, 4, 0, -10, 6),
                     (66, 3, 0, 4, 0), (86, -2, 0, 0, 0)],
               player=[(1, 0, 0, 0), (30, 0, 0, 0), (35, 0.8, 1.5, 0), (90, 0.8, 1.5, 0)],
               hits=[(30, "R", "chest", "pin"), (58, "R", "legs", "stab")], ground_stab=(30, "L", 50), web=31, pin_until=48),
    "S3": dict(title="S3 jab, jab, scissor", end=96,
               body=[(1, -4, 0, 0, 0), (16, 0, 0, 10, 8), (24, 1.5, 0, 14, 14), (34, 3, 0, 14, -14), (44, 4, 0, 18, 0),
                     (52, 4.5, 0, 22, 0), (70, 1, 0, 4, 0), (86, 0, 0, 0, 0)],
               player=[(1, 0, 0, 0), (24, 0, 0, 0), (28, 0.9, 0.2, -0.3), (34, 1.0, 0.05, 0), (38, 1.8, 0.25, 0.3), (48, 2.2, 0.1, 0),
                       (52, 2.2, 0.1, 0), (60, 7.5, 1.45, 0)],
               hits=[(24, "L", "chest", "stab"), (34, "R", "head", "stab"), (50, "L", "chest", "stab"), (51, "R", "legs", "stab")], web=52),
    "S4": dict(title="S4 the moveset chained", end=170,
               body=[(1, -10, 0, 0, 0), (14, -6, 0, 10, 10), (22, -4.5, 0, 14, 14), (32, -3, 0, 14, -14), (46, -10, -6, 2, 20),
                     (58, -10, 6, 18, -14), (68, 1, 0, -6, 0), (88, 1, 0, -6, 0), (100, 0, 0, 20, -6), (112, 3, 0, 34, -10),
                     (126, 2, 0, 20, -4), (148, -2, 0, 0, 0)],
               player=[(1, -3, 0, 0), (22, -3, 0, 0), (26, -2.2, 0.2, -0.3), (32, -2.0, 0.05, 0), (36, -1.0, 0.25, 0.3), (46, 0, 0, 0),
                       (68, 0, 0, 0), (73, 0.8, 1.5, 0), (90, 0.8, 1.5, 0), (98, 0.8, 0.6, 0), (106, 1.2, 0.1, 0), (112, 1.2, 0.1, 0),
                       (116, 1.8, 0.4, 0), (122, 5.0, 1.45, 0)],
               hits=[(22, "L", "chest", "stab"), (32, "R", "head", "stab"), (68, "R", "chest", "pin"), (112, "R", "chest", "stab"),
                     (118, "R", "legs", "drag")], ground_stab=(68, "L", 88), web=118, pin_until=88),
}


def strike_take(code, idx):
    cfg = STRIKES[code]
    title, F_END3 = cfg["title"], cfg["end"]
    O = area(idx)

    def B3(x, y, z):
        return O + Vector((x, -z, y))
    g3 = np.zeros((150, 20, 80), bool); g3[:, :4, :] = True
    course_mesh(f"{code} floor", g3, O)
    sp = Spider(code + " R2", Gait(spread=1.0, knee_out=0.45, arc_out=0.05 * SPAN, period=12))
    PX = 80

    def ppose(f):
        dx, tilt, side = ease_keys([(k[0], k[1:]) for k in cfg["player"]], f)
        return B3(PX + dx, 4, 40 + side), tilt

    def part(f, name):
        loc, tilt = ppose(f)
        return loc + Matrix.Rotation(tilt, 3, "Y") @ Vector((0, 0, PART_Z[name]))

    def body_pose(f, bx):
        fwd, side, pitch, yaw = ease_keys([(k[0], k[1:]) for k in cfg["body"]], f)
        pr, yr = math.radians(pitch), math.radians(yaw)
        fw = Vector((math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), math.sin(pr)))
        right = Vector((math.sin(yr), -math.cos(yr), 0))
        up = right.cross(fw).normalized()
        return B3(bx + fwd, 4, 40 - side) + Vector((0, 0, max(0, pitch) * 0.12)), fw, up

    legs_by_side = {"R": [L for L in sp.legs if L["k"] == 0 and L["side"] > 0][0],
                    "L": [L for L in sp.legs if L["k"] == 0 and L["side"] < 0][0]}
    # place the spider so every hit is within 88% of a leg's reach
    bx = PX - 24.0
    for _ in range(6):
        worst = -1e9
        for fh, sd, nm, kind in cfg["hits"]:
            p, fw, up = body_pose(fh, bx)
            sp.body(fh, p, fw, up)
            L = legs_by_side[sd]
            worst = max(worst, (part(fh, nm) - sp.M @ L["hip"]).length - 0.86 * (L["L1"] + L["L2"]))
        bx += worst
    contact = []
    override, locked = strike_driver(sp, cfg["hits"], part, cfg.get("ground_stab"), cfg.get("pin_until"), ppose)
    animate(sp, (1, F_END3), lambda f: body_pose(f, bx), period=12, override=override, locked_fn=locked)
    for fh, sd, nm, kind in cfg["hits"]:
        L = legs_by_side[sd]
        F = sp.rec[fh][id(L)][2]
        loc, tilt = ppose(fh)
        contact.append(round(player_hit_dist(F, loc, tilt), 2))
    pl = K.player(f"{code} player", tuple(B3(PX, 4, 40)))
    for f in range(1, F_END3 + 1):
        loc, tilt = ppose(f)
        pl.location = loc; pl.rotation_euler = (0, tilt, 0)
        pl.keyframe_insert("location", frame=f); pl.keyframe_insert("rotation_euler", frame=f)
    web_m = K._m("silk")
    fw_ = cfg["web"]
    for j in range(18):
        a = j / 18 * math.tau
        q = K.box(f"{code} web {j}", (math.cos(a) * 0.6, math.sin(a) * 0.6, 0.4 + (j % 5) * 0.35), (0.1, 1.5, 0.1), web_m, pl)
        q.rotation_euler = (rng.uniform(-1, 1), rng.uniform(-1, 1), a)
        q.scale = (0, 0, 0); q.keyframe_insert("scale", frame=1); q.keyframe_insert("scale", frame=fw_)
        q.scale = (1, 1, 1); q.keyframe_insert("scale", frame=fw_ + 3)
    for fh, sd, nm, kind in cfg["hits"]:
        for j in range(8):
            dirt_cube(part(fh, nm), Vector((rng.uniform(-8, 2), rng.uniform(-6, 6), rng.uniform(4, 12))), fh, 16, 0.35, K._m("spike"))
    REPORT[code + " contact"] = contact
    print(f"CONTACT {code}: spike-tip distance to your body at each hit {contact} (0 = touching)")
    check_legs(sp, code)
    ok = contact and max(contact) <= 0.01
    cam = follow(K.camera(f"{code} cam", tuple(B3(PX - 12, 16, 40 - 40)), tuple(B3(PX - 10, 6, 40)), 26), pl)
    label(cam, title, f"{len(contact)} hits, all touching you: {'yes' if ok else 'NO'}   legs through the floor: {REPORT[code]['ground']}   touching each other: {REPORT[code]['bad']}")
    K.light(f"{code} key", tuple(B3(PX - 20, 80, -20)), 180000, (1, 0.95, 0.9), "AREA", 120)
    take(code, title, cam, (1, F_END3))


def strike_driver(sp, hits, part, gs=None, pin_until=None, ppose=None, depth=0.25, ready_v=(0.55, 0.6, 0.45), rest_pt=None):
    """The front legs as weapons: returns (override, locked) for animate(). hits: [(frame, "L"/"R", part, kind)];
    part(f, name) is the point on you that spike aims at. Between far-apart hits the leg goes back to walking."""
    hits_of = {"R": [h for h in hits if h[1] == "R"], "L": [h for h in hits if h[1] == "L"]}

    def tip_in(f, nm, L):
        c = part(f, nm)
        return c + (c - sp.M @ L["hip"]).normalized() * depth          # a quarter block into you (0.1 side-on)

    def windows(sd):
        """Group this leg's hits into strike windows; between far-apart hits the leg goes back to walking."""
        out = []
        for fh, _, nm, kind in hits_of[sd]:
            until = (pin_until or fh + 3) if kind == "pin" else fh + 3
            if out and fh - 14 <= out[-1]["end"] + 20:
                out[-1]["hits"].append((fh, nm, kind, until)); out[-1]["end"] = until
            else:
                out.append(dict(start=fh - 14, end=until, hits=[(fh, nm, kind, until)]))
        return out
    WIN = {"R": windows("R"), "L": windows("L")}
    memo = {}

    def override(L, f):
        if L["k"] != 0:
            return None
        sd = "R" if L["side"] > 0 else "L"
        ready = sp.M @ Vector((L["rest"].x * ready_v[0], L["rest"].y * ready_v[1], ready_v[2] * SPAN))
        ground_pt = lambda: (rest_pt and rest_pt(L, f)) or cast_foot(sp, sp.M @ Vector((L["rest"].x, L["rest"].y, 0)), L=L)
        if gs and sd == gs[1] and gs[0] - 12 <= f <= gs[2] + 16:          # the other spike stabs the floor beside you
            loc, _ = ppose(gs[0])
            pt = loc + Vector((0.4, 2.4, 0))
            if f < gs[0] - 6:
                k_ = ("gs", sd)
                memo.setdefault(k_, L["planted"].copy() if L["planted"] is not None else ready)
                return memo[k_].lerp(ready, (f - (gs[0] - 12)) / 6)
            if f < gs[0] - 3:
                return ready
            if f <= gs[0]:
                return ready.lerp(pt, (f - (gs[0] - 3)) / 3)
            if f <= gs[2]:
                return pt
            if f <= gs[2] + 10:
                return pt.lerp(ready, (f - gs[2]) / 10)
            return ready.lerp(ground_pt(), (f - gs[2] - 10) / 6)
        for w_ in WIN[sd]:
            if not (w_["start"] <= f <= w_["end"] + 16):
                continue
            if f < w_["start"] + 6:                                         # lift the leg off the ground
                k_ = (sd, w_["start"])
                memo.setdefault(k_, L["planted"].copy() if L["planted"] is not None else ready)
                return memo[k_].lerp(ready, (f - w_["start"]) / 6)
            last_fh, last_nm, _, last_until = w_["hits"][-1]
            if f > last_until:                                              # back to ready, then down to the ground
                end_tip = tip_in(last_until, last_nm, L)
                if f <= last_until + 10:
                    return end_tip.lerp(ready, smooth((f - last_until) / 10))
                return ready.lerp(ground_pt(), (f - last_until - 10) / 6)
            prev = None
            for fh, nm, kind, until in w_["hits"]:
                if kind == "drag" and prev is not None and f <= fh:         # rip the spike down you
                    return tip_in(f, prev[1], L).lerp(tip_in(f, nm, L), smooth((f - prev[0]) / max(1, fh - prev[0])))
                if f <= fh:
                    if f < fh - 3:
                        if prev is not None and f <= prev[0] + 5:
                            return tip_in(prev[0], prev[1], L).lerp(ready, (f - prev[0]) / 5)
                        return ready
                    return ready.lerp(tip_in(fh, nm, L), (f - (fh - 3)) / 3)   # the stab: 3 frames
                if f <= until:
                    return tip_in(f, nm, L)                                # rides the hit / pins you
                prev = (until, nm)
            return tip_in(prev[0], prev[1], L)
        return None

    def locked(f):
        out = set()
        for i, L in enumerate(sp.legs):
            if L["k"] == 0 and override(L, f) is not None:
                out.add(i)
        return out

    return override, locked


for code in ("S1", "S2", "S3", "S4"):
    if want(code):
        strike_take(code, ai)
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


# ------------------------------------------------------------------ v2.0110: moving attacks
# J (round 10): "we will need more extending or movement attacks from the spider to make it not just stationary".
# Every strike here lands while R2 is walking, turning or climbing; the body never stops for a hit. Same leg rules
# (floor and leg-to-leg checks), every hit measured at 0 blocks, plus a new number: legs through you (any leg that
# isn't the striking spike passing through your body).
def player_rot(dirn, ang):
    """You tip over by ang, falling toward dirn (horizontal)."""
    d = Vector((dirn.x, dirn.y, 0))
    if ang == 0 or d.length < 1e-6:
        return Matrix.Identity(3)
    return Matrix.Rotation(ang, 3, Vector((0, 0, 1)).cross(d.normalized()))


def legs_through_you(sp, ploc_fn, locked_fn):
    """Frames where a leg that isn't striking (or a striking leg's thigh) passes through your body boxes."""
    n = []
    for f, legs in sorted(sp.rec.items()):
        loc, R = ploc_fn(f)
        Ri = R.transposed()
        lk = locked_fn(f)
        hit = False
        for i, L in enumerate(sp.legs):
            H, kn, F = legs[id(L)]
            segs = [(H, kn, sp.r_fem)] + ([] if i in lk else [(kn, F, sp.r_tib)])
            for a, b, r in segs:
                for t in np.linspace(0, 1, 14):
                    lp = Ri @ (a + (b - a) * float(t) - loc)
                    if min(box_dist(lp, Vector(c), Vector(h)) for c, h in PLAYER_BOXES) < r - 0.05:
                        hit = True; break
                if hit:
                    break
            if hit:
                break
        if hit:
            n.append(f)
    return n


def move_take(code, title, idx, grid, path, base, hits, end, cam_at, cam_aim, lens=26, smooth_half=4, period=12, enclosed=None, ready_v=(0.55, 0.6, 0.45), air=None, thread=None, cave=False):
    """A strike that lands while R2 keeps moving. path(f) -> (ground point, forward, up) in world; base(f) -> where you
    stand before any hit. hits: [(about frame, "L"/"R", part, push blocks, fall radians)]: each hit's exact frame is
    picked within 10 frames of its 'about' so the spike reaches you at 78% of the leg (never a straightened leg)."""
    O = area(idx)
    course_mesh(f"{code} ground", grid, O)
    sp = Spider(code + " R2", Gait(spread=1.0, knee_out=0.45, arc_out=0.05 * SPAN, period=period))
    pose = smoothed(path, smooth_half, 1, end)
    knocks = []                                                      # (frame, direction, push, fall)

    def ppose(f):
        loc = base(f).copy()
        R = Matrix.Identity(3)
        for fh, d, push, fall in knocks:
            u = smooth((f - fh) / (6 if fall > 1 else 4))
            loc = loc + d * push * u + Vector((0, 0, (1.6 if fall > 1 else 0.0) * math.sin(math.pi * u)))
            R = player_rot(d, fall * u) @ R
        return loc, R

    def part(f, nm):
        loc, R = ppose(f)
        return loc + R @ Vector((0, 0, PART_Z[nm]))
    sched = []
    for about, sd, nm, push, fall, *ratio in hits:
        ratio = ratio[0] if ratio else 0.78
        L = [l_ for l_ in sp.legs if l_["k"] == 0 and (l_["side"] > 0) == (sd == "R")][0]
        reach = L["L1"] + L["L2"]
        best = None
        for f in range(max(2, about - 10), min(end - 8, about + 10) + 1):
            p, fw, up = pose(f)
            sp.body(f, p, fw, up)
            dist = (part(f, nm) - sp.M @ L["hip"]).length
            score = abs(dist - ratio * reach) + 0.03 * abs(f - about)
            if dist <= 0.86 * reach and (best is None or score < best[0]):
                best = (score, f, dist)
        if best is None:
            print(f"MOVE {code}: no frame near {about} puts the {sd} spike in reach of your {nm}")
            best = (0, about, -1)
        fh = best[1]
        sched.append((fh, sd, nm, "stab"))
        p, fw, up = pose(fh)
        d = part(fh, nm) - (p + up * sp.body_h)
        d.z = 0
        knocks.append((fh, d.normalized(), push, fall))
        print(f"MOVE {code}: hit {sd} {nm} at frame {fh} (asked {about}), {best[2]:.1f} of {reach:.1f} blocks reach")
    def air_foot(L, f):
        """v2.0120, in the air: tucked toward the hips in flight; spreads down to the landing pose over the last 6
        frames (feet out and a little forward, just above the body's ground plane)."""
        f1 = next(g_ for g_ in range(f, f + 400) if not air(g_))
        z = 0.3 + 2.4 * smooth((f1 - f - 1) / 6)
        return sp.M @ Vector((L["rest"].x * 0.8, L["rest"].y * 0.8 + 1.5, z))
    override, locked = strike_driver(sp, sched, part, depth=0.1, ready_v=ready_v,
                                     rest_pt=(lambda L, f: air_foot(L, f) if air(f) else None) if air else None)
    if air is not None:
        # every leg that isn't striking takes the air pose, eased in over 5 frames from where it let go
        strike_over, strike_locked, take_off = override, locked, {}

        def override(L, f):
            o_ = strike_over(L, f)
            if o_ is not None or not air(f):
                return o_
            f0 = max(g_ for g_ in range(1, f + 1) if not air(g_ - 1)) if not air(1) else 1
            if id(L) not in take_off or take_off[id(L)][0] != f0:
                take_off[id(L)] = (f0, L["planted"].copy() if L["planted"] is not None else air_foot(L, f))
            return take_off[id(L)][1].lerp(air_foot(L, f), smooth((f - f0 + 1) / 5))

        def locked(f):
            return set(range(8)) if air(f) else strike_locked(f)
    animate(sp, (1, end), pose, period=period, override=override, locked_fn=locked, enclosed=enclosed)
    if thread is not None:                                           # the dragline: ceiling to spinnerets
        silk = K._m("silk")
        line = K.box(f"{code} dragline", (0, 0, 0), (0.12, 1, 0.12), silk, None)
        line.rotation_mode = "QUATERNION"
        for f in range(1, end + 1):
            a = thread(f)
            Mi = sp.recM[f].inverted()
            b = Mi @ Vector((0, -sp.ceph_l * 0.5 - 2.6 * S, sp.body_h + 0.4 * S))
            if a is None:
                line.scale = (0, 0.01, 0)
            else:
                line.location = (a + b) / 2
                line.rotation_quaternion = Vector((0, 1, 0)).rotation_difference((b - a).normalized())
                line.scale = (1, max(0.01, (b - a).length), 1)
            for dp in ("location", "rotation_quaternion", "scale"):
                line.keyframe_insert(dp, frame=f)
    contact = []
    for fh, sd, nm, kind in sched:
        L = [l_ for l_ in sp.legs if l_["k"] == 0 and (l_["side"] > 0) == (sd == "R")][0]
        F = sp.rec[fh][id(L)][2]
        loc, R = ppose(fh)
        contact.append(round(min(box_dist(R.transposed() @ (F - loc), Vector(c), Vector(h)) for c, h in PLAYER_BOXES), 2))
    pl = K.player(f"{code} player", tuple(base(1)))
    pl.rotation_mode = "QUATERNION"
    you = K.mat("you, bright", (0.35, 0.75, 1.0), 0.5, (0.35, 0.75, 1.0), 0.8)   # you're 2 blocks tall next to a 36-block spider: lit so you read
    for ch in pl.children:
        if ch.type == "MESH" and not ch.name.endswith("ring"):
            ch.data.materials.clear(); ch.data.materials.append(you)
    for f in range(1, end + 1):
        loc, R = ppose(f)
        pl.location = loc; pl.rotation_quaternion = R.to_quaternion()
        pl.keyframe_insert("location", frame=f); pl.keyframe_insert("rotation_quaternion", frame=f)
    for fh, sd, nm, kind in sched:
        for j in range(8):
            dirt_cube(part(fh, nm), Vector((rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(4, 12))), fh, 16, 0.35, K._m("spike"))
    REPORT[code + " contact"] = contact
    REPORT[code + " hit frames"] = [s[0] for s in sched]
    print(f"CONTACT {code}: spike-tip distance to your body at each hit {contact} (0 = touching)")
    check_legs(sp, code)
    thru = legs_through_you(sp, ppose, locked)
    REPORT[code]["through_you"] = len(thru)
    REPORT[code]["through_you_first"] = thru[:8]
    print(f"THROUGHYOU {code}: {len(thru)} frames, first {thru[:8]}")
    speed = [((pose(f + 1)[0] - pose(f)[0]).length * FPS) for f in range(1, end)]
    REPORT[code]["top_speed"] = round(max(speed), 1)
    print(f"SPEED {code}: fastest at frame {1 + int(np.argmax(speed))}", [round(v_) for v_ in speed[::10]])
    for fh, sd, nm, kind in sched:
        L = [l_ for l_ in sp.legs if l_["k"] == 0 and (l_["side"] > 0) == (sd == "R")][0]
        H, kn, F = sp.rec[fh][id(L)]
        print(f"  hit {fh}: hip-to-target {(part(fh, nm) - H).length:.1f}, hip-to-tip {(F - H).length:.1f}, reach {L['L1'] + L['L2']:.1f}")
    ok = contact and max(contact) <= 0.01
    aim = K.empty(f"{code} aim")                                     # the camera follows the middle of the fight
    for f in range(1, end + 1):
        p, fw, up = pose(f)
        aim.location = (p + up * sp.body_h).lerp(ppose(f)[0], 0.4)
        aim.keyframe_insert("location", frame=f)
    # a dolly: the camera travels with the fight at a fixed offset (cam_at, world blocks) so you stay in the shot
    cam = follow(K.camera(f"{code} cam", tuple(aim.location + cam_at), tuple(aim.location), lens), aim)
    for f in range(1, end + 1):
        p, fw, up = pose(f)
        cam.location = (p + up * sp.body_h).lerp(ppose(f)[0], 0.4) + cam_at
        cam.keyframe_insert("location", frame=f)
    cam.data.clip_end = 2.5 * cam_at.length + 120
    r_ = REPORT[code]
    label(cam, title, f"hits on you {sum(c_ <= 0.01 for c_ in contact)}/{len(contact)} | through floor {r_['ground']} | "
                      f"legs touching {r_['bad']} | through you {r_['through_you']}")
    K.light(f"{code} key", tuple(ppose(1)[0] + cam_at * 0.5 + Vector((0, 0, 80))), 300000, (1, 0.95, 0.9), "AREA", 160)
    if cave:                                                          # under a ceiling: light in from the open side
        lo = K.light(f"{code} side key", tuple(aim.location + cam_at * 1.3), 240000, (1, 0.95, 0.9), "AREA", 90)
        lo.rotation_mode = "QUATERNION"
        lo.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(-cam_at.normalized())
        K.light(f"{code} cave fill", tuple(aim.location + Vector((0, -20, 12))), 9000, (0.85, 0.9, 1), "POINT", 18)   # soft: no white spot on the floor
    take(code, title, cam, (1, end))
    return sp


def B6(x, y, z):
    """Grid coordinates (x along, y up, z across) to world, like the other takes."""
    return Vector((x, -z, y))


FLAT = np.zeros((260, 20, 110), bool); FLAT[:, :4, :] = True
Xw, Zw = Vector((1, 0, 0)), Vector((0, 0, 1))

# M1 drive-back combo: R2 walks you down. Four jabs, left-right-left-right, and it never stops: each hit knocks you
# back about 2 blocks and it steps straight into the gap; the last one throws you.
if want("M1"):
    def m1_path(f):
        f = min(max(f, 1), 150)
        x = 20 + 0.45 * min(f, 30) + 0.22 * max(0, f - 30)          # charges in, then drives on at 5 blocks a second
        return B6(x, 4, 55) + area(ai), Xw, Zw
    m1_base = lambda f: B6(53.5, 4, 55) + area(ai)
    move_take("M1", "M1 drive-back combo (walking)", ai, FLAT, m1_path, m1_base,
              [(44, "L", "chest", 4.0, 0.2), (62, "R", "chest", 4.0, 0.2), (80, "L", "head", 4.0, 0.3), (100, "R", "chest", 6.0, 1.45)],
              150, Vector((-10, 56, 18)), None, lens=24)
ai += 1

# M2 circling strikes: R2 circles you crabwise, facing you, darts in to strike from the side (left leg), keeps
# circling, swings round to face you head on for a right jab, reverses and circles the other way for the last hit.
if want("M2"):
    PC2 = (130.0, 55.0)

    def m2_path(f):
        f = min(max(f, 1), 170)
        # angle round you: counter-clockwise for 70 degrees, a pause to face you, then clockwise
        a = math.radians(200) + math.radians(70) * smooth(f / 70) - math.radians(80) * smooth((f - 96) / 64)
        dips = sum(9.0 * math.exp(-((f - c) / 12.0) ** 2) for c in (44, 84, 140))
        Rc = 27.0 - dips
        c = B6(PC2[0], 4, PC2[1]) + area(ai)
        rad = Vector((math.cos(a), math.sin(a), 0))
        s = 1.0 if f < 84 else -1.0
        tang = Vector((-math.sin(a), math.cos(a), 0)) * s
        beta = math.radians(50) + math.radians(40) * math.exp(-((f - 84) / 14.0) ** 2)   # head on at the turn
        fw = tang * math.cos(beta) - rad * math.sin(beta)
        return c + rad * Rc, fw, Vector((0, 0, 1))
    m2_base = lambda f: B6(PC2[0], 4, PC2[1]) + area(ai)
    move_take("M2", "M2 circling strikes (turning)", ai, FLAT, m2_path, m2_base,
              [(44, "L", "chest", 1.5, 0.25), (84, "R", "head", 1.5, 0.3), (140, "R", "chest", 6.0, 1.45)],
              170, Vector((34, 42, 24)), None, lens=24)
ai += 1

# M3 climbing strike (the move chart's "R2 climbs a wall to you"): you stand at the top of a 28-block cliff. R2
# runs at it, climbs, and stabs your legs and then your chest over the lip while still climbing; it rolls over the
# edge onto the top and the last stab throws you off your feet.
if want("M3"):
    WX, TOPY = 120, 32
    g7 = np.zeros((260, 40, 110), bool); g7[:, :4, :] = True
    g7[WX:, :TOPY, :] = True
    PZ3 = 55

    def m3_path(f):
        f = min(max(f, 1), 190)
        keys = [(1, B6(84, 4, PZ3), Xw, Zw), (34, B6(WX - 12, 4, PZ3), Xw, Zw),
                (46, B6(WX - 2, 9, PZ3), Vector((1, 0, 1)).normalized(), Vector((-1, 0, 1)).normalized()),
                (58, B6(WX, 14, PZ3), Zw, -Xw), (76, B6(WX, 23, PZ3), Zw, -Xw), (124, B6(WX, 27, PZ3), Zw, -Xw),
                (136, B6(WX + 2, TOPY - 2, PZ3), Vector((1, 0, 1)).normalized(), Vector((-1, 0, 1)).normalized()),
                (150, B6(WX + 5, TOPY, PZ3), Xw, Zw), (190, B6(WX + 9, TOPY, PZ3), Xw, Zw)]
        p, fw, up = keyed_pose([(k[0], k[1] + area(ai), k[2], k[3]) for k in keys])(f)
        return p, fw, up
    m3_base = lambda f: B6(WX + 12, TOPY, PZ3) + area(ai)
    move_take("M3", "M3 climbing strike (climbing)", ai, g7, m3_path, m3_base,
              [(86, "R", "legs", 0.8, 0.15, 0.75), (110, "L", "chest", 1.2, 0.3, 0.75), (140, "R", "chest", 6.0, 1.45, 0.6)],
              190, Vector((-34, 40, 26)), None, lens=24, smooth_half=6, ready_v=(0.8, 1.0, 0.5))
ai += 1

# M4 chase-down: you run; R2 runs you down from behind, hooks your legs (you go down) and, still walking on, pins
# you to the floor with the other spike.
if want("M4"):
    PZ4 = 55

    def m4_base(f):
        u = min(f, 92)
        return B6(70 + 0.24 * u - 0.24 * max(0, u - 80) ** 2 / 24, 4, PZ4) + area(ai)

    def m4_path(f):
        f = min(max(f, 1), 160)
        # 11.5 blocks a second, then it brakes hard once you are down
        x = 32 + sum(0.48 - 0.42 * smooth((g_ - 84) / 24) for g_ in range(1, f))
        return B6(x, 4, PZ4 + 2.5 * math.sin(f / 18)) + area(ai), Vector((1, 0.12 * math.cos(f / 18) * -1, 0)), Zw
    move_take("M4", "M4 chase-down (you running)", ai, FLAT, m4_path, m4_base,
              [(88, "R", "legs", 1.8, 1.4), (126, "L", "chest", 0.3, 0.0)],
              160, Vector((-14, 56, 20)), None, lens=24)
ai += 1


# ------------------------------------------------------------------ v2.0120: ceiling and leap strikes
# J picked "Ceiling and leap strikes" after keeping M1, M3 and M4: spiders dropping from the ceiling and leaping at
# you. Same rules; in the air every leg that isn't striking spreads into a landing pose and is still checked against
# the other legs, the body and you.
def tilt(pitch_deg=0.0, roll_deg=0.0):
    """Forward and up for a body heading +x, nose up by pitch, rolled by roll (180 = upside down)."""
    pr = math.radians(pitch_deg)
    fw = Vector((math.cos(pr), 0, math.sin(pr)))
    up = Vector((-math.sin(pr), 0, math.cos(pr)))
    up = Quaternion(fw, math.radians(roll_deg)) @ up
    return fw, up


CEIL6 = 44
CAVE6 = np.zeros((260, 52, 110), bool); CAVE6[:, :4, :] = True; CAVE6[:, CEIL6:50, :] = True
PZ6 = 55


def keyed6(keys):
    """keys in grid coordinates: (frame, x, y, pitch, roll); held before the first and after the last key."""
    kp = keyed_pose([(k[0], B6(k[1], k[2], PZ6) + area(ai), *tilt(k[3], k[4])) for k in keys])
    return lambda f: kp(min(max(f, keys[0][0]), keys[-1][0]))


# L1 thread drop: R2 walks the ceiling upside down, lets go on its dragline above you, rights itself as it drops,
# stabs you twice hanging on the thread, then lets the thread out, lands and walks into a throw.
if want("L1"):
    l1 = keyed6([(1, 72, CEIL6, 0, 180), (48, 108, CEIL6, 0, 180), (52, 110, CEIL6 - 1, 0, 180), (64, 112, 28, 0, 90),
                 (74, 113, 12, 0, 0), (92, 114, 9, 0, 0), (100, 115, 4, 0, 0), (150, 124, 4, 0, 0)])
    move_take("L1", "L1 thread drop (from the ceiling)", ai, CAVE6, l1, lambda f: B6(130, 4, PZ6) + area(ai),
              [(80, "L", "chest", 3.0, 0.2), (90, "R", "head", 3.0, 0.3), (124, "R", "chest", 6.0, 1.45)],
              150, Vector((-8, 58, 16)), None, lens=24, smooth_half=3,
              air=lambda f: 50 <= f < 100, thread=lambda f: B6(110, CEIL6, PZ6) + area(ai) if 50 <= f < 104 else None, cave=True)
ai += 1

# L2 leap strike: R2 walks up, crouches, leaps 30 blocks in an arc and the right spike hits you as it comes down;
# it lands, the left spike follows, and it walks on into a throw.
if want("L2"):
    l2 = keyed6([(1, 30, 4, 0, 0), (30, 48, 4, 0, 0), (40, 52, 2.2, 12, 0), (44, 58, 8, 28, 0), (52, 70, 16, 0, 0),
                 (60, 80, 8, -24, 0), (64, 84, 4, -6, 0), (70, 86, 4, 0, 0), (130, 96, 4, 0, 0)])
    move_take("L2", "L2 leap strike (leaping)", ai, FLAT, l2, lambda f: B6(104, 4, PZ6) + area(ai),
              [(58, "R", "chest", 2.5, 0.3), (68, "L", "head", 3.0, 0.3), (104, "R", "chest", 6.0, 1.45)],
              130, Vector((-10, 56, 18)), None, lens=24, smooth_half=3, air=lambda f: 41 <= f < 64)
ai += 1

# L3 ceiling pounce: you hover under the cave roof; R2 runs at you upside down on the ceiling, kicks off, rolls
# upright in the air and stabs you twice mid-air; you both fall, it lands and stabs you on the floor.
if want("L3"):
    l3 = keyed6([(1, 64, CEIL6, 0, 180), (44, 96, CEIL6, 0, 180), (48, 99, CEIL6 - 2, -10, 180), (56, 102, 30, -15, 175), (62, 104, 26, -5, 70),
                 (68, 106, 24, 0, 0), (76, 108, 22, 0, 0), (86, 110, 10, 0, 0), (92, 111, 4, 0, 0), (150, 116, 4, 0, 0)])

    def l3_base(f):
        y = 24 + 0.5 * math.sin(f * 0.15) if f < 74 else 24 - 20 * min(1.0, ((f - 74) / 14) ** 2)
        return B6(122, y, PZ6) + area(ai)
    move_take("L3", "L3 ceiling pounce (you flying)", ai, CAVE6, l3, l3_base,
              [(72, "L", "chest", 3.0, 0.3, 0.68), (80, "R", "chest", 3.0, 0.5, 0.68), (126, "R", "chest", 4.0, 1.45)],
              150, Vector((-8, 58, 12)), None, lens=24, smooth_half=3, air=lambda f: 46 <= f < 92, cave=True)
ai += 1

# L4 cliff leap: you stand 40 blocks out from the foot of a 28-block cliff; R2 runs to the edge, leaps off and down
# at you, the right spike hits you on the way down, it lands, the left spike follows, then the throw.
if want("L4"):
    g8 = np.zeros((260, 40, 110), bool); g8[:, :4, :] = True; g8[:60, :32, :] = True
    l4 = keyed6([(1, 26, 32, 0, 0), (30, 42, 32, 0, 0), (38, 45, 31.2, 6, 0), (46, 64, 38, 10, 0), (56, 76, 22, -34, 0),
                 (64, 84, 4, -8, 0), (70, 86, 4, 0, 0), (130, 94, 4, 0, 0)])
    move_take("L4", "L4 cliff leap (leaping down)", ai, g8, l4, lambda f: B6(102, 4, PZ6) + area(ai),
              [(58, "R", "chest", 2.5, 0.3), (76, "L", "head", 3.0, 0.3, 0.7), (104, "R", "chest", 6.0, 1.45)],
              130, Vector((-6, 60, 14)), None, lens=24, smooth_half=3, air=lambda f: 39 <= f < 64)
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
MODEL_AT = {"W1": 120, "W2": 120, "W3": 120, "D2": 44, "D3": 38, "P1": 90, "C1": 160, "S1": 36, "S2": 31, "S3": 50, "S4": 112, "C1b": 38}
MODEL_AT.update({c: REPORT[c + " hit frames"][1] for c in ("M1", "M2", "M3", "M4", "L1", "L2", "L3", "L4") if c + " hit frames" in REPORT})
RDIR = argv[argv.index("--rdir") + 1] if "--rdir" in argv else None              # a new folder per round (v2.0110: renders_anim4)
if "--stills" in argv:
    sdir = os.path.join(os.path.dirname(OUT), RDIR or "renders_anim2", "stills")
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
    rdir = os.path.join(os.path.dirname(OUT), RDIR or ("renders_anim" + ("3" if "spider_anims4" in OUT else "2")))
    os.makedirs(rdir, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.cycles.samples = 16
    sc.render.image_settings.media_type = "VIDEO"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"; sc.render.ffmpeg.constant_rate_factor = "MEDIUM"
    vcodes = set(argv[argv.index("--video-codes") + 1].split(",")) if "--video-codes" in argv else None
    for code, title, cam, (f0, f1) in takes:
        if vcodes is not None and code not in vcodes:
            continue
        show_only(code)
        sc.camera = cam; sc.frame_start, sc.frame_end = f0, f1
        sc.render.filepath = os.path.join(rdir, title.replace(" ", "_").replace("(", "").replace(")", "") + ".mp4")
        bpy.ops.render.render(animation=True)
        print("video", sc.render.filepath)
print("done", OUT)
