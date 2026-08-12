.po 1i
.TH UPDATE M Bell
.V 08/15/84 17:42:40
.\" @[$]update.M	1.6	08/15/84 17:42:40 - Zilog Inc.
.ad
.fi
.SH NAME
update \- periodic buffer flush
.SH SYNOPSIS
.B update
.SH DESCRIPTION
.B Update
causes a 
.B sync
every 30 seconds.
Since
.B update
never exits, it should only be executed once.
This is best done by running
.B update
from the 
file
.I  /etc/rc_csh
see
.BR init (M).
.SH FILES
/etc/update	the program
.SH SEE ALSO
sync(2).
