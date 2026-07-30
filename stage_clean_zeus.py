#!/usr/bin/env python3
"""Stage a clean ZEUS Model 31 installation from the recovered inventories."""

from __future__ import annotations

import argparse
import csv
import os
import shutil
from pathlib import Path


BASE_CLASSES = {"base-dump-inventory", "base-dump-structural"}
CONFIRMED_MISSING = "confirmed-common-distribution"
KERNEL_NAMES = {"/zeus", "/zeus2_Y.Z", "/zeus2_3.21", "/zeus-3.2.1"}


def safe_recreate(path: Path) -> None:
    resolved = path.resolve()
    if resolved == Path("/") or len(resolved.parts) < 3:
        raise SystemExit(f"refusing to replace unsafe staging path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def source_for(path: str, root_source: Path, usr_source: Path) -> Path:
    if path.startswith("/usr/"):
        return usr_source / path.removeprefix("/usr/")
    if path == "/usr":
        return root_source / "usr"
    fallbacks = {
        "/etc/rc": root_source / "etc/rc.s8000-2",
        "/etc/inittab": root_source / "etc/inittab.s8000-2",
    }
    normal = root_source / path.lstrip("/")
    return normal if normal.exists() else fallbacks.get(path, normal)


def destination_for(path: str, root_stage: Path, usr_stage: Path) -> Path:
    if path.startswith("/usr/"):
        return usr_stage / path.removeprefix("/usr/")
    return root_stage / path.lstrip("/")


def copy_entry(source: Path, destination: Path, kind: str) -> None:
    if kind == "directory":
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copystat(source, destination, follow_symlinks=False)
        return
    if kind != "file":
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination, follow_symlinks=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--missing", type=Path, required=True)
    parser.add_argument("--root-source", type=Path, required=True)
    parser.add_argument("--usr-source", type=Path, required=True)
    parser.add_argument("--root-stage", type=Path, required=True)
    parser.add_argument("--usr-stage", type=Path, required=True)
    parser.add_argument("--tmp-stage", type=Path, required=True)
    parser.add_argument("--z-stage", type=Path, required=True)
    parser.add_argument("--init", type=Path, required=True)
    parser.add_argument("--kernel", type=Path, required=True)
    args = parser.parse_args()

    safe_recreate(args.root_stage)
    safe_recreate(args.usr_stage)
    safe_recreate(args.tmp_stage)
    safe_recreate(args.z_stage)

    # makenewfs(M) created these directories during a normal installation.
    # Keep the auxiliary filesystems otherwise empty.
    for stage in (args.tmp_stage, args.z_stage):
        lost_found = stage / "lost+found"
        lost_found.mkdir()
        lost_found.chmod(0o750)

    selected: dict[str, dict[str, str]] = {}
    with args.manifest.open(newline="") as source:
        for row in csv.DictReader(source):
            if row["install_class"] in BASE_CLASSES or row["scope"] == "model-31-overlay":
                selected[row["path"]] = row
    with args.missing.open(newline="") as source:
        for row in csv.DictReader(source):
            if row["evidence"] == CONFIRMED_MISSING:
                selected.setdefault(row["path"], row)

    copied = 0
    skipped_overlay = 0
    for path, row in sorted(selected.items(), key=lambda item: (item[0].count("/"), item[0])):
        kind = row["type"]
        if path in KERNEL_NAMES:
            continue
        if kind == "documented-overlay-entry":
            # Model-specific device nodes are installed by mkdev.
            skipped_overlay += 1
            continue
        source = source_for(path, args.root_source, args.usr_source)
        if not source.exists():
            raise SystemExit(f"distribution source is missing: {path} ({source})")
        destination = destination_for(path, args.root_stage, args.usr_stage)
        copy_entry(source, destination, kind)
        copied += 1

    # Install the selected init under both names used by the ZEUS system.
    fixed_init = args.root_stage / "etc/init"
    fixed_init.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.init, fixed_init)
    fixed_init.chmod(0o755)
    upper_init = args.root_stage / "etc/INIT"
    if upper_init.exists():
        upper_init.unlink()
    os.link(fixed_init, upper_init)

    # Install one relinked kernel inode under both requested names.
    versioned_kernel = args.root_stage / "zeus-3.2.1"
    shutil.copy2(args.kernel, versioned_kernel)
    boot_kernel = args.root_stage / "zeus"
    if boot_kernel.exists():
        boot_kernel.unlink()
    os.link(versioned_kernel, boot_kernel)

    print(
        f"staged {copied} distribution entries; "
        f"{skipped_overlay} model-overlay entries deferred to mkdev"
    )
    print(f"init: {fixed_init} == {upper_init}")
    print(f"kernel: {boot_kernel} == {versioned_kernel}")


if __name__ == "__main__":
    main()
