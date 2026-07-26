#!/bin/bash
# ============================================================================
# rebuild_fs.sh -- rebuild a clean, bootable S8000 ZEUS 3.2.1 disk.
#
# A manifest-driven staging pass admits only recovered base-distribution files
# and the documented Model 31 overlay.  It intentionally excludes cores,
# backups, compiler traces, renamed boot files and other installed-snapshot
# residue.  The current fixed init and relinked kernel are explicit overlays.
# ============================================================================
set -euo pipefail

HERE=/Users/paxia/Projects/Zilog_S8000
RF=$HERE/tools/retro-fuse
BUILD=$HERE/build
CSVOL=/Volumes/ZeusFS
INVENTORY=$HERE/inventory
STAGER=$HERE/stage_clean_zeus.py
STAGE=$CSVOL/clean-stage
ROOT_STAGE=$STAGE/root
USR_STAGE=$STAGE/usr
IMG=$BUILD/s8000_vfs.img
CHD=$BUILD/s8000.chd
INSTALL=$HERE/s8000_smd.chd
DEBUG_INSTALL=$HERE/debug/s8000.chd
FIXED_INIT=$CSVOL/s8000_root/etc/init
RELINKED_ZEUS=$CSVOL/s8000_usr/sys/conf/zeus

DISK_BLOCKS=131936            # whole disk (589*7*32)
ROOT_SIZE=100000; ROOT_OFF=15200   # ~50MB root
USR_SIZE=15000;  USR_OFF=0        # enlarged to hold the complete S8000-2 /usr tree
CHS="589,7,32"

# Sanity-check all authoritative inputs before replacing an image.
[ -f "$INVENTORY/zeus_release_files.csv" ] || { echo "ERROR: no release inventory"; exit 1; }
[ -f "$INVENTORY/missing_from_s8000-2.csv" ] || { echo "ERROR: no archive comparison"; exit 1; }
[ -f "$FIXED_INIT" ] || { echo "ERROR: no fixed init"; exit 1; }
[ -f "$RELINKED_ZEUS" ] || { echo "ERROR: no relinked ZEUS kernel"; exit 1; }
[ -x "$RF/mkv7img" ] && [ -x "$RF/mkdev" ] || { echo "ERROR: filesystem tools missing"; exit 1; }
[ $((ROOT_OFF + ROOT_SIZE)) -le $DISK_BLOCKS ] || { echo "ERROR: root overflows disk"; exit 1; }

echo "== clean distribution staging =="
python3 "$STAGER" \
    --manifest "$INVENTORY/zeus_release_files.csv" \
    --missing "$INVENTORY/missing_from_s8000-2.csv" \
    --root-source "$CSVOL/s8000_root" \
    --usr-source "$CSVOL/s8000_usr" \
    --root-stage "$ROOT_STAGE" \
    --usr-stage "$USR_STAGE" \
    --init "$FIXED_INIT" \
    --kernel "$RELINKED_ZEUS"
[ "$ROOT_STAGE/zeus" -ef "$ROOT_STAGE/zeus-3.2.1" ] ||
    { echo "ERROR: staged kernels are not hard links"; exit 1; }

echo "== fresh image =="
rm -f "$IMG"
python3 -c "f=open('$IMG','wb');f.truncate($DISK_BLOCKS*512);f.close()"

echo "== filesystems (mkv7img) from clean staging trees =="
"$RF/mkv7img" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" 0 "$ROOT_STAGE" /
"$RF/mkv7img" "$IMG" "$USR_SIZE"  "$USR_OFF"  0 "$USR_STAGE"  /

echo "== /dev nodes =="
"$RF/mkdev" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" "$HERE/devs.txt"
python3 "$HERE/fix_dev_majors.py" "$IMG" "$HERE/devs.txt" "$ROOT_OFF"

echo "== block 0 (autoboot + rootdev + vfs table) =="
python3 "$HERE/mkblock0.py" "$IMG"

echo "== uncompressed CHD =="
rm -f "$CHD"
chdman createhd -i "$IMG" -o "$CHD" --chs "$CHS" --sectorsize 512 --compression none

echo "== install =="
cp "$CHD" "$INSTALL"
mkdir -p "$HERE/debug"
cp "$CHD" "$DEBUG_INSTALL"
echo "DONE -> $INSTALL and $DEBUG_INSTALL  (root ${ROOT_SIZE} blocks @ ${ROOT_OFF})"
