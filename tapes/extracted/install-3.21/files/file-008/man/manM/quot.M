.po 1i
.TH QUOT M Bell
.V 08/15/84 17:41:36
.\" @[$]quot.M	1.12 $D - Zilog Inc.
.ad
.fi
.SH NAME
quot \- summarize filesystem ownership
.SH SYNOPSIS
.B quot
.I [ \fB-cfn\fI ] filesystems\fR
.SH DESCRIPTION
.B Quot
prints the number of blocks in the named
.I filesystems
currently owned by each user.
The 
.I filesystems
may be specified either by device name
or by mounted directory name.
If no 
.I filesystems
are named, no default name is assumed.
.SH OPTIONS
.TP
.B \-n
To produce a list of all files and their owners,
use the pipeline:
.br
.sp
.B ncheck
\fIfilesystem | \fBsort +0n | quot \-n \fIfilesystem\fR
.br
.sp
Note that the \fB\-n\fR option is meaningless outside this pipeline. 
.TP
.B \-c
Print three columns giving file size in blocks, number of
files of that size, and cumulative total of blocks
in that size or smaller file.
.TP
.B \-f
Print count of number of files as well as space owned by each user.
.SH FILES
/etc/passwd      to access user names
.SH SEE ALSO
ls(1),
du(1).
.SH LIMITATIONS
Holes in files are counted as if they actually occupied space.
.sp
.B Quot
will ignore any uid greater than 1000.
