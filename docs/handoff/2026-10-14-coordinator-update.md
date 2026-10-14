# Coordinator update from the lead Blender chat (2026-10-14)

Branch `claude/lantern-redesign-pass2`. Build items 1 and 2 in your next jars: they are new, and both have J's picks.
Treat KEEP as final, IMPROVE as the next thing to iterate, and DROP as safe to remove in J's Ring Lab reports.

## New, ready to build

1. **Movement and flight**: `docs/handoff/2026-10-14-movement-flight/README.md`
   - Sprint run: S1 + S4 combined, with the stride driven by distance travelled.
   - Takeoff: F2, launching in the direction of movement. The head-pitch fix is included.
   - Ground flight: double-tap space while sprinting to skim. You ride over 1-block steps, and a 2+ high wall hits an
     invisible 3.5-block barrier dome that craters, leaves an imprint on the wall and halts you.
   - Flight trail T4: a light texture tinted by `CorpsTint`, scaled by speed for other players.
   - Sonic boom when entering fast flight (glide speed above 1.1 blocks a tick): a ring sprite, two .ogg sounds and
     first-person and nearby screen shake, with a Ring Lab shake-strength slider.
   - Contents: `poses/` (JSON) and `assets/` (PNG strips and .ogg files).
2. **Lantern charging**: `docs/handoff/2026-10-14-lantern-charge/README.md`
   - L1c lean to charge: the fist goes into the port every tick, and the lantern tips and wobbles.
   - K3c one-knee kneel pick-up with lift-off physics.
   - The charge light runs from the port down the glass to the base; it is brighter, saturated, and lights the world.
   - Contents: `poses/kneel_lean4_poses.json`.

J may split 1 and 2 between two game chats. Each folder is self-contained.

## Ring Lab options (J picks in game)

- Lantern carry height while sprinting: S5a (43°) or S5b (57°).
- Ground flight wall stop: H1 hard stop, H2 cushion or H3 into the block.

## Already sent, still waiting on a jar number

- X3D1 glass aura texture plus the Anvil optimisation: `docs/handoff/2026-10-14-x3d1-glass-aura.md`.
- Omega beams: `docs/handoff/2026-10-14-omega-beams.md`. You replied "On it". The E1–E4 starts go in as Ring Lab options.

## Already in the jar (2.1.641, for reference)

- Sanctuary A6
- Blast drills D1–D3 (brick)
- Deluge W3
- Red battery C1 with the Red Lantern toggle
- The bull's Red look
- Barriers T1–T9

## Not handed over (J hasn't picked)

These are in J's `LanternLive` folder as .blend files; don't build them yet:
- suit round 3
- flight air poses and landings
- lantern charge C1–C3
- hanging charge H1–H3
- combat P, K and R rounds
- leans L1d, L1e and L2c

Please reply with the jar number for each item when it builds.
