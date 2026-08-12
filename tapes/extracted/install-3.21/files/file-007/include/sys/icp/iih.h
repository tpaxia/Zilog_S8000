/* @[$]iih.h	1.1  08/15/83 20:52:19 - Zilog Inc */
/*
** iih.h
** Definition of ICP Equates
*/

/*
** table to keep track of buffers allocated
*/
struct iih_buftbl
{
    int			buf_adr;	/* address where memory was alloc'd */
    unsigned int	buf_len;	/* ACTUAL length-not request length */
};


/*
** protocol/port locator table
** one entry for each port
*/
struct iih_porttbl
{
    unsigned int	port_protoid;	/* protocol ID			    */
    long 		port_mctaddr;	/* task cntrl blk addr of port's MCT*/
    long		port_sem;	/* addr of Port Control Semaphore   */
    unsigned int	port_pflags;	/* tells current status of protocol */
};

/*
** definitions of IIH-related flags
*/
#define PSTART	1	/* protocol start	*/
#define PSTOP	2	/* protocol stop	*/
#define PNOMEM	4	/* no memory error	*/
#define PERR	8	/* protocol error	*/


/*
** priority for Main Control Tasks
*/
#define	MCT_PRIORITY	210


/*
** address of port/protocol locator table
*/
#define PORT_TBL_ADDR	0x100L

/*
** iih pseudo port number
*/
#define	IIH_PORT	9
