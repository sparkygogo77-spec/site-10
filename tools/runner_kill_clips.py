"""Dread Runner kill animations for J (Blender pass 420): four takes as clips in the rig's own format.

The rig (bbmodel/dread_runner_rig.json) holds per-joint angles: Blender XYZ Euler degrees in the
generator's frame (x right, y forward, z up), 24 frames a second (12-frame, 0.5 s stride). Each
clip here is a list of key poses, smoothstep-blended into per-frame angles, plus a root offset in
model px (x right, y forward, z up) for leaps and lunges, and a "target" track saying where the
victim's middle is held, measured from where a standing mob's middle sits (16 px up) at the runner's
start position (for the game to move the mob; null = released).

    python tools/runner_kill_clips.py RIG_IN RIG_OUT
writes RIG_OUT: the rig with a "clips" object {name: {"seconds", "frames", "root", "target", "hit"}}
("hit" = the frame the kill lands, for damage/sound).
"""
import json
import sys

PARTS = ["torso", "head", "arm_l", "fore_l", "arm_r", "fore_r", "thigh_l", "shin_l", "thigh_r", "shin_r"]
FPS = 24


def pose(**kw):
    """Key pose: part=(ax, ay, az) in degrees; root=(x, y, z) px; target=(x, y, z) px or None."""
    return kw


# Sprint frame 0, the pose every clip starts from and returns to.
RUN = dict(torso=(-38, 0, 0), head=(38.7, 0, 0), arm_l=(20, -18, 0), fore_l=(45, 0, 0), arm_r=(20, 18, 0),
           fore_r=(45, 0, 0), thigh_l=(34, 0, 0), shin_l=(-76.8, 0, 0), thigh_r=(34, 0, 0), shin_r=(-33.2, 0, 0))

