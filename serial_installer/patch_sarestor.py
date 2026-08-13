#!/usr/bin/env python3
"""Build serial sarestor directly from ZEUS 3.21 tape file 4."""

import argparse
import hashlib
import struct
from pathlib import Path

import serve_tape

SOUT_HEADER_SIZE = 24
SEGMENT_TABLE_SIZE = 16
IMAGE_FILE_OFFSET = SOUT_HEADER_SIZE + SEGMENT_TABLE_SIZE
CT_START = 0x2DE6
CT_END = 0x30A2
CT_SIZE = CT_END - CT_START
CT_CLOSE = 0x2E48
CT_STRATEGY = 0x2E5C
NOP = b"\x8d\x07"

EXPECTED_IMAGE_SHA256 = "d6feef2163246c632fd8ca815c5130aa38983965c563345d28d9a5472f90dad3"
EXPECTED_CT_SHA256 = "0206393535d06bf8ef4e6a17fe7eef9f4f5134fae847708e665bc1d935bc8697"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def patch(original, driver):
    if sha256(original) != EXPECTED_IMAGE_SHA256:
        raise ValueError("input is not the recovered ZEUS 3.21 install-tape file 4")
    if struct.unpack_from(">H", original, 0)[0] != 0xE707:
        raise ValueError("input is not a nonsegmented s.out executable")
    if len(driver) > CT_SIZE:
        raise ValueError(f"serial driver is {len(driver)} bytes; ct.o has only {CT_SIZE}")
    if len(driver) & 1:
        raise ValueError("serial driver length must be even")

    begin = IMAGE_FILE_OFFSET + CT_START
    end = IMAGE_FILE_OFFSET + CT_END
    if sha256(original[begin:end]) != EXPECTED_CT_SHA256:
        raise ValueError("ct.o bytes do not match the recovered executable")

    replacement = driver + NOP * ((CT_SIZE - len(driver)) // 2)
    result = original[:begin] + replacement + original[end:]
    if len(result) != len(original):
        raise AssertionError("patch changed executable length")
    if result[:begin] != original[:begin] or result[end:] != original[end:]:
        raise AssertionError("patch changed bytes outside ct.o")
    # The devsw pointers are outside ct.o and deliberately remain unchanged.
    # Check that they still select the three entry offsets enforced by .org in
    # serial_ct.s: strategy, open, close.
    devsw_ct = IMAGE_FILE_OFFSET + 0x520E
    pointers = struct.unpack_from(">HHH", result, devsw_ct + 2)
    if pointers != (CT_STRATEGY, CT_START, CT_CLOSE):
        raise AssertionError(f"unexpected ct devsw pointers: {pointers!r}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", type=Path)
    parser.add_argument("driver", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    files = serve_tape.read_tap(args.tape)
    if len(files) <= 4:
        parser.error("installation tape has no logical file 4")
    original = files[4]
    driver = args.driver.read_bytes()
    result = patch(original, driver)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(f"driver: {len(driver)}/{CT_SIZE} bytes")
    print(f"output: {args.output} ({sha256(result)})")


if __name__ == "__main__":
    main()
