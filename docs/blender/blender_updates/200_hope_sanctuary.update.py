# Pass 200: the floating Hope sanctuary, round 1 (lead Blender chat, 2026-10-13).
# J's brief (coordinator thread "Blue Lantern villager behavior", answers 12, 17, 18, 19):
#   a whole floating city in the sky, a wide cylinder funnel. The tops are the lanterns' flying / levitation area,
#   the bottoms hold the rescued mobs, gently grouped in their own bubbles, and in the middle a massive, almost
#   wind-turbine power-plant "squeezed cylinder" floating Hope logo. It rises after the dome, once everyone is safe
#   (17 b). Landmark scale but WIDE, not insanely tall, elegant; traversable for animals with no way to jump off
#   (18 c). The turbine powers lanterns and slowly recharges Blue rings nearby (19 b, c).
# The mark is an ORIGINAL Hope mark (open ring, rising four-point star, three rays), not any published emblem.
# Everything is whole Minecraft blocks in the mod's own textures (Skystone, Hope Quartz, Hope Bricks, Hope Lamp,
# blue construct brick and nebula glass), so a pick can be turned straight into a block plan for the game.
# Three takes side by side (cameras "Cam A1", "Cam A2", "Cam A3", "Cam all"):
#   A1 Hourglass funnel: a walled bowl for the herds, a pinched waist holding the turbine with the mark cut through
#      its walls, and an open flight crown with lantern posts.
#   A2 Turbine drum: a squat wide drum with louvred turbine fins all round, a walled spiral ramp from the pens up to
#      the roof deck, the turbine spinning in an open central shaft.
#   A3 Lotus tiers: four round terraces stepping in, each a walled paddock; the turbine floats above the top tier in
#      a halo held by four arched ribs, with the flyers' ring around it.
# Builds LanternLive\hope_sanctuary.blend; textures from LanternLive\hope_tex\.
import math, os
import bpy
import numpy as np

R = math.radians
TEX = os.path.join(FOLDER, "hope_tex")
OUT = os.path.join(FOLDER, "hope_sanctuary.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Hope Sanctuary")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Hope Sanctuary")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 400
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


# ---------------------------------------------------------------- materials (Minecraft look: whole-block UVs)
MATS = ["skystone_tiles", "skystone_bricks", "skystone_pillar", "hope_bricks", "hope_quartz", "hope_quartz_bricks",
        "hope_quartz_pillar", "hope_lamp", "hope_inlay", "construct_brick_blue", "nebula_glass_blue", "hope_crystal"]
GLASSY = {"nebula_glass_blue", "hope_crystal", "construct_brick_blue"}
GLOW = {"hope_lamp": 6.0, "construct_brick_blue": 1.6, "hope_crystal": 2.5, "hope_inlay": 0.6}
MI = {n: i for i, n in enumerate(MATS)}


