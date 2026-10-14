import struct, unittest
from tools.inventory import pe_metadata
class PEValidation(unittest.TestCase):
    def test_reject_truncated(self):
        for data in (b'', b'MZ', b'MZ'+bytes(62)):
            with self.assertRaises(ValueError): pe_metadata(data)
    def test_valid_pe32(self):
        data=bytearray(256); data[:2]=b'MZ'; struct.pack_into('<I',data,60,64)
        data[64:68]=b'PE\0\0'; struct.pack_into('<HH',data,68,0x14c,3)
        struct.pack_into('<H',data,88,0x10b); struct.pack_into('<I',data,104,0x1234)
        struct.pack_into('<I',data,116,0x400000)
        self.assertEqual(pe_metadata(data)['entry_rva'],'0x1234')
        self.assertEqual(pe_metadata(data)['machine'],'0x14c')
