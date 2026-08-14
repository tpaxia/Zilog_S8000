#!/usr/bin/env python3
"""Build the 128-MiB ZEUS 3.21 disk by following the install-tape flow.

The tape controller is replaced at the record-I/O boundary only.  The inputs
and ordering remain those of the recovered media:

  file 2  sawbz layout -> disk block zero
  file 3  standalone mkfs -> fresh root and /usr filesystems
  file 4  standalone restor -> files 5+6 (root), then 7+8 (/usr)
  makenewfs -> fresh /tmp and /z plus reserved lost+found directories

No files from the reconstructed clean-image staging tree are used.
"""

import argparse
import io
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "filesystem" / "tools"))

import extract_tape_images
import read_dump


BLOCK_SIZE = 512
DISK_BLOCKS = 262_144
INTERLEAVE = 16
SECTORS_PER_CYLINDER = 256
PARTITIONS = (
    ("usr", 0, 12_000),
    ("swap", 12_000, 3_200),
    ("root", 15_200, 6_000),
    ("tmp", 21_200, 6_000),
    ("z", 27_200, 234_944),
)
SUPERBLOCK_FNAME = 428
OPTIONAL_PACKAGES = {
    "acct": 9,
    "gopt": 10,
    "learn": 11,
    "sccs": 12,
    "zmenu": 13,
    "voldump": 14,
    "plzasm": 15,
    "games": 16,
    "crash": 17,
}


def merged_dump(tape_files, file_numbers):
    """Apply a level-0 dump and its level-1 overlay by inode, as restor does."""
    merged_inodes = {}
    merged_blocks = defaultdict(dict)
    headers = []
    for file_number in file_numbers:
        tape = extract_tape_images.load_dump(tape_files[file_number])
        header, inodes, blocks, _, missing, orphans = read_dump.parse(tape)
        if missing:
            raise ValueError(f"tape file {file_number} has missing dump records: {missing}")
        read_dump.adopt_orphans(inodes, blocks, orphans)
        if header is None:
            raise ValueError(f"tape file {file_number} has no dump header")
        if headers and header["ddate"] != headers[-1]["date"]:
            raise ValueError(
                f"tape file {file_number} is not an incremental of file {file_numbers[len(headers)-1]}"
            )
        headers.append(header)
        for inode, metadata in inodes.items():
            merged_inodes[inode] = metadata
            merged_blocks[inode] = dict(blocks[inode])
    return merged_inodes, merged_blocks, headers


def safe_field(value):
    value = str(value)
    if "\t" in value or "\n" in value:
        raise ValueError(f"pathname cannot be represented in restore manifest: {value!r}")
    return value


def manifest_line(kind, metadata, aux, path):
    fields = (
        kind,
        f'{metadata["mode"] & 0o7777:o}',
        metadata["uid"],
        metadata["gid"],
        metadata["atime"],
        metadata["mtime"],
        aux,
        path,
    )
    return "\t".join(safe_field(field) for field in fields) + "\n"


