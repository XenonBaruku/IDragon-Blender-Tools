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
            raise RuntimeError(str("Invalid MSH file or not MSH file from The I of the Dragon."))
        
        _ = self.fileStream.readUInt32()
        _ = self.fileStream.readUInt32()
        _ = self.fileStream.readUInt32()
        _ = self.fileStream.readUInt32()
        _ = self.fileStream.readUInt32()

        faceCount = self.fileStream.readUInt32()
        armatureOriginMatrix = [
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0],
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0],
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 0.0],
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), 1.0],
        ]
        vertexCount = self.fileStream.readUInt32()
        indexCount = self.fileStream.readUInt32()
        meshCount = self.fileStream.readUInt32()
        boneCount = self.fileStream.readUInt32()

        _ = self.fileStream.readUInt32()
        _ = self.fileStream.readUInt32()
        unknownSectionLength = self.fileStream.readUInt32()

        
        self.fileStream.seek(self.bodyEntry)

        positions = []
        weights = []
        normals = []
        UV = []
        for i in range(vertexCount):
            positions.append([self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()])
            weights.append([self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()])
            normals.append([self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()])
            UV.append([self.fileStream.readFloat32(), -self.fileStream.readFloat32() + 1.0]) # Filp UV by Y axis
        vertexInfoDict = {
            'positions': positions,
            'weights': weights,
            'normals': normals,
            'UV': UV
        }
        
        faceInfos = []
        for i in range(faceCount):
            faceInfos.append([self.fileStream.readUInt16(), self.fileStream.readUInt16(), self.fileStream.readUInt16()])

        meshInfos = []
        textures = []
        for i in range(meshCount):
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
                if bone != 0xFFFFFFFF:
                    boneIndices.append(bone)
            mesh['boneIndices'] = boneIndices

            meshTexture = self.fileStream.readString(self.fileStream.readUInt32())
            if meshTexture not in textures:
                textures.append(meshTexture)
            
            mesh['textureIndex'] = textures.index(meshTexture)

            meshInfos.append(mesh)

        boneInfos = []
        for i in range(boneCount):
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

        return vertexInfoDict, faceInfos, meshInfos, boneInfos, textures, armatureOriginMatrix



if __name__ == '__main__':
    file_path = 'D:/IOTD/Geometry/DragonSum/BlueDragon.MSH'
    MSHParser(path=file_path).read()