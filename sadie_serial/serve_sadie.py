#!/usr/bin/env python3
"""Serve the SADIE 3.5 multi-track tape to the read-only serial replacement."""

import argparse
import socket
import struct
import sys
import time
from pathlib import Path

SOH, STX, EOT, ACK, NAK, CAN = 1, 2, 4, 6, 0x15, 0x18
CRC_REQUEST = ord("C")
TRACE_BEFORE_STORE, TRACE_AFTER_STORE = 0x10, 0x11
PRIVATE_MARKER = 0x70000000
HERE = Path(__file__).resolve().parent
DEFAULT_BOOTSTRAP = HERE.parent / "serial_installer" / "build" / "bootstrap.bin"
DEFAULT_PRIMARY = HERE / "build" / "sadie_primary_serial.bin"
DEFAULT_EXECUTIVE = HERE / "build" / "sadie-executive-serial.bin"


def read_sadie_tap(path):
    data = path.read_bytes()
    tracks = {}
    files, records = [], []
    track = None
    offset = 0
    while offset + 4 <= len(data):
        marker = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if marker == 0xFFFFFFFF:
            if track is None or records:
                raise ValueError("invalid SADIE end-of-medium")
            tracks[track] = files
            break
        if marker & 0xF0000000 == PRIVATE_MARKER:
            if records:
                raise ValueError("track marker inside a logical file")
            if track is not None:
                tracks[track] = files
            track = marker & 0x0FFFFFFF
            if track in tracks:
                raise ValueError(f"duplicate SADIE track {track}")
            files = []
            continue
        if track is None:
            raise ValueError("SADIE data precedes its first track marker")
        if marker == 0:
            files.append(records)
            records = []
            continue
        if marker & 0xF0000000:
            raise ValueError(f"unsupported SIMH marker {marker:#x}")
        payload = data[offset:offset + marker]
        if len(payload) != marker:
            raise ValueError("truncated SIMH record")
        offset += marker + (marker & 1)
        if offset + 4 > len(data) or struct.unpack_from("<I", data, offset)[0] != marker:
            raise ValueError("mismatched SIMH trailing record length")
        offset += 4
        records.append(payload)
    if sorted(tracks) != list(range(len(tracks))):
        raise ValueError(f"non-contiguous SADIE tracks: {sorted(tracks)}")
    return tracks


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


def write_paced(port, data, delay):
    if not delay:
        write_all(port, data)
        return
    for byte in data:
        write_all(port, bytes((byte,)))
        time.sleep(delay)


def crc16_xmodem(payload):
    crc = 0
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def xmodem_packet(number, payload):
    payload = payload.ljust(128, b"\0")
    crc = crc16_xmodem(payload)
    return bytes((SOH, number, number ^ 0xFF)) + payload + crc.to_bytes(2, "big")


def monitor_record(address, payload):
    header = f"{address:04X}{len(payload):02X}"
    result = f"/{header}{sum(map(lambda c: int(c, 16), header)) & 0xff:02X}"
    encoded = payload.hex().upper()
    if encoded:
        result += encoded + f"{sum(map(lambda c: int(c, 16), encoded)) & 0xff:02X}"
    return result.encode("ascii") + b"\r"


def read_until(port, delimiter):
    result = bytearray()
    while not result.endswith(delimiter):
        result.extend(read_exact(port, 1))
    return bytes(result)


def send_monitor_image(port, image, verbose=False):
    command = read_until(port, b"\r")
    if verbose:
        print(f"monitor command: {command.rstrip()!r}", file=sys.stderr)
    if command[:1].upper() != b"L":
        raise ValueError(f"expected monitor L command, got {command!r}")
    write_all(port, b"\r0")
    records = [monitor_record(0xF000 + offset, image[offset:offset + 30])
               for offset in range(0, len(image), 30)]
    records.append(monitor_record(0xF000, b""))
    for number, record in enumerate(records, 1):
        while True:
            write_paced(port, record, 0.002)
            reply = read_exact(port, 1)
            while reply == b"\r":
                reply = read_exact(port, 1)
            read_until(port, b"\r")
            if reply == b"0":
                write_all(port, b"\r")
                break
            if reply != b"7":
                raise ValueError(f"monitor aborted record {number}: {reply!r}")
            write_all(port, b"\r")
        if verbose:
            print(f"monitor record {number}/{len(records)} acknowledged", file=sys.stderr)


