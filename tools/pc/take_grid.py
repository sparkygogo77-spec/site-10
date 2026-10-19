"""The review site in chat: a picture grid of one pass's takes for show_widget, then J rates them with AskUserQuestion.

J (2026-10-19): "I need a direct in chat grid of the same thing as the website essentially because its more important
we cut that gate out of the way". Widget buttons can't send in the Code tab, so the grid only shows; the rating clicks
are AskUserQuestion calls this script writes out for the chat. Default view: SendUserFile NNN.page.html with display
"render" (nothing to retype); show_widget with NNN.html when it must sit inline.

    python tools/pc/take_grid.py grid 609 [--stars stars.json] [--cols 3]
        -> _previews/takegrid/609.html  (paste into show_widget; 208 px base64 stills, ~3 KB each, ~45 KB in all)
           _previews/takegrid/609.page.html  (SendUserFile display "render": 360 px stills, full facts and ★ reasons)
           _previews/takegrid/609.questions.json  (AskUserQuestion calls, 4 takes per call, ★ option first)
    python tools/pc/take_grid.py rate 609 D1b2a=KEEP "D1b2b=IMPROVE:taller dome" D1b3a=DROP [--star-used]
        -> POSTs each to the site's ratings store (/api/reviews, the same rows the site's buttons write), re-pulls
           RATINGS.md + ratings.json, adds one DECISIONS.md line, prints the IMPROVEs for the next round.

Stills: review-site/media/<pass>/<code>.jpg if the site has one, else a frame of the take's 3p (or fp) clip read by
Blender's video reader (decision_stills.py's Blender mode; no ffmpeg on J's PC). Cached in _previews/takegrid/<pass>/.
stars.json: {"D1b2a": {"r": "KEEP", "why": "reads best from 3p"}} from the lantern-checker agent (or the chat's own
look at the stills). Takes without a star get ★ = the current site rating, else IMPROVE.
"""
import base64, datetime, html, io, json, os, subprocess, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))          # site-10
LIVE = os.path.dirname(REPO)                           # LanternLive
SITE_DIR = os.path.join(LIVE, "review-site")
SITE = "https://lantern-review-j.vercel.app"
OUT = os.path.join(LIVE, "_previews", "takegrid")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
STILLS = os.path.join(REPO, "tools", "review_site", "decision_stills.py")
COLOUR = {"KEEP": "#3ccf7a", "IMPROVE": "#e9b949", "DROP": "#e0605a", "": "#7d8a84"}


