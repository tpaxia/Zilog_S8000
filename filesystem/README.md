# Filesystem reconstruction sources

`originals/` contains the unmodified source archives used while reconstructing
the ZEUS disk filesystems. They are separate from the physical tape captures in
`../tapes/originals/`.

| Source | SHA-256 |
| --- | --- |
| `S8000-2.tar` | `938a8a82454d29f6d42ade187029cd734e7258f94de62b65bae1bde034ec0274` |
| `s8000_root.tar.gz` | `6b6ca0e23ae4036b002e1dbb9f9d274be0f2d27f0f85aa01bf2ee138f3e63bd2` |
| `s8000_usr.tar.gz` | `ca315452752eda89877d8782de4cdebeae669decb6b2797e0dba7707599b13c4` |
| `zeus-3.21-upgrade.tar` | `4a62cd9099bfb16499d2f563311d8c7aad3948d09326b00711394667fb41ea81` |
| `0-dump-911118-root.backup` | `b370b251ddb8bc6022f87507c6d78de8941a1ba434536bb8b2fc02fd23ef3fda` |

The two lowercase `s8000_*.tar.gz` archives are the older root and `/usr`
filesystem trees from
[pofo.de](http://www.pofo.de/S8000/misc/harddisk_images/). `S8000-2.tar` is the
later recovered installed tree.
`0-dump-911118-root.backup` is the independently recovered checksum-clean root
dump.

`tools/` contains the dump decoder and CRC repair utility used during the
recovery work.

`generated/` contains the bootable `s8000_smd.chd` and all fixed inputs to the
final image build: the native `/usr`, `/tmp`, and `/z` partition seeds, the
pristine init, and the relinked kernel.

| Fixed rebuild input | SHA-256 |
| --- | --- |
| `generated/root_overlays/init-pristine-1991-11-18` | `7a683ba63c8439398b2cd076dbc7ef08c6efc49f00ad1e55b9bc1a5749c6971a` |
| `generated/root_overlays/zeus-3.2.1-relinked` | `ed39635a5a6447e83685871c49728b88fdf2219b262966fb5eb4fbf560d1c8b1` |

The final `generated/s8000_smd.chd` has SHA-256
`b9a02009a8b6a0699beaab8246e0488e19fbe432625276a443afd9c714057265`.

The root filesystem builder honors `SOURCE_DATE_EPOCH`. `rebuild_fs.sh` pins
both filesystem creation and device-node creation to epoch `1786449783`,
matching the authoritative image. Conversion uses uncompressed CHD storage.
