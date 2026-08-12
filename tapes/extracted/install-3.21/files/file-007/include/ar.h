/* @[$]ar.h	1.1  07/23/82 17:35:55 - Zilog Inc */
#define	ARMAG	0177545
struct	ar_hdr {
	char	ar_name[14];
	long	ar_date;
	char	ar_uid;
	char	ar_gid;
	int	ar_mode;
	long	ar_size;
};
