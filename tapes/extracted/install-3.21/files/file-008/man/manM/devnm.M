.po 1i
.TH DEVNM M Bell
.V 08/15/84 17:39:34
.\" @[$]devnm.M	1.5  08/15/84 17:39:34 - Zilog Inc.
.ad
.fi
.SH NAME
devnm \- device name
.SH SYNOPSIS
.B devnm
[
.I names
]
.SH DESCRIPTION
.B Devnm
identifies the special file
associated with the mounted file system
where the argument \fIname\fP resides.
.PP
This command is most commonly used by
.I /etc/rc_csh
to construct a mount table entry for the
.I root
device.
.SH EXAMPLE
The command:
.sp
.RS
/etc/devnm /
.RE
.sp
produces
.sp
.RS
zd2 /
.RE
.sp
if
.B /
is mounted on
.IR /dev/zd2 .
.SH FILES
/dev/zd\(**
.br
/dev/md\(**
.br
/dev/smd\(**
.br
/etc/mnttab
.br
/etc/devnm	program
.SH SEE ALSO
setmnt(M).
