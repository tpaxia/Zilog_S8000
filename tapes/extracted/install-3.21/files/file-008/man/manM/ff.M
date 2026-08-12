.po 1i
.TH FF M Bell
.V 08/15/84 17:39:58
.\" @[$]ff.M	1.2 08/15/84 17:39:58 - Zilog Inc.
.ad
.fi
.SH NAME
f\&f \- list filenames and statistics for a filesystem
.SH SYNOPSIS
.B /etc/f\&f
[\fIoptions\fR] \fIspecial\fR
.SH DESCRIPTION
.B Ff\^
reads the i-list and directories of the 
.I special\^ 
file, assuming it to be a filesystem,
saving i-node data for files which match the selection criteria.
Output consists of the pathname for each saved inode, plus 
any other file information requested
using the print \fIoptions\fP below.
Output fields are positional.
The output is produced in inode order; fields are separated by tabs.
The default line produced by
.B f\&f
is:
.PP
.RS
\fIpathname \|i-number\fR
.RE
.PP
With all \fIoptions\fP enabled, output
fields would be:
.PP
.RS
\fIpathname \|i-number \|size \|uid\fR
.RE
.PP
The argument
.I n
in the \fIoption\fP descriptions that follow is used 
as a decimal integer (optionally signed), where
.BI + n\^
means more than
.IR n ,
.BI \- n\^
means less than
.IR n ,
and 
.I n\^
means exactly
.IR n \.
A day is defined as a 24 hour period.
.SH OPTIONS
.TP 10
.B \-I
Do not print the inode number after each pathname.
.TP
.B \-l
Generate a supplementary list of all pathnames for files with multiple
links.
.TP
\fB\-p \fIprefix\fR
The specified
.I prefix
will be added to each generated pathname.
The default is
.BR \&. . 
.TP
.B \-s
Print the file size, in bytes, after each pathname.
.TP
.B \-u
Print the owner's login name after each pathname.
.TP
\fB\-a \fIn\fR
Select if the inode has been accessed in
.I n\^
days.
.TP
\fB\-m \fIn\fR
Select if the inode has been modified in
.I n\^
days.
.TP
\fB\-c \fIn\fR
Select if the inode has been created in 
.I n\^
days.
.TP
\fB\-n \fIfile\fR
Select if the inode has been modified more recently than the argument
.IR file .
.bp
.TP
\fB\-i \fIinode-list\fR
Generate names for only those inodes specified in
.IR "inode-list" .
.SH EXAMPLES
To generate a list of the names of all files on a specified filesystem:
.PP
.RS
\fBf\&f \|\-I \|/dev/root\fR
.RE
.PP
To produce an index of files and i-numbers which are on a
filesystem and have been modified in the last 24 hours:
.PP
.RS
\fBf\&f \|\-m \|\-1 \|/dev/usr \|> \|/log/incbackup/usr/tuesday\fR
.RE
.PP
To obtain the pathnames for inodes 451 and 76 on 
a specified filesystem:
.RS
.PP
.B f\&f \|\-i \|451,76 \|/dev/md7
.RE
.SH "SEE ALSO"
find(1), frec(M), ncheck(M).
.SH LIMITATIONS
Only a single pathname out of all possible ones is generated for an
inode with multiple links, unless the
.B \-l
option is specified.
When
.B \-l
is specified, no selection criteria apply to the names generated.
All possible names for every linked file on the filesystem will be included
in the output.
.P
On very large filesystems, memory may run out before
.B f\&f
does.
