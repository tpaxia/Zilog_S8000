/* @[$]times.h	4.1  06/11/84 12:31:30 - Zilog Inc */
/*
 * Structure returned by times()
 */
struct tms 
{
	time_t	tms_utime;		/* user time */
	time_t	tms_stime;		/* system time */
	time_t	tms_cutime;		/* user time, children */
	time_t	tms_cstime;		/* system time, children */
};