def block_mat(name):
    m = bpy.data.materials.get("HS " + name) or bpy.data.materials.new("HS " + name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    t = N.new("ShaderNodeTexImage")
    path = os.path.join(TEX, name + ".png")
    img = bpy.data.images.get(name + ".png") or bpy.data.images.load(path)
    t.image = img; t.interpolation = "Closest"
    L.new(t.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.55
    if name.startswith(("hope_quartz", "skystone")):
        p.inputs["Roughness"].default_value = 0.3
    if name in GLASSY:
        L.new(t.outputs["Alpha"], p.inputs["Alpha"])
        if name == "nebula_glass_blue":                       # mostly clear: a faint blue film so it still reads
            mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; mx.inputs[1].default_value = 0.16
            L.new(t.outputs["Alpha"], mx.inputs[0]); L.new(mx.outputs[0], p.inputs["Alpha"])
            mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
            mix.inputs["A"].default_value = (0.45, 0.72, 1.0, 1)
            L.new(t.outputs["Alpha"], mix.inputs["Factor"]); L.new(t.outputs["Color"], mix.inputs["B"])
            L.new(mix.outputs["Result"], p.inputs["Base Color"])
            p.inputs["Emission Color"].default_value = (0.45, 0.72, 1.0, 1); p.inputs["Emission Strength"].default_value = 0.25
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        m.use_backface_culling = False
    if name in GLOW:
        L.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = GLOW[name]
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


MAT_OBJS = [block_mat(n) for n in MATS]


def flat_mat(name, rgb, emit=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = 0.5
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


# ---------------------------------------------------------------- voxels -> mesh with exposed faces only
DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
        ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
        ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
        ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]
UV = [(0, 0), (1, 0), (1, 1), (0, 1)]


def voxel_object(name, V, origin=(0, 0, 0)):
    verts, faces, mats, uvs = [], [], [], []
    for (x, y, z), m in V.items():
        for (dx, dy, dz), quad in DIRS:
            n = V.get((x + dx, y + dy, z + dz))
            if n is not None and (n == m or (n not in GLASSY_IDX)):
                continue
            b = len(verts)
            verts.extend((x + a, y + c, z + e) for a, c, e in quad)
            faces.append((b, b + 1, b + 2, b + 3)); mats.append(m); uvs.extend(UV)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for mo in MAT_OBJS:
        me.materials.append(mo)
    me.polygons.foreach_set("material_index", mats)
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", [c for uv in uvs for c in uv])
    me.update()
    o = bpy.data.objects.new(name, me)
    o.location = origin
    return link(o)


GLASSY_IDX = {MI[n] for n in GLASSY}


class Vox(dict):
    def put(self, x, y, z, m, keep=False):
        k = (int(x), int(y), int(z))
        if keep and k in self:
            return
        self[k] = MI[m]

    def clear_at(self, x, y, z):
        self.pop((int(x), int(y), int(z)), None)


def disc(V, z, r_out, m, r_in=-1.0, keep=False):
    ri = int(math.ceil(r_out))
    for x in range(-ri, ri + 1):
        for y in range(-ri, ri + 1):
            d = math.hypot(x + 0.5, y + 0.5)
            if r_in < d <= r_out:
                V.put(x, y, z, m, keep)


def ring(V, z, r, m, thick=1.0):
    disc(V, z, r, m, r - thick)


# ---------------------------------------------------------------- the original Hope mark, as a 2D pixel test
MARK = ["......#......",
        "......#......",
        ".....###.....",
        "...#######...",
        ".....###.....",
        "..#...#...#..",
        ".#....#....#.",
        "#...........#",
        "#...........#",
        "#...........#",
        ".#.........#.",
        "..##.....##..",
        "....#####...."]


def hope_mark(u, v):
    """u, v in [-1, 1]. J-original Hope mark: an open ring with a four-point star rising out of its gap."""
    n = len(MARK)
    i = min(n - 1, max(0, int((u + 1) / 2 * n))); j = min(n - 1, max(0, int((1 - v) / 2 * n)))
    return MARK[j][i] == "#"


def mark_cells(size):
    out = []
    for i in range(size):
        for j in range(size):
            u = (i + 0.5) / size * 2 - 1; v = (j + 0.5) / size * 2 - 1
            if hope_mark(u, v):
                out.append((i - size // 2, j - size // 2))
    return out


def cut_mark_in_wall(V, z_mid, r_wall, angle_deg, size, fill=None):
    """Cut (or fill with `fill`) the mark through a cylindrical wall, facing out at angle_deg."""
    a = R(angle_deg)
    nx, ny = math.cos(a), math.sin(a); tx, ty = -ny, nx
    for i, j in mark_cells(size):
        for depth in np.arange(r_wall - 2.5, r_wall + 1.5, 0.5):
            x = nx * depth + tx * i; y = ny * depth + ty * i; z = z_mid + j
            if fill:
                if (int(math.floor(x)), int(math.floor(y)), int(z)) in V:
                    V.put(math.floor(x), math.floor(y), z, fill)
            else:
                V.clear_at(math.floor(x), math.floor(y), z)


# ---------------------------------------------------------------- shared pieces
def lantern_post(V, x, y, z, h=4):
    for k in range(h):
        V.put(x, y, z + k, "hope_quartz_pillar")
    V.put(x, y, z + h, "hope_lamp")


def rail(V, z, r, h=2):
    """A see-through hard-light railing two blocks high: animals can't jump it."""
    for k in range(h):
        ring(V, z + k, r, "nebula_glass_blue")


def ramp(V, z0, z1, r_in, r_out, a0, m="skystone_tiles"):
    """A straight-run stair ramp along the wall, one block up per two blocks around, with glass rail on the inside."""
    steps = (z1 - z0) * 2
    for s in range(steps):
        a = R(a0) + s / (r_out * 1.0)
        z = z0 + s // 2
        for rr in np.arange(r_in, r_out, 0.5):
            V.put(math.floor(math.cos(a) * rr), math.floor(math.sin(a) * rr), z, m)
        for k in (1, 2):
            V.put(math.floor(math.cos(a) * (r_in - 0.6)), math.floor(math.sin(a) * (r_in - 0.6)), z + k,
                  "nebula_glass_blue", keep=True)


def underside(V, z_top, r_top, depth, step=2.0):
    """Stepped inverted cone below the floor, Hope Bricks with lamp drips: what you see floating overhead."""
    for k in range(1, depth + 1):
        r = r_top - k * step
        if r < 1.5:
            break
        ring(V, z_top - k, r + step, "hope_bricks", thick=step + 0.6)
        if k % 2 == 0:
            for t in range(0, 360, 30):
                V.put(math.floor(math.cos(R(t)) * (r + step - 0.5)), math.floor(math.sin(R(t)) * (r + step - 0.5)),
                      z_top - k - 1, "hope_lamp")


def turbine(name, r, h, blades=6, twist=60.0, origin=(0, 0, 0)):
    """The power turbine: a lamp hub column, twisted construct-brick vanes, the mark as a medallion both ways
    (four faces), all one object that spins slowly about its vertical axis."""
    V = Vox()
    for z in range(h):
        disc(V, z, 2.2, "hope_lamp")
        for b in range(blades):
            a = R(b * 360 / blades + twist * z / h)
            for rr in np.arange(2.5, r, 0.5):
                V.put(math.floor(math.cos(a) * rr), math.floor(math.sin(a) * rr), z, "construct_brick_blue")
    # end caps
    disc(V, 0, r * 0.55, "hope_quartz_bricks"); disc(V, h - 1, r * 0.55, "hope_quartz_bricks")
    ring(V, 0, r + 0.2, "hope_inlay", 1.2); ring(V, h - 1, r + 0.2, "hope_inlay", 1.2)
    o = voxel_object(name, V, origin)
    # medallions: the mark in Hope Crystal, two crossed plates through the hub
    size = 13
    M = Vox()
    for i, j in mark_cells(size):
        M.put(i, 0, j + h // 2, "hope_crystal"); M.put(0, i, j + h // 2, "hope_crystal")
    med = voxel_object(name + " mark", M, (0, 0, 0)); med.parent = o
    # slow spin: one turn per 20 s (400 frames at 20 fps), linear, cycling
    o.rotation_euler = (0, 0, 0); o.keyframe_insert("rotation_euler", index=2, frame=1)
    o.rotation_euler = (0, 0, R(360)); o.keyframe_insert("rotation_euler", index=2, frame=401)
    try:
        fc = o.animation_data.action.fcurves[0]
    except Exception:
        fc = None
        for layer in o.animation_data.action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fc = cb.fcurves[0]
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
    fc.modifiers.new("CYCLES")
    return o


MOB_RGB = {"cow": (0.25, 0.17, 0.12), "sheep": (0.92, 0.92, 0.9), "pig": (0.93, 0.6, 0.6),
           "villager": (0.45, 0.32, 0.22), "cat": (0.9, 0.55, 0.2), "horse": (0.5, 0.33, 0.2), "chicken": (0.95, 0.95, 0.95)}
BUB = flat_mat("HS bubble", (0.45, 0.75, 1.0), emit=0.35, alpha=0.22)


def mob_bubble(x, y, z, kind, phase):
    """A rescued mob in its own soft hard-light bubble, bobbing gently."""
    w, hgt = (0.9, 1.4) if kind in ("cow", "horse") else (0.7, 0.9) if kind != "villager" else (0.6, 1.9)
    bpy.ops.mesh.primitive_cube_add(size=1)
    body = bpy.context.active_object
    for c in body.users_collection:
        c.objects.unlink(body)
    link(body)
    body.scale = (w * 1.2 if kind in ("cow", "horse", "pig", "sheep") else w, w, hgt)
    body.location = (x, y, z + hgt / 2 + 0.3)
    body.data.materials.append(flat_mat("HS mob " + kind, MOB_RGB[kind]))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=max(w * 1.25, hgt * 0.75), segments=24, ring_count=12)
    b = bpy.context.active_object
    for c in b.users_collection:
        c.objects.unlink(b)
    link(b)
    b.location = (x, y, z + hgt / 2 + 0.3)
    b.data.materials.append(BUB)
    body.parent = b; body.location = (0, 0, 0); body.matrix_parent_inverse.identity()
    for f, dz in ((1, 0.0), (21, 0.25), (41, 0.0)):
        b.location.z = z + hgt / 2 + 0.35 + dz
        b.keyframe_insert("location", index=2, frame=f + phase)
    try:
        fcs = list(b.animation_data.action.fcurves)
    except Exception:
        fcs = [fc for layer in b.animation_data.action.layers for s in layer.strips for cb in s.channelbags
               for fc in cb.fcurves]
    for fc in fcs:
        fc.modifiers.new("CYCLES")
    return b


def herd(cx, cy, z, radius, n, seed):
    rng = np.random.default_rng(seed)
    kinds = list(MOB_RGB)
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi); r = radius * math.sqrt(rng.uniform(0.15, 1))
        mob_bubble(cx + math.cos(a) * r, cy + math.sin(a) * r, z, kinds[i % len(kinds)], int(rng.integers(0, 40)))


# ================================================================ A1: hourglass funnel
def take_a1(ox):
    V = Vox()
    # floor of the herd bowl and its stepped underside
    disc(V, 0, 25, "skystone_tiles")
    ring(V, 0, 25, "hope_inlay", 1.0)
    underside(V, 0, 25, 9, 2.4)
    # profile of the outer wall: (z, r). Bowl walls rise to z=9, pinch to the waist, open into the crown.
    prof = [(1, 26), (4, 26), (7, 25.5), (9, 25), (10, 22), (11, 18.5), (12, 15.5), (13, 14), (25, 14),
            (26, 15.5), (27, 18.5), (28, 21.5), (29, 24)]
    zs = [p[0] for p in prof]; rs = [p[1] for p in prof]
    for z in range(1, 30):
        r = float(np.interp(z, zs, rs))
        if z <= 9:
            m = "skystone_bricks" if z not in (5, 6) else "nebula_glass_blue"     # a window band round the bowl
            ring(V, z, r, m, 1.2)
        elif z < 13:
            ring(V, z, r, "hope_quartz_bricks", 1.6)
        elif z <= 25:
            ring(V, z, r, "hope_quartz", 1.4)                   # the waist: the mark is cut through here
        else:
            ring(V, z, r, "skystone_bricks" if z % 3 else "hope_inlay", 1.6)
    # the waist's four marks, cut right through so the turbine's light shows from outside
    for ang in (0, 90, 180, 270):
        cut_mark_in_wall(V, 19, 14, ang, 13, fill="hope_crystal")
    # second herd terrace inside the bowl (walkable shelf with a glass rail) and ramps up to it
    disc(V, 6, 25, "skystone_tiles", r_in=19)
    rail(V, 7, 19.6)
    for a0 in (20, 200):
        ramp(V, 1, 6, 19.5, 24.5, a0)
    # crown: the flyers' open deck, lantern posts all round
    disc(V, 29, 24, "hope_quartz_bricks", r_in=16)
    rail(V, 30, 24.2)
    for t in range(0, 360, 30):
        a = R(t + 15)
        lantern_post(V, math.floor(math.cos(a) * 20), math.floor(math.sin(a) * 20), 30, 3)
    # lamp ring under the bowl's rim
    for t in range(0, 360, 15):
        a = R(t)
        V.put(math.floor(math.cos(a) * 26.6), math.floor(math.sin(a) * 26.6), 9, "hope_lamp")
    # the waist sits between z 13 and 25 so the 13-tall mark fits; keep the quartz solid round it
    o = voxel_object("HS A1 hourglass", V, (ox, 0, 0))
    turbine("HS A1 turbine", 11, 13, blades=6, origin=(ox, 0, 12.5))
    herd(ox, 0, 1, 15, 14, 1)
    herd(ox + 0, 0, 7, 0, 0, 2)
    for k, a in enumerate(range(0, 360, 60)):                  # a few mobs out on the terrace shelf
        mob_bubble(ox + math.cos(R(a)) * 22, math.sin(R(a)) * 22, 7, list(MOB_RGB)[k % 7], k * 7)
    return o


# ================================================================ A2: turbine drum
def take_a2(ox):
    V = Vox()
    disc(V, 0, 26, "skystone_tiles")
    underside(V, 0, 26, 8, 2.8)
    H = 22
    for z in range(1, H):
        # louvred turbine fins all round: 36 angled fins in Skystone pillar with glass between
        for f in range(36):
            base = R(f * 10)
            for s in np.arange(0, 3.0, 0.5):                  # each fin runs 3 blocks, skewed like a turbine vane
                a = base + R(6) * s
                rr = 26 - s * 0.6
                V.put(math.floor(math.cos(a) * rr), math.floor(math.sin(a) * rr), z,
                      "skystone_pillar" if z not in (1, H - 1) else "hope_quartz_bricks")
        ring(V, z, 24.6, "nebula_glass_blue", 0.8)              # the glass skin inside the fins: no falling out
    ring(V, H, 26.4, "hope_inlay", 2.5)
    # the mark as windows on four sides, framed in Hope Lamp
    for ang in (45, 135, 225, 315):
        cut_mark_in_wall(V, 11, 25, ang, 13, fill="hope_crystal")
    # spiral ramp from the floor to the roof deck, inner rail
    ramp(V, 1, H, 19, 24.2, 0, "skystone_tiles")
    # two mid shelves for the herds
    disc(V, 8, 24.2, "skystone_tiles", r_in=18.5); rail(V, 9, 18.9)
    disc(V, 15, 24.2, "skystone_tiles", r_in=18.5); rail(V, 16, 18.9)
    # central shaft wall (low) and roof deck with open middle
    for z in range(1, 3):
        ring(V, z, 11, "nebula_glass_blue")
    disc(V, H, 24.2, "hope_quartz_bricks", r_in=11.5)
    rail(V, H + 1, 11.9)
    for t in range(0, 360, 36):
        a = R(t)
        lantern_post(V, math.floor(math.cos(a) * 22), math.floor(math.sin(a) * 22), H + 1, 4)
    o = voxel_object("HS A2 drum", V, (ox, 0, 0))
    turbine("HS A2 turbine", 10, 17, blades=8, twist=90, origin=(ox, 0, 3))
    herd(ox, 0, 1, 7, 6, 3)
    for k, a in enumerate(range(0, 360, 45)):
        mob_bubble(ox + math.cos(R(a)) * 21.5, math.sin(R(a)) * 21.5, 9, list(MOB_RGB)[k % 7], k * 5)
        mob_bubble(ox + math.cos(R(a + 20)) * 21.5, math.sin(R(a + 20)) * 21.5, 16, list(MOB_RGB)[(k + 3) % 7], k * 9)
    return o


# ================================================================ A3: lotus tiers
def take_a3(ox):
    V = Vox()
    tiers = [(0, 28), (6, 23), (12, 18), (18, 13)]
    shaft = 7.5
    for i, (z, r) in enumerate(tiers):
        disc(V, z, r, "skystone_tiles" if i % 2 == 0 else "hope_quartz_bricks", r_in=shaft)
        ring(V, z, r, "hope_inlay", 1.0)
        rail(V, z + 1, r)                                      # every paddock is walled in glass, two high
        # the riser up to the next tier, with the mark set in crystal on four sides
        if i + 1 < len(tiers):
            nz, nr = tiers[i + 1]
            for k in range(1, nz - z):
                ring(V, z + k, nr + 0.2, "skystone_bricks" if k != 3 else "hope_lamp", 1.2)
            for ang in (0, 90, 180, 270):
                pass
            for a0 in (i * 70, i * 70 + 180):                  # ramps up the riser
                ramp(V, z + 1, nz, nr + 0.4, nr + 3.6, a0)
        ring(V, z + 1, shaft + 0.8, "nebula_glass_blue"); ring(V, z + 2, shaft + 0.8, "nebula_glass_blue")
    underside(V, 0, 28, 10, 2.6)
    # four arched ribs rising from the top tier to hold the halo
    top_z, halo_z, halo_r = 18, 34, 13
    for ang in (45, 135, 225, 315):
        a = R(ang)
        for s in np.linspace(0, 1, 60):
            rr = 13 + 2.5 * math.sin(s * math.pi)
            zz = top_z + 1 + s * (halo_z - top_z - 1)
            for w in (-0.5, 0, 0.5):
                V.put(math.floor(math.cos(a) * rr - math.sin(a) * w), math.floor(math.sin(a) * rr + math.cos(a) * w),
                      zz, "hope_quartz_pillar")
    # the flyers' halo ring, open in the middle, posts round it
    disc(V, halo_z, halo_r + 2.5, "hope_quartz_bricks", r_in=halo_r - 1.5)
    ring(V, halo_z - 1, halo_r + 2.5, "hope_lamp", 0.8)
    for t in range(0, 360, 40):
        a = R(t + 20)
        lantern_post(V, math.floor(math.cos(a) * halo_r), math.floor(math.sin(a) * halo_r), halo_z + 1, 2)
    o = voxel_object("HS A3 lotus", V, (ox, 0, 0))
    turbine("HS A3 turbine", 9, 13, blades=4, twist=120, origin=(ox, 0, 20.5))
    for i, (z, r) in enumerate(tiers):
        rr = (r + (tiers[i + 1][1] if i + 1 < len(tiers) else shaft + 1)) / 2 + 1.5
        for k in range(6 - i):
            a = R(k * 360 / (6 - i) + i * 17)
            mob_bubble(ox + math.cos(a) * rr, math.sin(a) * rr, z + 1, list(MOB_RGB)[(k + i) % 7], k * 6 + i)
    return o


# ================================================================ scene
GAP = 85
take_a1(-GAP); take_a2(0); take_a3(GAP)

# ground far below: a green field with the rescue dome hint under each, to read the float height
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -34))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "HS ground"
g.data.materials.append(flat_mat("HS grass", (0.24, 0.42, 0.16)))
for ox in (-GAP, 0, GAP):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=12, location=(ox, 0, -34), segments=32, ring_count=16)
    d = bpy.context.active_object
    for c in d.users_collection:
        c.objects.unlink(d)
    link(d); d.name = "HS dome"
    d.data.materials.append(flat_mat("HS dome glass", (0.4, 0.7, 1.0), emit=0.4, alpha=0.18))
    d.scale.z = 0.7

