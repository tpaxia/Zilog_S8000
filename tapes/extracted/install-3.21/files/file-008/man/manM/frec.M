.po 1i
.TH FREC M Bell
.V 08/15/84 17:39:59
./" @[$]frec.M	1.5 08/15/84 17:39:59 - Zilog Inc.
.SH NAME
.ad
.fi
frec \- recover files from a backup tape
.SH SYNOPSIS
.B /etc/frec
[ \fB\-p \fIpath\fR]
[ \fB\-f \fIreqfile\fR]
[ \fB\-l \fIname\fR]
.I raw-tape
.I i-number : name
.B .\|.\|.
.SH DESCRIPTION
.B Frec\^
recovers files 
from the specified
.I raw-tape
backup tape written by \fBvolcopy\fR(M) using the
.IR i-numbers .
The data for each recovery request will be written into the
file given by
.IR name .
The
.B \-p
option allows you to specify a default prefixing
.I path 
different from your current working directory.
This will be prefixed to any
.I names
that are not fully qualified, i.e.
that do not begin with "\fB/\fR"
or "\fB./\fR".
If any directories are missing in the paths of recovery
.I names\^
they will be created.
.SH OPTIONS
.TP 16
.BI \-p " path"
Specifies a prefixing
.I path\^
to be used to fully qualify any names
that do not start with "\fB/\fR"
or "\fB./\fR".
.TP 16
.BI \-f " reqfile"
Specifies a file which contains recovery requests. The format is
.I i-number:newname,
one per line.
.TP 16
.BI \-l " name"
Gets the listing file of filesystem contents and puts it into 
.IR name .
This listing contains the name and inode number of each file on the
tape written by \fBvolcopy\fR(M).
.SH EXAMPLES
To recover a file, i-number 1216 when backed-up, into a file
named 'junk'
in your current working directory:
.PP
.RS
.B frec \|/dev/rmt0 \|1216:junk
.RE
.PP
To recover files with i-numbers 14156, 1232, and 3141 into files 
/usr/src/cmd/a, /usr/src/cmd/b, and
/usr/joe/a.c:
.PP
.RS
.B frec \|\-p \|/usr/src/cmd \|/dev/rmt0 \|14156:a \|1232:b
.B \|3141:/usr/joe/a.c
.RE
.PP
.SH "SEE ALSO"
cpio(1), ff(M), volcopy(M).
.SH LIMITATIONS
While paving a path (i.e. creating the intermediate directories
contained in a pathname) 
.B frec
can only recover inode fields for those directories contained
on the tape and requested for recovery.
