import io
import unittest

import patch_sarestor
import patch_loader
import serve_tape


class ShortWrite(io.BytesIO):
    def write(self, data):
        return super().write(bytes(data[:3]))


class Duplex:
    def __init__(self, incoming):
        self.incoming = io.BytesIO(incoming)
        self.outgoing = io.BytesIO()

    def read(self, count):
        return self.incoming.read(count)

    def write(self, data):
        return self.outgoing.write(data)

    def flush(self):
        pass


class FragmentedDuplex(Duplex):
    def read(self, count):
        return self.incoming.read(min(count, 1))


def tape_read_request(sequence, count):
    body = sequence.to_bytes(4, "big") + count.to_bytes(2, "big")
    checksum = ord("R")
    for byte in body:
        checksum ^= byte
    return b"R" + body + bytes((checksum,))


def legacy_read_request(count):
    high, low = count >> 8, count & 0xff
    return bytes((ord("R"), high, low, ord("R") ^ high ^ low))


def open_request(file_number, version=serve_tape.XMODEM_VERSION):
    checksum = serve_tape.SOH ^ ord("S") ^ ord("8") ^ version ^ file_number
    return bytes((serve_tape.SOH,)) + b"S8" + bytes((version, file_number, checksum))


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tape_files = serve_tape.read_tap(
            patch_loader.Path("../tapes/images/zeus-3.21-install.tap")
        )

    def test_packet(self):
        self.assertEqual(serve_tape.packet(b"abc"), b"\x02\x00\x03abc\x63\x03")

    def test_xmodem_packet(self):
        payload = bytes(range(128))
        self.assertEqual(
            serve_tape.xmodem_packet(7, payload),
            b"\x01\x07\xf8" + payload + b"\xe8\x0a",
        )

    def test_crc16_xmodem_known_vector_and_corruption(self):
        self.assertEqual(serve_tape.crc16_xmodem(b"123456789"), 0x31C3)
        payload = bytearray(range(128))
        expected = serve_tape.crc16_xmodem(payload)
        payload[63] ^= 0x04
        self.assertNotEqual(serve_tape.crc16_xmodem(payload), expected)

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

    def eof_exchange(self, file_number, reply=b""):
        version = 1 if file_number < 2 else serve_tape.XMODEM_VERSION
        request = open_request(file_number, version)
        read_request = legacy_read_request(1) if version == 1 else tape_read_request(0, 128)
        port = Duplex(request + read_request + reply)
        with self.assertRaises(EOFError):
            serve_tape.TapeServer([b""] * 6, response_delay=0).serve(port)
        return port.outgoing.getvalue()

    def test_loader_eof_is_eot(self):
        self.assertEqual(
            self.eof_exchange(1),
            bytes((serve_tape.ACK, serve_tape.EOT)),
        )

    def test_xmodem_eof_is_acknowledged_eot(self):
        self.assertEqual(
            self.eof_exchange(5, bytes((serve_tape.ACK,))),
            bytes((serve_tape.ACK, serve_tape.EOT)),
        )

    def test_xmodem_nak_retransmits_block(self):
        file_number = 5
        request = open_request(file_number)
        read_request = tape_read_request(0, 128)
        port = Duplex(
            request + read_request + bytes((serve_tape.NAK, serve_tape.ACK, serve_tape.ACK))
        )
        with self.assertRaises(EOFError):
            serve_tape.TapeServer([b""] * 5 + [b"x" * 128], response_delay=0).serve(port)
        response = serve_tape.xmodem_packet(1, b"x" * 128)
        self.assertEqual(
            port.outgoing.getvalue(),
            bytes((serve_tape.ACK,)) + response + response + bytes((serve_tape.EOT,)),
        )

    def test_duplicate_sequence_is_idempotent(self):
        file_number = 5
        request = open_request(file_number)
        port = Duplex(
            request +
            tape_read_request(0, 128) + bytes((serve_tape.ACK, serve_tape.ACK)) +
            tape_read_request(0, 128) + bytes((serve_tape.ACK, serve_tape.ACK)) +
            tape_read_request(1, 128) + bytes((serve_tape.ACK, serve_tape.ACK))
        )
        with self.assertRaises(EOFError):
            serve_tape.TapeServer(
                [b""] * 5 + [b"x" * 128 + b"y" * 128], response_delay=0
            ).serve(port)
        first = serve_tape.xmodem_packet(1, b"x" * 128) + bytes((serve_tape.EOT,))
        second = serve_tape.xmodem_packet(1, b"y" * 128) + bytes((serve_tape.EOT,))
        self.assertEqual(
            port.outgoing.getvalue(),
            bytes((serve_tape.ACK,)) + first + first + second,
        )

    def test_space_file_forward_commits_last_read_and_selects_next_file(self):
        files = [b""] * 5 + [b"x" * 128, b"y" * 128]
        port = Duplex(
            open_request(5) +
            tape_read_request(0x111, 128) + bytes((serve_tape.ACK, serve_tape.ACK)) +
            bytes((ord("F"), 1, ord("F") ^ 1)) +
            tape_read_request(0x112, 128) + bytes((serve_tape.ACK, serve_tape.ACK))
        )
        with self.assertRaises(EOFError):
            serve_tape.TapeServer(files, response_delay=0).serve(port)
        self.assertEqual(
            port.outgoing.getvalue(),
            bytes((serve_tape.ACK,)) +
            serve_tape.xmodem_packet(1, files[5]) + bytes((serve_tape.EOT, serve_tape.ACK)) +
            serve_tape.xmodem_packet(1, files[6]) + bytes((serve_tape.EOT,)),
        )

    def test_fragmented_sequence_request(self):
        file_number = 5
        request = open_request(file_number)
        port = FragmentedDuplex(
            request + tape_read_request(0x12345678, 128) +
            bytes((serve_tape.ACK, serve_tape.ACK))
        )
        with self.assertRaises(EOFError):
            serve_tape.TapeServer(
                [b""] * 5 + [b"ab" * 64], response_delay=0
            ).serve(port)
        self.assertEqual(
            port.outgoing.getvalue(),
            bytes((serve_tape.ACK,)) +
            serve_tape.xmodem_packet(1, b"ab" * 64) + bytes((serve_tape.EOT,)),
        )

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
        self.assertEqual(driver[0x9c:0xa0], b"\x0a\x0e\x06\x06")
        self.assertLessEqual(len(driver), patch_sarestor.CT_SIZE)
        # Shared timed receive starts by loading its bounded poll count.
        self.assertIn(b"\x21\x00\xff\xff\x3a\xa4\xff\x85", driver)

    def test_xmodem_has_no_artificial_default_delay(self):
        server = serve_tape.TapeServer([b""])
        self.assertEqual(server.xmodem_delay, 0.0)
        self.assertGreater(server.response_delay, 0.0)

    def test_loader_patcher_changes_only_ct_object(self):
        original = self.tape_files[1]
        driver = patch_sarestor.Path("build/serial_ct.bin").read_bytes()
        result = patch_loader.patch(original, driver)
        expected = bytearray(original)
        expected[patch_loader.CT_START:patch_loader.CT_END] = result[
            patch_loader.CT_START:patch_loader.CT_END
        ]
        self.assertEqual(result, bytes(expected))
        self.assertEqual(
            result[patch_loader.RAM_PROBE_PATTERN:patch_loader.RAM_PROBE_PATTERN + 2],
            b"\xc5\x5c",
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

    def test_bootstrap_recreates_tape_boot_registers(self):
        bootstrap = patch_loader.Path("build/bootstrap.bin").read_bytes()
        # Monitor ZT enters original file 0 with r4=1, r5=0x10, r7=0.
        # Original file 0 preserves all three registers until file 1.
        self.assertIn(b"\xbd\x41\x21\x05\x00\x10\xbd\x70", bootstrap)


if __name__ == "__main__":
    unittest.main()
