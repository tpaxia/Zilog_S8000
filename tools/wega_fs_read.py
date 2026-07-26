#!/usr/bin/env python3
"""Read/list/extract files from a WEGA/V7 big-endian filesystem in a disk image."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

BSIZE = 512
NADDR = 13
NDIRECT = NADDR - 3
NINDIR = BSIZE // 4
IFMT = 0o170000
IFDIR = 0o040000


class FS:
    def __init__(self, image: Path, block_offset: int):
        self.fp = image.open("rb")
        self.base = block_offset * BSIZE

    def block(self, number: int) -> bytes:
        self.fp.seek(self.base + number * BSIZE)
        data = self.fp.read(BSIZE)
        if len(data) != BSIZE:
            raise EOFError(f"short read of filesystem block {number}")
        return data

    def inode(self, number: int) -> dict:
        # WEGA retains the V7 inode mapping with the historical +15 bias.
        block = (number + 15) >> 3
        slot = (number + 15) & 7
        raw = self.block(block)[slot * 64 : slot * 64 + 64]
        mode, nlink, uid, gid, size, packed, atime, mtime, ctime = struct.unpack(
            ">HhHHL40sLLL", raw
        )
        addr = [
            int.from_bytes(b"\0" + packed[i : i + 3], "big")
            for i in range(0, 3 * NADDR, 3)
        ]
        return {
            "number": number, "mode": mode, "nlink": nlink, "uid": uid,
            "gid": gid, "size": size, "addr": addr, "atime": atime,
            "mtime": mtime, "ctime": ctime,
        }

    def _indirect(self, number: int, level: int):
        if not number:
            return
        words = struct.unpack(">128L", self.block(number))
        if level == 1:
            for word in words:
                if word:
                    yield word
        else:
            for word in words:
                if word:
                    yield from self._indirect(word, level - 1)

    def blocks(self, inode: dict):
        remaining = (inode["size"] + BSIZE - 1) // BSIZE
        for number in inode["addr"][:NDIRECT]:
            if not remaining:
                return
            yield number
            remaining -= 1
        for level, number in enumerate(inode["addr"][NDIRECT:], 1):
            for leaf in self._indirect(number, level):
                if not remaining:
                    return
                yield leaf
                remaining -= 1

    def read(self, inode: dict) -> bytes:
        data = b"".join(self.block(number) if number else bytes(BSIZE)
                        for number in self.blocks(inode))
        return data[:inode["size"]]

    def entries(self, inode: dict):
        data = self.read(inode)
        for offset in range(0, len(data) - 15, 16):
            number, raw_name = struct.unpack(">H14s", data[offset : offset + 16])
            if number:
                yield number, raw_name.split(b"\0", 1)[0].decode("ascii", "replace")

    def walk(self, number: int = 2, path: str = "/", seen=None):
        if seen is None:
            seen = set()
        inode = self.inode(number)
        yield path, inode
        if inode["mode"] & IFMT != IFDIR or number in seen:
            return
        seen.add(number)
        for child, name in self.entries(inode):
            if name not in (".", ".."):
                child_path = path.rstrip("/") + "/" + name
                yield from self.walk(child, child_path, seen)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--offset", type=int, default=0, help="filesystem block offset")
    parser.add_argument("--extract")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    fs = FS(args.image, args.offset)
    for path, inode in fs.walk():
        if args.extract == path:
            output = args.output or Path(path.rsplit("/", 1)[-1])
            output.write_bytes(fs.read(inode))
            print(f"{path} -> {output} ({inode['size']} bytes)")
            return
        if args.extract is None:
            print(f"{inode['number']:5d} {inode['mode']:06o} {inode['size']:9d} {path}")
    if args.extract:
        raise SystemExit(f"{args.extract}: not found")


if __name__ == "__main__":
    main()
