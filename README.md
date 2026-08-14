# Zilog System 8000 — bootable ZEUS 3.2.1 image for MAME

## Disk images

The repository provides two bootable ZEUS 3.2.1 (Zilog's System III Unix)
images for the Zilog System 8000 Model 31. The new
`build/zeus-3.21-tape-128-plzasm-games.chd` follows the recovered installation
tape flow, uses the tape's 128 MiB SMD layout, and adds the `plzasm` and games
packages plus the modern two-digit-year patch. The older
`filesystem/generated/s8000_smd.chd` remains available as the clean,
reconstructed development image.

Both perform the normal ZEUS multi-user startup. Point MAME at the desired CHD
as described in [Running](#running). Everything else in the repository is the
provenance trail and rebuild machinery for these images.

To run the original ZEUS installation-tape flow over a serial connection, see
the [serial installer guide](serial_installer/README.md).

### Images and passwords

There are two distinct image lines in this repository; do not interchange
their superuser passwords:

| Image | Description | Login | Password |
| --- | --- | --- | --- |
| `filesystem/generated/s8000_smd.chd` | Older clean/reconstructed image | `zeus` | `zeus` |
| `build/zeus-3.21-tape-128-plzasm-games.chd` | New 128 MiB install-tape image with `plzasm`, games, and the date patch | `zeus` | `jupiter` |

The new image retains the password hash restored from the ZEUS installation
tape. It also deliberately retains the tape's `vz console` entry; it does not
contain the temporary H19 terminal override used during diagnosis.

The SHA-256 of the committed new CHD is:

```text
e5d67c36d206caa548b3579c1aa04dc4811b75687e0e4ad3ef3e9032e407132b
```

The original archives used for the disk reconstruction are preserved under
`filesystem/originals/`. Generated tape images and their decoded contents are
kept separately under `tapes/`.

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
  Zilog *ZEUS System Administrator's Manual*, 03-3246-04,
  *System 8000 CPU Hardware Reference Manual*, 03-3200-01, and
  *System 8000 Hardware Reference Manual*,
  [03-3237-04](https://bitsavers.org/pdf/zilog/s8000/03-3237-04_hwRef_Dec82.pdf),
  whose section 5.9 documents the CPU monitor.

`S8000-2.tar` was obtained from the VCFed post linked above. It packages an
installed ZEUS tree and contains useful `.contents` inventories, as well as
installed-machine residue. The clean image is therefore generated from the
classified inventory in `inventory/`, not by copying every file found in the
archive or prepared host trees.

`0-dump-911118-root.backup` is a checksum-clean level-0 V7/System III dump of
the root filesystem from the same recovered machine. Files and device metadata
needed by the reconstruction are taken from it; its site-specific configuration
and software are not.

## Image contents

The authoritative uncompressed
`filesystem/generated/s8000_smd.chd` was rebuilt on 2026-08-11. Its SHA-256
is:

```text
b9a02009a8b6a0699beaab8246e0488e19fbe432625276a443afd9c714057265
```

The rebuilt filesystems match the staged manifest. The deliberate changes are
the relinked kernel, the documented `date`/`datem` Y2K patches, a sanitized
password file, and the H19 console mapping.

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
images are retained in `filesystem/generated/native_partitions/` and reused by
normal rebuilds.

### Filesystem checks and raw devices

The image contains the recovered ZEUS `/etc/fsck`, which passes all three
auxiliary filesystems.

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

Device nodes are defined by `devs.txt`. This image uses the SMD aliases
`/dev/root`, `/dev/usr`, `/dev/tmp`, and `/dev/z`; the recovered `zd`, tape, and
printer nodes refer to hardware not currently emulated by this machine.

## Running

Build current [mamedev/mame](https://github.com/mamedev/mame), or use an
official release containing merge commit `ab41620cf2d4`, and install the System
8000 ROMs. For CPU-A, enable the **Support Segmented OS** configuration jumper;
the included `s8000.cfg` sets this jumper.

The same `filesystem/generated/s8000_smd.chd` boots on both CPU boards. The
repository contains machine-specific `s8000.cfg` and `s8000s2.cfg` files. Pass
the repository to MAME with `-cfg_directory` so it loads the configuration
whose filename matches the selected machine. In particular, `s8000.cfg`
enables the CPU-A **Support Segmented OS** jumper required by ZEUS. MAME may
update the matching configuration file when it exits, so review or restore
that file if you change settings interactively.

Run CPU-A with the `s8000` machine:

```sh
./s8000 s8000 -rp roms \
  -cfg_directory /path/to/Zilog_S8000 \
  -hard1 /path/to/Zilog_S8000/filesystem/generated/s8000_smd.chd
```

When the MAME window opens, press numeric-keypad `+`, which is mapped to the
front-panel **START** key.

After shutting down CPU-A and exiting MAME, run HPCPU with the `s8000s2`
machine against the same image:

```sh
./s8000 s8000s2 -rp roms \
  -cfg_directory /path/to/Zilog_S8000 \
  -hard1 /path/to/Zilog_S8000/filesystem/generated/s8000_smd.chd
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

Current MAME provides an H19-compatible console for both machines.

Use `sync` before closing MAME. MAME normally stores disk writes in a
`diff/s8000*.dif` overlay; delete that overlay when you need to return to the
pristine committed image.

## Reverse-engineering notes

- [`MONITOR.md`](MONITOR.md) — CPU monitor commands and serial download mode.
- [`TCC.md`](TCC.md) — cartridge tape controller firmware and media format.
- [`tapes/INSTALL.md`](tapes/INSTALL.md) — decoded installation tape and the
  tape-derived 128 MiB SMD disk layout.
- [`STANDALONE.md`](STANDALONE.md) — stand-alone bootstrap chain.
- [`SERIAL-BOOT.md`](SERIAL-BOOT.md) — serial installation design notes.

## Rebuilding the clean image

The case-sensitive prepared source trees must be mounted at:

```text
/Volumes/ZeusFS/s8000_root
/Volumes/ZeusFS/s8000_usr
```

The installed init and relinked kernel are fixed rebuild inputs preserved in
`filesystem/generated/root_overlays/`. The build refuses to run unless they
match their recorded hashes. It also verifies and installs the recovered
`rc.sav`, `rc_csh`, `mfs`
(hard-linked as `umfs`), and Model 31 `inittab.s8000-2`. The exact relinked
kernel is `filesystem/generated/root_overlays/zeus-3.2.1-relinked`, and the
pristine init is
`filesystem/generated/root_overlays/init-pristine-1991-11-18`.

Run:

```sh
tools/retro-fuse/build-mkv7img.sh
tools/retro-fuse/build-mkdev.sh
./rebuild_fs.sh
```

The rebuild performs these steps:

1. `stage_clean_zeus.py` selects only base-distribution entries, confirmed
   common files missing from S8000-2, and the documented Model 31 overlay.
2. It overlays the pristine init, recovered startup/mount files, sanitized
   password and terminal configuration, and the relinked kernel.
3. It creates `/zeus` and `/zeus-3.2.1` as hard links.
4. `mkv7img` creates the root filesystem with its timestamp pinned to the
   authoritative image for byte-for-byte reproducibility. The saved native
   ZEUS `/usr`, `/tmp`, and `/z` partitions are copied into their documented
   offsets; the swap region remains freshly zeroed.
5. `mkdev` uses the same pinned timestamp, and `fix_dev_majors.py` corrects the
   major and minor numbers of all 68 device nodes.
6. `mkblock0.py` writes the autoboot, root/swap, and VFS configuration,
   including Monitor block-size code `1` for 512-byte CPU-A/HPCPU disk
   transfers.
7. `chdman` creates an uncompressed CHD.
8. The result is installed as `filesystem/generated/s8000_smd.chd`.

The pinned filesystem epoch is `1786449783` (2026-08-11 12:03:03 UTC), the
timestamp of the authoritative reconstructed image. Both `mkv7img` and
`mkdev` honor `SOURCE_DATE_EPOCH`; without pinning both operations, their V7
inode and superblock timestamps would make each rebuild different.

A successful full rebuild produces this final SHA-256 hash:

```text
b9a02009a8b6a0699beaab8246e0488e19fbe432625276a443afd9c714057265  filesystem/generated/s8000_smd.chd
```

Verify them with:

```sh
shasum -a 256 filesystem/generated/s8000_smd.chd
```

The staging trees live on `/Volumes/ZeusFS/clean-stage` because a normal
case-insensitive macOS filesystem cannot represent both `/etc/init` and
`/etc/INIT`.

Relevant files:

- `rebuild_fs.sh` — complete clean-image build;
- `stage_clean_zeus.py` — inventory filtering and init/kernel overlays;
- `inventory/` — recovered distribution classification;
- `devs.txt` — Model 31 and console device specification;
- `fix_dev_majors.py` — corrects the retro-fuse device-major encoding;
- `mkblock0.py` — writes the S8000 block-zero configuration;
- `tools/retro-fuse/src/v7adapt.c` — supplies the reproducible V7 filesystem
  clock from `SOURCE_DATE_EPOCH` when it is set.

## Model disk layouts

| Model | CPU | ZEUS | Controller | Disk layout |
| --- | --- | --- | --- | --- |
| 21 | CPU-A | Non-segmented | ZD | 29 MB |
| 31 | CPU-A | Non-segmented | SMD | 68 MB |
| 31 Plus | CPU-A | Segmented | SMD | 128 MB |
| 32 | HPCPU | Segmented | SMD | 128 MB |

The current CHD uses the 68 MB Model 31 layout with segmented ZEUS. A future
installation-tape build should use the 128 MB layout for Models 31 Plus and 32.
