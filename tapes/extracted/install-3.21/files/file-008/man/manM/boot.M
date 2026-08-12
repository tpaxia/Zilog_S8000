.po 1i
.TH BOOT M Zilog
.V 08/15/84 17:38:58
.\" @[$]boot.M	1.6	08/15/84 17:38:58 - Zilog Inc.
.ad
.fi
.SH NAME
boot  \- secondary bootstrapper
.SH SYNOPSIS
.B boot
.SH DESCRIPTION
.B Boot
is invoked by the primary bootstrapper.
For the Model 20, the primary bootstrap resides
on block 0 (the boot block) of the disk.
For other models the primary bootstrapper resides in
PROM on the CPU board.
.PP
Its primary function is to load the kernel from disk into
memory during normal bootstrap operations, but it is also
capable of loading and executing a variety of stand-alone
programs from either disk or cartridge tape.
.PP
.B Boot
must reside in the root of the first file system on the disk.
As currently configured, this file system gets mounted on
.I /usr,
so the fully-qualified pathname of the primary bootstrapper
is
.I /usr/boot.
.PP
A new secondary bootstrapper can be made using 
.BR sysgen (M).
.SH FILES
/usr/boot	program
.SH SEE ALSO
init(M).
