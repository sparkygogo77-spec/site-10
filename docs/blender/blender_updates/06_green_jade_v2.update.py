# Pass 6: Green Lantern construct walls, take two. The wall itself is green jade, milky and
# lit from inside, with the smoke drifting through it, darker where it is thick. Round the whole wall
# stands a separate light barrier, a quarter block out: clear glass that glows green at its edges
# and carries its own wisps of glowing smoke, flowing a different way from the smoke in the jade.
import bpy

scene = bpy.context.scene
walls = bpy.data.objects["Construct Walls"]
img = bpy.data.images["construct_flow.png"]
FRAMES, PERIOD = 48, 8.0
SEC_PER_FRAME = 6 / 20


def build_nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return nt.nodes, nt.links


def mathop(N, L, op, a, b=None):
    n = N.new("ShaderNodeMath")
    n.operation = op
    for i, src in enumerate((a, b)):
        if src is None:
            continue
        if isinstance(src, (int, float)):
            n.inputs[i].default_value = src
        else:
            L.new(src, n.inputs[i])
    return n.outputs[0]


def smoke_mask(N, L, ax, ay, frame_shift, drift):
    """0 where the flow texture is clear white, 1 where its smoke is thickest; ax, ay are world
    coordinates (in blocks) across the face; frame_shift starts it at another point of the loop."""
    clock = N.new("ShaderNodeValue")
    fc = clock.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"
    fc.driver.expression = f"frame / ({scene.render.fps} * {SEC_PER_FRAME}) + {frame_shift}"
    fl = mathop(N, L, "FLOOR", clock.outputs[0])
    blend = mathop(N, L, "SUBTRACT", clock.outputs[0], fl)
    # a slow slide on top of the texture's own drift, so the two layers move differently
    slide = mathop(N, L, "MULTIPLY", clock.outputs[0], drift)
    u = mathop(N, L, "FRACT", mathop(N, L, "DIVIDE", mathop(N, L, "ADD", ax, slide), PERIOD))
    v = mathop(N, L, "FRACT", mathop(N, L, "DIVIDE", ay, PERIOD))

    def sample(index):
        i = mathop(N, L, "MODULO", index, float(FRAMES))
        vv = mathop(N, L, "DIVIDE", mathop(N, L, "ADD", v, mathop(N, L, "SUBTRACT", float(FRAMES - 1), i)), float(FRAMES))
        comb = N.new("ShaderNodeCombineXYZ")
        L.new(u, comb.inputs[0])
        L.new(vv, comb.inputs[1])
        t = N.new("ShaderNodeTexImage")
        t.image = img
        t.interpolation = "Closest"
        t.extension = "CLIP"
        L.new(comb.outputs[0], t.inputs["Vector"])
        bw = N.new("ShaderNodeRGBToBW")
        L.new(t.outputs["Color"], bw.inputs[0])
        return bw.outputs[0]

    a = sample(fl)
    b = sample(mathop(N, L, "ADD", fl, 1.0))
    mix = N.new("ShaderNodeMix")
    L.new(blend, mix.inputs["Factor"])
    L.new(a, mix.inputs["A"])
    L.new(b, mix.inputs["B"])
    # the texture runs from white (0.96) down to smoke grey (about 0.4): stretch that to 0..1
    m = mathop(N, L, "MULTIPLY", mathop(N, L, "SUBTRACT", 0.95, mix.outputs[0]), 2.6)
    return mathop(N, L, "MINIMUM", mathop(N, L, "MAXIMUM", m, 0.0), 1.0)


def world_xz(N, L):
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep.inputs[0])
    return sep.outputs["X"], sep.outputs["Z"]


# ---- the jade ------------------------------------------------------------------------------------
jade = bpy.data.materials.get("construct_jade") or bpy.data.materials.new("construct_jade")
N, L = build_nodes(jade)
out = N.new("ShaderNodeOutputMaterial")
x, z = world_xz(N, L)
m = smoke_mask(N, L, x, z, 0.0, 0.0)
ramp = N.new("ShaderNodeValToRGB")          # clear jade -> deep green where the smoke is thick
ramp.color_ramp.elements[0].color = (0.07, 0.55, 0.22, 1)
ramp.color_ramp.elements[1].color = (0.004, 0.035, 0.015, 1)
ramp.color_ramp.elements.new(0.4).color = (0.02, 0.20, 0.08, 1)
L.new(m, ramp.inputs["Fac"])
bsdf = N.new("ShaderNodeBsdfPrincipled")
L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.22
bsdf.inputs["Subsurface Weight"].default_value = 0.6
bsdf.inputs["Subsurface Radius"].default_value = (0.3, 1.0, 0.45)
bsdf.inputs["Coat Weight"].default_value = 1.0
bsdf.inputs["Coat Roughness"].default_value = 0.05
# lit from inside: the clear jade glows, the smoke holds the glow back
L.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
inner = mathop(N, L, "MULTIPLY", mathop(N, L, "SUBTRACT", 1.0, m), 0.7)
L.new(inner, bsdf.inputs["Emission Strength"])
L.new(bsdf.outputs[0], out.inputs["Surface"])
walls.data.materials.clear()
walls.data.materials.append(jade)

