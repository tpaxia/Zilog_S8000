/* @[$]fatal.h	2.1  07/23/82 17:36:02 - Zilog Inc */
#include	<setret.h>
extern	int	Fflags;
extern	char	*Ffile;
extern	int	Fvalue;
extern	int	(*Ffunc)();
extern	ret_buf	Fjmp;

# define FTLMSG		0100000
# define FTLCLN		 040000
# define FTLFUNC	 020000
# define FTLACT		    077
# define FTLJMP		     02
# define FTLEXIT	     01
# define FTLRET		      0

# define FSAVE(val)	SAVE(Fflags,old_Fflags); Fflags = val;
# define FRSTR()	RSTR(Fflags,old_Fflags);
