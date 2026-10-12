# Lantern Ring with Complementary shaders

Complementary picks light colour and glow by the ID each block, item and entity has in its
`block.properties`, `item.properties` and `entity.properties`. The mod handles this two ways.

## 1. Any Complementary pack, automatically (`client/ShaderPackIds.java`)

When Iris loads a pack that doesn't list the ring's blocks, the mod files each glowing block under
the vanilla light closest to its corps colour: verdant froglight for green, redstone block for red,
crying obsidian for violet, shroomlight for orange and soul lantern for blue. The green Deluge is
filed as the pack's water. Held lanterns light the hand green, and the army constructs glow like a
glow squid.

## 2. The "+ Lantern Ring" copy of your pack (`client/ShaderPackPatcher.java`)

When the game starts, the mod looks in `.minecraft/shaderpacks` for Complementary packs (zip or
folder) and writes a copy next to each one, for example
`ComplementaryUnbound_r5.8.1 + Lantern Ring.zip`. Pick it in Video Settings > Shader Packs and keep
**Colored Lighting** on. The copy adds:

- each corps' exact light colour (light colour slots 85 to 90),
- glowing lanterns, fonts, the forge and the see-through constructs (block IDs 19000 to 19020),
- green light from the green Deluge, still drawn as the pack's water (block ID 32002),
- green and red held-item light (item IDs 44085 and 44086).

The copy is made on your own computer from your own pack because Complementary's licence
(License.txt in the pack) doesn't allow sharing a changed pack, so it is never uploaded here. Don't
share it. If a new Complementary version moves the code these edits look for, no copy is made
(the game log says why) and option 1 still works.
