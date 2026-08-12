# Plan: installing a bare System 8000 over a serial line

**Status: design only. Nothing here is implemented.** This records what has been
established from the firmware, the kernel build system and the manuals, the two
routes that follow from it, and a test order that validates most of the work
before any protocol code is written.

The goal is to bring up a machine that has working hardware and nothing else: no
bootable disk, no tape drive, only a serial line to another computer.

Background is in [`MONITOR.md`](MONITOR.md) (firmware, command set, Download
Mode) and [`STANDALONE.md`](STANDALONE.md) (the bootstrap chain and stand-alone
device model).

## What the release tape actually is

This is the fact the whole design turns on. From *ZEUS System Administrator's
Manual* §3.1:

| File | Contents |
|---|---|
| 0 | primary bootstrap — a 512-byte program |
| 1 | secondary bootstrap |
| 2 | disk formatting information |
| 3 | **stand-alone `mkfs`** |
| 4 | **stand-alone `restor`** |
| 5 | level 0 dump of the common root |
| 6–8 | level 1 dumps of Model 21 / 11 / 31 special root files |
| 9 | level 0 dump of the common `/usr` |
| 10 | level 1 dump of Model 21 and 31 special `/usr` files |
| 11+ | `tar` packages, installed with `package(M)` |

**The tape carries dump archives, not filesystems.** The manual describes
restoration as "creating empty ZEUS filesystems and restoring data files and
directories onto the empty filesystems". `mkfs` builds the filesystem *on the
machine*; `restor` unpacks files into it. Nothing filesystem-shaped is ever
transferred, so only allocated file content crosses the wire — never free space,
and `/tmp` and `/z` never cross at all because they are simply `mkfs`'d locally.

Two consequences matter:

- **The entire base install happens in stand-alone mode**, before any kernel
  runs. Root *and* `/usr` are both restored by the stand-alone `restor` at tape
  file 4. A serial device in the stand-alone bootstrapper would therefore cover
  the whole job; a kernel-level tape device is only needed for the optional
  `tar` packages at file 11 and beyond.
- **We do not have those stand-alone utilities.** `/usr/stand/.contents` lists
  exactly two entries, `boot` and `.contents`. Stand-alone `mkfs` and `restor`
  ship on the tape and are never installed to disk, so they are absent from
  every recovered tree. Only WEGA's `sa.mkfs.c` and `restor.c` source exists,
  for different hardware.

That second point is what forces the choice below.

## What the machine gives us

- **No serial boot device.** `ZBOOT` dispatches only `D`/`T`/`S`/`M`, and the
  U70 switch has two bits for four devices with no spare encoding.
- **But the monitor already loads and runs code over serial.** Download Mode
  (`L <filename>`) reads Tektronix records on **TTY0** — SIO 0 channel A, ports
  0xff81/0xff85 — checksums each record, and prints `ENTRY POINT`. `G` runs it.
  Load addresses below `0x8000` are rejected.
- **Serial I/O is free to stand-alone code.** `sc #24` reads a byte from the
  channel-A ring, `sc #26` writes one. The monitor owns the interrupt handler
  and ring buffer.
- **Stand-alone images link exactly where Download Mode needs them.** WEGA's
  `create.boot` uses `ld -s -e start -b 0x8000`; Download Mode's floor is
  `0x8000`. A stand-alone image is directly `L`-loadable.
- **The kernel has six unused driver slots.** `/usr/sys/dev/udev1.c` … `udev6.c`
  are stubs whose header states that `bdevsw` and `cdevsw` in `conf.c` already
  contain entries pointing at their symbols. You link an object defining those
  symbols instead of the stub. The manual assigns these slots **major numbers
  16–21**; sysgen asks for the `.o` filename and also fixes `rootdev`,
  `swapdev` and `pipedev`. The link it performs, recovered from `/etc/sysgen`:

  ```sh
  sld -Ns -o <kernel> z.o mch.o ver.o ../fpe/fpe.o \
      ../dev/{mt,lpr,ct,md,zd,smd}.o|.d.o \
      event.{icp|nicp}.o conf1.o conf2.{icp|nicp}.o \
      ../sys/LIB1 ../dev/LIB2
  ```

