"""Build data/jar.json for the review site's Jar view: the current jar, how to install it, and recent updates.

    python3 gen_jar.py [SITE_DIR]          # after gen_status.py --fetch (it fetches origin/main and origin/builds)

Reads, from git refs in SITE_DIR (a clone of site-10 whose `review-site` branch is the site):
    origin/builds  latest.json (version, note), lantern-ring-latest.jar (size), the time it was published
    origin/main    merged pull requests (git log --first-parent) and src/main/resources/lanternring/whats_new.json
                   (each update's in-game steps; matched to the pull request that added it)
and, on J's PC, the jar in his Lunar profile (LUNAR_MODS) to tell which updates are in the game he plays.

"New to you" = merged after the jar J had before the one he has now (`seenBefore`): when the installed version
changes, the previous one moves there. Rides the normal render push (data/ goes to live/ without a deploy).
"""
import json, os, re, subprocess, sys, time, zipfile

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SITE = os.path.abspath(ARGS[0] if ARGS else "/home/claude/review-site")
LUNAR_MODS = os.environ.get("LUNAR_MODS", os.path.expanduser(r"~\.lunarclient\profiles\26\mods\fabric-26.3"))
RAW = "https://github.com/sparkygogo77-spec/site-10/raw/builds/"
WHATS_NEW = "src/main/resources/lanternring/whats_new.json"
KEEP = 40                                             # updates on the page
# J's jar before 2026-10-18 (run 681, built 2026-10-12 12:41 UTC): the start of "new to you" until he installs again
FIRST_SEEN = {"version": "2.1.681+26.3", "builtAt": "2026-10-12T12:41:32Z"}
PASS_RE = re.compile(r"\bpass(?:es)?\s+((?:\d{3}[a-z]?)(?:\s*(?:,|and|&|/|\+)\s*\d{3}[a-z]?)*)", re.I)


def git(*a):
    r = subprocess.run(["git", "-C", SITE] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def current_jar():
    try:
        latest = json.loads(git("show", "origin/builds:latest.json") or "{}")
    except ValueError:
        latest = {}
    size = next((int(l.split()[3]) for l in git("ls-tree", "-l", "origin/builds").splitlines()
                 if l.endswith("\tlantern-ring-latest.jar")), None)
    ct = int(git("log", "-1", "--format=%ct", "origin/builds").strip() or 0)
    return {"version": latest.get("version"), "note": latest.get("note"), "builtAt": iso(ct) if ct else None,
            "bytes": size, "download": RAW + "lantern-ring-latest.jar", "zip": RAW + "lantern-ring-latest.zip"}


def installed_jar():
    """The Lantern Ring jar in J's Lunar profile (only on his PC)."""
    if not os.path.isdir(LUNAR_MODS):
        return None
    for f in sorted(os.listdir(LUNAR_MODS)):
        if f.startswith("lantern-ring") and f.endswith(".jar"):
            p = os.path.join(LUNAR_MODS, f)
            try:
                v = json.loads(zipfile.ZipFile(p).read("fabric.mod.json"))["version"]
            except Exception:
                continue
            return {"version": v, "at": iso(os.path.getmtime(p)), "file": f}
    return None


def pass_keys(*texts):
    out = []
    for t in texts:
        for m in PASS_RE.finditer(t or ""):
            out += re.findall(r"\d{3}", m.group(1))
        m = re.search(r"\bkeeps?\s*\(([\d,\s]+)\)", t or "", re.I)     # "review keeps (840, 701, 838, 844)"
        if m:
            out += re.findall(r"\d{3}", m.group(1))
    return list(dict.fromkeys(out))


def updates():
    try:
        entries = {e["id"]: e for e in json.loads(git("show", f"origin/main:{WHATS_NEW}"))["entries"]}
    except Exception:
        entries = {}
    out = []
    log = git("log", "origin/main", "--first-parent", f"-{KEEP + 20}", "--format=%H%x1f%ct%x1f%s%x1f%b%x1e")
    for rec in log.split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) < 4:
            continue
        sha, ct, subj, body = parts[0], int(parts[1]), parts[2], parts[3].strip()
        if "[skip ci]" in subj:
            continue
        m = re.match(r"Merge pull request #(\d+)(?::\s*(.*)| from \S+)", subj)
        pr = int(m.group(1)) if m else None
        title = (m.group(2) if m and m.group(2) else (body.splitlines() or [subj])[0]) if m else subj
        if re.match(r"(?i)merge (branch|remote)", title):
            continue
        # the whats_new entries this merge added (their ids appear as added lines in its diff)
        diff = git("diff", f"{sha}^1", sha, "--", WHATS_NEW) if pr else ""
        ids = re.findall(r'^\+[\s{]*"id":\s*"([^"]+)"', diff, re.M)     # one entry a line: +\t\t{"id": ...
        news = [{"id": i, "title": entries[i]["title"], "pass": entries[i].get("pass", ""), "steps": entries[i].get("steps", [])}
                for i in ids if i in entries]
        out.append({"pr": pr, "sha": sha[:8], "at": iso(ct), "title": title.strip(),
                    "detail": body if m and m.group(2) else "\n".join(body.splitlines()[1:]).strip(),
                    "passes": pass_keys(title, *[n["pass"] for n in news]), "whatsNew": news})
        if len(out) >= KEEP:
            break
    return out


def main():
    dest = os.path.join(SITE, "data", "jar.json")
    try:
        old = json.load(open(dest, encoding="utf-8"))
    except Exception:
        old = {}
    jar = current_jar()
    inst = installed_jar() or old.get("installed")
    seen = old.get("seenBefore") or FIRST_SEEN
    prev = old.get("installed")
    if inst and prev and inst.get("version") != prev.get("version"):
        seen = {"version": prev["version"], "builtAt": prev.get("builtAt") or prev.get("at")}
    if inst:
        if inst.get("version") == jar["version"]:
            inst["builtAt"] = jar["builtAt"]
        elif prev and prev.get("version") == inst.get("version"):
            inst["builtAt"] = prev.get("builtAt")
    ups = updates()
    for u in ups:
        u["state"] = ("game" if inst and inst.get("builtAt") and u["at"] <= inst["builtAt"]
                      else "latest" if jar["builtAt"] and u["at"] <= jar["builtAt"] else "next")
        u["new"] = u["state"] != "next" and u["at"] > (seen.get("builtAt") or "")
    data = {"generatedAt": iso(time.time()), "jar": jar, "installed": inst, "seenBefore": seen,
            "lunar": {"profile": "26", "folder": r"C:\Users\Josh\.lunarclient\profiles\26\mods\fabric-26.3"},
            "updates": ups}
    json.dump(data, open(dest, "w", encoding="utf-8"), indent=1)
    print(f"  jar.json: jar {jar['version']}, installed {inst and inst.get('version')}, "
          f"{len(ups)} updates ({sum(u['new'] for u in ups)} new to J)")


if __name__ == "__main__":
    main()
