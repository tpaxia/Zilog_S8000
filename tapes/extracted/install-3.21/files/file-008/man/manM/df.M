.po 1i
.TH DF M Bell
.V 08/15/84 17:39:36
.\" @[$]df.M	1.5	08/15/84 17:39:36 - Zilog Inc.
.ad
.fi
.SH NAME
df \- report number of free disk blocks
.SH SYNOPSIS
.B df
[
.B \-t
]
[
.B \-f
.I ] [ file-systems ]
.SH DESCRIPTION
.B Df
prints out the number of free blocks
and free i-nodes
available for on-line file systems
by examining the counts kept in the
super-blocks;
.I file-systems\^
may be specified either by device name (e.g.,
.IR /dev/zd1 )
or by mounted directory name (e.g.,
.IR /usr ).
If
the
.I file-systems\^
argument
is unspecified,
the free space on all of the
mounted file systems
is printed.
.PP
The
.B \-t
flag causes the total allocated block figures to be reported as well.
.PP
If the
.B \-f
flag is given,
only an actual count of the blocks in the
free list is made
(free i-nodes are not reported).
With this option,
.B df\^
will report on raw devices.
.SH FILES
/dev/zd\(**
.br
/dev/md\(**
.br
/dev/smd\(**
.br
/etc/mnttab
.SH SEE ALSO
fsck(1),
filesys(5),
mnttab(5).
