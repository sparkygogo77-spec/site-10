"""Renders a Blockbench model from the same nine angles as J's concept sheets, without the game.

    python tools/bbmodel_preview.py <model name> <out.png> [sheet.png] [--size 300]

Draws the .bbmodel in assets/lanternring/bbmodel/ the way the mod does (box UV laid out like
ModelPart, cube rotations as Blockbench's Z*Y*X Euler angles about the cube's origin, cut-out
texels, "glow"/"core"/"glass" cubes full-bright) with soft Minecraft-style entity lighting, in
the sheet's views: FRONT, BACK, TOP / LEFT, RIGHT, BOTTOM / FRONT LEFT, FRONT RIGHT, BACK RIGHT.
With a sheet image it puts the sheet on the left and the renders on the right, so the two can
be compared side by side while a lantern is being built.
"""
import base64, io, json, math, sys
import numpy as np
from PIL import Image, ImageDraw

A = "src/main/resources/assets/lanternring"

# Views: (label, yaw degrees round the model, starting at the front; elevation degrees).
VIEWS = [("FRONT", 0, 8), ("BACK", 180, 8), ("TOP", 0, 89),
         ("LEFT", 90, 8), ("RIGHT", -90, 8), ("BOTTOM", 0, -89),
         ("FRONT LEFT", 40, 14), ("FRONT RIGHT", -40, 14), ("BACK RIGHT", -140, 14)]


def rot_matrix(r):
    """Blockbench's cube rotation: X first, then Y, then Z (degrees)."""
    x, y, z = (math.radians(a) for a in r)
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rz @ ry @ rx


def face_corner(frm, to, face, a, b):
    """The model point at (a, b) across a face's UV rect (0..1 each), as ModelPart lays box UV
    once BbModel has turned the model about Z (the same mapping as blockbench_models._texel)."""
    (x0, y0, z0), (x1, y1, z1) = frm, to
    return {
        "north": (x1 - a * (x1 - x0), y1 - b * (y1 - y0), z0),
        "south": (x0 + a * (x1 - x0), y1 - b * (y1 - y0), z1),
        "east": (x1, y1 - b * (y1 - y0), z1 - a * (z1 - z0)),
        "west": (x0, y1 - b * (y1 - y0), z0 + a * (z1 - z0)),
        "up": (x1 - a * (x1 - x0), y1, z1 - b * (z1 - z0)),
        "down": (x1 - a * (x1 - x0), y0, z1 - b * (z1 - z0)),
    }[face]


NORMALS = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0),
           "up": (0, 1, 0), "down": (0, -1, 0)}


def load(name):
    with open(f"{A}/bbmodel/{name}.bbmodel") as f:
        bb = json.load(f)
    src = bb["textures"][0].get("source", "")
    # optimize_jar_assets.py strips the embedded copy: fall back to the texture the mod loads
    im = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1]))) if src.startswith("data:") \
        else Image.open(f"{A}/textures/entity/bb/{name}.png")
    tex = np.asarray(im.convert("RGBA")).astype(np.float32)
    return bb, tex


def samples(bb, tex, step):
    """Every visible texel sample of the model: positions, normals, colours, glow flags."""
    uw, uh = bb["resolution"]["width"], bb["resolution"]["height"]
    th, tw = tex.shape[:2]
    kx, ky = tw / uw, th / uh
    P, N, C, G = [], [], [], []
    for el in bb["elements"]:
        if el.get("type", "cube") != "cube" or el.get("visibility") is False:
            continue
        inf = el.get("inflate", 0) or 0
        frm = [v - inf for v in el["from"]]
        to = [v + inf for v in el["to"]]
        R = rot_matrix(el.get("rotation") or [0, 0, 0])
        o = np.array(el.get("origin") or [0, 0, 0], dtype=float)
        glow = el["name"].startswith(("glow", "core", "glass"))
        for face, f in el["faces"].items():
            u0, v0, u1, v1 = f["uv"]
            if u1 == u0 or v1 == v0:
                continue
            p00 = np.array(face_corner(frm, to, face, 0, 0))
            p10 = np.array(face_corner(frm, to, face, 1, 0))
            p01 = np.array(face_corner(frm, to, face, 0, 1))
            ea, eb = p10 - p00, p01 - p00
            if np.linalg.norm(ea) < 1e-6 or np.linalg.norm(eb) < 1e-6:
                continue
            na = max(2, int(math.ceil(np.linalg.norm(ea) / step)))
            nb = max(2, int(math.ceil(np.linalg.norm(eb) / step)))
            a = (np.arange(na) + 0.5) / na
            b = (np.arange(nb) + 0.5) / nb
            A2, B2 = np.meshgrid(a, b)
            A2, B2 = A2.ravel(), B2.ravel()
            tx = np.clip(((u0 + A2 * (u1 - u0)) * kx).astype(int), 0, tw - 1)
            ty = np.clip(((v0 + B2 * (v1 - v0)) * ky).astype(int), 0, th - 1)
            col = tex[ty, tx]
            keep = col[:, 3] > 127
            if not keep.any():
                continue
            pts = p00 + A2[:, None] * ea + B2[:, None] * eb
            pts = (pts - o) @ R.T + o
            n = R @ np.array(NORMALS[face], dtype=float)
            P.append(pts[keep])
            N.append(np.repeat(n[None], keep.sum(), 0))
            C.append(col[keep, :3])
            G.append(np.full(keep.sum(), glow))
    return np.concatenate(P), np.concatenate(N), np.concatenate(C), np.concatenate(G)


