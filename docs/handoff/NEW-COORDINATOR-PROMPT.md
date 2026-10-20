# New coordinator (one prompt)

Open a new Claude Code session in the desktop app with the folder `C:\Users\Josh\Documents\LanternLive` and paste the
block below (or type `/lantern-new-coordinator` in any LanternLive chat to get a fresh one). The coordinator rewrites
this file from what is true now (`PC-CHAT-BRIEF.md` section 4c) and copies the block to
`LanternLive\NEXT-COORDINATOR-PROMPT.txt`.

```
Start up as my Lantern Ring coordinator 4: pull C:\Users\Josh\Documents\LanternLive\site-10, rename this chat
"Lantern coordinator 4", then follow site-10\docs\handoff\PC-CHAT-BRIEF.md section 1 as the coordinator (sections 4d,
10 and 11 are your job). Never build yourself. Response style from the lantern-coordinator skill: picture link first,
a show_widget progress grid, plain words, then a question only when something new needs me (pathway options that say
what I will see, stills right above any rating question, a "Don't ask, use ★" option). Never repeat the same menu.
First, without asking: (1) one line on whether the /lantern commands and lantern skills loaded; (2) read
site-10\docs\handoff\NEW-COORDINATOR-PROMPT.md "What the coordinator inherits", LanternLive\chat-turns.json and
site-10\docs\handoff\retired\2026-10-19-coordinator-3.md; (3) SendMessage each open chat listed there that you are
coordinator 4 and they should report to you too; (4) show me the progress grid, the table and my menu.
Today: rate Dread Warren round 4 (v2.0109) when it lands; the spider lair chat retires and its replacement fixes lair
notes 1-4; then the charge-light lantern chat (it brings back the 10-minute render watcher).
```

What the coordinator inherits (2026-10-19, from coordinator 3, `local_8623a4e6-0851-419e-93bb-41cfe1c043a1`):

- **Open chats coordinator 3 started** (their automatic reports go to coordinator 3, so tell each to SendMessage its
  🟡/🔵/🔴 reports to you as well; read them with `list_events`, message them with SendMessage):
  - **Dread Warren round 4** `local_baab6020-8458-4a2b-9fca-b925dcd3f5ee`: v2.0109 (area Trials), 39 takes rendering on
    J's GPU: the 12 v2.0108 IMPROVEs (no Matron takes) plus disguised entrance, gallery and hatchery with calm/danger
    webs. Big pass: J rates on the site, link `https://lantern-review-j.vercel.app/#report/v2.0109`. Pass 1 of 3-4.
  - **Spider lair** (titled "Fallen Titan: pitch 6 original bosses") `local_bce53d18-8091-4bfe-a41c-77d203912c8f`:
    J rejected the Titan bosses and turned it into the giant spider lair, the Dread Warren's ending (Matron cut).
    Retiring after its last 3 videos (J: "Retire + replace"); its note will be
    `docs/handoff/retired/2026-10-19-spider-lair.md`. Then propose the queued replacement: lair notes 1-4 (legs never
    collide, burrow dive a quick animated dig, the real spider's strike makes contact, a more organized or natural
    tunnel grid). Page: https://claude.ai/artifact/Li4BpncsnWgGpg86XC4EBL. Brief for the game:
    `docs/handoff/2026-10-19-spider-lair/README.md`.
  - **Light test** `local_442ddcc8-56b1-4bbb-bf0c-ae1a8df4370b`: done and staged
    (`test-instances\lambdynamiclights`). LambDynamicLights works with the shader but not in Lunar (Fabric Loader 0.19.3
    vs 0.19.5) and its light is uncoloured. CreeperMeyt Dynamic Lights + our datapack wait for J to try in Lunar.
    Green held-ring light brief for the code chat: `docs/handoff/2026-10-19-ring-held-light-brief.md`. Retire it once
    J reports.
  - **Review site chat** `local_ce7ec561-ff66-4253-b6c1-99889e5c7a19`: PARKED on purpose (J: "Dont use it until we
    need to make necessary changes to the site"); doesn't count toward the 3. Built the per-pass Copy/Download report
    and the Trials area.
- **Queue** (3 working sub-chats at most): lair notes 1-4 → charge-light lantern chat (prompt in
  `LanternLive\NEXT-CHAT-PROMPT.txt`; owns the watcher; next free v2.01NN, v2.0109 is the Warren) → flight 400-499.
- **Waiting on J:** v2.0104 worn rings and v2.0105 fresh lanterns (unrated); Stormie's Spiders test (parked: "Later");
  game hand-offs for the spiders (`docs/handoff/2026-10-19-dread-warren-spiders/`) and the lair (J: "Not yet").
- **Web project:** the **Site 10** project https://claude.ai/code/project/chan_01YLUFj9KADvqrGT75FUzG27 replaces the
  old mc project. A skill-card retry (one skill at a time) was posted there; check J saved the cards. If not, the three
  SKILL.md files were sent to him for Settings → Skills.
- **Starting chats:** start_session is refused after menu answers or other chats' messages; it becomes a card J clicks.
  Start chats in J's typed turns when you can.
- **Archiving:** blocked by "Keep computer awake" on a chat; J archives from the sidebar or turns it off.
- **J's rules added today** (all in the lantern-coordinator skill and PC-CHAT-BRIEF 4d): menus are pathways; links and
  stills right above every visual question; rich replies (visual first); progress grid every reply; Chat controls
  (update / retire / retire + replace with setup questions, `/lantern-chat`); no repeated menus; chats archived
  without a note get one written by the coordinator.
- **Idea J asked about (open):** a site or program that runs this whole workflow while still driving the desktop
  Claude Code chats. Coordinator 3 proposed a "Lantern Control" pane (a Claude Code desktop mod) plus the review site's
  Control page as the phone view; see its retirement note.
- All notes in `docs/handoff/retired/` are FOLDED except the spider lair's (not written yet).
