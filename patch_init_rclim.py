#!/usr/bin/env python3
"""Patch the two compiled RCLIM=300 constants in reconstructed ZEUS init."""

from pathlib import Path
import argparse


OFFSETS = (0x604, 0xBC0)
EXPECTED = b"\x01\x2c"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("init", type=Path)
    parser.add_argument("seconds", type=int)
    args = parser.parse_args()

    if not 1 <= args.seconds <= 0x7FFF:
        raise SystemExit("timeout must fit a positive signed 16-bit value")

    data = bytearray(args.init.read_bytes())
    replacement = args.seconds.to_bytes(2, "big")
    for offset in OFFSETS:
        actual = bytes(data[offset : offset + 2])
        if actual != EXPECTED:
            raise SystemExit(
                f"{args.init}: expected RCLIM 0x012c at 0x{offset:x}, "
                f"found {actual.hex()}"
            )
        data[offset : offset + 2] = replacement
    args.init.write_bytes(data)
    print(f"patched {args.init}: init rc timeout={args.seconds} seconds")


if __name__ == "__main__":
    main()
