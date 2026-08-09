#!/bin/bash
# ============================================================================
# rebuild_fs.sh -- rebuild a clean, bootable S8000 ZEUS 3.2.1 disk.
#
# A manifest-driven staging pass admits only recovered base-distribution files
# and the documented Model 31 overlay.  It intentionally excludes cores,
# backups, compiler traces, renamed boot files and other installed-snapshot
# residue.  The pristine init and relinked kernel are explicit overlays.
#
# /etc/init is the original Zilog binary recovered from the pristine
# 1991-11-18 level-0 root dump.  It replaces the earlier source
# reconstruction (systemIII/init.c), which was only needed while the sole
# known copy of the original had a corrupt sector.
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
TMP_STAGE=$STAGE/tmpfs
Z_STAGE=$STAGE/zfs
IMG=$BUILD/s8000_vfs.img
CHD=$BUILD/s8000.chd
INSTALL=$HERE/s8000_smd.chd
DEBUG_INSTALL=$HERE/debug/s8000.chd
PRISTINE_INIT=$BUILD/init.pristine-911118
PRISTINE_INIT_SHA=7a683ba63c8439398b2cd076dbc7ef08c6efc49f00ad1e55b9bc1a5749c6971a
RELINKED_ZEUS=$CSVOL/s8000_usr/sys/conf/zeus
CLEAN_RC=$HERE/systemIII/rc.clean
CLEAN_PASSWD=$HERE/systemIII/passwd.clean
CLEAN_RC_CSH=$HERE/systemIII/rc_csh.clean
CLEAN_MFS=$HERE/systemIII/mfs.clean
CLEAN_INITTAB=$HERE/systemIII/inittab.clean
GETTY_CONSOLE=$HERE/systemIII/getty-console
TTYTYPE=$HERE/systemIII/ttytype.h19
DATE_PATCHER=$HERE/patch_date_y2k.py
NATIVE_PARTITIONS=$HERE/native_partitions
NATIVE_USR=$NATIVE_PARTITIONS/usr.fs
NATIVE_TMP=$NATIVE_PARTITIONS/tmp.fs
NATIVE_Z=$NATIVE_PARTITIONS/z.fs

DISK_BLOCKS=131936            # whole disk (589*7*32)
USR_SIZE=12000;  USR_OFF=0
SWAP_SIZE=3200;  SWAP_OFF=12000
ROOT_SIZE=6000;  ROOT_OFF=15200
TMP_SIZE=6000;   TMP_OFF=21200
Z_SIZE=104736;   Z_OFF=27200
CHS="589,7,32"

# Sanity-check all authoritative inputs before replacing an image.
[ -f "$INVENTORY/zeus_release_files.csv" ] || { echo "ERROR: no release inventory"; exit 1; }
[ -f "$INVENTORY/missing_from_s8000-2.csv" ] || { echo "ERROR: no archive comparison"; exit 1; }
[ -f "$PRISTINE_INIT" ] || { echo "ERROR: no pristine init"; exit 1; }
[ "$(shasum -a 256 "$PRISTINE_INIT" | cut -d' ' -f1)" = "$PRISTINE_INIT_SHA" ] ||
    { echo "ERROR: pristine init does not match the 1991-11-18 dump"; exit 1; }
[ -f "$RELINKED_ZEUS" ] || { echo "ERROR: no relinked ZEUS kernel"; exit 1; }
[ -f "$CLEAN_RC" ] || { echo "ERROR: no clean rc"; exit 1; }
[ -f "$CLEAN_PASSWD" ] || { echo "ERROR: no clean passwd"; exit 1; }
[ -f "$CLEAN_RC_CSH" ] || { echo "ERROR: no clean rc_csh"; exit 1; }
[ -f "$CLEAN_MFS" ] || { echo "ERROR: no clean mfs"; exit 1; }
[ -f "$CLEAN_INITTAB" ] || { echo "ERROR: no clean inittab"; exit 1; }
[ -f "$GETTY_CONSOLE" ] || { echo "ERROR: no console getty wrapper"; exit 1; }
[ -f "$TTYTYPE" ] || { echo "ERROR: no console ttytype"; exit 1; }
[ -f "$DATE_PATCHER" ] || { echo "ERROR: no date Y2K patcher"; exit 1; }
[ "$(stat -f %z "$NATIVE_USR")" -eq $((USR_SIZE * 512)) ] ||
    { echo "ERROR: invalid native /usr partition"; exit 1; }
[ "$(stat -f %z "$NATIVE_TMP")" -eq $((TMP_SIZE * 512)) ] ||
    { echo "ERROR: invalid native /tmp partition"; exit 1; }
[ "$(stat -f %z "$NATIVE_Z")" -eq $((Z_SIZE * 512)) ] ||
    { echo "ERROR: invalid native /z partition"; exit 1; }