def write_dump_manifest(work, name, inodes, blocks):
    all_paths = read_dump.build_all_paths(inodes, blocks, root="/")
    manifest = work / f"{name}.manifest"
    payloads = work / f"{name}-payloads"
    payloads.mkdir()

    reachable = [(inode, paths) for inode, paths in all_paths.items() if inode in inodes]
    directories = []
    objects = []
    links = []
    padding = []
    empty_payload = work / f"{name}-empty"
    empty_payload.touch()
    for inode, paths in reachable:
        metadata = inodes[inode]
        paths = sorted(paths, key=lambda p: (p.count("/"), p))
        file_type = metadata["mode"] & read_dump.IFMT
        first = paths[0]
        if file_type == read_dump.IFDIR:
            directories.append((first.count("/"), first, metadata))
            live_slots = len(read_dump.dirents(inode, inodes, blocks))
            desired_slots = metadata["size"] // 16
            if desired_slots < live_slots:
                raise ValueError(f"directory {first} is smaller than its live entries")
            padding.append((first, metadata, desired_slots - live_slots))
            continue
        if file_type == read_dump.IFREG:
            payload = payloads / f"inode-{inode:05d}.bin"
            payload.write_bytes(read_dump.filedata(inode, inodes, blocks))
            objects.append((first, "f", metadata, str(payload)))
        elif file_type in (read_dump.IFBLK, read_dump.IFCHR):
            kind = "b" if file_type == read_dump.IFBLK else "c"
            objects.append((first, kind, metadata, str(metadata["rdev"] & 0xFFFF)))
        else:
            raise ValueError(f"unsupported V7 inode type {file_type:o} at {first}")
        for alias in paths[1:]:
            links.append((alias, metadata, first))

    with manifest.open("w", encoding="utf-8") as output:
        output.write("# kind\tmode\tuid\tgid\tatime\tmtime\taux\tpath\n")
        for _, path, metadata in sorted(directories):
            output.write(manifest_line("d", metadata, "-", path))
        for path, kind, metadata, aux in sorted(objects):
            output.write(manifest_line(kind, metadata, aux, path))
        for path, metadata, target in sorted(links):
            output.write(manifest_line("h", metadata, target, path))
        # Standalone restor writes directory blocks verbatim, including empty
        # slots.  Grow each new directory to the dump's size with temporary
        # entries, then unlink them, reproducing those reusable slots.
        temporary_paths = []
        empty = dict(mode=read_dump.IFREG | 0o600, uid=0, gid=0, atime=0, mtime=0)
        for directory, _, count in sorted(padding):
            prefix = "" if directory == "/" else directory
            for number in range(count):
                path = f"{prefix}/.__R{number:04x}"
                output.write(manifest_line("f", empty, empty_payload, path))
                temporary_paths.append(path)
        for path in temporary_paths:
            output.write(manifest_line("u", empty, "-", path))
    return manifest, len(reachable), len(links)


def write_empty_manifest(work, name, reserve_lost_found):
    manifest = work / f"{name}.manifest"
    root = dict(mode=read_dump.IFDIR | 0o777, uid=0, gid=0, atime=0, mtime=0)
    lost = dict(mode=read_dump.IFDIR | 0o750, uid=0, gid=0, atime=0, mtime=0)
    empty = dict(mode=read_dump.IFREG | 0o644, uid=0, gid=0, atime=0, mtime=0)
    payload = work / "empty"
    payload.touch()
    with manifest.open("w", encoding="utf-8") as output:
        output.write(manifest_line("d", root, "-", "/"))
        if reserve_lost_found:
            output.write(manifest_line("d", lost, "-", "/lost+found"))
            for number in range(318, 0, -1):
                path = f"/lost+found/Z{number}"
                output.write(manifest_line("f", empty, payload, path))
            for number in range(318, 0, -1):
                path = f"/lost+found/Z{number}"
                output.write(manifest_line("u", empty, "-", path))
    return manifest


def write_makenewfs_links_manifest(work):
    """Reproduce makenewfs's Model 31 /dev hard-link loop."""
    manifest = work / "makenewfs-dev-links.manifest"
    metadata = dict(mode=0, uid=0, gid=0, atime=0, mtime=0)
    links = (
        ("/dev/smd0", "/dev/usr"),
        ("/dev/rsmd0", "/dev/rusr"),
        ("/dev/smd1", "/dev/swap"),
        ("/dev/smd2", "/dev/root"),
        ("/dev/rsmd2", "/dev/rroot"),
        ("/dev/smd3", "/dev/tmp"),
        ("/dev/rsmd3", "/dev/rtmp"),
        ("/dev/smd4", "/dev/z"),
        ("/dev/rsmd4", "/dev/rz"),
    )
    with manifest.open("w", encoding="utf-8") as output:
        for target, path in links:
            output.write(manifest_line("h", metadata, target, path))
    return manifest


