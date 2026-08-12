.po 1i
.TH DATEM M Zilog
.V 08/15/84 17:39:30
.\" @[$]datem.M	1.5	08/15/84 17:39:30 - Zilog Inc.
.ad
.fi
.SH NAME
datem \- friendly date and time setting
.SH SYNOPSIS
.B datem
.SH DESCRIPTION
.B Datem
prompts for and sets the date and time.
.LP
Enter the date in either of the popular forms:
.I dd-mo-yy,
where 
.I dd
is the day of the month,
.I mo
is the conventional abbreviation for the month,
and
.I yy
is the last two digits of the year;
or
mm/dd/yy,
where
.I mm
is the
.IR mm 'th
month of the year,
.I dd
is the day of the month,
and
.I yy
is the last two digits of the year.
Thus January 4, 1982, can be entered either as 4-Jan-82 or 1/4/82.
.LP
Enter the time using the 24-hour clock in the form hh:mm.
(Time is
.I local
time.)
Thus 3:31 P.M. is 15:31, midnight is 0:00, 8 a.m. is 08:00.
.LP
All impossible and some unlikely entries are rejected.
An empty date entry sets the time without changing the date.
.PP
If
.B datem
receives no reply in 5 minutes, it times out and exits.
.PP
.B Datem 
is normally invoked by including it in 
.I /etc/rc_csh,
the ZEUS startup file.
.SH FILES
/etc/datem 	the program
.SH SEE ALSO
date(1),
rc(M).
.SH DIAGNOSTICS
\fINot superuser\fR if anyone but superuser attempts to change
date and time.
.SH LIMITATIONS
Doesn't review date or time.
