/* @[$]icpcomm.h	1.1  08/15/83 20:52:07 - Zilog Inc */
/*
** This is the common include file used by the ZID and IIH.
*/
typedef	unsigned char BYTE;

#define	ICMD_PSIZ	10		/* number of words in parameter area*/

#define	ICP_CMAX	3		/* maximum number of ICPs (0 thru 7)*/
#define	ICP_PMAX	9		/* max number of ports per ICP (0-8)*/
#define	ICP_LMAX	27		/* max number of logical ports      */

#define	ICP_FCW		0xC000		/* icp fcw for coming out of reset  */
#define IIHBIT		0x8000		/* bit to test if this is a command */
					/* for the IIH			    */

#define	ICPREGS		0x20		/* start of save area for register  */
					/* in the icp when a trap occurs    */
#define	ICP_REGSIZ	48		/* size of the register save area   */

#define	Z_ERROR		0	/* non-specific error */

/*
** Value returned to a ZPD's interrupt routine if the ICP
** is either stopped or dead
*/
#define	Z_DIED		-1

/*
** flag values used in icpset()
*/
#define	Z_SETA		1	/* set interrupt addr */
#define	Z_SETP		2	/* set protocol       */
#define	Z_UNSETA	3	/* unset intr address */
#define	Z_UNSETP	4	/* unset protocol     */

/*
** Values for protocol names.
** If you add more protocols you need to define them here.
** For a specific protocol you just choose one of value below to
** represent it.
*/
#define	NULLPROTO	0x00	/* port is assoc. w/no proto		      */
#define	PROTOA		0x01	/* intelligent terminal protocol	      */
#define	PROTOB		0x02	/* intelligent line printer protocol          */
#define	PROTOC		0x03	/* not used				      */
#define	PROTOD		0x04	/* not used				      */
#define	PROTOE		0x05	/* not used				      */
#define	PROTOF		0x06	/* not used				      */
#define	PROTOG		0x07	/* not used				      */
#define	PROTOH		0x08	/* not used				      */
#define	PROTOI		0x09	/* not used				      */
#define	PROTOJ		0x0A	/* not used				      */
#define	PROTOK		0x0B	/* not used				      */
#define	PROTOL		0x0C	/* not used				      */
#define	PROTOM		0x0D	/* not used				      */
#define	PROTON		0x0E	/* not used				      */
#define	PROTOO		0x0F	/* not used				      */
#define	PROTOKERNEL	0xFF	/* protocol for the kernel		      */ 
/*
** ioctl commands
** as in "ioctl (fd, command, arg)"
*/
#define	STARTI		0x01	/* start icp                */
#define	STOPI		0x02	/* stop icp                 */
#define	STARTPP		0x03	/* start proto on port      */
#define	STOPPP		0x04	/* stop proto on port       */
#define	QUERY		0x05	/* info about icp state and */
				/* for all ports            */
#define	DEBUG		0x06	/* print out debug junk     */

/*
** Significant interrupt vector information
*/
#define	PORT0		0xA2	/* ICP 0 -- port 0	*/
#define	PORT72		0xEE	/* ICP 7 -- port 9	*/
#define	IIHINT		0xA0	/* Vector for the IIH	*/

/*
** reasons that the IIH interrupt
*/
#define	P_ASSOC		0x01	/* proto association w/port worked	*/
#define	P_NOASSOC	0x02	/* proto association w/port didnt work	*/
#define	INIT_COMP	0x03	/* ICP initialization is complete	*/
#define	NO_INIT		0x04	/* ICP did not complete init		*/
#define	NMI_RCV		0x05	/* ICP received an NMI			*/
#define	PARERR		0x06	/* ICP got a parity error		*/
#define	EX_INST		0x07	/* ICP got a extended instruction trap	*/
#define	PR_INST		0x08	/* ICP got a priv. instruction trap	*/
#define	ILG_SYS		0x09	/* ICP got an illegal system call	*/
#define	UNINIT_VEC	0x0A	/* ICP got an uninitialized vect. entry */
#define	CMD_INV		0x0B	/* ICP got an illegal command		*/
#define	P_FATAL		0x0C	/* ICP says a protocol got a fatal error*/

/*
** Various defines for the configurability of a port, i.e,
** what the hardware jumpers can be set to.
*/
#define	ICP_A	1		/* Async		*/
#define	ICP_S	2		/* Sync			*/
#define	ICP_O	3		/* Olympic???		*/
#define	ICP_Z	4		/* Znet			*/
#define	ICP_P	5		/* Parallel		*/

/*
** Various defines for sizes of various structures
*/
/* size of the global reference table	*/
#define	GTABSIZ		(sizeof (struct glob_ref))

/* offset into the icp memory to find the global reference table */
#define	GTABADR		0x0L

/* max number of entries in the memory map table	*/
#define	MMTABENTS	15

/* offset into the icp memory to find the memory map table */
#define	MMTABADR	0x50L

/*
 * Command block starting address for an icp.
 * If you change this, then the icp_blk_addr in icp must change also
*/
#define	ICP_CBADR	0x180L

/*
 * Defines the address where the system data structures stop
*/
#define	ENDDSTRUCTS	0x300L

/*
 * definition of the global reference structure
*/
struct	glob_ref		/* global reference table		*/
{
	unsigned int	g_clk,		/* echo of system clock for debugging */
			g_FCW,		/* fcw for coming out of reset        */
			g_SEG,		/* segment number for out of reset    */
			g_PC,		/* pc for coming out of reset         */
			g_flags;	/* flags for IIH use		      */
	char		g_icpid,	/* icp number of this icp	      */
			g_ivbase,	/* base of interrupt vector IPD to ZID*/
			g_iverr,	/* interrupt vector for IIH to ZID    */
			g_portcreate,	/* port id under creation	      */
			g_pproto[ ICP_PMAX ];	/* port configuration	      */
	long	g_sem;			/* addr of command semaphore in	      */
					/* conjunction with g_protcreate      */
};

/*
** Definition of the memory map table.
*/
struct 	mmtab			/* memory map table		*/
{
	char	mm_protoid,	/* protocol id number		*/
		mm_segflag;	/* segmented flag		*/
	long	mm_entrypt,	/* entry point of the protocol	*/
		mm_imsize;	/* total image size incl. bss	*/
};

/*
** command block that is used to communicate to
** the ICP.
*/
struct	icmd_blk			/* ICP parameter area block     */
{
	BYTE		icmd_busy;	/* command block is busy flag   */
	BYTE		icmd_cmd;	/* actual command               */
	long		icmd_addr;	/* physical memory address      */
	unsigned	icmd_len;	/* length of data               */
	int		icmd_parea[ICMD_PSIZ]; /* ioctl parameter area      */
};
