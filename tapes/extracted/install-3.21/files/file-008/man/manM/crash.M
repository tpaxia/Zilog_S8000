.po 1i
.TH CRASH M Bell
.V 08/15/84 17:39:05 
.\" @[$]crash.M	1.3 08/15/84 17:39:05 - Zilog Inc
.ad
.fi
.SH NAME
crash \- examine system images
.SH SYNOPSIS
.B /etc/crash
[ \fIsystem ] [ namelist\fR ]
.SH DESCRIPTION
.B Crash\^
is an interactive utility for examining
an operating system core image.
It has facilities for interpreting
and formating the various control structures
in the system and certain miscellaneous
functions that are useful when perusing a dump.
.PP
The arguments to
.B crash\^
are the file name where the system image
can be found and
a namelist file to be used
for symbol values.
The default values are /dev/kmem
and /zeus.
The default current process is the swapper, process 0.
Hence,
.B crash\^
with no arguments can be used to examine
an active system.
If a system image file is given,
it is assumed to be a system core dump and
the initial process is set to be that of the
process running at the time
of the crash.
.SH COMMANDS
Input to
.B crash\^
is typically of the form:
.sp
.ti 10
.I command [ options ] [ structures to be printed ]
.sp
When allowed,
options will modify the format of the print out.
If no specific structure elements are specified,
all valid entries will be used.
As an example,
.B proc \- 12 15 3
would print process table slots
12, 15 and 3 in a long format,
while
.B proc
would print the entire process table
in the standard format.
The current repertory consists of:
.TP
\fBu [\fIprocess table entries\fR]
Print the user structure of the processes named.
If none given, print the current process user structure.
.TP
\fBstack [\fIprocess table entries\fR]
Format a hex dump of the kernel stack of the
processes named.  If none given, dump the stack from the
current process user structure.
This can only be done for processes which are not swapped out.
The addresses shown are virtual system data addresses
rather than true physical locations.
.TP
\fBproc\fP [ \fB\-\fP[\fBr\fP] ] [ \fIlist of process table entries\fR ]
Format the process table.
The
.B \-r
option causes only runnable processes to be printed.
The
.B \-
alone generates a longer listing.
.bp
.TP
\fBinode\fP [ \fB\-\fP ] [ \fIlist of inode table entries\fR ]
Format the inode table.
The
.B \-
option will also print
the inode data block addresses.
.TP
\fBfile\fP [ \fIlist of file table entries\fR ]
Format the file table.
.TP
\fBmount\fP [\fI list of mount table entries\fR ]
Format the mount table.
.ne 4
.TP
\fBtext\fP [ \fIlist of text table entries\fR ]
Format the text table.
.TP
\fBtty\fP [ \fB\-\fP ] [ \fIlist of tty entries\fR ]
Print the tty structures.
The
.B \-
option prints the
.B stty
parameters for the given line.
.TP
.B stat
Print certain statistics found in the dump.
These include the
panic string, time of crash, system name,
and the registers saved by the dump mechanism.
.TP
.B var
Print the tunable system parameters.
.TP
\fBbuf\fP [ \fIlist of buffer headers\fR ]
Format the system buffer headers.
.TP
\fBbuffer\fP [ \fIformat\fR ] [ \fIlist of buffers\fR ]
Print the data in a system buffer
according to
.IR format .
Valid formats include
.BR decimal ,
.BR hexadecimal ,
.BR octal ,
.BR character ,
.BR byte ,
.BR hexbyte ,
.BR directory ,
.BR inode ,
and
.BR write .
The last creates a file containing the buffer data.
.TP
.B callout
Print all entries in the callout table.
.TP
\fBmap\fP [ \fIlist of map names\fR ]
Format the named system map structures.
.TP
\fBnm\fP [ \fIlist of symbols\fR ]
Print symbol value and type as found in the
namelist file.
.TP
\fBts\fP [ \fIlist of text addresses\fR ]
Find the closest text symbols to the given addresses.
.TP
\fBds\fP [ \fIlist of data addresses\fR ]
Find the closest data symbols to the given addresses.
.TP
\fBhd\fP [\fI symbol or data address ] [ count ] [ format\fR ]
Dump
.I count\^
data values
starting at the symbol value or address given
according to
.IR format .
Allowable formats
.bp
are
.BR hexadecimal ,
.BR octal ,
.BR decimal ,
.BR character ,
.BR hexbyte ,
or
.BR byte .
.TP
\fBpd\fP [\fI absolute physical data address ] [ count ] [ format\fR ]
Dump
.I count\^
data values
starting at the physical address given
according to
.IR format .
Allowable formats are
.BR hexadecimal ,
.BR octal ,
.BR decimal ,
.BR character ,
.BR hexbyte ,
or
.BR byte .
.TP
.B hbuf
Print the buffer hash lists.
.TP
\fBflock\fI [ list of lock entries\fR ]
Print the file record lock table.
If no lock entries are specified, then all entries with a non-NULL
process pointer are printed.
.TP
.B echo
Print the arguments to echo.  This is useful for annotating
information when output is diverted to a print file.
.TP
.B !
Escape to shell.
.TP
.B q
Exit from
.BR crash .
.TP
.B ?
Print synopsis of commands.
.SH NUMBER BASES
.B Crash\^
expects counts and indices into tables to be entered in decimal and addresses
to be entered in hex, and prints them out so as well.
To help avoid confusion, numbers printed in hex (or octal) are always printed
with left zero fill.
Major device numbers are output in decimal, and minor ones in hex.
The way the
.B hd
command determines whether input is an address or a symbol
is by examining its first character.  If it is not 0-9 the input is taken
as a symbol, thus hex numbers beginning with a-f must be preceeded by a 0.
This does not make them interpreted as octal!
The only octal, aside from that asked for by the user, that is output by 
.B crash\^
is the file mode (for historical reasons).
It is not possible to give octal input to
.B crash.
.SH ALIASES
There are built in aliases for many of the
commands and formats.
In general,
the first letter of a name
is satisfactory, thus,
.B k
is a shorthand notation for
.BR kernel .
Exceptions are
.B x
for
.B text
and
.B e
for
.BR decimal .
.SH FILES
/dev/kmem	default system image file for virtual addresses
/dev/mem	default system image file for physical addresses
.br
/zeus		default namelist file
.br
buf.#		files created containing buffer data
