.po 1i
.TH RMUSER M Zilog
.V 08/15/84 17:42:02
.\"@[$]rmuser.M	1.4	08/15/84 17:42:02 - Zilog Inc.
.ad
.fi
.SH NAME
rmuser \- remove a user from the system
.SH SYNOPSIS
.B rmuser
.I name
.SH DESCRIPTION
This shell procedure aids the system administrator in removing a user to
the system.  It handles the updating of 
.I /etc/passwd 
and 
.I /etc/group
and produces a list of all the files in the 
system owned by the departing
user for screening and eventual disposition.
Only the user's mailbox file is deleted, all other files are untouched.
The procedure is interactive and prompts for all needed information.
.SH FILES
/etc/group
	group file,
.I name
is removed from all groups
.sp
/etc/passwd
	password file,
.IR name 's
password is changed
.sp
.RI files. name
	file containing list of all files owned by name
/etc/rmuser
	the program
.SH SEE ALSO
passwd(1).
.SH DIAGNOSTICS
If
.I name
is not found in 
.I/etc/passwd,
the procedure exits with a complaint.
.SH LIMITATIONS
If the departing user has access to other user's passwords (e.g. bin,
root) these should be changed also.
.sp
Files owned by
.I name
in unmounted file systems are not included in
.RI files .name
for obvious reasons.
.sp
No check is made on the success of changing the user's password.
