# Pass v2.0124: spider drops, re-attaching and real leaps (Trials, Dread Warren R2 brute; spider moving attacks chat).
# Why (J on v2.0120, 2026-10-20): L1 "we need better dropping animations, and bending back up to attach to a surface
#   animation, I think we already have a decent one going up to the ceiling?"; L2 "the leap to look like its priming its
#   arms for you and the back legs push it off of whatever surface"; L3 "the pound defies physics and its basically
#   flying ... we need good ones without it where they fall faster and have a smooth landing (s)"; L4 "the legs ...
#   become unnaturally positioned while falling ... they should almost slink out in antticipation for grabbing onto its
#   next surface"; and "the spider should also not be able to hit you when the eyes cant see you".
# Takes (the file also carries the v2.0110 KEEPs M1, M3, M4):
#   L1a head-first drop, climb back   drops head first on its dragline, stabs hanging, climbs back hand over hand, bends
#                                     back onto the roof (C1's climb, rebuilt)
#   L1b free-fall drop, wall climb    no thread: falls with legs slinking out for the floor, lands softly, stabs, runs to
#                                     the cave wall, climbs it and bends round onto the roof
#   L1c abseil and zip back           lowers itself in three short drops, turning on the line, stabs, zips back up and
#                                     bends back onto the roof
#   J1-J4 leaps                       crouch with front legs cocked at you, the last pair pushes off, a real ballistic arc
#                                     at 40 blocks/s/s, legs slinking out for the landing, a soft sinking landing:
#                                     J1 floor, J2 off the roof at you on the floor, J3 off the roof at you flying, J4 off a cliff
#   M3b climbing strike, eyes first   M3, but it peeks over the edge and only stabs once its eyes see you
# Every hit needs a clear line from its eyes to you. Research: docs/findings/2026-10-20-spider-dragline-drop.md.
# Builder: tools/trials/spider_anim_tests.py; the renderer saves the scene as trials/spider_anims7.blend.
import os
import sys
import runpy

_root = globals().get("FOLDER") or r"C:\Users\Josh\Documents\LanternLive"
_repo = os.environ.get("KL_REPO") if os.path.exists(os.path.join(os.environ.get("KL_REPO", ""), "tools", "trials", "spider_anim_tests.py")) else os.path.join(_root, "site-10")
_builder = os.path.join(_repo, "tools", "trials", "spider_anim_tests.py")
_tmp = os.path.join(os.environ.get("TEMP", _root), "v2.0124_build.blend")
_argv = sys.argv
sys.argv = [_argv[0], "--", _tmp, "--only", "M1,M3,M4,M3b,L1a,L1b,L1c,J1,J2,J3,J4"]
try:
    runpy.run_path(_builder, run_name="__main__")
finally:
    sys.argv = _argv
