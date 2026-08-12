#!/usr/bin/env python3
"""Print the traced disassembly, one instruction per line, for grepping."""

import sys

import trace as tracer
from trace import load_seeds


if __name__ == "__main__":
    image = sys.argv[1]
    seeds = load_seeds(sys.argv[2:])
    code = tracer.trace(image, seeds)
    for addr in sorted(code):
        length, mnem, ops = code[addr]
        print(f"{addr:04x}\t{length}\t{mnem}\t{ops}")
