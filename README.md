# Zilog System 8000 — bootable ZEUS 3.2.1 image for MAME

This repository contains `s8000_smd.chd`, a clean, bootable ZEUS 3.2.1
(Zilog's System III Unix) disk image for the Zilog System 8000 Model 31.
It boots directly to an interactive root `#` prompt and includes the recovered
ZEUS development system, including the C compilers and the relinked kernel.

The image is a reconstruction from the recovered S8000-2 installed tree, the
older ZEUS archives, and the file inventories in the ZEUS System
Administrator's Manual. It is not a dump of an untouched physical disk.

## Important: official MAME is not sufficient

The fixes required to run this image are **not in official
[mamedev/mame](https://github.com/mamedev/mame) yet**. Use the System 8000 work
in the [tpaxia MAME fork](https://github.com/tpaxia/mame), branch
[`s8000`](https://github.com/tpaxia/mame/tree/s8000). This branch is based on
the CPU-only [`z8000_fixes`](https://github.com/tpaxia/mame/tree/z8000_fixes)
branch.

The tested fork contains two relevant commits:

- `e4ee708355b` — tip of the CPU-only Z8000 fixes used by this branch.
- `ce73a233b7a` — System 8000 clock, console, Z8010 MMU, interrupt, and SMD
  device handling.

In particular, ZEUS requires behavior that stock MAME currently lacks:

- correct disabled-EPU trapping for the `0x4f` instruction family;
- preservation of an indexed operand when `LDA`'s destination pair overlaps
  the index register;
- the Z8010 violation/instruction-address low bytes supplied by the CPU card;
- side-effect-free debugger reads through the Z8010;
- the CPU card's 1.2288 MHz real-time-clock input, producing the ZEUS 60 Hz
  system tick;
- console modem-line loopback so `/dev/console` has carrier;
- vectored-interrupt-line reevaluation after interrupt acknowledge;
- correct READY reporting for populated versus empty SMD units.

Using official MAME can cause boot hangs, phantom interrupts, MMU faults,
missing console input, compiler crashes, or kernel panics.

## Sources and credits

- System 8000 driver and Z8000/Z8010 devices:
  [tpaxia/mame](https://github.com/tpaxia/mame) and upstream MAME.
- Original System 8000 work and ROM collection:
  [ArcLight22/S8000-roms](https://github.com/ArcLight22/S8000-roms).
- Big-endian V7 filesystem implementation:
  [ArcLight22/retro-fuse](https://github.com/ArcLight22/retro-fuse), with local
  write-path, device-node, and hard-link helpers.
- ZEUS archives:
  <http://www.pofo.de/S8000/misc/harddisk_images/>.
- `S8000-2.tar`:
  [VCFed forum post in “Zilog System 8000 Model 21”](https://forum.vcfed.org/index.php?threads/zilog-system-8000-model-21.1255068/page-2#post-1511810).
- Hardware and installation details:
  Zilog *ZEUS System Administrator's Manual*, 03-3246-04, and
  *System 8000 CPU Hardware Reference Manual*, 03-3200-01.

`S8000-2.tar` was obtained from the VCFed post linked above. It packages an
installed ZEUS tree and contains useful `.contents` inventories, as well as
installed-machine residue. The clean image is therefore generated from the
classified inventory in `inventory/`, not by copying every file found in the
archive or prepared host trees.

## Image contents

The committed image was rebuilt on 2026-07-26. Its SHA-256 is:

```text
f7462ff894cc2998bdb28d8278087282087818fd07f3eb136f8549e5742d15dc
```

The raw filesystems were read back and compared with the staged manifest:

- root: 251 paths, with no missing or extra entries;
- `/usr`: 868 paths, with no missing or extra entries;
- 30 required character/block device nodes, with corrected on-disk majors;
- `/zeus` and `/zeus-3.2.1` are the same inode, with link count 2;
- `/etc/init` and `/etc/INIT` are the same fixed-init inode;
- the installed `ls`, `libc.a`, init, and kernel hashes match their selected
  source files.

The fixed init directly execs an interactive shell on `/dev/console`, producing
the `#` prompt. The original distribution `/etc/rc` and `/etc/inittab` are
present under their canonical names but are intentionally bypassed.

The kernel is the relinked `zeus` produced in `/usr/sys/conf`. Only the boot
copies `/zeus` and `/zeus-3.2.1` are installed; the build artifact
`/usr/sys/conf/zeus` is not included in the clean distribution image.

The clean build excludes cores, temporary compiler files, test sources,
instrumented binaries, `.pre-s8000-2` backups, renamed `.noboot` files, previous
kernel copies, AppleDouble files, and other unclassified installed-snapshot
residue.

## Disk layout

The CHD is an uncompressed 589×7×32 disk with 512-byte sectors:

| Region | Start block | Blocks | Purpose |
|---|---:|---:|---|
| `/usr` | 0 | 15,000 | ZEUS `/usr` filesystem |
| root | 15,200 | 100,000 | ZEUS root filesystem |
| swap | 115,200 | 16,736 | ZEUS swap area |

Total logical size: 131,936 blocks, or 67,551,232 bytes.

Block zero contains:

- magic `0xDEADBABE`;
- root device `8,2`, swap device `8,1`, pipe device `8,2`;
- root offset 15,200;
- VFS records for `/usr`, swap, and root.

The complete Model 31 device overlay includes `root`, `usr`, `tmp`, and `z`
aliases plus the corresponding raw SMD devices. `/tmp` itself is a directory
on the enlarged root filesystem; the historical `/dev/tmp` and `/dev/z` nodes
remain available for compatibility.

## Running

Build the `s8000` branch of
[tpaxia/mame](https://github.com/tpaxia/mame), install the System 8000 ROMs,
and enable the CPU-A **Support Segmented OS** configuration jumper. The
included `s8000.cfg` sets this jumper.

Launch:

```sh
./s8000 -rp roms s8000 -hard1 /path/to/Zilog_S8000/s8000_smd.chd
```

Press the front-panel START key (numeric keypad `+`). Block zero causes the
monitor to load `smd(0,15200)zeus`; the fixed init then opens the root shell:

```text
Zilog Zeus Kernel -- Release 3.21
...
#
```

Use `sync` before closing MAME. MAME normally stores disk writes in a
`diff/s8000*.dif` overlay; delete that overlay when you need to return to the
pristine committed image.

## Rebuilding the clean image

The case-sensitive prepared source trees must be mounted at:

```text
/Volumes/ZeusFS/s8000_root
/Volumes/ZeusFS/s8000_usr
```

The current fixed init is taken from `s8000_root/etc/init`; the relinked kernel
is taken from `s8000_usr/sys/conf/zeus`.

Run:

```sh
./rebuild_fs.sh
```

The rebuild performs these steps:

1. `stage_clean_zeus.py` selects only base-distribution entries, confirmed
   common files missing from S8000-2, and the documented Model 31 overlay.
2. It overlays the current fixed init and relinked kernel.
3. It creates `/zeus` and `/zeus-3.2.1` as hard links.
4. `mkv7img` creates fresh big-endian V7 filesystems.
5. `mkdev` and `fix_dev_majors.py` create and correct the Model 31 devices.
6. `mkblock0.py` writes the autoboot, root/swap, and VFS configuration.
7. `chdman` creates an uncompressed CHD.
8. The result is installed as both `s8000_smd.chd` and
   `debug/s8000.chd`.

The staging trees live on `/Volumes/ZeusFS/clean-stage` because a normal
case-insensitive macOS filesystem cannot represent both `/etc/init` and
`/etc/INIT`.

Relevant files:

- `rebuild_fs.sh` — complete clean-image build;
- `stage_clean_zeus.py` — inventory filtering and init/kernel overlays;
- `inventory/` — recovered distribution classification;
- `devs.txt` — Model 31 and console device specification;
- `fix_dev_majors.py` — corrects the retro-fuse device-major encoding;
- `mkblock0.py` — writes the S8000 block-zero configuration.
