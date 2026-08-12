# The cartridge tape controller: firmware, command set, and the monitor link

The System 8000's cartridge tape controller is an **intelligent Z80 board** with
its own 4 KB firmware. This documents what that firmware does, the command set
it implements, and how the commands the CPU monitor issues resolve to handlers
inside it.

The evidence below comes from the controller ROMs, the hardware manual and
board photographs, the recovered ZEUS `ct(4)` manual page, and captured SADIE
and installation media. Statements that remain inference rather than direct
evidence are marked at the end.

## The ROMs and their order

| File | SHA-256 | Address range |
|---|---|---|
| `tcc_34-0607-01a.u97` | `594a7c59fca586bb6db95aa42804ae1dc192c638d57fccffea284fcaa571881b` | 0x0000–0x07FF |
| `tcc_34-0608-01a.u96` | `c68fdc0b6c5232969da3247878574d621a183aef29cf69765c40278a07a2053d` | 0x0800–0x0FFF |

Concatenated in that order the image is
`27693532fc40a886b0f99dad936841c5585822aaee9995cfcee5faa54d7a8eda`.

The ordering was established empirically, not assumed: disassembled with `u97`
low, **55 of 55** absolute `jp`/`call` targets land on instruction boundaries.
Reversed, only 31 of 55 (56%). To reproduce:

```sh
cat tcc_34-0607-01a.u97 tcc_34-0608-01a.u96 > tcc.bin
z80dasm -a -t -g 0 tcc.bin > tcc.asm
```

## Where each layer of the tape format lives

The recording chain has three distinct layers, and only the top one is in this
firmware:

| Layer | Implemented by |
|---|---|
| MFM encode/decode and bit-clock recovery | **the drive**, which presents a serial NRZ interface — see below |
| Byte framing, serial↔parallel, block sequencing | **discrete TTL on the controller** |
| CRC generation and checking | **two 9401** CRC chips on the controller, U50 and U52 |
| Block structure, command execution, host transfer | **this Z80 firmware** |

### The drive interface is NRZ, not MFM

This is settled by the manual's own signal definitions, not inferred. The
drive-to-controller connector (03-3198-01 §4.5, Tables 4-25 and 4-26, and the
P2/J24 pinout) carries:

| Pin | Signal | Direction | Definition |
|---|---|---|---|
| 18 | `RNZ\` | drive → controller | read NRZ serial data |
| 19 | `RDS\` | drive → controller | read data strobe (recovered bit clock) |
| 20 | `DAD\` | drive → controller | data detected |
| 21 | `WDE\` | controller → drive | "enables sending of write-data strobes and the writing of data on the tape" |
| 22 | `WNZ\` | controller → drive | "serial data to be written to the tape drive" |
| 24 | `WDS\` | controller → drive | write data strobe |

Serial **NRZ plus a strobe in both directions**. So MFM encoding, decoding and
clock recovery all happen on the drive side; the controller never sees flux or
MFM cells.

**The practical consequence is that the sync mark is an ordinary data pattern,
not an encoding violation.** There is no clock for the controller to violate —
by the time data crosses this connector it is plain serial bits. Byte alignment
must therefore be recovered by searching the NRZ bit stream for a known pattern,
which is exactly what a shift register plus comparison logic does.

### The board itself

The card is silkscreened `CARTRIDGE TAPE CONTROLLER 09-0208`, `COPYRIGHT 1980`,
artwork `10-0208-01 REV.A`. There is **no LSI formatter of any kind** — the only
large-scale parts are the Z80B (`Z84008 PS`) and the two EPROMs, which carry the
very labels this document disassembles, `34-0607-01 A` and `34-0608-01 A`.

| Part | Refs | Role |
|---|---|---|
| `SN74LS166` 8-bit parallel-load shift register | U47 | serial↔parallel, and the sync-pattern search window |
| `SN74LS193` synchronous up/down counter ×4 | U29, U30, U44, U45 | bit and byte counting within a block |
| `SN74S225` 16×5 FIFO ×2 | U31, U46 | elastic buffer between the tape bit rate and the Z80 bus |
| `74LS109` dual JK ×~10, `DM74S74` dual D | left bank | block sequencer and strobe timing |
| `9401PC` ×2 | U50, U52 | CRC generate/check |

Test points on the card mirror the drive interface — **BCLK**, **RDS-**,
**WDS-**, **DS-**, **AS-**, **DAD-**, plus **FWD-**/**REV-** — consistent with
NRZ-level signalling rather than flux handling.

So the chain is:

```text
tape flux
  -> drive: MFM decode + PLL                       -> RNZ serial bits + RDS bit clock
  -> controller: 74LS166 sync search and assembly  -> bytes
  -> 74S225 FIFOs                                  -> elastic buffer
  -> 9401 x 2                                      -> CRC
  -> Z80B                                          -> blocking, commands
  -> host DMA
