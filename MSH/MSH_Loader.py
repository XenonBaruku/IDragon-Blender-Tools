import bpy
import os

from mathutils import Matrix

from .MSH_Parser import MSHParser

def loadMSH(filePath, collection=None, mergeMeshes=None, importTextures=False, textureInterpolation=None, /, *, texturesDir = None):
    parser = MSHParser(path=filePath)
    vertexInfoDict, faceInfos, meshInfos, boneInfos, textures, armatureOriginMatrix = parser.read()

    fileName = os.path.basename(filePath).split(".")[0]
    if collection is None:
        master_collection = bpy.context.scene.collection
        col = bpy.data.collections.new(fileName)
        master_collection.children.link(col)
    else:
        col = collection

    returnedObjects = []

    armatureObject = None
    if boneInfos is not None and len(boneInfos) > 0:
        armatureName = fileName + '_Armature'
        armatureData = bpy.data.armatures.new(armatureName)
        armatureObject = bpy.data.objects.new(armatureName, armatureData)
        if bpy.app.version >= (4, 0, 0):
            armatureData.relation_line_position = 'HEAD'
        #armatureData.display_type = 'STICK'
        col.objects.link(armatureObject)

        bpy.context.view_layer.objects.active = armatureObject
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        boneRoot = armatureData.edit_bones.new('Root')
        boneRoot.head = (0.0, 0.0, 0.0)
        boneRoot.tail = (0.0, 0.0, 1.0)
        boneRoot.matrix = Matrix(armatureOriginMatrix).transposed()
        for bone in boneInfos:
            boneNew = armatureData.edit_bones.new(bone['name'])
            matrixGlobal = Matrix(bone['matrixGlobal'])
            matrixGlobal.transpose()
            matrixLocal = Matrix(bone['matrixLocal'])
            matrixLocal.transpose()
            boneNew.head = (0.0, 0.0, 0.0)
            boneNew.tail = (0.0, 0.0, 1.0)

            if bone['parentIndex'] != 0xFFFFFFFF:
                parentName = boneInfos[bone['parentIndex']]['name']
                boneNew.parent = armatureData.edit_bones[parentName]
                boneNew.matrix = boneNew.parent.matrix @ matrixLocal
            else:
                boneNew.parent = boneRoot
                boneNew.matrix = boneRoot.matrix @ matrixLocal
            boneNew.inherit_scale = "NONE"

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        for bone in armatureData.bones:
            if bone.parent is not None:
                bone['baserots'] = bone.matrix.inverted().to_quaternion()
                bone['baseposs'] = (bone.parent.matrix_local.inverted() @ bone.matrix_local).to_translation()
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        armatureObject.pose.bones['Root'].matrix = Matrix()
        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        armatureData.edit_bones.remove(armatureData.edit_bones['Root'])
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        returnedObjects.append(armatureObject)

    if bpy.context.scene.view_settings.view_transform != 'Standard':
        bpy.context.scene.view_settings.view_transform = 'Standard'  # Closer to game color profile.

    #meshName = fileName + '_Group[{}]_Index[{}]_Material[{}]'
    meshesToMerge = {}
    for mesh in meshInfos:
        if mergeMeshes == 'NONE':
            meshName = fileName + '_Group[{}]_Index[{}]_Material[{}]'.format(mesh['group'], meshInfos.index(mesh), mesh['textureIndex'])
        elif mergeMeshes == 'GROUP':
            meshName = fileName + '_merged_Group[{}]'.format(mesh['group'])
        elif mergeMeshes == 'TEXTURE':
            meshName = fileName + '_merged_Material[{}]'.format(mesh['textureIndex'])
        meshNew = bpy.data.meshes.new(meshName)
        obj = bpy.data.objects.new(meshNew.name, meshNew)
        col.objects.link(obj)
        obj.rotation_mode = 'XYZ'

        meshFaces = []
        for i in range(mesh['faceCount']):
            meshFaces.append([index - mesh['vertexStart'] for index in faceInfos[mesh['faceStart'] // 3 + i]])
        meshNew.from_pydata(vertexInfoDict['positions'][mesh['vertexStart']:mesh['vertexStart'] + mesh['vertexCount']], [], meshFaces)

        if armatureObject is not None:
                obj.parent = armatureObject
                armatureModifier = obj.modifiers.new('Armature', 'ARMATURE')
                armatureModifier.object = armatureObject
        
        bpy.context.view_layer.objects.active = obj

        if hasattr(meshNew, 'create_normals_split'):
            meshNew.create_normals_split()
        meshNew.polygons.foreach_set('use_smooth', [True]*len(meshNew.polygons))
        meshNew.normals_split_custom_set_from_vertices(vertexInfoDict['normals'][mesh['vertexStart']:mesh['vertexStart'] + mesh['vertexCount']])
        if hasattr(meshNew, 'use_auto_smooth'):
            meshNew.use_auto_smooth = True
        if hasattr(meshNew, 'free_normals_split'):
            meshNew.free_normals_split()

        meshWeights = vertexInfoDict['weights'][mesh['vertexStart']:mesh['vertexStart'] + mesh['vertexCount']]
        for boneIndex in mesh['boneIndices']:
            if mesh['boneIndices'].index(boneIndex) < 3:
                VGroup = obj.vertex_groups.new(name=boneInfos[boneIndex]['name'])
                for i in range(mesh['vertexCount']):
                    if meshWeights[i][mesh['boneIndices'].index(boneIndex)] > 0:
                        VGroup.add([i], meshWeights[i][mesh['boneIndices'].index(boneIndex)], 'ADD')
            else:
                VGroup = obj.vertex_groups.new(name=boneInfos[boneIndex]['name'])
                for i in range(mesh['vertexCount']):
                    if meshWeights[i][0] + meshWeights[i][1] + meshWeights[i][0] != 1.0:
                        VGroup.add([i], (1 - meshWeights[i][0] - meshWeights[i][1] - meshWeights[i][2]), 'ADD')

        UVLayer = meshNew.uv_layers.new(name='UVMap')
        for face in meshNew.polygons:
            for vertexIndex, loopIndex in zip(face.vertices, face.loop_indices):
                UVLayer.data[loopIndex].uv = vertexInfoDict['UV'][mesh['vertexStart'] + vertexIndex]

        if importTextures:
            materialName = f'{fileName}_Material_{mesh["textureIndex"]}'
            if materialName not in bpy.data.materials:
                mat = bpy.data.materials.new(name=materialName)

                mat.use_nodes = True
                mat.blend_method = "HASHED"
                if bpy.app.version < (4,2,0):
                    mat.shadow_method = "HASHED"
                nodes = mat.node_tree.nodes
                nodes.clear()

                outputMaterial = nodes.new('ShaderNodeOutputMaterial')
                outputMaterial.location = (200, 100)
                diffuseShader = nodes.new('ShaderNodeBsdfDiffuse')
                diffuseShader.location = (-362.2864685058594, 8.5)
                transparentShader = nodes.new('ShaderNodeBsdfTransparent')
                transparentShader.location = (-355.2864685058594, 108.5)
                mixShader = nodes.new('ShaderNodeMixShader')
                mixShader.location = (-71, 75.6)
                mixShader.inputs[0].default_value = 1.0

                texImage = nodes.new('ShaderNodeTexImage')
                texImage.location = (-719, 75.23175048828125)
                if textureInterpolation:
                    texImage.interpolation = textureInterpolation

                texturePath = os.path.join(texturesDir, textures[mesh["textureIndex"]])
                if os.path.exists(texturePath):
                    texImage.image = bpy.data.images.load(texturePath)
                else:
                    print("WARNING: MSH texture '{}' is not found in textures directory. Attempting different formats now...".format(textures[mesh["textureIndex"]]))
                    if '.tga' in textures[mesh["textureIndex"]].lower():
                        texturePath = os.path.join(texturesDir, textures[mesh["textureIndex"]].replace('.tga', '.dds').replace('.TGA', '.DDS'))
                    elif '.dds' in textures[mesh["textureIndex"]].lower():
                        texturePath = os.path.join(texturesDir, textures[mesh["textureIndex"]].replace('.tga', '.dds').replace('.TGA', '.DDS'))
                    try:
                        texImage.image = bpy.data.images.load(texturePath)
                    except:
                        pass

                texImage.image.alpha_mode = 'CHANNEL_PACKED'
                
                UVMapNode = nodes.new('ShaderNodeUVMap')
                UVMapNode.location = (-974, 32.5)
                UVMapNode.uv_map = UVLayer.name

                links = mat.node_tree.links
                links.new(mixShader.outputs[0], outputMaterial.inputs[0])
                links.new(transparentShader.outputs[0], mixShader.inputs[1])
                links.new(diffuseShader.outputs[0], mixShader.inputs[2])
                links.new(texImage.outputs[0], diffuseShader.inputs[0])
                links.new(texImage.outputs[1], mixShader.inputs[0])
                links.new(UVMapNode.outputs[0], texImage.inputs[0])

            else:
                mat = bpy.data.materials[materialName]

            meshNew.materials.append(mat)
            mat_slot = obj.material_slots[0]
            mat_slot.link = 'OBJECT'
            mat_slot.material = mat

            if mergeMeshes == 'GROUP':
                try:
                    meshesToMerge[mesh['group']].append(obj)
                except:
                    meshesToMerge[mesh['group']] = []
                    meshesToMerge[mesh['group']].append(obj)
            elif mergeMeshes == 'TEXTURE':
                try:
                    meshesToMerge[mesh['textureIndex']].append(obj)
                except:
                    meshesToMerge[mesh['textureIndex']] = []
                    meshesToMerge[mesh['textureIndex']].append(obj)

            returnedObjects.append(obj)

    if mergeMeshes != 'NONE':
        for listObj in meshesToMerge.values():
            with bpy.context.temp_override(active_object=listObj[0], selected_editable_objects=listObj):
                bpy.ops.object.select_all(action='DESELECT')
                for groupObj in listObj:
                    groupObj.select_set(True)
                bpy.context.view_layer.objects.active = listObj[0]
                bpy.ops.object.join()

    bpy.ops.object.select_all(action='DESELECT')        
    return returnedObjects