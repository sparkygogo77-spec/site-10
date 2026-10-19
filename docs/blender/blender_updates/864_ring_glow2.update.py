# Pass 864: ring glow in first person, round 2 (PC chat, 2026-10-18).
# Why: J rated pass 860 G1 face glow, G2 rim line and G3 orbit pixels IMPROVE with no note (= 3 new variations each,
#   built differently) and dropped G4 face meter, G5 pulse on use and G6 knuckle light. 860's rules still hold (from his
#   "these light rays from blender are not it"): NOTHING on or along the arm/sleeve, no translucent sheets or volumes near
#   the camera, no light shafts, a small emissive area, saturated green that is never white. From the design skill:
#   darker cores, solid readable lines, never static but not fast, erratic beats regular.
# Rig, timeline, cameras, Bridge and stage are 860's (this script runs 860's builders, then adds its own takes).
# Timeline (every take): 1-60 ring charge 0 -> 100%; 60-90 hold; 90-120 Bridge used (arm pushes out, tiles 91-103).
# Takes:
#   G1a breathing face: G1's face glow = charge, then at full it breathes slowly (+-15%, 3 s), never static.
#   G1b dark core: the face's centre stays dark glass; a bright inner border = charge, so the core reads darker.
#   G1c fills from the centre: a lit square grows from the face's centre to its edges as charge rises (like the
#        lantern's light spreading from the port), then holds.
#   G2a two lines meet: two rim lines start at the bottom and trace both ways, meeting at the top at 100%; then one
#        brighter segment travels slowly round.
#   G2b double rim: the outer rim line traces 0-50% charge, a second inner line 50-100%.
#   G2c dashed rim: the rim is dark-green dashes (like the lantern's stitches); they light one by one with charge, and at
#        full a slow chase runs round them.
#   G3a erratic orbit: 4 pixels on uneven orbits (own radius, speed and wobble), still within 2 px of the face.
#   G3b trailing pixels: each pixel pulls a 2-pixel tail of darker green; slower than 860's.
#   G3c tilted orbits: 2 pairs of pixels orbit on tilted planes round the ring, like an atom; one pixel per 25% charge.
# Cameras "Cam <code> - first person" (120 deg, crosshair) and "Cam <code> - third person", plus "Cam all".
# Builds LanternLive\combat\ring_glow2.blend.
import math, os
import bpy
import numpy as np


def _find_860():
    names = []
    if os.environ.get("KL_REPO"):
        names.append(os.path.join(os.environ["KL_REPO"], "docs", "blender", "blender_updates"))
    if "__file__" in globals():
        names.append(os.path.dirname(os.path.abspath(__file__)))
    names.append(os.path.join(os.path.expanduser("~"), "Documents", "LanternLive", "site-10", "docs", "blender", "blender_updates"))
    names.append("/home/claude/site-10/docs/blender/blender_updates")
    for d in names:
        p = os.path.join(d, "860_ring_glow.update.py")
        if os.path.exists(p):
            return p
    raise FileNotFoundError("864 needs 860_ring_glow.update.py next to it (or KL_REPO set)")


_s860 = _find_860()
_t860 = open(_s860, encoding="utf-8").read()
exec(compile(_t860[:_t860.index("# ----------------------------------------------------------------- the six ideas")], _s860, "exec"), globals())
SCENE_NAME = "Ring Glow 2"
OUT_REL = "combat/ring_glow2.blend"
OUT = os.path.join(FOLDER, *OUT_REL.split("/"))
_old = bpy.data.scenes.get(SCENE_NAME)
if _old is not None and _old != scene:
    bpy.data.scenes.remove(_old)
scene.name = SCENE_NAME
rng = np.random.default_rng(864)
BREATH = 60                                    # 3 s at 20 ticks a second
# The first-person eye sees the ring from its back sides (mount +x and +y, measured: camera direction x+0.78 y+0.62
# z+0.03), never its front (-z). So every take must read on those sides, not only on the front face.
EMIT_CAP = 0.6                                 # 860's strengths (up to 2.6) clipped the green to pale mint: scale down


