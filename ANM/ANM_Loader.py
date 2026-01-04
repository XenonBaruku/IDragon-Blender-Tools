import bpy
import os
from mathutils import Matrix

from .ANM_Parser import ANMParser


def loadANM(filePath, armature = None, setFakeUser = False, framerate = 0):
    parsedANMData = ANMParser(filePath)
    boneInfos = parsedANMData.read()
    actual_framerate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base if framerate == 0 else framerate
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = int(parsedANMData.duration * actual_framerate) - 1

    fileName = os.path.basename(filePath).split(".")[0]
    action = bpy.data.actions.new(fileName + " (Frames: {})".format(int(parsedANMData.duration * actual_framerate)))
    action.use_fake_user = setFakeUser

    try:
        bpy.data.objects[armature].pose.bones
    except:
        raise TypeError("Invaild armature: {}".format(armature))

    armatureObject = bpy.data.objects[armature]
    if not armatureObject.animation_data:
        armatureObject.animation_data_create()
    armatureObject.animation_data.action = action

    for boneInfo in boneInfos:
        poseBone = armatureObject.pose.bones[boneInfo['name']]
        for frameInfo in boneInfo['frameInfos']:
            if poseBone.parent:
                poseBone.matrix = poseBone.parent.matrix @ Matrix(frameInfo['matrixGlobal']).transposed()
            else:
                poseBone.matrix = Matrix() @ Matrix(frameInfo['matrixGlobal']).transposed()
            frameIndex = boneInfo['frameInfos'].index(frameInfo)
            frame = int(boneInfo['frameInfos'][frameIndex]['duration'] * actual_framerate)
            poseBone.keyframe_insert(data_path="location", frame=frame)
            poseBone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            poseBone.keyframe_insert(data_path="scale", frame=frame)
    
    return action