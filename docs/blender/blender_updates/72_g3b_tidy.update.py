# Pass 72 (as 70, for G3 take 2): hide the lantern the watcher reloads after a file switch, and play G3 from the start.
import bpy
for o in bpy.context.scene.objects:
    if o.type in {"MESH", "EMPTY"} and not o.name.startswith(("Charge", "charge", "Cam", "Label")):
        o.hide_viewport = True; o.hide_render = True
bpy.context.scene.frame_set(1)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "RENDERED"
            with bpy.context.temp_override(window=w, area=a):
                if not bpy.context.screen.is_animation_playing:
                    bpy.ops.screen.animation_play()
            break
