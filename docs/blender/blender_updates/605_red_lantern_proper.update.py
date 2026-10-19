# Pass 605: proper Red Lantern models from J:red_lantern (PC chat, 2026-10-18; lanterns 600-699).
# Why: J picked "604-style pass" for the jar's Red Lantern (414 boxes: blocky crimson body, gold bands, a Y-shaped gold
#   cradle with a top ring, a plain square lens plate; preview LanternLive\_previews\J_red_lantern\). In game on
#   2026-10-16 he said the red "lantern needs to be fully redesigned" and to mix finishes by part (not 100% one
#   material). Same brief as 604: smooth glass, a richer frame, new silhouettes, 6 takes.
# Runs 604's builder (glass, gold, lathe, collars, tubes, stage, bloom) with a Red palette: near-black crimson ends,
#   crimson light in the middle band with some orange rage in the flow, dim gold cracks, darkest-red stitches.
# Red rules from the design skill: the claw mark (three claw slashes in a ring, never a corps logo) on a lens brought out
#   of its housing; smooth glossy crimson sRGB (188, 30, 47) with diamond-like reflectivity; finishes mixed by part (M1
#   ruby + gold, M2 obsidian + ruby lens, M3 lacquer + black steel + gold neck); blood falls as long thin streaks.
# Takes:
#   R1 Y cradle: the jar's shape made proper: a rounded-square crimson column in the gold Y cradle and arch, top ring.
#   R2 Ruby pinch: 604 A1's pinched column in crimson glass with gold (M1).
#   R3 Steel cage: round crimson glass in a black-steel cage with steel collars and a gold neck (M3).
#   R4 Clutched heart: a crimson glass orb gripped by three black-steel claws on an obsidian pedestal (M2).
#   R5 Rage spire: two obsidian-framed chambers under a jagged crown of uneven spikes, gold trims.
#   R6 Blood lamp: 604 B3's hourglass in crimson, long thin blood streaks running down from the top ring.
# Every take: the claw lens stands out of the front on a short gold neck; its three slashes light with the charge.
# Cameras "Cam <code> <name>", "Cam all". Builds LanternLive\red\red_lantern_proper.blend.
import math, os
import bpy
import numpy as np


def _find_604():
    names = []
    if os.environ.get("KL_REPO"):
        names.append(os.path.join(os.environ["KL_REPO"], "docs", "blender", "blender_updates"))
    if "__file__" in globals():
        names.append(os.path.dirname(os.path.abspath(__file__)))
    names.append(os.path.join(os.path.expanduser("~"), "Documents", "LanternLive", "site-10", "docs", "blender", "blender_updates"))
    names.append("/home/claude/site-10/docs/blender/blender_updates")
    for d in names:
        p = os.path.join(d, "604_lantern_models_proper.update.py")
        if os.path.exists(p):
            return p
    raise FileNotFoundError("605 needs 604_lantern_models_proper.update.py next to it (or KL_REPO set)")


PASS = "605"
OUT_NAME = "red_lantern_proper.blend"
PAL = dict(glass=(0.03, 0.002, 0.004), crack=(0.42, 0.26, 0.04), stitch=(0.008, 0.0, 0.001),
           flow=(0.85, 0.02, 0.045), flow2=(0.9, 0.2, 0.02), crack_glow=(0.9, 0.55, 0.06),
           lamp=(1.0, 0.22, 0.22), port=(0.08, 0.005, 0.01))
_s604 = _find_604()
_t604 = open(_s604, encoding="utf-8").read()
exec(compile(_t604[:_t604.index("# ---- 604 takes")], _s604, "exec"), globals())


