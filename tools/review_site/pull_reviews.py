"""Pull J's ratings and notes from the review site into the repo.

    python3 tools/review_site/pull_reviews.py            # writes docs/blender/review/RATINGS.md + ratings.json,
                                                         # and MARKUPS.md + markups/<id>.jpg (J's 3D markups)

Every chat (mc project chat, Blender chats) runs this at the start of a session and commits the two files with its
work, so J's latest KEEP / IMPROVE / DROP and notes are in the repo for everyone.
Source: https://lantern-review-j.vercel.app/api/reviews (ratings) and /data/site.json (pass and take names).
"""
import json, os, sys, urllib.request

SITE = os.environ.get("LANTERN_REVIEW_URL", "https://lantern-review-j.vercel.app")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "docs", "blender", "review")


def get(path, raw=False):
    req = urllib.request.Request(SITE + path, headers={"Cache-Control": "no-cache", "User-Agent": "lantern-pull"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        return data if raw else json.loads(data.decode("utf-8"))


reviews = get("/api/reviews")
site = get("/data/site.json")
names = {t["id"]: (p, t) for p in site["passes"] for t in p["takes"]}

os.makedirs(OUT, exist_ok=True)
json.dump(reviews, open(os.path.join(OUT, "ratings.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)

lines = ["# J's ratings from the review site", "",
         f"Pulled from {SITE} by `tools/review_site/pull_reviews.py`. KEEP is final, IMPROVE is the next thing to work",
         "on (read the note), DROP is safe to remove. \"Re-rendered since\" means the take changed after J rated it.", ""]
scrapped = sorted(rid[5:] for rid, r in reviews.items() if rid.startswith("pass_") and r.get("scrapped"))
lines += ["**Scrapped passes (J: don't build on these, don't render them):** " + (", ".join(scrapped) or "none"), ""]
by_pass = {}
for rid, r in reviews.items():
    if rid.startswith("pass_"):
        continue
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


# ---------------------------------------------------------------- J's markups from the 3D editor
RANGES = [(400, 499, "movement and flight (coordinator)"), (500, 589, "combat"), (590, 599, "rings, suits, tools"),
          (600, 699, "lanterns and charging"), (700, 799, "construct surfaces, walls, corps looks"),
          (800, 899, "rings, suits, tools"), (350, 399, "textures, metals, Red islands"), (900, 999, "construct tools")]


def owner(num):
    try:
        n = int(str(num)[:3])
    except ValueError:
        return "?"
    return next((f"{a}-{b} {name}" for a, b, name in RANGES if a <= n <= b), "coordinator")


try:
    marks = get("/api/markups")
except Exception as e:                       # the site may not have the markup API yet
    marks = []; print("markups: none pulled (", e, ")")
mdir = os.path.join(OUT, "markups"); os.makedirs(mdir, exist_ok=True)
for m in marks:
    f = os.path.join(mdir, m["id"] + ".jpg")
    if m.get("image") and not os.path.exists(f):
        try:
            open(f, "wb").write(get("/api/markups?img=" + m["id"], raw=True))
        except Exception as e:
            print("  image", m["id"], "not pulled:", e)
ml = ["# J's markups from the review site (3D editor)", "",
      "Each one: J picked parts (numbered pins), drew on the model and wrote what should change. The Blender chat that owns",
      "the pass takes it as its next round; the coordinator also posts it to the mc thread and marks it `sent`",
      "(POST /api/markups {id, status}). Newest first. Pulled by `tools/review_site/pull_reviews.py`.", ""]
for m in sorted(marks, key=lambda x: x.get("createdAt", ""), reverse=True):
    p, t = names.get(f"{m['pass']}_{m['take']}", ({"title": ""}, {"name": ""}))
    ml += [f"## {m['createdAt'][:16].replace('T', ' ')} pass {m['pass']} {m['take']} {t.get('name', '')}  [{m.get('status', 'new')}]",
           f"- Owner: {owner(m['pass'])}",
           f"- J: \"{m.get('prompt') or '(drawing only)'}\""]
    if m.get("parts"):
        ml.append("- Parts: " + "; ".join(f"{x['n']} = {x['label']} (material {x.get('material') or '?'}, at {x.get('pos')})" for x in m["parts"]))
    ml.append(f"- 3D view: orbit {m.get('orbit')}, time {m.get('time', 0):.2f} s")
    if m.get("image"):
        ml.append(f"- Picture: `docs/blender/review/markups/{m['id']}.jpg`")
    ml.append("")
open(os.path.join(OUT, "MARKUPS.md"), "w", encoding="utf-8").write("\n".join(ml))
new = sum(1 for m in marks if m.get("status", "new") == "new")
print(f"{len(marks)} markups ({new} new) -> docs/blender/review/MARKUPS.md")
