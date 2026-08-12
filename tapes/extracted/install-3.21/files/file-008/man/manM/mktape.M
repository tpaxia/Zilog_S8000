.po 1i
.TH MKTAPE M Zilog
.V 08/15/84 17:41:17
.\" @[$]mktape.M	1.4	08/15/84 17:41:17 - Zilog Inc.
.ad
.fi
.SH NAME
mktape \- make special files for cartridge tape devices
.SH SYNOPSIS
.B mktape
[
.B 0
] [
.B 1
] [
.B 2
] [
.B 3
] 
.SH DESCRIPTION
.B Mktape
makes appropriate special files in 
.I /dev
for the various
kinds of tape access associated with a particular unit.  
It can be used to simplify the task of creating all the tape
special files since a total of 20 are required per tape unit.
For example the command:
.sp
.RS
\fBmktape 1\fR
.RE
.sp
would make the following special files:
.sp
.nf
.na
  \- non-raw 
  /dev/ct1 /dev/ct1a /dev/ct1b /dev/ct1c /dev/ct1d
.sp
  \- raw 
  /dev/rct1 /dev/rct1a /dev/rct1b /dev/rct1c /dev/rct1d
.sp
  \- no rewind
  /dev/nct1 /dev/nct1a /dev/nct1b /dev/nct1c /dev/nct1d
.sp
  \- no rewind raw
  /dev/nrct1 /dev/nrct1a /dev/nrct1b /dev/nrct1c /dev/nrct1d
.ad
.fi
.SH FILES
/etc/mktape	the program
.SH SEE ALSO
mknod(M).
