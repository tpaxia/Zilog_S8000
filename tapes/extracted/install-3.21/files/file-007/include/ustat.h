/* @[$]ustat.h	2.1 07/23/82 17:36:24 - Zilog Inc */

struct  ustat {
	daddr_t	f_tfree;	/* total free */
	ino_t	f_tinode;	/* total inodes free */
	char	f_fname[6];	/* filsys name */
	char	f_fpack[6];	/* filsys pack name */
};
