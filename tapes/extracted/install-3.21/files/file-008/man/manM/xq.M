.po 1i
.TH XQ M Zilog
.V  08/15/84 17:42:59
.\" @[$]xq.M	1.24 08/15/84 17:42:59 - Zilog Inc.
.ad
.fi
.SH NAME
xq  \- examine or delete requests from the line printer spooler
.SH SYNOPSIS
.B xq
.I [ modifiers ] [ options ]
.SH DESCRIPTION
The ZEUS queuing system allows the enqueuing, examination/deletion, and 
dispatching (dequeuing) of print requests.
\fBXq\fR  
examines, and may delete, jobs queued for the print devices attached
to the system.
.sp
The system administrator and the system group are capable of executing
all commands described in \fBxq\fR(1). By specifying the \fB-o\fR modifier
as the first argument to \fBxq\fR, they may exercise requests against
queued files they do not own.  
.sp
\fBXq\fR takes two types of arguments: modifiers and options. Only one
option per \fBxq\fR entry may be made, but the option may be specified
with either or both of the two modifiers. The modifiers must precede the
options on the command line; and if  
both modifiers are specified, the \fB-o\fR modifier must
precede the \fB-q\fR modifier. 
.sp 
With no arguments,
.B xq
gives a status list of all the queues and devices.
.sp
Additional options can be used to control operation of
.BR dqueuer (M)
and the queues and devices involved.
.SH MODIFIERS
.TP 8
.B \-o
Although this 
requester is not owner of the file the \fBxq\fR request references,
nevertheless honor requester as owner. Requester must be super-user or
member of the systems group. Again, this modifier must be the first argument to
\fBxq\fR.  
.TP 8
.BI \-q " queue:device"  
Specifies the queue and device that are being referenced in a request
against a printing queue-member. This modifier must be the first
argument to \fBxq\fR, or the second, if the 
.B -o 
modifier is also specified.
.SH OPTIONS
.TP 8
.B  \-b
Backup device.
Causes a device to backup its output one page (used when
a printer has become fouled, or needs new paper loaded).
.TP 8
\fB\-cp\fR [\fBR, N, D\fR]
Set the priority of the queue specified with a preceding \fB-q\fR modifier to
Rush, Normal or
Deferred. This acts as a mask for job priorities set with the \fB-p\fR
option of \fBnq\fR(1).
Lowercase letters may be used for
\fBR\fR, \fBN\fR,
or
\fBD\fR.
A space must exist between the \fB-cp\fR and
\fBR\fR, \fBN\fR,
or
\fBD\fR.
.TP 8
\fB\-cs\fR [\fBF, S\fR]
Change the selection criteria (the order that jobs will be executed in)
to FIFO or SIZE for the queue specified with a preceding \fB-q\fR modifier. 
SIZE is smaller jobs first.
Lowercase letters may be used for
\fBF\fR or \fBS\fR. 
A space must exist between the \fB-cs\fR and
\fBF \fRor \fBS\fR.
.TP 8
\fB\-d \fISEQ#\fR
Delete from the queue the not-printing queue-member whose sequence
number is specified by
\fISEQ#\fR.
At the time a request is queued, the queue-member is assigned a       
sequence number which is available for reference UNTIL the
file begins printing.
Execution of an 
.BR xq
command with no options reveals a SEQN header in the first column
where sequence numbers assigned queue-members are given.
.TP 8
.B  \-Dd
Down device.
Sets a device to the "DOWN"  state.
This is commonly used if a printer is temporarily out of service, 
or to interrupt normal service.
A device designated as "DOWN" will continue to print a file in
progress, but will not be selected for printing additional requests.
.TP 8
.B  \-Dq
Down queue.
Sets a queue to the "DOWN" state.
No requests to this queue will be accepted while its status
is "DOWN", nor can any  devices in this queue be accessed.
This step should only be used if all devices in a queue are likely
to be down for an extended period of time.
.TP 8
.B  \-r
Restart indicated \fIqueue:device\fR.
Causes printing of the current file on the indicated device to be started 
over.
This command is used to restart requests when a printer
becomes fouled.
.TP 8
.BR  \-s [\fBkd\fR]
Stop printing.
Causes printing on specified device to stop immediately.
If 
.B k 
is specified, the file currently printing is kept in the queue; 
otherwise it is deleted.
If 
.B d 
is specified, the status of the device affected is 
set to "DOWN" 
to temporarily prevent future printing.
.TP 8
.B  \-Ud
Up device.
Makes a device available for print selection (see \fB-Dd\fR).
.bp
.TP 8
.B  \-Uq
Up queue.
Makes a queue available for print requests (see \fB-Dq\fR).
.SH EXAMPLES
.nf
	\fBxq -d \fISEQ#\fR 
.fi
.ad
.sp
The above example deletes the not-printing queue-member whose sequence number
is given in SEQ#.      
.sp
.nf
	\fBxq -q lpr:1 -sk\fR 
.ad
.fi
.sp
The above example says: stop printing, but retain in the queue, the currently
printing file assigned to the lpr queue, device 1. 
.sp
The user may control the order in which members of a selected queue
are printed. The ordering
may be on the basis of chronology or size of job. When first-in, first-out
selection criteria is to be implemented, the command is
.sp
.nf
	\fBxq -q lpr -cs F\fR
.sp
.fi
The above example sets the selection criteria for all subsequent requests
against the lpr queue to first-in, first-out (FIFO). This remains
in effect until contradicted by a \fB-cs S\fR specification. When specified,
the \fB-cs S\fR sets selection criteria to size-of-job, where SMALLEST
jobs are printed first. Note that selection criteria cannot be specified at
the device level; "\fBxq -q lpr:1 -cs F\fR" is incorrect for this reason. 
Note the space between the \fB-cs\fR and the \fBF\fR. The default selection
criteria is set within the particular system configuration during \fBsysgen\fR.
.sp
.nf
	\fBxq -q text -cp R\fR
.sp 
.fi
Using the \fB-p\fR option, print requests
can be assigned a job-priority of RUSH, NORMAL, or DEFERRED when enqueued
with \fBnq\fR(1). In addition, it is possible to 
set a priority for the entire queue with 
\fBxq\fR that
masks the job priority set with \fBnq\fR. The
above example sets the text queue priority mask to RUSH, with the
result that only print requests enqueued in the text queue
at a job-priority level of RUSH will be honored. If the queue priority mask is 
NORMAL,
only jobs enqueued at a job-priority level of NORMAL or RUSH will be honored. If
the queue-priority mask is DEFERRED, all job priorities will be 
honored. Again, this
mask cannot be set at the device level within the queue.
.sp
To bring down and to bring up a device, the respective commands are:
.nf
.sp
	\fBxq -q \fIque:dev \fB-Dd\fR

	\fBxq -q \fIque:dev \fB-Ud\fR
.fi
.sp
To bring down and to bring up an entire queue, the respective commands are:
.nf
.sp
	\fBxq -q \fIque \fB-Dq\fR 
   
	\fBxq -q \fIque \fB-Uq\fR
.fi
.SH FILES
.nf
/usr/spool/queuer/activeconfig	active configuration file
.br
/usr/spool/queuer/logfile
.br
/usr/spool/queuer/statusdir
.br
/usr/spool/queuer/requestdir
.br
/tmp/queuer
.fi
.SH SEE ALSO
nq(1),
xq(1),
lp(M),
dqueuer(M).
.SH DIAGNOSTICS
If any part of the spooling system appears to have inconsistencies,
.BR xq
will print an error and log it in the spooler error log file.
