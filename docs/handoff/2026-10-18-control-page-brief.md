# Brief: a Control page on the review site (one place J clicks to run everything)

From the first PC chat, 2026-10-18. J, looking at the PC chat menu: "this menu is insufficient ... buttons dont lead
anywhere just from looking at it i can tell ima have to read everything before i know where to go, maybe update the
site of the website". He wants to click and have things happen, with pictures, not to read.

## What exists
- `tools/pc/menu.html` (standalone page, `.\lr menu` opens it): grouped buttons with one plain line each; Claude
  commands are copied to the clipboard for pasting into the PC chat; green buttons act at once (`lanternrender://`
  starts a render on J's PC, links open the site, catalogue and Site 10 project).
- Inline chat widgets can't send messages in the Claude Code tab, so a page can't drive the chat directly. What a
  page **can** do: start the PC render via the `lanternrender:` protocol ("Set up Render button.cmd" registers it), show
  live render progress (`/api/render`), show ratings and passes (`data/site.json`, `/api/reviews`), and copy prompts.

## Build (on the `review-site` branch: `index.html` style, one push = one Vercel deploy, batch it)
A **Control** tab next to "In the game" on https://lantern-review-j.vercel.app, phone-first:
1. **Now:** live render banner (from `/api/render`), last upload, a big "Render everything missing" button
   (`lanternrender://go`, desktop only, hidden on phones).
2. **Waiting on you:** WAITING passes as picture cards (first take's still from `media/<pass>/`), ★ the one that
   unblocks most; tap = that pass's review page.
3. **Pick what's next:** a picture grid of jar models (catalogue `.glb` thumbnails; add the 79 missing with
   `tools/catalogue/jar_to_glb.py`), recent `.blend` passes and textures, each with "Build from this" which copies a
   ready prompt ("Menu: build next J:dark_lantern, 3 takes: <note>") with a note box.
4. **Chats:** "Copy start-up prompt" (the block from `docs/handoff/DESKTOP-KICKOFF.md`, Today filled from the pick),
   "Copy close-out" ("Menu: close out"), "Copy thread prompt" (`NEW-CHAT-PROMPT.md`).
Copy buttons show "Copied: paste into your PC chat (Ctrl+V, Enter)".

Rules: site style and size limits in `tools/review_site/README.md`; never push media from the cloud; test on a phone
width; update `tools/pc/menu.html` to link to the Control tab when it ships; tell J what to tap first.
