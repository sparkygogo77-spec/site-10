# Pass 593: the skin workshop - every current construct texture, barrier surface, particle wall, ring and lantern look in
# one Blender file, a shelf per group (Chat C, 2026-10-14; built here because J asked in this chat).
# J: "were going to make a skin workshop of all of our current textures and necessary skin textures and construct /
# particle skin renders". Picks: one Blender file with a shelf per group; green picks, barrier surfaces T1-T9 + particle
# walls W1-W5, ring and lantern looks; each texture shown on the A1 Plates suit, as a block wall, as a dome/shield and
# as particles.
# Shelves (left to right along x):
#   GREEN  : W1 neon, W1 emerald, H1 neon, H2 neon, HW emerald, BR1 emerald/jade/lime/neon, BRD neon, X1 emerald,
#            X3 emerald, X5 emerald, X5 neon, X3D1 emerald, R2 K1 dark jade (the default construct look).
#   BARRIER: T1, T2, T3, T5, T6, T7, T9 (the barrier surfaces in the jar; T4 and T8 were never kept).
#   WALLS  : particle walls W1 curtain, W2 lattice, W3 swarm, W4 rising, W5 shards (pass 700, unchanged).
#   RINGS  : ring models A, B, B1-B4, C, L1-L3 and the square emblem ring (shown 4x size).
#   LANTERNS: Dark Lantern L1 and L2, Dark Lantern 5 L1/L2 (pixel builds), Blue Lantern.
# Each texture stand: the A1 Plates suit (J's pick), a 3x2 block wall (outer shell only), a dome/shield of radius 1.5,
# and a particle construct (pixels living on a sphere's surface over a faint shell). Every texture plays as its game
# strip does (frames x frametime, interpolated); everything forms feet first (frames 1-34), then holds.
# Cameras: "Cam shelf <group>", per texture "Cam <code>" (the whole stand), "Cam <code> suit", "Cam <code> wall",
# "Cam <code> dome", "Cam <code> particles"; "Cam walls", "Cam rings", "Cam lanterns", "Cam workshop".
# Builds LanternLive\constructs\skin_workshop.blend (textures packed).
import math, os
import bpy
import numpy as np
from mathutils import Matrix, Vector


