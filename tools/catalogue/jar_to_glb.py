"""Turns the jar's own models into .glb files for the site's model catalogue (catalogue.html).

Reads the models straight from a git ref of the mod (main by default), so the review-site branch does not need
the mod's sources checked out:

    python3 tools/catalogue/jar_to_glb.py --repo . --ref origin/main --jar 2.1.667+26.3 --out catalogue

For each catalogue entry it writes catalogue/<id>.glb and updates catalogue/index.json. A .glb holds one node
per part: "body" (the Minecraft block model: elements, per-face UVs and rotations, element rotations; cutout
texture, nearest-pixel) and one node per overlay the game draws on top ("glow", "swirl": the Blockbench models,
emissive and blended). Faces sharing a texture are merged into one mesh. Faces that are fully transparent, or
buried inside an opaque neighbouring cube, are dropped, and the meshes are stored with KHR_mesh_quantization
(16-bit positions, byte normals, 16-bit UVs; three.js reads it natively), to keep the file small. Overlay animation frames
(e.g. the swirl's) are written next to it as catalogue/tex/<texture>.png for the page to flip through.

1 unit = 1 block. The model stands on y = 0, centred on x = z = 0, front (north, where the ring docks) at -z.
Needs numpy and Pillow.
"""
import argparse, io, json, math, os, struct, subprocess
import numpy as np
from PIL import Image

ASSETS = "src/main/resources/assets/lanternring/"

# What the catalogue shows. "block" is a block model (models/block/<name>.json). Each overlay is a .bbmodel in
# the same frame as the lantern's own bbmodel ("frame"), which the block model is a scaled copy of; "texture" is
# the frame the game draws at rest, "frames" the textures it animates through, "idle" its rest brightness
# (LanternFirstPerson: IDLE_GLOW 0.13 for the glow, 0.12 for the swirl).
ENTRIES = [
    {
        "id": "dark_lantern", "name": "Dark lantern", "group": "Lanterns", "corps": "green",
        "block": "dark_lantern", "frame": "dark_lantern",
        "overlays": [
            {"node": "glow", "bbmodel": "dark_lantern_glow", "texture": "dark_lantern_glow_c23",
             "alpha_from": ["dark_lantern_glow_c%d" % i for i in range(24)] + ["dark_lantern_glow_climax", "dark_lantern_glow_flash"],
             "idle": 0.13},
            {"node": "swirl", "bbmodel": "dark_lantern_swirl", "texture": "dark_lantern_swirl_0",
             "frames": ["dark_lantern_swirl_%d" % i for i in range(8)], "idle": 0.12},
        ],
    },
]

FACES = ("north", "south", "east", "west", "up", "down")
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


class Repo:
    def __init__(self, path, ref):
        self.path, self.ref = path, ref

    def read(self, rel):
        return subprocess.run(["git", "-C", self.path, "show", f"{self.ref}:{rel}"], check=True, capture_output=True).stdout

    def json(self, rel):
        return json.loads(self.read(rel))

    def png(self, rel):
        return Image.open(io.BytesIO(self.read(rel))).convert("RGBA")

    def commit(self):
        return subprocess.run(["git", "-C", self.path, "rev-parse", "--short", self.ref], check=True, capture_output=True, text=True).stdout.strip()


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


def axis_rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Cube:
    """One element, in the model's own pixel units: its box, how it is turned, and its faces' UVs (0..1)."""

    def __init__(self, f, t, R, origin, faces):
        self.f, self.t, self.R, self.o, self.faces = np.array(f, float), np.array(t, float), R, np.array(origin, float), faces


def block_cubes(model):
    """Minecraft block model elements: UVs in 0..16, rotation {origin, axis, angle, rescale}."""
    out = []
    for e in model["elements"]:
        R, o = None, (8, 8, 8)
        r = e.get("rotation")
        if r and r.get("angle"):
            R, o = axis_rot(r["axis"], r["angle"]), r.get("origin", o)
            if r.get("rescale"):
                k = 1 / math.cos(math.radians(abs(r["angle"])))
                sc = np.array([1.0 if r["axis"] == a else k for a in "xyz"])
                R = R @ np.diag(sc)
        faces = {}
        for name, fd in e.get("faces", {}).items():
            uv = fd.get("uv") or [0, 0, 16, 16]
            faces[name] = ([u / 16 for u in uv], int(fd.get("rotation", 0)))
        out.append(Cube(e["from"], e["to"], R, o, faces))
    return out


