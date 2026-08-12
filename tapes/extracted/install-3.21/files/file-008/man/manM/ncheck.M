.po 1i
.TH NCHECK M Bell
.V 08/15/84 17:41:26
.\" @[$]ncheck.M	1.4	08/15/84 17:41:26 - Zilog Inc.
.ad
.fi
.SH NAME
ncheck  \- generate names from i-numbers
.SH SYNOPSIS
.B ncheck
[
.B \-i
.I numbers ] [
.B \-as
.I ] [ filesystem ]
.SH DESCRIPTION
.B Ncheck
generates a pathname vs. i-number list of all files
on the file system specified.
Names of directory files are followed by `/\fB.\fR'.
The
.B \-i
option reduces the report to only those files whose i-numbers follow.
The
.B \-a
option allows printing of the names
.RB ` . '
and
.RB ` .. ',
which are ordinarily suppressed.
The
.B \-s
option reduces the report to special files and files
with set-user-ID mode;
it is intended to discover concealed violations of security policy.
.PP
The report is in no special order, so sorting may be desirable.
.SH SEE ALSO
sort(1),
dcheck(M),
icheck(M).
.SH DIAGNOSTICS
When the filesystem structure is improper, `??' denotes
the `parent' of a parentless file and
a pathname beginning with `...' denotes a loop.
