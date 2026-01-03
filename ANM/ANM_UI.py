import bpy
import os

from bpy.types import Panel, Operator, OperatorFileListElement
from bpy.props import CollectionProperty, StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper

from .ANM_Loader import loadANM

class ANM_Import_Panel:
    @staticmethod
    def draw_options(panel: Panel | Operator, context) -> None:
        layout = panel.layout
        box = panel.layout.box()
        box.label(text="Options", icon="SETTINGS")
        col = box.column()
        col.row().label(text="Armature: ")
        col.row().prop_search(panel, "armature", bpy.context.scene, "objects", text="")
        col.separator()
        col.row().label(text="Frame Rate: ")
        col.row().prop(panel, "framerate")
        col.row().label(text="(Set 0 to use scene framerate)")
        col.separator()
        col.row().prop(panel, "addFakeUser")
        col.separator()

class ANM_Import(bpy.types.Operator, ImportHelper):
    '''Import The I of the Dragon ANM Files'''
    bl_idname = "idragon_anm.import"
    bl_label = 'Import ANM'
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = "*.ANM"

    files: CollectionProperty(type=OperatorFileListElement)
    directory : StringProperty(
			subtype='DIR_PATH',
			options={'SKIP_SAVE'}
	)
    filter_glob: StringProperty(default="*.ANM")

    armature: StringProperty( 
        name = "", 
        description = "Set the armature that imported animations attach to."
    )
    framerate: IntProperty(
        name = "",
        description = "Set framerate that imported animations base on.\n0 = Use scene output framerate settings"
    )
    addFakeUser: BoolProperty(
        name = "Add Fake User", 
        description = "Add fake user to imported animations to prevent them from being deleted while saving blend files.",
        default = False
    )

    is_armature_set = False
    def draw(self, context):
        ANM_Import_Panel.draw_options(self, context)
        if not self.is_armature_set:
            try:
                if bpy.data.armatures.get(bpy.context.object.name):
                    self.armature = bpy.context.object.name
                else:
                    self.armature = bpy.data.armatures[len(bpy.data.armatures) - 1].name
                self.is_armature_set = True
            except:
                pass

    def execute(self, context):
        if self.files:
            folder = (os.path.dirname(self.filepath))
            filepaths = [os.path.join(folder, x.name) for x in self.files]
        else:
            filepaths = [str(self.filepath)]

        for filepath in filepaths:
            anms = loadANM(filepath, self.armature, self.addFakeUser)
        return {"FINISHED"}