/* @[$]core.h	1.1  07/23/82 17:35:56 - Zilog Inc */
/* machine dependent stuff for core files */
#define TXTRNDSIZ 256L
#define stacktop(siz) (0x10000L)
#define stackbas(siz) (0x10000L-siz)