CLIPS = {
    # K1: drop low, spring, slam both claws down on the mob and lunge with the head, then rise.
    "kill_k1_pounce_pin": dict(hit=17, keys=[
        (0, pose(**RUN, root=(0, 0, 0), target=(0, 26, 0))),
        (6, pose(torso=(-62, 0, 0), head=(58, 0, 0), arm_l=(55, -25, 0), fore_l=(60, 0, 0), arm_r=(55, 25, 0),
                 fore_r=(60, 0, 0), thigh_l=(80, 0, 0), shin_l=(-120, 0, 0), thigh_r=(80, 0, 0), shin_r=(-120, 0, 0),
                 root=(0, -2, -8), target=(0, 24, 0))),
        (12, pose(torso=(-28, 0, 0), head=(30, 0, 0), arm_l=(150, -15, 0), fore_l=(-10, 0, 0), arm_r=(150, 15, 0),
                  fore_r=(-10, 0, 0), thigh_l=(-25, 0, 0), shin_l=(-30, 0, 0), thigh_r=(-15, 0, 0), shin_r=(-50, 0, 0),
                  root=(0, 6, 12), target=(0, 28, 0))),
        (17, pose(torso=(-78, 0, 0), head=(70, 0, 0), arm_l=(108, -12, 0), fore_l=(20, 0, 0), arm_r=(108, 12, 0),
                  fore_r=(20, 0, 0), thigh_l=(70, 0, 0), shin_l=(-110, 0, 0), thigh_r=(85, 0, 0), shin_r=(-125, 0, 0),
                  root=(0, 10, -6), target=(0, 32, -14))),
        (21, pose(torso=(-82, 0, 0), head=(95, 0, 0), arm_l=(104, -12, 0), fore_l=(24, 0, 0), arm_r=(104, 12, 0),
                  fore_r=(24, 0, 0), thigh_l=(72, 0, 0), shin_l=(-112, 0, 0), thigh_r=(86, 0, 0), shin_r=(-126, 0, 0),
                  root=(0, 11, -7), target=(0, 32, -14))),
        (26, pose(torso=(-80, 0, 0), head=(60, 0, 0), arm_l=(100, -12, 0), fore_l=(22, 0, 0), arm_r=(100, 12, 0),
                  fore_r=(22, 0, 0), thigh_l=(70, 0, 0), shin_l=(-110, 0, 0), thigh_r=(84, 0, 0), shin_r=(-124, 0, 0),
                  root=(0, 11, -7), target=(0, 32, -14))),
        (38, pose(**RUN, root=(0, 30, 0), target=None)),
    ]),
    # K2: seize the mob with the right hand, hoist it overhead, twist and hurl it to the side.
    "kill_k2_grab_hurl": dict(hit=30, keys=[
        (0, pose(**RUN, root=(0, 0, 0), target=(0, 26, 0))),
        (6, pose(torso=(-45, 0, -10), head=(45, 0, 10), arm_l=(30, -25, 0), fore_l=(50, 0, 0), arm_r=(125, 10, 0),
                 fore_r=(-5, 0, 0), thigh_l=(50, 0, 0), shin_l=(-80, 0, 0), thigh_r=(20, 0, 0), shin_r=(-40, 0, 0),
                 root=(0, 6, -3), target=(-2, 22, 4))),
        (12, pose(torso=(-30, 0, -15), head=(30, 0, 15), arm_l=(30, -30, 0), fore_l=(50, 0, 0), arm_r=(95, 15, 0),
                  fore_r=(-40, 0, 0), thigh_l=(45, 0, 0), shin_l=(-75, 0, 0), thigh_r=(20, 0, 0), shin_r=(-40, 0, 0),
                  root=(0, 8, -2), target=(-6, 16, 10))),
        (22, pose(torso=(-5, 0, 25), head=(10, 0, -20), arm_l=(10, -40, 0), fore_l=(40, 0, 0), arm_r=(170, 20, 0),
                  fore_r=(-30, 0, 0), thigh_l=(35, 0, 0), shin_l=(-60, 0, 0), thigh_r=(15, 0, 0), shin_r=(-35, 0, 0),
                  root=(0, 9, 0), target=(-10, 4, 38))),
        (30, pose(torso=(-45, 0, -45), head=(40, 0, 35), arm_l=(40, -20, 0), fore_l=(55, 0, 0), arm_r=(85, -40, 0),
                  fore_r=(-10, 0, 0), thigh_l=(40, 0, 0), shin_l=(-70, 0, 0), thigh_r=(25, 0, 0), shin_r=(-45, 0, 0),
                  root=(0, 12, -2), target=(-14, 34, 16))),
        (31, pose(torso=(-45, 0, -45), head=(40, 0, 35), arm_l=(40, -20, 0), fore_l=(55, 0, 0), arm_r=(85, -40, 0),
                  fore_r=(-10, 0, 0), thigh_l=(40, 0, 0), shin_l=(-70, 0, 0), thigh_r=(25, 0, 0), shin_r=(-45, 0, 0),
                  root=(0, 12, -2), target=None)),
        (42, pose(**RUN, root=(0, 14, 0), target=None)),
    ]),
    # K3: stop dead, rear up, fling the arms wide and scream fear into the mob, then sag and run on.
    "kill_k3_fear_scream": dict(hit=20, keys=[
        (0, pose(**RUN, root=(0, 0, 0), target=(0, 30, 0))),
        (8, pose(torso=(8, 0, 0), head=(-25, 0, 0), arm_l=(-10, -70, -20), fore_l=(-20, 0, 0), arm_r=(-10, 70, 20),
                 fore_r=(-20, 0, 0), thigh_l=(10, 0, 0), shin_l=(-20, 0, 0), thigh_r=(-5, 0, 0), shin_r=(-10, 0, 0),
                 root=(0, 2, 4), target=(0, 30, 0))),
        (14, pose(torso=(15, 0, 0), head=(-40, 0, 0), arm_l=(-20, -100, -30), fore_l=(-35, 0, 0), arm_r=(-20, 100, 30),
                  fore_r=(-35, 0, 0), thigh_l=(10, 0, 0), shin_l=(-20, 0, 0), thigh_r=(-5, 0, 0), shin_r=(-10, 0, 0),
                  root=(0, 2, 5), target=(0, 30, 0))),
        (20, pose(torso=(-20, 0, 0), head=(55, 0, 0), arm_l=(15, -100, -10), fore_l=(-10, 0, 0), arm_r=(15, 100, 10),
                  fore_r=(-10, 0, 0), thigh_l=(20, 0, 0), shin_l=(-35, 0, 0), thigh_r=(5, 0, 0), shin_r=(-20, 0, 0),
                  root=(0, 4, 1), target=(0, 30, 0))),
        (30, pose(torso=(-25, 0, 0), head=(60, 0, 0), arm_l=(20, -98, -10), fore_l=(-10, 0, 0), arm_r=(20, 98, 10),
                  fore_r=(-10, 0, 0), thigh_l=(20, 0, 0), shin_l=(-35, 0, 0), thigh_r=(5, 0, 0), shin_r=(-20, 0, 0),
                  root=(0, 4, 1), target=None)),
        (44, pose(**RUN, root=(0, 6, 0), target=None)),
    ]),
    # K4: no stop: two raking claw swipes across the mob mid-stride (legs keep running).
    "kill_k4_rake_through": dict(hit=10, keys=[
        (0, pose(**RUN, root=(0, 0, 0), target=(0, 20, 0))),
        (5, pose(torso=(-40, 0, 25), head=(40, 0, -20), arm_l=(30, -30, 0), fore_l=(50, 0, 0), arm_r=(195, 60, 0),
                 fore_r=(-30, 0, 0), thigh_l=(34, 0, 0), shin_l=(-33, 0, 0), thigh_r=(34, 0, 0), shin_r=(-77, 0, 0),
                 root=(0, 6, 0), target=(0, 14, 0))),
        (10, pose(torso=(-40, 0, -25), head=(40, 0, 20), arm_l=(30, -30, 0), fore_l=(50, 0, 0), arm_r=(70, -40, 0),
                  fore_r=(-10, 0, 0), thigh_l=(34, 0, 0), shin_l=(-77, 0, 0), thigh_r=(34, 0, 0), shin_r=(-33, 0, 0),
                  root=(0, 12, 0), target=(4, 10, 0))),
        (15, pose(torso=(-40, 0, -25), head=(40, 0, 20), arm_l=(195, -60, 0), fore_l=(-30, 0, 0), arm_r=(30, 30, 0),
                  fore_r=(50, 0, 0), thigh_l=(34, 0, 0), shin_l=(-33, 0, 0), thigh_r=(34, 0, 0), shin_r=(-77, 0, 0),
                  root=(0, 18, 0), target=(2, 4, 2))),
        (20, pose(torso=(-40, 0, 25), head=(40, 0, -20), arm_l=(70, 40, 0), fore_l=(-10, 0, 0), arm_r=(30, 30, 0),
                  fore_r=(50, 0, 0), thigh_l=(34, 0, 0), shin_l=(-77, 0, 0), thigh_r=(34, 0, 0), shin_r=(-33, 0, 0),
                  root=(0, 24, 0), target=None)),
        (26, pose(**RUN, root=(0, 30, 0), target=None)),
    ]),
}


