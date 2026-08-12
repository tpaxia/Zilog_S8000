.po 1i
.TH ACCTPRC M Bell
.V 08/15/84 17:38:41
.\" @[$]acctprc.M	1.3	08/15/84 17:38:41 - Zilog Inc.
.ad
.fi
.SH NAME
acctprc \- process accounting
.SH SYNOPSIS
\fBacctprc1\fR [\fBctmp\fR]
.PP
.B acctprc2
.SH DESCRIPTION
.B Acctprc1
reads input in the form described by
.BR acct (5),
adds login names corresponding to user IDs, then writes
for each process an ASCII line giving user ID, login name,
prime CPU time (tics), non-prime CPU time (tics),
and mean memory size (in 64-byte units).
If
.B ctmp
is given, it is expected to contain a list of login sessions,
in the form described in
.BR acctcon (M),
sorted by user ID and login name.
If this file is not supplied,
it obtains login names from the password file.
The information in
.B ctmp
helps it distinguish among different login names that
share the same user ID.
.PP
.B Acctprc2
reads records in the form written by
.BR acctprc1 ,
summarizes them by user ID and name, then writes the sorted
summaries to the standard output as total accounting records.
.SH EXAMPLES
These commands are typically used as shown below:
.PP
.RS
acctprc1 \|ctmp \|</usr/adm/pacct \|\(bv \|acctprc2 \|>ptacct
.RE
.SH FILES
/etc/passwd
.SH SEE ALSO
acctcom(M),
acct(2),
acct(5),
utmp(5),
acct(M),
acctcms(M),
acctcon(M),
acctmerg(M),
acctsh(M),
fwtmp(M),
runacct(M).
.SH LIMITATIONS
Although it is possible to distinguish among login names
that share user IDs for commands run normally,
it is difficult to do this for those commands run from
.BR cron (M),
for example.
More precise conversion can be done by faking login sessions
on the console via the
.B acctwtmp
program in
.BR acct (M).
