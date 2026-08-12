/* @[$]sysparm.h	4.8  06/11/84 12:31:25 - Zilog Inc */

/*
 * This is the header file that contains the constants needed by the Zeus kernel
 * which are modifiable by the customer through the SYSGEN procedure. This file
 * is included in : z.c .      
 */

# define CANBSIZ	256	/* max size of input line from terminal	*/
# define DSTFLAG	1	/* Daylight Savings Time flag	     	*/
# define MAXMEM		512	/* maximum memory per process           */
# define MAXUPRC	20	/* maximum number of processes per user */

# define NBUF1		127	/* number of buffers in pool 1 (max 127)*/
# define NBUF2		20	/* number of buffers in pool 2 (max 127)*/
# define NBUF3		1	/* number of buffers in pool 3 (max 127)*/
# define NBUF4		1	/* number of buffers in pool 4 (max 127)*/
# define NBUF5		1	/* number of buffers in pool 5 (max 127)*/
# define NHBUF	  	17	/* number of slots in buffer hash 	*/
				/* should be a prime number		*/

# define NCLIST		100	/* number of small buffers for term io  */
# define NFILE		175	/* size of system open file table       */
# define NINODE		200	/* number of in core i-nodes            */
# define NMOUNT		64	/* number of mountable file systems     */
# define NPROC		70	/* max number of active processes       */
# define NTEXT		40	/* max number of shared text segments   */
# define TIMEZONE 	(8*60)	/* minutes westward from GMT            */
# define NFLOCK		100	/* number of lockable regions in a file */
# define NICP		0	/* number of ICPs			*/

# define SYSNAME	"SYS 8000"	/* System name  (8 char Max.)  */
# define NODENAME	"ZEUS"		/* Node name    (8 char Max.)  */
# define VERSION	"SYS III" 	/* Version name	(8 char Max.)  */
