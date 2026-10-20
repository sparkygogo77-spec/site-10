# New coordinator (one prompt)

Open a new Claude Code session in the desktop app with the folder `C:\Users\Josh\Documents\LanternLive` and paste the
block below (or type `/lantern-new-coordinator` in any LanternLive chat to get a fresh one). The coordinator rewrites
this file from what is true now (`PC-CHAT-BRIEF.md` section 4c) and copies the block to
`LanternLive\NEXT-COORDINATOR-PROMPT.txt`.

```
Start up as my Lantern Ring coordinator 5: pull C:\Users\Josh\Documents\LanternLive\site-10, rename this chat
"Lantern coordinator 5", then follow site-10\docs\handoff\PC-CHAT-BRIEF.md section 1 as the coordinator (sections 4d,
10 and 11 are your job). Never build yourself. Response style from the lantern-coordinator skill: picture link first,
a show_widget progress grid, plain words, then a question only when something new needs me (pathway options that say
what I will see, stills right above any rating question, a "Don't ask, use ★" option). Never repeat the same menu.
First, without asking: (1) one line on whether the /lantern commands and lantern skills loaded; (2) get your own
session id with get_session "self"; (3) read site-10\docs\handoff\NEW-COORDINATOR-PROMPT.md "What the coordinator
inherits", LanternLive\chat-turns.json and site-10\docs\handoff\retired\2026-10-20-coordinator-4.md; (4) SendMessage
each open chat listed there that you are coordinator 5, with your real session id, and they should report to you too;
(5) show me the progress grid, the table and my menu.
Today: start the mc build chat for the Dread Warren mineshaft entrance (brief
site-10\docs\handoff\2026-10-20-warren-mineshaft-entrance\README.md) as soon as I type a message here; rate the
creatures (v2.0112) and the spider lair round 9 when they land; then the charge-light lantern chat (it brings back the
10-minute render watcher).
```

What the coordinator inherits (2026-10-20, from coordinator 4, `local_ff09b134-9e28-43ae-9598-ac2bcc88d743`):

- **Open chats** (their automatic reports go to coordinator 4, so tell each to SendMessage its 🟡/🔵/🔴 reports to you;
  check each with `get_session <id>`, since chats an older coordinator started don't show in the linked list):
  - **Spider lair notes 1-4** `local_43a5a77b-a11c-4624-96fb-242b1507a723`: J's lair notes (legs never through each
    other or the floor, quick dig, strikes that touch, tunnels). Round 8 picked (DECISIONS 5050166b: digs D2 and D3,
    "utilize all 3" strikes, "T1 orb web ★"); round 9 rendered (page https://claude.ai/artifact/C6YUbn59hLWzFWG46mHN9F,
    `trials\spider_anims3.blend` sent), asking J for picks in its window. Flag for the game: R2 needs burrows about 24
    wide, the web tunnels are 9 wide. Round 8 page: https://claude.ai/artifact/FUgD85FBw2CmbaXmSueMxD. Pass 2 of 3-4.
  - **Creatures refine** `local_7c1f35f2-0248-4687-9b0e-d46c13a663e1`: v2.0112, 3+ refined takes each of the grizzly,
    upgraded Yellow Lantern enderman and blue great white (from `trials\titan_killer2.blend`; round 4 page
    https://claude.ai/artifact/3bCtijyZohEWHMqp1WHn9d). Pass 1 DONE: 9 takes (G2a-c, E2a-c, S2a-c), page
    https://claude.ai/artifact/XGpo7dmcEvjnt9yZK6UN2N, `trials\grizzly_enderman_shark.blend`, bb4e085e; asking J for
    ratings in its window.
  - **Dread Warren look 2** `local_baab6020-8458-4a2b-9fca-b925dcd3f5ee`: RETIRED (note
    `docs/handoff/retired/2026-10-20-dread-warren-look-2.md`, FOLDED). Done: v2.0114 and v2.0115 on the site,
    W1a7a-c KEEP saved (449085b8), blends `trials\dread_warren_r7.blend` / `_r8.blend` sent. Archive it on J's yes.
  - **Review site chat** `local_ce7ec561-ff66-4253-b6c1-99889e5c7a19`: PARKED (J: only for necessary site changes;
    doesn't count toward the 3). Last fix: rating saves survive GitHub's rate limit (review-site 32486eb7).
- **J's next slot pick:** "the minecraft entrance" = an mc build chat (game code on `main`, worktree) for
  `docs/handoff/2026-10-20-warren-mineshaft-entrance/README.md`. Start it on J's first typed desktop message.
- **Queue** (3 working sub-chats at most): mineshaft entrance build → ring models round 2 (J: "Queue ring models
  next"; better once he rates v2.0104) → charge-light lantern chat (prompt in `LanternLive\NEXT-CHAT-PROMPT.txt`; owns
  the watcher) → flight 400-499. Next free pass after v2.0115: v2.0116.
- **Waiting on J:** v2.0104 worn rings and v2.0105 fresh lanterns (unrated); unrated leftovers in v2.0109, v2.0111,
  v2.0113 (leave alone); v2.0115 (5 entrance scenarios) once rendered; the light test's CreeperMeyt Lunar try (staged,
  `docs/handoff/retired/2026-10-19-light-test.md`); Lantern Control "yes, install" (`LanternLive\mods\lantern-control`,
  note `2026-10-19-lantern-control.md`); game hand-offs for spiders and lair (J: "Not yet").
- **Parked ideas:** red Grasp hand → nether fortress redesign. Fallen Titan shelved ("forget the titan,").
- **Starting chats:** start_session works only on J's typed desktop message. It is refused after menu answers,
  `/lantern-` commands, other chats' messages and Remote Control (phone) messages, and proposal cards don't show on his
  phone. When J types a request for a chat, start it in that turn, before any menu.
- **Web project:** Site 10 https://claude.ai/code/project/chan_01YLUFj9KADvqrGT75FUzG27.
- All notes in `docs/handoff/retired/` are FOLDED.
