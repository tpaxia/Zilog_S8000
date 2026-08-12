.po 1i
.TH DCHECK M Bell
.V 08/15/84 17:39:32
.\" @[$]dcheck.M	1.4	08/15/84 17:39:32 - Zilog Inc.
.ad
.fi
.SH NAME
dcheck \- file system directory consistency check
.SH SYNOPSIS
.B dcheck
[
.B \-i
.I numbers 
]
.I [ filesystem ]
.SH DESCRIPTION
.B Dcheck
reads the directories in a file system and compares
the link-count in each i-node with the number of directory
entries by which it is referenced.
If the file system is not specified, a set of default
file systems is checked.
.PP
The
.B \-i
flag is followed by a list of i-numbers;
when one of those i-numbers turns up in a directory,
the number, the i-number of the directory,
and the name of the entry are reported.
.PP
The program is fastest if the raw version of the special
file is used, since the i-list is read in large chunks.
.SH FILES
/etc/dcheck	program
.SH SEE ALSO
filsys(5),
clri(M),
icheck(M),
ncheck(M).
.SH DIAGNOSTICS
When a file turns up for which the link-count and the number
of directory entries disagree, the relevant facts are reported.
Allocated files which have 0 link-count and no entries are also
listed.
The only dangerous situation occurs when there are more
entries than links;
if entries are removed, so the link-count drops to 0,
the remaining entries point to thin air.
They should be removed.
When there are more links than entries, or there is
an allocated file with neither links nor entries,
some disk space may be lost but the situation will not degenerate.
.SH LIMITATIONS
Since
.B dcheck
is inherently two-pass in nature, extraneous diagnostics
may be produced if applied to active file systems.
