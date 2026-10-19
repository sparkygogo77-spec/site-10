"""Pass v2.0103 voxels: reliquary round 4, the designs developed (PC chat, 2026-10-19).

J on v2.0102: "ports are bigger slightly better on the small ones but it shouldnt have been the main focus of the new
round". He picked "Develop the designs" and "All green": two new directions for each 612 pick, the 2.25x lit port kept
on every take (pixel_lanterns14) but no longer the subject.
  KEEP    R2a gold arms        -> R2d winged arms, R2e four arms on claw feet
  KEEP    R4a spinning rings   -> R4d rings round a gilded cage, R4e four rings on a tall claw stand
  KEEP    R4b gyroscope        -> R4f gyroscope with a gem crown, R4g wide gimbals held by gold arms
  IMPROVE R1c gold foot        -> R1d tiered gold pedestal, R1e fully gilded (plate, collar, crown, chains)
  IMPROVE R6c hourglass        -> R6d the frame turns round the glass, R6e hourglass in a cage of gold rings
  IMPROVE R2b gold arms        -> R2f cathedral (arms, net, crown, claws), R2g arms raising a gold halo
"""
import math
import numpy as np
import pixel_lanterns6 as P6
from pixel_lanterns6 import grid, circle, ngon, band, stepped, rod, ring_xz, EMPTY, GOLD, GOLD_DK, GOLD_ENG
from pixel_lanterns7 import core, studs, coarsen_glass, fin, CORE
import pixel_lanterns10 as P10
from pixel_lanterns10 import BRONZE, tilted_ring
import pixel_lanterns11 as P11
from pixel_lanterns11 import reliquary, amph_r, Z0R, Z1R
import pixel_lanterns12 as P12
from pixel_lanterns12 import gold_net, gold_wire, gem_crown, claw_feet, arms_pts, body_r, ring_part, small_amphora, MID, PZ4
import pixel_lanterns13 as P13
import pixel_lanterns14 as P14                          # the 2.25x lit port, raised, hot ring

STYLE = P13.STYLE
_w = P13._with_port


def _gold_arms(part, X, Y, Z, sx, turn=0.0, z1=Z1R):
    """612 R2a's gilded, wire-wrapped arm, swung `turn` degrees round the body."""
    a = math.radians(turn)
    pts = [(x * math.cos(a), x * math.sin(a), z) for x, _, z in arms_pts(sx, z1=z1)]
    rod(part, X, Y, Z, pts, 0.6, GOLD)
    gold_wire(part, X, Y, Z, pts[1:13], wrap=0.75, turns=8)
    for i in (3, 6, 9):
        studs(part, X, Y, Z, [pts[i]], r=0.75, pid=GOLD_DK)
    return pts


# ------------------------------------------------------------------ KEEP R2a gold arms, two ways further
def r2d_winged(X, Y, Z):
    part, pz = P12.r2a_gold_arms(X, Y, Z)
    for sx in (-1, 1):                                  # open gold wings: five feather spars fanning back from the shoulder
        pts = arms_pts(sx)
        root = (pts[9][0], 0.6, pts[9][2])
        tips = [(sx * 7.4, 2.6, 7.5), (sx * 8.8, 2.8, 11.5), (sx * 9.4, 3.0, 15.5), (sx * 8.9, 2.8, 19.5), (sx * 6.6, 2.0, 23.0)]
        for k, tip in enumerate(tips):
            mid = tuple(root[d] + (tip[d] - root[d]) * 0.55 + (0.0, 0.6, 0.3)[d] for d in range(3))
            rod(part, X, Y, Z, [root, mid, tip], 0.34 if k % 2 else 0.28, GOLD if k % 2 else GOLD_DK)
            studs(part, X, Y, Z, [tip], r=0.42, pid=CORE)
        rod(part, X, Y, Z, [root] + [tuple(root[d] + (t[d] - root[d]) * 0.55 for d in range(3)) for t in tips], 0.24, GOLD)
    return part, pz


