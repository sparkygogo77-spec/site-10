# Pass 210: Hope sanctuary, round 2 (lead Blender chat, 2026-10-13).
# J picked A3 Lotus tiers, then: "we can make the power battery taller on top of the base of the hourglass type and
# an open ended cone on the type with some designs meant for flyers to navigate as the villagers. do both".
# All on A3's four walled tiers (unchanged; A3 itself is shown on the left for reference):
#   A4 Battery spire: a tall Blue power battery rises from the top tier, hourglass-shaped (a lower bulb, a pinched
#      waist, an upper bulb, a cap and an arched handle), ribbed in Hope Quartz with hard-light glass walls, a lamp
#      core running its whole height, the Hope mark in crystal on four sides, the turbine turning in the lower bulb.
#   A5 Flyer cone: an open-ended cone opening upward off the top tier, a lattice of ribs and lit rings (open between
#      them, so flyers can pass through anywhere), with a flight course inside: glowing hoops up a spiral, guide
#      lights between them, perches with lantern posts on the ribs, and a landing ring round the open top.
#   A6 Both: the battery spire standing in the middle of the flyer cone, the hoops spiralling round it.
# Same blocks as pass 200 (Skystone, Hope Quartz, Hope Lamp, blue construct brick, nebula glass, Hope crystal).
# Cameras "Cam A3".."Cam A6", "Cam A5 course" and "Cam A6 inside" (down into the cone), "Cam all". Builds LanternLive\hope_sanctuary2.blend.
import math, os
import bpy
import numpy as np

R = math.radians
TEX = os.path.join(FOLDER, "hope_tex")
OUT = os.path.join(FOLDER, "hope_sanctuary2.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Hope Sanctuary Two")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Hope Sanctuary Two")
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




def a3_base(V):
    """A3's four walled tiers, shaft wall and underside (no halo or arches)."""
    tiers = [(0, 28), (6, 23), (12, 18), (18, 13)]
    shaft = 7.5
    for i, (z, r) in enumerate(tiers):
        disc(V, z, r, "skystone_tiles" if i % 2 == 0 else "hope_quartz_bricks", r_in=shaft if i < 3 else -1)
        ring(V, z, r, "hope_inlay", 1.0)
        rail(V, z + 1, r)
        if i + 1 < len(tiers):
            nz, nr = tiers[i + 1]
            for k in range(1, nz - z):
                ring(V, z + k, nr + 0.2, "skystone_bricks" if k != 3 else "hope_lamp", 1.2)
            for a0 in (i * 70, i * 70 + 180):
                ramp(V, z + 1, nz, nr + 0.4, nr + 3.6, a0)
            ring(V, z + 1, shaft + 0.8, "nebula_glass_blue"); ring(V, z + 2, shaft + 0.8, "nebula_glass_blue")
    underside(V, 0, 28, 10, 2.6)
    return tiers


def herd_on_tiers(ox, tiers, shaft=7.5):
    for i, (z, r) in enumerate(tiers[:3]):
        rr = (r + tiers[i + 1][1]) / 2 + 1.5
        for k in range(6 - i):
            a = R(k * 360 / (6 - i) + i * 17)
            mob_bubble(ox + math.cos(a) * rr, math.sin(a) * rr, z + 1, list(MOB_RGB)[(k + i) % 7], k * 6 + i)


def battery_radius(z, z0=19):
    t = z - z0
    if t < 2:
        return 8.0                                              # foot
    if t < 15:
        return 6.0 + 1.8 * math.sin(math.pi * (t - 2) / 13)   # lower bulb
    if t < 20:
        return 3.6                                              # waist
    if t < 33:
        return 5.2 + 1.5 * math.sin(math.pi * (t - 20) / 13)  # upper bulb
    return 6.8                                                  # cap


