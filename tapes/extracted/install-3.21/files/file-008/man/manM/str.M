.po 1i
.TH STR M Zilog
.V 08/15/84 17:42:24
.\" @[$]str.M	1.6 08/15/84 17:42:25 - Zilog Inc.
.ad
.fi
.SH NAME
str \- software trouble report input program
.SH SYNOPSIS
\fBstr\fR [ \fB-l\fR ]
.SH DESCRIPTION
This program is used for the initial capture of software
trouble reports.
It prompts the user for all needed information.
The user also has the option of entering the editor,
.BR vi (1)
is the default editor.
The user may enter the editor at the beginning of the
.I Problem Description
field  or just before submitting the trouble report.
.PP
Each submitted trouble report is assigned a sequence number, 
and is reflected in a master tracking file.
.SH OPTIONS
.TP
.B \-l
Produce a line printer listing upon completion of the trouble report.
.SH FILES
/usr/lib/problems/strfile 
.br
	Data base for tracking trouble report progress
.sp
/usr/lib/problems/seqno	
.br
	File containing the last used sequence number
.sp
/usr/lib/problems	
.br
	Directory in which problem reports are kept
.sp
/usr/lib/problems/scrb_date	
.br
	File containing date of next review meeting
.SH SEE ALSO
strfile(5),
strprint(M).
