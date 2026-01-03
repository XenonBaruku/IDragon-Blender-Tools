import bpy
import os
from mathutils import Matrix

from .ANM_Parser import ANMParser

def loadANM(filePath, armature = None, setFakeUser = False, framerate = 0):
    parser = ANMParser(filePath)
    boneInfos = parser.read()
    actual_framerate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base if framerate == 0 else framerate
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = int(parser.duration * actual_framerate)

    fileName = os.path.basename(filePath).split(".")[0]
    action = bpy.data.actions.new(fileName)
    action.use_fake_user = setFakeUser

    if armature:
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
                if frameIndex == 0:
                    poseBone.keyframe_insert(data_path="location", frame=boneInfo['frameInfos'].index(frameInfo))
                    poseBone.keyframe_insert(data_path="rotation_quaternion", frame=boneInfo['frameInfos'].index(frameInfo))
                    poseBone.keyframe_insert(data_path="scale", frame=boneInfo['frameInfos'].index(frameInfo))
                else:
                    frame = int(boneInfo['frameInfos'][frameIndex - 1]['duration'] * actual_framerate)
                    poseBone.keyframe_insert(data_path="location", frame=frame)
                    poseBone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    poseBone.keyframe_insert(data_path="scale", frame=frame)

    # # F-Curve
    # dataPath = "pose.bones[\"{}\"].{}"
    # for boneInfo in boneInfos:
    #     print(boneInfo['name'])
    #     fcurve_loc_x = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "location"), index=0)
    #     fcurve_loc_y = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "location"), index=1)
    #     fcurve_loc_z = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "location"), index=2)

    #     fcurve_rot_w = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "rotation_quaternion"), index=0)
    #     fcurve_rot_x = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "rotation_quaternion"), index=1)
    #     fcurve_rot_y = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "rotation_quaternion"), index=2)
    #     fcurve_rot_z = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "rotation_quaternion"), index=3)

    #     fcurve_scl_x = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "scale"), index=0)
    #     fcurve_scl_y = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "scale"), index=1)
    #     fcurve_scl_z = action.fcurves.new(data_path=dataPath.format(boneInfo['name'], "scale"), index=2)
    #     armatureObject.animation_data.action_slot = action.slots[0]
    #     for frameInfo in boneInfo['frameInfos']:
    #         frame = int(frameInfo['timecode'] * actual_framerate)
    #         print("{}: {}".format(frame, frameInfo['matrixGlobal']))
    #         if boneInfo['parentName'] == "":
    #             matrix = Matrix() @ Matrix(frameInfo['matrixGlobal']).transposed()
    #         else:
    #             matrix = armatureObject.pose.bones[boneInfo['parentName']].matrix @ Matrix(frameInfo['matrixGlobal']).transposed()
    #         loc, rot, scl = matrix.decompose()

    #         keyframe = fcurve_loc_x.keyframe_points.insert(frame, loc[0])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
    #         keyframe = fcurve_loc_y.keyframe_points.insert(frame, loc[1])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
    #         keyframe = fcurve_loc_z.keyframe_points.insert(frame, loc[2])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"

    #         keyframe = fcurve_rot_w.keyframe_points.insert(frame, rot[0])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
    #         keyframe = fcurve_rot_x.keyframe_points.insert(frame, rot[1])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
    #         keyframe = fcurve_rot_y.keyframe_points.insert(frame, rot[2])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
    #         keyframe = fcurve_rot_z.keyframe_points.insert(frame, rot[3])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
            
    #         keyframe = fcurve_scl_x.keyframe_points.insert(frame, scl[0])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
    #         keyframe = fcurve_scl_y.keyframe_points.insert(frame, scl[1])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"
    #         keyframe = fcurve_scl_z.keyframe_points.insert(frame, scl[2])
    #         keyframe.handle_left_type = "VECTOR"
    #         keyframe.handle_right_type = "VECTOR"


    # # test
    # if armature:
    #     armatureObject = bpy.data.objects[armature]

    #     for boneInfo in boneInfos:
    #         poseBone = armatureObject.pose.bones[boneInfo['name']]
    #         if poseBone.parent:
    #             poseBone.matrix = poseBone.parent.matrix @ Matrix(boneInfo['frameInfos'][0]['matrixGlobal']).transposed()
    #         else:
    #             poseBone.matrix = Matrix() @ Matrix(boneInfo['frameInfos'][0]['matrixGlobal']).transposed()