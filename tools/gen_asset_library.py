"""Build docs/library/LIBRARY.md: a short, navigable list of everything a Blender chat can start from.

    python tools/gen_asset_library.py            # from the repo root (site-10)

Every entry has a stable short id J can answer with ("P:863", "J:dark_lantern", "T:br1/green", "F:movement/flight_barrier"):
  P:  Blender passes waiting on J (docs/blender/review/INBOX.md) with their spec, script and .blend
  J:  models in the mod jar (src/main/resources/assets/lanternring/bbmodel on main; fetch origin/main and origin/builds
      first, or it falls back to this branch's older copy)
  T:  construct textures in the texture library (docs/texture_library/<colour>/<name>)
  B:  base models for Blender (docs/blender/models)
  R:  rigs and starting scripts to copy from
  F:  .blend files on J's PC (C:\\Users\\Josh\\Documents\\LanternLive\\<area>). Only the PC can list them: run there,
      this script also writes docs/library/pc_files.json, which cloud chats then read.
"""
import json, os, re, sys, time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIVE = os.environ.get("LANTERN_LIVE", r"C:\Users\Josh\Documents\LanternLive")
OUT = os.path.join(REPO, "docs", "library")
AREAS = ["lanterns", "movement", "combat", "constructs", "red", "suit"]

JAR_GROUPS = [            # first match wins
    ("Lanterns and batteries", r"lantern|battery|port|nebula|lava_font"),
    ("Rings and the forge", r"ring|crest|crown|forge|gauntlet|stone"),
    ("Construct tools and weapons", r"construct_|blast_drill|fear_nuke"),
    ("Mobs, mounts and armour", r"armour|ravager|hawk|runner|golem|bull"),
]
RIGS = [
    ("R:player_rig", "docs/blender/blender_updates/228_ground_flight.update.py", "player rig (lines 37-215): body, arms, ring hand"),
    ("R:construct_material", "docs/blender/blender_updates/400_power_slide.update.py", "construct material and bloom set-up"),
    ("R:spec_firstperson", "docs/blender/review/specs/803.json", "review spec for a first-person rig"),
    ("R:spec_body", "docs/blender/review/specs/406.json", "review spec for a player body animation"),
    ("R:bbmodel_export", "tools/pixel_rage_battery_bbmodel.py", "voxel model to Blockbench (greedy boxes, box UV)"),
    ("R:pack_blend", "tools/blender_pipeline/pack_blend.py", "pack a .blend with its textures"),
]


def rel(*p):
    return os.path.join(REPO, *p)


def waiting_passes():
    path = rel("docs", "blender", "review", "INBOX.md")
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"## (\d{4}-\d\d-\d\d) pass (v\d+\.\d+|\d+)(?: rev \d+)?: (.+?)\s+\[status: WAITING\]", line)
        if not m:
            continue
        date, num, title = m.groups()
        spec = rel("docs", "blender", "review", "specs", f"{num}.json")
        blend = script = ""
        if os.path.exists(spec):
            s = json.load(open(spec, encoding="utf-8"))
            blend, script = s.get("blend") or "", s.get("script") or ""
        rows.append((f"P:{num}", date, title, blend, script))
    return rows


def git(*a):
    import subprocess
    r = subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def jar_version():
    """The jar J plays (latest.json on the builds branch), if this clone has fetched it."""
    try:
        return json.loads(git("show", "origin/builds:latest.json"))["version"]
    except Exception:
        return ""


def jar_models():
    """Models in the jar: from main (what CI builds the jar from) when fetched; this branch lags behind it."""
    bb = "src/main/resources/assets/lanternring/bbmodel/"
    listed = git("ls-tree", "--name-only", "origin/main", bb).split()
    if listed:
        names, jar_models.source = sorted(os.path.basename(f)[:-8] for f in listed if f.endswith(".bbmodel")), "origin/main"
    else:
        d = rel(*bb.split("/"))
        names = sorted(f[:-8] for f in os.listdir(d) if f.endswith(".bbmodel")) if os.path.isdir(d) else []
        jar_models.source = "this branch (fetch main for the jar's list)"
    groups = {g: [] for g, _ in JAR_GROUPS}
    groups["Other"] = []
    for n in names:
        g = next((g for g, rx in JAR_GROUPS if re.search(rx, n)), "Other")
        groups[g].append(n)
    return groups


