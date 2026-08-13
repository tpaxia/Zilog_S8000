#!/usr/bin/env python3
"""Decode the built-in disk layouts in the ZEUS install tape's sawbz."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


# Avoid leaving __pycache__ in the source tree when this reporting tool runs.
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "zdis"))

from sout import SOut  # noqa: E402


DEFAULT_BINARY = ROOT / "tapes/extracted/install-3.21/logical/file-002.bin"
DEFAULT_RECORD = struct.Struct(">HHIHIIHIHHHHHHI")
PARTITION_COUNT = 16


@dataclass(frozen=True)
class Partition:
    number: int
    name: str
    offset_blocks: int
    size_blocks: int


@dataclass(frozen=True)
class Layout:
    drive: str
    size_key_mib: int
    boot_fs_type: int
    boot_drive: int
    boot_offset: int
    root_fs_type: int
    root_drive: int
    root_offset: int
    root_device_major: int
    root_device_minor: int
    swap_device_major: int
    swap_device_minor: int
    pipe_device_major: int
    pipe_device_minor: int
    swap_size: int
    partitions: tuple[Partition, ...]

    @property
    def total_blocks(self) -> int:
        return sum(partition.size_blocks for partition in self.partitions)


def symbol_address(obj: SOut, name: str) -> int:
    matches = [symbol.value & 0xFFFF for symbol in obj.symbols if symbol.name == name]
    if len(matches) != 1:
        raise ValueError(f"expected one {name} symbol, found {len(matches)}")
    return matches[0]


def cstring(image: bytes, address: int) -> str:
    end = image.find(b"\0", address)
    if end < 0:
        raise ValueError(f"unterminated string at {address:#x}")
    return image[address:end].decode("ascii")


def decode(path: Path) -> list[Layout]:
    obj = SOut(str(path))
    image = obj.image
    table_address = symbol_address(obj, "_dflt_tbl")
    sizes_address = symbol_address(obj, "_dflt_sz")
    names_address = symbol_address(obj, "_dflt_nam")

    first_name_address = struct.unpack_from(">H", image, table_address)[0]
    table_bytes = first_name_address - table_address
    if table_bytes <= 0 or table_bytes % DEFAULT_RECORD.size:
        raise ValueError("default table does not end at its first drive-name string")
    layout_count = table_bytes // DEFAULT_RECORD.size
    if sizes_address + layout_count * PARTITION_COUNT * 4 != names_address:
        raise ValueError("partition-size table does not end at _dflt_nam")

    name_addresses = struct.unpack_from(
        f">{PARTITION_COUNT}H", image, names_address
    )
    partition_names = tuple(cstring(image, address) for address in name_addresses)

    layouts = []
    for index in range(layout_count):
        record_address = table_address + index * DEFAULT_RECORD.size
        (
            drive_address,
            size_key_mib,
            boot_fs_type,
            boot_drive,
            boot_offset,
            root_fs_type,
            root_drive,
            root_offset,
            root_device_major,
            root_device_minor,
            swap_device_major,
            swap_device_minor,
            pipe_device_major,
            pipe_device_minor,
            swap_size,
        ) = DEFAULT_RECORD.unpack_from(image, record_address)

        sizes = struct.unpack_from(
            f">{PARTITION_COUNT}I",
            image,
            sizes_address + index * PARTITION_COUNT * 4,
        )
        offset = 0
        partitions = []
        for number, (name, size) in enumerate(zip(partition_names, sizes)):
            partitions.append(Partition(number, name, offset, size))
            offset += size

        layouts.append(
            Layout(
                drive=cstring(image, drive_address),
                size_key_mib=size_key_mib,
                boot_fs_type=boot_fs_type,
                boot_drive=boot_drive,
                boot_offset=boot_offset,
                root_fs_type=root_fs_type,
                root_drive=root_drive,
                root_offset=root_offset,
                root_device_major=root_device_major,
                root_device_minor=root_device_minor,
                swap_device_major=swap_device_major,
                swap_device_minor=swap_device_minor,
                pipe_device_major=pipe_device_major,
                pipe_device_minor=pipe_device_minor,
                swap_size=swap_size,
                partitions=tuple(partitions),
            )
        )
    return layouts


def print_text(path: Path, layouts: list[Layout]) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"source: {path}")
    print(f"sha256: {digest}")
    print()
    print("drive  size-key  blocks    bytes")
    for layout in layouts:
        print(
            f"{layout.drive:<5}  {layout.size_key_mib:>8}  "
            f"{layout.total_blocks:>6}  {layout.total_blocks * 512:>11}"
        )

    for layout in layouts:
        print()
        print(f"{layout.drive} size-key {layout.size_key_mib}")
        print(
            f"  root={layout.root_device_major}/{layout.root_device_minor} "
            f"at {layout.root_offset}; "
            f"swap={layout.swap_device_major}/{layout.swap_device_minor} "
            f"size {layout.swap_size}; "
            f"pipe={layout.pipe_device_major}/{layout.pipe_device_minor}"
        )
        print("  vd  name      offset    blocks")
        for partition in layout.partitions:
            if partition.size_blocks or partition.name:
                print(
                    f"  {partition.number:>2}  {partition.name:<8}  "
                    f"{partition.offset_blocks:>6}  {partition.size_blocks:>8}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", nargs="?", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--drive", help="show only this drive type (for example smd)")
    parser.add_argument("--size-key", type=int, help="show only this size key in MiB")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    layouts = decode(args.binary)
    if args.drive is not None:
        layouts = [layout for layout in layouts if layout.drive == args.drive]
    if args.size_key is not None:
        layouts = [layout for layout in layouts if layout.size_key_mib == args.size_key]
    if not layouts:
        parser.error("no matching built-in layout")

    if args.json:
        print(json.dumps([asdict(layout) for layout in layouts], indent=2))
    else:
        print_text(args.binary, layouts)


if __name__ == "__main__":
    main()
