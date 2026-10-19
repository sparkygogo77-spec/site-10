# Pass 865: ring glow in first person, round 3: 864 G3 variations (PC chat, 2026-10-18).
# Why: J rated 864 G3a erratic orbit, G3b trailing pixels and G3c tilted orbits IMPROVE with no note and dropped G1/G2;
#   he picked "3 variations of each" (DECISIONS, decision manager, next-864). The primed Shift glow (handover Q24) waits
#   on this pick.
# Kept from 860/864: nothing on the arm or sleeve, no panes or shafts near the eye, small emissive pixels, saturated green
#   capped at 0.6 x 860 (no mint), every pixel within ~2 px of the face and in front of the gold frame so it reads from the
#   ring's back sides (what the first-person eye sees), one pixel per 25% charge, all tuck in when the Bridge is used,
#   motion one way only (the flare rule), never static but not fast.
# Timeline (every take, 864's): 1-60 charge 0 -> 100%; 60-90 hold; 90-120 Bridge used.
# Takes (each a sibling of its parent, built differently):
#   G3a1 drifting radii: 4 pixels whose orbit radius slowly breathes 1.3-2.0 px on its own beat, so they pass each other.
#   G3a2 darting: pixels rest, then dash a quarter-lap with an eased hop, each on its own uneven timing.
#   G3a3 wandering loops: each pixel traces its own rose-curve loop round the face (petals in and out), never a circle.
#   G3b1 comet tails: 2 pixels, each with a 4-pixel tail fading to nothing (emit 2.0 -> 0.2).
#   G3b2 spiral in: 4 tailed pixels spiral from 2.3 px in to 1.4 px as the charge rises, then hold that orbit.
#   G3b3 stretching tails: the lap speed swells and eases; the tails stretch when fast and close up when slow.
#   G3c1 three planes: 3 orbits tilted 0 and +-60 degrees, one pixel each, a fourth joins the flat one at 100%.
#   G3c2 precessing: 864 G3c's two tilted orbits, with the tilt axis turning slowly round the face.
#   G3c3 atom with a heart: 864 G3c plus one dim pixel at the face's centre that pulses with the laps.
# Cameras "Cam <code> - first person" / "- third person", "Cam all". Builds LanternLive\combat\ring_glow3.blend.
import math, os
import bpy
import numpy as np


def _find(name):
    names = []
    if os.environ.get("KL_REPO"):
        names.append(os.path.join(os.environ["KL_REPO"], "docs", "blender", "blender_updates"))
    if "__file__" in globals():
        names.append(os.path.dirname(os.path.abspath(__file__)))
    names.append(os.path.join(os.path.expanduser("~"), "Documents", "LanternLive", "site-10", "docs", "blender", "blender_updates"))
    names.append("/home/claude/site-10/docs/blender/blender_updates")
    for d in names:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("865 needs " + name + " next to it (or KL_REPO set)")


_s864 = _find("864_ring_glow2.update.py")
_t864 = open(_s864, encoding="utf-8").read()
exec(compile(_t864[:_t864.index("TAKES = [")], _s864, "exec"), globals())     # 860 rig + 864 helpers and G3 builders
SCENE_NAME = "Ring Glow 3"
OUT_REL = "combat/ring_glow3.blend"
OUT = os.path.join(FOLDER, *OUT_REL.split("/"))
_old = bpy.data.scenes.get(SCENE_NAME)
if _old is not None and _old != scene:
    bpy.data.scenes.remove(_old)
scene.name = SCENE_NAME
rng = np.random.default_rng(865)


def _face(tag, code):
    return lit_mat(f"{tag} {code} face", [(1, 0.4), (60, 0.9)])


