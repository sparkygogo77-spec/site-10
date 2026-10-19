"""Rebuild data/site.json in a review-site checkout from specs/*.json and the media that exists.

    python3 gen_site.py [SITE_DIR]

Passes are listed newest first (spec "added"). Superseded passes with no media are left off.
Each take's renderedAt is the newest modification time of its media files.
"""
import json, os, re, sys, time

SITE = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/review-site"


def slug(c):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", c)


AREAS = ["Movement & flight", "Combat & powers", "Tools & weapons", "Rings & ring glow", "Suits & armour",
         "Constructs & textures", "Lanterns & charging", "Enemies & mounts", "World"]
AREA_RULES = [   # first match on the title wins; a spec's own "area" overrides all of this
    (r"island|halo", "World"),
    (r"^skin|ripple|brick|particle wall|construct animals|big constructs", "Constructs & textures"),
    (r"mount|enem|wisp|stalker", "Enemies & mounts"),
    (r"suit|mech|armou?r", "Suits & armour"),
    (r"first-person tools|pickaxe|sword|\bbows?\b|shield|construct tools|hammer", "Tools & weapons"),
    (r"flight|take-?off|landing|arm lead|animation catalogue|first-person moves", "Movement & flight"),
    (r"\bring\b(?! beam)|\brings\b|gesture", "Rings & ring glow"),
    (r"lantern|charge", "Lanterns & charging"),
]


def area_of(p):
    if p.get("area") in AREAS:
        return p["area"]
    title = p.get("title", "").lower()
    for rx, a in AREA_RULES:
        if re.search(rx, title):
            return a
    n = int(re.sub(r"\D", "", str(p.get("pass", "0")))[:3] or 0)
    return {4: "Movement & flight", 5: "Combat & powers", 6: "Lanterns & charging", 7: "Constructs & textures",
            9: "Tools & weapons"}.get(n // 100, "Combat & powers")


def pose_frac(t):
    """Where the 3D view opens, 0..1 through the clip: the spec's "model_at" frame (e.g. the middle of a beam), else the end."""
    at, fr = t.get("model_at"), t.get("frames")
    if at is None or not fr or fr[1] <= fr[0]:
        return None
    return round(min(1, max(0, (at - fr[0]) / (fr[1] - fr[0]))), 4)


specs = []
for f in os.listdir(os.path.join(SITE, "specs")):
    if f.endswith(".json"):
        specs.append(json.load(open(os.path.join(SITE, "specs", f), encoding="utf-8")))
specs.sort(key=lambda s: s.get("added", ""), reverse=True)

out = []
for p in specs:
    k = p["key"]
    takes = []
    for t in p["takes"]:
        files = {}
        for name, suffix in (("clip3p", "-3p.mp4"), ("clipfp", "-fp.mp4"), ("still", ".jpg"), ("model", ".gltf.json")):
            rel = f"media/{k}/{slug(t['code'])}{suffix}"
            files[name] = rel if os.path.exists(os.path.join(SITE, rel)) else None
        mt = [os.path.getmtime(os.path.join(SITE, v)) for v in files.values() if v]
        tags = list(t.get("tags", []))
        if t.get("default") and not any("default" in x or "pick" in x for x in tags):
            tags.append("default / J's pick")
        skip = os.path.join(SITE, "media", k, slug(t["code"]) + "-fp.skip")
        fp_note = None
        if not files["clipfp"] and os.path.exists(skip):
            fp_note = f"No 1st-person clip: the arms are in view in {float(open(skip).read() or 0):.0%} of frames from the eyes"
        takes.append({"id": f"{k}_{t['code']}", "code": t["code"], "name": t["name"], "facts": t.get("facts", ""),
                      "tags": tags, **files, "fpNote": fp_note, "poseFrac": pose_frac(t),
                      "renderedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(max(mt))) if mt else None})
    if p.get("superseded_by") and not any(t["clip3p"] or t["still"] for t in takes):
        continue
    out.append({"pass": p["pass"], "key": k, "title": p["title"], "desc": p.get("desc", ""), "area": area_of(p),
                "added": p.get("added", ""),
                "superseded_by": p.get("superseded_by"), "orbit": p.get("orbit"), "blend": p.get("blend"),
                "takes": takes})
os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
json.dump({"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "areas": AREAS, "passes": out}, open(os.path.join(SITE, "data", "site.json"), "w", encoding="utf-8"), separators=(",", ":"))
n = sum(len(p["takes"]) for p in out)
m = sum(1 for p in out for t in p["takes"] if t["clip3p"] or t["still"])
print(f"{len(out)} passes, {n} takes, {m} with media")
