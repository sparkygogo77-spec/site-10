"""Nebula light takes (Blender pass 430) as bbmodels for the placed block.

Each lathe quad from tools/nebula_light_profiles.json becomes one zero-thickness panel at the quad's
middle, tilted (X) to the profile's slope and turned (Y) to face out, with per-face UVs in 16ths of
ONE strip frame. tools/bbmodel_json.py turns these into block elements (free 26.x angles); point the
model's light texture at the corps' strip (lanternring:block/construct_ripples_<strip>) and the
block atlas animates it. Panels are named "glow_light..." so the block draws them full-bright.
Sloped quads are trapezoids; a panel is the rectangle through their middle (the self-check prints
how far its corners land from the true lathe, in model px).

    python tools/nebula_light_block.py OUT_DIR
writes OUT_DIR/nebula_light_<take>.bbmodel.
"""
import json
import math
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILES = json.load(open(os.path.join(HERE, "nebula_light_profiles.json")))


def r(v):
    return round(v, 4)


def panels(part):
    """(from, to, origin, rotation, uv) for every panel of one lathe part, plus the worst corner error."""
    seg, prof, every = part["segments"], part["profile"], part.get("every", 1)
    rmax = max(rad for _, rad in prof)
    circ = 2 * math.pi * rmax
    vs, s = [0.0], 0.0
    for (y0, r0), (y1, r1) in zip(prof, prof[1:]):
        s += math.hypot(y1 - y0, r1 - r0)
        vs.append(s / circ)
    out, worst = [], 0.0
    half = math.pi / seg
    for k in range(seg):
        if k % every:
            continue
        a = 2 * math.pi * (k + 0.5) / seg
        for j in range(len(prof) - 1):
            (y0, r0), (y1, r1) = prof[j], prof[j + 1]
            if r0 == 0 and r1 == 0:
                continue
            rm, ym = (r0 + r1) / 2, (y0 + y1) / 2
            d = rm * math.cos(half)                  # the flat panel's distance from the axis
            w = 2 * rm * math.sin(half)
            length = math.hypot(y0 - y1, r0 - r1)
            tilt = -math.degrees(math.atan2(r0 - r1, y0 - y1))   # top leans out when r0 > r1
            c = (d * math.sin(a), ym, -d * math.cos(a))
            frm = [c[0] - w / 2, ym - length / 2, c[2]]
            to = [c[0] + w / 2, ym + length / 2, c[2]]
            yaw = -math.degrees(a)
            # u runs left to right seen from outside: 1 - angle/360, measured from north toward east (+X)
            uv = [16 * (1 - (k + 1) / seg), 16 * vs[j], 16 * (1 - k / seg), 16 * vs[j + 1]]
            out.append((frm, to, c, (tilt, yaw, 0.0), uv))
            # self-check: the panel's corners against the lathe quad's corners
            for sx, sy, ang, yy, rr in ((1, 1, a + half, y0, r0), (-1, 1, a - half, y0, r0),
                                        (1, -1, a + half, y1, r1), (-1, -1, a - half, y1, r1)):
                p = [sx * w / 2, sy * length / 2, 0.0]
                tx, ty = math.radians(tilt), math.radians(yaw)
                p = [p[0], p[1] * math.cos(tx) - p[2] * math.sin(tx), p[1] * math.sin(tx) + p[2] * math.cos(tx)]
                p = [p[0] * math.cos(ty) + p[2] * math.sin(ty), p[1], -p[0] * math.sin(ty) + p[2] * math.cos(ty)]
                p = [p[i] + c[i] for i in range(3)]
                worst = max(worst, math.dist(p, (rr * math.sin(ang), yy, -rr * math.cos(ang))))
    return out, worst


def bbmodel(take):
    elements = []
    report = []
    for pi, part in enumerate(PROFILES["takes"][take]["parts"]):
        ps, worst = panels(part)
        report.append(f"part {pi}: {len(ps)} panels, corners within {worst:.2f} px")
        for n, (frm, to, c, rot, uv) in enumerate(ps):
            faces = {f: {"uv": [0, 0, 0, 0], "texture": None} for f in ("east", "west", "up", "down")}
            faces["north"] = {"uv": [r(v) for v in uv], "texture": 0}
            faces["south"] = {"uv": [r(uv[2]), r(uv[1]), r(uv[0]), r(uv[3])], "texture": 0}
            elements.append({"name": f"glow_light_{pi}_{n}", "type": "cube", "box_uv": False,
                             "from": [r(v) for v in frm], "to": [r(v) for v in to], "origin": [r(v) for v in c],
                             "rotation": [r(v) for v in rot], "faces": faces, "inflate": 0,
                             "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"nebula_light/{take}/{pi}/{n}"))})
    model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
             "name": f"nebula_light_{take}", "resolution": {"width": 16, "height": 16},
             "elements": elements, "outliner": [e["uuid"] for e in elements],
             "textures": [{"name": "strip", "path": "", "id": "0"}]}
    return model, report


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for take in PROFILES["takes"]:
        model, report = bbmodel(take)
        json.dump(model, open(f"{out}/nebula_light_{take}.bbmodel", "w"), indent=1)
        print(take, "; ".join(report))