def smooth(a, b, t):
    t = t * t * (3 - 2 * t)
    return [a[i] + (b[i] - a[i]) * t for i in range(len(a))]


def bake(clip):
    keys = clip["keys"]
    n = keys[-1][0] + 1
    frames, root, target = [], [], []
    for f in range(n):
        k = max(i for i, (kf, _) in enumerate(keys) if kf <= f)
        k2 = min(k + 1, len(keys) - 1)
        f0, a = keys[k]
        f1, b = keys[k2]
        t = 0 if f1 == f0 else (f - f0) / (f1 - f0)
        frames.append({p: [round(v, 2) for v in smooth(list(a.get(p, RUN[p])), list(b.get(p, RUN[p])), t)] for p in PARTS})
        root.append([round(v, 2) for v in smooth(list(a["root"]), list(b["root"]), t)])
        ta, tb = a.get("target"), b.get("target")
        target.append([round(v, 2) for v in smooth(list(ta), list(tb), t)] if ta is not None and tb is not None else
                      ([round(v, 2) for v in ta] if ta is not None and t < 1 else None))
    return {"seconds": round(n / FPS, 3), "frames": frames, "root": root, "target": target, "hit": clip["hit"]}


if __name__ == "__main__":
    rig = json.load(open(sys.argv[1]))
    rig["clips"] = {name: bake(c) for name, c in CLIPS.items()}
    rig["clips_note"] = ("Kill clips (Blender pass 420): angles like 'frames', 24 fps; 'root' = runner offset in model px "
                         "(x right, y forward, z up) added to its position; 'target' = where the victim's middle is held, "
                         "in model px (x right, y forward, z up) from a standing mob's middle (16 px up) at the runner's start "
                         "position (null = released / thrown); 'hit' = the frame the kill lands.")
    json.dump(rig, open(sys.argv[2], "w"), indent=1)
    for name, c in rig["clips"].items():
        print(f"{name}: {c['seconds']} s, {len(c['frames'])} frames, hit at {c['hit']}")
