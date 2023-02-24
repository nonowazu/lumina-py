import os
from io import BufferedReader
import enum
import zlib
from typing import List, Dict, Tuple


class SqPackCatergories(enum.IntEnum):
    COMMON = 0x0
    BGCOMMON = 0x1
    BG = 0x2
    CUT = 0x3
    CHARA = 0x4
    SHADER = 0x5
    UI = 0x6
    SOUND = 0x7
    VFX = 0x8
    UI_SCRIPT = 0x9
    EXD = 0xA
    GAME_SCRIPT = 0xB
    MUSIC = 0xC
    SQPACK_TEST = 0x12
    DEBUG = 0x13


class SqPackPlatformId(enum.IntEnum):
    WIN32 = 0x0
    PS3 = 0x1
    PS4 = 0x2


class SqPackFileType(enum.IntEnum):
    EMPTY = 1
    STANDARD = 2
    MODEL = 3
    TEXTURE = 4


class DatBlockType(enum.IntEnum):
    COMPRESSED = 4713
    UNCOMPRESSED = 32000


class SqPackFileInfo:  # pylint: disable=too-few-public-methods
    def __init__(self, data: bytes, offset: int):
        self.header_size = int.from_bytes(data[0:4], byteorder='little')
        self.type = SqPackFileType(int.from_bytes(data[4:8], byteorder='little'))
        self.raw_file_size = int.from_bytes(data[8:12], byteorder='little')
        self.unknown = [
            int.from_bytes(data[12:16], byteorder='little'),
            int.from_bytes(data[16:20], byteorder='little'),
        ]
        self.number_of_blocks = int.from_bytes(data[20:24], byteorder='little')
        self.offset = offset


class DatStdFileBlockInfos:  # pylint: disable=too-few-public-methods
    def __init__(self, data: bytes):
        self.offset = int.from_bytes(data[0:4], byteorder='little')
        self.compressed_size = int.from_bytes(data[4:6], byteorder='little')
        self.uncompressed_size = int.from_bytes(data[6:8], byteorder='little')


class DatBlockHeader:  # pylint: disable=too-few-public-methods
    def __init__(self, data: bytes):
        self.size = int.from_bytes(data[0:4], byteorder='little')
        self.unknown1 = int.from_bytes(data[4:8], byteorder='little')
        self.block_data_size = int.from_bytes(data[8:12], byteorder='little')
        self.dat_block_type = int.from_bytes(data[12:16], byteorder='little')

    def __str__(self):
        return (
            f'Size: {self.size} Unknown1: {self.unknown1} '
            f'DatBlockType: {self.dat_block_type} BlockDataSize: {self.block_data_size}'
        )


class HeaderNotSupported(Exception):
    pass


class SqPackHeader:  # pylint: disable=too-few-public-methods
    def __init__(self, file: BufferedReader):
        self.magic = file.read(8)
        self.platform_id = SqPackPlatformId(int.from_bytes(file.read(1), byteorder='little'))
        self.unknown = file.read(3)
        if self.platform_id != SqPackPlatformId.PS3:
            self.size = int.from_bytes(file.read(4), byteorder='little')
            self.version = int.from_bytes(file.read(4), byteorder='little')
            self.type = int.from_bytes(file.read(4), byteorder='little')
        else:
            raise HeaderNotSupported('PS3 is not supported')

    def __str__(self):
        return (
            f'Magic: {self.magic} Platform: {self.platform_id} '
            f'Size: {self.size} Version: {self.version} Type: {self.type}'
        )


