/* @[$]file.h	4.2  06/11/84 12:30:55 - Zilog Inc */

/*
 * One file structure is allocated for each open/creat/pipe call. Main use is to
 * hold the read/write pointer associated with each open file.
 */

struct	file
{
	char		f_flag;
	cnt_t		f_count;	/* reference count 		*/
	struct inode 	*f_inode;	/* pointer to inode structure 	*/
	union 
	{
		off_t	f_off;		/* read/write character pointer */
	} f_un;
	unsigned 	f_smcnt;	/* semaphore count used by 	*/
					/* sequenced reads & writes	*/
};

# define f_offset	f_un.f_off

extern struct file 	file[];		/* The file table itself 	*/

/* 
 * flags
 */
# define FOPEN		(-1)
# define FREAD		00001
# define FWRITE		00002
# define FNDELAY	00004
# define FAPPEND	00010
# define FMASK		00377

/* 
 * open only modes
 */
# define FCREAT		00400
# define FTRUNC		01000
# define FEXCL		02000
/************************** temporary *************************/
# define FPIPE		00004
