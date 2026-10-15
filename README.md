# Lantern Review

Phone review site for the Lantern Ring Blender takes (https://lantern-review-j.vercel.app), deployed by Vercel
(project `lantern-review`) on every push to `main` of this repo. It moved here from branch `review-site` of
`sparkygogo77-spec/site-10` on 2026-10-15, so pushes to site-10 no longer use up Vercel deployments.
Specs and update scripts still come from site-10 branch `claude/lantern-redesign-pass2`; only J's PC pushes here.
- `index.html`: the page. `data/site.json`: passes and takes (built by the Blender chat's gen_site.py).
- `media/<pass>/<take>-3p.mp4`, `-fp.mp4` (first person), `.jpg` (stills), `.gltf.json` (3D, player held in place).
- `api/reviews.js`: J's KEEP / IMPROVE / DROP and notes, kept in a private Vercel Blob (`reviews/reviews.json`).
  GET `/api/reviews` returns them all.
