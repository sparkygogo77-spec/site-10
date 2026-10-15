# Pass 704: ripple packing, three takes for each of 702's X5Ea, X5Eb, X5Na (Chat E, construct surfaces, 2026-10-15).
# J rated 702 at 20:56: X5Ea (emerald, deeper), X5Eb (emerald, brighter), X5Na (neon, deeper) IMPROVE with no notes ->
# three new labelled variations each, with his 701 X5E note in mind: "we need textures where the ripples are more
# efficiently packed onto big texture surfaces". X5Ec dropped.
# Each take keeps its 702 parent's colour and grading (deeper: value x0.6, saturation x1.3, glow x0.7; brighter: glow
# x1.6, saturation x1.3) and changes how the ripples are packed (strips from tools/construct_designs11.py):
#   1  grid          one ripple source per block (16 per 4 x 4 tile instead of 1), neighbours out of step
#   2  honeycomb     sources on a hex lattice, about two per block, rings meeting their six neighbours along clean lines
#   3  interference  seven sources per tile whose waves add up into a moving lattice over the whole surface
# Takes X5Ea1-3, X5Eb1-3, X5Na1-3, each a copy of the texture's lane in its own row with 701's close tour
# "Cam <code> close". Opens LanternLive\constructs\skin_workshop_close.blend, saves skin_variations3.blend.
import os
import bpy
from mathutils import Vector

_src = os.path.join(os.environ.get("KL_REPO", "/home/claude/site-10"), "docs", "blender", "blender_updates",
                    "702_skin_variations.update.py")
_txt = open(_src).read()
exec(compile(_txt[:_txt.index("made = []")], _src, "exec"), globals())     # opens the workshop; make_tour, copy_lane, var_mat
OUT = os.path.join(FOLDER, "constructs", "skin_variations3.blend")
TEXDIR = os.path.join(FOLDER, "suit_tex")
OLD = {bpy.data.images["suit strip x5_emerald"], bpy.data.images["suit strip x5_neon"]}


def strip(key):
    im = bpy.data.images.load(os.path.join(TEXDIR, key + "_strip.png")); im.name = "suit strip " + key
    im.pack()
    return im


PACK = [("1", "grid", "x5g"), ("2", "honeycomb", "x5h"), ("3", "interference", "x5i")]
PARENTS = [("X5Ea", "X5E", "emerald", VARS["a"]), ("X5Eb", "X5E", "emerald", VARS["b"]), ("X5Na", "X5N", "neon", VARS["a"])]
IMG = {f"{k}_{pal}": strip(f"{k}_{pal}") for _, _, pal, _ in PARENTS for _, _, k in PACK}

made = []
row = 0
for parent, code, pal, (gname, p) in PARENTS:
    for n_, pname, k in PACK:
        nc = parent + n_
        y = -28.0 - 14.0 * row; row += 1
        copy_lane(code, nc, Vector((0.0, y, 0.0)), parent[-1] + "704" + n_, p)
        for o in bpy.data.objects:
            if (o.name.startswith(f"WS {nc} ") or o.name.startswith(f"KL WS {nc} ")) and o.type == "MESH":
                for m in o.data.materials:
                    if m is not None and m.use_nodes:
                        for nd in m.node_tree.nodes:
                            if nd.type == "TEX_IMAGE" and nd.image in OLD:
                                nd.image = IMG[f"{k}_{pal}"]
        make_tour(nc)
        made.append(nc)
        print(nc, gname, pname, "row y", y, flush=True)

scene.frame_start, scene.frame_end = 1, 160
scene.camera = bpy.data.objects.get("Cam X5Ea1 close")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("saved", OUT, made)
