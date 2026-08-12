.po 1i
.TH RUNACCT M Bell
.V 08/15/84 17:42:04
.\" @[$]runacct.M	1.5	08/15/84 17:42:04 - Zilog Inc.
.ad
.fi
.SH NAME
runacct \- run daily accounting
.SH SYNOPSIS
.B runacct
[
.I mmdd
[
.I state
]]
.SH DESCRIPTION
.B Runacct
is the main daily accounting shell procedure.
It is normally initiated via
.BR cron (M).
.B Runacct
processes connect, fee, disk, and process accounting files.
It also prepares summary files for
.B prdaily
or billing purposes.
.PP
.B Runacct
takes care not to damage active accounting files or summary
files in the event of errors.
It records its progress by writing descriptive diagnostic
messages into 
.IR active .
When an error is detected, a message is written to
.IR /dev/console ,
mail (see 
.BR mail (1))
is sent to
.BR zeus \ and \ adm ,
and 
.B runacct
terminates.
.B Runacct
uses a series of lock files to protect against re-invocation.
The files 
.I lock
and 
.I lock1
are used to prevent
simultaneous invocation, and 
.I lastdate
is used to
prevent more than one invocation per day.
.PP
.B Runacct
breaks its processing into separate, restartable 
.I states
using 
.I statefile
to remember the last 
.I state
completed.
It accomplishes this by writing the
.I state
name into
.BR statefile .
.PP
.B Runacct
then looks in 
.I statefile
to see what it has done
and to determine what to process next.
.I States
are executed in the following order:
.LP
.TP 12
.B SETUP
Move active accounting files into working files.
.TP 12
.B WTMPFIX
Verify integrity of
.B wtmp
file, correcting date changes if necessary.
.TP 12
.B CONNECT1
Produce connect session records in
.I ctmp.h
format.
.TP 12
.B CONNECT2
Convert
.I ctmp.h
records into
.I tacct.h
format.
.TP 12
.B PROCESS
Convert process accounting records into
.I tacct.h
format.
.TP 12
.B MERGE
Merge the connect and process accounting records.
.TP 12
.B FEES
Convert output of
.B chargefee
into
.I tacct.h
format and merge with connect and process accounting records.
.TP 12
.B DISK
Merge disk accounting records with connect, process,
and fee accounting records.
.TP 12
.B MERGETACCT
Merge the daily total accounting records in
.I daytacct
with the summary total accounting records in
.IR /usr/adm/acct/sum/tacct .
.TP 12
.B CMS
Produce command summaries.
.TP 12
.B USEREXIT
Any installation-dependent accounting programs can be
included here.
.TP 12
.B CLEANUP
Cleanup temporary files and exit.
.PP
To restart
.B runacct
after a failure, first check the
.B active
file for diagnostics, then fix up any corrupted data files
such as
.IR pacct \ or \ wtmp .
The
.B lock
files and
.B lastdate
file must be removed before
.B runacct
can be restarted.
The argument
.I mmdd
is necessary if 
.B runacct
is being restarted,
and specifies the month and day for which
.B runacct
will rerun the accounting.
Entry point for processing is based on the contents of
.IR statefile ;
to override this,
include the desired
.I state
on the command line to designate where processing
should begin.
.SH EXAMPLES
To start 
.BR runacct .
.RS 5
nohup runacct 2> /usr/adm/acct/nite/fd2log &
.RE
.PP
To restart 
.BR runacct .
.RS 5
nohup runacct 0601 2>> /usr/adm/acct/nite/fd2log &
.RE
.PP
To restart 
.B runacct
at a specific 
.IR state .
.RS 5
nohup runacct 0601 MERGE 2>> /usr/adm/acct/nite/fd2log &
.RE
.SH FILES
/usr/lib/acct/runacct
.br
/usr/adm/wtmp
.br
/usr/adm/pacct[1-9]
.br
/usr/src/cmd/acct/tacct.h
.br
/usr/src/cmd/acct/ctmp.h
.br
/usr/adm/acct/nite/active
.br
/usr/adm/acct/nite/daytacct
.br
/usr/adm/acct/nite/lock
.br
/usr/adm/acct/nite/lock1
.br
/usr/adm/acct/nite/lastdate
.br
/usr/adm/acct/nite/statefile
.br
/usr/adm/acct/nite/ptacct[1-9].
.I mmdd
.SH SEE ALSO
acctcom(M),
acct(2),
acct(5),
utmp(5),
acct(M),
acctcms(M),
acctcon(M),
acctmerg(M),
acctprc(M),
acctsh(M),
cron(M),
fwtmp(M).
.br
.I "The PWB/ZEUS Accounting System"
in the ZEUS Utilities Manual
.SH DIAGNOSTICS
Self explanatory.
.SH LIMITATIONS
Normally it is not a good idea to restart
.B runacct
in the
.B SETUP
.IR state .
Run
.B SETUP
manually and restart via:
.PP
.RS 5
.B runacct
.I mmdd
.B WTMPFIX
.RE
.PP
If
.B runacct
failed in the
.B PROCESS
.IR state,
remove the last
.B ptacct
file because it will not be complete.
