/* @[$]state.h	4.3  06/11/84 12:31:21 - Zilog Inc */

/*
 *  state.h:
 *    constants, etc. dealing with machine status
 */

# define NUMREG	15

struct state 
{
	unsigned	s_reg[NUMREG];
	unsigned	s_sp;
	unsigned	s_eventid;
	unsigned	s_ps;
	unsigned	s_pcseg;
	unsigned	s_pc;
};

# define SEGFCW		0x8000		/* segmented bit in fcw 	   */
# define FCWBITS	0xF8FC		/* used flag and control word bits */
# define TBIT		0x0001		/* trace bit in PS		   */
# define TRPBIT		0x0002		/* trap bit: indicates trap 	   */
# define EBIT		0x0080		/* user error bit in PS: c-bit 	   */
# define EPUBIT		0x0100		/* running epu instruction	   */
# define SYSBIT		0x4000		/* running in system mode	   */
# define NVIBIT		0x0800		/* handling non vectored interrupt */

# define TRPMODE(ps)	((ps)  & TRPBIT)
# define EPUMODE(ps)	((ps)  & EPUBIT)
# define SYSMODE(ps)	((ps)  & SYSBIT)
# define USRMODE(ps)	(((ps) & SYSBIT) == 0)
# define HIPRI(ps)	(((ps) & NVIBIT) == 0)

# define RETRLO		4		/* system call return value (low)  */
# define RETRHI		5		/* system call return value (high) */
# define SCINS		0x7F00		/* system call instruction 	   */


/*
 *  states of floating point emulator:
 *  	FPSTEP - being single stepped
 *  	FPRUN - in floating point emulator (preemption enabled)
 */

# define FPRUN		0x0001
# define FPSTEP		0x0002

/*
 *  interrupt vector for floating point board.
 */
#define	FPPINTV		0xfc		/* see event.s			*/

/*
 *  Syscon register bits for the floating point board set:
 */

#define FP_IVMASK	0xFFL		/* mask for interrupt vector 	*/
#define	FP_SHFTV	0x200L		/* Shift interrupt vector left 1 */
#define	FP_VIS		0x400L		/* Interrupt vector includes status */
#define	FP_NOVECT	0x800L		/* No interrupt vector. 		 */
#define	FP_DIELC	0x1000L		/* Disable ints-lower daisy chain*/
#define	FP_MIE		0x8000L		/* Enable interrupts			*/
#define	FP_IR0		0x10000000L	/* Interrupt reason bit 0 	*/
#define	FP_IR1		0x20000000L	/* Interrupt reason bit 1 	*/
#define	FP_IRBITS	FP_IR0&FP_IR1	/* Interrupt reason bits	*/
#define	IRARITH		0L		/* Arithmetic interrupt		*/
#define	IRINVOP		FP_IR0		/* Invalid opcode		*/
#define	IRINVID 	FP_IR1		/* Invalid EPU i.d.		*/
#define	IRPRIV  	FP_IR0|FP_IR1	/* Privileged mode violation.	*/
