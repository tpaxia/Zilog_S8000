.po 1i
.TH ACCTMERG M Bell
.V 08/15/84 17:38:39
.\" @[$]acctmerg.M	1.3	08/15/84 17:38:39 - Zilog Inc.
.ad
.fi
.SH NAME
acctmerg \- merge or add total accounting files
.SH SYNOPSIS
.B acctmerg
.B [-aiptuv]
.I [file]
.SH DESCRIPTION
.B Acctmerg
reads its standard input and up to nine additional files,
all in the
.B tacct
format (see
.BR acct (5)),
or an ASCII version.
It merges these inputs by adding records whose keys
(normally user ID and name) are identical, and expects
the inputs to be sorted on those keys.
.SH OPTIONS
.TP
.B \-a
Produce output in ASCII version of
.BR tacct .
.TP
.B \-i
Input files are in ASCII version of
.BR tacct .
.TP
.B \-p
Print input with no processing.
.TP
.B \-t
Produce a single record that totals all input.
.TP
.B \-u
Summarize by user ID, rather than user ID and name.
.TP
.B \-v
Produce output in verbose ASCII format,
with more precise notation for floating point numbers.
.SH EXAMPLES
The following sequence is useful for making "repairs"
to any file kept in this format:
.PP
.RS
.nf
acctmerg \|\-v \|<file1 \|>file2
	\f2edit file2 as desired\fP .\|.\|.
acctmerg \|\-i \|<file2 \|>file1
.fi
.RE
.SH SEE ALSO
acctcom(M),
acct(2),
acct(5),
utmp(5),
acct(M),
acctcms(M),
acctcon(M),
acctprc(M),
acctsh(M),
fwtmp(M),
runacct(M).
