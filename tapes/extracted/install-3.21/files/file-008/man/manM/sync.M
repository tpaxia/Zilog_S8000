.po 1i
.TH SYNC M Bell
.V 08/15/84 17:42:29
.\" @[$]sync.M	1.4	08/15/84 17:42:29 - Zilog Inc.
.ad
.fi
.SH NAME
sync \- update the super block
.SH SYNOPSIS
.B sync
.SH DESCRIPTION
.B Sync
executes the
.B sync
system primitive.
If the system is to be stopped,
.B sync
must be called to insure
file system integrity.
See
.BR sync (2)
for details.
.SH SEE ALSO
sync(2),
update(M).
