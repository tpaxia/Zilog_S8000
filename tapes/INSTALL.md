# ZEUS 3.21 installation tape

The recovered installation tape can be studied and used to construct disks
without emulating the cartridge tape controller.  `build_tape_images.py`
validates the physical-capture CRCs and writes a SIMH image;
`extract_tape_images.py` then produces the logical tape files and expands the
archive contents on the host.

## Logical files

| File | Contents |
| ---: | --- |
| 0 | Primary bootstrap, 512 bytes |
| 1 | Secondary bootstrap |
| 2 | Standalone `sawbz`, the block-zero and disk-layout program |
| 3 | Standalone `mkfs` |
| 4 | Standalone `restor` |
| 5 | Level-0 root dump |
| 6 | Level-1 root overlay, based on file 5 |
| 7 | Level-0 `/usr` dump |
| 8 | Level-1 `/usr` overlay, based on file 7 |
| 9 | Accounting package (`tar`) |
| 10 | Global optimizer (`tar`) |
| 11 | `learn` package (`tar`) |
| 12 | SCCS and help package (`tar`) |
| 13 | Zmenu package (`tar`) |
| 14 | Volume-copy utilities (`tar`) |
| 15 | Assembler package (`tar`) |
| 16 | Games package (`tar`) |
| 17 | Crash utility (`tar`) |

The administration manual calls files 5–10 dump files, but the recovered
media shows that files 9 onward are tar archives.  Files 5–8 use the ZEUS
big-endian V7 dump format.

## The `sawbz` default layouts

Tape file 2 is a nonsegmented Z8000 `s.out` executable.  It retains symbols
for `_dflt_tbl`, `_dflt_sz`, and `_dflt_nam`.  The table contains seven
default layouts.  Each 40-byte record identifies a drive type and size key,
the block-zero root/swap/pipe configuration, and a row of sixteen partition
sizes.  `sawbz` calculates each partition offset by summing the sizes before
it.

Decode the table reproducibly with:

```sh
python3 tools/decode_sawbz.py
python3 tools/decode_sawbz.py --drive smd --size-key 128
```

The two SMD defaults are:

| Size key | `/usr` | swap | root | `/tmp` | `/z` | Total blocks |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 12,000 | 3,200 | 6,000 | 6,000 | 104,736 | 131,936 |
| 128 | 12,000 | 3,200 | 6,000 | 6,000 | 234,944 | 262,144 |

Both use the same cumulative offsets:

| Virtual disk | Name | Offset | 64-key size | 128-key size |
| ---: | --- | ---: | ---: | ---: |
| 0 | `/usr` | 0 | 12,000 | 12,000 |
| 1 | swap | 12,000 | 3,200 | 3,200 |
| 2 | root | 15,200 | 6,000 | 6,000 |
| 3 | `/tmp` | 21,200 | 6,000 | 6,000 |
| 4 | `/z` | 27,200 | 104,736 | 234,944 |

The 128-key layout therefore changes only the size and ending boundary of
`/z`.  Its 262,144 512-byte blocks are exactly 134,217,728 bytes (128 MiB).

## How `sawbz` selects an SMD layout

The SMD driver's `_sizing` routine issues controller command 15 (`SIZE`) and
records the returned sector, head, and cylinder counts.  `_smdcommand` then
computes:

```text
size key = cylinders * heads * sectors_per_track / 2048
```

There are 2,048 512-byte blocks in one MiB.  Integer division produces the
key compared with `_dflt_tbl`; the tape does not compare an exact geometry.

