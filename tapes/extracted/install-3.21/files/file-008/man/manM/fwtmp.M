.po 1i
.TH FWTMP M Bell
.V 08/15/84 17:40:10
.\" @[$]fwtmp.M	1.3	08/15/84 17:40:10 - Zilog Inc.
.ad
.fi
.SH NAME
fwtmp, wtmpfix \- manipulate wtmp records
.SH SYNOPSIS
\fBfwtmp\fR [\fB\-ic\fR]
.br
\fBwtmpfix\fR [\fIfiles\fR]
.SH DESCRIPTION
.B Fwtmp
reads from the standard input and writes to the
standard output, converting binary records of the type found in
.I wtmp
to formated ASCII records.
The ASCII version is useful to enable editing, via
.BR ed (1),
bad records or general purpose maintenance of the file.
.B Wtmpfix
examines the standard input or named files in
.B wtmp
format, corrects the time/date stamps to make the
entries consistent, and writes to the standard output.
A \fB\-\fR can be used in place of \fIfiles\fR to indicate
the standard input.
If time/date corrections are not made,
.B acctcon1
will fault when it encounters certain date change records.
.PP
Each time the date is set while operating in multi-user
mode, a pair of date change records are written to
.IR /usr/adm/wtmp .
The first record is the old date denoted
by \fB\|\fR in the name field.
The second record specifies the new date and is
denoted by a \fB{\fR in the name field.
.B Wtmpfix
uses these records to synchronize all time stamps in the file.
.SH OPTIONS
.TP
.B \-ic
Used to denote that input is in ASCII form,
and output is to be written in binary form.
.SH FILES
/usr/adm/wtmp
.br
/usr/include/utmp.h
.SH SEE ALSO
acctcom(M),
acct(2),
acct(5),
utmp(5),
acct(M),
acctcms(M),
acctcon(M),
acctmerg(M),
acctprc(M),
acctsh(M),
runacct(M).
