"""Adds a Lantern Corps' assets beside the red ones: python tools/add_corps.py <assets_dir> <corps>

Run tools/corps_textures.py first for the textures and models. This copies every corps=red
blockstate variant and every "red" case in the item model definitions to the new corps (pointing at
its _<corps> models), and adds its particle definitions. Safe to run twice.
"""
import json, os, sys

ASSETS = sys.argv[1]
CORPS = sys.argv[2]


def swap(node):
    if isinstance(node, dict):
        return {k: swap(v) for k, v in node.items()}
    if isinstance(node, list):
        return [swap(v) for v in node]
    if isinstance(node, str) and node.endswith("_red"):
        return node[:-4] + "_" + CORPS
    return node


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent="\t")
        f.write("\n")


for name in os.listdir(os.path.join(ASSETS, "blockstates")):
    path = os.path.join(ASSETS, "blockstates", name)
    with open(path) as f:
        state = json.load(f)
    variants = state.get("variants", {})
    if not any("corps=red" in k for k in variants):
        continue
    out = {}
    for key, value in variants.items():
        out[key] = value
        if "corps=red" in key:
            out[key.replace("corps=red", "corps=" + CORPS)] = swap(value)
    state["variants"] = out
    save(path, state)


def add_cases(node):
    if isinstance(node, dict):
        cases = node.get("cases")
        if isinstance(cases, list) and any(c.get("when") == "red" for c in cases):
            if not any(c.get("when") == CORPS for c in cases):
                red = next(c for c in cases if c.get("when") == "red")
                cases.append({"when": CORPS, "model": swap(red["model"])})
        for v in node.values():
            add_cases(v)
    elif isinstance(node, list):
        for v in node:
            add_cases(v)


for name in os.listdir(os.path.join(ASSETS, "items")):
    path = os.path.join(ASSETS, "items", name)
    with open(path) as f:
        item = json.load(f)
    before = json.dumps(item)
    add_cases(item)
    if json.dumps(item) != before:
        save(path, item)

for kind in ["drip", "mote", "pane", "shard", "spark"]:
    with open(os.path.join(ASSETS, "particles", "red_glow_" + kind + ".json")) as f:
        particle = json.load(f)
    save(os.path.join(ASSETS, "particles", CORPS + "_glow_" + kind + ".json"), particle)
