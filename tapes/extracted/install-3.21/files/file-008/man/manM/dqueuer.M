.po 1i
.TH DQUEUER M Zilog
.V 08/15/84 17:39:41
.\" @[$]dqueuer.M	1.7	08/15/84 17:39:41 - Zilog Inc.
.ad
.fi
.SH NAME
dqueuer \- process and remove print queue command requests from
.BR nq
.SH SYNOPSIS
.B dqueuer 
[
.B -rnk
]
.SH DESCRIPTION
.B Dqueuer
takes requests from
.BR nq (1)
and
.BR xq (M)
and prints files on a set of shared devices. 
It communicates with 
.B nq
and
.B xq
through signals and sets of control files.
.B Dqueuer
is meant to run at all times and is usually 
initiated at system boot time through
.I /etc/rc.
.PP
All the devices under the control of
.B dqueuer
are defined by the system administrator in 
.I /usr/spool/queuer/config.
(See Section 7 of the System Administrator Manual.)
.PP
.B Dqueuer
checks to see if the active configuration file, 
.I /usr/spool/queuer/activeconfig,
exists or if the 
.B -r 
option (reread) is set. 
In either case, it parses the raw configuration file,
.I /usr/spool/queuer/config,
and creates the active config file.
.PP
The active configuration file contains the same information 
as the configuration file in a binary, machine convenient 
format and also includes the pid of
.B dqueuer
if it is running. 
It is the active configuration file that
.B nq
and
.B xq
use to process their requests. 
.PP
If the dqueuer is already running when the -r option 
is given, the new process will signal the previous 
dqueuer and exit immediately.  
The signal will cause the current dqueuer process 
to reparse the configuration file and create the
active configuration file.
.PP
The 
.B -n
option (no execute) can be used to print a 
summary of the configuration file, to check for errors, 
without actually changing the active configuration 
file and without bringing up the dqueuer.
.PP
The 
.B -k
option kills the dqueuer, 
although outstanding backends will
finish their current file.
.PP
.B Dqueuer
receives requests for service from
.B nq
and
.B xq.
These programs create files in the directory 
.I /usr/spool/queuer/requestdir
with the appropriate 
information, and then send a signal to
.B dqueuer.
These files contain the information neccessary 
for processing print requests.
.PP
Upon receipt of a signal from either
.B nq
or
.B xq,
.B dqueuer
wakes up and processes any outstanding requests it 
finds in the request directory.
.PP
To actually print files,
.B dqueuer
must be supplied with a set of 'backend' programs that 
are specifically written for each device to be used. 
The names of these backends are supplied to
.B dqueuer
through the configuration file.  
Two are supplied with the queueing package, 
.I /usr/lib/lp
for line printers and /usr/lib/text for
text quality typewriter devices.
.SH FILES
/usr/spool/queuer/config
.br
/usr/spool/queuer/activeconfig
.br
/usr/spool/queuer/statusdir 
.br
/usr/spool/queuer/requestdir
.br
/tmp/queuer        
.br
/usr/spool/queuer/logfile
.fi
.SH SEE ALSO
nq(1),
xq(1),
lp(M),
spool(7),
xq(M).
