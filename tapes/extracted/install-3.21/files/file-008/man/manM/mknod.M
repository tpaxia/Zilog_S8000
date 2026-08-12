.po 1i
.TH MKNOD M Bell
.V 08/15/84 17:41:14
.\" @[$]mknod.M	1.10 $D - Zilog Inc.
.ad
.fi
.SH NAME
mknod \- build special file
.SH SYNOPSIS
.B mknod
.I name
[
.B c
] [
.B b
]
.I major minor
.br
.B mknod
.I name
.B p
.SH DESCRIPTION
.B Mknod
makes a directory entry and corresponding inode
for a special file.
.PP
.B Mknod
can also create fifo's (a.k.a named pipes)
(second case in
.B SYNOPSIS
above).
This use of
.B mknod
can be by any user.
The first case can be used only by members of the 'system' group.
It is used to create special device files.
.PP
The first argument is the
.I name
of the entry.
In the first case, the second is
.B b
if the special file is block-type (disks, tape) or
.B c
if it is character-type (other devices).
The last two arguments are
numbers specifying the
.I major
device type
and the
.I minor
device (e.g. unit, drive, or line number),
which may be either decimal or octal.
Major and minor device numbers with a leading 0
means they are octal.
.PP
The assignment of major device numbers depends on
the position of the driver in dispatch tables in the kernel.
The major device numbers for current drivers is as follows:
.nf
.sp
Device              Character Dev.        Block Dev. 
                     Major Number        Major Number

ZD                       32                    0
CT                        1                    1
SMD                       2                    8
MT                        3                    9
MD                        4                    10
ERR                       5                    --
MEM                       6                    --
TTY                       7                    --
SIO                       8                    --
LP                        9, 10                --
PTC                       11                   --
PTS                       12                   --
UP                        13                   --
UU                        14                   --
UD                        15                   --
U1  (user defined dev)    16                   2
U2  (user defined dev)    17                   3
U3  (user defined dev)    18                   4
.bp
Device              Character Dev.        Block Dev. 
                     Major Number        Major Number
.sp
U4  (user defined dev)    19                   5
U5  (user defined dev)    20                   6
U6  (user defined dev)    21                   7
.fi
.PP
The minor device number is device dependent.
For disks, the minor device number is the number of the filesystem.
The first digit (decimal) corresponds to the drive number and
the second digit (decimal) is the order of the filesystem on the disk.
For ttys, the minor device number is the number of the port.
For other devices the numbers represent options passed to 
the drivers (eg. no-rewind for tapes).
.SH FILES
/etc/mknod	the program
.SH SEE ALSO
mknod(1),
mknod(2).
