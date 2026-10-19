"""Pass v2.0101 voxels: the reliquary round 2, from J's 612 picks (PC chat, 2026-10-19).

J on 612: KEEP R2a gold arms, R4a spinning rings, R4b gyroscope; IMPROVE R1c gold foot, R6c hourglass, R2b red, with
"Cant see the port on any of these, maybe want darker red for lantern red in this visual so it looks near metallic
like the dark lantern". So every take gets a port 1.5x the 612 size, raised off the body and lit (a glowing ring and a
bright socket), and each design comes twice: 1 = green as kept, 2 = near-black metallic crimson with polished gold
(R2b: both crimson). The crimson turns the ribbed and plated glass into dark polished metal and keeps only the smoke
glass see-through, so the core shows through a window; the gold stays as it was.
"""
import colorsys
import math
import numpy as np
import pixel_lanterns6 as P6
from pixel_lanterns6 import G, grid, circle, band, rod, EMPTY, GOLD, GOLD_DK, GOLD_ENG, SILVER, HOLE, SOCKET, SMOKE, RIB, PLATE
from pixel_lanterns7 import core, studs, coarsen_glass, CORE
import pixel_lanterns10 as P10
from pixel_lanterns10 import BRONZE
import pixel_lanterns11 as P11
from pixel_lanterns11 import Z0R, Z1R
import pixel_lanterns12 as P12
from pixel_lanterns12 import gold_wire, gem_crown, gold_net, arms_pts, body_r

P10.CORPS["k"] = ("dark red", 0.985, (0.62, 0.0, 0.03), (0.95, 0.12, 0.03))    # near-black crimson, a hot red core
STYLE = {"dark": False}
PORT_SCALE = 1.5                                        # 612's ports were pr 1.3-1.5: "Cant see the port"

# ------------------------------------------------------------------ dark metallic crimson (guarded: reloads keep the original)
_base_face = getattr(P6, "_p13_face", P6.face_colour)
_base_glow = getattr(P6, "_p13_glow", P6.glow_weight)
P6._p13_face, P6._p13_glow = _base_face, _base_glow


def face_colour(pid, i, j, k, n, c):
    col, kind = _base_face(pid, i, j, k, n, c)
    if not STYLE["dark"] or pid not in (SMOKE, RIB, PLATE):
        return col, kind
    r, g, b = (np.clip(col, 0, 255) / 255.0).tolist()
    _, s, v = colorsys.rgb_to_hsv(r, g, b)
    v = 0.16 + 0.55 * v                                  # near-black
    if n[2] > 0:
        v *= 1.7                                         # lit lip on top, like the gold
    elif n[2] < 0:
        v *= 0.5
    az = math.degrees(math.atan2(c[1], c[0]))
    if pid != SMOKE and abs((az + 110.0 + 180) % 360 - 180) < 8:
        v = min(1.0, v * 2.4)                            # the gold's specular column, in crimson: reads as metal
    col = np.array(colorsys.hsv_to_rgb(0.985, max(s, 0.88), min(v, 1.0))) * 255.0
    return col, (4 if pid == SMOKE else 1)               # ribs and plates opaque polished metal; smoke stays a window


def glow_weight(pid, i, j, k, c, pz, span):
    w = _base_glow(pid, i, j, k, c, pz, span)
    if pid == SOCKET:
        return 3.6                                       # the port's heart and ring: lit
    if STYLE["dark"] and pid in (RIB, PLATE):
        return 0.0                                       # metal doesn't glow
    if STYLE["dark"] and pid == SMOKE:
        return w * 0.7
    return w


P6.face_colour = face_colour
P6.glow_weight = glow_weight


# ------------------------------------------------------------------ the port, 1.5x, raised and lit
def lit_port(part, X, Y, Z, pz, pr=1.5, lift=0.5):
    """612's port at PORT_SCALE x pr, stepped `lift` px further out, with a glowing ring between the knurled steps and a
    bright square socket. Sits on the front of whatever is there at pz (over the old port if there is one)."""
    pr = pr * PORT_SCALE
    col = (np.abs(X) < pr) & (np.abs(Z - pz) < pr) & (part > 0)
    ys = np.where(col, Y, np.inf)
    fy = float(ys.min()) if np.isfinite(ys.min()) else -5.0
    rr = np.hypot(X, Z - pz)
    for rad, out_, pid in ((pr, 0.5, GOLD_DK), (pr * 0.93, 0.75, GOLD), (pr * 0.86, 1.0, GOLD_DK),
                           (pr * 0.79, 1.25, GOLD), (pr * 0.7, 1.25, GOLD)):
        part[(rr <= rad) & (Y >= fy - out_ - lift) & (Y <= fy + 1.0)] = pid
    part[(rr <= pr * 0.86) & (rr > pr * 0.79) & (Y >= fy - 1.25 - lift) & (Y < fy - 1.0 - lift)] = SOCKET   # glowing ring
    face = (rr <= pr * 0.7) & (Y >= fy - 1.5 - lift) & (Y < fy - 1.25 - lift)
    part[face] = GOLD
    part[face & (rr > pr * 0.6) & (rr <= pr * 0.66)] = GOLD_ENG
    half = min(5 * G, pr * 0.42)
    sq = np.maximum(np.abs(X), np.abs(Z - pz))
    f0 = fy - lift
    part[(sq <= half + G) & (Y >= f0 - 1.5) & (Y < f0 - 1.0)] = HOLE
    part[(sq <= half) & (sq > half - G) & (Y >= f0 - 1.75) & (Y < f0 - 1.25)] = GOLD
    part[(sq <= half - 2 * G) & (Y >= f0 - 1.75) & (Y < f0 - 1.0)] = SOCKET
    for sx, sz in ((-1, 1), (1, -1)):
        part[(np.hypot(X - sx * pr * 0.55, Z - pz - sz * pr * 0.42) <= 0.25) & (Y >= f0 - 1.75) & (Y < f0 - 1.5)] = SILVER
    return fy


