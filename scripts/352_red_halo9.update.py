# Pass 352: nine Red Lantern halo islands, all built on pass 351's P3 Halo ring (J, 2026-10-14: "P3 should be the base
# for another 9 build attempt structures, i need there to be room for a lot of red lanterns on top, as well as enraged
# mob fields on the floor, and possibly red prison chambers around the island but under only the main surface").
# Every take keeps P3's base: a big ring-shaped crimson-diamond deck floating at z 40 with black rims and a lit edge,
# the red beacon beam, rage smoke falling to an enraged mob field on the ground. New in all nine:
#   - Red Lanterns on top: rows of lantern spots (a glowing block under a black cap, one block each, as in game)
#   - red prison cells hung under the main deck only (black frame, glowing red bars, a mob inside)
#   - a bigger mob field on the ground, everything fighting everything
# What changes per take is the one idea for the deck:
#   H1 Halo rings      - P3 as it was, lanterns in three rings, twelve cells round the rim
#   H2 Full disc       - the hole closed: the most floor for lanterns, a small altar under the beam
#   H3 Amphitheatre    - terraces stepping up toward the hole, a lantern row on every step
#   H4 Spoked wheel    - outer ring plus six spokes to a central hub; lanterns along the spokes
#   H5 Lantern field   - an octagon deck with lanterns on a square grid; cells as one continuous gallery
#   H6 Crescent gate   - the ring opened by a 60 degree gap, a gate for flyers
#   H7 Sunken arena    - a lowered fighting pit inside, lantern ring outside; cells hung on chains
#   H8 Twin halos      - a smaller upper halo as a lantern gallery, ramps down to the main deck
#   H9 Great lantern   - a giant Red Lantern standing in the hole, lantern lines radiating from it
# Builds LanternLive\red_halo9.blend. Needs LanternLive\red_tex (preview copies only) and LanternLive\texture_library.
import math, os
import bpy
import numpy as np

R = math.radians
TEX = os.path.join(FOLDER, "red_tex")
LIB = os.path.join(FOLDER, "texture_library")
OUT = os.path.join(FOLDER, "red_halo9.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Red Halo")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Red Halo")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 120
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