def battery_spire(V, z0=19):
    top = z0 + 35
    for z in range(z0, top):
        r = battery_radius(z, z0)
        t = z - z0
        if t < 2 or t >= 33:
            disc(V, z, r, "hope_quartz_bricks")
            ring(V, z, r, "hope_inlay", 1.0)
            continue
        ring(V, z, r, "construct_brick_blue", 1.0)               # hard-light glass wall
        if t % 6 == 0:
            ring(V, z, r + 0.6, "hope_inlay", 1.0)               # bands
        for k in range(8):                                       # ribs
            a = R(k * 45 + 22.5)
            V.put(math.cos(a) * (r + 0.5), math.sin(a) * (r + 0.5), z, "hope_quartz_pillar")
        disc(V, z, 1.6, "hope_lamp")                             # lamp core all the way up
    for ang in (0, 90, 180, 270):
        cut_mark_in_wall(V, z0 + 8, battery_radius(z0 + 8, z0), ang, 9, fill="hope_crystal")
    # arched handle over the cap
    for s in np.linspace(0, math.pi, 50):
        x = 5.5 * math.cos(s); z = top + 1 + 6 * math.sin(s)
        for dy in (-0.5, 0.0, 0.5):
            V.put(x, dy, z, "hope_quartz_pillar")
    V.put(0, 0, top, "hope_lamp"); V.put(0, 0, top + 1, "hope_lamp")
    return top


def hoop(V, cx, cy, cz, tang, r=2.6, m="construct_brick_blue"):
    """A vertical ring facing along the flight path."""
    tx, ty = math.cos(tang), math.sin(tang)
    ux, uy = -ty, tx
    for th in np.linspace(0, 2 * math.pi, 48):
        x = cx + r * math.cos(th) * ux; y = cy + r * math.cos(th) * uy; z = cz + r * math.sin(th)
        V.put(x, y, z, m)


