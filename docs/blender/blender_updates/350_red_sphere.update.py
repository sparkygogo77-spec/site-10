# Pass 350: Red Lantern sphere facility (J, 2026-10-14: "I need different designs, these are all unsatisfactory
# regardless of the material used. I need an entire red lantern structure which are flyers but also ground creatures,
# perhaps it should be a spherical floating structure, but I still did have the idea of a rage field flowing like heavy
# smoke below and out of the facility and onto the ground causing everything to get enraged and aggressive and forget
# loyalties").
# Three takes, one idea each, all floating spheres over a pool of heavy rage smoke that pours out of the underside,
# runs down to the ground and spreads. Flyers circle the sphere; ground creatures fight each other in the smoke
# (zombies on skeletons, wolves on sheep and on each other: loyalties gone).
#   S1 Rage moon       - crimson diamond sphere, a smooth black-metal equator band with eight glowing hangar mouths
#                        (the flyers' doors); smoke falls from one big vent underneath
#   S2 Clutched heart  - smooth black-metal sphere held from below by five crimson-diamond claws (nothing touches the
#                        ground); three glowing claw slashes cut through it (the Red mark); smoke spills between the claws
#   S3 Blood drop      - a BR1 crimson construct-brick teardrop, its tip pointing down and dripping the smoke; two tilted
#                        crimson-diamond rings orbit it as perches for the flyers
# Builds LanternLive\red_sphere.blend. Needs LanternLive\red_tex (preview copies only) and LanternLive\texture_library.
import math, os
import bpy
import numpy as np

R = math.radians
TEX = os.path.join(FOLDER, "red_tex")
LIB = os.path.join(FOLDER, "texture_library")
OUT = os.path.join(FOLDER, "red_sphere.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Red Sphere")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Red Sphere")
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


# ================================================================ S1 rage moon
CZ = 40


def take_s1(ox):
    V = Vox()
    r = 17
    def pick(x, y, z, nx, ny, nz):
        if nz < -0.82:
            return None                                            # the big vent underneath
        if abs(z) < 3.2:                                           # the black equator band
            a = math.degrees(math.atan2(y, x)) % 45
            if abs(z) < 1.8 and 15 < a < 30:
                return "core"                                      # eight glowing hangar mouths
            return "black"
        if abs(abs(z) - 3.7) < 0.6:
            return "redstone"                                      # thin light lines either side of the band
        return "diamond"
    shell(V, CZ, r, pick)
    for z in range(CZ - 17, CZ - 14):                              # a black lip round the vent
        for x in range(-9, 10):
            for y in range(-9, 10):
                d = math.hypot(x + 0.5, y + 0.5)
                if 6 < d <= 8.5 and (x, y, z) not in V:
                    if math.sqrt((x + .5) ** 2 + (y + .5) ** 2 + (z - CZ + .5) ** 2) < r + 0.5:
                        V.put(x, y, z, "black")
    o = voxel_object("RS S1 rage moon", V, (ox, 0, 0))
    rage_orb("RS S1 orb", (ox, 0, CZ), 5.0)
    smoke(ox, [(0, 0, 6.0)], CZ - 16)
    return o


