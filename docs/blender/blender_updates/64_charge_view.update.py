# Pass 64: tidy the charge file: hide the lantern the watcher reloads on a file switch, rendered view, play.
import bpy
for o in bpy.data.objects:
    if not o.name.startswith(("Charge", "Cam", "Label", "charge")) and o.type in {"MESH", "EMPTY"}:
        o.hide_viewport = True; o.hide_render = True
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "RENDERED"
                    try:
                        sp.shading.use_compositor = "ALWAYS"
                    except Exception:
                        pass
            a.tag_redraw()
            with bpy.context.temp_override(window=w, area=a):
                if not bpy.context.screen.is_animation_playing:
                    bpy.ops.screen.animation_play()
