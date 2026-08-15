#!/usr/bin/env python3
"""Extract the authoritative ZEUS 3.21 SIMH install and upgrade tapes."""

import hashlib
import shutil
import struct
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "filesystem" / "tools"))

import read_dump


IMAGES = HERE / "images"
EXTRACTED = HERE / "extracted"
INSTALL_TAP = IMAGES / "zeus-3.21-install.tap"
UPGRADE_TAP = IMAGES / "zeus-3.21-upgrade.tap"
SADIE_TAP = IMAGES / "sadie-3.5.tap"
OUTPUT = EXTRACTED / "install-3.21"
UPGRADE_OUTPUT = EXTRACTED / "upgrade-3.21"
SADIE_OUTPUT = EXTRACTED / "sadie-3.5"
PRIVATE_MARKER = 0x70000000

# SADIE command numbers are two greater than the corresponding track-1 tape
# file number.  File 35 is not a command: FPPMON/FPPWHET load it as FPP
# control-store data.
SADIE_DIAGNOSTICS = {
    0: "MDCFMT",
    1: "MDCMEDIA",
    2: "MDCTEST",
    3: "MDCMON",
    4: "MDCCRC",
    5: "SMDFMT",
    6: "SMDMEDIA",
    7: "SMDTEST",
    8: "SMDMON",
    9: "SMDCRC",
    10: "WDCFMT",
    11: "WDCMEDIA",
    12: "WDCTEST",
    13: "WDCMON",
    14: "WDCCRC",
    15: "TCUMON",
    16: "TCOM",
    17: "TEX",
    18: "CIOTST",
    19: "SCCTST",
    20: "CACHETST",
    21: "MEMTEST",
    22: "MMUTST",
    23: "CENT.PRT",
    24: "SIOTEST",
    25: "SIOMODEM",
    26: "ECCTEST",
    27: "MTCMON",
    28: "MTCOM",
    29: "ICPTST1",
    30: "ICPTST2",
    31: "ICPTST3",
    32: "ICPTST4",
    33: "FPPTST",
    34: "FPPMON",
    36: "FPPWHET",
}
SADIE_SUPPORT_FILES = {35: "FPP-U-CODE"}


def read_tap(path):
    data = path.read_bytes()
    files, records = [], []
    offset = 0
    while offset + 4 <= len(data):
        marker = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if marker == 0xffffffff:
            break
        if marker == 0:
            files.append(records)
            records = []
            continue
        if marker & 0xf0000000:
            raise ValueError(f"unsupported SIMH marker {marker:08x} at {offset - 4:#x}")
        length = marker
        end = offset + length
        payload = data[offset:end]
        if len(payload) != length:
            raise ValueError("truncated SIMH record")
        offset = end + (length & 1)
        if offset + 4 > len(data) or struct.unpack_from("<I", data, offset)[0] != marker:
            raise ValueError("mismatched trailing SIMH record length")
        offset += 4
        records.append(payload)
    if records:
        raise ValueError("unterminated SIMH tape file")
    return files


def read_sadie_tap(path):
    data = path.read_bytes()
    tracks = {}
    files, records = [], []
    current_track = None
    offset = 0
    while offset + 4 <= len(data):
        marker = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if marker == 0xffffffff:
            if current_track is None:
                raise ValueError("SADIE tape has no track markers")
            if records:
                raise ValueError("unterminated SADIE tape file")
            tracks[current_track] = files
            break
        if marker & 0xf0000000 == PRIVATE_MARKER:
            if records:
                raise ValueError("SADIE track marker inside a tape file")
            if current_track is not None:
                tracks[current_track] = files
            current_track = marker & 0x0fffffff
            if current_track in tracks:
                raise ValueError(f"duplicate SADIE track {current_track}")
            files = []
            continue
        if current_track is None:
            raise ValueError(f"SADIE data before first track marker at {offset - 4:#x}")
        if marker == 0:
            files.append(records)
            records = []
            continue
        if marker & 0xf0000000:
            raise ValueError(f"unsupported SIMH marker {marker:08x} at {offset - 4:#x}")
        length = marker
        end = offset + length
        payload = data[offset:end]
        if len(payload) != length:
            raise ValueError("truncated SIMH record")
        offset = end + (length & 1)
        if offset + 4 > len(data) or struct.unpack_from("<I", data, offset)[0] != marker:
            raise ValueError("mismatched trailing SIMH record length")
        offset += 4
        records.append(payload)
    expected = list(range(len(tracks)))
    if sorted(tracks) != expected:
        raise ValueError(f"non-contiguous SADIE tracks: {sorted(tracks)}")
    return tracks


def logical_suffix(file_no):
    if file_no < 5:
        return ".bin"
    if file_no < 9:
        return ".dump"
    return ".tar"


def write_logical_files(files, root, install=True, suffix=None):
    logical = root / "logical"
    logical.mkdir(parents=True, exist_ok=True)
    paths = {}
    for file_no, records in enumerate(files):
        file_suffix = logical_suffix(file_no) if install else suffix
        destination = logical / f"file-{file_no:03d}{file_suffix}"
        with destination.open("wb") as output:
            for payload in records:
                output.write(payload)
        paths[file_no] = destination
    return paths


