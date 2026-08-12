# The stand-alone environment: bootstrap chain, device addressing, and serial loading

This describes the layer between the firmware monitor and a running ZEUS
kernel — the *stand-alone* programs that build filesystems and restore
software onto a bare machine. It answers three questions:

- how an installation tape gets from a monitor with no drivers to a kernel with
  drivers, and then to files it can execute;
- where the device nodes are in that world (there are none);
- whether a stand-alone program can create filesystems and pull files over a
  serial line, and what it would take.

Sources are cited inline. Monitor addresses are image offsets in
`re/monitor/monitor30.s`. See [`MONITOR.md`](MONITOR.md) for the firmware itself.

## The four-stage boot chain

Nothing loads everything at once. Each stage exists only to bring in the next.

| Stage | What it is | How it is found |
|---|---|---|
| 1 | Monitor tape loader, 110 bytes | Relocated to 0xf800 by `cmd_Z`'s `T` branch; reads a fixed chunk from load point into address 0 and jumps there |
| 2 | Primary bootstrapper (`boot0.*`), tape file 0 | Whatever stage 1 landed at address 0 |
| 3 | Secondary bootstrapper (`boot`), tape file 1 | Pulled in by stage 2 |
| 4 | A kernel or a stand-alone utility | Typed at the secondary bootstrapper's `:` prompt |

Stage 1 has no drivers and no notion of names — see `MONITOR.md`. Stage 2 has
just enough of one device to reach stage 3. **Stage 3 is where the drivers
live**, and it is the interesting one.

The ZEUS release tape is laid out to match. §2.4 of the *ZEUS System
Administrator's Manual* is explicit that a tape file argument "must be greater
than 1 since the first and second files on tape are the bootstrappers
themselves", and §3.1 gives the full manifest:

| File | Contents |
|---|---|
| 0 | primary bootstrap — a 512-byte program |
| 1 | secondary bootstrap |
| 2 | disk formatting information |
| 3 | stand-alone `mkfs` |
| 4 | stand-alone `restor` |
| 5 | **level 0 dump of the common root** — identical on all models |
| 6 | level 1 dump of Model 21 special root files |
| 7 | level 1 dump of Model 11 special root files |
| 8 | level 1 dump of Model 31 special root files |
| 9 | **level 0 dump of the common `/usr`** — identical on all models |
| 10 | level 1 dump of Model 21 and Model 31 special `/usr` files |
| 11+ | `tar`-recorded packages — accounting, global optimizer, learn, sccs, v7 nroff, zmenu — installed with `package(M)` |

**The tape carries dump archives, not filesystems.** The manual describes the
restoration as "creating empty ZEUS filesystems and restoring data files and
directories onto the empty filesystems" — `mkfs` builds the filesystem *on the
machine*, and `restor` unpacks files into it. Nothing filesystem-shaped is ever
transferred, so a tape holds only allocated file content, never free space.

Those dumps are the same V7/System III `dump` format this repository already
decodes; see the pristine root dump described in the main README.

The common/model-specific split is why files 5–10 are paired the way they are: a
level 0 dump of the parts every machine shares, then a level 1 overlay of the
handful that differ. The manual lists the Model 31 overlay in full — `/zeus`,
`/zeus2_Y.Z`, `/dev/smd0`–`smd4`, `/dev/rsmd0`–`rsmd4`, the partition aliases
`/dev/{z,rz,usr,rusr,tmp,rtmp,root,rroot,swap}`, and `/etc/group` — and notes
that selection is "through tape location rather than filename", since the
model-specific files are identically named across models.

## Device addressing: there are no device nodes

Stand-alone programs never open `/dev/anything`. They cannot — at the point
`mkfs` runs there is no filesystem, let alone a `/dev` in it.

Instead the drivers are compiled into the image and selected by **name string**
from a device-switch table. From WEGA's `bconf.c`:

```c
struct devsw devsw[] =  {
	"md",	mdstrategy,	nullsys,	nullsys,
	"zd",	mdstrategy,	nullsys,	nullsys,
	"fd",	fdstrategy,	nullsys,	nullsys,
	"ud",	udstrat,	udopen,		udclose,
	"rm",	rmstrat,	rmopen,		rmclose,
	0,0,0,0
};
```

