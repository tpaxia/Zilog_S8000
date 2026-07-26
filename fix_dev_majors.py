#!/usr/bin/env python3
"""
fix_dev_majors.py <disk.img> <devs.txt> <root-fs-offset-blocks>

Work around a bug in the retro-fuse fork's v7fs_mknod: it writes the device
minor into the on-disk inode but drops the major (di_addr[0] ends up
[major,0,minor] instead of the correct [0,major,minor], so the kernel reads
major 0).  This reads the intended majors from devs.txt and stamps each /dev
node's di_addr[0] to [0, major, minor].

V7 device inode:  i_rdev == i_addr[0], stored big-endian in di_addr[0..2].
The kernel's rdev = (di_addr[0][1]<<8) | di_addr[0][2] -> major=byte1, minor=byte2.
"""
import struct, sys

def main(img, devsfile, root_off_blocks):
    fs_start = int(root_off_blocks) * 512
    with open(img, 'r+b') as f:
        d = bytearray(f.read())

        def inode_off(n):
            fsblk = 2 + (n - 1) // 8
            return fs_start + fsblk * 512 + ((n - 1) % 8) * 64

        def entries(off):
            out = []
            for i in range(0, 512, 16):
                ino = struct.unpack('>H', d[off+i:off+i+2])[0]
                nm = d[off+i+2:off+i+16]; z = nm.find(b'\x00')
                name = nm[:z if z >= 0 else 14]
                if ino and 0 < ino < 20000 and name and all(33 <= c < 127 for c in name):
                    out.append((ino, name.decode('latin1')))
            return out

        def readdir(ino):
            nd = d[inode_off(ino):inode_off(ino)+64]
            ptrs = [(nd[12+i*3] << 16) | (nd[12+i*3+1] << 8) | nd[12+i*3+2]
                    for i in range(13) if (nd[12+i*3] | nd[12+i*3+1] | nd[12+i*3+2])]
            r = {}
            for pb in ptrs:
                for i, n in entries(fs_start + pb*512):
                    r[n] = i
            return r

        # parse devs.txt: /dev/<name> <c|b> <major> <minor> <mode>
        want = {}
        for line in open(devsfile):
            line = line.split('#', 1)[0].split()
            if len(line) != 5:
                continue
            path, typ, maj, minr, mode = line
            want[path.rsplit('/', 1)[-1]] = (int(maj), int(minr))

        root = readdir(2)
        if 'dev' not in root:
            sys.exit("ERROR: no /dev in root fs")
        dev = readdir(root['dev'])

        fixed = 0
        for name, ino in dev.items():
            if name not in want:
                continue
            maj, minr = want[name]
            io = inode_off(ino)
            # di_addr[0] = [0, major, minor]  (offsets +12,+13,+14)
            if d[io+12] != 0 or d[io+13] != maj or d[io+14] != (minr & 0xff):
                d[io+12] = 0; d[io+13] = maj & 0xff; d[io+14] = minr & 0xff
                fixed += 1
        f.seek(0); f.write(d)
    print("fixed %d /dev node major/minors" % fixed)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit("usage: fix_dev_majors.py <disk.img> <devs.txt> <root-fs-offset-blocks>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
