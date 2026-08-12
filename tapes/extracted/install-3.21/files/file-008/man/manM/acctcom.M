.po 1i
.TH ACCTCOM M Bell
.V 08/15/84 17:38:33
.\"@[$]acctcom.M	1.3	08/15/84 17:38:33 - Zilog Inc.
.ad
.fi
.SH NAME
acctcom \- search and print process accounting file(s)
.SH SYNOPSIS
\fBacctcom\fR [[\fIoptions\fR] [\fIfile\fR]\] 
.SH DESCRIPTION
.B Acctcom
reads
.IR file ,
the standard input, or
.IR /usr/adm/pacct ,
in the form described by
.BR acct (5)
and writes selected records to the standard output.
Each record represents the execution of one process.
The output shows:
.sp
.RS
.B COMMAND NAME 
.br
.B USER
.br
.BR TTYNAME 
.br
.B START TIME
.br
.B END TIME
.br
.B REAL (SEC)
.br
.B CPU (SEC)
.br
.B MEAN SIZE(K)
.RE
.sp
and optionally,
.B F
(the
.BR fork / exec
flag: \fB1\fR for \fBfork\fR without \fBexec\fR) and
.B STAT\
(the system exit status).
.PP
The command name is prepended with a
.B #
if it was executed with
.IR super - user
privileges.
If a process is not associated with a known terminal,
a \fB?\fR is printed in the
.B TTYNAME
field.
.PP
If no \fIfiles\fR are specified and if the standard input
is associated with a terminal or
.I /dev/null
(as is the case when using
.B &
in the shell),
.I /usr/adm/pacct
is read, otherwise the standard input is read.
.PP
If any
.I file
arguments are given, they are read in their respective order.
Each file is normally read forward, i.e., in chronological
order by process completion time.
The file
.I /usr/adm/pacct
is usually the current file to be examined;
a busy system may need several files,
in which case all but the current will be found in
.BR /usr/adm/pacct? .
.SH OPTIONS
.TP 12
.B \-b
Read backwards, showing latest commands first.
.TP
.BI \-C \ time
Show only those processes that exceed
.I time
that indicates the total CPU time.
.TP
.BI \-d \ mm/dd
Any
.I time
arguments following this flag are assumed to occur on the
given month and day, rather than during the last 24 hours.
This is needed for looking at old files.
.TP
.BI \-e \ time
Show only those processes that existed on or before
.IR time .
Using the same
.I time
for both
.B \-s
and
.B \-e
shows the processes that existed at
.IR time .
.TP
.B \-f
Print the
.BR fork / exec
flag and system exit status columns in the output.
.TP
.BI \-g \ group
Show only processes belonging to
.IR group .
The \fIgroup\fP may be designated by either the
group ID or group name.
.TP
.B \-h
Instead of mean memory size, show the fraction of total available
CPU time consumed by the process during its execution.
This "hog factor" is computed as:
.nf
               (total\ CPU\ time)/(elapsed\ time).
.fi
.TP
.BI \-H \ factor
Show only processes that exceed
.IR factor ,
where factor is the "hog factor" as explained in option
.BR \-h \ above.
.TP
.B \-i
Print columns containing the I/O counts in the output.
.TP
.B \-k
Instead of memory size, show total kcore-minutes.
.TP
.BI \-l \ line
Show only processes belonging to terminal
.I /dev/line.
.TP
.B \-m
Show mean core size (the default).
.TP
.BI \-n \ pattern
Show only commands matching
.I pattern
that may be a regular expression as in
.BR ed (1)
except that \fB+\fP means one or more occurrences.
.TP
.BI \-O \ time
Show only those processes with operating system CPU time exceeding
.IR time .
.TP
.B \-r
Show CPU factor (user time/(system-time + user-time).
.TP
.BI \-s \ time
Show only those processes that existed on or after
.IR time ,
given in the form
.IB hr : min : sec \fR.\fP
The
.BI : sec
or
.BI : min : sec
may be omitted.
.TP
.B \-t
Show separate system and user CPU times.
.TP
.BI \-u \ user
Show only processes belonging to
.I user
that may be specified by: a user ID, a login name that is
then converted to a user ID, a \fB#\fP which designates only
those processes executed with
.IR super - user
privileges, or
.B ?
which designates only those processes associated with unknown
user IDs.
.TP
.B \-v
Exclude column headings from the output.
.PP
Listing options together has the effect of a logical \fIand\fR.
.SH FILES
/etc/passwd
.br
/usr/adm/pacct
.br
/etc/group
.SH SEE ALSO
ps(1),
su(1),
acct(2),
acct(5),
utmp(5),
acct(M),
acctcms(M),
acctcon(M),
acctmerg(M),
acctprc(M),
acctsh(M),
fwtmp(M),
runacct(M).
.SH LIMITATIONS
.B Acctcom
only reports on processes that have terminated; use
.BR ps (1)
for active processes.
.br
.DT
