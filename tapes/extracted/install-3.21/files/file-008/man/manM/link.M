.po 1i
.TH LINK M Bell
.V 08/15/84 17:40:49
.\" @[$]link.M	1.3	08/15/84 17:40:49 - Zilog Inc.
.ad
.fi
.SH NAME
link, unlink \- exercise link and unlink system calls
.SH SYNOPSIS
\fBlink \fIfile1 file2\fR
.br
\fBunlink \fIfile\fR
.SH DESCRIPTION
.B Link
and
.B unlink
perform their respective system calls on their arguments,
abandoning all error checking.
These commands can only be executed by the super-user.
.SH FILES
/etc/link	the program
.sp
/etc/unlink	the program
.SH SEE ALSO
rm(1),
link(2),
unlink(2).
.SH LIMITATIONS
The programs cannot cross filesystem boundaries.