# ================================================================ S2 clutched heart
def take_s2(ox):
    V = Vox()
    r = 14
    slashes = [(-0.38, 0.0), (0.0, 0.0), (0.38, 0.0)]
    def pick(x, y, z, nx, ny, nz):
        if ny < -0.2:                                              # three claw slashes across the front, glowing
            for sx, _ in slashes:
                if abs(nx - sx - 0.25 * nz) < 0.07 and abs(nz) < 0.75:
                    return "core"
        return "black"
    shell(V, CZ, r, pick)
    for k in range(5):                                             # five crimson-diamond claws cupping it from below
        a = R(18 + k * 72)
        for s in np.linspace(0, 1, 160):
            ang = R(-150 + 125 * s)                                # sweep from under the sphere up its side
            rr = r + 1.5 + 2.2 * math.sin(s * math.pi)
            th = 2.4 * (1 - s) + 0.8
            cx, cy, cz = math.cos(a) * rr * math.cos(ang), math.sin(a) * rr * math.cos(ang), CZ + rr * math.sin(ang)
            if s > 0.88:                                           # the tip hooks inward over the top
                cx *= 0.93; cy *= 0.93
            ti = int(math.ceil(th))
            for dx in range(-ti, ti + 1):
                for dy in range(-ti, ti + 1):
                    for dz in range(-ti, ti + 1):
                        if dx * dx + dy * dy + dz * dz <= th * th:
                            V.put(cx + dx, cy + dy, cz + dz, "diamond")
    # the claws meet in a palm under the sphere; leave its centre open so the smoke pours out between the claws
    o = voxel_object("RS S2 clutched heart", V, (ox, 0, 0))
    rage_orb("RS S2 orb", (ox, 0, CZ), 4.5)
    vents = [(math.cos(R(54 + k * 72)) * 10, math.sin(R(54 + k * 72)) * 10, 2.2) for k in range(5)]
    smoke(ox, vents, CZ - 10)
    return o


# ================================================================ S3 blood drop
def take_s3(ox):
    V = Vox()
    r = 14
    def pick(x, y, z, nx, ny, nz):
        if z < 0 and math.hypot(x, y) < 2.2:
            return None                                            # the dripping tip is open
        return "br1"
    shell(V, CZ, r, pick, thick=1.6, drop=0.55)
    for k, tilt in ((0, 22), (1, -28)):                            # two tilted crimson-diamond perch rings
        t = R(tilt); spin = R(k * 70)
        for s in np.linspace(0, 2 * math.pi, 520):
            px, py = math.cos(s) * (r + 7), math.sin(s) * (r + 7)
            y2, z2 = py * math.cos(t), py * math.sin(t)
            x3, y3 = px * math.cos(spin) - y2 * math.sin(spin), px * math.sin(spin) + y2 * math.cos(spin)
            for dz in (0, 1):
                V.put(x3, y3, CZ + z2 + dz, "diamond")
            V.put(x3 * 1.04, y3 * 1.04, CZ + z2, "diamond")
    o = voxel_object("RS S3 blood drop", V, (ox, 0, 0))
    rage_orb("RS S3 orb", (ox, 0, CZ + 1), 4.5)
    smoke(ox, [(0, 0, 2.5)], CZ - int(r * 1.9))
    return o


# ================================================================ scene
GAP = 120
rng = np.random.default_rng(350)
for ox, fn, tag in ((-GAP, take_s1, "S1"), (0, take_s2, "S2"), (GAP, take_s3, "S3")):
    fn(ox); ground(ox); brawls(ox, rng); flock(ox, CZ, 16, 9, rng, tag)
bpy.ops.mesh.primitive_plane_add(size=900, location=(0, 0, -1.01))
g = obj_from_op("RS world ground"); g.data.materials.append(mat_flat("RS far grass", (0.2, 0.36, 0.13)))

for ox, label in ((-GAP, "S1 Rage moon"), (0, "S2 Clutched heart"), (GAP, "S3 Blood drop")):
    cu = bpy.data.curves.new("RS label " + label, "FONT"); cu.body = label; cu.size = 6; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("RS label " + label, cu)); t.location = (ox, -58, 0.1)
    t.data.materials.append(mat_flat("RS label", (1.0, 0.75, 0.7), 2.0))

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
    scene.eevee.volumetric_end = 600; scene.eevee.volumetric_tile_size = "8"; scene.eevee.volumetric_samples = 48
except Exception as e:
    print("volumes:", e)
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
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


cams = {"S1": cam("Cam S1", (-GAP + 50, -92, 26), (-GAP, 0, 24), 28),
        "S2": cam("Cam S2", (50, -92, 26), (0, 0, 24), 28),
        "S3": cam("Cam S3", (GAP + 50, -92, 26), (GAP, 0, 22), 28),
        "all": cam("Cam all", (0, -330, 70), (0, 0, 26), 30)}
scene.camera = cams["all"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c; scene.frame_set(9)
        scene.render.filepath = os.path.join(rdir, f"350_red_sphere_{key}.png")
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
