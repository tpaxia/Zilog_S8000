.po 1i
.TH KDB M Zilog
.V 08/15/84 17:40:42
.\" @[$]kdb.M	1.1 08/15/84 17:40:42 - Zilog Inc
.ad
.fi
.SH NAME
kdb  \- enable or disable kernel debugger
.SH SYNOPSIS
.B kdb
[
.B n
] [
.B y
] [
.B on
] [
.B off
]
.SH DESCRIPTION
.B Kdb
with argument
.B n
or
.B off
disables the kernel debugger by clearing the global variable
kdebug in the kernel's data space.
.B Kdb
with argument
.B y
or
.B on
enables the kernel debugger by setting kdebug to 1.
By itself,
.B kdb
reports the current state without changing it.
.SH RESTRICTIONS
Only the super-user
can change the state of the debug flag, though anyone can look at it.
.SH FILES
/dev/kmem
.br
/zeus for namelist
.SH DIAGNOSTICS
.B Kdb
considers it an error if it finds kdebug to have a value other than 0 or 1.
If the kernel does not have the debugger installed,
.B kdb
says "no namelist" and exits.
Exit status is 0 if the kernel debugger is enabled,
1 if not, 2 on error.
