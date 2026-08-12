# The System 8000 CPU monitor: commands, boot, and serial download

This describes the firmware monitor in the System 8000 boot EPROMs — its
command set, what it can boot from, and the serial **Download Mode** that loads
and runs a program sent from another machine.

Two monitors are covered:

| Monitor | Board | ROMs |
|---|---|---|
| 3.0 | CPU-A (Model 11/21/31) | `cpu_34-0715-03a.u76`, `-0716-03a.u74`, `-0717-03a.u75`, `-0718-03a.u77` |
| 10.1 | HPCPU (Series Two) | `hpcpu_34-1117-00_v10.1_common.19e`, `hpcpu_34-1119-00_v10.1_16user.21e` |

Every claim below is stated from one of two places: the *System 8000 Hardware
Reference Manual*, 03-3237-04 (Dec 82), section 5.9; or the annotated Monitor
3.0 disassembly in `monitor/`, cited by image address. Where the two disagree,
that is noted — the manual predates both ROMs.

## Command set

Manual §5.9.3 lists the Monitor Mode commands. They are exactly the fifteen
letters in Monitor 3.0's dispatch table at `monitor30.s` `0x01b2`, in the same
order:

| Letter | Name | Parameters | Handler |
|---|---|---|---|
| `B` | BREAK | `[<address>] [<n>]` — set and clear breakpoint | `0x0c3e` |
| `C` | COMPARE | `<address1> <address2>` — compare memory blocks | `0x033e` |
| `D` | DISPLAY | `<address> [<count>] [L\|W\|B]` — display and alter memory | `0x03b2` |
| `F` | FILL | `<address1> <address2> <data>` | `0x02f4` |
| `G` | GO | branch to the last PC in the user register array | `0x0b54` |
| `I` | IOPORT | `<port address> [W\|B]` — I/O port read/write | `0x06d4` |
| `J` | JUMP | `<address>` | `0x0b42` |
| `L` | LOAD | `<filename>` — enters Download Mode; see below | `0x0dc2` |
| `M` | MOVE | `<address1> - <address2>` — move memory block | `0x0316` |
| `N` | NEXT | `[<m>]` — step instruction | `0x0bc6` |
| `T` | TEST | enter Test Mode | `0x148e` |
| `Q` | QUIT | enter Transparent Mode | `0x0bf8` |
| `R` | REGISTER | `[<register name>]` — display and alter registers | `0x07a6` |
| `Z` | ZBOOT | `[D\|S\|T]` — read and execute a bootstrap program | `0x1294` |
| `P` | PORT | `<port address> [W\|B]` — special I/O read/write | `0x06de` |

Output in Monitor Mode suspends with XOFF (control-S) and resumes with XON
(control-Q).

Monitor 10.1 has seventeen letters — `B C D E F G I J L M N P Q R S T Z`, held
alphabetically rather than in dispatch order. `E` and `S` are new and are not
documented in the Dec 82 manual; nothing in 10.1's string table suggests either
is boot-related. They have not been disassembled.

## Booting: local storage only

`ZBOOT` is the only automatic boot path, and it reaches local mass storage
only. There is **no serial or network boot device**. Three independent sources
agree:

- The manual documents `ZBOOT [D|S|T]`.
- `cmd_Z` at `0x1294` dispatches on `D` (0x44), `T` (0x54), `S` (0x53) and `M`.
  Monitor 3.0 therefore adds `M`, mini-winchester, which the Dec 82 manual does
  not list. Both ROMs carry exactly four `BOOTING FROM …` messages and
  controller-error strings for those four (`WDC`, `TCC`, `SMC`, `MDC`).
- The primary boot device is selected by two bits of switch U70. *CPU Hardware
  Reference Manual* 03-3200-01, Table 2-9, gives the four settings as 8-inch
  disk, 5¼-inch disk, SMD disk, and **Reserved**. Two bits, four devices, no
  spare encoding for a serial source.

Having selected a device, the monitor prompts for the name of a secondary
bootstrapper to read and execute. The ROM holds the default at `0x3214` as the
string `stand/boot`, with a second label at `0x321a` pointing at just `boot`,
so either form can be referenced.

## Transparent Mode (`Q`)

From manual §5.9.3:

> In Transparent Mode, all keyboard inputs and console outputs are passed
> between the remote computer system and the local system. The console controls
> the remote computer system operating system. […] The START switch on the
> System 8000 is used to return to Monitor Mode.

So the console becomes a terminal onto the remote host. The intended workflow
is `Q` to log in and stage a file, START to come back, then `L` to fetch it.

## Download Mode (`L <filename>`)

This is the serial load mechanism. It is not a boot device, but `L` followed by
`G` or `J` downloads an arbitrary Z8000 image over a serial line and runs it,
which is remote boot in practice.

### The port

The remote system connects to **TTY0 on the rear panel** — SIO 0 channel A,
data `0xff81`, control `0xff85`. This is *not* the console, which is SIO 0
channel B at `0xff83`/`0xff87`. The I/O map in 03-3200-01 names `0xff81` as
"SIO 0, channel 0, data".

