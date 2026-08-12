.po 1i
.TH FSDB M
.V 08/15/84 17:40:08
.\" @[$]fsdb.M	1.2 08/15/84 17:40:08 - Zilog Inc.
.ad
.fi
.SH NAME
fsdb \- file system debugger
.SH SYNOPSIS
.B /etc/fsdb
.I special-file
.RB [ " \- " ]
.SH DESCRIPTION
.B Fsdb\^
patches 
a damaged file system
following a crash.
It has conversions
to translate block and i-numbers
into their corresponding disk addresses; 
it has mnemonic offsets
to access different parts
of an i-node.
The task 
of correcting control block entries
or descending the file system tree is greatly simplified.
.PP
.B Fsdb\^
contains several error-checking routines
to verify i-node and block addresses.
As the basis for these checks, 
.B fsdb\^
reads the i-size and f-size entries
from the superblock of the file system. 
If necessary, the checks can be disabled 
by invoking 
.B fsdb\^
with the optional
.B \-
argument
or by using the 
\f3O\fP
symbol.
\c
.PP
.B Fsdb\^
accepts numbers in octal (a leading 0 designates) and decimal;
decimal is the default.
During any assignment operation,
numbers are checked 
for truncation 
due to a size mismatch
between source and destination.
.PP
Because
.B fsdb\^
reads a block at a time, 
it works with raw as well as block
I/O. 
To reduce the number of system calls to read,
a buffer management routine 
retains commonly used
blocks of data. 
All assignment operations result
in an immediate write-through
of the corresponding block.
.PP
The symbols recognized by
.B fsdb\^
are:
.RS
.TP 13
.B #
absolute address
.br
.ns
.TP 13
.B i
convert from i-number to i-node address
.br
.ns
.TP 13
.B b
convert to block address
.br
.ns
.TP 13
.B d 
directory slot offset
.br
.ns
.TP 13
.BR + , \-
address arithmetic
.br
.ns
.TP 13
.B q
quit
.br
.ns
.TP 13
.BR > , <
save, restore an address
.br
.ns
.TP 13
.B =
numerical assignment
.br
.ns
.TP 13
.B =+
incremental assignment
.br
.ns
.TP 13
.B =\-
decremental assignment
.br
.ns
.TP 13
.B ="
character string assignment
.br
.ns
.TP 13
.B O
error checking flip-flop
.br
.ns
.TP 13
.B p
general print facilities
.br
.ns
.TP 13
.B f
file print facility
.br
.ns
.TP 13
.B B
byte mode
.br
.ns
.TP 13
.B W
word mode
.br
.ns
.TP 13
.B D
double word mode
.br
.ns
.TP 13
.B !
escape to shell
.RE
.PP
The print facilities generate formatted output
in various styles.
The current address is normalized 
to an appropriate boundary before printing begins.
The address advances with the printing; 
the last address is the address of the last item printed.
The output can be terminated at any time
by typing the delete character.
If a number follows the \f3p\fP symbol,
that many entries are printed.
Since logically sequential blocks are generally not physically
sequential, 
a check is made to detect block-boundary overflows.
If a count of zero is used, all entries to the end of the
current block are printed.
The print options are:
.RS
.TP 13
.B i
print as i-nodes
.br
.ns
.TP 13
.B d
print as directories
.br
.ns
.TP 13
.B o
print as octal words
.br
.ns
.TP 13
.B e
print as decimal words
.br
.ns
.TP 13
.B c
print as characters
.br
.ns
.TP 13
.B b
print as octal bytes
.RE
.PP
The
\f3f\fP
symbol is  used
to print data blocks
associated with the current i-node.
If followed by a number,
that block of the file is printed.
Blocks are numbered from zero.
The desired print option letter 
follows the block number,
if present,
or the 
\f3f\fP
symbol.
This print facility works
for small as well as large files.
It checks for special devices;
it checks that
the block pointers
used to find the data
are not zero.
.PP
Dots, tabs and spaces may be used
as function delimiters but are not necessary.
A line containing only a new-line character 
will increment the current address
by the size of the data type last printed.
That is,
the address is set to the next byte,
word, double word, directory entry or i-node,
allowing the user
to step through a region of a file system.
Information is printed
in a format appropriate to the data type.
Bytes, words and double words
are displayed with the octal address
followed by the value in octal and decimal.
A \f3.B\fP or \f3.D\fP
is appended to the address
for byte and double word values, respectively.
Directories are printed as a
directory slot offset
followed by the decimal
i-number and the character representation
of the entry name.
I-nodes are printed
with labeled fields
describing each element.
.PP
The following mnemonics
are used for i-node examination
and refer to the current working i-node:
.RS
.TP 13
.B md
mode
.br
.ns
.TP 13
.B ln
link count
.br
.ns
.TP 13
.B uid
user
.SM ID
number
.br
.ns
.TP 13
.B gid
group
.SM ID
number
.br
.ns
.TP 13
.B sz
file size
.br
.ns
.TP 13
.B a#
data block numbers (0 \-\| 12)
.br
.ns
.TP 13
.B at
access time
.br
.ns
.TP 13
.B mt
modification time
.br
.ns
.TP 13
.B maj
major device number
.br
.ns
.TP 13
.B min
minor device number
.RE
.SH EXAMPLES
.TP 16
386i
prints i-number 386 in an i-node format.
This becomes the current working i-node.
.TP 16
ln=4
changes the link count for the 
working i-node to 4.
.TP 16
ln=+1
increments the link count by 1.
.TP 16
fc
prints, in \s-1ASCII\s0,
block zero of the file associated
with the working i-node.
.TP 16
2i.fd
prints the first 32 directory
entries for the root i-node of this file system.
.TP 16
d5i.fc
changes the current i-node to that
associated with the 5th directory entry
(numbered from zero)
found from the above command.
The first 512 bytes of the file
are printed in \s-1ASCII\s0.
.TP 16
1b.p0o
prints the superblock of this file system
in octal.
.TP 16
2i.a0b.d7=3
changes the i-number for the 
seventh directory slot in the root directory to 3.
This example also shows how several 
operations can be combined in one command line.
.ne 3
.TP 16
d7.nm="name"
changes the name field
in the directory slot to the given string.
If the first character is alphabetic, 
quotes are optional
with \f3nm\fP. 
.sp
.SH SEE ALSO
fsck(M), dir(5), filesys(5).
