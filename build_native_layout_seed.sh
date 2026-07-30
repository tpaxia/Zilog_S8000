#!/bin/bash
# Build the one-shot image used to create /usr, /tmp and /z with ZEUS mkfs.
set -euo pipefail

HERE=/Users/paxia/Projects/Zilog_S8000
RF=$HERE/tools/retro-fuse
BUILD=$HERE/build
CSVOL=/Volumes/ZeusFS
STAGE=$CSVOL/clean-stage
ROOT_STAGE=$STAGE/root
USR_STAGE=$STAGE/usr
TMP_STAGE=$STAGE/tmpfs
Z_STAGE=$STAGE/zfs
IMG=$BUILD/s8000_native_layout_seed.img
CHD=$BUILD/s8000_native_layout_seed.chd
USR_TAR=$BUILD/usr.tar
USR_LIST=$BUILD/usr-files.list

DISK_BLOCKS=131936
USR_SIZE=12000; USR_OFF=0
ROOT_SIZE=6000; ROOT_OFF=15200
TMP_SIZE=6000; TMP_OFF=21200
Z_SIZE=104736; Z_OFF=27200
CHS=589,7,32

# Start from the normal clean staging pass and image overlays.
"$HERE/rebuild_fs.sh"

echo "== native /usr restore archive =="
(
	cd "$USR_STAGE"
	find . -type f -print | LC_ALL=C sort > "$USR_LIST"
)
bsdtar -cf "$USR_TAR" --format v7tar --no-recursion \
	--uid 0 --gid 0 --uname root --gname root \
	-C "$USR_STAGE" -T "$USR_LIST"

echo "== one-shot construction overlays =="
cp "$USR_TAR" "$Z_STAGE/usr.tar"
chmod 600 "$Z_STAGE/usr.tar"
cp "$ROOT_STAGE/etc/rc" "$ROOT_STAGE/etc/rc.final"
cp "$HERE/systemIII/rc.native-layout-build" "$ROOT_STAGE/etc/rc"
chmod 700 "$ROOT_STAGE/etc/rc" "$ROOT_STAGE/etc/rc.final"
cp "$HERE/systemIII/native_layout.csh" "$ROOT_STAGE/etc/native_layout.csh"
chmod 700 "$ROOT_STAGE/etc/native_layout.csh"
# The native build takes longer than init's normal five-minute rc limit.
# Patch only this disposable seed; native_layout.csh restores the ordinary rc,
# and the final image can return to the unmodified init after capture.
python3 "$HERE/patch_init_rclim.py" "$ROOT_STAGE/etc/init" 1800

echo "== seed disk =="
truncate -s $((DISK_BLOCKS * 512)) "$IMG"
"$RF/mkv7img" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" 0 "$ROOT_STAGE" /
"$RF/mkv7img" "$IMG" "$USR_SIZE" "$USR_OFF" 0 "$USR_STAGE" /
"$RF/mkv7img" "$IMG" "$TMP_SIZE" "$TMP_OFF" 0 "$TMP_STAGE" /
"$RF/mkv7img" "$IMG" "$Z_SIZE" "$Z_OFF" 0 "$Z_STAGE" /
"$RF/mkdev" "$IMG" "$ROOT_SIZE" "$ROOT_OFF" "$HERE/devs.txt"
python3 "$HERE/fix_dev_majors.py" "$IMG" "$HERE/devs.txt" "$ROOT_OFF"
python3 "$HERE/mkblock0.py" "$IMG"

echo "== seed CHD =="
rm -f "$CHD"
chdman createhd -i "$IMG" -o "$CHD" --chs "$CHS" \
	--sectorsize 512 --compression none
echo "DONE -> $CHD"
