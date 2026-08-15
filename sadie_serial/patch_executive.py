#!/usr/bin/env python3
"""Patch only SADIE 3.5 track 0/file 1's embedded tape-routine region."""

import argparse
import hashlib
from pathlib import Path

import serve_sadie

START = 0x2874
END = 0x2D36
SIZE = END - START
EXPECTED_SHA256 = "28540a8bd03e29764a98f863ebd6064a50d30a484e85b6e9171068a752023b01"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def patch(original, driver):
    if sha256(original) != EXPECTED_SHA256:
        raise ValueError("input is not SADIE 3.5 track 0/file 1")
    if len(driver) != SIZE:
        raise ValueError(f"serial replacement must be exactly {SIZE} bytes")
    result = original[:START] + driver + original[END:]
    if len(result) != len(original):
        raise AssertionError("patch changed executive length")
    if result[:START] != original[:START] or result[END:] != original[END:]:
        raise AssertionError("patch changed bytes outside the tape routines")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", type=Path)
    parser.add_argument("driver", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    tracks = serve_sadie.read_sadie_tap(args.tape)
    original = b"".join(tracks[0][1])
    result = patch(original, args.driver.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(f"driver: {SIZE}/{SIZE} bytes")
    print(f"output: {args.output} ({sha256(result)})")


if __name__ == "__main__":
    main()
