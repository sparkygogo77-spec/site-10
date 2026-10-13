"""The Blue Lantern from J's sheet, modelled in Blender (run with Blender's Python module):
a chamfered stone block with a raised frame inset round every face, chamfer and corner (as the
sheet draws its panels), octagonal windows cut into the four sides with bevelled stone frames, the
emblem glowing behind the glass front and back, domed lenses with bronze ports on the sides, a
turned bronze cap with bolts and the crown, a stepped octagonal foot with corner feet and a chunky
bevelled stone handle. Renders the sheet's nine views and sets them beside the sheet.

    python tools/blender/blue_lantern.py <work dir with emblem.png, captop.png> <sheet.jpg> <out.png> [--blend out.blend]

Units are the mod's (1 = 1/16 block); Blender's Z is up and the lantern's front faces -Y.
"""
import math, os, sys
import bpy, bmesh
from mathutils import Vector, Matrix

WORK, SHEET, OUT = sys.argv[1:4]
BLEND = sys.argv[sys.argv.index("--blend") + 1] if "--blend" in sys.argv else None
FAST = "--fast" in sys.argv

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
C8 = math.cos(math.radians(22.5))

# ---- dimensions (measured from the sheet's front and side views) ------------------------------------
BX, BZ_HALF = 6.5, 6.6          # body half width/depth and half height
BY = 10.0                       # body centre height
CH = 2.5                        # chamfer cut
INSET = 0.38                    # frame width round each panel
B = 3.75                        # window octagon half size (flat to centre)
FRAME = 0.5                     # window frame width
TOP = BY + BZ_HALF


# ---- helpers ----------------------------------------------------------------------------------------
def link(obj):
    scene.collection.objects.link(obj)
    return obj


def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def smooth(obj, angle=35):
    for p in obj.data.polygons:
        p.use_smooth = True
    try:
        obj.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass


def bevel_mod(obj, width, segs=2, limit_angle=30):
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segs
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(limit_angle)
    m.harden_normals = True
    return m


def boolean(obj, cutter, op="DIFFERENCE"):
    m = obj.modifiers.new("bool", "BOOLEAN")
    m.operation = op
    m.object = cutter
    m.solver = "EXACT"
    cutter.hide_render = True
    cutter.hide_viewport = True
    return m


def apply_all(obj):
    bpy.context.view_layer.objects.active = obj
    for m in list(obj.modifiers):
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=m.name)


