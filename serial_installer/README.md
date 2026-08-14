# ZEUS installation tape over serial

This directory preserves the installation tape's bootstrap and standalone
flow while replacing cartridge-tape reads with TTY0 serial reads. The original
SIMH tape is never modified.

The executed chain is:

```text
monitor L/J stage at 0xf000
  -> patched tape file 0 loaded directly at address 0
  -> file 0 relocates its working body to 0xf800
  -> patched tape file 1 loaded directly at address 0
  -> original secondary-loader MMU/PSAP setup
  -> ct(0,2), ct(0,3), ct(0,4), ...
```

This matches the recovered tape path. The ROM tape routine normally DMA-loads
file 0 at zero and jumps there. Original file 0 relocates from `0x001a` to
`0xf800`, loads file 1 at zero, and jumps there. The serial versions retain
those addresses and handoffs; file 1 is never staged at `0x8000`.

The monitor's `J` command does not provide the same register environment as
its `ZT` path. On CPU-A, the real relocated tape routine enters with `r4=1`,
`r5=0x10`, and passes the jumper configuration in `r7`. File 1 consumes these
values during RAM/MMU sizing. The monitor-loaded serial stage therefore
recreates `r4/r5` and preserves `r7`; file 0 preserves all three exactly as the
original file 0 does.

Both file 1 and file 4 need their own patched `ct.o`:

- file 1 uses it to load standalone programs such as `sawbz`, `mkfs`, and
  `sarestor`;
- after file 4 starts, its separately patched copy reads dump files 5–8.

`serve_tape.py` therefore substitutes the built file 0, file 1, and file 4
while serving every other logical file from the unmodified tape image.

## Build and host-side tests

```sh
cd serial_installer
make
```

`make` is the normal build command. To run the Python integrity and protocol
tests as well, use `make test`. These tests run entirely on the host computer;
they do not communicate with a System 8000.

Outputs are:

- `build/bootstrap.bin`: monitor-loaded serial equivalent of the ROM's tape
  stage;
- `build/primary-serial.bin`: patched 512-byte file-0 program (zero padded by
  the server);
- `build/loader-serial.bin`: repaired file 1 with its 700-byte `ct.o` replaced;
- `build/sarestor-serial.bin`: file 4 with only its 700-byte `ct.o` replaced.

The current CRC-16/XMODEM replacement is 526 bytes, leaving 174 bytes of the
original 700-byte `ct.o` region unused. It preserves every fixed entry used by
the unchanged standalone device switches:

| Entry | Relative offset | File-4 address |
|---|---:|---:|
| open | `0x00` | `0x2de6` |
| close | `0x62` | `0x2e48` |
| strategy | `0x76` | `0x2e5c` |
| ioctl/command | `0x9c` | `0x2e82` |

The Makefile takes `tapes/images/zeus-3.21-install.tap` directly as its only
tape input. It parses logical files 1 and 4 in memory; it does not build from
the extracted-file tree. The patchers hash-check those logical files. Tests
verify that files 1 and 4 change only inside their respective `ct.o` regions.
They also check all four entry offsets, XMODEM packet construction and retry,
duplicate read requests, fragmented host input, and the file-5-to-file-6 space
operation used by `sarestor`. A generated-code check verifies that the bounded
UART polling loop is present and that version-3 XMODEM has no artificial
default byte delay.

### File 1 recovery and its RAM probe

The recovered physical-tape archive omitted one complete 512-byte record from
file 1 at image offset `0x3200`. `tapes/build_tape_images.py` restores the exact
record from the independent `/usr/boot` executable in `S8000-2.tar` and checks
that the resulting 23,040-byte padded tape file matches its loadable image.
This also restores the original nonzero RAM-probe word `0xc55c` at address
`0x38bc`; `patch_loader.py` does not modify that word.

## Original hardware

The Python server accepts a physical serial device as its second positional
argument. Install its serial-port dependency and build the patched tape
programs first:

```sh
python3 -m pip install pyserial
cd /Users/paxia/Projects/Zilog_S8000/serial_installer
make
```

Connect the host computer to rear-panel **TTY0** (SIO 0 channel A), not to the
System 8000 console. The console remains available for entering monitor and
installer commands; TTY0 carries only the monitor download and binary tape
protocol. Configure the connection as 9600 baud, 8 data bits, no parity, and
2 stop bits, with hardware and software flow control disabled.

Start the server, replacing `/dev/ttyUSB0` with the host's serial-device path:

