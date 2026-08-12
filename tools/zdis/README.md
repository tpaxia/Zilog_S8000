# zdis — ZEUS / WEGA (Zilog S8000) binary reversing toolkit

Tools for disassembling ZEUS 3.21 binaries and reconstructing what they do,
using the WEGA kernel/library C sources as a cross-reference.

All binaries are big-endian **z8000**, in the Zilog **s.out** object format
(see `WEGA/src/head/sys/s.out.h`).

## Format cheat-sheet

`s_exec` header (24 B) + segment table + memory image + symbol table.

| magic  | meaning                          |
|--------|----------------------------------|
| E707   | nonsegmented executable          |
| E711   | nonsegmented, separate I & D     |
| E607   | segmented executable             |
| E611   | segmented, separate I & D        |

- `s_imsize` = loadable code+data; `s_bss` loaded zeroed after it.
- Image layout (nonseg, seg 0): `code[0..sg_code)`, `data[..+sg_data)`, `bss`.
- `flag & 1` (SF_STRIP) = relocation stripped. Most binaries are stripped of
  named symbols but **retain N_FN (0x1f) object-file boundary markers**
  (`crt0.o`, `printf.o`, `malloc.o`, …) — a map of the linked library modules.

## Tools

- **`sout.py <bin>`** — parse & report header, sections, symbols.
- **`zdis.py <bin> [--start A] [--stop B]`** — annotated disassembly
  (backend: MAME `unidasm`). Auto-annotates:
  - syscalls: `sc #%NN → SYS <name>` (table in `syscalls.json`)
  - immediate/absolute operands that point into data → the string/word there
  - call/branch targets past the image end → `!! PAST image-end (heap/zero)`
  - `.o`/symbol boundaries printed as labels
- **`libmap.py <tree> [--module NAME]`** — catalog the C-library `.o` modules
  across every symbol-bearing binary; locate where a module (e.g. `malloc.o`,
  `sbrk.o`) lives so you can identify the same routine inside a stripped one.

## Workflow to "derive source"

1. `sout.py bin` — understand the image map (where code/data/bss/heap are).
2. `zdis.py bin` — read the annotated code; syscalls + strings orient you fast.
3. For an unknown routine, `libmap.py` a symbol-bearing binary that links the
   same `.o` (same C library) to get its **name and size**, then match the
   routine by structure against the WEGA C source for that module.

## Finding: why `/etc/init` never reaches a login (trace + tools)

`init` runs correctly (argc≤1 → `getpid`=1 → 14 signals → close fds), then in
its `malloc` at `0x20D4` executes a hardcoded **`call 0x3578`** — an address
past the end of its own image (code ends 0x2732, bss ends 0x352A). `0x3578` is
zeroed heap, so it wild-executes zeros, wraps back to the entry `0x0000`, and
re-enters `main` with a corrupted stack → `r7>1` → prints `init: invalid state`
and exits. The `argc>1` / "invalid state" is a *symptom of the crash*, not a
boot-argument problem.

`zdis.py` flags the bad call automatically; `libmap.py` shows the call is a
`sbrk`/`morecore`-class memory routine that this image simply doesn't contain —
i.e. init's library linkage is incomplete for this build.
