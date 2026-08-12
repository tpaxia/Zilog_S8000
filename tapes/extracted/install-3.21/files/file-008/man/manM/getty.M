.po 1i
.TH GETTY M Bell
.ad
.fi
.V 08/15/84 17:40:13
.\" @[$]getty.M	1.8 08/15/84 17:40:13 - Zilog Inc.
.SH NAME
GETTY \- set the modes of a terminal
.SH SYNOPSIS
.B GETTY
name type delay
.SH DESCRIPTION
.B GETTY
is normally invoked
by
.BR INIT (M)
as the first step in allowing users to login to the system.
Lines in
.I /etc/inittab
tell
.B INIT
to invoke
.B GETTY
with the proper arguments.
.PP
.I Name
should be the name of a terminal in
.I /dev
(e.g.,
.BR tty03 );
.I type
should be a single character chosen from
.BR \- ,
.BR 0 ,
.BR 1 ,
.BR 2 ,
.BR 3 ,
.BR 4 ,
.BR 5 ,
.BR 6,
.BR 7,
or
.B 8 
(may vary locally)
which selects a speed table in
.BR GETTY ,
or
.BR ! ,
which tells
.B GETTY
to update
.I /etc/utmp
and exit;
.I delay
is relevant for dial-up ports only.
It specifies the time in seconds that should elapse
before the port is disconnected if the user does
not respond to the \fBZeus login:\fP request.
.PP
First,
.B GETTY
types the \fBZeus login:\fP message.
The 
.B "Zeus login:"
message depends on the speed table being used,
and may include
the characters that put the 
.SM GE
TermiNet 300
terminal into full-duplex,
take the
.SM DASI
terminals out of the plot mode,
or put a
.SM TELETYPE\*S\*R
Model 37
into full-duplex.
If the terminal type as given in 
.I /etc/ttytype
can have its screen cleared,
the 
.B Zeus login:
message
will also contain the characters that will clear the screen.
The Zeus portion of the login prompt,
is obtained from the nodename field of
.BR uname (2).
.PP
Then the user's login
name
is read, a character at a time.
.PP
While reading,
.B GETTY
tries to adapt to the terminal, speed,
and mode that is being used.
If a null character is received, it is assumed to be the result
of a "break" ("interrupt").
The speed is then
changed based on the speed table that
.B GETTY
is using, and 
.B Zeus login:
is typed again.
Subsequent breaks cause a cycling through
the speeds in the speed table being used.
.PP
The user's
login name
is terminated by a new-line or
carriage-return character.
The latter results in the system being set to
treat carriage returns appropriately.
If the
login name
contains only upper-case alphabetic characters,
the
system is told to map any future upper-case characters
into the corresponding lower-case characters.
.PP
Finally,
.BR login (1)
is called with the user's login
name
as argument.
.PP
Speed sequences for the speed tables:
.PP
.PD 0
.RS
.TP
.B \-
B110;  for 110 baud console
.SM TTY\*S.
.TP
.B 0
B300\-B1200\-B150\-B110; 
normal dial-up sequence starting at B300. 
Useful as a
default for dialup lines accessed by a variety of terminals.
.TP
.B 1
B150;  
no sequence.  
Optimized for a 150-baud Teletype Model 37.
.TP
.B 2
B9600;  
no sequence.  
Intended for an on-line 9600-baud terminal.
.TP
.B 3
B1200\-B300;  
normal dial-up sequence starting at B1200. 
Useful with Bell 212
datasets where most terminals run at 1200-baud.
.TP
.B 4
B300;  for 300-baud terminals similar to the LA36 \s-1DEC\s0writer.
.TP
.B 5
B300\-B1200;  normal dial-up sequence starting at B300.
.TP
.B 6
B2400;  no sequence.
.TP
.B 7
EXTA (19200); no sequence.
.TP
.B 8
B4800; no sequence.
.RE
.PD
.SH FILES
/etc/GETTY	The program
.SH SEE ALSO
login(1), tty(4), inittab(5), utmp(5), INIT(M), uname(2), ttytype(5).
.SH BUGS
Ideally, the speed tables would be read from a file,
not compiled into
.BR GETTY .
