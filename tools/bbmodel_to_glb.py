"""Converts the mod's Blockbench models (assets/lanternring/bbmodel/*.bbmodel) into .glb files Blender
can import, with their own textures (nearest-pixel) and their glow cubes ("glow..." / "core...") in a
separate "<name>_glow" material, so Blender can light them like the game does. 1 unit = 1 block.

    python tools/bbmodel_to_glb.py OUTDIR [names...]
"""
import base64, io, json, math, os, sys
import numpy as np
import trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src", "main", "resources", "assets", "lanternring", "bbmodel")


def corners(f, t, face):
    x0, y0, z0 = f
    x1, y1, z1 = t
    return {
        "north": [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
        "south": [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
        "east": [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
        "west": [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
        "up": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        "down": [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
    }[face]


def rot_matrix(r):
    rx, ry, rz = (math.radians(a) for a in r)
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def textures(d, name):
    out = []
    for i, t in enumerate(d.get("textures", [])):
        src = t.get("source", "")
        if src.startswith("data:"):
            im = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1]))).convert("RGBA")
        else:
            png = os.path.join(SRC, "..", "textures", "entity", "bb", name + ".png")
            im = Image.open(png).convert("RGBA")
        out.append(im)
    if not out:
        out.append(Image.open(os.path.join(SRC, "..", "textures", "entity", "bb", name + ".png")).convert("RGBA"))
    return out


def convert(name, outdir):
    d = json.load(open(os.path.join(SRC, name + ".bbmodel")))
    res = d.get("resolution", {"width": 16, "height": 16})
    rw, rh = res["width"], res["height"]
    texs = textures(d, name)
    groups = {}                      # (texture, glow) -> (verts, uvs)
    for e in d["elements"]:
        if e.get("type", "cube") != "cube" or e.get("visibility") is False:
            continue
        inf = e.get("inflate", 0)
        f = np.array(e["from"], float) - inf
        t = np.array(e["to"], float) + inf
        R = rot_matrix(e.get("rotation", [0, 0, 0]))
        o = np.array(e.get("origin", [0, 0, 0]), float)
        glow = e.get("name", "").startswith(("glow", "core"))
        for face, fd in e.get("faces", {}).items():
            if fd is None or fd.get("texture") is None or "uv" not in fd:
                continue
            u0, v0, u1, v1 = fd["uv"]
            uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            k = int(fd.get("rotation", 0)) // 90
            uv = uv[-k:] + uv[:-k] if k else uv
            cs = [(R @ (np.array(c) - o)) + o for c in corners(f, t, face)]
            key = (int(fd["texture"]) if isinstance(fd["texture"], int) else 0, glow)
            V, U = groups.setdefault(key, ([], []))
            V.extend(cs)
            U.extend([(a / rw, 1 - b / rh) for a, b in uv])
    scene = trimesh.Scene()
    for (ti, glow), (V, U) in groups.items():
        V = np.asarray(V) / 16.0
        n = len(V) // 4
        b = np.arange(n)[:, None] * 4
        F = np.vstack([np.hstack([b, b + 1, b + 2]), np.hstack([b, b + 2, b + 3])])
        im = texs[min(ti, len(texs) - 1)]
        m = trimesh.visual.material.PBRMaterial(name=f"{name}{'_glow' if glow else ''}_{ti}",
                                                baseColorTexture=im, metallicFactor=0.0, roughnessFactor=0.8,
                                                alphaMode="MASK" if not glow else "BLEND")
        mesh = trimesh.Trimesh(V, F, visual=trimesh.visual.TextureVisuals(uv=np.asarray(U), material=m), process=False)
        scene.add_geometry(mesh, node_name=f"{name}_{ti}{'_glow' if glow else ''}")
    path = os.path.join(outdir, name + ".glb")
    scene.export(path)
    return path, sum(len(v[0]) // 4 for v in groups.values())


if __name__ == "__main__":
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    names = sys.argv[2:] or sorted(f[:-8] for f in os.listdir(SRC) if f.endswith(".bbmodel"))
    for n in names:
        try:
            p, faces = convert(n, outdir)
            print(f"{n}: {faces} faces, {os.path.getsize(p):,} bytes")
        except Exception as ex:
            print(f"{n}: FAILED {ex}")