class SadieServer:
    def __init__(self, tracks, primary, executive, verbose=False,
                 legacy_delay=0.00125, turnaround_delay=0.0):
        self.tracks = tracks
        self.special = {(0, 0): primary.ljust(512, b"\0"), (0, 1): executive}
        self.verbose = verbose
        self.legacy_delay = legacy_delay
        self.turnaround_delay = turnaround_delay
        self.stream = None
        self.stream_position = 0
        self.track = self.file = self.record = None

    def log(self, message):
        if self.verbose:
            print(message, file=sys.stderr, flush=True)

    def logical_file(self, track, file_number):
        if (track, file_number) in self.special:
            return self.special[(track, file_number)]
        return b"".join(self.tracks[track][file_number])

    def serve_legacy_open(self, port, request):
        version, file_number, checksum = request
        valid = (version == 1 and file_number < len(self.tracks[0]) and
                 checksum == (SOH ^ ord("S") ^ ord("8") ^ version ^ file_number))
        if not valid:
            write_all(port, bytes((CAN,)))
            return
        self.stream = self.logical_file(0, file_number)
        self.stream_position = 0
        self.log(f"legacy open track 0 file {file_number}: {len(self.stream)} bytes")
        write_all(port, bytes((ACK,)))

    def addressable(self, track, file_number, record):
        return (track in self.tracks and file_number < len(self.tracks[track]) and
                record <= len(self.tracks[track][file_number]))

    def position(self, track, file_number, record):
        """Select a track, logical file, and record without a host request."""
        if not self.addressable(track, file_number, record):
            raise ValueError(
                f"no SADIE track {track} file {file_number} record {record}")
        self.track, self.file, self.record = track, file_number, record
        self.stream = None

    def serve_position(self, port, request):
        version, track, file_number, record_hi, record_lo, checksum = request
        expected = SOH ^ ord("S") ^ ord("D")
        for byte in request[:-1]:
            expected ^= byte
        record = record_hi << 8 | record_lo
        if (version != 1 or checksum != expected or
                not self.addressable(track, file_number, record)):
            write_all(port, bytes((CAN,)))
            return
        self.position(track, file_number, record)
        self.log(f"position track {track} file {file_number} record {record}")
        write_all(port, bytes((ACK,)))

    def serve_legacy_read(self, port, request):
        count = request[0] << 8 | request[1]
        if request[2] != (ord("R") ^ request[0] ^ request[1]):
            write_all(port, bytes((CAN,)))
            return
        payload = self.stream[self.stream_position:self.stream_position + count]
        if not payload:
            write_all(port, bytes((EOT,)))
            return
        header = bytes((STX, len(payload) >> 8, len(payload) & 0xFF))
        checksum = request[0] ^ request[1]
        checksum = (len(payload) >> 8) ^ (len(payload) & 0xFF)
        for byte in payload:
            checksum ^= byte
        response = header + payload + bytes((checksum, 3))
        while True:
            write_paced(port, response, self.legacy_delay)
            reply = read_exact(port, 1)[0]
            if reply == ACK:
                self.stream_position += len(payload)
                return
            if reply != NAK:
                raise ValueError(f"unexpected legacy reply {reply:#x}")

    def serve_record_read(self, port, request):
        maximum = request[0] << 8 | request[1]
        if (self.track is None or not maximum or
                request[2] != (ord("R") ^ request[0] ^ request[1])):
            write_all(port, bytes((CAN,)))
            return
        records = self.tracks[self.track][self.file]
        if self.record == len(records):
            write_all(port, bytes((EOT,)))
            if read_exact(port, 1)[0] != ACK:
                raise ValueError("SADIE EOF was not acknowledged")
            return
        payload = records[self.record][:maximum]
        self.record += 1
        self.log(
            f"sending track {self.track} file {self.file} record {self.record - 1}: "
            f"{len(payload)} bytes"
        )
        header = bytes((STX, len(payload) >> 8, len(payload) & 0xFF))
        write_all(port, header)
        if read_exact(port, 1)[0] != CRC_REQUEST:
            raise ValueError("SADIE record did not request XMODEM-CRC")
        time.sleep(self.turnaround_delay)
        for number, offset in enumerate(range(0, len(payload), 128), 1):
            packet = xmodem_packet(number & 0xFF, payload[offset:offset + 128])
            response = packet
            while True:
                write_all(port, response)
                response = packet
                reply = read_exact(port, 1)[0]
                while reply in (TRACE_BEFORE_STORE, TRACE_AFTER_STORE):
                    stage = "before" if reply == TRACE_BEFORE_STORE else "after"
                    self.log(f"packet {number & 0xFF}: {stage} physical store")
                    reply = read_exact(port, 1)[0]
                if reply == ACK:
                    break
                if reply != NAK:
                    raise ValueError(f"unexpected XMODEM reply {reply:#x}")
                self.log(f"NAK: retransmitting SADIE record packet {number & 0xFF}")
            time.sleep(self.turnaround_delay)
        write_all(port, bytes((EOT,)))
        if read_exact(port, 1)[0] != ACK:
            raise ValueError("SADIE record EOT was not acknowledged")
        self.log(f"read track {self.track} file {self.file} record {self.record - 1}: {len(payload)} bytes")

    def serve(self, port):
        while True:
            command = read_exact(port, 1)[0]
            if command == SOH:
                magic = read_exact(port, 2)
                if magic == b"S8":
                    self.serve_legacy_open(port, read_exact(port, 3))
                elif magic == b"SD":
                    self.serve_position(port, read_exact(port, 6))
                else:
                    write_all(port, bytes((CAN,)))
            elif command == ord("R"):
                request = read_exact(port, 3)
                if self.stream is not None:
                    self.serve_legacy_read(port, request)
                else:
                    self.serve_record_read(port, request)
            elif command == CAN:
                self.stream = None
                self.track = self.file = self.record = None
            else:
                self.log(f"ignoring byte {command:#x}")


