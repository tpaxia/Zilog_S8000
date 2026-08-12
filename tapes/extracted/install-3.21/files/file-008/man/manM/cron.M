.po 1i
.TH CRON M Bell
.V 08/15/84 17:39:21
.\" @[$]cron.M	1.5 08/15/84 17:39:21 - Zilog Inc.
.ad
.fi
.SH NAME
cron \- clock daemon
.SH SYNOPSIS
.B cron
.SH DESCRIPTION
.B Cron
executes commands at specified dates and times.
It follows the instructions in
.IR /usr/lib/crontab .
Because
.B cron
never exits, it should be executed only once.
This is best done by running
.B cron
from the initialization process through the file
.I /etc/rc
(see
.BR init (M)).
.PP
The file
.I crontab
consists of lines of six fields each.
The fields are separated by spaces or tabs.
The first five are integer patterns specifying the minute (0-59),
hour (0-23), day of the month (1-31), month of the year (1-12),
and day of the week (0-6, with 0=Sunday).
Each of these patterns can contain:
.PP
.RS
a number in the (respective) range indicated above;
.br
two numbers separated by a minus (indicating an inclusive range);
.br
a list of numbers separated by commas (meaning all of these numbers); or
.br
an asterisk (meaning all legal values).
.RE
.PP
The sixth field is a string that is executed by the 
shell at the specified time(s).
A
.B %
in this field is translated into a new-line character.
Only the first line (up to a
.B %
or the end of line) of the command field is executed by the shell.
The other lines are made available to the command as standard input.
.PP
.B Cron
examines
.I crontab
once a minute to see if it has changed;
if it has,
.B cron
reads it.
It takes only a minute for entries to become effective.
.SH FILES
/usr/lib/crontab
.br
/usr/lib/cronlog
.SH SEE ALSO
sh(1),
init(M).
.SH DIAGNOSTICS
A history of all actions by
.B cron
are recorded in
.IR /usr/lib/cronlog .
.SH LIMITATIONS
.B Cron
reads
.I crontab
only when it has changed, but it reads the in-core
version of that table once a minute.
A more efficient algorithm could be used.
The overhead in running
.B cron
is about one percent of the CPU,
exclusive of any commands executed by
.BR cron .