def r2e_four_arms(X, Y, Z):
    part, pz = P10.n2_reliquary(X, Y, Z)
    for turn in (35.0, -35.0):                          # four gilded arms at the corners, the front left open for the port
        for sx in (-1, 1):
            _gold_arms(part, X, Y, Z, sx, turn=turn if sx > 0 else -turn)
    claw_feet(part, X, Y, Z, n=4, r0=3.6)
    band(part, X, Y, Z, circle(X, Y, 2.9), Z1R - 1.0, Z1R - 0.2, GOLD, "zig")   # a collar the hands grip
    return part, pz


# ------------------------------------------------------------------ KEEP R4a spinning rings, two ways further
def _floating_gilded(X, Y, Z, seed, crown=False, net=True):
    part, pz = P12._floating(X, Y, Z, seed)
    if net:
        gold_net(part, X, Y, Z, Z0R + 2.0 + 8.0, Z1R + 2.0 - 1.2, lambda z: body_r(z - 2.0), cell=2.0)
    if crown:
        gem_crown(part, X, Y, Z, Z1R + 2.0 + 0.4, n=8, r0=2.0, h=1.4)
    return part, pz


def r4d_gilded_cage(X, Y, Z):
    return _floating_gilded(X, Y, Z, 1341)


def r4e_tall_stand(X, Y, Z):
    part, pz = P12._floating(X, Y, Z, 1342)
    claw_feet(part, X, Y, Z, n=4, r0=3.2)
    for k in range(4):                                  # four gold posts rise from the foot to cradle the floating body
        a = math.radians(45 + 90 * k)
        c, s = math.cos(a), math.sin(a)
        rod(part, X, Y, Z, [(3.0 * c, 3.0 * s, 1.5), (3.6 * c, 3.6 * s, 4.0), (2.6 * c, 2.6 * s, 6.2)], 0.35, GOLD)
        studs(part, X, Y, Z, [(2.6 * c, 2.6 * s, 6.2)], r=0.45, pid=CORE)
    return part, pz


# ------------------------------------------------------------------ KEEP R4b gyroscope, two ways further
def r4f_crowned_gyro(X, Y, Z):
    return _floating_gilded(X, Y, Z, 1343, crown=True, net=False)


def r4g_held_gyro(X, Y, Z):
    part, pz = P12._floating(X, Y, Z, 1344)
    for sx in (-1, 1):                                  # gold arms rise from the foot to the outer gimbal's pivots
        pts = [(sx * 3.6, 0.0, 1.2), (sx * 6.2, 0.0, 4.0), (sx * 8.6, 0.0, 8.0), (sx * 8.9, 0.0, PZ4 - 0.6)]
        rod(part, X, Y, Z, pts, 0.5, GOLD)
        gold_wire(part, X, Y, Z, pts, wrap=0.6, turns=6)
        studs(part, X, Y, Z, [(sx * 8.9, 0.0, PZ4)], r=0.75, pid=GOLD_DK)
    return part, pz


# ------------------------------------------------------------------ IMPROVE R1c gold foot, redesigned
def r1d_pedestal(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 1311, float_gap=2.0)       # lifted 2 px onto a tiered gold pedestal
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.4 + g), Z0R + 2.0,
            [(0.6, 0.5, GOLD, "dots"), (1.2, 0.5, GOLD_DK, None), (2.0, 0.5, GOLD, "zig")], down=True)
    claw_feet(part, X, Y, Z, n=4, r0=3.8)
    for k in range(6):                                  # gold ribs climbing the lower body
        a = math.radians(30 + 60 * k)
        pts = [((body_r(z - 2.0) + 0.35) * math.cos(a), (body_r(z - 2.0) + 0.35) * math.sin(a), z)
               for z in np.linspace(Z0R + 2.2, Z0R + 2.0 + (Z1R - Z0R) * 0.32, 8)]
        if abs(math.degrees(a) - 270) > 40:             # leave the front for the port
            rod(part, X, Y, Z, pts, 0.3, GOLD)
    core(part, 0, 0, pz, 2.9)
    return coarsen_glass(part), pz


def r1e_gilded(X, Y, Z):
    part, pz = P13.r1c_plus(X, Y, Z)                    # 612 R1c foot + v2.0101 collar and gems
    gold_net(part, X, Y, Z, Z0R + 9.5, Z1R - 3.5, body_r, cell=2.4)
    gem_crown(part, X, Y, Z, Z1R + 2.3, n=8, r0=2.0, h=1.4)
    for sx in (-1, 1):                                  # chains from the crown to the hands
        for t in np.linspace(0.05, 1, 8):
            studs(part, X, Y, Z, [(sx * (2.2 + 0.6 * math.sin(math.pi * t)), -0.5 * math.sin(math.pi * t), Z1R + 2.4 - 2.6 * t)],
                  r=0.26, pid=GOLD)
    return part, pz


