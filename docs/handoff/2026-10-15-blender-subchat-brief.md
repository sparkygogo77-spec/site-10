# Brief for Blender sub chats (desktop modellers)

For **every Blender modelling chat** J starts on the desktop. Paste the starter as the first message. The coordinator
brief (`docs/handoff/2026-10-14-coordinator-brief.md`) has the bigger picture; this one is what a modeller needs.

## Starter (paste into a fresh desktop chat; change the range and area)

```
You're one of my Blender modellers for my Lantern Ring Minecraft mod.
Your passes: <NNN-NNN>. Your area: <area>. Stay in your range.
Setup, in order:
1. Attach GitHub repo sparkygogo77-spec/site-10 with push access; clone branch claude/lantern-redesign-pass2
   (git clone --depth 1 --branch claude/lantern-redesign-pass2 ..., 10-minute timeout).
2. Read docs/handoff/2026-10-15-blender-subchat-brief.md and load the lantern-ring-design skill.
3. Run python3 tools/review_site/pull_reviews.py, then read docs/blender/review/RATINGS.md (my ratings and the
   passes I scrapped), docs/blender/review/DECISIONS.md (what I decided in chats) and the INBOX entries in your range.
4. pip install bpy --break-system-packages. Ask me to approve folder access, then request
   C:\Users\Josh\Documents\LanternLive.
Then tell me in 3 lines what's waiting in your range and ask short multiple-choice questions.
```

**One-line note for chats already running** (paste into each):

```
New rule for every finish: read docs/handoff/2026-10-15-blender-subchat-brief.md on claude/lantern-redesign-pass2 (pull first) and follow its "Every finish" steps: write a review spec to docs/blender/review/specs/<pass>.json, and check RATINGS.md and DECISIONS.md before you start anything; when I decide something in chat, add it to DECISIONS.md.
```

## How chats talk (GitHub only, no deploys)

| Channel | Who writes | Who reads | Costs a Vercel deploy? |
|---|---|---|---|
| `claude/lantern-redesign-pass2`: scripts, review folders, INBOX, **specs**, hand-offs | Blender chats, coordinator, mc chat | everyone; J's PC renderer reads specs and scripts from here | **No** (Vercel skips every branch except `review-site`) |
| The site's ratings API (`/api/reviews`), pulled into `docs/blender/review/RATINGS.md` | J, on his phone | every chat, at the start of a session | **No** (stored data, not a deploy) |
| `review-site` branch | **only J's PC renderer** | Vercel | yes: one per rendered pass |

- **Never push to `review-site`.** Never commit media yourself. Put your spec on the working branch; J's PC renders it.
- The INBOX entry is still the record of what you built. The spec is how it reaches the site.
- Telling the mc chat through the browser is only for KEEP hand-offs (J picked something for the game). Reviews
  don't need a message: J sees them on the site.

## Every finish (in this order)

1. **Build** the pass headless: `docs/blender/blender_updates/<NNN>_<name>.update.py`, 3+ labelled takes, one check
   render (test once).
2. **Deliver** the packed `.blend` to `C:\Users\Josh\Documents\LanternLive\<area>\<name>.blend`
   (`device_commit_files`). Areas: `lanterns`, `movement`, `combat`, `constructs`, `red`, `suit`.
3. **Review folder + INBOX entry**: `docs/blender/review/<NNN>_<name>/README.md`, entry at the top of
   `docs/blender/review/INBOX.md` (status WAITING).
4. **Spec** for the site: `docs/blender/review/specs/<NNN>.json` (format in `tools/review_site/README.md`). Copy
   `specs/803.json` (first-person rig) or `specs/406.json` (player body) as a template. Exact camera names from your
   script. Every player animation gets a 3rd-person camera and a first-person one (`camfp` + `fp_prefix`, or
   `fp_head`).
5. **Commit and push** to `claude/lantern-redesign-pass2` (`git pull --rebase` first; INBOX conflicts: keep both
   entries, newest first).
6. **Tell J** in one short message: the pass and title, the .blend path and camera, and "render with:
   `blender -b --python review-site\tools\lantern_review.py -- <NNN>`" (run from `C:\Users\Josh\Documents\LanternLive`).
   End with what's still waiting on him.

**Changing a take after J rated it IMPROVE:** edit the script, bump `"rev"` on that take in its spec (1 → 2), push.
Only that take re-renders. Never bump takes J rated KEEP or DROP.

## Before you start any round

- **When J decides something in chat** (not on the site), append one line to `docs/blender/review/DECISIONS.md`
  (newest first, his words in quotes) in the same commit as your work.

- `python3 tools/review_site/pull_reviews.py`, then read `RATINGS.md`:
  - **KEEP**: final. Hand it off for the game (`docs/handoff/<date>-<topic>/README.md`); don't redesign it.
  - **IMPROVE**: your next round; the note says what.
  - **DROP**: leave it out.
  - **Scrapped passes**: J is done with them. Don't build on them; set `"superseded_by"` in their spec if you replace them.
- Take the next free number in your own range: `ls docs/blender/blender_updates | sort -n`.

## Design rules (short; the lantern-ring-design skill has the detail)

- 3+ takes, labelled; carry praise forward word for word; change only what he criticised.
- Fast and snappy, never take control from the player (3–6 tick windows), landings under 1 block and 0.3 s.
- The ring arm leads (0.08 s) and points where you move. Slow flight is upright (20° lean); the sprint is a flat glide.
- Saturated green glow, never white; constructs see-through (≤99% opaque), darker, smoother, slower.
- Original marks only (no Green Lantern emblem, corps logos or character names).
- Replies to J: short; full path, camera, frames; spell out abbreviations; end with what's waiting on him.