[ -x "$RF/mkv7img" ] && [ -x "$RF/mkdev" ] || { echo "ERROR: filesystem tools missing"; exit 1; }
[ $((USR_OFF + USR_SIZE)) -eq "$SWAP_OFF" ] || { echo "ERROR: /usr/swap boundary mismatch"; exit 1; }
[ $((SWAP_OFF + SWAP_SIZE)) -eq "$ROOT_OFF" ] || { echo "ERROR: swap/root boundary mismatch"; exit 1; }
[ $((ROOT_OFF + ROOT_SIZE)) -eq "$TMP_OFF" ] || { echo "ERROR: root//tmp boundary mismatch"; exit 1; }
[ $((TMP_OFF + TMP_SIZE)) -eq "$Z_OFF" ] || { echo "ERROR: /tmp//z boundary mismatch"; exit 1; }
[ $((Z_OFF + Z_SIZE)) -eq "$DISK_BLOCKS" ] || { echo "ERROR: /z does not end at disk boundary"; exit 1; }

echo "== clean distribution staging =="
python3 "$STAGER" \
    --manifest "$INVENTORY/zeus_release_files.csv" \
    --missing "$INVENTORY/missing_from_s8000-2.csv" \
    --root-source "$CSVOL/s8000_root" \
    --usr-source "$CSVOL/s8000_usr" \
    --root-stage "$ROOT_STAGE" \
    --usr-stage "$USR_STAGE" \
    --tmp-stage "$TMP_STAGE" \
    --z-stage "$Z_STAGE" \
    --init "$PRISTINE_INIT" \
    --kernel "$RELINKED_ZEUS"
cp "$CLEAN_RC" "$ROOT_STAGE/etc/rc"
chmod 700 "$ROOT_STAGE/etc/rc"
cp "$CLEAN_PASSWD" "$ROOT_STAGE/etc/passwd"
chmod 644 "$ROOT_STAGE/etc/passwd"
cp "$CLEAN_RC_CSH" "$ROOT_STAGE/etc/rc_csh"
chmod 700 "$ROOT_STAGE/etc/rc_csh"
cp "$CLEAN_MFS" "$ROOT_STAGE/etc/mfs"
chmod 700 "$ROOT_STAGE/etc/mfs"
rm -f "$ROOT_STAGE/etc/umfs"
ln "$ROOT_STAGE/etc/mfs" "$ROOT_STAGE/etc/umfs"
cp "$CLEAN_INITTAB" "$ROOT_STAGE/etc/inittab"
chmod 600 "$ROOT_STAGE/etc/inittab"
cp "$GETTY_CONSOLE" "$ROOT_STAGE/etc/getty-console"
chmod 700 "$ROOT_STAGE/etc/getty-console"
cp "$TTYTYPE" "$ROOT_STAGE/etc/ttytype"
chmod 644 "$ROOT_STAGE/etc/ttytype"
python3 "$DATE_PATCHER" "$ROOT_STAGE/bin/date" "$ROOT_STAGE/etc/datem"
[ "$ROOT_STAGE/zeus" -ef "$ROOT_STAGE/zeus-3.2.1" ] ||
    { echo "ERROR: staged kernels are not hard links"; exit 1; }

echo "== fresh image =="
rm -f "$IMG"
python3 -c "f=open('$IMG','wb');f.truncate($DISK_BLOCKS*512);f.close()"

echo "== root filesystem from clean staging tree =="
"$RF/mkv7img" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" 0 "$ROOT_STAGE" /

echo "== pristine native ZEUS auxiliary partitions =="
dd if="$NATIVE_USR" of="$IMG" bs=512 seek="$USR_OFF" count="$USR_SIZE" conv=notrunc status=none
dd if="$NATIVE_TMP" of="$IMG" bs=512 seek="$TMP_OFF" count="$TMP_SIZE" conv=notrunc status=none
dd if="$NATIVE_Z" of="$IMG" bs=512 seek="$Z_OFF" count="$Z_SIZE" conv=notrunc status=none

echo "== /dev nodes =="
"$RF/mkdev" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" "$HERE/devs.txt"
python3 "$HERE/fix_dev_majors.py" "$IMG" "$HERE/devs.txt" "$ROOT_OFF"

echo "== block 0 (autoboot + rootdev + vfs table) =="
python3 "$HERE/mkblock0.py" "$IMG"

echo "== uncompressed CHD =="
rm -f "$CHD"
chdman createhd -i "$IMG" -o "$CHD" --chs "$CHS" --sectorsize 512 --compression none

echo "== install =="
# The committed CHD is intentionally read-only.  Make an existing artifact
# writable for replacement, then restore its published mode.
[ ! -e "$INSTALL" ] || chmod u+w "$INSTALL"
cp "$CHD" "$INSTALL"
chmod 444 "$INSTALL"
mkdir -p "$HERE/debug"
cp "$CHD" "$DEBUG_INSTALL"
echo "DONE -> $INSTALL and $DEBUG_INSTALL  (documented Model 31 five-region layout)"
