#!/usr/bin/env python3
"""
zdis.py -- annotated z8000 disassembler for ZEUS / WEGA s.out binaries.

    zdis.py <binary> [--start 0xADDR] [--stop 0xADDR] [--data]

Pipeline:  sout.py (parse header/sections/symbols)
        -> unidasm (MAME z8000 backend)  for the raw disassembly
        -> annotate: syscall names, .o/symbol labels, call/branch targets,
           data & string references, entry-jump copyright string.

Backends resolved from:
    UNIDASM env, else ~/Projects/mame_latest/mame/unidasm
"""
import os, re, subprocess, sys, json, struct
import sout

HERE = os.path.dirname(os.path.abspath(__file__))
UNIDASM = os.environ.get("UNIDASM", os.path.expanduser("~/Projects/mame_latest/mame/unidasm"))
SYSCALLS = {int(k): v for k, v in json.load(open(os.path.join(HERE, "syscalls.json"))).items()} \
           if os.path.exists(os.path.join(HERE, "syscalls.json")) else {}

LINE = re.compile(r"^([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2,4}\s)+)\s*(.*)$")
HEXIMM = re.compile(r"%([0-9a-fA-F]{2,8})")      # unidasm renders values as %hhhh

def run_unidasm(code, base=0):
    """Return list of (addr, rawbytes, text) by disassembling `code`."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(code); tmp = f.name
    try:
        out = subprocess.run([UNIDASM, tmp, "-arch", "z8000", "-basepc", "0x%x" % base],
                             capture_output=True, text=True).stdout
    finally:
        os.unlink(tmp)
    rows = []
    for ln in out.splitlines():
        m = LINE.match(ln)
        if not m:
            continue
        addr = int(m.group(1), 16)
        raw = m.group(2).strip()
        rows.append((addr, raw, m.group(3).rstrip()))
    return rows

def printable(bs):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in bs)

class Disasm:
    def __init__(self, path):
        self.o = sout.SOut(path)
        self.code, self.cbase = self.o.code_section()
        self.data, self.dbase = self.o.data_section()
        self.dend = self.dbase + len(self.data)
        self.bss_end = self.dend + (self.o.segs[0].bss if self.o.segs else 0)
        # symbol map: addr -> name  (object-file boundaries etc.)
        self.symat = {}
        for s in self.o.symbols:
            self.symat.setdefault(s.value & 0xffff, s.name)
        self.rows = run_unidasm(self.code, self.cbase)
        self.addrs = {a for a, _, _ in self.rows}

    def data_at(self, addr):
        """If addr points into the data/rodata image, return a short preview."""
        # strings/rodata can also live in the code section (e.g. copyright)
        for blob, base, end in ((self.data, self.dbase, self.dend),
                                (self.code, self.cbase, self.cbase + len(self.code))):
            if base <= addr < end:
                off = addr - base
                chunk = blob[off:off+24]
                s = chunk.split(b"\0")[0]
                if len(s) >= 3 and all(9 <= c < 127 for c in s):
                    return '"%s"' % s.decode("latin1")
                w = struct.unpack(">H", chunk[:2])[0] if len(chunk) >= 2 else 0
                return "=0x%04x [%s]" % (w, printable(chunk[:8]))
        return None

    def annotate(self, addr, text):
        notes = []
        # syscalls:  sc #%NN
        m = re.search(r"\bsc\s+#%([0-9a-fA-F]+)", text)
        if m:
            n = int(m.group(1), 16)
            notes.append("SYS %s (#%d)" % (SYSCALLS.get(n, "?"), n))
        # branch/call targets:  call|calr|jp|jr [cc,] %XXXX   (absolute, no (rN))
        for m in re.finditer(r"\b(call|calr|jp|jr)\b[^%]*%([0-9a-fA-F]{2,8})(?!\s*\()", text):
            tgt = int(m.group(2), 16)
            if tgt in self.symat:
                notes.append("-> %s" % self.symat[tgt])
            elif tgt >= self.bss_end:
                notes.append("!! target 0x%x PAST image-end 0x%x (heap/zero)" % (tgt, self.bss_end))
        # immediate pointer loads:  ld rN,#%XXXX  (not register-relative)
        for m in re.finditer(r"\bld[bl]?\s+r+\w+,#%([0-9a-fA-F]{3,8})(?!\s*\()", text):
            tgt = int(m.group(1), 16)
            if tgt in self.symat:
                notes.append("#%s" % self.symat[tgt])
            else:
                d = self.data_at(tgt)
                if d:
                    notes.append("%x %s" % (tgt, d))
        # absolute memory operands:  ld rN,%XXXX  (no # , no (rN))
        for m in re.finditer(r"(?<![#(])%([0-9a-fA-F]{3,8})(?!\s*\()", text):
            if m.group().startswith("#"):
                continue
            tgt = int(m.group(1), 16)
            if self.dbase <= tgt < self.dend:
                d = self.data_at(tgt)
                if d and d not in " ".join(notes):
                    notes.append("[%x]%s" % (tgt, d))
        return "   ; " + " | ".join(dict.fromkeys(notes)) if notes else ""

    def dump(self, start=None, stop=None):
        out = [self.o.report(), ""]
        for addr, raw, text in self.rows:
            if start is not None and addr < start:  continue
            if stop  is not None and addr >= stop:  break
            if addr in self.symat:
                out.append("\n%s:  <%s>" % ("%04x" % addr, self.symat[addr]))
            out.append("%04x:  %-14s %-28s%s" % (addr, raw, text, self.annotate(addr, text)))
        return "\n".join(out)

if __name__ == "__main__":
    ap = sys.argv[1:]
    if not ap:
        sys.exit("usage: zdis.py <binary> [--start 0xADDR] [--stop 0xADDR]")
    path = ap[0]
    def opt(name, d=None):
        return int(ap[ap.index(name)+1], 0) if name in ap else d
    print(Disasm(path).dump(opt("--start"), opt("--stop")))
