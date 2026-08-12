.po 1i
.TH UUSUB M Bell   
.V 08/15/84 17:42:47 
.\"  @[$]uusub.M	1.8   08/15/84 17:42:47  - Zilog Inc.
.ad
.fi
.SH NAME
uusub \- monitor uucp network
.SH SYNOPSIS
.B uusub
.I [ options ]
.SH DESCRIPTION
.B Uusub
defines a
.B uucp
subnetwork and monitors the connection
and traffic among the members of the subnetwork.
.SH OPTIONS
The following options are available:
.PP
.PD 0
.TP 8
.BI \-a sys\^
Add
.I sys\^
to the subnetwork.
.sp
.TP 8
.BI \-c sys\^
Exercise the connection to the system
.IR sys .
If
.I sys\^
is specified as
.BR all ,
then exercise the connection to all the systems in the subnetwork.
.sp
.TP 8
.BI \-d sys\^
Delete
.I sys\^
from the subnetwork.
.sp
.TP 8
.B \-f
Flush the connection statistics.
.sp
.TP 8
.BI \-l
Report the statistics on connections.
.sp
.TP 8
.B \-r
Report the statistics on traffic amount.
.sp
.TP 8
.BI \-u hr\^
Gather the traffic statistics over the past
.I hr\^
hours.
.PD
.PP
Note: the \fBa\fR, \fBd\fR, and \fBf\fR options may only be executed by
the system administrator.
.sp
The meanings of the connections report are:
.IP
sys #call #ok time #dev #login #nack #other
.PP
where
.I sys\^
is the remote system name,
.I #call\^
is the number of times the local system tries to call
.I sys\^
since the last flush was performed,
.I #ok\^
is the number of successful connections,
.I time\^
is the the latest successful connect time,
.I #dev\^
is the number of unsuccessful connections because
of no available device (e.g. \s-1ACU\s+1),
.I #login\^
is the number of unsuccessful connections because
of login failure,
.I #nack\^
is the number of unsuccessful connections because
of no response (e.g. line busy, system down),
and
.I #other\^
is the number of unsuccessful connections because
of other reasons.
.PP
The meanings of the traffic statistics are:
.IP
sfile sbyte rfile rbyte
.PP
where
.I sfile
is the number of files and
.I sbyte
is the number
of bytes sent over the period of time indicated in the latest
.B uusub
command with the
.BI \-u hr\^
option.
Similarly,
.I rfile\^
and
.I rbyte\^
are the numbers of files and bytes received.
.PP
The command:
.IP
.B "uusub \-c all \-u 24"
.PP
is typically started by \fBcron\fR(M) once a day.
.SH FILES
.PD 0
.TP 1.7i
/usr/spool/uucp/\s-1SYSLOG\s+1
system log file
.TP
/usr/lib/uucp/\s-1L\s+1_sub
connection statistics
.TP
/usr/lib/uucp/\s-1R\s+1_sub
traffic statistics
.PD
.SH SEE ALSO
uucp(1), uustat(1).
