"""Turn a Blender block plan (docs/handoff/.../*.json from the lead Blender chat) into the compact
plan the game reads: python tools/blender_plan.py <in.json> <out.plan>

The JSON has parts, each a list of [x, y, z, name] in Minecraft axes round the structure's centre,
with names being Blender texture names. The .plan file is plain text:
    block <index> <block id>           the palette, Blender names mapped to game blocks
    part <name> <moving 0|1>           then one "x y z index" line per block of that part
Blocks are written bottom layer first, so the game can raise a structure in that order.
"""
import json, sys

# Blender texture names that aren't block ids as they stand.
NAMES = {
    "nebula_glass_blue": "minecraft:light_blue_stained_glass",
    "nebula_glass_red": "minecraft:red_stained_glass",
    "construct_brick_blue": "lanternring:construct_brick[corps=blue]",
    "construct_brick_red": "lanternring:rage_light",
    "hay_block_side": "minecraft:hay_block",
    "smoker_front": "minecraft:smoker",
    "campfire_fire": "minecraft:campfire",
    "magma": "minecraft:magma_block",
}
MOD = {"hope_inlay", "skystone_tiles", "skystone_bricks", "hope_lamp", "hope_quartz_bricks", "hope_quartz_pillar",
       "hope_bricks", "hope_crystal", "rage_light"}


def block_id(name):
    if name in NAMES:
        return NAMES[name]
    return ("lanternring:" if name in MOD else "minecraft:") + name


src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src))
palette = {}
lines = []
for pname, part in d["parts"].items():
    lines.append("part %s %d" % (pname.replace(" ", "_"), 1 if part.get("moving") else 0))
    for x, y, z, name in sorted(part["blocks"], key=lambda b: (b[1], b[0], b[2])):
        bid = block_id(name)
        i = palette.setdefault(bid, len(palette))
        lines.append("%d %d %d %d" % (x, y, z, i))
with open(out, "w") as fh:
    fh.write("# %s, from the lead Blender chat's block plan (tools/blender_plan.py)\n" % d.get("take", src))
    for bid, i in palette.items():
        fh.write("block %d %s\n" % (i, bid))
    fh.write("\n".join(lines) + "\n")
print(out, len(lines), "lines,", len(palette), "blocks")
