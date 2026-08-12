.po 1i
.TH MVDIR M Bell
.V 08/15/84 17:41:25
.\" @[$]mvdir.M	1.3	08/15/84 17:41:25 - Zilog Inc.
.ad
.fi
.SH NAME
mvdir \- move a directory
.SH SYNOPSIS
.B mvdir
.I "dirname  name"
.SH DESCRIPTION
.B Mvdir
renames directories within a file system.
.I Dirname
must be a directory;
.I name
must not exist.
Neither name can be a sub-set of the other
.RB ( /x/y
cannot be moved to
.BR /x/y/z ,
nor vice versa).
.PP
Only the super-user can use
.BR mvdir .
.SH FILES
/etc/mvdir	the program
.SH SEE ALSO
mkdir(1).
.SH LIMITATIONS
Directories cannot be moved across filesystems
