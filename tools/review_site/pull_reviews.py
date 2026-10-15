"""Pull J's ratings and notes from the review site into the repo.

    python3 tools/review_site/pull_reviews.py            # writes docs/blender/review/RATINGS.md + ratings.json

Every chat (mc project chat, Blender chats) runs this at the start of a session and commits the two files with its
work, so J's latest KEEP / IMPROVE / DROP and notes are in the repo for everyone.
Source: https://lantern-review-j.vercel.app/api/reviews (ratings) and /data/site.json (pass and take names).
"""
import json, os, sys, urllib.request

SITE = os.environ.get("LANTERN_REVIEW_URL", "https://lantern-review-j.vercel.app")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "docs", "blender", "review")


def get(path):
    req = urllib.request.Request(SITE + path, headers={"Cache-Control": "no-cache", "User-Agent": "lantern-pull"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


reviews = get("/api/reviews")
site = get("/data/site.json")
names = {t["id"]: (p, t) for p in site["passes"] for t in p["takes"]}

os.makedirs(OUT, exist_ok=True)
json.dump(reviews, open(os.path.join(OUT, "ratings.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)

lines = ["# J's ratings from the review site", "",
         f"Pulled from {SITE} by `tools/review_site/pull_reviews.py`. KEEP is final, IMPROVE is the next thing to work",
         "on (read the note), DROP is safe to remove. \"Re-rendered since\" means the take changed after J rated it.", ""]
by_pass = {}
for rid, r in reviews.items():
    if not (r.get("rating") or r.get("note")):
        continue
    p, t = names.get(rid, ({"pass": rid.split("_")[0], "key": rid.split("_")[0], "title": "(not on the site now)"},
                           {"code": rid.split("_", 1)[-1], "name": "", "renderedAt": None}))
    by_pass.setdefault((p["key"], p["pass"], p["title"]), []).append((t, r))
for (key, num, title), rows in sorted(by_pass.items(), key=lambda x: x[0][0], reverse=True):
    lines += [f"## Pass {num}: {title}", "", "| Take | Rating | Note | Rated |", "|---|---|---|---|"]
    for t, r in sorted(rows, key=lambda x: x[0]["code"]):
        stale = " (re-rendered since)" if t.get("renderedAt") and r.get("updatedAt", "") < t["renderedAt"] else ""
        note = (r.get("note") or "").replace("|", "/").replace("\n", " ")
        lines.append(f"| {t['code']} {t.get('name', '')} | **{r.get('rating') or '-'}** | {note} | "
                     f"{(r.get('updatedAt') or '')[:16].replace('T', ' ')}{stale} |")
    lines.append("")
open(os.path.join(OUT, "RATINGS.md"), "w", encoding="utf-8").write("\n".join(lines))
n = sum(len(v) for v in by_pass.values())
print(f"{n} rated takes across {len(by_pass)} passes -> docs/blender/review/RATINGS.md")