## The one hard constraint

**The kernel cannot be sent by Download Mode.** It is `0xE611` — s.out
segmented, separate I&D — and 123,926 bytes. Download Mode transfers no segment
information; everything lands in segment 0. A small non-segmented loader has to
go first, and that is the only reason such a loader appears in either route.

## Two routes

### Route A — serial as tape (faithful)

Swap the strategy routine behind the name **`ct`** in the stand-alone
bootstrapper's `devsw`, keeping the name. The original documented procedure then
runs verbatim: `ct(0,3)` fetches `mkfs`, `ct(0,4)` fetches `restor`, `ct(0,5)`
and `ct(0,9)` feed it the dumps. Nothing above the device layer knows the tape
is a wire. No kernel changes at all.

Tape and serial are both sequential, and `ct(n,m)` means only "skip to file *m*,
then stream", so the host side is small.

**Blocked on:** stand-alone `mkfs` and `restor` built for ZEUS. They exist on no
recovered medium. Porting WEGA's sources means retargeting to SMD and to this
monitor's system calls — real work, and unverifiable without a reference binary.

### Route B — RAM root and the recovered userland (pragmatic)

Relink the kernel with a RAM-disk block driver in user slot 1 (major 16) and
`rootdev 16,0`. Serial-load kernel and a small root image, boot ZEUS from RAM,
and then use the **userland** `/etc/mkfs` and `/etc/restor` — both original
recovered ZEUS binaries, both already in this repository's image.

`restor` supports this directly. From `restor(M)`:

> `f` — Use the first *argument* as the name of the tape instead of `/dev/rct0`.

So it will read a dump from an ordinary file or another device; no kernel tape
device is required.

Sequence once ZEUS is up from RAM:

1. `mkfs` the real root and `/usr` partitions — no transfer, built locally.
2. `restor rf <source> /dev/rroot`, host streaming the level 0 root dump.
3. Same for `/usr` with the level 0 `/usr` dump.
4. `mkfs` `/tmp` and `/z` locally.
5. Write block 0, reboot from disk.

**Costs:** a kernel relink and a ~50-line driver. **Buys:** every utility that
does real work is an original recovered binary rather than something we wrote.

### Recommendation

**Route B**, because Route A is blocked on binaries that exist only on a tape
nobody has. Route A remains the preservation-grade goal — if a release tape is
ever imaged, files 3 and 4 unblock it immediately, and at that point Route A is
both simpler and more faithful than Route B.

## Open questions

**`_b0rd` with no disk.** `mkblock0.py` documents that the kernel reads
`rdev`/`sdev`/`pdev` from block 0 at 0x18/0x1a/0x1c. On a diskless boot there is
no block 0. Either sysgen's baked-in `rootdev` stands when that read fails, or
the kernel wedges on a controller that is not there. Ways out: place a synthetic
block 0 at the head of the RAM-disk region so `_b0rd` is satisfied from major
16, or disassemble around `_b0rd` and read the failure path. **This decides
whether the RAM-disk driver is fifty lines or needs a patch**, and it can be
answered by static analysis with no build.

**Does `restor r` read strictly sequentially?** If it does, the source argument
can be a serial device read live. If it seeks or makes a second pass, the dump
must be spooled to a file first — which needs somewhere to put several MB that
is neither the RAM root nor the filesystem being restored.

**Line discipline.** `/dev/tty0` is a tty. Binary dump data will be mangled by
the default line discipline; the line needs raw mode, and flow control has to be
real rather than XON/XOFF, since a dump contains those bytes.

**Memory sizing.** A bootstrap root — shell, `mkfs`, `fsck`, `restor`, `dd`,
`tar`, `mknod`, `mount` — is estimated at 300–400 KB, but that is an estimate.
Check it against `MAXMEM` in `sysparm.h` for the Model 31 configuration.

**Swap on a diskless boot.** sysgen wants a swap major/minor. Either point it at
the RAM disk or configure small enough not to swap. Untested.

## Test order

Nearly everything can be proven **before** any protocol exists, because of two
facilities:

