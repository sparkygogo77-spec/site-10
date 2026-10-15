"""Build review-site/data/site.json from the render manifest + media that exists."""
import json, os, re
R = "/tmp/claude-0/-home-claude-site-10/339d885c-9635-527f-8aeb-f861000ea518/scratchpad/review"
SITE = "/home/claude/review-site"
man = json.load(open(f"{R}/manifest.json"))
extra = json.load(open("/home/claude/review-tools/extra_passes.json"))
mvm = [p for p in json.load(open("/home/claude/review-tools/movement_manifest.json"))["passes"] if not p.get("fponly")]
extra["passes"] = extra["passes"][:1] + mvm + extra["passes"][1:]

def key_of(p):
    return p["pass"] + ("cps" if p.get("entry") == "combat pick sheet" else "")

def slug(code):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", code)

def media(k, code, suffix):
    rel = f"media/{k}/{slug(code)}{suffix}"
    return rel if os.path.exists(os.path.join(SITE, rel)) else None

out = []
for p in extra["passes"] + man["passes"]:
    if p["pass"] in ("403", "404", "405", "406") and p in man["passes"]:
        continue
    k = key_of(p)
    takes = []
    for t in p["takes"]:
        tags = list(t.get("tags", []))
        if t.get("default") and "default" not in " ".join(tags):
            tags.append("default / J's pick")
        takes.append({"id": f"{k}_{t['code']}", "code": t["code"], "name": t["name"], "facts": t.get("facts", ""),
                      "tags": tags,
                      "clip3p": media(k, t["code"], "-3p.mp4"), "clipfp": media(k, t["code"], "-fp.mp4"),
                      "still": media(k, t["code"], ".jpg"), "model": media(k, t["code"], ".gltf.json")})
    out.append({"pass": p["pass"], "key": k, "title": p["title"], "desc": p.get("desc", ""),
                "superseded_by": p.get("superseded_by"), "orbit": p.get("orbit"), "takes": takes})
os.makedirs(f"{SITE}/data", exist_ok=True)
json.dump({"passes": out}, open(f"{SITE}/data/site.json", "w"), separators=(",", ":"))
n = sum(len(p["takes"]) for p in out); m = sum(1 for p in out for t in p["takes"] if t["clip3p"] or t["still"])
print(f"{len(out)} passes, {n} takes, {m} with media")
