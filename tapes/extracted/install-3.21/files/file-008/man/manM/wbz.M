.po 1i
.TH WBZ M Zilog
.V 08/15/84 17:42:56 
.\" @[$]wbz.M	1.2 08/15/84 17:42:56 - Zilog Inc.
.ad
.fi
.SH NAME
wbz  \-  configure block 0 of a system drive
.SH SYNOPSIS
.B wbz 
.SH DESCRIPTION
.B Wbz 
is an interactive utility which allows the user to write ZEUS
kernel configuration information to logical block 0 of any disk
drive on the system.
.PP
If block 0 of the default boot drive is to be rewritten,
.B wbz
prompts for information concerning the location, size and type
of root, swap and secondary boot filesystems along with the
layout of the virtual disks.
If the drive to be configured is not the
default boot device then 
.B wbz
prompts for the virtual disk layout of the drive.
This utility is identical to the 'stand-alone' 
.B wbz
described in the ZEUS Administrator Manual.
.PP
Only the super-user can use \fBwbz\fR.
.SH FILES
/etc/wbz 
.SH SEE ALSO
System 8000 ZEUS Administrator Manual
