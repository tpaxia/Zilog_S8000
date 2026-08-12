#!/usr/bin/env python3
"""Find operands that are provably addresses, and emit pointers.txt lines.

Outside branches and pointer tables, an operand that happens to fall inside the
ROM may be an address or may be an ordinary constant, and getting it wrong is
worse than leaving it as hex: substituting a symbol for a constant means the
constant silently changes if any code ahead of it moves.  `ld r7,#0x202` at
0x03b8 is a plain number; `ld r11,#0x160a` at 0x204a is an address.  Nothing in
the encoding distinguishes them.

So this only reports operands whose use proves what they are:

  * the argument register of a call to a routine that takes a pointer
  * LDA, which by definition computes an address
  * the r11/r13 pair set up immediately before the `jp @r12` dispatch

Everything else stays hex until a human reads it.

    pointers.py <image> <seeds> <regions>   > pointers.txt
"""

import re
import sys

import trace as tracer
from trace import load_seeds

# routine -> the register that carries the pointer argument
POINTER_ARGS = {
    0x050c: "r2",       # putmsg: r2 -> length-prefixed message
}
LOOKAHEAD = 3           # instructions between the load and the call


def find_wrappers(code):
    """Grow POINTER_ARGS with routines that just forward their argument.

    Several handlers reach putmsg through a one-line wrapper (0x12ea prints the
    message in r2 and then loads a couple of globals), so the callers of those
    wrappers are loading pointers too.
    """
    entries = set()
    for _, mnem, ops in code.values():
        if mnem in ("call", "calr"):
            m = re.search(r"0x([0-9a-f]+)\s*$", ops)
            if m:
                entries.add(int(m.group(1), 16))
    changed = True
    while changed:
        changed = False
        for entry in entries:
            if entry in POINTER_ARGS or entry not in code:
                continue
            _, mnem, ops = code[entry]
            if mnem not in ("call", "calr"):
                continue
            m = re.search(r"0x([0-9a-f]+)\s*$", ops)
            if m and int(m.group(1), 16) in POINTER_ARGS:
                POINTER_ARGS[entry] = POINTER_ARGS[int(m.group(1), 16)]
                changed = True


def main():
    image, seeds_path, regions_path = sys.argv[1:4]
    code = tracer.trace(image, load_seeds([seeds_path]))
    for line in open(regions_path):
        line = line.split("#")[0].split()
        if len(line) >= 3 and line[2] == "code":
            code.update(tracer.linear(image, int(line[0], 0), int(line[1], 0)))

    find_wrappers(code)
    ordered = sorted(code)
    index = {a: i for i, a in enumerate(ordered)}
    out = []

    def emit(addr, value, why):
        out.append((addr, value, why))

    for i, addr in enumerate(ordered):
        _, mnem, ops = code[addr]

        # LDA computes an address by definition
        m = re.match(r"^r\d+,0x([0-9a-f]+)", ops)
        if mnem == "lda" and m:
            emit(addr, int(m.group(1), 16), "LDA computes an address")
            continue

        # a pointer loaded into the argument register of a pointer-taking call
        m = re.match(r"^(r\d+),#0x([0-9a-f]+)$", ops)
        if mnem == "ld" and m:
            reg, value = m.group(1), int(m.group(2), 16)
            for j in range(i + 1, min(i + 1 + LOOKAHEAD, len(ordered))):
                _, m2, o2 = code[ordered[j]]
                if m2 not in ("call", "calr", "jp"):
                    continue
                t = re.search(r"0x([0-9a-f]+)\s*$", o2)
                if not t:
                    break
                target = int(t.group(1), 16)
                if POINTER_ARGS.get(target) == reg:
                    emit(addr, value, f"argument to the routine at 0x{target:04x}")
                break

    # the r11/r13 pair handed to the `jp @r12` dispatch
    for i, addr in enumerate(ordered):
        _, mnem, ops = code[addr]
        if not (mnem == "jp" and ops.endswith("@r12")):
            continue
        for j in range(max(0, i - 3), i):
            a2 = ordered[j]
            _, m2, o2 = code[a2]
            m = re.match(r"^(r11|r13),#0x([0-9a-f]+)$", o2)
            if m2 == "ld" and m:
                emit(a2, int(m.group(2), 16), "block bounds for the jp @r12 dispatch")

    print("# Operands that are addresses, not constants -- see tools/pointers.py.")
    print("# Generated candidates; hand-verified entries may be added below.")
    print("#   <instruction address> <operand value>   # why")
    for addr, value, why in sorted(set(out)):
        print(f"{addr:04x} {value:04x}   # {why}")


if __name__ == "__main__":
    main()