def _ease(t):
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------- G3a: erratic orbit, three ways
def fx_G3a1(tag, pt, px, eye_obj):
    """Radii breathe 1.3-2.0 px, each on its own slow beat (37-61 ticks), laps 54-76 ticks, so pixels overtake inside
    and outside each other."""
    mt = mount_of(pt); c = 0.6 * px
    lap = [62, 54, 76, 68]; beat = [41, 53, 37, 61]; ph = [0.0, 1.6, 3.3, 4.8]; dz = [0.7, 0.9, 0.6, 0.8]
    def path(j, f):
        a = (f - 1) * 2 * math.pi / lap[j] + ph[j]
        rr = (1.65 + 0.35 * math.sin(2 * math.pi * f / beat[j] + j)) * _tuck(f) * px
        return (c + rr * math.cos(a), rr * math.sin(a), -dz[j] * px)
    _motes(tag, mt, px, "G3a1", path)
    return _face(tag, "G3a1")


def fx_G3a2(tag, pt, px, eye_obj):
    """Each pixel rests, then dashes a quarter lap in 6 ticks (eased), on an uneven schedule of its own (rests 9-23
    ticks); a radius of 1.5-1.9 px."""
    mt = mount_of(pt); c = 0.6 * px
    rad = [1.85, 1.5, 1.7, 1.6]
    sched = []
    for j in range(4):
        t, s, ang = 1, [], j * math.pi / 2
        r2 = np.random.default_rng(8650 + j)
        while t < FRAME_END + 30:
            rest = int(r2.integers(9, 24))
            s.append((t + rest, ang)); ang += math.pi / 2; t += rest + 6
        sched.append(s)
    def ang_at(j, f):
        a = j * math.pi / 2
        for start, a0 in sched[j]:
            if f < start:
                return a0
            if f < start + 6:
                return a0 + math.pi / 2 * _ease((f - start) / 6)
            a = a0 + math.pi / 2
        return a
    def path(j, f):
        a = ang_at(j, f)
        rr = rad[j] * _tuck(f) * px
        return (c + rr * math.cos(a), rr * math.sin(a), -0.8 * px)
    _motes(tag, mt, px, "G3a2", path)
    return _face(tag, "G3a2")


def fx_G3a3(tag, pt, px, eye_obj):
    """Rose-curve loops: r = 1.55 + 0.4 sin(k a) with k = 3, 5, 4, 7 petals, each pixel at its own lap (60-88 ticks)."""
    mt = mount_of(pt); c = 0.6 * px
    k = [3, 5, 4, 7]; lap = [72, 60, 88, 66]; ph = [0.0, 1.2, 2.9, 4.4]
    def path(j, f):
        a = (f - 1) * 2 * math.pi / lap[j] + ph[j]
        rr = (1.55 + 0.4 * math.sin(k[j] * a)) * _tuck(f) * px
        return (c + rr * math.cos(a), rr * math.sin(a), -(0.75 + 0.15 * math.cos(k[j] * a)) * px)
    _motes(tag, mt, px, "G3a3", path)
    return _face(tag, "G3a3")


# ----------------------------------------------------------------- G3b: trailing pixels, three ways
def _tailed(tag, mt, px, code, path_lag, lags, sizes, emits, n=4, appear=None):
    for i, (lag, s, e) in enumerate(zip(lags, sizes, emits)):
        _motes(tag, mt, px, code if i == 0 else f"{code} tail{i}", path_lag(lag), n=n, size=s, emit=e, appear=appear)


def fx_G3b1(tag, pt, px, eye_obj):
    """2 pixels opposite each other at 1.8 px, a lap per 96 ticks, each with a 4-pixel tail fading 2.0 -> 0.2; they
    appear at 25% and 50%; the tails grow in at 75% and 100%."""
    mt = mount_of(pt); c = 0.6 * px
    def path_lag(lag):
        def path(j, f):
            a = (f - 1) * 2 * math.pi / 96 + j * math.pi - lag
            rr = 1.8 * _tuck(f) * px
            return (c + rr * math.cos(a), rr * math.sin(a), -0.8 * px)
        return path
    lags = [0.0, 0.22, 0.44, 0.66, 0.88]
    for i, lag in enumerate(lags):
        size = [0.17, 0.15, 0.13, 0.11, 0.09][i]
        emit = [2.0, 1.2, 0.7, 0.4, 0.2][i]
        appear = (lambda j: 15 * (j + 1)) if i == 0 else (lambda j, i=i: 45 if i <= 2 else 60)
        _motes(tag, mt, px, "G3b1" if i == 0 else f"G3b1 tail{i}", path_lag(lag), n=2, size=size, emit=emit, appear=appear)
    return _face(tag, "G3b1")


