"""The PC chat's work grid: one card per pass, in columns by where it stands, for show_widget in the Code tab.

J: "when things are done update and move them on the grid but always send the grid, and i should have a direct
download/open in blender button with the chat link and associated jars if completed".

Columns: Building (passes named with --building) / Waiting on you (unrated takes) / Your picks (KEEP or PICKED, not in
the jar yet) / In the game (named by a jar update on main). Dropped and superseded passes are one line at the bottom.
Cards link to the review site (rate, watch), the jar download when the pass is in the game, and the chat or thread that
made it. Widget links open https only; opening the .blend in Blender is a menu button (the chat runs `lr open NNN`).

    python tools/chat_grid.py [--review-site ../review-site] [--passes 600-699,864,865] [--building 610:"title"]
        -> prints the HTML fragment to paste into show_widget (also writes ../_previews/grid.html)
"""
import argparse, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SITE = "https://lantern-review-j.vercel.app"
PROJECT = "https://claude.ai/code/project/chan_01Nh3k9VYj9ScKTPZ7pDFFDu"


def parse_ranges(s):
    out = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out |= {str(n) for n in range(int(a), int(b) + 1)}
        elif part:
            out.add(part)
    return out


def pass_key(num):
    """Sort order: v2 ids (v2.0101 ...) after every old 3-digit pass."""
    return (1, num) if num.startswith("v") else (0, f"{int(num):06d}")


