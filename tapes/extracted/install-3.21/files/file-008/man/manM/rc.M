.po 1i
.TH RC M Zilog
.V 08/15/84 17:41:39
.\" @[$]rc.M	1.5	08/15/84 17:41:39 - Zilog Inc.
.ad
.fi
.SH NAME
rc  \- "read command" startup control script
.br
rc_csh \- "read command" Cshell multi-user startup script
.SH SYNOPSIS
.B rc
.br
.B rc_csh
.SH DESCRIPTION
.B Rc
is invoked by 
.B INIT 
when the system changes states (e.g. from multi-user
mode to single-user mode, and vise versa). 
.B Rc_csh
in invoked by 
.B rc
when the system goes to multi-user mode.
.B Rc_csh
is a shell script, and as such can easily be altered
to suit the particular needs of a system.
Generally, commands in
.B rc_csh
perform miscellaneous functions such as checking the
consistency of the disk, mounting file systems, etc.
.PP
.B INIT
invokes
.B rc
with three arguments: target state, the number of times
the state has been entered and the last state. This allows
.B rc
to invoke other programs selectively depending on the
specified state transition (e.g. 
.B rc_csh
should be invoked when the system goes multi-user).
If the system is booted to a multi-user state automatically,
the last state is "0".
.SH FILES
/etc/rc		the program
.sp
/etc/rc_csh	the program
.SH SEE ALSO
INIT(M).
.SH THE PROGRAMS
.PP
The \fBrc\fR file:
.nf
.na

: "@[$]rc	2.11  03/28/83 09:21:03 - Zilog Inc"
: "This is the rc control script. Init invokes this script
: "and then for the other important states where real work 
: "occurs we use csh(1) scripts"

TZ=PST8PDT
export TZ
trap "INIT 1" 2

: "In all cases i/o is re-directed to the console"

: "zero out the mount table if this is a bootup"
if [ $3 = "0" ]
	then /bin/cat /dev/null > /etc/mnttab
	     /etc/devnm / | grep root | /etc/setmnt
fi

(
case ${1-2} in
1)
	echo
	uname -sn
	echo Single-User Mode
	if [ $3 = "2" ]
		then /etc/killall
	fi
	/etc/umfs > /dev/null 2>&1
	;;
2)
	if [ $1 != $3 ]
		then exec rc_csh
	fi
	;;

*)
	echo "Unknown state for init:" $*
	;;
esac
)

.sp
.PP
The \fBrc_csh\fR file:
.nf
.na

# "@[$]rc_csh	2.18  03/28/83 09:21:04 - Zilog Inc"
	echo
	uname -sn
	echo "Multi-user Startup"
	echo

# Check for filesystem consistency
	/etc/fsck -y /dev/root
	/etc/fsck -y /dev/rusr /dev/rtmp
	/etc/fsck -y -t /scratch /dev/rz

# Set the date
	/etc/datem

# Now mount the filesystems
	/etc/mfs

# Give the user a chance to interrupt, then go multi-user
	/bin/echo -n 'The date the system knows is ' ; date
	echo 'Going multi-user in 30 seconds\!'

# configure system for correct modem/tty configuration
	/etc/ttyconfig -t 0-7

# Remove the remote lock file
	cat /dev/null > /usr/spool/uucp/LCK..tmp
	rm -f /usr/spool/uucp/LCK..*

# Save the su and cron log files
	if ( -e /usr/adm/sulog ) then
		mv /usr/adm/sulog /usr/adm/osulog
	endif
	if ( -e /usr/lib/cronlog ) then
		mv /usr/lib/cronlog /usr/lib/ocronlog
	endif

# zero out utmp file
	cat /dev/null > /etc/utmp

	exit 0
.fi
.ad
