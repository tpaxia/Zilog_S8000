.po 1i
.TH MAKEKEY M Bell
.V 08/15/84 17:40:53
.\" @[$]makekey.M	1.4	08/15/84 17:40:53 - Zilog Inc.
.ad
.fi
.SH NAME
makekey \- generate encryption key
.SH SYNOPSIS
.B /usr/lib/makekey
.SH DESCRIPTION
.B Makekey
improves the usefulness of encryption schemes depending on a key
by increasing the amount of time required to search the key space.
It reads 10 bytes from its standard input,
and writes 13 bytes on its standard output.
The output depends on the input in a way intended to be difficult
to compute (i.e. to require a substantial fraction of a second).
.PP
The first eight input bytes (the
.IR "input key" )
can be arbitrary ASCII characters.
The last two (the
.IR salt )
are best chosen from the set of digits, upper- and lower-case
letters, and `.' and `/'.
The salt characters are repeated as the first two characters
of the output.
The remaining 11 output characters are chosen from the same set
as the salt and constitute the
.I "output key."
.PP
The transformation performed is essentially the following:
the salt is used to select one of 4096 cryptographic
machines all based on the National Bureau of Standards
DES algorithm, but modified in 4096 different ways.
Using the input key as key, a constant string is fed into
the machine and recirculated a number of times.
The 64 bits that come out are distributed into the
66 useful key bits in the result.
.PP
.B Makekey
is intended for programs that perform encryption (e.g.
.B ed
and
.BR crypt (1)).
Usually its input and output will be pipes.
.SH SEE ALSO
crypt(1),
ed(1).
.SH LIMITATIONS
Although it can be invoked from the prompt, 
\fBmakekey\fR is used mainly within the body of a program.