def fx_G3b2(tag, pt, px, eye_obj):
    """4 tailed pixels on a spiral: the radius shrinks 2.3 -> 1.4 px as the charge fills (ticks 1-60), then holds; a lap
    per 80 ticks; 2-pixel tails like 864 G3b."""
    mt = mount_of(pt); c = 0.6 * px
    def path_lag(lag):
        def path(j, f):
            a = (f - 1) * 2 * math.pi / 80 + j * math.pi / 2 - lag
            rr = (2.3 - 0.9 * _ease(min(1.0, max(0.0, (f - 1) / 59)))) * _tuck(f) * px
            return (c + rr * math.cos(a), rr * math.sin(a), -0.8 * px)
        return path
    _tailed(tag, mt, px, "G3b2", path_lag, [0.0, 0.3, 0.6], [0.17, 0.13, 0.1], [2.0, 0.9, 0.4])
    return _face(tag, "G3b2")


def fx_G3b3(tag, pt, px, eye_obj):
    """The lap speed swells and eases (one swell per 40 ticks); the tail pixels sit a fixed time behind, so the tail
    stretches when fast and closes up when slow. Always the same direction."""
    mt = mount_of(pt); c = 0.6 * px
    def phase(f):
        return (f - 1) * 2 * math.pi / 90 + 0.9 * math.sin(2 * math.pi * f / 40)    # speed 0.03 .. 0.21 rad per tick
    def path_lag(dt):
        def path(j, f):
            a = phase(f - dt) + j * math.pi / 2
            rr = 1.8 * _tuck(f) * px
            return (c + rr * math.cos(a), rr * math.sin(a), -0.8 * px)
        return path
    _tailed(tag, mt, px, "G3b3", path_lag, [0.0, 2.0, 4.0], [0.17, 0.13, 0.1], [2.0, 0.9, 0.4])
    return _face(tag, "G3b3")


# ----------------------------------------------------------------- G3c: tilted orbits, three ways
def _orbit(c, px, f, rr, tilt, lap, ph, axis_turn=0.0, z0=1.2):
    a = (f - 1) * 2 * math.pi / lap + ph
    x, y = rr * math.cos(a), rr * math.sin(a)
    y2 = y * math.cos(tilt)
    z = -z0 * px - abs(y * math.sin(tilt)) * 0.5                       # tilted plane, kept in front of the face
    ca, sa = math.cos(axis_turn), math.sin(axis_turn)
    return (c + x * ca - y2 * sa, x * sa + y2 * ca, z)


def fx_G3c1(tag, pt, px, eye_obj):
    """3 orbits at 1.7 px: flat, tilted +60 and -60 degrees (laps 70, 78, 86); one pixel each at 25/50/75%, and a fourth
    joins the flat orbit opposite the first at 100%."""
    mt = mount_of(pt); c = 0.6 * px
    plan = [(0.0, 70, 0.0), (R(60), 78, 1.0), (R(-60), 86, 2.0), (0.0, 70, math.pi)]
    def path(j, f):
        tilt, lap, ph = plan[j]
        return _orbit(c, px, f, 1.7 * _tuck(f) * px, tilt, lap, ph)
    _motes(tag, mt, px, "G3c1", path)
    return _face(tag, "G3c1")