def site_url():
    """The alias redirects (307) to the branch URL; POSTs must go straight there (urllib won't re-POST)."""
    req = urllib.request.Request(SITE + "/", method="HEAD", headers={"User-Agent": "lantern-take-grid"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.geturl().rstrip("/")


def reviews():
    try:
        req = urllib.request.Request(SITE + "/api/reviews", headers={"Cache-Control": "no-cache", "User-Agent": "lantern-take-grid"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:                                   # offline: the last pull
        try:
            return json.load(open(os.path.join(REPO, "docs", "blender", "review", "ratings.json"), encoding="utf-8"))
        except (OSError, ValueError):
            return {}


def load_pass(key):
    site = json.load(open(os.path.join(SITE_DIR, "data", "site.json"), encoding="utf-8"))
    p = next((x for x in site["passes"] if x["key"] == key), None)
    if not p:
        sys.exit(f"pass {key} is not on the site yet (render it first)")
    spec = {}
    try:
        spec = {t["code"]: t for t in json.load(open(os.path.join(SITE_DIR, "specs", key + ".json"), encoding="utf-8"))["takes"]}
    except (OSError, ValueError, KeyError):
        pass
    return p, spec


def stills(key, takes, spec):
    """One 320-wide JPEG per take in OUT/<key>/<code>.jpg; returns {code: path}."""
    from PIL import Image
    d = os.path.join(OUT, key)
    os.makedirs(d, exist_ok=True)
    jobs, out, raw = [], {}, {}
    for t in takes:
        jpg = os.path.join(d, t["code"] + ".jpg")
        src = os.path.join(SITE_DIR, "media", key, t["code"] + ".jpg")
        clip = t.get("clip3p") or t.get("clipfp")
        clip = os.path.join(SITE_DIR, *clip.split("/")) if clip else None
        newest = max([os.path.getmtime(x) for x in (src, clip) if x and os.path.exists(x)] or [0])
        if os.path.exists(jpg) and os.path.getmtime(jpg) >= newest:
            out[t["code"]] = jpg
        elif os.path.exists(src):
            raw[t["code"]] = src
        elif clip and os.path.exists(clip):
            s = spec.get(t["code"], {})
            frac = t.get("poseFrac") or (s.get("still_frame") / s["frames"][1] if s.get("still_frame") and s.get("frames") else 0.6)
            png = os.path.join(tempfile.gettempdir(), "lr_takegrid", f"{key}_{t['code']}.png")
            os.makedirs(os.path.dirname(png), exist_ok=True)
            jobs.append([clip, min(0.98, frac), png])   # the last frame of a clip can come back black
            raw[t["code"]] = png
    if jobs:
        job = os.path.join(tempfile.gettempdir(), "lr_takegrid", "jobs.json")
        json.dump(jobs, open(job, "w"))
        subprocess.run([BLENDER, "-b", "--factory-startup", "--python", STILLS, "--", job], capture_output=True, text=True)
    for code, src in raw.items():
        if os.path.exists(src):
            im = Image.open(src).convert("RGB")
            im.thumbnail((360, 360))
            jpg = os.path.join(d, code + ".jpg")
            im.save(jpg, quality=72, optimize=True)
            out[code] = jpg
    return out


def data_uri(path, width, quality):
    """The chat retypes the widget, so its stills stay tiny (~2.5 KB at 208 px); the side-panel page gets the 360 px ones."""
    from PIL import Image
    im = Image.open(path)
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def grid(key, stars_file=None, cols=3):
    p, spec = load_pass(key)
    revs = reviews()
    stars = json.load(open(stars_file, encoding="utf-8")) if stars_file else {}
    pics = stills(key, p["takes"], spec)
    star_of, rows = {}, []
    for t in p["takes"]:
        r = revs.get(t["id"], {})
        st = stars.get(t["code"], {})
        star_of[t["code"]] = (st.get("r") or r.get("rating") or "IMPROVE", st.get("why", ""))
        rows.append((t, r.get("rating", ""), r.get("note", "")))
    rated = sum(1 for _, rt, _ in rows if rt)
    sub = (f'{len(rows)} takes · {rated} rated · v{p.get("version", 1)} · {html.escape(p.get("blend") or "")} '
           f'(Menu: open blend {key}) · <a href="{SITE}/#{key}">site ↗</a>')
    TONE = {"KEEP": "success", "IMPROVE": "warning", "DROP": "danger", "": "neutral"}

    def cards(width, quality, page):
        out = []
        for t, rating, note in rows:
            img = (f'<img src="{data_uri(pics[t["code"]], width, quality)}" alt="{html.escape(t["code"])}">'
                   if t["code"] in pics else '<div class="ni">no still yet</div>')
            sr, why = star_of[t["code"]]
            facts = t.get("facts", "") if page else t.get("facts", "").split(". ")[0]
            out.append(f'<div class="c">{img}<div class="b"><span class="rt {TONE[rating]}">{rating or "unrated"}</span>'
                       f'<b>{html.escape(t["code"])}</b> {html.escape(t.get("name", ""))}'
                       f'<div class="f">{html.escape(facts)}</div>'
                       + (f'<div class="n">J: {html.escape(note)}</div>' if note else "")
                       + f'<div class="s">★ {sr}{": " + html.escape(why) if why and page else ""}</div>'
                       f'<a href="{SITE}/#{key}/{t["code"]}">site ↗</a></div></div>')
        return "".join(out)

    css = (".tg{font-size:13px;line-height:1.4;color:var(--text-primary)}.tg .sub{color:var(--text-secondary);margin:0 0 8px}"
           f".tg .g{{display:grid;grid-template-columns:repeat({cols},minmax(0,1fr));gap:8px}}"
           ".tg .c{background:var(--surface-1);border:0.5px solid var(--border);border-radius:12px;overflow:hidden}"
           ".tg img,.tg .ni{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:#0b0d0c;color:#888}"
           ".tg .b{padding:6px 8px 8px}.tg .f{color:var(--text-secondary);font-size:12px}"
           ".tg .n{color:var(--text-warning);font-size:12px}.tg .s{color:var(--text-secondary);font-size:12px}"
           ".tg .rt{float:right;font-size:11px;font-weight:500;border-radius:4px;padding:1px 6px}"
           ".tg .success{background:var(--bg-success);color:var(--text-success)}.tg .warning{background:var(--bg-warning);color:var(--text-warning)}"
           ".tg .danger{background:var(--bg-danger);color:var(--text-danger)}.tg .neutral{background:var(--surface-2);color:var(--text-secondary)}"
           ".tg a{color:var(--text-accent);font-size:12px;text-decoration:none}"
           ".sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}")
    title = html.escape(p.get("title", ""))
    frag = (f'<style>{css}</style><h2 class="sr-only">Pass {key} take grid: {len(rows)} takes with stills, ratings and star picks</h2>'
            f'<div class="tg"><div class="sub">Pass {key}: {title} · {sub}</div><div class="g">{cards(208, 50, False)}</div></div>')
    page = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Pass {key} takes</title><style>:root{{--text-primary:#e8ece9;--text-secondary:#9aa59f;--text-warning:#e9b949;'
            '--text-success:#3ccf7a;--text-danger:#e0605a;--text-accent:#78c8f0;--surface-1:#151917;--surface-2:#222824;'
            '--border:#2a312d;--bg-success:#163d27;--bg-warning:#3d3216;--bg-danger:#3d1a18}'
            f'body{{background:#0e100f;font-family:system-ui,sans-serif;margin:16px}}{css}</style>'
            f'<div class="tg"><h3 style="color:#e8ece9;margin:0">Pass {key}: {title}</h3><div class="sub">{sub}</div>'
            f'<div class="g">{cards(360, 72, True)}</div></div>')
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, f"{key}.html")
    open(hp, "w", encoding="utf-8").write(frag)
    pp = os.path.join(OUT, f"{key}.page.html")
    open(pp, "w", encoding="utf-8").write(page)
    qs = questions(key, p["takes"], star_of)
    qp = os.path.join(OUT, f"{key}.questions.json")
    json.dump(qs, open(qp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{hp}  (show_widget, {len(frag) // 1024} KB, {len(pics)}/{len(p['takes'])} stills)")
    print(f"{pp}  (SendUserFile display render: big stills, full facts)")
    print(f"{qp}  ({len(qs)} AskUserQuestion calls)")


def options(star):
    """J's rule: the ★ pick first, then the other ratings, then "Don't ask, use ★" (= ★ for this and every take after it)."""
    sr, why = star
    desc = {"KEEP": "final, goes on toward the game", "IMPROVE": "next round works on it (notes: Other)",
            "DROP": "safe to remove"}
    opts = [{"label": f"★ {sr} (Recommended)", "description": why or desc[sr]}]
    opts += [{"label": r, "description": desc[r]} for r in ("KEEP", "IMPROVE", "DROP") if r != sr]
    opts.append({"label": "Don't ask, use ★", "description": "★ for this take and every take after it"})
    return opts[:4]


def questions(key, takes, star_of):
    calls = []
    for i in range(0, len(takes), 4):
        qs = []
        for t in takes[i:i + 4]:
            sr, why = star_of[t["code"]]
            qs.append({"question": f"{key} {t['code']} {t.get('name', '')}: rating? (notes: Other)",
                       "header": t["code"][:12], "multiSelect": False, "options": options((sr, why))})
        calls.append({"questions": qs})
    return calls


def post(base, rid, rating, note):
    body = {"id": rid, "rating": rating}
    if note:
        body["note"] = note
    req = urllib.request.Request(base + "/api/reviews", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "lantern-take-grid"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def rate(key, pairs, star_used=False):
    p, _ = load_pass(key)
    names = {t["code"]: t.get("name", "") for t in p["takes"]}
    base = site_url()
    done, improve = [], []
    for pair in pairs:
        code, _, rest = pair.partition("=")
        rating, _, note = rest.partition(":")
        rating = rating.strip().upper()
        if code not in names or rating not in ("KEEP", "IMPROVE", "DROP"):
            sys.exit(f"bad rating {pair!r} (want CODE=KEEP|IMPROVE|DROP[:note], codes {', '.join(names)})")
        res = post(base, f"{key}_{code}", rating, note.strip())
        if not res.get("ok"):
            sys.exit(f"site refused {pair}: {res}")
        done.append(f"{code} {rating}" + (f" ({note.strip()})" if note.strip() else ""))
        if rating == "IMPROVE":
            improve.append(f"{code} {names[code]}" + (f": {note.strip()}" if note.strip() else ""))
    subprocess.run([sys.executable, os.path.join(REPO, "tools", "review_site", "pull_reviews.py")], cwd=REPO)
    log = os.path.join(REPO, "docs", "blender", "review", "DECISIONS.md")
    text = open(log, encoding="utf-8").read()
    head = "## Ratings from the in-chat take grid (PC chats, tools/pc/take_grid.py)"
    line = (f"- **{datetime.date.today()} {key}:** J rated in chat: {'; '.join(done)}"
            + (" (★ picks, J: \"Don't ask, use ★\")" if star_used else "") + ". Saved to the site's ratings.")
    if head in text:
        text = text.replace(head + "\n\n", head + "\n\n" + line + "\n", 1)
    else:
        first = text.index("\n## ")
        text = text[:first] + f"\n{head}\n\n{line}\n" + text[first:]
    open(log, "w", encoding="utf-8").write(text)
    print("saved:", "; ".join(done))
    print("next round (IMPROVE):", "; ".join(improve) or "none")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "grid":
        stars = a[a.index("--stars") + 1] if "--stars" in a else None
        cols = int(a[a.index("--cols") + 1]) if "--cols" in a else 3
        grid(a[1], stars, cols)
    elif len(a) >= 3 and a[0] == "rate":
        rate(a[1], [x for x in a[2:] if x != "--star-used"], "--star-used" in a)
    else:
        sys.exit(__doc__)
