.po 1i
.TH RESTOR M Bell
.V 08/15/84 17:41:49
.\" @[$]restor.M	1.22 $D - Zilog Inc.
.ad
.fi
.SH NAME
restor \- incremental filesystem restore
.SH SYNOPSIS
.B restor
.I " key [ argument ... ] "
.SH DESCRIPTION
.B Restor
is used to read cartridge and magnetic tapes dumped with the
.BR dump (M)
command.
The default source device is /dev/dumpdev.
If /dev/dumpdev
does not exist, then /dev/rct0 is used.
The
.I key
specifies what is to be done.
.SH KEYS
.I Key
is one of the characters
.B rtxl
optionally combined with \fBf\fR, \fBw\fR, \fBd\fR
and
.BR v.
.PP
.TP
.B  f
Use the first
.I argument
as the name of the tape instead of /dev/rct0.
.TP
.B  r
The tape is read and loaded into the filesystem specified in
.I argument.
This should not be done lightly (see below).
.TP
.B  x
Each file on the tape named by an 
.I argument
is extracted.
The file name has all 'mount' prefixes removed;
for example, /usr/bin/lpr is named /bin/lpr
on the tape.
The file extracted is placed in a file  with the same name.
All necessary directories are automatically created with
reference to the present working directory.
In order to keep the amount of tape read to a minimum,
the following procedure is recommended:
.sp
Mount volume 1 of the set of dump tapes.
.sp
Type the
.B restor
command.
.sp
.B Restor
will announce whether or not it found the files,
and rewind the tape.
.sp
It then prompts you to "mount desired volume that contains
file of the last volume if you aren't sure".
It then asks for the volume number that you just mounted.
Type the number of the volume you choose.
On a multi-volume dump, the recommended procedure is to mount
the last through the first volume in that order.
.B Restor
checks to see if any of the files requested are on the mounted
tape (or a later tape, thus the reverse order) and doesn't
read through the tape if none of the files are on it.
If you are working with a single volume dump or the number of files
being restored is large, respond to the query with '1' and
.B restor
will read the tapes in sequential order.
.sp
If you have a hierarchy to restore you can use the \fB-l\fR option
to produce the list of names and a tape.
.TP
.B w
Causes 
.B restor
to prompt the user with the filename to be restored immediately 
before it is extracted.
It waits for a confirmation.
If a word beginning with 'y' is given, the file is extracted into
the original filename; if a word beginning with 'y' followed by
another word, this second word is taken as the filename to which
the file will be extracted.
Any other response is taken as negative, that file
won't be extracted.
.TP
.B t
Print the filesystem name, user comments made at dump time,
the date the tape was written and the date the filesystem
was dumped from.
.TP
.B l
Does everything the \fB-t\fR option does plus lists the names
of the files that are on the dump.
.TP
.B v
Only meaningful when used with the \fB-l\fR option.
This gives a verbose listing of the filenames including the
owner group, permissions, and date of last modification.
.TP
.B d
Take the next argument as the position (starting with 1) of the
file on the tape with respect to the current position of the tape.
This enables the user to
.B restor
from a dump even though it isn't
the first file on the tape.
For example the command 
.B restor -dx 3 \fBfilename\fR will
cause \fBrestor\fR to space to the third file on the tape (assuming
the tape was rewound prior to the command) to do the extracting.
.PP
The
.B r
option should only be used to restore a complete dump tape onto a
clear filesystem or to restore an incremental dump tape onto this.
Thus:
.PP
	\fB/etc/mkfs /dev/rzd0 12000 12 96
.br
	restor r /dev/rzd0\fR
.PP
is a typical sequence to restore a complete dump.
Another
.B restor
can be done to get an incremental dump in on top of this.
.PP
A
.B dump
followed by a
.B mkfs
and a
.B restor
is used to change the size of a filesystem.
.SH FILES
/tmp/rst*
.sp
/etc/restor	the program
.SH SEE ALSO
dump(M),
mkfs(M).
.SH WARNINGS
If two files being extracted are links to each other,
only the first file encountered will be extracted.  A message will be returned
informing the user that the second file is a link to the first. 
If he wishes to retain the link, he will have to re-establish the link
after restoration.
.SH DIAGNOSTICS
There are various diagnostics involved with reading the tape
and writing the disk.
There are also diagnostics if the i-list or the free list
of the filesystem is not large enough to hold the dump.
.SH LIMITATIONS
There is redundant information on the tape
that could be used in case of tape reading problems.
Unfortunately,
.B restor
doesn't use it.
