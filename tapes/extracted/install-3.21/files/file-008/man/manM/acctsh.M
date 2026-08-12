.po 1i
.TH ACCTSH M Bell
.V 08/15/84 17:38:42
.\" @[$]acctsh.M	1.4	08/15/84 17:38:43 - Zilog Inc.
.ad
.fi
.SH NAME
acctsh \- shell procedures for accounting
.SH SYNOPSIS
.B chargefee
.I login-name number
.PP
.B ckpacct
.I [blocks]
.PP
.B dodisk
.PP
.B lastlogin
.PP
.B monacct
.I number
.PP
.B nulladm
.I file
.PP
.B prctmp
.PP
.B prdaily
.PP
.B prtacct
.I file [ heading ]
.PP
.B runacct
.I [mmdd] [mmdd state]
.PP
.B shutacct
.I [ reason ]
.PP
.B startup
.PP
.B turnacct
[
.B on
|
.B off
|
.B switch
]
.SH DESCRIPTION
.B Chargefee
is invoked to charge
.I number
dollars to
.IR login-name .
A record is written to
.IR /usr/adm/fee ,
to be merged with other accounting records during the night.
.PP
.B Ckpacct
is initiated via 
.BR cron .
It periodically checks the size of
.IR /usr/adm/pacct .
If the size exceeds \fIblocks\fP, 1000 by default,
.B turnacct
will be invoked with argument
.IR switch .
.PP
.B Dodisk
is invoked by
.B cron
to perform the disk accounting functions.
.PP
.B Lastlogin
is invoked by
.B runacct
to update
.IR /usr/adm/acct/sum/loginlog ,
which shows the last date on which each person logged in.
.PP
.B Monacct
should be invoked once each month or each accounting
period.
.I Number
indicates
which month or period it is.
It creates summary files in
.I /usr/adm/acct/fiscal
and restarts summary file in
.IR /usr/adm/acct/sum .
.B Nulladm
creates
.I file
with mode 644 and insures owner is
.BR adm .
It is called by
.BR lastlogin ,
.BR runacct ,
and
.BR turnacct .
.PP
.B Prctmp
can be used to print the session record file (normally
.I /usr/adm/acct/nite/ctmp
created by
.B acctcon1
(see
.BR acctcon (M)).
.PP
.B Prdaily
is invoked by
.B runacct
to print a report of the previous day's accounting.
The report resides in
.I /usr/adm/acct/sum/rprt xxxx
where
.I xxxx
is the month and day of the report.
The
daily accounting reports may be printed with the
command:
.sp
.RS
\fBcat /usr/adm/acct/sum/rprt\(**\fR
.RE
.sp
as often
as desired and they must be explicitly deleted
when no longer needed.
.PP
.B Prtacct
can be used to format and print any total accounting file.
.PP
.B Runacct
performs the accumulation of connect,
process,
fee,
and disk accounting on a daily basis.
It also creates summaries of command usage.
For more information, see \fIrunacct\fP(M).
.PP
.B Shutacct
should be invoked during a system shutdown to turn process accounting
off and append a "reason" record to
.IR /usr/adm/wtmp .
.B Startup
should be called by
.BR rc (8)
to turn the accounting on
whenever the system is brought up.
.PP
.B Turnacct
is an interface to
.B accton
(see
.BR acct (M))
to turn process accounting \fBon\fP or \fBoff\fP.
The
.B switch
argument moves the current
.I /usr/adm/pacct
to
the next free name in
.IR /usr/adm/pacct[1-9] ,
turns accounting off,
then turns it back on again.
This procedure is called by
.B ckpacct
via the \fBcron\fP to keep the \fIpacct\fP file
size smaller.
.SH FILES
.ta \w'/usr/adm/pacct[1-9]\ \ \ \ 'u +.5i
.nf
/usr/adm/fee	accumulator for fees
.sp
/usr/adm/pacct	current file for per-process accounting
.sp
/usr/adm/pacct[1-9]	used if pacct gets large and during
	execution of daily accounting procedure
.sp
/usr/adm/wtmp	login/logoff summary
.sp
/usr/adm/wtmp[1-9]	used during daily accounting procedure
.sp
/usr/adm/acct/nite	working directory
.sp
/usr/lib/acct	holds all accounting commands listed in
	sub-class M of this manual
/usr/adm/acct/sum	summary directory, should be saved
.fi
.DT
.SH SEE ALSO
acct(M),
acctcms(M),
acctcom(M),
acctcon(M),
acctmerg(M),
acctprc(M),
fwtmp(M),
runacct(M),
acct(2),
acct(5),
utmp(5).
