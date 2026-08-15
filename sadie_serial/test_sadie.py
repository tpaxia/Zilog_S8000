import io
import unittest
from pathlib import Path

import patch_executive
import serve_sadie


HERE = Path(__file__).resolve().parent
TAPE = HERE.parent / "tapes" / "images" / "sadie-3.5.tap"


class Duplex:
    def __init__(self, received=b""):
        self.received = io.BytesIO(received)
        self.sent = io.BytesIO()
        self.writes = []

    def read(self, count):
        return self.received.read(count)

    def write(self, data):
        self.writes.append(bytes(data))
        return self.sent.write(data)

    def flush(self):
        pass


class SadieTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tracks = serve_sadie.read_sadie_tap(TAPE)

    def test_tracks_files_and_record_sizes(self):
        self.assertEqual([len(self.tracks[n]) for n in range(3)], [4, 37, 21])
        self.assertEqual([len(r) for r in self.tracks[0][0]], [8000])
        self.assertEqual([len(r) for r in self.tracks[0][1]], [1024] * 27)
        self.assertEqual([len(r) for r in self.tracks[2][0]], [4000, 4000])
        self.assertEqual([len(r) for r in self.tracks[2][1]], [1000])
        self.assertEqual([len(r) for r in self.tracks[2][2]], [1300])

    def test_executive_patch_boundary(self):
        original = b"".join(self.tracks[0][1])
        driver = (HERE / "build" / "sadie_tape_serial.bin").read_bytes()
        result = patch_executive.patch(original, driver)
        self.assertEqual(result[:patch_executive.START], original[:patch_executive.START])
        self.assertEqual(result[patch_executive.END:], original[patch_executive.END:])
        self.assertEqual(len(result), len(original))

    def test_driver_fixed_entries(self):
        driver = (HERE / "build" / "sadie_tape_serial.bin").read_bytes()
        self.assertEqual(len(driver), 0x4C2)
        for offset in (0, 0x144, 0x214, 0x37A, 0x38C, 0x4A4, 0x4B0):
            self.assertNotEqual(driver[offset:offset + 4], b"\0" * 4)

    def test_primary_fits_monitor_stage(self):
        primary = (HERE / "build" / "sadie_primary_serial.bin").read_bytes()
        self.assertLessEqual(len(primary), 512)
        self.assertEqual(primary[:4], b"\x21\x00\x40\x00")
        # Disable/clear only SIO0-A interrupt state before entering SADIE.
        self.assertIn(
            bytes.fromhex("c8013a86ff858c883a86ff85c8303a86ff85c8383a86ff85"),
            primary,
        )

    def test_position_selects_track_file_record(self):
        server = serve_sadie.SadieServer(self.tracks, b"p", b"e")
        request = bytes((1, 2, 3, 0, 1))
        checksum = serve_sadie.SOH ^ ord("S") ^ ord("D")
        for byte in request:
            checksum ^= byte
        port = Duplex()
        server.serve_position(port, request + bytes((checksum,)))
        self.assertEqual(port.sent.getvalue(), bytes((serve_sadie.ACK,)))
        self.assertEqual((server.track, server.file, server.record), (2, 3, 1))

    def test_record_response_preserves_length_and_crc(self):
        server = serve_sadie.SadieServer(self.tracks, b"p", b"e")
        server.track, server.file, server.record = 2, 1, 0
        maximum = 0xFFFF
        request = bytes((maximum >> 8, maximum & 0xFF,
                         ord("R") ^ (maximum >> 8) ^ (maximum & 0xFF)))
        # 1,000 bytes require eight packets, followed by record EOT.
        packet_reply = bytes((serve_sadie.TRACE_BEFORE_STORE,
                              serve_sadie.TRACE_AFTER_STORE,
                              serve_sadie.ACK))
        port = Duplex(bytes((serve_sadie.CRC_REQUEST,)) + packet_reply * 8 +
                      bytes((serve_sadie.ACK,)))
        server.serve_record_read(port, request)
        response = port.sent.getvalue()
        # A distinct CRC request enters the shared ZEUS XMODEM loop.
        self.assertEqual(port.writes[0], response[:3])
        self.assertEqual(port.writes[1], response[3:3 + 133])
        self.assertEqual(response[:3], bytes((serve_sadie.STX, 3, 0xE8)))
        packet = response[3:3 + 133]
        self.assertEqual(packet[0:3], bytes((serve_sadie.SOH, 1, 0xFE)))
        self.assertEqual(int.from_bytes(packet[-2:], "big"),
                         serve_sadie.crc16_xmodem(packet[3:131]))
        self.assertEqual(response[-1], serve_sadie.EOT)
        self.assertEqual(server.record, 1)


if __name__ == "__main__":
    unittest.main()
