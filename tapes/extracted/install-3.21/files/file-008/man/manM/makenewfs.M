.po 1i
.TH MAKENEWFS M Zilog
.V 08/15/84 17:40:56
.\" @[$]makenewfs.M	1.8 08/15/84 17:40:56 - Zilog Inc.
.ad
.fi
.SH NAME
makenewfs \- sets the date, removes nonapplicable /dev entries, and
constructs and restores filesystems 
.SH SYNOPSIS
.B /etc/makenewfs
.SH DESCRIPTION
.B Makenewfs
is a C shell script which performs five main functions.
.PP
.B Makenewfs
is intended to be run during the initial boot from tape.
It should be run in single-user mode after root (/) and /usr
are restored from tape.
.PP
.B Makenewfs
constructs the default filesystem layout.
It also requests, and then sets the current date.
It interactively removes all nonapplicable /dev entries,
and it creates links for the nodes in 
the /dev directory depending on the
model type determined by
.BR model (M).
For example, if the model is determined to be an
.BR 11 ,
.B makenewfs
links the filenames (r)usr, swap, (r)root, (r)tmp
and (r)z to the nodes
(r)md0, md1, (r)md2, (r)md3, and (r)md4, respectively.
At this point, the system administrator may elect to quit,
leaving the /z and /tmp filesystems unaltered.
This is useful if only a
.BR restor (M)
of root and /usr is needed.
If desired, it creates the filesystems /tmp and /z,
and then labels those filesystems.
.PP
The program may be run to restore the disk after severe damage to
it has occurred.
It is important to note that if filesystems /z or /tmp are 
already on the disk and the program is run to completion,
.B THEY WILL BE COMPLETELY DESTROYED.
Therefore, this program should be run only on an initial boot
or when the filesystems have been irreparably damaged.
.PP
In order to safeguard against malicious or unintentional usage, the
program is owned by zeus with mode 000. 
It is necessary to enter
.B chmod 700 /etc/makenewfs
before executing this program.
The program will revert to mode 000 and owner zeus upon termination.
.SH SEE ALSO
mkfs(M), restor(M), model(M).
.br
The System 8000 ZEUS Administrator Manual
.SH LIMITATIONS
This program applies only to the default disk layout, and standard
Zilog distribution tape, as specified in the ZEUS Administrator Manual.
It will have to be changed for non-standard disk layouts or
other dump tapes.