def write_package_manifests(work, package, file_number, tape_records):
    """Translate one optional-package tar file into root and /usr restores."""
    manifests = {}
    payload_root = work / f"package-{file_number:03d}-payloads"
    payload_root.mkdir()
    archive_data = b"".join(tape_records)
    with tarfile.open(fileobj=io.BytesIO(archive_data)) as archive:
        members = archive.getmembers()
        for filesystem in ("root", "usr"):
            selected = []
            directories = set()
            prefix = "usr/"
            for member in members:
                name = member.name.lstrip("./")
                on_usr = name.startswith(prefix)
                if (filesystem == "usr") != on_usr:
                    continue
                relative = name[len(prefix):] if on_usr else name
                if not relative or relative.startswith("/") or ".." in Path(relative).parts:
                    raise ValueError(f"unsafe package path in file {file_number}: {member.name}")
                path = "/" + relative
                selected.append((member, path))
                parent = Path(path).parent
                while str(parent) != "/":
                    directories.add(str(parent))
                    parent = parent.parent
            if not selected:
                continue

            manifest = work / f"package-{file_number:03d}-{filesystem}.manifest"
            with manifest.open("w", encoding="utf-8") as output:
                output.write("# kind\tmode\tuid\tgid\tatime\tmtime\taux\tpath\n")
                # Old tar archives do not carry entries for implicitly-created
                # parent directories.  Reproduce tar's usual root-owned 0755
                # directories deterministically before installing their files.
                directory_time = min(member.mtime for member, _ in selected)
                directory_metadata = dict(
                    mode=read_dump.IFDIR | 0o755,
                    uid=0,
                    gid=0,
                    atime=directory_time,
                    mtime=directory_time,
                )
                for directory in sorted(directories, key=lambda p: (p.count("/"), p)):
                    output.write(manifest_line("d", directory_metadata, "-", directory))

                paths = {}
                for index, (member, path) in enumerate(selected):
                    metadata = dict(
                        mode=(read_dump.IFREG | member.mode),
                        uid=member.uid,
                        gid=member.gid,
                        atime=member.mtime,
                        mtime=member.mtime,
                    )
                    if member.isfile():
                        source = archive.extractfile(member)
                        if source is None:
                            raise ValueError(f"cannot read package member: {member.name}")
                        payload = payload_root / f"{filesystem}-{index:04d}.bin"
                        payload.write_bytes(source.read())
                        output.write(manifest_line("f", metadata, payload, path))
                        paths[member.name.lstrip("./")] = path
                    elif member.islnk():
                        target_name = member.linkname.lstrip("./")
                        if filesystem == "usr" and target_name.startswith(prefix):
                            target_name = target_name[len(prefix):]
                        target = paths.get(member.linkname.lstrip("./"), "/" + target_name)
                        output.write(manifest_line("h", metadata, target, path))
                    else:
                        raise ValueError(
                            f"unsupported member type in package {package}: {member.name}"
                        )
            manifests[filesystem] = (manifest, len(selected))
    return manifests