- **`null_modem` + bitbanger.** `sio0:cha:tty0` is a real `RS232_PORT` built
  with `default_rs232_devices`, which includes `null_modem`; `null_modem` is
  backed by a `bitbanger_device` that streams a **file** in and out. The
  Tektronix format is fully specified, so the stream can be generated offline.
  No host program is needed for testing.

  ```sh
  ./s8000 s8000 -rp roms -hard1 … \
    -sio0:cha:tty0 null_modem -bitb /path/to/stream.bin
  ```

- **The MAME debugger's `load`** (`src/emu/debug/debugcmd.cpp:283`):
  `load <filename>,<address>[,<length>]` puts a file straight into memory.

**Rung 0 — the user slot works, with no serial and no boot risk.** Relink with
the RAM-disk driver at major 16 but leave `rootdev` on the SMD disk. Boot
normally; from a shell run `mknod /dev/ud0 b 16 0`, `mkfs`, `mount`, copy files,
`umount`, `fsck`. Proves the symbol substitution links, that `bdevsw[16]`
reaches `usr1strategy`, and that the driver logic is right — while the machine
still boots as it does today.

**Rung 1 — root on the user slot, still no serial.** Same kernel, `rootdev
16,0`. Populate the RAM disk with the debugger: break before the kernel starts,
`load rootfs.img,<ramdisk address>`, continue. Answers the `_b0rd` question
directly, at no transport cost.

**Rung 2 — `restor` from a non-tape source, still no serial.** With the machine
booted normally, run `restor rf <file> <fs>` against a dump held in an ordinary
file, and confirm it populates the target. Settles the sequential-read question
and proves the `f` key does what the manual says.

**Rung 3 — the monitor's `L` path with a canned stream.** Generate Tektronix
records offline, feed them with `-bitb`, watch for `ENTRY POINT`. Validates
record format, checksums, the `>0x8000` rule and the handshake.

**Rung 4 — segment placement, without serial.** The loader's hard part is
`loadit()`, not the transport. Load it from disk with the existing `boot`
(`smd(0,15200)yourloader`) and have it pull the kernel from `smd(...)` too. Only
then swap the device layer for serial.

**Known hazard in rung 3.** The bitbanger plays its file back unconditionally at
line rate and cannot wait for the monitor's per-record acknowledge. The receive
ring is 256 bytes and `cmd_L` does real work per record, so a large canned
stream may overrun it. Start with a few records at a low baud rate; an overrun
establishes that the real host side must be ACK-driven rather than free-running.

## Deliverables, if it proceeds

1. A RAM-disk block driver replacing `udev1.c` — `usr1open`, `usr1close`,
   `usr1strategy`.
2. A relinked kernel with that driver and `rootdev 16,0`.
3. A small bootstrap root filesystem image.
4. A non-segmented stand-alone loader: `loadit()` segment placement plus a
   channel-A device using `sc #24`/`sc #26`.
5. A host-side sender — for testing, a script emitting a canned stream; for use,
   something that serves dumps on demand.

Items 1–3 are exercised by rungs 0–2, item 4 by rung 4, item 5 by rung 3.

## Sources

- [`MONITOR.md`](MONITOR.md), [`STANDALONE.md`](STANDALONE.md) — firmware and
  stand-alone environment, with ROM addresses and manual citations.
- *ZEUS System Administrator's Manual*, 03-3246-04, §3.1 — the release tape
  manifest; §5 — sysgen, the six user device slots and their major numbers.
- *System 8000 Hardware Reference Manual*, 03-3237-04, §5.9.4 — Download Mode.
- `restor(M)` and `mkfs(M)` in the recovered `/usr/man/manM`.
- `/etc/sysgen` on the ZEUS image — the `sld` link line.
- `/usr/sys/dev/udev1.c` … `udev6.c`, `/usr/sys/conf/z.c` — the driver slots.
- `/usr/stand/.contents` — evidence that only `boot` is installed to disk.
- `src/devices/bus/zbi/s8k_cpu.cpp` and `src/devices/bus/rs232/` in the MAME
  fork — the TTY0 RS232 port and `null_modem`.