# ---------------------------------------------------------------- materials
def principled(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    m.node_tree.links.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m, p


def tex_mat(name, file, metal=False, glow=0.0):
    m, p = principled("RS " + name)
    N, L = m.node_tree.nodes, m.node_tree.links
    t = N.new("ShaderNodeTexImage"); t.interpolation = "Closest"
    t.image = bpy.data.images.load(os.path.join(TEX, file))
    L.new(t.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.6
    if metal:                                                  # polished, like the diamond ID shines in shaders
        p.inputs["Metallic"].default_value = 0.85; p.inputs["Roughness"].default_value = 0.16
        for nm, v in (("Coat Weight", 0.35), ("Coat Roughness", 0.05)):
            if nm in p.inputs:
                p.inputs[nm].default_value = v
    if glow:
        L.new(t.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = glow
    return m


def lib_mat(tex, colour, glow=1.6):
    """A library texture as a movie, box-mapped, glowing like a construct."""
    import json
    idx = json.load(open(os.path.join(LIB, "index.json")))
    nm = f"blender_{tex}_{colour}.mp4"
    m, p = principled(f"RS lib {tex} {colour}")
    N, L = m.node_tree.nodes, m.node_tree.links
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 1)
    t = N.new("ShaderNodeTexImage"); t.projection = "BOX"; t.interpolation = "Closest"
    im = bpy.data.images.load(os.path.join(LIB, "blender_mp4", nm)); im.source = "MOVIE"
    im.filepath = "//texture_library/blender_mp4/" + nm
    t.image = im
    iu = t.image_user; iu.frame_duration = idx["textures"][tex]["colours"][colour]["mp4_frames"]
    iu.frame_start = 1; iu.use_cyclic = True; iu.use_auto_refresh = True
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], t.inputs["Vector"])
    L.new(t.outputs["Color"], p.inputs["Base Color"]); L.new(t.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = glow; p.inputs["Roughness"].default_value = 0.3
    return m


def mat_flat(name, rgb, emit=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, p = principled(name)
    p.inputs["Base Color"].default_value = (*rgb, 1)
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    return m


MATS = {
    "diamond": tex_mat("crimson diamond", "diamond_block_crimson.png", metal=True),
    "black": tex_mat("smooth black metal", "mb_smooth.png", metal=True),
    "redstone": tex_mat("glowing redstone", "redstone_block.png", glow=3.0),
    "br1": lib_mat("br1", "crimson", glow=0.9),
    "core": mat_flat("RS hangar glow", (1.0, 0.06, 0.03), 2.5),
    "nylium": tex_mat("crimson nylium", "crimson_nylium.png"),
    "netherrack": tex_mat("netherrack", "netherrack.png"),
    "dirt": tex_mat("coarse dirt", "coarse_dirt.png"),
    "grass": tex_mat("grass", "grass_block_top.png"),
    "blackstone": tex_mat("blackstone", "blackstone.png"),
}
NAMES = list(MATS)
MI = {n: i for i, n in enumerate(NAMES)}

# ---------------------------------------------------------------- voxels (outer shell only)
DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
        ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
        ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
        ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]
UV = [(0, 0), (1, 0), (1, 1), (0, 1)]


class Vox(dict):
    def put(self, x, y, z, m):
        self[(int(math.floor(x)), int(math.floor(y)), int(math.floor(z)))] = MI[m]


def voxel_object(name, V, origin=(0, 0, 0)):
    verts, faces, mats, uvs = [], [], [], []
    for (x, y, z), m in V.items():
        for (dx, dy, dz), quad in DIRS:
            if (x + dx, y + dy, z + dz) in V:
                continue
            b = len(verts)
            verts.extend((x + a, y + c, z + e) for a, c, e in quad)
            faces.append((b, b + 1, b + 2, b + 3)); mats.append(m); uvs.extend(UV)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for n in NAMES:
        me.materials.append(MATS[n])
    me.polygons.foreach_set("material_index", mats)
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", [c for uv in uvs for c in uv])
    me.update()
    o = bpy.data.objects.new(name, me); o.location = origin
    return link(o)


def shell(V, cz, r, mat_of, thick=1.6, squash=1.0, drop=0.0):
    """A hollow voxel sphere (or teardrop when drop > 0); mat_of(x, y, z, nx, ny, nz) picks each block or None."""
    ri = int(r * (1 + drop)) + 2
    for x in range(-ri, ri + 1):
        for y in range(-ri, ri + 1):
            for z in range(-ri - int(r * drop * 1.6), ri + 1):
                px, py, pz = x + 0.5, y + 0.5, z + 0.5
                rr = r
                if drop and pz < 0:                            # teardrop: the lower half narrows to a point
                    rr = r * max(0.0, 1 - (-pz / (r * (1 + drop * 1.6)))) ** 0.7
                    d = math.hypot(px, py)
                    if rr - thick < d <= rr and -pz < r * (1 + drop * 1.6):
                        m = mat_of(px, py, pz, px / max(d, 1e-3), py / max(d, 1e-3), -0.3)
                        if m:
                            V.put(x, y, cz + z, m)
                    continue
                d = math.sqrt(px * px + py * py + (pz / squash) ** 2)
                if r - thick < d <= r:
                    m = mat_of(px, py, pz, px / d, py / d, pz / d)
                    if m:
                        V.put(x, y, cz + z, m)


# ---------------------------------------------------------------- the orb, creatures, smoke
def obj_from_op(name):
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = name
    return o


def rage_orb(name, loc, r=3.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=loc)
    o = obj_from_op(name); o.data.materials.append(mat_flat("RS rage orb", (0.9, 0.04, 0.02), 6.0))
    lt = link(bpy.data.objects.new(name + " light", bpy.data.lights.new(name + " light", "POINT")))
    lt.data.energy = 30000; lt.data.color = (1.0, 0.15, 0.08); lt.location = loc
    return o


def cube(name, loc, size, mat, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = obj_from_op(name); o.scale = size; o.rotation_euler.z = rot
    o.data.materials.append(mat)
    return o


EYE = mat_flat("RS rage eyes", (1.0, 0.05, 0.02), 14.0)
MOBS = {"zombie": ((0.25, 0.45, 0.3), (0.6, 0.35, 1.9)), "skeleton": ((0.78, 0.78, 0.74), (0.5, 0.3, 1.95)),
        "wolf": ((0.78, 0.76, 0.72), (0.5, 1.2, 0.85)), "sheep": ((0.9, 0.9, 0.88), (0.9, 1.3, 1.2)),
        "hoglin": ((0.62, 0.38, 0.3), (1.0, 1.6, 1.4)), "pillager": ((0.3, 0.3, 0.33), (0.6, 0.35, 1.95)),
        "cow": ((0.25, 0.17, 0.12), (0.9, 1.4, 1.3)), "villager": ((0.55, 0.4, 0.3), (0.6, 0.4, 1.95))}


def mob(kind, x, y, yaw, tag):
    rgb, (w, d, h) = MOBS[kind]
    b = cube(f"RS {kind}{tag}", (x, y, h / 2), (w, d, h), mat_flat("RS mob " + kind, rgb), yaw)
    for s in (-1, 1):
        e = cube(f"RS eye{tag}{s}", (0, 0, 0), (0.12, 0.05, 0.1), EYE)
        e.parent = b; e.location = (s * 0.18, -0.52, 0.36 if h > 1.5 else 0.2)
    return b


FIGHTS = [("zombie", "skeleton"), ("wolf", "wolf"), ("wolf", "sheep"), ("villager", "villager"),
          ("hoglin", "cow"), ("pillager", "pillager"), ("cow", "cow")]


def brawls(ox, rng, n=14, r0=10, r1=34):
    """Pairs facing off in the smoke: everything turns on whatever is nearest, friends included."""
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(r0, r1)
        x, y = ox + math.cos(a) * r, math.sin(a) * r
        k1, k2 = FIGHTS[i % len(FIGHTS)]
        face = rng.uniform(0, 2 * math.pi)
        dx, dy = math.cos(face) * 0.8, math.sin(face) * 0.8
        m1 = mob(k1, x - dx, y - dy, face - math.pi / 2, f"_{ox}_{i}a")
        m2 = mob(k2, x + dx, y + dy, face + math.pi / 2, f"_{ox}_{i}b")
        for m, s in ((m1, 1), (m2, -1)):                           # lunge at each other and recoil
            base = m.location.copy(); off = (i * 7) % 24
            for f, k in ((1, 0.0), (6, 0.35), (10, -0.1), (24, 0.0)):
                m.location.x = base.x + s * dx * k; m.location.y = base.y + s * dy * k
                m.keyframe_insert("location", frame=f + off)


FLYER = mat_flat("RS flyer", (0.32, 0.03, 0.04))
WING = mat_flat("RS flyer wing", (0.55, 0.05, 0.06), 0.6)


def flyer(name, loc, yaw, flap):
    """A Red Lantern flyer: a crimson body, two glowing membrane wings, rage eyes."""
    b = cube(name, loc, (1.4, 2.8, 1.0), FLYER, yaw)          # big enough to carry a rider
    for s in (-1, 1):
        w = cube(f"{name} wing{s}", (0, 0, 0), (2.2, 0.7, 0.08), WING)
        w.parent = b; w.location = (s * 0.65, 0.1, 0.15); w.rotation_euler.y = s * flap
        e = cube(f"{name} eye{s}", (0, 0, 0), (0.15, 0.06, 0.12), EYE)
        e.parent = b; e.location = (s * 0.22, -0.52, 0.12)
    return b


def flock(ox, cz, r, n, rng, tag):
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
        rr = r + rng.uniform(4, 14); z = cz + rng.uniform(-r * 0.6, r * 0.9)
        flyer(f"RS flyer {tag} {i}", (ox + math.cos(a) * rr, math.sin(a) * rr, z), a, R(rng.uniform(-30, 30)))


SMOKE = None


def smoke_mat():
    """Heavy rage smoke: dark red volume, lumpy noise, faintly lit from inside."""
    global SMOKE
    if SMOKE:
        return SMOKE
    m = bpy.data.materials.new("RS rage smoke"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); v = N.new("ShaderNodeVolumePrincipled")
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.12; nz.inputs["Detail"].default_value = 4; nz.inputs["Roughness"].default_value = 0.6
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.42; ramp.color_ramp.elements[1].position = 0.7
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 1.1
    L.new(tc.outputs["Object"], nz.inputs["Vector"]); L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], mul.inputs[0]); L.new(mul.outputs[0], v.inputs["Density"])
    v.inputs["Color"].default_value = (0.16, 0.01, 0.015, 1)
    v.inputs["Emission Color"].default_value = (0.8, 0.04, 0.02, 1); v.inputs["Emission Strength"].default_value = 0.02
    v.inputs["Anisotropy"].default_value = 0.3
    L.new(v.outputs["Volume"], out.inputs["Volume"])
    SMOKE = m
    return m


