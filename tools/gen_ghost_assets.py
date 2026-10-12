"""Blockstates, models and textures for the Build mode's green ghost blocks (stairs, slabs,
fences, panes, walls, doors, trapdoors, gates, carpets, ladders, lanterns, leaves, plants).

Each copies a vanilla blockstate and its models' parents, with every texture swapped for hard
light. Run from the repo root: python3 tools/gen_ghost_assets.py
"""
import glob, io, json, os, re, zipfile
from PIL import Image

jar = glob.glob('.gradle/loom-cache/minecraftMaven/net/minecraft/minecraft-clientOnly-*/26.3/*.jar')[0]
z = zipfile.ZipFile(jar)
A = 'src/main/resources/assets/lanternring/'

def vanilla(path):
    return json.loads(z.read('assets/minecraft/' + path))

# ghost name -> vanilla block whose blockstate it copies
SHAPES = {
    'stairs': 'oak_stairs', 'slab': 'oak_slab', 'fence': 'oak_fence', 'pane': 'glass_pane',
    'wall': 'cobblestone_wall', 'door': 'oak_door', 'trapdoor': 'oak_trapdoor', 'gate': 'oak_fence_gate',
    'carpet': 'white_carpet', 'ladder': 'ladder', 'lantern': 'lantern', 'leaves': 'oak_leaves',
}
SPRITE = {'leaves': 'lanternring:block/construct_leaves', 'plant': 'lanternring:block/construct_plant'}

def sprite(name):
    s = SPRITE.get(name, 'lanternring:block/construct_inner')
    return {'sprite': s, 'force_translucent': True}

def model(name, ref):
    """Writes lanternring:block/ghost_<name>_<model> from a vanilla model reference; returns its id."""
    short = ref.split('/')[-1]
    out = f'ghost_{name}_{short}'
    m = vanilla('models/block/' + short + '.json')
    textures = {k: (sprite(name) if k != 'particle' else SPRITE.get(name, 'lanternring:block/construct_inner'))
                for k in m.get('textures', {})}
    textures.setdefault('particle', SPRITE.get(name, 'lanternring:block/construct_inner'))
    new = {'parent': m['parent'] if 'parent' in m else 'minecraft:block/block', 'textures': textures}
    if 'elements' in m:
        new['elements'] = m['elements']
    json.dump(new, open(A + f'models/block/{out}.json', 'w'), indent='\t')
    return 'lanternring:block/' + out

def rewrite(obj, name, seen):
    if isinstance(obj, dict):
        return {k: (seen.setdefault(v, model(name, v)) if k == 'model' else rewrite(v, name, seen)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rewrite(v, name, seen) for v in obj]
    return obj

for name, block in SHAPES.items():
    bs = vanilla(f'blockstates/{block}.json')
    json.dump(rewrite(bs, name, {}), open(A + f'blockstates/ghost_{name}.json', 'w'), indent='\t')

# Plants: one cross.
json.dump({'parent': 'minecraft:block/cross', 'textures': {'cross': sprite('plant'), 'particle': SPRITE['plant']}},
          open(A + 'models/block/ghost_plant.json', 'w'), indent='\t')
json.dump({'variants': {'': {'model': 'lanternring:block/ghost_plant'}}}, open(A + 'blockstates/ghost_plant.json', 'w'), indent='\t')

def glow(src, out, alpha):
    """A vanilla grey texture recoloured as hard light: bright jade, see-through."""
    im = Image.open(io.BytesIO(z.read('assets/minecraft/textures/block/' + src))).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            v = (r + g + b) / 765
            px[x, y] = (int(40 + 90 * v), int(200 + 55 * v), int(90 + 80 * v), alpha)
    im.save(A + 'textures/block/' + out)

glow('oak_leaves.png', 'construct_leaves.png', 170)
glow('short_grass.png', 'construct_plant.png', 200)
print('done')