def write_upgrade_manifest(work, tape_path):
    """Stage the 3.21 update tape in /z so the machine can apply it itself."""
    tape_files = extract_tape_images.read_tap(tape_path)
    if len(tape_files) != 1:
        raise ValueError(f"upgrade tape has {len(tape_files)} files, expected one")
    payloads = work / "upgrade-payloads"
    payloads.mkdir()
    manifest = work / "upgrade-z.manifest"
    with tarfile.open(fileobj=io.BytesIO(b"".join(tape_files[0]))) as archive:
        members = archive.getmembers()
        directories = set()
        for member in members:
            name = member.name.lstrip("./")
            if not name or name.startswith("/") or ".." in Path(name).parts:
                raise ValueError(f"unsafe upgrade path: {member.name}")
            parent = Path("/" + name).parent
            while str(parent) != "/":
                directories.add(str(parent))
                parent = parent.parent

        with manifest.open("w", encoding="utf-8") as output:
            output.write("# kind\tmode\tuid\tgid\tatime\tmtime\taux\tpath\n")
            # The update tar carries no directory members of its own.
            directory_time = min(member.mtime for member in members)
            directory_metadata = dict(
                mode=read_dump.IFDIR | 0o755,
                uid=0,
                gid=0,
                atime=directory_time,
                mtime=directory_time,
            )
            for directory in sorted(directories, key=lambda p: (p.count("/"), p)):
                output.write(manifest_line("d", directory_metadata, "-", directory))

            links = []
            for index, member in enumerate(members):
                path = "/" + member.name.lstrip("./")
                metadata = dict(
                    mode=(read_dump.IFREG | member.mode),
                    uid=member.uid,
                    gid=member.gid,
                    atime=member.mtime,
                    mtime=member.mtime,
                )
                if member.isfile():
                    payload = payloads / f"{index:04d}.bin"
                    payload.write_bytes(archive.extractfile(member).read())
                    output.write(manifest_line("f", metadata, payload, path))
                elif member.islnk():
                    # /z/3.21.update/scc is a hard link to cc; INSTALL moves both.
                    links.append((path, metadata, "/" + member.linkname.lstrip("./")))
                else:
                    raise ValueError(f"unsupported upgrade member type: {member.name}")
            for path, metadata, target in links:
                output.write(manifest_line("h", metadata, target, path))
    return manifest, len(members)


def write_date_patch_manifest(work, root_inodes, root_blocks):
    """Patch the tape's date tools while retaining their dump metadata."""
    paths = read_dump.build_all_paths(root_inodes, root_blocks, root="/")
    by_path = {
        path: (inode, root_inodes[inode])
        for inode, inode_paths in paths.items()
        for path in inode_paths
    }
    manifest = work / "date-y2k.manifest"
    date = work / "date-y2k"
    datem = work / "datem-y2k"
    shutil.copyfile(HERE / "extracted/install-3.21/files/file-005/bin/date", date)
    shutil.copyfile(HERE / "extracted/install-3.21/files/file-005/etc/datem", datem)
    subprocess.run([str(REPO / "patch_date_y2k.py"), str(date), str(datem)], check=True)
    with manifest.open("w", encoding="utf-8") as output:
        output.write("# kind\tmode\tuid\tgid\tatime\tmtime\taux\tpath\n")
        for path, payload in (("/bin/date", date), ("/etc/datem", datem)):
            if path not in by_path:
                raise ValueError(f"date patch target is absent from root dump: {path}")
            _, metadata = by_path[path]
            output.write(manifest_line("f", metadata, payload, path))
    return manifest


def run_helper(helper, image, size, offset, action, manifest="-"):
    subprocess.run(
        [str(helper), str(image), str(size), str(offset), str(INTERLEAVE),
         str(SECTORS_PER_CYLINDER), action, str(manifest)],
        check=True,
    )


def write_block_zero(image):
    block = bytearray(BLOCK_SIZE)
    struct.pack_into(">I", block, 0x00, 0xDEADBABE)
    struct.pack_into(">I", block, 0x04, 1)
    struct.pack_into(">I", block, 0x14, 15_200)
    struct.pack_into(">H", block, 0x18, 0x0802)
    struct.pack_into(">H", block, 0x1A, 0x0801)
    struct.pack_into(">H", block, 0x1C, 0x0802)
    struct.pack_into(">I", block, 0x1E, 3_200)
    for index, (name, offset, size) in enumerate(PARTITIONS):
        pos = 0x22 + index * 16
        struct.pack_into(">II", block, pos, offset, size)
        block[pos + 8:pos + 16] = name.encode("ascii").ljust(8, b"\0")
    with image.open("r+b") as disk:
        disk.seek(0)
        disk.write(block)


