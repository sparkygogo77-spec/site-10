# New coordinator (one prompt)

Open a new Claude Code session in the desktop app with the folder `C:\Users\Josh\Documents\LanternLive` and paste the
block below (or type `/lantern-new-coordinator` in any LanternLive chat to get a fresh one). The coordinator rewrites
this file from what is true now (`PC-CHAT-BRIEF.md` section 4c) and copies the block to
`LanternLive\NEXT-COORDINATOR-PROMPT.txt`.

```
Start up as my Lantern Ring coordinator: pull C:\Users\Josh\Documents\LanternLive\site-10, then follow
site-10\docs\handoff\PC-CHAT-BRIEF.md section 1 in full as the coordinator (sections 10 and 11 are your job: the
table of every chat each reply with a Turns column, routing my answers, delegating at once, a Retire option in every
menu, never more than 3 sub-chats, the /lantern- commands). Never build yourself.
First, without asking: (1) tell me in one line whether the /lantern commands and lantern skills loaded; (2) read
site-10\docs\handoff\NEW-COORDINATOR-PROMPT.md "What the coordinator inherits" and LanternLive\chat-turns.json;
(3) start the site chat "Review site: take one pass's report" with the brief in that file; (4) once "Pass 613
lanterns" has retired, start a fresh lantern PC chat (it owns the 10-minute watcher) with the prompt in
C:\Users\Josh\Documents\LanternLive\NEXT-CHAT-PROMPT.txt; (5) show me the table and the menu.
Today: rate v2.0104 rings and the open lantern rounds; the Stormie's Spiders test world waits on me.
```

What the coordinator inherits (2026-10-19, from the second coordinator):
- **Open chats it did not start** (their automatic reports go to the old coordinator, so they also SendMessage every
  🟡/🔵/🔴 report to you; you can read them with `list_events` and message them with SendMessage):
  - **Ring models** `local_32bd0ca5-a768-493c-8205-7dbf4706ff2e`: built v2.0104 (12 worn rings, hero mesh + 1/4 px
    voxel twin), waiting on J's rating. 1 pass; retire after 3-4.
  - **Pass 613 lanterns** `local_4c94be1f-5c7c-493a-a023-b1117c25082c`: built v2.0101-v2.0103 (J dropped all 12
    v2.0103 takes), owned the watcher. Retiring after its open question (J: "Hand over + retire 613"); its close-out
    rewrites `NEXT-CHAT-PROMPT.txt` for the next lantern chat, which you start so it reports to you.
- **Sub-chat limit:** J: "NEVER MORE THAN 3 Subchats at a time ... retire and fold these chats skills in after no
  more than 3 or 4 passes each". Count before every start_session; research/concept chats retire once their doc is in.
- **Turns ledger:** `LanternLive\chat-turns.json`; the table shows Turns and Passes per chat plus a coordinator row.
- **Site chat brief (start it first):** "Site chat for J's Lantern Ring review site (no Blender builds). J
  (2026-10-19): 'adjust the site so i can take the report of a specific pass from the site'. Find how the review site
  is generated (site-10\tools\review_site\, review-site\) and how ratings flow (pull_reviews.py, RATINGS.md,
  ratings.json, the site-data branch). On each pass's page and card add a 'Copy report' button (pass id, title, date,
  .blend path, each take with KEEP/IMPROVE/DROP/unrated and J's note, same shape as the Ring Lab's 'Copy report'),
  a 'Download report' link with the same text, and a per-pass report URL if cheap. Include site ratings not yet pulled
  into the repo. Test on 2-3 passes including a v2.01NN one; one Vercel deploy at the end. Never commit or stash other
  chats' files in the shared checkout. Reply 🔵 DONE with where J clicks; retire when done."
- **Trials:** concept in `docs/plans/trials/2026-10-19-trials-concept.md`. Dread Warren (fear spider cave), any corps
  can enter; next trial = Fallen Titan. Ceiling-walking waits on J watching the Stormie's Spiders test world
  (`LanternLive\test-instances\stormies-spiders`, steps in `docs/research/2026-10-19-mods-physics.md`; J adds the
  launcher installation and logs in himself).
- **Mods:** `docs/research/2026-10-19-mods-physics.md`: J wants to test ★1 LambDynamicLights and ★2 Physics Mod
  (maybe ★3 Sound Physics); the keep-ours/swap survey of our systems (flight, constructs, tether, effects) is there.
- **Numbering:** new passes are v2.01NN (next free after v2.0104); specs need an explicit "area".
- **Account skills:** J saved the 12:43 AM cards; a fresh post (6:42 AM) covers later coordinator lessons. Repo
  skills changed again since (3ac4c834: research chats, trials, 3-chat rule, Turns column): post the skill-update
  prompt once more after asking J.
- All notes in `docs/handoff/retired/` are FOLDED except the ones written after 2026-10-19 15:00.
