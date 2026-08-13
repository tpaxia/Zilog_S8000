#!/usr/bin/env python3
"""Serve logical files from a SIMH .tap to serial-patched sarestor."""

import argparse
import socket
import struct
import sys
import time
from pathlib import Path

SOH, STX, ETX, EOT, ACK, NAK, CAN = 1, 2, 3, 4, 6, 0x15, 0x18
OPEN_FIXED_XOR = SOH ^ ord("S") ^ ord("8") ^ 1
HERE = Path(__file__).resolve().parent
DEFAULT_BOOTSTRAP = HERE / "build/bootstrap.bin"
DEFAULT_PRIMARY = HERE / "build/primary-serial.bin"
DEFAULT_LOADER = HERE / "build/loader-serial.bin"
DEFAULT_SARESTOR = HERE / "build/sarestor-serial.bin"


def read_tap(path):
    data = path.read_bytes()
    files, records = [], []
    offset = 0
    while offset + 4 <= len(data):
        marker = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if marker == 0xFFFFFFFF:
            break
        if marker == 0:
            files.append(b"".join(records))
            records = []
            continue
        if marker & 0xF0000000:
            raise ValueError(f"unsupported SIMH marker {marker:#x}")
        end = offset + marker
        payload = data[offset:end]
        if len(payload) != marker:
            raise ValueError("truncated SIMH tape record")
        offset = end + (marker & 1)
        if offset + 4 > len(data) or struct.unpack_from("<I", data, offset)[0] != marker:
            raise ValueError("mismatched SIMH trailing record length")
        offset += 4
        records.append(payload)
    if records:
        raise ValueError("unterminated SIMH tape file")
    return files


def read_exact(port, count):
    result = bytearray()
    while len(result) < count:
        chunk = port.read(count - len(result))
        if not chunk:
            raise EOFError("serial connection closed")
        result.extend(chunk)
    return bytes(result)


def write_all(port, data):
    view = memoryview(data)
    while view:
        count = port.write(view)
        if not count:
            raise EOFError("serial connection closed while writing")
        view = view[count:]
    if hasattr(port, "flush"):
        port.flush()


def write_paced(port, data, delay=0.002):
    """Keep MAME's socket-backed bitbanger from ingesting a whole record at once."""
    for byte in data:
        write_all(port, bytes((byte,)))
        if delay:
            time.sleep(delay)


def packet(payload):
    count = len(payload)
    header = bytes((STX, count >> 8, count & 0xFF))
    checksum = (count >> 8) ^ (count & 0xFF)
    for byte in payload:
        checksum ^= byte
    return header + payload + bytes((checksum, ETX))


class TapeServer:
    def __init__(self, files, special_files=None, verbose=False):
        self.files = files
        self.special_files = special_files or {}
        self.verbose = verbose
        self.file_number = None
        self.position = 0

    def log(self, message):
        if self.verbose:
            print(message, file=sys.stderr, flush=True)

    def serve(self, port):
        while True:
            command = read_exact(port, 1)[0]
            if command == SOH:
                request = read_exact(port, 5)
                requested_file = request[3]
                if (request[:3] != b"S8\x01" or
                        request[4] != (OPEN_FIXED_XOR ^ requested_file) or
                        (requested_file >= len(self.files) and requested_file not in self.special_files)):
                    write_all(port, bytes((CAN,)))
                    continue
                self.file_number = requested_file
                self.position = 0
                source = self.source()
                self.log(f"open file {self.file_number:#x}: {len(source)} bytes")
                write_all(port, bytes((ACK,)))
            elif command == ord("R"):
                request = read_exact(port, 3)
                requested = request[0] << 8 | request[1]
                if request[2] != (ord("R") ^ request[0] ^ request[1]) or self.file_number is None:
                    write_all(port, bytes((CAN,)))
                    continue
                source = self.source()
                if self.position >= len(source):
                    write_all(port, bytes((EOT,)))
                    continue
                payload = source[self.position:self.position + requested]
                response = packet(payload)
                while True:
                    write_all(port, response)
                    reply = read_exact(port, 1)[0]
                    if reply == ACK:
                        self.position += len(payload)
                        if self.position == len(source):
                            self.log(f"file {self.file_number:#x} completely transferred")
                        break
                    if reply != NAK:
                        raise ValueError(f"unexpected packet reply {reply:#x}")
                    self.log("NAK: retransmitting response")
            elif command == CAN:
                self.log("close")
                self.file_number = None
                self.position = 0
            else:
                self.log(f"ignoring byte {command:#x} while waiting for a request")

    def source(self):
        if self.file_number in self.special_files:
            return self.special_files[self.file_number]
        return self.files[self.file_number]


def sload_memory_image(path):
    data = path.read_bytes()
    if len(data) < 40 or struct.unpack_from(">H", data, 0)[0] != 0xE707:
        raise ValueError(f"not a nonsegmented s.out executable: {path}")
    image_size = struct.unpack_from(">I", data, 2)[0]
    segment_table_size = struct.unpack_from(">H", data, 10)[0]
    image_offset = 24 + segment_table_size
    return data[image_offset:image_offset + image_size]