```sh
cd /Users/paxia/Projects/Zilog_S8000/serial_installer
python3 serve_tape.py ../tapes/images/zeus-3.21-install.tap /dev/ttyUSB0 \
  -v
```

That is the complete normal command. The server automatically uses
`build/bootstrap.bin`, `build/primary-serial.bin`,
`build/loader-serial.bin`, and `build/sarestor-serial.bin` from this folder.
The corresponding long options exist only to override those defaults while
developing or diagnosing a different build.

Use `--baud` if TTY0 is configured for another rate, for example:

```sh
python3 serve_tape.py ../tapes/images/zeus-3.21-install.tap /dev/tty.usbserial-1234 \
  --baud 4800 -v
```

Then use the separate System 8000 console:

1. Enter `L SERIAL` at the monitor prompt.
2. Wait until the host reports `bootstrap loaded; enter J F000 (or G)` and the
   monitor has returned to its prompt.
3. Enter `J F000` (or `G`, using LOAD's saved entry point).
4. At the secondary loader's `Boot:` prompt, follow the release-tape sequence
   below, beginning with `ct(0,2)`.

Do not enter `J F000` until the monitor has printed its prompt and TTY0 output
has drained. The bootstrap takes direct ownership of that SIO channel.

### Non-destructive real-hardware smoke test

There is no automated real-hardware test yet. After starting the server, the
manual transport test is:

1. Enter `L SERIAL` on the System 8000 console.
2. Wait for the server to report that the monitor bootstrap has loaded.
3. Enter `J F000` and verify that verbose server output reports complete
   transfers for logical files 0 and 1.
4. Verify that the secondary loader displays its `Boot:` prompt.
5. Enter `ct(0,2)`, verify that the disk-format information program loads and
   displays its text, then press RETURN and verify that `Boot:` returns.

This stops before any disk write. Do not enter `ct(0,3)` during a smoke test:
file 3 is stand-alone `mkfs`, and the installation procedure deliberately
destroys and recreates filesystems.

The physical serial-device path is implemented but has not yet been exercised
on original System 8000 hardware. The socket-backed MAME path is the currently
verified transport test. `make test` verifies tape parsing, input hashes,
patch boundaries, packet encoding, and short serial writes, but is not a
substitute for the manual hardware sequence above.

## Exact visible MAME installer smoke-test launch

Use these commands exactly. Start the tape server first and leave it running;
then start MAME from a second terminal. The MAME window is the operator console.

Build and test the serial images:

```sh
cd /Users/paxia/Projects/Zilog_S8000/serial_installer
make test
```

Create a separate blank 128 MiB SMD disk for the installer. This does not
modify either of the existing installed-system images:

```sh
chdman createhd \
  -o /private/tmp/s8000-install-blank-128.chd \
  --chs 1024,8,32 --sectorsize 512 -c none
```

Terminal 1:

```sh
cd /Users/paxia/Projects/Zilog_S8000/serial_installer
python3 serve_tape.py ../tapes/images/zeus-3.21-install.tap \
  --listen 127.0.0.1:8148 -v
```

Terminal 2:

```sh
cd /Users/paxia/Projects/mame_latest/mame
./s8000 s8000 -rp roms \
  -cfg_directory /Users/paxia/Projects/Zilog_S8000/serial_installer/mame_cfg \
  -slot_cpu:cpu_a:sio0:cha:tty0 null_modem \
  -slot_cpu:cpu_a:sio0:chb:console terminal \
  -bitb socket.127.0.0.1:8148 \
  -hard1 /private/tmp/s8000-install-blank-128.chd \
  -skip_gameinfo -window -nothrottle -sound none
```

This is intentionally a visible, manually operated test. Do not add an
autoboot script. In the MAME terminal window enter `L SERIAL`, wait for `ENTRY
POINT F000`, and enter `J F000`. At each subsequent `Boot:` prompt enter the
release-tape commands from the table below.

After `ct(0,2)` transfers, `sawbz` recognizes this geometry and displays:

```text
Do you want the standard configuration for a 'smd' drive (y or n)?
```

If no disk is attached, `sawbz` instead reports that it cannot find the SMD
drive type in its default table. That message reflects the missing disk, not
a serial-transfer failure.

The supplied configuration enables CPU-A's **Support Segmented OS** jumper and
sets TTY0 to 8-N-2.

The tape server uses TTY0 through the bitbanger socket; the MAME window remains
the separate operator console. Use only a new or disposable disk image here.

Visible MAME testing has verified all of the following:

- the monitor accepted every bootstrap record;
- patched file 0 transferred completely (512 bytes);
- patched file 1 transferred completely (23,040 bytes);
- file 0 executed from its relocated address;
- file 1 began executing;
- file 1 contained its original `0xc55c` at probe address `0x38bc`;
- the RAM probe terminated at the installed-memory boundary (`r10=0x0f00`);
- execution continued into file 1 at `pc=0x2134` after the probe;
- file 2 transferred completely (21,504 bytes);
- `sawbz` executed and recognized the attached 128 MiB SMD disk;
- file 3 ran and created the root filesystem;
- file 4 loaded and entered `sarestor`;
- CRC-16/XMODEM delivered all 2,805,760 bytes of file 5 at approximately
  3.89 KB/s without a reported retry or CRC failure;
- the file-spacing ioctl advanced the server from file 5 to file 6 and the
  root-only restore completed.

The first full file-5 test then failed exactly at the tape-file boundary. That
run used a replacement which preserved only open, close, and strategy. Static
disassembly proved that `sarestor` next called the missing fourth entry at
`ct.o + 0x9c`; the CPU therefore entered the middle of replacement code. The
current build preserves that entry and has both a host-side regression test and
a successful end-to-end MAME run through the resulting file-5-to-file-6
transition.

The earlier automated `sawbz` smoke test ended with:

```text
sawbz test: requested L SERIAL
sawbz test: entered J F000
sawbz test: RAM probe passed; waiting for Boot prompt
sawbz test: entered ct(0,2)
sawbz test: PASS, DEADBABE written; pc=2064
```

### Required MAME Z8010 correction

The test exposed an error in MAME's Z8010 MMU descriptor auto-increment.
`sawbz` reads and rewrites a four-byte segment descriptor with `sinirb` and
`sotirb`. After the attribute byte, the real descriptor pointer wraps to its
base-address-high byte. MAME instead left it pinned on the attribute byte, so
`sawbz`'s third output byte replaced the segment attributes with `0xff` and
destroyed its own mapping.

Apply the repository-supplied correction to the MAME source tree and rebuild
the `s8000` target:

```sh
cd /Users/paxia/Projects/mame_latest/mame
git apply /Users/paxia/Projects/Zilog_S8000/serial_installer/mame-z8010-descriptor-wrap.patch
make -j1 SUBTARGET=s8000 SOURCES=zilog/s8k.cpp USE_LIBSDL=1 \
  SDL_PKGCONFIG_PATH=/opt/homebrew/bin \
  LDFLAGS='-L/opt/homebrew/lib -Wl,-rpath,/opt/homebrew/lib -lSDL3'
```

No change to file 1 or file 2 is needed for this issue. With the correction,
the visible 2026-08-13 run reached the standard-configuration question quoted
above. The earlier `0xbf82` in-memory checksum also matched the expected tape
file checksum before the unmodified file-1 handoff.

## Original release-tape installation flow

This is the operator flow in the *ZEUS System Administrator's Manual*, part
03-3246-04, section 3.2 (printed pages 3-4 through 3-17). Only the Model 31 disk
name and Model 31 Plus geometry are selected here; the order of the original
tape programs is unchanged.

> **Destructive:** both file-3 runs initialize filesystems. Use a new or
> disposable disk. The test above attaches a blank disk; answering `y` and
> continuing the program will write its block-zero configuration.

| At the `Boot:` prompt | Program | Responses |
|---|---|---|
| `ct(0,2)` | disk-format information | press RETURN after reading it |
| `ct(0,3)` | stand-alone `mkfs` for root | `6000`, `smd(0,15200)`, `16 256` |
| `ct(0,3)` | stand-alone `mkfs` for `/usr` | `12000`, `smd(0,0)`, `16 256` |
| `ct(0,4)` | stand-alone `restor` (`sarestor`) | use the answers below |

The manual's older Model 31 table specifies `16 224` for an 80 MiB,
131,936-block disk. The recovered ZEUS 3.21 `/etc/makenewfs` specifies `16 256`
for Model 31 Plus/32, matching the 128 MiB MAME disk geometry of 1024 cylinders,
8 heads, and 32 sectors. Do not use the older `16 224` value on that disk.

The standard initial-install answers at the start of `sarestor` are:

| Prompt | Response |
|---|---|
| factory-supplied Zilog release tape? | `y` |
| instructions? | `n` |
| restore root filesystem? | `y` |
| restore `/usr` filesystem? | `y` |
| root disk type | RETURN to accept `smd` |
| root unit | RETURN to accept 0 |
| root offset | RETURN to accept 15200 |
| `/usr` disk type | RETURN to accept `smd` |
| `/usr` unit | RETURN to accept 0 |
| `/usr` offset | RETURN to accept 0 |
| tape unit | `0` (this prompt does not accept an empty response) |
| OK to restore? | `y` |

The serial-patched file 4 then asks the server for the same logical dump files
that unmodified `sarestor` reads from cartridge tape. A visible MAME run on
2026-08-14 transferred file 5 completely, advanced to file 6 through the
original `ioctl(tape_fd, 6, 1)` path, and completed a root-only restore.

## How `sarestor` actually calls the tape driver

The unmodified file-4 executable was disassembled before defining the
file-boundary behavior. Its relevant path is:

```text
_readtape (0x0cc2)
  -> read(tape_fd, tbf, ntrec * 512)
  -> _read (0x1ea0)
  -> devread
  -> ctstrategy (0x2e5c)

after the common root restore returns from _doit (0x05a2):
  ioctl(tape_fd, 6, 1) at 0x06a0
  -> _ioctl (0x223e), which packs 0x0106
  -> devioctl
  -> ctcommand (0x2e82)
  -> run _doit again for the special root dump
```

`ntrec` starts at 20, so normal dump reads are 10,240 bytes. `_read` increments
the 32-bit `i_offset` by one after every driver call; it does not increment it
by the byte count. The `TS_END` record is contained in the last successful
10,240-byte read. `sarestor` consumes that record and spaces the tape forward;
it does not perform an additional zero-length read at the logical tape-file
boundary.

Original cartridge command 6 is “space file forward.” The count is in the high
byte of the packed command, so the observed `0x0106` means one file. The serial
replacement sends this as `F 01 47`; the server commits the final pending read,
changes its selected logical file from 5 to 6, resets per-file sequence state,
and acknowledges the operation. The tape descriptor remains open.

## Wire protocol

The request-driven binary protocol is 8-N-2:

```text
open v1/v3: SOH "S8" version file xor                 -> ACK or CAN
legacy read: "R" count_hi count_lo xor
v3 read:     "R" i_offset[4] count_hi count_lo xor
v3 block:    SOH block (0xff-block) data[128] crc_hi crc_lo -> ACK or NAK
v3 read end: EOT                                       -> ACK
space file:  "F" count ("F" xor count)                 -> ACK or CAN
legacy data: STX count_hi count_lo payload xor ETX     -> ACK or NAK
legacy EOF:  EOT
close:       CAN
```

Version 1 is used only by the monitor bootstrap and file-0/file-1 handoff.
The replacement `ct.o` opens protocol version 3. Each standalone strategy call
is one short CRC-16/XMODEM session: block numbers restart at 1, every packet
contains 128 bytes, and EOT terminates that strategy call rather than the
logical tape file. The CRC uses polynomial `0x1021`, initial value zero, no
reflection, no final XOR, and is sent high byte first. Its standard
`123456789` check value is `0x31c3`. A normal `sarestor` request consists of
eighty XMODEM blocks followed by EOT.

The server holds the most recently acknowledged strategy payload until the
next `i_offset` or space-file request arrives. Repeating the same `i_offset`
retransmits the same payload; the next value commits it. This makes an outer
read retry idempotent.

Legacy protocol version 1 retains 1.25 ms pacing per response byte for MAME.
Version-3 XMODEM has no artificial byte delay: the sender writes a complete
packet as fast as the socket or physical serial device accepts it and then
waits for ACK or NAK. A physical serial device naturally enforces its selected
baud rate. `--xmodem-byte-delay` exists only as a diagnostic override.

The XMODEM receive routine polls the UART with a bounded counter for every
expected byte. On a timeout, bad block number/complement, or CRC failure,
it drains input until one complete inter-byte timeout has elapsed, sends NAK,
and waits for the block again. It accepts and ACKs a valid duplicate of the
preceding block without copying it a second time. Ten consecutive damaged
packets terminate the strategy call with an error instead of hanging forever.

Verbose progress is based on committed logical-file bytes, not CHD size. It is
reported after at least 65,536 additional bytes. Since `sarestor` requests
10,240 bytes at a time, reports normally occur every seven reads (71,680
bytes). The displayed rate is committed bytes divided by elapsed time since
the logical file was selected, so it includes pauses for disk writes and can
lag the bytes already received by one 10,240-byte request.

The standalone caller chooses the logical file exactly as it did with
`ct(0,N)`; only the driver's byte source has changed.
