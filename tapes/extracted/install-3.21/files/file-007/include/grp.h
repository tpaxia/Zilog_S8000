/* @[$]grp.h	2.1  07/23/82 17:36:03 - Zilog Inc */
struct	group { /* see getgrent(3) */
	char	*gr_name;
	char	*gr_passwd;
	int	gr_gid;
	char	**gr_mem;
};
