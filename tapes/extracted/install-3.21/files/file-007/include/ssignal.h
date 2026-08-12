/* @[$]ssignal.h	1.3  05/23/84 17:22:37 - Zilog Inc */
#include <sys/signal.h>

long	(*signal())();
#define	SIG_DFL	(long (*)())0
#define	SIG_IGN	(long (*)())1
