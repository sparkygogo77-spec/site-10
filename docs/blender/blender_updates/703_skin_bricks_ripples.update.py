# Pass 703: BRD bricks and X5E ripples, three takes each (Chat E, construct surfaces, 2026-10-15). J re-rated 701 at 18:47:
#   BRD (was KEEP, now IMPROVE): "try giving this one more detail on the bricks, or make them one of our new metallic
#        materials for the brick material (not the glowing lines though)"
#   X5E: "we need textures where the ripples are more efficiently packed onto big texture surfaces"
# Textures from tools/construct_designs11.py (LanternLive\suit_tex\brdc_neon_strip.png, brdc_mask_strip.png,
# x5g/x5i/x5r_emerald_strip.png). The brick metals are the pass 603 suit metals (pinstripe alloy, hex plate), applied
# only where the mask says brick; the mortar and sparks keep their glow.
#   BRDa  carved bricks: bevelled edges, grain, hairline cracks, chipped corners, pits; glowing mortar and sparks as BRD
#   BRDb  brushed alloy bricks: BRDa's carving as relief on brushed metal (603 T4 pinstripe alloy), mortar still glowing
#   BRDc  dark gunmetal bricks: hammered dark metal (603 T2 hex plate's metal) with the carving as relief, mortar glowing
#   X5Pa  ripple grid: one ripple source per block (16 per tile instead of 1), rings interlocking
#   X5Pb  ripple interference: seven sources per tile, waves adding into a moving lattice over the whole surface
#   X5Pc  ripple rain: 46 small ripples spawning all over at different times
# Each is a copy of the texture's lane (suit, 3x2 wall, dome, particle sphere) in its own row, with 701's close tour
# "Cam <code> close". Opens LanternLive\constructs\skin_workshop_close.blend, saves skin_variations2.blend.
import math, os
import bpy
import numpy as np
from mathutils import Vector, Matrix

_src = os.path.join(os.environ.get("KL_REPO", "/home/claude/site-10"), "docs", "blender", "blender_updates",
                    "702_skin_variations.update.py")
_txt = open(_src).read()
exec(compile(_txt[:_txt.index("made = []")], _src, "exec"), globals())     # opens the workshop; bbox, make_tour, copy_lane
OUT = os.path.join(FOLDER, "constructs", "skin_variations2.blend")
TEXDIR = os.path.join(FOLDER, "suit_tex")


def strip(key):
    im = bpy.data.images.load(os.path.join(TEXDIR, key + "_strip.png")); im.name = "suit strip " + key
    im.pack()
    return im


NEW = {k: strip(k) for k in ("brdc_neon", "brdc_mask", "x5g_emerald", "x5i_emerald", "x5r_emerald")}
NEW["brdc_mask"].colorspace_settings.name = "Non-Color"
OLD = {"BRD": bpy.data.images["suit strip brd_neon"], "X5E": bpy.data.images["suit strip x5_emerald"]}


def swap_images(code, im):
    """Every material on the lane's objects that samples the old strip now samples the new one."""
    seen = set()
    for o in bpy.data.objects:
        if not (o.name.startswith(f"WS {code} ") or o.name.startswith(f"KL WS {code} ")) or o.type != "MESH":
            continue
        for m in o.data.materials:
            if m is None or m.name in seen or not m.use_nodes:
                continue
            seen.add(m.name)
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image in OLD.values():
                    n.image = im
    return seen


