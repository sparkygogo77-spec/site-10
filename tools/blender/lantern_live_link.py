bl_info = {
    "name": "Lantern Live Link",
    "author": "Claude for J",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar (N) > Lantern Live",
    "description": "Watches a folder and reloads the lantern the moment Claude changes it",
    "category": "3D View",
}

"""Lantern Live Link: keeps the open Lantern Live scene in step with Claude's work.

Every second it looks in the watched folder (the folder the .blend is in, unless you pick
another) for:
- lantern_model.npz: the lantern's model; when it changes, the Lantern object is rebuilt in place.
- *.update.py: small scene changes (lights, glow, camera); each new or changed one is run once.
It writes live_status.txt and, when asked, renders into renders/, so Claude can see the result.

It only ever runs files from that one folder. Switch it off with the Watch button.
"""
import os, time
import bpy
import numpy as np

_state = {"model_mtime": 0.0, "done": {}, "status": "Not watching", "timer": False}


def _folder(scene):
    f = bpy.path.abspath(scene.lantern_live_folder) if scene.lantern_live_folder else ""
    if not f and bpy.data.filepath:
        f = os.path.dirname(bpy.data.filepath)
    return f


def _write_status(folder, text):
    _state["status"] = text
    try:
        with open(os.path.join(folder, "live_status.txt"), "w") as fh:
            fh.write(time.strftime("%H:%M:%S ") + text + "\n")
    except OSError:
        pass
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == "VIEW_3D":
                a.tag_redraw()


def load_model(path):
    d = np.load(path)
    quads, col, kind = d["quads"], d["col"], d["kind"]
    verts = quads.reshape(-1, 3)
    me = bpy.data.meshes.new("lantern")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(col, np.float32) / 255.0) ** 2.2
    attr = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    attr.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    obj = bpy.data.objects.get("Lantern")
    if obj is None:
        obj = bpy.data.objects.new("Lantern", me)
        obj.scale = (1 / 16,) * 3
        bpy.context.scene.collection.objects.link(obj)
        old = None
    else:
        old = obj.data
        for m in old.materials:
            me.materials.append(m)
        obj.data = me
    me.polygons.foreach_set("material_index", np.asarray(kind, np.int32))
    if old is not None and old.users == 0:
        bpy.data.meshes.remove(old)
    return len(quads)


def _tick():
    scene = bpy.context.scene
    if not getattr(scene, "lantern_live_watch", False):
        _state["timer"] = False
        return None
    folder = _folder(scene)
    if not folder or not os.path.isdir(folder):
        _write_status(folder or ".", "Pick a folder to watch")
        return 1.0
    try:
        mp = os.path.join(folder, "lantern_model.npz")
        if os.path.exists(mp):
            mt = os.path.getmtime(mp)
            if mt != _state["model_mtime"] and time.time() - mt > 0.5:
                n = load_model(mp)
                _state["model_mtime"] = mt
                _write_status(folder, f"Lantern reloaded ({n:,} pixel faces)")
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".update.py"):
                continue
            p = os.path.join(folder, name)
            mt = os.path.getmtime(p)
            if _state["done"].get(name) == mt or time.time() - mt < 0.5:
                continue
            _state["done"][name] = mt
            with open(p, encoding="utf-8") as fh:
                code = fh.read()
            exec(compile(code, p, "exec"), {"bpy": bpy, "np": np, "__name__": "lantern_update", "FOLDER": folder})
            _write_status(folder, f"Applied {name}")
    except Exception as e:  # keep watching; say what went wrong
        _write_status(folder, f"Error: {e}")
    return 1.0


def _watch_changed(self, context):
    if context.scene.lantern_live_watch and not _state["timer"]:
        _state["timer"] = True
        _state["model_mtime"] = 0.0
        bpy.app.timers.register(_tick, first_interval=0.2)
    elif not context.scene.lantern_live_watch:
        _state["status"] = "Not watching"


class LANTERNLIVE_OT_render(bpy.types.Operator):
    bl_idname = "lantern_live.render"
    bl_label = "Render still"
    bl_description = "Render the current frame into renders/ in the watched folder"

    def execute(self, context):
        folder = _folder(context.scene)
        out = os.path.join(folder, "renders")
        os.makedirs(out, exist_ok=True)
        context.scene.render.filepath = os.path.join(out, time.strftime("lantern_%H%M%S.png"))
        bpy.ops.render.render(write_still=True)
        _write_status(folder, "Rendered " + os.path.basename(context.scene.render.filepath))
        return {"FINISHED"}


class LANTERNLIVE_PT_panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lantern Live"
    bl_label = "Lantern Live Link"

    def draw(self, context):
        s = context.scene
        col = self.layout.column()
        col.prop(s, "lantern_live_watch", text="Watching" if s.lantern_live_watch else "Watch for Claude's changes",
                 toggle=True, icon="PLAY" if not s.lantern_live_watch else "PAUSE")
        col.prop(s, "lantern_live_folder", text="Folder")
        col.label(text=_state["status"])
        ctl = bpy.data.objects.get("Lantern Controls")
        if ctl is not None:
            col.separator()
            col.prop(ctl, '["charge"]', text="Charge", slider=True)
            col.prop(ctl, '["turntable"]', text="Turntable", slider=True)
        col.separator()
        col.operator("lantern_live.render", icon="RENDER_STILL")


def register():
    bpy.types.Scene.lantern_live_folder = bpy.props.StringProperty(
        name="Folder", subtype="DIR_PATH", description="Where Claude drops updates (empty: the .blend's folder)")
    bpy.types.Scene.lantern_live_watch = bpy.props.BoolProperty(name="Watch", default=False, update=_watch_changed)
    bpy.utils.register_class(LANTERNLIVE_OT_render)
    bpy.utils.register_class(LANTERNLIVE_PT_panel)


def unregister():
    bpy.utils.unregister_class(LANTERNLIVE_PT_panel)
    bpy.utils.unregister_class(LANTERNLIVE_OT_render)
    del bpy.types.Scene.lantern_live_watch
    del bpy.types.Scene.lantern_live_folder


if __name__ == "__main__":
    register()
