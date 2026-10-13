# Pass 201: Blue squad armour and the Blue ravager's skin, round 1 (lead Blender chat, 2026-10-13).
# J's brief (coordinator thread "Blue Lantern villager behavior"): the squad spawns in blue construct armour with
# hard-light weapons; 2 flyers (ring beams, lasso and slam), a ground warrior (the arc-jump slam hammer) and a rider
# on a blue reskinned ravager (a lance of light). The ravager forms from hard light beside the lantern.
# Built on BlueVillagerModel's proportions (head 8x10x8 with the villager nose, body 8x12x4, arms and legs 4x12x4),
# one voxel per model pixel, armour one pixel proud of the suit, so a pick maps straight onto ModelPart boxes.
# Three takes, a row each (cameras "Cam B1", "Cam B2", "Cam B3", "Cam squads"):
#   B1 Pearl plate: polished Skystone-pale plate with deep-blue trim and a crystal gem on the chest, crested helm.
#      Ravager R1: pale barding plates over a navy hide, chanfron on the face, plated knees.
#   B2 Hard-light shell: translucent construct-blue shell with bright rims, see-through visor.
#      Ravager R2: the whole beast is hard light, translucent blue with glowing edges and a bright core.
#   B3 Night guard: dark Hope-brick blue plate with pale glowing seams, a narrow glowing visor slit, swept fins.
#      Ravager R3: dark plates with glowing seam lines and glowing eyes.
# Each row: flyer (light wings), flyer (lasso coil on the hip), warrior (hammer), rider on the ravager (lance).
# Builds LanternLive\squad_armour.blend.
import math, os
import bpy
import numpy as np

R = math.radians
OUT = os.path.join(FOLDER, "squad_armour.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Squad Armour")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Squad Armour")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 80
win = bpy.context.window
if win:
    win.scene = scene
PX = 1 / 16


def link(o):
    col.objects.link(o)
    return o


def srgb(c):
    return tuple(((v / 255) / 12.92) if v / 255 <= 0.04045 else (((v / 255 + 0.055) / 1.055) ** 2.4) for v in c)


# ---------------------------------------------------------------- one material reading per-face colour / glow
def vox_mat(name, glass):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    c = N.new("ShaderNodeAttribute"); c.attribute_name = "col"
    g = N.new("ShaderNodeAttribute"); g.attribute_name = "glow"
    mt = N.new("ShaderNodeAttribute"); mt.attribute_name = "metal"
    L.new(c.outputs["Color"], p.inputs["Base Color"])
    L.new(c.outputs["Color"], p.inputs["Emission Color"])
    L.new(g.outputs["Fac"], p.inputs["Emission Strength"])
    L.new(mt.outputs["Fac"], p.inputs["Metallic"])
    p.inputs["Roughness"].default_value = 0.32
    if glass:
        p.inputs["Alpha"].default_value = 0.5
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        m.use_backface_culling = False
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


MAT_SOLID = vox_mat("SA solid", False)
MAT_GLASS = vox_mat("SA glass", True)

DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], 0.86),
        ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)], 0.86),
        ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)], 0.78),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], 0.95),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 1.0),
        ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)], 0.6)]


class V(dict):
    """(x, y, z) model px -> (rgb 0-255, glow, glass, metal)."""

    def box(self, x0, x1, y0, y1, z0, z1, rgb, glow=0.0, glass=False, metal=0.0, shell=False):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    if shell and x0 < x < x1 - 1 and y0 < y < y1 - 1 and z0 < z < z1 - 1:
                        continue
                    self[(x, y, z)] = (rgb, glow, glass, metal)

    def paint(self, pred, rgb, glow=None, glass=None, metal=None):
        for k, v in list(self.items()):
            if pred(*k):
                self[k] = (rgb, v[1] if glow is None else glow, v[2] if glass is None else glass,
                           v[3] if metal is None else metal)


