"""Red corps battery, round two (J, 2026-10-13): "B2 is the best looking one". Built from B2 (bleeding) with:
  - the port opened into a hole whose back wall is cut with three claw marks; the light comes out through the
    claws (kind 7, the charge light, so Blender can drive it on its own);
  - a stone plate (a separate model) closing the hole, which slides down and away when the charge starts;
  - the Red corps mark raised on the top of the cap and on the outer face of both side drums.
Original marks only (the claw mark is ours).

    python tools/pixel_rage_battery2.py OUTDIR -> battery2_body.npz, battery2_plate.npz
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["pixel_rage_battery.py", os.path.join(OUT, "_r1")]
sys.path.insert(0, HERE)
import pixel_rage_battery as B  # noqa: E402
sys.argv = _argv
X, Y, Z, R, TH = B.X, B.Y, B.Z, B.R, B.TH
PORTLIGHT, PLATE, GROOVE = 10, 11, 12
pal = dict(B.PAL["b2"])
pal[PORTLIGHT] = (255, 70, 50)
pal[PLATE] = (88, 38, 34)
pal[GROOVE] = (40, 14, 13)
B.KIND.update({PORTLIGHT: 7, PLATE: 1, GROOVE: 0})
B.GLOW.update({PORTLIGHT: 1.0})


def claws(u, v, r):
    """The Red corps mark in a plane: three raking claw slashes, curved, tapering, inside a ring of radius r."""
    out = np.zeros(u.shape, bool)
    for off in (-0.42, 0.0, 0.42):
        cu = u - off * r - 0.12 * r * (v / r) ** 2                 # each slash bows a little
        w = (0.15 - 0.07 * np.abs(v) / r) * r                       # and tapers to its tips
        out |= (np.abs(cu * 0.94 + v * 0.34) < w * 0.5) & (np.abs(v) < r * (0.78 - 0.45 * abs(off)))
    return out


def mark(u, v, r):
    rho = np.hypot(u, v)
    return (np.abs(rho - 0.9 * r) < 0.11 * r) | claws(u, v, 0.8 * r)


def build():
    part = B.battery("b2")
    front_y = -(9.0 + 3.4)
    pc_z = 24.0
    lx, lz = X, Z - pc_z
    pr = np.hypot(lx, lz)
    # open the hole: everything inside the light ring, from the port face back to the wall
    hole = (pr < 5.6) & (Y < front_y + 1.0) & (Y > front_y - 3.0)
    part[hole] = B.EMPTY
    wall = (pr < 5.8) & (Y >= front_y + 1.0) & (Y < front_y + 2.0)
    part[wall] = B.DARK
    cut = wall & claws(lx, lz, 4.4)
    part[cut] = B.EMPTY
    part[(pr < 5.8) & (Y >= front_y + 2.0) & (Y < front_y + 3.0)] = PORTLIGHT       # the light behind the claws
    part[(np.abs(pr - 6.0) < 0.4) & (Y < front_y + 2.4) & (Y > front_y - 2.6)] = PORTLIGHT  # the ring of light
    # raised marks: top of the cap, and the outer face of each side drum
    top = (Z >= 42.5) & (Z < 43.5) & mark(X, Y, 4.2)
    part[top] = B.RUNE
    for s in (-1, 1):
        side = (s * X >= 14.5) & (s * X < 15.5) & mark(Y * -s, Z - 24.0, 3.6)
        part[side] = B.RUNE
    # the plate that closes the hole (its own model so it can slide away)
    plate = np.zeros(X.shape, np.int8)
    pm = (pr < 5.5) & (Y >= front_y - 2.6) & (Y < front_y - 0.6)
    plate[pm] = PLATE
    plate[pm & (np.abs(pr - 4.7) < 0.35) & (Y < front_y - 1.9)] = GROOVE
    plate[pm & (Y < front_y - 1.9) & claws(lx, lz, 3.4)] = GROOVE
    plate[pm & (B.HASH < 0.06)] = B.FLECK
    return part, plate


if __name__ == "__main__":
    body, plate = build()
    for name, p in (("body", body), ("plate", plate)):
        q, c, k, g = B.quads(p, pal)
        np.savez_compressed(os.path.join(OUT, f"battery2_{name}.npz"), quads=q, col=c, kind=k, glow=g)
        print(name, len(q), "faces", np.bincount(k, minlength=8))
