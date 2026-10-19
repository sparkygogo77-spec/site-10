# New coordinator (one prompt)

Open a new Claude Code session in the desktop app with the folder `C:\Users\Josh\Documents\LanternLive` and paste the
block below (or type `/lantern-new-coordinator` in any LanternLive chat to get a fresh one). The coordinator rewrites
this file from what is true now (`PC-CHAT-BRIEF.md` section 4c) and copies the block to
`LanternLive\NEXT-COORDINATOR-PROMPT.txt`.

```
Start up as my Lantern Ring coordinator: pull C:\Users\Josh\Documents\LanternLive\site-10, then follow
site-10\docs\handoff\PC-CHAT-BRIEF.md section 1 in full as the coordinator (sections 10 and 11 are your job: the
table of every chat each reply, routing my answers, the /lantern- commands). You own the watcher, the grid and the
menu, start a side chat per area when I ask, and retire them with /lantern-retire-chats.
First: (1) type-check that /lantern commands and the lantern skills loaded and tell me in one line; (2) post in my Site
10 project's main box (ask me first) "Update the account skills lantern-ring-design and lantern-coordinator from
docs/skills/ on claude/lantern-redesign-pass2 and propose the cards" so I can save them; (3) show me the table and menu.
Today: rate pass 612 (reliquary round, 12 takes) in chat; keep the lantern PC chat going on lanterns 600-699.
```

What the coordinator inherits (2026-10-19, from the first coordinator):
- **Open chats:** the lantern PC chat (local_f8850f43-1d91-40e2-b0f9-cd4535d62dd4, passes 600-699, owns the 10-minute
  watcher; restart it with `/lantern-start` later so it gets the new commands). The in-chat review grid chat
  (local_319551d4-cae9-4acd-8c7c-77d7dee3139f) is closing out. The Control page chat is closed out; J archives it from
  the sidebar (keep-awake blocks archiving).
- **Lanterns:** 606 -> 607 (kept D1b molten vault) -> 608 (J circled D1b2/3/5/6) -> 609 (rated in chat) -> 610 (original
  designs; picked N2g, N2r, N1o, N3b, N5y) -> 611 (relics; picked Q1, Q4, Q6, S4) -> 612 reliquary round, WAITING.
- **Ring glow:** 864 -> 865, waiting on ratings; the primed Shift glow (handover Q24) waits on the pick.
- **Site:** Control tab, Decisions, Jar view, pass `v# · age`; ratings, markups, render banner and saves all on the
  `site-data` branch of private site-10 via GITHUB_TOKEN (no Vercel Blob, no deploy per save). Renders skip deploys too.
- **In chat:** take grid + rating clicks (`tools/pc/take_grid.py`, `/lantern-rate NNN`), chat grid
  (`tools/chat_grid.py`), skills and agents in `LanternLive\.claude\` (lantern-modeller, lantern-checker, lantern-router).
- **Account skills** (claude.ai) for lantern-ring-design and lantern-coordinator are behind `docs/skills/`; J saves
  the cards the project coordinator proposes.
- All retirement notes in `docs/handoff/retired/` are FOLDED (2026-10-19).