def build(name, vox, loc, rot_z=0.0):
    verts, faces, mats, cols, glows, metals = [], [], [], [], [], []
    for (x, y, z), (rgb, gl, glass, metal) in vox.items():
        for (dx, dy, dz), quad, shade in DIRS:
            n = vox.get((x + dx, y + dy, z + dz))
            if n is not None and (not n[2] or glass):
                continue
            b = len(verts)
            verts.extend((x + a, y + c, z + e) for a, c, e in quad)
            faces.append((b, b + 1, b + 2, b + 3)); mats.append(1 if glass else 0)
            c = srgb(tuple(min(255, v * (shade if gl < 1 else 1)) for v in rgb))
            cols.extend([(*c, 1.0)] * 4); glows.extend([gl] * 4); metals.extend([metal] * 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(MAT_SOLID); me.materials.append(MAT_GLASS)
    me.polygons.foreach_set("material_index", mats)
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER"); a.data.foreach_set("color", [v for c in cols for v in c])
    g = me.attributes.new("glow", "FLOAT", "CORNER"); g.data.foreach_set("value", glows)
    mt = me.attributes.new("metal", "FLOAT", "CORNER"); mt.data.foreach_set("value", metals)
    me.update()
    o = link(bpy.data.objects.new(name, me))
    o.scale = (PX, PX, PX); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


# ---------------------------------------------------------------- the Blue villager underneath (front is -y)
SKIN = (189, 139, 114); HAIR = (89, 60, 44); NAVY = (14, 30, 78); NAVY_HI = (24, 54, 128); LINE = (90, 170, 255)


def villager(v, legs_z=0):
    z = legs_z
    v.box(-4, 0, -2, 2, z, z + 12, NAVY); v.box(0, 4, -2, 2, z, z + 12, NAVY)            # legs
    v.box(-4, 4, -2, 2, z + 12, z + 24, NAVY_HI)                                          # body
    v.box(-8, -4, -2, 2, z + 12, z + 24, NAVY); v.box(4, 8, -2, 2, z + 12, z + 24, NAVY)  # arms
    v.box(-8, -4, -2, 2, z + 12, z + 14, SKIN); v.box(4, 8, -2, 2, z + 12, z + 14, SKIN)  # hands
    v.box(-4, 4, -4, 4, z + 24, z + 34, SKIN)                                              # head
    v.box(-4, 4, -4, 4, z + 32, z + 34, HAIR); v.box(-4, 4, 2, 4, z + 26, z + 34, HAIR)
    v.box(-1, 1, -6, -4, z + 25, z + 29, SKIN)                                             # nose
    for x in (-3, 2):
        v.box(x, x + 1, -5, -4, z + 30, z + 31, (34, 34, 34))                             # eyes (on the face)
    v.box(-1, 1, -3, -2, z + 18, z + 20, LINE, glow=3.0)                                   # suit's chest light


# ---------------------------------------------------------------- armour pieces, one pixel proud of the suit
STYLE = {
    "B1": dict(plate=(214, 232, 250), shade=(148, 182, 226), trim=(42, 58, 104), glow=(120, 205, 255),
               glass=False, metal=0.6, plate_glow=0.0, trim_glow=0.0),
    "B2": dict(plate=(88, 153, 220), shade=(70, 125, 196), trim=(190, 232, 255), glow=(220, 245, 255),
               glass=True, metal=0.0, plate_glow=0.6, trim_glow=4.0),
    "B3": dict(plate=(16, 26, 58), shade=(10, 16, 38), trim=(150, 205, 255), glow=(150, 215, 255),
               glass=False, metal=0.3, plate_glow=0.0, trim_glow=3.0),
}


def armour(v, key, z=0):
    s = STYLE[key]
    P = dict(glow=s["plate_glow"], glass=s["glass"], metal=s["metal"])
    T = dict(glow=s["trim_glow"], glass=s["glass"] and key == "B2", metal=s["metal"])
    # helmet: shell over the head with the face open
    v.box(-5, 5, -5, 5, z + 27, z + 35, s["plate"], shell=True, **P)
    for k in [k for k in v if -4 <= k[0] <= 3 and k[1] == -5 and z + 27 <= k[2] <= z + 31]:
        del v[k]                                                                        # face opening
    v.box(-5, 5, -5, -4, z + 31, z + 32, s["trim"], **T)                                 # brow band
    if key == "B1":                                                                     # crest
        v.box(-1, 1, -5, 5, z + 35, z + 37, s["trim"], **T); v.box(-1, 1, -6, -5, z + 33, z + 36, s["glow"], glow=3.0)
    if key == "B2":                                                                     # see-through visor
        v.box(-4, 4, -6, -5, z + 27, z + 31, (170, 225, 255), glow=1.2, glass=True)
    if key == "B3":                                                                     # slit visor and swept fins
        v.box(-4, 4, -6, -5, z + 27, z + 31, s["plate"], metal=s["metal"])
        v.box(-3, 3, -7, -6, z + 29, z + 30, s["glow"], glow=5.0)
        for sx in (-6, 5):
            for k in range(5):
                v.box(sx, sx + 1, 1 + k, 2 + k, z + 30 + k, z + 32 + k, s["trim"], **T)
    # chest plate and back
    v.box(-5, 5, -3, 3, z + 13, z + 25, s["plate"], shell=True, **P)
    v.box(-5, 5, -3, -2, z + 13, z + 14, s["trim"], **T)                                 # belt
    v.box(-5, 5, -3, -2, z + 24, z + 25, s["trim"], **T)                                 # collar
    v.box(-1, 1, -4, -3, z + 18, z + 21, s["glow"], glow=4.0)                            # chest gem / core
    if key == "B3":
        for zz in (16, 21):
            v.box(-5, 5, -4, -3, z + zz, z + zz + 1, s["trim"], **T)                       # glowing seams
    # pauldrons
    for x0 in (-9, 4):
        v.box(x0, x0 + 5, -3, 3, z + 21, z + 25, s["plate"], shell=True, **P)
        v.box(x0, x0 + 5, -3, 3, z + 21, z + 22, s["trim"], **T)
    # gauntlets
    for x0 in (-9, 3):
        v.box(x0, x0 + 6 if x0 > 0 else x0 + 6, -3, 3, z + 13, z + 16, s["shade"], shell=True, **P)
    # greaves
    for x0 in (-5, 0):
        v.box(x0, x0 + 5, -3, 3, z, z + 7, s["shade"], shell=True, **P)
        v.box(x0, x0 + 5, -3, -2, z + 6, z + 7, s["trim"], **T)
    # keep the hands showing
    for k in [k for k in v if (k[0] <= -8 or k[0] >= 7) and z + 12 <= k[2] < z + 13]:
        pass


def wings(v, key, z=0):
    s = STYLE[key]
    for side in (-1, 1):
        for i in range(14):
            for j in range(10 - abs(i - 4) // 2):
                x = side * (3 + i); zz = z + 26 - i // 3 - j
                v[(x, 4, zz)] = (s["glow"] if j == 0 else s["plate"], 3.0 if j == 0 else 0.9, True, 0.0)


def lasso(v, key, z=0):
    s = STYLE[key]
    for t in range(0, 360, 20):
        a = R(t)
        v[(int(6 + 3 * math.cos(a)), int(-1 + 3 * math.sin(a)), z + 11)] = (s["glow"], 3.5, False, 0.0)
        v[(int(6 + 2.4 * math.cos(a)), int(-1 + 2.4 * math.sin(a)), z + 10)] = (s["glow"], 3.5, False, 0.0)


def hammer(v, key, z=0):
    s = STYLE[key]
    v.box(8, 10, -3, -1, z + 12, z + 36, s["trim"], glow=2.5)                          # haft
    v.box(5, 14, -6, 2, z + 34, z + 41, s["plate"], glow=1.2 if key != "B3" else 0.0, glass=key == "B2",
          metal=s["metal"], shell=True)
    v.box(5, 14, -7, 3, z + 37, z + 38, s["glow"], glow=4.0)                            # glowing band


def lance(v, key, z=0):
    s = STYLE[key]
    for k in range(-30, 10):
        v[(8, k, z + 18 + k // 8)] = (s["glow"], 4.0, False, 0.0)
        v[(9, k, z + 18 + k // 8)] = (s["glow"], 4.0, False, 0.0)
    v.box(6, 12, 8, 10, z + 15, z + 22, s["trim"], **dict(glow=s["trim_glow"], metal=s["metal"]))   # guard


# ---------------------------------------------------------------- the ravager (approximate vanilla proportions)
def ravager(key):
    v = V()
    s = STYLE[key]
    hide = {"B1": (20, 34, 74), "B2": (60, 120, 200), "B3": (10, 14, 30)}[key]
    gl = key == "B2"
    G = dict(glass=gl, glow=0.5 if gl else 0.0)
    for lx in (-8, 4):
        for ly in (-10, 8):
            v.box(lx, lx + 4 + 0, ly, ly + 4, 0, 22, hide, **G)                         # legs
    v.box(-7, 7, -12, 12, 20, 36, hide, **G)                                             # body
    v.box(-5, 5, -22, -12, 26, 36, hide, **G)                                            # neck
    v.box(-8, 8, -34, -22, 22, 42, hide, **G)                                            # head
    v.box(-4, 4, -36, -34, 22, 30, hide, **G)                                            # mouth
    for hx in (-10, 8):
        v.box(hx, hx + 2, -28, -24, 38, 46, (230, 236, 246) if key != "B3" else s["trim"],
              glow=3.0 if key == "B3" else 0.0)                                          # horns
    for ex in (-8, 7):
        v.box(ex, ex + 1, -33, -31, 34, 36, s["glow"] if key != "B1" else (250, 210, 120), glow=5.0)   # eyes
    if key == "B1":                                                                      # barding
        v.box(-8, 8, -12, 12, 26, 37, s["plate"], metal=0.6, shell=True)
        v.box(-8, 8, -13, 13, 26, 27, s["trim"], metal=0.6)
        v.box(-9, 9, -35, -24, 34, 43, s["plate"], metal=0.6, shell=True)              # chanfron
        v.box(-1, 1, -36, -35, 36, 40, s["glow"], glow=4.0)
        for lx in (-9, 3):
            for ly in (-11, 7):
                v.box(lx, lx + 6, ly, ly + 6, 8, 13, s["plate"], metal=0.6, shell=True)
    if key == "B2":                                                                      # bright edges and core
        for k, val in list(v.items()):
            x, y, z = k
            edge = sum(1 for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
                       if (x + d[0], y + d[1], z + d[2]) not in v)
            if edge >= 2:
                v[k] = (s["trim"], 3.5, True, 0.0)
        v.box(-2, 2, -3, 3, 26, 30, (240, 250, 255), glow=8.0)
    if key == "B3":
        for k, val in list(v.items()):
            x, y, z = k
            if val[0] == hide and (y % 6 == 0 or z in (28, 35)):
                v[k] = (s["trim"], 2.5, False, 0.3)
    return v


# ================================================================ scene: three rows
ROWS = {"B1": 0.0, "B2": 15.0, "B3": 30.0}
for key, ox in ROWS.items():
    y = 0.0
    for i, role in enumerate(("flyer", "flyer2", "warrior")):
        v = V(); villager(v); armour(v, key)
        if role == "flyer":
            wings(v, key)
        if role == "flyer2":
            lasso(v, key)
        if role == "warrior":
            hammer(v, key)
        o = build(f"SA {key} {role}", v, (ox + i * 2.2, y, 0))
        if role.startswith("flyer"):                                                     # flyers hover and bob
            for f, dz in ((1, 0.6), (21, 0.85), (41, 0.6)):
                o.location.z = dz; o.keyframe_insert("location", index=2, frame=f + (i * 7))
    rav = build(f"SA {key} ravager", ravager(key), (ox + 9.5, y + 0.5, 0), R(90))
    rider = V(); villager(rider); armour(rider, key); lance(rider, key)
    r = build(f"SA {key} rider", rider, (ox + 9.5, y + 0.5, 36 * PX - 10 * PX), R(90))
    cu = bpy.data.curves.new("SA label " + key, "FONT")
    cu.body = {"B1": "B1 Pearl plate / R1", "B2": "B2 Hard-light shell / R2", "B3": "B3 Night guard / R3"}[key]
    cu.size = 0.6
    t = link(bpy.data.objects.new("SA label " + key, cu)); t.location = (ox - 1.5, y - 2.4, 0.02)
    m = bpy.data.materials.new("SA label"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.8, 0.9, 1, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2
    t.data.materials.append(m)

bpy.ops.mesh.primitive_plane_add(size=120, location=(20, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "SA floor"
gm = bpy.data.materials.new("SA floor"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.26, 0.2, 1)
g.data.materials.append(gm)

world = bpy.data.worlds.get("SA world") or bpy.data.worlds.new("SA world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.18, 0.24, 0.36, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("SA sun", bpy.data.lights.new("SA sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(45), R(-15), R(-30))
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


cams = {k: cam("Cam " + k, (ox + 5.5, -11.5, 3.0), (ox + 5.2, 0, 1.4), 35) for k, ox in ROWS.items()}
cams["squads"] = cam("Cam squads", (20, -42, 12), (20, 0, 1), 30)
cams["backs"] = cam("Cam backs", (5.5, 11.5, 3.0), (5.2, 0, 1.4), 35)
scene.camera = cams["squads"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c; scene.frame_set(10)
        scene.render.filepath = os.path.join(rdir, f"201_armour_{key}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["squads"]
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
