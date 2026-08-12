/* @[$]signal.h	2.2  05/23/84 17:20:51 - Zilog Inc */
#include <sys/signal.h>

int	(*signal())();
#define	SIG_DFL	(int (*)())0
#if lint
#define	SIG_IGN (int (*)())0
#else
#define	SIG_IGN	(int (*)())1
#endif
