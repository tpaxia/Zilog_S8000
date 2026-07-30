#!/usr/bin/env python3
"""
patch_init.py <path-to-etc/init>

Repair a single-bit defect in the shipped ZEUS /etc/init binary.

malloc() (WEGA/src/lib/libc/gen/malloc.c) calls sbrk() twice:
    q = sbrk(0);
    q = sbrk(temp*WORD);
Both must call the same routine.  In this init the FIRST call is
`call 0x2578` (the real _sbrk, verified against brk.s) but the SECOND is
`call 0x3578` -- high byte 0x25 flipped to 0x35 (one bit, +0x1000), sending
malloc's arena-extension into unmapped zero memory.  It is the ONLY call in
the whole userland that lands past its image; every other binary (incl. the
8 others linked from the same malloc.o) calls sbrk twice at one address.

Fix: rewrite the second call operand 0x3578 -> 0x2578.

Anchored, not offset-blind: we locate `call 0x2578` (5f 00 25 78) and the
following `call 0x3578` (5f 00 35 78) and patch only that one byte, and only
if the file still shows the defect.  Idempotent.
"""
import sys

GOOD = bytes.fromhex("5f002578")   # call _sbrk
BAD  = bytes.fromhex("5f003578")   # corrupted second call

def main(path):
    d = bytearray(open(path, "rb").read())
    g = d.find(GOOD)
    if g < 0:
        sys.exit("ERROR: first `call sbrk` (5f00 2578) not found -- not the expected init?")
    b = d.find(BAD, g)
    if b < 0:
        # already patched?
        if d.find(GOOD, g + 4) >= 0:
            print("init already patched (both sbrk calls -> 0x2578); nothing to do.")
            return
        sys.exit("ERROR: corrupted second call (5f00 3578) not found; unexpected init.")
    # sanity: the two calls should be close together (same malloc routine)
    if b - g > 0x40:
        sys.exit("ERROR: 5f00 3578 found but too far from the sbrk call (%#x); aborting." % (b - g))
    d[b + 2] = 0x25                 # 0x35 -> 0x25
    open(path, "wb").write(d)
    print("patched %s: second `call 0x3578` -> `call 0x2578` at file offset 0x%x" % (path, b))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: patch_init.py <path-to-etc/init>")
    main(sys.argv[1])
