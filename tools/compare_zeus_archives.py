#!/usr/bin/env python3
"""Classify files absent from S8000-2.tar but present in older archives."""

from __future__ import annotations

import argparse
import csv
import posixpath
import struct
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


ORIGINALS = Path(__file__).resolve().parents[1] / "filesystem" / "originals"


@dataclass(frozen=True)
class Entry:
    path: str
    kind: str
    size: int
    source: str
    member: str
    evidence: str


def normalize(name: str, prefix: str = "") -> str:
    while name.startswith("./"):
        name = name[2:]
    name = name.rstrip("/")
    return posixpath.normpath(prefix + "/" + name) if name else (prefix or "/")


def wrapper_metadata(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return "__MACOSX" in parts or any(part.startswith("._") for part in parts)


def member_kind(member: tarfile.TarInfo) -> str:
    if member.isfile():
        return "file"
    if member.isdir():
        return "directory"
    if member.issym():
        return "symlink"
    if member.islnk():
        return "hardlink"
    return "other"


def printable(value: str) -> str:
    """Render undecodable filename bytes as \\xNN so CSV remains valid UTF-8."""
    return "".join(
        f"\\x{ord(char) - 0xDC00:02x}"
        if 0xDC80 <= ord(char) <= 0xDCFF
        else char
        for char in value
    )


def parse_contents(data: bytes) -> set[str]:
    """Return names from ZEUS 22-byte mode/uid/gid/name directory records."""
    if len(data) % 22:
        return set()
    names = set()
    for offset in range(0, len(data), 22):
        _, _, _, raw_name = struct.unpack(">HHH16s", data[offset : offset + 22])
        name = raw_name.rstrip(b"\0").decode("ascii", "replace")
        if name:
            names.add(name)
    return names


def path_set(tar_path: str) -> set[str]:
    with tarfile.open(tar_path, "r:*") as archive:
        return {
            path
            for member in archive.getmembers()
            if not wrapper_metadata(path := normalize(member.name))
        }


def root_usr_entries(tar_path: str, prefix: str) -> list[Entry]:
    """Classify root or /usr members using their parent directory inventory."""
    with tarfile.open(tar_path, "r:*") as archive:
        members = archive.getmembers()
        inventories: dict[str, set[str]] = {}
        for member in members:
            path = normalize(member.name, prefix)
            if member.isfile() and posixpath.basename(path) == ".contents":
                extracted = archive.extractfile(member)
                inventories[posixpath.dirname(path)] = parse_contents(
                    extracted.read() if extracted else b""
                )

        result = []
        for member in members:
            path = normalize(member.name, prefix)
            # "." is only the modern tar's container, not a ZEUS directory entry.
            if path == "/":
                continue
            listed = posixpath.basename(path) in inventories.get(
                posixpath.dirname(path), set()
            )
            result.append(
                Entry(
                    path=path,
                    kind=member_kind(member),
                    size=member.size,
                    source=PurePosixPath(tar_path).name,
                    member=member.name,
                    evidence=(
                        "confirmed-common-distribution"
                        if listed
                        else "unclassified-root-usr"
                    ),
                )
            )
        return result


def z_archive_entries(tar_path: str, prefix: str) -> list[Entry]:
    """Select /z members without claiming they came from the base release tape."""
    with tarfile.open(tar_path, "r:*") as archive:
        return [
            Entry(
                path=normalize(member.name, prefix),
                kind=member_kind(member),
                size=member.size,
                source=PurePosixPath(tar_path).name,
                member=member.name,
                evidence="separate-z-archive",
            )
            for member in archive.getmembers()
        ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s8000-2", default=str(ORIGINALS / "S8000-2.tar"))
    parser.add_argument(
        "--root",
        default=str(ORIGINALS / "s8000_root.tar.gz"),
    )
    parser.add_argument(
        "--usr",
        default=str(ORIGINALS / "s8000_usr.tar.gz"),
    )
    parser.add_argument(
        "--z", default=str(ORIGINALS / "s8000_z.tar.gz")
    )
    parser.add_argument(
        "--output", default="inventory/missing_from_s8000-2.csv"
    )
    args = parser.parse_args()

    installed = path_set(args.s8000_2)
    candidates = (
        root_usr_entries(args.root, "")
        + root_usr_entries(args.usr, "/usr")
        + z_archive_entries(args.z, "/z")
    )

    # The root archive's /z mount point and the z archive's root are the same path.
    missing_by_path: dict[str, Entry] = {}
    for entry in candidates:
        if entry.path not in installed:
            missing_by_path.setdefault(entry.path, entry)
    missing = sorted(missing_by_path.values(), key=lambda entry: entry.path)

    with open(args.output, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=["path", "type", "size", "source", "member", "evidence"],
        )
        writer.writeheader()
        for entry in missing:
            writer.writerow(
                {
                    "path": printable(entry.path),
                    "type": entry.kind,
                    "size": entry.size,
                    "source": entry.source,
                    "member": printable(entry.member),
                    "evidence": entry.evidence,
                }
            )

    confirmed_files = [
        entry
        for entry in missing
        if entry.kind == "file"
        and entry.evidence == "confirmed-common-distribution"
    ]
    unclassified_files = [
        entry
        for entry in missing
        if entry.kind == "file"
        and entry.evidence == "unclassified-root-usr"
    ]
    z_files = [
        entry
        for entry in missing
        if entry.kind == "file" and entry.evidence == "separate-z-archive"
    ]
    directories = [entry for entry in missing if entry.kind == "directory"]
    inventory_files = [
        entry for entry in missing if posixpath.basename(entry.path) == ".contents"
    ]
    print(f"confirmed common-distribution files missing: {len(confirmed_files)}")
    print(f"unclassified root+/usr files missing: {len(unclassified_files)}")
    print(f"separate /z archive files missing: {len(z_files)}")
    print(
        "all regular files missing from the three archives: "
        f"{len(confirmed_files) + len(unclassified_files) + len(z_files)}"
    )
    print(f"of which .contents inventory files: {len(inventory_files)}")
    print(f"missing directories needed for those files: {len(directories)}")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
