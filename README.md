# site-data: files the review site saves, with no Vercel deploy

Vercel never deploys this branch (vercel.json here and on review-site). The site at
https://lantern-review-j.vercel.app reads it at runtime through `/api/files`, pinned to the newest commit.

- `live/`: renders from J's PC (`tools/lantern_review.py` pushes `media/<key>/` and `data/` here with plain git).
- everything else: written by the site through `POST /api/files` (for example `models/` from "Make 3D for this").

Don't merge this branch into anything; it only holds data.
