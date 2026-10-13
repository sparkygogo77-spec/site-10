# Pass 205: the Lantern suit, Green, round 1 (lead Blender chat, 2026-10-13).
# Spec (coordinator, from J): a hard-light uniform that forms over the player, toggled with one key; looks only,
# covers the full body; matches that corps' construct textures and lantern; several options per corps, Green first;
# the helmet is optional and lantern-themed, with several helmet options.
# Built on the player's skin boxes (head 8, body 8x12x4, arms and legs 4x12x4), one voxel per model pixel, the suit
# one pixel proud like the skin's outer layer. No published emblem: the chest mark is J's own lantern, as a small
# pixel lantern (body, collars, handle) with a glowing port.
# The suit forms from the feet up over 1.5 s, holds, dissolves and loops (key: "form" on each suit material).
# Takes (cameras "Cam suits", "Cam helmets", "Cam backs", one per suit "Cam S1"...):
#   S1 Corps uniform: dark jade body with bright green panels down the flanks and arms, black gloves and boots,
#      glowing seams, the lantern mark on the chest.
#   S2 Hard-light shell: the whole suit in the translucent green construct texture with bright rims and a brighter
#      core light at the chest; you can see the player through it.
#   S3 Jade plate: segmented dark-jade plates with gold trim and dashed darkest-green stitches (the Dark Lantern's
#      language), gold collar and belt, green light only in the seams.
# Helmets (front row, on S1): H1 lantern cap (a lantern-top dome with collars and a handle crest), H2 glass dome with
# lantern-cage ribs, H3 domino mask and hood, H4 none.
# Builds LanternLive\lantern_suit.blend; textures from LanternLive\tool_tex\.
import math, os
import bpy
import numpy as np

R = math.radians
TEX = os.path.join(FOLDER, "tool_tex")
OUT = os.path.join(FOLDER, "lantern_suit.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Lantern Suit")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Lantern Suit")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 100
win = bpy.context.window
if win:
    win.scene = scene
PX = 1 / 16


def link(o):
    col.objects.link(o)
    return o


def srgb(c):
    return tuple(((v / 255) / 12.92) if v / 255 <= 0.04045 else (((v / 255 + 0.055) / 1.055) ** 2.4) for v in c)


# ------------------------------------------------------------------ materials: per-face colour, glow, and the form sweep
def suit_mat(name, glass=False, textured=False):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    c = N.new("ShaderNodeAttribute"); c.attribute_name = "col"
    g = N.new("ShaderNodeAttribute"); g.attribute_name = "glow"
    base = c.outputs["Color"]
    if textured:
        tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2, 2, 2)
        t = N.new("ShaderNodeTexImage")
        img = bpy.data.images.get("ls_construct") or bpy.data.images.load(os.path.join(TEX, "construct_brick.png"))
        img.name = "ls_construct"; t.image = img; t.interpolation = "Closest"; t.projection = "BOX"
        L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], t.inputs["Vector"])
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        L.new(c.outputs["Color"], mix.inputs["A"]); L.new(t.outputs["Color"], mix.inputs["B"])
        base = mix.outputs["Result"]
    L.new(base, p.inputs["Base Color"]); L.new(base, p.inputs["Emission Color"])
    L.new(g.outputs["Fac"], p.inputs["Emission Strength"])
    p.inputs["Roughness"].default_value = 0.3
    # the form sweep: visible below a rising line, a bright band at its front edge
    tc2 = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc2.outputs["Object"], sep.inputs["Vector"])
    form = N.new("ShaderNodeValue"); form.name = "form"; form.label = "form"; form.outputs[0].default_value = 1.0
    sc = N.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 40.0                # object z is in model px (0 = feet, ~38 = helmet top)
    L.new(form.outputs[0], sc.inputs[0])
    lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"
    L.new(sep.outputs["Z"], lt.inputs[0]); L.new(sc.outputs[0], lt.inputs[1])
    a = 0.5 if glass else 1.0
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = a
    L.new(lt.outputs[0], mul.inputs[0]); L.new(mul.outputs[0], p.inputs["Alpha"])
    # the sweep front glows
    df = N.new("ShaderNodeMath"); df.operation = "SUBTRACT"
    L.new(sc.outputs[0], df.inputs[0]); L.new(sep.outputs["Z"], df.inputs[1])
    band = N.new("ShaderNodeMapRange"); band.inputs["From Min"].default_value = 0.0
    band.inputs["From Max"].default_value = 2.0; band.inputs["To Min"].default_value = 12.0
    band.inputs["To Max"].default_value = 0.0; band.clamp = True
    L.new(df.outputs[0], band.inputs["Value"])
    add = N.new("ShaderNodeMath"); add.operation = "ADD"
    L.new(g.outputs["Fac"], add.inputs[0]); L.new(band.outputs["Result"], add.inputs[1])
    L.new(add.outputs[0], p.inputs["Emission Strength"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    m.use_backface_culling = False
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], 0.86),
        ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)], 0.86),
        ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)], 0.78),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], 0.95),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 1.0),
        ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)], 0.6)]


