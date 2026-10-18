"""Packs J's pass 844 S3b KEEP (first-person construct sword: stepping wide sweep pair) into the table the game reads
(assets/lanternring/poses/fp_sword.json, played by SwordSwing).

    python3 tools/fp_sword_poses.py FP_TOOLS3_POSES_JSON OUT_JSON

FP_TOOLS3_POSES_JSON is LanternLive\\combat\\fp_tools3_poses.json, written by
docs/blender/blender_updates/844_fp_tools3.update.py (it also runs headless: bpy 5.0 in a Python 3.11 venv, the
construct_*_green.bbmodel files in FOLDER\\kl_assets). Each tick is the right arm's pitch, yaw, roll (degrees, pitch 90 =
straight ahead, yaw + toward the left, roll about the arm), the sword's tilt forward in the fist, the shoulder's reach
(m, + forward) and the sword's twist about its length (degrees, the edge leading). "form" is the forming ticks before
the swing (the sword extrudes from the fist behind a scan plate), "swing" the swing's ticks, "hits" its contact ticks.
"""
import json
import sys

SRC, OUT = sys.argv[1:3]
take = json.load(open(SRC))["takes"]["S3b"]
form, swing = take["forming_ticks"], take["swing_ticks"]
ticks = take["ticks"]


def row(t):
    a = t["arm"]
    return [round(float(v), 3) for v in (a[0], a[1], a[2], t["tool_tilt"], t["reach"], t["tool_twist"])]


swing_rows = [row(ticks[form + k]) for k in range(swing + 1)]
hits = [k for k in range(swing + 1) if ticks[form + k]["hit"]]
out = {"S3B": {"name": take["name"], "form": form, "swing": swing, "hits": hits, "rest": row(ticks[0]), "ticks": swing_rows}}
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print("wrote", OUT, "swing", swing, "hits", hits)
