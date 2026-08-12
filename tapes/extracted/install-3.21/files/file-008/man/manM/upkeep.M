.po 1i
.TH UPKEEP M Bell
.V 08/15/84 17:42:42
.\" @[$]upkeep.M	1.4	08/15/84 17:42:42 - Zilog Inc.
.ad
.fi
.SH NAME
upkeep \- directory maintenance
.SH SYNOPSIS
.B upkeep [
.B -mdfsli
] [
.I directory ]
.SH DESCRIPTION
.B upkeep
maintains a .contents file and its corresponding directory.
The .contents file is used as a master file.
It contains information on what files (and their corresponding
mode, user ID, group ID) should be in the directory.
The flags have the following meanings:
.sp 1
.TP
.BR -i
Initialize the .contents file with current specified directory.
.sp 1
.TP
.BR -l
List .contents file
.sp 1
.TP
.BR -d
Report the difference between .contents file and its corresponding
directory.
.sp 1
.TP
.BR -f
Fast update of directory, change the directory to match .contents
file, produces a change report.
.sp 1
.TP
.BR -s
Slow update, same action as fast update, except before each change
action, a confirmation request will be display on the terminal and
user can confirm or deny action interactively.
.sp 1
.TP
.BR -m
Modification of .contents file and directory.
In this mode upkeep accepts the user specified file name and
performs one of the following requested actions:
.sp 1
.RS +4
.TP
.BR add
- add file to .contents file.
File must be in the directory before this operation can be performed.
.sp 1
.TP
.BR delete
- delete file from .contents and directory.
.sp 1
.TP
.BR change
- change mode, uid and/or gid of file in .contents to be
same as in directory.
.s1
.TP
.BR correct
- correct the mode, uid and/or gid of file in directory
to be same as in .contents.
.sp 1
.RE
A ctl-D answer to an interactive prompt terminates the program. Only
owner or super user can make .contents/directory changes.
.SH FILES
\&.contents
.br
\&/tmp/upk.aXXXXX