class V(dict):
    def box(self, x0, x1, y0, y1, z0, z1, rgb, glow=0.0, shell=False):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    if shell and x0 < x < x1 - 1 and y0 < y < y1 - 1 and z0 < z < z1 - 1:
                        continue
                    self[(x, y, z)] = (rgb, glow)

    def paint(self, pred, rgb, glow=None):
        for k, v in list(self.items()):
            if pred(*k):
                self[k] = (rgb, v[1] if glow is None else glow)


def build(name, vox, loc, mat):
    verts, faces, cols, glows = [], [], [], []
    for (x, y, z), (rgb, gl) in vox.items():
        for (dx, dy, dz), quad, shade in DIRS:
            if (x + dx, y + dy, z + dz) in vox:
                continue
            b = len(verts)
            verts.extend((x + a, y + c, z + e) for a, c, e in quad)
            faces.append((b, b + 1, b + 2, b + 3))
            c = srgb(tuple(min(255, v * (shade if gl < 1 else 1)) for v in rgb))
            cols.extend([(*c, 1.0)] * 4); glows.extend([gl] * 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(mat)
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER"); a.data.foreach_set("color", [v for c in cols for v in c])
    g = me.attributes.new("glow", "FLOAT", "CORNER"); g.data.foreach_set("value", glows)
    me.update()
    o = link(bpy.data.objects.new(name, me))
    o.scale = (PX, PX, PX); o.location = loc
    return o


# ------------------------------------------------------------------ the player underneath (z up in px, front is -y)
SKIN = (189, 139, 114); HAIR = (60, 40, 28); SHIRT = (40, 110, 160); PANTS = (40, 40, 110); SHOE = (60, 60, 60)
PLAYER_MAT = None


def player(v):
    v.box(-4, 0, -2, 2, 0, 12, PANTS); v.box(0, 4, -2, 2, 0, 12, PANTS)
    v.box(-4, 0, -2, 2, 0, 2, SHOE); v.box(0, 4, -2, 2, 0, 2, SHOE)
    v.box(-4, 4, -2, 2, 12, 24, SHIRT)
    v.box(-8, -4, -2, 2, 12, 24, SHIRT); v.box(4, 8, -2, 2, 12, 24, SHIRT)
    v.box(-8, -4, -2, 2, 12, 15, SKIN); v.box(4, 8, -2, 2, 12, 15, SKIN)
    v.box(-4, 4, -4, 4, 24, 32, SKIN); v.box(-4, 4, -4, 4, 30, 32, HAIR); v.box(-4, 4, 2, 4, 25, 32, HAIR)
    for x in (-3, 1):
        v.box(x, x + 2, -5, -4, 28, 29, (255, 255, 255)); v.box(x + (1 if x < 0 else 0), x + 1 + (1 if x < 0 else 0), -5, -4, 28, 29, (60, 90, 200))


# ------------------------------------------------------------------ suits: a shell one pixel proud of each box
JADE = (8, 54, 30); JADE_HI = (22, 120, 60); LIME = (60, 230, 110); BLACK = (12, 16, 14); GOLD = (214, 160, 52)
DEEP = (3, 26, 14); BRIGHT = (170, 255, 190)


def shell_boxes():
    """(name, x0, x1, y0, y1, z0, z1) of the suit layer: body, arms, legs (head handled by helmets)."""
    return [("legR", -5, 0, -3, 3, 0, 13), ("legL", 0, 5, -3, 3, 0, 13), ("body", -5, 5, -3, 3, 12, 25),
            ("armR", -9, -4, -3, 3, 12, 25), ("armL", 4, 9, -3, 3, 12, 25)]


def lantern_mark(v, cx, z0, rgb_body, rgb_trim, glow_port):
    """J's own lantern as a 5x7 pixel mark on the chest front (y = -3)."""
    y = -4
    rows = [".###.", ".#.#.", "#####", ".#O#.", ".#O#.", "#####"]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = cx - 2 + i; z = z0 + 6 - j
            if ch == "O":
                v[(x, y, z)] = (BRIGHT, glow_port)
            elif j in (0, 1, 2, 5):
                v[(x, y, z)] = (rgb_trim, 0.0 if rgb_trim != LIME else 2.0)
            else:
                v[(x, y, z)] = (rgb_body, 0.0)


def suit_s1(v):
    for n, *b in shell_boxes():
        v.box(*b, JADE, shell=True)
    # bright green flank panels and arm stripes
    v.paint(lambda x, y, z: x in (-5, 4) and 12 <= z < 25, LIME, 1.5)
    v.paint(lambda x, y, z: x in (-9, 8) and 13 <= z < 25, LIME, 1.5)
    v.paint(lambda x, y, z: x in (-5, 4) and z < 13 and z > 2, JADE_HI)
    # gloves and boots
    v.paint(lambda x, y, z: (x <= -5 or x >= 5) and 12 <= z < 16 and abs(x) >= 5, BLACK, 0.0)
    v.paint(lambda x, y, z: z < 4, BLACK, 0.0)
    # glowing seams: belt and collar
    v.paint(lambda x, y, z: z == 12 and -5 <= x < 5, LIME, 2.5)
    v.paint(lambda x, y, z: z == 24 and -5 <= x < 5, LIME, 2.5)
    lantern_mark(v, 0, 15, JADE, LIME, 4.0)


def suit_s2(v):
    for n, *b in shell_boxes():
        v.box(*b, (110, 255, 150), 0.8, shell=True)
    # bright rims on every box edge
    for n, x0, x1, y0, y1, z0, z1 in shell_boxes():
        for k in list(v):
            x, y, z = k
            if x0 <= x < x1 and y0 <= y < y1 and z0 <= z < z1:
                e = (x in (x0, x1 - 1)) + (y in (y0, y1 - 1)) + (z in (z0, z1 - 1))
                if e >= 2:
                    v[k] = (BRIGHT, 3.5)
    v.box(-1, 1, -4, -3, 18, 21, BRIGHT, 8.0)                 # chest core light
    lantern_mark(v, 0, 15, (110, 255, 150), BRIGHT, 6.0)


def suit_s3(v):
    for n, *b in shell_boxes():
        v.box(*b, JADE, shell=True)
    # plate segments: darker bands every 3 px with dashed darkest-green stitches down the middle
    v.paint(lambda x, y, z: z % 3 == 0, DEEP)
    v.paint(lambda x, y, z: y == -3 and x in (-1, 0) and z % 2 == 0 and z > 2, DEEP)
    for x0 in (-9, 4):                                         # stitch down each arm
        v.paint(lambda x, y, z, x0=x0: y == -3 and x == x0 + 2 and z % 2 == 0 and z >= 12, DEEP)
    # gold trim: collar, belt, cuffs, knee bands
    v.paint(lambda x, y, z: z in (24, 12) and -5 <= x < 5, GOLD)
    v.paint(lambda x, y, z: z == 15 and (x < -4 or x > 3), GOLD)
    v.paint(lambda x, y, z: z == 6, GOLD)
    # green light only in the seams between plates on the chest
    v.paint(lambda x, y, z: y == -3 and z in (14, 17, 20) and -5 < x < 4 and x not in (-1, 0), LIME, 2.2)
    lantern_mark(v, 0, 15, JADE, GOLD, 4.0)


def helmet(v, kind, base_rgb=JADE, trim=GOLD, glow_rgb=LIME):
    if kind == "H1":                                           # lantern cap
        v.box(-5, 5, -5, 5, 27, 34, base_rgb, shell=True)
        for k in [k for k in v if -4 <= k[0] <= 3 and k[1] == -5 and 27 <= k[2] <= 30]:
            del v[k]
        v.box(-5, 5, -5, 5, 30, 31, trim)                       # collar
        v.box(-4, 4, -4, 4, 34, 35, trim)                       # top plate
        v.box(-1, 1, -1, 1, 35, 37, trim); v.box(-2, 2, -1, 1, 37, 38, trim)   # handle crest
        v.box(-1, 1, -6, -5, 31, 33, glow_rgb, 4.0)             # port light on the brow
    elif kind == "H2":                                         # glass dome with cage ribs
        for x in range(-6, 6):
            for y in range(-6, 6):
                for z in range(24, 38):
                    d = math.sqrt((x + 0.5) ** 2 + (y + 0.5) ** 2 + ((z - 29.5) * 0.9) ** 2)
                    if 6.0 <= d < 7.0:
                        rib = (x in (-1, 0) or y in (-1, 0)) and z > 30
                        v[(x, y, z)] = (trim, 0.0) if rib else ((150, 255, 190), 1.0)
        v.box(-6, 6, -6, 6, 24, 25, trim)
    elif kind == "H3":                                         # domino mask and hood
        v.box(-5, 5, -5, 5, 26, 34, base_rgb, shell=True)
        for k in [k for k in v if -4 <= k[0] <= 3 and k[1] == -5 and 24 <= k[2] <= 33]:
            del v[k]
        v.box(-5, 5, -6, -5, 27, 30, base_rgb)                 # the mask band over the eyes
        for x in (-3, 1):
            v.box(x, x + 2, -7, -6, 28, 29, BRIGHT, 4.0)        # eye slits
        v.box(-5, 5, 4, 5, 18, 26, base_rgb)                    # hood falls down the back


# ------------------------------------------------------------------ build the line-up
PLAYER_MAT = bpy.data.materials.get("LS player") or bpy.data.materials.new("LS player")
PLAYER_MAT.use_nodes = True
nt = PLAYER_MAT.node_tree
attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_name = "col"
nt.links.new(attr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])

