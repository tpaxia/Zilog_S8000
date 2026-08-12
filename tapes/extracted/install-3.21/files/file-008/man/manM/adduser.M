.po 1i
.TH ADDUSER M Zilog
.V 08/15/84 17:38:50
.\"@[$]adduser.M	1.5	08/15/84 17:38:50 - Zilog Inc.
.ad
.fi
.SH NAME
adduser \- add a new user to the system
.SH SYNOPSIS
.B adduser
.SH DESCRIPTION
This shell procedure aids the system administrator in adding a user to
the system.  It updates 
.I /etc/passwd 
and 
.I /etc/group
and creates various directories and files for the new user.
.B Adduser
is interactive and prompts for all needed information.
The new user is assigned a uid that is 
the least used uid 
already in 
.I /etc/passwd.
.PP
.B Adduser
prompts for the new user's name, home directory name,
group at login,
and other group names the user is also belong to.
The home directory name must be the full, explicit pathname.
The list of additional groups is used by
.BR newgrp (1).
An example session of
.B adduser
is:
.sp 3
.nf
.na
.in +6
New user's name: doug
Scanning for a uid number.
Home directory: /z/doug
Login shell (/bin/csh is the default): <cr>
Default group at login ('other' is the default): <cr>
.fi
.ad
.sp
Enter groups OTHER THAN the default group that `doug' should
belong to. Enter one group name per line, with a control-d to end.
If the user should belong only to her/his default group, just
type control-d to the question.
Group: END
.nf
.na
.sp
User:            doug
Uid:             76
Gid:             1
Dir:             /z/doug
Login shell:     /bin/csh

Okay to add (yes or no)? yes
doug: Added
New password:
Retype new password:
.in -6
.fi
.ad
.PP
In response to the prompt "Okay to add (yes or no)? ", 
if anything other than
a yes or a y is typed it will be interpreted an a no response.
.SH FILES
/etc/group		group file
.br
/etc/passwd		password file
.br
/usr/spool/mail	directory in which mailbox is created
.SH SEE ALSO
mkdir(1),
passwd(1),
rmuser(M).
.SH DIAGNOSTICS
Invalid inputs are rejected and re-requested.
.SH LIMITATIONS
There is a tiny time window in which two 
simultaneously running copies of
.B adduser
might interact to their mutual harm.
No check is made on the success of 
giving the new user an initial password.
If the password initialization fails, (e.g. the password is not entered
identically in response to the two requests from 
.BR passwd (1) 
for the new password)
the new user is left without a password, a possible security flaw.
.LP
.B Adduser
is a C-shell script and is slow.