# Consider replacing with a dictionary
class SqPackIndexHeader:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self, data: bytes):
        self.size = int.from_bytes(data[0:4], byteorder='little')
        self.version = int.from_bytes(data[4:8], byteorder='little')
        self.index_data_offset = int.from_bytes(data[8:12], byteorder='little')
        self.index_data_size = int.from_bytes(data[12:16], byteorder='little')
        self.index_data_hash = data[16:80]
        self.number_of_data_file = int.from_bytes(data[80:84], byteorder='little')
        self.synonym_data_offset = int.from_bytes(data[84:88], byteorder='little')
        self.synonym_data_size = int.from_bytes(data[88:92], byteorder='little')
        self.synonym_data_hash = data[92:156]
        self.empty_block_data_offset = int.from_bytes(data[156:160], byteorder='little')
        self.empty_block_data_size = int.from_bytes(data[160:164], byteorder='little')
        self.empty_block_data_hash = data[164:228]
        self.dir_index_data_offset = int.from_bytes(data[228:232], byteorder='little')
        self.dir_index_data_size = int.from_bytes(data[232:236], byteorder='little')
        self.dir_index_data_hash = data[236:300]
        self.index_type = int.from_bytes(data[300:304], byteorder='little')
        self.reserved = data[304:960]
        self.hash = data[960:1024]

    def __str__(self):
        return (
            f'Size: {self.size} Version: {self.version} '
            f'Index Data Offset: {self.index_data_offset} Index Data Size: {self.index_data_size} '
            f'Index Data Hash: {self.index_data_hash} Number Of Data File: {self.number_of_data_file} '
            f'Synonym Data Offset: {self.synonym_data_offset} Synonym Data Size: {self.synonym_data_size} '
            f'Synonym Data Hash: {self.synonym_data_hash} Empty Block Data Offset: {self.empty_block_data_offset} '
            f'Empty Block Data Size: {self.empty_block_data_size} '
            f'Empty Block Data Hash: {self.empty_block_data_hash} '
            f'Dir Index Data Offset: {self.dir_index_data_offset} '
            f'Dir Index Data Size: {self.dir_index_data_size} '
            f'Dir Index Data Hash: {self.dir_index_data_hash} '
            f'Index Type: {self.index_type} Reserved: {self.reserved} Hash: {self.hash}'
        )


class SqPackIndexHashTable:
    def __init__(self, data: bytes):
        self.hash_ = int.from_bytes(data[0:8], byteorder='little')
        self.data = int.from_bytes(data[8:12], byteorder='little')
        self.padding = int.from_bytes(data[12:16], byteorder='little')

    def is_synonym(self):
        return (self.data & 0b1) == 0b1

    def data_file_id(self):
        return (self.data & 0b1110) >> 1

    def data_file_offset(self):
        return (self.data & ~0xF) * 0x08

    def __str__(self):
        return (
            f'Hash: {self.hash_} Data: {self.data} Padding: {self.padding} Is Synonym: {self.is_synonym()} '
            f'Data File ID: {self.data_file_id()} Data File Offset: {self.data_file_offset()}'
        )


class NotADataFile(Exception):
    pass


class DataFileEmpty(Exception):
    pass


class SqPackTypeNotImplemented(Exception):
    pass