def prism(name, verts, radius, depth, loc, rot=(0, 0, 0), phase=0.0):
    """A closed prism (a cylinder with few sides) of ``verts`` sides, standing on Z, then turned."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius, radius2=radius, depth=depth,
                          matrix=Matrix.Rotation(math.radians(phase), 4, "Z"))
    o = mesh_obj(name, bm)
    o.location = loc
    o.rotation_euler = rot
    return o


def box(name, size, loc):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    o = mesh_obj(name, bm)
    o.location = loc
    return o


# ---- materials --------------------------------------------------------------------------------------
def nodes_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes, nt.links, nt.nodes["Principled BSDF"]


def stone_mat():
    m, nt, N, L, bsdf = nodes_mat("stone")
    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.35
    noise.inputs["Detail"].default_value = 10
    noise.inputs["Roughness"].default_value = 0.6
    L.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.05, 0.085, 0.15, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.13, 0.2, 0.31, 1)
    L.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    # worn, paler edges: pointiness picks out convex edges
    geo = N.new("ShaderNodeNewGeometry")
    wear = N.new("ShaderNodeValToRGB")
    wear.color_ramp.elements[0].position = 0.53
    wear.color_ramp.elements[1].position = 0.6
    L.new(geo.outputs["Pointiness"], wear.inputs["Fac"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[7].default_value = (0.36, 0.45, 0.58, 1)
    L.new(wear.outputs["Color"], mix.inputs["Factor"])
    L.new(ramp.outputs["Color"], mix.inputs[6])
    # dark grime in crevices
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.6
    grime = N.new("ShaderNodeMix")
    grime.data_type = "RGBA"
    grime.blend_type = "MULTIPLY"
    grime.inputs["Factor"].default_value = 0.7
    L.new(mix.outputs[2], grime.inputs[6])
    L.new(ao.outputs["AO"], grime.inputs[7])
    L.new(grime.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.82
    # pitted surface and chipped edges
    vor = N.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 2.2
    L.new(tc.outputs["Object"], vor.inputs["Vector"])
    fine = N.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 6
    fine.inputs["Detail"].default_value = 12
    L.new(tc.outputs["Object"], fine.inputs["Vector"])
    add = N.new("ShaderNodeMath")
    add.operation = "ADD"
    L.new(vor.outputs["Distance"], add.inputs[0])
    L.new(fine.outputs["Fac"], add.inputs[1])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.05
    L.new(add.outputs[0], bump.inputs["Height"])
    bev = N.new("ShaderNodeBevel")
    bev.inputs["Radius"].default_value = 0.06
    L.new(bev.outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def bronze_mat():
    m, nt, N, L, bsdf = nodes_mat("bronze")
    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.2
    noise.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.32, 0.17, 0.07, 1)
    ramp.color_ramp.elements[1].color = (0.62, 0.39, 0.19, 1)
    L.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.4
    mul = N.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 0.6
    L.new(ramp.outputs["Color"], mul.inputs[6])
    L.new(ao.outputs["AO"], mul.inputs[7])
    L.new(mul.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.38
    bev = N.new("ShaderNodeBevel")
    bev.inputs["Radius"].default_value = 0.05
    L.new(bev.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def emblem_mat():
    m, nt, N, L, bsdf = nodes_mat("emblem")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / (2 * B / C8), 1 / (2 * B / C8), 1)
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(WORK, "emblem.png"))
    img.extension = "EXTEND"
    L.new(mp.outputs["Vector"], img.inputs["Vector"])
    L.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(img.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Coat Weight"].default_value = 1.0
    return m


def lens_mat():
    m, nt, N, L, bsdf = nodes_mat("lens")
    tc = N.new("ShaderNodeTexCoord")
    grad = N.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / (B * 1.05),) * 3
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    L.new(mp.outputs["Vector"], grad.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.004, 0.03, 0.25, 1)
    ramp.color_ramp.elements[1].color = (0.75, 0.92, 1.0, 1)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].position = 0.85
    mid = ramp.color_ramp.elements.new(0.45)
    mid.color = (0.03, 0.25, 1.0, 1)
    L.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Coat Weight"].default_value = 1.0
    return m


def captop_mat():
    m, nt, N, L, bsdf = nodes_mat("captop")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 6.3, 1 / 6.3, 1)
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(WORK, "captop.png"))
    L.new(mp.outputs["Vector"], img.inputs["Vector"])
    L.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.4
    return m


STONE, BRONZE, EMBLEM, LENS, CAPTOP = stone_mat(), bronze_mat(), emblem_mat(), lens_mat(), captop_mat()


def set_mat(o, mat):
    o.data.materials.clear()
    o.data.materials.append(mat)


# ---- the body: chamfered block, every panel framed ---------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, vec=Vector((2 * BX, 2 * BX, 2 * BZ_HALF)), verts=bm.verts)
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=CH, segments=1, affect="EDGES", profile=0.5)
# a raised frame round every face, chamfer and corner: inset each panel and sink its middle
# a raised lip round every panel, then the panel sunk inside it, as the sheet draws them
panels = list(bm.faces)
bmesh.ops.inset_individual(bm, faces=panels, thickness=INSET * 0.55, depth=0.12)
bmesh.ops.inset_individual(bm, faces=panels, thickness=INSET * 0.45, depth=-0.32)
body = mesh_obj("body", bm)
body.location = (0, 0, BY)
set_mat(body, STONE)
# the sheet's body swells like a barrel: subdivide it flat, then cast it part way to a sphere
sub = body.modifiers.new("sub", "SUBSURF")
sub.subdivision_type = "SIMPLE"
sub.levels = sub.render_levels = 3
cast = body.modifiers.new("cast", "CAST")
cast.cast_type = "SPHERE"
cast.factor = 0.16
cast.use_z = True
apply_all(body)

bevel_mod(body, 0.1, 2, 35)
apply_all(body)
smooth(body, 35)

# window frames, glass and ports
sides = {"front": ((0, -1, 0), (math.radians(90), 0, 0)), "back": ((0, 1, 0), (math.radians(-90), 0, math.radians(180))),
         "left": ((1, 0, 0), (math.radians(90), 0, math.radians(90))), "right": ((-1, 0, 0), (math.radians(90), 0, math.radians(-90)))}
def surface(n):
    """Where the swollen body's surface actually is along direction n from its centre."""
    o = Vector((0, 0, BY)) + n * 30 - body.location
    hit, loc, nrm, idx = body.ray_cast(o, -n)
    return body.location + loc if hit else Vector((0, 0, BY)) + n * BX