`devread`, `devwrite`, `devopen` and `devclose` are one-line dispatchers
through this table. `open()` in `bsys.c` parses the familiar syntax:

```text
dev(unit,offset)filename
```

- everything before `(` is matched against `dv_name`; the **table index**
  becomes `i_dev`, and that is the only "device number" in play;
- `unit` is a single digit, 0–7;
- `offset` is the start block of a filesystem on that unit;
- `filename`, if present, is looked up by walking a V7 filesystem — `openi`,
  `dlook`, `sbmap` and `find` are a miniature read-only filesystem
  implementation linked into the image;
- an empty filename, or the pseudo-unit `'r'`, means raw sequential access with
  no filesystem at all.

The source's own example is `zd(0,13200)wega`, structurally identical to the
ZEUS form `smd(0,15200)zeus`. Major and minor numbers never enter into it.

The ZEUS secondary bootstrapper `/usr/stand/boot` carries its name table at
file offset 0x5362:

```text
zd   ct   smd   md   mt
```

Zilog disk, cartridge tape, storage-module disk, mini disk, and nine-track
magnetic tape. All local storage — note what is absent, discussed below.

Device nodes appear only later. `restor` writes a root filesystem that already
contains `/dev`, and those nodes matter only once the real kernel is running.
This repository builds that `/dev` with `mkdev` and `devs.txt`.

## Loading a kernel is the same operation as loading a utility

`loadit()` in `boot.c` reads the executable header and dispatches on the magic:

| Magic | Format |
|---|---|
| `0xE607` / `0xE611` | `s.out` segmented, executable / separate I&D |
| `0xE707` / `0xE711` | `s.out` non-segmented, executable / separate I&D |
| `0xE807` / `0xE811` | `z.out` non-segmented, executable / separate I&D |

It then walks the segment table and loads each segment's code, data and bss to
that segment's number, and takes the entry point from the header. Offset
segments are rejected outright (`Cannot load offset segs yet`).

**There is no special case for a kernel.** `smd(0,15200)zeus` and
`ct(0,2)sa.mkfs` take identical paths. That is the whole trick behind
installation: the same stage-3 program can run `mkfs`, `format` and `restor`
against a bare disk, and then boot ZEUS off that same disk once the filesystems
exist. A kernel is just an `s.out` image that happens not to return.

The stand-alone utilities that ship in WEGA's `sacmd` source are `sa.mkfs`,
`sa.install`, `sa.format`, `sa.verify`, `sa.cat`, `sa.timer`, `sa.shipdisk`,
plus stand-alone `restor`, `dump`, `dumpdir` and `tar`. Each is linked against
`BOOTLIB`, the same saio framework and driver set as `boot` itself.

## Serial loading

### WEGA already shipped a serial device driver

`brm.s` is the `rm` entry in the table above. Its header:

> Device driver for loading WEGA procedure files from a Local System such as a
> GDS 6000 under UDOS, over the console TTY channel.

So `rm(0,0)filename` fetches a file over the serial line through exactly the
same `open()`/`read()` path as a disk file. `rmopen` sets `i_unit` to `'r'`,
which makes `bsys.c` treat it as a raw stream and skip the filesystem walk.
Only reading is supported; opening for write fails.

The wire protocol is hand-rolled and small:

```text
host request:   SOH  ESC  'S'          -> host ACKs
file type:      0x01 (binary)          -> host ACKs
filename:       STX <name> ETX <cksum> -> host ACKs
```

The checksum is a byte-wise XOR over the name; the driver retries ten times.
`CAN`, `NAK` and `EOT` cover the error and end-of-file paths. Its three
diagnostics are `rm: cannot open file on local system`, `rm: read error from
local system`, and `rm: cannot write to local system`.

There is also a **`boot0.rm`** target in `create.boot` — a *primary*
bootstrapper that comes up over the serial link, so the entire chain can start
from a host rather than from media.

### The S8000 monitor gives serial I/O away for free

WEGA's `brm.s` does not program the SIO. It issues `sc #TTIN` and `sc #TTWR`
— `SC` traps into the monitor, with `TTIN := %04` and `TTWR := %06`.

