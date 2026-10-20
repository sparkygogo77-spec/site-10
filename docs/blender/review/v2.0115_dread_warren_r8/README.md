# Pass v2.0115: Dread Warren round 8 (Trials), the last pass of the Warren look chat

J on v2.0114 W1a7a-c (in chat, 2026-10-20): "all three are good, more scenarios like this, perfect utilization of
existing generations,it will be textured naturally or can you attempt updated themed modern looking shafts even though
naturally generated modern ones would be perfect, the cave would need texturing, prepare to retire soon".

- Script: `docs/blender/blender_updates/v2.0115_dread_warren_r8.update.py` (v2.0114's library plus a textured round-8
  section: `tex_mat` 16-pixel procedural textures, `textured()` runs a v2.0114 builder with them).
- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r8.blend`, cameras `Cam <code> <name>`.
- Review: https://lantern-review-j.vercel.app/#report/v2.0115

| Code | What |
|---|---|
| W1a8a | W1a7c (inside a mine, where it becomes ours) with pixel textures |
| W1a8b | W1a7b (a ravine through a mineshaft) with pixel textures |
| W1a8c | A modern shaft: steel frames, concrete lining, a cable run, lamps all but dead; ours at the end |
| W1a9a | A plain dungeon (cobblestone, spawner, chests) whose far wall has cracked into our tunnel |
| W1a9b | A dripstone cave, ours behind the stalagmites at the foot of the far wall |

Texturing: in the game the mineshaft, dungeon and cave are the game's own blocks, so they take Minecraft's textures
(and J's pack and shaders) by themselves; only our section (dark stone, old timber) needs our blocks. The modern shaft
would need new blocks (steel beam, concrete lining, a dead lamp) or a mod that adds modern mines.
