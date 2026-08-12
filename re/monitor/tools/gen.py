#!/usr/bin/env python3
"""Generate monitor30.s from the ROM image plus the annotation files.

Code extents come from tools/trace.py; regions.txt overrides that with the data
areas (strings, dispatch tables, message blocks) as they get identified.
Anything neither claims is emitted as .word data with an ASCII gloss, so the
output always reassembles byte-for-byte even where the code/data split is still
unknown.

Understanding of the ROM lives in three hand-edited files rather than in the
generated source, so regenerating never loses it:

  regions.txt     code/data map
  equates.txt     names for RAM and I/O addresses, substituted into operands
  annotations.txt symbols, block comments and end-of-line comments, by address
  escapes.txt     instructions gas re-encodes differently; emitted as raw .word

    gen.py <image> <regions> <seeds> <escapes> <equates> <annotations>
"""

import re
import struct
import sys

import trace as tracer
from trace import load_seeds

SIZE = 0x4000
COL = 48                                    # column the /* addr: bytes */ note starts at

TARGET_OPS = re.compile(r"0x([0-9a-f]+)\s*$")
# operands gas can resolve from a symbol (absolute or PC-relative)
TARGET_MNEMONICS = {"jr", "jp", "call", "calr", "djnz", "dbjnz", "ldar"}
# any hex literal in an operand, immediate (#0x..) or direct (0x..)
HEXNUM = re.compile(r"(#?)0x([0-9a-f]+)")


def read_regions(path):
    """`start end kind [name]`; kind is code|ptr|word|byte|string|msg|fill|blank."""
    regions = []
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line:
            continue
        f = line.split()
        regions.append((int(f[0], 0), int(f[1], 0), f[2], f[3] if len(f) > 3 else None))
    return sorted(regions)


def read_escapes(path):
    return {int(line.split("#")[0].strip(), 0)
            for line in open(path) if line.split("#")[0].strip()}


def read_equates(path):
    """`addr name  # comment` -> {value: name} plus the ordered list for .equ."""
    order, by_value = [], {}
    for line in open(path):
        body, _, note = line.partition("#")
        f = body.split()
        if len(f) < 2:
            continue
        value, name = int(f[0], 0), f[1]
        by_value[value] = name
        order.append((name, value, note.strip()))
    return by_value, order


def read_annotations(path):
    """`addr = symbol`, `addr : eol comment`, `addr ; block comment line`."""
    symbols, eol, block = {}, {}, {}
    for line in open(path):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"\s*([0-9a-fA-Fx]+)\s*([=:;])\s?(.*)$", line)
        if not m:
            raise SystemExit(f"annotations: cannot parse {line!r}")
        addr, op, text = int(m.group(1), 16), m.group(2), m.group(3)
        if op == "=":
            symbols[addr] = text.strip()
        elif op == ":":
            eol[addr] = text.strip()
        else:
            block.setdefault(addr, []).append(text)
    return symbols, eol, block


def gloss(chunk):
    return "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)


def read_pointers(path):
    """`insn_addr value` -- operands proved to be addresses, not constants.

    Substituting a symbol for something that is really a constant is worse than
    leaving hex, because the constant then changes if code ahead of it moves.
    So an operand naming a ROM address is only symbolised where it appears
    here; see tools/pointers.py for how the list is derived.
    """
    declared = {}
    for line in open(path):
        f = line.split("#")[0].split()
        if len(f) >= 2:
            declared.setdefault(int(f[0], 16), set()).add(int(f[1], 16))
    return declared


def substitute(ops, equ, labels, allowed):
    """Name equates freely; name ROM addresses only where declared.

    Equates are absolute RAM and I/O addresses -- they never move, so naming
    one can only affect readability.  A ROM address does move, so it is named
    only when `allowed` says this operand really is an address.
    """
    def repl(m):
        hashmark, digits = m.group(1), m.group(2)
        value = int(digits, 16)
        if value in equ:
            return hashmark + equ[value]
        if value in allowed and value in labels:
            return hashmark + labels[value]
        # a table scanned backwards is addressed one below its first entry
        if value + 1 in allowed and value + 1 in labels:
            return f"{hashmark}{labels[value + 1]}-1"
        return m.group(0)
    return HEXNUM.sub(repl, ops)