def smoke(ox, vents, z_top, pool_r=40):
    """Smoke falls from each vent (x, y, radius) as a widening column and spreads into a low pool on the ground."""
    parts = []
    for i, (vx, vy, vr) in enumerate(vents):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=vr * 2.6, radius2=vr, depth=z_top, location=(ox + vx, vy, z_top / 2))
        parts.append(obj_from_op(f"RS smoke fall {ox} {i}"))
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=pool_r, depth=4.5, location=(ox, 0, 2.25))
    parts.append(obj_from_op(f"RS smoke pool {ox}"))
    m = smoke_mat()
    for p in parts:
        p.data.materials.append(m)
    return parts


def ground(ox, r=52):
    G = Vox()
    for x in range(-r, r + 1):
        for y in range(-r, r + 1):
            d = math.hypot(x, y)
            if d < r:
                h = ((x * 73856093) ^ (y * 19349663)) % 11
                G.put(x, y, -1, "nylium" if d < 18 + h % 4 else "netherrack" if d < 30 + h % 4 else "dirt" if h < 8 - (d - 32) / 3 else "grass")
    return voxel_object(f"RS ground {ox}", G, (ox, 0, 0))



# ================================================================ decks, beacon
def mob_on(kind, x, y, z, yaw, tag):
    m = mob(kind, x, y, yaw, tag); m.location.z += z
    return m


