.po 1i
.TH ICPLOAD M Zilog
.V 08/15/84 17:40:26
.\" @[$]icpload.M	1.3 08/15/84 17:40:26 - Zilog Inc.
.ad
.fi
.SH NAME
icpload \- load and configure an ICP 8/02
.SH SYNOPSIS
.B "icpload icp#"
[ [ \fB-k \fIkernel\fR ] [ \fB-c \fIports:config ] protocols ]\fR
.SH DESCRIPTION
.B Icpload
configures ports and load protocols or kernels on the ICP 8/02.
If
.B icpload
is invoked with only the icp number, information is given
about the current port configuration and loaded protocols.
.PP
When loading protocols, the entry point of each protocol
is taken to be where it is loaded in the ICP 8/02 memory.
The name of the protocol object file, must be the `official'
name by which the protocol is known.
Only the `tail' of the path name is checked against the
offical list of protocol names.
So, if 
.I /usr/protocols/itty
is used, only
the itty portion is verified.
Currently the offical protocol names are:
.sp
.RS
itty     Intelligent terminal protocol
.RE
.sp
.SH OPTIONS
.TP
\fB-c\fI ports:config\fR
Since the ICP 8/02 has no way to determine what the configuration
of its various ports are, this option is used to set that
information into the ICP 8/02.
.I Ports
are given as a range of ports or a comma separated list.
An
.B ICP
has 9 ports which range from 0 to 8.
.RS
.I Config
is the hardware configuration of the port, and is one of the following:
.IP \fBA\fR
Asynchronous (all ports, execpt 8).
.IP \fBS\fR
Synchronous  (ports 6 and 7 only).
.IP \fBO\fR
Olympic      (ports 4 and 5 only).
.IP \fBZ\fR
Znet         (ports 6 and 7 only).
.IP \fBP\fR
Parallel     (port 8 only).
.RE
.IP
When configuring a port its adjacent port must be given the same
configuration.  Adjacent ports are defined as:
.sp
.ce 4
0,1
2,3
4,5
6,7
.TP
\fB-k\fI kernel\fR
Load the object module
.I kernel
as the kernel on the ICP 8/02.  Because of various constraints the
kernel object module must be segmented.  The kernel entry point
is where execution begins
when the ICP 8/02 comes out of reset.
Loading a kernel
also has the effect of zeroing out the port configuration and
loaded protocol information.
.SH FILES
/dev/icp*
.SH SEE ALSO
icpcntrl(M),
icp(4).
.SH DIAGNOSTICS
All diagnostics are intended to be self-explanatory.