```

This corroborates the firmware analysis below from the other side. The Z80 has
no bit-level code because the 166 assembles bytes for it — and, as the
instruction census further down shows, it does not handle the data bytes at all.

**There are no jumpers, strap headers, cut traces or wire-wrap anywhere on the
card.** The 9401 mode pins are therefore hardwired in the PCB artwork, which
means the CRC polynomial is identical on every TCC board. Recorded blocks and
the file-mark CRC establish it as CRC-16 polynomial `0x8005`, MSB-first, initial
value zero, no final XOR. The accumulation span is the two-byte biased length
followed by the payload; the preamble and sync byte are excluded. The CRC is
stored high byte first. This cannot be read reliably from the solder-side
photograph (no silkscreen on that side, and half of every net runs on the
component layer), but the recorded data determines it directly.

The firmware's own instruction mix is the evidence that it sits above the bit
layer:

| Measure | Count | Implication |
|---|---|---|
| total instructions | 2,092 | |
| `LDIR`/`LDDR`/`INIR`/`OTIR`/`LDI`/`INI`/`OUTI`/`CPIR` | **0** | no block-move instructions anywhere |
| shift/rotate (`sla`/`srl`/`rlc`/`rrc`/`rl`/`rr`) | **26** | software bit serialisation needs one shift *per bit* in a hot loop; 26 in 4 KB is nowhere near that |
| `exx` | 121 | alternate register bank held as state |
| `out` / `in` | 182 / 113 | a port-driven state machine |

So the Z80 never sees an unaligned bitstream, never computes a CRC, and never
searches for a sync pattern. Byte alignment is already resolved by the time data
reaches it.

**Consequence for anyone reading these tapes with modern equipment:** the
preamble, sync byte, length field and CRC are consumed by hardware and never
delivered to the host. Nothing in the S8000 — firmware or software — ever
strips them on the read side, because nothing ever receives them. They are
written by the firmware on the *write* side, which is how the format below was
recovered.

## Port map

Ports the firmware touches, by usage:

| Port | Direction | Use |
|---|---|---|
| 0x01 | out | host handshake / acknowledge strobe |
| 0x02 | in | host command register |
| 0x03 | in | a readiness condition gating several commands |
| 0x0a–0x0d | out | four result/status registers, zeroed at command entry |
| 0x0e | in/out | flag register, bit 7 cleared at command entry |
| 0x20 | in/out | primary drive control and status (69 out, 31 in) |
| 0x30 | in | drive status |
| 0x40, 0x50, 0x71, 0x74, 0x10 | out | drive/board control |

## Command reception

```
0068  in   a,(002h)      poll host command register
006a  or   a
006b  jr   z,$-3         spin until non-zero
006d  ld   a,002h
006f  out  (001h),a      handshake / acknowledge
0071  in   a,(002h)      read the command
0073  ld   c,a           C holds the command from here on
0074  in   a,(00eh)
0076  and  07fh
0078  out  (00eh),a      clear flag bit 7
007a  xor  a
007b  out  (00ah),a      zero the four result registers 0x0a-0x0d
007d  out  (00bh),a      -- these are what the host reads back afterwards
007f  out  (00ch),a
0081  out  (00dh),a
0083  in   a,(030h)
0085  and  020h
0087  jp   nz,00155h     error exit
```

It then reads port 0x20 into `B` — the drive status — and decodes `C`.

## Command table

The command register uses zero to mean that no command is pending. Nonzero
commands use low-byte opcodes **0x01–0x10** and are dispatched by a compare
chain rather than a jump table. The names and definitions below are the
manufacturer's, from Table 4-22 of 03-3198-01; the handler addresses and gate
conditions are from the ROM. Every documented command was found in the
disassembly. Opcode 0x0D is the one dispatched value absent from the manual.

| Cmd | Name | Definition | Handler | Gates first |
|---|---|---|---|---|
| `0000` | NOP | controller loops waiting for a command | — | — |
| `0n0B` | SEL | select drive *n* (0–3) | 0x086d | — |
| `0n0C` | MRTRY | set max retries *n* (0–15); default 10 | 0x0927 | — |
| `0n0F` | MODE | mode 0 = one long serpentine track; **mode 1 = four separate tracks**, each with its own logical BOT/EOT | 0x098c | — |
| `0009` | LOAD | move tape to logical load point; BOT, track 0 | 0x093a | (B&5)==1, (B&7)==3 |
| `nn04` | SKBF | skip *nn* blocks forward (0–255) | 0x04cc | + not (B&0x10) |
| `nn05` | SKBR | skip *nn* blocks reverse | 0x054e | " |
| `nn06` | SKFF | skip *nn* files forward — a file is a group of blocks followed by a file mark | 0x05de | " |
| `nn07` | SKFR | skip *nn* files reverse | 0x065e | " |
| `0n0E` | STRK | rewind and select track *n* (0–3) | 0x0902 | " |
| `0001` | **READ** | **reads one block**; backspaces and retries if necessary | 0x021d | + port 0x03 == 0 |
| `0003` | REWIND | rewind to logical beginning (6 inches past load point) | 0x0755 | " |
| `000A` | UNLD | move tape to physical load point | 0x0957 | " |
| `0002` | WRITE | write one block; on retry backspaces, erases 3 inches, retries | 0x0342 | + port 0x20 bit 6 |
| `0008` | WFM | write file mark | 0x07a2 | " |
| `000D` | *(undocumented)* | absent from Table 4-22 but present in the ROM | 0x0776 | " |
| `0010` | DIAG | self-test: ROM, FIFO, host interface ports | 0x09bc | port 0x03 == 0 |

The gate ladder recovered from the ROM matches the semantics exactly: SEL,
MRTRY and MODE are accepted in almost any state, while WRITE and WFM sit behind
every gate including the port 0x20 bit 6 test — which is the write-enable
condition. **0x0D is dispatched by the firmware but does not appear in the
manufacturer's table**, so it is either an internal or a withdrawn command.

Note the operand encoding: `nn` occupies the high byte for the skip commands
(0–255) and `n` the upper nibble for SEL, MRTRY, STRK and MODE (0–15). That is
what the apparently odd values in the SADIE bootstrap turn out to be.

The gates form a readiness ladder. `0x0b`, `0x0c` and `0x0f` are accepted in
almost any drive state — a status/reset class. `0x02`, `0x08` and `0x0d` sit
behind every gate including the port 0x20 bit 6 test, which is the shape of a
write-enable class.

Error exits at 0x139, 0x141, 0x14f and 0x155 set the result registers that were
zeroed at entry; that is what the host samples afterwards.

## The monitor's sequence, resolved

From `re/monitor/monitor30.s`, the relocated tape loader at `L_325e` (see
[`MONITOR.md`](MONITOR.md)):

```text
cmd 0003  REWIND    rewind to logical BOT
cmd 000A  UNLD      move to physical load point
cmd 000B  SEL 0     select drive 0
cmd 000F  MODE 0    one long serpentine track
cmd 000E  STRK 0    rewind, select track 0
          out (0x4e),#0            disable interrupts
