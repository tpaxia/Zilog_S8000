/* @[$]utsname.h	4.2  06/11/84 12:31:39 - Zilog Inc */

#define UTS_LENGTH	9

struct utsname 
{
	char	sysname[UTS_LENGTH];
	char	nodename[UTS_LENGTH];
	char	release[UTS_LENGTH];
	char	version[UTS_LENGTH];
};

struct utsname 	utsname;
