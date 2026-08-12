#!/usr/bin/env python3
"""Recursive-descent code discovery for the S8000 monitor image.

The Z8000 opcode map is dense enough that a linear sweep decodes data as
plausible instructions, so a straight objdump can't tell code from tables.
This walks control flow instead, seeded from the reset vector and any
addresses given on the command line, and reports the reachable code extents.

Decoding is delegated to `z8k-coff-objdump -m z8002`: for each seed we
disassemble a window starting exactly at that (known-good) boundary and take
instructions until a flow terminator or an already-decoded address.
"""

import re
import subprocess
import sys

OBJDUMP = "z8k-coff-objdump"
WINDOW = 0x400

LINE = re.compile(r"^\s*([0-9a-f]+):\t((?:[0-9a-f]{4} ?)+)\s*\t(\S+)(?:\t(.*))?$")

# unconditional flow terminators: nothing after them is necessarily code
TERMINATORS = {"iret", "halt"}
# cc `t` (always) makes these terminate; any other cc falls through
COND_TERM = {"jp", "jr", "ret"}
# operands that name a code target
CALLS = {"call", "calr"}
BRANCHES = {"jp", "jr", "djnz", "dbjnz"}


def disasm(image_path, start, stop):
    out = subprocess.run(
        [OBJDUMP, "-D", "-b", "binary", "-m", "z8002",
         f"--start-address=0x{start:x}", f"--stop-address=0x{stop:x}", image_path],
        capture_output=True, text=True, check=True).stdout
    insns = []
    for line in out.splitlines():
        m = LINE.match(line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        raw = m.group(2).split()
        insns.append((addr, len(raw) * 2, m.group(3), (m.group(4) or "").strip()))
    return insns


def trace(image_path, seeds, size=0x4000):
    code = {}                      # addr -> (length, mnemonic, operands)
    pending = list(seeds)
    seen_seeds = set()
    while pending:
        seed = pending.pop()
        if seed in code or seed in seen_seeds or not (0 <= seed < size):
            continue
        seen_seeds.add(seed)
        for addr, length, mnem, ops in disasm(image_path, seed, min(seed + WINDOW, size)):
            if addr in code:
                break                       # rejoined known code
            code[addr] = (length, mnem, ops)
            target = None
            if mnem in CALLS or mnem in BRANCHES:
                m = re.search(r"0x([0-9a-f]+)\s*$", ops)
                if m:
                    target = int(m.group(1), 16)
            if target is not None and target not in code:
                pending.append(target)
            if mnem in TERMINATORS:
                break
            if mnem in COND_TERM and (ops == "t" or ops.startswith("t,")):
                break
    return code


def extents(code):
    """Collapse decoded addresses into contiguous [start,end) runs."""
    runs = []
    for addr in sorted(code):
        length = code[addr][0]
        if runs and runs[-1][1] == addr:
            runs[-1][1] = addr + length
        else:
            runs.append([addr, addr + length])
    return [tuple(r) for r in runs]


def load_seeds(args):
    """Seeds come from literal addresses and/or `# comment`-annotated files."""
    seeds = []
    for a in args:
        if a.startswith("0x") or a.isdigit():
            seeds.append(int(a, 0))
            continue
        for line in open(a):
            line = line.split("#")[0].strip()
            if line:
                seeds.append(int(line, 0))
    return seeds


if __name__ == "__main__":
    image = sys.argv[1]
    seeds = load_seeds(sys.argv[2:]) or [0x0070]
    code = trace(image, seeds)
    runs = extents(code)
    covered = sum(e - s for s, e in runs)
    print(f"# {len(code)} instructions, {covered} bytes code, {len(runs)} runs")
    prev_end = 0
    for s, e in runs:
        if s > prev_end:
            print(f"  GAP  {prev_end:04x}-{s:04x}  ({s - prev_end} bytes)")
        print(f"  CODE {s:04x}-{e:04x}  ({e - s} bytes)")
        prev_end = e
    if prev_end < 0x4000:
        print(f"  GAP  {prev_end:04x}-4000  ({0x4000 - prev_end} bytes)")


def linear(image_path, lo, hi):
    """Decode [lo,hi) as a straight instruction run.

    For blocks that control flow provably enters but whose entry address is
    only known at run time -- reached through `jp @rN`, or relocated elsewhere
    before being executed.  The caller must have evidence the range is code;
    this checks the two things that would show it is not, namely an undefined
    opcode or a final instruction that overruns the end of the range.
    """
    insns = {}
    for addr, length, mnem, ops in disasm(image_path, lo, hi):
        if mnem == ".word":
            raise SystemExit(f"linear 0x{lo:04x}-0x{hi:04x}: "
                             f"undefined opcode at 0x{addr:04x} -- not code")
        insns[addr] = (length, mnem, ops)
    if insns:
        last = max(insns)
        if last + insns[last][0] != hi:
            raise SystemExit(f"linear 0x{lo:04x}-0x{hi:04x}: last instruction "
                             f"at 0x{last:04x} ends at 0x{last + insns[last][0]:04x}, "
                             f"not on the boundary -- misaligned")
    return insns
