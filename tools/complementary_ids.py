"""Writes Complementary Reimagined's block/item/entity.properties with the Lantern Ring's blocks added.

Complementary picks light colour, glow and effects by the material ID each block, item and entity is
listed under. This adds ours to the lines of the vanilla things they should copy (the same mapping
the mod applies at runtime in client/ShaderPackIds.java) and writes the three files to
shaderpacks/complementary/shaders/. Run it on a copy of the pack's own shaders/ folder so the IDs
match the pack version exactly:

    python3 tools/complementary_ids.py path/to/ComplementaryReimagined/shaders
"""
import pathlib
import re
import sys

N = "lanternring:"
CORPS_BLOCKS = ["light_construct", "construct_brick", "power_battery"]


def corps(colour):
    return [f"{N}{b}:corps={colour}" for b in CORPS_BLOCKS]


GHOSTS = ["ghost_" + g for g in "stairs slab fence pane wall door trapdoor gate carpet ladder lantern leaves plant".split()]

# The vanilla block whose line each of ours joins: its light colour under Complementary.
BLOCKS = {
    "verdant_froglight": corps("green") + [N + "blast_glow", N + "beam_glow", N + "ring_forge",
                                           N + "great_battery:filled=true"] + [N + g for g in GHOSTS],
    "redstone_block": corps("red") + [N + "lava_font:filled=true", N + "ember_liquid"],
    "crying_obsidian": corps("violet"),
    "shroomlight": corps("orange"),
    "soul_lantern": corps("blue"),
    "ochre_froglight": corps("yellow"),
    # The green Deluge is drawn as the pack's water (waves, reflections, its green tint).
    "water": [N + "hard_light_liquid"],
}
ITEMS = {
    "verdant_froglight": [N + "power_battery", N + "great_battery", N + "ring_forge"],
    "redstone_block": [N + "lava_font"],
}
ENTITIES = {
    "glow_squid": [N + "warden_construct", N + "dragon_construct", N + "sentry_construct"],
}


def patch(text, prefix, extras):
    done = set()

    def add(match):
        key, names = match.group(1), match.group(2)
        words = names.split()
        for vanilla, ours in extras.items():
            if vanilla in words:
                done.add(vanilla)
                words += [o for o in ours if o not in words]
        return f"{key}={' '.join(words)}"

    out = re.sub(rf"^({prefix}\.\d+)=(.*)$", add, text, flags=re.M)
    missing = set(extras) - done
    if missing:
        sys.exit(f"{prefix}.properties has no line for {sorted(missing)}")
    return out


def main():
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    dest = pathlib.Path(__file__).resolve().parent.parent / "shaderpacks/complementary/shaders"
    dest.mkdir(parents=True, exist_ok=True)
    for name, extras in (("block", BLOCKS), ("item", ITEMS), ("entity", ENTITIES)):
        text = (src / f"{name}.properties").read_text()
        (dest / f"{name}.properties").write_text(patch(text, name, extras))
        print("wrote", dest / f"{name}.properties")


if __name__ == "__main__":
    main()
