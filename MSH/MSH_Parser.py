from ..COMMON.Reader import FStream


class MSHParser():
    def __init__(self, path = None, data = None):
        self.path = path
        if data is None:
            with open(path, "rb") as msh_file:
                data = msh_file.read()
        self.fileStream = FStream(data)
    
    def read(self):
        self.bodyEntry = self.fileStream.readUInt32()
        self.magic = self.fileStream.readUInt32()
        if self.magic != 536938242:
            raise RuntimeError("Invalid MSH file or not a MSH file from IotD: {}".format(self.path))
        
        self.MSHVersion = self.fileStream.readUInt32()
        self.MSHVersionSub = self.fileStream.readUInt32()
        self.MSHVersionLast = self.fileStream.readUInt32()

        # Render Flags: Binary array that controls how mesh was rendered.
        #   1st byte
        #       2nd bit - Unknown. May lead to access violation error while exiting the game when set to 1
        #       5th bit - Alpha mode. Use alpha testing (0) or alpha blending (1) for transparency.
        self.renderFlags = self.fileStream.readUInt32()
        
        _ = self.fileStream.readUInt32()

        self.faceCount = self.fileStream.readUInt32()
        armatureOriginMatrix = [
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0],
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0],
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0],
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 1.0],
        ]
        self.vertexCount = self.fileStream.readUInt32()
        self.indexCount = self.fileStream.readUInt32()
        self.meshCount = self.fileStream.readUInt32()
        self.boneCount = self.fileStream.readUInt32()

        _ = self.fileStream.readUInt32()
        _ = self.fileStream.readUInt32()
        boundingSectionSize = self.fileStream.readUInt32()

        self.fileStream.seek(self.bodyEntry)

        positions = []
        weights = []
        normals = []
        UV = []
        for i in range(self.vertexCount):
            positions.append([self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()])
            weightsRaw = [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()]
            weights.append([weightsRaw[0], weightsRaw[1], weightsRaw[2], 1.0 - weightsRaw[0] - weightsRaw[1] - weightsRaw[2]])
            normals.append([self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()])
            UV.append([self.fileStream.readFloat32(), -self.fileStream.readFloat32() + 1.0]) # Filp UV by Y axis
        vertexInfoDict = {
            'positions': positions,
            'weights': weights,
            'normals': normals,
            'UV': UV
        }
        
        faceInfos = []
        for i in range(self.faceCount):
            faceInfos.append([self.fileStream.readUInt16(), self.fileStream.readUInt16(), self.fileStream.readUInt16()])

        meshInfos = []
        textures = []
        for i in range(self.meshCount):
            mesh = {}
            length = self.fileStream.readUInt32()
            mesh['group'] = self.fileStream.readUInt32()

            mesh['vertexStart'] = self.fileStream.readUInt32()
            mesh['vertexCount'] = self.fileStream.readUInt32()

            mesh['faceStart'] = self.fileStream.readUInt32()
            meshIndexCount = self.fileStream.readUInt32()
            mesh['faceCount'] = self.fileStream.readUInt32()

            boneIndices = []
            for k in range(4):
                bone = self.fileStream.readUInt32()
                boneIndices.append(bone)
            mesh['boneIndices'] = boneIndices

            meshTexture = self.fileStream.readString(self.fileStream.readUInt32())
            if meshTexture not in textures:
                textures.append(meshTexture)
            
            mesh['textureIndex'] = textures.index(meshTexture)

            meshInfos.append(mesh)

        boneInfos = []
        for i in range(self.boneCount):
            bone = {}
            bone['parentIndex'] = self.fileStream.readUInt32()
            bone['matrixGlobal'] = [
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()]
            ]
            bone['matrixLocal'] = [
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()]
            ]
            bone['name'] = self.fileStream.readString(self.fileStream.readUInt32())
            boneInfos.append(bone)
        
        boundingSectionEnd = self.fileStream.tell() + boundingSectionSize
        boundingInfos = []
        boundingPlaneCount = self.fileStream.readUInt32()
        for i in range(boundingPlaneCount):
            blockSize = self.fileStream.readUInt32()
            blockEnd = self.fileStream.tell() + blockSize
            pointCount = self.fileStream.readUInt32()

            boundingInfo = {
                'points': [ [self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0] for j in range(pointCount) ],
            }

            boundingCountExtra = self.fileStream.readUInt32()
            extraBoundingInfos = []
            for k in range(boundingCountExtra):
                pointCountExtra = self.fileStream.readUInt32()
                extraBounding = [ [self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0] for l in range(pointCountExtra)  ]
                extraBoundingInfos.append(extraBounding)
            
            boundingInfo['extraBoundingInfos'] = extraBoundingInfos
                
            
            self.fileStream.seek(blockEnd)
            boundingInfos.append(boundingInfo)

        self.fileStream.seek(boundingSectionEnd)
        MSHInfo = self.fileStream.readString(self.fileStream.readUInt32())
        print(f"\nMSH Info: {MSHInfo}\n")

        return vertexInfoDict, faceInfos, meshInfos, boneInfos, textures, armatureOriginMatrix, boundingInfos



if __name__ == '__main__':
    file_path = 'D:/IOTD/Geometry/DragonSum/BlueDragon.MSH'
    MSHParser(path=file_path).read()