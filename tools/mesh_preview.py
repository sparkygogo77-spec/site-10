"""Renders a mesh lantern (mesh_kit JSON) from the nine angles of J's concept sheets, beside the
sheet, so each pass can be checked against it without the game or a browser.

    python tools/mesh_preview.py <model.json> <out.png> [sheet.png] [--size 300]
"""
import base64, io, json, math, sys
import numpy as np
from PIL import Image, ImageDraw

VIEWS = [("FRONT", 0, 6), ("BACK", 180, 6), ("TOP", 0, 89), ("LEFT", 90, 6), ("RIGHT", -90, 6),
         ("BOTTOM", 0, -89), ("FRONT LEFT", 40, 12), ("FRONT RIGHT", -40, 12), ("BACK RIGHT", -140, 12)]
BASE = {"stone": (1.0, 1.0, 1.0), "bronze": (0.66, 0.43, 0.23)}
UNLIT = {"emblem", "lens", "gem", "star", "runes"}


def load(path):
    d = json.load(open(path))
    tex = {}
    for k, v in d["textures"].items():
        tex[k] = np.asarray(Image.open(io.BytesIO(base64.b64decode(v.split(",")[1]))).convert("RGB"), float) / 255
    return d["parts"], tex


def render(parts, tex, yaw, pitch, size, bbox):
    lo, hi = bbox
    ctr = (lo + hi) / 2
    ext = np.linalg.norm(hi - lo) * 0.52
    y, p = math.radians(yaw), math.radians(pitch)
    # camera looks at the model's front (-z) when yaw = 0
    fwd = np.array([-math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p)])
    right = np.cross([0, 1, 0], fwd)
    right = right / (np.linalg.norm(right) or 1) if abs(p) < math.radians(85) else np.array([math.cos(y), 0, math.sin(y)])
    up = np.cross(fwd, right)
    img = np.full((size, size, 3), 0.78)
    zb = np.full((size, size), np.inf)
    L = np.array([-0.35, 0.75, -0.55])
    L /= np.linalg.norm(L)
    for part in parts:
        P = np.array(part["pos"]).reshape(-1, 3) - ctr
        N = np.array(part["nrm"]).reshape(-1, 3)
        UV = np.array(part["uv"]).reshape(-1, 2)
        C = np.array(part["col"]).reshape(-1, 3)
        I = np.array(part["idx"]).reshape(-1, 3)
        sx = (P @ right / ext * 0.5 + 0.5) * size
        sy = (0.5 - P @ up / ext * 0.5) * size
        sz = P @ fwd
        mat = part["mat"]
        t = tex.get(mat) if mat not in ("stone",) else tex.get("stone")
        for a, b, c in I:
            xs, ys = (sx[a], sx[b], sx[c]), (sy[a], sy[b], sy[c])
            area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
            if abs(area) < 1e-9:
                continue
            x0, x1 = max(int(min(xs)), 0), min(int(max(xs)) + 1, size)
            y0, y1 = max(int(min(ys)), 0), min(int(max(ys)) + 1, size)
            if x0 >= x1 or y0 >= y1:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            w0 = ((xs[1] - gx) * (ys[2] - gy) - (xs[2] - gx) * (ys[1] - gy)) / area
            w1 = ((xs[2] - gx) * (ys[0] - gy) - (xs[0] - gx) * (ys[2] - gy)) / area
            w2 = 1 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            z = w0 * sz[a] + w1 * sz[b] + w2 * sz[c]
            sub = zb[y0:y1, x0:x1]
            vis = inside & (z < sub)
            if not vis.any():
                continue
            sub[vis] = z[vis]
            n = (w0[..., None] * N[a] + w1[..., None] * N[b] + w2[..., None] * N[c])[vis]
            n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
            col = (w0[..., None] * C[a] + w1[..., None] * C[b] + w2[..., None] * C[c])[vis]
            if t is not None and mat in ("stone", "emblem", "captop", "star", "runes"):
                uv = (w0[..., None] * UV[a] + w1[..., None] * UV[b] + w2[..., None] * UV[c])[vis]
                th, tw = t.shape[:2]
                if mat == "stone":
                    tu = (uv[:, 0] % 1) * (tw - 1)
                    tv = (uv[:, 1] % 1) * (th - 1)
                else:
                    tu = np.clip(uv[:, 0], 0, 1) * (tw - 1)
                    tv = (1 - np.clip(uv[:, 1], 0, 1)) * (th - 1)
                base = t[tv.astype(int), tu.astype(int)]
                col = base * (col if mat == "stone" else 1)
            else:
                col = col * np.array(BASE.get(mat, (1, 1, 1)))
            if mat not in UNLIT:
                diff = np.clip(n @ L, 0, 1)[:, None]
                spec = 0.0
                if mat in ("bronze", "captop"):
                    h = L - fwd
                    h /= np.linalg.norm(h)
                    spec = (np.clip(n @ h, 0, 1) ** 30)[:, None] * 0.6
                col = col * (0.42 + 0.75 * diff) + spec
            img[y0:y1, x0:x1][vis] = np.clip(col, 0, 1)
    return img


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    size = 300
    if "--size" in sys.argv:
        size = int(sys.argv[sys.argv.index("--size") + 1])
        args = [a for a in args if a != str(size)]
    parts, tex = load(args[0])
    allp = np.concatenate([np.array(p["pos"]).reshape(-1, 3) for p in parts])
    bbox = (allp.min(0), allp.max(0))
    tiles = []
    for label, yaw, pitch in VIEWS:
        im = Image.fromarray((render(parts, tex, yaw, pitch, size, bbox) * 255).astype(np.uint8))
        ImageDraw.Draw(im).text((6, 4), label, fill=(0, 0, 0))
        tiles.append(im)
    grid = Image.new("RGB", (size * 3, size * 3))
    for i, t in enumerate(tiles):
        grid.paste(t, ((i % 3) * size, (i // 3) * size))
    if len(args) > 2:
        sheet = Image.open(args[2]).convert("RGB")
        sheet = sheet.resize((int(sheet.width * size * 3 / sheet.height), size * 3))
        both = Image.new("RGB", (sheet.width + grid.width, size * 3))
        both.paste(sheet, (0, 0))
        both.paste(grid, (sheet.width, 0))
        grid = both
    grid.save(args[1])


main()
