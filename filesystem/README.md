# Filesystem reconstruction sources

`originals/` contains the unmodified source archives used while reconstructing
the ZEUS disk filesystems. They are separate from the physical tape captures in
`../tapes/originals/`.

| Source | SHA-256 |
| --- | --- |
| `S8000-2.tar` | `938a8a82454d29f6d42ade187029cd734e7258f94de62b65bae1bde034ec0274` |
| `s8000_root.tar.gz` | `6b6ca0e23ae4036b002e1dbb9f9d274be0f2d27f0f85aa01bf2ee138f3e63bd2` |
| `s8000_usr.tar.gz` | `ca315452752eda89877d8782de4cdebeae669decb6b2797e0dba7707599b13c4` |
| `s8000_z.tar.gz` | `3ab868dcbc98fdf9b6b17b9db51462f9004fc1d2ac645807f402ffb0ff909439` |
| `S8000-z-bin.tar` | `447cc343c30386167ad333db795f8b4ebeb6d2b85cea46b3afa194e18baf6a4d` |
| `zeus-3.21-upgrade.tar` | `4a62cd9099bfb16499d2f563311d8c7aad3948d09326b00711394667fb41ea81` |
| `0dump-1991-06-18-usr-recovered.tar` | `5b56f8efcc8840d70e531cbf90fbb708d18c6633e50995621f20ade94d9373db` |
| `0-dump-911118-root.backup` | `b370b251ddb8bc6022f87507c6d78de8941a1ba434536bb8b2fc02fd23ef3fda` |

The three lowercase `s8000_*.tar.gz` archives are the older filesystem trees
from [pofo.de](http://www.pofo.de/S8000/misc/harddisk_images/). `S8000-2.tar`
is the later recovered installed tree. `0dump-1991-06-18-usr-recovered.tar` is
the one-time extraction of a damaged 1991 `/usr` dump; see its adjacent note.
`0-dump-911118-root.backup` is the independently recovered checksum-clean root
dump.

`tools/` contains the dump decoder and CRC repair utility used during the
recovery work.

`generated/` contains the bootable `s8000_smd.chd` and the native `/usr`,
`/tmp`, and `/z` partition seeds used by `rebuild_fs.sh`. It also preserves the
relinked kernel installed as `/zeus` and `/zeus-3.2.1`.

| Artifact | SHA-256 |
| --- | --- |
| `build/s8000_vfs.img` | `80771ec1983b0faf3c83a788ba97237e143e96ce276176f663396fa1cae782ec` |
| `generated/s8000_smd.chd` | `b9a02009a8b6a0699beaab8246e0488e19fbe432625276a443afd9c714057265` |
| `generated/kernel/zeus-3.2.1-relinked` | `ed39635a5a6447e83685871c49728b88fdf2219b262966fb5eb4fbf560d1c8b1` |

The root filesystem builder honors `SOURCE_DATE_EPOCH`. `rebuild_fs.sh` pins
both filesystem creation and device-node creation to epoch `1786449783`,
matching the authoritative image. Conversion uses uncompressed CHD storage;
the resulting raw image and CHD have the hashes listed above.