def deck(V, cz, r, sides=8, cx=0.0, cy=0.0, r_in=-1.0, under=0.0):
    """A usable floor: crimson-diamond top, black-metal rim with a parapet every other block, a lit redstone edge
    line just under the rim, and an optional tapered black underside (depth `under`) so it hangs like an island."""
    disc(V, cz, r, "diamond", r_in, cx, cy, sides)
    ring(V, cz, r, "black", 1.2, cx, cy, sides)
    ring(V, cz - 1, r - 0.3, "redstone", 0.7, cx, cy, sides)
    ring(V, cz + 1, r, "black", 1.0, cx, cy, sides)
    if r_in > 0:
        disc(V, cz + 1, r_in + 1.0, "black", r_in, cx, cy, sides)
    for k in range(int(under)):
        rr = r * (1 - (k + 1) / (under + 1)) ** 0.8
        lo = r_in * (1 - (k + 1) / (under + 1)) if r_in > 0 else -1.0
        if rr > lo + 0.5:
            disc(V, cz - 2 - k, rr, "black", lo, cx, cy, sides)


def disc(V, z, r_out, m, r_in=-1.0, cx=0.0, cy=0.0, sides=0):
    ri = int(math.ceil(r_out)) + 1
    for x in range(-ri, ri + 1):
        for y in range(-ri, ri + 1):
            px, py = x + 0.5, y + 0.5
            if sides:
                a = math.atan2(py, px); seg = 2 * math.pi / sides
                d = math.hypot(px, py) * math.cos((a % seg) - seg / 2) / math.cos(seg / 2)
            else:
                d = math.hypot(px, py)
            if r_in < d <= r_out:
                V.put(cx + x, cy + y, z, m)