def metal_bricks(m, kind):
    """Bricks become metal, the glowing lines stay light: sample the mask strip exactly as the colour strip is sampled
    (same two frame lookups and blend), then metal where mask = 0, the strip's own glow where mask = 1."""
    N, Lk = m.node_tree.nodes, m.node_tree.links
    texs = sorted([n for n in N if n.type == "TEX_IMAGE"], key=lambda n: n.name)
    blend = next(n for n in N if n.type == "MIX" and n.data_type == "RGBA")
    fac = blend.inputs["Factor"].links[0].from_socket
    p = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    col = p.inputs["Base Color"].links[0].from_socket
    ms = []
    for t in texs:
        mt = N.new("ShaderNodeTexImage"); mt.image = NEW["brdc_mask"]; mt.interpolation = "Closest"
        Lk.new(t.inputs["Vector"].links[0].from_socket, mt.inputs["Vector"]); ms.append(mt)
    mm = N.new("ShaderNodeMix"); mm.data_type = "FLOAT"
    Lk.new(fac, mm.inputs["Factor"]); Lk.new(ms[0].outputs["Color"], mm.inputs["A"]); Lk.new(ms[1].outputs["Color"], mm.inputs["B"])
    mask = mm.outputs["Result"]
    # relief from the carving: the strip's brightness drives a bump (bevels, cracks, chips read in the metal)
    bw = N.new("ShaderNodeRGBToBW"); Lk.new(col, bw.inputs[0])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6; bump.inputs["Distance"].default_value = 0.02
    Lk.new(bw.outputs[0], bump.inputs["Height"])
    uvn = next(n for n in N if n.type == "UVMAP")
    if kind == "alloy":                                # 603 T4 pinstripe alloy: brushed streaks, anisotropic
        no = N.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = 40.0; no.inputs["Detail"].default_value = 2.0
        st = N.new("ShaderNodeVectorMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = (1.0, 60.0, 1.0)
        Lk.new(uvn.outputs["UV"], st.inputs[0]); Lk.new(st.outputs[0], no.inputs["Vector"])
        sh = N.new("ShaderNodeMapRange"); sh.inputs["To Min"].default_value = 0.55; sh.inputs["To Max"].default_value = 0.95
        Lk.new(no.outputs["Fac"], sh.inputs["Value"])
        tint, rough, metal = (0.42, 0.52, 0.46), 0.22, 0.95
        try:
            p.inputs["Anisotropic"].default_value = 0.8
        except Exception:
            pass
    else:                                              # 603 T2 hex plate's metal, darker and hammered
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 18.0
        Lk.new(uvn.outputs["UV"], vo.inputs["Vector"])
        sh = N.new("ShaderNodeMapRange"); sh.inputs["To Min"].default_value = 0.5; sh.inputs["To Max"].default_value = 1.0
        Lk.new(vo.outputs["Distance"], sh.inputs["Value"])
        b2 = N.new("ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.35; b2.inputs["Distance"].default_value = 0.01
        Lk.new(vo.outputs["Distance"], b2.inputs["Height"]); Lk.new(b2.outputs["Normal"], bump.inputs["Normal"])
        tint, rough, metal = (0.11, 0.15, 0.13), 0.32, 0.85
    # metal colour = tint x brushed/hammered shade x the brick's own carved tone (so dark cracks stay dark)
    tone = N.new("ShaderNodeMapRange"); tone.inputs["From Min"].default_value = 0.0; tone.inputs["From Max"].default_value = 0.12
    tone.inputs["To Min"].default_value = 0.35; tone.inputs["To Max"].default_value = 1.0; Lk.new(bw.outputs[0], tone.inputs["Value"])
    k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; Lk.new(sh.outputs["Result"], k.inputs[0]); Lk.new(tone.outputs["Result"], k.inputs[1])
    mc = N.new("ShaderNodeVectorMath"); mc.operation = "SCALE"; mc.inputs[0].default_value = tint
    Lk.new(k.outputs[0], mc.inputs["Scale"])
    bc = N.new("ShaderNodeMix"); bc.data_type = "RGBA"
    Lk.new(mask, bc.inputs["Factor"]); Lk.new(mc.outputs[0], bc.inputs["A"]); Lk.new(col, bc.inputs["B"])
    Lk.new(bc.outputs["Result"], p.inputs["Base Color"])
    inv = N.new("ShaderNodeMath"); inv.operation = "MULTIPLY_ADD"; inv.inputs[1].default_value = -metal; inv.inputs[2].default_value = metal
    Lk.new(mask, inv.inputs[0]); Lk.new(inv.outputs[0], p.inputs["Metallic"])
    rg = N.new("ShaderNodeMath"); rg.operation = "MULTIPLY_ADD"; rg.inputs[1].default_value = 0.5 - rough; rg.inputs[2].default_value = rough
    Lk.new(mask, rg.inputs[0]); Lk.new(rg.outputs[0], p.inputs["Roughness"])
    es = p.inputs["Emission Strength"]
    if not es.links:                                   # only the lines glow (a little stronger, so they read on the metal)
        e = N.new("ShaderNodeMath"); e.operation = "MULTIPLY"; e.inputs[1].default_value = es.default_value * 1.6
        Lk.new(mask, e.inputs[0]); Lk.new(e.outputs[0], es)
    Lk.new(bump.outputs["Normal"], p.inputs["Normal"])
    # metal is solid where it's brick (constructs stay see-through in the glowing lines' own alpha)
    a_node = next((n for n in N if n.type == "MATH" and n.operation == "MAXIMUM"), None)
    if a_node is not None:
        hi = N.new("ShaderNodeMath"); hi.operation = "MAXIMUM"; hi.inputs[1].default_value = 0.0
        slot = next((i for i in a_node.inputs if i.links and i.links[0].from_node.type == "MATH"
                     and i.links[0].from_node.operation == "MULTIPLY"
                     and any(x.links and x.links[0].from_node.type == "MIX" for x in i.links[0].from_node.inputs)), None)
        src = slot.links[0].from_socket if slot is not None else None
        if src is not None:
            lift = N.new("ShaderNodeMath"); lift.operation = "MULTIPLY_ADD"; lift.inputs[1].default_value = 0.6; lift.inputs[2].default_value = 0.25
            # alpha' = max(alpha, 0.25 + 0.6 * (1 - mask)) on bricks: a solid-looking metal that you can still just see through
            one_m = N.new("ShaderNodeMath"); one_m.operation = "SUBTRACT"; one_m.inputs[0].default_value = 1.0
            Lk.new(mask, one_m.inputs[1]); Lk.new(one_m.outputs[0], lift.inputs[0])
            Lk.new(src, hi.inputs[0]); Lk.new(lift.outputs[0], hi.inputs[1])
            Lk.new(hi.outputs[0], slot)


VARS703 = [("BRD", "a", "carved", "brdc_neon", None), ("BRD", "b", "brushed alloy", "brdc_neon", "alloy"),
           ("BRD", "c", "dark gunmetal", "brdc_neon", "gunmetal"),
           ("X5E", "a", "ripple grid", "x5g_emerald", None), ("X5E", "b", "ripple interference", "x5i_emerald", None),
           ("X5E", "c", "ripple rain", "x5r_emerald", None)]
ID = dict(sat=1.0, val=1.0, glow=1.0)
made = []
for code, v, vname, key, metal in VARS703:
    nc = ("X5P" if code == "X5E" else code) + v   # X5P (packed): 702 already has X5Ea-c
    n = copy_lane(code, nc, Vector((0.0, ROW[v], 0.0)), v + "703", ID)
    mats = swap_images(nc, NEW[key])
    if metal:
        for mn in mats:
            if mn.startswith(f"WS {code} suit") or mn.startswith(f"WS {code} shell"):
                metal_bricks(bpy.data.materials[mn], metal)
    make_tour(nc)
    made.append(nc)
    print(nc, vname, n, "objects", sorted(mats), flush=True)

scene.frame_start, scene.frame_end = 1, 160
scene.camera = bpy.data.objects.get("Cam BRDa close")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("saved", OUT, made)
