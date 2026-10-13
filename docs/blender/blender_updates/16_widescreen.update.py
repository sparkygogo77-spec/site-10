# Pass 16: widescreen frame (1920 x 1080) so a row of four walls fills the view.
import bpy
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y = 1920, 1080
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            a.tag_redraw()
