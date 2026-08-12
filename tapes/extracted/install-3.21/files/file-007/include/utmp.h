/* @[$]utmp.h	2.1  07/23/82 17:36:25 - Zilog Inc */
/*
 * Format of /etc/utmp and /usr/adm/wtmp
 */

struct utmp {
	char	ut_line[8];		/* tty name */
	char	ut_name[8];		/* user id */
	long	ut_time;		/* time on */
};
