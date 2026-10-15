# Lantern Review loop

J reviews every Blender take on his phone at **https://lantern-review-j.vercel.app**: a looping third-person clip, a
first-person (eye camera) clip, a 3D pose he can spin, and KEEP / IMPROVE / DROP plus a note per take.
The site is the `review-site` branch of this repo, deployed by Vercel (project `lantern-review`) on every push
to that branch. Ratings are stored by the site (`/api/reviews`) and pulled into the repo by the chats.

```
 Blender chat builds a pass ─► docs/blender/review/specs/<key>.json on the working branch (no deploy)
          ▲                                   │
          │                     J's PC renders it (lantern_review.py, GPU, minutes)
          │                                   │  git push review-site ─► Vercel redeploys the site
          │                                   ▼
  chats read RATINGS.md ◄── pull_reviews.py ◄── J rates on his phone (KEEP / IMPROVE / DROP + note)
```

## 1. Blender chats: after every finish (add to the every-finish routine)

1. Build the pass as usual (update script, packed .blend in the area folder, review README, INBOX entry).
2. Write a **review spec** for the pass on the working branch as `docs/blender/review/specs/<key>.json` (key = pass
   number, or pass number + a suffix when one pass has two entries). The PC renderer fetches specs and update scripts
   from that branch. **Never push to `review-site`** (every push there is a Vercel deploy; only J's PC pushes there):

```json
{
 "pass": "407", "key": "407", "added": "2026-10-15T10:00:00Z",
 "title": "Short title J will recognise",
 "desc": "One or two plain sentences: what this round is and what J asked for.",
 "superseded_by": null,
 "kind": "animation",
 "blend": "movement/arm_lead2.blend",
 "script": "docs/blender/blender_updates/407_arm_lead2.update.py",
 "orbit": "155deg 65deg auto",
 "takes": [
  {"code": "U1", "name": "Upright lead", "facts": "numbers J judges by", "tags": ["jar default"], "default": true,
   "cam3p": "Cam U1", "camfp": null, "fp_head": "KL U1", "frames": [1, 130], "player": "KL U1"}
 ]
}
```

   - `kind`: `animation` (clip), `turntable` (clip at every 4th frame), `static` (one still; set `still_frame`).
   - `cam3p`: the exact camera name for the third-person clip. `camfp`: an eye camera the script built, **or**
     `fp_head`: the player prefix, and the renderer adds a Minecraft eye camera (70° view, head and body hidden).
   - `player`: the player object prefix (objects `"<prefix> body"`, `"<prefix> head"`...) for the 3D view.
   - `blend` is relative to `LanternLive\`; if it isn't found, the renderer runs `scripts/<script name>`.
   - When a new round replaces an old one, set the old spec's `superseded_by` (it drops off the site unless it has media).
   - Takes keep their rating id `<key>_<code>`: re-rendering a take keeps J's rating and shows him
     "New render since you rated".
   - **Changed a take?** Add or bump `"rev": 2` (3, 4…) on that take. Only takes whose `rev` went up re-render, and
     never ones J rated KEEP or DROP (`--force` overrides). Don't bump untouched takes.
   - `fp_prefix` (with `camfp`): the prefix of the first-person rig's objects, used for the visibility check below.
   - `model_at` (optional): the frame the 3D view opens on (e.g. the middle of a beam). Default: the last frame, the
     finished look. The 3D model includes everything parented under the player's parts; procedural looks (suits) are
     baked at the last frame. First-person clips render at 120 degrees horizontal field of view.

**What the renderer skips, to keep runs short** (J: "optimize the amount rendered"):
- takes that already have clips (unless their `rev` went up);
- takes J rated KEEP or DROP;
- first-person clips where the arms/ring/tool are in view in under 5% of frames (the site says so instead);
- clips over 100 frames render every 2nd frame (10 a second); EEVEE uses 8 samples.
3. Commit and push the working branch. Then ask J to render (step 2).

## 2. J's PC: render and publish (once set up, one command)

Setup, once (PowerShell):

```
cd C:\Users\Josh\Documents\LanternLive
git clone -b review-site --single-branch https://github.com/sparkygogo77-spec/site-10 review-site
```

Render and publish:

```
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python review-site\tools\lantern_review.py -- 407
```

(`-- --all` renders every spec that has no clips yet; `--force` re-renders; `--no-push` renders without pushing.
It pushes ONCE at the end of a run (one Vercel deploy); `--push-each` pushes after every pass instead.)
It pulls the branch, renders with EEVEE on the graphics card (about 0.05–0.1 s a frame, so a pass takes minutes),
writes `media/<key>/`, rebuilds `data/site.json`, commits and pushes. Vercel redeploys in about a minute.
A desktop Blender chat can run that command itself when it has a shell on the PC.

Fallback (no PC): a cloud chat can render with Cycles on CPU (about 1.5 s a frame, hours for a big pass). Use the same
spec; render frames, encode with ffmpeg, put the files in `media/<key>/` and run `tools/gen_site.py`.

## 3. Every chat: read J's ratings at the start of a session

```
python3 tools/review_site/pull_reviews.py
```

writes `docs/blender/review/RATINGS.md` (a table per pass: rating, note, when, and whether the take was re-rendered
since) and `ratings.json`. Commit them with your work. KEEP is final, IMPROVE is the next thing to work on (the note
says what), DROP is safe to remove. The raw data is also at `https://lantern-review-j.vercel.app/api/reviews`.

- **mc project chat:** build what J KEEPs (hand-offs as before); list IMPROVE items for the Blender chats.
- **Blender chats:** take the IMPROVE notes in your area as the next round; write its spec; render; push.

## Files

| Where | What |
|---|---|
| `review-site` branch: `index.html`, `api/reviews.js` | the page and the ratings API (private Vercel Blob `reviews/reviews.json`) |
| `review-site`: `specs/`, `scripts/`, `assets/kl_assets/` | one spec per pass, the update scripts and models they need |
| `review-site`: `media/<key>/`, `data/site.json` | rendered clips, stills, 3D; the page's list (built by `tools/gen_site.py`) |
| `tools/review_site/lantern_review.py` (also on `review-site` as `tools/`) | the PC renderer |
| `tools/review_site/pull_reviews.py` | ratings into `docs/blender/review/RATINGS.md` |

**Scrapping:** J can tap "Scrap pass" on the site. The renderer skips scrapped passes and `RATINGS.md` lists them, so
chats stop building on them. "Restore pass" undoes it.
