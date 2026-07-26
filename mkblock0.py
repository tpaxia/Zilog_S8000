#!/usr/bin/env python3
"""
mkblock0.py <disk.img>  -- write the S8000 boot record (block 0) into a raw
disk image so ZEUS auto-boots and the kernel's _b0rd finds the right devices.

Block-0 layout (sys/block0.h; magic BLK0MAGIC=0xDEADBABE):
  0x00 b0_MAGIC   (long)  0xDEADBABE
  0x04 b0_bfstype (long)  0   secondary-boot fs type   -- MUST stay 0 (monitor reads it)
  0x08 b0_bdrv    (short) 0   secondary-boot drive     -- MUST stay 0 (monitor cp#0 -> autoboot)
  0x0a b0_boff    (long)  0   secondary-boot offset     -- MUST stay 0 (monitor reads it)
  0x0e b0_rfstype (long)  0   root fs type              -- keep 0
  0x12 b0_rdrv    (short) 0   root drive unit
  0x14 b0_roff    (long)  15200  root partition block offset
  0x18 b0_rdev    (short) 0x0802  root  makedev smd(maj8) u0 vd2   <- kernel _b0rd -> _rootdev
  0x1a b0_sdev    (short) 0x0801  swap  makedev smd(maj8) u0 vd1   <- _swapdev
  0x1c b0_pdev    (short) 0x0802  pipe  makedev = rdev             <- _pipedev
  0x1e b0_ssz     (long)  16736   swap size (blocks); nswap = ssz-1
  0x22 b0_vfs[16] { long vd_blkoff; long vd_nblocks; char nam[8]; }  (16 bytes each)
       vd0 usr  @0      /15000
       vd1 swap @115200 /16736
       vd2 root @15200  /100000

The PROM monitor autoboots off a HARDCODED ROM string when magic==DEADBABE and
b0_bdrv(0x08)==0; it never reads 0x18+. The kernel reads rdev/sdev/pdev at
0x18/0x1a/0x1c.  All big-endian.
"""
import struct, sys

def main(img):
    with open(img, 'r+b') as f:
        b = bytearray(512)
        struct.pack_into('>I', b, 0x00, 0xDEADBABE)   # magic
        # 0x04..0x16 stay zero except roff
        struct.pack_into('>I', b, 0x14, 15200)        # b0_roff
        struct.pack_into('>H', b, 0x18, 0x0802)       # b0_rdev  smd u0 vd2 (root)
        struct.pack_into('>H', b, 0x1a, 0x0801)       # b0_sdev  smd u0 vd1 (swap)
        struct.pack_into('>H', b, 0x1c, 0x0802)       # b0_pdev  smd u0 vd2
        struct.pack_into('>I', b, 0x1e, 16736)        # b0_ssz
        vfs = [(0, 15000, b'usr'), (115200, 16736, b'swap'),
               (15200, 100000, b'root')]
        for i, (blk, n, nam) in enumerate(vfs):
            o = 0x22 + i * 16
            struct.pack_into('>I', b, o, blk)
            struct.pack_into('>I', b, o + 4, n)
            b[o + 8:o + 16] = nam.ljust(8, b'\x00')
        f.seek(0)
        f.write(b)
    print("block 0 written: magic=DEADBABE rdev=0802 sdev=0801 pdev=0802 "
          "roff=15200 ssz=16736; vfs " +
          " ".join("%s@%d/%d" % (nam.decode(), blk, n) for blk, n, nam in vfs))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit("usage: mkblock0.py <disk.img>")
    main(sys.argv[1])