def flyer_cone(V, z0=19, z1=46, r0=9.0, r1=26.5, spiral_r=None):
    def rad(z):
        return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    # ribs up the cone and lit rings round it, open between
    for k in range(16):
        a = R(k * 22.5)
        for z in range(z0 + 1, z1 + 1):
            V.put(math.cos(a) * rad(z), math.sin(a) * rad(z), z, "hope_quartz_pillar")
    for z in range(z0 + 3, z1, 6):
        ring(V, z, rad(z) + 0.5, "hope_lamp" if (z // 6) % 2 else "hope_inlay", 1.0)
    # landing ring round the open top, glass rail on the outside
    disc(V, z1, r1 + 2.5, "hope_quartz_bricks", r_in=r1 - 1.0)
    rail(V, z1 + 1, r1 + 2.5)
    for t in range(0, 360, 30):
        a = R(t + 15)
        lantern_post(V, math.cos(a) * (r1 + 1), math.sin(a) * (r1 + 1), z1 + 1, 2)
    # flight course: hoops up a spiral inside, guide lights between them
    turns, n = 1.6, 11
    for i in range(n):
        s = i / (n - 1)
        z = z0 + 4 + s * (z1 - z0 - 7)
        rr = spiral_r(z) if spiral_r else rad(z) * 0.55
        a = s * turns * 2 * math.pi
        hoop(V, math.cos(a) * rr, math.sin(a) * rr, z, a + math.pi / 2)
        if i < n - 1:
            for j in range(1, 4):                               # guide lights to the next hoop
                s2 = (i + j / 4) / (n - 1)
                z2 = z0 + 4 + s2 * (z1 - z0 - 7)
                r2 = spiral_r(z2) if spiral_r else rad(z2) * 0.55
                a2 = s2 * turns * 2 * math.pi
                V.put(math.cos(a2) * r2, math.sin(a2) * r2, z2, "hope_lamp")
    # perches on every other rib: a little ledge and a lantern post
    for k in range(0, 16, 2):
        a = R(k * 22.5)
        z = z0 + 8 + (k % 4) * 5
        r = rad(z) - 1.5
        for d in (0, 1):
            for w in (-1, 0, 1):
                V.put(math.cos(a) * (r - d) - math.sin(a) * w, math.sin(a) * (r - d) + math.cos(a) * w, z,
                      "skystone_tiles")
        lantern_post(V, math.cos(a) * (r - 1), math.sin(a) * (r - 1), z + 1, 1)


def flyers(ox, n=4, z0=24, z1=40, rr=None, seed=0):
    """A few Blue flyers on the course (simple stand-ins), bobbing."""
    for i in range(n):
        s = (i + 0.5) / n
        z = z0 + s * (z1 - z0)
        r = rr(z) if rr else 8 + s * 6
        a = s * 1.6 * 2 * math.pi + 0.2
        bpy.ops.mesh.primitive_cube_add(size=1, location=(ox + math.cos(a) * r, math.sin(a) * r, z))
        o = bpy.context.active_object
        for c in o.users_collection:
            c.objects.unlink(o)
        link(o); o.name = f"HS flyer {ox} {i}"; o.scale = (0.5, 0.4, 1.2)
        o.data.materials.append(flat_mat("HS flyer", (0.15, 0.3, 0.75), emit=0.6))


def take_a4(ox):
    V = Vox(); tiers = a3_base(V); battery_spire(V)
    o = voxel_object("HS A4 battery spire", V, (ox, 0, 0))
    turbine("HS A4 turbine", 5, 10, blades=4, twist=120, origin=(ox, 0, 22.5))
    herd_on_tiers(ox, tiers)
    return o


def take_a5(ox):
    V = Vox(); tiers = a3_base(V); flyer_cone(V)
    o = voxel_object("HS A5 flyer cone", V, (ox, 0, 0))
    turbine("HS A5 turbine", 9, 13, blades=4, twist=120, origin=(ox, 0, 20.5))
    herd_on_tiers(ox, tiers); flyers(ox, rr=lambda z: (9 + 17.5 * (z - 19) / 27) * 0.55)
    return o


def take_a6(ox):
    V = Vox(); tiers = a3_base(V); battery_spire(V)
    # the hoops spiral between the battery and the cone wall
    flyer_cone(V, spiral_r=lambda z: (battery_radius(z) + (9 + 17.5 * (z - 19) / 27)) / 2 + 1.5)
    o = voxel_object("HS A6 battery + cone", V, (ox, 0, 0))
    turbine("HS A6 turbine", 5, 10, blades=4, twist=120, origin=(ox, 0, 22.5))
    herd_on_tiers(ox, tiers)
    flyers(ox, rr=lambda z: (battery_radius(z) + (9 + 17.5 * (z - 19) / 27)) / 2 + 1.5)
    return o


# ================================================================ scene
GAP = 80
XS = {"A3": -1.5 * GAP, "A4": -0.5 * GAP, "A5": 0.5 * GAP, "A6": 1.5 * GAP}
take_a3(XS["A3"]); take_a4(XS["A4"]); take_a5(XS["A5"]); take_a6(XS["A6"])

bpy.ops.mesh.primitive_plane_add(size=800, location=(0, 0, -34))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "HS ground"
g.data.materials.append(flat_mat("HS grass", (0.24, 0.42, 0.16)))
for key, label in (("A3", "A3 Lotus tiers (picked)"), ("A4", "A4 Battery spire"), ("A5", "A5 Flyer cone"),
                   ("A6", "A6 Battery + cone")):
    cu = bpy.data.curves.new("HS label " + label, "FONT"); cu.body = label; cu.size = 5; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("HS label " + label, cu))
    t.location = (XS[key], -40, -33.5)
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


cams = {**{k: cam("Cam " + k, (x + 72, -112, 50), (x, 0, 30), 35) for k, x in XS.items()},
        "A5top": cam("Cam A5 course", (XS["A5"] + 4, -30, 62), (XS["A5"], 2, 24), 22),
        "A6in": cam("Cam A6 inside", (XS["A6"] + 4, -30, 62), (XS["A6"], 2, 24), 22),
        "all": cam("Cam all", (0, -300, 90), (0, 0, 15), 30)}
scene.camera = cams["all"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c
        scene.frame_set(60)
        scene.render.filepath = os.path.join(rdir, f"210_hope_{key}.png")
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
