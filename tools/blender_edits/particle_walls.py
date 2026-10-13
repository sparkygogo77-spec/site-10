"""New particle wall designs (J, 2026-10-13: "I want a new particle wall design(s)"). Five 4 x 3 block walls in
rage_battery_c.blend, row at y = -20, cameras "Cam walls". Each is a different way of building a wall from particles,
all in the corps' green shades, never more than 99% opaque:

  W1 curtain   : pixels pour down the wall like a waterfall of light and are reborn at the top
  W2 lattice   : pixels lock into a block grid on the face, flicker, drop out and lock back in
  W3 swarm     : a thick cloud of pixels swirling round inside the wall's volume, held by an invisible box
  W4 rising    : embers of light rising from the ground line, fading as they reach the top edge
  W5 shards    : bigger flat shards tumbling slowly in place, catching the light, a dark shell behind

Run headless: S=<scratch> bpython tools/blender_edits/particle_walls.py (opens and re-saves the outputs blend)."""
import math, os
import bpy, bmesh
from mathutils import Vector

S = os.environ["S"]
SRC = os.environ.get("SRC_BLEND", "/mnt/user-data/outputs/rage_battery_c.blend")
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene; col = sc.collection
R = math.radians
SHADES = [(0.0, 0.08, 0.03), (0.01, 0.3, 0.1), (0.05, 0.6, 0.2), (0.4, 1.0, 0.5)]
for o in [o for o in bpy.data.objects if o.name.startswith(("Wall option", "Wall pixel", "Wall label", "Cam walls"))]:
    bpy.data.objects.remove(o)


