/* @[$]dir.h	4.1  06/11/84 12:30:54 - Zilog Inc */

# ifndef DIRSIZ
# define DIRSIZ		14
# endif DIRSIZ

struct	direct
{
	ino_t	d_ino;
	char	d_name[DIRSIZ];
};
