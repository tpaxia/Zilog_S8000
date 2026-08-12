.po 1i
.TH MAKEWHATIS M UCB
.V 08/15/84 17:41:01
.\" @[$]makewhatis.M	1.4	08/15/84 17:41:01 - Zilog Inc.
.ad
.fi
.SH NAME
makewhatis \- remake the data base for the whatis and apropos commands
.SH SYNOPSIS
.B makewhatis
.SH DESCRIPTION
.B Makewhatis
remakes the data base for the whatis and apropos commands
from the manual sections in
.I /usr/man/*.
It uses
.BR getNAME (1)
to extract relevant text from each manual entry
and then rearranges and sorts this output.
Manuals sections may be in either the old  (version 6)
or version 7 manual formats.
.SH FILES
/usr/lib/whatis		constructed data base
.sp
/etc/makewhatis		the program
.SH SEE ALSO
getNAME(1).
