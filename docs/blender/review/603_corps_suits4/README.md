# Pass 603: corps suits round 4: C8b in new textures, fixed suit-up, corps-coloured reveal, C5c gauntlets, new C8b designs

J on 827: "C8b Crest knight is good now the skin needs new textures and the suits dont obey the suitup completely, THE
SUIT COMING ON THE BRIGHT LIGHT THAT REVEALS IT SHOULD BE THE CORPS COLOR, not green, change the hue to match, for the
brick C5b suit the hands should be thicker almost like a gauntlet but i want to see new designs, make a few new designs
based on c8b".

- Open in Blender: `LanternLive\suit\corps_suits4.blend`, scene "Corps Suits 4".
  - Press play to watch the suit-up; it's formed by frame 34.
  - The row camera is `Cam row R4`. Each suit has `Cam <key>`, `Cam <key> shoulder` and `Cam <key> back`.
- Builds on pass 827's rig, suit builders and materials (script `blender_updates/603_corps_suits4.update.py`).

## Fixed on every suit
- **Suit-up:** every piece now forms under the rising light. In 827 the C8 materials (plated, carbon, crystal) and
  their glowing seams were there from frame 1, so those suits never "suited up".
- **Reveal light in the corps colour:** the bright band that runs up the body is now the suit's corps colour (violet,
  blue, red, yellow, orange) instead of mint green.
  - It's dimmer per layer (1.5 instead of 12), because the suit's 3–4 see-through layers add their bands together and
    washed out to white.
  - The ring flare at the end of the forming is the corps colour too.

## Takes

| Key | Take | Corps | Texture |
|---|---|---|---|
| C8b | Crest Knight as kept (shape unchanged) | Violet | carbon weave |
| T1 | C8b's shape in a new texture: circuit (dark plate, thin glowing traces that turn at right angles, pads) | Blue | circuit |
| T2 | C8b in hex plate (raised hex cells, the gaps glow) | Red | hex plate |
| T3 | C8b in scale mail (overlapping scales, lit lower rims) | Yellow | scales |
| T4 | C8b in pinstripe alloy (brushed metal, fine glowing lines) | Orange | pinstripe |
| C5c | Ribbed Warden in brick with thick gauntlet hands (cuff with a glowing rim, armoured fist, knuckle ridge) | Orange | brick |
| N1 | Crest Heavy: C8b + three-layer gauntlets, big pauldron caps, thigh plates | Violet | carbon |
| N2 | Crest Spine: C8b + fins down the back, forearm blades, a tall head crest | Blue | circuit |
| N3 | Crest Warlord: C8b + stepped chest chevrons, horns on the faceplate, spiked gauntlets | Red | hex plate |

All the new textures are procedural (built in Blender's shader, no image files), tinted to the corps colour and 92%
opaque, like 827's materials.

Open for J: KEEP / IMPROVE / DROP per take; which texture(s) for C8b; N1–N3.
