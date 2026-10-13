# Brief for a game thread: Fear Nuke rework, fear frenzy, construct weapons, and a 1911 item

From J, in his words (plus a follow-up: "The nuke should never reach the ground and explode at least a 4x larger crater"): "The nuke also isn't a throw, it should spend its time being constructed in the arm
instead and the ring should be locked into the constructing position which people should see your hand come
up when you use the ring. It should realistically explode and incinerate around it (doesn't damage but it
causes fear in every mob the radius poisons (potion effect) and they go crazy and start killing each other
and the yellow gas gives them yellow construct weapons to do it, villagers with crossbows AKs, I'd even like
a nice 1911 added as a new item".

## The split
- **Blender session (me):** the models.
  - the 1911 pistol item;
  - the yellow construct weapons (an AK-style rifle and a crossbow);
  - the nuke as it is built in the hand.

  They come as bbmodels and item textures on branch claude/lantern-redesign-pass2, posted here.
- **Game thread (you):** everything below. Use stand-ins until the models land.

## 1. Build it in the hand, not a throw (corps/FearNuke)
- **No throw.** Holding use builds the nuke on the ring hand. It grows from the ring over the
  FEAR_NUKE_ORB time, as yellow hard light that assembles plate by plate.
- **Locked pose.** While building, the ring arm is locked raised in a "constructing" pose, in first
  person and in third person, so other players see the hand come up when the ring is used.
  The lantern charge pose code is the model for this (LanternCarry / LanternFirstPerson raise).
- **Release.** Releasing when it's full sends it toward the aim point.
- **Airburst (J, follow-up).** It never reaches the ground: it detonates in the air above the target.

## 2. The explosion
- **Realistic look.** A white-yellow flash, a fireball, a rising mushroom of yellow smoke, a shock ring
  along the ground, and the yellow "incinerate" aura (Burn) sweeping out.
- **Crater (J, follow-up).** It blasts a crater at least 4x larger than today's: 4x the radius the
  Burn/incinerate sweep covers now. It destroys blocks, not creatures.
- **No damage to mobs or players.** J: "doesn't damage". The fear does the killing, through the frenzy below.

## 3. Fear in the radius
- **Fear effect.** Every mob in the radius gets a new "Fear" potion effect (MobEffect, yellow icon) for
  RingTuning seconds. Fear is the poison here: it does no damage itself.
- **Frenzy.** Feared mobs go crazy. Clear their targets and make them attack the nearest other living thing,
  so they kill each other. Players are not forced, but the yellow gas lingers as a darkening yellow fog.
- **Construct weapons.** The yellow gas hands feared mobs yellow construct weapons, which vanish when
  the effect ends:
  - villagers: an AK-style construct rifle (fires hard-light rounds) or a construct crossbow;
  - zombies, skeletons and piglins: construct melee weapons or crossbows.

## 4. A 1911 pistol item
- **The item.** A new item `lanternring:pistol_1911`: hold it, right-click to fire.
  - It is hitscan or a fast bullet entity.
  - It has a 7-round magazine, reloads with R (or a sneak + use), and has a muzzle flash and a sound.
- **Model.** Mine, from Blender. Wire the item and the first- and third-person holds; I'll match the
  model to your hold transforms.

## Notes
- **Jar size.** The jar is at 29.86 MB, right at the limit (see the charge-meter findings). Keep textures
  small or paletted.
- **Durations.** Add RingTuning entries for the build time, the fear time, the weapon lifetime and the
  gas time, so J can tune them in the Ring Lab.
