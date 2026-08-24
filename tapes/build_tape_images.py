#!/usr/bin/env python3
"""Build authoritative SIMH images from the recovered ZEUS tape sources."""

import re
import hashlib
import struct
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
FILESYSTEM_ORIGINALS = HERE.parent / "filesystem" / "originals"
ORIGINALS = HERE / "originals"
IMAGES = HERE / "images"
INSTALL_SOURCE = ORIGINALS / "install-3.21" / "zeus-3.21-install-download.gz"
BLOCK_169 = ORIGINALS / "install-3.21" / "zeus-3.21-install-file8-block169.bin"
INSTALL_TAP = IMAGES / "zeus-3.21-install.tap"
UPGRADE_SOURCE = FILESYSTEM_ORIGINALS / "zeus-3.21-upgrade.tar"
UPGRADE_TAP = IMAGES / "zeus-3.21-upgrade.tap"
RECOVERED_USR = FILESYSTEM_ORIGINALS / "S8000-2.tar"
SADIE_SOURCE = ORIGINALS / "sadie-3.5" / "sadie-3.5-all-tracks.tar.gz"
SADIE_TAP = IMAGES / "sadie-3.5.tap"

NAME_RE = re.compile(r"_FILE_(\d+)_BLOCK_(\d+)_")
CRC_RE = re.compile(r"_CRC_([0-9A-F]{4})_")
TRACK_RE = re.compile(r"TRK(\d+)")
MAGIC = 60011
CHECKSUM = 84446 & 0xffff
TS_INODE = 2
EOM = 0xffffffff
PRIVATE_MARKER = 0x70000000
REPAIR_HASHES = {
    "boot": "9064564f79f97580fb1e3f517da3cb8fa529e07d31c904b64f8c4f3c401e320e",
    "ftBC": "549fb48c786f59672cdfb25f6cc654aabdb22655a25f9c1877fe832a6a754568",
    "ftB": "c871545e0ca31fb98d18dbe9ab46f4bb2dad52a4f4cc203e336efeedbc05cf48",
    "man_contents": "16563a22c5422aeaa8ead77ca04b67269d0536f86f65a682eff52011fc6ca93d",
    "manM_contents": "8ad034b2a3d17ec98a2e748f77274200b857b243a30cc764a549608e201670df",
    "xq": "2f9cfabc23396606b47af36a86928717cd4152fca315f83f33ed434ba3096e99",
}
FILE_1_HASH = "1c038e3d0f640e0fade2b842fd6b221a3742666033e43b643b837e3779cf7d2c"
FILE_1_RECORDS = 45
TAPE_RECORD_SIZE = 512
TAPE_BLOCK_SIZE = 10240
BLOCK_169_HASH = "dbebce3cae7a171e1a925cd1ca761a83b4425eee92ab47a672044b2a37e9de5a"
# Which 512-byte records of block 169 hold which recovered file's contents,
# as (first record, file, first block of that file, number of blocks).  The
# records not listed here are the four dump inode headers.
BLOCK_169_LAYOUT = (
    (0, "ftBC", 0, 1),
    (2, "ftB", 0, 1),
    (4, "man_contents", 0, 1),
    (6, "manM_contents", 0, 4),
    (11, "xq", 0, 9),
)
BLOCK_169_INODES = (1, 3, 5, 10)


def dump_checksum(record):
    return sum(struct.unpack(">256H", record)) & 0xffff


def tcc_crc(data):
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x8005) & 0xffff if crc & 0x8000 else (crc << 1) & 0xffff
    return crc


def file_blocks(data):
    return [data[offset:offset + 512].ljust(512, b"\0")
            for offset in range(0, len(data), 512)]


def load_repair_files():
    names = {
        "boot": "usr/boot",
        "ftBC": "usr/lib/font/ftBC",
        "ftB": "usr/lib/font/ftB",
        "man_contents": "usr/man/.contents",
        "manM_contents": "usr/man/manM/.contents",
        "xq": "usr/man/manM/xq.M",
    }
    if not RECOVERED_USR.is_file():
        raise FileNotFoundError(f"independent recovered /usr archive not found: {RECOVERED_USR}")
    with tarfile.open(RECOVERED_USR) as archive:
        files = {key: archive.extractfile(name).read() for key, name in names.items()}
    for key, data in files.items():
        actual = hashlib.sha256(data).hexdigest()
        if actual != REPAIR_HASHES[key]:
            raise ValueError(f"unexpected recovered file hash for {key}: {actual}")
    return files


def verify_file_1(records):
    """Check the raw secondary loader against the independent /usr/boot copy."""
    block_numbers = [number for number, _ in records]
    if block_numbers != list(range(FILE_1_RECORDS)) or any(
            len(payload) != TAPE_RECORD_SIZE for _, payload in records):
        raise ValueError("unexpected recovered layout for installation tape file 1")

    loader = b"".join(payload for _, payload in records)
    actual = hashlib.sha256(loader).hexdigest()
    if actual != FILE_1_HASH:
        raise ValueError(f"unexpected recovered file 1 hash: {actual}")

    boot = load_repair_files()["boot"]
    magic, image_size, _, segment_table_size = struct.unpack(">HIIH", boot[:12])
    header_size = 24 + segment_table_size
    if magic != 0xe707 or image_size != 0x58da or header_size != 40:
        raise ValueError("independent /usr/boot has an unexpected s.out layout")
    image = boot[header_size:header_size + image_size]
    if len(boot) != header_size + image_size:
        raise ValueError("independent /usr/boot has unexpected trailing data")

    padded = image.ljust(
        (len(image) + TAPE_RECORD_SIZE - 1) // TAPE_RECORD_SIZE * TAPE_RECORD_SIZE,
        b"\0",
    )
    if loader != padded:
        raise ValueError("recovered file 1 does not match the independent /usr/boot")


