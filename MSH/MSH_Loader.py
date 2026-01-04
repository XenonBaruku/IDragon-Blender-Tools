import bpy
import os

from mathutils import Matrix

from .MSH_Parser import MSHParser

WARNINGINFO_SK_NOTFOUND = "{}: Can't find MSH file of another version for shape keys import. Shape keys import aborted."
WARNINGINFO_SK_INCONSISTANT = "{}: Inconsistent vertex or mesh counts with another MSH file. Shape keys import aborted."
WARNINGINFO_SK_INCONSISTANT_MESH = "{}: Inconsistent vertex counts with another MSH file. Shape keys for this mesh part are not imported."

def loadMSH(filePath, collection=None, createCollections=False, mergeMeshes=None, importBoundings=False, importDragonShapKeys=False, importTextures=False, textureInterpolation=None, /, *, texturesDir=None):
    warnings = []


    parsedMSHData = MSHParser(path=filePath)
    vertexInfoDict, faceInfos, meshInfos, boneInfos, textures, armatureOriginMatrix, boundingInfos = parsedMSHData.read()
    
    fileNameFull = os.path.basename(filePath)
    fileName = os.path.basename(filePath).split(".")[0]
    if collection is None:
        master_collection = bpy.context.scene.collection
        if createCollections:
            col = bpy.data.collections.new(fileName)
            master_collection.children.link(col)
        else:
            col = master_collection
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
            if bone.parent:
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
    
    if importDragonShapKeys:
        directoryMSH = os.path.split(filePath)[0]
        print("Import of shape keys enabled, detecting files now...")
        if "small" in fileName.lower():
            print("Small version of mesh detected for imorted MSH. Looking for big version MSH now...")
            basisShape = 'Small'
            deformShape = 'Big'
            MSH2path = os.path.join(directoryMSH, fileNameFull.replace('-Small', '-Big').replace('-small', '-big').replace('Small', 'Big').replace('small', 'big'))
            print("Attempting: " + MSH2path)
            if not os.path.exists(MSH2path):
                print(f"Shape key mesh not found: {MSH2path}\n")
                MSH2path = os.path.join(directoryMSH, fileNameFull.replace('-Small', '').replace('-small', '').replace('Small', '').replace('small', ''))
                print("Attempting: " + MSH2path)
        elif "big" in fileName.lower():
            print("Big version of mesh detected for imorted MSH. Looking for small version MSH now...")
            basisShape = 'Big'
            deformShape = 'Small'
            MSH2path = os.path.join(directoryMSH, fileNameFull.replace('-Big', '-Small').replace('-big', '-small').replace('Big', 'Small').replace('big', 'small'))
            print("Attempting: " + MSH2path)
        else:
            print("Can't find specific suffix from filename of imorted MSH. Imported MSH might be big version of mesh. Looking for small version MSH now...")
            basisShape = 'Big'
            deformShape = 'Small'
            MSH2path = os.path.join(directoryMSH, f'{fileName}Small.MSH')
            print("Attempting: " + MSH2path)
            if not os.path.exists(MSH2path):
                print(f"Shape key mesh not found: {MSH2path}\n")
                MSH2path = os.path.join(directoryMSH, f'{fileName}-Small.MSH')
                print("Attempting: " + MSH2path)

        if (not MSH2path) or MSH2path == "" or (not os.path.exists(MSH2path)):
            print(WARNINGINFO_SK_NOTFOUND.format(fileNameFull))
            warnings.append(WARNINGINFO_SK_NOTFOUND.format(fileNameFull))
            importDragonShapKeys = False
        else:
            print(f"Shape key mesh found: {MSH2path}\n")
            parsedMSHData2 = MSHParser(MSH2path)
            vertexInfoDict2, _, meshInfos2, _, _, _, _ = parsedMSHData2.read()
            if parsedMSHData2.vertexCount != parsedMSHData.vertexCount or parsedMSHData2.meshCount != parsedMSHData.meshCount:
                print(WARNINGINFO_SK_INCONSISTANT.format(fileNameFull))
                warnings.append(WARNINGINFO_SK_INCONSISTANT.format(fileNameFull))
                importDragonShapKeys = False

    #meshName = fileName + '_Group[{}]_Index[{}]_Material[{}]'
    meshesToMerge = {}
    if createCollections:
        colMeshes = bpy.data.collections.new(fileName + '_Meshes')
        colMeshes.color_tag = "COLOR_01"
        col.children.link(colMeshes)
    else:
        colMeshes = col
    for mesh in meshInfos:
        if mergeMeshes == 'NONE':
            meshName = fileName + '_Group[{}]_Index[{}]_Material[{}]'.format(mesh['group'], meshInfos.index(mesh), mesh['textureIndex'])
        elif mergeMeshes == 'GROUP':
            meshName = fileName + '_merged_Group[{}]'.format(mesh['group'])
        elif mergeMeshes == 'TEXTURE':
            meshName = fileName + '_merged_Texture[{}]'.format(textures[mesh['textureIndex']])
        elif mergeMeshes == 'ALL':
            meshName = fileName + '_merged'
        meshNew = bpy.data.meshes.new(meshName)
        obj = bpy.data.objects.new(meshNew.name, meshNew)
        colMeshes.objects.link(obj)
        obj.rotation_mode = 'XYZ'

        meshFaces = []
        for i in range(mesh['faceCount']):
            meshFaces.append([index - mesh['vertexStart'] for index in faceInfos[mesh['faceStart'] // 3 + i]])
        meshNew.from_pydata(vertexInfoDict['positions'][mesh['vertexStart']:mesh['vertexStart'] + mesh['vertexCount']], [], meshFaces)

        if armatureObject:
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
            if boneIndex == 0xFFFFFFFF:
                continue
            VGroup = obj.vertex_groups.new(name=boneInfos[boneIndex]['name'])
            for i in range(mesh['vertexCount']):
                if meshWeights[i][mesh['boneIndices'].index(boneIndex)] > 0.0:
                    VGroup.add([i], meshWeights[i][mesh['boneIndices'].index(boneIndex)], 'ADD')

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
                links.new(UVMapNode.outputs[0], texImage.inputs[0])
                links.new(texImage.outputs[0], diffuseShader.inputs[0])
                if parsedMSHData.renderFlags & (1 << 4):  # Alpha blending
                    links.new(texImage.outputs[1], mixShader.inputs[0])
                else:  # Alpha testing
                    mathNode = nodes.new('ShaderNodeMath')
                    mathNode.location = (-352, -133)
                    mathNode.operation = 'GREATER_THAN'
                    mathNode.inputs[1].default_value = 254 / 255
                    links.new(texImage.outputs[1], mathNode.inputs[0])
                    links.new(mathNode.outputs[0], mixShader.inputs[0])

            else:
                mat = bpy.data.materials[materialName]

            meshNew.materials.append(mat)
            mat_slot = obj.material_slots[0]
            mat_slot.link = 'OBJECT'
            mat_slot.material = mat

        if importDragonShapKeys:
            sk_basis = obj.shape_key_add(name=basisShape)
            sk_basis.interpolation = 'KEY_LINEAR'
            sk_deform = obj.shape_key_add(name=deformShape, from_mix=False)
            sk_deform.interpolation = 'KEY_LINEAR'
            mesh2 = meshInfos2[meshInfos.index(mesh)]

            if len(vertexInfoDict2['positions'][mesh2['vertexStart']:mesh2['vertexStart'] + mesh2['vertexCount']]) == len(meshNew.vertices):
                for i in range(len(meshNew.vertices)):
                    sk_deform.data[i].co = vertexInfoDict2['positions'][mesh2['vertexStart'] + i]
                meshNew.shape_keys.use_relative = True
            else:
                print(WARNINGINFO_SK_INCONSISTANT_MESH.format(meshName))
                warnings.append(WARNINGINFO_SK_INCONSISTANT_MESH.format(meshName))
                
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
        elif mergeMeshes == 'ALL':
            try:
                meshesToMerge[0].append(obj)
            except:
                meshesToMerge[0] = []
                meshesToMerge[0].append(obj)

        returnedObjects.append(obj)

    if mergeMeshes != 'NONE':
        for listObj in meshesToMerge.values():
            mergedMeshes = []
            with bpy.context.temp_override(active_object=listObj[0], selected_editable_objects=listObj):
                bpy.ops.object.select_all(action='DESELECT')
                for mergeObj in listObj:
                    mergeObj.select_set(True)
                    mergedMeshes.append(mergeObj.data)
                bpy.context.view_layer.objects.active = listObj[0]
                bpy.ops.object.join()

                for meshDataMerged in mergedMeshes:
                    if meshDataMerged.users == 0:
                        bpy.data.meshes.remove(meshDataMerged)

    if importBoundings:
        if createCollections:
            colBoundings = bpy.data.collections.new(fileName + "_BoundingPlanes")
            colBoundings.color_tag = "COLOR_05"
            col.children.link(colBoundings)
        else:
            colBoundings = col

        for boundingPlane in boundingInfos:
            meshBoundingPlane = bpy.data.meshes.new("{}_BoundingPlane_{}".format(fileName, boundingInfos.index(boundingPlane)))
            objBoundingPlane = bpy.data.objects.new(meshBoundingPlane.name, meshBoundingPlane)
            colBoundings.objects.link(objBoundingPlane)
            objBoundingPlane.rotation_mode = 'XYZ'

            if len(boundingPlane['points']) == 1:
                meshBoundingPlane.from_pydata(boundingPlane['points'], [], [])
            elif len(boundingPlane['points']) == 2:
                meshBoundingPlane.from_pydata(boundingPlane['points'], [0, 1], [])
            else:
                meshBoundingPlane.from_pydata(boundingPlane['points'], [], [range(len(boundingPlane['points']))])
            
            if armatureObject:
                objBoundingPlane.parent = armatureObject

            if boundingPlane['extraBoundingInfos']:
                for extraBounding in boundingPlane['extraBoundingInfos']:
                    meshBoundingSub = bpy.data.meshes.new("{}_BoundingPlane_{}_Sub_{}".format(fileName, boundingInfos.index(boundingPlane), boundingPlane['extraBoundingInfos'].index(extraBounding)))
                    objBoundingSub = bpy.data.objects.new(meshBoundingSub.name, meshBoundingSub)
                    colBoundings.objects.link(objBoundingSub)
                    objBoundingSub.rotation_mode = 'XYZ'
                    
                    if len(boundingPlane['points']) == 1:
                        meshBoundingPlane.from_pydata(boundingPlane['points'], [], [])
                    elif len(boundingPlane['points']) == 2:
                        meshBoundingPlane.from_pydata(boundingPlane['points'], [0, 1], [])
                    else:
                        meshBoundingSub.from_pydata(extraBounding, [], [range(len(extraBounding))])

                    if armatureObject:
                        objBoundingSub.parent = armatureObject

    if armatureObject:
        bpy.context.view_layer.objects.active = armatureObject
    bpy.ops.object.select_all(action='DESELECT')
    return returnedObjects, warnings