def solid(name, rgb, metal=0.0, rough=0.3, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    return m


STEEL = solid(f"{TAG} black steel", (0.035, 0.035, 0.04), metal=1.0, rough=0.28)
OBSIDIAN = solid(f"{TAG} obsidian", (0.012, 0.008, 0.012), rough=0.08, coat=1.0)
CLAW = bpy.data.materials.new(f"{TAG} claw light")
CLAW.use_nodes = True
_cb = CLAW.node_tree.nodes["Principled BSDF"]
_cb.inputs["Base Color"].default_value = (0.3, 0.01, 0.02, 1)
_cb.inputs["Emission Color"].default_value = (0.85, 0.02, 0.045, 1)
drive(_cb.inputs["Emission Strength"], "default_value", "1.2 * (" + CHARGE + ")")
BLOOD = bpy.data.materials.new(f"{TAG} blood")
BLOOD.use_nodes = True
_bb = BLOOD.node_tree.nodes["Principled BSDF"]
_bb.inputs["Base Color"].default_value = (0.25, 0.005, 0.012, 1)
_bb.inputs["Roughness"].default_value = 0.1
_bb.inputs["Emission Color"].default_value = (0.7, 0.01, 0.03, 1)
drive(_bb.inputs["Emission Strength"], "default_value", "0.15 + 0.35 * (" + CHARGE + ")")
rnd = poly_shape(0, 0)
LENS = solid(f"{TAG} ruby lens", (0.16, 0.004, 0.01), rough=0.05, coat=1.0)    # dark ruby: the lit slashes read on it
_lb = LENS.node_tree.nodes["Principled BSDF"]
_lb.inputs["Emission Color"].default_value = (0.85, 0.02, 0.045, 1)
drive(_lb.inputs["Emission Strength"], "default_value", "0.12 * (" + CHARGE + ")")


def claw_lens(name, parent, front, z, r=0.085, neck=0.05, rim=None):
    """The Red corps mark (three claw slashes in a ring) on a lens standing out of the front (-Y) on a short neck."""
    lens = lathe(name + " lens", [(0.0, 0.0), (r, 0.0), (r, 0.018), (r * 0.75, 0.034), (0.0, 0.04)], rnd,
                 mat=LENS, parent=parent)
    lens.rotation_euler = (math.pi / 2, 0, 0)                 # lathe axis +Z -> -Y (out of the front)
    lens.location = (0, -(front + neck), z)
    ring = lathe(name + " rim", [(r - 0.004, -0.006), (r + 0.022, -0.006), (r + 0.026, 0.02), (r + 0.016, 0.042),
                                 (r - 0.004, 0.036)], rnd, closed=True, mat=rim or GOLD, parent=lens)
    lathe(name + " neck", [(r * 0.45, -neck - 0.02), (r * 0.6, -neck - 0.02), (r * 0.5, 0.0), (r * 0.4, 0.0)], rnd,
          closed=True, mat=rim or GOLD, parent=lens)
    for k, dx in enumerate((-0.034, 0.0, 0.034)):              # three slashes, raked down to the right, slightly curved
        pts = []
        for i in range(9):
            t = i / 8 - 0.5
            pts.append((dx + 0.05 * t + 0.014 * (0.25 - t * t), -0.13 * t + 0.008 * (k - 1), 0.05))
        tube(f"{name} slash {k}", pts, 0.0105, lens, mat=CLAW)
    return lens


def ring_lathe(name, r, z, h, shape, parent, mat, depth=0.035, lip=0.012):
    ri, ro = r - 0.006, r + depth
    return lathe(name, [(ri, z), (ro - lip, z), (ro, z + lip), (ro, z + h - lip), (ro - lip, z + h), (ri, z + h)],
                 shape, closed=True, mat=mat, parent=parent, sharp=R(50))


# R1 Y cradle
root, lamp = take("R1", "Y cradle", 0, 0)
sqr = poly_shape(4, 0.5)
gp = glass_profile(0.12, 0.98, 0.21, 0.235, pinch=0.9, cap=0.02)
glass(f"{TAG} R1 glass", gp, sqr, root)
lathe(f"{TAG} R1 base", [(0.0, 0.0), (0.3, 0.0), (0.3, 0.05), (0.26, 0.09), (0.0, 0.09)], sqr, closed=True, mat=GOLD,
      parent=root, sharp=R(40))
for nm, z in (("low", 0.36), ("high", 0.72)):
    ring_lathe(f"{TAG} R1 band {nm}", r_at(gp, z), z - 0.015, 0.035, sqr, root, GOLD, depth=0.022)
ring_lathe(f"{TAG} R1 collar top", 0.21, 0.96, 0.07, sqr, root, GOLD, depth=0.035)
for sx in (-1, 1):                                            # the Y: a post that forks into an outer horn and the arch
    tube(f"{TAG} R1 post {sx}", [(sx * 0.33, 0, 0.05), (sx * 0.33, 0, 0.82)], 0.02, root)
    tube(f"{TAG} R1 horn {sx}", [(sx * 0.33, 0, 0.82), (sx * 0.39, 0, 0.98), (sx * 0.44, 0, 1.12)], 0.018, root)
arch = [(0.33 * math.cos(math.pi * k / 30), 0, 0.82 + 0.4 * math.sin(math.pi * k / 30)) for k in range(31)]
tube(f"{TAG} R1 arch", arch, 0.016, root)
tube(f"{TAG} R1 top ring", [(0.07 * math.cos(TAU * k / 32), 0, 1.29 + 0.07 * math.sin(TAU * k / 32)) for k in range(33)],
     0.014, root)
port(f"{TAG} R1 port", 1.03, root)
claw_lens(f"{TAG} R1 claw", root, 0.235, 0.55)
lamp.location = (0, 0, 0.55)

# R2 Ruby pinch (604 A1 in crimson, M1 ruby + gold)
root, lamp = take("R2", "Ruby pinch", 4, 0)
tri = poly_shape(3, 0.55)
gp = glass_profile(0.13, 1.0, 0.27, 0.215, pinch=1.4)
glass(f"{TAG} R2 glass", gp, tri, root, twist=R(3))
for nm, z in (("bottom", 0.06), ("top", 0.97)):
    collar(f"{TAG} R2 collar {nm}", 0.27, z, 0.09, tri, root, depth=0.04)
for k, z in enumerate((0.3, 0.8)):
    collar(f"{TAG} R2 band {k}", r_at(gp, z), z - 0.018, 0.035, tri, root, depth=0.025)
for k in range(3):
    th = -math.pi / 2 + math.pi / 3 + k * TAU / 3
    pts = [((r * tri(th) + 0.012) * math.cos(th), (r * tri(th) + 0.012) * math.sin(th), z) for r, z in gp[1:-1] if 0.14 <= z <= 0.99]
    tube(f"{TAG} R2 rib {k}", pts, 0.011, root)
lathe(f"{TAG} R2 cap", [(0.0, 1.06), (0.2, 1.06), (0.12, 1.1), (0.0, 1.1)], tri, closed=True, mat=GOLD, parent=root)
port(f"{TAG} R2 port", 1.1, root)
bail(f"{TAG} R2 bail", 1.08, 0.21, 0.42, root, "tri")
claw_lens(f"{TAG} R2 claw", root, 0.215 * tri(-math.pi / 2), 0.56)
lamp.location = (0, 0, 0.55)

# R3 Steel cage (M3: lacquer glass, black steel, gold neck)
root, lamp = take("R3", "Steel cage", 8, 0)
gp = glass_profile(0.12, 0.98, 0.23, 0.2, pinch=1.2)
glass(f"{TAG} R3 glass", gp, rnd, root)
ring_lathe(f"{TAG} R3 collar bottom", 0.23, 0.04, 0.09, rnd, root, STEEL, depth=0.055)
ring_lathe(f"{TAG} R3 collar top", 0.23, 0.96, 0.07, rnd, root, STEEL, depth=0.055)
for k in range(8):
    th = -math.pi / 2 + TAU / 16 + k * TAU / 8
    pts = [((r + 0.028) * math.cos(th), (r + 0.028) * math.sin(th), z) for r, z in gp[1:-1]]
    tube(f"{TAG} R3 bar {k}", pts, 0.013, root, mat=STEEL)
lathe(f"{TAG} R3 neck", [(0.0, 1.03), (0.14, 1.03), (0.09, 1.1), (0.07, 1.16), (0.1, 1.19), (0.0, 1.19)], rnd, closed=True,
      mat=GOLD, parent=root)
port(f"{TAG} R3 port", 1.19, root, r=0.045)
bail(f"{TAG} R3 bail", 1.04, 0.25, 0.34, root, "arch", r=0.016)
claw_lens(f"{TAG} R3 claw", root, 0.2 + 0.028, 0.55)
lamp.location = (0, 0, 0.55)

# R4 Clutched heart (M2: obsidian + ruby lens)
root, lamp = take("R4", "Clutched heart", 0, 7)
orb = [(0.0, 0.22)] + [(0.34 * math.sin(math.pi * k / 30), 0.56 - 0.34 * math.cos(math.pi * k / 30)) for k in range(1, 30)] \
      + [(0.0, 0.9)]
glass(f"{TAG} R4 glass", orb, rnd, root)
lathe(f"{TAG} R4 pedestal", [(0.0, 0.0), (0.26, 0.0), (0.26, 0.05), (0.12, 0.12), (0.1, 0.2), (0.16, 0.25), (0.0, 0.25)],
      poly_shape(6, 0.1), closed=True, mat=OBSIDIAN, parent=root, sharp=R(40))
for k in range(3):                                            # claws curl up round the orb, tips hooking inward
    th = -math.pi / 2 + math.pi / 3 + k * TAU / 3
    pts = []
    for i in range(16):
        a = R(-60 + 130 * i / 15)                             # from under the orb to past its shoulder
        rr = 0.37 + 0.03 * math.sin(math.pi * i / 15)
        rr *= 1.0 - 0.25 * max(0, (i - 11) / 4)               # the tip hooks in
        pts.append((rr * math.cos(a) * math.cos(th), rr * math.cos(a) * math.sin(th), 0.56 + rr * math.sin(a)))
    tube(f"{TAG} R4 claw {k}", pts, 0.03, root, mat=STEEL)
    tube(f"{TAG} R4 claw tip {k}", [pts[-1], (pts[-1][0] * 0.82, pts[-1][1] * 0.82, pts[-1][2] - 0.04)], 0.012, root,
         mat=STEEL)
lathe(f"{TAG} R4 crown", [(0.0, 0.89), (0.09, 0.89), (0.09, 0.95), (0.05, 0.97), (0.0, 0.97)], rnd, closed=True, mat=GOLD,
      parent=root)
port(f"{TAG} R4 port", 0.96, root, r=0.04)
claw_lens(f"{TAG} R4 claw", root, 0.34, 0.56, rim=GOLD)
lamp.location = (0, 0, 0.56)

# R5 Rage spire
root, lamp = take("R5", "Rage spire", 4, 7)
octs = poly_shape(8, 0.05)
lathe(f"{TAG} R5 plinth", [(0.0, 0.0), (0.3, 0.0), (0.3, 0.06), (0.26, 0.09), (0.0, 0.09)], octs, closed=True,
      mat=OBSIDIAN, parent=root, sharp=R(40))
g1 = glass_profile(0.11, 0.6, 0.2, 0.225, pinch=0.8, cap=0.02)
g2 = glass_profile(0.68, 1.06, 0.17, 0.19, pinch=0.8, cap=0.02)
glass(f"{TAG} R5 glass low", g1, octs, root, sharp=R(30))
glass(f"{TAG} R5 glass high", g2, octs, root, sharp=R(30))
ring_lathe(f"{TAG} R5 collar low", 0.21, 0.08, 0.05, octs, root, GOLD, depth=0.03)
ring_lathe(f"{TAG} R5 collar mid", 0.21, 0.59, 0.1, octs, root, OBSIDIAN, depth=0.04)
ring_lathe(f"{TAG} R5 collar high", 0.18, 1.04, 0.06, octs, root, GOLD, depth=0.035)
rng = np.random.default_rng(605)
for k in range(9):                                            # jagged crown: uneven spikes, leaning out
    th = -math.pi / 2 + k * TAU / 9 + rng.uniform(-0.15, 0.15)
    hgt = rng.uniform(0.12, 0.3)
    lean = rng.uniform(0.02, 0.08)
    b0 = 0.17
    sp = lathe(f"{TAG} R5 spike {k}", [(0.0, 0.0), (0.035, 0.0), (0.012, hgt * 0.7), (0.0, hgt)], poly_shape(4, 0.0),
               mat=OBSIDIAN, parent=root, sharp=R(30))
    sp.location = (b0 * math.cos(th), b0 * math.sin(th), 1.08)
    sp.rotation_euler = (0, math.atan2(lean, hgt) * 2.5, th)          # tapered, leaning out
    sp.rotation_mode = "YXZ"                                      # lean (Y) first, then turn to its angle (Z)
lathe(f"{TAG} R5 cap", [(0.0, 1.09), (0.18, 1.09), (0.1, 1.16), (0.0, 1.17)], octs, closed=True, mat=OBSIDIAN, parent=root,
      sharp=R(40))
port(f"{TAG} R5 port", 1.16, root, r=0.045)
claw_lens(f"{TAG} R5 claw", root, 0.225, 0.36, r=0.075)
lamp.location = (0, 0, 0.36)

# R6 Blood lamp (604 B3 in crimson, blood streaks)
root, lamp = take("R6", "Blood lamp", 8, 7)
tri_s = poly_shape(3, 0.12)
hg = [(0.0, 0.16)] + [(0.33 - 0.21 * (1 - abs(1 - 2 * k / 30)) ** 1.15, 0.16 + 0.9 * k / 30) for k in range(31)] + [(0.0, 1.06)]
glass(f"{TAG} R6 glass", hg, tri_s, root, twist=R(3), sharp=R(40))
collar(f"{TAG} R6 waist", 0.12, 0.585, 0.05, tri_s, root, depth=0.04)
collar(f"{TAG} R6 base ring", 0.33, 0.12, 0.05, tri_s, root, depth=0.03)
collar(f"{TAG} R6 top ring", 0.33, 1.04, 0.05, tri_s, root, depth=0.03)
for k in range(3):
    th = -math.pi / 2 + math.pi / 3 + k * TAU / 3
    c, s = math.cos(th), math.sin(th)
    rr = 0.33 * tri_s(th) + 0.02
    tube(f"{TAG} R6 leg {k}", [(rr * c, rr * s, 0.13), ((rr + 0.04) * c, (rr + 0.04) * s, 0.05),
                               ((rr + 0.07) * c, (rr + 0.07) * s, 0.0)], 0.018, root)
for k in range(11):                                           # long thin streaks running down the upper cone
    th = -math.pi / 2 + rng.uniform(-math.pi, math.pi)
    if abs(math.atan2(math.sin(th + math.pi / 2), math.cos(th + math.pi / 2))) < 0.35:
        continue                                              # keep the lens clear
    ln = rng.uniform(0.12, 0.4)
    pts = []
    for i in range(10):
        z = 1.04 - ln * i / 9
        r = r_at(hg, z) * tri_s(th) + 0.007
        pts.append((r * math.cos(th), r * math.sin(th), z))
    tube(f"{TAG} R6 streak {k}", pts, 0.006 + 0.003 * rng.random(), root, mat=BLOOD)
lathe(f"{TAG} R6 cap", [(0.0, 1.09), (0.3, 1.09), (0.16, 1.13), (0.0, 1.13)], tri_s, closed=True, mat=GOLD, parent=root,
      sharp=R(40))
port(f"{TAG} R6 port", 1.13, root)
bail(f"{TAG} R6 bail", 1.11, 0.24, 0.38, root, "tri")
claw_lens(f"{TAG} R6 claw", root, r_at(hg, 0.34) * tri_s(-math.pi / 2), 0.34, r=0.07)
lamp.location = (0, 0, 0.6)

exec(compile(_t604[_t604.index("# ------------------------------------------------------------------ stage, light, cameras"):],
             _s604, "exec"), globals())
