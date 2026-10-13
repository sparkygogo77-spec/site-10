# Pass 12: higher-quality live view (your graphics card can take it). Watch these values change in
# the Render tab as this lands:
#  Sampling > Viewport Samples 32 | Shadows: Rays 2, Steps 10, Volume Shadows on
#  Raytracing: Resolution 1:1, Max Roughness 0.6 | Volumes: Tile Size 2 px, Samples 128
#  Film: Filter Size 0.50 px
import bpy
scene = bpy.context.scene
ee = scene.eevee
changed = []
def setp(obj, attr, val):
    try:
        setattr(obj, attr, val)
        changed.append(attr)
    except Exception as e:
        print("Lantern Live: could not set", attr, e)
setp(ee, "taa_samples", 32)
setp(ee, "taa_render_samples", 128)
setp(ee, "shadow_ray_count", 2)
setp(ee, "shadow_step_count", 10)
setp(ee, "use_volumetric_shadows", True)
setp(ee, "volumetric_shadow_samples", 32)
setp(ee, "volumetric_tile_size", "2")
setp(ee, "volumetric_samples", 128)
setp(ee, "use_raytracing", True)
setp(ee, "ray_tracing_method", "SCREEN")
opts = getattr(ee, "ray_tracing_options", None)
if opts is not None:
    setp(opts, "resolution_scale", "1")
    setp(opts, "use_denoise", True)
setp(ee, "use_fast_gi", True)
setp(ee, "light_threshold", 0.01)
setp(scene.render, "filter_size", 0.5)
setp(scene.render, "preview_pixel_size", "1")
print("Lantern Live quality:", ", ".join(changed))
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception:
        pass
