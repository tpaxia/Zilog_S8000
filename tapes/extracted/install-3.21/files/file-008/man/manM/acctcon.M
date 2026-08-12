.po 1i
.TH ACCTCON M Bell
.V 08/15/84 17:38:37
.\" @[$]acctcon.M	1.3	08/15/84 17:38:37 - Zilog Inc.
.ad
.fi
.SH NAME
acctcon \- connect-time accounting
.SH SYNOPSIS
\fBacctcon1\fR [\fIoptions\fR]
.PP
.B acctcon2
.SH DESCRIPTION
.B Acctcon1
converts a sequence of login/logoff records read from its
standard input to a sequence of records, one per login session.
Its input should normally be redirected from
.I /usr/adm/wtmp.
Its output is ASCII, giving device, user ID, login name,
prime connect time (seconds), non-prime connect time (seconds),
session starting time (numeric), and starting date and time.
.PP
.B Acctcon2
expects as input a sequence of login session records and converts them
into total accounting records
(see
.B tacct
format in
.BR acct (5)).
.SH OPTIONS
.TP
.BI \-l " file"
.I File
is created to contain a summary of line usage showing line name,
number of minutes used, percentage of total elapsed time used,
number of sessions charged, number of logins, and number of logoffs.
This file helps track line usage, identify bad lines,
and find software and hardware oddities.
Both hang-up and termination of the login shell generate
a logoff record, so that the number of logoffs is often twice
the number of sessions.
.TP
.BI \-o " file"
.I File
is filled with an overall record for the accounting period,
giving starting time, ending time, number of reboots,
and number of date changes.
.TP
.B \-p
Print input only, showing line name, login name,
and time (in both numeric and date/time formats).
.TP
.B \-t
.B Acctcon1
maintains a list of lines on which users are logged in.
When it reaches the end of its input, it emits a session
record for each line that still appears to be active.
It normally assumes that its input is a current file,
so that it uses the current time as the ending time for
each session still in progress.
The
.B \-t
flag causes it to use the last time found in its input,
assuring reasonable and repeatable numbers for non-current files.
.SH EXAMPLES
These commands are typically used as shown below.
The file
.B ctmp
is created only for the use of
.BR acctprc (M)
commands:
.PP
acctcon1 \-t \-l lineuse \-o reboots <wtmp \(bv sort +1n +2 >ctmp
.br
acctcon2 <ctmp \(bv acctmerg >ctacct
.SH FILES
/usr/adm/wtmp
.SH SEE ALSO
acctcom(M),
acct(2),
acct(5),
utmp(5),
acct(M),
acctcms(M),
acctmerg(M),
acctprc(M),
acctsh(M),
fwtmp(M),
runacct(M).
.SH LIMITATIONS
The line usage report is confused by date changes.
Use \fBwtmpfix\fR (see
.BR fwtmp (M))
to correct this situation.