def monitor_record(address, payload):
    if len(payload) > 30:
        raise ValueError("monitor records hold at most 30 bytes")
    header = f"{address:04X}{len(payload):02X}"
    header_sum = sum(int(digit, 16) for digit in header) & 0xFF
    result = f"/{header}{header_sum:02X}".encode("ascii")
    if payload:
        encoded = payload.hex().upper()
        result += encoded.encode("ascii")
        result += f"{sum(int(digit, 16) for digit in encoded) & 0xff:02X}".encode("ascii")
    return result + b"\r"


def read_until(port, delimiter):
    result = bytearray()
    while not result.endswith(delimiter):
        result.extend(read_exact(port, 1))
    return bytes(result)


def send_monitor_image(port, image, address=0xF000, verbose=False):
    command = read_until(port, b"\r")
    if verbose:
        print(f"monitor command: {command.rstrip()!r}", file=sys.stderr)
    if not command[:1].upper() == b"L":
        raise ValueError(f"expected monitor L command, got {command!r}")
    # Reply to the LOAD procedure startup handshake.
    write_all(port, b"\r0")
    records = [monitor_record(address + offset, image[offset:offset + 30])
               for offset in range(0, len(image), 30)]
    records.append(monitor_record(address, b""))
    for number, record in enumerate(records):
        while True:
            write_paced(port, record)
            # L_111a/L_1112 send the status through L_11c2, which appends CR.
            # Ignore any preceding command-line CR and consume the reply CR so
            # it cannot be mistaken for the following record's status.
            reply = read_exact(port, 1)
            while reply == b"\r":
                reply = read_exact(port, 1)
            read_until(port, b"\r")
            if verbose:
                print(f"monitor record {number + 1} reply {reply!r}", file=sys.stderr)
            if reply == b"0":
                write_all(port, b"\r")
                break
            if reply != b"7":
                raise ValueError(f"monitor aborted record {number}: {reply!r}")
            write_all(port, b"\r")
        if verbose:
            print(f"monitor record {number + 1}/{len(records)} acknowledged", file=sys.stderr)


def open_port(name, baud):
    try:
        import serial
    except ImportError as error:
        raise SystemExit("pyserial is required for a real serial port: python3 -m pip install pyserial") from error
    return serial.Serial(name, baudrate=baud, bytesize=8, parity="N", stopbits=serial.STOPBITS_TWO,
                         timeout=None, write_timeout=None, xonxoff=False,
                         rtscts=False, dsrdtr=False)


def listen_socket(specification):
    host, separator, port_text = specification.rpartition(":")
    if not separator or not port_text.isdigit():
        raise ValueError("--listen must be HOST:PORT")
    listener = socket.create_server((host or "127.0.0.1", int(port_text)), reuse_port=False)
    print(f"waiting for MAME on {host or '127.0.0.1'}:{port_text}", file=sys.stderr)
    connection, address = listener.accept()
    listener.close()
    print(f"MAME connected from {address[0]}:{address[1]}", file=sys.stderr)
    return connection.makefile("rwb", buffering=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", type=Path, help="SIMH .tap installation tape")
    parser.add_argument("port", nargs="?", help="serial device, for example /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--listen", metavar="HOST:PORT", help="listen for a MAME bitbanger socket")
    parser.add_argument("--bootstrap", type=Path, default=DEFAULT_BOOTSTRAP,
                        help="monitor bootstrap override (default: build/bootstrap.bin)")
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY,
                        help="file-0 override (default: build/primary-serial.bin)")
    parser.add_argument("--loader", type=Path, default=DEFAULT_LOADER,
                        help="file-1 override (default: build/loader-serial.bin)")
    parser.add_argument("--sarestor", type=Path, default=DEFAULT_SARESTOR,
                        help="file-4 override (default: build/sarestor-serial.bin)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if bool(args.port) == bool(args.listen):
        parser.error("specify either a serial port or --listen")
    files = read_tap(args.tape)
    primary = args.primary.read_bytes()
    if len(primary) > 512:
        parser.error("--primary must fit in tape file 0's 512 bytes")
    special_files = {
        0: primary.ljust(512, b"\0"),
        1: args.loader.read_bytes(),
        4: args.sarestor.read_bytes(),
    }
    endpoint = args.listen or f"{args.port} at {args.baud} baud"
    print(f"serving {len(files)} tape files from {args.tape} on {endpoint}", file=sys.stderr)
    port = listen_socket(args.listen) if args.listen else open_port(args.port, args.baud)
    with port:
        send_monitor_image(port, args.bootstrap.read_bytes(), verbose=args.verbose)
        print("bootstrap loaded; enter J F000 (or G) at the monitor console", file=sys.stderr)
        try:
            TapeServer(files, special_files, args.verbose).serve(port)
        except EOFError:
            print("serial connection closed", file=sys.stderr)


if __name__ == "__main__":
    main()
