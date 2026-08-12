.po 1i
.TH INIT M Bell
.ad
.fi
.V 08/15/84 17:40:29
.\" @[$]init.M	1.6	08/15/84 17:40:29 - Zilog Inc.
.SH NAME
INIT \- process control initialization
.SH SYNOPSIS
.B INIT
.I [ state ]
.SH DESCRIPTION
.B INIT
is invoked inside
.SM ZEUS
as the last step in the boot procedure.
It is process number one, and is the ancestor of every other process
in the system.
As such, it can be used to control the process structure of the system.
This is done 
by the super-user
invoking
.B INIT
 with an argument.
.PP
.B INIT
has 9 states, 1 through 9;
it is invoked by the system in state 1 during manual bootstrapping,
and in state 2 during auto-booting.
It
performs the same functions on entering each state.
When a state is entered,
.B INIT
reads the file
.IR /etc/inittab
 which defines the transition into each
state.
Lines in this file have the format:
.PP
.RS
state:id:flags:command
.PP
where
.PP
.I state
is an integer from 1 to 9,
.PP
.I id
is a two character identifier (i.e. co for console, 00 for tty00, etc)
standing for some process that might be active in that state,
.PP
.I flags
are the characters t, k, c, or o,
.PP
.I command
is the name of an executable file with its optional arguments.
.RE
.PP
All lines in which the state field matches
.BR INIT 's
current state are recognized.
A process whose two character
.I id
matches one on a recognized line may be terminated (signal 15), killed
(signal 9), or both by including the
.I flags
.B t
and
.B k
in the order desired.
The signal is sent to all processes in the process group associated
with the
.IR id .
The
.I command
field is saved for later execution (see below).
.PP
After reading
.I /etc/inittab
and signaling running processes as required,
but before invoking any processes under the new state,
.B INIT
invokes
.I /etc/rc
with three arguments.
.I /etc/rc
performs housekeeping
such as removing temporary files,
mounting file systems, and starting
daemons.
The three arguments
that it receives  are the current state, the number of
times this state has been entered previously, and the prior state.
.PP
When
.I /etc/rc
has finished executing,
.B INIT
invokes all
.I commands
waiting to be executed.
(A
.I command
is considered to be
waiting to be executed if there is no process currently
running that has the same
.I id
as the command.)
The
.I flag
.B c
(continuous)
requires the
.I command
to be continuously reinvoked whenever the process with that
.I id
dies.
The
.I flag
.B o
(off)
causes the
.I command
to be ignored.
This is useful for turning lines off without extensive editing.
Otherwise, the
.I command
is invoked a maximum of one time in the current state.
.PP
.B INIT
invokes the
.I command
field read from
.I /etc/inittab
by opening
.I /
for reading and writing on file descriptors 0, 1, and 2,
resetting all signals to system default,
setting up a new process group
.RB ( setpgrp (2)),
and
.BR exec ing:
.PP
.RS
/bin/sh \|\-c \|exec\|
.I command
.RE
.SH EXAMPLES
The inittab line
.PP
1:co:c:/bin/csh </dev/console > /dev/console 2>&1
.PP
creates a single user environment when
.B INIT 1
is invoked by the super-user.  It states that in state 1
(by convention single-user mode), a process with the arbitrary
unique identifier 
.I co
should be created.  The program invoked for this process should be
the c-shell, taking its input from the console and directing
both its default output and error output back to the console.
When this process exits (i.e. logout) it should be reinvoked.
.PP
Invoking
.B INIT 2
when
.I inittab
contains the entry
.PP
2:co:c:/etc/getty console 2
.PP
attaches a
.B login
process to the console in multi-user state (state 2)
and sets its baud rate to 9600.
the entry
.PP
2:05:c:/etc/getty tty05 2
.PP
sets up line /dev/tty05 for use by 9600 baud terminals,
while
.PP
1:05:k:/etc/getty !
.PP
will ensure that it is not active on return (or entry)
to single-user mode.
.SH DIAGNOSTICS
When
.B INIT
can do nothing else because of a missing
.I /etc/inittab
or when it has no children left,
it will try to execute a shell on
.IR /dev/console .
When the problem has been fixed, it is necessary to change states,
and terminate the shell.
.SH LIMITATIONS
.B INIT
does not complain if the state\-id pairs in
.I /etc/inittab
are not unique.
For any given pair, the last one in the file is valid.
.SH FILES
/etc/INIT	The program
.br
/etc/inittab
.br
/etc/rc
.br
/bin/sh
.br
/dev/console
.SH SEE ALSO
login(1),
sh(1),
exec(2),
setpgrp(2),
inittab(5),
getty(M).