for nm, (n, rot) in sides.items():
    n = Vector(n)
    face = surface(n) - n * 0.25
    # the frame: a thick octagonal ring standing proud, bevelled
    ring = prism(f"frame_{nm}", 8, (B + FRAME) / C8, 1.5, face, rot, 22.5)
    hole = prism(f"frame_hole_{nm}", 8, B / C8, 3.0, face, rot, 22.5)
    boolean(ring, hole)
    bevel_mod(ring, 0.14, 3, 30)
    apply_all(ring)
    smooth(ring, 35)
    set_mat(ring, STONE)
    glass_at = face + n * 0.4   # just proud of the swollen stone
    if nm in ("front", "back"):
        g = prism(f"glass_{nm}", 8, B / C8, 0.05, glass_at, rot, 22.5)
        set_mat(g, EMBLEM)
    else:
        bmg = bmesh.new()
        bmesh.ops.create_uvsphere(bmg, u_segments=8, v_segments=8, radius=B / C8,
                                  matrix=Matrix.Rotation(math.radians(22.5), 4, "Z"))
        bmesh.ops.delete(bmg, geom=[v for v in bmg.verts if v.co.z < -1e-4], context="VERTS")
        bmesh.ops.scale(bmg, vec=Vector((1, 1, 0.42)), verts=bmg.verts)
        g = mesh_obj(f"lens_{nm}", bmg)
        g.location = glass_at
        g.rotation_euler = rot
        smooth(g, 80)
        set_mat(g, LENS)
        # the bronze port at the lens's crown: a thick ring with a dark hollow
        port = prism(f"port_{nm}", 32, 1.55, 0.9, glass_at + n * (B / C8 * 0.42 + 0.05), rot)
        hole = prism(f"port_hole_{nm}", 32, 0.95, 3.0, glass_at + n * (B / C8 * 0.42 + 0.3), rot)
        boolean(port, hole)
        bevel_mod(port, 0.14, 3, 30)
        apply_all(port)
        smooth(port, 40)
        set_mat(port, BRONZE)
        dark = prism(f"port_dark_{nm}", 32, 0.97, 0.05, glass_at + n * (B / C8 * 0.42 - 0.2), rot)
        dm = bpy.data.materials.new("hollow")
        dm.diffuse_color = (0.01, 0.01, 0.01, 1)
        set_mat(dark, dm)

# ---- the cap: a wide low bronze collar, a ring above it, the crowned top; bolts round both ---------------
def cyl(name, r, h, z, segs=64, mat=BRONZE, bev=0.12):
    o = prism(name, segs, r, h, (0, 0, z + h / 2))
    bevel_mod(o, bev, 3, 30)
    apply_all(o)
    smooth(o, 40)
    set_mat(o, mat)
    return o


cyl("cap_collar", 4.5, 0.95, TOP - 0.2)
cyl("cap_ring", 3.85, 0.95, TOP + 0.75)
top = cyl("cap_top", 3.15, 0.45, TOP + 1.7, mat=BRONZE, bev=0.1)
disc = prism("cap_disc", 64, 3.0, 0.04, (0, 0, TOP + 2.17))
set_mat(disc, CAPTOP)


def bolt(name, pos, nrm, r):
    bmb = bmesh.new()
    bmesh.ops.create_uvsphere(bmb, u_segments=12, v_segments=8, radius=r)
    o = mesh_obj(name, bmb)
    o.location = pos
    o.scale = (1, 1, 1)
    smooth(o, 90)
    set_mat(o, BRONZE)


for i in range(16):
    th = 2 * math.pi * (i + 0.5) / 16
    bolt(f"bolt_{i}", (4.5 * math.sin(th), -4.5 * math.cos(th), TOP + 0.28), None, 0.2)
