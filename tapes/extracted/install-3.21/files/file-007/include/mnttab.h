/* @[$]mnttab.h	2.2  01/17/83 22:52:27 - Zilog Inc */
/* Format of the /etc/mnttab file which is set by the mount(M)
 * command
 */
#define NAMSIZ 32

struct mnttab {
	char	mt_dev[NAMSIZ],
		mt_filsys[NAMSIZ];
		short	mt_ro_flg;
	time_t	mt_time;
};
