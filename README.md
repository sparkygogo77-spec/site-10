# Lantern Review (branch `review-site`)

Phone review site for the Lantern Ring Blender takes, deployed by Vercel from this branch.
- `index.html`: the page. `data/site.json`: passes and takes (built by the Blender chat's gen_site.py).
- `media/<pass>/<take>-3p.mp4`, `-fp.mp4` (first person), `.jpg` (stills), `.gltf.json` (3D, player held in place).
- `api/reviews.js`: J's KEEP / IMPROVE / DROP and notes (`reviews/reviews.json`).
- `api/markups.js`: J's 3D-editor markups (`markups/markups.json` + `markups/<id>.jpg`).
- `api/render.js`: the PC render's progress banner (`render/status.json`).
- All three keep their state on site-10's `site-data` branch through `api/_gitstore.js` (GitHub contents API,
  GITHUB_TOKEN; a save is a commit, never a deploy). The site stopped using Vercel Blob on 2026-10-19 (it answered 403).
  GET `/api/reviews` returns them all.
