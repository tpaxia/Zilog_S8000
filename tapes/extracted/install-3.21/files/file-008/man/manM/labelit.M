.po 1i
.TH LABELIT M Bell
.V 08/15/84 17:40:46
.\" @[$]labelit.M	1.11 08/15/84 17:40:46 - Zilog Inc.
.ad
.fi
.SH NAME
labelit \- label filesystems
.SH SYNOPSIS
.B /etc/labelit
.IR special [
.I fsname volume
[ 
.B \-n
[
.I ff-inode
] ] ]
.SH DESCRIPTION
.PP
.B Labelit
can be used to provide initial labels for unmounted disk or
tape filesystems.
With the optional arguments omitted,
.B labelit
prints current label values.
The
.B \-n
option provides for initial labeling of new tapes only
(this destroys previous contents).
.I Ff-inode
is the inode number of a file produced by 
.BR ff (M)
that gives a listing of the contents of the filesystem being dumped with
.BR volcopy (M).
This number is recorded in the header that
.B labelit
creates on the tape.
The
.I fsname
argument represents the mounted name (e.g.
.BR root ,
.BR usr ,
etc.)
of the filesystem being copied.
.PP
The
.I special
argument should be the physical disk section or tape (e.g.
.IR /dev/rzd1 ,
.IR /dev/rmt0 ,
etc.).
In order to label the root filesystem (which is always mounted),
\fIspecial\fR must be the blocked device; for example, /dev/md2 instead
of /dev/rmd2.
.PP
.I Fsname
and
.I volname
are recorded in the last 12 characters of the superblock
(char s_fname[6], s_fpack[6]).
.SH EXAMPLES
To label the /usr superblock:
.sp
.nf
	\fBlabelit /dev/rusr /usr 1\fR
.sp
To label the /z superblock:
.sp
	\fBlabelit /dev/rz /z 1\fR
.sp
To label the root superblock:
.sp
	\fBlabelit /dev/root root 1\fR
.sp
.fi
Notice that the volume number is required to change a label.
.SH SEE ALSO
filsys(5).
.SH LIMITATIONS
Only device names beginning
/dev/[n]rct? or /dev/[fsn]rmt?
are treated as tapes.
Tape record sizes are determined both by density and by drive type.
