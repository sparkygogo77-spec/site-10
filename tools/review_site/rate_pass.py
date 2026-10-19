"""Rate a pass from the PC chat: pictures of the unrated takes, then KEEP / IMPROVE / DROP saved where the site reads them.

    python rate_pass.py show <pass> [--all] [--site DIR]
        -> one picture sheet per 4 unrated takes (_previews\\rate\\...) and, as JSON on stdout, the batches:
           [{"sheet": path, "takes": [{"code", "id", "name", "facts", "rating"}]}]  (--all: rated takes too)
    python rate_pass.py save <pass> CODE=KEEP CODE=IMPROVE:"note" CODE=DROP ...
        -> POST /api/reviews for each (same store as the site's buttons), then refreshes ratings.json
    python rate_pass.py flush      -> sends ratings queued while the site's ratings store was down

"Menu: rate <pass>" in docs/handoff/PC-CHAT-BRIEF.md shows each sheet (SendUserFile) and asks one AskUserQuestion
per batch: one question per take, options KEEP / IMPROVE / DROP, a note through "Other". When the ratings API fails
(2026-10-19: Vercel Blob answers 403), ratings go to docs/blender/review/ratings_queue.json (committed, so any chat
can flush it) and into the local ratings.json, so RATINGS.md, the grid and the decision cards still see them.
"""
import json, os, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LIVE = os.path.dirname(REPO)
ARGS = sys.argv[1:]
def opt(name, default=None):
    if name in ARGS:
        i = ARGS.index(name); v = ARGS[i + 1]; del ARGS[i:i + 2]; return v
    return default
SITE = opt("--site", os.path.join(LIVE, "review-site"))
ALL = "--all" in ARGS and not ARGS.remove("--all")
API = os.environ.get("LR_REVIEWS_API", "https://lantern-review-j.vercel.app/api/reviews")   # tests point it elsewhere
LOCAL = os.path.join(REPO, "docs", "blender", "review", "ratings.json")
QUEUE = os.path.join(REPO, "docs", "blender", "review", "ratings_queue.json")
OUT = os.path.join(LIVE, "_previews", "rate")
RATINGS = ("KEEP", "IMPROVE", "DROP")


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return default


def ratings():
    """The site's ratings (falls back to the last pulled ratings.json), plus anything still queued."""
    try:
        with urllib.request.urlopen(API, timeout=15) as r:
            got = json.load(r)
    except Exception:
        got = load(LOCAL, {})
    for q in load(QUEUE, []):
        got[q["id"]] = {"rating": q["rating"], "note": q.get("note", "")}
    return got


def take_list(key):
    site = load(os.path.join(SITE, "data", "site.json"), {})
    p = next((p for p in site.get("passes", []) if p["key"] == key), None)
    if not p:
        sys.exit(f"pass {key} isn't on the site yet (render it first: Menu: render pass {key})")
    return p


def show(key):
    p, rev = take_list(key), ratings()
    takes = [t for t in p["takes"] if (t.get("clip3p") or t.get("clipfp")) and (ALL or not rev.get(t["id"], {}).get("rating"))]
    batches = [takes[i:i + 4] for i in range(0, len(takes), 4)]
    out = []
    for b in batches:
        codes = [t["code"] for t in b]
        folder = os.path.join(OUT, key, "-".join(codes))
        cards = os.path.join(tempfile.gettempdir(), f"lr_rate_{key}.json")
        json.dump({"cards": [{"pass": key, "takes": codes}]}, open(cards, "w", encoding="utf-8"))
        subprocess.run([sys.executable, os.path.join(HERE, "decision_stills.py"), cards, SITE, folder],
                       capture_output=True, text=True)
        sheet = os.path.join(folder, f"{key}.jpg")
        out.append({"sheet": sheet if os.path.exists(sheet) else None,
                    "takes": [{"code": t["code"], "id": t["id"], "name": t.get("name", ""), "facts": t.get("facts", ""),
                               "rating": rev.get(t["id"], {}).get("rating", "")} for t in b]})
    print(json.dumps({"pass": key, "title": p["title"], "link": f"https://lantern-review-j.vercel.app/#{key}",
                      "batches": out}, indent=1, ensure_ascii=False))


def post(item):
    req = urllib.request.Request(API, data=json.dumps({"id": item["id"], "rating": item["rating"], "note": item.get("note", "")}).encode(),
                                 headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def keep_local(items):
    local = load(LOCAL, {})
    for it in items:
        local[it["id"]] = {"note": it.get("note", ""), "rating": it["rating"], "updatedAt": it["at"]}
    json.dump(local, open(LOCAL, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def save(key, pairs):
    p = take_list(key)
    ids = {t["code"].lower(): t["id"] for t in p["takes"]}
    items, bad = [], []
    for pair in pairs:
        code, _, rest = pair.partition("=")
        rating, _, note = rest.partition(":")
        rating = rating.strip().upper()
        if code.lower() not in ids or rating not in RATINGS:
            bad.append(pair); continue
        items.append({"id": ids[code.lower()], "rating": rating, "note": note.strip().strip('"'),
                      "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    if bad:
        print("skipped (unknown take or rating):", ", ".join(bad))
    sent = [it for it in items if post(it)]
    queued = [it for it in items if it not in sent]
    if queued:
        q = load(QUEUE, [])
        q = [x for x in q if x["id"] not in {it["id"] for it in queued}] + queued
        json.dump(q, open(QUEUE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    keep_local(items)
    print(f"pass {key}: {len(sent)} saved on the site" + (f", {len(queued)} queued (the site's ratings store didn't answer; "
          f"they're in ratings.json now and `rate_pass.py flush` sends them later)" if queued else ""))


def flush():
    q = load(QUEUE, [])
    left = [it for it in q if not post(it)]
    if left:
        json.dump(left, open(QUEUE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    elif os.path.exists(QUEUE):
        os.remove(QUEUE)
    print(f"{len(q) - len(left)} sent, {len(left)} still queued")


if __name__ == "__main__":
    if ARGS[:1] == ["show"] and len(ARGS) == 2:
        show(ARGS[1])
    elif ARGS[:1] == ["save"] and len(ARGS) >= 3:
        save(ARGS[1], ARGS[2:])
    elif ARGS[:1] == ["flush"]:
        flush()
    else:
        print(__doc__)
