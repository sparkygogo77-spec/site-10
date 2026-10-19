# Desktop session kickoff (paste into a new Claude Code session in LanternLive)

Use this whenever you start a fresh desktop chat. It picks up from `STATE.md`, so nothing needs re-explaining.

```
You're the PC renderer for my Lantern Ring mod. Work in C:\Users\Josh\Documents\LanternLive.
1. Make sure a clone of the Blender branch exists at LanternLive\site-10 (if not: git clone -b
   claude/lantern-redesign-pass2 --single-branch https://github.com/sparkygogo77-spec/site-10 site-10), else
   git -C site-10 pull. Also git -C review-site pull (the renderer script lives there and was stale).
2. Read site-10\docs\handoff\STATE.md and follow its rules. Load my skills lantern-coordinator and lantern-ring-design if you have them.
3. Render every WAITING pass: run "Render Lantern Review.cmd" (or the Blender command in STATE.md). If a pass fails,
   read the error, fix the cause if it's in the renderer or a missing file, rerun just that pass, and keep going.
4. Before you finish: add a line to the Render log in STATE.md (date, passes rendered, failures), add a Handoff log line,
   then git pull --rebase and push site-10 to claude/lantern-redesign-pass2.
5. Tell me in 3 lines: what rendered, what failed, what is waiting on me.
Don't build game code or new Blender passes here; project threads do that. Keep replies short.
```

## Switching back to the project

Open Site 10 in the Claude app and say "pick up from STATE.md". Project threads read it first and update it the same way.
