.po 1i
.TH ICPCNTRL M Zilog
.V 08/15/84 17:40:24 
.\" @[$]icpcntrl.M	1.3 08/15/84 17:40:24 - Zilog Inc.
.ad
.fi
.SH NAME
icpcntrl \- start and stop ICP's and their protocols
.SH SYNOPSIS
.B icpcntrl
.I " icp# [ [-start [protocol:ports] ] [-stop [protocol:ports] ] "
.SH DESCRIPTION
.B Icpcntrl
is used to control the running of an ICP 8/02 and its protocols.
If
.B icpcntrl
is invoked with only the icp number, information is given about the
protocols that are currently active on the various ports.
.PP
When giving an protocol name, the name must be the `official'
name by which the protocol is known (the name it was loaded
by, using 
.BR icpload (M)).
Currently the offical protocol names are:
.nf
     itty    Intelligent terminal protocol
.fi
.SH OPTIONS
.TP
\fB-start\fI [protocol:ports]\fR
Start an ICP 8/02 or an indicated protocol.
If the \fIstart\fR option is given with no arguments,
then only the ICP is started.
.br
When the information for the protocol and ports are given,
they have the following meanings:
.RS
.IP \fIprotocol\fR
This is the `official' name by which the protocol is known.
.IP \fIports\fR
This field gives the ports the indicated protocol should be started on.
The ports are given as a range of ports or a comma separated list.
An \fBICP\fR has 9 ports which range from 0 to 8.
.RE
.TP
\fB-stop\fI [protocol:ports]\fR
Stop an ICP 8/02 or an indicated protocol.
If the 
.B stop
option is given with no arguments, then the
ICP is stopped (a side-effect is that all protocols are stopped
ungracefully also).
.br
The
.I protocol
and
.I ports
information has the same meanings as in the
.B start
options.
.SH FILES
/dev/icp*
.SH SEE ALSO
icpload(M),
icp(4).
