.po 1i
.TH WALL M Bell
.V 08/15/84 17:42:55
.\" @[$]wall.M	1.4	08/15/84 17:42:55 - Zilog Inc.
.ad
.fi
.SH NAME
wall  \- write to all users
.SH SYNOPSIS
.B wall
.SH DESCRIPTION
.B Wall
reads its standard input until an end-of-file.
It then sends this message, preceded by `Broadcast Message ...',
to all logged in users.
.PP
The sender should be super-user to override
any protections the users may have invoked.
.SH FILES
/etc/wall 	the program
.sp
/dev/tty?
.sp
/etc/utmp
.SH SEE ALSO
mesg(1),
write(1).
.SH DIAGNOSTICS
"Cannot send to 
.I name"
if the terminal is write-protected (see 
.BR mesg (1)).
.SH LIMITATIONS
Some protection should be possible to avoid interfering with
communications occurring over a terminal line.
