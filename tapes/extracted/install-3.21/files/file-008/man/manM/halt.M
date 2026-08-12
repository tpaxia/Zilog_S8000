.po 1i
.TH HALT M Zilog
.V 08/15/84 17:40:20
.\" @[$]halt.M	1.6	08/15/84 17:40:20 - Zilog Inc.
.ad
.fi
.V 08/15/84 17:40:20
.\" @[$]halt.M	1.6 08/15/84 17:40:20 - Zilog Inc.
.SH NAME
halt \- take the system down
.SH SYNOPSIS
.B halt
.SH DESCRIPTION
.B Halt
is a Shell file to halt the system promptly.
It gives a 30-second warning, then system buffers are flushed
and a 
.B kill -1 1
is issued.
After this has been done, 
.B halt
replaces
.I /etc/motd
with
.I /etc/motd.save
if that file exists.
.LP
This command will work only if it is issued by Superuser.
.SH FILES
/etc/halt	the program
.sp
/etc/motd	message of the day file
.sp
/etc/motd.save	message of the day (saved) file
.SH SEE ALSO
down(M),
wall(M),
kill(1).
