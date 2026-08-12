.po 1i
.TH MFS M Zilog
.V 08/15/84 17:41:02
.\"@[$]mfs.M	1.3	08/15/84 17:41:02 - Zilog Inc.
.ad
.fi
.SH NAME
mfs \- mount all file systems
.br
umfs \- unmount all file systems
.SH SYNOPSIS
.B mfs
.br
.B umfs
.SH DESCRIPTION
.B Mfs
is a shell script used to mount all 
file systems in the current configuration.
It is intended that mfs be run after
.BR fsck (M)
has run successfully.
Note that if the system's disk 
configuration is changed from the default,
.I /etc/mfs
must be changed accordingly.
.B Umfs
is a shell script used to un-mount all file systems in the current
configuration.
.SH FILES
/etc/mtab
.sp
/dev/zd*
.sp
/etc/mfs	the program
.sp
/etc/umfs	the program
.SH SEE ALSO
fsck(M),
mount(M),
mtab(5).
.SH LIMITATIONS
If
.B mfs
is not run before bringing the system up multi-user,
.I /usr
will not mount correctly.
This is because the system creates several files in
.I /usr
after going multi-user and keeps them open as long as the system is
running.
So in order to mount 
.I /usr,
the system must be brought back to
single user mode.
.PP
.B Mfs/umfs
will not mount/unmount  
.I /usr
if 
.BR cron (M)
.BR update (M)
or
.BR dequeuer (M)
are running, or if accounting (
.BR acct (M))
is on.
