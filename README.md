# Lantern Ring

A Fabric mod for Minecraft **26.3** inspired by the classic green power ring. Charge the ring at a
Power Battery, then fly, tunnel through mountains, and build constructs out of hard light.

## Install

1. Install [Fabric Loader](https://fabricmc.net/use/) for 26.3 and drop
   [Fabric API](https://modrinth.com/mod/fabric-api) into your `mods` folder.
2. Build the mod with `./gradlew build` (Java 25) and copy `build/libs/lantern-ring-2.0.0+26.3.jar` into `mods`.
   Or grab a ready-made jar from `modpack/`.

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
| **Wall** | 20, then drains while held | **Hold right-click:** a 7×7 hard-light shield 3 blocks out, facing wherever you look. Dark see-through jade, glowing brightest around its outline. Gone the moment you let go. |
| **Dome** | 40, then drains while held | **Hold right-click:** a curved shell of glowing green bricks (about 30% of a sphere) facing wherever you look. It breaks everything it touches except bedrock, so you can push straight through terrain. It never digs below your feet; look down and it becomes a bowl you can stand in, even over lava. No fall damage while held. |
| **Bridge** | 60 | 3-wide, 13-long hard-light bridge at your feet, heading where you face (10 s) |
| **Shockwave** | 35 | Hurls every mob within 7 blocks away from you |
| **Tether** | 20 | Pulls a mob to you, or, aimed at a block, yanks you to it |

The ring is worn on your hand: in third person you see it on your character's fingers, and in
first person your fist is held knuckles-down with the ring's gold top facing you.

## Ring Lab (press **K**)

A test menu for trying different versions of the look and telling the builder which to keep:

- **Ring model**: Signet, Slim band, Lantern crown
- **First-person hand**: Fist down, Knuckles forward, Flat item
- **Ring glow**, **Beam / tether**, **Blast**, **Flight**: several particle styles each
- **Block glow**: Off, constructs only, or nearby blocks weep green light like crying obsidian
- **Particle amount**: Subtle, Normal, Intense

Click a setting to try the next version and the button next to it to rate it Keep / Improve /
Drop. The **Try** buttons play an effect in front of you without breaking anything. **Copy
report** copies your picks and ratings to the clipboard so you can paste them back. Settings are
saved in `config/lanternring-lab.json`.

## Texture drafts

Construct blocks ship at 32×32. Two more drafts are built in: turn on **Lantern Ring: 16px
constructs** or **Lantern Ring: 64px constructs** under Options → Resource Packs.

**Flight:** with flight toggled on and charge left, double-tap jump to fly. It drains 1 charge every
half second (about 8 minutes on a full ring), and a charged ring also stops fall damage. When the
ring runs dry you drop out of the sky, so watch the charge bar.

**Charge:** 1000 when full, shown as the green bar under the item. Right-click a **Power Battery**
with the ring to refill it.

## Recipes

- **Power Ring:** emerald block on top, gold ingot / eye of ender / gold ingot across the middle, gold ingot at the bottom
- **Power Battery:** iron, emerald, iron / emerald, lantern, emerald / iron, glowstone, iron
