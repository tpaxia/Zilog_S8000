# Native ZEUS partition templates

These files were created once inside ZEUS 3.21 using the native Model 31
`mkfs` command and captured from the completed CHD. They are copied
block-for-block into normal clean-image rebuilds so every build uses the exact
native installation result without repeating the destructive creation and
restore procedure.

Earlier `fsck` failures attributed to host-created filesystem metadata were
subsequently isolated to large reads through MAME's raw SMD character-device
path. They do not establish that `mkv7img` produces invalid metadata. These
templates remain authoritative because they were created by ZEUS itself and
have been independently verified through the working buffered block-device
path.

| File | Blocks | Start block | SHA-256 |
|---|---:|---:|---|
| `usr.fs` | 12,000 | 0 | `e244a656fc2daa6fd64050aaa6e8444108606ab87c11bb17d24d892341d9e8b3` |
| `tmp.fs` | 6,000 | 21,200 | `59b0ec27eda56a3444db1c55d8c3fe373bb1eff80c3dee1e6627f7c624496c9a` |
| `z.fs` | 104,736 | 27,200 | `6271a02bae73fe3222c3902087cbcf3152cecb7d23397017492a8deecdafefca` |

`usr.fs` contains exactly the 804 regular-file paths from the clean `/usr`
restore archive. `tmp.fs` and `z.fs` contain only their preallocated
`lost+found` directories.

Swap is deliberately not stored here. The captured swap area contained
runtime paging data; a normal rebuild leaves its 3,200-block range zeroed.
