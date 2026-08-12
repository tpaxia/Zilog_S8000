# Zilog System 8000 — bootable ZEUS 3.2.1 image for MAME

## Use `s8000_smd.chd`

**`s8000_smd.chd` is the deliverable.** It is a clean, bootable ZEUS 3.2.1
(Zilog's System III Unix) disk image for the Zilog System 8000 Model 31. It
performs the normal ZEUS multi-user startup and reaches `ZEUS login:`, and it
includes the recovered ZEUS development system with the C compilers and the
relinked kernel. Download that one file, point MAME at it (see
[Running](#running)), and you are done.

**Everything else in this repository exists only to reproduce that file.** The
build script, staging tools, inventories, recovered binaries, partition seeds
and configuration sources are the provenance trail and the rebuild path. You do
not need any of them to run ZEUS, and you should not need to run
`rebuild_fs.sh` unless you are changing what goes into the image.

The image is a reconstruction from the recovered S8000-2 installed tree, the
older ZEUS archives, a pristine 1991-11-18 level-0 root dump, and the file
inventories in the ZEUS System Administrator's Manual. It is not a dump of an
untouched physical disk.

## MAME version required

The CPU, MMU, and System 8000 corrections required to run this image were
merged into [mamedev/mame](https://github.com/mamedev/mame) by
[PR #15866](https://github.com/mamedev/mame/pull/15866) on 2026-08-12. Build
upstream MAME at or after merge commit
[`ab41620cf2d4`](https://github.com/mamedev/mame/commit/ab41620cf2d4bace0497922b03cb48e1d5169b50),
or use an official MAME release that contains that commit. Older releases do
not contain the complete fixes.

ZEUS depends on the merged changes for:

- correct disabled-EPU trapping for the `0x4f` instruction family;
- preservation of an indexed operand when `LDA`'s destination pair overlaps
  the index register;
- the Z8010 violation/instruction-address low bytes supplied by the CPU card;
- side-effect-free debugger reads through the Z8010;
- the CPU card's 1.2288 MHz real-time-clock input, producing the ZEUS 60 Hz
  system tick;
- console modem-line loopback so `/dev/console` has carrier;
- vectored-interrupt-line reevaluation after interrupt acknowledge;
- ZBI vectored-interrupt-line reevaluation after hardware RETI, so an HPCPU
  CIO interrupt cannot leave a lower-priority SMD disk interrupt hidden;
- correct READY reporting for populated versus empty SMD units;
- complete multi-sector SMD DMA rather than silently truncating a request to
  its first 512-byte sector.

Using a MAME version from before the merge can cause boot hangs, phantom
interrupts, MMU faults, missing console input, compiler crashes, or kernel
panics.

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
- `0-dump-911118-root.backup`, a level-0 `dump` of a live S8000 root
  filesystem taken 1991-11-18:
  <https://drive.google.com/file/d/1cgpqKmj1a6vdj1PsfsX_Nna7iOSctdRk/view>.
- Hardware and installation details:
  Zilog *ZEUS System Administrator's Manual*, 03-3246-04, and
  *System 8000 CPU Hardware Reference Manual*, 03-3200-01.

`S8000-2.tar` was obtained from the VCFed post linked above. It packages an
installed ZEUS tree and contains useful `.contents` inventories, as well as
installed-machine residue. The clean image is therefore generated from the
classified inventory in `inventory/`, not by copying every file found in the
archive or prepared host trees.

`0-dump-911118-root.backup` is a complete, checksum-clean level-0 V7/System III
`dump` of the **root** filesystem only — it contains no `/usr` and no `/z`. All
432 of its record headers pass checksum, and it restores to 282 paths. It is
the same physical machine as the recovered tree used elsewhere here, about
eleven months later: the staged `/etc/termcap` is byte-identical to the dump's
own pre-edit backup `/etc/termcapo`. Two things are taken from it: the pristine
`/etc/init` and the 38 additional device nodes. Its site-specific
configuration, its 1991 netnews and mail software, and its `zd`-configured
kernel are not used, because they belong to that installation rather than to
the Zilog distribution this image reconstructs.

## Image contents

The image was rebuilt on 2026-08-11. Its SHA-256 is:

```text
b9a02009a8b6a0699beaab8246e0488e19fbe432625276a443afd9c714057265
```

The raw filesystems were read back and compared with the staged manifest:

- root: 265 inodes reachable, with no missing or extra entries;
- `/usr`: 868 paths, with no missing or extra entries;
- 68 character/block device nodes, each verified on the raw image for type,
  major and minor;
- `/zeus` and `/zeus-3.2.1` are the same inode, with link count 2;
- `/etc/init` and `/etc/INIT` are the same inode, with link count 2, and their
  on-disk bytes hash to the pristine init below;
- the installed `ls`, `libc.a`, init, and kernel hashes match their selected
  source files.

### `/etc/init` is the original Zilog binary

`/etc/init` is the **original stripped ZEUS 3.21 executable**, 11,980 bytes,
SHA-256 `7a683ba63c8439398b2cd076dbc7ef08c6efc49f00ad1e55b9bc1a5749c6971a`,
recovered from a pristine 1991-11-18 level-0 `dump` of a real S8000 root
filesystem. `/etc/init` and `/etc/INIT` are hard links to it.

Earlier builds could not use the original. The only copy then available,
`archive/INIT.zeus-3.21-original`, has a corrupt 512-byte sector: nine bytes
differ from the pristine binary at file offsets 0x220c–0x23ee, seven of them
single-bit flips, all inside the region 0x2200–0x23FF. The `s.out` header and
segment table are undamaged, which is why nothing caught it structurally. Those
builds instead installed a source reconstruction, compiled on ZEUS from
`systemIII/init.c`.

The dump independently confirms that reconstruction work: the byte the project
had derived by disassembly and patched at 0x220c (`0x35` → `0x25`) is exactly
what the pristine binary contains, and the `f464` → `0004` pair at 0x2284 is
the corrupt allocator call described in `systemIII/README.md`. The
reconstruction's source and evidence are retained for that reason; the
compiled artifact is not, since it is no longer installed.

With the original restored, **every executable in the installed userland is an
original recovered ZEUS binary**, including `/etc/init`, `/etc/fsck`, `getty`,
`login`, the shell, and both C compilers.
The kernel is relinked from the original ZEUS objects, and the narrowly scoped
`date`/`datem` Y2K byte patches are documented below. The installed `rc`,
`rc_csh`, `mfs`/`umfs`, and Model 31 `inittab` are original recovered files.
The sanitized password file and H19 terminal mapping are reconstructed
installation configuration rather than executable replacements.

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
- Monitor block-size code `1` (512-byte blocks) at offset `0x04`; CPU-A accepts
  this value, and HPCPU Monitor 10.1 requires it rather than the former zero
  value;
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

The earlier raw-device `fsck` failures and low-memory swap corruption had the
same emulation cause: the SMDC packet byte count (`CT`) is the size of the
whole request, but MAME treated every value above 512 as invalid, replaced it
with 512, and reported the truncated operation as complete. Commit
`8d7158bbe1a` processes the full request sector by sector. A 1 MiB regression
run now swaps successfully and completes a ZEUS kernel link that previously
ended in `panic: kernel segmentation violation`.

The production `rc_csh` still checks the buffered devices `/dev/usr`,
`/dev/tmp`, and `/dev/z` while they are unmounted; this matches the tested boot
configuration and avoids changing the disk image solely because the emulator
bug was repaired. As with any historical filesystem, use `fsck -n` first when
experimenting with a raw device or a modified image.

### Device nodes

`/dev` holds 68 nodes, specified by `devs.txt` and verified on the raw image.
Thirty are the Model 31 working set: `console`, `tty0`–`tty7`, `tty`, `mem`,
`kmem`, `null`, the SMD disks (`smd*` block major 8, `rsmd*` char major 2), and
the partition aliases `root`, `swap`, `usr`, `tmp`, `z` and their raw forms.
These are the only nodes the boot path opens.

The remaining 38 were recovered from the same pristine 1991-11-18 root dump as
`/etc/init`, with the major and minor numbers exactly as recorded in that
machine's on-disk inodes: cartridge tape (`ct0*`, `nct0*`, `rct0*`, `nrct0*`,
major 1, with `+128` minors for the no-rewind variants), six line printers
(`lp*`, major 9), the default archive devices `tardev`, `dumpdev` and `resdev`
that `tar`, `dump` and `restor` fall back to, and the `zd*`/`rzd*` disk names.

Two caveats:

- The S8000 MAME machine emulates no cartridge tape and no printer, so those
  nodes open with an error. They are present for fidelity and so the archive
  tools find their default paths.
- **Do not use the `zd*`/`rzd*` nodes.** The dump machine reached its disks
  through the `zd` driver (block major 0, raw char major 32); this image is
  SMD. They name the same partitions but route through a controller that is not
  emulated. Use `/dev/root`, `/dev/usr`, `/dev/tmp` and `/dev/z` instead.

The dump carried `rct0`, `dumpdev` and `resdev` as hard links to `tardev`'s
inode, and `zd1` as a link to `swap`. `mkdev` has no link support, so they are
created as separate inodes with identical major/minor, which the kernel treats
identically.

## Running

Build current [mamedev/mame](https://github.com/mamedev/mame), or use an
official release containing merge commit `ab41620cf2d4`, and install the System
8000 ROMs. For CPU-A, enable the **Support Segmented OS** configuration jumper;
the included `s8000.cfg` sets this jumper.

The same `s8000_smd.chd` boots on both CPU boards. The repository contains
machine-specific `s8000.cfg` and `s8000s2.cfg` files. Pass the repository to
MAME with `-cfg_directory` so it loads the configuration whose filename
matches the selected machine. In particular, `s8000.cfg` enables the CPU-A
**Support Segmented OS** jumper required by ZEUS. MAME may update the matching
configuration file when it exits, so review or restore that file if you change
settings interactively.

Run CPU-A with the `s8000` machine:

```sh
./s8000 s8000 -rp roms \
  -cfg_directory /path/to/Zilog_S8000 \
  -hard1 /path/to/Zilog_S8000/s8000_smd.chd
```

When the MAME window opens, press numeric-keypad `+`, which is mapped to the
front-panel **START** key.

After shutting down CPU-A and exiting MAME, run HPCPU with the `s8000s2`
machine against the same image:

```sh
./s8000 s8000s2 -rp roms \
  -cfg_directory /path/to/Zilog_S8000 \
  -hard1 /path/to/Zilog_S8000/s8000_smd.chd
```

When the MAME window opens, press numeric-keypad `+` to press the HPCPU
front-panel **START** key.

Do not open the writable CHD in both machines simultaneously. Block zero
causes either monitor to load `smd(0,15200)zeus`; init checks the unmounted
auxiliary filesystems, prompts for the date, mounts `/z`, `/tmp`, and `/usr`,
and enters multi-user mode:

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
can also be maintained on top of current upstream MAME without changing MAME's
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

The installed init is the pristine original `build/init.pristine-911118`; the
build refuses to run unless it hashes to the value recorded above. The
superseded reconstruction survives only as source, in `systemIII/init.c`.
The build also verifies and installs the recovered `rc.sav`, `rc_csh`, `mfs`
(hard-linked as `umfs`), and Model 31 `inittab.s8000-2`. The relinked kernel is
taken from `s8000_usr/sys/conf/zeus`.

Run:

```sh
./rebuild_fs.sh
```

The rebuild performs these steps:

1. `stage_clean_zeus.py` selects only base-distribution entries, confirmed
   common files missing from S8000-2, and the documented Model 31 overlay.
2. It overlays the pristine init, recovered startup/mount files, sanitized
   password and terminal configuration, and the relinked kernel.
3. It creates `/zeus` and `/zeus-3.2.1` as hard links.
4. `mkv7img` creates the root filesystem. The saved native ZEUS `/usr`,
   `/tmp`, and `/z` partitions are copied into their documented offsets; the
   swap region remains freshly zeroed.
5. `mkdev` and `fix_dev_majors.py` create and correct all 68 device nodes.
6. `mkblock0.py` writes the autoboot, root/swap, and VFS configuration,
   including Monitor block-size code `1` for 512-byte CPU-A/HPCPU disk
   transfers.
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
