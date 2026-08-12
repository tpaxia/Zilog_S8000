#!/usr/bin/env python3
"""
sout.py -- parser for the Zilog s.out / z.out object-module format used by
ZEUS / WEGA (Zilog System 8000).  Big-endian z8000.

Reference: WEGA/src/head/sys/s.out.h  and  .../z.out.h

File layout:
    [ s_exec header (24 bytes) ]
    [ segment table  (s_segt bytes, 16 bytes / entry) ]
    [ memory image   (s_imsize bytes = code+data of all segments) ]
    [ symbol table   (s_syms bytes, 14 bytes / entry) ]

s_exec (s.out.h struct s_exec), all big-endian:
    int      s_magic  (2)   magic number
    long     s_imsize (4)   size of the loadable memory-image section
    long     s_bss    (4)   size of bss
    unsigned s_segt   (2)   size of the segment-table section (bytes)
    unsigned s_syms   (2)   size of the symbol-table section (bytes)
    long     s_entry  (4)   entry-point address
    unsigned s_flag   (2)   flags (SF_STRIP=1 => relocation stripped)
    unsigned s_codesz (2)   8-bit padded code size
    unsigned s_lines  (2)   number of line-table entries

struct segt (16 bytes):
    char sg_segno, sg_coff, sg_doff, sg_boff     (offsets are *256)
    unsigned sg_code, sg_data, sg_bss            (section sizes)
    int  sg_atr                                  (SG_CODE/DATA/BSS/STACK/...)
    long sg_unused
"""
import struct, sys, json

# magic -> (family, segmented?, separate-I&D?, human)
MAGICS = {
    0xE607: ("s.out", True,  False, "Segmented executable"),
    0xE611: ("s.out", True,  True,  "Segmented separate I&D"),
    0xE605: ("s.out", True,  False, "Segmented overlay"),
    0xE707: ("s.out", False, False, "Nonsegmented executable"),
    0xE711: ("s.out", False, True,  "Nonsegmented separate I&D"),
    0xE705: ("s.out", False, False, "Nonsegmented overlay"),
    0xE507: ("s.out", False, False, "8-bit executable"),
    0xE511: ("s.out", False, True,  "8-bit separate I&D"),
    0xE807: ("z.out", False, False, "z.out Nonsegmented executable"),
    0xE811: ("z.out", False, True,  "z.out Nonsegmented separate I&D"),
    0xE810: ("z.out", False, False, "z.out Nonsegmented"),
}
SG_CODE, SG_DATA, SG_BSS, SG_STACK = 0x1, 0x2, 0x4, 0x8
SF_STRIP = 0x0001

class Segt:
    __slots__ = ("segno","coff","doff","boff","code","data","bss","atr","idx")
    def __init__(self, raw, idx):
        self.segno, self.coff, self.doff, self.boff = raw[0], raw[1], raw[2], raw[3]
        self.code, self.data, self.bss, self.atr = struct.unpack(">HHHH", raw[4:12])
        self.idx = idx
    def attrs(self):
        a=[]
        if self.atr & SG_CODE: a.append("CODE")
        if self.atr & SG_DATA: a.append("DATA")
        if self.atr & SG_BSS:  a.append("BSS")
        if self.atr & SG_STACK:a.append("STACK")
        return "|".join(a) or "-"

class Sym:
    __slots__ = ("value","type","segt","name")
    def __init__(self, value, typ, segt, name):
        self.value, self.type, self.segt, self.name = value, typ, segt, name

class SOut:
    def __init__(self, path):
        self.path = path
        self.raw = open(path, "rb").read()
        d = self.raw
        (self.magic, self.imsize, self.bss, self.segt_sz, self.syms_sz,
         self.entry, self.flag, self.codesz, self.lines) = struct.unpack(">HIIHHIHHH", d[:24])
        if self.magic not in MAGICS:
            raise ValueError("not an s.out/z.out object (magic=%04x)" % self.magic)
        self.family, self.segmented, self.sep_id, self.desc = MAGICS[self.magic]
        # segment table
        self.hdr_size = 24 + self.segt_sz
        self.segs = [Segt(d[24+i*16:24+i*16+16], i) for i in range(self.segt_sz // 16)]
        # memory image
        self.image = d[self.hdr_size : self.hdr_size + self.imsize]
        # symbol table
        so = self.hdr_size + self.imsize
        self.symbols = self._parse_syms(d[so : so + self.syms_sz]) if self.syms_sz else []

    def _parse_syms(self, s):
        out, i = [], 0
        while i + 14 <= len(s):
            value = struct.unpack(">i", s[i:i+4])[0]
            typ, segt = s[i+4], s[i+5]
            nb = s[i+6:i+14]
            if nb[0] & 0x80:                      # long name: len byte + overflow entries
                ln = nb[0] & 0x7F
                name = nb[1:]; need = ln - len(name) - 1
                j = i + 14
                while need > 0 and j + 14 <= len(s):
                    name += s[j:j+14]; need -= 14; j += 14
                name = name[:ln-1]; i = j
            else:
                name = nb.split(b"\0")[0]; i += 14
            out.append(Sym(value, typ, segt, name.decode("latin1", "replace")))
        return out

    # ---- code/data extraction -------------------------------------------
    def code_section(self):
        """Return (bytes, base_addr) for the primary code segment."""
        # nonseg: code occupies [0 .. sg_code); it is first in the image
        cs = self.segs[0].code if self.segs else self.imsize
        return self.image[:cs], 0

    def data_section(self):
        cs = self.segs[0].code if self.segs else 0
        ds = self.segs[0].data if self.segs else 0
        return self.image[cs:cs+ds], cs

    def layout(self):
        """List of (name, start, end, size) memory regions for seg 0 (nonseg)."""
        if not self.segs:
            return [("image", 0, self.imsize, self.imsize)]
        s = self.segs[0]
        code_end = s.code
        data_end = code_end + s.data
        bss_end  = data_end + s.bss
        return [("code", 0, code_end, s.code),
                ("data", code_end, data_end, s.data),
                ("bss",  data_end, bss_end, s.bss)]

    def uni_arch(self):
        return "z8000"

    def report(self):
        L = []
        L.append("%s" % self.path)
        L.append("  magic  : %04x  (%s, %s%s)" % (self.magic, self.desc,
                 "segmented" if self.segmented else "nonsegmented",
                 ", split I&D" if self.sep_id else ""))
        L.append("  imsize : 0x%x   bss: 0x%x   entry: 0x%x   flag: 0x%x%s" %
                 (self.imsize, self.bss, self.entry, self.flag,
                  "  (STRIP)" if self.flag & SF_STRIP else ""))
        L.append("  segt   : 0x%x (%d entry)   syms: 0x%x (%d)" %
                 (self.segt_sz, len(self.segs), self.syms_sz, len(self.symbols)))
        for s in self.segs:
            L.append("  seg[%d] segno=%02x code=0x%-5x data=0x%-5x bss=0x%-5x  "
                     "off(c/d/b)=%x/%x/%x  atr=%s" %
                     (s.idx, s.segno, s.code, s.data, s.bss,
                      s.coff*256, s.doff*256, s.boff*256, s.attrs()))
        for name, a, b, sz in self.layout():
            L.append("    %-4s 0x%04x .. 0x%04x  (0x%x)" % (name, a, b, sz))
        return "\n".join(L)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: sout.py <binary> [binary...]")
    for p in sys.argv[1:]:
        try:
            print(SOut(p).report()); print()
        except Exception as e:
            print("%s: %s\n" % (p, e))
