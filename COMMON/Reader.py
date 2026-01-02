import struct

class FStream():
    def __init__(self, data):
        self.cursor = 0
        self.data = data

    def read(self, data_type, data_size):
        result = struct.unpack(data_type, self.data[self.cursor:self.cursor+data_size])[0]
        self.cursor += data_size
        return result
    def seek(self, offset, /, *, relative = False):
        if not relative:
            self.cursor = offset
        else:
            self.cursor += offset
    def tell(self):
        return self.cursor

    def readInt8(self):    return self.read("b", 1)
    def readUInt8(self):   return self.read("B", 1)
    def readInt16(self):   return self.read("h", 2)
    def readUInt16(self):  return self.read("H", 2)
    def readInt32(self):   return self.read("i", 4)
    def readUInt32(self):  return self.read("I", 4)
    def readFloat32(self): return self.read("f", 4)

    def readString(self, length):
        text = ""
        for _ in range(length):
            text += chr(self.readUInt8())
        return text