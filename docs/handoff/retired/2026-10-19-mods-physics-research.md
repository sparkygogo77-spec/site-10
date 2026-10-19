# Retired 2026-10-19: mods / physics research (side session of the coordinator)

## Range / role
A research-only side session. It used no pass numbers and made no Blender or code changes. The work is all in
`docs/research/2026-10-19-mods-physics.md`:
- **Round 1:** ★ top 5 are LambDynamicLights, Physics Mod, Sound Physics Remastered, Stormie's Spiders and Mutant
  Monsters, followed by a conflict list.
- **Round 2:** replacements for each of our systems. Most verdicts are "keep ours"; the real wins are Player Animation
  Library (poses) and GeckoLib (new animated constructs); watch Sable (constructs as physics objects).
- **Round 3:** Stormie's Spiders' real extent, plus a test instance.

## Open work
- **Waiting on J:** the Stormie's Spiders test. The instance is ready at
  `C:\Users\Josh\Documents\LanternLive\test-instances\stormies-spiders\` (Fabric API, Stormie's Spiders 3.3.1,
  lantern-ring 2.1.1712, room datapack). J has to add the launcher installation himself (click-by-click steps are in
  the doc, section "Stormie's Spiders test instance"), then run tests 1-3 and report back. The datapack hasn't been run yet.
- **Asked, not answered:** whether to set up a second test instance with 1+2(+3) (LambDynamicLights, Physics Mod,
  Sound Physics Remastered). Its test plan is in the doc ("How to test 1, 2 (and 3)").
- Possible code tasks are in the doc's "Integration opportunities" section and round 2 table. The one worth doing first
  is the LambDynamicLights JSON in `assets/lanternring/dynamiclights/`. None of them has been started.

## Files
- `C:\Users\Josh\Documents\LanternLive\test-instances\` (outside the repo): `stormies-spiders\` is the test instance,
  and `_downloads\fabric-installer-1.1.2.jar` can go to `_to_delete\` once the test is done.
- Fabric Loader 0.19.5 for 26.3 was installed into `%APPDATA%\.minecraft\versions\fabric-loader-0.19.5-26.3` (harmless;
  J's real profiles weren't touched).

## Lessons for the design skill
- J wants research that answers "can this **replace or build on** what we made" (his words: "mods that mesh well with
  replacements for stuff in mine like maybe flight mechanics"), not only add-ons. Give a keep-ours/swap verdict for
  each system.
- J wants to **see** a mod's real extent before we build the same feature ourselves (his words: "show me the extent
  of stormies spiders before creating ceiling walking"). Offer a test world first, and code only after that.

## Coordinator rule (J, via the coordinator)
- The coordinator keeps **at most 3 sub-chats** running at once.

## Gotchas
- Web search can't tell you what's on MC 26.3, because that's past most sources. Ask the Modrinth API instead:
  `https://api.modrinth.com/v2/project/<slug>/version?loaders=["fabric"]&game_versions=["26.3"]`. An empty list
  means there's no 26.3 build. Search with `/v2/search?facets=[["categories:fabric"],["versions:26.3"]]`.
  Send a User-Agent header. The project JSON's `gallery` and `body` fields give the media links and the full description.
- Running `python -I` on Windows prints in cp1252 and crashes on the emoji in mod descriptions. Call
  `sys.stdout.reconfigure(encoding="utf-8")` in the script. `-I` ignores PYTHONIOENCODING, so the env var won't fix it.
- Windows paths inside a Python `'''...'''` string in a bash heredoc break with a `\U` unicode escape error. Use the
  Edit tool for markdown with Windows paths.
- Check the real class hierarchy before you claim a compat effect. `BroodSpider` extends `ConstructAlly`, not
  vanilla `Spider`, so Stormie's Spiders (which mixes into `Spider`) doesn't touch it.
- To judge conflict risk, list our mixin targets first (`*.mixins.json` + `@Inject method=`). The mod only uses
  `@Inject`, so clashes show up as fighting behaviour (arm poses, camera), not crashes.
- `git pull --rebase` refuses to run while other chats have uncommitted files in the shared checkout. Don't stash
  their work: commit only your own file and push. Pull only once the tree is clean.
- Editing `%APPDATA%\.minecraft\launcher_profiles.json` to add an installation is blocked by the auto-mode classifier
  ("Unauthorized Persistence"). Write click-by-click launcher steps for J instead. Installing Fabric Loader with
  `java -jar fabric-installer.jar client -dir <.minecraft> -mcversion 26.3 -loader <v> -noprofile` is allowed (the
  Java 8 on PATH is enough).
- Get the 26.3 data pack format from `.minecraft/versions/26.3/26.3.jar` → `version.json` → `pack_version.data_major`
  (121). Fabric meta lists unstable loaders first, so pick the newest `stable: true` one (0.19.5).
- Our own jar for a test instance: `git show origin/builds:lantern-ring-latest.jar`, renamed to the version in
  `origin/builds:latest.json`.
