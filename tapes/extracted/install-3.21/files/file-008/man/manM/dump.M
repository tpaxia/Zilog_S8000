.po 1i
.TH DUMP M Bell
.V 08/15/84 17:39:49
.\" @[$]dump.M	1.22 08/15/84 17:39:49 - Zilog Inc.
.ad
.fi
.SH NAME
dump \- incremental filesystem dump
.SH SYNOPSIS
.B dump
\fI[ key [ argument ... ] [ key [ argument ... ] ] ... filesystem ]\fR
.SH DESCRIPTION
.B Dump
copies to cartridge or magnetic tape all files changed after a certain
date in the
.I filesystem.
.PP
The default destination device is /dev/dumpdev.
If /dev/dumpdev does not exist, /dev/rct0
is used for the default.
.PP
Always perform dumps on quiescent filesystems.
Dumping active filesystems may lead to unfortunate results
when restoring with \fBrestor\fR(M).
.PP
When
.B dump
is run in background, or receives input that has been redirected from
a file (instead of the terminal), the tape changing mechanism is turned
off.
In either of these situations, if the dump requires a second tape,
it will abort instead of prompting for a new tape.
.SH KEYS
The
.I key
specifies the date and other options about the dump.
.TP 5
.B  a
If the dump will span more than one tape, then 
.B dump
will abort before any data has been dumped and print a message
to this effect to the standard output device.
.TP 5
.B  b
Allow specification of blocksize to make the tape.
.TP 5
.B  f
Place the dump on the next 
.I argument 
file instead of /dev/dumpdev.
.TP 5
.B  h
The next argument is taken as a user comment and is written
onto the dump-tape header;
394 characters are allowed for this comment.
.TP 5
.B  n
The next argument is taken as the name of the filesystem
being dumped and is written onto the dump-tape header;
30 characters are allocated for this name.
.TP 5
.B s
The next argument is the length of the tape in feet.
The default is 450 feet for cartridge tape and 2400 feet
for mag tape.
.TP 5
.B  u
If the dump completes successfully, write the date of the
beginning of the dump on file /etc/ddate.
This file records a separate date for
each filesystem and each dump level.
.TP 5
.B w
If this key is specified, dump does not wait for the tape to finish
rewinding before exiting. 
.TP 5
.B  0\-9
This number is the 'dump level'.
All files modified since the last date stored in the file
/etc/ddate for the same filesystem at lesser levels
will be dumped.
If no date is determined by the level,
the beginning of time is assumed.
Thus, the option
.B 0
causes the entire filesystem to be dumped.
.PP
.DT
If no arguments are given, the
.I key
is assumed to be
.B 9u
and the filesystem name and comment fields will contain nulls. 
The tape length will default to 450 feet.
.SH EXAMPLES
Start with a full level 0 dump
.PP
	\fBdump 0u \fIfilesystem\fR
.PP
Next, periodic level 9 dumps should be taken on an
exponential progression of tapes.
This is sometimes called Tower of Hanoi:  1 2 1 3 1 2 1 4 ...
tape 1 used every other time,
tape 2 used every fourth,
tape 3 used every eighth, etc.
.PP
	\fBdump 9u \fIfilesystem\fR
.PP
When the level 9 incremental approaches a full tape,
a level 1 dump should be taken.
.PP
	\fBdump 1u \fIfilesystem\fR
.PP
After this, the exponential series should progress as uninterrupted.
These level 9 dumps are based on the level 1 dump which
is based on the level 0 full dump.
This progression of levels of dump can be carried
as far as desired.
.SH FILES
/etc/ddate: record dump dates of filesystem/level
.SH SEE ALSO
restor(M)
.SH LIMITATIONS
Read errors on the filesystem are ignored.
Write errors on the magtape are usually fatal.
When doing a dump of a filesystem, always use the same name for
it.
For example, when
.B dump
reads the /etc/ddate
file to determine the last date a file
system was dumped, it considers /dev/rzd0 and
/dev/zd0 two different filesystems. 
