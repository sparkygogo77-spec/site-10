"""Rebuild data/site.json in a review-site checkout from specs/*.json and the media that exists.

    python3 gen_site.py [SITE_DIR]

Passes are listed newest first (spec "added"). Superseded passes with no media are left off.
Each take's renderedAt is the newest modification time of its media files.
"""
import json, os, re, sys, time

SITE = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/review-site"


def slug(c):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", c)


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
                      "tags": tags, **files, "fpNote": fp_note,
                      "renderedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(max(mt))) if mt else None})
    if p.get("superseded_by") and not any(t["clip3p"] or t["still"] for t in takes):
        continue
    out.append({"pass": p["pass"], "key": k, "title": p["title"], "desc": p.get("desc", ""),
                "superseded_by": p.get("superseded_by"), "orbit": p.get("orbit"), "blend": p.get("blend"),
                "takes": takes})
os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
json.dump({"passes": out}, open(os.path.join(SITE, "data", "site.json"), "w", encoding="utf-8"), separators=(",", ":"))
n = sum(len(p["takes"]) for p in out)
m = sum(1 for p in out for t in p["takes"] if t["clip3p"] or t["still"])
print(f"{len(out)} passes, {n} takes, {m} with media")