MATS = {"S1": suit_mat("LS suit S1"), "S2": suit_mat("LS suit S2", glass=True, textured=True), "S3": suit_mat("LS suit S3")}
SUITS = {"S1": suit_s1, "S2": suit_s2, "S3": suit_s3}
suit_objs = []
for i, (key, fn) in enumerate(SUITS.items()):
    x = i * 2.2
    pv = V(); player(pv); build(f"LS {key} player", pv, (x, 0, 0), PLAYER_MAT)
    sv = V(); fn(sv)
    hk = {"S1": "H1", "S2": "H2", "S3": "H3"}[key]
    helmet(sv, hk, base_rgb=JADE if key != "S2" else (110, 255, 150), trim=GOLD if key != "S2" else BRIGHT)
    suit_objs.append(build(f"LS {key} suit", sv, (x, 0, 0), MATS[key]))
    cu = bpy.data.curves.new("LS label " + key, "FONT")
    cu.body = {"S1": "S1 Corps uniform", "S2": "S2 Hard-light shell", "S3": "S3 Jade plate"}[key]
    cu.size = 0.22; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("LS label " + key, cu)); t.location = (x, -0.6, 0.01)

# helmet row on S1 bodies
for j, hk in enumerate(("H1", "H2", "H3", "H4")):
    x = 8.0 + j * 2.2; y = 0.0
    pv = V(); player(pv); build(f"LS {hk} player", pv, (x, y, 0), PLAYER_MAT)
    sv = V(); suit_s1(sv)
    if hk != "H4":
        helmet(sv, hk)
    suit_objs.append(build(f"LS {hk} suit", sv, (x, y, 0), MATS["S1"]))
    cu = bpy.data.curves.new("LS label " + hk, "FONT")
    cu.body = {"H1": "H1 Lantern cap", "H2": "H2 Glass dome", "H3": "H3 Mask + hood", "H4": "H4 None"}[hk]
    cu.size = 0.22; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("LS label " + hk, cu)); t.location = (x, y - 0.6, 0.01)