def write_labels(image, names):
    wanted = set(names)
    with image.open("r+b") as disk:
        for name, offset, _ in PARTITIONS:
            if name not in wanted:
                continue
            disk.seek((offset + 1) * BLOCK_SIZE + SUPERBLOCK_FNAME)
            disk.write(name.encode("ascii").ljust(6, b"\0"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--chd", type=Path)
    parser.add_argument("--packages", nargs="*", choices=OPTIONAL_PACKAGES,
                        default=[], metavar="PACKAGE",
                        help="install selected optional packages from tape files 9-17")
    parser.add_argument("--patch-date", action="store_true",
                        help="apply the documented date/datem Y2K compatibility patch")
    parser.add_argument("--stage-upgrade", action="store_true",
                        help="stage the 3.21 update tape in /z, to be applied on the machine")
    parser.add_argument("--no-chd", action="store_true", help="leave only the raw disk image")
    parser.add_argument("--force", action="store_true", help="replace the requested outputs")
    args = parser.parse_args()

    unknown_duplicates = len(args.packages) != len(set(args.packages))
    if unknown_duplicates:
        parser.error("a package may be selected only once")
    selected_packages = sorted(args.packages, key=lambda name: OPTIONAL_PACKAGES[name])
    suffix = "-" + "-".join(selected_packages) if selected_packages else ""
    if args.stage_upgrade:
        suffix += "-upgrade"
    if args.image is None:
        args.image = REPO / "build" / f"zeus-3.21-tape-128{suffix}.img"
    if args.chd is None:
        args.chd = REPO / "build" / f"zeus-3.21-tape-128{suffix}.chd"

    tape_path = HERE / "images" / "zeus-3.21-install.tap"
    if not tape_path.is_file():
        parser.error(f"missing recovered install tape: {tape_path}")
    upgrade_tape_path = HERE / "images" / "zeus-3.21-upgrade.tap"
    if args.stage_upgrade and not upgrade_tape_path.is_file():
        parser.error(f"missing recovered upgrade tape: {upgrade_tape_path}")
    for output in (args.image,) if args.no_chd else (args.image, args.chd):
        if output.exists() and not args.force:
            parser.error(f"output exists (use --force): {output}")
    args.image.parent.mkdir(parents=True, exist_ok=True)
    args.chd.parent.mkdir(parents=True, exist_ok=True)

    helper = REPO / "tools" / "retro-fuse" / "taperestore"
    if not helper.is_file():
        subprocess.run([str(REPO / "tools" / "retro-fuse" / "build-taperestore.sh")], check=True)

    tape_files = extract_tape_images.read_tap(tape_path)
    if len(tape_files) < 18:
        raise ValueError(f"install tape has {len(tape_files)} files, expected at least 18")

    print("[file 2: sawbz] selecting SMD size-key 128: 262144 blocks", flush=True)
    print("[tape decode] preparing dump manifests from files 5 through 8", flush=True)
    root_inodes, root_blocks, root_headers = merged_dump(tape_files, (5, 6))
    usr_inodes, usr_blocks, usr_headers = merged_dump(tape_files, (7, 8))

    with tempfile.TemporaryDirectory(prefix="zeus-tape-install-") as temporary:
        work = Path(temporary)
        root_manifest, root_count, root_links = write_dump_manifest(
            work, "root-files-5-6", root_inodes, root_blocks
        )
        usr_manifest, usr_count, usr_links = write_dump_manifest(
            work, "usr-files-7-8", usr_inodes, usr_blocks
        )
        tmp_manifest = write_empty_manifest(work, "tmp-makenewfs", True)
        z_manifest = write_empty_manifest(work, "z-makenewfs", True)
        links_manifest = write_makenewfs_links_manifest(work)
        package_manifests = {
            package: write_package_manifests(
                work, package, OPTIONAL_PACKAGES[package], tape_files[OPTIONAL_PACKAGES[package]]
            )
            for package in selected_packages
        }
        date_patch_manifest = (
            write_date_patch_manifest(work, root_inodes, root_blocks)
            if args.patch_date else None
        )
        upgrade_manifest, upgrade_count = (
            write_upgrade_manifest(work, upgrade_tape_path)
            if args.stage_upgrade else (None, 0)
        )

        with args.image.open("wb") as disk:
            disk.truncate(DISK_BLOCKS * BLOCK_SIZE)
        print("[file 2: sawbz] writing DEADBABE block zero and VFS table", flush=True)
        write_block_zero(args.image)

        print("[file 3: mkfs] creating root then /usr", flush=True)
        run_helper(helper, args.image, 6_000, 15_200, "mkfs")
        run_helper(helper, args.image, 12_000, 0, "mkfs")

        print(f"[file 4: sarestor] root files 5+6: {root_count} inodes, {root_links} hard links",
              flush=True)
        run_helper(helper, args.image, 6_000, 15_200, "restore", root_manifest)
        print(f"[file 4: sarestor] /usr files 7+8: {usr_count} inodes, {usr_links} hard links",
              flush=True)
        run_helper(helper, args.image, 12_000, 0, "restore", usr_manifest)
        print("[makenewfs] linking /dev/{usr,swap,root,tmp,z} to SMD partitions", flush=True)
        run_helper(helper, args.image, 6_000, 15_200, "restore", links_manifest)
        print("[makenewfs] labeling root and /usr", flush=True)
        write_labels(args.image, ("root", "usr"))
        print("[makenewfs] creating /tmp and /z with 318-slot lost+found directories", flush=True)
        run_helper(helper, args.image, 6_000, 21_200, "mkfs")
        run_helper(helper, args.image, 234_944, 27_200, "mkfs")
        run_helper(helper, args.image, 6_000, 21_200, "restore", tmp_manifest)
        run_helper(helper, args.image, 234_944, 27_200, "restore", z_manifest)
        print("[makenewfs] labeling /tmp and /z", flush=True)
        write_labels(args.image, ("tmp", "z"))

        for package in selected_packages:
            file_number = OPTIONAL_PACKAGES[package]
            print(f"[package] installing {package} from tape file {file_number}", flush=True)
            for filesystem, (manifest, count) in package_manifests[package].items():
                size, offset = ((6_000, 15_200) if filesystem == "root" else (12_000, 0))
                print(f"[package] {package}: {count} {filesystem} entries", flush=True)
                run_helper(helper, args.image, size, offset, "restore", manifest)

        if date_patch_manifest:
            print("[post-install] patching /bin/date and /etc/datem for two-digit modern years",
                  flush=True)
            run_helper(helper, args.image, 6_000, 15_200, "restore", date_patch_manifest)

        if upgrade_manifest:
            print(f"[post-install] staging the 3.21 update in /z: {upgrade_count} entries",
                  flush=True)
            run_helper(helper, args.image, 234_944, 27_200, "restore", upgrade_manifest)

    actual = args.image.stat().st_size
    if actual != DISK_BLOCKS * BLOCK_SIZE:
        raise ValueError(f"raw disk has wrong size: {actual}")

    if not args.no_chd:
        chdman = shutil.which("chdman")
        if not chdman:
            raise RuntimeError("chdman is not installed; raw image is complete, rerun with --no-chd")
        command = [chdman, "createhd", "-i", str(args.image), "-o", str(args.chd),
                   "--chs", "1024,8,32", "--sectorsize", "512",
                   "--compression", "none"]
        if args.force:
            command.append("--force")
        subprocess.run(command, check=True)
        print(f"complete: {args.chd}")
    print(f"raw tape-flow disk: {args.image}")
    print(f"dump chain dates: root {root_headers[0]['date']}->{root_headers[1]['date']}; "
          f"usr {usr_headers[0]['date']}->{usr_headers[1]['date']}")


if __name__ == "__main__":
    main()
