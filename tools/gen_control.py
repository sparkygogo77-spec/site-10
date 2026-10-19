"""Build data/control.json for the review site's Control tab: what J taps to run the PC chat.

    python3 gen_control.py [SITE_DIR]          # after gen_status.py --fetch (it fetches origin/dev and origin/main)

Reads, from git refs in SITE_DIR (a clone of site-10 whose `review-site` branch is the site):
    origin/dev   docs/blender/review/INBOX.md (WAITING passes), docs/texture_library, docs/library/pc_files.json,
                 docs/handoff/DESKTOP-KICKOFF.md and NEW-CHAT-PROMPT.md (the prompts the page copies)
    origin/main  src/main/resources/assets/lanternring/bbmodel/*.bbmodel and their textures (the jar models)
and, on J's PC, the .blend files in LanternLive\\<area>\\ (the folder above SITE_DIR); elsewhere pc_files.json.

Writes data/control.json and small pictures in data/control/: jar models drawn as a shaded three-quarter view
(j_<name>.png, from the model's cubes and the average colour of each face's texture) and the first frame of each
library texture (t_<name>_<colour>.png). Pictures are only redrawn when their source changes (blob ids in
control.json), so a render run adds no new files unless a model or texture changed. Pure Python: no Pillow needed.
"""
import json, math, os, re, struct, subprocess, sys, time, zlib

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SITE = os.path.abspath(ARGS[0] if ARGS else "/home/claude/review-site")
LIVE = os.environ.get("LANTERN_LIVE", os.path.dirname(SITE))
OUT = os.path.join(SITE, "data", "control")
ASSETS = "src/main/resources/assets/lanternring/"
AREAS = ["lanterns", "movement", "combat", "constructs", "red", "suit"]
JAR_GROUPS = [            # first match wins (same as tools/gen_asset_library.py)
    ("Lanterns and batteries", r"lantern|battery|port|nebula|lava_font"),
    ("Rings and the forge", r"ring|crest|crown|forge|gauntlet|stone"),
    ("Construct tools and weapons", r"construct_|blast_drill|fear_nuke"),
    ("Mobs, mounts and armour", r"armour|ravager|hawk|runner|golem|bull"),
]
CORPS = {"green": (47, 214, 127), "blue": (80, 150, 255), "red": (235, 60, 60), "crimson": (220, 40, 70),
         "orange": (255, 150, 40), "yellow": (250, 215, 60), "violet": (170, 90, 240), "dark": (120, 140, 130)}


def git(*a, binary=False):
    r = subprocess.run(["git", "-C", SITE] + list(a), capture_output=True)
    if r.returncode:
        return b"" if binary else ""
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def tree(ref, path):
    """{path: blob id} for every file under path at ref."""
    out = {}
    for line in git("ls-tree", "-r", ref, path).splitlines():
        meta, _, p = line.partition("\t")
        out[p] = meta.split()[2]
    return out


