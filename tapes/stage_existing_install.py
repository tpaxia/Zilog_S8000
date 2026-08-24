#!/usr/bin/env python3
"""Add tape packages, the date patch, or the 3.21 update to an existing raw disk.

This is intended for a disk installed by the serial tape installer.  It does
not construct or restore the base filesystems; it copies the input image and
adds only the explicitly requested post-install material.
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import extract_tape_images
import install_from_tape as installer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="completed serial-installed raw image")
    parser.add_argument("output", type=Path, help="new raw image to create")
    parser.add_argument(
        "--packages", nargs="*", choices=installer.OPTIONAL_PACKAGES,
        default=[], metavar="PACKAGE",
    )
    parser.add_argument("--patch-date", action="store_true")
    parser.add_argument("--stage-upgrade", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"source image does not exist: {args.source}")
    expected_size = installer.DISK_BLOCKS * installer.BLOCK_SIZE
    if args.source.stat().st_size != expected_size:
        parser.error(
            f"source image is {args.source.stat().st_size} bytes; expected {expected_size}"
        )
    if args.output.exists() and not args.force:
        parser.error(f"output exists (use --force): {args.output}")
    if args.source.resolve() == args.output.resolve():
        parser.error("source and output must differ; the serial-installed base is immutable")
    if len(args.packages) != len(set(args.packages)):
        parser.error("a package may be selected only once")

    tape_path = installer.HERE / "images" / "zeus-3.21-install.tap"
    upgrade_path = installer.HERE / "images" / "zeus-3.21-upgrade.tap"
    if not tape_path.is_file():
        parser.error(f"missing install tape: {tape_path}")
    if args.stage_upgrade and not upgrade_path.is_file():
        parser.error(f"missing upgrade tape: {upgrade_path}")

    helper = installer.REPO / "tools" / "retro-fuse" / "taperestore"
    if not helper.is_file():
        subprocess.run(
            [str(installer.REPO / "tools" / "retro-fuse" / "build-taperestore.sh")],
            check=True,
        )

    tape_files = extract_tape_images.read_tap(tape_path)
    selected = sorted(args.packages, key=lambda name: installer.OPTIONAL_PACKAGES[name])
    root_inodes, root_blocks, _ = installer.merged_dump(tape_files, (5, 6))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.source, args.output)

    with tempfile.TemporaryDirectory(prefix="zeus-stage-existing-") as temporary:
        work = Path(temporary)
        for package in selected:
            file_number = installer.OPTIONAL_PACKAGES[package]
            manifests = installer.write_package_manifests(
                work, package, file_number, tape_files[file_number]
            )
            for filesystem, (manifest, count) in manifests.items():
                size, offset = (
                    (6_000, 15_200) if filesystem == "root" else (12_000, 0)
                )
                print(f"[package] {package}: {count} {filesystem} entries", flush=True)
                installer.run_helper(
                    helper, args.output, size, offset, "restore", manifest
                )

        if args.patch_date:
            manifest = installer.write_date_patch_manifest(
                work, root_inodes, root_blocks
            )
            print("[post-install] patching /bin/date and /etc/datem", flush=True)
            installer.run_helper(
                helper, args.output, 6_000, 15_200, "restore", manifest
            )

        if args.stage_upgrade:
            manifest, count = installer.write_upgrade_manifest(work, upgrade_path)
            print(f"[post-install] staging the 3.21 update: {count} entries", flush=True)
            installer.run_helper(
                helper, args.output, 234_944, 27_200, "restore", manifest
            )

    if args.output.stat().st_size != expected_size:
        raise ValueError(f"output image has wrong size: {args.output.stat().st_size}")
    print(f"staged existing installation: {args.output}")


if __name__ == "__main__":
    main()