class Emitter:
    def __init__(self, img, symbols, eol, block, labels):
        self.img, self.symbols, self.eol, self.block = img, symbols, eol, block
        self.labels, self.out = labels, []

    def line(self, text, addr, raw=""):
        note = f"{addr:04x}: {raw}" if raw else f"{addr:04x}"
        comment = self.eol.get(addr)
        if comment:
            note = f"{note}  -- {comment}" if raw else f"{note}  {comment}"
        self.out.append(f"{text:<{COL}}/* {note} */")

    RULE = "/* " + "-" * 68
    END = " " + "-" * 68 + " */"

    def at(self, addr):
        lines = self.block.get(addr)
        if lines:
            self.out.append("")
            self.out.append(self.RULE)
            for text in lines:
                self.out.append(f" * {text}".rstrip())
            self.out.append(self.END)
        if addr in self.labels:
            self.out.append(f"{self.labels[addr]}:")


def main():
    (image_path, regions_path, seeds_path, escapes_path,
     equates_path, annotations_path, pointers_path) = sys.argv[1:8]

    img = open(image_path, "rb").read()
    assert len(img) == SIZE
    regions = read_regions(regions_path)
    escapes = read_escapes(escapes_path)
    equ, equ_order = read_equates(equates_path)
    symbols, eol, block = read_annotations(annotations_path)
    declared = read_pointers(pointers_path)
    code = tracer.trace(image_path, load_seeds([seeds_path]))
    # blocks we have evidence for but the tracer cannot reach on its own
    for start, end, k, _ in regions:
        if k == "code":
            code.update(tracer.linear(image_path, start, end))

    # ---- classify every byte -------------------------------------------------
    kind = ["word"] * SIZE                  # default: undifferentiated data
    for start, end, k, _ in regions:
        for a in range(start, end):
            kind[a] = k
    for addr, (length, _, _) in code.items():
        span = range(addr, addr + length)
        if all(kind[a] == "word" for a in span):    # regions.txt wins outright
            for a in span:
                kind[a] = "code"

    # ---- labels: branch targets, region names, hand-given symbols ------------
    labels = {}
    for addr, (_, mnem, ops) in code.items():
        m = TARGET_OPS.search(ops)
        if m and mnem in TARGET_MNEMONICS:
            t = int(m.group(1), 16)
            if t < SIZE:
                labels.setdefault(t, f"L_{t:04x}")
    # an address that falls inside an instruction cannot carry a label; the
    # CPDRB tables are addressed one byte below their first entry, so those
    # get named as `table-1` instead (see substitute()).
    interior = {a for addr, (length, _, _) in code.items()
                for a in range(addr + 1, addr + length)}
    for values in declared.values():
        for value in values:
            if value < SIZE and value not in interior:
                labels.setdefault(value, f"L_{value:04x}")
    for start, end, k, _ in regions:
        if k != "ptr":
            continue
        for a in range(start, end, 2):
            target = struct.unpack_from(">H", img, a)[0]
            if target in code:
                labels.setdefault(target, f"L_{target:04x}")
    for start, _, _, name in regions:
        if name:
            labels[start] = name
    labels.update(symbols)

    em = Emitter(img, symbols, eol, block, labels)
    w = em.out.append

    w("/*")
    w(" * Zilog System 8000 CPU-A monitor, version 3.0")
    w(" *")
    w(" * Reassembled from the four 2732 EPROMs on the CPU-A board:")
    w(" *   cpu_34-0715-03a.u76  cpu_34-0716-03a.u74   image 0x0000..0x1fff")
    w(" *   cpu_34-0718-03a.u77  cpu_34-0717-03a.u75   image 0x2000..0x3fff")
    w(" * u76/u77 supply the even (high) bytes, u74/u75 the odd (low) bytes.")
    w(" *")
    w(" * The Z8001 comes out of reset segmented, but the monitor drops to")
    w(" * non-segmented operation at 0x0078 and stays there, so the image")
    w(" * assembles as Z8002 code throughout.")
    w(" *")
    w(" * Generated by tools/gen.py from regions.txt, equates.txt and")
    w(" * annotations.txt; `make verify` proves the result rebuilds the four")
    w(" * EPROM images byte for byte.")
    w(" */")
    w("")
    w("\tunsegm")
    w("")
    for name, value, note in equ_order:
        text = f"\t.equ\t{name},0x{value:04x}"
        w(f"{text:<{COL}}/* {note} */" if note else text)
    w("")
    w("\t.text")
    w("")

    addr = 0
    while addr < SIZE:
        em.at(addr)
        k = kind[addr]

        if k == "code" and addr in code and addr in escapes:
            # gas cannot reproduce this encoding: emit the whole instruction,
            # every word of it, as data and keep the disassembly in the note.
            length, mnem, ops = code[addr]
            words = [struct.unpack_from(">H", img, a)[0]
                     for a in range(addr, addr + length, 2)]
            vals = ", ".join(f"0x{v:04x}" for v in words)
            em.line(f"\t.word\t{vals}", addr, f"{mnem} {ops}")
            addr += length

        elif k == "code" and addr in code:
            length, mnem, ops = code[addr]
            m = TARGET_OPS.search(ops)
            if m and mnem in TARGET_MNEMONICS and int(m.group(1), 16) in labels:
                ops = ops[:m.start()] + labels[int(m.group(1), 16)]
            else:
                ops = substitute(ops, equ, labels,
                                 declared.get(addr, frozenset()))
            raw = " ".join(f"{struct.unpack_from('>H', img, addr + i)[0]:04x}"
                           for i in range(0, length, 2))
            em.line(f"\t{mnem}\t{ops}".rstrip(), addr, raw)
            addr += length

        elif k == "ptr":
            # a table of code addresses: emit each as a symbol so that the
            # table tracks the code when anything ahead of it changes size
            target = struct.unpack_from(">H", img, addr)[0]
            text = labels[target] if target in labels and target in code \
                else f"0x{target:04x}"
            em.line(f"\t.word\t{text}", addr, f"{target:04x}")
            addr += 2

        elif k == "fill":
            end = addr
            while end < SIZE and kind[end] == "fill":
                end += 1
            em.line("\t.balign\t0x100,0x00", addr,
                    f"{end - addr} pad bytes to a 256-byte boundary")
            addr = end

        elif k == "blank":
            # erased EPROM: supplied by the build (objcopy --gap-fill), so the
            # source stops here and new code can simply grow into the space
            end = addr
            while end < SIZE and kind[end] == "blank":
                end += 1
            em.out.append("")
            em.out.append(f"\t/* 0x{addr:04x}..0x{end - 1:04x} is erased EPROM"
                          f" (0xff), added by the build */")
            addr = end

        elif k == "msg":
            length = struct.unpack_from(">H", img, addr)[0]
            text = img[addr + 2:addr + 2 + length]
            em.line(f"\t.word\t{length}", addr, f"{length} bytes of text follow")
            for chunk in _ascii_lines(text):
                w(chunk)
            addr += 2 + length
            if addr & 1:                    # messages are word-aligned; pad byte
                w(f"\t.byte\t0x{img[addr]:02x}")
                addr += 1

        elif k == "string":
            end = addr
            while end < SIZE and kind[end] == "string":
                if end != addr and end in labels:   # a label may point inside
                    break                           # a string: split it there
                end += 1
            em.line(_ascii_lines(img[addr:end])[0], addr, "")
            for chunk in _ascii_lines(img[addr:end])[1:]:
                w(chunk)
            addr = end

        elif k == "byte":
            end = addr
            while end < SIZE and kind[end] == "byte" and end - addr < 6:
                if end != addr and end in labels:
                    break
                end += 1
            vals = ", ".join(f"0x{b:02x}" for b in img[addr:end])
            em.line(f"\t.byte\t{vals}", addr, gloss(img[addr:end]))
            addr = end

        else:
            n = 1 if addr in escapes else 4
            end = addr
            while end < SIZE and kind[end] == kind[addr] and end - addr < 2 * n:
                if end != addr and end in labels:
                    break
                end += 2
            words = [struct.unpack_from(">H", img, a) [0] for a in range(addr, end, 2)]
            vals = ", ".join(f"0x{v:04x}" for v in words)
            raw = gloss(img[addr:end])
            if addr in escapes:
                _, mnem, ops = code[addr]
                raw = f"{mnem} {ops}"
            em.line(f"\t.word\t{vals}", addr, raw)
            addr = end

    print("\n".join(em.out))


def _ascii_lines(data):
    """Render bytes as .ascii runs with explicit .byte for anything else."""
    lines, run = [], bytearray()
    for b in data:
        if 0x20 <= b < 0x7F and b not in (0x22, 0x5C):
            run.append(b)
            continue
        if run:
            lines.append(f'\t.ascii\t"{run.decode("ascii")}"')
            run = bytearray()
        lines.append(f"\t.byte\t0x{b:02x}")
    if run:
        lines.append(f'\t.ascii\t"{run.decode("ascii")}"')
    return lines or ["\t/* empty */"]


if __name__ == "__main__":
    main()
