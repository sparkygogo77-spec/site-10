# J's markups from the review site (3D editor)

Each one: J picked parts (numbered pins), drew on the model and wrote what should change. The Blender chat that owns
the pass takes it as its next round; the coordinator also posts it to the mc thread and marks it `sent`
(POST /api/markups {id, status}). Newest first. Pulled by `tools/review_site/pull_reviews.py`.
