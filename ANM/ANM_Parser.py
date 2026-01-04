from ..COMMON.Reader import FStream


class ANMParser():
    def __init__(self, path = None, data = None):
        self.path = path
        if data is None:
            with open(path, "rb") as anm_file:
                data = anm_file.read()
        self.fileStream = FStream(data)
    
    def read(self):
        self.bodyEntry = self.fileStream.readUInt32()
        self.magic = self.fileStream.readUInt32()
        if self.magic != 536937236:
            raise RuntimeError("Invalid ANM file or not an ANM file from IotD: {}".format(self.path))
        self.ANMVersion = self.fileStream.readUInt32()
        self.ANMVersionSub = self.fileStream.readUInt32()
        self.ANMVersionLast = self.fileStream.readUInt32()

        self.boneCount = self.fileStream.readUInt32()
        self.duration = self.fileStream.readFloat32()
        unknownMatrix = [
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
            [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()]
        ]

        boneInfos = []
        for i in range(self.boneCount):
            boneInfo = {}
            _ = self.fileStream.readUInt32()
            _ = self.fileStream.readFloat32()
            frameCount = self.fileStream.readUInt32()
            boneInfo['name'] = self.fileStream.readString(self.fileStream.readUInt32())
            boneInfo['parentName'] = self.fileStream.readString(self.fileStream.readUInt32())

            frameInfos = []
            for j in range(frameCount):
                frameInfo = {}
                frameInfo['duration'] = self.fileStream.readFloat32()
                frameInfo['matrixGlobal'] = [
                    [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                    [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                    [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()],
                    [self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32(), self.fileStream.readFloat32()]
                ]
                self.fileStream.cursor += 4 * 11
                frameInfos.append(frameInfo)
            boneInfo['frameInfos'] = frameInfos

            boneInfos.append(boneInfo)

        return boneInfos


if __name__ == '__main__':
    file_path = 'D:/IOTD/Geometry/Dragon/Dragon_Blow.ANM'
    ANMParser(path=file_path).read()