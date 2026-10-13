# Pass 60: keep the texture designs playing (J: "animations aren't moving"). Restarts playback, loops the
# timeline, and hides the lantern the watcher dropped onto the P1 wall when it reloaded.
import bpy
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 48
for o in bpy.data.objects:
    if o.name.lower().startswith("lantern") and not o.name.startswith("Label"):
        o.hide_viewport = True; o.hide_render = True
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            with bpy.context.temp_override(window=w, area=a):
                if not bpy.context.screen.is_animation_playing:
                    bpy.ops.screen.animation_play()
            break
print("playing", [o.name for o in bpy.data.objects if o.hide_viewport][:10])
