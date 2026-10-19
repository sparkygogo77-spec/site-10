# Retired 2026-10-19: mods / physics research (side session of the coordinator)

## Range / role
A research-only side session. It used no pass numbers and made no Blender or code changes. The work is
`docs/research/2026-10-19-mods-physics.md` (commit 457a5177): ★ top 5 are LambDynamicLights, Physics Mod,
Sound Physics Remastered, Stormie's Spiders and Mutant Monsters, followed by a conflict list.

## Open work
- Nothing has been installed or downloaded. If J wants to try a pick, ask (🟡 QUESTION) before fetching any jar.
- Possible future code tasks are listed in the doc's "Integration opportunities" section. The one worth
  doing first is the LambDynamicLights JSON in `assets/lanternring/dynamiclights/`. None of them has been started.

## Files
- Nothing stray.

## Lessons for the design skill
- None from J this chat (he gave no feedback on the picks).

## Gotchas
- Web search can't tell you what's on MC 26.3, because that's past most sources. Ask the Modrinth API instead:
  `https://api.modrinth.com/v2/project/<slug>/version?loaders=["fabric"]&game_versions=["26.3"]`. An empty list
  means there's no 26.3 build. Search with `/v2/search?facets=[["categories:fabric"],["versions:26.3"]]`.
  Send a User-Agent header.
- Running `python -I` on Windows prints in cp1252 and crashes on the emoji in mod descriptions. Call
  `sys.stdout.reconfigure(encoding="utf-8")` in the script. `-I` ignores PYTHONIOENCODING, so the env var won't fix it.
- Check the real class hierarchy before you claim a compat effect. `BroodSpider` extends `ConstructAlly`, not
  vanilla `Spider`, so mods that change spider AI don't touch it.
- To judge conflict risk, list our mixin targets first (`*.mixins.json` + `@Inject method=`). The mod only uses
  `@Inject`, so clashes show up as fighting behaviour (arm poses, camera), not crashes.
- `git pull --rebase` refuses to run while other chats have uncommitted files in the shared checkout. Don't stash
  their work: commit only your own file and push. Pull only once the tree is clean.