def ring(V, z, r, m, thick=1.0, cx=0.0, cy=0.0, sides=0):
    disc(V, z, r, m, r - thick, cx, cy, sides)


def column(V, z0, z1, r, m, sides=8, cx=0.0, cy=0.0):
    for z in range(z0, z1):
        disc(V, z, r, m, cx=cx, cy=cy, sides=sides)


def pad(V, z, cx, cy, r=3.2):
    """A flyer landing pad: a lit redstone circle on the deck."""
    ring(V, z, r, "redstone", 0.8, cx, cy)


def pen(ox, z, cx, cy, kinds, tag, rng):
    """Ground creatures on a deck, already turned on each other."""
    for i, k in enumerate(kinds):
        a = rng.uniform(0, 2 * math.pi)
        mob_on(k, ox + cx + math.cos(a) * 2.5, cy + math.sin(a) * 2.5, z + 1, a + math.pi / 2, f"{tag}{i}")


def perched(ox, z, cx, cy, tag):
    flyer(f"RS perched {tag}", (ox + cx, cy, z + 1.6), math.atan2(cy, cx), R(20))


BEAM = None


def beacon(ox, z, cx=0.0, cy=0.0, h=260):
    """The rage beacon: a red beam into the sky, the thing you see from far away."""
    global BEAM
    if BEAM is None:
        BEAM = mat_flat("RS beacon beam", (1.0, 0.05, 0.03), 9.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.0, depth=h, location=(ox + cx, cy, z + h / 2))
    b = obj_from_op(f"RS beam {ox}"); b.data.materials.append(BEAM)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.2, depth=h, location=(ox + cx, cy, z + h / 2))
    g = obj_from_op(f"RS beam glow {ox}"); g.data.materials.append(mat_flat("RS beacon halo", (0.8, 0.02, 0.02), 1.2))
    try:
        g.visible_shadow = False; b.visible_shadow = False
    except Exception:
        pass
    return b



# ================================================================ halo pieces
Z = 40
LANTERNS = [0]


def lantern(V, x, y, z):
    """One Red Lantern spot: a glowing block with a black cap, standing on the deck."""
    V.put(x, y, z + 1, "core"); V.put(x, y, z + 2, "black")
    LANTERNS[0] += 1


def lantern_ring(V, z, r, n, cx=0.0, cy=0.0, skip=None):
    for i in range(n):
        a = 2 * math.pi * i / n
        if skip and skip(a):
            continue
        lantern(V, cx + math.cos(a) * r, cy + math.sin(a) * r, z)


def cage(V, cx, cy, ztop, w=5, h=5):
    """A red prison cell hung under the deck: black frame and floor, glowing bars on the sides."""
    x0, y0 = int(cx - w // 2), int(cy - w // 2)
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + w):
            for z in range(ztop - h, ztop):
                ex = x in (x0, x0 + w - 1); ey = y in (y0, y0 + w - 1); ez = z in (ztop - h, ztop - 1)
                if ez:
                    V.put(x, y, z, "black")
                elif ex and ey:
                    V.put(x, y, z, "black")
                elif (ex or ey) and (x + y) % 2 == 0:
                    V.put(x, y, z, "redstone")
    return x0 + w / 2, y0 + w / 2, ztop - h + 1


PRISONERS = ["zombie", "skeleton", "pillager", "villager", "wolf", "hoglin"]


def cells(V, r, n, rng, tag, ztop=Z - 1, h=5, chain=0):
    """n cells round the rim, under the main deck only; each holds one enraged mob."""
    out = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        cx, cy = math.cos(a) * r, math.sin(a) * r
        for k in range(chain):                                       # optional chains down to the cell
            V.put(cx - 2, cy, ztop - k, "black"); V.put(cx + 2, cy, ztop - k, "black")
        out.append(cage(V, cx, cy, ztop - chain, h=h))
    return out


