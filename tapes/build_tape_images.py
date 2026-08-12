#!/usr/bin/env python3
"""Build authoritative SIMH images from the recovered ZEUS tape sources."""

import re
import hashlib
import struct
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ORIGINALS = HERE / "originals"
IMAGES = HERE / "images"
INSTALL_SOURCE = ORIGINALS / "install-3.21" / "zeus-3.21-install-recovery.tar"
INSTALL_TAP = IMAGES / "zeus-3.21-install.tap"
UPGRADE_SOURCE = ORIGINALS / "upgrade-3.21" / "zeus-3.21-upgrade.tar"
UPGRADE_TAP = IMAGES / "zeus-3.21-upgrade.tap"
RECOVERED_USR = ORIGINALS / "install-3.21" / "S8000-2.tar"
SADIE_SOURCES = tuple(
    ORIGINALS / "sadie-3.5" / f"sadie-3.5-track{track}.tar.gz"
    for track in range(3)
)
SADIE_TAPS = tuple(IMAGES / f"sadie-3.5-track{track}.tap" for track in range(3))

NAME_RE = re.compile(r"_FILE_(\d+)_BLOCK_(\d+)_")
MAGIC = 60011
CHECKSUM = 84446 & 0xffff
TS_INODE = 2
EOM = 0xffffffff
REPAIR_HASHES = {
    "ftBC": "549fb48c786f59672cdfb25f6cc654aabdb22655a25f9c1877fe832a6a754568",
    "ftB": "c871545e0ca31fb98d18dbe9ab46f4bb2dad52a4f4cc203e336efeedbc05cf48",
    "man_contents": "16563a22c5422aeaa8ead77ca04b67269d0536f86f65a682eff52011fc6ca93d",
    "manM_contents": "8ad034b2a3d17ec98a2e748f77274200b857b243a30cc764a549608e201670df",
    "xq": "2f9cfabc23396606b47af36a86928717cd4152fca315f83f33ed434ba3096e99",
}


def dump_checksum(record):
    return sum(struct.unpack(">256H", record)) & 0xffff


def tcc_crc(data):
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x8005) & 0xffff if crc & 0x8000 else (crc << 1) & 0xffff
    return crc


def inode_header(tapea, inode, size, mode, uid, gid, timestamp, blocks):
    record = bytearray(512)
    struct.pack_into(">hIIhIHHH", record, 0,
                     TS_INODE, 469764657, 469763850, 1, tapea,
                     inode, MAGIC, 0)
    struct.pack_into(">HhhhI", record, 22, mode, 1, uid, gid, size)
    struct.pack_into(">III", record, 74, timestamp, timestamp, timestamp)
    struct.pack_into(">h", record, 86, 10)
    record[88:88 + min(blocks, 10)] = bytes([1]) * min(blocks, 10)
    struct.pack_into(">H", record, 20, (CHECKSUM - dump_checksum(record)) & 0xffff)
    assert dump_checksum(record) == CHECKSUM
    return bytes(record)


def file_blocks(data):
    return [data[offset:offset + 512].ljust(512, b"\0")
            for offset in range(0, len(data), 512)]


def load_repair_files():
    names = {
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


def reconstruct_block_169():
    files = load_repair_files()
    records = []
    records += file_blocks(files["ftBC"])
    records.append(inode_header(3381, 925, len(files["ftB"]), 0o100644, 3, 0, 469764374, 1))
    records += file_blocks(files["ftB"])
    records.append(inode_header(3383, 927, len(files["man_contents"]), 0o100664, 3, 0, 469764520, 1))
    records += file_blocks(files["man_contents"])
    records.append(inode_header(3385, 928, len(files["manM_contents"]), 0o100664, 3, 0, 469764583, 4))
    records += file_blocks(files["manM_contents"])
    records.append(inode_header(3390, 929, len(files["xq"]), 0o100644, 5, 0, 469764372, 10))
    records += file_blocks(files["xq"])[:9]
    assert len(records) == 20
    return b"".join(records)


def read_install_records():
    grouped = {}
    crc_failures = []
    with tarfile.open(INSTALL_SOURCE) as archive:
        for member in archive:
            match = NAME_RE.search(member.name)
            if not match:
                continue
            file_no, block_no = map(int, match.groups())
            raw = archive.extractfile(member).read()
            encoded_length = (len(raw) - 1).to_bytes(2, "big")
            if tcc_crc(encoded_length + raw):
                crc_failures.append((file_no, block_no))
            if "FILEMARK" in member.name:
                continue
            payload = raw[:-2]
            if file_no == 8 and block_no == 169:
                payload = reconstruct_block_169()
            grouped.setdefault(file_no, []).append((block_no, payload))
    if crc_failures != [(8, 169)]:
        raise ValueError(f"unexpected TCC CRC failures: {crc_failures}")
    return {file_no: sorted(records) for file_no, records in grouped.items()}


def read_sadie_records(source):
    grouped = {}
    crc_failures = []
    with tarfile.open(source) as archive:
        for member in archive:
            match = NAME_RE.search(member.name)
            if not match:
                continue
            file_no, block_no = map(int, match.groups())
            raw = archive.extractfile(member).read()
            encoded_length = (len(raw) - 1).to_bytes(2, "big")
            if tcc_crc(encoded_length + raw):
                crc_failures.append((file_no, block_no))
            if "FILEMARK" in member.name:
                continue
            grouped.setdefault(file_no, []).append((block_no, raw[:-2]))
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
    for source, destination in zip(SADIE_SOURCES, SADIE_TAPS):
        grouped = read_sadie_records(source)
        write_tap(destination,
                  [[payload for _, payload in grouped[file_no]]
                   for file_no in sorted(grouped)])


def main():
    build_install()
    build_upgrade()
    build_sadie()
    print(f"wrote {INSTALL_TAP}")
    print(f"wrote {UPGRADE_TAP}")
    for path in SADIE_TAPS:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
