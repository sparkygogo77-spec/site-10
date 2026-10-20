# Pass v2.0120: spider ceiling and leap strikes (Trials, Dread Warren R2 brute; spider moving attacks chat, 2026-10-20).
# Why: J kept v2.0110 M1, M3, M4 (dropped M2) and picked "Ceiling and leap strikes": spiders dropping from the
#   ceiling and leaping at you. Lair rules kept: legs never through each other, the floor/ceiling or you; hits touch.
# Takes (the file also carries the v2.0110 KEEPs M1, M3, M4):
#   L1 thread drop (from the ceiling)  walks the ceiling upside down, drops on its dragline, rights itself, stabs twice
#                                      hanging on the thread, lands and walks into a throw
#   L2 leap strike (leaping)           crouches, leaps 30 blocks, the right spike hits you coming down, lands, left, throw
#   L3 ceiling pounce (you flying)     you hover under the roof; it kicks off the ceiling, rolls upright, stabs you twice
#                                      mid-air, you both fall, it lands and stabs you on the floor
#   L4 cliff leap (leaping down)       leaps off a 28-block cliff at you on the floor below, hits on the way down, lands
# In the air every leg that isn't striking tucks toward the hips, then spreads to a landing pose over the last 6 frames;
#   every frame is still measured (burnt into each clip's label).
# Builder: tools/trials/spider_anim_tests.py; the renderer saves the scene as trials/spider_anims6.blend.
import os
import sys
import runpy

_root = globals().get("FOLDER") or r"C:\Users\Josh\Documents\LanternLive"
_repo = os.environ.get("KL_REPO") if os.path.exists(os.path.join(os.environ.get("KL_REPO", ""), "tools", "trials", "spider_anim_tests.py")) else os.path.join(_root, "site-10")
_builder = os.path.join(_repo, "tools", "trials", "spider_anim_tests.py")
_tmp = os.path.join(os.environ.get("TEMP", _root), "v2.0120_build.blend")
_argv = sys.argv
sys.argv = [_argv[0], "--", _tmp, "--only", "M1,M3,M4,L1,L2,L3,L4"]
try:
    runpy.run_path(_builder, run_name="__main__")
finally:
    sys.argv = _argv
