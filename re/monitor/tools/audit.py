#!/usr/bin/env python3
"""Sanity-check the regions.txt claims and report coverage.

Asserting that a range is code is the one thing in this workspace that `make
verify` cannot catch: a block of text reassembles byte for byte whether it is
labelled code or data.  The 0x132c block was originally asserted as code on the
strength of "decodes with no undefined opcodes and ends on the boundary", and
it turned out to be the diagnostic message table.

So each asserted code region is scored the way that mistake would have been
caught: text has a high proportion of printable bytes and, more tellingly, long
unbroken runs of them.  Real code here sits around 20-38% printable with runs
of 3 or under; the message block was 76% with a run of 25.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gen  # noqa: E402

RUN_LIMIT = 8               # a printable run this long wants explaining
BRANCH = {"jr", "jp", "call", "calr", "djnz", "dbjnz", "ldar"}


def score(blob):
    best = cur = 0
    for b in blob:
        cur = cur + 1 if 0x20 <= b < 0x7F else 0
        best = max(best, cur)
    return sum(1 for b in blob if 0x20 <= b < 0x7F) / max(len(blob), 1), best


def main():
    image, regions_path = sys.argv[1], sys.argv[2]
    img = pathlib.Path(image).read_bytes()
    regions = gen.read_regions(regions_path)

    print("asserted code regions (kind = code in regions.txt):")
    suspect = 0
    for lo, hi, kind, name in regions:
        if kind != "code":
            continue
        printable, run = score(img[lo:hi])
        flag = ""
        if run >= RUN_LIMIT:
            flag = f"  <-- {run}-byte printable run; confirm it is not text"
            suspect += 1
        print(f"  0x{lo:04x}..0x{hi:04x} {hi - lo:6d} B  printable {printable:4.0%}"
              f"  longest run {run:3d}{flag}")

    covered = [False] * len(img)
    for lo, hi, kind, _ in regions:
        for a in range(lo, hi):
            covered[a] = True
    unclaimed = sum(1 for lo, hi, kind, _ in regions
                    for a in range(lo, hi) if kind == "word")
    unmapped = covered.count(False)
    print(f"\ncoverage: {len(img) - unmapped - unclaimed} bytes classified, "
          f"{unclaimed} bytes mapped as undifferentiated .word data, "
          f"{unmapped} bytes not in regions.txt (tracer or fallback)")
    # --- operands that name a ROM address but are still written as hex -------
    import re
    src = pathlib.Path("monitor30.s").read_text().splitlines()
    candidates = []
    insn_starts = set()
    for line in src:
        m = re.match(r"\t(\S+)\t(\S.*?)\s{2,}/\* ([0-9a-f]{4}):", line)
        if m and not m.group(1).startswith("."):
            insn_starts.add(int(m.group(3), 16))
    for line in src:
        m = re.match(r"\t(\S+)\t(\S.*?)\s{2,}/\* ([0-9a-f]{4}):", line)
        if not m or m.group(1).startswith(".") or m.group(1) in BRANCH:
            continue
        for _, dig in re.findall(r"(#?)0x([0-9a-f]+)", m.group(2)):
            v = int(dig, 16)
            if len(dig) >= 3 and v < len(img) and v in insn_starts:
                candidates.append((m.group(3), m.group(1), m.group(2), v))
    print(f"\nbare hex operands whose value is an instruction boundary: "
          f"{len(candidates)}")
    print("  each is either an address nobody has proved yet, or a constant "
          "that happens\n  to collide with one -- see tools/pointers.py")
    for at, mnem, ops, v in candidates[:10]:
        print(f"    {at}  {mnem:6} {ops}")
    if len(candidates) > 10:
        print(f"    ... {len(candidates) - 10} more")

    if suspect:
        print(f"\n{suspect} region(s) flagged for review -- advisory, not a failure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
