"""Adds another Lantern Corps' entries to the shared asset files, copied from the red ones:
python tools/add_corps.py src/main/resources/assets/lanternring violet

Run tools/corps_textures.py for the corps first (it makes the _<corps> textures and models). This
copies every "red" case in the ring and lantern item models, every corps=red variant in the
construct and lantern blockstates, and the red_glow_* particle definitions, pointing them at the
corps' own models. Running it again for a corps that is already there changes nothing.
"""
import json, os, sys

ASSETS = sys.argv[1]
CORPS = sys.argv[2]


def rename(node):
    if isinstance(node, dict):
        return {k: rename(v) for k, v in node.items()}
    if isinstance(node, list):
        return [rename(v) for v in node]
    if isinstance(node, str) and node.endswith("_red"):
        return node[:-4] + "_" + CORPS
    return node


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent="\t")
        f.write("\n")


# Blockstates: corps=red,... -> corps=<corps>,...
for name in ["construct_brick", "light_construct", "power_battery"]:
    path = os.path.join(ASSETS, "blockstates", name + ".json")
    data = load(path)
    out = {}
    for key, value in data["variants"].items():
        out[key] = value
        if "corps=red" in key:
            new = key.replace("corps=red", "corps=" + CORPS)
            if new not in data["variants"]:
                out[new] = rename(value)
    data["variants"] = out
    save(path, data)

# Item models: the select on the corps gets a case for <corps>.
for name in ["power_ring", "power_battery"]:
    path = os.path.join(ASSETS, "items", name + ".json")
    data = load(path)
    cases = data["model"]["cases"]
    if not any(c["when"] == CORPS for c in cases):
        red = next(c for c in cases if c["when"] == "red")
        cases.append({"when": CORPS, "model": rename(red["model"])})
    save(path, data)

# Particles.
pdir = os.path.join(ASSETS, "particles")
for f in sorted(os.listdir(pdir)):
    if f.startswith("red_"):
        out = os.path.join(pdir, CORPS + f[3:])
        if not os.path.exists(out):
            save(out, load(os.path.join(pdir, f)))
