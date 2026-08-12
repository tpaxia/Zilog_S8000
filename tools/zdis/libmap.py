#!/usr/bin/env python3
"""
libmap.py -- catalog the C-library object modules (.o boundaries) across every
symbol-bearing ZEUS binary in a tree.  The linker leaves N_FN (type 0x1f)
file-name symbols at each object's code start even in otherwise-"stripped"
executables, so this recovers a map of which library modules exist, their
sizes, and where their source likely lives in the WEGA tree.

    libmap.py <root-dir> [--module printf]

Use it to identify a routine seen in a *stripped* binary (e.g. init's malloc
at 0x20D4): find a symbol-bearing binary that contains the same module and
read its named boundaries.
"""
import os, sys, glob
import sout

N_FN = 0x1f

def modules(o):
    """Yield (name, start, size) for each .o boundary in load order."""
    fns = sorted(((s.value & 0xffff, s.name) for s in o.symbols if s.type == N_FN))
    code_end = o.segs[0].code if o.segs else o.imsize
    for i, (a, nm) in enumerate(fns):
        end = fns[i+1][0] if i+1 < len(fns) else code_end
        yield nm, a, max(0, end - a)

def main(root, want=None):
    catalog = {}   # module -> list of (binary, start, size)
    for p in sorted(glob.glob(os.path.join(root, "**", "*"), recursive=True)):
        if not os.path.isfile(p):
            continue
        try:
            o = sout.SOut(p)
        except Exception:
            continue
        if not o.symbols:
            continue
        for nm, a, sz in modules(o):
            catalog.setdefault(nm, []).append((os.path.basename(p), a, sz))

    if want:
        print("module '%s':" % want)
        for b, a, sz in catalog.get(want, []):
            print("  %-16s @0x%04x  size 0x%x" % (b, a, sz))
        return
    print("== ZEUS C-library module atlas (%d distinct modules) ==" % len(catalog))
    for nm in sorted(catalog, key=lambda n: -len(catalog[n])):
        seen = catalog[nm]
        sizes = {sz for _, _, sz in seen}
        print("  %-14s  in %2d binaries   size(s): %s" %
              (nm, len(seen), ",".join("0x%x" % s for s in sorted(sizes))))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: libmap.py <root-dir> [--module NAME]")
    want = sys.argv[sys.argv.index("--module")+1] if "--module" in sys.argv else None
    main(sys.argv[1], want)
