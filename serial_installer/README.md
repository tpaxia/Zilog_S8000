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
- `build/loader-serial.bin`: file 1 with its 700-byte `ct.o` replaced and its
  two-byte RAM-probe pattern changed from `0x0000` to `0xa5a5`;
- `build/sarestor-serial.bin`: file 4 with only its 700-byte `ct.o` replaced.

The Makefile takes `tapes/images/zeus-3.21-install.tap` directly as its only
tape input. It parses logical files 1 and 4 in memory; it does not build from
the extracted-file tree. The patchers hash-check those logical files. Tests
verify that file 4 changes only inside `ct.o`, and that file 1 changes only
inside `ct.o` plus the two-byte probe word at `0x38bc`.

### Why file 1 uses `0xa5a5`

Original file 1 uses the initialized word at address `0x38bc` as the source for
its RAM read/write comparison. The tape contains `0x0000` there. MAME's
pristine ZBI RAM implementation discards a write outside installed RAM and
returns zero for the subsequent read, so a zero probe falsely succeeds forever.
The ROM monitor memory test does not have this problem because it uses nonzero
patterns.

`patch_loader.py` changes only that word to `0xa5a5`. Installed RAM stores and
reads the pattern successfully; absent RAM still returns zero and terminates
the probe. This keeps MAME pristine and makes the workaround part of the
serial-patched standalone loader where it belongs.

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

## Known-working MAME downloader setup

This is the frozen, verified setup. Do not substitute `s8000h19` or attach the
H19 terminal device. The test uses MAME's generic serial terminal, and
`mame_downloader_test.lua` aborts if an H19 device exists.

The final verified pristine executable is:

```text
/Users/paxia/Projects/mame_latest/mame/s8000
SHA-256 600479d717eaa51a0625075183ee7f63d4908ed14e539657c990fe67da0a3a8f
```

There is no `s8k_ram.cpp` modification in this build. The earlier open-bus
experiment was reverted before this hash was produced and before the test
below passed.

Build and test the serial images:

```sh
cd /Users/paxia/Projects/Zilog_S8000/serial_installer
make test
```

In terminal 1:

```sh
cd /Users/paxia/Projects/Zilog_S8000/serial_installer
python3 serve_tape.py ../tapes/images/zeus-3.21-install.tap \
  --listen 127.0.0.1:8148 -v
```

In terminal 2:

```sh
cd /Users/paxia/Projects/mame_latest/mame
./s8000 s8000 -rp roms \
  -cfg_directory /Users/paxia/Projects/Zilog_S8000/serial_installer/mame_cfg \
  -slot_cpu:cpu_a:sio0:cha:tty0 null_modem \
  -slot_cpu:cpu_a:sio0:chb:console terminal \
  -bitb socket.127.0.0.1:8148 \
  -autoboot_delay 2 \
  -autoboot_script /Users/paxia/Projects/Zilog_S8000/serial_installer/mame_downloader_test.lua \
  -window -nothrottle -sound none
```

The supplied configuration enables CPU-A's **Support Segmented OS** jumper and
sets TTY0 to 8-N-2. The Lua script enters `L SERIAL`, verifies the bootstrap at
`0xf000`, enters `J F000`, observes file 0 running from its relocated high
address, and then observes file 1 executing at a low address. It sends no
installer command and touches no disk.

The successful run verified all of the following:

- the monitor accepted every bootstrap record;
- patched file 0 transferred completely (512 bytes);
- patched file 1 transferred completely (22,528 bytes);
- file 0 executed from its relocated address;
- file 1 began executing;
- file 1 contained `0xa5a5` at probe address `0x38bc`;
- the RAM probe terminated at the installed-memory boundary (`r10=0x0f00`);
- execution continued into file 1 at `pc=0x2134` after the probe;
- no H19 device was instantiated.

The exact successful test ended with:

```text
downloader test: requested monitor L SERIAL; no H19 instantiated
downloader test: bootstrap present; entered J F000
downloader test: file 1 entered at pc=01fe
downloader test: PASS, RAM probe ended at r10=0f00; pc=2134
```

That is the current verified boundary. File 1 now works through RAM sizing on
pristine MAME. The later `ct(0,2)` through `sarestor` interaction is not
verified yet.

## Original release-tape installation flow

This is the operator flow in the *ZEUS System Administrator's Manual*, part
03-3246-04, section 3.2 (printed pages 3-4 through 3-17). Only the Model 31 disk
name and Model 31 Plus geometry are selected here; the order of the original
tape programs is unchanged.

> **Destructive:** both file-3 runs initialize filesystems. Use a new or
> disposable disk. The downloader-only test above does not attach or alter a
> disk.

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
| tape unit | RETURN to accept 0 |
| OK to restore? | `y` |

The serial-patched file 4 then asks the server for the same logical dump files
that unmodified `sarestor` reads from cartridge tape. The restore phase is not
yet verified.

## Wire protocol

The request-driven binary protocol is 8-N-2:

```text
open:     SOH "S8" version file xor              -> ACK or CAN
read:     "R" count_hi count_lo xor              -> response
data:     STX count_hi count_lo payload xor ETX   -> ACK or NAK
EOF:      EOT
close:    CAN
```

The standalone caller chooses the logical file exactly as it did with
`ct(0,N)`; only the driver's byte source has changed.
