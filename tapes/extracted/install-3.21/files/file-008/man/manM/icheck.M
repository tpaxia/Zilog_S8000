.po 1i
.TH ICHECK M Bell
.V 08/15/84 17:40:21
.\" @[$]icheck.M	1.4	08/15/84 17:40:21 - Zilog Inc.
.ad
.fi
.SH NAME
icheck \- file system storage consistency check
.SH SYNOPSIS
.B icheck
[
.B \-s
]  [
.B \-b
.I numbers ] filesystem
.SH DESCRIPTION
.B Icheck
examines a file system, builds a bit map of used blocks,
and compares this bit map against
the free list maintained on the file system.
The normal output of
.B icheck
includes a report of
.IP ""
The total number of files and the numbers of
regular, directory, block special and character special files.
.IP ""
The total number of blocks in use and the numbers of 
single-, double-, and triple-indirect blocks and directory blocks.
.IP ""
The number of free blocks.
.IP ""
The number of blocks missing; i.e. not in any file
nor in the free list.
.PP
The
.B \-s
option causes
.B icheck
to ignore the actual free list and reconstruct a new one
by rewriting the super-block of the file system.
The file system should be dismounted while this is done;
if this is not possible (for example if the root file
system has to be salvaged) care should be taken that the system
is quiescent and that it is rebooted immediately afterwards so
that the old, bad in-core copy of the super-block will not
continue to be used.
Notice also that the words in the super-block which indicate
the size of the free list and of the i-list are believed.
If the super-block has been curdled
these words will have to be patched.
The
.B \-s
option causes the normal output reports to be suppressed.
.PP
Following the
.B \-b
option is a list of block numbers;
whenever any of the named blocks turns up in a file,
a diagnostic is produced.
.PP
.B Icheck
is faster if the raw version of the special file is used,
since it reads the i-list many blocks at a time.
.SH FILES
/etc/icheck	the program
.sp
Default file systems vary with installation.
.SH SEE ALSO
filsys(5),
clri(M),
dcheck(M),
ncheck(M).
.SH DIAGNOSTICS
For duplicate blocks and bad blocks (which lie outside the file system)
.B icheck
announces the difficulty, the i-number, and the kind of block involved.
If a read error is encountered,
the block number of the bad block is printed and
.B icheck
considers it to contain 0.
.PP
\&`Bad freeblock' means that
a block number outside the available space was encountered
in the free list.
.PP
\&`\fIn\fR dups in free'
means that
.I n 
blocks were found in the free list which duplicate blocks either
in some file or in the earlier part of the free list.
.SH LIMITATIONS
Since
.B icheck
is inherently two-pass in nature, extraneous diagnostics
may be produced if applied to active file systems.
.sp
It believes even preposterous super-blocks and
consequently can get core images.
