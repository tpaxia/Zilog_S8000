.po 1i
.TH INSTALL M Bell
.V 08/15/84 17:40:38
.\" @[$]install.M	1.3	08/15/84 17:40:38 - Zilog Inc.
.ad
.fi
.SH NAME
install \- install commands
.SH SYNOPSIS
\fBinstall\fR
.br
	[\fB\-c\fI dira\fR ]
.br
	[\fB\-f\fI dirb\fR ]
.br
	[\fB\-i\fR]
.br
	[\fB\-n\fI dirc\fR ]
.br
	[\fB\-o\fR]
.br
	[\fB\-s\fR]
.br
	\fIfile\fR
.br
	[ \fIdirx\fR \.\.\.]
.SH DESCRIPTION
.B Install
is most commonly used in "makefiles" (see
.BR make (1))
to install a
.I file
(updated target file) in a specific place within a file system.
Each
.I file
is installed by copying it into the appropriate directory,
retaining the mode and owner of the original command.
The program prints messages telling exactly what files
it is replacing or creating and where they are going.
.PP
If no options or directories
.RI ( dirx " .\|.\|.)"
are given,
.B install
will search (using
.BR find (1))
a set of default directories (
.I  /bin, /usr/bin, /etc, /lib,
and
.I /usr/lib ,
in that order)
for a file with the same name as 
.IR file .
When the first occurrence is found,
.B install
issues a message saying it is overwriting that file with
.IR file ,
and proceeds to do so.
If the file is not found, the program states this and exits
without further action.
.PP
If one or more directories
.RI ( dirx " \.\.\.)"
are specified after
.IR file ,
those directories will be searched before the directories
specified in the default list.
.SH OPTIONS
.TP 15
.BI \-c "  dira"
Installs a new command in the directory specified in
.IR dira .
Looks for
.I file
in
.I dira
and installs it there if not found.
If found,
.B install
issues a message saying the file already exists, and exits
without overwriting it.
Can be used alone or with the
.B \-s
option.
.TP 15
.BI \-f "  dirb"
Forces
.I file
to be installed in given directory, whether or not one already exists.
If it does not already exist, the mode and owner of the new file
will be set to \fB751\fR and \fBbin\fR, respectively.
If the file already exists, the mode and owner will be that
of the already existing file.
Can be used alone or with the
.B \-o
or
.B \-s
options.
.TP 15
.B \-i
Ignores default directory list, searching only through the
given directories
.RI ( dirx " \.\.\.)."
Can be used alone or with other options,  except
.B \-c
and
.BR \-f .
.TP 15
.BI \-n "  dirc"
If
.I file
is not found in any of the searched directories, it is put in
the directory specified in
.IR dirc .
The mode and owner of the new file will be set to \fB755\fR and
\fBbin\fR, respectively.
Can be used alone or with other options, except
.B \-c
and
.BR \-f .
.TP 15
.B \-o
If
.I file
is found, this saves the "found" file by copying it to
.BI OLD file
in the directory in which it was found.
Can be used alone or with other options, except
.BR \-c .
.TP 15
.B \-s
Suppresses printing of messages other than error messages.
Can be used alone or with any other options.
.SH FILES
/etc/install	the program
.SH WARNING
.B Install
is a Bourne shell script. If your login shell is the
C shell,
.B install
must be invoked as a shell script from 
.I makefile
as follows:
.sp
.RS
/bin/sh /etc/install file
.RE
.sp
This can be done easily as a 
.B make
macro definition. For example, 
.sp
.RS
INS=/bin/sh /etc/install
.RE
.sp
and to execute 
.B install
.sp
.RS
$(INS) file
.RE
.sp
This is not necessary if your login shell is the 
.I Bourne Shell,
or if you use 
.B install 
from the command level
of either shell, or if it is invoked from command scripts.
