.po 1i
.TH MOUNT M Bell
.V 08/15/84 17:41:21
.\" @[$]mount.M	1.5  08/15/84 17:41:21 - Zilog Inc.
.ad
.fi
.SH NAME
mount, umount \- mount and dismount file system
.SH SYNOPSIS
.B mount
.I [ special directory [
.B \-r
] ]
.PP
.B umount
.I special
.SH DESCRIPTION
.B Mount
announces to the system that a removable file system
is present on the device
.IR special .
The
.I directory
must exist already; it becomes the name of the root of the
newly mounted file system.
.PP
These commands maintain a table of mounted devices.
If invoked with no arguments,
.B mount
prints the table.
.PP
The optional last argument indicates that the file
is to be mounted read-only.
Physically write-protected and magnetic tape file systems must
be mounted in this way or errors will occur when access times
are updated, whether or not any explicit write is attempted.
.PP
.B Umount
announces to the system that the removable file system previously
mounted on device
.I special
is to be removed.
.SH FILES
/etc/mnttab	mount table
.sp
/etc/mount	the program
.sp
/etc/umount	the program
.SH SEE ALSO
mount(2),
mnttab(5).
.SH DIAGNOSTICS
.B Mount
issues a warning if the file system to be mounted
is currently mounted under another name.
.PP
.B Umount
complains if the special file is not mounted or if it is busy.
The file system is busy if it contains an open file or some
user's working directory.
.SH LIMITATIONS
Some degree of validation is done on the file system, however
it is generally unwise to mount garbage file systems.
