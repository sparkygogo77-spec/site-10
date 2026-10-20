FOLDED 2026-10-20 by coordinator 5 (lessons -> lantern-ring-design, gotchas -> lantern-coordinator)

# Retired: mc build chat, Dread Warren mineshaft entrance + lair (PC), 2026-10-20

Started by coordinator 5 (local_13dd87e9-ca17-45a2-88fe-73ead1b32a93) from
`docs/handoff/2026-10-20-warren-mineshaft-entrance/README.md`. Game code only, no Blender passes; pass label used:
"Pass v2.0114 Â· Warren mineshaft entrance" / "Pass v2.0114 Â· Warren lair".

## Range / role

mc build chat (game code on `main`). In the jar: **2.1.1954+26.3** (builds/latest.json note "Merge pull request #365").

| PR | What | Merged |
|---|---|---|
| #364 | Mineshaft entrance: dead ends of vanilla mineshafts near a Warren carry on as ours (2-3 old dark-oak frames, a round tunnel lined in dread stone dropping ~9 blocks, a first cave ~14 x 12 x 7) | b06f3786 |
| #365 | The lair at every Warren site (W1 cave, ~200-250 x 130-160 x 56, floor y -30, lobes, hourglass columns, ~90 big dripstone spikes + small ones, bones), ring tunnel + 5 dens (30 x 24 x 14) + burrows and den links, dread-stone lining, fluid sealing; a narrow tunnel from each entrance's first cave into the lair | f1de92d1 |

Code: `src/main/java/com/sparky/lanternring/warren/` (`WarrenSites`, `WarrenEntrance`, `WarrenTunnel`, `WarrenLair`),
mixins `MineshaftStructureMixin`, `StructurePiecesBuilderAccessor`, `ChunkGeneratorMixin`. Tests `WarrenEntranceTest`,
`WarrenLairTest`. Screenshots `docs/screenshots/warren_entrance/`, `docs/screenshots/warren_lair/`.

Numbers (J on #364: "Easier to find"): a Warren chance of 70% per 512-block region, site 200+ blocks from the
region edge, entrance reach 150 blocks (300 across), 60% of dead ends, max 3 per mine; land >= y 60 at 9 points, no
deep dark.

## J's decisions in this chat (not yet in DECISIONS.md: coordinator, please add)

- 2026-10-20 "Is that all that it adds?" -> "new iterations and lair cave built and textured and designed more within".
- 2026-10-20 lair timing: "Start now (Recommended)" (build the lair from his existing picks; textures/inside updated
  after the new Blender takes).
- 2026-10-20 "Merge both (Recommended)" (#364 then #365).

## Open work

- **New Blender iterations of the lair's inside** (J asked): for a modeller chat; then update `WarrenLair` textures/dÃ©cor.
- **Modern themed shaft (v2.0115 take)**: needs new blocks; ask J before building.
- **Waiting on the spider build**: cave 1 (the run, ~160 x 100 x 30) and the collapse funnel above the lair, the
  hard-light spike tips (a quarter of the big spikes; needs a construct-spike block), webs (danger only, on walls,
  never across a walkway), the spiders, fall fight. See `docs/handoff/2026-10-19-spider-lair/README.md`.
- J has jar 2.1.1954 to walk a new world's mineshaft into the lair; no rating asked yet.

## Files

- `LanternLive\_jdk\` (on J's PC): Temurin JDK 25.0.4 for Gradle (the PC only had Java 8 and JREs), test logs, PR json,
  the sent jar. Keep the JDK for the next build chat; the rest can go to `_to_delete\`.
- Worktree `LanternLive\mc` removed when retiring.

## Lessons for the design skill

- Entrances reuse vanilla generation and add our part on the end, with no tell above: J: "perfect utilization of
  existing generations" (v2.0114 W1a7a-c), then "Easier to find" (#364): common enough to meet in a normal mine.
- A first build of a place should be the whole walk, not a stub: J on the empty first cave: "Is that all that it
  adds?" -> build the lair behind it ("lair cave built and textured and designed more within").

## Gotchas

- **Java on J's PC:** only Java 8 + JREs; unzip Temurin 25 (windows x64 zip from api.adoptium.net) into
  `LanternLive\_jdk` and set `JAVA_HOME` for `./gradlew`. Client game tests run on J's real GPU (no xvfb); the game
  window pops up on his desktop and a run sometimes ends early with a bare "Stopping!" (window closed): rerun.
- **No `gh` on the PC:** REST with curl and the token from `git credential fill`; write JSON bodies to a file (a "Â·"
  in an inline `-d` body gave "Problems parsing JSON").
- **Merge one PR at a time:** each main build force-pushes the `builds` branch, so two merges back to back raced and
  #364's slower run overwrote #365's jar. Re-run the newer run (`POST actions/runs/<id>/rerun`; a 403 right after
  the run ended worked on retry) or wait for each jar before the next merge. "Update the latest release" and the
  "screenshots" job fail on main already; the jar still publishes.
- **26.3 worldgen:** the feature system is rewritten (Feature is a codec interface); carving a big custom cave is
  easiest as a mixin at `ChunkGenerator.applyBiomeDecoration` TAIL, with the shape a pure function of seed + site so
  each chunk carves its own part. Biomes: `BiomeSource.createUncachedResolver(randomState).getNoiseBiome(quart xyz)`.
- **Structure pieces only generate within 8 chunks of the structure's start chunk:** pieces added to a mineshaft
  (mixin at `MineshaftStructure.generatePiecesAndAdjust` RETURN) must stay in reach, or they're cut off.
- **Vanilla corridor frames check the block above the box:** when post-processing a piece by hand in a test, pass a
  chunk box larger than the piece (`inflatedBy(4)`), or the frames vanish.
- **Region-bound sites:** a site only carves inside its own 512 region, so a test site must sit mid-region (256, 256),
  never at 0, 0 (three quarters of the lair went missing).
- **Windows Python** `open(p, 'w')` writes CRLF; pass `newline=''`/`'\n'` when patching files.
