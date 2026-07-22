# Zilog System 8000 — bootable ZEUS 3.21 disk image for MAME

This repository contains a ready‑to‑use hard‑disk image (`s8000_smd.chd`) that boots
**ZEUS 3.21** (Zilog's Unix, SYS III) on the **Zilog System 8000** in
[MAME](https://www.mamedev.org/), together with notes on how the image was produced
and how to run it.

The image reproduces a genuine System 8000 SMD system disk (Model 31/32, CPU‑A with
Monitor / BIOS v3.0). Booting it in MAME brings the kernel all the way up through its
own initialization (memory sizing, scheduler, etc.); see **Status** below.

## Credits & upstream sources

This work stands entirely on the S8000 preservation work of **A. Lenard (ArcLight22)**:

- **MAME System 8000 driver & Z‑Bus/CPU/MMU devices** — <https://github.com/ArcLight22/mame>
  (also upstreamed into mainline MAME; driver `src/mame/zilog/s8k.cpp`).
- **MAME ROMs** — <https://github.com/ArcLight22/S8000-roms>
  (mirrored/compiled from pofo.de, bitsavers, and the Uni‑Stuttgart computer museum).
- **retro-fuse (big‑endian / ZEUS‑capable fork)** — <https://github.com/ArcLight22/retro-fuse>

The extracted ZEUS filesystem archives (`s8000_root.tar.gz`, `s8000_usr.tar.gz`,
`s8000_z.tar.gz`) come from **<https://github.com/tpaxia/P8000>**.

Hardware / layout facts below are taken from the Zilog *ZEUS System Administrator's
Manual* (03‑3246‑04, Oct 1983) and the *System 8000 CPU Hardware Reference Manual*
(03‑3200‑01, Sep 1982), both on bitsavers.

## Producing the disk image

### 1. Build the filesystem writer

ZEUS is a big‑endian Version‑7 Unix. The image is written with a tiny non‑FUSE helper
(`mkv7img`) built on top of ArcLight22's big‑endian **retro-fuse** fork. A couple of
small fixes were needed in that code to make the *write* path usable (a file‑create
bug, and reconstruction of hard links that `tar` had flattened); those details are out
of scope here — see the retro-fuse fork.

### 2. Lay out the disk and populate the filesystems

The System 8000 SMD system disk holds two ZEUS filesystems at fixed block offsets, per
the ZEUS Administrator's Manual (§3.3–3.4, Table 3‑2). All sizes are in **512‑byte
blocks**:

| Filesystem | Device        | Offset (blocks) | Size (blocks) | Size |
|------------|---------------|-----------------|---------------|------|
| `/usr`     | `smd(0,0)`    | 0               | 12000         | ~6 MB |
| *(swap)*   | —             | 12000           | 3200          | ~1.6 MB |
| `/` (root) | `smd(0,15200)`| 15200           | 6000          | ~3 MB |

Free‑list interleave for this drive is **m=16, n=224** (again from Table 3‑2).

The two filesystems are created empty at those offsets, then the extracted ZEUS trees
are copied in — i.e. `s8000_usr.tar.gz` is unpacked into the `/usr` filesystem and
`s8000_root.tar.gz` into the root filesystem. (Hard links such as the two kernel names,
`sh`/`rsh`, `od`/`hd`, etc. are restored during the copy, which lets the root tree fit
the authentic 6000‑block partition.)

### 3. Wrap the raw image in a CHD reproducing the physical drive

The System 8000 SMD controller (SMDC) in MAME expects a hard disk whose CHS geometry
matches the real drive, because ZEUS's disk driver and the controller both translate
between logical block numbers and cylinder/head/sector. The system disk is a
**Fujitsu M2312K**‑class 8" SMD drive:

```
cylinders = 589
heads     =   7
sectors   =  32     (512 bytes each)
------------------------------------
589 × 7 × 32 = 131936 blocks = 67,551,232 bytes  (~67.5 MB)
```

That total exactly matches the 131936‑block "logical size" the manual lists for this
drive, and the CHS split (heads × sectors = 224) matches the driver's blocks‑per‑cylinder.

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

### Launch and boot

Attach the CHD to the first SMD drive and start the machine (the console is on the
CPU‑A's second serial channel):

```sh
mame s8000 -hard1 s8000_smd.chd
```

At the console, do a manual boot (Model 31 / SMD): the primary bootstrapper loads the
secondary bootstrapper from the first filesystem, which in turn loads the kernel from
the root filesystem at block 15200:

```
S8000 Monitor 3.0 - Press START to Load System
Z S                     <- boot from Storage-Module Disk
boot                    <- load secondary bootstrapper from the first filesystem
smd(0,15200)zeus        <- load the kernel /zeus from the root filesystem @ offset 15200
```

## Status

With segmented mode enabled, the kernel loads and initializes:

```
Zilog Zeus Kernel -- Release 3.21 -- Generated 03/21/86 00:23:11
System:SYS 8000   Node:ZEUS   Release:3.21   Version:SYS III
number of users = 16 ... kernel memory size = 238848 bytes
user memory size = 809728 bytes ... type of memory = parity ... default boot device = smd
...
ID = 0 -- panic: Unexpected interrupt
```

It currently panics on an *Unexpected interrupt* during scheduler start‑up — an open
gap in the emulator's vectored‑interrupt handling (the MAME `s8000` driver is marked
`MACHINE_NOT_WORKING`). The disk image itself is sound: the kernel loads byte‑perfect
from it and runs its entire startup sequence off it.
