/* @[$]misc.h	1.1  07/23/82 17:36:06 - Zilog Inc */
/*
 * structure to access an
 * integer in bytes
 */
struct
{
	char	hibyte;
	char	lobyte;
};

/*
 * structure to access an integer
 */
struct
{
	int	integ;
};

/*
 * structure to access a long as integers
 */
struct {
	int	hiword;
	int	loword;
};

/*
 *	structure to access an unsigned
 */
struct {
	unsigned	unsignd;
};
