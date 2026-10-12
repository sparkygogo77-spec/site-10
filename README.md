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
| **Lasso** | 1, then 1 a second (0.1% each) | Hold right-click (reach 64 blocks) to catch a mob in a glowing cracked-jade bubble on a smooth tube of light, which hums higher the further out it goes. A far catch is reeled in (space stops or restarts the reel). Swing your view to swing it; let go and the bubble is flung hard and flies on with its momentum until it hits something and pops. Hold left-click to push it further out, faster the longer you hold, as far as you can see the mob; it stays where you leave it. You can walk, sprint and fly at full speed while holding a catch; while flying, space rises instead of toggling the reel. A fast bubble bowls over mobs it hits, and a hard slam into the ground or a wall blasts everything nearby back. Double-click and hold to gather every mob within 3 blocks of the spot you aim at into one big bubble. Or hold left-click first and sweep the crosshair over mobs to pick them (each glows, 0.5% each, up to 24); the next right-click pulls them all into one tightly packed bubble that costs nothing to hold. Nothing can hurt the mob in the bubble except those slams |
| **Anvil** | 120 | Hold right-click and a glowing anvil-shaped marker slides along the ground under your cursor (left-click while aiming changes the level: anvil, drill bit or anchor). Let go and a giant hard-light anvil (3x3 base, 5 tall) builds itself about 10 blocks up, glowing bright, cools to clear jade as it drops, and smashes a round crater about 13 blocks wide, flinging some blocks out. It rests in the crater, then fades |
| **Black Hole** | 50 / 100 / 200 | Hold right-click and a small whirl of light marks the spot, floating just off whatever you point at (left-click while aiming picks the size: small, large or supermassive). Let go and a black hole opens there: a black core with a spinning green accretion disk and a ring of bent light round it. For 6 seconds it pulls in mobs, dropped items, arrows and loose blocks (sand, gravel, dirt, snow, leaves, plants near it, up to a limit), spinning them in and crushing whatever reaches the core. Then it collapses with a flash that throws what is left outward and drops every item it caught in a pile underneath |
| **Portal** | 40 (80 to another dimension); setting the exit is free | A Rick and Morty portal gun. Hold right-click to set the exit where you look (it stands on the floor, or flat against a wall). Tap to open a swirling green portal where you look, linked to the exit; both stay open for 15 seconds (Ring Lab > Durations). Walk, fly or throw things into one and they come out of the other with their speed, even in another dimension |
| **Loot Golem** | 100 | Summons a hard-light copper golem that floats beside you and picks up item drops within 14 blocks. When its sack is full (27 stacks) it opens a portal and carries the loot into the chest by your Portal exit (set the exit next to a chest), then comes back. After 2 minutes, or when you use the mode again, it makes a last trip and goes. Without a chest by the exit it hands the loot back at your feet |
| **Army** | 150-250 (or the last of it) | Hold right-click and a ring of light marks where a hard-light ally will form; left-click while holding picks **Warden** (walks with you, smashes and sonic-booms mobs), **Dragon** (an ender dragon a third the size that circles above you and breathes green bolts) or **Sentry** (a spiked eye that loops around the spot you leave it and knocks mobs flying with a beam). Let go to summon it. Allies only attack hostile mobs, never players, pets, villagers or animals, and break no blocks. Each lives on the charge it took: 2 minutes for a full share, less if it took the last of your charge, and hits burn some off. Crouch as you let go to give it all your charge for a long-lived guard. Up to 4 at a time |

The ring is worn on your hand: in third person you see it on your character's fingers, and in
first person your fist is held knuckles-down with the ring's gold top facing you.

## Red Lantern ring

The first of the other Lantern Corps (more are planned). The **Red Power Ring** works like the green
one (same controls, flight, charge) with red constructs and effects. It cycles through Blast, Beam,
Wall, Dome, Shockwave, Shield and its own **Lava Deluge**: aimed and dropped like the Deluge, but the
globe holds red burning liquid. It bursts in a ring of fire, floods out and sets everything it touches
alight, melts the ground under it a layer every 2.25 s, twice, so it sinks in as it drains and leaves a pit floored mostly with magma.
Its **Flame Ring** sends a ring of burning red liquid and fire 14 blocks out from you: every mob it reaches
is held in a pool of the liquid and melts down into it, burning, before it's gone.
It charges only at a **Red Lantern** (and the green ring only at a green one).

