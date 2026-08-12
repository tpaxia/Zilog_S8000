/* @[$]fblk.h	4.1  06/11/84 12:30:54 - Zilog Inc */

struct fblk
{
	int    	df_nfree;
	daddr_t	df_free[NICFREE];
};
