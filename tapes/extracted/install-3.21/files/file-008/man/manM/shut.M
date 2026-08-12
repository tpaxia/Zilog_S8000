.po 1i
.TH SHUT M Zilog
.V 08/15/84 17:42:21
.\" @[$]shut.M	1.7	08/15/84 17:42:21 - Zilog Inc.
.ad
.fi
.SH NAME
shut \- warns of system shutdown
.SH SYNOPSIS
.B shut
.I [ dtime btime ]
.SH DESCRIPTION
.B Shut
is called by the shell file "down".
It sends warning messages to users.
The optional arguments,
.I dtime
and
.I btime,
specify the time, in minutes, until
system shutdown and the time between error messages, respectively.
If the arguments are not supplied the user is prompted for them.
At the appropriate times messages are broadcast to all logged-on
users until the final warning message is sent then the program exits.
.LP
At the five minute mark
.B shut
begins to issue warnings at 1 minute intervals.
.SH FILES
/etc/utmp
.SH SEE ALSO
down(M).
.SH DIAGNOSTICS
Diagnostics are intended to be self-explanatory.