Monitor 3.0 implements exactly that ABI. `trap_syscall` at `0x0f2c` takes the
`SC` operand byte, subtracts 4, and uses the result as a byte offset into a
word table at `0x0056`:

| `sc #` | Target | Service |
|---|---|---|
| 4 | `0x0a4a` `getc` | console read (WEGA's `TTIN`) |
| 6 | `0x0a68` `conout` | console write (WEGA's `TTWR`) |
| 8 | `0x09d8` `getedit` | read one character with line editing |
| 10 | `0x0a80` `crlf` | |
| 12 | `0x050c` `putmsg` | print a length-prefixed message |
| 14 | `0x0540` `puthex16` | |
| 16 | `0x0594` `putline` | |
| 18 | `0x0544` `puthex8` | |
| 20 | `0x0398` | not identified |
| 22 | `0x03a4` | not identified |
| **24** | **`0x11aa`** | **read a byte from serial channel A — the TTY0 download port** |
| **26** | **`0x0cae`** | **write a byte to serial channel A** |

`sc #4` and `sc #6` landing on `getc` and `conout` is independent confirmation
that the two firmwares share this call numbering, which is why WEGA's
stand-alone console code is portable at all.

Entries **24 and 26 are the important ones**. They are the channel-A ring read
and port write that Download Mode itself uses. A stand-alone driver for the
*auxiliary* serial port is therefore two instructions per byte, with the
monitor owning the interrupt handler and ring buffer — no SIO programming at
all, and without stealing the console the way `rm` does.

### Stand-alone images are directly loadable over serial

`create.boot` links the secondary bootstrapper with:

```sh
ld -s -e start -b 0x8000 -o boot bstart.o BOOTLIB
```

Base address **0x8000**. Monitor Download Mode rejects any record whose load
address is below 0x8000 (`cp r4,#0x8000` at `0x0e54`). The two agree exactly,
so a stand-alone image can be sent straight down the wire with `L` and started
with `G` — no disk, no tape, nothing on the machine but firmware.

## What a serial install would take here

The pieces exist but not in one place. ZEUS's `devsw` is `zd ct smd md mt` —
**there is no `rm`**. The serial driver is WEGA's, and WEGA is the EAW P8000
line: same Z8000 saio heritage, different hardware, no `smd` or `ct` driver.
Compounding it, we have WEGA stand-alone *source* but only a ZEUS stand-alone
*binary*; no ZEUS stand-alone source has been recovered.

Two routes:

1. **Port.** Take `bsys.c`, `bconf.c`, `boot.c` and `brm.s`; retarget `brm.s`
   from `sc #4`/`sc #6` to `sc #24`/`sc #26` so it uses TTY0 instead of the
   console; add an SMD `strategy` routine. `sa.mkfs` and the rest then drop in
   unchanged, and the result is `L`-loadable because it links at 0x8000.
2. **Patch.** Add an `rm` entry to the existing ZEUS `boot` binary at 0x5362.
   Less work in principle, but it means hand-assembling into a stripped image.

Either way the host side is missing. `rm` expects a program on the remote
machine that answers `ESC 'S'`; that was a GDS 6000 under UDOS and nothing
recovered here implements it. The same is true of Download Mode's `LOAD`
procedure file. Both protocols are fully specified — `brm.s` for one, manual
§5.9.4 for the other — so both host ends are small programs, but they have to
be written.

## Sources

- WEGA 3.1 stand-alone command sources, `sacmd.tar` — `bconf.c`, `bsys.c`,
  `boot.c`, `bmch.s`, `brm.s`, `create.boot`, `sa.mkfs.c`, `sa.install.c`.
  These are from the EAW P8000 WEGA source set and are **not part of this
  repository**.
- `/usr/stand/boot` in the recovered ZEUS `/usr` tree — the compiled secondary
  bootstrapper; device-name table at file offset 0x5362.
- `re/monitor/monitor30.s` and `re/monitor/monitor30.bin` — the annotated Monitor 3.0
  disassembly; `trap_syscall` at 0x0f2c and the service table at 0x0056.
- *System 8000 Hardware Reference Manual*, 03-3237-04, §5.9 — monitor commands
  and Download Mode.
- *ZEUS System Administrator's Manual*, 03-3246-04, §2.4 — the operator-facing
  boot procedure and release-tape file numbering.
