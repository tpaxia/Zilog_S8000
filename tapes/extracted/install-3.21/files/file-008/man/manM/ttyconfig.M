.po 1i
.TH TTYCONFIG M Zilog
.V 08/15/84 17:42:37
.\" @[$]ttyconfig.M	1.11 08/15/84 17:42:37 - Zilog Inc.
.ad
.fi
.SH NAME
ttyconfig \- configure ports for terminal or modem line
.SH SYNOPSIS
.B ttyconfig
[
.B -m
.I ports ] [
.B -t
.I ports ]
.SH DESCRIPTION
.B Ttyconfig
is used by the system administrator to configure ports 
for use with a terminal or modem. 
Typical use of
.B ttyconfig
is in the start-up script /etc/rc_csh.
.PP
If
.B ttyconfig
is invoked with no arguments, it reports the current 
settings of the ports.
The options have the following meanings:
.TP 4
.B -m
Configure the user supplied list of ports for use with a modem.
.TP 4
.B -t
Configure the user supplied list of ports for use with a terminal.
.PP
The syntax for specifying a list of ports for the above options 
is a range of ports or a comma separated list. 
For example, to configure the Ports 1 to 6 for use
with a terminal the command line would read:
.sp
.in +6
.B ttyconfig
.B -t 1-6
.in -6
.sp
To configure Ports 0 to 4 and 15 for use with a modem
the command line would read:
.sp
.in +6
.B ttyconfig
.B -m 0-4,15
.in -6
.PP
The initial state when the system is booted, is that all 
ports are configured for use with terminals.
.SH SEE ALSO
mdmctl(2).
.SH DIAGNOSTICS
Diagnostics are issued for invalid options, invalid ports or
ranges, and not being able to get or set the port configuration.
