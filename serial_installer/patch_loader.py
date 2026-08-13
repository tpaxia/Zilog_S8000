#!/usr/bin/env python3
"""Build the serial secondary loader directly from ZEUS 3.21 tape file 1."""

import argparse
import hashlib
import struct
from pathlib import Path

import serve_tape

CT_START = 0x26FA
CT_END = 0x29B6
CT_SIZE = CT_END - CT_START
CT_STRATEGY = 0x2770
CT_CLOSE = 0x275C
DEVSW_CT = 0x5108
NOP = b"\x8d\x07"
RAM_PROBE_PATTERN = 0x38BC
RAM_PROBE_VALUE = b"\xa5\xa5"

EXPECTED_SHA256 = "190df37c142f2b00a15eeeaa32858fae8fe435a34077115cfa60ed508a72345d"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def patch(original, driver):
    if sha256(original) != EXPECTED_SHA256:
        raise ValueError("input is not recovered ZEUS 3.21 installation-tape file 1")
    if len(driver) > CT_SIZE or len(driver) & 1:
        raise ValueError(f"serial driver must be even and no larger than {CT_SIZE} bytes")
    name, strategy, opened, closed = struct.unpack_from(">HHHH", original, DEVSW_CT)
    if (name, strategy, opened, closed) != (0x533D, CT_STRATEGY, CT_START, CT_CLOSE):
        raise ValueError("secondary-loader ct devsw does not have the expected fixed entries")
    if original[RAM_PROBE_PATTERN:RAM_PROBE_PATTERN + 2] != b"\0\0":
        raise ValueError("secondary-loader RAM probe does not use the expected zero pattern")

    replacement = driver + NOP * ((CT_SIZE - len(driver)) // 2)
    result = bytearray(original[:CT_START] + replacement + original[CT_END:])
    result[RAM_PROBE_PATTERN:RAM_PROBE_PATTERN + 2] = RAM_PROBE_VALUE
    result = bytes(result)
    if len(result) != len(original):
        raise AssertionError("patch changed loader length")
    expected = bytearray(original)
    expected[CT_START:CT_END] = replacement
    expected[RAM_PROBE_PATTERN:RAM_PROBE_PATTERN + 2] = RAM_PROBE_VALUE
    if result != bytes(expected):
        raise AssertionError("patch changed bytes outside ct.o and the RAM probe word")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", type=Path)
    parser.add_argument("driver", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    files = serve_tape.read_tap(args.tape)
    if len(files) <= 1:
        parser.error("installation tape has no logical file 1")
    result = patch(files[1], args.driver.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(f"loader driver: {len(args.driver.read_bytes())}/{CT_SIZE} bytes")
    print(f"output: {args.output} ({sha256(result)})")


if __name__ == "__main__":
    main()
