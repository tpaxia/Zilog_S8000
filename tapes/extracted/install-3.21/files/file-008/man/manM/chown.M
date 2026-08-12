.po 1i
.TH CHOWN M Bell
.V 08/15/84 17:39:01
.\"@[$]chown.M	1.3	08/15/84 17:39:01 - Zilog Inc.
.ad
.fi
.SH NAME
chown, chgrp \- change owner or group
.SH SYNOPSIS
.B chown
.I owner file 
.PP
.B chgrp
.I group file
.SH DESCRIPTION
.B Chown
changes the owner of the
.I files
to
.IR owner .
The owner may be either a decimal UID or
a login name found in the password file.
.PP
.B Chgrp
changes the group-ID of the
.I files
to
.IR group .
The group may be either a decimal GID or
a group name found in the group-ID file.
.SH FILES
/etc/passwd	user names and user ID numbers
.br
/etc/group	group names and ID numbers
.br
/etc/chown	the program
.br
/etc/chgrp	the program
.SH SEE ALSO
chown(2),
passwd(5),
group(5),
chmog(M).
