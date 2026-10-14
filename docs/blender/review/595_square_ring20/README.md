# Pass 595: the square emblem ring, 20 takes — WAITING

**Script:** `docs/blender/blender_updates/595_square_ring20.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\lanterns\square_ring20.blend` (Cam T01 Faithful, press play:
it lights up from frame 20)
**Sheet:** `sheet.png`, T01 lit at frame 70 (check render)

J, with his concept image: "I need extreme effort put into making the ring look good for the square emblem ring head or
face, it will have to light up, the rest of the rings are garbage, give me 20 takes on the ring, no repeats, stay
faithful to this ring".

**Faithful in every take:**
- a pixel-noisy grey metal band, faceted and wide under the face, tapering toward the palm;
- a square face wider than the band, with a gold frame;
- green bars along the top and bottom edges inside thin gold outlines;
- green side columns;
- a centre square of concentric gold frames round a stepped emerald that gets lighter toward the middle.

The rings are built on the game ring's grid: 0.25 model px voxels, a 6 px face. Each one is about 4,500–5,800 voxel faces.

**Light-up:**
- Each ring starts dark.
- From frame 20 the light spreads from the core across the face over 24 frames (and down the band, where it has a channel or veins), swells at frame 52, then breathes, and goes dark again by frame 188.
- The light is saturated green, never white.
- A green point light in each face lights the pedestal.

| Take | Band | Face |
|---|---|---|
| T01 Faithful | octagonal, stone grey | 2 gold rings, 2×2 core, flat; rings glow |
| T02 Stepped pyramid | octagonal, silver | 3 rings, centre steps up; core glows |
| T03 Inset vault | round, steel | frames stand taller, centre sunk; plus core; glowing line in each bar |
| T04 Cells | strong taper, silver | bars and side columns split into gold cells; everything glows |
| T05 Cathedral | cathedral shoulders rising to the face | 3 rings, diamond core, gold bezel rim |
| T06 Split shank | band splits into two prongs under the face, pale silver | gradient bars, notched corners |
| T07 Light channel | gunmetal with a glowing green channel all the way round | gradient side columns; the light runs down the band |
| T08 Studded | octagonal, gunmetal | gold corner studs, plus core, pyramid |
| T09 Notched steps | shoulders in steps, steel | 3 rings, cell bars, notched corners |
| T10 Grand face | cathedral, stone | a bigger 7 px face, 4 rings, pyramid |
| T11 Twin bars | octagonal, pale | narrower bars with a double gold line, 3 rings, diamond core |
| T12 Ribbed shank | ribbed silver | domed centre, gradient side columns |
| T13 Knife edge | a ridge along the band's top, pale | domed, cell side columns, notched corners |
| T14 Gold-trimmed band | silver with gold edges | gold bezel rim, everything glows |
| T15 Pierced gallery | stone, windows cut in the shoulders | inset centre, cell bars |
| T16 Twisted shank | twisted, steel | cell bars, diamond core, studs |
| T17 Deep frame | octagonal, gunmetal | a 2-voxel gold frame, 1 ring, a big 4×4 core |
| T18 Glowing veins | gunmetal with glowing green veins across the band | 3 rings, pyramid, glowing line in each bar |
| T19 Claw bezel | strong taper, silver | gold claws at the corners gripping a bezel rim |
| T20 Radiant | round, pale | faceted gem rising in steps, gold spokes from core to corners |

All 20 rings stand in one line, in four groups of five, and each turns slowly on its pedestal.

Cameras:
- `Cam T## <name>`: three-quarter view from above, like J's image.
- `Cam T## <name> face`: straight down on the face.
- `Cam row 1` to `Cam row 4`, and `Cam all`.

Rings are the lanterns area (Chat D); this was built as 595 because J asked in this chat.