def load_block_169():
    """Return the original install tape file 8, block 169.

    The block-level capture of this block is short -- 3,583 bytes of 10,240 --
    and fails its TCC CRC, so earlier builds synthesised it from independently
    recovered files.  This is the real block, and it is strictly better: its
    four dump inode headers carry valid dump checksums, the recorded access
    times, and the inode disk address arrays that a synthesised header cannot
    know.  Its file contents are identical to the recovered files, which is
    still checked here rather than assumed.
    """
    block = BLOCK_169.read_bytes()
    if len(block) != TAPE_BLOCK_SIZE:
        raise ValueError(f"block 169 is {len(block)} bytes, expected {TAPE_BLOCK_SIZE}")
    actual = hashlib.sha256(block).hexdigest()
    if actual != BLOCK_169_HASH:
        raise ValueError(f"unexpected block 169 hash: {actual}")

    records = [block[offset:offset + TAPE_RECORD_SIZE]
               for offset in range(0, len(block), TAPE_RECORD_SIZE)]
    files = load_repair_files()
    for first, key, start, count in BLOCK_169_LAYOUT:
        expected = file_blocks(files[key])[start:start + count]
        if records[first:first + count] != expected:
            raise ValueError(f"block 169 disagrees with the recovered {key}")
    for index in BLOCK_169_INODES:
        record = records[index]
        kind, = struct.unpack_from(">h", record, 0)
        magic, = struct.unpack_from(">H", record, 18)
        if kind != TS_INODE or magic != MAGIC or dump_checksum(record) != CHECKSUM:
            raise ValueError(f"block 169 record {index} is not a valid inode header")
    return block


def read_install_records():
    """Read the block capture, whose members hold the payload without its CRC."""
    grouped = {}
    crc_failures = []
    with tarfile.open(INSTALL_SOURCE) as archive:
        for member in archive:
            match = NAME_RE.search(member.name)
            if not match:
                continue
            file_no, block_no = map(int, match.groups())
            payload = archive.extractfile(member).read()
            crc = CRC_RE.search(member.name)
            if not crc:
                raise ValueError(f"captured block without a CRC: {member.name}")
            encoded_length = (len(payload) + 1).to_bytes(2, "big")
            if tcc_crc(encoded_length + payload + bytes.fromhex(crc.group(1))):
                crc_failures.append((file_no, block_no))
            if "FILEMARK" in member.name:
                continue
            if file_no == 8 and block_no == 169:
                payload = load_block_169()
            grouped.setdefault(file_no, []).append((block_no, payload))
    if sorted(crc_failures) != [(8, 169)]:
        raise ValueError(f"unexpected TCC CRC failures: {sorted(crc_failures)}")
    verify_file_1(sorted(grouped[1]))
    return {file_no: sorted(records) for file_no, records in grouped.items()}


def read_sadie_records(source, track):
    grouped = {}
    crc_failures = []
    with tarfile.open(source) as archive:
        for member in archive:
            track_match = TRACK_RE.search(member.name)
            match = NAME_RE.search(member.name)
            if not track_match or int(track_match.group(1)) != track or not match:
                continue
            file_no, block_no = map(int, match.groups())
            payload = archive.extractfile(member).read()
            crc = CRC_RE.search(member.name)
            if not crc:
                raise ValueError(f"captured SADIE block without a CRC: {member.name}")
            encoded_length = (len(payload) + 1).to_bytes(2, "big")
            if tcc_crc(encoded_length + payload + bytes.fromhex(crc.group(1))):
                crc_failures.append((file_no, block_no))
            if "FILEMARK" in member.name:
                continue
            grouped.setdefault(file_no, []).append((block_no, payload))
    if crc_failures:
        raise ValueError(f"SADIE CRC failures in {source}: {crc_failures}")
    file_numbers = sorted(grouped)
    if file_numbers != list(range(len(file_numbers))):
        raise ValueError(f"non-contiguous SADIE file numbers in {source}: {file_numbers}")
    return {file_no: sorted(records) for file_no, records in grouped.items()}


def write_record(output, payload):
    marker = struct.pack("<I", len(payload))
    output.write(marker)
    output.write(payload)
    if len(payload) & 1:
        output.write(b"\0")
    output.write(marker)


def write_tap(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as output:
        for records in files:
            for payload in records:
                write_record(output, payload)
            output.write(struct.pack("<I", 0))
        output.write(struct.pack("<I", EOM))


def build_install():
    grouped = read_install_records()
    write_tap(INSTALL_TAP,
              [[payload for _, payload in grouped[file_no]]
               for file_no in sorted(grouped)])


def build_upgrade():
    data = UPGRADE_SOURCE.read_bytes()
    if len(data) % 10_240:
        raise ValueError("upgrade tar is not an integral number of 10,240-byte blocks")
    records = [data[offset:offset + 10_240]
               for offset in range(0, len(data), 10_240)]
    write_tap(UPGRADE_TAP, [records])


def build_sadie():
    SADIE_TAP.parent.mkdir(parents=True, exist_ok=True)
    with SADIE_TAP.open("wb") as output:
        for track in range(3):
            output.write(struct.pack("<I", PRIVATE_MARKER | track))
            grouped = read_sadie_records(SADIE_SOURCE, track)
            for file_no in sorted(grouped):
                for _, payload in grouped[file_no]:
                    write_record(output, payload)
                output.write(struct.pack("<I", 0))
        output.write(struct.pack("<I", EOM))


def main():
    build_install()
    build_upgrade()
    build_sadie()
    print(f"wrote {INSTALL_TAP}")
    print(f"wrote {UPGRADE_TAP}")
    print(f"wrote {SADIE_TAP}")


if __name__ == "__main__":
    main()
