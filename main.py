import os
from io import BufferedReader
import enum

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
    Win32 = 0x0
    PS3 = 0x1
    PS4 = 0x2

class SqPackHeader:
    def __init__(self, file: BufferedReader):
        self.magic = file.read(8)
        self.platform_id = SqPackPlatformId(int.from_bytes(file.read(1), byteorder='little'))
        self.unknown = file.read(3)
        if(self.platform_id != SqPackPlatformId.PS3):
            self.size = int.from_bytes(file.read(4), byteorder='little')
            self.version = int.from_bytes(file.read(4), byteorder='little')
            self.type = int.from_bytes(file.read(4), byteorder='little')
        else:
            raise Exception('PS3 is not supported')
    
    def __str__(self):
        return f'''Magic: {self.magic} Platform: {self.platform_id} Size: {self.size} Version: {self.version} Type: {self.type}'''

class SqPackIndexHeader:
    def __init__(self, bytes: bytes):
        self.size = int.from_bytes(bytes[0:4], byteorder='little')
        self.version = int.from_bytes(bytes[4:8], byteorder='little')
        self.index_data_offset = int.from_bytes(bytes[8:12], byteorder='little')
        self.index_data_size = int.from_bytes(bytes[12:16], byteorder='little')
        self.index_data_hash = bytes[16:80]
        self.number_of_data_file = int.from_bytes(bytes[80:84], byteorder='little')
        self.synonym_data_offset = int.from_bytes(bytes[84:88], byteorder='little')
        self.synonym_data_size = int.from_bytes(bytes[88:92], byteorder='little')
        self.synonym_data_hash = bytes[92:156]
        self.empty_block_data_offset = int.from_bytes(bytes[156:160], byteorder='little')
        self.empty_block_data_size = int.from_bytes(bytes[160:164], byteorder='little')
        self.empty_block_data_hash = bytes[164:228]
        self.dir_index_data_offset = int.from_bytes(bytes[228:232], byteorder='little')
        self.dir_index_data_size = int.from_bytes(bytes[232:236], byteorder='little')
        self.dir_index_data_hash = bytes[236:300]
        self.index_type = int.from_bytes(bytes[300:304], byteorder='little')
        self.reserved = bytes[304:960]
        self.hash = bytes[960:1024]
    
    def __str__(self):
        return f'''Size: {self.size} Version: {self.version} Index Data Offset: {self.index_data_offset} Index Data Size: {self.index_data_size} Index Data Hash: {self.index_data_hash} Number Of Data File: {self.number_of_data_file} Synonym Data Offset: {self.synonym_data_offset} Synonym Data Size: {self.synonym_data_size} Synonym Data Hash: {self.synonym_data_hash} Empty Block Data Offset: {self.empty_block_data_offset} Empty Block Data Size: {self.empty_block_data_size} Empty Block Data Hash: {self.empty_block_data_hash} Dir Index Data Offset: {self.dir_index_data_offset} Dir Index Data Size: {self.dir_index_data_size} Dir Index Data Hash: {self.dir_index_data_hash} Index Type: {self.index_type} Reserved: {self.reserved} Hash: {self.hash}'''
    
class SqPackIndexHashTable:
    def __init__(self, bytes: bytes):
        self.hash = int.from_bytes(bytes[0:8], byteorder='little')
        self.data = int.from_bytes(bytes[8:12], byteorder='little')
        self.padding = int.from_bytes(bytes[12:16], byteorder='little')
    
    def is_synonym(self):
        return (self.data & 0b1) == 0b1
    
    def data_file_id(self):
        return ( self.data & 0b1110 ) >> 1
    
    def data_file_offset(self):
        return ( self.data & ~0xF ) * 0x08
    
    def __str__(self):
        return f'''Hash: {self.hash} Data: {self.data} Padding: {self.padding} Is Synonym: {self.is_synonym()} Data File ID: {self.data_file_id()} Data File Offset: {self.data_file_offset()}'''

class SqPack:
    def __init__(self, path: str):
        self.path = path
        self.file = open(path, 'rb')
        self.header = SqPackHeader(self.file)

    def get_index_header(self):
        self.file.seek(self.header.size)
        return SqPackIndexHeader(self.file.read(0x400))
    
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
        self.data_files = []
        for file in get_sqpack_files(self.path):
            names = file.split('.')
            for i in range(self.index_header.number_of_data_file):
                name = names[0] + '.' + names[1] + '.dat' + i
                if file == name:
                    self.data_files.append(file)
    
    def get_file(self, hash: int):
        for entry in self.hash_table:
            if(entry.hash == hash):
                # read dat file to get the data
                return None
        
        return None

def get_files(path):
    files: list[bytes] = []
    for (dir_path, dir_names, file_names) in os.walk(path):
        files.extend(os.path.join(dir_path, file) for file in file_names)

    return files

def get_sqpack_files(path):
    for file in get_files(path):
        print(file.split('.'))
        ext = file.split('.')[-1]
        if(ext.startswith('dat')):
            yield file

def get_sqpack_index(path):
    for file in get_files(path):
        if(file.endswith('.index')):
            yield file
            
def get_sqpack_index2(path):
    for file in get_files(path):
        if(file.endswith('.index2')):
            yield file

def main():
    path = 'C:\\Program Files (x86)\\SquareEnix\\FINAL FANTASY XIV - A Realm Reborn\\game\\sqpack\\ffxiv\\'
    
    for file in get_sqpack_index(path):
        print(file)
        pack = SqPack(file)
        print(pack.header)
        index_header = pack.get_index_header()
        print(index_header)
        index_hash_table = pack.get_index_hash_table(index_header)
        index_hash_table.sort(key=lambda x: x.data_file_offset())
        for entry in index_hash_table:
            print(entry)
        break

    for file in get_sqpack_files(path):
        print(file)
        break

main()