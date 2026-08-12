#!/usr/bin/env python3
"""List or extract the UNIX V7 `dump` tape in this directory.

The tape is a level-0 `dump` of the /usr filesystem of a Zilog System 8000
running ZEUS (dump magic 60011, header checksum constant 84446, big-endian
Z8000 byte order).

Layout, working outward:

  *.bin_N.hex   one tape block, ASCII hex: 4096 data bytes + 2-byte CRC-16
                (poly 0x8005, MSB-first, init 0x0000, xorout 0xC00C, big-endian;
                see verify_tape_crc.py)
  tape block    8 x 512-byte dump records; record number == 8*N + k, which
                matches the dump's own c_tapea counter exactly
  dump record   either a `spcl` header (magic at offset 18) or file data

Four blocks were short reads, so 18 of the 800 records are missing.  Because
record numbering is anchored to the block index, the loss stays local instead
of shifting everything after it.  The .out file carries one further block
(records 800-807) that has no .hex counterpart; pass --out to include it.

Usage:
    read_dump.py -l                  list everything
    read_dump.py -x DESTDIR          extract the file data that is present
    read_dump.py -l --out FILE.out   also use the extra block from the .out
"""

import argparse
import binascii
import glob
import os
import re
import struct
import sys
from collections import defaultdict
from datetime import datetime, timezone

MAGIC = 60011
CHECKSUM = 84446 & 0xFFFF
CRC_POLY = 0x8005
CRC_XOROUT = 0xC00C
RECLEN, DATALEN, RECS_PER_BLOCK = 4098, 4096, 8

TS_TAPE, TS_INODE, TS_BITS, TS_ADDR, TS_END, TS_CLRI = 1, 2, 3, 4, 5, 6
TSNAME = {1: 'TS_TAPE', 2: 'TS_INODE', 3: 'TS_BITS', 4: 'TS_ADDR', 5: 'TS_END', 6: 'TS_CLRI'}

IFMT = 0o170000
IFDIR, IFREG, IFCHR, IFBLK, IFIFO = 0o040000, 0o100000, 0o020000, 0o060000, 0o010000
TYPECH = {IFDIR: 'd', IFREG: '-', IFCHR: 'c', IFBLK: 'b', IFIFO: 'p'}

_TAB = []
for _i in range(256):
    _c = _i << 8
    for _ in range(8):
        _c = ((_c << 1) ^ CRC_POLY) & 0xFFFF if _c & 0x8000 else (_c << 1) & 0xFFFF
    _TAB.append(_c)


def crc16(data):
    c = 0
    for b in data:
        c = ((c << 8) ^ _TAB[(c >> 8) ^ b]) & 0xFFFF
    return c ^ CRC_XOROUT


def repair_single_bit(payload, stored):
    buf = bytearray(payload)
    for pos in range(len(buf)):
        orig = buf[pos]
        for bit in range(8):
            buf[pos] = orig ^ (1 << bit)
            if crc16(bytes(buf)) == stored:
                return pos, orig ^ (1 << bit)
        buf[pos] = orig
    return None


