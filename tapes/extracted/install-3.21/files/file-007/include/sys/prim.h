/* @[$]prim.h	4.1  06/11/84 12:31:09 - Zilog Inc */

# define NOSLEEP	0400
# define FORCE		01000
# define NORM		02000
# define KEEP		04000
# define CLR		010000

int	bwaiting, wcount;

char 	*getepack();
