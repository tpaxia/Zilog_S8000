# One-shot construction of the documented Model 31 auxiliary filesystems.
# /z initially contains usr.tar; it is remade only after /usr is restored.

onintr failed

echo "Mounting seed /z filesystem"
/etc/mount /dev/z /z
if ($status) goto failed

echo "Creating native /usr filesystem"
/etc/mkfs /dev/rusr 12000 16 224
if ($status) goto failed
/etc/labelit /dev/rusr /usr 1 > /dev/null
/etc/mount /dev/usr /usr
if ($status) goto failed

echo "Restoring /usr from /z/usr.tar"
cd /usr
/bin/tar xvf /z/usr.tar
if ($status) goto failed
cd /

echo "Creating native /tmp filesystem"
/etc/mkfs /dev/rtmp 6000 16 224
if ($status) goto failed
/etc/labelit /dev/rtmp /tmp 1 > /dev/null
/etc/mount /dev/tmp /tmp
if ($status) goto failed

# Reserve directory slots exactly as makenewfs does, so fsck can reconnect
# orphaned files without allocating directory blocks on a damaged filesystem.
foreach dir (/usr/lost+found /tmp/lost+found)
	if (! -d $dir) then
		mkdir $dir
	endif
	/etc/chmog 0750 zeus 0 $dir
	@ j = 318
	while ($j)
		echo > $dir/Z$j
		@ j--
	end
	@ j = 318
	while ($j)
		rm $dir/Z$j
		@ j--
	end
end

sync
/etc/umount /dev/tmp
/etc/umount /dev/usr
/etc/umount /dev/z

echo "Creating native /z filesystem"
/etc/mkfs /dev/rz 104736 16 224
if ($status) goto failed
/etc/labelit /dev/rz /z 1 > /dev/null
/etc/mount /dev/z /z
if ($status) goto failed

mkdir /z/lost+found
/etc/chmog 0750 zeus 0 /z/lost+found
@ j = 318
while ($j)
	echo > /z/lost+found/Z$j
	@ j--
end
@ j = 318
while ($j)
	rm /z/lost+found/Z$j
	@ j--
end

sync
/etc/umount /dev/z

# Put the normal startup script in place for the validation reboot and remove
# the construction-only files from the final root filesystem.
cp /etc/rc.final /etc/rc
chmod 0700 /etc/rc
rm -f /etc/rc.final /etc/native_layout.csh
sync

echo
echo "NATIVE FILESYSTEM BUILD COMPLETE"
echo "Quit MAME completely, then report done."
echo
exit 0

failed:
echo
echo "NATIVE FILESYSTEM BUILD FAILED -- DO NOT REBOOT"
echo
exit 1