lab = bpy.data.materials.new("LS label"); lab.use_nodes = True
lab.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.8, 1, 0.85, 1)
lab.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2
for o in col.objects:
    if o.name.startswith("LS label"):
        o.data.materials.append(lab)

# the form animation: feet to head in 1.5 s, hold, dissolve top-down, gone, loop
for m in MATS.values():
    sock = m.node_tree.nodes["form"].outputs[0]
    for f, val in ((1, 0.0), (31, 1.0), (75, 1.0), (90, 0.0), (101, 0.0)):
        sock.default_value = val; sock.keyframe_insert("default_value", frame=f)

bpy.ops.mesh.primitive_plane_add(size=60, location=(7, 2, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "LS floor"
gm = bpy.data.materials.new("LS floor"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.14, 0.13, 1)
g.data.materials.append(gm)
world = bpy.data.worlds.get("LS world") or bpy.data.worlds.new("LS world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.1, 0.12, 0.14, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("LS sun", bpy.data.lights.new("LS sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(50), R(-10), R(-25))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


cams = {"suits": cam("Cam suits", (2.6, -7.5, 1.7), (2.2, 0, 1.0), 40),
        "helmets": cam("Cam helmets", (11.3, -10.5, 2.0), (11.3, 0, 1.2), 40),
        "backs": cam("Cam backs", (2.2, 4.0 - 4.5, 1.6), (2.2, 8, 1.0), 40)}
for i, key in enumerate(SUITS):
    cams[key] = cam("Cam " + key, (i * 2.2 + 1.5, -4.6, 1.7), (i * 2.2, 0, 1.1), 45)
cams["backs"].location = (2.6, 7.5, 1.7)
d = np.array((2.2, 0, 1.0)) - np.array((2.6, 7.5, 1.7))
cams["backs"].rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
scene.camera = cams["suits"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c; scene.frame_set(50)
        scene.render.filepath = os.path.join(rdir, f"205_suit_{key}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["suits"]; scene.frame_set(18)
    scene.render.filepath = os.path.join(rdir, "205_suit_forming.png")
    bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["suits"]
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
