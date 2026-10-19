# Lantern Review loop

J reviews every Blender take on his phone at **https://lantern-review-j.vercel.app**: a looping third-person clip, a
first-person (eye camera) clip, a 3D pose he can spin, and KEEP / IMPROVE / DROP plus a note per take.
The site is the `review-site` branch of this repo, deployed by Vercel (project `lantern-review`) on every push
to that branch. Ratings are stored by the site (`/api/reviews`) and pulled into the repo by the chats.
Renders and files the site saves go to the private repo **`lantern-review-data`** instead (no deploy): see "Saving without a deploy" below.

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
It pushes the new media and data to `live/` in `lantern-review-data` (no Vercel deploy; the site shows them within
seconds). `--deploy` also pushes review-site (one deploy): only needed when the page or tools changed.)
It pulls the branch, renders with EEVEE on the graphics card (about 0.05–0.1 s a frame, so a pass takes minutes),
writes `media/<key>/`, rebuilds `data/site.json`, commits here and pushes to `lantern-review-data`.
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
| `review-site`: `#control`, `data/control.json`, `data/control/` | the Control tab (J's one place to click: live render, ★ waiting passes, jar models / .blend files / textures with "Build from this", chat prompts); built by `tools/review_site/gen_control.py` on every render run |

**Versions and age (2026-10-19):** J: "I need the age or I need a chronological v.# update for every website pass".
Next to each pass title: `v3 · 2 h ago` = the 3rd render of that pass, the last one 2 h ago. A new version starts
whenever a take gets media for the first time or is rendered again after its `rev` went up. Under the description:
"Made …" (the spec's `added`), "re-rendered …", "Round 2 · builds on 860" / "Next round: 864" (links), and "History"
(v1, v2… with dates and takes). "New since you rated" = a take was re-rendered after J rated it. "Newest first" in the
header lists every pass by its last render. The pass menu shows `v3 2h` too. Kept by `gen_site.py` in
`data/history.json` (backfilled from git on first run); rounds come from `superseded_by` and older pass numbers named
in a spec's title or first sentence ("860 G1 variations", "J on 604").

**Scrapping:** J can tap "Scrap pass" on the site. The renderer skips scrapped passes and `RATINGS.md` lists them, so
chats stop building on them. "Restore pass" undoes it.

## Areas (2026-10-18)
The site groups passes by area, then status. Set `"area"` in a spec to one of: Movement & flight, Combat & powers, Tools & weapons,
Rings & ring glow, Suits & armour, Constructs & textures, Lanterns & charging, Enemies & mounts, World. Without it, the area comes
from the title (gen_site.py AREA_RULES), then the pass number range. Pass numbers stay as they are.

## Saving without a deploy (private repo `lantern-review-data`, 2026-10-18)

J: "I need to be able from site to be able to push to git and have vercel update instead of redeploy", and site-10 is
going private ("make sure we cant make any actions through github"). Every push to `review-site` is one Vercel deploy
(free plan, about 100 a day). Files that change often live in the **private repo `sparkygogo77-spec/lantern-review-data`**
instead: it holds no mod code, isn't connected to Vercel (so it never deploys), and the site reaches it only through
`/api/files` with a token that can touch that one repo. A save is a git commit and shows on the site in about 5 seconds.

```
 site button ─► POST /api/files ─► GitHub API commit on lantern-review-data ─┐
 J's PC render ─► git push lantern-review-data (live/media, live/data) ──────┤
                                                                             ▼
 page ─► GET /api/files?prefix=… (newest commit + file list, cached 5 s) ─► GET /api/files?path=…&b=<blob>&s=<size>
```

- **API** (`api/files.js` on review-site): `GET /api/files?prefix=models/` → `{sha, files:[{path, size, url}]}`;
  the `url`s are `/api/files?path=…&b=<blob>&s=<size>`, cached by Vercel for good (a new version has a new blob);
  `GET /api/files?path=<file>` → the newest version (usable as an `<img>`/`<video>` src; Range works for phones);
  `POST /api/files {message, files:[{path, text|base64|delete:true}]}` → one commit, `{ok, sha, files:[{path, url}]}`.
  Up to 20 files and about 3 MB per call (Vercel's 4.5 MB body limit). Files over 4 MB are answered with a short-lived
  GitHub download link. `live/` is the PC's and is refused. Saved .html/.svg are served sandboxed (can't run as the site).
- **In a page:** `<script src="assets/sitefiles.js"></script>`, then `SiteFiles.save([{path, blob}], "message")`,
  `SiteFiles.list(prefix)`, `SiteFiles.url(listing, path)`, `SiteFiles.readJSON(path)`.
- **Renders:** `lantern_review.py` copies `media/<key>/` of the passes it rendered and all of `data/` to `live/` in a
  clone at `LanternLive
eview-data` and pushes it (J's own git login). The page uses `live/data/*.json` when its
  `generatedAt` is at least as new as the deployed copy, and points `media/…` / `data/…` paths at `live/` when the file
  is there. Older media stays on review-site and still loads from the deployment.
- **Secret:** `GITHUB_TOKEN` in the Vercel project. Only J creates or sees it. Without it, reads and saves answer 503.
  1. github.com/new → name `lantern-review-data` → Private → tick "Add a README file" → Create repository.
  2. github.com → your picture → Settings → Developer settings → Personal access tokens → Fine-grained tokens →
     Generate new token → name `lantern-review data`, expiry 1 year, Only select repositories: `lantern-review-data`
     (only that one), Repository permissions → Contents: Read and write → Generate → Copy.
  3. vercel.com → `lantern-review` → Settings → Environment Variables → Key `GITHUB_TOKEN`, paste, Production +
     Preview, Sensitive on → Save. Then Deployments → newest → ⋯ → Redeploy (env vars apply from the next deploy).
- Anyone with the site link can save (same as ratings); paths are checked and only lantern-review-data is written.
- The old `site-data` branch in site-10 (first version, public reads) is unused; delete it when convenient.
