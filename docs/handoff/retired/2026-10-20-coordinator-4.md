FOLDED 2026-10-20 (coordinator 4 folded its own lessons as it went: lantern-coordinator skill, memory
start-session-only-on-typed-turn)

# Retired: Lantern coordinator 4 (Claude Code in LanternLive), 2026-10-19/20

**Role:** PC coordinator, session `local_ff09b134-9e28-43ae-9598-ac2bcc88d743`, about 27 turns. Retired on J's words
"coordinator will prepare to update and retire as well".

## What it did

- Took over from coordinator 3; told every open chat to report to it.
- Retired and folded: spider lair (b839db1c), light test (note written by coordinator, 7753d9a8), Lantern Control
  (e56cc4ba, archived), Dread Warren look 2 (d914ac84). Archived the duplicate coordinator fork.
- Started: Spider lair notes 1-4 (local_43a5a77b, rounds 8-9), Creatures refine (local_7c1f35f2, v2.0112).
- Woke the review site chat: ratings were reverting because the site's GitHub token hit its 5000/hour limit; fixed in
  review-site 32486eb7 (taps wait and retry, "Not saved yet", banner with the reset time).
- Routed J's ratings: v2.0109 (31/39), v2.0111 (18/33), v2.0113 W1a5a (entrance steer, one version at a time).
- Wrote the game hand-off `docs/handoff/2026-10-20-warren-mineshaft-entrance/README.md` (J's next slot pick).

## Open work

See `NEW-COORDINATOR-PROMPT.md` "What the coordinator inherits".

## Lessons (J's words)

- "the minecraft entrance": the Warren slot goes to a game build chat for the mineshaft entrance.
- "Review these 3 times (one at a time" -> "3 new versions, one by one": steer designs one take at a time.
- "I want grizzly refined, shark and the other i named as well"; "create a new creature refine i cant find it":
  proposal cards don't show on J's phone, so a card is not a start. Start chats on his typed desktop message.
- "Rated it on the website but the website reverted?": check `/api/reviews` for an error before doubting J.

## Gotchas

- **Know your own session id:** `get_session("self")`. Coordinator 4 guessed an id from its scratchpad path and sent
  it to four chats; their reports went nowhere until corrected.
- **start_session is refused** on turns begun by a menu answer, a `/lantern-` command, another chat's message, or a
  Remote Control (phone) message ("did not come from this app's composer"); only J's typed desktop message starts one.
- **Linked list:** chats an older coordinator started don't show in `list_sessions {"linked": true}`; check them with
  `get_session <id>`.
- **"No preference" answers** = J skipped; never record them as ratings.