def extract_sadie_diagnostics(logical):
    """Give SADIE's track-1 flat images stable diagnostic names."""
    root = SADIE_OUTPUT / "tests"
    root.mkdir(parents=True, exist_ok=True)
    manifest = ["command\ttrack\tfile\tname\tkind\tsize\tsha256"]

    expected = set(SADIE_DIAGNOSTICS) | set(SADIE_SUPPORT_FILES)
    if set(logical) != expected:
        raise ValueError(
            f"unexpected SADIE track-1 files: got {sorted(logical)}, "
            f"expected {sorted(expected)}"
        )

    for file_no, source in logical.items():
        if file_no in SADIE_DIAGNOSTICS:
            name = SADIE_DIAGNOSTICS[file_no]
            command = file_no + 2
            kind = "diagnostic"
            destination = root / f"test-{command:02d}-{name}.bin"
            command_field = str(command)
        else:
            name = SADIE_SUPPORT_FILES[file_no]
            kind = "support"
            destination = root / f"support-{name}.bin"
            command_field = "-"

        payload = source.read_bytes()
        destination.write_bytes(payload)
        manifest.append(
            f"{command_field}\t1\t{file_no}\t{name}\t{kind}\t{len(payload)}\t"
            f"{hashlib.sha256(payload).hexdigest()}"
        )

    (root / "manifest.tsv").write_text("\n".join(manifest) + "\n")
    (root / "README.md").write_text(
        "# Extracted SADIE diagnostics\n\n"
        "These are exact, named copies of the logical files on SADIE track 1. "
        "They are flat standalone images, not `s.out` files. SADIE command "
        "numbers are two greater than the track-1 file number; for example, "
        "command/test 24 loads track 1 file 22, `MMUTST`.\n\n"
        "`support-FPP-U-CODE.bin` is control-store data used by the floating-"
        "point diagnostics and is not itself a menu command. `manifest.tsv` "
        "records every mapping, size, and SHA-256 digest. Regenerate this "
        "directory with `python3 tapes/extract_tape_images.py`.\n"
    )


def load_dump(records):
    tape = {}
    for block_no, payload in enumerate(records):
        if len(payload) != 10_240:
            raise ValueError(f"dump block {block_no} has length {len(payload)}")
        for record in range(20):
            tape[block_no * 20 + record] = payload[record * 512:(record + 1) * 512]
    return tape


def extract_dump(file_no, records):
    tape = load_dump(records)
    _, inodes, blocks, _, _, orphans = read_dump.parse(tape)
    read_dump.adopt_orphans(inodes, blocks, orphans)
    paths = read_dump.build_paths(inodes, blocks, root="/")
    root = OUTPUT / "files" / f"file-{file_no:03d}"
    count = 0
    for inode, metadata in inodes.items():
        if metadata["mode"] & read_dump.IFMT != read_dump.IFREG or not metadata["size"]:
            continue
        relative = paths.get(inode, f"_unnamed/ino{inode:05d}").lstrip("/")
        destination = root / relative
        if root.resolve() not in destination.resolve().parents:
            raise ValueError(f"unsafe dump path: {relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(read_dump.filedata(inode, inodes, blocks))
        count += 1
    return count


def extract_tar(file_no, path, output_root=OUTPUT):
    root = output_root / "files" / f"file-{file_no:03d}"
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        resolved_root = root.resolve()
        for member in members:
            destination = (root / member.name).resolve()
            if destination != resolved_root and resolved_root not in destination.parents:
                raise ValueError(f"unsafe tar path: {member.name}")
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.isfile() or member.islnk() or member.issym():
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists() or destination.is_symlink():
                    destination.unlink()
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f"cannot read tar member: {member.name}")
                with source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
        return sum(member.isfile() or member.islnk() or member.issym() for member in members)


def decode_install():
    files = read_tap(INSTALL_TAP)
    logical = write_logical_files(files, OUTPUT)
    for file_no in range(5, 9):
        print(f"file {file_no}: extracted {extract_dump(file_no, files[file_no])} dump files")
    for file_no in range(9, 18):
        print(f"file {file_no}: extracted {extract_tar(file_no, logical[file_no])} tar files")


def decode_upgrade():
    files = read_tap(UPGRADE_TAP)
    if len(files) != 1:
        raise ValueError(f"upgrade tape contains {len(files)} files, expected one")
    logical = write_logical_files(files, UPGRADE_OUTPUT, install=False, suffix=".tar")
    print(f"upgrade: extracted {extract_tar(0, logical[0], UPGRADE_OUTPUT)} tar files")


def decode_sadie():
    for track, files in read_sadie_tap(SADIE_TAP).items():
        root = SADIE_OUTPUT / f"track-{track}"
        logical = write_logical_files(files, root, install=False, suffix=".bin")
        if track == 1:
            extract_sadie_diagnostics(logical)
        records = sum(len(file_records) for file_records in files)
        print(f"SADIE track {track}: wrote {len(files)} logical files from {records} records")


def main():
    for path in (INSTALL_TAP, UPGRADE_TAP, SADIE_TAP):
        if not path.is_file():
            sys.exit(f"authoritative tape image not found: {path}")
    for path in (OUTPUT, UPGRADE_OUTPUT, SADIE_OUTPUT):
        if path.exists():
            shutil.rmtree(path)
    decode_install()
    decode_upgrade()
    decode_sadie()


if __name__ == "__main__":
    main()