cmd 0009  LOAD      move to logical load point, track 0
          in (0x4a); bit 0         status bit 0 = NOTAP, "no cartridge in drive"
          out (0x44),#0            DMA address = 0
          out (0x46),#0
          out (0x48),#0x4000       DMA length (must be < 32 KB)
cmd 0001  READ      one block
          jp 0x0000
```

A complete reset-and-position sequence, then a single block read. Since READ
transfers **one block**, the primary bootstrap has to fit in one block — which
is why the *ZEUS System Administrator's Manual* describes tape file 0 as "a 512
byte program".

The SADIE primary bootstrap recovered from tape uses the operand encoding:

```text
cmd 0x10F  MODE 1   four separate tracks
cmd 0x00E  STRK 0   rewind, select track 0
           out (0x4e),#0
cmd 0x106  SKFF 1   skip one file forward
           out (0x44/46/48)        address 0, length 0x4000
cmd 0x001  READ     one block
           in (0x4a); bit 1        status bit 1 = FMDET, "file mark detected"
           loop back to READ while FMDET is clear
           jp 0x0000
```

So it switches to four-track mode, selects track 0, steps over its own file, and
then reads blocks until it hits a file mark — loading the whole of the next tape
file into memory at address 0 before entering it. The DMA address is programmed
once, so the controller advances it across successive blocks.

Both end on READ, and both jump to address 0. That identifies **0x021d as the
read handler**.

## Inside command 1

```text
021d  in a,(020h); and 080h; jp nz,014f     reject on drive bit 7
0224  ld ix,022bh; jp 0c50h                 fetch and validate DMA parameters
0237  ld a,0feh; out (020h),a               drive control
024a  ld bc,003fbh / ld h,0a7h / ld de,0244h    timeout counters
025a  in a,(030h); and 010h                 poll a hardware status bit
0260  dec l; jr nz                          36 retries, else error code 0x27
0271  dec bc ... jr nz                      long timeout
0276  ld ix,027dh; jp 0c08h                 post-transfer
027e  ld sp,hl                              SP holds the DMA address
027f  ld iy,0; add iy,bc                    IY holds the count
```

The calling convention throughout is `ld ix,<addr>` then `jp <routine>`, with
the routine returning by jumping through IX. The major services are at 0x0bfa,
0x0c08 and 0x0c50.

**0x0c50 — DMA parameter fetch and validation.** This is where the host's
registers arrive on the Z80 side:

```text
0c51  in a,(009h) / in a,(008h)   BC = DMA length, from host 48H
0c57  ld hl,08000h; sbc hl,bc
0c5d  jr c,error                  length must be < 32 KB
0c68  in a,(004h) / in a,(005h)   HL = DMA address low word, from host 44H
0c6e  in a,(007h); out (050h),a   high address byte, from host 46H
0c72  bit 0,l; jr nz,error        address must be word aligned
0c86  ld sp,hl                    park the address
0c89  ld iy,0; add iy,bc          park the count
```

Both checks are exactly the constraints Table 4-19 documents for `44H` and
`48H`. This also fixes the Z80-side port map: **0x04/0x05 and 0x07 mirror the
host's DMA address, 0x08/0x09 mirror the DMA length.**

**0x017f — post-transfer accounting.** It computes a residual and reports it:

```text
018f  sbc hl,bc                   residual = programmed length - transferred
0193  out (009h),a / out (008h),a  write it back to the length ports
019b  ...retry arithmetic...
01a7  out (00ch),a                -> host 4CH bits 0-3, "number of retries"
```

### The firmware does not move data

This is worth stating explicitly because it is easy to assume otherwise, and it
constrains what the on-media format can require of software. A census of the
whole 4 KB:

| Check | Count |
|---|---|
| memory-write instructions (`ld (hl),`, `(de),`, `(ix+d),`, `(iy+d),`) | **1** |
| `push` / `pop` | 0 |
| `ldir` / `ldi` / `inir` / `ini` / `otir` / `outi` | 0 |
| `im 0` / `im 1` / `im 2` | **0** |
| `ei`, `di`, `reti`, `retn` | **0** |

No interrupt mode is ever set and interrupts are never enabled, so there is no
service routine either. The 121 `exx` instructions are register pressure, not an
ISR technique — the firmware is using both banks plus SP, IX, IY and even the
`I` register (`ld i,a` / `ld a,i`) as scratch storage. `ld sp,hl` is a parking
space for a 16-bit value, not a data pointer.

So the Z80 validates parameters, programs the hardware, polls status, and does
arithmetic on counts. **Every data byte moves between the FIFOs and host memory
without the CPU touching it.**

## How a transfer terminates

READ is documented as reading **one block**, and the firmware has no counting
loop, so the transfer is ended by a hardware condition rather than by software.

The DMA length is a **bound, not a required record size**. Let `R` be the
payload length recorded on tape and `N` the DMA length supplied by the host:

| Condition | Bytes DMA'd and returned | Tape position afterwards |
|---|---:|---|
| `R < N` | `R` | next record |
| `R = N` | `N` | next record |
| `R > N` | `N` | next record; the remaining `R-N` bytes are skipped |

This is not merely inferred from the residual arithmetic. The recovered
ZEUS `ct(4)` page states that the record size is returned when it fits, and
that if the record is longer than the user's buffer, "the extra data is
skipped over without notification." Thus a record longer than the DMA bound
is a **successful, silently truncated read**, not `BPARM`.

`BPARM`, "bad DMA parameters," instead covers an invalid request. The firmware
at 0x0c50 rejects a DMA count outside its permitted range and an odd DMA
address; the ZEUS driver additionally requires an even read-buffer length.
An odd-length record is nevertheless valid: if it is shorter than an even
buffer, `read(2)` returns the actual odd length.

After the transfer, 0x017f writes the unused DMA count back to the length
registers. The ZEUS driver's interrupt routine reads that value into the
buffer residual, and the ordinary `physio` path returns:

```text
bytes read = requested DMA length - residual = min(R, N)
```

Consequently there are two hardware termination cases. End-of-record can stop
DMA early, leaving a nonzero residual; exhaustion of the DMA allowance stops
delivery to memory, while the controller still consumes the rest of the
physical record so that the next READ starts at the next record.

This is why the monitor requests `0x4000` and receives a single block, and why
the SADIE bootstrap must *loop* READ until `FMDET` appears in status: one
command yields one block, so reading a whole tape file means issuing READ
repeatedly until the file mark is reported.

Note the distinction: each READ is terminated by **the end of a block**; the
file mark is a separate condition reported in status bit 1, indicating the end
of a *file*. There is no byte length stored for a tape file. A tape file is a
sequence of independently sized records followed by a file mark, and a raw
device read of that mark returns zero bytes.

## How a tape file is selected

There is **no file number in the controller-level tape format**. A file number
is only the zero-based ordinal position of a group of records between file
marks:

```text
logical BOT
    records belonging to file 0
    FILE MARK
    records belonging to file 1
    FILE MARK
    records belonging to file 2
    FILE MARK
    ...
