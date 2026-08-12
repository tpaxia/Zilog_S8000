.po 1i
.TH ACCT M Bell
.V 08/15/84 17:38:27
.\"@[$]acct.M	1.5	08/15/84 17:38:27 - Zilog Inc.
.ad
.fi
.SH NAME
acct \- overview of accounting and miscellaneous accounting commands
.SH SYNOPSIS
.B acctdisk
.PP
.B acctdusg
[\fB\-p\fR \fIfile\fR] [\fB\-u \fIfile\fR] > \fIdtmp-file\fR
.PP
\fBaccton\fR [\fIfile\fR]
.PP
\fBacctwtmp\fR [\fIname[line]]\fR \fB>> \fI/usr/adm/wtmp
.SH DESCRIPTION
Accounting software is structured as a set of tools (consisting
of both C programs and shell procedures) that can be used to
build accounting systems.
.BR Acctsh (M)
describes the set of shell procedures developed from C programs.
.PP
Connect time accounting is handled by various programs that write
records into
.IR /usr/adm/wtmp ,
as described in
.BR utmp (5).
The programs described in
.BR acctcon (M)
convert this file into session and charging records,
which are then summarized by
.BR acctmerg (M).
.PP
Process accounting is performed by the ZEUS kernel.
Upon termination of a process, one record per process is
written to a file (normally
.IR /usr/adm/pacct ).
The programs in
.BR acctprc (M)
summarize this data for charging purposes;
.BR acctcms (M)
is used to summarize command usage.
Current process data may be examined using
.BR acctcom (1).
.PP
Process accounting and connect time accounting (or any
accounting records described in
.BR acct (5))
can be merged and summarized into total accounting records by
.B acctmerg
(see \fItacct\fP format in
.BR acct (5)).
.B Prtacct
(see
.BR acctsh (M))
is used to format any or all accounting records.
.PP
.B Acctdisk
reads lines that contain user ID, login name, and number of
disk blocks, and converts them to total accounting
records that can be merged with other accounting records.
.PP
.B Acctdusg
reads its standard input (usually from
.BR "find / \-print" )
and computes disk resource consumption (including indirect
blocks) by login.
.PP
.B Accton
alone turns process accounting off.
If
.I file
is given, it must be the name of an existing file,
to which the kernel appends process accounting records
(see
.BR acct (2)
and
.BR acct (5)).
.PP
.B Acctwtmp
writes a
.BR wtmp (5)
record to its standard output.
The record contains the current time,
.IR name ,
and
.IR line .
If
.I line
is omitted, a value is emitted that is interpreted
by other programs as a reboot.
For more precise accounting, the following are recommended
for use in reboot and shutdown procedures, respectively:
.PP
.RS
acctwtmp \|\*`uname\*` \|>>/usr/adm/wtmp
.br
acctwtmp \|reason \|>>/usr/adm/wtmp
.RE
.SH OPTIONS
.TP
.B \-p
.I file
is the name of the password file.
This option is not needed if the password file is
.IR /etc/passwd .
.TP
.B \-u
records consisting of those file names for which
.I acctdusg
charges no one are placed in
.I file
(a potential source for finding users trying to avoid disk charges).
.SH FILES
.ta \w'/usr/adm/wtmp\ \ \ \ 'u +.5i
.nf
/etc/passwd	used for login name to user \s-1ID\s+1 conversions
/usr/lib/acct	holds all accounting commands listed in
	section M of this manual
/usr/adm/pacct	current process accounting file
/usr/adm/wtmp	login/logoff history file
.fi
.SH SEE ALSO
acctcom(M),
acct(2),
acct(5),
utmp(5),
acctcms(M),
acctcon(M),
acctmerg(M),
acctprc(M),
acctsh(M),
fwtmp(M),
runacct(M).
.br
.I "The PWB/ZEUS Accounting System"
in the ZEUS Utilities Manual
.DT