class SqPack:
    def __init__(self, root: str, path: str):
        self.root = root
        self.path = path
        self.file = open(path, 'rb')  # pylint: disable=R1732
        self.header = SqPackHeader(self.file)
        self.index_header = None
        self.hash_table = None
        self.data_files: List[str] = []

    def __del__(self):
        self.file.close()

    def get_index_header(self):
        self.file.seek(self.header.size)
        return SqPackIndexHeader(self.file.read(1024))

    def get_index_hash_table(self, index_header: SqPackIndexHeader):
        self.file.seek(index_header.index_data_offset)
        entry_count = index_header.index_data_size // 16
        return [SqPackIndexHashTable(self.file.read(16)) for _ in range(entry_count)]

    def load_index_header(self):
        self.index_header = self.get_index_header()

    def load_hash_table(self):
        self.hash_table = self.get_index_hash_table(self.index_header)

    def discover_data_files(self):
        self.load_index_header()
        self.load_hash_table()
        for file in get_sqpack_files(self.root, self.path.rsplit('\\', 1)[0].split('\\')[-1]):
            for i in range(0, self.index_header.number_of_data_file):
                name = self.path.rsplit('.', 1)[0] + '.dat' + str(i)
                if file == name:
                    self.data_files.append(file)

    def read_file(self, offset: int):
        if self.path.rsplit('.', 1)[1][0:3] != 'dat':
            raise NotADataFile(self.path)
        self.file.seek(offset)
        file_info_bytes = self.file.read(24)
        file_info = SqPackFileInfo(file_info_bytes, offset)
        data: List[bytes] = []
        if file_info.type == SqPackFileType.EMPTY:
            raise DataFileEmpty('File located at 0x' + hex(offset) + ' is empty.')
        if file_info.type == SqPackFileType.STANDARD:
            data = self.read_standard_file(file_info)
        else:
            raise SqPackTypeNotImplemented(str(file_info.type))
        return data

    def read_standard_file(self, file_info: SqPackFileInfo):
        block_bytes = self.file.read(file_info.number_of_blocks * 8)
        data: List[bytes] = []
        for i in range(file_info.number_of_blocks):
            block = DatStdFileBlockInfos(block_bytes[i * 8 : i * 8 + 8])
            self.file.seek(file_info.offset + file_info.header_size + block.offset)
            block_header = DatBlockHeader(self.file.read(16))
            print(block_header)
            if block_header.dat_block_type == 32000:
                data.append(self.file.read(block_header.block_data_size))
            else:
                data.append(zlib.decompress(self.file.read(block_header.block_data_size), wbits=-15))

        return data

    def __str__(self):
        return f'Path: {os.path.join(self.root, "sqpack", self.path)} Header: {self.header}'


class Repository:
    def __init__(self, name: str, root: str):
        self.root = root
        self.name = name
        self.version = None
        self.sqpacks: List[SqPack] = []
        self.index: Dict[int, Tuple[SqPackIndexHashTable, SqPack]] = {}
        self.expansion_id = 0
        self.get_expansion_id()

    def get_expansion_id(self):
        if self.name.startswith('ex'):
            self.expansion_id = int(self.name.removeprefix('ex'))

    def parse_version(self):
        version_path = ""
        if self.name == 'ffxiv':
            version_path = os.path.join(self.root, 'ffxivgame.ver')
        else:
            version_path = os.path.join(self.root, 'sqpack', self.name, self.name + '.ver')
        with open(version_path, 'r', encoding='utf8') as f:
            self.version = f.read().strip()

    def setup_indexes(self):
        for file in get_sqpack_index(self.root, self.name):
            self.sqpacks.append(SqPack(self.root, file))

        for sqpack in self.sqpacks:
            sqpack.discover_data_files()
            for indexes in sqpack.hash_table:
                self.index[indexes.hash_] = [indexes, sqpack]

    def get_index(self, hash_: int):
        return self.index[hash_]

    def get_file(self, hash_: int):
        index, sqpack = self.get_index(hash_)
        file_id = index.data_file_id()
        offset = index.data_file_offset()
        return SqPack(self.root, sqpack.data_files[file_id]).read_file(offset)

    def __str__(self):
        return f'Repository: {self.name} ({self.version}) - {self.expansion_id}'


class GameData:
    def __init__(self, root: str):
        self.root = root
        self.repositories: Dict[int, Repository] = {}
        self.setup()

    def get_repo_index(self, folder: str):
        if folder == 'ffxiv':
            return 0
        return int(folder.removeprefix('ex'))

    def setup(self):
        for folder in get_game_data_folders(self.root):
            self.repositories[self.get_repo_index(folder)] = Repository(folder, self.root)

        for folder in self.repositories:  # pylint: disable=C0206
            repo = self.repositories[folder]
            repo.parse_version()
            repo.setup_indexes()

    def get_file(self, file: 'ParsedFileName'):
        return self.repositories[self.get_repo_index(file.repo)].get_file(file.index)

    def __str__(self):
        return f'Repositories: {self.repositories}'


