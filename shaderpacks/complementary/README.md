# Lantern Ring files for Complementary Reimagined

Complementary decides light colour, glow and effects from the ID each block, item and entity is
listed under in `shaders/block.properties`, `item.properties` and `entity.properties`. These copies
add the Lantern Ring's things to the lines of the vanilla things they should look like.

The mod already does the same thing by itself when Iris loads a pack (`client/ShaderPackIds.java`),
so these files are optional: use them if the mod's automatic mapping ever stops working (a new Iris
version), or to see exactly what is mapped.

| Lantern Ring | Filed under | Look in Complementary |
|---|---|---|
| Green constructs, lantern, Blast and Beam light, Great Battery, Ring Forge, Build ghosts | verdant froglight | green light, glowing |
| Red constructs and lantern, filled Lava Font, Red Deluge liquid | redstone block | red light |
| Violet constructs and lantern | crying obsidian | purple light |
| Orange constructs and lantern | shroomlight | orange light |
| Blue constructs and lantern | soul lantern | blue-cyan light |
| Green Deluge liquid | water | the pack's water, tinted green |
| Held lantern, Great Battery, Ring Forge (items) | verdant froglight | green hand light |
| Warden, Dragon and Sentry constructs | glow squid | glow all over |

## Install

1. Turn on **Colored Lighting** in Complementary's shader settings.
2. Open your shaderpacks folder and the Complementary zip inside it (or unzip it to a folder there).
3. Replace `shaders/block.properties`, `shaders/item.properties` and `shaders/entity.properties`
   with the three files from this folder.
4. Pick the pack again in Video Settings > Shader Packs (or press R in the shader menu).

The files are built from Complementary's latest source. If your pack version's own lines differ,
rebuild them from your copy: `python3 tools/complementary_ids.py <unzipped pack>/shaders`.
