.po 1i
.TH SETMNT M Bell
.V 08/15/84 17:42:16
.\" @[$]setmnt.M	1.8 08/15/84 17:42:16 - Zilog Inc.
.ad
.fi
.SH NAME
setmnt \- establish mnttab table
.SH SYNOPSIS
.B setmnt
.SH DESCRIPTION
.B Setmnt
creates the
.I /etc/mnttab
table (see
.BR mnttab (5)),
which is needed for both the
.BR mount (M)
and
.BR umount (M)
commands.
.B Setmnt
reads standard input and creates a
.B mnttab
entry for each line.
Input lines have the format:
.PP
.RS
filesys node
.RE
.PP
where
.I filesys
is the name of the file system's
.I special file
(e.g.,
.I /dev/rz??
) and
.I node
is the root name of that file system.
.I Filesys
and
.I node
become the first two strings in the
.BR mnttab (5)
entry.
.SH FILES
/etc/mnttab
.sp
/etc/setmnt	the program
.SH SEE ALSO
mnttab(5).
.SH LIMITATIONS
Do not make
.I filesys
or
.I node
longer than 32 characters.
.br
.B Setmnt
silently enforces an upper limit on the maximum number of
.B mnttab
entries; this limit is based on the system parameter
.B Nmount
in the kernel
