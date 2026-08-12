.po 1i
.TH CHMOG M Zilog
.V 08/15/84 17:38:59
.\"@[$]chmog.M	1.4	08/15/84 17:38:59 - Zilog Inc.
.ad
.fi
.SH NAME
chmog, chog \- change mode, owner and group of a file
.SH SYNOPSIS
.B chmog
.I octal-mode user group file
.sp
.B chog
.I user group file
.SH DESCRIPTION
.B Chmog
will change the mode, owner and group of the listed
files to 
.I octal-mode, 
.I user,
and 
.I group
respectively.
.B Chog
will change the owner and group of the listed files.
The 
.I user
and 
.I group
may be specified by either the user id,
group id or the user name or group name.
.SH FILES
/etc/passwd
.br
/etc/group
.br
/etc/chmog
.br
/etc/chog
.SH SEE ALSO
chmod(1),
chmod(2),
chgrp(1),
chown(M).