def bb_cubes(model):
    """Blockbench elements: UVs in texture pixels, rotation [rx, ry, rz] about origin, inflate."""
    res = model.get("resolution", {"width": 16, "height": 16})
    out = []
    for e in model["elements"]:
        if e.get("type", "cube") != "cube" or e.get("visibility") is False:
            continue
        inf = e.get("inflate", 0)
        rot = e.get("rotation", [0, 0, 0])
        R = None
        if any(rot):
            R = axis_rot("z", rot[2]) @ axis_rot("y", rot[1]) @ axis_rot("x", rot[0])
        faces = {}
        for name, fd in e.get("faces", {}).items():
            if fd is None or fd.get("texture") is None or "uv" not in fd:
                continue
            u0, v0, u1, v1 = fd["uv"]
            faces[name] = ([u0 / res["width"], v0 / res["height"], u1 / res["width"], v1 / res["height"]], int(fd.get("rotation", 0)))
        out.append(Cube(np.array(e["from"]) - inf, np.array(e["to"]) + inf, R, e.get("origin", (0, 0, 0)), faces))
    return out


def coverage(alpha, uv):
    """'empty', 'full' or 'mixed': the alpha of the texture pixels a face shows."""
    h, w = alpha.shape
    u0, v0, u1, v1 = uv
    x0, x1 = sorted((u0 * w, u1 * w))
    y0, y1 = sorted((v0 * h, v1 * h))
    x0, y0 = int(math.floor(x0 + 1e-6)), int(math.floor(y0 + 1e-6))
    x1, y1 = max(x0 + 1, int(math.ceil(x1 - 1e-6))), max(y0 + 1, int(math.ceil(y1 - 1e-6)))
    a = alpha[max(0, y0):min(h, y1), max(0, x0):min(w, x1)]
    if a.size == 0 or a.max() == 0:
        return "empty"
    return "full" if a.min() == 255 else "mixed"


def buried(cubes, cov):
    """Faces hidden inside an opaque, unturned neighbour (every face of it full): {(cube index, face)}."""
    solid = [i for i, c in enumerate(cubes) if c.R is None and len(c.faces) == 6 and all(cov[(i, n)] == "full" for n in FACES)]
    if not solid:
        return set()
    lo = np.array([cubes[i].f for i in solid])
    hi = np.array([cubes[i].t for i in solid])
    idx = np.array(solid)
    eps = 1e-4
    out = set()
    for i, c in enumerate(cubes):
        if c.R is not None:
            continue
        for name in c.faces:
            n = NORMAL[name]
            ax = int(np.argmax(np.abs(n)))
            plane = c.t[ax] if n[ax] > 0 else c.f[ax]
            # the neighbour must fill the space just outside this face ...
            if n[ax] > 0:
                ok = (lo[:, ax] <= plane + eps) & (hi[:, ax] > plane + eps)
            else:
                ok = (hi[:, ax] >= plane - eps) & (lo[:, ax] < plane - eps)
            # ... across the whole face
            for o in range(3):
                if o != ax:
                    ok &= (lo[:, o] <= c.f[o] + eps) & (hi[:, o] >= c.t[o] - eps)
            ok &= idx != i
            if ok.any():
                out.add((i, name))
    return out


def mesh(cubes, alpha, scale, offset, keep_mixed=True):
    """Positions, normals, UVs and triangle indices of every visible face, in blocks."""
    cov = {(i, n): coverage(alpha, uv) for i, c in enumerate(cubes) for n, (uv, _) in c.faces.items()}
    hidden = buried(cubes, cov)
    P, N, U = [], [], []
    for i, c in enumerate(cubes):
        for name, (uv, rot) in c.faces.items():
            if cov[(i, name)] == "empty" or (i, name) in hidden:
                continue
            u0, v0, u1, v1 = uv
            q = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            k = (rot // 90) % 4
            q = q[-k:] + q[:-k] if k else q
            cs = np.array(corners(c.f, c.t, name), float)
            n = np.array(NORMAL[name], float)
            if c.R is not None:
                cs = (cs - c.o) @ c.R.T + c.o
                n = c.R @ n
                n /= np.linalg.norm(n)
            cs = cs * scale + offset
            # wind the quad counter-clockwise seen from outside, as glTF expects
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), n) < 0:
                cs, q = cs[::-1], q[::-1]
            P.extend(cs)
            N.extend([n] * 4)
            U.extend(q)
    P = np.asarray(P, np.float32)
    n = len(P) // 4
    b = np.arange(n)[:, None] * 4
    I = np.hstack([b, b + 1, b + 2, b, b + 2, b + 3]).reshape(-1)
    return P, np.asarray(N, np.float32), np.asarray(U, np.float32), I