The manual requires both channels to run at the same baud rate. The ROM
enforces this structurally: reset derives one CTC time constant from the U70
baud switches and programs both channels from it (`0x0080`–`0x00c2`).

Channel A is interrupt-driven and has its own receive ring, entirely separate
from the console driver: the handler at `0x1090` fills a ring at `0x42b0` with
head and tail at `0x43a6`/`0x43a8`; `L_11aa` and `L_1200` read it; `L_0cae`
polls `0xff85` for transmit-ready and writes `0xff81`.

### The remote side

A procedure file named `LOAD` must exist on the remote system. `cmd_L`
transmits the command line verbatim over channel A (`L_112c`), which invokes
that procedure; it opens the named file, converts the binary to Tektronix
records, and streams them back. Filenames may be upper or lower case and may be
full path names. Error messages carry ZEUS error codes, so the far end was
expected to be another ZEUS machine.

### Record format

Tektronix hex, ASCII only, at most 30 data bytes per record, with two
checksums — one over the address and count fields, one over the data:

```text
data record:  <address(4)> <count(2)> <checksum1(2)> <data(2)> … <checksum2(2)> <CR>
last record:  <entry address(4)> 00 <checksum(4)> <CR>
error record: / <message in ASCII text> <CR>
```

A count field of `00` marks the end of the load data; that record carries the
program's entry address, which the monitor displays as `ENTRY POINT <addr>`
when the transfer completes.

No segment information is transferred. Everything lands in segment 0; use
`MOVE` to place data in another segment. The load address must be greater than
`0x8000` — `cmd_L` rejects anything lower (`cp r4,#0x8000` at `0x0e54`) with
`/INCORRECT LOAD ADDRESS`.

### Handshake

| Meaning | Byte | ROM |
|---|---|---|
| Acknowledge — checksums verified | ASCII `0` | `L_111a` |
| Non-acknowledge — retransmit, up to ten times | ASCII `7` | `L_1112` |
| Abort-acknowledge — ESC pressed | ASCII `9` | `L_1116` |

After ten failed retries the monitor sends an error record and returns to
Monitor Mode, and the remote `LOAD` program is aborted too. Pressing ESC aborts
from the local end. Any breakpoints from a previous program must be cleared
before loading a new one.

Records are `/`-framed on the wire: `L_10de` discards input until it sees `/`
(0x2f), then buffers to CR.

### Error messages

The manual documents, for the Dec 82 firmware:

```text
/ABORT
/UNABLE TO OPEN FILE (XX)      XX = ZEUS error code from the remote system
/FILENAME ERROR
/NOT PROCEDURE FILE
/ERROR IN READING FILE (XX)
/RECORD CHECKSUM ERROR
/INCORRECT LOAD ADDRESS
```

Monitor 3.0's ROM carries a shorter set — `/INCORRECT LOAD ADDRESS`,
`/CKSUM ERROR`, `/FILE WRITE ERROR`, `/OPEN FILE ERROR`, `/ABORT` — and 10.1
spells the second as `/CHECKSUM ERROR`. The wording drifted between the manual
and the shipped ROMs. Note that `/FILE WRITE ERROR` implies the monitor can ask
the host to *write* a file, a direction the Dec 82 edition does not document.

## Using it under emulation

MAME exposes the download port as `:slot_cpu:cpu_a:sio0:cha:tty0`, so the
transport is already available; `s8000.cfg` in this repository configures its
baud rate alongside the console's.

What does not exist is the host side. The `LOAD` procedure file was a ZEUS
program on the remote machine and is not part of any recovered tree here.
Writing a replacement is small — the record format, checksums and three
handshake bytes above are the whole protocol — but until one exists, `L` has
nothing to talk to.

## Sources

- *System 8000 Hardware Reference Manual*, 03-3237-04, Dec 82, §5.9 —
  <https://bitsavers.org/pdf/zilog/s8000/03-3237-04_hwRef_Dec82.pdf>.
  The scan has no text layer; it was read by rendering with `pdftoppm` and
  running `tesseract`. Manual page 5-37 is PDF page 200.
- *System 8000 CPU Hardware Reference Manual*, 03-3200-01, Sep 82 — I/O map
  and Table 2-9, the U70 baud-rate and primary-boot-device switch.
- *ZEUS System Administrator's Manual*, 03-3246-04, §2.4 — the operator-facing
  boot procedure (`ZBOOT D`, `ZBOOT S`, `ZBOOT T`) and the secondary
  bootstrapper's `:xxx(n,m)name` syntax.
- `monitor/` — the annotated, reassemblable Monitor 3.0 disassembly. All ROM
  addresses cited here are image offsets in `monitor/monitor30.s`.

See also [`STANDALONE.md`](STANDALONE.md) for the layer above the monitor — the
bootstrap chain, stand-alone device addressing, and the monitor system calls
(including the two that expose the download port) that stand-alone programs
use — and [`TCC.md`](TCC.md) for the layer below, where the tape commands this
monitor issues are decoded and executed by the controller's own Z80 firmware.