# labels
for ox, label in ((-GAP, "A1 Hourglass"), (0, "A2 Turbine drum"), (GAP, "A3 Lotus tiers")):
    cu = bpy.data.curves.new("HS label " + label, "FONT"); cu.body = label; cu.size = 5; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("HS label " + label, cu))
    t.location = (ox, -40, -33.5)
    t.data.materials.append(flat_mat("HS label", (0.85, 0.93, 1.0), emit=2.0))

# world, sun, look
world = bpy.data.worlds.get("HS sky") or bpy.data.worlds.new("HS sky")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.42, 0.62, 0.95, 1); bg.inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("HS sun", bpy.data.lights.new("HS sun", "SUN")))
sun.data.energy = 3.2; sun.rotation_euler = (R(50), R(10), R(35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass


def cam(name, loc, look, lens=35):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_end = 2000
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


cams = {"A1": cam("Cam A1", (-GAP + 62, -82, 26), (-GAP, 0, 12)),
        "A2": cam("Cam A2", (62, -82, 26), (0, 0, 10)),
        "A3": cam("Cam A3", (GAP + 62, -82, 30), (GAP, 0, 15)),
        "all": cam("Cam all", (0, -250, 70), (0, 0, 2), 30),
        "A1in": cam("Cam A1 inside", (-GAP + 18, -12, 5), (-GAP - 6, 8, 3), 20),
        "A2in": cam("Cam A2 inside", (5, -20, 10), (0, 5, 12), 18),
        "A3top": cam("Cam A3 halo", (GAP + 10, -22, 40), (GAP, 0, 24), 22)}
scene.camera = cams["all"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c
        scene.frame_set(60)
        scene.render.filepath = os.path.join(rdir, f"200_hope_{key}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["all"]

try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def _after():
    try:
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    for sp in a.spaces:
                        if sp.type == "VIEW_3D":
                            sp.region_3d.view_perspective = "CAMERA"
                            sp.shading.type = "MATERIAL"
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
