.po 1i
.TH UUCLEAN M
.ad
.SH NAME
uuclean \- uucp spool directory clean-up
.SH SYNOPSIS
.B uuclean
.I [ options ] ...
.SH DESCRIPTION
.B Uuclean\^
scans the spool directory for files with the
specified prefix and deletes all those 
older than the specified number of hours.
.SH OPTIONS
.TP 3 
.BI \-d directory\^
Clean
.I directory\^
instead of the spool directory.
.TP 
.B \-m
Send mail to the owner of the file
when it is deleted.
.TP
.BI \-n time\^
Files whose age is more than
.I time\^
hours will be deleted if the prefix
test is satisfied
(default time is 72 hours).
.TP
.BI \-p pre\^
Scan for files with
.I pre\^
as the file prefix.
Up to 10
.B \-p
arguments may be specified.
A
.B \-p
without any
.I pre\^
following will cause all files older than the
specified time to be deleted.
.PP
This program will typically be started by \fBcron\fR(M).
.SH FILES
.PD 0
.TP 1.1i
/usr/lib/uucp
directory with commands used by
\fBuuclean\fR
internally
.TP
/usr/spool/uucp
spool directory
.PD
.SH SEE ALSO
uucp(1), uux(1).
