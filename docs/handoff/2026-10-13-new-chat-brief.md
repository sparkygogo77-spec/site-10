# Brief for a new Blender chat (from the retired Blender thread, 2026-10-13)

Repo `sparkygogo77-spec/site-10`, branch `claude/lantern-redesign-pass2`.

**Read first:**
- `CLAUDE.md`
- the `lantern-ring-design` skill (J's rules and picks)

**Roles:**
- You make models, textures and animation in Blender.
- Game code goes to the coordinator ("mc" project) as briefs in `docs/handoff/`.
- The lead Blender chat owns the queue and LanternLive passes 200 and up; the battery range was 100-199.

## Where J views things

Everything is in `C:\Users\Josh\Documents\LanternLive`. Open each file with File > Open, choose the camera named
below and press Space to play.

| File | What it shows | Cameras |
|---|---|---|
| `red_battery_final.blend` | the final Red battery, exactly as handed to the game | Cam battery |
| `rage_battery_c.blend` | the battery options and everything around them | Cam C1/C2/C3, Cam port, Cam diamond, Cam shells, Cam blends 1-5 / 5-9, Cam walls, Cam constructs |
| `corps_red_yellow.blend` | the Red and Yellow kits: lantern with flare, ring, construct walls | Cam red, Cam yellow (+ "lantern") |
| `corps_blue_violet_orange.blend` | the Blue, Violet and Orange kits | Cam blue / violet / orange (+ "lantern"), Cam all |
| `texture_round6.blend` | green textures X1-X5 | |
| `texture_round5.blend` | green textures V1-V10 | |
| `lanterns_and_drill.blend` | the Torus, Red, Yellow, Nebula and Blue lanterns, plus drill options D1-D3 | Cam all lanterns, Cam drills, Cam torus |
| `lantern_fixes.blend` | the Red lantern before and after (gold, mark) and the Blue lantern lit on both sides | |

## Choices still open for J

1. **Battery handle:** the game model uses C1 (arched). C2 (ring) or C3 (horns) is a one-command swap:
   `tools/pixel_rage_battery_bbmodel.py OUT c2|c3`.
2. **Particle walls W1-W5** (Cam walls): which to keep. W1 curtain, W2 lattice, W3 swarm, W4 rising, W5 shards.
3. **Orange constructs:** O1 coins, O2 chains or O3 molten gold.
4. **Blue constructs B1-B3:** J said "to test". Confirm the picks after testing in game.
5. **Drill:** D1 auger, D2 tiered or D3 crystal (`lanterns_and_drill.blend`).
6. **Torus, Red, Yellow and Nebula lanterns:** improvement options were asked for and never started. The Blue
   lantern needs "one last look".
7. **Logo:** J may draw his own mark and save it as `LanternLive\logo.png` to have it raised on the battery and
   lanterns. Never copy the official corps logos.

## Handed to the coordinator (check they arrived; two messages may not have)

- `2026-10-13-red-battery-final/`: the battery and cover models, the behaviour spec, and the handle note.
- `2026-10-13-red-battery-diamond-reflect.md`: the battery takes the diamond block's shader ID. **Delivery not
  confirmed.**
- `2026-10-13-barrier-surfaces/`: barrier surfaces T1, T2, T3, T5, T6, T7 and T9. **Delivery not confirmed.**
- `2026-10-13-corps-looks/`: construct textures for each ring colour, plus the Red and Blue lantern fixes.
- `2026-10-13-round6-green/`: X5 (emerald and neon), X3 emerald, X1 emerald.
- `2026-10-13-construct-feedback.md`: opacity, seams, stretching on scaled constructs, and the lantern's
  always-on light.
- `2026-10-13-constructs-and-lantern/`: the G3 R4 charge and the round 4 picks.

**Jar budget:** the jar is close to its 30 MB limit, and these hand-offs add about 14 MB at 32 px. The coordinator
must cut something or ask for 16 px versions.

## Gotchas

- **The LanternLive watcher often stops.** Build the .blend headless (`/opt/bl/venv/bin/python`), copy it into
  LanternLive, and tell J which file to open.
- **The coordinator project URL now opens into a finished thread**, where messages vanish. Confirm a message
  appears on the page, or give J a line to paste.
- **Give glow cubes inflate 0.02 px**, so they don't z-fight with their solid twin.