# ---- the light barrier: its own box, a quarter block out round the whole wall ----------------------
old = bpy.data.objects.get("Light Barrier")
if old:
    bpy.data.objects.remove(old)
xs = [v.co.x for v in walls.data.vertices]
ys = [v.co.y for v in walls.data.vertices]
zs = [v.co.z for v in walls.data.vertices]
P = 0.25
x0, x1, y0, y1, z0, z1 = min(xs) - P, max(xs) + P, min(ys) - P, max(ys) + P, min(zs), max(zs) + P
bv = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
bf = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)]
bm = bpy.data.meshes.new("light_barrier")
bm.from_pydata(bv, [], bf)
# cut it into 1-block squares so the edge glow and smoke shade smoothly across it
barrier = bpy.data.objects.new("Light Barrier", bm)
barrier.location = walls.location
scene.collection.objects.link(barrier)

shell = bpy.data.materials.get("light_barrier") or bpy.data.materials.new("light_barrier")
N, L = build_nodes(shell)
out = N.new("ShaderNodeOutputMaterial")
x, z = world_xz(N, L)
m2 = smoke_mask(N, L, x, z, 24.0, 0.35)       # half a loop on, sliding sideways as well
lw = N.new("ShaderNodeLayerWeight")
lw.inputs["Blend"].default_value = 0.35
# how much light the barrier shows: its grazing edges, the wisps on it, and a faint sheen everywhere
edge = mathop(N, L, "POWER", lw.outputs["Facing"], 2.0)
glow = mathop(N, L, "ADD", mathop(N, L, "ADD", mathop(N, L, "MULTIPLY", edge, 1.1), mathop(N, L, "MULTIPLY", m2, 0.3)), 0.0)
glow = mathop(N, L, "MINIMUM", glow, 1.0)
em = N.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (0.35, 1.0, 0.5, 1)
em.inputs["Strength"].default_value = 2.2
glass = N.new("ShaderNodeBsdfGlossy")
glass.inputs["Color"].default_value = (0.7, 1.0, 0.8, 1)
glass.inputs["Roughness"].default_value = 0.03
tr = N.new("ShaderNodeBsdfTransparent")
see = N.new("ShaderNodeMixShader")            # clear with a thin glassy reflection
see.inputs[0].default_value = 0.12
L.new(tr.outputs[0], see.inputs[1])
L.new(glass.outputs[0], see.inputs[2])
mix = N.new("ShaderNodeMixShader")
L.new(glow, mix.inputs[0])
L.new(see.outputs[0], mix.inputs[1])
L.new(em.outputs[0], mix.inputs[2])
L.new(mix.outputs[0], out.inputs["Surface"])
try:
    shell.surface_render_method = "BLENDED"
except Exception:
    pass
shell.use_backface_culling = False
bm.materials.append(shell)

# a little green light spilling from the barrier onto everything near it
lamp = bpy.data.objects.get("Barrier Light")
if lamp is None:
    ld = bpy.data.lights.new("Barrier Light", "AREA")
    lamp = bpy.data.objects.new("Barrier Light", ld)
    scene.collection.objects.link(lamp)
lamp.data.shape = "RECTANGLE"
lamp.data.size, lamp.data.size_y = x1 - x0, z1 - z0
lamp.data.energy = 60
lamp.data.color = (0.3, 1.0, 0.45)
lamp.location = (walls.location.x + (x0 + x1) / 2, walls.location.y + y0 - 0.6, walls.location.z + (z0 + z1) / 2)
lamp.rotation_euler = (1.5708, 0, 0)          # facing the wall

# a three-quarter view so the barrier's depth and edges show
cam = bpy.data.objects["Walls Camera"]
from mathutils import Vector
cam.location = (walls.location.x - 24.0, -34.0, 11.0)
centre = Vector((walls.location.x + (x0 + x1) / 2, walls.location.y, walls.location.z + (z0 + z1) / 2))
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
