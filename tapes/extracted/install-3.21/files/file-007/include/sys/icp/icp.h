/* @[$]icp.h	1.1  08/15/83 20:51:49 - Zilog Inc */
/*
** icp.h -- header file for the zeus/icp driver
*/


/*
** Miscellaneous Defines
*/

#define	IIH_PPORT	9		/* faked IIH physical port          */
#define	IIH_LPORT	10		/* faked IIH logical port           */

#define	TRUE		1		/* you'll have to guess what these  */
#define FALSE		0		/* are, can you do it??		    */

#define PHYSEG		0xFF0000	/* mask for checking physical       */
					/* segment number 		    */
#define TICKS		120		/* number of ticks to timeout ICP   */
#define NEXTPHYSEG	0x10000		/* add this to icp_phys_addr to get */
					/* addr of next segment in same ICP */
/*
** Return values from icpcmd(), icpset(), icpioctl() and icpdq()
*/
#define	Z_BUSY		2	/* ICP is busy        */


/*
** Commands to the ICP status
** register
*/
#define	ICPNMI	0x01    /* Generate NMI in the  ICP          */
#define	EPROM	0x02    /* enable ICP PROM                   */
#define	ICPEI	0x04    /* enable interrupts from ICP        */
#define	PARNMI	0x08    /* ICP parity error gives ZEUS NMI   */
#define	PARSEG	0x10    /* ICP par. err. gives ICP seg. trap */
#define	MEMOFF	0x20    /* turn off dual port mem.           */
#define	ICPGO	0x40    /* remove stop from ICP              */
#define	NORESET	0x80    /* no reset -- 0 = reset ICP         */
#define	ICP_BSY	0x01	/* the ICP's intr register is busy   */

/*
** Macro for calculating the address of any ICP
** command block.
** y is physical port on a given ICP.
** x is the ICP controller number
*/
#define blk_addr(x,y) (icp_blk_addr[x] + (sizeof(struct icmd_blk)) * y)

/*
** ICP states.
** These are the values that are put into the variable
** ic_state
*/
#define	ICP_RUNNING	0x01	/* The ICP is running (~running)	*/
#define	ICP_ISOPEN	0x02	/* The ICP is open (~open)		*/
#define	ICP_ERROR	0x04	/* the ICP has a hardware error		*/
#define	ICP_SOFTERR	0x08	/* ICP couldnt do function asked	*/
#define	ICP_ACK		0x10	/* ICP is acknowledging requests	*/

/*
** zid state and address table
*/
struct	icp
{
	BYTE ic_state;		/* state of ICP, e.g. run, stop   */
	struct
	{
		BYTE ic_proto;		/* protocol associated w/port     */
		int  (*ic_func)(); 	/* protocols interrupt addresses  */
	} ic_ports[ICP_PMAX];		/* one for each physical port     */
};

static struct icp	icps[ICP_CMAX];        /* one struct per physical ICP   */

/*
** structure of data returned from
** an ioctl call for query ICP
*/
struct	icpquery
{
	BYTE icpq_istate;		/* state of the ICP          */
	struct
	{
		BYTE icpq_pstate;	/* protocol state	     */
		BYTE icpq_pp;		/* protocol on port          */
	} iport[ICP_PMAX];		/* one iport struct per port */
};

/*
** ICP command block start addresses.
*/
static long icp_blk_addr[ICP_CMAX] = {
         0x700180,		/* icp 0 */
         0x720180,		/* icp 1 */
         0x740180,		/* icp 2 */
#ifdef ALL8
         0x760180,		/* icp 3 */
         0x780180,		/* icp 4 */
         0x7A0180,		/* icp 5 */
         0x7C0180,		/* icp 6 */
         0x7E0180		/* icp 7 */
#endif
};

/*
** register address array
*/
static int icp_reg_addr[ICP_CMAX] = {
	0xEF01,			/* icp 0 */
	0xEF03,			/* icp 1 */
	0xEF05,			/* icp 2 */
#ifdef ALL8
	0xEF07,			/* icp 3 */
	0xEF09,			/* icp 4 */
	0xEF0B,			/* icp 5 */
	0xEF0D,			/* icp 6 */
	0xEF0F			/* icp 7 */
#endif
};


/*
** ICP physical memory address array.  These values represent the
** beginning of memory for a particular icp.
*/
static long icp_phys_addr[ICP_CMAX] = {
         0x700000,		/* icp 0 */
         0x720000,		/* icp 1 */
         0x740000,		/* icp 2 */
#ifdef ALL8
         0x760000,		/* icp 3 */
         0x780000,		/* icp 4 */
         0x7A0000,		/* icp 5 */
         0x7C0000,		/* icp 6 */
         0x7E0000		/* icp 7 */
#endif
};
