# Pass v2.0110: spider moving attacks (Trials, Dread Warren R2 brute; spider moving attacks chat, 2026-10-20).
# Why: J on the final lair set (round 10): "we will need more extending or movement attacks from the spider to make it
#   not just stationary". Lair rules kept: legs never through each other or the floor, strikes touch you.
# Takes (each strike lands while R2 keeps moving; the body never stops for a hit):
#   M1 drive-back combo (walking)   four jabs left-right-left-right while it walks you backwards, the last throws you
#   M2 circling strikes (turning)   circles you crabwise, darts in for a side stab, turns head on, reverses, last stab
#   M3 climbing strike (climbing)   climbs a 28-block cliff to you, stabs over the lip mid-climb, rolls over and throws you
#   M4 chase-down (you running)     runs you down from behind, hooks your legs, then stabs you on the floor
# Every frame is measured (burnt into each clip's label): legs through the floor, legs touching each other or the
#   body, legs through you, and the spike-to-you distance at each hit (0 = touching).
# The builder is tools/trials/spider_anim_tests.py (the lair rounds 8-10 rig and leg IK); this runs it for M1-M4 and
#   leaves the scene built (globals bpy, np, FOLDER); the renderer saves it as trials/spider_anims5.blend.
import os
import sys
import runpy

_root = globals().get("FOLDER") or r"C:\Users\Josh\Documents\LanternLive"
_repo = os.environ.get("KL_REPO") if os.path.exists(os.path.join(os.environ.get("KL_REPO", ""), "tools", "trials", "spider_anim_tests.py")) else os.path.join(_root, "site-10")
_builder = os.path.join(_repo, "tools", "trials", "spider_anim_tests.py")
_tmp = os.path.join(os.environ.get("TEMP", _root), "v2.0110_build.blend")
_argv = sys.argv
sys.argv = [_argv[0], "--", _tmp, "--only", "M1,M2,M3,M4"]
try:
    runpy.run_path(_builder, run_name="__main__")
finally:
    sys.argv = _argv
