#!/usr/bin/env python3
"""Join / split the System 8000 CPU-A monitor EPROM set.

The CPU-A carries four 2732 EPROMs holding a 16 KB, 16-bit-wide monitor.
MAME's ROM_REGION16_BE(0x4000) for `s8k_cpu` loads them interleaved:

    u76  even bytes  0x0000..0x1fff      u74  odd bytes  0x0000..0x1fff
    u77  even bytes  0x2000..0x3fff      u75  odd bytes  0x2000..0x3fff

so the flat image is big-endian words made of (u76,u74) then (u77,u75).

    rom.py join  <romdir> <out.bin>     4 EPROMs -> flat image
    rom.py split <in.bin>  <outdir>     flat image -> 4 EPROMs
"""

import pathlib
import sys

# (image base, even/high-byte EPROM, odd/low-byte EPROM)
BANKS = [
    (0x0000, "cpu_34-0715-03a.u76", "cpu_34-0716-03a.u74"),
    (0x2000, "cpu_34-0718-03a.u77", "cpu_34-0717-03a.u75"),
]
EPROM_SIZE = 0x1000
IMAGE_SIZE = 0x4000


def join(romdir, out):
    romdir = pathlib.Path(romdir)
    img = bytearray(IMAGE_SIZE)
    for base, even, odd in BANKS:
        e = (romdir / even).read_bytes()
        o = (romdir / odd).read_bytes()
        for name, blob in ((even, e), (odd, o)):
            if len(blob) != EPROM_SIZE:
                sys.exit(f"{name}: expected {EPROM_SIZE} bytes, got {len(blob)}")
        for i in range(EPROM_SIZE):
            img[base + 2 * i] = e[i]
            img[base + 2 * i + 1] = o[i]
    pathlib.Path(out).write_bytes(img)


def split(inp, outdir):
    img = pathlib.Path(inp).read_bytes()
    if len(img) != IMAGE_SIZE:
        sys.exit(f"{inp}: expected {IMAGE_SIZE} bytes, got {len(img)}")
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for base, even, odd in BANKS:
        (outdir / even).write_bytes(bytes(img[base + 2 * i] for i in range(EPROM_SIZE)))
        (outdir / odd).write_bytes(bytes(img[base + 2 * i + 1] for i in range(EPROM_SIZE)))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    cmd, a, b = sys.argv[1:]
    if cmd == "join":
        join(a, b)
    elif cmd == "split":
        split(a, b)
    else:
        sys.exit(__doc__)