# ------------------------------------------------------------------ IMPROVE R6c hourglass, redesigned
def _hourglass_glass(X, Y, Z, seeds=(1361, 1362)):
    part = np.zeros(X.shape, np.int8)
    small_amphora(part, X, Y, Z, 0.0, 0.0, 3.0, 12.4, seeds[0], scale=1.15)
    tmp = np.zeros(X.shape, np.int8)
    small_amphora(tmp, X, Y, 26.0 - Z, 0.0, 0.0, 3.0, 12.4, seeds[1], scale=1.15)
    part[tmp > 0] = tmp[tmp > 0]
    band(part, X, Y, Z, circle(X, Y, 2.5), 11.8, 14.2, GOLD, "dots")
    band(part, X, Y, Z, circle(X, Y, 2.7), 12.7, 13.3, GOLD_ENG)
    return part


def r6d_turning(X, Y, Z):
    """The glass stands still on a gold base; the frame (moving) turns slowly round it."""
    part = _hourglass_glass(X, Y, Z)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.6 + g), 1.0, [(0.8, 0.5, GOLD, None), (2.4, 0.5, GOLD_DK, "dots")], down=True)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.6 + g), 25.0, [(0.8, 0.5, GOLD, None), (2.4, 0.5, GOLD_DK, "dots")])
    ring_xz(part, X, Y, Z, 27.0, 1.0, 0.33, GOLD, axis="y")
    return coarsen_glass(part), 7.8


def r6d_frame(X, Y, Z):
    """The turning frame, built round MID (pivot at z 13): four gold-wound posts with top and bottom rings."""
    part = np.zeros(X.shape, np.int8)
    off = MID - 13.0
    for k in range(4):
        a = math.radians(45 + 90 * k)
        cx, cy = 4.8 * math.cos(a), 4.8 * math.sin(a)
        rod(part, X, Y, Z, [(cx, cy, 1.8 + off), (cx, cy, 24.2 + off)], 0.42, BRONZE)
        gold_wire(part, X, Y, Z, [(cx, cy, z + off) for z in np.linspace(2.0, 24.0, 12)], r_wire=0.22, wrap=0.6, turns=9)
        studs(part, X, Y, Z, [(cx, cy, 13.0 + off)], r=0.6, pid=CORE)
    for zc in (1.6, 24.4):
        ring_xz(part, X, Y, Z, zc + off, 4.8, 0.38, GOLD)
    return part


def r6e_ring_cage(X, Y, Z):
    part = _hourglass_glass(X, Y, Z, seeds=(1363, 1364))
    for tilt, turn in ((90, 0), (90, 60), (90, 120)):   # three upright gold rings: a sphere cage round the glass
        tilted_ring(part, X, Y, Z, 13.0, 8.6, 0.38, tilt, turn, GOLD)
    tilted_ring(part, X, Y, Z, 13.0, 8.6, 0.36, 0, 0, GOLD_DK)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.4 + g), 4.4, [(1.0, 0.75, GOLD, "dots"), (2.4, 0.75, BRONZE, "zig"),
                                                                (3.6, 0.6, GOLD_DK, None)], down=True)
    gem_crown(part, X, Y, Z, 22.0, n=8, r0=1.6, h=1.2)
    return coarsen_glass(part), 7.8


# ------------------------------------------------------------------ IMPROVE R2b gold arms, redesigned in green
def r2f_cathedral(X, Y, Z):
    part, pz = P12.r2a_gold_arms(X, Y, Z)
    gold_net(part, X, Y, Z, Z0R + 9.0, Z1R - 1.4, body_r, cell=1.9)
    gem_crown(part, X, Y, Z, Z1R + 1.75, n=10, r0=1.9, h=1.6)
    claw_feet(part, X, Y, Z, n=4, r0=3.4)
    for sx in (-1, 1):                                  # spires on the shoulders
        rod(part, X, Y, Z, [(sx * 4.4, 0.0, 15.0), (sx * 4.8, 0.0, 19.5)], 0.35, GOLD)
        studs(part, X, Y, Z, [(sx * 4.8, 0.0, 19.9)], r=0.5, pid=CORE)
    return part, pz