def textures():
    d = rel("docs", "texture_library")
    out = {}
    if not os.path.isdir(d):
        return out
    for colour in sorted(os.listdir(d)):
        cd = os.path.join(d, colour)
        if os.path.isdir(cd):
            for name in sorted(os.listdir(cd)):
                if os.path.isdir(os.path.join(cd, name)):
                    out.setdefault(name, []).append(colour)
    return out


def base_models():
    d = rel("docs", "blender", "models")
    if not os.path.isdir(d):
        return []
    return sorted({os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith((".glb", ".npz", ".blend"))})


def pc_files():
    """List J's area folders when run on his PC (and save the list); elsewhere read the saved list."""
    snap = os.path.join(OUT, "pc_files.json")
    if os.path.isdir(LIVE):
        files = {}
        for a in AREAS:
            ad = os.path.join(LIVE, a)
            if os.path.isdir(ad):
                files[a] = sorted(
                    ({"name": f[:-6], "mb": round(os.path.getsize(os.path.join(ad, f)) / 1e6, 1),
                      "date": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(os.path.join(ad, f))))}
                     for f in os.listdir(ad) if f.endswith(".blend")),
                    key=lambda r: r["date"], reverse=True)
        data = {"listed": time.strftime("%Y-%m-%d %H:%M"), "areas": files}
        os.makedirs(OUT, exist_ok=True)
        json.dump(data, open(snap, "w", encoding="utf-8"), indent=1)
        return data
    return json.load(open(snap, encoding="utf-8")) if os.path.exists(snap) else {"listed": "never", "areas": {}}


def main():
    passes, jar, tex, models, pc = waiting_passes(), jar_models(), textures(), base_models(), pc_files()
    L = ["# Lantern Ring asset library",
         "",
         f"Made by `tools/gen_asset_library.py` on {time.strftime('%Y-%m-%d %H:%M')}. Don't edit by hand; re-run it.",
         "Answer with an id to start from it, e.g. `P:860 improve the glow`, `J:dark_lantern new lens`, `T:br1/green on F:red/...`.",
         "",
         "## Start here: newest passes waiting on J",
         ""]
    for pid, date, title, blend, _ in passes[:8]:
        L.append(f"- **{pid}** {title} ({date})" + (f" · `{blend}`" if blend else ""))
    L += ["", f"## P: every waiting pass ({len(passes)})", "",
          "| id | date | title | .blend (in LanternLive) | script |", "|---|---|---|---|---|"]
    L += [f"| {p} | {d} | {t} | `{b}` | `{os.path.basename(s)}` |" for p, d, t, b, s in passes]
    L += ["", f"## J: models in the mod jar ({sum(len(v) for v in jar.values())})", "",
          f"Jar {jar_version() or '(version unknown)'}; list from {jar_models.source}. Files: "
          "`src/main/resources/assets/lanternring/bbmodel/<name>.bbmodel` on `main` (read with "
          "`git show origin/main:<path>` after `git fetch --depth 1 origin +refs/heads/main:refs/remotes/origin/main`).", ""]
    for g, names in jar.items():
        if names:
            L.append(f"- **{g}:** " + ", ".join(f"`J:{n}`" for n in names))
    L += ["", f"## T: construct textures ({len(tex)})", "",
          "Files: `docs/texture_library/<colour>/<name>/` (notes in its README.md).", ""]
    L += [f"- `T:{n}/<colour>` in " + ", ".join(c) for n, c in tex.items()]
    L += ["", f"## B: base models for Blender ({len(models)})", "", "Files: `docs/blender/models/`.", "",
          ", ".join(f"`B:{m}`" for m in models), "",
          "## R: rigs and starting points", ""]
    L += [f"- `{rid}` `{p}`: {what}" for rid, p, what in RIGS]
    L += ["", f"## F: .blend files on J's PC (listed {pc['listed']})", "",
          "Path: `C:\\Users\\Josh\\Documents\\LanternLive\\<area>\\<name>.blend`. Newest first, 6 per area.", ""]
    for a, rows in pc["areas"].items():
        if rows:
            more = f" (+{len(rows) - 6} more)" if len(rows) > 6 else ""
            L.append(f"- **{a}:** " + ", ".join(f"`F:{a}/{r['name']}` {r['date']}" for r in rows[:6]) + more)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "LIBRARY.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print(f"LIBRARY.md: {len(passes)} waiting passes, {sum(len(v) for v in jar.values())} jar models, "
          f"{len(tex)} textures, {len(models)} base models, PC files listed {pc['listed']}")


if __name__ == "__main__":
    main()
