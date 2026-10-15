"""Build data/status.json for the review site: what's in the current jar, and what isn't on the site yet.

    python3 gen_status.py [SITE_DIR] [--fetch]

Reads git refs in SITE_DIR (a clone of site-10; the review site is its `review-site` branch):
    origin/builds  the jar branch: latest.json (version, note) and the time the jar was published
    origin/main    the mod's code: commits up to the jar's time are in the jar, later ones come in the next jar
    origin/dev     the chats' branch (claude/lantern-redesign-pass2): INBOX.md and the review specs
--fetch fetches those three first (the PC renderer passes it; it costs no Vercel deploy).

"In the game" for a pass = its number ("pass 807", "passes 403 and 404") or its hand-off folder name appears in a
main commit message. That is a best guess from commit messages, so the page says "found in the jar's changes".
"""
import json, os, re, subprocess, sys, time

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SITE = ARGS[0] if ARGS else "/home/claude/review-site"
DEV = "claude/lantern-redesign-pass2"


def git(*a):
    r = subprocess.run(["git", "-C", SITE] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


if "--fetch" in sys.argv:
    for src, dst, depth in (("main", "main", "400"), ("builds", "builds", "5"), (DEV, "dev", "50")):
        subprocess.run(["git", "-C", SITE, "fetch", "-q", "--depth", depth, "origin",
                        f"+refs/heads/{src}:refs/remotes/origin/{dst}"], capture_output=True)

# ---------------------------------------------------------------- the jar
jar = {"version": None, "note": None, "publishedAt": None}
try:
    j = json.loads(git("show", "origin/builds:latest.json") or "{}")
    jar["version"], jar["note"] = j.get("version"), j.get("note")
except ValueError:
    pass
jar_time = int((git("log", "-1", "--format=%ct", "origin/builds").strip() or "0"))
if jar_time:
    jar["publishedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(jar_time))

PASS_RE = re.compile(r"\bpass(?:es)?\s+((?:\d{3}[a-z]?)(?:\s*(?:,|and|&|/|\+)\s*\d{3}[a-z]?)*)", re.I)


def passes_in(text):
    out = set()
    for m in PASS_RE.finditer(text):
        out.update(re.findall(r"\d{3}", m.group(1)))
    return out


log = git("log", "origin/main", "--no-merges", "--format=%H%x1f%ct%x1f%s%x1f%b%x1e")
in_jar, next_jar = [], []
for rec in log.split("\x1e"):
    parts = rec.strip("\n").split("\x1f")
    if len(parts) < 4:
        continue
    sha, ct, subj, body = parts[0], int(parts[1]), parts[2], parts[3]
    if re.match(r"(?i)merge\b", subj) or "[skip ci]" in subj:
        continue
    item = {"sha": sha[:8], "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ct)), "title": subj.replace("[skip ci]", "").strip(),
            "passes": sorted(passes_in(subj)),        # the subject only: bodies mention passes in passing ("redo in 407")
            "handoffs": sorted(set(re.findall(r"docs/handoff/([A-Za-z0-9._-]+)", subj + "\n" + body)))}
    (in_jar if (not jar_time or ct <= jar_time) else next_jar).append(item)
# Housekeeping commits that never trigger a jar build ([skip ci]) aren't "coming in the next jar"

pass_in_jar, pass_next = {}, {}
handoff_in_jar, handoff_next = set(), set()
for c in in_jar:
    for p in c["passes"]:
        pass_in_jar.setdefault(p, c["title"])
    handoff_in_jar.update(c["handoffs"])
for c in next_jar:
    for p in c["passes"]:
        pass_next.setdefault(p, c["title"])
    handoff_next.update(c["handoffs"])

# A hand-off named in a jar commit covers the passes its README names ("passes 404 and 405")
readme_in_jar, readme_next = {}, {}       # only trusted for passes J already decided (not WAITING)
for names, target in ((handoff_in_jar, readme_in_jar), (handoff_next, readme_next)):
    for h in names:
        readme = git("show", f"origin/dev:docs/handoff/{h}/README.md") or git("show", f"origin/dev:docs/handoff/{h}")
        for p in passes_in(readme[:3000]):
            target.setdefault(p, f"hand-off {h}")

# ---------------------------------------------------------------- the chats' deliveries (INBOX) and the site
inbox = git("show", "origin/dev:docs/blender/review/INBOX.md")
entries = []
for block in re.split(r"\n(?=## 20)", inbox):
    m = re.match(r"## (20\d\d-\d\d-\d\d) (pass(?:es)? [^:]+?):\s*(.*?)\s*\[(?:status:\s*)?([^\]]*)\]", block)
    if not m:
        continue
    nums = re.findall(r"\d{3}", m.group(2))
    if not nums:
        continue
    blend = re.search(r"^- Open in Blender:\s*(.+)$", block, re.M)
    hand_lines = "\n".join([block.split("\n", 1)[0]] + re.findall(r"^- For the game:.*$", block, re.M))
    hand = re.findall(r"docs/handoff/([A-Za-z0-9._-]+)", hand_lines)   # this pass's own hand-off, not ones it mentions
    entries.append({"pass": nums[0], "date": m.group(1), "title": m.group(3).strip(), "status": m.group(4).strip(),
                    "blend": blend.group(1).strip().strip("`") if blend else None, "handoffs": sorted(set(hand))})

specs = {}
for path in git("ls-tree", "--name-only", "origin/dev", "docs/blender/review/specs/").split():
    if path.endswith(".json"):
        try:
            s = json.loads(git("show", f"origin/dev:{path}") or "{}")
        except ValueError:
            continue
        specs[os.path.basename(path)[:-5]] = s

site_path = os.path.join(SITE, "data", "site.json")
site = json.load(open(site_path, encoding="utf-8")) if os.path.exists(site_path) else {"passes": []}
on_site = {}
for p in site["passes"]:
    media = any(t.get("clip3p") or t.get("still") for t in p["takes"])
    on_site[str(p["pass"])] = on_site.get(str(p["pass"]), False) or media


RATINGS = {}
try:                                      # J's site ratings: a pass with a KEEP take is decided
    import urllib.request
    req = urllib.request.Request(os.environ.get("LANTERN_REVIEW_URL", "https://lantern-review-j.vercel.app") + "/api/reviews",
                                 headers={"User-Agent": "lantern-status"})
    with urllib.request.urlopen(req, timeout=20) as r:
        RATINGS = json.loads(r.read().decode("utf-8"))
except Exception:
    pass
KEPT = {k.split("_")[0][:3] for k, v in RATINGS.items() if isinstance(v, dict) and v.get("rating") == "KEEP"}


def game_state(num, handoffs, status):
    decided = num in KEPT or bool(status) and not re.match(r"(?i)waiting", status)
    if num in pass_in_jar or set(handoffs) & handoff_in_jar or (decided and num in readme_in_jar):
        return "in_jar"
    if num in pass_next or set(handoffs) & handoff_next or (decided and num in readme_next):
        return "next_jar"
    if re.match(r"(?i)handed off|in bundle", status):
        return "handed_off"
    return "not_in_game"


passes = {}
for e in entries:                       # newest entry per pass wins (INBOX is newest first)
    passes.setdefault(e["pass"], e)

not_on_site = []
seen = set()
for num, e in passes.items():
    seen.add(num)
    st = e["status"]
    if not re.match(r"(?i)waiting", st):   # picked / handed off / old: decided outside the site, nothing to rate
        continue
    spec = next((s for k, s in specs.items() if k.startswith(num)), None)
    if spec and spec.get("superseded_by"):
        continue
    if on_site.get(num):
        continue
    if num in on_site:
        why = "on the site, but no clips yet: waiting for your PC render"
    elif spec:
        why = "spec ready: waiting for your PC render"
    else:
        why = "no review spec: the Blender chat didn't add it to the site"
    not_on_site.append({"pass": num, "date": e["date"], "title": e["title"], "status": st, "why": why, "blend": e["blend"],
                        "game": game_state(num, e["handoffs"], st)})
for k, s in specs.items():               # specs with no INBOX entry
    num = str(s.get("pass", k))[:3]
    if num in seen or on_site.get(num) or s.get("superseded_by"):
        continue
    seen.add(num)
    not_on_site.append({"pass": num, "date": (s.get("added") or "")[:10], "title": s.get("title", ""), "status": "",
                        "why": "on the site, but no clips yet: waiting for your PC render" if num in on_site
                        else "spec ready: waiting for your PC render", "blend": s.get("blend"),
                        "game": game_state(num, [], "")})
not_on_site.sort(key=lambda x: (x["date"], x["pass"]), reverse=True)

game = {}
for num in set(on_site) | set(passes):
    e = passes.get(num, {"handoffs": [], "status": ""})
    st = game_state(num, e["handoffs"], e["status"])
    game[num] = {"state": st, "change": pass_in_jar.get(num) or pass_next.get(num) or readme_in_jar.get(num) or readme_next.get(num)}

out = {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "jar": jar,
       "inJar": in_jar[:25], "nextJar": next_jar[:15], "notOnSite": not_on_site, "game": game}
os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
json.dump(out, open(os.path.join(SITE, "data", "status.json"), "w", encoding="utf-8"), separators=(",", ":"))
print(f"status: jar {jar['version']}, {len(in_jar)} changes in it, {len(next_jar)} for the next jar, "
      f"{len(not_on_site)} passes not on the site, {sum(1 for g in game.values() if g['state'] == 'in_jar')} passes found in the jar")