```

Selecting file *n* therefore means establishing a known position—normally by
rewinding to logical BOT—and counting *n* file marks. `SKFF nn` searches
forward and `SKFR nn` searches in reverse; `nn` is the high byte of the command
word, giving a per-command count of 0–255. The controller recognizes file marks
while the tape moves, decrements the requested count for each mark, and leaves
the tape positioned at the beginning of the selected file. ZEUS exposes these
commands as `CTIOFF` and `CTIOFR`.

For example, the SADIE primary bootstrap begins in file 0 and issues `SKFF 1`.
That skips the mark terminating file 0 and positions the tape at the first
record of file 1. A stand-alone name such as `ct(0,3)` consequently means
"position to the fourth tape file, whose ordinal is 3," not "find a header
containing file number 3."

Status register 1 reports the number of files actually skipped by the most
recent command. It is a command result, not a persistent current-file-number
register. Record seeking works the same way: `CTIOSB` takes a record ordinal
relative to the beginning of the current file and reaches it by block skips;
record numbers are not present in the controller's record header either.

In mode 1, which treats the four tracks as separate logical tapes, file
ordinals are relative to the selected track's logical BOT. In mode 0 they are
relative to the continuous serpentine logical path. Higher-level payloads may
of course contain their own sequence numbers—for example, a filesystem dump
format can number its records—but those numbers are data as far as the tape
controller is concerned.

The `WFM` handler establishes the bytes used to identify a file mark. It writes
the ordinary four-byte preamble and sync byte followed by an encoded length of
one:

```text
00 00 00 00   preamble
01            sync
00 01         encoded length = 1
```

Because an ordinary data record stores `payload length + 1`, this is the
reserved zero-payload record. The read-side TTL sequencer can recognize the
normal preamble and sync, decode length one as a file mark rather than starting
payload DMA, and assert `FMDET`. `SKFF` and `SKFR` count occurrences of that
condition. The file mark carries the ordinary CRC over its length field. With
no payload, `CRC(00 01) = 0x8005`, so its complete header and CRC are:

```text
00 00 00 00 01 00 01 80 05
```

What remains uncertain is the exact electrical interpretation of the
post-record/gap sequence that follows it.

## What this settles about reading these tapes

- **The monitor reads no header of any kind.** It supplies the DMA address and
  length itself, issues command 1, and jumps to address 0. There is no magic
  number, load address, entry point, length field or checksum anywhere in the
  boot path.
- **So the first byte the controller delivers is the first byte executed.** For
  a tape's boot file, anything appearing before the first instruction in a
  decoded stream is framing that the original hardware consumed.
- **Nothing in software parses the media format.** The firmware census above
  rules out any software involvement in sync detection, header parsing or CRC
  checking. Whatever structure exists between blocks is handled entirely by the
  TTL sequencer and the two 9401s.
- **Block size is not fixed at the driver level.** `ct(4)` states that "the tape
  blocks can be any size." Each raw `read(2)` consumes one physical record and
  returns `min(record length, buffer length)`; if the buffer is too short, the
  rest of that record is discarded without an error.

## Confirmation from recovered media

The recovered SADIE 3.5 tracks and ZEUS 3.21 installation tape independently
confirm the controller-level format. Their recovery archives store each record
as payload followed by its two-byte CRC; the preamble, sync byte and biased
length have already been removed. Reconstructing the biased length from the
stored record size makes the CRC residue zero for every complete SADIE record
and every installation record except the one known damaged capture.

| Media | Logical files | Data records | Payload sizes | File marks | CRC result |
|---|---:|---:|---|---:|---|
| SADIE track 0 | 4 | 46 | 1,024 and 8,000 bytes | 4 | all valid |
| SADIE track 1 | 37 | 666 | 1,024 bytes | 37 | all valid |
| SADIE track 2 | 21 | 22 | 1,000, 1,300 and 4,000 bytes | 21 | all valid |
| ZEUS install | 18 | 1,279 | 512 and 10,240 bytes | 18 | file 8/block 169 damaged; all others valid |

The first installation file is one 512-byte record, exactly matching the
documented monitor bootstrap. SADIE supplies particularly clear evidence that
record length is not fixed: even within one cartridge it uses several sizes,
all validated by the same length-prefixed CRC calculation. Every file-mark
member contains only `80 05`, which is the CRC of biased length `00 01` with no
payload.

SADIE uses controller mode 1. Its extended SIMH image uses private markers
`0x70000000` through `0x70000002` to identify tracks 0 through 2. This is an
S8000-specific convention: the upper nibble selects SIMH's private-marker class
and the lower 28-bit marker value is the track number. File ordinals restart at
logical BOT on every track.

## Host interface registers

Confirmed against Table 4-19 of 03-3198-01, which matches what the ROM and the
monitor behaviour implied:

| Address | Register | Notes |
|---|---|---|
| `40H` | interrupt vector (low byte) / **status (high byte)** | the host polls **BUSY** here before issuing a command — this is the `bit 9` the monitor tests |
| `42H` | **command** | "the controller accepts only valid commands" |
| `44H` | low DMA start address | bit 0 must be 0, word aligned |
| `46H` | high DMA start address | bits 16–23 |
| `48H` | **DMA length** | must be less than 32 KB; the monitor uses 0x4000 |
| `4AH` | **status** | bit 0 NOTAP, 1 FMDET, 2 HWERR, 3 INVAL, 4 INAP, 6 BPARM, 7 BLKTAP, 8 PROT, 9 LBOT, 10 LEOT, 11 RTRYAT, 12–13 unit, 14–15 track |
| `4CH` | status 1 | bits 0–3 retries, bits 8–15 blocks or files skipped |
| `4EH` | interrupt control | the monitor writes 0 to disable |

## Drive and media parameters

From Table 2-4 of 03-3198-01:

| Item | Value |
|---|---|
| Read/write speed | 30 ips |
| Rewind/search speed | 90 ips |
| Tracks | 4 |
| Recording density | 6400 BPI |

6400 BPI at 30 ips is **192,000 bits/s**, i.e. a bit cell of about 5.2 µs.

## The on-media block header

The WRITE handler emits the block framing byte by byte, so the format is read
directly out of the firmware rather than inferred. **Port 0x40 writes into the
serial data path** — it is written 19 times in the ROM and never read. Whether
a particular value reaches tape is gated by the current port-0x20 control
state; some writes prime or control the path rather than appearing literally
in the captured stream.

From `cmd_WRITE` at 0x0342, immediately after the DMA parameters have been
fetched and validated by 0x0c50:

```text
0368  ld b,004h
036a  xor a
036b  out (040h),a       write 0x00 ...
036d  djnz $-2           ... four times            -> PREAMBLE
036f  ld a,001h
0371  out (040h),a       write 0x01                -> SYNC BYTE
0373  exx
0374  inc bc             BC = DMA length + 1
0375  ld a,b
0376  out (040h),a       high byte                 -> LENGTH, big-endian
0378  ld a,c
0379  out (040h),a       low byte
037b  dec bc
037c  exx
```

So every block begins:

```text
00 00 00 00   preamble, four zero bytes
01            sync byte
hh ll         (DMA transfer length + 1), big-endian
<data>        the payload, DMA'd from host memory
```

This accounts for the observed capture exactly:

```text
00 00 00 00 01 1F 41 21 00 40 00 ...
~~~~~~~~~~~ ~~ ~~~~~ ~~~~~~~~~~~~~~
preamble    |  length  payload begins here
            sync
