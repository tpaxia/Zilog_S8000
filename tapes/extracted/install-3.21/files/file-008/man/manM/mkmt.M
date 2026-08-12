.po 1i
.TH MKMT M Zilog
.V 08/15/84 17:41:11
.\" @[$]mkmt.M	1.7	08/15/84 17:41:11 - Zilog Inc.
.ad
.fi
.SH NAME
mkmt \- make special files for magnetic tape devices
.SH SYNOPSIS
.B mkmt
[
.B mt0
] [
.B mt1
] [
.B mt2
] [
.B mt3
] 
.SH DESCRIPTION
.B Mkmt
makes appropriate special files in 
.I /dev
for the varieties
of tape access associated with a particular 
nine track magnetic tape unit.  
It simplifies the task of creating the tape
special files.
For example,
.B mkmt mt0
makes the following special files:
.sp
.nf
    /dev/mt0 /dev/rmt0 /dev/nmt0 /dev/fmt0 /dev/smt0
.br
    /dev/frmt0 /dev/nrmt0 /dev/srmt0 /dev/fnmt0 /dev/snmt0
.br
    /dev/fsmt0 /dev/fnrmt0 /dev/snrmt0 /dev/fsrmt0 /dev/fsnmt0
.br
    /dev/fsnrmt0
.fi
.SH FILES
/etc/mkmt	the program
.SH SEE ALSO
mknod(M),
mt(4).
