.po 1i
.TH CHROOT M Bell
.V 08/15/84 17:39:02
.\" @[$]chroot.M	1.4	08/15/84 17:39:02 - Zilog Inc.
.ad
.fi
.SH NAME
chroot \- change root directory for a command
.SH SYNOPSIS
.B chroot
.I newroot
.I command
.SH DESCRIPTION
The
.I command
is executed relative to the new root.
The meaning of any initial slashes (\fB/\fR)
in path names is changed for 
.I command 
and any of its children to
.IR newroot .
The initial working directory is 
.I newroot\fR.
The new root path name is always relative to the current root:
even if a 
.B chroot
is currently in effect, the 
.I newroot
argument is relative to the current root of the running process.
.PP
This command is restricted to the super-user.
.SH EXAMPLES
The command syntax:
.PP
.RS
\fBchroot \fInewroot command > newfile\fR
.RE
.PP
creates the file
.I newfile
relative to the original root, not the new one.
.SH FILES
/etc/chroot	the program
.SH SEE ALSO
chdir(2).
.SH LIMITATIONS
Exercise extreme caution when referencing special files in
the new root file system.
