# Pass 9: stone-detailed jade at 128 pixels per block (grain, cloudy mottling, fibrous veins,
# mineral flecks, chips, jagged cracks). Reloads the jade textures from the folder.
import os
import bpy
for img in bpy.data.images:
    if img.name.startswith("jade_"):
        img.filepath = os.path.join(FOLDER, img.name)
        img.reload()
