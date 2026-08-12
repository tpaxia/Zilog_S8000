#!/usr/bin/env python3
"""Verify / repair the per-block CRC-16 on an ASCII-hex Zilog S8000 tape dump.

Each *.bin_N.hex file holds one tape record as a single unbroken hex string:
4096 data bytes followed by a 2-byte big-endian CRC-16.  Short records (the
tail of a read, or a truncated read) carry no CRC and are passed through.

CRC parameters, recovered by exhaustive search over the polynomial space using
the GF(2) linearity of CRCs (T(a) ^ T(b) == CRC_init0(a ^ b) for equal-length
messages, which cancels init and xorout):

    width=16  poly=0x8005  refin=false  refout=false  init=0x0000  xorout=0xC00C

Equivalently init=0x6006 / xorout=0x0000 -- the two are indistinguishable at a
single message length.  Running the CRC over the whole 4098-byte record leaves
the constant residue 0x0027.

Usage:
    verify_tape_crc.py <dir> [-o corrected.out] [--fix] [--reference orig.out]

Without --fix a failing block is reported and its payload written unchanged.
With --fix, blocks whose CRC is repairable by a single bit flip are corrected.

--reference names the original .out image; any bytes it holds beyond what the
.hex records account for are appended, so the output is that image with the
CRC repairs applied rather than a shorter reassembly of it.
"""

import argparse
import binascii
import glob
import os
import re
import struct
import sys

POLY = 0x8005
XOROUT = 0xC00C
RESIDUE = 0x0027
RECLEN = 4098
DATALEN = 4096

TAB = []
for _i in range(256):
    _c = _i << 8
    for _ in range(8):
        _c = ((_c << 1) ^ POLY) & 0xFFFF if _c & 0x8000 else (_c << 1) & 0xFFFF
    TAB.append(_c)


def crc16(data, init=0):
    c = init
    for b in data:
        c = ((c << 8) ^ TAB[(c >> 8) ^ b]) & 0xFFFF
    return c


def block_crc(payload):
    """The CRC as it is stored on tape."""
    return crc16(payload) ^ XOROUT


def repair_single_bit(payload, stored):
    """Return (offset, bitmask) of the lone bit flip that satisfies the CRC, or None.

    A CRC syndrome determines a single-bit error position uniquely, so this
    either finds exactly one candidate or the damage is more than one bit.
    """
    if block_crc(payload) == stored:
        return None
    buf = bytearray(payload)
    for pos in range(len(buf)):
        orig = buf[pos]
        for bit in range(8):
            buf[pos] = orig ^ (1 << bit)
            if block_crc(bytes(buf)) == stored:
                buf[pos] = orig
                return pos, 1 << bit
        buf[pos] = orig
    return None


def hex_files(directory):
    """*.bin_N.hex sorted by the numeric N, not lexically."""
    files = glob.glob(os.path.join(directory, "*.hex"))
    def key(p):
        m = re.search(r"_(\d+)\.hex$", p)
        return int(m.group(1)) if m else -1
    return sorted(files, key=key)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("directory", help="directory of *.bin_N.hex records")
    ap.add_argument("-o", "--output", help="write the reassembled payload stream here")
    ap.add_argument("--fix", action="store_true",
                    help="repair blocks whose CRC is off by a single bit")
    ap.add_argument("--reference",
                    help="original .out image; carry over any tail it holds that "
                         "the .hex records do not cover")
    args = ap.parse_args()

    files = hex_files(args.directory)
    if not files:
        sys.exit("no *.hex records found in %s" % args.directory)

    stream = bytearray()
    n_ok = n_bad = n_fixed = n_nocrc = 0

    for path in files:
        idx = int(re.search(r"_(\d+)\.hex$", path).group(1))
        raw = binascii.unhexlify(open(path).read().strip())

        if len(raw) != RECLEN:
            # short read: no CRC appended, the whole record is data
            n_nocrc += 1
            print("blk %-4d %6d bytes  no CRC (short record)" % (idx, len(raw)))
            stream += raw
            continue

        payload = raw[:DATALEN]
        stored = struct.unpack(">H", raw[DATALEN:])[0]

        if block_crc(payload) == stored:
            n_ok += 1
            stream += payload
            continue

        n_bad += 1
        offset = len(stream)
        fix = repair_single_bit(payload, stored)
        if fix is None:
            print("blk %-4d CRC FAIL  stored=%04x computed=%04x  (not a single-bit error)"
                  % (idx, stored, block_crc(payload)))
            stream += payload
            continue

        pos, mask = fix
        good = payload[pos] ^ mask
        print("blk %-4d CRC FAIL  single-bit error at block offset %d "
              "(stream offset %d): %02x -> %02x%s"
              % (idx, pos, offset + pos, payload[pos], good,
                 "  [fixed]" if args.fix else "  [use --fix to repair]"))
        if args.fix:
            payload = payload[:pos] + bytes([good]) + payload[pos + 1:]
            n_fixed += 1
        stream += payload

    print("\n%d records: %d CRC ok, %d CRC failed (%d repaired), %d without CRC"
          % (len(files), n_ok, n_bad, n_fixed, n_nocrc))
    print("%d bytes of payload" % len(stream))

    if args.reference:
        ref = open(args.reference, "rb").read()
        if ref[:len(stream)] != bytes(stream) and not (n_bad and args.fix):
            print("warning: %s disagrees with the reassembled records" % args.reference)
        tail = ref[len(stream):]
        if tail:
            print("carrying over %d trailing bytes from %s (%d blocks the .hex set lacks)"
                  % (len(tail), args.reference, len(tail) // DATALEN))
            stream += tail

    if args.output:
        with open(args.output, "wb") as f:
            f.write(stream)
        print("wrote %s" % args.output)

    return 1 if (n_bad - n_fixed) else 0


if __name__ == "__main__":
    sys.exit(main())
