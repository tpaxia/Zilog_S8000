/* @[$]timeb.h	4.1  06/11/84 12:31:30 - Zilog Inc */

/*
 * Structure returned by ftime system call
 */

struct timeb 
{
	time_t		time;
	unsigned short 	millitm;
	short		timezone;
	short		dstflag;
};