# --------------------------------------------------------------- the particle walls (pass 700 code, unchanged, run first:
# it starts from an empty file); its objects are moved onto the WALLS shelf below.
_PW = '# Pass 700: particle walls W1-W5 as their own file (Chat E, 2026-10-14). The five walls from\n# tools/blender_edits/particle_walls.py were built into rage_battery_c.blend on 2026-10-13 but that copy never reached\n# LanternLive, so J has not seen them. Same five designs, unchanged, in a small standalone scene on a dark floor:\n#   W1 curtain : pixels pour down the wall like a waterfall of light and are reborn at the top\n#   W2 lattice : pixels lock into a block grid on the face, flicker, drop out and lock back in\n#   W3 swarm   : a thick cloud of pixels swirling inside the wall\'s volume\n#   W4 rising  : embers rising from the ground line, fading at the top edge\n#   W5 shards  : bigger flat shards tumbling slowly in place over a dark shell\n# All in the corps greens, never more than 99% opaque. Cameras "Cam W1".."Cam W5" (each wall head-on, a little from\n# the right) and "Cam wall all" (all five). Builds LanternLive\\particle_walls.blend.\n\nimport bmesh\nfrom mathutils import Vector\nOUT = os.path.join(FOLDER, "kl_assets", "_ws_particle_walls.blend")\nbpy.ops.wm.read_factory_settings(use_empty=True)\nsc = bpy.context.scene; sc.name = "Particle Walls"; col = sc.collection\nsc.frame_start, sc.frame_end = 1, 200\nsc.render.fps = 20\nR = math.radians\nw = bpy.data.worlds.new("PW world"); sc.world = w; w.use_nodes = True\nw.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.015, 1)\nfl = bpy.data.meshes.new("PW floor"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=40); bm.to_mesh(fl); bm.free()\nflo = bpy.data.objects.new("PW floor", fl); col.objects.link(flo); flo.location = (50, -20, 0)\nfm = bpy.data.materials.new("PW floor"); fm.use_nodes = True\nfm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.035, 0.04, 1)\nfm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6; fl.materials.append(fm)\nsun = bpy.data.objects.new("PW sun", bpy.data.lights.new("PW sun", "SUN")); col.objects.link(sun)\nsun.data.energy = 0.6; sun.rotation_euler = (R(55), 0, R(-30))\nSHADES = [(0.0, 0.08, 0.03), (0.01, 0.3, 0.1), (0.05, 0.6, 0.2), (0.4, 1.0, 0.5)]\n\n\ndef mat_pixel(name, glow=2.2, amin=0.5):\n    m = bpy.data.materials.new(name); m.use_nodes = True\n    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()\n    oi = N.new("ShaderNodeObjectInfo")\n    rp = N.new("ShaderNodeValToRGB"); els = rp.color_ramp.elements\n    els[0].color = SHADES[0] + (1,); els[1].color = SHADES[-1] + (1,)\n    for i, c in enumerate(SHADES[1:-1]):\n        e = els.new((i + 1) / 3); e.color = c + (1,)\n    L.new(oi.outputs["Random"], rp.inputs["Fac"])\n    bs = N.new("ShaderNodeBsdfPrincipled")\n    L.new(rp.outputs["Color"], bs.inputs["Base Color"]); L.new(rp.outputs["Color"], bs.inputs["Emission Color"])\n    bs.inputs["Emission Strength"].default_value = glow; bs.inputs["Roughness"].default_value = 0.2\n    al = N.new("ShaderNodeMapRange"); al.inputs["To Min"].default_value = amin; al.inputs["To Max"].default_value = 0.99\n    L.new(oi.outputs["Random"], al.inputs["Value"]); L.new(al.outputs["Result"], bs.inputs["Alpha"])\n    out = N.new("ShaderNodeOutputMaterial"); L.new(bs.outputs[0], out.inputs[0])\n    try:\n        m.surface_render_method = "BLENDED"\n    except Exception:\n        pass\n    return m\n\n\ndef pixel(name, size, flat=False):\n    me = bpy.data.meshes.new(name)\n    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=size)\n    if flat:\n        for v in bm.verts:\n            v.co.y *= 0.15\n    bm.to_mesh(me); bm.free()\n    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = (0, 0, -70)\n    me.materials.append(mat_pixel(name, 3.0 if flat else 2.2))\n    return o\n\n\ndef plane(name, at, w=4.0, h=3.0, depth=None):\n    me = bpy.data.meshes.new(name)\n    bm = bmesh.new()\n    if depth:\n        bmesh.ops.create_cube(bm, size=1.0)\n        for v in bm.verts:\n            v.co.x *= w; v.co.y *= depth; v.co.z = (v.co.z + 0.5) * h\n    else:\n        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)\n        for v in bm.verts:\n            x, y = v.co.x, v.co.y\n            v.co.x, v.co.y, v.co.z = x * w, 0.0, (y + 0.5) * h\n    bm.to_mesh(me); bm.free()\n    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = at\n    return o\n\n\ndef system(o, name, inst, count, life, start=-120, normal=0.0, rnd=0.0, grav=0.0, damp=0.0, brown=0.0,\n           size=1.0, srand=0.5, emit="FACE", phys="NEWTON", rot=True):\n    mod = o.modifiers.new(name, "PARTICLE_SYSTEM")\n    ps = mod.particle_system.settings\n    ps.count = count; ps.frame_start = start; ps.frame_end = 288; ps.lifetime = life; ps.lifetime_random = 0.4\n    ps.emit_from = emit; ps.normal_factor = normal; ps.factor_random = rnd\n    ps.physics_type = phys\n    ps.effector_weights.gravity = grav; ps.damping = damp; ps.brownian_factor = brown\n    ps.render_type = "OBJECT"; ps.instance_object = inst\n    ps.particle_size = size; ps.size_random = srand\n    ps.use_rotations = rot; ps.rotation_factor_random = 1.0 if rot else 0.0\n    return ps\n\n\ndef shell(o, alpha=0.25, rgb=(0.1, 1, 0.3)):\n    m = bpy.data.materials.new(o.name + " shell"); m.use_nodes = True\n    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()\n    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35\n    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = rgb + (1,); em.inputs["Strength"].default_value = 1.0\n    tr = N.new("ShaderNodeBsdfTransparent")\n    f = N.new("ShaderNodeMath"); f.operation = "MULTIPLY"; f.inputs[1].default_value = alpha; L.new(lw.outputs["Facing"], f.inputs[0])\n    mx = N.new("ShaderNodeMixShader"); L.new(f.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])\n    out = N.new("ShaderNodeOutputMaterial"); L.new(mx.outputs[0], out.inputs[0])\n    try:\n        m.surface_render_method = "BLENDED"\n    except Exception:\n        pass\n    o.data.materials.clear(); o.data.materials.append(m)\n\n\ndef label(text, at):\n    cu = bpy.data.curves.new(text, "FONT"); cu.body = text; cu.size = 0.24; cu.align_x = "CENTER"\n    lo = bpy.data.objects.new("Wall label " + text[:2], cu); lo.location = at; lo.rotation_euler = (R(90), 0, 0)\n    m = bpy.data.materials.new("lab " + text[:2]); m.use_nodes = True\n    p = m.node_tree.nodes.get("Principled BSDF"); p.inputs["Emission Color"].default_value = (0.8, 1, 0.85, 1); p.inputs["Emission Strength"].default_value = 2\n    cu.materials.append(m); col.objects.link(lo)\n\n\nY = -20.0\npx = pixel("Wall pixel", 0.07)\npx_big = pixel("Wall pixel big", 0.11)\nshard = pixel("Wall pixel shard", 0.22, flat=True)\nxs = [40.0 + i * 5.0 for i in range(5)]\n\n# W1 curtain: emit from a thin strip along the top edge, fall down the face, die at the bottom\ntop = plane("Wall option W1 top", Vector((xs[0], Y, 2.95)), 4.0, 0.05)\nsystem(top, "curtain", px, 3200, 80, grav=1.0, damp=0.05, rnd=0.005)\nback = plane("Wall option W1", Vector((xs[0], Y, 0)), 4.0, 3.0); shell(back, 0.3)\nlabel("W1  curtain  -  pixels pouring down", Vector((xs[0], Y - 0.6, 3.5)))\n\n# W2 lattice: pixels born on the face at a grid of points, sitting still, short lives so they flicker in and out\ngrid = plane("Wall option W2", Vector((xs[1], Y, 0)), 4.0, 3.0)\nbpy.context.view_layer.objects.active = grid\nme = grid.data\nbm = bmesh.new(); bm.from_mesh(me); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=23, use_grid_fill=True); bm.to_mesh(me); bm.free()\nps = system(grid, "lattice", px_big, 4000, 18, emit="VERT", phys="NO", rot=False, srand=0.3)\nshell(grid, 0.3)\nlabel("W2  lattice  -  pixels lock into a grid, flicker", Vector((xs[1], Y - 0.6, 3.5)))\n\n# W3 swarm: volume emitter, brownian motion with heavy damping, so they swirl but stay inside\nbox = plane("Wall option W3", Vector((xs[2], Y, 0)), 4.0, 3.0, depth=0.5)\nsystem(box, "swarm", px, 4500, 40, emit="VOLUME", brown=0.25, damp=1.0)\nshell(box, 0.2)\nbox.modifiers["swarm"].particle_system.settings.distribution = "RAND"\nlabel("W3  swarm  -  a cloud swirling inside", Vector((xs[2], Y - 0.6, 3.5)))\n\n# W4 rising: emit along the ground line, rise slowly\nbase = plane("Wall option W4 base", Vector((xs[3], Y, 0.02)), 4.0, 0.05)\nsystem(base, "rising", px, 2200, 100, grav=-0.6, brown=0.03, damp=0.45)\nback4 = plane("Wall option W4", Vector((xs[3], Y, 0)), 4.0, 3.0); shell(back4, 0.25)\nlabel("W4  rising  -  embers of light rising", Vector((xs[3], Y - 0.6, 3.5)))\n\n# W5 shards: big flat shards on the face, tumbling slowly in place, over a darker shell\nsh = plane("Wall option W5", Vector((xs[4], Y, 0)), 4.0, 3.0)\nps5 = system(sh, "shards", shard, 900, 300, start=-300, brown=0.0, damp=1.0)\nps5.angular_velocity_mode = "RAND"; ps5.angular_velocity_factor = 0.6\nshell(sh, 0.45, (0.02, 0.35, 0.1))\nlabel("W5  shards  -  tumbling shards on a dark shell", Vector((xs[4], Y - 0.6, 3.5)))\n\ncd = bpy.data.cameras.new("Cam wall all"); cd.lens = 24\ncam = bpy.data.objects.new("Cam wall all", cd); col.objects.link(cam)\ncam.location = (50.0, Y - 13.5, 3.0); cam.rotation_euler = (Vector((50.0, Y, 1.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()\nfor i, x in enumerate(xs):\n    cd = bpy.data.cameras.new("Cam wall W%d" % (i + 1)); cd.lens = 32\n    c = bpy.data.objects.new("Cam wall W%d" % (i + 1), cd); col.objects.link(c)\n    c.location = (x + 1.6, Y - 7.0, 2.0)\n    c.rotation_euler = (Vector((x, Y, 1.5)) - c.location).to_track_quat("-Z", "Y").to_euler()\ntry:\n    tree = bpy.data.node_groups.new("PW Glow", "CompositorNodeTree")\n    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")\n    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")\n    gl = tree.nodes.new("CompositorNodeGlare")\n    if "Type" in gl.inputs:\n        gl.inputs["Type"].default_value = "Bloom"\n    for nm, val in (("Size", 0.6), ("Strength", 0.5), ("Threshold", 1.0)):\n        if nm in gl.inputs:\n            gl.inputs[nm].default_value = val\n    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])\n    sc.compositing_node_group = tree\nexcept Exception as e:\n    print("no glow:", e)\nsc.view_settings.view_transform = "Standard"\nsc.render.resolution_x, sc.render.resolution_y = 1600, 900\nsc.camera = bpy.data.objects["Cam wall W1"]; sc.frame_current = 60\nbpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)\nprint("saved", OUT)\n'
os.makedirs(os.path.join(FOLDER, "kl_assets"), exist_ok=True)
exec(compile("import math, os\n" + _PW, "700_particle_walls", "exec"), {"bpy": bpy, "np": np, "FOLDER": FOLDER, "__name__": "__ll__"})

R = math.radians
OUT = os.path.join(FOLDER, "constructs", "skin_workshop.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
TEXDIR = os.path.join(FOLDER, "suit_tex")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Skin Workshop")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Skin Workshop")
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


# ------------------------------------------------------------------ rig (Minecraft model space: px, y down, -z forward)
PIVOT = {"head": (0, 0, 0), "body": (0, 0, 0), "rarm": (-5, 2, 0), "larm": (5, 2, 0),
         "rleg": (-1.9, 12, 0), "lleg": (1.9, 12, 0), "rshin": (-1.9, 18, 0), "lshin": (1.9, 18, 0)}
