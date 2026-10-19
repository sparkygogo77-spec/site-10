"""Pass v2.0102 voxels: reliquary round 3, v2.0101 with a bigger lit port and darker crimson (PC chat, 2026-10-19).

J, after v2.0101 was built: build the next pass now with the lit port BIGGER on every take, the KEEPs (R2a, R4a, R4b)
too, and the red near-black crimson ("darker red ... near metallic like the dark lantern", 612). He picked the port
2.25x the 612 size (v2.0101 had 1.5x), raised further off the body with a brighter ring, and 1 green + 1 crimson take
of each design. R2b (612's red IMPROVE) keeps its crimson glass window as the crimson take; its green take is the gold
arms with gold shoulders.
"""
import colorsys
import math
import numpy as np
import pixel_lanterns6 as P6
from pixel_lanterns6 import SMOKE, RIB, PLATE, SOCKET
import pixel_lanterns10 as P10
import pixel_lanterns13 as P13

P13.PORT_SCALE = 2.25                                   # v2.0101 had 1.5x and J asked for bigger
P10.CORPS["k"] = ("dark red", 0.985, (0.62, 0.0, 0.03), (1.0, 0.16, 0.04))     # glow stays hot: only the body darkens
STYLE = P13.STYLE
PORT_LIFT = 1.0                                         # v2.0101 lifted 0.5 px: raise it so it reads side-on too

# ------------------------------------------------------------------ the port: bigger and raised (guarded for reloads)
_base_port = getattr(P13, "_p14_port", P13.lit_port)
P13._p14_port = _base_port


def lit_port(part, X, Y, Z, pz, pr=1.5, lift=PORT_LIFT):
    return _base_port(part, X, Y, Z, pz, pr=pr, lift=lift)


P13.lit_port = lit_port

# ------------------------------------------------------------------ near-black metallic crimson (darker than v2.0101)
_base_face = P13._base_face                             # P6's original, kept by v2.0101's guard
_base_glow = P13._base_glow


def face_colour(pid, i, j, k, n, c):
    col, kind = _base_face(pid, i, j, k, n, c)
    if STYLE["dark"] and pid == SOCKET:
        return np.array([255.0, 46.0, 30.0]), kind      # the hue shift left the ring dull pink: make it hot red
    if not STYLE["dark"] or pid not in (SMOKE, RIB, PLATE):
        return col, kind
    r, g, b = (np.clip(col, 0, 255) / 255.0).tolist()
    _, s, v = colorsys.rgb_to_hsv(r, g, b)
    v = 0.09 + 0.38 * v                                  # near-black (v2.0101: 0.16 + 0.55 v)
    if n[2] > 0:
        v *= 1.8                                         # lit lip on top
    elif n[2] < 0:
        v *= 0.45
    az = math.degrees(math.atan2(c[1], c[0]))
    if pid != SMOKE and abs((az + 110.0 + 180) % 360 - 180) < 8:
        v = min(1.0, v * 2.8)                            # the specular column: what makes it read as metal
    col = np.array(colorsys.hsv_to_rgb(0.985, max(s, 0.92), min(v, 1.0))) * 255.0
    return col, (4 if pid == SMOKE else 1)


def glow_weight(pid, i, j, k, c, pz, span):
    if pid == SOCKET:
        return 4.6                                       # the bigger port's ring and socket: brighter (v2.0101: 3.6)
    return P13.glow_weight(pid, i, j, k, c, pz, span)


P6.face_colour = face_colour
P6.glow_weight = glow_weight

# ------------------------------------------------------------------ the takes: 1 green, 1 crimson of each design
_w = P13._with_port
_r2a = _w(P13.P12.r2a_gold_arms, pr=1.87)
_r2s = _w(P13.r2b_shoulders, pr=1.87)
_r4a = _w(P13.P12.r4a_three_rings)
_r4b = _w(P13.P12.r4b_gyroscope)
_r1c = _w(P13.r1c_plus)
_r6c = _w(P13.r6c_plus, pr=1.4)

DESIGNS = {"R2a1": ("Gold arms: big lit port", _r2a, "g"), "R2a2": ("Gold arms: near-black crimson", _r2a, "k"),
           "R4a1": ("Three spinning rings: big lit port", _r4a, "g"), "R4a2": ("Three spinning rings: near-black crimson", _r4a, "k"),
           "R4b1": ("Gyroscope: big lit port", _r4b, "g"), "R4b2": ("Gyroscope: near-black crimson", _r4b, "k"),
           "R1c1": ("Gold foot and collar: big lit port", _r1c, "g"), "R1c2": ("Gold foot and collar: near-black crimson", _r1c, "k"),
           "R6c1": ("Hourglass, gold waist: big lit port", _r6c, "g"), "R6c2": ("Hourglass, gold waist: near-black crimson", _r6c, "k"),
           "R2b1": ("Gold arms and shoulders: big lit port", _r2s, "g"), "R2b2": ("Gold arms: crimson glass window", _r2a, "k")}

MOVING = {c: P13.P12.MOVING[c[:3]] for c in DESIGNS if c[:3] in P13.P12.MOVING}
MID = P13.MID


def build(code):
    X, Y, Z = P6.grid()
    corps = DESIGNS[code][2]
    P10.STYLE["hue"] = P10.CORPS[corps][1]
    STYLE["dark"] = corps == "k"
    return DESIGNS[code][1](X, Y, Z)


quads = P13.quads
model_boxes = P13.model_boxes
