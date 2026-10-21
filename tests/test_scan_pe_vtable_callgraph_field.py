import unittest
from pathlib import Path

from tools.scan_pe_vtable_callgraph_field import scan


class VtableFieldCallgraphScanTests(unittest.TestCase):
    def test_suika_player_field_884_reaches_only_reset_helper(self):
        exe = Path("original/th123.exe")
        if not exe.is_file():
            self.skipTest("local reference original/th123.exe is unavailable")
        report = scan(exe, 0x85DA84, 48, 0x884)
        self.assertEqual(report["exe_sha256"],
                         "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e")
        self.assertEqual(report["executable_roots"], 25)
        self.assertGreater(report["direct_call_reachable_functions"], 300)
        self.assertEqual(report["references"], [{
            "entry": "0x0048b000",
            "pc": "0x0048b15a",
            "mnemonic": "mov",
            "instruction": "word ptr [esi + 0x884], ax",
            "call_chain": ["slot17@00608670", "call@0060867f"],
        }])
        self.assertIn("does not resolve jump tables or indirect calls/jumps",
                      report["limitations"])


if __name__ == "__main__":
    unittest.main()
