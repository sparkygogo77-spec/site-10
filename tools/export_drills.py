"""Exports the three new Blast Drills (tools/pixel_blast_drill.py: D1 auger, D2 tiered, D3 crystal) as bbmodels the
game can draw in place of blast_drill.bbmodel (J, 2026-10-13: "D1 and D2, D3 will be good with different construct
textures"):

    python tools/export_drills.py src/main/resources/assets/lanternring
      -> bbmodel/blast_drill_d1.bbmodel, _d2, _d3 and textures/entity/bb/blast_drill_d<n>.png

Same frame as blast_drill.bbmodel: tip toward -Z, collar at Z = 0..+6, about 100 model px long. The voxel shape is
resampled at 2 model px per cell (so each drill stays under 1 MB) and neighbouring cells of a part merge into boxes. Cube prefixes:
  glass_hardlight_* the hard-light body (BODY, LIGHTP): translucent, full-bright. This is where J's construct
                    texture goes (brick / inner / rim per drill, Blender pass 211), if the renderer lays it on;
  glow_*            cutting edges, the core light, the collar slot;
  anything else     the dark jade core and collar.
"""
import base64, io, json, math, os, sys, uuid
from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "src/main/resources/assets/lanternring")
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
_x = open(os.path.join(HERE, "export_round1_models.py")).read()
exec(_x[_x.index("def flat("):_x.index("def load(")])
sys.argv = [sys.argv[0], "/tmp"]
_d = open(os.path.join(HERE, "pixel_blast_drill.py")).read()
g = {"__name__": "drill"}
exec(compile(_d[:_d.index("def quads(")], "pixel_blast_drill.py", "exec"), g)
DENSITY = 1
ONLY = None
STEP = 0.8          # drill-space units per cell; each cell is 2 model px, so the 40-unit drill is 100 px long
CELL = 2.0
COL = {g["CORE"]: ("dark_core", (10, 46, 28)), g["BODY"]: ("glass_hardlight_body", (24, 150, 80)),
       g["LIGHTP"]: ("glass_hardlight_lit", (70, 196, 118)), g["EDGE"]: ("glow_edge", (205, 255, 215)),
       g["GLOW"]: ("glow_light", (40, 230, 96))}


def export(v, fn):
    part = fn()
    AX, AZ = g["AX"], g["AZ"]
    xs = np.arange(-10, 10, STEP) + STEP / 2
    zs = np.arange(0, 40, STEP) + STEP / 2
    ix = np.clip(np.searchsorted(AX, xs), 0, len(AX) - 1)
    iz = np.clip(np.searchsorted(AZ, zs), 0, len(AZ) - 1)
    sub = part[np.ix_(ix, ix, iz)]
    parts = {}
    n0 = len(xs) // 2
    for pid, (prefix, rgb) in COL.items():
        # stand the drill along -Z: drill height k becomes z = 6 - k ("dark_core", not "core": BbModel's core* is a lantern heart)
        cells = {(int(i) - n0, int(j) - n0, 3 - int(k)) for i, j, k in np.argwhere(sub == pid)}
        if cells:
            parts[prefix] = (rgb, cells)
    return write_model(f"blast_drill_{v}", parts, CELL)


if __name__ == "__main__":
    for v in ("d1", "d2", "d3"):
        print(v, export(v, g[v]), "cubes")