BOX = {"head": ((-4, -8, -4), (4, 0, 4)), "body": ((-4, 0, -2), (4, 12, 2)), "rarm": ((-3, -2, -2), (1, 10, 2)),
       "larm": ((-1, -2, -2), (3, 10, 2)), "rleg": ((-2, 0, -2), (2, 6, 2)), "lleg": ((-2, 0, -2), (2, 6, 2)),
       "rshin": ((-2, 0, -2), (2, 6, 2)), "lshin": ((-2, 0, -2), (2, 6, 2))}
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")


def euler_of(Rm):
    """XYZ euler (x, y, z) of R = Rz @ Ry @ Rx, the inverse of rot()."""
    y = math.asin(max(-1.0, min(1.0, -Rm[2, 0])))
    return (math.atan2(Rm[2, 1], Rm[2, 2]), y, math.atan2(Rm[1, 0], Rm[0, 0]))
GROUND = 24.0
A = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # MC model axes -> Blender axes (x, z, -y)


def rot(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def corners(part, pivot, r):
    a, b = BOX[part]
    pts = np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])], float)
    return pts @ rot(*r).T + np.asarray(pivot, float)


def solve(p):
    """Pose (ring = right side) -> per part rotation and pivot. The body turns about the hips, the legs hang from the
    hips, grounded poses drop the hips until the lowest foot touches, `sink` lowers the torso into the legs."""
    rot_ = {"body": p.get("body", (0, 0, 0)), "head": p.get("head", (0, 0, 0))}
    for k, part, sgn in (("ring", "rarm", 1), ("free", "larm", -1), ("ringleg", "rleg", 1), ("freeleg", "lleg", -1)):
        x, y, z = p.get(k, (0, 0, 0))
        rot_[part] = (x, sgn * y, sgn * z)
    Rb = rot(*rot_["body"])
    sink = float(p.get("sink", 0.0))
    piv = {}

    def place(d):
        hip = np.array([0.0, 12.0 + d, -float(p.get("fwd", 0.0))])
        neck = hip + Rb @ np.array([0.0, -12.0, 0.0]) + np.array([0.0, sink, 0.0])
        piv["body"] = neck; piv["head"] = neck.copy()
        piv["rarm"] = neck + Rb @ np.array([-5.0, 2.0, 0.0]); piv["larm"] = neck + Rb @ np.array([5.0, 2.0, 0.0])
        piv["rleg"] = hip + Rb @ np.array([-1.9, 0.0, 0.0]) * np.array([1, 0, 1]) + np.array([0, 0, 0])
        piv["lleg"] = hip + Rb @ np.array([1.9, 0.0, 0.0]) * np.array([1, 0, 1])
        for leg, shin in (("rleg", "rshin"), ("lleg", "lshin")):
            piv[shin] = piv[leg] + rot(*rot_[leg]) @ np.array([0.0, 6.0, 0.0])

    for leg, shin, kk in (("rleg", "rshin", "ringknee"), ("lleg", "lshin", "freeknee")):
        k = float(p.get(kk, 0.0))
        rot_[shin] = euler_of(rot(*rot_[leg]) @ rot(k, 0, 0))
    place(0.0)
    d = 0.0
    if p.get("grounded", True):
        low = max(corners(k, piv[k], rot_[k])[:, 1].max() for k in ("rleg", "lleg", "rshin", "lshin"))
        d = GROUND - low
        place(d)
    return {k: (np.asarray(rot_[k], float), piv[k]) for k in PARTS}


def hand_point(sol, part="rarm"):
    r, pv = sol[part]
    return np.array([-1.0 if part == "rarm" else 1.0, 10.0, 0.0]) @ rot(*r).T + pv


def to_bl(v):
    v = np.asarray(v, float)
    return A @ np.array([v[0], v[1] - GROUND, v[2]]) / 16.0


