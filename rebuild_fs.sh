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
# 1991-11-18 level-0 root dump.
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
INSTALL=$HERE/filesystem/generated/s8000_smd.chd
PRISTINE_INIT=$BUILD/init.pristine-911118
PRISTINE_INIT_SHA=7a683ba63c8439398b2cd076dbc7ef08c6efc49f00ad1e55b9bc1a5749c6971a
RELINKED_ZEUS=$HERE/filesystem/generated/kernel/zeus-3.2.1-relinked
RELINKED_ZEUS_SHA=ed39635a5a6447e83685871c49728b88fdf2219b262966fb5eb4fbf560d1c8b1
ROOT_FS_EPOCH=1786449783
PRISTINE_RC=$HERE/image-config/rc
PRISTINE_RC_SHA=763766e6725c96b302398a232a250a71c4b12327ce6aa21e18f7d3a2e8608aca
CLEAN_PASSWD=$HERE/image-config/passwd
PRISTINE_RC_CSH=$HERE/image-config/rc_csh
PRISTINE_RC_CSH_SHA=6fc0837f67582b878f9151431111dd753825d5bc30bf6e8bea567872e3cc5120
PRISTINE_MFS=$HERE/image-config/mfs
PRISTINE_MFS_SHA=a860102e6c41a1bd0a61d92e1d430376c355fb40b71d92aadb40f2a85d7390be
PRISTINE_INITTAB=$HERE/image-config/inittab
PRISTINE_INITTAB_SHA=f383b6520bc1fde907d4eb050650946ca1d2fee51d6758f5ab391e91962a1cc3
TTYTYPE=$HERE/image-config/ttytype
DATE_PATCHER=$HERE/patch_date_y2k.py
NATIVE_PARTITIONS=$HERE/filesystem/generated/native_partitions
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
[ "$(shasum -a 256 "$RELINKED_ZEUS" | cut -d' ' -f1)" = "$RELINKED_ZEUS_SHA" ] ||
    { echo "ERROR: relinked ZEUS kernel hash mismatch"; exit 1; }
[ "$(shasum -a 256 "$PRISTINE_RC" | cut -d' ' -f1)" = "$PRISTINE_RC_SHA" ] ||
    { echo "ERROR: rc does not match recovered rc.sav"; exit 1; }
[ -f "$CLEAN_PASSWD" ] || { echo "ERROR: no clean passwd"; exit 1; }
[ "$(shasum -a 256 "$PRISTINE_RC_CSH" | cut -d' ' -f1)" = "$PRISTINE_RC_CSH_SHA" ] ||
    { echo "ERROR: rc_csh does not match recovered root filesystem"; exit 1; }
[ "$(shasum -a 256 "$PRISTINE_MFS" | cut -d' ' -f1)" = "$PRISTINE_MFS_SHA" ] ||
    { echo "ERROR: mfs does not match recovered root filesystem"; exit 1; }
[ "$(shasum -a 256 "$PRISTINE_INITTAB" | cut -d' ' -f1)" = "$PRISTINE_INITTAB_SHA" ] ||
    { echo "ERROR: inittab does not match recovered inittab.s8000-2"; exit 1; }
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
cp "$PRISTINE_RC" "$ROOT_STAGE/etc/rc"
chmod 700 "$ROOT_STAGE/etc/rc"
cp "$CLEAN_PASSWD" "$ROOT_STAGE/etc/passwd"
chmod 644 "$ROOT_STAGE/etc/passwd"
cp "$PRISTINE_RC_CSH" "$ROOT_STAGE/etc/rc_csh"
chmod 700 "$ROOT_STAGE/etc/rc_csh"
cp "$PRISTINE_MFS" "$ROOT_STAGE/etc/mfs"
chmod 700 "$ROOT_STAGE/etc/mfs"
rm -f "$ROOT_STAGE/etc/umfs"
ln "$ROOT_STAGE/etc/mfs" "$ROOT_STAGE/etc/umfs"
cp "$PRISTINE_INITTAB" "$ROOT_STAGE/etc/inittab"
chmod 600 "$ROOT_STAGE/etc/inittab"
cp "$TTYTYPE" "$ROOT_STAGE/etc/ttytype"
chmod 644 "$ROOT_STAGE/etc/ttytype"
python3 "$DATE_PATCHER" "$ROOT_STAGE/bin/date" "$ROOT_STAGE/etc/datem"
[ "$ROOT_STAGE/zeus" -ef "$ROOT_STAGE/zeus-3.2.1" ] ||
    { echo "ERROR: staged kernels are not hard links"; exit 1; }

echo "== fresh image =="
rm -f "$IMG"
python3 -c "f=open('$IMG','wb');f.truncate($DISK_BLOCKS*512);f.close()"

echo "== root filesystem from clean staging tree =="
SOURCE_DATE_EPOCH="$ROOT_FS_EPOCH" \
    "$RF/mkv7img" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" 0 "$ROOT_STAGE" /

echo "== pristine native ZEUS auxiliary partitions =="
dd if="$NATIVE_USR" of="$IMG" bs=512 seek="$USR_OFF" count="$USR_SIZE" conv=notrunc status=none
dd if="$NATIVE_TMP" of="$IMG" bs=512 seek="$TMP_OFF" count="$TMP_SIZE" conv=notrunc status=none
dd if="$NATIVE_Z" of="$IMG" bs=512 seek="$Z_OFF" count="$Z_SIZE" conv=notrunc status=none

echo "== /dev nodes =="
SOURCE_DATE_EPOCH="$ROOT_FS_EPOCH" \
    "$RF/mkdev" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" "$HERE/devs.txt"
python3 "$HERE/fix_dev_majors.py" "$IMG" "$HERE/devs.txt" "$ROOT_OFF"

echo "== block 0 (autoboot + rootdev + vfs table) =="
python3 "$HERE/mkblock0.py" "$IMG"

echo "== uncompressed CHD =="
rm -f "$CHD"
chdman createhd -i "$IMG" -o "$CHD" --chs "$CHS" --sectorsize 512 --compression none

echo "== install =="
# Loose CHDs must remain writable for ZEUS startup and normal filesystem I/O.
[ ! -e "$INSTALL" ] || chmod u+w "$INSTALL"
cp "$CHD" "$INSTALL"
chmod 644 "$INSTALL"
echo "DONE -> $INSTALL  (documented Model 31 five-region layout)"
