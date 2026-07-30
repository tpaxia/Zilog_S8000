# Zilog System 8000 — bootable ZEUS 3.2.1 image for MAME

This repository contains `s8000_smd.chd`, a clean, bootable ZEUS 3.2.1
(Zilog's System III Unix) disk image for the Zilog System 8000 Model 31.
It performs the normal ZEUS multi-user startup and reaches `ZEUS login:`.
The image includes the recovered ZEUS development system, including the C
compilers and the relinked kernel.

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

The committed image was rebuilt on 2026-07-30. Its SHA-256 is:

```text
8e75be052e41692100948f48d4353cd3a5a221f7e44221e9ac10391c88ea5d75
```

The raw filesystems were read back and compared with the staged manifest:

- root: 251 paths, with no missing or extra entries;
- `/usr`: 868 paths, with no missing or extra entries;
- 30 required character/block device nodes, with corrected on-disk majors;
- `/zeus` and `/zeus-3.2.1` are the same inode, with link count 2;
- `/etc/init` and `/etc/INIT` are the same fixed-init inode;
- the installed `ls`, `libc.a`, init, and kernel hashes match their selected
  source files.

`/etc/init` is the one rebuilt executable in the installed userland. It was
compiled on ZEUS with the recovered Zilog non-segmented C toolchain from the
source reconstruction in `systemIII/init.c`. That reconstruction begins with
the AT&T System III process-management core and restores the Zilog-specific
behavior recovered from disassembly of the stripped ZEUS 3.21 binary:

- the initial `HOME`, `PATH`, `TERM`, `SHELL`, and `LOGNAME` environment;
- console terminal-type lookup through `/etc/ttytype`;
- initial multi-user state selection from the executable name;
- the ZEUS console-process handling during a state 1-to-2 transition;
- the ZEUS run-state signal handling.

It also naturally omits the corrupt second allocator call found in the
recovered binary. The rebuilt init runs the normal `/etc/rc`, reads
`/etc/inittab`, and reaches the normal multi-user login service; it does not
bypass startup with a hard-coded shell. `/etc/init` and `/etc/INIT` are hard
links to this rebuilt executable. See `systemIII/README.md` for the
source-to-disassembly evidence.

All other installed userland executables, including `/etc/fsck`, `getty`,
`login`, the shell, and both C compilers, are original recovered ZEUS binaries.
The kernel is relinked from the original ZEUS objects, and the narrowly scoped
`date`/`datem` Y2K byte patches are documented below. The startup, mount,
password, and terminal configuration files are reconstructed installation
configuration rather than executable replacements.

The kernel is the relinked `zeus` produced in `/usr/sys/conf`. Only the boot
copies `/zeus` and `/zeus-3.2.1` are installed; the build artifact
`/usr/sys/conf/zeus` is not included in the clean distribution image.

The clean build excludes cores, temporary compiler files, test sources,
instrumented binaries, `.pre-s8000-2` backups, renamed `.noboot` files, previous
kernel copies, AppleDouble files, and other unclassified installed-snapshot
residue.

The shipped `datem` accepted only years 70 through 99, and `date` interpreted
all two-digit years as 19xx. During the clean rebuild, `patch_date_y2k.py`
changes the interactive check to accept 00 through 99 and makes `date`
interpret 00 through 69 as 2000 through 2069. The signed 32-bit ZEUS time
format still imposes the normal January 2038 limit.

## Disk layout

The CHD is an uncompressed 589×7×32 disk with 512-byte sectors:

| Region | Start block | Blocks | Purpose |
|---|---:|---:|---|
| `/usr` | 0 | 12,000 | ZEUS `/usr` filesystem |
| swap | 12,000 | 3,200 | ZEUS swap area |
| root | 15,200 | 6,000 | ZEUS root filesystem |
| `/tmp` | 21,200 | 6,000 | Temporary filesystem |
| `/z` | 27,200 | 104,736 | Development and user-work filesystem |

Total logical size: 131,936 blocks, or 67,551,232 bytes.

Block zero contains:

- magic `0xDEADBABE`;
- root device `8,2`, swap device `8,1`, pipe device `8,2`;
- root offset 15,200;
- VFS records for `/usr`, swap, root, `/tmp`, and `/z`.

The complete Model 31 device overlay includes `root`, `usr`, `tmp`, and `z`
aliases plus the corresponding raw SMD devices.  This is the default Model 31
layout documented in Table 4-1 of the ZEUS System Administrator Manual.
`/tmp` and `/z` are initialized as separate empty filesystems with
preallocated `lost+found` directories. The `/usr`, `/tmp`, and `/z`
filesystems were created by native ZEUS `mkfs`; their pristine partition
images are retained in `native_partitions/` and reused by normal rebuilds.

### Filesystem checks and raw devices

The image contains the original 1984 ZEUS `/etc/fsck`, not the separately
rebuilt System III checker used during diagnosis. The original checker passes
all three pristine auxiliary filesystems and reports:

- `/usr`: 869 files, 9,557 blocks, 1,961 free;
- `/tmp`: 3 files, 11 blocks, 5,747 free;
- `/z`: 3 files, 11 blocks, 100,534 free.

Under the current MAME S8000 emulation, large reads through the raw SMD
character devices (`/dev/rusr`, `/dev/rtmp`, and `/dev/rz`) return incorrect
data. `fsck` then falsely reports allocated inodes as unallocated and can
damage a filesystem if run with `-y`. The same checker works correctly through
the buffered block devices. The production `rc_csh` therefore checks
`/dev/usr`, `/dev/tmp`, and `/dev/z` while they are unmounted. Until the raw
SMD transfer bug is fixed, do not run a repairing check on an `r*` device;
use `fsck -n` for experiments and use the corresponding block device for real
checks.

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
monitor to load `smd(0,15200)zeus`; init checks the unmounted auxiliary
filesystems, prompts for the date, mounts `/z`, `/tmp`, and `/usr`, and enters
multi-user mode:

```text
Zilog Zeus Kernel -- Release 3.21
...
ZEUS login:
```

The superuser account is `zeus` with password `zeus`.

MAME's built-in S8000 terminal is usable but not a perfect emulation of the
terminal expected by ZEUS. The first login banner can be visually mangled, and
full-screen programs such as `vi` may not redraw perfectly. Pressing Return
normally produces a clean `ZEUS login:` prompt. For more faithful cursor,
screen, and keyboard behavior, connect an H19/Heath-compatible terminal
emulator to the S8000 console instead. An experimental MAME H19-console branch
can also be maintained on top of the `s8000` branch without changing MAME's
global terminal default.

Use `sync` before closing MAME. MAME normally stores disk writes in a
`diff/s8000*.dif` overlay; delete that overlay when you need to return to the
pristine committed image.

## Rebuilding the clean image

The case-sensitive prepared source trees must be mounted at:

```text
/Volumes/ZeusFS/s8000_root
/Volumes/ZeusFS/s8000_usr
```

The rebuilt init is taken from `build/init.corrected-rebuilt`; its reconstructed
source is `systemIII/init.c`. The relinked kernel is taken from
`s8000_usr/sys/conf/zeus`.

Run:

```sh
./rebuild_fs.sh
```

The rebuild performs these steps:

1. `stage_clean_zeus.py` selects only base-distribution entries, confirmed
   common files missing from S8000-2, and the documented Model 31 overlay.
2. It overlays the current fixed init and relinked kernel.
3. It creates `/zeus` and `/zeus-3.2.1` as hard links.
4. `mkv7img` creates the root filesystem. The saved native ZEUS `/usr`,
   `/tmp`, and `/z` partitions are copied into their documented offsets; the
   swap region remains freshly zeroed.
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