# ---------------------------------------------------------------- PNG in and out, without Pillow
def png_read(data, max_rows=None):
    """(width, height, rows of RGBA tuples) for 8-bit non-interlaced PNGs; None for anything else."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    i, idat, plte, trns = 8, [], None, None
    while i < len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8]); body = data[i + 8:i + 8 + n]; i += 12 + n
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, lace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            plte = [tuple(body[j:j + 3]) for j in range(0, len(body), 3)]
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
    if depth != 8 or lace or ctype not in (0, 2, 3, 4, 6):
        return None
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride, rows_wanted = w * bpp, min(h, max_rows or h)
    raw, z, need = bytearray(), zlib.decompressobj(), rows_wanted * (w * bpp + 1)
    for chunk in idat:                       # only inflate as far as the rows we want (texture strips are tall)
        raw += z.decompress(chunk, need - len(raw))
        if len(raw) >= need:
            break
    prev, rows = bytearray(stride), []
    for y in range(rows_wanted):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b, c = prev[x], (prev[x - bpp] if x >= bpp else 0)
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        px = []
        for x in range(w):
            v = line[x * bpp:(x + 1) * bpp]
            if ctype == 6: px.append(tuple(v))
            elif ctype == 2: px.append((v[0], v[1], v[2], 255))
            elif ctype == 0: px.append((v[0], v[0], v[0], 255))
            elif ctype == 4: px.append((v[0], v[0], v[0], v[1]))
            else: px.append(plte[v[0]] + ((trns[v[0]] if trns and v[0] < len(trns) else 255),))
        rows.append(px)
    return w, h, rows


def png_write(path, w, h, rgba):
    """rgba: flat bytearray, 4 bytes a pixel."""
    raw = b"".join(b"\0" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    chunk = lambda k, d: struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d) & 0xffffffff)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def shrink(w, h, rows, size):
    """Box-filter a square crop of rows down to size x size (nearest when it's already small: pixel art)."""
    s = min(w, len(rows))
    out = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            if s <= size:
                px = rows[y * s // size][x * s // size]
            else:
                y0, y1, x0, x1 = y * s // size, (y + 1) * s // size, x * s // size, (x + 1) * s // size
                acc, n = [0, 0, 0, 0], 0
                for yy in range(y0, y1):
                    for p in rows[yy][x0:x1]:
                        acc[0] += p[0]; acc[1] += p[1]; acc[2] += p[2]; acc[3] += p[3]; n += 1
                px = [v // n for v in acc]
            out[(y * size + x) * 4:(y * size + x) * 4 + 4] = bytes(px)
    return out


# ---------------------------------------------------------------- a jar model as a small picture
W, H, SS = 160, 120, 2                     # picture size; drawn at 2x and shrunk for smooth edges
YAW, PITCH = math.radians(-35), math.radians(28)
LIGHT = (-0.45, 0.75, -0.5)


def rot(p, rx, ry, rz):
    x, y, z = p
    if rx: c, s = math.cos(rx), math.sin(rx); y, z = y * c - z * s, y * s + z * c
    if ry: c, s = math.cos(ry), math.sin(ry); x, z = x * c + z * s, -x * s + z * c
    if rz: c, s = math.cos(rz), math.sin(rz); x, y = x * c - y * s, x * s + y * c
    return x, y, z


def view(p):
    """World (front at -z) to camera: the viewer stands front-right and a little above."""
    x, y, z = rot(p, 0, YAW, 0)
    return rot((x, y, z), -PITCH, 0, 0)


CUBE_FACES = {  # corner indices (bit 0 = x max, bit 1 = y max, bit 2 = z max) and normal
    "north": ((0, 2, 3, 1), (0, 0, -1)), "south": ((4, 5, 7, 6), (0, 0, 1)),
    "west": ((0, 4, 6, 2), (-1, 0, 0)), "east": ((1, 3, 7, 5), (1, 0, 0)),
    "down": ((0, 1, 5, 4), (0, -1, 0)), "up": ((2, 6, 7, 3), (0, 1, 0)),
}


def face_colour(face, textures, res):
    tex = textures.get(face.get("texture"))
    uv = face.get("uv")
    if not tex or not uv:
        return None
    tw, th, rows = tex
    sx, sy = tw / res[0], th / res[1]
    x0, x1 = sorted((int(uv[0] * sx), int(math.ceil(uv[2] * sx))))
    y0, y1 = sorted((int(uv[1] * sy), int(math.ceil(uv[3] * sy))))
    acc, n = [0, 0, 0], 0
    for y in range(max(0, y0), min(th, max(y1, y0 + 1))):
        for p in rows[y][max(0, x0):min(tw, max(x1, x0 + 1))]:
            if p[3] > 24:
                acc[0] += p[0]; acc[1] += p[1]; acc[2] += p[2]; n += 1
    return tuple(v // n for v in acc) if n else None


def draw_model(bb, textures, tint):
    res = (bb.get("resolution") or {}).get("width", 16), (bb.get("resolution") or {}).get("height", 16)
    quads = []
    for e in bb.get("elements", []):
        if e.get("type", "cube") != "cube" or e.get("visibility") is False or "from" not in e:
            continue
        inf = e.get("inflate", 0) or 0
        f, t = [v - inf for v in e["from"]], [v + inf for v in e["to"]]
        o, r = e.get("origin", [0, 0, 0]), [math.radians(v) for v in e.get("rotation", [0, 0, 0])]
        corners = []
        for i in range(8):
            p = (t[0] if i & 1 else f[0], t[1] if i & 2 else f[1], t[2] if i & 4 else f[2])
            if any(r):
                p = rot((p[0] - o[0], p[1] - o[1], p[2] - o[2]), *r); p = (p[0] + o[0], p[1] + o[1], p[2] + o[2])
            corners.append(view(p))
        for name, (idx, n) in CUBE_FACES.items():
            face = (e.get("faces") or {}).get(name)
            if face is None or face.get("texture") is None:
                continue
            col = face_colour(face, textures, res) if textures else None
            if textures and col is None:
                continue                      # a see-through face (cutouts, glass edges)
            nw = rot(n, *r) if any(r) else n
            nv = view(nw)
            if nv[2] > 0.02:                  # facing away from the viewer
                continue
            lit = 0.5 + 0.5 * max(0.0, sum(a * b for a, b in zip(nw, LIGHT)) / math.sqrt(sum(v * v for v in LIGHT)))
            base = col or tint
            quads.append(([corners[i] for i in idx], tuple(min(255, int(c * lit)) for c in base)))
    if not quads:
        return None
    xs = [p[0] for q, _ in quads for p in q]; ys = [p[1] for q, _ in quads for p in q]
    span = max(max(xs) - min(xs), (max(ys) - min(ys)) * W / H) or 1
    sc, cx, cy = 0.86 * W * SS / span, (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    BW, BH = W * SS, H * SS
    zbuf, img = [1e9] * (BW * BH), bytearray(BW * BH * 4)
    for q, col in quads:
        P = [(BW / 2 + (p[0] - cx) * sc, BH / 2 - (p[1] - cy) * sc, p[2]) for p in q]
        for a, b, c in ((P[0], P[1], P[2]), (P[0], P[2], P[3])):
            area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(area) < 1e-9:
                continue
            for y in range(max(0, int(min(a[1], b[1], c[1]))), min(BH, int(max(a[1], b[1], c[1])) + 1)):
                py = y + 0.5
                for x in range(max(0, int(min(a[0], b[0], c[0]))), min(BW, int(max(a[0], b[0], c[0])) + 1)):
                    px = x + 0.5
                    w0 = ((b[0] - px) * (c[1] - py) - (b[1] - py) * (c[0] - px)) / area
                    w1 = ((c[0] - px) * (a[1] - py) - (c[1] - py) * (a[0] - px)) / area
                    w2 = 1 - w0 - w1
                    if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                        continue
                    z = w0 * a[2] + w1 * b[2] + w2 * c[2]
                    k = y * BW + x
                    if z < zbuf[k]:
                        zbuf[k] = z; img[k * 4:k * 4 + 4] = bytes((*col, 255))
    out = bytearray(W * H * 4)               # 2x2 average, keeping see-through edges soft
    for y in range(H):
        for x in range(W):
            acc = [0, 0, 0, 0]
            for dy in range(SS):
                for dx in range(SS):
                    k = ((y * SS + dy) * BW + x * SS + dx) * 4
                    a = img[k + 3]
                    acc[0] += img[k] * a; acc[1] += img[k + 1] * a; acc[2] += img[k + 2] * a; acc[3] += a
            a = acc[3]
            out[(y * W + x) * 4:(y * W + x) * 4 + 4] = bytes((acc[0] // a, acc[1] // a, acc[2] // a, a // (SS * SS)) if a else (0, 0, 0, 0))
    return out


def jar_models(old):
    bbs = tree("origin/main", ASSETS + "bbmodel/")
    texs = {}
    for p, blob in tree("origin/main", ASSETS + "textures/").items():
        texs.setdefault(os.path.basename(p), (p, blob))
    catalogue = set()
    try:
        catalogue = {m["id"] for m in json.load(open(os.path.join(SITE, "catalogue", "index.json")))["models"]}
    except Exception:
        pass
    seen, out = {e["id"]: e for e in old.get("jar", [])}, []
    for path, blob in sorted(bbs.items()):
        if not path.endswith(".bbmodel"):
            continue
        name = os.path.basename(path)[:-8]
        group = next((g for g, rx in JAR_GROUPS if re.search(rx, name)), "Other")
        tint = next((v for k, v in CORPS.items() if k in name), CORPS["green"])
        img, rel = f"j_{name}.png", f"data/control/j_{name}.png"
        prev = seen.get(name, {})
        entry = {"id": f"J:{name}", "name": name.replace("_", " "), "group": group,
                 "catalogue": name in catalogue, "src": blob, "img": prev.get("img")}
        if prev.get("src") != blob or not prev.get("img") or not os.path.exists(os.path.join(SITE, rel)):
            entry["img"] = None
            try:
                bb = json.loads(git("show", f"{blob}"))
                textures = {}
                for i, t in enumerate(bb.get("textures", [])):
                    tname = os.path.basename(t.get("name") or t.get("path") or "")
                    if not tname.endswith(".png"):
                        tname += ".png"
                    src = None
                    if (t.get("source") or "").startswith("data:image/png;base64,"):
                        import base64
                        src = base64.b64decode(t["source"].split(",", 1)[1])
                    elif tname in texs:
                        src = git("show", texs[tname][1], binary=True)
                    dec = png_read(src) if src else None
                    if dec:
                        textures[i] = textures[t.get("id", i)] = dec
                pic = draw_model(bb, textures, tint)
                if pic:
                    png_write(os.path.join(OUT, img), W, H, pic); entry["img"] = rel
            except Exception as e:
                print(f"  ({name}: no picture, {e})")
        out.append(entry)
    return out


def textures(old):
    seen, out = {e["id"]: e for e in old.get("textures", [])}, []
    by = {}
    for p, blob in tree("origin/dev", "docs/texture_library/").items():
        m = re.match(r"docs/texture_library/([^/]+)/([^/]+)/construct_\2_\1\.png$", p)
        if m:
            by.setdefault(m.group(2), {})[m.group(1)] = blob
    for name in sorted(by):
        colours = by[name]
        first = "green" if "green" in colours else sorted(colours)[0]
        tid = f"T:{name}"
        prev, rel = seen.get(tid, {}), f"data/control/t_{name}.png"
        entry = {"id": tid, "name": name, "colours": sorted(colours), "colour": first, "src": colours[first], "img": prev.get("img")}
        if prev.get("src") != colours[first] or not prev.get("img") or not os.path.exists(os.path.join(SITE, rel)):
            entry["img"] = None
            try:
                data = git("show", colours[first], binary=True)
                w = struct.unpack(">I", data[16:20])[0]
                dec = png_read(data, max_rows=w)           # the first square frame of the strip
                if dec:
                    png_write(os.path.join(OUT, f"t_{name}.png"), 96, 96, shrink(dec[0], dec[1], dec[2], 96)); entry["img"] = rel
            except Exception as e:
                print(f"  ({name}: no picture, {e})")
        out.append(entry)
    return out


# ---------------------------------------------------------------- passes, .blend files, prompts
def waiting(site):
    inbox = git("show", "origin/dev:docs/blender/review/INBOX.md")
    entries = re.findall(r"^## (\d{4}-\d\d-\d\d) pass (\d+)(?: rev \d+| update)?: (.+?)\s+\[(?:status: )?([A-Z ]+?)(?:[:\]])", inbox, re.M)
    titles = [(n, t) for _, n, t, _ in entries] + [(p["pass"], p["title"]) for p in site.get("passes", [])]
    out, done = [], set()
    for date, num, title, status in entries:
        if status.strip() != "WAITING" or num in done:
            continue
        done.add(num)
        # passes that build on this one name it in their title ("round 2 (860 G1, G2 variations)")
        refs = sorted({n for n, t in titles if n != num and re.search(rf"\b{num}\b", t)})
        out.append({"pass": num, "date": date, "title": title, "builtOnBy": refs})
    return out


def blends(site):
    by_blend = {}
    for p in site.get("passes", []):
        if p.get("blend"):
            by_blend.setdefault(p["blend"].replace("\\", "/"), p["key"])
    rows = []
    if os.path.isdir(os.path.join(LIVE, "movement")):          # on J's PC: read the folders themselves
        for area in AREAS:
            d = os.path.join(LIVE, area)
            for f in os.listdir(d) if os.path.isdir(d) else []:
                if f.endswith(".blend"):
                    st = os.stat(os.path.join(d, f))
                    rows.append((st.st_mtime, area, f[:-6], round(st.st_size / 1e6, 1)))
    else:
        try:
            pc = json.loads(git("show", "origin/dev:docs/library/pc_files.json"))
            for area, files in pc.get("areas", {}).items():
                for f in files:
                    rows.append((time.mktime(time.strptime(f["date"], "%Y-%m-%d")), area, f["name"], f.get("mb")))
        except Exception:
            pass
    rows.sort(reverse=True)
    return [{"id": f"F:{a}/{n}", "name": n.replace("_", " "), "area": a, "mb": mb,
             "date": time.strftime("%Y-%m-%d", time.localtime(t)), "pass": by_blend.get(f"{a}/{n}.blend")}
            for t, a, n, mb in rows[:36]]


def fenced(path):
    m = re.search(r"```\n(.*?)\n```", git("show", f"origin/dev:{path}"), re.S)
    return m.group(1) if m else ""


def main():
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(SITE, "data", "control.json")
    try:
        old = json.load(open(dest, encoding="utf-8"))
    except Exception:
        old = {}
    try:
        site = json.load(open(os.path.join(SITE, "data", "site.json"), encoding="utf-8"))
    except Exception:
        site = {}
    data = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "waiting": waiting(site),
        "jar": jar_models(old),
        "blends": blends(site),
        "textures": textures(old),
        "prompts": {"kickoff": fenced("docs/handoff/DESKTOP-KICKOFF.md"), "thread": fenced("docs/handoff/NEW-CHAT-PROMPT.md"),
                    "closeOut": "Menu: close out"},
    }
    json.dump(data, open(dest, "w", encoding="utf-8"), indent=1)
    print(f"  control.json: {len(data['waiting'])} waiting, {len(data['jar'])} jar models "
          f"({sum(1 for j in data['jar'] if j['img'])} pictures), {len(data['blends'])} .blend files, {len(data['textures'])} textures")
    dec = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_decisions.py")
    if os.path.exists(dec):     # the Decisions cards (decision manager) refresh with the same render run
        subprocess.run([sys.executable, dec, SITE], check=False)


if __name__ == "__main__":
    main()
