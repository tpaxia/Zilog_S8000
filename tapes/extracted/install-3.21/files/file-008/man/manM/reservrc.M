.po 1i
.TH RESERVRC M Zilog
.V 08/15/84 17:41:43
.\" @[$]reservrc.M	1.8 08/15/84 17:41:43 - Zilog Inc.
.ad
.fi
.SH NAME
reservrc, taperrc \- reserv install and remove utility
.SH SYNOPSIS
\fBreservrc\fR [\fB\-i\fR][\fB\-r\fR]
.SH DESCRIPTION
.B Reservrc
installs or removes the 
.BR reserv (1)
utility for the system.
.PP
.B Reserv
runs under the ZEUS operating system as a utility.
The actions of
.B reserv
depend on what keys the user entered on the
command line.
There is no other user interaction after the program has been invoked.
.B Reserv
lets the user know what has happened both by messages sent to
stdout and by values left in the 'status' shell variable.
.PP
The primary function of 
.B reserv
is to reserve the tape drive for a user.
With programs such as 
.BR tar (1)
or
.BR dump (M),
the device must first be opened to use a tape.
There are 20 virtual tape devices for a given drive.
For example, 
.B tar
could open /dev/nrct0
(no rewind, raw, cartridge tape #0)
or /dev/ct0a
(cooked cartridge tape #0, track a).
.PP
Before 
.B tar
can open any of these,
.B reserv
must be run to reserve drive #0.  
.PP
The unreserved state of the device is permissions set to 000
and owner set to 'bin' for each virtual device.
This prohibits anyone from opening the device.
.B Reserv
reserves the device by changing (for all virtual devices)
permissions to 0600 and owner to the person running 
.B reserv
at the time.
This allows only the owner to open the device.
A
.BR fork (2)
is performed, the parent is killed and the child
continues to execute.
It is the child who does all of the queueing and abandoning.
Thus for every person on the queue and the person who has
possession of the tape drive, there is a process running.
.PP
.B Taperrc 
is a link to 
.BR reservrc .
.SH KEYS
.TP 8
.B \-i
Installs reserv into the system.
The line "/etc/reservrc -i" should be added to the /etc/rc_csh script.
.TP  8
.B \-r
Removes 
.B reserv
from the system.
The line "/etc/reservrc -i" should be removed from  the /etc/rc_csh
script.
All tape drives must be free before this is executed.
.SH FILES
/etc/reservrc
.sp
/etc/rc_csh
.sp
/usr/spool/reserv/*
.SH SEE ALSO
rc(M),
reserv(1).
