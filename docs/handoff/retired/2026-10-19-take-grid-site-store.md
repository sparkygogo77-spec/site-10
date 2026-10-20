FOLDED 2026-10-20 by coordinator 4 (lessons and gotchas -> lantern-blender-modeller "Review in chat")

# Retired 2026-10-19: in-chat take grid + site state on git (PC side session)

## Range / role
A side session of the PC coordinator. It used no pass numbers (it didn't touch any pass scripts) and built tools only.

## What it shipped
- `tools/pc/take_grid.py`: a review-site-style grid in chat. `grid NNN --stars <json>` writes `_previews/takegrid/NNN.page.html`, which you send with SendUserFile, display "render" (the default). It also writes `NNN.html` for show_widget, but that means retyping about 40 KB of base64, so it's the fallback. `NNN.questions.json` holds the AskUserQuestion calls, 4 takes each: the ★ option first, then the other ratings, then "Don't ask, use ★". `rate` and `flush` save ratings to the site, re-pull RATINGS.md and add a DECISIONS.md line. While the site is down, ratings queue in `pending_ratings.json`. PC-CHAT-BRIEF section 3 step 7 and `Menu: review pass NNN` cover it, and so do the lantern-blender-modeller skill and the lantern-modeller agent (both copies of each).
- Site state is off Vercel Blob, which answered 403 to everything from about 07:00 UTC on 2026-10-19. J: "Move ratings to git", then "Yes, move them". `api/_gitstore.js` reads and writes JSON and binary files on site-10's `site-data` branch through the GitHub contents API, retrying on a sha clash. `api/reviews.js` uses `reviews/reviews.json`, `api/markups.js` uses `markups/markups.json` plus `markups/<id>.jpg`, and `api/render.js` uses `render/status.json`. The response shapes are unchanged. The `@vercel/blob` dependency is gone. This was review-site 4e478114 and 38c44424, with the seed at site-data 60d2c2dc (530 rows from ratings.json).
- Proved on the live site: chat flushes for 609 and 611 (12 takes each), the site's own IMPROVE button, a test markup with its picture and a status change, and a render-banner POST and GET.

## Open work
- None promised. J's 609 IMPROVEs (D1b3a, D1b5a, D1b5b, D1b6a, D1b6b, and D1b6c with J's note "I DONT LIKE THE DRIPS") were sent to the lantern PC chat (pc-lanterns) for its next round.
- Each render take now makes one commit on site-data (`render/status.json`). That's harmless, but if the history gets noisy, have lantern_review.py post every few takes instead of every take.

## Files
- Nothing stray. `_previews/takegrid/` is a cache and can be regenerated.

## Lessons for the design skill
- Ratings happen in chat (J: "I need something like the lantern review site as my responses in blender model chats"): after every pass, show the take grid, then ask the rating questions. Don't send J to the site to rate.
- J overruled most of my ★ picks on 609. He dropped the whole hex line, which I had marked KEEP, and kept nothing. Treat ★ as a starting point, and lean toward IMPROVE when you're unsure.

## Gotchas
- show_widget can't load local files, and the chat has to retype every byte of an inline base64 image. Use SendUserFile with display "render" for picture grids.
- Clicking the site's rating button for the rating a take already has clears it (setRating toggles). To test without changing anything, click twice.
- Another chat wrote ratings into ratings.json by hand while the store was down. pull_reviews.py overwrites that file from the site, so check before committing a pull, and use `take_grid.py rate` / `flush` instead of editing ratings.json.
- When /api/markups fails, pull_reviews.py writes an empty MARKUPS.md. Don't commit that.
- The auto-mode classifier blocks a push to review-site (it's a production deploy) until J says yes in chat.