def load_tape(directory, outfile=None, quiet=False):
    """Return {absolute record number: 512 bytes}."""
    files = sorted(glob.glob(os.path.join(directory, '*.hex')),
                   key=lambda p: int(re.search(r'_(\d+)\.hex$', p).group(1)))
    if not files:
        sys.exit('no *.hex records in %s' % directory)

    tape, consumed, nblocks = {}, 0, 0
    for path in files:
        bi = int(re.search(r'_(\d+)\.hex$', path).group(1))
        raw = binascii.unhexlify(open(path).read().strip())
        if len(raw) == RECLEN:
            payload, stored = raw[:DATALEN], struct.unpack('>H', raw[DATALEN:])[0]
            if crc16(payload) != stored:
                fix = repair_single_bit(payload, stored)
                if fix:
                    pos, good = fix
                    if not quiet:
                        print('blk %d: repaired single-bit error at offset %d (%02x -> %02x)'
                              % (bi, pos, payload[pos], good), file=sys.stderr)
                    payload = payload[:pos] + bytes([good]) + payload[pos + 1:]
                elif not quiet:
                    print('blk %d: CRC failed and is not a single-bit error' % bi, file=sys.stderr)
        else:
            payload = raw          # short read, no CRC
        for k in range(len(payload) // 512):
            tape[bi * RECS_PER_BLOCK + k] = payload[k * 512:(k + 1) * 512]
        consumed += len(payload)
        nblocks = max(nblocks, bi + 1)

    if outfile:
        # the .out is the same payload stream; anything past it is extra blocks
        extra = open(outfile, 'rb').read()[consumed:]
        for j in range(len(extra) // DATALEN):
            bi = nblocks + j
            for k in range(RECS_PER_BLOCK):
                tape[bi * RECS_PER_BLOCK + k] = extra[j * DATALEN + k * 512:
                                                      j * DATALEN + (k + 1) * 512]
        if extra and not quiet:
            print('picked up %d extra block(s) from %s' % (len(extra) // DATALEN, outfile),
                  file=sys.stderr)
    return tape


def parse_header(r):
    ty, date, ddate, vol, tapea, ino, magic, cks = struct.unpack('>hIIhIHHH', r[:22])
    if magic != MAGIC or sum(struct.unpack('>256H', r)) & 0xFFFF != CHECKSUM:
        return None
    return dict(type=ty, date=date, ddate=ddate, volume=vol, tapea=tapea, inum=ino)


def parse_dinode(b):
    mode, nlink, uid, gid, size = struct.unpack('>HhhhI', b[:12])
    atime, mtime, ctime = struct.unpack('>III', b[52:64])
    return dict(mode=mode, nlink=nlink, uid=uid, gid=gid, size=size,
                atime=atime, mtime=mtime, ctime=ctime)


def parse(tape):
    """Walk the record stream.

    Returns (tapehdr, inodes, blocks, order, missing, orphans).  An orphan is a
    data record with no owning TS_INODE -- either the TS_CLRI/TS_BITS maps, or
    a record whose own header was lost inside a short block.
    """
    last = max(tape)
    missing = [n for n in range(last + 1) if n not in tape]
    tapehdr, inodes, order, orphans = None, {}, [], []
    blocks = defaultdict(dict)          # inode -> {logical block: 512 bytes}
    cur, amap, ai, logical = None, [], 0, 0

    def take_slot():
        """Advance past holes and return the logical block this record fills."""
        nonlocal ai, logical
        while ai < len(amap) and amap[ai] == 0:
            ai += 1
            logical += 1
        if ai >= len(amap):
            return None
        lb = logical
        ai += 1
        logical += 1
        return lb

    for n in range(last + 1):
        r = tape.get(n)
        if r is None:                    # lost record still consumes a map slot
            if cur is not None:
                take_slot()
            continue
        h = parse_header(r)
        if h:
            if h['type'] == TS_TAPE:
                tapehdr = h
                cur, amap = None, []
            elif h['type'] == TS_INODE:
                ino = h['inum']
                inodes[ino] = parse_dinode(r[22:86])
                order.append((h['tapea'], ino))
                cnt = struct.unpack('>h', r[86:88])[0]
                cur, amap, ai, logical = ino, list(r[88:88 + cnt]), 0, 0
            elif h['type'] == TS_ADDR:
                cnt = struct.unpack('>h', r[86:88])[0]
                amap, ai = list(r[88:88 + cnt]), 0
            else:                        # TS_CLRI / TS_BITS / TS_END
                cur, amap = None, []
            continue
        lb = take_slot() if cur is not None else None
        if lb is None:
            orphans.append((n, r))
        else:
            blocks[cur][lb] = r
    return tapehdr, inodes, blocks, order, missing, orphans


def adopt_orphans(inodes, blocks, orphans):
    """Reattach orphaned directory blocks.

    A V7 directory's first block opens with `.` naming the directory's own
    inode, which is enough to place the block even though its TS_INODE header
    was lost.  Only first blocks are adopted, so the logical index is always 0.
    """
    adopted = []
    for n, r in orphans:
        ino = struct.unpack('>H', r[0:2])[0]
        if r[2:16].split(b'\0')[0] != b'.' or not ino:
            continue
        if ino in blocks and 0 in blocks[ino]:
            continue
        # size 512 = the whole block; deleted slots carry inode 0 and are skipped
        # when the entries are read, so trailing padding costs nothing
        inodes.setdefault(ino, dict(mode=IFDIR | 0o777, nlink=0, uid=0, gid=0,
                                    size=512, atime=0, mtime=0, ctime=0))
        blocks[ino][0] = r
        adopted.append((n, ino))
    return adopted


def scheduled_inodes(tape):
    """Inodes the TS_BITS map says this dump was going to write."""
    for n in sorted(tape):
        h = parse_header(tape[n])
        if h and h['type'] == TS_BITS:
            cnt = struct.unpack('>h', tape[n][86:88])[0]
            m = b''.join(tape[n + 1 + k] for k in range(cnt) if (n + 1 + k) in tape)
            return [i + 1 for i in range(len(m) * 8) if m[i // 8] >> (i % 8) & 1]
    return []


def filedata(ino, inodes, blocks):
    """Reassemble a file; missing records come back as NUL, like a hole."""
    size = inodes[ino]['size']
    out = bytearray()
    for lb in range((size + 511) // 512):
        out += blocks[ino].get(lb, b'\0' * 512)
    return bytes(out[:size])


def dirents(ino, inodes, blocks):
    """V7 directory: 16-byte entries of 2-byte big-endian inum + 14-byte name."""
    out, size = [], inodes[ino]['size']
    for lb in range((size + 511) // 512):
        b = blocks[ino].get(lb)
        if b is None:
            continue
        for o in range(0, 512, 16):
            if lb * 512 + o >= size:
                break
            i = struct.unpack('>H', b[o:o + 2])[0]
            nm = b[o + 2:o + 16].split(b'\0')[0]
            if i:
                out.append((i, nm.decode('ascii', 'replace')))
    return out


def build_paths(inodes, blocks, root='/usr'):
    paths, queue = {2: root}, [2]
    while queue:
        ino = queue.pop(0)
        if (inodes.get(ino, {}).get('mode', 0) & IFMT) != IFDIR:
            continue
        for cino, nm in dirents(ino, inodes, blocks):
            if nm in ('.', '..') or cino in paths:
                continue
            paths[cino] = paths[ino].rstrip('/') + '/' + nm
            queue.append(cino)
    return paths


def ts(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if t else '-'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-d', '--dir', default=os.path.dirname(os.path.abspath(__file__)),
                    help='directory of *.bin_N.hex records')
    ap.add_argument('--out', help='.out image to source any blocks the .hex set lacks')
    ap.add_argument('-l', '--list', action='store_true', help='list the dump')
    ap.add_argument('-x', '--extract', metavar='DESTDIR', help='write out the file data present')
    args = ap.parse_args()
    if not (args.list or args.extract):
        ap.error('give -l or -x')

    tape = load_tape(args.dir, args.out)
    tapehdr, inodes, blocks, order, missing, orphans = parse(tape)
    adopted = adopt_orphans(inodes, blocks, orphans)
    paths = build_paths(inodes, blocks)
    for n, ino in adopted:
        print('adopted orphaned directory block at record %d as inode %d (%s)'
              % (n, ino, paths.get(ino, '?')), file=sys.stderr)

    if args.list:
        print('level-%s dump  volume %d  taken %s UTC'
              % ('0' if tapehdr['ddate'] == 0 else '?', tapehdr['volume'], ts(tapehdr['date'])))
        print('%d of %d tape records present; missing: %s'
              % (len(tape), max(tape) + 1, missing or 'none'))
        want = scheduled_inodes(tape)
        print('TS_BITS schedules %d inodes for this dump; %d reached the tape before it ends'
              % (len(want), len(inodes)))
        print('%d path names recovered\n' % len(paths))
        for tapea, ino in order:
            di = inodes[ino]
            have = len(blocks[ino])
            want = (di['size'] + 511) // 512
            print('rec %-5d ino %-5d %s%04o %-4d %-4d %9d  %s  %s%s'
                  % (tapea, ino, TYPECH.get(di['mode'] & IFMT, '?'), di['mode'] & 0o7777,
                     di['uid'], di['gid'], di['size'], ts(di['mtime']),
                     paths.get(ino, '<name lost with its parent directory>'),
                     '' if have >= want else '   [%d/%d blocks]' % (have, want)))
        named_only = sorted(p for i, p in paths.items() if i not in inodes)
        print('\n%d names appear in directories but their inodes are past the end '
              'of the tape:' % len(named_only))
        for p in named_only:
            print('   ', p)

    if args.extract:
        n = 0
        for ino in inodes:
            di = inodes[ino]
            if (di['mode'] & IFMT) != IFREG or not di['size']:
                continue
            rel = paths.get(ino, '_unnamed/ino%05d' % ino).lstrip('/')
            dest = os.path.join(args.extract, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as f:
                f.write(filedata(ino, inodes, blocks))
            n += 1
        print('extracted %d files to %s' % (n, args.extract))


if __name__ == '__main__':
    main()
