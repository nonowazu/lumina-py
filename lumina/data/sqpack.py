from io import BufferedReader
from functools import partial
from enum import IntEnum, auto

from lumina.data.structs import PlatformId

# TODO: remove later once binary reader is in place
int_from_little = partial(int.from_bytes, byteorder='little')

class HeaderNotSupported(Exception):
    pass

class FileType(IntEnum):
    Empty = auto()
    Standard = auto()
    Model = auto()
    Texture = auto()

class Header:
    # TODO: replace BufferedReader with a LuminaBinaryReader analogue
    def __init__(self, file: BufferedReader):
        self.magic: bytes = file.read(8)
        self.platform_id: PlatformId = int_from_little(file.read(1))
        # TODO: handle inside BinaryReader analogue so you get PS3 support
        if self.platform_id == PlatformId.PS3:
            raise HeaderNotSupported(PlatformId.PS3.name)
        self.__unknown = file.read(3)
        self.size = int_from_little(file.read(4))
        self.version = int_from_little(file.read(4))
        self.type = int_from_little(file.read(4))

    def __repr__(self) -> str:
        return f'<sqpack.Header {PlatformId(self.platform_id).name}, ver:{self.version}>'

class IndexHeader:
    def __init__(self, data: bytes):
        self.size = int_from_little(data[0:4])
        self.version = int_from_little(data[4:8])
        self.index_data_offset = int_from_little(data[8:12])
        self.index_data_size = int_from_little(data[12:16])
        self.index_data_hash = data[16:80]
        self.number_of_data_file = int_from_little(data[80:84], byteorder='little')
        self.synonym_data_offset = int_from_little(data[84:88], byteorder='little')
        self.synonym_data_size = int_from_little(data[88:92], byteorder='little')
        self.synonym_data_hash = data[92:156]
        self.empty_block_data_offset = int_from_little(data[156:160], byteorder='little')
        self.empty_block_data_size = int_from_little(data[160:164], byteorder='little')
        self.empty_block_data_hash = data[164:228]
        self.dir_index_data_offset = int_from_little(data[228:232], byteorder='little')
        self.dir_index_data_size = int_from_little(data[232:236], byteorder='little')
        self.dir_index_data_hash = data[236:300]
        self.index_type = int_from_little(data[300:304], byteorder='little')
        self.reserved = data[304:960]
        self.hash = data[960:1024]

    def __repr__(self) -> str:
        return f'<sqpack.IndexHeader size:{self.size}>'


class FileInfo:
    def __init__(self, data: bytes, offset: int):
        self.size = int_from_little(data[0:4])
        self.type = FileType(int_from_little(data[4:8]))
        self.raw_file_size = int_from_little(data[8:12])
        self.unknown = [
            int_from_little(data[12:16]),
            int_from_little(data[16:20]),
        ]
        self.number_of_blocks = int_from_little(data[20:24])
        self.offset = offset
