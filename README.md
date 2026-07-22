# Zilog System 8000 — bootable ZEUS 3.21 disk image for MAME

This repository contains a ready‑to‑use hard‑disk image (`s8000_smd.chd`) that boots
**ZEUS 3.21** (Zilog's Unix, SYS III) on the **Zilog System 8000** in
[MAME](https://www.mamedev.org/), together with notes on how the image was produced
and how to run it.

It is a reconstruction: the ZEUS filesystems published on pofo.de (see below), written
into the on‑disk layout the ZEUS Administrator's Manual documents for the System 8000
SMD system disk, given a valid **block‑0 boot record** so it auto‑boots, and packaged as
a CHD whose geometry the MAME SMD controller accepts. In MAME (CPU‑A, Monitor / BIOS
v3.0) it auto‑boots ZEUS 3.21 and the kernel runs its **entire** startup — bootstrap,
memory sizing, scheduler — reaching the idle loop with the real‑time clock ticking.

Two things are required beyond a stock build, both described below: the CPU‑A must run in
**segmented‑OS** mode, and MAME needs a **one‑line interrupt fix** (without it the kernel
panics early). See **Status** for exactly how far it currently gets.

## Credits & sources

- **MAME System 8000 driver & Z‑Bus/CPU/MMU devices** — `src/mame/zilog/s8k.cpp`,
  `src/devices/bus/zbi/s8k_cpu.cpp`, `src/devices/machine/z8010.cpp`. These source files
  carry the header `copyright-holders: A. Lenard`. A MAME fork containing System 8000
  work is at <https://github.com/ArcLight22/mame>.
- **MAME ROMs** — <https://github.com/ArcLight22/S8000-roms>. That repo's README states
  the dumps were mirrored/compiled from pofo.de, bitsavers, and the Uni‑Stuttgart
  computer museum.
- **retro-fuse (big‑endian fork used to write the ZEUS filesystems)** —
  <https://github.com/ArcLight22/retro-fuse>.

The input filesystems are the ZEUS archives published at
**<http://www.pofo.de/S8000/misc/harddisk_images/>** — `s8000_root.tar.gz` and
`s8000_usr.tar.gz` (a `s8000_z.tar.gz` is also there but not used for a bootable
root+/usr disk). The copies used here are byte‑for‑byte identical in size to those files.

Hardware / layout facts below are taken from the Zilog *ZEUS System Administrator's
Manual* (03‑3246‑04, Oct 1983) and the *System 8000 CPU Hardware Reference Manual*
(03‑3200‑01, Sep 1982), both on bitsavers.

## Producing the disk image

### 1. Build the filesystem writer

ZEUS is a big‑endian Version‑7 Unix. The image is written with a tiny non‑FUSE helper
(`mkv7img`) built on top of ArcLight22's big‑endian **retro-fuse** fork. A couple of
small fixes were needed in that code to make the *write* path usable (a file‑create
bug, and reconstruction of hard links, which are not present in the extracted trees);
those details are out of scope here — see the retro-fuse fork.

### 2. Lay out the disk and populate the filesystems

The System 8000 SMD system disk holds two ZEUS filesystems at fixed block offsets, per
the ZEUS Administrator's Manual (§3.4). All sizes are in **512‑byte blocks**:

| Filesystem | Device        | Offset (blocks) | Size (blocks) | Size |
|------------|---------------|-----------------|---------------|------|
| `/usr`     | `smd(0,0)`    | 0               | 12000         | ~6 MB |
| *(gap)*    | —             | 12000           | 3200          | ~1.6 MB |
| `/` (root) | `smd(0,15200)`| 15200           | 6000          | ~3 MB |

The sizes (`/usr` 12000, root 6000) and offsets (`smd(0,0)` and `smd(0,15200)`) are the
values shown in the manual's `mkfs` steps (§3.4). The 3200‑block gap between them is not
described in the sections consulted (on Unix systems this region is typically swap).

The two filesystems are created empty at those offsets, then the extracted ZEUS trees
are copied in — i.e. `s8000_usr.tar.gz` is unpacked into the `/usr` filesystem and
`s8000_root.tar.gz` into the root filesystem. (Hard links such as the two kernel names,
`sh`/`rsh`, `od`/`hd`, etc. are restored during the copy, which lets the root tree fit
the authentic 6000‑block partition.)

### 3. Determine the disk geometry (for the CHD)

The System 8000 SMD controller (SMDC) in MAME expects a hard disk whose CHS geometry
matches the real drive, because ZEUS's disk driver and the controller both translate
between logical block numbers and cylinder/head/sector.

The manual (Table 3‑2) lists the Model 31/32 system disk as an 8" Winchester "smd"
drive (marked *Fujitsu / Memorex*) with a **logical size of 131936** 512‑byte blocks
and interleave **n = 224** blocks per cylinder. That fixes the cylinder count:

```
131936 / 224 = 589 cylinders
```

The manual does not give the head/sector split, only n = 224 blocks per cylinder. Any
split with heads × sectors = 224 reproduces the same block↔CHS mapping the SMDC uses;
the geometry chosen here is:

```
cylinders = 589
heads     =   7      (7 × 32 = 224 blocks/cylinder)
sectors   =  32
bytes/sec =  512
------------------------------------
589 × 7 × 32 = 131936 blocks = 67,551,232 bytes  (~67.5 MB)
```

### 4. Write the block‑0 boot record (so it auto‑boots)

The secondary bootstrapper reads a configuration record from **physical block 0** of the
drive (which coincides with the reserved boot block of the `/usr` filesystem at offset
0). Its layout is `sys/block0.h`; the magic is `BLK0MAGIC = 0xDEADBABE`. Disassembling
`/usr/boot` shows the default (hands‑off) boot only needs three big‑endian fields:

```
offset 0x00  b0_MAGIC  = 0xDEADBABE
offset 0x12  b0_rdrv   = 0            (root drive unit)
offset 0x14  b0_roff   = 15200        (root filesystem block offset)
```

With those in place the monitor auto‑constructs `smd(0,15200)zeus` and boots the kernel
with no console input. (A real system's block 0 also carries the root/swap/pipe device
numbers and the full virtual‑disk table; those are written by the stand‑alone `wbz`
utility and are not required just to load the kernel.)

### 5. Create the `/dev` device nodes

The pofo.de archives contain **no** device nodes, so the root filesystem's `/dev` must be
repopulated with `mknod`. Device majors are from the Administrator's Manual §4.2.2:
**SMD disks = major 8**, so root = `(8,2)`, swap = `(8,1)` (minor = virtual‑disk number:
root is vd 2 at offset 15200, swap is vd 1). The char‑device majors (console, tty, mem,
null) are not yet pinned down — see **Status**.

### 6. Convert the raw image to a CHD

The raw 131936‑block image is converted to a MAME CHD with `chdman`:

```sh
chdman createhd -i s8000_smd.img -o s8000_smd.chd --chs 589,7,32 --sectorsize 512
```

The resulting `s8000_smd.chd` is what ships in this repo.

## Running it in MAME

### ROMs

Obtain the System 8000 ROM set from
[ArcLight22/S8000-roms](https://github.com/ArcLight22/S8000-roms) and copy the contents
of its `roms/s8000/` directory into your MAME ROM path under an `s8000` folder:

```
<mame>/roms/s8000/cpu_34-0715-03a.u76      (and the other cpu_/wdc_/mwdc_/tcc_/hpcpu_ dumps)
```

Verify with:

```sh
mame -rp <mame>/roms s8000 -verifyroms s8000     # -> "romset s8000 is good"
```

The default machine is a **CPU‑A with BIOS v3.0**, which uses the `smd` disk controller —
exactly what this image targets.

### Boot in **segmented** mode (required)

ZEUS 3.21 is a **segmented‑OS** build, so the CPU‑A's *"Support Segmented OS"* jumper
must be set to **Yes**. MAME has no command‑line switch for a board jumper, so use one of:

- **UI:** press **Tab → Machine Configuration → "Support Segmented OS" → Yes**, or
- **Config file (non‑interactive):** drop a `cfg/s8000.cfg` next to MAME containing:

  ```xml
  <?xml version="1.0"?>
  <mameconfig version="10">
      <system name="s8000">
          <input>
              <port tag=":slot_cpu:cpu_a:SEGJP" type="CONFIG" mask="1" defvalue="0" value="1" />
          </input>
      </system>
  </mameconfig>
  ```

  (A copy is included in this repo as `s8000.cfg`.)

With the jumper still at the default **No**, ZEUS will not boot — the kernel runs into
the wrong MMU‑routing path and crashes shortly after enabling the MMU.

### Apply the interrupt fix (required)

With a stock build the kernel panics (`ID = 0 -- panic: Unexpected interrupt`) moments
after the scheduler starts: when the SMD disk interrupt is acknowledged, the ZBI bus
does not refresh the CPU's vectored‑interrupt line, so the Z8001 then takes a phantom
interrupt that no device owns. One line in `src/devices/bus/zbi/zbi.cpp`,
`zbi_bus_device::viack_r()`, fixes it — re‑evaluate the line after the acknowledge:

```cpp
uint16_t zbi_bus_device::viack_r()
{
    device_z80daisy_interface *intf = daisy_get_irq_device();
    uint16_t vec = intf ? intf->z80daisy_irq_ack() : 0;
    vi_w(CLEAR_LINE);   // <-- add: the ack changed the device's daisy state (INT -> IEO)
    return vec;
}
```

Rebuild the `s8000` target after applying it.

### Launch and boot

Attach the CHD to the first SMD drive and start the machine (the console is on the
CPU‑A's second serial channel):

```sh
mame s8000 -hard1 s8000_smd.chd
```

Because block 0 now holds a valid boot record, this **auto‑boots** — press the front‑panel
**START** (numeric‑keypad `+`) and the monitor loads the kernel by itself, no typing:

```
S8000 Monitor 3.0 - Press START to Load System
> stand/boot
Boot
: smd(0,15200)zeus        <- constructed automatically from block 0
```

(A manual boot also works if block 0 is absent — type `Z S`, then `boot`, then
`smd(0,15200)zeus` at the console.)

## Status

With segmented mode enabled and the interrupt fix applied, the kernel auto‑boots and
runs its full startup:

```
Zilog Zeus Kernel -- Release 3.21 -- Generated 03/21/86 00:23:11
System:SYS 8000   Node:ZEUS   Release:3.21   Version:SYS III
number of users = 16 ... kernel memory size = 238848 bytes
user memory size = 809728 bytes ... type of memory = parity ... default boot device = smd
```

After the banner the kernel mounts root and settles into its **idle loop with the
real‑time clock ticking** — i.e. it is up and scheduling, but no login prompt appears
yet. The remaining gap is `/dev`: the console/tty **char‑device major numbers** used to
rebuild `/dev/console` are not yet confirmed (the block‑device majors are), so `init`
has no working console to run a shell on. Pinning those down (from the ZEUS `cdevsw`
table) is the next step toward a `ZEUS login:` prompt.

The MAME `s8000` driver is still marked `MACHINE_NOT_WORKING`; the disk image itself is
sound — the kernel loads byte‑perfect from it and runs its entire startup off it.