_lit_860 = lit_mat
def lit_mat(name, emit_keys, rgb=GLOW_RGB, base=DARK_RGB):
    return _lit_860(name, [(f, v * EMIT_CAP) for f, v in emit_keys], rgb, base)


def face_box(tag, mt, px, m, half, z0=-1.02, z1=-0.98, name="face part"):
    """A thin square on the front of the ring face (the face spans c +-0.95 px, front at z -1.0 px)."""
    c = 0.6 * px
    return box(f"{tag} {name}", (c - half * px, -half * px, z0 * px), (c + half * px, half * px, z1 * px), m, mt)


# ----------------------------------------------------------------- G1: the face itself
def fx_G1a(tag, pt, px, eye_obj):
    """Face glow = charge (0.1 -> 2.0 over 1-60), then a slow breath 1.7..2.3 every 3 s; a small lift on Bridge."""
    keys = [(f, 0.1 + 1.9 * charge(f)) for f in range(1, 61, 6)] + [(60, 2.0)]
    for f in range(60, FRAME_END + 1, BREATH // 4):
        keys.append((f, 2.0 + 0.3 * math.sin((f - 60) / BREATH * 2 * math.pi)))
    keys += [(91, 2.5), (95, 2.0)]
    return lit_mat(f"{tag} G1a face", sorted(dict(keys).items()))


def fx_G1b(tag, pt, px, eye_obj):
    """Dark glass core: a dark band through the middle of the face's depth (wraps all four sides), so each side reads as
    two bright edge lines round a dark centre; plus a dark square on the front (0.55 px half-width) for third person.
    The face round them glows = charge."""
    mt = mount_of(pt); c = 0.6 * px
    core = mat(f"{tag} G1b core", DARK_RGB, rough=0.15)
    box(f"{tag} G1b core band", (c - 0.97 * px, -0.97 * px, -0.86 * px), (c + 0.97 * px, 0.97 * px, -0.54 * px), core, mt)
    face_box(tag + " G1b", mt, px, core, 0.55, name="dark core")
    return lit_mat(f"{tag} G1b face", [(f, 0.15 + 2.25 * charge(f)) for f in range(1, 61, 6)] + [(60, 2.4), (90, 2.4), (92, 2.8), (96, 2.4)])


def fx_G1c(tag, pt, px, eye_obj):
    """Two lit bars cross the dark face (one full-length along x, one along y, both full depth and just proud of every
    side) and grow outward from the centre over 1-60, so the visible sides fill from their middle and the front fills
    as a widening cross, then a full square. On Bridge they narrow a little (the cost) and regrow by 110."""
    mt = mount_of(pt); c = 0.6 * px
    m = lit_mat(f"{tag} G1c fill", [(1, 2.1)])
    for axis in ("x", "y"):
        piv = empty(f"{tag} G1c fill pivot {axis}", (c, 0, 0), mt)
        box(f"{tag} G1c fill {axis}", (-0.97 * px, -0.97 * px, -1.03 * px), (0.97 * px, 0.97 * px, -0.37 * px), m, piv)
        def sc(s):
            return (1, s, 1) if axis == "x" else (s, 1, 1)
        for f in list(range(1, 61, 4)) + [60]:
            key(piv, f, sc=sc(max(0.0001, smooth(charge(f)))))
        key(piv, 90, sc=sc(1)); key(piv, 93, sc=sc(0.75)); key(piv, 110, sc=sc(1))
    return lit_mat(f"{tag} G1c face", [(1, 0.05)])


# ----------------------------------------------------------------- G2: lines round the rim
def fx_G2a(tag, pt, px, eye_obj):
    """16 rim segments; the trace starts at the middle of the bottom edge and runs both ways, meeting at the top at
    100%. From 64 one segment glows brighter (3.2 vs 1.6) and moves one step every 4 ticks, a slow lap."""
    mt = mount_of(pt); n = 16
    # rim_loop's order: bottom edge left->right is k 0-3, right side 4-7, top right->left 8-11, left side 12-15.
    start = 2                                         # just right of the bottom middle
    dist = {}
    for k in range(n):
        d1 = (k - start) % n; d2 = (start - 1 - k) % n
        dist[k] = min(d1, d2)                         # steps from the start, going either way
    far = max(dist.values())
    segs = []
    def keys(k, n_):
        fa = 1 + int(round(58 * (dist[k] + 1) / (far + 1)))
        return [(1, 0.0001), (fa - 2, 0.0001), (fa, 1.0)]
    for k in range(n):
        line = lit_mat(f"{tag} G2a rim {k}", [(1, 1.6)])
        segs.append(line)
    objs = rim_loop(tag + " G2a", mt, px, segs[0], keys=keys)
    for k, o in enumerate(objs):
        o.data = o.data.copy(); o.data.materials[0] = segs[k]
        keyf = [(1, 1.6), (63, 1.6)]
        for lap in range(64, FRAME_END + 1, 4 * n):
            fk = lap + 4 * ((k - start) % n)
            keyf += [(fk - 1, 1.6), (fk, 3.2), (fk + 4, 1.6)]
        anim_emit(segs[k], sorted(dict((f, v) for f, v in keyf if f <= FRAME_END).items()))
    return lit_mat(f"{tag} G2a face", [(1, 0.3)])


def fx_G2b(tag, pt, px, eye_obj):
    """Outer rim line (16 segments) traces over 1-30 (0-50%), then a second line as a belt round the face's sides (12
    segments, mid-depth, so first person sees it) over 30-60 (50-100%). Both steady at 1.7; the face stays dim."""
    mt = mount_of(pt); c = 0.6 * px
    outer = lit_mat(f"{tag} G2b outer", [(1, 1.7)])
    rim_loop(tag + " G2b", mt, px, outer,
             keys=lambda k, n: [(1, 0.0001), (int(round(29 * (k + 1) / n)) - 1, 0.0001), (int(round(29 * (k + 1) / n)) + 1, 1.0)])
    inner = lit_mat(f"{tag} G2b inner", [(1, 1.7)])
    r = 0.96 * px; t = 0.05 * px
    corners = [(c - r, -r), (c + r, -r), (c + r, r), (c - r, r)]
    k = 0; n = 12
    for s in range(4):
        (xa, ya), (xb, yb) = corners[s], corners[(s + 1) % 4]
        for j in range(3):
            u0, u1 = j / 3, (j + 1) / 3
            pa = (xa + (xb - xa) * u0, ya + (yb - ya) * u0); pb = (xa + (xb - xa) * u1, ya + (yb - ya) * u1)
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            piv = empty(f"{tag} G2b inner pivot {k}", (mid[0], mid[1], 0), mt)
            box(f"{tag} G2b inner line {k}", (min(pa[0], pb[0]) - mid[0] - t, min(pa[1], pb[1]) - mid[1] - t, -0.79 * px),
                (max(pa[0], pb[0]) - mid[0] + t, max(pa[1], pb[1]) - mid[1] + t, -0.65 * px), inner, piv)
            fa = 30 + int(round(30 * (k + 1) / n))
            key(piv, 1, sc=0.0001); key(piv, fa - 2, sc=0.0001); key(piv, fa, sc=1.0)
            k += 1
    return lit_mat(f"{tag} G2b face", [(1, 0.25)])


def fx_G2c(tag, pt, px, eye_obj):
    """24 short dashes round the rim with gaps, dark green (0.15) until charge reaches them (one by one, 1.8); at full a
    slow chase: each dash brightens to 2.6 in turn, one every 3 ticks."""
    mt = mount_of(pt); c = 0.6 * px; r = 1.12 * px; t = 0.1 * px
    corners = [(c - r, -r), (c + r, -r), (c + r, r), (c - r, r)]
    k = 0; n = 24
    for s in range(4):
        (xa, ya), (xb, yb) = corners[s], corners[(s + 1) % 4]
        for j in range(6):
            u0, u1 = (j + 0.2) / 6, (j + 0.8) / 6           # 60% dash, 40% gap
            pa = (xa + (xb - xa) * u0, ya + (yb - ya) * u0); pb = (xa + (xb - xa) * u1, ya + (yb - ya) * u1)
            fa = 1 + int(round(58 * (k + 1) / n))
            keyf = [(1, 0.15), (fa - 1, 0.15), (fa, 1.8), (62, 1.8)]
            for lap in range(62, FRAME_END + 1, 3 * n):
                fk = lap + 3 * k
                keyf += [(fk - 1, 1.8), (fk, 2.6), (fk + 3, 1.8)]
            m = lit_mat(f"{tag} G2c dash {k}", sorted(dict((f, v) for f, v in keyf if f <= FRAME_END).items()))
            box(f"{tag} G2c dash {k}", (min(pa[0], pb[0]) - t, min(pa[1], pb[1]) - t, -0.62 * px),
                (max(pa[0], pb[0]) + t, max(pa[1], pb[1]) + t, -0.42 * px), m, mt)
            k += 1
    return lit_mat(f"{tag} G2c face", [(1, 0.3)])


# ----------------------------------------------------------------- G3: pixels near the face
def _motes(tag, mt, px, code, path, n=4, size=0.17, emit=2.0, appear=None):
    """n solid pixels; path(j, f) -> local (x, y, z); pixel j appears at appear(j) (default each 25% of charge)."""
    mm = lit_mat(f"{tag} {code} mote", [(1, emit)])
    pm = pixel_mesh(mm, size * px)
    objs = []
    for j in range(n):
        o = link(bpy.data.objects.new(f"{tag} {code} mote {j}", pm)); o.parent = mt
        fa = appear(j) if appear else 15 * (j + 1)
        for f in sorted(set(list(range(1, FRAME_END + 1, 2)) + [fa - 1, fa])):
            key(o, f, loc=path(j, f), sc=0.0001 if f < fa else 1.0)
        objs.append(o)
    return objs


def _tuck(f):
    return 1.0 - 0.35 * math.sin((f - 90) / 8 * math.pi) if 90 <= f <= 98 else 1.0


def fx_G3a(tag, pt, px, eye_obj):
    """4 pixels, each with its own radius (1.4-1.9 px), speed (a lap in 50-80 ticks), direction-safe (all one way) and a
    small in/out wobble, so the pattern never repeats in the clip; depth 0.6-1.0 px in front."""
    mt = mount_of(pt); c = 0.6 * px
    rad = [1.9, 1.4, 1.7, 1.55]; lap = [64, 50, 80, 58]; ph = [0.0, 2.1, 4.0, 5.3]; dz = [0.8, 0.6, 1.0, 0.7]
    def path(j, f):
        a = (f - 1) * 2 * math.pi / lap[j] + ph[j]
        rr = (rad[j] + 0.15 * math.sin(f * 0.21 + j)) * _tuck(f) * px
        return (c + rr * math.cos(a), rr * math.sin(a), -dz[j] * px)
    _motes(tag, mt, px, "G3a", path)
    return lit_mat(f"{tag} G3a face", [(1, 0.4), (60, 0.9)])


def fx_G3b(tag, pt, px, eye_obj):
    """4 pixels at 1.8 px, a lap per 90 ticks (slower than 860's 60); each pulls a tail of 2 smaller, darker pixels
    (emit 0.9 and 0.4) a few degrees behind it."""
    mt = mount_of(pt); c = 0.6 * px
    def ring_path(lag):
        def path(j, f):
            a = (f - 1) * 2 * math.pi / 90 + j * math.pi / 2 - lag
            rr = 1.8 * _tuck(f) * px
            return (c + rr * math.cos(a), rr * math.sin(a), -0.8 * px)
        return path
    _motes(tag, mt, px, "G3b", ring_path(0.0))
    _motes(tag, mt, px, "G3b tail1", ring_path(0.32), size=0.13, emit=0.9)
    _motes(tag, mt, px, "G3b tail2", ring_path(0.64), size=0.1, emit=0.4)
    return lit_mat(f"{tag} G3b face", [(1, 0.4), (60, 0.9)])


def fx_G3c(tag, pt, px, eye_obj):
    """2 orbits tilted 55 degrees either way round the face's centre (like an atom), 2 pixels each, at 1.7 px; laps of 70
    and 84 ticks. The tilt keeps every pixel within 2 px of the face and in front of the gold frame."""
    mt = mount_of(pt); c = 0.6 * px
    def path(j, f):
        tilt = R(55) if j < 2 else R(-55)
        lap = 70 if j < 2 else 84
        a = (f - 1) * 2 * math.pi / lap + (j % 2) * math.pi
        rr = 1.7 * _tuck(f) * px
        x, y = rr * math.cos(a), rr * math.sin(a)
        z = -1.2 * px - abs(y * math.sin(tilt)) * 0.5      # tilted plane, kept in front of the face
        return (c + x, y * math.cos(tilt), z)
    _motes(tag, mt, px, "G3c", path, appear=lambda j: 15 * ([1, 3, 2, 4][j]))
    return lit_mat(f"{tag} G3c face", [(1, 0.4), (60, 0.9)])


TAKES = [("G1a", "breathing face", fx_G1a,
          ["G1's face glow = charge, then at full it", "breathes slowly (+-15%, every 3 s).", "Never static; nothing on the arm."]),
         ("G1b", "dark core", fx_G1b,
          ["The face's centre stays dark glass; a bright", "inner border round it = charge.", "Darker core, steady."]),
         ("G1c", "fills from the centre", fx_G1c,
          ["A lit square grows from the face's centre", "to its edges as charge rises, like the", "lantern's light spreading from the port."]),
         ("G2a", "two lines meet", fx_G2a,
          ["Two rim lines start at the bottom and trace", "both ways, meeting at the top at 100%.", "Then one bright segment travels slowly round."]),
         ("G2b", "double rim", fx_G2b,
          ["The outer rim line traces 0-50% charge,", "a second inner line 50-100%.", "Steady; face stays dim."]),
         ("G2c", "dashed rim", fx_G2c,
          ["Dark-green dashes round the rim light one", "by one with charge (like the lantern's", "stitches); at full a slow chase runs round."]),
         ("G3a", "erratic orbit", fx_G3a,
          ["4 pixels on uneven orbits: own radius,", "speed and wobble, never repeating.", "Within 2 px of the face; one per 25%."]),
         ("G3b", "trailing pixels", fx_G3b,
          ["Each pixel pulls a 2-pixel tail of darker", "green; slower laps than 860 G3.", "One per 25% charge; tuck in on Bridge."]),
         ("G3c", "tilted orbits", fx_G3c,
          ["2 pairs of pixels orbit on tilted planes", "round the ring, like an atom.", "One per 25% charge; tuck in on Bridge."])]

# ----------------------------------------------------------------- from here on: 860's take loop and stage
_t = _t860
exec(compile(_t[_t.index("def fp_ring_pose(fpr, f, eye):"):_t.index("START_CAM, START_FRAME")], _s860, "exec"), globals())
START_CAM, START_FRAME, WORLD_RGB, SUN = "Cam G1a - first person", 75, (0.16, 0.2, 0.28), 2.2
_stage = _t[_t.index("# ------------------------------------------------------------------ stage, light, bloom, save"):]
exec(compile(_stage, _s860, "exec"), globals())
