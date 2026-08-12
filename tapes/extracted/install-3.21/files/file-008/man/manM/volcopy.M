.po 1i
.TH VOLCOPY M Bell
.V 08/15/84 17:42:50
.\" @[$]volcopy.M	1.6 08/15/84 17:42:50 - Zilog Inc.
.ad
.fi
.SH NAME
volcopy \- copy filesystems with label checking
.SH SYNOPSIS
.B /etc/volcopy
[\fIoptions\fR] \fIfsname special1 volname1 special2 volname2\fR
.SH DESCRIPTION
.B Volcopy\^
makes a literal copy of the filesystem
using
a blocksize matched to the device.
.SH OPTIONS
.TP
.B \-a
Invokes a verification sequence
requiring a positive operator response instead of the
standard 10 second delay before the copy is made.
.TP
.B \-s
Invokes the
"\s-1DEL\s+1 if wrong"
verification sequence (default).
.PP
\fIOptions\fP used only with tapes:
.TP
.BI \-feet size
Size of reel in feet (i.e., 1200/2400).
.TP
.BI \-reel num
Beginning reel number for a restarted copy.
.TP
.B \-buf
Use double buffered I/O.
.TP
.BI \-i inode
Inode number in filesystem of listing produced by 
.BR ff (M).
.TP
.B \-l
Create a tape label where required.
.PP
The program requests length
information if it is not given on the
command line or is not recorded on an input tape label.
If the filesystem is too large to fit on one reel,
.B volcopy\^
will prompt for additional reels.
Labels of all reels are checked.
Tapes may be mounted alternately on two or more drives.
.PP
The
.I fsname\^
argument represents the mounted name (e.g.: root, u1, etc.)
of the filesystem being copied.
.PP
The
.I special\^
should be the physical disk section or tape (e.g.:
/dev/rsmd15, /dev/rmt0,
etc.).
.PP
The
.I volname\^
is the physical volume name (e.g.: pk3, t0122, etc.)
and should match the external label sticker.
Such label names are limited to six or fewer characters.
.I Volname
may be
.B \-
to use the existing volume name.
.PP
.I Special1\^
and
.I volname1\^
are the device and volume from which the copy of the filesystem is
being extracted.
.I Special2\^
and
.I volname2\^
are the target device and volume.
.PP
.I Fsname\^
and
.I volname\^
are recorded in the last 12 characters
of the superblock (char fsname[6], volname[6];).
.SH FILES
/etc/log/filesave.log	a record of filesystems/volumes copied
.SH "SEE ALSO"
filsys(5)
.SH LIMITATIONS
Only device names beginning /dev/[n]rct?
or /dev/[fsn]rmt?
are treated as tapes.
Tape record sizes are determined both by density and by
drive type.
.br
If a filesystem copy requires multiple tape volumes, then
that filesystem copy must start at the beginning of the first
reel.