class ExcelListFile:
    def __init__(self, data: List[bytes]):
        self.data = b''.join(data).split('\r\n'.encode('utf-8'))
        self.parse()

    def parse(self):
        self.header = self.data[0].decode('utf-8').split(',')
        self.version = int(self.header[1])
        self.data = self.data[1:]
        self.dict: Dict[int, str] = {}
        for line in [x.decode('utf-8') for x in self.data]:
            if line == '':
                continue
            linearr = line.split(',')
            if linearr[1] == '-1':
                continue
            self.dict[int(linearr[1])] = linearr[0]

    def __repr__(self) -> str:
        return '<ExcelListFile>'


class ParsedFileName:  # pylint: disable=too-few-public-methods
    def __init__(self, path: str):
        self.path = path.lower().strip()
        parts = self.path.split('/')
        self.category = parts[0]
        self.index = crc.calc_index(self.path)
        self.index2 = crc.calc_index2(self.path)
        self.repo = parts[1]
        if self.repo[0] != 'e' or self.repo[1] != 'x' or not self.repo[2].isdigit():
            self.repo = 'ffxiv'


class Crc32:
    def __init__(self):
        self.poly = 0xEDB88320
        self.table = [0] * 256 * 16
        for i in range(256):
            res = i
            for j in range(16):
                for _ in range(8):
                    if res & 1:
                        res = (res >> 1) ^ self.poly
                    else:
                        res >>= 1
                self.table[i + j * 256] = res

    def calc(self, value: bytes):
        start = 0
        size = len(value)
        crc_local = 4294967295 ^ 0
        while size >= 16:
            a = (
                self.table[(3 * 256) + value[start + 12]]
                ^ self.table[(2 * 256) + value[start + 13]]
                ^ self.table[(1 * 256) + value[start + 14]]
                ^ self.table[(0 * 256) + value[start + 15]]
            )
            b = (
                self.table[(7 * 256) + value[start + 8]]
                ^ self.table[(6 * 256) + value[start + 9]]
                ^ self.table[(5 * 256) + value[start + 10]]
                ^ self.table[(4 * 256) + value[start + 11]]
            )
            c = (
                self.table[(11 * 256) + value[start + 4]]
                ^ self.table[(10 * 256) + value[start + 5]]
                ^ self.table[(9 * 256) + value[start + 6]]
                ^ self.table[(8 * 256) + value[start + 7]]
            )
            d = (
                self.table[(15 * 256) + value[start + 0]]
                ^ self.table[(14 * 256) + value[start + 1]]
                ^ self.table[(13 * 256) + value[start + 2]]
                ^ self.table[(12 * 256) + value[start + 3]]
            )
            crc_local = d ^ c ^ b ^ a
            start += 16
            size -= 16

        while size > 0:
            crc_local = self.table[(crc_local ^ value[start]) & 0xFF] ^ (crc_local >> 8)
            start += 1
            size -= 1

        return ~(crc_local ^ 4294967295) % (1 << 32)

    def calc_index(self, path: str):
        path_parts = path.split('/')
        filename = path_parts[-1]
        folder = path.rstrip(filename).rstrip('/')

        foldercrc = self.calc(folder.encode('utf-8'))
        filecrc = self.calc(filename.encode('utf-8'))

        return foldercrc << 32 | filecrc

    def calc_index2(self, path: str):
        return self.calc(path.encode('utf-8'))


crc = Crc32()


def get_game_data_folders(root: str):
    for folder in os.listdir(os.path.join(root, 'sqpack')):
        if os.path.isdir(os.path.join(root, 'sqpack', folder)):
            yield folder


def get_files(path):
    files: List[bytes] = []
    for dir_path, _, file_names in os.walk(path):
        files.extend(os.path.join(dir_path, file) for file in file_names)

    return files


def get_sqpack_files(root: str, path: str):
    for file in get_files(os.path.join(root, 'sqpack', path)):
        ext = file.split('.')[-1]
        if ext.startswith('dat'):
            yield file


def get_sqpack_index(root: str, path: str):
    for file in get_files(os.path.join(root, 'sqpack', path)):
        if file.endswith('.index'):
            yield file


def get_sqpack_index2(root: str, path: str):
    for file in get_files(os.path.join(root, 'sqpack', path)):
        if file.endswith('.index2'):
            yield file
