.po 1i
.TH SYSGEN M Zilog
.V 08/15/84 17:42:30
.\" @[$]sysgen.M	1.8	08/15/84 17:42:31 - Zilog Inc.
.ad
.fi
.SH NAME
sysgen  \-  generate a ZEUS kernel                 
.SH SYNOPSIS
.B sysgen 
[\fB-f\fR
.I file] [
.B -d
.I {11 11P 21 21P 31 31P}]
.SH DESCRIPTION
.B Sysgen 
is a ZEUS kernel generation utility. 
.B Sysgen
allows a user to interactively modify certain kernel
parameters,
configure up to four disk drives, include user
written device drivers, add line printers and tape drives into the ZEUS
kernel that is generated.
This is a system administrator's function that is outlined in
more detail in the ZEUS Administrator Manual.
The resulting kernel file is named zeus unless the 
.B -f
option is used.
.PP
The
.B -d
option tells
.B sysgen
to use default answers to all the questions
normally asked.  The 
.B -d 11
option is used for the Model 11; the
.B -d 11P
option is for the Model 11 Plus.  The
.B -d 21
option is used for the Model 21; the
.B -d 21P
option is for the Model 21 Plus.  The
.B -d 31
option is used for the Model 31, and the
.B -d 31P
is for the Model 31 Plus.
.SH FILES
/etc/sysgen 
.br
/usr/sys/conf/z.c
.br
/usr/sys/conf/ver.c+
.br
/usr/sys/h/sysparm.h
.SH DIAGNOSTICS  
The user must have write permission in /usr/sys/conf.
.SH SEE ALSO
ZEUS Administrator Manual
