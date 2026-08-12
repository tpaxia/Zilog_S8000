# ZEUS release-tape inventory

This directory separates what is documented from what is inferred:

- `zeus_release_tape_layout.csv` transcribes release-tape locations 0–10
  from the ZEUS Administrator's Manual, section 3.1.
- `zeus_release_files.csv` combines the installed common tree recovered
  from `S8000-2.tar` with the complete Model 21 and Model 31 overlay lists
  on manual page 3-3.
- `zeus_release_links.csv` records explicit links from the manual as
  `documented` and byte-identical link candidates from `S8000-2.tar` as
  `inferred`.
- `missing_from_s8000-2.csv` compares `S8000-2.tar` with the older
  `s8000_root.tar.gz` and `s8000_usr.tar.gz` archives.
  Its `evidence` column distinguishes common-distribution files confirmed
  by `.contents` from uncatalogued root or `/usr` files. The latter are not
  asserted to be base-tape files.

Important limitation: `S8000-2.tar` is a modern tar wrapper around an
installed filesystem tree, not a block-for-block release tape. It contains
no tar hard-link records and omits the model-specific device-node overlay.
The `.contents` files recover original mode, uid, and gid metadata, but do
not contain inode numbers. Therefore byte-identical files are candidates,
not proof of hard linkage.

macOS AppleDouble files (`._name`) present in the modern wrapper are excluded;
they were not ZEUS filesystem entries.

The `install_class` column is important:

- `base-dump-inventory` means the entry appears in its original ZEUS
  `.contents` directory inventory.
- `base-dump-structural` marks the necessary top-level directories.
- `documented-model-overlay` comes directly from manual page 3-3.
- `unclassified-installed-snapshot` exists in the recovered machine but is
  absent from `.contents`; it may be an optional tape package, a later
  installation, or runtime/user residue. It must not yet be treated as a
  base-tape file.

Regenerate:

```sh
python3 tools/build_zeus_tape_manifest.py \
  filesystem/originals/S8000-2.tar \
  --output-prefix inventory/zeus_release

python3 tools/compare_zeus_archives.py
```
