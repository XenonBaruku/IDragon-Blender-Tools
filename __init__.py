bl_info = {
    "name": "IDragon Blender Tools",
    "author": "XenonValstrax",
    "blender": (2, 93, 0),
    "version": (1, 1, 0),
    "description": "Import MSH & ANM files from game - The I of the Dragon",
    "warning": "",
    "category": "Import-Export",
}

import bpy
from bpy.types import Context, Menu

from .MSH.MSH_UI import MSH_Import
from .ANM.ANM_UI import ANM_Import


class CustomAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    texturesPath: bpy.props.StringProperty(
        name="Textures directory",
        subtype="DIR_PATH",
    )
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Path to unpacked textures (from Textures.res)")
        layout.prop(self, "texturesPath")

class IDragon_import_menu(bpy.types.Menu):
    bl_label = "The I of the Dragon"
    bl_idname = "IDRAGON_MT_menu_import"

    def draw(self, context):
        self.layout.operator(ANM_Import.bl_idname, text="Animation Files (.ANM)", icon="ACTION")
        self.layout.operator(MSH_Import.bl_idname, text="Mesh Files (.MSH)", icon="MESH_DATA")

def draw_import_menu(self: Menu, context: Context) -> None:
    self.layout.menu(IDragon_import_menu.bl_idname)

# Drag & drop import, for blender version 4.1 or later.
if bpy.app.version >= (4, 1, 0):
    class MSH_FH_drag_import(bpy.types.FileHandler):
        bl_idname = "MSH_FH_drag_import"
        bl_label = "IDragon MSH drag & drop file handler"
        bl_import_operator = "idragon_msh.import"
        bl_file_extensions = ".MSH"

        @classmethod
        def poll_drop(cls, context):
            return (context.area and context.area.type == 'VIEW_3D')
        
    class ANM_FH_drag_import(bpy.types.FileHandler):
        bl_idname = "ANM_FH_drag_import"
        bl_label = "IDragon ANM drag & drop file handler"
        bl_import_operator = "idragon_anm.import"
        bl_file_extensions = ".ANM"

        @classmethod
        def poll_drop(cls, context):
            return (context.area and context.area.type == 'VIEW_3D')

def register() -> None:
    bpy.utils.register_class(MSH_Import)
    bpy.utils.register_class(ANM_Import)
    bpy.utils.register_class(CustomAddonPreferences)
    bpy.utils.register_class(IDragon_import_menu)
    if bpy.app.version >= (4, 1, 0):
        bpy.utils.register_class(MSH_FH_drag_import)
        bpy.utils.register_class(ANM_FH_drag_import)
    bpy.types.TOPBAR_MT_file_import.append(draw_import_menu)
    #bpy.types.TOPBAR_MT_file_export.append(draw_export_menu)
    pass

def unregister() -> None:
    bpy.utils.unregister_class(MSH_Import)
    bpy.utils.register_class(ANM_Import)
    bpy.utils.unregister_class(CustomAddonPreferences)
    bpy.utils.unregister_class(IDragon_import_menu)
    if bpy.app.version >= (4, 1, 0):
        bpy.utils.unregister_class(MSH_FH_drag_import)
        bpy.utils.register_class(ANM_FH_drag_import)
    bpy.types.TOPBAR_MT_file_import.remove(draw_import_menu)
    #bpy.types.TOPBAR_MT_file_export.remove(draw_export_menu)
    pass

if __name__ == "__main__":
    register()