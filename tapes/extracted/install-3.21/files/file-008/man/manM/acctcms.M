.po 1i
.TH ACCTCMS M Bell
.V 08/15/84 17:38:31
.\" @[$]acctcms.M	1.3	08/15/84 17:38:31 - Zilog Inc.
.ad
.fi
.SH NAME
acctcms \- command summary from per-process accounting records
.SH SYNOPSIS
\fBacctcms\fR [\fIoptions\fR] \fIfiles\fR
.SH DESCRIPTION
.B Acctcms
reads one or more
.IR files ,
normally in the form described in
.BR acct (5).
It adds all records for processes that executed
identically-named commands, sorts them, and writes them to the
standard output, normally using an internal summary format.
.SH OPTIONS
.TP
.B \-a
Print output in ASCII rather than in the internal summary format.
The output includes command name, number of times executed,
total kcore-minutes, total CPU minutes, total real minutes,
mean size (in K), mean CPU minutes per invocation,
and "hog factor", as in
.BR acctcom (M).
Output is normally sorted by total kcore-minutes.
.TP
.B \-c
Sort by total CPU time, rather than total kcore-minutes.
.TP
.B \-j
Combine all commands invoked only once under "***other".
.TP
.B \-n
Sort by number of command invocations.
.TP
.B \-s
Any file names encountered hereafter are already in internal
summary format.
.SH EXAMPLES
A typical sequence for performing daily command accounting and
for
maintaining a running total is:
.PP
.RS
.nf
acctcms \|file \|.\|.\|. \|>today
cp \|total \|previoustotal
acctcms \|\-s \|today \|previoustotal \|>total
acctcms \|\-a \|\-s \|today
.fi
.RE
.SH SEE ALSO
acctcom(M),
acct(2),
acct(5),
utmp(5),
acct(M),
acctcon(M),
acctmerg(M),
acctprc(M),
acctsh(M),
fwtmp(M),
runacct(M).
