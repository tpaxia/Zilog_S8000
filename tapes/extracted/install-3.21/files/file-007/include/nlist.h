/* @[$]nlist.h	1.1  07/23/82 17:36:08 - Zilog Inc */
struct	nlist {			/* Argument list to nlist(3) */
	char	*nl_name;	/* Pointer to null-terminated name */
	long	nl_value;	/* Value field */
	char	nl_type;	/* Type (see s.out(5)) */
};
