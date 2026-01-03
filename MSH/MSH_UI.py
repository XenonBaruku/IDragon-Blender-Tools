import bpy
import os
import addon_utils

from bpy.types import Panel, Operator, OperatorFileListElement
from bpy.props import CollectionProperty, StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper

from .MSH_Loader import loadMSH


class MSH_Import_Panel:
    @staticmethod
    def draw_options(panel: Panel | Operator, context) -> None:
        candidate_modules = [mod for mod in addon_utils.modules() if mod.bl_info["name"] == "IDragon Blender Tools"]
        mod = candidate_modules[0]
        addon_prefs = context.preferences.addons[mod.__name__].preferences
        layout = panel.layout
        box = panel.layout.box()
        box.label(text="Options", icon="SETTINGS")
        col = box.column()
        col.row().label(text="Merge Mesh Parts: ")
        col.row().prop(panel, "mergeMeshes")
        col.separator()
        col.row().prop(panel, "importBoundings")
        col.separator()
        col.row().prop(panel, "importTextures")
        col.separator()
        

        if panel.importTextures:
            #col2 = box.column()
            #col2.row().label(text="Texture Options: ")
            col.row().label(text="Texture Interpolation: ")
            col.row().prop(panel, "textureInterpolation")
            col.separator()
            if addon_prefs.texturesPath == "":
                col.row().label(icon="ERROR", text="Textures directory is not set.")
                col.row().label(text="See addon preferences for the setting.")
                col.separator()


class MSH_Import(bpy.types.Operator, ImportHelper):
    '''Import The I of the Dragon MESH File'''
    bl_idname = "idragon_msh.import"
    bl_label = 'Import MSH'
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = "*.MSH"

    files: CollectionProperty(type=OperatorFileListElement)
    directory : StringProperty(
			subtype='DIR_PATH',
			options={'SKIP_SAVE'}
	)
    filter_glob: StringProperty(default="*.MSH")

    mergeMeshes: EnumProperty(
        #name ="Merge Meshes",
        name = "",
		description = "Whether to merge mesh parts or not",
		items = [
                ("NONE", "None", "No mesh parts would be merged."),
                ("GROUP", "By Groups", "Merge mesh parts by groups."),
				("TEXTURE", "By Textures", "Merge mesh parts by textures."),
			   ],
        default = "NONE"
    )
    importBoundings: BoolProperty(
        name = "Import Bounding Planes", 
        description = "Import 2D planes data stored in MSH files that likely to be bounds.",
        default = False
    )
    importTextures: BoolProperty(
        name = "Import Textures", 
        description = "Import textures and auto setup materials. Make sure textures path in addon preferences is set correctly.",
        default = True
    )
    textureInterpolation: EnumProperty(
        #name ="Interpolation",
        name = "",
		description = "Interpolation mode for imported textures",
		items = [
                ("Linear", "Linear", "Linear interpolation."),
                ("Closest", "Closest", "Closest interpolation."),
				("Cubic", "Cubic", "Cubic interpolation."),
                ("Smart", "Smart", "Smart interpolation.")
			   ],
        default = "Linear"
    )

    def draw(self, context):
        MSH_Import_Panel.draw_options(self, context)
    
    def execute(self, context):
        candidate_modules = [mod for mod in addon_utils.modules() if mod.bl_info["name"] == "IDragon Blender Tools"]
        mod = candidate_modules[0]
        addon_prefs = context.preferences.addons[mod.__name__].preferences

        if self.files:
            folder = (os.path.dirname(self.filepath))
            filepaths = [os.path.join(folder, x.name) for x in self.files]
        else:
            filepaths = [str(self.filepath)]

        if addon_prefs.texturesPath == "" and self.importTextures:
            self.report({"ERROR"}, "Import textures was enabled, while the textures directory in not set in the addon preferences.")
            return {"CANCELLED"}
        
        for filepath in filepaths:
            objs = loadMSH(filepath, None, self.mergeMeshes, self.importBoundings, self.importTextures, self.textureInterpolation, texturesDir=addon_prefs.texturesPath)
        return {"FINISHED"}
    
    def invoke(self, context, event):
        if self.directory:
            context.window_manager.invoke_props_dialog(self)
        else:
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}