def fill_cells(spots, rng, tag):
    for i, (x, y, z) in enumerate(spots):
        mob_on(PRISONERS[i % len(PRISONERS)], x - 0.5, y - 0.5, z - 0.5, rng.uniform(0, 6.3), f"_{tag}_cell{i}")


def core_above(tag, z=Z + 18):
    pass


def finish(V, name, tag, rng, orb_z=Z + 18, core=True, vents=((0, 0, 9.0),), beam_z=None):
    if core:
        shell(V, orb_z, 7, lambda *a: "black", thick=7)
        ring(V, orb_z, 7.5, "redstone", 1.0)
    o = voxel_object(f"RS {tag} {name}", V)
    rage_orb(f"RS {tag} orb", (0, 0, orb_z), 4.0)
    beacon(0, beam_z if beam_z is not None else orb_z + 7)
    brawls(0, rng, n=22, r0=8, r1=46)                                 # the enraged mob field on the floor
    smoke(0, list(vents), Z - 6, pool_r=46)
    ground(0)
    flock(0, Z + 8, 30, 5, rng, tag)
    return o


# ================================================================ the nine takes
def h1(rng):                                                        # Halo rings
    V = Vox(); deck(V, Z, 32, sides=16, r_in=12, under=2)
    for r, n in ((16, 18), (21, 24), (26, 30)):
        lantern_ring(V, Z, r, n)
    sp = cells(V, 27, 12, rng, "H1")
    finish(V, "Halo rings", "H1", rng); fill_cells(sp, rng, "H1")


def h2(rng):                                                        # Full disc
    V = Vox(); deck(V, Z, 32, sides=16, under=2)
    for x in range(-28, 29, 3):
        for y in range(-28, 29, 3):
            if 5 < math.hypot(x, y) < 29:
                lantern(V, x, y, Z)
    disc(V, Z + 1, 3.5, "black"); disc(V, Z + 2, 2.5, "redstone")    # a small altar under the beam
    sp = cells(V, 27, 12, rng, "H2")
    finish(V, "Full disc", "H2", rng, core=False, orb_z=Z + 6, vents=[(math.cos(R(a)) * 30, math.sin(R(a)) * 30, 3.0) for a in range(0, 360, 60)])
    fill_cells(sp, rng, "H2")


def h3(rng):                                                        # Amphitheatre
    V = Vox(); deck(V, Z, 32, sides=16, r_in=12, under=2)
    for s in range(4):                                               # terraces stepping up toward the hole
        r_out = 28 - s * 4
        disc(V, Z + 1 + s, r_out, "diamond", 12, sides=16)
        ring(V, Z + 1 + s, r_out, "black", 1.0, sides=16)
        lantern_ring(V, Z + 1 + s, r_out - 2, 14 + 6 * (3 - s))
    sp = cells(V, 27, 12, rng, "H3")
    finish(V, "Amphitheatre", "H3", rng, orb_z=Z + 20); fill_cells(sp, rng, "H3")


def h4(rng):                                                        # Spoked wheel
    V = Vox(); deck(V, Z, 32, sides=16, r_in=22, under=2)
    deck(V, Z, 8, sides=8)
    for k in range(6):
        a = R(k * 60)
        for s in np.linspace(8, 23, 60):
            for w in (-1.5, -0.5, 0.5, 1.5):
                V.put(math.cos(a) * s - math.sin(a) * w, math.sin(a) * s + math.cos(a) * w, Z, "diamond")
            V.put(math.cos(a) * s - math.sin(a) * 2.5, math.sin(a) * s + math.cos(a) * 2.5, Z + 1, "black")
            V.put(math.cos(a) * s + math.sin(a) * 2.5, math.sin(a) * s - math.cos(a) * 2.5, Z + 1, "black")
        for s in range(10, 22, 3):
            lantern(V, math.cos(a) * s, math.sin(a) * s, Z)
    lantern_ring(V, Z, 25, 30); lantern_ring(V, Z, 29, 36)
    sp = cells(V, 27, 12, rng, "H4")
    finish(V, "Spoked wheel", "H4", rng, core=False, orb_z=Z + 6,
           vents=[(math.cos(R(a + 30)) * 15, math.sin(R(a + 30)) * 15, 4.0) for a in range(0, 360, 60)])
    fill_cells(sp, rng, "H4")


