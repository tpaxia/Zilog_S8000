# System 8000 CPU-A monitor 3.0 — annotated disassembly

A reassemblable, progressively annotated source for the 16 KB monitor EPROM set
on the Zilog System 8000 CPU-A board (the CPU used by the Model 11/21/**31**).

`make verify` proves the source is faithful: it assembles `monitor30.s` with the
z8k binutils and compares the result against the original ROM images byte for
byte. `make eproms` splits the rebuild back into the four 2732 files and prints
their SHA1s, which match MAME's `s8k_cpu` v3.0 set exactly.

## Layout

| file | role |
|---|---|
| `monitor30.s` | **generated** — do not hand-edit; regenerate with `make gen` |
| `monitor30.bin` | generated 16 KB reference image (`../../roms` interleaved) |
| `regions.txt` | code/data map: instructions, pointer tables, messages, filler |
| `seeds.txt` | code entry points the tracer cannot reach on its own |
| `equates.txt` | names for RAM and I/O addresses, substituted into operands |
| `annotations.txt` | symbols, block comments and end-of-line comments, by address |
| `escapes.txt` | instructions gas re-encodes differently; emitted as raw `.word` |
| `pointers.txt` | operands proved to be addresses rather than constants |
| `tools/rom.py` | join/split the four EPROMs ↔ flat image |
| `tools/trace.py` | recursive-descent code discovery |
| `tools/gen.py` | emit `monitor30.s` from the image plus the four map files |
| `tools/audit.py` | score the asserted code regions; catch text claimed as code |

All understanding lives in the hand-edited map files, never in `monitor30.s`, so
regenerating never loses work. The workflow is: learn something → record it in
`regions.txt` / `equates.txt` / `annotations.txt` / `seeds.txt` → `make gen` →
`make verify`.

## Targets

    make            assemble monitor30.s -> build/monitor30.bin
    make verify     byte-compare the rebuild against the original EPROMs
    make gen        regenerate monitor30.s from the image + map files
    make trace      report which parts of the image control flow reaches
    make audit      score the asserted code regions and report coverage
    make pointers   regenerate the provable address-operand declarations
    make eproms     split the rebuild into the four 2732 files and hash them

Requires the z8k binutils (`z8k-coff-as`, `z8k-coff-ld`, `z8k-coff-objdump`,
`z8k-coff-objcopy`) on `PATH`.

## Two things that make this ROM awkward to disassemble

**It is Z8002 code in a Z8001 ROM.** The Z8001 resets into segmented mode and
takes its initial FCW and PC from the reset PSA at image 0x0000. The monitor's
third instruction loads FCW `0x4000` — system mode, segmentation off — and
everything from 0x0078 onward uses non-segmented addressing. Disassembling with
`-m z8001` produces plausible-looking nonsense, because segmented operands are a
word longer. Everything here uses `-m z8002` / `unsegm`.

**A linear sweep cannot find the data.** The Z8000 opcode map is dense enough
that tables and text decode as valid instructions — a straight `objdump -D` of
the whole image yields only 27 invalid words in 16 KB. `tools/trace.py` walks
control flow instead, seeded from the reset vector, the command dispatch table
and the trap vectors.

That gets 4698 bytes. The rest is entered at addresses only known at run time —
through `jp @rN` with the target in RAM, and through two blobs that relocate
themselves before executing — so `regions.txt` asserts those ranges as code and
`tools/trace.py:linear()` decodes them, rechecking on every build that the range
has no undefined opcodes and that its last instruction ends exactly on the
boundary. Anything still unclaimed is emitted as `.word` data with an ASCII
gloss, which keeps the rebuild exact either way.

## What is known so far

**Reset (0x0070).** Drop to non-segmented mode, clear MMU register 0, read the
console baud rate from the DIP switches in the top nibble of the system
configuration register (I/O 0xffc1), program the two console CTC channels and
both SIO channels, zero local RAM, install the program status area, print the
banner, enable interrupts.

**Console.** SIO0 **channel B** — data at 0xff83, control at 0xff87. Receive is
interrupt-driven into a 256-byte ring at 0x41b0; transmit polls RR0 bit 1 and
honours an XOFF hold-off flag set by the receive interrupt. The CTC counts a
1.2288 MHz clock and the SIO runs a ×64 sample rate, so the divisors in
`baud_table` (0x02f0) are 0x40/0x10/0x02/0x01 for 300/1200/9600/19200 baud.

**Command loop (0x016c).** Reloads the stack pointer every iteration and pushes
its own address as the handler return address, so handlers exit with a plain
`RET`. The command letter is matched by scanning `cmd_letters` (0x01b2)
*backwards* with `CPDRB`, which leaves a zero-based index in r1 that then
indexes `cmd_dispatch` (0x01c2). The 15 commands are:

| | | | | |
|---|---|---|---|---|
| B 0x0c3e | C 0x033e | D 0x03b2 | F 0x02f4 | G 0x0b54 |
| I 0x06d4 | J 0x0b42 | L 0x0dc2 | M 0x0316 | N 0x0bc6 |
| T 0x148e | Q 0x0bf8 | R 0x07a6 | Z 0x1294 | P 0x06de |

**Program status area.** A 144-byte template at 0x0250 is copied to RAM 0x4400
and installed with `LDCTL PSAPOFF`. It uses the Z8001 *segmented* PSA format
(four words per trap) even though the loaded FCWs select non-segmented mode,
because the PSA layout follows the CPU type, not the current mode. Every unused
trap and vector points at `trap_uninit_vector` (0x0218), which prints
`UNINITIALIZED VECTOR ENTRY ID=` plus the vector it arrived through. The live
entries are the system-call trap (0x0f2c, entered segmented), the NMI (0x12fc),
and four console SIO vectors (0x12/0x14/0x1a/0x1c).

**Messages.** Most monitor text is length-prefixed: a word holding the byte
count, then that many characters, then a pad byte to restore word alignment.
`putmsg` (0x050c) copies such a block into the output buffer and ships it.
A few strings (`ENTRY POINT `) are plain NUL-terminated instead.

**Power-up diagnostics (0x2bd8).** The diagnostic relocates itself: it copies
0x66c bytes to 0xf000 and jumps there, so that it can test the memory it came
from. Image 0x2bf2..0x325e is therefore linked for 0xf000 — absolute addresses
inside it are runtime addresses, not image offsets, and internal calls are
PC-relative so they survive the move.

## Relocatability

Not every address in the source is symbolic, and it deliberately cannot be.

| where | symbolic? |
|---|---|
| branch, call and `ldar` targets | yes — all 931 |
| `ptr` table entries (`reset_psa`, `rom_entry_vec`, `cmd_dispatch`, `psa_template`) | yes, `.word <label>` |
| every other operand | only where `pointers.txt` declares it |

The last row is the awkward one. An operand such as `ld r7,#0x202` may be an
address or an ordinary number, and nothing in the encoding distinguishes them —
`0x202` there is a plain constant, while `ld r11,#0x160a` two kilobytes away is
a real address. Guessing wrong is *worse than leaving hex*: naming a constant
means its value silently changes as soon as any code ahead of it moves.

So `tools/gen.py` symbolises a ROM address only where `pointers.txt` says the
operand is one. `make pointers` regenerates the provable subset — LDA (which
computes an address by definition), the argument register of a call to a
pointer-taking routine and its forwarding wrappers, and the `r11`/`r13` pair set
up before the `jp @r12` dispatch — and the rest of the file is hand-verified
additions. Equates are exempt: RAM and I/O addresses are absolute and never
move, so naming one can only affect readability.

`make audit` reports what is left: currently 52 bare operands whose value
happens to be an instruction boundary, each either an unproved address or a
constant that collides with one.

The trailing filler is not in the source.  The image ends with 26 zero bytes
aligning the last routine to a 256-byte boundary, then 3328 bytes of erased
EPROM.  The source emits `.balign 0x100,0x00` for the first and stops; the
build supplies the rest with `objcopy --pad-to 0x4000 --gap-fill 0xff`, and the
Makefile refuses an image over 16384 bytes.  So there is 3.25 KB of slack that
new code can grow into without touching anything else.

Inserting an instruction at `reset` now behaves: the image stays 16384 bytes and
every dispatch table follows.

| table entry | before | after inserting one NOP |
|---|---|---|
| `cmd_dispatch['B']` | 0x0c3e | 0x0c40 |
| `rom_entry_vec[1]` | 0x0a68 | 0x0a6a |
| PSA system-call vector | 0x0f2c | 0x0f2e |

**The caveat is whatever is still `.word`.** Those blocks are instructions
frozen as data: they do not relocate, and any address inside them goes stale.
Until a region is classified as code or as a `ptr` table, inserting anything
ahead of it is unsafe.

## Asserting that a range is code

`make verify` cannot catch a wrong code/data call: a block of text reassembles
byte for byte whether it is labelled code or data. Two checks compensate.

`tools/trace.py:linear()` refuses a range containing an undefined opcode, or one
whose last instruction overruns the end — a misaligned guess almost always trips
one of those. GNU as is the second arbiter, and a stricter one than objdump: it
rejects encodings objdump will happily print, such as the odd register pair in
`subl rr13,...`. That is what exposed the strings embedded at the end of the
0xf000 blob.

Neither is sufficient. `0x132c..0x148e` passed both — 103 instructions, no
undefined opcodes, ending exactly on the boundary — and is in fact the
power-up diagnostic message table. `tools/audit.py` scores each asserted region
the way that mistake would have been caught: real code here runs 20–38%
printable bytes with runs of 3 or under, while that block was 76% printable with
a 25-byte run.

## Known assembler differences

Two instructions cannot be reproduced by GNU as and are emitted as `.word` (see
`escapes.txt`): `srlb rl3,#4` at 0x0084 and `srlb rl0,#6` at 0x149e. The shift
count is a signed 16-bit word of which byte operations use only the low byte;
the original assembler sign-extended it (`0xfffc`), gas emits `0x00fc` and
rejects the sign-extended form as out of range. The instructions are identical
in effect — this is an encoding choice, not a semantic difference.

## Still to do

11636 of the 16384 bytes are now instructions in the source. Of the remainder,
3354 are filler and the rest is identified data — messages, dispatch tables, the
PSA template, the diagnostic tables at 0x1402. Two things are still open:

- **The two relocated blobs are decoded but not yet understood.** Image
  0x2bf2–0x3210 runs at 0xf000 and 0x325e–0x32cc at 0xf800. Internal `calr` and
  `ldar` are PC-relative, so assembling them at their image address reproduces
  the bytes exactly and the labels work; but their *absolute* operands are
  runtime addresses (0xfexx, 0xffxx) and are still bare hex.
- **Command handlers are named by letter.** `cmd_B` … `cmd_P`, because guessing
  a mnemonic would be inventing information. `cmd_Z` (boot, with a D/T/S/M
  sub-letter) and `cmd_T` (off-board memory test) are the two read closely
  enough to describe. The driver entries called indirectly through `iovec_read`
  / `iovec_write` (0x43ba/0x43bc) are also still unidentified.
