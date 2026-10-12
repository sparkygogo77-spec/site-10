# Lantern Ring

A Fabric mod for Minecraft **26.3** inspired by the classic green power ring. Charge the ring at a
Power Battery, then fly, tunnel through mountains, and build constructs out of hard light.

## Install

1. Install [Fabric Loader](https://fabricmc.net/use/) for 26.3 and drop
   [Fabric API](https://modrinth.com/mod/fabric-api) into your `mods` folder.
2. Build the mod with `./gradlew build` (Java 25) and copy `build/libs/lantern-ring-2.1.0-dev+26.3.jar` into `mods`.
   Or grab a ready-made jar from the [latest release](https://github.com/sparkygogo77-spec/site-10/releases/tag/latest).
   Each CI build is versioned `2.1.<build number>+26.3`; the ring's tooltip and the Ring Lab show which one is loaded.

Version 1.0.0 (Minecraft 1.21.1) is in this repo's git history.

## The ring

| Control | What it does |
| --- | --- |
| Right-click | Use the current mode |
| Sneak + right-click | Switch to the next mode |
| **V** (rebindable) | Toggle flight on or off |

| Mode | Cost | What it does |
| --- | --- | --- |
| **Blast** | 100 | Bores a 3×3 tunnel 50 blocks long, starting right in front of you, in whatever direction you look. About 30% of the broken blocks throw crumbs of their own texture. Mobs in the tunnel take 10 damage. Bedrock and blocks with contents (chests, furnaces) are left alone. |
| **Beam** | 15 | Energy bolt: 8 damage and knockback, 48 block range |
| **Wall** | 50 | A flat, upright 9×9 wall of green construct bricks held together by glowing mortar, 3 blocks in front of you, standing on the ground and square to the way you face. Stays for 30 seconds (editable under Durations). |
| **Dome** | 40, then drains while held | **Hold right-click:** a curved shell of see-through hard light with a glowing hexagon lattice (about 30% of a sphere) facing wherever you look, so you can see out of it. You can run and sprint while holding it. Crouch and it pushes further out and its edge spreads wider, almost to a half sphere. It breaks everything it touches except bedrock, so you can push straight through terrain. It never digs below your feet; look down and it becomes a bowl you can stand in, even over lava. No fall damage while held. |
| **Bridge** | 60 | 3-wide, 13-long hard-light bridge at your feet, heading where you face (10 s) |
| **Shockwave** | 35 | A clear green dome of light bursts out from you to 7 blocks; every mob its wall reaches is hurled away and grass, ferns and flowers are flattened |
| **Lasso** | 1, then 1 a second (0.1% each) | Hold right-click (reach 64 blocks) to catch a mob in a glowing cracked-jade bubble on a twisted rope of light, which hums higher the further out it goes. A far catch is reeled in (space stops or restarts the reel). Swing your view to swing it; let go and the bubble is flung hard and flies on with its momentum until it hits something and pops. Hold left-click to push it further out, faster the longer you hold, as far as you can see the mob; it stays where you leave it. You can walk, sprint and fly at full speed while holding a catch; while flying, space rises instead of toggling the reel. A fast bubble bowls over mobs it hits, and a hard slam into the ground or a wall blasts everything nearby back. Double-click and hold to gather every mob within 3 blocks of the spot you aim at into one big bubble. Nothing can hurt the mob in the bubble except those slams |
| **Anvil** | 120 | Hold right-click and a glowing anvil-shaped marker slides along the ground under your cursor. Let go and a giant hard-light anvil (3x3 base, 5 tall) builds itself about 10 blocks up, glowing bright, cools to clear jade as it drops, and smashes a round crater about 13 blocks wide, flinging some blocks out. It rests in the crater, then fades |

The ring is worn on your hand: in third person you see it on your character's fingers, and in
first person your fist is held knuckles-down with the ring's gold top facing you.

## Ring Lab (press **K**)

A test menu for trying different versions of the look and telling the builder which to keep:

- **Ring model**: Signet with a silver band, all-gold Signet, Raised gem (the three from the reference sheet), Emblem, and the older Signet, Slim band and Lantern crown drafts
- **First-person hand**: Knuckles in (the fist turned so you see the ring face), Fist down, Knuckles forward, Flat item
- **Ring glow**, **Beam / tether**, **Blast**, **Flight**: several particle styles each
- **Block glow**: Off, constructs only, or nearby blocks weep green light like crying obsidian
- **Particle amount**: Subtle, Normal, Intense

Click a setting to try the next version and the button next to it to rate it Keep / Improve /
Drop. The **Try** buttons play an effect in front of you without breaking anything. **Copy
report** copies your picks and ratings to the clipboard so you can paste them back. Settings are
saved in `config/lanternring-lab.json`.

**Durations...** opens an editor for the mod's timings, in seconds: how long Bridge blocks last,
how long a full ring keeps you flying, and each mode's cooldown (none by default). Type a value or use - and +;
changes apply straight away, changed values show green, and they go into the copied report. They
are saved in `config/lanternring-tuning.json`, which a server reads for its own values.

## Texture drafts

Construct blocks ship at 32×32. Two more drafts are built in: turn on **Lantern Ring: 16px
constructs** or **Lantern Ring: 64px constructs** under Options → Resource Packs.

**Flight:** with flight toggled on and charge left, double-tap jump to fly. It drains 1 charge every
half second (about 8 minutes on a full ring), and a charged ring also stops fall damage. When the
ring runs dry you drop out of the sky, so watch the charge bar.

**Charge:** 1000 when full, shown as the green bar under the item. Right-click a **Power Battery**
with the ring to refill it, or carry the battery as a lantern. The lantern only goes in your
**off hand** (pick it in the hotbar and it moves there by itself), and with it there the ring
works exactly as without it: every mode, held ones like Lasso, Wall and Dome included.
- **Charge in hand:** crouch and **hold right-click** for 0.75 seconds. The lantern rises, your
  ring hand pushes into its lens and the ring is full 1.5 seconds later while the lantern blazes.
  A quick crouch-tap still changes mode.
- **Set it down:** **double-click right-click on a block and hold** the second click for half a
  second. A single click never places it. Then right-click the placed lantern with the ring.

In first person the lantern hangs from your fist and swings as you walk and turn. All of these
times are in the Ring Lab's Durations page.

## Models (Blockbench)

The lantern in your hand and the rings (`ring_crest`, `ring_crest_gold`, `ring_beacon`, `power_ring`) are Blockbench models in
`src/main/resources/assets/lanternring/bbmodel/`. Open one in [Blockbench](https://www.blockbench.net/)
(File > Open Model), edit it, save it over the old file and rebuild. Cubes whose name starts with
`glow` light up. `tools/blockbench_models.py` generated the first versions.

## Recipes

- **Power Ring:** emerald block on top, gold ingot / eye of ender / gold ingot across the middle, gold ingot at the bottom
- **Power Battery:** iron, emerald, iron / emerald, lantern, emerald / iron, glowstone, iron

## Development

Java 25, `./gradlew build`. `CLAUDE.md` has build notes, the code layout, and how to run the
screenshot tests in a headless container. Texture generator scripts are in `tools/`, and reference
screenshots in `docs/screenshots/`.