for i in range(20):
    th = 2 * math.pi * i / 20
    bolt(f"bolt_hi_{i}", (3.85 * math.sin(th), -3.85 * math.cos(th), TOP + 1.22), None, 0.15)

# ---- the foot: stepped octagons, corner feet --------------------------------------------------------
for nm, r, z0, z1 in (("foot_slab", 4.6, 0.0, 1.3), ("foot_step", 3.95, 1.3, 2.6), ("foot_neck", 3.3, 2.6, BY - BZ_HALF + 0.3)):
    o = prism(nm, 8, r / C8, z1 - z0, (0, 0, (z0 + z1) / 2), (0, 0, 0), 22.5)
    bevel_mod(o, 0.12, 2, 30)
    apply_all(o)
    smooth(o, 35)
    set_mat(o, STONE)
for i in range(4):
    th = math.radians(45 + 90 * i)
    o = box(f"foot_corner_{i}", (1.8, 1.8, 1.7), (4.45 * math.sin(th), -4.45 * math.cos(th), 0.85))
    o.rotation_euler = (0, 0, th)
    bevel_mod(o, 0.15, 3, 30)
    apply_all(o)
    smooth(o, 35)
    set_mat(o, STONE)

# ---- the handle: a squared stone loop with stepped corners ------------------------------------------
HT = 1.24
parts = [((HT, HT, 4.3), (4.0, 0, TOP + 3.9)), ((HT, HT, 4.3), (-4.0, 0, TOP + 3.9)),
         ((HT, HT, HT), (3.15, 0, TOP + 6.4)), ((HT, HT, HT), (-3.15, 0, TOP + 6.4)),
         ((5.8, HT, HT), (0, 0, TOP + 7.45))]
for i, (sz, loc) in enumerate(parts):
    o = box(f"handle_{i}", sz, loc)
    bevel_mod(o, 0.2, 3, 30)
    apply_all(o)
    smooth(o, 35)
    set_mat(o, STONE)

# ---- studio like the sheet: grey backdrop, soft key from upper front left -----------------------------
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.43, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45


def area(name, loc, power, size):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.size = size
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    d = Vector((0, 0, 11)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


area("key", (-28, -40, 40), 14000, 30)
area("fill", (35, -25, 12), 3500, 30)
area("rim", (10, 40, 30), 6000, 25)

scene.render.engine = "CYCLES"
scene.cycles.samples = 16 if FAST else 48
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
SIZE = 360
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.render.film_transparent = False

cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = 27
cam = link(bpy.data.objects.new("cam", cam_d))
scene.camera = cam

VIEWS = [("FRONT", 0, 6), ("BACK", 180, 6), ("TOP", 0, 89.5), ("LEFT", 90, 6), ("RIGHT", -90, 6),
         ("BOTTOM", 0, -89.5), ("FRONT LEFT", 40, 14), ("FRONT RIGHT", -40, 14), ("BACK RIGHT", -140, 14)]
target = Vector((0, 0, 11.3))
tiles = []
for label, yaw, pitch in VIEWS:
    y, p = math.radians(yaw), math.radians(pitch)
    # yaw 0 looks at the front (-Y); positive yaw swings round to the lantern's left (+X... seen as LEFT)
    d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = target + d * 80
    up = Vector((0, 0, 1)) if abs(pitch) < 80 else Vector((0, 1, 0))
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler() if abs(pitch) < 80 else \
        ((-d).to_track_quat("-Z", "Y")).to_euler()
    path = os.path.join(WORK, f"view_{label.replace(' ', '_')}.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    tiles.append((label, path))

if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)

from PIL import Image, ImageDraw
grid = Image.new("RGB", (SIZE * 3, SIZE * 3))
for i, (label, path) in enumerate(tiles):
    im = Image.open(path).convert("RGB")
    ImageDraw.Draw(im).text((8, 6), label, fill=(0, 0, 0))
    grid.paste(im, ((i % 3) * SIZE, (i // 3) * SIZE))
sheet = Image.open(SHEET).convert("RGB")
sheet = sheet.resize((int(sheet.width * SIZE * 3 / sheet.height), SIZE * 3))
both = Image.new("RGB", (sheet.width + grid.width, SIZE * 3))
both.paste(sheet, (0, 0))
both.paste(grid, (sheet.width, 0))
both.save(OUT)
print("wrote", OUT)
