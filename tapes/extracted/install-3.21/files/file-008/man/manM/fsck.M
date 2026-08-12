.po 1i
.TH FSCK M Zilog
.V 08/15/84 17:40:02
.\" @[$]fsck.M	1.7	08/15/84 17:40:02 - Zilog Inc.
.ad
.fi
.SH NAME
fsck \- file system consistency check and interactive repair
.SH SYNOPSIS
.B fsck
.I [[ \fB-fnsSty\fI ] filesystem ]\fR
.SH DESCRIPTION
.B  Fsck
audits and interactively repairs inconsistent conditions
for the named
.IR filesystems.
If a file system is consistent then the number of files, 
number of blocks used, and number of blocks free are reported.
If the file system is inconsistent the operator is prompted 
for concurrence before each correction is attempted.
Most corrections lose data;
all losses are reported.
The default action for each correction is to wait for the
operator to respond `yes' or `no'.
Without write permission 
.B fsck
defaults to
.BR "\-n " action.
.PP
If no filesystems are given to 
.B fsck
then a default list of file systems is read from
the file
.IR /etc/checklist .
.PP
.ne 10
Inconsistencies checked are as follows:
.TP
1.
Blocks claimed by more than one inode or the free list.
.TP
2.
Blocks claimed by an inode or the free list outside the 
range of the file system.
.TP
3.
Incorrect link counts.
.TP
4.
Size checks:
.RS
Incorrect number of blocks in file.
.br
Directory size not a multiple of 16 bytes.
.RE
.TP
5.
Bad inode format.
.TP
6.
Blocks not accounted for anywhere.
.TP
7.
Directory checks:
.RS
Discrepency between number of directory entries and inode link counts
.br
Inode number out of range.
.RE
.TP
8.
Super Block checks:
.RS
More than 65536 inodes.
.br
More blocks for inodes than there are in the file system.
.RE
.TP
9.
Bad free block list format.
.TP
10.
Total free block and/or free inode count incorrect.
.PP
Orphaned files and directories (allocated but unreferenced) are,
with the operator's concurrence, reconnected by
placing them in the "lost+found" directory.
The name assigned is the inode number.
The only restriction is that the directory "lost+found" must
preexist in the root of the filesystem being checked and
must have empty slots in which entries can be made.
This is accomplished by making "lost+found", copying
a large number of files to the directory, and then removing
them (before
.B fsck
is executed).
(See the System Administrator Manual for more
information about making "lost+found" directories.)
.PP
Checking the raw device is almost always faster.
.SH OPTIONS
.TP
.B  \-f
Echoes the output from the command into /tmp/fsck.err.
This option does not work if the filesystem being fscked is
/tmp or if /tmp isn't mounted.
.TP
.B  \-n
Assume a no response to all questions.
.TP
.B  \-s
Ignore the actual free block list and (unconditionally) construct a new
one by rewriting the super-block of the file system.  
The file system should be unmounted while this is done,
or extreme care should be taken that the system is quiescent
and that it is rebooted immediately afterwards.
This precaution is necessary so that the old, bad, in-core copy
of the superblock will not continue to be used, or written on the 
file system.
.IP
The free list can be created with optimal interleaving
according to the specification :
.RS
.IP
.br
.BI \-s c : s
space free blocks
.I s
blocks apart in cylinders of
.I c
blocks each.
.RE
.IP
If
.I c:s 
is not given, the values used when the filesystem
was created are used.
If these values were not specified, then 
.IR c =72,
.IR s =9
is assumed.
.TP
.B  \-S
Conditionally reconstruct the free list.
This option is like
.BR \-s
except that the free list is rebuilt only if there were
no discrepancies discovered in the file system.
It is useful for forcing free list reorganization
on uncontaminated file systems.
.B \-S
forces
.BR \-n .
.TP
.B \-t
If
.B fsck
cannot obtain enough memory to keep its tables,
it uses scratch files.
If the 
.B -t
option is specified, the file named in the next argument
is used as the scratch file.
Without the
.B \-t
option,
.B fsck
prompts if it needs a scratch file.
The file should not be on the file system being checked,
and if it is not a special file or did not already exist,
it is removed when
.B fsck
completes.
.TP
.B  \-y
Assume a yes response to all questions.
.SH FILES
/etc/checklist
.br
	contains default list of file systems to check.
.sp
/etc/fsck	
	the program
.SH SEE ALSO
dcheck(M),
icheck(M),
filesys(5).
.SH LIMITATIONS
Inode numbers for the "dot" directory, "\ \fB.\fR\ "
and the "parent" directory, "\ \fB..\ \fR"
in each directory should be checked for validity.
.br
The
.B \-b
option of
.BR icheck (M)
should be available.
