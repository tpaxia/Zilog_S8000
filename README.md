# Zilog System 8000 — ZEUS 3.2.1 for MAME

This repository contains recovered ZEUS media, bootable System 8000 disk
images, and three working image-production pipelines. The recommended image is
the 128 MiB disk installed from the recovered tape through the serial installer
in MAME, then updated inside ZEUS.

## Images

| Image | Build path | Login | Password | SHA-256 |
| --- | --- | --- | --- | --- |
| `build/zeus-3.21-serial-128-plzasm-upgrade.chd` | Serial tape install in MAME, `plzasm` and date patch staged on the host, vendor update and sysgen run in ZEUS | `zeus` | `jupiter` | `6144ed1482bc12237f7ec8a1c680c6a87526bd411345e496391e2473538309fb` |
| `build/zeus-3.21-tape-128-plzasm-upgrade.chd` | Tape records replayed by host scripts, vendor update and sysgen run in ZEUS | `zeus` | `jupiter` | `d695bf43725f2911e6507cb6323c08c8604d46407463bd474fcbf8eacd3afc07` |
| `filesystem/generated/s8000_smd.chd` | Reconstructed from recovered tar archives and classified filesystem inventories | `zeus` | `zeus` | `b9a02009a8b6a0699beaab8246e0488e19fbe432625276a443afd9c714057265` |

The pristine serial-installed base is
`build/zeus-3.21-serial-install-128.chd`, SHA-256
`62cbadfd9eda3efe47f2e24770a22b7eea330000592d450fd1882af21c480415`.

### Model disk layouts

| Model | CPU | ZEUS mode | Controller | Disk layout |
| --- | --- | --- | --- | --- |
| 21 | CPU-A | Non-segmented | ZD | 29 MB |
| 31 | CPU-A | Non-segmented | SMD | 68 MB |
| 31 Plus | CPU-A | Segmented | SMD | 128 MB |
| 32 | HPCPU | Segmented | SMD | 128 MB |

