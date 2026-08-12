.po 1i
.TH KILLALL M Bell
.V 08/15/84 17:40:43
.\" @[$]killall.M	1.5 $D - Zilog Inc.
.SH NAME
killall \- kill all active processes
.SH SYNOPSIS
.B /etc/killall
[\fI signal\fR ]
.SH DESCRIPTION
.PP
.B Killall
is is a procedure used by
/etc/rc
to kill all active processes not directly related to the
shut down procedure.
.PP
.PP
.B Killall
is chiefly used to terminate all processes with open files
so that the mounted filesystems will be unbusied and can be unmounted.
.PP
.B Killall
sends
.I signal
(see
.BR kill (1))
to all remaining processes not belonging to the above group of exclusions.
If no
.I signal
is specified, a default of
.B 9
is used.
.SH FILES
/etc/rc
.SH SEE ALSO
kill(1),
ps(1),
signal(2),
rc(M).
