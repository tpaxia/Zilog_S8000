.po 1i
.TH CLRI M Bell
.V 08/15/84 17:39:03
.\"@[$]clri.M	1.3	08/15/84 17:39:03 - Zilog Inc.
.ad
.fi
.SH NAME
clri \- clear i-node
.SH SYNOPSIS
.B clri
.I filesystem i-number 
.SH DESCRIPTION
.B Clri
writes zeros on the i-nodes
with the decimal
.I i-numbers
on the
.I filesystem.
After
.B clri,
any blocks
in the affected file
will show up as `missing' in an
.BR icheck (M)
of the
.I filesystem.
.PP
Read and write permission is required on the specified
file system device.
The i-node becomes allocatable.
.PP
The primary purpose of this routine
is to remove a file which
for some reason appears in no
directory.
If it is used to zap an i-node
which does appear in a directory, care should be taken to track down
the directory entry and remove it first.
Otherwise, when the i-node is reallocated to some new file,
the old entry will still point to that file.
At that point removing the old entry will destroy the new file.
The new entry will again point to an unallocated i-node,
so the whole cycle is likely to be repeated again and again.
.SH FILES
/etc/clri	program
.SH SEE ALSO
icheck(M).
.SH LIMITATIONS
If the file is open,
.B clri
is likely to be ineffective.