def fx_G3c2(tag, pt, px, eye_obj):
    """864 G3c's two orbits (tilted +-55, laps 70 and 84), with the axis they tilt about turning once per 120 ticks."""
    mt = mount_of(pt); c = 0.6 * px
    def path(j, f):
        tilt = R(55) if j < 2 else R(-55)
        lap = 70 if j < 2 else 84
        return _orbit(c, px, f, 1.7 * _tuck(f) * px, tilt, lap, (j % 2) * math.pi, axis_turn=(f - 1) * 2 * math.pi / 120)
    _motes(tag, mt, px, "G3c2", path, appear=lambda j: 15 * ([1, 3, 2, 4][j]))
    return _face(tag, "G3c2")


def fx_G3c3(tag, pt, px, eye_obj):
    """864 G3c, plus a heart: one dim pixel just in front of the face's centre that pulses (0.5 -> 1.1) each time a
    pixel crosses the top (about every 35 ticks)."""
    mt = mount_of(pt); c = 0.6 * px
    def path(j, f):
        tilt = R(55) if j < 2 else R(-55)
        lap = 70 if j < 2 else 84
        return _orbit(c, px, f, 1.7 * _tuck(f) * px, tilt, lap, (j % 2) * math.pi)
    _motes(tag, mt, px, "G3c3", path, appear=lambda j: 15 * ([1, 3, 2, 4][j]))
    keys_ = [(1, 0.0), (14, 0.0)]
    for f in range(15, FRAME_END + 1, 5):
        keys_.append((f, 0.5 + 0.6 * max(0.0, math.cos(2 * math.pi * (f - 15) / 35)) ** 4))
    hm = lit_mat(f"{tag} G3c3 heart", keys_)
    heart = link(bpy.data.objects.new(f"{tag} G3c3 heart", pixel_mesh(hm, 0.15 * px))); heart.parent = mt
    key(heart, 1, loc=(c, 0.0, -1.15 * px))
    return _face(tag, "G3c3")


TAKES = [("G3a1", "drifting radii", fx_G3a1,
          ["G3a's 4 pixels; each orbit's radius breathes", "1.3-2.0 px on its own beat, so they pass", "inside and outside each other."]),
         ("G3a2", "darting", fx_G3a2,
          ["Pixels rest, then dash a quarter lap", "with an eased hop, each on its own", "uneven timing. One way only."]),
         ("G3a3", "wandering loops", fx_G3a3,
          ["Each pixel traces its own rose-curve", "loop round the face (3-7 petals),", "never a plain circle."]),
         ("G3b1", "comet tails", fx_G3b1,
          ["2 pixels, each with a 4-pixel tail", "fading to nothing; the tails grow in", "at 75% and 100% charge."]),
         ("G3b2", "spiral in", fx_G3b2,
          ["4 tailed pixels spiral in from 2.3 to", "1.4 px as the charge fills,", "then hold that orbit."]),
         ("G3b3", "stretching tails", fx_G3b3,
          ["The lap speed swells and eases; the", "tails stretch when fast and close up", "when slow. Same direction always."]),
         ("G3c1", "three planes", fx_G3c1,
          ["3 orbits: flat and tilted +-60 degrees,", "one pixel each; a fourth joins the", "flat orbit at 100%."]),
         ("G3c2", "precessing", fx_G3c2,
          ["864 G3c's two tilted orbits, with the", "tilt axis turning slowly round", "the face (one turn per 6 s)."]),
         ("G3c3", "atom with a heart", fx_G3c3,
          ["864 G3c plus one dim pixel at the", "face's centre that pulses each time", "a pixel crosses the top."])]

# ----------------------------------------------------------------- 864's take loop and stage (which are 860's)
_tail = _t864[_t864.index("# ----------------------------------------------------------------- from here on: 860's take loop and stage"):]
_tail = _tail.replace('"Cam G1a - first person", 75', '"Cam G3a1 - first person", 75')
assert "Cam G3a1 - first person" in _tail
exec(compile(_tail, _s864, "exec"), globals())
