# Lantern Review (branch `review-site`)

Phone review site for the Lantern Ring Blender takes, deployed by Vercel from this branch.
- `index.html`: the page. `data/site.json`: passes and takes (built by the Blender chat's gen_site.py).
- `media/<pass>/<take>-3p.mp4`, `-fp.mp4` (first person), `.jpg` (stills), `.gltf.json` (3D, player held in place).
- `api/reviews.js`: J's KEEP / IMPROVE / DROP and notes, kept in a private Vercel Blob (`reviews/reviews.json`).
  GET `/api/reviews` returns them all.