```

`0x1F41` = 8001, so that block carries **8000 bytes** of data — comfortably
inside the `< 0x8000` bound that 0x0c50 enforces on the host's DMA length.

### File marks are the zero-payload length code

The distinct `WFM` handler at 0x07a2 writes the same preamble and sync followed
by the literal length value `0x0001`:

```text
07c8  ld b,004h
07ca  xor a
07cb  out (040h),a       write 0x00 four times       -> PREAMBLE
07cd  djnz $-2
07cf  ld a,001h
07d1  out (040h),a       write 0x01                  -> SYNC BYTE
07d3  xor a
07d4  out (040h),a       write 0x00                  -> LENGTH high
07d6  inc a
07d7  out (040h),a       write 0x01                  -> LENGTH low
```

Thus the programmed file-mark bytes are:

```text
00 00 00 00 01 00 01
```

Normal records encode `payload length + 1`, so length code one means a payload
length of zero. It is the reserved file-mark sentinel. This gives the hardware
a direct recognition rule: after finding the normal sync, `length == 1` means
assert `FMDET` and perform no payload DMA. The skip-file commands count those
detected sentinels; no file number is stored with them.

### CRC span and parameters

The bytes immediately following an observed file-mark length are `80 05`.
They are its two-byte CRC, not part of the gap:

```text
CRC-16 polynomial  0x8005
bit order          MSB-first
initial value      0x0000
final XOR          0x0000
covered bytes      encoded length || payload
stored order       big-endian
```

For the zero-payload file mark:

```text
CRC(00 01)         = 80 05
CRC(00 01 80 05)   = 00 00       zero residue
```

This also resolves the apparent `xorout=0xC00C` obtained earlier by checking
only the 4096-byte payloads in the recovered dump. Those records have biased
length `0x1001`, and for that fixed payload length the omitted `10 01` prefix
has exactly the same effect as XORing the payload-only result with `0xC00C`:

```text
CRC(10 01 || payload, init=0) = CRC(payload, init=0) XOR 0xC00C
```

The underlying format therefore uses no final XOR; the apparent constant was
the effect of leaving the length field out of the calculation.

### What follows the file-mark CRC

An observed file mark continues:

```text
01 00 01 80 05 80 00 00 ...
~~ ~~~~~ ~~~~~ ~~~~~~~~~~~~~
|  length CRC   post-record sequence begins
sync
```

The `WFM` firmware contains the exact continuation. On the branch matching
this capture it changes the port-0x20 control state, then writes `0x80`, four
zero values and `0x0F` through port 0x40:

```text
0803  out (074h),a
0805  ld a,0aeh
0807  out (020h),a
0809  out (040h),a       prime the data path while in this control state
080b  or 040h            A = 0xee
080d  out (020h),a       change the write-control state
080f  ld a,080h
0811  out (040h),a       0x80
0813  ld b,004h
0815  xor a
0816  out (040h),a       0x00 four times
0818  djnz $-2
081a  ld a,00fh
081c  out (040h),a       0x0f
```

Thus the capture predicts the complete visible continuation:

```text
80 00 00 00 00 0F
```

This is a post-record/inter-record-gap generation sequence, but the ROM alone
does not establish the electrical meaning of each value. In particular,
`0xAE` is written to port 0x40 while port 0x20 is in a different state and does
not appear in the capture. Port 0x20 therefore gates or changes the meaning of
port-0x40 writes; it is unsafe to assume that every `out (040h),a` becomes a
literal byte on tape.

The ordinary data-WRITE handler has a related but distinct conditional branch.
After writing `0x80`, it performs either 64 or 128 readiness-gated writes of
zero and finally writes `0x0F`. The choice made by the ROM is:

| Programmed data length | Zero writes in this branch |
|---:|---:|
| less than 128 bytes | 128 |
| 128 bytes or more | 64 |

That is an exact count of port-0x40 output operations, **not yet proof of 64 or
128 literal zero bytes on the medium**. The branch is conditional and the
surrounding port-0x20 state controls the data path. It must be checked against a
capture or the TTL schematic before being described as an on-media gap length.

Two consequences worth stating:

- **The header supplies the physical record length.** The discrete sequencer
  can use it both to stop a short DMA at end-of-record and to consume the tail
  of a record longer than the host's DMA allowance. No software counting is
  involved — which is what the firmware census (above) requires, since the Z80
  cannot count bytes it never sees.
- **It also explains why the header never reaches the host.** It is generated on
  the write side by the controller and consumed on the read side by the
  sequencer; it is framing, not payload. That is why the monitor can DMA a block
  to address 0 and jump straight to address 0.

The `+1` is therefore a **biased length representation** that reserves code one
for the zero-payload file mark. It may simultaneously suit the terminal-count
behavior of the four 74LS193s—for example, by counting through zero or including
one non-payload state—but the ROM alone does not establish the individual
counter clocks or terminal-count polarity.

The CRC placement, span and parameters are now settled. What remains open is
how the port-0x20 control state gates the post-record writes, how those values
map electrically onto `WDE`/`WNZ`/`WDS`, and whether the four-zero WFM tail has
distinct gap timing beyond the bytes visible in the capture.

## Inferences, flagged

Most of what was previously inferred here is now confirmed by 03-3198-01 — the
register map, the command names and operand encodings, and the status bits the
monitor tests. What remains open:

- The mapping from the Z8000-side port 0x42 to the Z80-side port 0x02 is still
  inferred from behaviour rather than a schematic, though the manual's register
  table makes the correspondence unambiguous in function.
- **Command 0x0D is dispatched at 0x0776 but is absent from Table 4-22.** Its
  purpose is unknown; it sits behind the write-enable gate.
- The on-media block layout is **not** documented in 03-3198-01, which specifies
  the host interface only. The preamble, sync byte and length field recorded
  above were recovered from the WRITE handler in the firmware. The CRC
  parameters and span were recovered from recorded data and the file-mark
  sentinel.
- The exact TTL path that loads and clocks the four 74LS193 record-length
  counters has not been traced from a schematic. Their use of the header length
  on READ is established by the observable record semantics and firmware
  architecture, but the individual counter clocks and terminal-count polarity
  remain to be recovered.
- The firmware establishes the programmed file-mark bytes as
  `00 00 00 00 01 00 01`, a normal header with biased length one and no
  payload. Its CRC is `0x8005`, covering the length `00 01`. The subsequent
  `80 00 00` prefix is matched between ROM and capture, and the ROM predicts
  the complete `80 00 00 00 00 0F` sequence; its precise TTL gating and
  physical gap interpretation remain unknown.

## Sources

- *System 8000 Hardware Reference Manual*, 03-3198-01, Mar 1982 — §4.5.3–4.5.4,
  Tables 4-19, 4-22, 4-23, 4-25, 4-26, and Table 2-4.
  <https://bitsavers.org/pdf/zilog/s8000/03-3198-01_System_8000_Hardware_Reference_Manual_Mar1982.pdf>
- `tcc_34-0607-01a.u97`, `tcc_34-0608-01a.u96` from the MAME `s8000` ROM set.
- Board photographs, component and solder side:
  <https://bitsavers.org/pdf/zilog/s8000/s8000_sys_w_fpu/Zilog_Cartridge_Tape_Controller/>
- [`MONITOR.md`](MONITOR.md) — the CPU monitor side, including the tape loader
  at `L_325e` and the `ZBOOT` dispatch.
- [`STANDALONE.md`](STANDALONE.md) — the bootstrap chain these commands serve.
- `ct(4)` in the recovered `/usr/man/man4` — the ZEUS-side device semantics,
  record lengths, tape marks, and the four-track minor-number encoding.
- Recovered SADIE 3.5 track archives and ZEUS 3.21 installation media linked
  from the [VCFed System 8000 recovery thread](https://forum.vcfed.org/index.php?threads/zilog-system-8000-model-21.1255068/page-4),
  preserved and converted reproducibly under [`tapes/`](tapes/README.md).