def render(P, N, C, G, yaw, pitch, size, bounds):
    """Orthographic view: yaw turns the camera round the model from the front (+ toward its left
    side), pitch looks down from above."""
    y, p = math.radians(yaw), math.radians(pitch)
    # The camera looks along d (into the scene); at yaw 0 it stands north of the model (-Z).
    d = np.array([-math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p)])
    up0 = np.array([0, 1, 0]) if abs(pitch) < 80 else np.array([0, 0, 1 if pitch > 0 else -1])
    r = np.cross(d, up0)
    r /= np.linalg.norm(r)
    u = np.cross(r, d)
    centre, extent = bounds
    s = size * 0.9 / extent
    ss = 2  # supersample
    S = size * ss
    sx = ((P - centre) @ r * s * ss + S / 2).astype(int)
    sy = (S / 2 - (P - centre) @ u * s * ss).astype(int)
    depth = (P - centre) @ d
    facing = (N @ d) < 0.05
    ok = facing & (sx >= 0) & (sx < S) & (sy >= 0) & (sy < S)
    sx, sy, depth, Nn, Cc, Gg = sx[ok], sy[ok], depth[ok], N[ok], C[ok], G[ok]
    # Minecraft entity lighting: two lights from above, ambient 0.4.
    L0 = np.array([0.2, 1.0, -0.7]); L0 /= np.linalg.norm(L0)
    L1 = np.array([-0.2, 1.0, 0.7]); L1 /= np.linalg.norm(L1)
    lum = np.minimum(1.0, 0.4 + 0.6 * (np.maximum(0, Nn @ L0) + np.maximum(0, Nn @ L1)))
    lum = np.where(Gg, 1.0, lum)
    col = np.clip(Cc * lum[:, None], 0, 255)
    order = np.argsort(-depth)  # far first, near last wins
    img = np.full((S, S, 3), 200, dtype=np.float32)
    img[sy[order], sx[order]] = col[order]
    im = Image.fromarray(img.astype(np.uint8))
    return im.resize((size, size), Image.LANCZOS)


def sheet(name, out, ref=None, size=300):
    bb, tex = load(name)
    P, N, C, G = samples(bb, tex, step=0.5 / (size * 0.9 / 24) / 2)
    lo, hi = P.min(0), P.max(0)
    centre = (lo + hi) / 2
    extent = float(np.linalg.norm(hi - lo)) * 0.82
    grid = Image.new("RGB", (size * 3, size * 3), (200, 200, 200))
    dr = ImageDraw.Draw(grid)
    for i, (label, yaw, pitch) in enumerate(VIEWS):
        im = render(P, N, C, G, yaw, pitch, size, (centre, extent))
        grid.paste(im, ((i % 3) * size, (i // 3) * size))
        dr.text(((i % 3) * size + 6, (i // 3) * size + 4), label, fill=(0, 0, 0))
    if ref:
        r = Image.open(ref).convert("RGB")
        r = r.resize((int(r.width * grid.height / r.height), grid.height))
        both = Image.new("RGB", (r.width + grid.width, grid.height))
        both.paste(r, (0, 0))
        both.paste(grid, (r.width, 0))
        grid = both
    grid.save(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    size = 300
    if "--size" in args:
        i = args.index("--size")
        size = int(args[i + 1])
        del args[i:i + 2]
    sheet(args[0], args[1], args[2] if len(args) > 2 else None, size)
