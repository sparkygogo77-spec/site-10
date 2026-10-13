# Pass 8: settings so Blender shows things the way Minecraft (with Complementary) draws them, and
# saves them into lantern_live.blend so they stay.
#  - EEVEE, the real-time renderer: smooth and fast while you watch (Cycles is for final stills)
#  - sharp Minecraft pixels: no texture smoothing, no film blur
#  - Complementary's look: bloom on glowing things, ray-traced reflections and bounced coloured
#    light, soft fog for the smoke, the same punchy contrast
#  - Open Shading Language off (it crashed Blender)
import bpy

scene = bpy.context.scene
for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
ee = scene.eevee


def setp(obj, attr, val):
    try:
        setattr(obj, attr, val)
    except Exception:
        pass


setp(ee, "taa_samples", 16)                 # viewport: settles in a moment, no grain
setp(ee, "taa_render_samples", 64)
setp(ee, "use_raytracing", True)            # reflections and bounce light, like Complementary's
setp(ee, "ray_tracing_method", "SCREEN")
setp(ee.ray_tracing_options, "resolution_scale", "1") if hasattr(ee, "ray_tracing_options") else None
setp(ee, "use_fast_gi", True)
setp(ee, "use_shadows", True)
setp(ee, "volumetric_tile_size", "4")       # the dry-ice smoke
setp(ee, "volumetric_samples", 64)
setp(ee, "volumetric_end", 120.0)
setp(scene.render, "filter_size", 0.5)      # crisp pixel edges
setp(scene.cycles, "shading_system", False)  # Open Shading Language off
scene.view_settings.view_transform = "AgX"
setp(scene.view_settings, "look", "AgX - Medium High Contrast")
setp(scene.view_settings, "exposure", 0.0)

# every texture drawn as hard Minecraft pixels
for mat in bpy.data.materials:
    if mat.use_nodes and mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE":
                n.interpolation = "Closest"

# the 3D views: live render, bloom showing, no grid or outlines in the way
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "RENDERED"
                    setp(sp.shading, "use_compositor", "ALWAYS")
                    sp.overlay.show_overlays = False
            a.tag_redraw()

# keep it: save into the file
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("Lantern Live: could not save:", e)