def inbox_entries():
    text = open(os.path.join(REPO, "docs", "blender", "review", "INBOX.md"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^## (\S+) pass (v\d+\.\d+|\d+): (.*?)\s+\[status: ([^\]]*)\]\s*\n((?:- .*\n?)*)", text, re.M):
        date, num, title, status, body = m.groups()
        if num not in out:                                     # newest first: keep the newest entry
            blend = re.search(r"Open in Blender: (\S+\.blend)", body)
            out[num] = dict(date=date, title=title, status=status, body=body, blend=blend.group(1) if blend else "",
                            pc="by the PC chat" in body or "PC chat" in body)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-site", default=os.path.join(os.path.dirname(REPO), "review-site"))
    ap.add_argument("--passes", default="600-699,864,865")
    ap.add_argument("--building", action="append", default=[], help='NNN:"title" for a pass being built now')
    ap.add_argument("--out", default=os.path.join(os.path.dirname(REPO), "_previews", "grid.html"))
    a = ap.parse_args()

    want = parse_ranges(a.passes)
    specs = {}
    sdir = os.path.join(REPO, "docs", "blender", "review", "specs")
    for f in os.listdir(sdir):
        if f.endswith(".json") and (f[:-5] in want or f.startswith("v")):     # v2.01xx: J's v2 numbering (2026-10-19)
            specs[f[:-5]] = json.load(open(os.path.join(sdir, f), encoding="utf-8"))
    ratings = json.load(open(os.path.join(REPO, "docs", "blender", "review", "ratings.json"), encoding="utf-8"))
    inbox = inbox_entries()
    jar, in_jar = {}, {}
    try:
        j = json.load(open(os.path.join(a.review_site, "data", "jar.json"), encoding="utf-8"))
        jar = j.get("jar", {})
        for u in j.get("updates", []):
            for p in u.get("passes", []):
                in_jar.setdefault(p, u)
    except Exception:
        pass

    cols = {"build": [], "wait": [], "picks": [], "game": []}
    gone = []
    for b in a.building:
        num, _, title = b.partition(":")
        cols["build"].append(dict(num=num, title=title.strip('"'), meta="building now", links=[], blend=""))
    for num in sorted(specs, key=pass_key, reverse=True):
        sp = specs[num]
        ib = inbox.get(num, {})
        status = ib.get("status", "")
        if sp.get("superseded_by") or status.upper().startswith(("DROPPED", "SCRAPPED")):
            gone.append(f"{num} {sp.get('title', '')[:40]}" + (f" (→ {sp['superseded_by']})" if sp.get("superseded_by") else ""))
            continue
        takes = [t["code"] for t in sp.get("takes", [])]
        r = [ratings.get(f"{num}_{c}", {}).get("rating") for c in takes]
        k, i, d, u = r.count("KEEP"), r.count("IMPROVE"), r.count("DROP"), sum(1 for x in r if not x)
        picked = "PICKED" in status.upper() or "KEEP" in status.upper()
        bits = [f"{k} keep" if k else "", f"{i} improve" if i else "", f"{d} drop" if d else "", f"{u} to rate" if u else ""]
        meta = " · ".join(b for b in bits if b) or f"{len(takes)} takes"
        if picked:                                            # what J picked and where it went, from the INBOX status
            meta = status.split("(", 1)[0].replace("PICKED", "Picked").strip()
            if "(" in status and ")" in status:
                meta += " · " + status[status.index("(") + 1:status.rindex(")")][:60].replace("->", "→")
        links = [("Rate on the site" if u else "Watch on the site", f"{SITE}/#{num}/{takes[0]}" if takes else f"{SITE}/#{num}")]
        if num in in_jar and jar.get("download"):
            links.append((f"Jar {jar.get('version', '')}", jar["download"]))
        head = ""
        try:
            head = open(os.path.join(REPO, sp.get("script", "")), encoding="utf-8").read(400)
        except Exception:
            pass
        by_pc = ib.get("pc") or "PC chat" in head
        if not by_pc:
            links.append(("Thread that made it", PROJECT))
        if by_pc:
            meta += " · made by the PC chat"
        card = dict(num=num, title=sp.get("title", ib.get("title", "")), meta=meta, links=links,
                    blend=sp.get("blend", ""), status=status)
        if u == 0 and k == 0 and i == 0 and takes:
            gone.append(f"{num} {sp.get('title', '')[:40]} (all dropped)")
            continue
        if num in in_jar:
            cols["game"].append(card)
        elif picked or u == 0:
            cols["picks"].append(card)
        else:
            cols["wait"].append(card)

    head = {"build": ("Building", "ti-hammer"), "wait": ("Waiting on you", "ti-eye"),
            "picks": ("Your picks", "ti-star"), "game": ("In the game", "ti-device-gamepad-2")}
    e = html.escape
    parts = ['<h2 class="sr-only">Lantern work grid: passes by where they stand, with links to rate, watch and download.</h2>',
             '<style>.g{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;padding:.5rem 0}'
             '.h{font-size:13px;color:var(--text-secondary);display:flex;gap:6px;align-items:center;margin:0 0 6px}'
             '.c{background:var(--surface-2);border:.5px solid var(--border);border-radius:12px;padding:10px 12px;margin:0 0 8px}'
             '.n{font-weight:500;font-size:14px;margin:0}.t{font-size:13px;margin:2px 0 4px;line-height:1.4}'
             '.m{font-size:12px;color:var(--text-secondary);margin:0 0 6px}.b{font-size:11px;color:var(--text-muted);margin:0 0 6px;'
             'font-family:var(--font-mono);word-break:break-all}.l a{display:inline-block;font-size:12px;margin:0 8px 2px 0;'
             'color:var(--text-accent);text-decoration:none}.e{font-size:12px;color:var(--text-muted)}'
             '.f{font-size:12px;color:var(--text-muted);margin:.25rem 0 0}</style><div class="g">']
    for key in ("build", "wait", "picks", "game"):
        name, icon = head[key]
        parts.append(f'<div><p class="h"><i class="ti {icon}" aria-hidden="true"></i>{name} ({len(cols[key])})</p>')
        if not cols[key]:
            parts.append('<p class="e">Nothing here</p>')
        for c in cols[key]:
            links = "".join(f'<a href="{e(u)}" target="_blank">{e(t)} <i class="ti ti-external-link" aria-hidden="true"></i></a>'
                            for t, u in c["links"])
            parts.append(f'<div class="c"><p class="n">{e(c["num"])}</p><p class="t">{e(c["title"][:70])}</p>'
                         f'<p class="m">{e(c["meta"])}</p>' + (f'<p class="b">{e(c["blend"])}</p>' if c["blend"] else "")
                         + f'<div class="l">{links}</div></div>')
        parts.append("</div>")
    parts.append("</div>")
    if gone:
        parts.append(f'<p class="f">Dropped or replaced: {e("; ".join(gone))}</p>')
    out = "".join(parts)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(out)
    try:
        import sys
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(out)


if __name__ == "__main__":
    main()