def mat(name, rgb, emit=0.0, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


SKIN = mat("KL skin", (0.62, 0.42, 0.3)); SHIRT = mat("KL shirt", (0.04, 0.28, 0.12))
PANTS = mat("KL pants", (0.03, 0.05, 0.09)); HAIR = mat("KL hair", (0.08, 0.05, 0.03))
RINGM = mat("KL ring", (0.1, 1.0, 0.25), emit=3.0)
SHOES = mat("KL shoes", (0.12, 0.12, 0.13))
PART_MAT = {"head": SKIN, "body": SHIRT, "rarm": SHIRT, "larm": SHIRT, "rleg": PANTS, "lleg": PANTS,
            "rshin": PANTS, "lshin": PANTS}


def box_mesh(name, a, b, m):
    a = np.array(a, float); b = np.array(b, float)
    pts = [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    verts = [tuple(A @ p / 16.0) for p in pts]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.materials.append(m)
    return me


def make_player(tag):
    objs = {}
    for k in PARTS:
        a, b = BOX[k]
        o = link(bpy.data.objects.new(f"KL {tag} {k}", box_mesh(f"KL {tag} {k}", a, b, PART_MAT[k])))
        o.rotation_mode = "XYZ"
        objs[k] = o
    # details as children: hair cap, hands, ring
    for k, (a, b), m in (("head", ((-4.05, -8.05, -4.05), (4.05, -6.5, 4.05)), HAIR),
                         ("rarm", ((-3.02, 7, -2.02), (1.02, 10.02, 2.02)), SKIN),
                         ("larm", ((-1.02, 7, -2.02), (3.02, 10.02, 2.02)), SKIN),
                         ("rarm", ((-3.4, 6.2, -2.4), (1.4, 7.4, 2.4)), RINGM),
                         ("rshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES),
                         ("lshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES)):
        c = link(bpy.data.objects.new(f"KL {tag} {k} detail", box_mesh(f"KL {tag} {k} d", a, b, m)))
        c.parent = objs[k]
        if m is RINGM:
            objs["ring"] = c
    return objs


def set_pose(objs, sol, origin, frame, side=0.0):
    rs = np.array([[math.cos(side), -math.sin(side), 0], [math.sin(side), math.cos(side), 0], [0, 0, 1]])
    for k in PARTS:
        r, pv = sol[k]
        Rb = rs @ (A @ rot(*r) @ A.T)
        loc = rs @ to_bl(pv) + np.asarray(origin)
        o = objs[k]
        M = np.eye(4); M[:3, :3] = Rb; M[:3, 3] = loc
        from mathutils import Matrix, Vector
        o.matrix_world = Matrix(M.tolist())
        o.keyframe_insert("location", frame=frame); o.keyframe_insert("rotation_euler", frame=frame)


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c



LOOKS = [("W1", "w1_neon", "W1 neon")]
TILE = 32.0                 # model px per texture tile (2 blocks)
FORM_END, LOOP = 34, 400

# ------------------------------------------------------------------ the forming height, shared by every suit material
form = bpy.data.node_groups.new("Suit forming", "ShaderNodeTree")
form.interface.new_socket("Height", in_out="OUTPUT", socket_type="NodeSocketFloat")
fv = form.nodes.new("ShaderNodeValue"); fo = form.nodes.new("NodeGroupOutput")
form.links.new(fv.outputs[0], fo.inputs[0])
for f, h in ((1, -0.05), (FORM_END, 2.15), (LOOP - 10, 2.15), (LOOP - 9, -0.05)):
    fv.outputs[0].default_value = h
    fv.outputs[0].keyframe_insert("default_value", frame=f)


def suit_mat(name, image=None, rgb=(0.02, 0.12, 0.06), emit=0.0, alpha_tex=True, solid=False):
    """A suit surface that only exists below the forming height, with a bright band at the edge."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF"); out = N.get("Material Output")
    p.inputs["Roughness"].default_value = 0.35
    g = N.new("ShaderNodeGroup"); g.node_tree = form
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    below = N.new("ShaderNodeMath"); below.operation = "LESS_THAN"
    L.new(sep.outputs["Z"], below.inputs[0]); L.new(g.outputs[0], below.inputs[1])
    dz = N.new("ShaderNodeMath"); dz.operation = "SUBTRACT"; L.new(sep.outputs["Z"], dz.inputs[0]); L.new(g.outputs[0], dz.inputs[1])
    ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(dz.outputs[0], ab.inputs[0])
    band = N.new("ShaderNodeMapRange"); band.inputs["From Min"].default_value = 0.0; band.inputs["From Max"].default_value = 0.05
    band.inputs["To Min"].default_value = 1.0; band.inputs["To Max"].default_value = 0.0; L.new(ab.outputs[0], band.inputs["Value"])
    if image is not None:
        t = N.new("ShaderNodeTexImage"); t.image = image; t.interpolation = "Closest"
        uv = N.new("ShaderNodeUVMap"); uv.uv_map = "box"; L.new(uv.outputs["UV"], t.inputs["Vector"])
        L.new(t.outputs["Color"], p.inputs["Base Color"]); L.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emit
        a_src = t.outputs["Alpha"]
    else:
        p.inputs["Base Color"].default_value = (*rgb, 1)
        if emit:
            p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
        a_src = None
    am = N.new("ShaderNodeMath"); am.operation = "MULTIPLY"; L.new(below.outputs[0], am.inputs[0])
    if a_src is not None and alpha_tex:
        a2 = N.new("ShaderNodeMath"); a2.operation = "MAXIMUM"; a2.inputs[1].default_value = 0.0
        L.new(a_src, a2.inputs[0]); L.new(a2.outputs[0], am.inputs[1])
    else:
        am.inputs[1].default_value = 1.0
    # the forming edge: a bright mint band that runs up the body
    edge = N.new("ShaderNodeEmission"); edge.inputs["Color"].default_value = (0.5, 1.0, 0.65, 1)
    L.new(band.outputs["Result"], edge.inputs["Strength"])
    es = N.new("ShaderNodeMath"); es.operation = "MULTIPLY"; L.new(band.outputs["Result"], es.inputs[0]); es.inputs[1].default_value = 12.0
    L.new(es.outputs[0], edge.inputs["Strength"])
    add = N.new("ShaderNodeAddShader"); L.new(p.outputs[0], add.inputs[0]); L.new(edge.outputs[0], add.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    L.new(am.outputs[0], mix.inputs["Fac"]); L.new(tr.outputs[0], mix.inputs[1]); L.new(add.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED" if not solid else "DITHERED"
    except Exception:
        pass
    return m


def load_img(key):
    im = bpy.data.images.get("suit " + key)
    if im is None:
        im = bpy.data.images.load(os.path.join(TEXDIR, key + ".png")); im.name = "suit " + key
        try:
            im.pack()
        except Exception:
            pass
    return im


UNDER = suit_mat("Suit undersuit", None, (0.015, 0.07, 0.035), solid=True)
MASK = suit_mat("Suit mask band", None, (0.01, 0.012, 0.012), solid=True)
EYES = suit_mat("Suit eyes", None, (1.0, 1.0, 1.0), emit=4.0, solid=True)
EMBLEM = suit_mat("Suit emblem", None, (0.3, 1.0, 0.45), emit=8.0, solid=True)


def uv_box_mesh(name, a, b, m):
    """A box in model px with box-projected UVs (TILE px per texture tile), so the pattern keeps square pixels."""
    a = np.array(a, float); b = np.array(b, float)
    pts = [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    axes = [(1, 2), (1, 2), (0, 2), (0, 2), (0, 1), (0, 1)]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(A @ p / 16.0) for p in pts], [], faces); me.update()
    uvl = me.uv_layers.new(name="box")
    i = 0
    for fi, poly in enumerate(me.polygons):
        u, v = axes[fi]
        for li in poly.loop_indices:
            pv = pts[me.loops[li].vertex_index]
            uvl.data[li].uv = (pv[u] / TILE, -pv[v] / TILE)
    me.materials.append(m)
    return me


def child_box(parent, name, a, b, m, inflate=0.0):
    a = np.array(a, float) - inflate; b = np.array(b, float) + inflate
    o = link(bpy.data.objects.new(name, uv_box_mesh(name, a, b, m))); o.parent = parent
    return o


STANCE = dict(body=(0.0, 0, 0), head=(0.0, 0, 0), ring=(-0.08, 0, 0.12), free=(0.05, 0, -0.1),
              ringleg=(0.0, 0, 0.04), freeleg=(0.0, 0, -0.04))

# ------------------------------------------------------------------ one animated construct texture per suit (J: "only use
# one texture at once", "I also need it animated"). Each strip plays like the game: frame k of N, frametime ft ticks,
# interpolated into the next frame, looping.
def strip_mat(name, image, n, ft, emit, rnd=False, alpha_k=1.0):
    m = suit_mat(name, image, emit=emit)
    N, L = m.node_tree.nodes, m.node_tree.links
    t0 = next(nd for nd in N if nd.type == "TEX_IMAGE"); uvn = next(nd for nd in N if nd.type == "UVMAP")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uvn.outputs["UV"], sep.inputs[0])
    su, sv = sep.outputs[0], sep.outputs[1]
    if rnd:
        # particles: each instance shows its own patch of the texture (Object Info Random offsets the UV)
        oi = N.new("ShaderNodeObjectInfo")
        for i_, ax in enumerate((su, sv)):
            mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 37.0 + 11 * i_
            L.new(oi.outputs["Random"], mul.inputs[0])
            ad = N.new("ShaderNodeMath"); ad.operation = "ADD"; L.new(ax, ad.inputs[0]); L.new(mul.outputs[0], ad.inputs[1])
            if i_ == 0:
                su = ad.outputs[0]
            else:
                sv = ad.outputs[0]
    fu = N.new("ShaderNodeMath"); fu.operation = "FRACT"; L.new(su, fu.inputs[0])
    fv = N.new("ShaderNodeMath"); fv.operation = "FRACT"; L.new(sv, fv.inputs[0])
    tick = N.new("ShaderNodeValue"); fc = tick.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"; fc.driver.expression = f"frame/{ft}"
    fl = N.new("ShaderNodeMath"); fl.operation = "FLOOR"; L.new(tick.outputs[0], fl.inputs[0])
    wv = N.new("ShaderNodeMath"); wv.operation = "SUBTRACT"; L.new(tick.outputs[0], wv.inputs[0]); L.new(fl.outputs[0], wv.inputs[1])
    outs = []
    for step, tex in ((0, t0), (1, N.new("ShaderNodeTexImage"))):
        tex.image = image; tex.interpolation = "Closest"
        k = N.new("ShaderNodeMath"); k.operation = "ADD"; k.inputs[1].default_value = step; L.new(fl.outputs[0], k.inputs[0])
        km = N.new("ShaderNodeMath"); km.operation = "FLOORED_MODULO"; km.inputs[1].default_value = n; L.new(k.outputs[0], km.inputs[0])
        # strip frame k sits at v in [1-(k+1)/n, 1-k/n]: v' = (fract(v) + n - 1 - k) / n
        a = N.new("ShaderNodeMath"); a.operation = "SUBTRACT"; a.inputs[0].default_value = n - 1; L.new(km.outputs[0], a.inputs[1])
        b = N.new("ShaderNodeMath"); b.operation = "ADD"; L.new(fv.outputs[0], b.inputs[0]); L.new(a.outputs[0], b.inputs[1])
        c = N.new("ShaderNodeMath"); c.operation = "DIVIDE"; c.inputs[1].default_value = n; L.new(b.outputs[0], c.inputs[0])
        cmb = N.new("ShaderNodeCombineXYZ"); L.new(fu.outputs[0], cmb.inputs[0]); L.new(c.outputs[0], cmb.inputs[1])
        L.new(cmb.outputs[0], tex.inputs["Vector"])
        outs.append(tex)
    # crossfade colour and alpha between frame k and k+1 (the game's "interpolate": true)
    mc = N.new("ShaderNodeMix"); mc.data_type = "RGBA"; L.new(wv.outputs[0], mc.inputs["Factor"])
    L.new(outs[0].outputs["Color"], mc.inputs[6]); L.new(outs[1].outputs["Color"], mc.inputs[7])
    ma = N.new("ShaderNodeMix"); ma.data_type = "FLOAT"; L.new(wv.outputs[0], ma.inputs["Factor"])
    olds = [lk.to_socket for lk in L if lk.from_node == outs[0] and lk.from_socket.name == "Alpha"]
    for lk in [lk for lk in L if lk.from_node == outs[0] and lk.from_socket.name == "Alpha"]:
        L.remove(lk)
    L.new(outs[0].outputs["Alpha"], ma.inputs[2]); L.new(outs[1].outputs["Alpha"], ma.inputs[3])
    ak = N.new("ShaderNodeMath"); ak.operation = "MULTIPLY"; ak.inputs[1].default_value = alpha_k
    L.new(ma.outputs[0], ak.inputs[0])
    for to in olds:
        L.new(ak.outputs[0], to)
    p = N.get("Principled BSDF")
    L.new(mc.outputs[2], p.inputs["Base Color"]); L.new(mc.outputs[2], p.inputs["Emission Color"])
    return m


def load_strip(key):
    im = bpy.data.images.get("suit strip " + key)
    if im is None:
        im = bpy.data.images.load(os.path.join(TEXDIR, key + "_strip.png")); im.name = "suit strip " + key
        try:
            im.pack()
        except Exception:
            pass
    return im





# ------------------------------------------------------------------ the A1 Plates suit (J's pick, 590 V3 / 591 A1)
# J on 590: "the armored one here is great" (V3 Plates). KEEP word for word: V3's dark undersuit with raised plates on
# chest, shoulders, forearms, thighs and shins, the band mask with white eyes, the square emblem. "make another several
# designs of armor ... only use one texture at once ... bigger armor variants ... animated".
DESIGNS = [("A1", "Plates", "V3 as J picked it"),
           ("A2", "Heavy", "bigger: oversized pauldrons, thick breastplate, big gauntlets, knee guards, greaves"),
           ("A3", "Lamellar", "overlapping bands down the torso, arms and legs, dark gaps between"),
           ("A4", "Knight", "full cuirass, gorget collar, two-tier pauldrons, tassets over the thighs, long sabatons"),
           ("A5", "Titan", "biggest: towering pauldrons with fins, protruding breastplate, huge gauntlets and boots")]
LIMBS = ("rarm", "larm", "rleg", "lleg", "rshin", "lshin")


def face_marks(objs, tag, front=-2.75):
    for (a, b) in (((-1.5, 3.0), (1.5, 3.6)), ((-1.5, 6.4), (1.5, 7.0)), ((-1.5, 3.0), (-0.9, 7.0)), ((0.9, 3.0), (1.5, 7.0))):
        child_box(objs["body"], f"{tag} emblem", (a[0], a[1], front), (b[0], b[1], front + 0.2), EMBLEM)
    child_box(objs["head"], f"{tag} mask", (-4, -5.4, -4), (4, -3.0, 4), MASK, 0.08)
    child_box(objs["head"], f"{tag} eye r", (-3.0, -4.7, -4.2), (-1.0, -3.7, -4.12), EYES)
    child_box(objs["head"], f"{tag} eye l", (1.0, -4.7, -4.2), (3.0, -3.7, -4.12), EYES)


def arm_x(part):
    return (-3, 1) if part == "rarm" else (-1, 3)


def out_in(part, outer, inner=0.0):
    """Widen an arm box outward (away from the body) by `outer` and inward by `inner`."""
    x0, x1 = arm_x(part)
    return (x0 - outer, x1 + inner) if part == "rarm" else (x0 - inner, x1 + outer)


def detailed(objs, tag, T, Sm):
    """A plate with ridges on its top and bottom edges, a glowing seam across the middle and rivets on its front."""
    def make(part, nm, a, b, inf):
        a = np.array(a, float); b = np.array(b, float)
        child_box(objs[part], f"{tag} {nm}", a, b, T, inf)
        h = b[1] - a[1]
        if h >= 2.0:
            r = min(0.55, h * 0.16)
            child_box(objs[part], f"{tag} {nm} ridge t", (a[0], a[1], a[2]), (b[0], a[1] + r, b[2]), T, inf + 0.2)
            child_box(objs[part], f"{tag} {nm} ridge b", (a[0], b[1] - r, a[2]), (b[0], b[1], b[2]), T, inf + 0.2)
            ym = (a[1] + b[1]) / 2
            child_box(objs[part], f"{tag} {nm} seam", (a[0], ym - 0.14, a[2]), (b[0], ym + 0.14, b[2]), Sm, inf + 0.06)
        w = b[0] - a[0]
        if w >= 2.5 and h >= 2.5:
            for xx in (a[0] + 0.55, b[0] - 0.95):
                for yy in (a[1] + 0.75, b[1] - 1.15):
                    child_box(objs[part], f"{tag} {nm} rivet", (xx, yy, a[2] - inf - 0.32), (xx + 0.4, yy + 0.4, a[2] - inf),
                              Sm)
    return make


def extras(objs, tag, d, T, Sm, box):
    """Per-design intricate extras."""
    box("body", "collar", (-3.0, -1.0, -2.3), (3.0, 0.6, 2.3), 0.35)
    box("body", "belt", (-4, 10.7, -2), (4, 12, 2), 0.55)
    child_box(objs["body"], f"{tag} buckle", (-1.0, 10.6, -2.9), (1.0, 12.1, -2.5), Sm)
    for part in ("rarm", "larm"):
        x0, x1 = arm_x(part)
        child_box(objs[part], f"{tag} knuckles {part}", (x0 - 0.2, 8.8, -2.9), (x1 + 0.2, 9.8, -2.2), T, 0.2)
        if d in ("A2", "A4", "A5"):
            o0, o1 = out_in(part, 1.6 if d == "A5" else 1.2)
            child_box(objs[part], f"{tag} trim {part}", (o0, 1.4, -2.9), (o1, 2.0, 2.9), Sm, 0.3)
    if d in ("A1", "A3"):
        for part in ("rshin", "lshin"):
            child_box(objs[part], f"{tag} kneecap {part}", (-1.2, -0.8, -2.9), (1.2, 0.8, -2.0), T, 0.25)
    if d == "A5":
        child_box(objs["body"], f"{tag} chest ridge", (-0.5, -0.4, -4.4), (0.5, 7.0, -3.6), Sm, 0.2)


def dress(objs, tag, d, T, fine=False, Sm=None):
    for part in ("body",) + LIMBS:
        a, b = BOX[part]
        child_box(objs[part], f"{tag} under {part}", a, b, UNDER, 0.12)
    box = (detailed(objs, tag, T, Sm) if fine else
           (lambda part, nm, a, b, inf: child_box(objs[part], f"{tag} {nm}", a, b, T, inf)))
    front = -2.75
    if d == "A1":                                             # V3 Plates, unchanged
        P = 0.5
        box("body", "chest", (-3.5, 0.5, -2), (3.5, 6.5, 2), P)
        box("body", "abs", (-3.0, 7.2, -2), (3.0, 10.2, 2), P - 0.1)
        for part in ("rarm", "larm"):
            x0, x1 = arm_x(part)
            box(part, "cap " + part, (x0, -2, -2), (x1, 1.2, 2), P + 0.1)
            box(part, "fore " + part, (x0, 5.0, -2), (x1, 9.0, 2), P)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2, 0.6, -2), (2, 5.2, 2), P)
        for part in ("rshin", "lshin"):
            box(part, "shin " + part, (-2, 0.4, -2), (2, 4.8, 2), P)
    elif d == "A2":                                           # Heavy
        box("body", "breast", (-4, 0.0, -2.6), (4, 7.0, 2.4), 0.5)
        box("body", "abs", (-3.4, 7.4, -2.2), (3.4, 10.4, 2.2), 0.45)
        box("body", "belt", (-4, 10.6, -2), (4, 12, 2), 0.6)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 1.2)
            box(part, "pauldron " + part, (x0, -2.6, -2.8), (x1, 1.8, 2.8), 0.5)
            g0, g1 = out_in(part, 0.7, 0.4)
            box(part, "gauntlet " + part, (g0, 5.2, -2.6), (g1, 10.2, 2.6), 0.4)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2.3, 0.4, -2.3), (2.3, 5.0, 2.3), 0.45)
            box(part, "knee " + part, (-1.6, 4.6, -2.9), (1.6, 6.6, -1.2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "greave " + part, (-2.4, 0.6, -2.5), (2.4, 4.4, 2.4), 0.45)
            box(part, "boot " + part, (-2.5, 4.4, -3.2), (2.5, 6.0, 2.5), 0.4)
        front = -3.3
    elif d == "A3":                                           # Lamellar bands
        for i, y in enumerate((0.0, 2.3, 4.6, 6.9, 9.2)):
            box("body", f"band{i}", (-4, y, -2), (4, y + 2.0, 2), 0.45 + 0.05 * i)
        for part in ("rarm", "larm"):
            x0, x1 = arm_x(part)
            for i, y in enumerate((-2.0, 0.6, 3.2, 5.8)):
                box(part, f"band{i} {part}", (x0, y, -2), (x1, y + 2.2, 2), 0.5 - 0.04 * i)
        for part in ("rleg", "lleg", "rshin", "lshin"):
            for i, y in enumerate((0.2, 2.3, 4.4) if part.endswith("leg") else (0.2, 2.3)):
                box(part, f"band{i} {part}", (-2, y, -2), (2, y + 1.8, 2), 0.45)
            if part.endswith("shin"):
                box(part, "boot " + part, (-2, 4.3, -2.4), (2, 6, 2), 0.4)
        front = -2.75 - 0.4
    elif d == "A4":                                           # Knight
        box("body", "cuirass", (-4, 0.0, -2), (4, 10.6, 2), 0.6)
        box("body", "gorget", (-3.2, -0.9, -2.4), (3.2, 0.8, 2.4), 0.4)
        box("body", "fauld", (-4.2, 10.6, -2.2), (4.2, 12.0, 2.2), 0.5)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 1.0)
            box(part, "pauldron " + part, (x0, -2.5, -2.6), (x1, 0.8, 2.6), 0.5)
            x0, x1 = out_in(part, 0.6)
            box(part, "pauldron2 " + part, (x0, 0.8, -2.3), (x1, 2.6, 2.3), 0.45)
            box(part, "vambrace " + part, (*arm_x(part)[:1], 5.6, -2), (arm_x(part)[1], 9.4, 2), 0.5)
        for part in ("rleg", "lleg"):
            box(part, "tasset " + part, (-2.3, -0.2, -2.6), (2.3, 3.0, 2.2), 0.4)
            box(part, "cuisse " + part, (-2, 3.0, -2), (2, 5.8, 2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "poleyn " + part, (-1.5, -0.6, -2.8), (1.5, 1.2, -1.4), 0.4)
            box(part, "greave " + part, (-2, 1.2, -2), (2, 4.6, 2), 0.45)
            box(part, "sabaton " + part, (-2.1, 4.6, -3.6), (2.1, 6.0, 2.1), 0.4)
        front = -2.75 - 0.4
    elif d == "A5":                                           # Titan
        box("body", "breast", (-4.4, -0.4, -3.4), (4.4, 7.4, 2.6), 0.5)
        box("body", "spine", (-1.0, 0.0, 2.6), (1.0, 10.0, 3.6), 0.4)
        box("body", "abs", (-3.6, 7.6, -2.6), (3.6, 10.6, 2.4), 0.45)
        box("body", "belt", (-4.4, 10.6, -2.4), (4.4, 12.2, 2.4), 0.5)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 2.0)
            box(part, "pauldron " + part, (x0, -3.6, -3.2), (x1, 2.2, 3.2), 0.5)
            fx = (x0 - 0.2, x0 + 1.0) if part == "rarm" else (x1 - 1.0, x1 + 0.2)
            box(part, "fin " + part, (fx[0], -5.6, -0.6), (fx[1], -3.6, 1.6), 0.35)
            g0, g1 = out_in(part, 1.0, 0.6)
            box(part, "gauntlet " + part, (g0, 4.6, -3.0), (g1, 10.6, 3.0), 0.45)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2.6, 0.0, -2.8), (2.6, 5.4, 2.6), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "knee " + part, (-1.8, -0.8, -3.4), (1.8, 1.6, -1.4), 0.45)
            box(part, "greave " + part, (-2.6, 1.0, -2.8), (2.6, 4.2, 2.6), 0.45)
            box(part, "boot " + part, (-2.8, 4.2, -3.8), (2.8, 6.1, 2.8), 0.4)
        front = -3.4 - 0.75
    if fine:
        extras(objs, tag, d, T, Sm, lambda part, nm, a, b, inf: child_box(objs[part], f"{tag} {nm}", a, b, T, inf))
        front -= 0.35
    face_marks(objs, tag, front)




# ================================================================== pass 593: the shelves
# (code, strip file key, label, frames, frametime): frames = strip height / width
GREEN = [("W1", "w1_neon", "W1 neon weave", 24, 4), ("W1E", "w1_emerald", "W1 emerald weave", 24, 4),
         ("H1", "h1_neon", "H1 neon hex", 24, 4), ("H2", "h2_neon", "H2 neon hex", 24, 5),
         ("HW", "hw_emerald", "HW emerald", 24, 4), ("BRE", "br1_emerald", "BR1 emerald bricks", 24, 4),
         ("BRJ", "br1_jade", "BR1 jade bricks", 24, 4), ("BRL", "br1_lime", "BR1 lime bricks", 24, 4),
         ("BRN", "br1_neon", "BR1 neon bricks", 24, 4), ("BRD", "brd_neon", "BRD neon bricks", 24, 4),
         ("X1", "x1_emerald", "X1 cosmic dust", 32, 5), ("X3", "x3_emerald", "X3 power aura", 32, 5),
         ("X5E", "x5_emerald", "X5 quantum ripple emerald", 32, 5), ("X5N", "x5_neon", "X5 quantum ripple neon", 32, 5),
         ("X3D1", "x3d1_emerald", "X3D1 emerald glass", 32, 5), ("R2K1", "r2k1", "R2 K1 dark jade (default)", 1, 1)]
BARRIER = [(f"T{i}", f"barrier_t{i}", f"T{i} barrier", 32, 5) for i in (1, 2, 3, 5, 6, 7, 9)]
TEX = GREEN + BARRIER
MATS = {}
for code, key, _, n, ft in TEX:
    im = load_strip(key)
    n = max(1, im.size[1] // max(1, im.size[0]))             # trust the strip itself for the frame count
    MATS[code] = dict(suit=strip_mat(f"WS {code} suit", im, n, ft, 1.2),
                      seam=strip_mat(f"WS {code} bright", im, n, ft, 4.5),
                      pix=strip_mat(f"WS {code} pixel", im, n, ft, 2.6, rnd=True),
                      shell=strip_mat(f"WS {code} shell", im, n, ft, 0.8, alpha_k=0.3))
LBL = mat("WS label", (0.85, 1.0, 0.9), emit=2.0)


def label(text, at, size=0.22):
    cu = bpy.data.curves.new("WS label", "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("WS label " + text, cu)); tl.location = at; tl.rotation_euler = (R(90), 0, 0)
    tl.data.materials.append(LBL)
    return tl


def uv_mesh(name, verts, faces, uvs, m):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uvl = me.uv_layers.new(name="box")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index] if not callable(uvs) else uvs(poly, me.loops[li].vertex_index)
    me.materials.append(m)
    return me


def block_wall(name, at, m, w=3, h=2, d=1):
    """Outer shell of a w x h x d block wall, one texture tile per block face (as constructs are in game)."""
    x0, y0, z0 = at[0] - w / 2, at[1] - d / 2, 0.0
    P = [(x0 + x, y0 + y, z0 + z) for x in (0, w) for y in (0, d) for z in (0, h)]
    F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    AX = [(1, 2), (1, 2), (0, 2), (0, 2), (0, 1), (0, 1)]
    me = bpy.data.meshes.new(name); me.from_pydata(P, [], F); me.update()
    uvl = me.uv_layers.new(name="box")
    for fi, poly in enumerate(me.polygons):
        u, v = AX[fi]
        for li in poly.loop_indices:
            p = P[me.loops[li].vertex_index]
            uvl.data[li].uv = (p[u] - (x0, y0, z0)[u], p[v] - (x0, y0, z0)[v])
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def dome(name, at, m, r=1.5, seg=32, rings=10):
    """A hemisphere shield; UVs are arc lengths in blocks so the texel size stays about one tile per block."""
    V, F, UV = [], [], []
    for i in range(rings + 1):
        el = (math.pi / 2) * i / rings
        for j in range(seg + 1):
            az = 2 * math.pi * j / seg
            V.append((at[0] + r * math.cos(el) * math.cos(az), at[1] + r * math.cos(el) * math.sin(az), r * math.sin(el)))
            UV.append((az * r, el * r))
    for i in range(rings):
        for j in range(seg):
            a = i * (seg + 1) + j; b = a + seg + 1
            F.append((a, a + 1, b + 1, b))
    return link(bpy.data.objects.new(name, uv_mesh(name, V, F, UV, m)))


PIXEL = None


def particles(name, at, mpix, mshell, r=0.75, count=420):
    """Pixels living on a sphere's surface over a faint shell of the same texture, drifting slowly."""
    global PIXEL
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(at[0], at[1], 1.1))
    em = bpy.context.active_object
    for c in em.users_collection:
        c.objects.unlink(em)
    link(em); em.name = name
    # the faint shell is the emitter itself
    uvl = em.data.uv_layers.new(name="box")
    for poly in em.data.polygons:
        for li in poly.loop_indices:
            co = em.data.vertices[em.data.loops[li].vertex_index].co
            uvl.data[li].uv = (math.atan2(co.y, co.x) * r, math.asin(max(-1, min(1, co.z / r))) * r)
    em.data.materials.append(mshell)
    pm = cube_mesh(name + " px", 1.0)
    uv = pm.uv_layers.new(name="box")
    for poly in pm.polygons:
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = ((0, 0), (0.12, 0), (0.12, 0.12), (0, 0.12))[k % 4]
    pm.materials.append(mpix)
    px = link(bpy.data.objects.new(name + " pixel", pm)); px.location = (at[0], at[1], -50)
    px.hide_render = False
    ps = em.modifiers.new("pixels", "PARTICLE_SYSTEM").particle_system
    st = ps.settings
    st.count = count; st.frame_start = 1; st.frame_end = 1; st.lifetime = 5000; st.emit_from = "FACE"
    st.normal_factor = 0.0; st.physics_type = "NEWTON"; st.brownian_factor = 0.015; st.damping = 0.3
    st.effector_weights.gravity = 0.0
    st.render_type = "OBJECT"; st.instance_object = px; st.particle_size = 0.07; st.size_random = 0.6
    st.use_rotations = True; st.rotation_mode = "NOR"; st.phase_factor_random = 2.0
    st.display_method = "RENDER"
    em.show_instancer_for_render = True
    return em


def cube_mesh(name, size=1.0):
    h = size / 2
    verts = [(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    return me


STAND_W, SH_GAP = 11.0, 8.0
cams = {}
x = 0.0
shelf_x = {}
for group, items in (("Green picks", GREEN), ("Barrier surfaces", BARRIER)):
    gx0 = x
    for code, key, tname, _, _ in items:
        Mt = MATS[code]
        sx = x                                                # suit at sx, wall, dome, particles to its right
        objs = make_player(f"WS {code}")
        set_pose(objs, solve(STANCE), np.array([sx, 0.0, 0.0]), 1)
        dress(objs, f"WS {code}", "A1", Mt["suit"], False, Mt["seam"])
        block_wall(f"WS {code} wall", (sx + 3.0, 0.0), Mt["suit"])
        dome(f"WS {code} dome", (sx + 6.6, 0.0), Mt["suit"])
        particles(f"WS {code} particles", (sx + 9.4, 0.0), Mt["pix"], Mt["shell"])
        label(f"{code}  {tname}", (sx + 4.7, 1.6, 2.7), 0.3)
        for nm, xx, w in (("suit", sx, 0), ("wall", sx + 3.0, 0), ("dome", sx + 6.6, 0), ("particles", sx + 9.4, 0)):
            cam(f"Cam {code} {nm}", (xx + 1.6, -4.6, 1.6), (xx, 0, 1.0), 40)
        cams[code] = cam(f"Cam {code}", (sx + 4.7, -14.0, 3.0), (sx + 4.7, 0, 1.0), 40)
        x += STAND_W + 2.0
    shelf_x[group] = (gx0, x - 2.0)
    label(group.upper(), ((gx0 + x - 2.0) / 2, 2.5, 4.2), 1.0)
    x += SH_GAP

# --------------------------------------------------------------- WALLS: particle walls W1-W5 (pass 700, unchanged)
WX = x + 22.0
pw_scene = bpy.data.scenes.get("Particle Walls")
if pw_scene is not None:
    cy = bpy.data.objects["Cam wall all"].location.y + 13.5
    for o in list(pw_scene.collection.all_objects):
        if o.name in ("PW floor", "PW sun"):
            continue
        if o.name not in col.objects:
            col.objects.link(o)
        if o.parent is None:
            o.location.x += WX - 50.0
            o.location.y -= cy
    bpy.data.scenes.remove(pw_scene)
label("PARTICLE WALLS", (WX, 2.5, 5.0), 1.0)
x = WX + 34.0

# --------------------------------------------------------------- RINGS and LANTERNS
ASSETS = os.path.join(FOLDER, "kl_assets")


def kind_mats():
    out = []
    base = bpy.data.materials.new("WS model base"); base.use_nodes = True
    for k, (metal, rough, emit) in enumerate(((0.0, 0.55, 0.0), (1.0, 0.25, 0.0), (0.0, 0.4, 3.0), (0.0, 0.4, 5.0),
                                              (0.6, 0.3, 0.0), (0.0, 0.2, 2.0))):
        m = bpy.data.materials.new(f"WS model kind {k}"); m.use_nodes = True
        N_, L_ = m.node_tree.nodes, m.node_tree.links
        p = N_.get("Principled BSDF"); at = N_.new("ShaderNodeAttribute"); at.attribute_name = "col"
        L_.new(at.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Metallic"].default_value = metal; p.inputs["Roughness"].default_value = rough
        if emit:
            gw = N_.new("ShaderNodeAttribute"); gw.attribute_name = "glow"
            mul = N_.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"; mul.inputs[1].default_value = emit
            mul.inputs[2].default_value = 0.0
            L_.new(gw.outputs["Fac"], mul.inputs[0])
            L_.new(at.outputs["Color"], p.inputs["Emission Color"]); L_.new(mul.outputs[0], p.inputs["Emission Strength"])
        out.append(m)
    return out


KMATS = kind_mats()


def npz_model(name, path, at, scale, rot=0.0):
    d = np.load(path)
    q = d["quads"]; verts = q.reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    g = me.attributes.new("glow", "FLOAT", "CORNER")
    gl = np.asarray(d["glow"], np.float32) if "glow" in d.files else np.ones(len(q), np.float32)
    g.data.foreach_set("value", np.repeat(gl, 4))
    for m in KMATS:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.clip(np.asarray(d["kind"], np.int32), 0, len(KMATS) - 1))
    o = link(bpy.data.objects.new(name, me))
    o.scale = (scale,) * 3
    # stand it on the floor, centred on `at`
    bb = verts * scale
    o.location = (at[0] - (bb[:, 0].min() + bb[:, 0].max()) / 2, at[1] - (bb[:, 1].min() + bb[:, 1].max()) / 2,
                  0.6 - bb[:, 2].min() if at[2] is None else at[2] - bb[:, 2].min())
    o.rotation_euler = (0, 0, rot)
    return o


def pedestal(at, h=0.6):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.45, depth=h, location=(at[0], at[1], h / 2))
    p = bpy.context.active_object
    for c in p.users_collection:
        c.objects.unlink(p)
    link(p); p.name = "WS pedestal"; p.data.materials.append(mat("WS pedestal", (0.06, 0.065, 0.07), rough=0.4))
    return p


RINGS = [("ring_sq", "Square emblem ring (default)"), ("ring_a", "Ring A"), ("ring_b", "Ring B"), ("ring_b1", "Ring B1"),
         ("ring_b2", "Ring B2"), ("ring_b3", "Ring B3"), ("ring_b4", "Ring B4"), ("ring_c", "Ring C"),
         ("ring_l1", "Ring L1"), ("ring_l2", "Ring L2"), ("ring_l3", "Ring L3")]
RX = x
for i, (key, nm) in enumerate(RINGS):
    px_ = RX + i * 1.6
    pedestal((px_, 0.0))
    p = os.path.join(ASSETS, key + ".npz")
    if os.path.exists(p):
        npz_model("WS " + nm, p, (px_, 0.0, None), 2.0 / 16.0, R(-25))
    label(nm, (px_, 0.6, 1.75), 0.13)
cam("Cam rings", (RX + 8.0, -14.0, 2.6), (RX + 8.0, 0, 0.9), 40)
label("RINGS (2x size)", (RX + 8.0, 2.5, 2.6), 0.6)
x = RX + 11 * 1.6 + 8.0

LX = x
LANT = [("dark_lantern_L1.glb", "Dark Lantern L1"), ("dark_lantern_L2.glb", "Dark Lantern L2"),
        ("dark5_l1.npz", "Dark Lantern 5 L1"), ("dark5_l2.npz", "Dark Lantern 5 L2"), ("blue_lantern.glb", "Blue Lantern")]
for i, (fn, nm) in enumerate(LANT):
    px_ = LX + i * 2.6
    p = os.path.join(ASSETS, fn)
    if not os.path.exists(p):
        continue
    if fn.endswith(".npz"):
        npz_model("WS " + nm, p, (px_, 0.0, 0.0), 1.0 / 16.0, R(-20))
    else:
        before = set(bpy.data.objects)
        try:
            bpy.ops.import_scene.gltf(filepath=p)
        except Exception as e:
            print("gltf", fn, e); continue
        new = [o for o in bpy.data.objects if o not in before]
        root = link(bpy.data.objects.new("WS " + nm, None))
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            if o.parent is None:
                o.parent = root
        bpy.context.view_layer.update()
        pts = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]
        if pts:
            lo = Vector((min(p_.x for p_ in pts), min(p_.y for p_ in pts), min(p_.z for p_ in pts)))
            hi = Vector((max(p_.x for p_ in pts), max(p_.y for p_ in pts), max(p_.z for p_ in pts)))
            k = 1.3 / max(1e-6, hi.z - lo.z)
            root.scale = (k, k, k)
            root.location = (px_ - k * (lo.x + hi.x) / 2, -k * (lo.y + hi.y) / 2, -k * lo.z)
            root.rotation_euler = (0, 0, R(-20))
    label(nm, (px_, 0.9, 2.5), 0.16)
cam("Cam lanterns", (LX + 5.2, -14.0, 2.4), (LX + 5.2, 0, 1.0), 40)
label("LANTERNS", (LX + 5.2, 2.5, 3.4), 0.6)
x = LX + 5 * 2.6

# --------------------------------------------------------------- shelf cameras, floor, light, save
for group, (a_, b_) in shelf_x.items():
    mid = (a_ + b_) / 2
    cam(f"Cam shelf {group}", (mid, -(b_ - a_) * 0.95 - 10, 14.0), (mid, 0, 1.0), 35)
cam("Cam walls", (WX, -19.0, 3.2), (WX, 0, 1.5), 20)
MIDX = x / 2
cam("Cam workshop", (MIDX, -x * 0.75, x * 0.22), (MIDX, 0, 1.0), 35)
_rs = RINGM.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for _f, _e in ((1, 3.0), (FORM_END - 3, 3.0), (FORM_END + 1, 30.0), (FORM_END + 10, 3.0), (LOOP, 3.0)):
    _rs.default_value = _e; _rs.keyframe_insert("default_value", frame=_f)
scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=1, location=(MIDX, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "WS floor"; g.scale = (x + 200, 400, 1)
g.data.materials.append(mat("WS floor", (0.05, 0.055, 0.06), rough=0.8))
world = bpy.data.worlds.new("WS world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.045, 1)
scene.world = world
sun = link(bpy.data.objects.new("WS sun", bpy.data.lights.new("WS sun", "SUN")))
sun.data.energy = 1.6; sun.rotation_euler = (R(45), R(-10), R(-20))
fill = link(bpy.data.objects.new("WS fill", bpy.data.lights.new("WS fill", "SUN")))
fill.data.energy = 0.5; fill.rotation_euler = (R(-60), 0, R(160))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("WS Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm_, val in (("Size", 0.6), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm_ in gl.inputs:
            gl.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects["Cam W1"]
scene.frame_set(60)
for sc_ in list(bpy.data.scenes):
    if sc_ != scene:
        bpy.data.scenes.remove(sc_)
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

