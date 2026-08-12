/* @[$]conf.h	4.2  06/11/84 12:30:53 - Zilog Inc */

/*
 * Declaration of block device switch. Each entry (row) is the only link between
 * the main unix code and the driver. The initialization of the device switches
 * is in the file conf1.c.
 */
extern struct bdevsw
{
	int		(*d_open)();
	int		(*d_close)();
	int		(*d_strategy)();
} bdevsw[];


/*
 * Character device switch.
 */
extern struct cdevsw
{
	int		(*d_open)();
	int		(*d_close)();
	int		(*d_read)();
	int		(*d_write)();
	int		(*d_ioctl)();
	int		(*d_stop)();
	struct tty 	*d_ttys;
} cdevsw[];


/*
 * tty line control switch.
 */
extern struct linesw
{
	int		(*l_open)();
	int		(*l_close)();
	int		(*l_read)();
	int		(*l_write)();
	int		(*l_ioctl)();
	int		(*l_input)();
	int		(*l_output)();
	int		(*l_start)();
	int		(*l_mdmint)();
} linesw[];

extern int	linecnt;	/* number of entries in lineswitch table */


/*
 * Disk layout info -- used only by drivers: Virtual disk specification:
 */
struct	vd_size 
{
	long    vd_blkoff;
	long    vd_nblocks;
	char	vd_nam[8];
};
