"""Rebuild data/site.json in a review-site checkout from specs/*.json and the media that exists.

    python3 gen_site.py [SITE_DIR]

Passes are listed newest first (spec "added"). Superseded passes with no media are left off.
Each take's renderedAt is the newest modification time of its media files.

Versions (J: "I need the age or I need a chronological v.# update for every website pass"): data/history.json keeps,
per pass, v1, v2… with a date and the takes rendered in each. A new version starts when any take gets media for the
first time or its media/<key>/<take>.rev goes up (the renderer writes it from the spec's "rev"). The first run backfills
from git history. Rounds: a pass whose title/desc names an older pass ("860 G1 variations", "J on 604") or that an
older pass's superseded_by points to is linked to it both ways.
"""
import json, os, re, subprocess, sys, time
from datetime import datetime, timezone

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

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
HIST_PATH = os.path.join(SITE, "data", "history.json")
try:
    HIST = json.load(open(HIST_PATH, encoding="utf-8"))
except Exception:
    HIST = None


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def utc(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def secs(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()


def backfill():
    """No history yet: one version per git commit that brought a pass new clips/stills/.rev files (commits closer
    than 30 min merged: the renderer's left-over/carried-over commits)."""
    hist = {}
    r = subprocess.run(["git", "-C", SITE, "log", "--reverse", "--format=@%cI", "--name-only", "--", "media"],
                       capture_output=True, text=True)
    at = None
    for line in r.stdout.splitlines():
        if line.startswith("@"):
            at = line[1:]; continue
        m = re.match(r"media/([^/]+)/(.+?)(-3p\.mp4|-fp\.mp4|\.jpg|\.rev)$", line.strip())
        if not m or not at:
            continue
        k, code = m.group(1), m.group(2)
        at_z = utc(at)
        h = hist.setdefault(k, {"versions": [], "seen": {}})
        v = h["versions"][-1] if h["versions"] else None
        if v and secs(at_z) - secs(v["at"]) < 1800:
            if code not in v["takes"]:
                v["takes"].append(code)
        else:
            h["versions"].append({"v": len(h["versions"]) + 1, "at": at_z, "takes": [code]})
    return hist


def rev_of(k, code):
    try:
        return int(open(os.path.join(SITE, "media", k, slug(code) + ".rev")).read().strip() or 0)
    except Exception:
        return 0


def track(k, takes):
    """Add a version when a take gets media for the first time or its rev went up; return this pass's history."""
    h = HIST.setdefault(k, {"versions": [], "seen": {}})
    changed, newest = [], ""
    for t in takes:
        if not (t["clip3p"] or t["clipfp"] or t["still"]):
            continue
        r = rev_of(k, t["code"])
        if t["code"] not in h["seen"] or r > h["seen"][t["code"]]:
            changed.append(t["code"])
            newest = max(newest, t["renderedAt"] or NOW)
        h["seen"][t["code"]] = max(r, h["seen"].get(t["code"], 0))
    if changed and not (backfilled and h["versions"]):   # a backfill already has these from git
        h["versions"].append({"v": len(h["versions"]) + 1, "at": min(newest or NOW, NOW), "takes": changed})
    return h


backfilled = HIST is None
if HIST is None:
    HIST = backfill()

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
    h = track(k, takes)
    vs = h["versions"]
    out.append({"pass": p["pass"], "key": k, "title": p["title"], "desc": p.get("desc", ""), "area": area_of(p),
                "added": p.get("added", ""), "version": len(vs), "versions": vs[-12:],
                "renderedAt": vs[-1]["at"] if vs else None,
                "superseded_by": p.get("superseded_by"), "orbit": p.get("orbit"), "blend": p.get("blend"),
                "takes": takes})
# rounds: links between a pass and the older passes it builds on
keys = {p["key"]: p for p in out}
added = {s["key"]: s.get("added", "") for s in specs}
for s in specs:
    sup = str(s.get("superseded_by") or "")
    for nk in re.findall(r"\b(\d{3}[a-z]*)\b", sup):
        if nk in keys and s["key"] in keys and nk != s["key"]:
            keys[nk].setdefault("roundOf", [])
            if s["key"] not in keys[nk]["roundOf"]:
                keys[nk]["roundOf"].append(s["key"])
for p in out:
    first = p["title"] + " " + re.split(r"(?<=[.!?])\s", p["desc"] or "", maxsplit=1)[0]
    p.setdefault("roundOf", [])
    for ok in re.findall(r"\b(\d{3}[a-z]*)\b", first):
        if ok != p["key"] and ok in keys and added.get(ok, "") < p["added"] and ok not in p["roundOf"]:
            p["roundOf"].append(ok)
    if not p["roundOf"]:
        del p["roundOf"]
for p in out:
    for ok in p.get("roundOf", []):
        keys[ok].setdefault("nextRounds", []).append(p["key"])


def round_no(k, seen=()):
    rs = [round_no(o, seen + (k,)) for o in keys[k].get("roundOf", []) if o not in seen]
    return 1 + max(rs) if rs else 1


for p in out:
    if p.get("roundOf"):
        p["round"] = round_no(p["key"])

os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
json.dump(HIST, open(HIST_PATH, "w", encoding="utf-8"), separators=(",", ":"))
json.dump({"generatedAt": NOW, "areas": AREAS, "passes": out}, open(os.path.join(SITE, "data", "site.json"), "w", encoding="utf-8"), separators=(",", ":"))
n = sum(len(p["takes"]) for p in out)
m = sum(1 for p in out for t in p["takes"] if t["clip3p"] or t["still"])
print(f"{len(out)} passes, {n} takes, {m} with media")
