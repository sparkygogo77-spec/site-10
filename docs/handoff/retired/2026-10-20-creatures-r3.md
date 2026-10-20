# Retired: creatures round 3 chat (polar bear / Lantern endermen / sharks), 2026-10-20

## Range / role

PC Blender modeller chat started by Lantern coordinator 5 for creatures round 3 (Trials area), after J picked "New
iterations" on v2.0116. Passes used: **v2.0117** (+ rev 2), **v2.0118**, **v2.0119**, **v2.0121** (v2.0120 is the
spider chat's pass: the numbers collided once; check `ls docs/blender/review/specs` right before taking a number).

## Where things stand

| Pass | What | J's rating |
|---|---|---|
| v2.0117 | 3 versions each of bear (PB7-9), Yellow enderman (YE10-12), Orange enderman (OE4-6), shark (SK8-10) | KEEP OE5, SK8, SK9; DROP OE6; SK10 unrated; IMPROVE the rest |
| v2.0117 rev 2 | his notes: PB8 fuller face, PB9 inward anteater claws, YE12 fist + spell cage, OE4 greedy chest hug | IMPROVE "improve all, the animations are too simple" |
| v2.0118 | 3 new versions each of PB7 (slam/sway/display), YE10 (crack/pool/door), YE11 (shattered/veins/fissures) | IMPROVE (same note) |
| v2.0119 | bear combos that move, 5 s: BC1 charge/rear/double swipe, BC2 stalk/lunge/swipe/back off, BC3 circle/rear/rakes | unrated; J picked "New iterations" |
| v2.0121 | more bear combos: BC4 pounce/pin/bite, BC5 drive-by rake/wheel/roar, BC6 rear/snow-shockwave slam/double bite | WAITING |

## Open work (for the next creatures chat)

- **Rate v2.0121** (`LanternLive\trials\creature_combos2.blend`, cameras `Cam BC4-6`, frames 1-100), and v2.0119 if J
  wants (`trials\creature_combos.blend`, `Cam BC1-3`).
- **Endermen combos next** (J's pick for "too simple": combos + moving attacks + more body motion + new iterations, one
  creature at a time; bear done first). Planned: Yellow: teleport behind you then slam, advance and cast twice (lava in a
  fist with the spell cage, then water jet), blink chain ending in a lantern swing; Orange: hit then flee then greedy
  hug, kneel/bow with a protective snap at you, hunched walk away glancing back. Needs a biped version of `run_gait`
  (phases 0 / 0.5, duty 0.6, stride ~2 blocks for the 7-block enderman).
- SK10 thresher tail slap is unrated; SK8/SK9 sharks and OE5 are KEEP (no hand-off written yet: J hasn't asked).
- Picture page (all rounds, newest first): https://claude.ai/artifact/QQHBRhkJNiFnbTUvWd23S3

## How the scripts are made

The creature scripts are generated, not hand-edited: the first full copy of v2.0116's script (it is duplicated in the
file; only lines up to the first `# === the takes` are used) + exact-match patches (each must match once) + a shared
helpers block + the pass's takes. Generator and parts were in the chat's scratchpad; the committed `.update.py` files
are complete and self-contained, so the next chat can copy one and edit it directly. Useful pieces inside them:
- `BV` / `EV` / `OV` / `SKV`: per-take version settings read by the v2.0116 builders (bear girth, face, claws, claw_in,
  scars, hump, rear style; enderman skin, cracks mode, spell, seam style, fold axis; prayer lantern/hand spots; shark kind,
  scars).
- `build_path` + `run_gait` (v2.0119/0121): a gait driven by distance travelled, so planted feet keep their world spot
  while the body moves, turns or backs up; moves cover whole strides so every foot is down when the creature stops.
- `bear_combo`: rear-ups, swipes (paw lifts first), bites, leaps with tucked legs, snow shockwave, multi-hit knockback.

## Files

- `LanternLive\trials\creatures_r3.blend` (v2.0117 rev 2), `creatures_r4.blend` (v2.0118), `creature_combos.blend`
  (v2.0119), `creature_combos2.blend` (v2.0121). `creatures_r2.blend` (v2.0116) is superseded but keep until J rates.
- `LanternLive\_previews\takegrid\v2.0117..v2.0121*`: take grids and star files (can go after rating).

## Lessons for the design skill

- **"the animations are too simple" means chain and travel** (v2.0117 rev 2 / v2.0118, J picked every option):
  combos of 3-4 moves over ~5 s, attacks that move (charge, lunge, pounce, drive-by), head tracking the player, weight
  shifts and thuds. Single moves standing in place are no longer enough for creatures.
- **Polar bear face: "doesnt need to be as skinny"** (v2.0117 PB8): head, muzzle and jaw ~25-30% wider than v2.0116.
- **Bear claws: "arms turned inward ... big sharp sloth like claws/anteater"** (v2.0117 PB9): front claws curve in
  toward the body, thick and long (~1.4 blocks).
- **Spells are cast, not tossed: "make a fist ... and construct around the element ... like casting spells"** (v2.0117
  YE12): a clenched fist and a hard-light cage round the element it throws.
- **The Orange Lantern hug is greedy: "arms hugging it to the chest greedily"** (v2.0117 OE4), not lifted to the face;
  OE5 (both knees, bowed over the lantern on the ground) is KEEP; the rocking forehead press (OE6) was dropped.
- **Sharks: scarred great white (SK8) and hunting hammerhead (SK9) are KEEP.**
- J rates big passes on the site and small rounds in chat; when he rates on the site, never overwrite with a chat star
  pick (a chat KEEP overwrote his site IMPROVE on PB8 once and had to be put back).

## Gotchas

- **Pass-number collisions between chats:** two chats took v2.0120 within minutes. Run `git pull` and list specs
  immediately before creating the files, and renumber an untracked script if another chat got there first.
- **Long sloth arms clip the floor when posed by euler blends:** lift the paw (~1 block) with IK first, then blend to the
  swipe pose, and set it down last; a rear-up must start after any crouch finishes.
- **Turning while walking stretches planted legs:** keep turns under ~0.3 rad per stride cycle or hind feet can't reach.
- **Hind legs on a lean body:** pitching the body nose-down lifts the hips (2 blocks behind the centre): keep forward
  lean under 0.05 rad on the 5-block bear, and lower the body ~0.1 while moving.
- **Side swipes while running:** the head turns into the raised arm if it tracks the player; damp the head yaw during
  a swipe, and abduct the struck pose outward so the return doesn't cross the other front leg.
- **Raw strings can't end in a backslash** (`r"...\"` swallows the quote): join paths with `chr(92)` or `os.path.join`.
- **Heredocs halve backslashes in Python** (`\\n` becomes a newline mid-string): write generator scripts with the Write
  tool.
