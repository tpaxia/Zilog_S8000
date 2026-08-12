.po 1i
.TH STRPRINT M Zilog
.V 08/15/84 17:42:27
.\" @[$]strprint.M	1.6 08/15/84 17:42:27 - Zilog Inc.
.ad
.fi
.SH NAME
strprint \- software trouble report listing program
.SH SYNOPSIS
\fBstrprint\fR
.SH DESCRIPTION
This shell procedure is used for printing a copy of all software
trouble reports on the line printer.  
Each trouble report is printed on a separate page.
Each installation should periodically send a a copy of the output 
from this program to Zilog.
Also, this listing should be made available to users so that they
become aware of any software trouble reports about the system.
.SH FILES
/usr/strfile
.br
	data base for tracking trouble report progress
.sp
/usr/seqno
.br
	file containing the last used sequence number
.sp
/usr/problems
.br
	directory in which problem reports are kept
.sp
/usr/scrb_date
.br
	File containing date of next review meeting
.SH SEE ALSO
strfile(5),
str(M).
