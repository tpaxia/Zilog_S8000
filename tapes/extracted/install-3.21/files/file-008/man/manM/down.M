.po 1i
.TH DOWN M Zilog
.V 08/15/84 17:39:38
.\" @[$]down.M	1.10 08/15/84 17:39:38 - Zilog Inc.
.ad
.fi
.SH NAME
down \- take the system down
.SH SYNOPSIS
.B down
[ 
.I " dtime btime "
]
.SH DESCRIPTION
.B Down
is a Shell script that can be used to
take the system down in an orderly manner.
.LP
The arguments,
.I dtime
and
.I btime,
can be used to specify the time, in minutes, until system
shutdown and the time between warning messages, respectively.
If these arguments are not specified the user is prompted for them.
.LP
At the appropriate times a message is sent to all logged in
users telling them how many minutes until system shutdown.
When the total time for system shutdown has elapsed all system
buffers are flushed and a 
.B kill -1 1
is issued.
This is done by invoking 
.BR halt (M).
.LP
A line is added to the message-of-the-day file, saying that the
system will be taken down shortly.
The previous contents of the \fImotd\fR file are saved to be
restored after the system has been halted.
.SH RESTRICTIONS
This command will work only if issued by Superuser.
.B Down
will not let you take the system down any sooner than 5
minutes from the current time.
If you specify a time until shutdown that is less than 5 minutes
.B down
will assume 5 minutes, and tell you so.
If you want to take the system down now, but in an
orderly manner, use
.BR halt (M).
.SH FILES
/etc/motd	message of the day file
.sp
/etc/motd.save 	message of the day file (saved)
.SH SEE ALSO
kill(1),
halt(M).