class Glb:
    """A minimal glTF 2.0 binary writer: meshes, nearest-pixel PNG textures, PBR materials, named nodes."""

    def __init__(self):
        self.bin = bytearray()
        self.g = {"asset": {"version": "2.0", "generator": "tools/catalogue/jar_to_glb.py"}, "scene": 0, "scenes": [{"nodes": []}],
                  "nodes": [], "meshes": [], "materials": [], "textures": [], "images": [], "accessors": [], "bufferViews": [],
                  "samplers": [{"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}], "buffers": []}

    def view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        v = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            v["target"] = target
        self.bin.extend(data)
        self.g["bufferViews"].append(v)
        return len(self.g["bufferViews"]) - 1

    def accessor(self, arr, kind, target, minmax=False, normalized=False):
        ctype = {np.float32: 5126, np.int8: 5120, np.int16: 5122, np.uint16: 5123, np.uint32: 5125}[arr.dtype.type]
        data = arr
        stride = None
        if arr.ndim == 2 and arr.nbytes // len(arr) % 4:
            # vertex attributes must sit on 4-byte boundaries: pad each one out
            stride = -(-arr.nbytes // len(arr) // 4) * 4
            pad = np.zeros((len(arr), stride // arr.itemsize), arr.dtype)
            pad[:, :arr.shape[1]] = arr
            data = pad
        a = {"bufferView": self.view(data.tobytes(), target), "componentType": ctype, "count": len(arr), "type": kind}
        if stride:
            self.g["bufferViews"][a["bufferView"]]["byteStride"] = stride
        if normalized:
            a["normalized"] = True
        if minmax:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
        self.g["accessors"].append(a)
        return len(self.g["accessors"]) - 1

    def texture(self, im):
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        self.g["images"].append({"bufferView": self.view(buf.getvalue()), "mimeType": "image/png"})
        self.g["textures"].append({"sampler": 0, "source": len(self.g["images"]) - 1})
        return len(self.g["textures"]) - 1

    def material(self, name, tex, emissive):
        m = {"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": tex}, "metallicFactor": 0.0, "roughnessFactor": 0.7}}
        if emissive:
            m["pbrMetallicRoughness"]["baseColorFactor"] = [0, 0, 0, 1]
            m["emissiveTexture"] = {"index": tex}
            m["emissiveFactor"] = [1, 1, 1]
            m["alphaMode"] = "BLEND"
        else:
            m["alphaMode"], m["alphaCutoff"] = "MASK", 0.5
        self.g["materials"].append(m)
        return len(self.g["materials"]) - 1

    def node(self, name, P, N, U, I, mat, extras):
        """A mesh node, stored small with KHR_mesh_quantization: positions as 16-bit steps that the node's
        translation and (uniform) scale turn back into blocks, normals as bytes and UVs as 16-bit fractions."""
        lo, hi = P.min(0), P.max(0)
        step = float((hi - lo).max()) / 65534 or 1.0
        mid = (lo + hi) / 2
        Q = np.round((P - mid) / step).astype(np.int16)
        Nq = np.round(N * 127).astype(np.int8)
        Uq = np.round(np.clip(U, 0, 1) * 65535).astype(np.uint16)
        idx = I.astype(np.uint16 if len(P) < 65536 else np.uint32)
        prim = {"attributes": {"POSITION": self.accessor(Q, "VEC3", 34962, True), "NORMAL": self.accessor(Nq, "VEC3", 34962, normalized=True),
                               "TEXCOORD_0": self.accessor(Uq, "VEC2", 34962, normalized=True)},
                "indices": self.accessor(idx, "SCALAR", 34963), "material": mat}
        self.g["meshes"].append({"name": name, "primitives": [prim]})
        self.g["nodes"].append({"name": name, "mesh": len(self.g["meshes"]) - 1, "extras": extras,
                                "translation": mid.tolist(), "scale": [step] * 3})
        return len(self.g["nodes"]) - 1

    def write(self, path, root_name, children, extras):
        self.g["nodes"].append({"name": root_name, "children": children, "extras": extras})
        self.g["scenes"][0]["nodes"] = [len(self.g["nodes"]) - 1]
        while len(self.bin) % 4:
            self.bin.append(0)
        self.g["buffers"] = [{"byteLength": len(self.bin)}]
        self.g["extensionsUsed"] = self.g["extensionsRequired"] = ["KHR_mesh_quantization"]
        js = json.dumps(self.g, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            f.write(struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin))


def convert(repo, entry, out, jar):
    tex_dir = os.path.join(out, "tex")
    os.makedirs(tex_dir, exist_ok=True)
    block = repo.json(ASSETS + f"models/block/{entry['block']}.json")
    tname = block["textures"]["t"].split(":", 1)[1]
    body_tex = repo.png(ASSETS + f"textures/{tname}.png")
    frame = repo.json(ASSETS + f"bbmodel/{entry['frame']}.bbmodel")
    # The block model is the lantern's bbmodel scaled to one block tall and moved to the block's centre; the
    # overlays share the bbmodel's frame, so they get the same scale.
    els = [e for e in frame["elements"] if e.get("type", "cube") == "cube"]
    height = max(e["to"][1] for e in els) - min(e["from"][1] for e in els)
    bb_scale = 1.0 / height
    glb = Glb()
    nodes, stats = [], {}
    cubes = block_cubes(block)
    P, N, U, I = mesh(cubes, np.asarray(body_tex)[:, :, 3], 1 / 16, np.array([-0.5, 0, -0.5]))
    nodes.append(glb.node("body", P, N, U, I, glb.material("body", glb.texture(body_tex), False), {"part": "body"}))
    stats["body"] = (len(cubes), len(P) // 4)
    overlays = []
    for ov in entry.get("overlays", []):
        model = repo.json(ASSETS + f"bbmodel/{ov['bbmodel']}.bbmodel")
        frames = ov.get("frames", [])
        tex = repo.png(ASSETS + f"textures/entity/bb/{ov['texture']}.png")
        alpha = np.zeros(np.asarray(tex).shape[:2], np.uint8)
        for t in ov.get("alpha_from", []) + frames + [ov["texture"]]:
            alpha = np.maximum(alpha, np.asarray(repo.png(ASSETS + f"textures/entity/bb/{t}.png"))[:, :, 3])
        cubes = bb_cubes(model)
        P, N, U, I = mesh(cubes, alpha, bb_scale, np.zeros(3))
        nodes.append(glb.node(ov["node"], P, N, U, I, glb.material(ov["node"], glb.texture(tex), True),
                              {"part": "overlay", "idle": ov["idle"]}))
        stats[ov["node"]] = (len(cubes), len(P) // 4)
        for t in frames:
            repo.png(ASSETS + f"textures/entity/bb/{t}.png").save(os.path.join(tex_dir, t + ".png"), optimize=True)
        overlays.append({"node": ov["node"], "idle": ov["idle"], "frames": [f"catalogue/tex/{t}.png" for t in frames]})
    path = os.path.join(out, entry["id"] + ".glb")
    glb.write(path, entry["id"], nodes, {"jar": jar})
    return path, stats, overlays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--jar", required=True, help="jar version the models came from, e.g. 2.1.667+26.3")
    ap.add_argument("--out", default="catalogue")
    ap.add_argument("ids", nargs="*")
    a = ap.parse_args()
    repo = Repo(a.repo, a.ref)
    os.makedirs(a.out, exist_ok=True)
    index_path = os.path.join(a.out, "index.json")
    index = json.load(open(index_path)) if os.path.exists(index_path) else {"models": []}
    by_id = {m["id"]: m for m in index["models"]}
    for e in ENTRIES:
        if a.ids and e["id"] not in a.ids:
            continue
        path, stats, overlays = convert(repo, e, a.out, a.jar)
        size = os.path.getsize(path)
        by_id[e["id"]] = {"id": e["id"], "name": e["name"], "group": e["group"], "corps": e["corps"], "jar": a.jar,
                          "commit": repo.commit(), "glb": f"catalogue/{e['id']}.glb", "bytes": size, "overlays": overlays}
        print(f"{e['id']}: {size:,} bytes; " + ", ".join(f"{k} {c} cubes -> {f} faces" for k, (c, f) in stats.items()))
    order = [e["id"] for e in ENTRIES]
    index["models"] = sorted(by_id.values(), key=lambda m: order.index(m["id"]) if m["id"] in order else len(order))
    with open(index_path, "w") as f:
        json.dump(index, f, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
