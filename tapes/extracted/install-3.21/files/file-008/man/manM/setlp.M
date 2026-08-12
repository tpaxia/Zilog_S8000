.po 1i
.TH SETLP M Zilog
.V 08/15/84 17:42:13
.\" @[$]setlp.M	1.7 08/15/84 17:42:13 - Zilog Inc.
.ad
.fi
.SH NAME
setlp \- set line printer parameters
.SH SYNOPSIS
.B setlp
[
.B -lwsd
]
.SH DESCRIPTION
.B Setlp
displays and changes the line printer parameters:  number of columns,
lines per page, and indent (number of blanks before first column).
If no options are given,
.B setlp
displays the current parameter settings.
.LP
These are the options.
.TP 
.B \-l \fInumber\fR
The number of lines is set to the decimal number given.
.TP 
.B \-w \fInumber\fR
The number of columns is set to the decimal number given.
.br
.TP 
.B \-s \fInumber\fR
The starting column (numbered from 0) is set to the decimal
number given.
.TP 
.B \-d \fIdevname\fR
The device file set or examined is 
.I devname.
If this option is missing, the device file used is
.I /dev/lp.
.SH SEE ALSO
ioctl(2),
stty(1).
