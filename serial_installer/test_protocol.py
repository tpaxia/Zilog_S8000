import io
import unittest

import patch_sarestor
import patch_loader
import serve_tape


class ShortWrite(io.BytesIO):
    def write(self, data):
        return super().write(bytes(data[:3]))


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tape_files = serve_tape.read_tap(
            patch_loader.Path("../tapes/images/zeus-3.21-install.tap")
        )

    def test_packet(self):
        self.assertEqual(serve_tape.packet(b"abc"), b"\x02\x00\x03abc\x63\x03")

    def test_monitor_record(self):
        self.assertEqual(serve_tape.monitor_record(0xF000, b"abc"),
                         b"/F0000312" b"61626318\r")
        self.assertEqual(serve_tape.monitor_record(0xF000, b""), b"/F000000F\r")

    def test_sarestor_memory_image(self):
        path = patch_sarestor.Path("build/sarestor-serial.bin")
        image = serve_tape.sload_memory_image(path)
        self.assertEqual(len(image), 0x57E0)
        self.assertEqual(image[:2], path.read_bytes()[40:42])

    def test_write_all_handles_short_writes(self):
        stream = ShortWrite()
        serve_tape.write_all(stream, b"abcdefgh")
        self.assertEqual(stream.getvalue(), b"abcdefgh")

    def test_patcher_changes_only_ct_object(self):
        original = self.tape_files[4]
        replacement = b"\x8d\x07" * 10
        result = patch_sarestor.patch(original, replacement)
        begin = patch_sarestor.IMAGE_FILE_OFFSET + patch_sarestor.CT_START
        end = patch_sarestor.IMAGE_FILE_OFFSET + patch_sarestor.CT_END
        self.assertEqual(result[:begin], original[:begin])
        self.assertEqual(result[end:], original[end:])
        self.assertEqual(len(result), len(original))

    def test_driver_entry_offsets(self):
        driver = patch_sarestor.Path("build/serial_ct.bin").read_bytes()
        # Each entry starts with a known first instruction.  More importantly,
        # these are the offsets hard-coded in the unchanged standalone devsw.
        self.assertEqual(driver[0:2], b"\xc8\x01")
        self.assertEqual(driver[0x62:0x64], b"\xc8\x18")
        self.assertEqual(driver[0x76:0x7a], b"\x0b\x06\x00\x01")

    def test_loader_patcher_changes_only_ct_object_and_probe_word(self):
        original = self.tape_files[1]
        driver = patch_sarestor.Path("build/serial_ct.bin").read_bytes()
        result = patch_loader.patch(original, driver)
        expected = bytearray(original)
        expected[patch_loader.CT_START:patch_loader.CT_END] = result[
            patch_loader.CT_START:patch_loader.CT_END
        ]
        expected[
            patch_loader.RAM_PROBE_PATTERN:patch_loader.RAM_PROBE_PATTERN + 2
        ] = patch_loader.RAM_PROBE_VALUE
        self.assertEqual(result, bytes(expected))
        self.assertEqual(
            result[patch_loader.RAM_PROBE_PATTERN:patch_loader.RAM_PROBE_PATTERN + 2],
            b"\xa5\xa5",
        )
        self.assertEqual(len(result), len(original))

    def test_serial_primary_preserves_original_relocation_flow(self):
        original = self.tape_files[0]
        primary = patch_loader.Path("build/primary-serial.bin").read_bytes()
        # FCW 0x4000, destination 0xf800, source 0x001a and jump 0xf800 are
        # the original file-0 handoff.  Only the relocated device body differs.
        self.assertEqual(primary[:14], original[:14])
        self.assertEqual(primary[18:26], original[18:26])
        self.assertLessEqual(len(primary), 512)


if __name__ == "__main__":
    unittest.main()