The exact Model 31 Plus geometry comes from Zilog
[Hardware Reference Manual 03-3237-06B](https://bitsavers.org/pdf/zilog/s8000/03-3237-06B_M21_M31hw_Apr84.pdf),
April 1984, Table 2-5 on printed page 2-6 (PDF page 40), "168M Byte Drive
Specifications and Characteristics":

| Characteristic | Value |
| --- | ---: |
| Formatted capacity | 134,217,728 bytes |
| Cylinders | 1,024 |
| Tracks/heads per cylinder | 8 |
| Active sectors per track | 32 |
| Spare sectors per track | 1 |
| Formatted track capacity | 16,384 bytes |

Thus the MAME-compatible CHD geometry is unambiguous:

```text
1024 cylinders * 8 heads * 32 active sectors * 512 bytes
    = 134,217,728 bytes
```

The period hardware documentation calls this a 168M-byte drive by its
unformatted capacity.  ZEUS and `sawbz` expose its formatted capacity as the
128-MiB size class.

## Replaying the installation flow on the host

`install_from_tape.py` constructs the disk from the recovered SIMH tape rather
than from the repository's reconstructed filesystem staging tree. It follows
the distribution's installation stages at the tape-record boundary:

1. Apply tape file 2's SMD 128 default, allocate 262,144 blocks, and write its
   block-zero VFS table.
2. Perform the file 3 `mkfs` stage for root and `/usr`, using the Model 31
   Plus interleave of 16 and 256 sectors per cylinder.
3. Perform the file 4 `sarestor` stage in tape order: root files 5 and 6,
   followed by `/usr` files 7 and 8.
4. Perform the installed `/etc/makenewfs` device-linking, labeling, and
   `/tmp`/`/z` creation, including its 318-slot `lost+found` reservation.
5. Create a CHD with geometry `1024,8,32` and 512-byte sectors.

Run it from the repository root:

```sh
python3 tapes/install_from_tape.py
```

The outputs are `build/zeus-3.21-tape-128.img` and
`build/zeus-3.21-tape-128.chd`. Existing outputs are not replaced unless
`--force` is given. Use `--no-chd` to produce only the raw image.

The host restore preserves dump contents, modes, ownership, device numbers,
timestamps, hard-link identity, and directory sizes. It does not preserve the
dump's numerical inode assignments or inode change times; neither is used to
locate files or boot ZEUS. Files 9–17 are optional packages and are not added
to the base installation. Select packages explicitly to produce a separate
image whose filename includes the packages in tape order. For example:

```sh
python3 tapes/install_from_tape.py --packages plzasm --patch-date
```

This writes `build/zeus-3.21-tape-128-plzasm.img` and `.chd` without altering
the base tape-flow outputs. Package files, modes, owners, groups, timestamps,
and hard links come from their tar records. Parent directories omitted by the
old tar format are created root-owned with mode 0755. The optional
`--patch-date` post-install step applies the documented, hash-guarded Y2K
compatibility patches to the tape's `/bin/date` and `/etc/datem` binaries.

## Applying the 3.21 update tape

`--stage-upgrade` writes the recovered upgrade tape into the new disk's `/z`
filesystem so that ZEUS can apply it with the vendor's own script. The update
is not applied host-side: its final steps run `ar` over `/lib/slibc.a` and
`/usr/sys/sys/LIB1`, and it ends with a kernel sysgen.

```sh
python3 tapes/install_from_tape.py --packages plzasm --patch-date --stage-upgrade
```

The staged tree is `/z/3.21.update` plus `/z/INSTALL`, taken from
`images/zeus-3.21-upgrade.tap`; `scc` is staged as a hard link to `cc`, as on
the tape. Boot the resulting CHD, log in as `zeus`, and run:

```text
cd /z
csh INSTALL
```

`INSTALL` is a csh script and performs its own `cd 3.21.update`. It moves the
staged files into `/lib`, `/bin`, `/usr/bin`, `/usr/lib`, `/usr/lib/me`, and
`/usr/sys`, saving the replaced originals under `/tmp/save`, then rebuilds the
two archives. Sysgen a new kernel and reboot to complete it.

The update needs roughly 470 free blocks on `/usr`, which has 12,000. The base
tape installation leaves 725 free; the `games` package consumes 504 of those, so
`games` and the update do not both fit in the tape's default `/usr` size. Root
is left with 91 free blocks after `plzasm`, which is enough because the update's
`/bin` replacements free more than its `/lib` replacements consume, and `/lib`
is processed first. `ar` writes its temporary files to `/tmp`.

Because `INSTALL` moves rather than copies, a failed run cannot be resumed:
rebuild the image and start again.

## Image credentials and local changes

The older clean image, `filesystem/generated/s8000_smd.chd`, has superuser
login `zeus` and password `zeus`. The new tape-derived
`build/zeus-3.21-tape-128-plzasm-upgrade.chd` has login `zeus` and password
`jupiter`, inherited from the password hash in tape file 5.

The new image installs only the `plzasm` optional package; it does not install
`games` or `crash`. Its `date` and `datem` programs have the optional modern
two-digit-year patch. `/etc/ttytype` remains byte-for-byte as restored from the
tape, including `vz console`; the temporary `h19 console` test change is not
part of this build. The 3.21 update was applied on the machine as described
above, followed by a sysgen, so `/zeus` is a relinked kernel rather than the
one restored from tape.

The committed CHD is created from the post-update disk with the same
`chdman createhd --chs 1024,8,32 --sectorsize 512 --compression none`
parameters as the build script, not from the file MAME writes while running.
Its SHA-256 is:

```text
d695bf43725f2911e6507cb6323c08c8604d46407463bd474fcbf8eacd3afc07
```

Tape-device emulation would reproduce the historical interactive installation
dialogue, but it is not required to execute the same media and filesystem flow.