def h5(rng):                                                        # Lantern field
    V = Vox(); deck(V, Z, 33, sides=8, r_in=10, under=2)
    for x in range(-30, 31, 3):
        for y in range(-30, 31, 3):
            d = max(abs(x), abs(y)) * 0.92 + min(abs(x), abs(y)) * 0.38   # roughly octagonal
            if 12 < math.hypot(x, y) and d < 30:
                lantern(V, x, y, Z)
    sp = cells(V, 28, 24, rng, "H5")                                 # one continuous gallery of cells
    finish(V, "Lantern field", "H5", rng); fill_cells(sp, rng, "H5")


def h6(rng):                                                        # Crescent gate
    V = Vox(); deck(V, Z, 32, sides=16, r_in=12, under=2)
    for (x, y, z) in list(V.keys()):                                  # cut a 60 degree gate facing the front
        a = math.degrees(math.atan2(y + 0.5, x + 0.5)) % 360
        if 240 < a < 300:
            del V[(x, y, z)]
    gate = lambda a: 235 < math.degrees(a) % 360 < 305
    for r, n in ((17, 18), (22, 24), (27, 30)):
        lantern_ring(V, Z, r, n, skip=gate)
    sp = [s for i, s in enumerate(cells(V, 27, 12, rng, "H6"))]
    for (x, y, z) in list(V.keys()):                                  # no cells hang in the gate
        a = math.degrees(math.atan2(y + 0.5, x + 0.5)) % 360
        if 240 < a < 300 and z < Z:
            del V[(x, y, z)]
    sp = [s for s in sp if not (240 < math.degrees(math.atan2(s[1], s[0])) % 360 < 300)]
    finish(V, "Crescent gate", "H6", rng); fill_cells(sp, rng, "H6")


def h7(rng):                                                        # Sunken arena
    V = Vox(); deck(V, Z, 32, sides=16, r_in=21, under=2)
    disc(V, Z - 3, 21, "diamond", 8, sides=16)                       # the pit floor, three blocks down
    for z in range(Z - 2, Z + 1):
        ring(V, z, 21, "black", 1.0, sides=16); ring(V, z, 8.6, "black", 0.8, sides=16)
    ring(V, Z - 4, 21, "redstone", 1.0, sides=16)
    lantern_ring(V, Z, 25, 30); lantern_ring(V, Z, 29, 36)
    for i in range(8):                                               # enraged mobs fighting in the pit too
        a = 2 * math.pi * i / 8
        mob_on(PRISONERS[i % 6], math.cos(a) * 14, math.sin(a) * 14, Z - 2, a, f"_H7_pit{i}")
    sp = cells(V, 27, 12, rng, "H7", chain=4)
    finish(V, "Sunken arena", "H7", rng); fill_cells(sp, rng, "H7")


def h8(rng):                                                        # Twin halos
    V = Vox(); deck(V, Z, 32, sides=16, r_in=12, under=2)
    deck(V, Z + 10, 20, sides=16, r_in=12)                           # the upper lantern gallery
    for k in range(4):                                               # four ramps down to the main deck
        a = R(45 + k * 90)
        for s in np.linspace(0, 1, 50):
            r = 18 + 8 * s; z = Z + 10 - 10 * s
            for w in (-1, 0, 1):
                V.put(math.cos(a) * r - math.sin(a) * w, math.sin(a) * r + math.cos(a) * w, z, "diamond")
    lantern_ring(V, Z + 10, 16, 20); lantern_ring(V, Z + 10, 18.5, 26)
    lantern_ring(V, Z, 28, 34)
    sp = cells(V, 27, 12, rng, "H8")
    finish(V, "Twin halos", "H8", rng, orb_z=Z + 26); fill_cells(sp, rng, "H8")


