# Build brief: a catalogue of the jar's models on the review site (start: the dark lantern)

From the coordinator, 2026-10-15. J: "I would like a model catalogue of my jar too, starting with being able to view my
dark lantern in the site on its own through a catalogue, but also in the render it is at now and ... another simulation
of light through my complementary shaders and ray tracing light sources".

## What J gets

A **Catalogue** page on https://lantern-review-j.vercel.app (link it from the site header next to "In the game").
One model at a time, big viewer (same look as the review page: one big view, a strip of models underneath), the jar
version it came from, and three looks he can switch between:

1. **Render** -- like the Blender check renders and the site's current 3D: neutral studio light, dark green-black
   background, bloom on emissive parts, Standard-like tone mapping (greens stay saturated, never washed to white).
2. **Complementary at night** (real time) -- an approximation of his shader pack: night sky (deep blue, moon as a
   directional light with soft shadows), a grass/stone block floor around the model, light fog, the lantern's glow as
   a real light source (green PointLight at the glass, casting shadows on the floor), strong bloom, its idle glow at
   10-15% as in the game. Say on the page that it is an approximation; the final check is in game.
3. **Ray traced** -- progressive path tracing in the browser, where the emissive glass really lights the scene (same
   night scene). Sharpens over a few seconds; a sample counter; pauses while the camera moves. Fall back to look 2 with
   a note when WebGL2 float textures aren't available (phones).

Start with the **dark lantern** (green). Then every jar model, grouped (lanterns, batteries, rings, construct blocks,
tools, mobs), each corps colour as a variant switch.

## Where the models come from (the jar, not Blender)

- Block model: `src/main/resources/assets/lanternring/models/block/dark_lantern.json` (2,118 Minecraft elements,
  texture `lanternring:block/dark_lantern`), corps variants `dark_lantern_<corps>.json`.
- Overlays drawn by the game: `bbmodel/dark_lantern_glow.bbmodel` (textures `textures/entity/bb/dark_lantern_glow_<name>.png`,
  emissive) and `bbmodel/dark_lantern_swirl.bbmodel` (animated frames `dark_lantern_swirl_<frame>.png`), see
  `LanternFirstPerson.java` (lines ~97 and ~583-589) for how they are placed and recoloured per corps.
- Write a converter (Python, in `tools/catalogue/`) from Minecraft block JSON (elements, per-face UVs, element
  rotations, display transforms) and .bbmodel to .glb: nearest-neighbour textures, glow parts as emissive, one node per
  overlay so the page can switch them. Output `catalogue/<id>.glb` + `catalogue/index.json` (id, name, group, corps,
  jar version, which overlays) on the `review-site` branch. Keep each .glb small (merge faces sharing a texture).
- Check the converted lantern against `docs/screenshots/` / the DarkLanternTest game-test shots before shipping.

## Site rules (please keep)

- The site is the `review-site` branch; every push there is a Vercel deployment (free plan, about 100 a day). Build and
  test locally, then push **once**. Never push media or touch `media/`, `specs/`, `data/site.json` (J's PC renders those).
- Libraries only from cdn.jsdelivr.net with exact versions. The review page already uses an import map with
  `three@0.163.0` for model-viewer 3.5.0; the catalogue is its own page (`catalogue.html`), so it can use a newer
  three.js. `three-gpu-pathtracer@0.0.27` needs `three>=0.185.0` and `three-mesh-bvh>=0.9.15` (0.9.16 exists).
- Dark and light mode, phone width (no sideways scroll), same fonts and colours as `index.html`.
- Original marks only: no Green Lantern emblem or corps logos.

## Report back

The page link (`/catalogue.html#dark_lantern`), the jar version the models came from, .glb size, and one screenshot per
look. Name "catalogue" in the commit subject.
