.po 1i
.TH MKFS M Bell
.V 08/15/84 17:41:04
.\" @[$]mkfs.M	1.5	08/15/84 17:41:04 - Zilog Inc.
.ad
.fi
.SH NAME
mkfs \- construct a file system
.SH SYNOPSIS
.B mkfs
.I special proto
.br
.B mkfs
.I special blocks interleave sectors
.SH DESCRIPTION
.B Mkfs
constructs a file system by writing on the special file
.I special
according to the directions found in the remainder of
the command line.
If the second argument is 
.I proto
.B mkfs
constructs a filesystem according to the prototype file
.I proto.
The prototype file contains tokens separated by spaces or
new lines.
.PP
The first token is the name of a file to be copied onto block
zero as the bootstrap program.
The second token is a number specifying the
size of the created file system.
Typically it will be the number of blocks on the device,
perhaps diminished by space for swapping.
.PP
The next token is the number of i-nodes in the i-list.
The next set of tokens comprise the specification
for the root file.
File specifications consist of tokens giving the mode,
the user-id, the group id, and the initial contents of the file.
The syntax of the contents field depends on the mode.
.PP
The mode token for a file is a 6 character string.
The first character specifies the type of the file.
(The characters
.B \-bcd
specify regular, block special, character special and
directory files respectively.)
The second character of the type is either
.B u
or
.B \-
to specify set-user-id mode or not.
The third is
.B g
or
.B \-
for the set-group-id mode.
The rest of the mode is a three digit octal number giving the
owner, group, and other read, write, execute permissions, see
.BR chmod (1).
.PP
Two decimal number tokens come after the mode;
they specify the user and group ID's of the owner of the file.
.PP
If the file is a regular file, the next token is a pathname
whence the contents and size are copied.
.PP
If the file is a block or character special file, two decimal
number tokens follow which give the major and minor device numbers.
.PP
If the file is a directory,
.B mkfs
makes the entries
.BR . ""
and
.B  ..
and then
reads a list of names and (recursively) file specifications
for the entries in the directory.
The scan is terminated with the token
.BR $ .
.PP
If the second argument is 
.IR blocks ,
.B mkfs
builds a file system with a single empty directory on it.
The size of the file system is the value of
.I blocks
interpreted as a decimal number.
The number of i-nodes is calculated as a 
function of the filesystem size.
.PP
A sample prototype specification follows:
.RS
.sp
.nf
/usr/diag/uboot
4872 55
d\-\-777 3 1
usr	d\-\-777 3 1
	sh	\-\-\-755 3 1 /bin/sh
	ken	d\-\-755 6 1
		$
	b0	b\-\-644 3 1 0 0
	c0	c\-\-644 3 1 0 0
	$
$
.fi
.RE
.sp
.SH FILES
/etc/mkfs	the program
.SH SEE ALSO
dir(5),
filsys(5).
.SH LIMITATIONS
There should be some way to specify links.
