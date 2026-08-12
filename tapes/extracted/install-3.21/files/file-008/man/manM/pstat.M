.po 1i
.TH PSTAT M Zilog
.V 08/15/84 17:41:32
.\" @[$]pstat.M	1.4	08/15/84 17:41:32 - Zilog Inc.
.ad
.fi
.SH NAME
pstat \- print system facts
.SH SYNOPSIS
.B pstat
[
.B \-aixptuf
.I ] [ suboptions ] [ file ]
.SH DESCRIPTION
.B Pstat
interprets the contents of certain system tables.
If
.I file
is given, the tables are sought there, otherwise in
.I /dev/mem
and
.I /dev/kmem.
(System core images not currently supported).
The required namelist is taken from
.I /zeus.
Options are
.TP \w'WCHAN\ 'u
.B \-a
Under
.BR \-p ,
describe all process slots rather than just active ones.
.TP
.B \-i
Print the inode table with the these headings:
.IP LOC
The core location of this table entry.
.PD 0
.IP FLAGS
Miscellaneous state variables encoded thus:
.RS
.IP L
locked
.IP U
update time
.BR (filsys (5))
must be corrected
.IP A
access time must be corrected
.IP M
file system is mounted here
.IP W
wanted by another process (L flag is on)
.IP T
contains a text file
.IP C
changed time must be corrected
.RE
.IP CNT
Number of open file table entries for this inode.
.IP DEV
Major and minor device number of file system in which
this inode resides.
.IP INO
I-number within the device.
.IP MODE
Mode bits, see
.BR chmod (2).
.IP NLK
Number of links to this inode.
.IP UID
User ID of owner.
.IP SIZ/DEV
Number of bytes in an ordinary file, or
major and minor device of special file.
.PD
.TP
.B \-x
Print the text table with these headings:
.IP LOC
The core location of this table entry.
.PD 0
.IP FLAGS
Miscellaneous state variables encoded thus:
.RS
.IP T
.BR ptrace (2)
in effect
.IP W
text not yet written on swap device
.IP L
loading in progress
.IP K
locked
.IP w
wanted (L flag is on)
.RE
.PD
.IP DADDR
Disk address in swap, measured in multiples of 512 bytes.
.IP CADDR
Core address, measured in multiples of 256 bytes.
.IP SIZE
Size of text segment, measured in multiples of 256 bytes.
.IP IPTR
Core location of corresponding inode.
.IP CNT
Number of processes using this text segment.
.IP CCNT
Number of processes in core using this text segment.
.PD
.TP
.B \-p
Print process table for active processes with these headings:
.IP LOC
The core location of this table entry.
.PD 0
.IP S
Run state encoded thus:
.RS
.IP 0
no process
.IP 1
waiting for some event
.IP 3
runnable
.IP 4
being created
.IP 5
being terminated
.IP 6
stopped under trace
.RE
.IP F
Miscellaneous state variables, or-ed together:
.RS
.IP 001
loaded
.IP 002
the scheduler process
.IP 004
locked
.IP 008
swapped out
.IP 010
traced
.IP 020
used in tracing
.IP 040
locked in by
.BR lock (2).
.RE
.IP PR
Scheduling priority, see
.BR nice (2).
.IP SG
Signals received (signals 1-16 coded in bits 0-15),
.IP UID
Real user ID.
.IP TIM
Time resident in seconds; times over 127 coded as 127.
.IP CPU
Weighted integral of CPU time, for scheduler.
.IP NI
Nice level, see
.BR nice (2).
.IP PGRP
Process number of root of process group
(the opener of the controlling terminal).
.IP PID
The process ID number.
.IP PPID
The process ID of parent process.
.IP ADDR
If in core, the physical address of the `u-area' of
the process measured in multiples of 256 bytes.
If swapped out, the position in the swap area
measured in multiples of 512 bytes.
.IP SZE
Size of process image in multiples of 256 bytes.
.IP WCHN
Wait channel number of a waiting process.
.IP LINK
Link pointer in list of runnable processes.
.IP TEXTP
If text is pure, pointer to location of text table entry.
.IP CLKT
Countdown for
.BR alarm (2)
measured in seconds.
.PD
.TP
.B \-t
Print table for terminals (sio ports)
with these headings:
.IP RAW
Number of characters in raw input queue.
.PD 0
.IP CAN
Number of characters in canonicalized input queue.
.IP OUT
Number of characters in output queue.
.IP IMODE
Input mode flags
.IP OMODE
Output mode flags
.IP CMODE
Control mode flags
.IP LDMODE
Line discipline mode flags
.IP IOADDR
IO address.
.IP CTCADDR
CTC address.
.IP DEL
Number of delimiters (newlines) in canonicalized input queue.
.IP COL
Calculated column position of terminal.
.IP STATE
Miscellaneous state variables encoded thus:
.RS
.IP W
waiting for open to complete
.IP O
open
.IP S
has special (output) start routine
.IP C
carrier is on
.IP B
busy doing output
.IP A
process is awaiting output
.IP X
open for exclusive use
.IP H
hangup on close
.RE
.IP PGRP
Process group for which this is controlling terminal.
.PD
.TP
.B \-u
print information about a user process;
the next argument is its address as given by
.BR ps (1).
The process must be in main memory, or the file used can
be a user core image and the address 0.
.TP
.B \-f
Print the open file table with these headings:
.IP LOC
The core location of this table entry.
.PD 0
.IP FLG
Miscellaneous state variables encoded thus:
.RS
.IP R
open for reading
.IP W
open for writing
.IP P
pipe
.RE
.IP CNT
Number of processes that know this open file.
.IP IPTR
The location of the inode table entry for this file.
.IP OFFS
The file offset, see
.BR lseek (2).
.PD
.PP
.SH FILES
.ta \w'/dev/kmem  'u
/zeus	namelist
.br
/dev/mem	default source of user structure
.br
/dev/kmem	default source of kernel data tables
.SH SEE ALSO
ps(1), stat(2), filsys(5)
