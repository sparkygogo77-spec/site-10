# Pass 301: the new Red corps towers, designed round the metals (J, 2026-10-14: "make it use multiple of them and look
# well designed"). Same three towers, now two-tone: crimson metals for the faces and black metals (the gunmetal from
# corps_metal_recolour.py) for frames, ribs, collars and caps, so each metal reads against the next one; glowing
# redstone in slits and seams; blackstone and polished deepslate for the footings. No quartz, smooth quartz or plain
# nether bricks. Every tower uses at least eight metals:
#   D1 Rage obelisk  - black netherite footing in three tiers; crimson quartz-brick faces framed by black quartz pillars;
#                      crimson chiseled-quartz and gold bands; redstone seams; black iron collar; crimson diamond cap
#   D2 Blood citadel - crimson red-nether-brick keep with black chiseled-nether-brick buttresses and redstone window
#                      slits; crimson quartz-pillar turrets with gold rings and black netherite cones; black iron
#                      battlements; crimson diamond spire ringed with black emerald
#   D3 Furnace gate  - black cracked-nether-brick pillars with crimson copper bands and crimson chiseled-nether-brick
#                      capitals; crimson emerald lintel framed in black chiseled quartz; a crown stepping crimson quartz
#                      bricks and black diamond; BR1 crimson construct lattice in the gate
# Builds LanternLive\red_tower_new3.blend. Needs LanternLive\red_tex (m_*.png crimson, mb_*.png black).
import math, os
import bpy
import numpy as np

R = math.radians
TEX = os.path.join(FOLDER, "red_tex")
OUT = os.path.join(FOLDER, "red_tower_new3.blend")
LIB = os.path.join(FOLDER, "texture_library")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Red Tower New 3")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Red Tower New 3")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 120
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


MATS = ["blackstone", "polished_blackstone_bricks", "chiseled_polished_blackstone", "gilded_blackstone",
        "nether_bricks", "red_nether_bricks", "crimson_nylium", "netherrack", "magma", "crimson_planks",
        "crimson_stem", "shroomlight", "basalt_side", "polished_basalt_side", "coarse_dirt", "grass_block_top",
        "hay_block_side", "smoker_front", "campfire_fire", "construct_brick_red", "nebula_glass_red",
        "sanctuary_blood", "blood_still", "obsidian", "crying_obsidian", "redstone_block",
        "polished_deepslate", "polished_blackstone",
        "m_diamond", "m_emerald", "m_iron", "m_gold", "m_netherite", "m_copper", "m_chiseled_quartz", "m_quartz_bricks", "m_quartz_pillar", "m_red_nether_bricks", "m_chiseled_nether_bricks", "m_cracked_nether_bricks",
        "mb_diamond", "mb_emerald", "mb_iron", "mb_netherite", "mb_chiseled_quartz", "mb_quartz_pillar", "mb_chiseled_nether_bricks", "mb_cracked_nether_bricks"]
GLASSY = {"nebula_glass_red", "construct_brick_red", "campfire_fire"}
GLOW = {"magma": 2.5, "shroomlight": 4.0, "construct_brick_red": 2.0, "campfire_fire": 6.0, "crying_obsidian": 1.2,
        "sanctuary_blood": 0.5, "blood_still": 0.4, "redstone_block": 3.0}
MI = {n: i for i, n in enumerate(MATS)}


