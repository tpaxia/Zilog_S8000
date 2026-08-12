/******************************************************************************* 
	This is the file used by SYSGEN to build a customer configured
	Zeus Kernel.  The structures and variables defined here were
	extracted from various Zeus Kernel source files as noted.

*******************************************************************************/

# include	"../h/sysparm.h"

# define	BUF_SIZEOF	42	/* sizeof(struct buf) - segmented
					   WARNING:  must match ../h/buf.h */
# define	BASF		0
# define	IMI		1
# define	UTS_LENGTH	9

char zsavwstr[] = "@[$]z.c	Rev : 1.3       05/27/84 15:13:16";

/* interrupt status flags for various devices */
int	zd_flag  	= 0, 
    	smd_flag 	= 0, 
    	md_flag  	= 0, 
    	ct_flag  	= 0,
    	mt_flag  	= 0,
    	user1_flag  	= 0,
    	user2_flag  	= 0,
    	user3_flag  	= 0,
    	user4_flag  	= 0,
    	user5_flag  	= 0,
    	user6_flag  	= 0;

int	last_int_serv 	= 0;	/* type of last interrupt serviced */


int	nicp		= NICP;
int	Canbsiz		= CANBSIZ;
int	Dstflag		= DSTFLAG;
int	Maxmem 		= MAXMEM ;
int	Maxuprc		= MAXUPRC;

int	Nbuf1  		= NBUF1;
int	Nbuf2  		= NBUF2;
int	Nbuf3  		= NBUF3;
int	Nbuf4  		= NBUF4;
int	Nbuf5  		= NBUF5;
int	Nhbuf  		= NHBUF;

int	Nclist 		= NCLIST;
int	Nfile  		= NFILE ;
int	Ninode 		= NINODE;
int	Nmount 		= NMOUNT;
int	Nproc  		= NPROC ;
int	Ntext  		= NTEXT ;
int	Timezone	= TIMEZONE; 
int	Nflock 		= NFLOCK;

struct	inode
	{
	char	coop[82];
	}	inode[NINODE];

struct	mount 
	{		/**  from mount.h  **/
	char	poop[12];
	}	mount[NMOUNT];

char buffer1 [NBUF1][512];
char buffer2 [NBUF2][512];
char buffer3 [NBUF3][512];
char buffer4 [NBUF4][512];
char buffer5 [NBUF5][512];

char canonb  [CANBSIZ];

struct	buf 
	{               /**  from conf.c  **/
	char	loop[BUF_SIZEOF];
	}	buf1[NBUF1],
		buf2[NBUF2],  
		buf3[NBUF3],  
		buf4[NBUF4],  
		buf5[NBUF5];  

struct 	hbuf
	{
	char	soup[10];
	}	hbuf[NHBUF];

struct	file 
	{
	char	boop[12];
	}	file[NFILE];

struct	proc 
	{
	char	doop[44];
	}	proc[NPROC];

struct rq
	{
	short 		rq_pgrp;		
	unsigned int 	rq_cpu;
	struct proc 	*rq_link;
	struct rq 	*rq_nxt;
	struct rq 	*rq_prev;
	}	run_q[NPROC+1];

struct	text 
	{
	char	hoop[14];
	}	text[NTEXT];

struct	cblock 
	{               /*  from prim.c  **/
	char	dummy[30];
	}	cfree[NCLIST];

struct	vd_size 
	{
	long    vd_blkoff;
	long    vd_nblocks;
	char	vd_nam[8];
	};

struct	locklist 
	{
	char	lkdumy[18];
	}	locklist[NFLOCK];

typedef	long		time_t;
typedef	int		dev_t;

# define	makedev(x,y)	(dev_t)((x)<<8 | (y))

struct	map
	{
	short		m_size;
	unsigned short 	m_addr;
	};

char utsysname[UTS_LENGTH] = SYSNAME;
char utsnodename[UTS_LENGTH] = NODENAME;
char utsversion[UTS_LENGTH] = VERSION;