def mat_pixel(name, glow=2.2, amin=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()
    oi = N.new("ShaderNodeObjectInfo")
    rp = N.new("ShaderNodeValToRGB"); els = rp.color_ramp.elements
    els[0].color = SHADES[0] + (1,); els[1].color = SHADES[-1] + (1,)
    for i, c in enumerate(SHADES[1:-1]):
        e = els.new((i + 1) / 3); e.color = c + (1,)
    L.new(oi.outputs["Random"], rp.inputs["Fac"])
    bs = N.new("ShaderNodeBsdfPrincipled")
    L.new(rp.outputs["Color"], bs.inputs["Base Color"]); L.new(rp.outputs["Color"], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = glow; bs.inputs["Roughness"].default_value = 0.2
    al = N.new("ShaderNodeMapRange"); al.inputs["To Min"].default_value = amin; al.inputs["To Max"].default_value = 0.99
    L.new(oi.outputs["Random"], al.inputs["Value"]); L.new(al.outputs["Result"], bs.inputs["Alpha"])
    out = N.new("ShaderNodeOutputMaterial"); L.new(bs.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def pixel(name, size, flat=False):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=size)
    if flat:
        for v in bm.verts:
            v.co.y *= 0.15
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = (0, 0, -70)
    me.materials.append(mat_pixel(name, 3.0 if flat else 2.2))
    return o


def plane(name, at, w=4.0, h=3.0, depth=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if depth:
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= w; v.co.y *= depth; v.co.z = (v.co.z + 0.5) * h
    else:
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        for v in bm.verts:
            x, y = v.co.x, v.co.y
            v.co.x, v.co.y, v.co.z = x * w, 0.0, (y + 0.5) * h
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = at
    return o


def system(o, name, inst, count, life, start=-120, normal=0.0, rnd=0.0, grav=0.0, damp=0.0, brown=0.0,
           size=1.0, srand=0.5, emit="FACE", phys="NEWTON", rot=True):
    mod = o.modifiers.new(name, "PARTICLE_SYSTEM")
    ps = mod.particle_system.settings
    ps.count = count; ps.frame_start = start; ps.frame_end = 288; ps.lifetime = life; ps.lifetime_random = 0.4
    ps.emit_from = emit; ps.normal_factor = normal; ps.factor_random = rnd
    ps.physics_type = phys
    ps.effector_weights.gravity = grav; ps.damping = damp; ps.brownian_factor = brown
    ps.render_type = "OBJECT"; ps.instance_object = inst
    ps.particle_size = size; ps.size_random = srand
    ps.use_rotations = rot; ps.rotation_factor_random = 1.0 if rot else 0.0
    return ps


def shell(o, alpha=0.25, rgb=(0.1, 1, 0.3)):
    m = bpy.data.materials.new(o.name + " shell"); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = rgb + (1,); em.inputs["Strength"].default_value = 1.0
    tr = N.new("ShaderNodeBsdfTransparent")
    f = N.new("ShaderNodeMath"); f.operation = "MULTIPLY"; f.inputs[1].default_value = alpha; L.new(lw.outputs["Facing"], f.inputs[0])
    mx = N.new("ShaderNodeMixShader"); L.new(f.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    out = N.new("ShaderNodeOutputMaterial"); L.new(mx.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    o.data.materials.clear(); o.data.materials.append(m)


def label(text, at):
    cu = bpy.data.curves.new(text, "FONT"); cu.body = text; cu.size = 0.24; cu.align_x = "CENTER"
    lo = bpy.data.objects.new("Wall label " + text[:2], cu); lo.location = at; lo.rotation_euler = (R(90), 0, 0)
    m = bpy.data.materials.new("lab " + text[:2]); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF"); p.inputs["Emission Color"].default_value = (0.8, 1, 0.85, 1); p.inputs["Emission Strength"].default_value = 2
    cu.materials.append(m); col.objects.link(lo)


Y = -20.0
px = pixel("Wall pixel", 0.07)
px_big = pixel("Wall pixel big", 0.11)
shard = pixel("Wall pixel shard", 0.22, flat=True)
xs = [40.0 + i * 5.0 for i in range(5)]

# W1 curtain: emit from a thin strip along the top edge, fall down the face, die at the bottom
top = plane("Wall option W1 top", Vector((xs[0], Y, 2.95)), 4.0, 0.05)
system(top, "curtain", px, 3200, 80, grav=1.0, damp=0.05, rnd=0.005)
back = plane("Wall option W1", Vector((xs[0], Y, 0)), 4.0, 3.0); shell(back, 0.3)
label("W1  curtain  -  pixels pouring down", Vector((xs[0], Y - 0.6, 3.5)))

# W2 lattice: pixels born on the face at a grid of points, sitting still, short lives so they flicker in and out
grid = plane("Wall option W2", Vector((xs[1], Y, 0)), 4.0, 3.0)
bpy.context.view_layer.objects.active = grid
me = grid.data
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=23, use_grid_fill=True); bm.to_mesh(me); bm.free()
ps = system(grid, "lattice", px_big, 4000, 18, emit="VERT", phys="NO", rot=False, srand=0.3)
shell(grid, 0.3)
label("W2  lattice  -  pixels lock into a grid, flicker", Vector((xs[1], Y - 0.6, 3.5)))

# W3 swarm: volume emitter, brownian motion with heavy damping, so they swirl but stay inside
box = plane("Wall option W3", Vector((xs[2], Y, 0)), 4.0, 3.0, depth=0.5)
system(box, "swarm", px, 4500, 40, emit="VOLUME", brown=0.25, damp=1.0)
shell(box, 0.2)
box.modifiers["swarm"].particle_system.settings.distribution = "RAND"
label("W3  swarm  -  a cloud swirling inside", Vector((xs[2], Y - 0.6, 3.5)))

# W4 rising: emit along the ground line, rise slowly
base = plane("Wall option W4 base", Vector((xs[3], Y, 0.02)), 4.0, 0.05)
system(base, "rising", px, 2200, 100, grav=-0.6, brown=0.03, damp=0.45)
back4 = plane("Wall option W4", Vector((xs[3], Y, 0)), 4.0, 3.0); shell(back4, 0.25)
label("W4  rising  -  embers of light rising", Vector((xs[3], Y - 0.6, 3.5)))

# W5 shards: big flat shards on the face, tumbling slowly in place, over a darker shell
sh = plane("Wall option W5", Vector((xs[4], Y, 0)), 4.0, 3.0)
ps5 = system(sh, "shards", shard, 900, 300, start=-300, brown=0.0, damp=1.0)
ps5.angular_velocity_mode = "RAND"; ps5.angular_velocity_factor = 0.6
shell(sh, 0.45, (0.02, 0.35, 0.1))
label("W5  shards  -  tumbling shards on a dark shell", Vector((xs[4], Y - 0.6, 3.5)))

cd = bpy.data.cameras.new("Cam walls"); cd.lens = 24
cam = bpy.data.objects.new("Cam walls", cd); col.objects.link(cam)
cam.location = (50.0, Y - 13.5, 3.0); cam.rotation_euler = (Vector((50.0, Y, 1.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()
fo = bpy.data.objects.get("Battery floor")
if fo:
    fo.scale = (3.0, 3.0, 1.0); fo.location = (40, 18, fo.location.z)
bpy.ops.wm.save_as_mainfile(filepath="/mnt/user-data/outputs/rage_battery_c.blend", compress=True)
if os.environ.get("RENDER"):
    sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.render.resolution_x = 1200; sc.render.resolution_y = 420
    for f in range(1, 61):
        sc.frame_set(f)
    sc.camera = cam; sc.render.filepath = S + "/walls.png"; bpy.ops.render.render(write_still=True)