The reconstructed filesystem image uses the 68 MB SMD layout. Both
tape-derived pipelines use the 128 MB Model 31 Plus layout. The recovered
partition tables, CHD geometry, and `sawbz` selection logic are documented in
[tapes/INSTALL.md](tapes/INSTALL.md#the-sawbz-default-layouts).

## Running an image

Use current MAME containing the System 8000 fixes merged in
[mamedev/mame PR #15866](https://github.com/mamedev/mame/pull/15866), at or
after merge commit
[`ab41620cf2d4`](https://github.com/mamedev/mame/commit/ab41620cf2d4bace0497922b03cb48e1d5169b50).
The included `s8000.cfg` enables CPU-A's **Support Segmented OS** jumper.

```sh
./s8000 s8000 -rp roms \
  -cfg_directory /path/to/Zilog_S8000 \
  -hard1 /path/to/Zilog_S8000/build/zeus-3.21-serial-128-plzasm-upgrade.chd
```

Press numeric-keypad `+` for the front-panel **START** key. ZEUS loads
`smd(0,15200)zeus`, checks and mounts its filesystems, asks for the date, and
enters multi-user mode.

The CHD is writable. Keep a pristine copy, do not attach it to two MAME
instances simultaneously, and run `sync` followed by `/etc/halt` before
exiting MAME.

## Image-production pipelines

### 1. Reconstruct from tar archives

This pipeline creates the older 68 MiB clean development image from recovered
filesystem archives and the classified release inventory. It uses the tracked
startup files in `image-config/`, fixed kernel/init overlays, native ZEUS
partition templates, and the local retro-fuse tools.

Detailed inputs and provenance:

- [filesystem/README.md](filesystem/README.md)
- [inventory/README.md](inventory/README.md)
- [native partition templates](filesystem/generated/native_partitions/README.md)

Build from the repository root:

```sh
tools/retro-fuse/build-mkv7img.sh
tools/retro-fuse/build-mkdev.sh
./rebuild_fs.sh
```

`rebuild_fs.sh` expects its case-sensitive prepared source trees under
`/Volumes/ZeusFS` and writes `filesystem/generated/s8000_smd.chd`.

### 2. Build from tape with host scripts

This pipeline validates the recovered tape, converts it to SIMH TAP format,
replays the tape's layout, `mkfs`, restore, package, and `makenewfs` stages on
the host, and creates a 128 MiB CHD.

```sh
python3 tapes/build_tape_images.py
python3 tapes/extract_tape_images.py
python3 tapes/install_from_tape.py \
  --packages plzasm --patch-date --stage-upgrade
```

The command stages the 3.21 update under `/z`; the vendor `INSTALL` script and
kernel sysgen are then run inside ZEUS. See:

- [tape media and extraction](tapes/README.md)
- [host tape-flow installation](tapes/INSTALL.md)

### 3. Install from tape over serial

This pipeline executes the recovered tape's `sawbz`, `mkfs`, and `sarestor`
programs in MAME. Cartridge reads are replaced with a checked serial protocol
over TTY0; the operator console remains in the MAME window.

Build the serial loader and create a blank 128 MiB disk:

```sh
cd serial_installer
make test
cd ..
chdman createhd \
  -o build/zeus-3.21-serial-install-128.chd \
  --chs 1024,8,32 --sectorsize 512 -c none
```

Run the tape server and MAME as documented in
[serial_installer/README.md](serial_installer/README.md), then follow the
original `ct(0,2)`, `ct(0,3)`, and `ct(0,4)` installation sequence. After the
base install and clean shutdown, extract it and stage the post-install material
on a copy:

```sh
chdman extractraw \
  -i build/zeus-3.21-serial-install-128.chd \
  -o build/zeus-3.21-serial-install-128.img
python3 tapes/stage_existing_install.py \
  build/zeus-3.21-serial-install-128.img \
  build/zeus-3.21-serial-128-plzasm-upgrade-staged.img \
  --packages plzasm --patch-date --stage-upgrade
chdman createhd \
  -i build/zeus-3.21-serial-128-plzasm-upgrade-staged.img \
  -o build/zeus-3.21-serial-128-plzasm-upgrade-staged.chd \
  --chs 1024,8,32 --sectorsize 512 --compression none
```

Move any old `diff/s8000.dif` aside and boot the staged CHD. Inside ZEUS, apply
the vendor update, rebuild and install the Model 31 Plus kernel, remove the
update staging files and backups, and halt cleanly:

```text
cd /z
csh INSTALL
cd /usr/sys/conf
/etc/sysgen -d 31P
rm /zeus /zeus2_3.21
mv zeus /zeus
ln /zeus /zeus2_3.21
rm -rf /tmp/save /z/INSTALL /z/3.21.update
sync
/etc/halt
```

After MAME exits, merge its child CHD with the staged parent and create the
standalone final image:

```sh
chdman extractraw \
  -i diff/s8000.dif \
  -ip build/zeus-3.21-serial-128-plzasm-upgrade-staged.chd \
  -o build/zeus-3.21-serial-128-plzasm-upgrade.img
chdman createhd \
  -i build/zeus-3.21-serial-128-plzasm-upgrade.img \
  -o build/zeus-3.21-serial-128-plzasm-upgrade.chd \
  --chs 1024,8,32 --sectorsize 512 --compression none
shasum -a 256 build/zeus-3.21-serial-128-plzasm-upgrade.chd
```

## Technical documentation

- [ZEUS tape contents and disk layout](tapes/INSTALL.md)
- [Serial tape installer](serial_installer/README.md)
- [SADIE 3.5 serial diagnostics](sadie_serial/README.md)
- [CPU-A monitor](MONITOR.md)
- [Annotated monitor disassembly](re/monitor/README.md)
- [Cartridge tape controller and media format](TCC.md)
- [Standalone bootstrap and filesystem tools](STANDALONE.md)
- [Z8000 reverse-engineering tools](tools/zdis/README.md)

## Sources and credits

- System 8000 driver and Z8000/Z8010 devices:
  [tpaxia/mame](https://github.com/tpaxia/mame) and upstream MAME.
- Original System 8000 work and ROM collection:
  [ArcLight22/S8000-roms](https://github.com/ArcLight22/S8000-roms).
- Big-endian V7 filesystem implementation:
  [ArcLight22/retro-fuse](https://github.com/ArcLight22/retro-fuse), with local
  System 8000 extensions.
- ZEUS archives: <http://www.pofo.de/S8000/misc/harddisk_images/>.
- Period documentation: Zilog *ZEUS System Administrator's Manual* 03-3246-04
  and the System 8000 hardware reference manuals preserved by
  [Bitsavers](https://bitsavers.org/pdf/zilog/s8000/).