def h9(rng):                                                        # Great lantern
    V = Vox(); deck(V, Z, 32, sides=16, r_in=12, under=2)
    disc(V, Z, 12.5, "black", sides=8)                               # the hole becomes a plaza for one giant lantern
    disc(V, Z + 1, 6, "black", sides=4); disc(V, Z + 14, 6, "black", sides=4)
    for z in range(Z + 2, Z + 14):                                   # a giant Red Lantern: black corners, glowing sides
        disc(V, z, 5, "core", sides=4); disc(V, z, 5.6, "black", 5.0, sides=4)
    disc(V, Z + 15, 3, "black", sides=4)
    for k in range(12):                                              # lantern lines radiating from it
        a = R(k * 30)
        for s in range(15, 30, 3):
            lantern(V, math.cos(a) * s, math.sin(a) * s, Z)
    sp = cells(V, 27, 12, rng, "H9")
    finish(V, "Great lantern", "H9", rng, core=False, orb_z=Z + 19,
           vents=[(math.cos(R(a + 15)) * 20, math.sin(R(a + 15)) * 20, 3.5) for a in range(0, 360, 60)])
    fill_cells(sp, rng, "H9")


# ================================================================ scene: a 3 x 3 grid, each take built at the origin then moved
TAKES = [("H1", h1, "Halo rings"), ("H2", h2, "Full disc"), ("H3", h3, "Amphitheatre"),
         ("H4", h4, "Spoked wheel"), ("H5", h5, "Lantern field"), ("H6", h6, "Crescent gate"),
         ("H7", h7, "Sunken arena"), ("H8", h8, "Twin halos"), ("H9", h9, "Great lantern")]
SX, SY = 140, 170
POS = {}
rng = np.random.default_rng(352)
for i, (tag, fn, label) in enumerate(TAKES):
    ox, oy = (i % 3 - 1) * SX, (1 - i // 3) * SY
    POS[tag] = (ox, oy)
    before = set(col.objects)
    n0 = LANTERNS[0]
    fn(rng)
    print(tag, "lanterns", LANTERNS[0] - n0)
    cu = bpy.data.curves.new("RS label " + tag, "FONT"); cu.body = f"{tag} {label}"; cu.size = 7; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("RS label " + tag, cu)); t.location = (0, -60, 0.1)
    t.data.materials.append(mat_flat("RS label", (1.0, 0.75, 0.7), 2.0))
    for o in set(col.objects) - before:
        if o.parent is None:
            o.location.x += ox; o.location.y += oy
bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -1.01))
g = obj_from_op("RS world ground"); g.data.materials.append(mat_flat("RS far grass", (0.2, 0.36, 0.13)))

world = bpy.data.worlds.new("RS sky"); world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.30, 0.15, 0.14, 1); bg.inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("RS sun", bpy.data.lights.new("RS sun", "SUN")))
sun.data.energy = 2.6; sun.data.color = (1.0, 0.82, 0.7); sun.rotation_euler = (R(52), R(8), R(25))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
try:
    scene.eevee.volumetric_end = 1200; scene.eevee.volumetric_tile_size = "8"; scene.eevee.volumetric_samples = 48
except Exception as e:
    print("volumes:", e)
scene.render.resolution_x, scene.render.resolution_y = 1440, 810
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass


def cam(name, loc, look, lens=35):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_end = 3000
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c




cams = {tag: cam("Cam " + tag, (POS[tag][0] + 52, POS[tag][1] - 78, Z + 44), (POS[tag][0], POS[tag][1], Z - 6), 26)
        for tag, _, _ in TAKES}
cams["all"] = cam("Cam all", (0, -620, 330), (0, 0, 20), 32)
scene.camera = cams["all"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c; scene.frame_set(9)
        scene.render.filepath = os.path.join(rdir, f"352_red_halo_{key}.png")
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
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