def r2g_halo(X, Y, Z):
    part, pz = P10.n2_reliquary(X, Y, Z)
    for sx in (-1, 1):                                  # the arms keep rising past the neck and lift a gold halo
        pts = arms_pts(sx)
        pts = pts + [(sx * 3.6, 0.0, Z1R + 2.0), (sx * 3.4, 0.0, Z1R + 5.4)]
        rod(part, X, Y, Z, pts, 0.6, GOLD)
        gold_wire(part, X, Y, Z, pts[1:15], wrap=0.75, turns=10)
        studs(part, X, Y, Z, [pts[-1]], r=0.8, pid=GOLD_DK)
    hz, hr, tilt = Z1R + 6.2, 4.0, math.radians(35)     # the halo leans toward the viewer so it reads from the front
    tilted_ring(part, X, Y, Z, hz, hr, 0.45, 35, 0, GOLD)
    for k in range(10):
        a = k * 2 * math.pi / 10
        x, y = hr * math.cos(a), hr * math.sin(a)
        studs(part, X, Y, Z, [(x, y * math.cos(tilt), hz + y * math.sin(tilt))], r=0.55, pid=CORE if k % 2 else GOLD_DK)
    return part, pz


DESIGNS = {"R2d": ("Gold arms: winged", _w(r2d_winged, pr=1.87), "g"),
           "R2e": ("Gold arms: four arms, claw feet", _w(r2e_four_arms, pr=1.87), "g"),
           "R4d": ("Spinning rings: gilded cage", _w(r4d_gilded_cage), "g"),
           "R4e": ("Spinning rings: tall claw stand", _w(r4e_tall_stand), "g"),
           "R4f": ("Gyroscope: gem crown", _w(r4f_crowned_gyro), "g"),
           "R4g": ("Gyroscope: held by gold arms", _w(r4g_held_gyro), "g"),
           "R1d": ("Gold foot: tiered pedestal", _w(r1d_pedestal), "g"),
           "R1e": ("Gold foot: fully gilded", _w(r1e_gilded), "g"),
           "R6d": ("Hourglass: turning frame", _w(r6d_turning, pr=1.4), "g"),
           "R6e": ("Hourglass: cage of gold rings", _w(r6e_ring_cage, pr=1.4), "g"),
           "R2f": ("Gold arms: cathedral", _w(r2f_cathedral, pr=1.87), "g"),
           "R2g": ("Gold arms: raising a halo", _w(r2g_halo, pr=1.87), "g")}

_RINGS4 = P12.MOVING["R4a"] + [("ring D", lambda: ring_part(8.4, 0.3, GOLD, nodes=10), (0, 0, PZ4), (30, 0, 75), 2, "frame * -0.04")]
_GYRO_WIDE = [("gimbal outer", lambda: ring_part(8.6, 0.42, BRONZE, nodes=4), (0, 0, PZ4), (90, 0, 0), 0, "frame * 0.04"),
              ("gimbal middle", lambda: ring_part(7.7, 0.38, GOLD, nodes=4), (0, 0, PZ4), (90, 0, 90), 1, "frame * 0.06"),
              ("gimbal inner", lambda: ring_part(6.8, 0.36, BRONZE, nodes=6), (0, 0, PZ4), (0, 0, 0), 2, "frame * 0.09")]
MOVING = {"R4d": P12.MOVING["R4a"], "R4e": _RINGS4, "R4f": P12.MOVING["R4b"], "R4g": _GYRO_WIDE,
          "R6d": [("frame", lambda: r6d_frame(*grid()), (0, 0, 13.0), (0, 0, 0), 2, "frame * 0.03")]}
MID = P12.MID


def build(code):
    X, Y, Z = grid()
    P10.STYLE["hue"] = P10.CORPS[DESIGNS[code][2]][1]
    STYLE["dark"] = False
    return DESIGNS[code][1](X, Y, Z)


quads = P13.quads
model_boxes = P13.model_boxes