def _pz_of(part, Z):
    """Where the core is (612 put the port there)."""
    zs = Z[part == CORE]
    return float(np.median(zs)) if zs.size else (Z0R + Z1R) / 2


def _no_port(*a, **k):
    return None


def _with_port(fn, pr=1.5):
    """Build fn with its old small port left off, then put the lit port where it was (612 stacked them: a drum)."""
    def b(X, Y, Z):
        saved = (P6.port, P11.small_port, P12.small_port)
        P6.port = P11.small_port = P12.small_port = _no_port
        try:
            out = fn(X, Y, Z)
        finally:
            P6.port, P11.small_port, P12.small_port = saved
        part, pz = out if isinstance(out, tuple) else (out, None)
        pz = _pz_of(part, Z) if pz is None else pz
        lit_port(part, X, Y, Z, pz, pr=pr)
        return part, pz
    return b


# ------------------------------------------------------------------ IMPROVE: R1c gold foot, more gold detail
def r1c_plus(X, Y, Z):
    part, pz = P12.r1c_gold_foot(X, Y, Z)
    zs = Z0R + (Z1R - Z0R) * 0.78                                   # an engraved gold collar under the neck
    rr = np.hypot(X, Y)
    want = body_r(zs) + 0.35
    collar = (np.abs(rr - want) <= 0.4) & (Z > zs - 0.9) & (Z <= zs + 0.9)
    part[collar] = GOLD
    ang = np.arctan2(Y, X)
    part[collar & (np.abs(((ang * 8 / math.pi) % 1) - 0.5) < 0.12)] = GOLD_ENG
    gems = [((want + 0.3) * math.cos(a), (want + 0.3) * math.sin(a), zs) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
    studs(part, X, Y, Z, gems, r=0.38, pid=SOCKET)                   # lit gems round the collar
    for sx in (-1, 1):                                               # gold wire climbing from the foot to the collar
        gold_wire(part, X, Y, Z, arms_pts(sx)[4:12], wrap=0.7, turns=6)
    return part, pz


# ------------------------------------------------------------------ IMPROVE: R6c hourglass, a richer gold waist and frame
def r6c_plus(X, Y, Z):
    part, pz = P12.r6c_hourglass(X, Y, Z)
    band(part, X, Y, Z, circle(X, Y, 2.5), 11.8, 14.2, GOLD, "dots")       # a heavier waist
    band(part, X, Y, Z, circle(X, Y, 2.7), 12.7, 13.3, GOLD_ENG)
    for k in range(4):                                                     # gold wire wound up the bronze posts
        a = math.radians(45 + 90 * k)
        cx, cy = 4.8 * math.cos(a), 4.8 * math.sin(a)
        pts = [(cx, cy, z) for z in np.linspace(1.5, 24.5, 12)]
        gold_wire(part, X, Y, Z, pts, r_wire=0.22, wrap=0.6, turns=9)
    for zc in (3.0, 23.0):                                                 # gold caps where the bulbs meet the frame
        band(part, X, Y, Z, circle(X, Y, 2.2), zc - 0.5, zc + 0.5, GOLD_DK, "zig")
    return part, pz


# ------------------------------------------------------------------ R2b2: gold arms and shoulders, all crimson
def r2b_shoulders(X, Y, Z):
    part, pz = P12.r2a_gold_arms(X, Y, Z)
    gold_net(part, X, Y, Z, Z0R + 9.0, Z1R - 1.4, body_r, cell=2.0)
    gem_crown(part, X, Y, Z, Z1R + 1.75, n=8, r0=1.8, h=1.2)
    return part, pz


_r2a = _with_port(P12.r2a_gold_arms, pr=1.87)
_r4a = _with_port(P12.r4a_three_rings)
_r4b = _with_port(P12.r4b_gyroscope)
_r1c = _with_port(r1c_plus)
_r6c = _with_port(r6c_plus, pr=1.4)

DESIGNS = {"R2a1": ("Gold arms: lit port", _r2a, "g"), "R2a2": ("Gold arms: dark crimson", _r2a, "k"),
           "R4a1": ("Three spinning rings: lit port", _r4a, "g"), "R4a2": ("Three spinning rings: dark crimson", _r4a, "k"),
           "R4b1": ("Gyroscope: lit port", _r4b, "g"), "R4b2": ("Gyroscope: dark crimson", _r4b, "k"),
           "R1c1": ("Gold foot and collar: lit port", _r1c, "g"), "R1c2": ("Gold foot and collar: dark crimson", _r1c, "k"),
           "R6c1": ("Hourglass, gold waist: lit port", _r6c, "g"), "R6c2": ("Hourglass, gold waist: dark crimson", _r6c, "k"),
           "R2b1": ("Gold arms: crimson glass window", _r2a, "k"), "R2b2": ("Gold arms and shoulders: crimson", _with_port(r2b_shoulders, pr=1.87), "k")}

MOVING = {c: P12.MOVING[c[:3]] for c in DESIGNS if c[:3] in P12.MOVING}
MID = P12.MID


def build(code):
    X, Y, Z = grid()
    corps = DESIGNS[code][2]
    P10.STYLE["hue"] = P10.CORPS[corps][1]
    STYLE["dark"] = corps == "k"
    return DESIGNS[code][1](X, Y, Z)


def quads(part, pz):
    return P12.quads(part, pz)


model_boxes = P12.model_boxes