def block_mat(name):
    m = bpy.data.materials.get("RT " + name) or bpy.data.materials.new("RT " + name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    t = N.new("ShaderNodeTexImage")
    img = bpy.data.images.get("rt_" + name) or bpy.data.images.load(os.path.join(TEX, name + ".png"))
    img.name = "rt_" + name
    t.image = img; t.interpolation = "Closest"
    L.new(t.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.6
    if name.startswith("m_") or name.startswith("mb_"):                                     # J's crimson metals: polished, like diamond in shaders
        p.inputs["Metallic"].default_value = 0.85; p.inputs["Roughness"].default_value = 0.16
        for nm, v in (("Coat Weight", 0.35), ("Coat Roughness", 0.05)):
            if nm in p.inputs:
                p.inputs[nm].default_value = v
    if name in ("sanctuary_blood", "blood_still"):
        p.inputs["Roughness"].default_value = 0.12
    if name in GLASSY:
        if name == "nebula_glass_red":
            mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; mx.inputs[1].default_value = 0.2
            L.new(t.outputs["Alpha"], mx.inputs[0]); L.new(mx.outputs[0], p.inputs["Alpha"])
            mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["A"].default_value = (0.8, 0.05, 0.05, 1)
            L.new(t.outputs["Alpha"], mix.inputs["Factor"]); L.new(t.outputs["Color"], mix.inputs["B"])
            L.new(mix.outputs["Result"], p.inputs["Base Color"])
            p.inputs["Emission Color"].default_value = (0.9, 0.08, 0.05, 1); p.inputs["Emission Strength"].default_value = 0.5
        else:
            L.new(t.outputs["Alpha"], p.inputs["Alpha"])
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
import json as _json
LIB_INDEX = _json.load(open(os.path.join(LIB, "index.json")))


def diamond_mat():
    m = bpy.data.materials.new("RT diamond block crimson"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled"); t = N.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(TEX, "diamond_block_crimson.png")); t.interpolation = "Closest"
    L.new(t.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Metallic"].default_value = 0.85                  # polished metal, the way the diamond ID shines in shaders
    p.inputs["Roughness"].default_value = 0.16
    for nm, v in (("Coat Weight", 0.35), ("Coat Roughness", 0.05)):
        if nm in p.inputs:
            p.inputs[nm].default_value = v
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


def lib_mat(tex, col, glow=1.6):
    """A library texture as a movie, box-mapped 4 blocks to a tile, glowing like a construct."""
    nm = f"blender_{tex}_{col}.mp4"
    m = bpy.data.materials.new(f"RT lib {tex} {col}"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.25, 0.25, 0.25)
    t = N.new("ShaderNodeTexImage"); t.projection = "BOX"; t.interpolation = "Closest"
    im = bpy.data.images.load(os.path.join(LIB, "blender_mp4", nm)); im.source = "MOVIE"; im.filepath = "//texture_library/blender_mp4/" + nm
    t.image = im
    iu = t.image_user; iu.frame_duration = LIB_INDEX["textures"][tex]["colours"][col]["mp4_frames"]
    iu.frame_start = 1; iu.use_cyclic = True; iu.use_auto_refresh = True
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], t.inputs["Vector"])
    L.new(t.outputs["Color"], p.inputs["Base Color"]); L.new(t.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = glow; p.inputs["Roughness"].default_value = 0.3
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


DIAMOND = diamond_mat()
LIBM = {k: lib_mat(*k) for k in (("br1", "crimson"), ("w1", "crimson"), ("h1", "crimson"), ("r2", "crimson"))}
M = lambda n: MAT_OBJS[MI[n]]
BODY = {"red_nether_bricks": M("m_red_nether_bricks"), "nether_bricks": M("m_red_nether_bricks")}   # the plinth's trim
LOOKS = [("BR1", "br1", "BR1 bricks in crimson on every construct part")]
REMAPS = {tag: dict(BODY, construct_brick_red=LIBM[(t, "crimson")], nebula_glass_red=LIBM[(t, "crimson")]) for tag, t, _ in LOOKS}
ROW = -130.0


def remap(me, table):
    for n, mat in table.items():
        me.materials[MI[n]] = mat
GLASSY_IDX = {MI[n] for n in GLASSY}

DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
        ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
        ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
        ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]
UV = [(0, 0), (1, 0), (1, 1), (0, 1)]


class Vox(dict):
    def put(self, x, y, z, m, keep=False):
        k = (int(math.floor(x)), int(math.floor(y)), int(math.floor(z)))
        if keep and k in self:
            return
        self[k] = MI[m]


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


def disc(V, z, r_out, m, r_in=-1.0, cx=0.0, cy=0.0, sides=0):
    ri = int(math.ceil(r_out)) + 1
    for x in range(-ri, ri + 1):
        for y in range(-ri, ri + 1):
            px, py = x + 0.5, y + 0.5
            if sides:                                              # regular polygon distance
                a = math.atan2(py, px); seg = 2 * math.pi / sides
                d = math.hypot(px, py) * math.cos((a % seg) - seg / 2) / math.cos(seg / 2)
            else:
                d = math.hypot(px, py)
            if r_in < d <= r_out:
                V.put(cx + x, cy + y, z, m)


def ring(V, z, r, m, thick=1.0, cx=0.0, cy=0.0, sides=0):
    disc(V, z, r, m, r - thick, cx, cy, sides)


def box(V, x0, x1, y0, y1, z0, z1, m, hollow=False):
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                if hollow and x0 < x < x1 - 1 and y0 < y < y1 - 1 and z0 < z < z1 - 1:
                    continue
                V.put(x, y, z, m)


# ---------------------------------------------------------------- shared: plinth, steak farms
PLINTH = 8


def plinth(V, r=22):
    """Raised blackstone plinth with a stepped skirt, a crimson-nylium top and two sunken terraces for steak farms."""
    for z in range(PLINTH):
        rr = r + (PLINTH - z) * 0.9
        disc(V, z, rr, "polished_blackstone_bricks" if z % 3 else "chiseled_polished_blackstone", rr - 2.2, sides=8)
        disc(V, z, rr - 2.2, "blackstone", sides=8)
    disc(V, PLINTH, r, "crimson_nylium", sides=8)
    ring(V, PLINTH, r, "red_nether_bricks", 1.0, sides=8)
    for z in (PLINTH + 1,):
        ring(V, z, r, "nether_bricks", 1.0, sides=8)                 # low parapet
    # stair cut down the front (-y) so the field and the tower connect
    for s in range(PLINTH + 1):
        box(V, -2, 3, -int(r + PLINTH * 0.9) + s, -int(r + PLINTH * 0.9) + s + 1, 0, PLINTH - s + 1, "polished_blackstone_bricks")
        for k in range(PLINTH - s + 1, PLINTH + 3):
            V.pop((0, -int(r + PLINTH * 0.9) + s, k), None)


def steak_farm(V, cx, cy, w=8, d=7, z=PLINTH):
    """A fenced cattle pen: coarse-dirt floor, crimson fence (as a crimson-plank kerb and stems), hay bales,
    a smoker and a campfire grill on the side. Returns pen centre for the cows."""
    box(V, cx, cx + w, cy, cy + d, z, z + 1, "coarse_dirt")
    for x in range(cx - 1, cx + w + 1):
        for y in (cy - 1, cy + d):
            V.put(x, y, z + 1, "crimson_planks")
            if (x - cx) % 3 == 0:
                V.put(x, y, z + 2, "crimson_stem")
    for y in range(cy - 1, cy + d + 1):
        for x in (cx - 1, cx + w):
            V.put(x, y, z + 1, "crimson_planks")
            if (y - cy) % 3 == 0:
                V.put(x, y, z + 2, "crimson_stem")
    V.put(cx + 1, cy + d - 2, z + 1, "hay_block_side"); V.put(cx + 2, cy + d - 2, z + 1, "hay_block_side")
    V.put(cx + 1, cy + d - 2, z + 2, "hay_block_side")
    V.put(cx + w + 1, cy + 1, z + 1, "smoker_front"); V.put(cx + w + 1, cy + 3, z + 1, "campfire_fire")
    V.put(cx + w + 1, cy + 2, z + 1, "magma")
    return cx + w / 2, cy + d / 2, z + 1


# ---------------------------------------------------------------- mobs (simple boxes), chains, posts
def mat_flat(name, rgb, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1)
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    return m


def cube(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = name; o.scale = size
    o.data.materials.append(mat)
    return o


MOBS = {"zombie": ((0.25, 0.45, 0.3), (0.6, 0.35, 1.9)), "skeleton": ((0.78, 0.78, 0.74), (0.5, 0.3, 1.95)),
        "spider": ((0.18, 0.15, 0.14), (1.4, 1.0, 0.9)), "hoglin": ((0.62, 0.38, 0.3), (1.0, 1.6, 1.4)),
        "pillager": ((0.3, 0.3, 0.33), (0.6, 0.35, 1.95)), "cow": ((0.25, 0.17, 0.12), (0.9, 1.4, 1.3))}
EYE = mat_flat("RT rage eyes", (1.0, 0.05, 0.02), 12.0)
CHAIN = mat_flat("RT chain", (0.22, 0.22, 0.26))
AURA = mat_flat("RT rage aura", (0.9, 0.05, 0.03), 1.2)


def mob(kind, x, y, z, yaw, enraged=True, tag=""):
    rgb, (w, d, h) = MOBS[kind]
    b = cube(f"RT {kind}{tag}", (x, y, z + h / 2), (w, d, h), mat_flat("RT mob " + kind, rgb))
    b.rotation_euler.z = yaw
    if enraged:
        for s in (-1, 1):
            e = cube(f"RT eye{tag}", (0, 0, 0), (0.12, 0.05, 0.1), EYE)
            e.parent = b; e.location = (s * 0.18, -0.52, 0.36 if h > 1.5 else 0.2)
    return b


def chained(kind, px, py, ang, length, tag):
    """A post with a chain run out to an enraged mob that lunges and snaps back on its tether."""
    post = cube("RT post" + tag, (px, py, 1.0), (0.45, 0.45, 2.0), mat_flat("RT post", (0.12, 0.1, 0.1)))
    cube("RT post cap" + tag, (px, py, 2.1), (0.6, 0.6, 0.2), mat_flat("RT cap", (0.45, 0.08, 0.06), 0.8))
    mx, my = px + math.cos(ang) * length, py + math.sin(ang) * length
    m = mob(kind, mx, my, 0, ang + math.pi / 2, tag=tag)
    # chain: a row of thin links
    n = int(length * 3)
    for i in range(1, n):
        t = i / n
        sag = 0.35 * math.sin(math.pi * t)
        cube(f"RT link{tag}_{i}", (px + (mx - px) * t, py + (my - py) * t, 1.6 - 1.0 * t - sag),
             (0.1, 0.18, 0.1) if i % 2 else (0.18, 0.1, 0.1), CHAIN)
    # lunge animation: strain toward anything, snap back
    for f, k in ((1, 0.0), (9, 0.55), (14, 0.0), (40, 0.0), (47, 0.5), (52, 0.0)):
        m.location.x = mx + math.cos(ang) * k; m.location.y = my + math.sin(ang) * k
        m.keyframe_insert("location", frame=f + (hash(tag) % 30))
    return m


def field(ox, r_in=31, r_out=44, n=22, seed=0):
    """The enraged defence field below the plinth: posts spaced out on scorched ground, chained mobs."""
    rng = np.random.default_rng(seed)
    kinds = ["zombie", "skeleton", "spider", "hoglin", "pillager"]
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.08, 0.08)
        r = rng.uniform(r_in, r_out)
        chained(kinds[i % len(kinds)], ox + math.cos(a) * r, math.sin(a) * r, a + rng.uniform(-0.6, 0.6),
                rng.uniform(2.2, 3.6), f"_{ox}_{i}")


def cows(cx, cy, z, n, tag):
    for i in range(n):
        mob("cow", cx + (i % 3 - 1) * 2.2, cy + (i // 3 - 0.5) * 2.2, z, R(30 * i), enraged=False, tag=f"{tag}{i}")


def rage_orb(name, loc, r=2.4):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=loc)
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = name
    o.data.materials.append(mat_flat("RT rage orb", (0.9, 0.04, 0.02), 3.5))
    lt = link(bpy.data.objects.new(name + " light", bpy.data.lights.new(name + " light", "POINT")))
    lt.data.energy = 6000; lt.data.color = (1.0, 0.15, 0.08); lt.location = loc
    for f, s in ((1, 1.0), (10, 1.12), (20, 1.0), (30, 1.12), (60, 1.0)):            # heartbeat
        o.scale = (s, s, s); o.keyframe_insert("scale", frame=f)
    try:
        fcs = list(o.animation_data.action.fcurves)
    except Exception:
        fcs = [fc for layer in o.animation_data.action.layers for s in layer.strips for cb in s.channelbags
               for fc in cb.fcurves]
    for fc in fcs:
        fc.modifiers.new("CYCLES")
    return o


def blood_fall(V, x, y, z_top, z_bot):
    for z in range(z_bot, z_top):
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            V.put(x + dx, y + dy, z, "sanctuary_blood")
    disc(V, z_bot, 2.2, "blood_still", cx=x, cy=y)


# ================================================================ C1 fang spire
def take_c1(ox):
    V = Vox(); plinth(V)
    H = 52
    for z in range(PLINTH + 1, PLINTH + H):
        t = (z - PLINTH) / H
        r = 8.5 * (1 - t) ** 0.8 + 1.2
        disc(V, z, r, "polished_blackstone_bricks" if (z // 4) % 2 else "blackstone", sides=6)
        if z % 7 == 0:
            ring(V, z, r + 0.6, "gilded_blackstone", 0.8, sides=6)
    # claws: six construct ribs spiralling up and curling out at the top
    for k in range(6):
        for s in np.linspace(0, 1, 140):
            z = PLINTH + 1 + s * (H - 6)
            t = (z - PLINTH) / H
            r = 8.5 * (1 - t) ** 0.8 + 2.2 + 3.5 * max(0, s - 0.75) * 4
            a = R(k * 60) + s * R(110)
            V.put(math.cos(a) * r, math.sin(a) * r, z, "construct_brick_red")
    # two balconies with blood falls to the plinth
    for zb, ang in ((PLINTH + 18, 200), (PLINTH + 30, 20)):
        t = (zb - PLINTH) / H; r = 8.5 * (1 - t) ** 0.8 + 1.2
        a = R(ang)
        cx, cy = math.cos(a) * (r + 2.5), math.sin(a) * (r + 2.5)
        disc(V, zb, 3.2, "red_nether_bricks", cx=cx, cy=cy)
        blood_fall(V, cx + math.cos(a) * 2.5, cy + math.sin(a) * 2.5, zb, PLINTH + 1)
    # red glass crown
    zc = PLINTH + H - 8
    for z in range(zc, zc + 7):
        ring(V, z, 4.2 + (z - zc) * 0.25, "nebula_glass_red", 0.8, sides=6)
    o = voxel_object("RT C1 fang", V, (ox, 0, 0))
    rage_orb("RT C1 orb", (ox, 0, zc + 3.5), 2.2)
    steak_farm_obj(ox, -20, -3); steak_farm_obj(ox, 12, -3)
    return o


FARM_V = {}


def steak_farm_obj(ox, cx, cy):
    V = FARM_V.setdefault(ox, Vox())
    fx, fy, fz = steak_farm(V, cx, cy)
    cows(ox + fx, fy, fz, 5, f"_{ox}_{cx}")
    return fx, fy, fz


# ================================================================ C2 rage furnace
def take_c2(ox):
    V = Vox(); plinth(V)
    H = 26
    for z in range(PLINTH + 1, PLINTH + H):
        ring(V, z, 9, "nether_bricks" if z % 5 else "red_nether_bricks", 1.4, sides=8)
        if z % 6 == 3:
            for k in range(8):                                     # magma heat vents
                a = R(k * 45 + 22.5)
                V.put(math.cos(a) * 8.6, math.sin(a) * 8.6, z, "magma")
                V.put(math.cos(a) * 8.6, math.sin(a) * 8.6, z + 1, "magma")
    disc(V, PLINTH + H, 9, "polished_blackstone_bricks", sides=8)
    for k in range(16):                                            # crenels
        if k % 2 == 0:
            a = R(k * 22.5)
            V.put(math.cos(a) * 8.6, math.sin(a) * 8.6, PLINTH + H + 1, "chiseled_polished_blackstone")
    for k in range(4):                                             # buttress towers
        a = R(45 + k * 90)
        cx, cy = math.cos(a) * 10.5, math.sin(a) * 10.5
        for z in range(PLINTH + 1, PLINTH + H + 6):
            disc(V, z, 2.6, "polished_basalt_side" if z % 4 else "gilded_blackstone", cx=cx, cy=cy)
        disc(V, PLINTH + H + 6, 3.2, "shroomlight", cx=cx, cy=cy)
    # construct cage crown
    zc = PLINTH + H + 1
    for k in range(8):
        a = R(k * 45)
        for s in np.linspace(0, 1, 40):
            r = 7 - 4 * math.sin(s * math.pi * 0.9)
            V.put(math.cos(a) * r, math.sin(a) * r, zc + s * 13, "construct_brick_red")
    o = voxel_object("RT C2 furnace", V, (ox, 0, 0))
    rage_orb("RT C2 orb", (ox, 0, zc + 6.5), 2.6)
    steak_farm_obj(ox, -20, -3); steak_farm_obj(ox, 12, -3)
    return o


# ================================================================ C3 split claw
def take_c3(ox):
    V = Vox(); plinth(V)
    top = PLINTH + 44
    for k in range(3):
        a = R(90 + k * 120)
        for s in np.linspace(0, 1, 220):
            z = PLINTH + 1 + s * (top - PLINTH - 1)
            r = 12 - 10.5 * (s ** 1.6)                         # base wide, bending in toward the orb
            r += 2.0 * math.sin(s * math.pi)                   # a slight outward belly before curling in
            thick = 3.4 * (1 - s) + 0.9
            cx, cy = math.cos(a) * r, math.sin(a) * r
            if s > 0.97:
                break
            ri = int(math.ceil(thick))
            for dx in range(-ri, ri + 1):
                for dy in range(-ri, ri + 1):
                    if dx * dx + dy * dy <= thick * thick:
                        m = "blackstone" if (int(z) // 3) % 2 else "polished_blackstone_bricks"
                        if dx * dx + dy * dy > (thick - 1) ** 2 and int(z) % 9 == 0:
                            m = "construct_brick_red"
                        V.put(cx + dx, cy + dy, z, m)
    # red glass webbing between the horns low down
    for z in range(PLINTH + 1, PLINTH + 12):
        ring(V, z, 11.5 - (z - PLINTH) * 0.2, "nebula_glass_red", 0.8)
    disc(V, PLINTH + 1, 10, "crying_obsidian")
    o = voxel_object("RT C3 claw", V, (ox, 0, 0))
    rage_orb("RT C3 orb", (ox, 0, top - 3), 3.0)
    steak_farm_obj(ox, -20, 0); steak_farm_obj(ox, 12, 0)
    return o



# ================================================================ D1 rage obelisk
def take_d1(ox):
    V = Vox(); plinth(V)
    z0 = PLINTH + 1
    for k, w in enumerate((10, 9, 8)):                             # black netherite footing in three tiers
        box(V, -w, w, -w, w, z0 + k, z0 + k + 1, "mb_netherite")
        for x in range(-w, w):
            for y in (-w, w - 1):
                if (x + k) % 4 == 0:
                    V.put(x, y, z0 + k, "polished_deepslate"); V.put(y, x, z0 + k, "polished_deepslate")
    zb = z0 + 3
    H = 46
    for z in range(zb, zb + H):
        t = (z - zb) / H
        w = int(round(6.5 * (1 - t) + 2.0))
        band = (z - zb) % 8
        m = "m_chiseled_quartz" if band == 0 else "m_gold" if band == 4 and t < 0.75 else "m_quartz_bricks"
        box(V, -w, w, -w, w, z, z + 1, m)
        for sx in (-w, w - 1):                                     # glowing redstone seams
            V.put(sx, 0, z, "redstone_block"); V.put(0, sx, z, "redstone_block")
            V.put(sx, -1, z, "redstone_block" if band in (2, 3, 5, 6) else m); V.put(-1, sx, z, "redstone_block" if band in (2, 3, 5, 6) else m)
        for cx in (-w - 1, w):                                     # black quartz-pillar frames on the corners
            for cy in (-w - 1, w):
                V.put(cx, cy, z, "mb_quartz_pillar")
    zt = zb + H
    box(V, -3, 3, -3, 3, zt, zt + 2, "mb_iron")                    # black iron collar
    for k in range(4):                                             # crimson diamond cap
        box(V, -2 + k // 2, 2 - k // 2, -2 + k // 2, 2 - k // 2, zt + 2 + k, zt + 3 + k, "m_diamond")
    for k in range(4):                                             # BR1 construct claws
        a = R(45 + k * 90)
        for s_ in np.linspace(0, 1, 70):
            r = 2.5 + 6 * s_ ** 1.6
            V.put(math.cos(a) * r, math.sin(a) * r, zt - 6 + s_ * 16 - 6 * s_ ** 3, "construct_brick_red")
    o = voxel_object("RT D1 obelisk", V, (ox, 0, 0))
    rage_orb("RT D1 orb", (ox, 0, zt + 11), 2.2)
    steak_farm_obj(ox, -20, -3); steak_farm_obj(ox, 12, -3)
    return o


# ================================================================ D2 blood citadel
def take_d2(ox):
    V = Vox(); plinth(V)
    H = 24
    z0 = PLINTH + 1
    disc(V, z0, 10.5, "polished_deepslate"); ring(V, z0, 10.5, "mb_netherite", 1.0)
    for z in range(z0 + 1, PLINTH + H):
        m = "m_chiseled_nether_bricks" if z % 8 == 0 else "m_red_nether_bricks"
        ring(V, z, 8.5, m, 1.6)
        for k in range(8):                                         # black chiseled-nether-brick buttresses
            a = R(k * 45)
            V.put(math.cos(a) * 9.1, math.sin(a) * 9.1, z, "mb_chiseled_nether_bricks")
            if z % 8 in (3, 4, 5):                                  # redstone window slits between them
                b = R(k * 45 + 22.5)
                V.put(math.cos(b) * 8.0, math.sin(b) * 8.0, z, "redstone_block")
    ring(V, PLINTH + H, 9.6, "mb_iron", 1.2)
    for k in range(24):                                            # black iron battlements
        if k % 2 == 0:
            a = R(k * 15)
            V.put(math.cos(a) * 9.0, math.sin(a) * 9.0, PLINTH + H + 1, "mb_iron")
    disc(V, PLINTH + H, 8.4, "polished_deepslate")
    tops = []
    for k in range(6):                                             # crimson quartz-pillar turrets
        a = R(k * 60 + 30)
        cx, cy = math.cos(a) * 11.8, math.sin(a) * 11.8
        for z in range(z0, PLINTH + H + 6):
            disc(V, z, 2.3, "m_gold" if z % 7 == 0 else "m_quartz_pillar", cx=cx, cy=cy)
        ring(V, PLINTH + H + 6, 2.9, "mb_iron", 1.0, cx=cx, cy=cy)
        for j in range(6):                                         # black netherite cones
            disc(V, PLINTH + H + 7 + j, 2.9 - j * 0.5, "mb_netherite", cx=cx, cy=cy)
        tops.append((cx, cy, PLINTH + H + 13))
    zs = PLINTH + H + 1
    for j in range(24):                                            # crimson diamond spire, black emerald rings
        r = max(0.6, 4.2 * (1 - j / 24) ** 0.8)
        disc(V, zs + j, r, "mb_emerald" if j % 6 == 5 else "m_diamond")
    for cx, cy, zt in tops:                                        # BR1 construct arcs to the spire
        for s_ in np.linspace(0, 1, 60):
            V.put(cx * (1 - s_), cy * (1 - s_), zt + 8 * math.sin(s_ * math.pi) + s_ * 6, "construct_brick_red")
    o = voxel_object("RT D2 citadel", V, (ox, 0, 0))
    rage_orb("RT D2 orb", (ox, 0, zs + 28), 2.4)
    steak_farm_obj(ox, -20, -3); steak_farm_obj(ox, 12, -3)
    return o


# ================================================================ D3 furnace gate
def take_d3(ox):
    V = Vox(); plinth(V)
    H = 32
    z0 = PLINTH + 1
    for side in (-1, 1):
        x0 = 6 if side > 0 else -11
        box(V, x0 - 1, x0 + 6, -4, 4, z0, z0 + 2, "polished_deepslate")
        box(V, x0 - 1, x0 + 6, -4, 4, z0 + 2, z0 + 3, "mb_netherite")
        for z in range(z0 + 3, PLINTH + H - 3):
            m = "m_copper" if z % 7 == 0 else "mb_cracked_nether_bricks"
            box(V, x0, x0 + 5, -3, 3, z, z + 1, m)
            ix = x0 if side > 0 else x0 + 4                         # redstone on the inner faces
            V.put(ix, -1, z, "redstone_block"); V.put(ix, 0, z, "redstone_block")
        box(V, x0 - 1, x0 + 6, -4, 4, PLINTH + H - 3, PLINTH + H, "m_chiseled_nether_bricks")   # capitals
    zl = PLINTH + H
    box(V, -12, 12, -3, 3, zl, zl + 4, "m_emerald")                 # crimson emerald lintel
    for x in range(-12, 12):                                       # black chiseled-quartz frame
        for y in (-3, 2):
            V.put(x, y, zl, "mb_chiseled_quartz"); V.put(x, y, zl + 3, "mb_chiseled_quartz")
    for k in range(4):                                             # crown: crimson quartz bricks and black diamond
        box(V, -10 + k * 2, 10 - k * 2, -2, 2, zl + 4 + k, zl + 5 + k, "m_quartz_bricks" if k % 2 == 0 else "mb_diamond")
    for x in range(-5, 6):                                         # BR1 construct lattice in the gate
        for z in range(z0, zl):
            if (x + z) % 4 == 0 or (x - z) % 4 == 0:
                V.put(x, 0, z, "construct_brick_red")
    o = voxel_object("RT D3 gate", V, (ox, 0, 0))
    rage_orb("RT D3 orb", (ox, -1.5, zl - 3.5), 2.2)
    steak_farm_obj(ox, -20, -3); steak_farm_obj(ox, 12, -3)
    return o


# ================================================================ scene
GAP = 110
take_d1(-GAP); take_d2(0); take_d3(GAP)
for ox, V in FARM_V.items():
    voxel_object(f"RT farms {ox}", V, (ox, 0, 0))
for i, ox in enumerate((-GAP, 0, GAP)):
    field(ox, seed=i)

# scorched field ground: grass far out, coarse dirt / netherrack near the plinth
G = Vox()
for ox in (-GAP, 0, GAP):
    for x in range(-48, 49):
        for y in range(-48, 49):
            d = math.hypot(x, y)
            if d < 47:
                h = ((x * 73856093) ^ (y * 19349663)) % 11
                G.put(x + ox, y, -1, "netherrack" if d < 31 + h % 3 else "coarse_dirt" if h < 7 - (d - 33) / 3 else "grass_block_top")
voxel_object("RT field ground", G)
bpy.ops.mesh.primitive_plane_add(size=900, location=(0, 0, -1.01))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "RT world ground"; g.data.materials.append(mat_flat("RT grass", (0.2, 0.36, 0.13)))

for ox, label in ((-GAP, "D1 Rage obelisk"), (0, "D2 Blood citadel"), (GAP, "D3 Furnace gate")):
    cu = bpy.data.curves.new("RT label " + label, "FONT"); cu.body = label; cu.size = 5; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("RT label " + label, cu)); t.location = (ox, -54, 0.1)
    t.data.materials.append(mat_flat("RT label", (1.0, 0.75, 0.7), 2.0))

def is_vox(o):
    return o.type == "MESH" and (o.name.startswith("RT C") or o.name.startswith("RT D") or o.name.startswith("RT farms")) and len(o.data.materials) == len(MATS)


base = [o for o in col.objects if not (o.name.startswith("RT world ground") or o.name == "RT sun")]
for i, (tag, t, name) in enumerate(LOOKS):
    if i == 0:
        for o in base:
            if is_vox(o):
                remap(o.data, REMAPS[tag])
    else:
        made = {}
        for o in base:
            c = o.copy()
            if is_vox(o):
                c.data = o.data.copy(); remap(c.data, REMAPS[tag])
            elif o.type == "FONT":
                c.data = o.data.copy()
            c.name = f"{o.name} {tag}"
            if o.parent is None:
                c.location.y += ROW * i
            link(c); made[o.name] = c
        for o in base:
            if o.parent is not None and o.parent.name in made:
                made[o.name].parent = made[o.parent.name]
    cu = bpy.data.curves.new("RT row " + tag, "FONT"); cu.body = name; cu.size = 7; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("RT row " + tag, cu)); tl.location = (0, -64 + ROW * i, 0.1)
    tl.data.materials.append(mat_flat("RT label", (1.0, 0.75, 0.7), 2.0))

world = bpy.data.worlds.get("RT sky") or bpy.data.worlds.new("RT sky")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.32, 0.16, 0.14, 1); bg.inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("RT sun", bpy.data.lights.new("RT sun", "SUN")))
sun.data.energy = 2.6; sun.data.color = (1.0, 0.82, 0.7); sun.rotation_euler = (R(58), R(8), R(25))
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
    c.location = loc; c.data.lens = lens; c.data.clip_end = 3000
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


cams = {"field": cam("Cam field", (14, -58, 2.6), (-4, -34, 1.5), 26),
        "D1": cam("Cam D1", (-GAP + 62, -88, 30), (-GAP, 0, 30), 30),
        "D2": cam("Cam D2", (62, -88, 30), (0, 0, 28), 30),
        "D3": cam("Cam D3", (GAP + 58, -84, 26), (GAP, 0, 24), 30),
        "all": cam("Cam all", (0, -300, 90), (0, 0, 22), 30)}
scene.camera = cams["all"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c; scene.frame_set(9)
        scene.render.filepath = os.path.join(rdir, f"301_red_tower_{key}.png")
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
