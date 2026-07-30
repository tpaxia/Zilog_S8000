#!/usr/bin/env python3
"""Patch the shipped ZEUS date/datem binaries for two-digit years after 1999."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


DATE_SHA256 = "d339d73964d0974cdd1a9834968c1e50f4b5707c746b47812cb66e0ba767b9fd"
DATEM_SHA256 = "47d9599fce1d655197b0d1f3afe130765134471995dfc5d6d2a861ee05b26b12"

# s.out header (24 bytes) plus one 16-byte segment entry.
IMAGE_OFFSET = 0x28

# date's entry instruction jumps over the original copyright string at
# addresses 0x0002..0x0017.  Reuse that unreachable space for:
#
#   if (year < 70)
#       year += 100;
#   year += 1900;
#   return;
#
# The original "year += 1900" at 0x0524 becomes a call to this routine.
DATE_CAVE = bytes.fromhex(
    "0b0d0046"  # cp r13,#70
    "e103"      # jr lt,0x000e
    "010d076c"  # add r13,#1900
    "9e08"      # ret
    "010d0064"  # add r13,#100
    "010d076c"  # add r13,#1900
    "9e08"      # ret
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace(data: bytearray, offset: int, old: bytes, new: bytes, name: str) -> None:
    actual = bytes(data[offset : offset + len(old)])
    if actual != old:
        raise SystemExit(
            f"{name}: unexpected bytes at 0x{offset:x}: "
            f"{actual.hex()} != {old.hex()}"
        )
    if len(old) != len(new):
        raise SystemExit(f"{name}: replacement changes file size")
    data[offset : offset + len(new)] = new


def patch_date(path: Path) -> None:
    data = bytearray(path.read_bytes())
    if sha256(data) != DATE_SHA256:
        raise SystemExit(f"{path}: not the expected original ZEUS /bin/date")

    replace(
        data,
        IMAGE_OFFSET + 0x0002,
        b"COPR. 1981 ZILOG INC.\0",
        DATE_CAVE,
        str(path),
    )
    replace(
        data,
        IMAGE_OFFSET + 0x0524,
        bytes.fromhex("010d076c"),  # add r13,#1900
        bytes.fromhex("5f000002"),  # call 0x0002
        str(path),
    )
    path.write_bytes(data)


def patch_datem(path: Path) -> None:
    data = bytearray(path.read_bytes())
    if sha256(data) != DATEM_SHA256:
        raise SystemExit(f"{path}: not the expected original ZEUS /etc/datem")

    replace(
        data,
        IMAGE_OFFSET + 0x0330,
        bytes.fromhex("0046"),  # lower bound 70
        bytes.fromhex("0000"),  # lower bound 0
        str(path),
    )
    path.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("date", type=Path)
    parser.add_argument("datem", type=Path)
    args = parser.parse_args()

    patch_date(args.date)
    patch_datem(args.datem)
    print(f"patched {args.date}: yy 00-69 -> 2000-2069")
    print(f"patched {args.datem}: accept yy 00-99")


if __name__ == "__main__":
    main()