## Violet Lantern ring

The Star Sapphire ring of love, in purple. It cycles through **Mind Link**, Wall, Dome, Lasso and Shield,
and charges only at a **Violet Lantern**. **Mind Link** ties every mob within 16 blocks to you with a
violet thread: each one gets amethyst-trimmed iron armour and a sword (archers keep their bow), stops
seeing you or the others as a target, and fights for you. Aim at a creature as you link to send them
all after it; otherwise they go for whatever hurts you or whatever you hit, and follow you between
fights. A link lasts 60 s (Ring Lab Durations) and costs 2% of the ring per mob; when it ends the mob
gets its own gear back.

## Orange Lantern ring

Larfleeze's ring of avarice. It isn't handed out: you craft it (and its **Orange Lantern**) from rare
treasure. It cycles through Blast, Beam, Shield, Lasso and Army in orange, plus three greedy powers:
- **Hoard** pulls every item and XP orb within 20 blocks to you; each stack hauled in feeds 0.5% back into the ring.
- **Steal** snatches what the mob you look at holds or wears, weapon first. A mob with nothing on is robbed of
  the loot it would drop (once per mob).
- **Avarice** calls up orange-outlined copies of the last 3 kinds of mob you killed while wearing the ring.
  They fight for you, never hurt you or your pets, drop nothing, and fade after a minute.
## Blue Lantern ring

The ring of hope. The **Blue Power Ring** has blue Wall, Dome, Bridge, Lasso, Shield and Build, plus:
- **Renew:** a wave of blue light heals you and every friendly creature within 12 blocks and regrows
  the land: grass on bare dirt, flowers, ripe crops, grown saplings, living coral.
- **Restore:** brings back the last villager or tamed pet that died near you (or your own pet, wherever
  it died in this world since the game was opened).
- **Villager Spark:** two blue builder villagers appear where you aim and build a house with a bed and a
  workstation (the first gets a bell). While they're still blue, the village grows another house with
  another builder every 2 minutes. They fade to normal colours over 15 minutes and stop building then.
- **Hope Golem:** a blue iron golem with 300 health and 30 attack that guards the area for 5 minutes.

The times are in the Ring Lab's Durations menu. It charges only at a **Blue Lantern**.

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
- **Charge in hand:** **hold left-click and right-click together** for half a second. The lantern
  rises, your ring hand pushes into its lens and the ring is full 1.5 seconds later while the
  lantern blazes. While left-click is down, right-click never fires the ring's power, and pressing
  left-click while a power is held lets it go and starts charging instead (in Anvil mode a quick
  left-click picks the size; hold it for the charge). With the ring and lantern, left-click doesn't
  hit or mine blocks.
- **Set it down:** **crouch and hold right-click on a block** for half a second (a quick crouched
  click still changes mode), or **double-click right-click on a block and hold** the second click
  for half a second. A single click never places it, and the double-click doesn't place in Lasso mode (it
  gathers a group) or Anvil mode (holding aims); crouch and hold works in every mode. Then right-click the placed lantern with the ring.

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
- **Red Power Ring:** redstone block on top, gold ingot / blaze powder / gold ingot across the middle, gold ingot at the bottom
- **Red Lantern:** iron, redstone block, iron / redstone block, lantern, redstone block / iron, magma block, iron
- **Violet Power Ring:** amethyst shard on top, gold ingot / echo shard / gold ingot across the middle, gold ingot at the bottom
- **Violet Lantern:** iron, amethyst block, iron / amethyst block, lantern, amethyst block / iron, pink petals, iron
- **Orange Power Ring:** totem of undying on top, gold block / diamond block / gold block across the middle, gold block at the bottom
- **Orange Lantern:** gold block, emerald block, gold block / emerald block, lantern, emerald block / gold block, heart of the sea, gold block
- **Blue Power Ring:** lapis block on top, gold ingot / golden apple / gold ingot across the middle, gold ingot at the bottom
- **Blue Lantern:** iron, lapis block, iron / lapis block, lantern, lapis block / iron, sea lantern, iron

## Development

Java 25, `./gradlew build`. `CLAUDE.md` has build notes, the code layout, and how to run the
screenshot tests in a headless container. Texture generator scripts are in `tools/`, and reference
screenshots in `docs/screenshots/`.