def parse_position(text):
    parts = text.split(",")
    if len(parts) != 3 or not all(part.strip().isdigit() for part in parts):
        raise ValueError("--position must be TRACK,FILE,RECORD")
    return tuple(int(part) for part in parts)


def open_port(name, baud):
    try:
        import serial
    except ImportError as error:
        raise SystemExit("pyserial is required for real hardware") from error
    return serial.Serial(name, baudrate=baud, bytesize=8, parity="N", stopbits=2,
                         timeout=None, write_timeout=None, xonxoff=False,
                         rtscts=False, dsrdtr=False)


def listen_socket(specification):
    host, separator, port_text = specification.rpartition(":")
    if not separator or not port_text.isdigit():
        raise ValueError("--listen must be HOST:PORT")
    listener = socket.create_server((host or "127.0.0.1", int(port_text)))
    print(f"waiting for MAME on {host or '127.0.0.1'}:{port_text}", file=sys.stderr)
    connection, address = listener.accept()
    listener.close()
    print(f"MAME connected from {address[0]}:{address[1]}", file=sys.stderr)
    return connection.makefile("rwb", buffering=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", type=Path)
    parser.add_argument("port", nargs="?")
    parser.add_argument("--listen", metavar="HOST:PORT")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--bootstrap", type=Path, default=DEFAULT_BOOTSTRAP)
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--executive", type=Path, default=DEFAULT_EXECUTIVE)
    parser.add_argument("--serve-only", action="store_true",
                        help="skip the monitor download; serve a SADIE already in memory")
    parser.add_argument("--position", metavar="TRACK,FILE,RECORD",
                        help="prime the tape position, for use with --serve-only")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if bool(args.port) == bool(args.listen):
        parser.error("specify either a serial port or --listen")
    tracks = read_sadie_tap(args.tape)
    endpoint = args.listen or f"{args.port} at {args.baud} baud"
    print(f"serving SADIE tracks {sorted(tracks)} on {endpoint}", file=sys.stderr)
    turnaround_delay = 0.003 if args.listen else 0.0
    server = SadieServer(tracks, args.primary.read_bytes(), args.executive.read_bytes(),
                         args.verbose, turnaround_delay=turnaround_delay)
    if args.position:
        server.position(*parse_position(args.position))
        print(f"tape primed at track {server.track} file {server.file} "
              f"record {server.record}", file=sys.stderr)
    port = listen_socket(args.listen) if args.listen else open_port(args.port, args.baud)
    with port:
        if args.serve_only:
            print("serving records only; no monitor download", file=sys.stderr)
        else:
            send_monitor_image(port, args.bootstrap.read_bytes(), args.verbose)
            print("bootstrap loaded; enter J F000 (or G)", file=sys.stderr)
        server.serve(port)


if __name__ == "__main__":
    main()
