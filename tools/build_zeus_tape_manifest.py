#!/usr/bin/env python3
"""Build a provenance-aware ZEUS release-tape/install manifest.

The administration manual documents the tape layout and the complete
model-specific overlays, but not every file in the common root and /usr
dumps.  S8000-2.tar supplies an installed-tree snapshot for those common
files.  Its .contents files preserve the original mode/uid/gid values even
though the enclosing modern tar did not preserve them faithfully.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import struct
import tarfile
from collections import defaultdict
from pathlib import PurePosixPath


MANUAL = "03-3246-04_ZeusAdmin_Oct83.pdf"
MANUAL_RELEASE_PAGE = "3-2 (PDF 31)"
MANUAL_LINK_PAGE = "3-3 (PDF 32)"

FILE_FIELDS = [
    "path",
    "type",
    "size",
    "mode",
    "uid",
    "gid",
    "mtime",
    "scope",
    "install_class",
    "source",
    "source_reference",
    "sha256",
    "notes",
]

LINK_FIELDS = [
    "scope",
    "path",
    "target",
    "link_type",
    "basis",
    "confidence",
    "source",
    "source_reference",
]


def absolute_path(name: str) -> str:
    name = name.removeprefix("./").rstrip("/")
    return "/" if not name else "/" + name


def is_wrapper_metadata(name: str) -> bool:
    """Exclude macOS AppleDouble/PAX wrapper artifacts, not ZEUS files."""
    parts = PurePosixPath(name.removeprefix("./")).parts
    return "__MACOSX" in parts or any(part.startswith("._") for part in parts)


def parse_contents(raw: bytes) -> dict[str, tuple[int, int, int]]:
    """Parse ZEUS .contents records: mode, uid, gid, name[16]."""
    record_size = 22
    result: dict[str, tuple[int, int, int]] = {}
    if len(raw) % record_size:
        return result
    for offset in range(0, len(raw), record_size):
        mode, uid, gid, encoded_name = struct.unpack(
            ">HHH16s", raw[offset : offset + record_size]
        )
        name = encoded_name.rstrip(b"\0").decode("ascii", "replace")
        if name:
            result[name] = (mode, uid, gid)
    return result


def tar_manifest(
    tar_path: str,
) -> tuple[list[dict[str, object]], dict[str, bytes], set[str]]:
    rows: list[dict[str, object]] = []
    contents_by_dir: dict[str, dict[str, tuple[int, int, int]]] = {}
    payload_by_path: dict[str, bytes] = {}
    base_inventory_paths: set[str] = set()

    with tarfile.open(tar_path, "r:*") as archive:
        members = archive.getmembers()
        for member in members:
            if is_wrapper_metadata(member.name):
                continue
            path = absolute_path(member.name)
            if member.isfile():
                extracted = archive.extractfile(member)
                payload = extracted.read() if extracted else b""
                payload_by_path[path] = payload
                if PurePosixPath(path).name == ".contents":
                    contents_by_dir[str(PurePosixPath(path).parent)] = parse_contents(
                        payload
                    )

        for member in members:
            if is_wrapper_metadata(member.name):
                continue
            path = absolute_path(member.name)
            parent = str(PurePosixPath(path).parent)
            preserved = contents_by_dir.get(parent, {}).get(PurePosixPath(path).name)
            mode, uid, gid = (
                preserved if preserved else (member.mode, member.uid, member.gid)
            )
            if member.isdir():
                kind = "directory"
            elif member.isfile():
                kind = "file"
            elif member.issym():
                kind = "symlink"
            elif member.islnk():
                kind = "hardlink"
            else:
                kind = "other"
            payload = payload_by_path.get(path)
            if preserved:
                install_class = "base-dump-inventory"
                base_inventory_paths.add(path)
            elif parent in contents_by_dir:
                install_class = "unclassified-installed-snapshot"
            elif path in {
                "/bin",
                "/dev",
                "/etc",
                "/lib",
                "/lost+found",
                "/tmp",
                "/usr",
            }:
                install_class = "base-dump-structural"
                base_inventory_paths.add(path)
            else:
                install_class = "unclassified-installed-snapshot"
            rows.append(
                {
                    "path": path,
                    "type": kind,
                    "size": member.size,
                    "mode": f"{mode:04o}",
                    "uid": uid,
                    "gid": gid,
                    "mtime": member.mtime,
                    "scope": "common-installed-snapshot",
                    "install_class": install_class,
                    "source": PurePosixPath(tar_path).name,
                    "source_reference": member.name,
                    "sha256": hashlib.sha256(payload).hexdigest()
                    if payload is not None
                    else "",
                    "notes": (
                        "mode/uid/gid recovered from parent .contents"
                        if preserved
                        else "metadata from modern tar wrapper"
                    ),
                }
            )
    return rows, payload_by_path, base_inventory_paths


def overlay_rows(model: str) -> list[dict[str, object]]:
    disk = "zd" if model == "21" else "smd"
    raw_disk = "r" + disk
    paths = [
        "/zeus",
        "/zeus2_Y.Z",
        f"/dev/{disk}0",
        f"/dev/{disk}2",
        f"/dev/{disk}3",
        f"/dev/{disk}4",
        f"/dev/{raw_disk}0",
        f"/dev/{raw_disk}2",
        f"/dev/{raw_disk}3",
        f"/dev/{raw_disk}4",
        "/dev/z",
        "/dev/rz",
        "/dev/usr",
        "/dev/rusr",
        "/dev/tmp",
        "/dev/rtmp",
        "/dev/root",
        "/dev/rroot",
        "/dev/swap",
        "/etc/group",
    ]
    return [
        {
            "path": path,
            "type": "documented-overlay-entry",
            "size": "",
            "mode": "",
            "uid": "",
            "gid": "",
            "mtime": "",
            "scope": f"model-{model}-overlay",
            "install_class": "documented-model-overlay",
            "source": MANUAL,
            "source_reference": MANUAL_LINK_PAGE,
            "sha256": "",
            "notes": "Complete model-specific file list documented by Zilog",
        }
        for path in paths
    ]


def documented_links(model: str) -> list[dict[str, str]]:
    disk = "zd" if model == "21" else "smd"
    raw_disk = "r" + disk
    pairs = [
        ("/zeus", "/zeus2_Y.Z"),
        ("/dev/usr", f"/dev/{disk}0"),
        ("/dev/rusr", f"/dev/{raw_disk}0"),
        ("/dev/root", f"/dev/{disk}2"),
        ("/dev/rroot", f"/dev/{raw_disk}2"),
        ("/dev/tmp", f"/dev/{disk}3"),
        ("/dev/rtmp", f"/dev/{raw_disk}3"),
        ("/dev/z", f"/dev/{disk}4"),
        ("/dev/rz", f"/dev/{raw_disk}4"),
    ]
    return [
        {
            "scope": f"model-{model}-overlay",
            "path": alias,
            "target": target,
            "link_type": "hardlink",
            "basis": "Zilog manual explicitly says names are linked to same file",
            "confidence": "documented",
            "source": MANUAL,
            "source_reference": MANUAL_LINK_PAGE,
        }
        for alias, target in pairs
    ]


def manual_common_links() -> list[dict[str, str]]:
    return [
        {
            "scope": "common",
            "path": "/etc/login",
            "target": "/bin/login",
            "link_type": "hardlink",
            "basis": "Zilog manual explicitly says /etc/login is linked to /bin/login",
            "confidence": "documented",
            "source": MANUAL,
            "source_reference": "7-11 (PDF 102)",
        },
        {
            "scope": "common",
            "path": "/usr/bin/nq",
            "target": "/usr/bin/lpr",
            "link_type": "hardlink",
            "basis": "Zilog manual explicitly says nq and lpr are linked together",
            "confidence": "documented",
            "source": MANUAL,
            "source_reference": "7-4 (PDF 95)",
        },
    ]


def inferred_links(
    payload_by_path: dict[str, bytes],
    documented: set[frozenset[str]],
    eligible_paths: set[str],
) -> list[dict[str, str]]:
    groups: dict[tuple[int, str], list[str]] = defaultdict(list)
    for path, payload in payload_by_path.items():
        if (
            path in eligible_paths
            and payload
            and PurePosixPath(path).name != ".contents"
        ):
            digest = hashlib.sha256(payload).hexdigest()
            groups[(len(payload), digest)].append(path)

    rows: list[dict[str, str]] = []
    for (size, digest), paths in sorted(groups.items()):
        if len(paths) < 2:
            continue
        paths.sort()
        target = paths[0]
        for alias in paths[1:]:
            pair = frozenset((alias, target))
            if pair in documented:
                continue
            rows.append(
                {
                    "scope": "common-installed-snapshot",
                    "path": alias,
                    "target": target,
                    "link_type": "hardlink-candidate",
                    "basis": f"byte-identical regular files ({size} bytes, sha256 {digest})",
                    "confidence": "inferred",
                    "source": "S8000-2.tar",
                    "source_reference": "content comparison; tar wrapper contains no link records",
                }
            )
    return rows


def tape_layout_rows() -> list[dict[str, str]]:
    descriptions = {
        "0": "Primary bootstrap, 512 bytes",
        "1": "Secondary bootstrap",
        "2": "Disk formatting information",
        "3": "Standalone mkfs(M)",
        "4": "Standalone restor(M)",
        "5": "Level 0 dump: common root filesystem",
        "6": "Level 1 dump: Model 21 special root files",
        "7": "Level 1 dump: Model 11 special root files",
        "8": "Level 1 dump: Model 31 special root files",
        "9": "Level 0 dump: common /usr filesystem",
        "10": "Level 1 dump: Model 21 and Model 31 special /usr files",
        ">10": "tar(1) software packages restored with package(M)",
    }
    return [
        {
            "tape_location": location,
            "description": description,
            "source": MANUAL,
            "source_reference": MANUAL_RELEASE_PAGE,
        }
        for location, description in descriptions.items()
    ]


def write_csv(path: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", help="Path to S8000-2.tar")
    parser.add_argument("--output-prefix", default="inventory/zeus_release")
    args = parser.parse_args()

    files, payloads, base_inventory_paths = tar_manifest(args.archive)
    files.extend(overlay_rows("21"))
    files.extend(overlay_rows("31"))
    files.sort(key=lambda row: (str(row["scope"]), str(row["path"])))

    links = documented_links("21") + documented_links("31") + manual_common_links()
    documented = {frozenset((row["path"], row["target"])) for row in links}
    links.extend(inferred_links(payloads, documented, base_inventory_paths))
    links.sort(key=lambda row: (row["confidence"], row["scope"], row["path"]))

    write_csv(args.output_prefix + "_files.csv", FILE_FIELDS, files)
    write_csv(args.output_prefix + "_links.csv", LINK_FIELDS, links)
    write_csv(
        args.output_prefix + "_tape_layout.csv",
        ["tape_location", "description", "source", "source_reference"],
        tape_layout_rows(),
    )

    print(f"files: {len(files)}")
    print(f"links: {len(links)}")
    print(f"tape layout entries: {len(tape_layout_rows())}")


if __name__ == "__main__":
    main()
