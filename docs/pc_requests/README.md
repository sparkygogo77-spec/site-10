# Requests for the PC chat

Project threads hand jobs to the PC chat (Claude Code on J's PC, with his graphics card and files) by pushing a file here
to `claude/lantern-redesign-pass2`. The PC chat checks every 10 minutes while it's open.

File: `docs/pc_requests/<YYYY-MM-DD>-<pass>-<slug>.md`

```
route: B            # B = build/look-dev on the PC, C = run live in J's Blender
pass: 864
from: Blender: rings 800-899 (thread link if you have it)
script: docs/blender/blender_updates/864_ring_glow2.update.py   # if one exists
blend: combat/ring_glow2.blend                                 # where J's file should land

What to make or check, in J's words where possible (his note, the pass and take ids, numbers).
What "done" looks like.
```

When it's done, the PC chat moves the file to `done/`, adds what it made (paths, cameras, renders, failures) at the
bottom, pushes, and posts a one-line note in the requesting thread.
