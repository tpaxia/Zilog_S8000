char lprwstr[] = "@[$]lpr.c		Rev : 4.12 	10/12/84 14:12:50" ;

/*
 *  Line printer driver - Centronics and Data Products interface
 *  PIO port 1
 *
 *  Interfaces with the Z-80 Parallel I/O (PIO) Circuit
 */


/*
**	This module has been modified to work with both CPU-A
** and the HPCPU boards. The differences in the hardware (from a
** programming point of view) are listed below.
**
**	1) HPCPU has no system break register for the MMUs.
**
**	2) HPCPU has no on-board printer port.
**
**	3) HPCPU uses an 8530 SCC for the console port and tty0
**	(instead of an SIO). Tty2-ttyn are mapped off-board.
**
**	4) HPCPU uses an 8536 CIO for the counter/timer functions
**	instead of Z-80 CTCs.
**
**	5) The System Configuration Register on the HPCPU is a full
**	16 bits wide. The SCR on CPU-A is only 8 bits wide, but
**	may be read or written as a word register (ignoring the
**	high byte). All bit definitions in the low byte of the HPCPU
**	SCR correspond directly to the definitions for the CPU-A bits.
**	There are additional bits in the high byte of the HPCPU SCR
**	such as another boot device bit and a cache memory enable/disable
**	bit.
**
**	6) The 'serial number' that is passed in R7 from the CPU PROMs
**	has always been zero for CPU-A, but will have the low bit (bit #0)
**	set for the HPCPU and the next bit (bit #1) set if cache memory
**	is present and passes the power-up diagnostics.
**
**	7) Single-step on the HPCPU is done with a hardware register and
**	NMI instead of a CTC as on CPU-A.
**
*/


# include	"../h/signal.h"
# include	"../h/param.h"
# include	"../h/dir.h"
# include	"../h/mmu.h"
# include	"../h/state.h"
# include	"../h/tty.h"
# include	"../h/s.out.h"
# include	"../h/user.h"
# include	"../h/conf.h"
# include	"../h/ioctl.h"
# include	"../h/sysinfo.h"
# include	"../h/systm.h"

# define LPPRI		(PZERO+8)
# define LPLOWAT	0x20
# define LPHIWAT	0x40
# define LINGER		25	/* hang around port polling for no more than
				 * this many empty loops for printer ready.
				 * (we want 100 microsecs max, actually).
				 */
#ifdef LOOPCOUNT
long oloop[LINGER+1];		/* a little instrumentation */
long lloop[LINGER+1];
#endif
# define IMPATIENT 	500	/* if inputs haven't settled yet, forget it */

# define MAXPORTS 	3	/* maximum number of PIOs for printers. if this
				 * gets changed, be sure to change the array of 				 * printer data 	   
				 */

# define NLPT		3	/* number of line printer types     */

# define CENTRON	0	/* encoding of minor device number: */
# define DATAPROD	1	/* 	   x x x x r t a a	    */ 
# define RAWCENT	2	/* where x is don't care, r is raw/notraw */
# define RAWDATAP	3	/* t is interface type and a is port # */

# define UNCONFIG 	0xFFFF	/* port not configured with terminal type */

# define LP1INTVEC 	0xE6	/* interrupt vector address */
# define LP2INTVEC 	0xE8	/* interrupt vector address */
# define LP3INTVEC 	0xEE	/* interrupt vector address */

# define PIO1CHA	0xFFB9
# define PIO1CHB	0xFFBB
# define PIO1CHAsel	0xFFBD
# define PIO1CHBsel	0xFFBF

# define PIO2CHA	0xFF79
# define PIO2CHB	0xFF7B
# define PIO2CHAsel	0xFF7D
# define PIO2CHBsel	0xFF7F

# define PIO3CHA	0xFF39
# define PIO3CHB	0xFF3B
# define PIO3CHAsel	0xFF3D
# define PIO3CHBsel	0xFF3F


/* 
 * Interrupts should be generated when LPBUSY goes high (i.e. the printer says
 * give me another character).  If interrupts are disabled and enabled
 * again, and LPBUSY went high while they were disabled, the interrupt
 * will be lost.  Thus interrupts are generated when both LPBUSY (bit 4)
 * and bit 3 go high.  Bit 3 is made to go low and then high after interrupts
 * are enabled and this will 'catch' the case where LPBUSY has already
 * gone high before enabling.  If LPBUSY hasn't gone high yet, when it 
 * does an interrupt will be generated since bit 3 is high.
 */
# define INACTIVE  	0xFF
# define LOWER		0x7
# define RAISE		0xF
# define FALSE   	0x0

/*
**	Macro for bumping the lpr numbers for HPCPU since there is
** no printer port on the HPCPU itself.
*/

#define	LPRADR(a,b)	b = ((hpcpu) ? (a + 1) : a)

/*
**	Macro for determining maximum number of lpr's allowed.
*/

#define	MAXPORT(a)	a = ((hpcpu) ? (MAXPORTS - 1) : MAXPORTS)


struct lp_dtype
{
	char		flag, 	/* reset in "lp_close".  		*/
			ind;    /* size of the line indentation 	*/

	int		ccc, 	/* current char cnt (actual char cnt)	*/
			mcc, 	/* max char cnt  (logical char count) If 
				 * non-zero, then current line is not empty */
			mlc, 	/* mmax line cnt (if non-zero, then # lines 
				 * completed since form feed  		*/
			line, 	/* Max # lines per page			*/
			col;    /* max # chars per line 		*/

	struct clist	l_outq;	/* l_outq->c_cc is the count of the # of chars
				 * waiting to be sent to the line printer */
};

extern	int		last_int_serv;
extern unsigned char	hpcpu;		/* HPCPU flag			*/

static struct Port_struct 
{
	unsigned	Lpr_type,
			Control,	/* PIO control channel 		*/
			Output,		/* PIO output channel		*/
			ControlSel,
			OutputSel, 	/* set channel mode */
			cyc_started; 	/* used by interrupt routine to 
					 * determine if cycle was started
					 */
        struct lp_dtype	lpr_data;
} 			Port[MAXPORTS] =

/* CHB: Data output.  Disable interrupts. CHA: Control. 
 * Set direction.  Set interrupt vector addr.  Enable interrupts.
 */

	{
		UNCONFIG,
		PIO1CHA, PIO1CHB,
		PIO1CHAsel, PIO1CHBsel,
		FALSE,
		{ 0, 1, 0, 0, 0, 66, 130, 0 },
		UNCONFIG,
		PIO2CHA, PIO2CHB,
		PIO2CHAsel, PIO2CHBsel,	
		FALSE,
		{ 0, 1, 0, 0, 0, 66, 130, 0 },
		UNCONFIG,
		PIO3CHA, PIO3CHB,
		PIO3CHAsel, PIO3CHBsel,	
		FALSE,
		{ 0, 1, 0, 0, 0, 66, 130, 0 }
	};

# define OPEN		0x08
# define NOCR		0x20
# define ASLP		0x40

# define FORM		0x0C
# define BACKSPACE  	0x08

# define ENABLE		0xE7	/* enable interrupts - use old mask */
# define DISABLE	0x67	/* disable interrupts */
# define ONLINE		0x20	/* printer is on-line */
# define INTVER		0x40	/* interface verification */
# define LPBUSY		0x10	/* Centronics printer is ready for a character*/
# define DDEMAND	0x80	/* same as above only for Data Products */
# define CONTROL	0x0CF	/* set up port for control mode */
# define NOINTR		0x07	/* mask interrupts on port */
# define DOUTPUT	0x0F	/* set up port for data output mode */
# define INTR		0xF7	/* port A will generate interrupts (mode 3) */
# define MASKC		0xE7	/* Centronics: interrupt on bit 3 & LPBUSY */
					/* (ON-LINE is redundant) */
# define MASKD		0x77	/* Data Products: interrupt on bit 3 & DDEMAND*/
# define DIRECTION	0xF0	/* direction mask for control mode port */


/* 
 * proc name:  lpr_init
 * description: PIO initialization
 * input params: Number,Type
 *		 PIO number and printer type.
 * returns:
*/

lpr_init(Number, Type)
unsigned 	Number, 	/* Port number */
		Type;		/* printer type */
{
	unsigned	SetDataChan,
			SetControl,
			Control,
			i,
			hpNumber;	/* Modified lpr # for HPCPU	*/

	LPRADR(Number, hpNumber);

	Port[Number].Lpr_type = Type;
	SetControl = Port[hpNumber].ControlSel;
	Control = Port[hpNumber].Control;
	SetDataChan = Port[hpNumber].OutputSel;
	outb(SetDataChan, DOUTPUT);
	outb(SetDataChan, NOINTR);
	outb(Control,INACTIVE);		/* insure control outputs inactive */
	outb(SetControl, CONTROL);
	outb(SetControl, DIRECTION);

	for (i = 0; i < IMPATIENT; i++)
		;			/* wait for inputs to settle */

	switch (Number)
	{
		case 0: 
			outb(SetControl, LP1INTVEC);
			break;

		case 1: 
			outb(SetControl, LP2INTVEC);
			break;

		case 2: 
			outb(SetControl, LP3INTVEC);
			break;
	}

	outb(SetControl, INTR);

	if ((Type == CENTRON)||(Type == RAWCENT))
		outb(SetControl, MASKC);
	else
		outb(SetControl, MASKD);
}

/*$
 * proc name:  lp_open
 * input params:  device #
 * returns:
 * 	description: open a line printer file
$*/

lp_open(dev)
dev_t	dev;
{
	register int	minordev;
	register char 	status,
			maxports;	/* Modified max # of ports	*/
	register int 	loop,
			port_no,
			hpport_no;	/* Modified port # for HPCPU	*/
	unsigned 	ContChan;	/* control channel */
	struct lp_dtype	*lp_d_ptr;
	int 		Type = UNCONFIG;

	minordev = minor(dev);
	port_no = (minordev & 3);
	LPRADR(port_no, hpport_no);
	MAXPORT(maxports);

        if (port_no >= maxports) 
	{ 	/* Attempt to reference fanciful port number */
	       	u.u_error = EIO;
	       	return;
	}

	Type =  Port[port_no].Lpr_type;

	if (Type == UNCONFIG)		/* then we will configure it */
	{
		Type = minordev >> 2;

		if (Type >= NLPT)
		{	/* unimplimented type */
		       	u.u_error = ENXIO;
		       	return;
		};

		lpr_init(port_no,Type);
	}

     	/* 
	 * Take the error exit if another line printer file is already open
	 */
	lp_d_ptr = &Port[port_no].lpr_data;

	if (lp_d_ptr->flag) 
	{
		u.u_error = EIO;
		return;
	}

	ContChan = Port[hpport_no].Control;


     	/* 
	 * Take the error exit if the line printer is not ready (e.g. the power
	 * is off or there is no paper or the printer drum gate is open or the 
	 * temperature is too high or the operator has switched the printer off-
	 * line)
	 */
	if ((Type == CENTRON)||(Type == RAWCENT)) 
	{
		for (loop=0; loop<LINGER; loop++) 
		{
			status = inb(ContChan);

			if (status & LPBUSY)
				break;
		}

#ifdef LOOPCOUNT
		oloop[loop]++;
#endif

		if (((status&ONLINE)==0) || ((status&INTVER)==0) || 
			((status&LPBUSY)==0)) 
		{
			u.u_error = EIO;
			return;
		}
	}
	else 
	{ 				/* Data Products */
		status = inb(ContChan);

		if (((status&ONLINE)==0) || (((~status)&INTVER)==0) 
			|| ((status&DDEMAND)==0)) 
		{
			u.u_error = EIO;
			return;
		}
	}


     	/* 
	 * Indicate that the file is open
	 */
	lp_d_ptr->flag = (dev&077)|OPEN;
       
     	/* 
	 * Send a formfeed (new page) to the line printer if not in raw mode.
	 */
	if ((Type!=RAWCENT)&&(Type!=RAWDATAP))
		lp_output(port_no,FORM);
}


/*$
 * proc name: lp_close
 * input params: dev #
 * returns:
 * description: close a file opened by 'lp_open'.  Output a form feed (new
 * 		page) if not in raw mode.
$*/

lp_close(dev)
dev_t	dev;
{
	register unsigned 	Type, 
				port_no;

	port_no = (minor(dev) & 3);
	Type = Port[port_no].Lpr_type;

	if ((Type!=RAWCENT)&&(Type!=RAWDATAP))
		lp_output(port_no,FORM);

	Port[port_no].lpr_data.flag = 0;
}


/*$
 * proc name: lp_write
 * input params: dev #
 * returns:
 * description: "lp_write" takes the non-null chars of a null terminated
 *		string recorded in the user area and passes them to 
 *		"lp_output", one at a time.  Finally, it calls "printc"
 *		to print the final line (or whole thing, as the case may be)
$*/

lp_write(dev)
dev_t	dev;
{
	int	 		c;
	register int		slept;
	register int 		s;
	register int 		firstime;
	register unsigned	port_no,
				hpport_no;	/* Modified lpr # for HPCPU */
	unsigned 		Type, 
				SetControl,
				Control;
	struct lp_dtype 	*lp_d_ptr;

	port_no = (minor(dev) & 3);
	LPRADR(port_no, hpport_no);

	lp_d_ptr = &Port[port_no].lpr_data;
	SetControl = Port[hpport_no].ControlSel;
	Control = Port[hpport_no].Control;
	Type = Port[port_no].Lpr_type;

	while ( (c = cpass()) != -1 ) 
	{
		outb(SetControl, DISABLE);

	    	/*  
		 * if the number of chars waiting to be sent to the line 
		 * printer is already large enough, sleep so as not to flood
		 * the character buffer pool
		 */

		while(lp_d_ptr->l_outq.c_cc > LPHIWAT) 
		{
			printc(port_no);
			lp_d_ptr->flag |= ASLP;

			s = dvi();
			outb(SetControl, ENABLE);
			outb(Control, LOWER);
			outb(Control, RAISE);
			sleep(lp_d_ptr, LPPRI);
			outb(SetControl, DISABLE);
			rvi(s);
		}

		outb(SetControl, ENABLE);

		/* check for parity bit set when not in raw mode	*/
		if ((c & 0x80)&&(Type==CENTRON||Type==DATAPROD)) {
			u.u_error = EFAULT;
			break;
		}

		lp_output(port_no,c);
	}

	outb(SetControl, DISABLE);
	printc(port_no);
	outb(SetControl, ENABLE);
	outb(Control, LOWER);
	outb(Control, RAISE);
}


/*$
 * proc name: lp_output
 * input params: char to be (massaged and) printed, and port #. 
 *
 * returns:
 * description: put a char in getc's buffer (associated with the device),
 *		interpreting the character, possibly making modifications
 *		to it.  Insertions and deletions may occur.  If char =
 *		carriage return, call "printc" to print the line.
$*/

lp_output(port_no,c)
register int	port_no,
		c;
{

	struct lp_dtype   	*lp_d_ptr;
	unsigned 		SetControl, 
				Control, 
				Type,
				hpport_no;  /* Modified lpr # for HPCPU	*/

	LPRADR(port_no, hpport_no);

	lp_d_ptr = &Port[port_no].lpr_data;
	SetControl = Port[hpport_no].ControlSel;
	Control = Port[hpport_no].Control;
	Type = Port[port_no].Lpr_type;

	if ((Type == RAWCENT)||(Type == RAWDATAP))
	{
		putc(c, &lp_d_ptr->l_outq);
		lp_d_ptr->mcc++;
		lp_d_ptr->ccc++;
		return;
	}

	switch(c) 
	{
	case '\t':
    		/*  
		 * round the current char count up to the next multiple of four.
		 * Do not output any blank chars immediately
		 */
		lp_d_ptr->ccc = ((lp_d_ptr->ccc+8-lp_d_ptr->ind) & ~7) + 
			lp_d_ptr->ind;
		return;

	case '\n':
    		/* 
		 * Increment the completed line count. On the Data Products 
		 * printer, '\n' causes a carriage and line feed to be emitted.
		 * A '\r' causes just a carriage return to take place.  On the 
		 * Centronics, a '\r' and '\n' must be printed in order to 
		 * emit a carriage return and line feed; a '\r' causes just a 
		 * carriage return to take place.  Note that most Centronics 
		 * line printers have an automatic line feed option where just 
		 * printing a '\r' causes both a carriage return and line feed 
		 * to take place - this should be disabled so that underlining 
		 * can take place.  Finally some line printers have an 
		 * automatic skip option where some lines are skipped before 
		 * the perforation on the page.  This should also be disabled.
     		 */
		lp_d_ptr->mlc++;

		if ((lp_d_ptr->line) && (lp_d_ptr->mlc >= lp_d_ptr->line))
		{
			c = FORM;
		}
		else if (Port[port_no].Lpr_type == CENTRON)
		{
			putc('\r', &lp_d_ptr->l_outq);
		}

	case FORM:
    		/* "mcc = 0" means the current line is empty.  If some lines 
		 * have been completed since the last form feed (lp_d_ptr->mlc) 
		 * then output the char and if it was a form feed, reset the 
		 * number of completed lines to zero. Thus any string of form 
		 * feed's (ff's) or new lines's which begins with a ff will, if
		 * sent to a printer, be reduced to a single ff.
		 */
		lp_d_ptr->mcc = 0;
		if (lp_d_ptr->mlc) 
		{
			if (c == FORM) 
			{
				if (Port[port_no].Lpr_type == CENTRON)
					putc('\r', &lp_d_ptr->l_outq);

				lp_d_ptr->mlc = 0;
			}

			putc(c, &lp_d_ptr->l_outq);
		}

	case '\r':
    		/*  
		 * Carriage returns. Note the above may fall through to here.
		 */
		lp_d_ptr->ccc = lp_d_ptr->ind;

		if (c == '\r') 
		{
			putc(c, &lp_d_ptr->l_outq);
			lp_d_ptr->mcc = 0;
		}

	    	/*  
		 * inhibit interrupts from the line printer
		 */
		outb(SetControl, DISABLE);
		printc(port_no);
		outb(SetControl, ENABLE);
		outb(Control, LOWER);
		outb(Control, RAISE);
		return;

	case BACKSPACE:
    		/*  
		 * backspace
		 */
		if (lp_d_ptr->ccc > lp_d_ptr->ind)
			lp_d_ptr->ccc--;

		return;

	case ' ':
		lp_d_ptr->ccc++;
		return;

	default:
    		/* 
		 * If a string of "backspace"s (real or contrived) and/or 
		 * "carriage returns" have been received, output a single 
		 * "carriage return" and reset the max char count to zero 
		 * (unless flag is on). Provided the current char cnt doesn't 
		 * exceed the maximum allowable line length, output blank chars
		 * to bring the max char cnt to the current char cnt.  Output 
		 * the actual character.
		 */
    
		if(lp_d_ptr->ccc < lp_d_ptr->mcc) 
		{
			if (lp_d_ptr->flag&NOCR) 
			{
				lp_d_ptr->ccc++;
				return;
			}

			putc('\r', &lp_d_ptr->l_outq);
			lp_d_ptr->mcc = 0;
		}

		if(lp_d_ptr->ccc < lp_d_ptr->col) 
		{
			while(lp_d_ptr->ccc > lp_d_ptr->mcc) 
			{
				putc(' ', &lp_d_ptr->l_outq);
				lp_d_ptr->mcc++;
			}

			putc(c, &lp_d_ptr->l_outq);
			lp_d_ptr->mcc++;
		}

		lp_d_ptr->ccc++;
	}
}




/*$
 * proc name:  printc
 * input params:  port #
 *
 * returns:
 * description:  print chars, taking them from internal buffer.
 *		 Interrupts from the device are always disabled during
 *		 printc's execution.
$*/

printc(port_no)
register unsigned port_no;
{
	register int 	status,
			c;
	register int 	loop;
	unsigned 	Control,
			Output,
			Type,
			hpport_no;	/* Modified lpr # for HPCPU	*/
	struct lp_dtype	*lp_d_ptr;

	LPRADR(port_no, hpport_no);

	lp_d_ptr = &Port[port_no].lpr_data;
	Control = Port[hpport_no].Control;
	Output = Port[hpport_no].Output;
	Type = Port[port_no].Lpr_type;

	if ((Type == CENTRON)||(Type == RAWCENT))
		while (1) 
		{
/* NEC printer wants us to test for BUSY at least 3.5 us after trailing edge */
/* of data strobe--with hpcpu and ed script spl.ed run against lpr.s file    */
/* we test after only 3.0 us, so the diversion below has been added	     */
			if(hpcpu)		/* keep NEC printer happy */
				lpdelay();	/* wait another microsec  */
			for (loop=0; loop<LINGER; loop++)
				if ((status = inb(Control)) & LPBUSY)
					break;

#ifdef LOOPCOUNT
			lloop[loop]++;
#endif

			if ((status & LPBUSY) == 0)
				return;

			if ((c = getc(&lp_d_ptr->l_outq)) >= 0) 
			{
				if (c == '\n' || c == '\r' || c == FORM)
					Port[port_no].cyc_started = 1;

				outb(Output, c);
				outb(Control,0x0E);	/* assert data strobe */
				outb(Control,0x0F);	/* remove data strobe */
			}
			else 
				return;
		}
	else		/* Data Products */
		while ((((status = inb(Control)) & DDEMAND) != 0) &&
		      ((c = getc(&lp_d_ptr->l_outq)) >= 0)) 
		{
			if (c == '\n' || c == '\r' || c == FORM)
				Port[port_no].cyc_started = 1;

			outb(Output, c);
		}
}



/*$
 * proc name:  lpr_int
 * input params:  interrupted routine's saved info pointer (if not
 *		  called, i.e. entered because of an interrupt)
 * returns:
 * description:  handles interrupts from the device, due to:
 *
 *	a)  completion of a print cycle
 *	b)  the printer going ready after a period during which it was
 *	    it was off-line or not ready;
 *
 *	"lpr_int" transfers chars into the printer buffer
 *	(which the controller buffers) and when done, wakes up any sleeping
 *	process wanting to send more.
$*/

lpr_int(s)
register struct state *s;
{
	register unsigned	port_no,
				hpport_no;  /* Modified lpr # for HPCPU	*/
	unsigned 		SetControl,
				Control;
	struct lp_dtype		*lp_d_ptr;

	last_int_serv = LPRINT;		/* record that this was the last*/


	switch (s->s_eventid&0xff)
	{
	    case LP1INTVEC:  
		port_no =  0;
		break;

	    case LP2INTVEC:  
		port_no =  1;
		break;

	    case LP3INTVEC:  
		port_no =  2;
		break;
	}

	LPRADR(port_no, hpport_no);	/* Adjust port # for HPCPU	*/

	SetControl = Port[hpport_no].ControlSel;
	outb(SetControl, DISABLE);
	reti0(); 	/* fake z80 reti for on-board z80 devices */
	reti1(); 	/* fake z80 reti for off-board z80 devices */
			/* NOTE: this is to emulate the old reti();
			 * Sam W. says that this often didn't reset the
			 * PIO anyway.				  
			 */
	evi();				/* DISABLE keeps them out	*/

	lp_d_ptr = &Port[port_no].lpr_data;
	Control = Port[hpport_no].Control;

	/* 
	 * Only generate another interrupt if a print cycle was started, i.e. 
	 * a line terminator was moved to the printer buffer.
	 */
	Port[port_no].cyc_started = 0;
	 
    	/* 
	 * Start transferring characters into the printer buffer again, i.e.
         * while the line printer is ready and while there are still chars
	 * stored away, keep sending chars to the printer controller.
	 */
	printc(port_no);

    	/* 
	 * Wake up the process waiting to feed chars to the printer if the
	 * number of chars waiting to be sent is within range
	 */
	if (lp_d_ptr->l_outq.c_cc <= LPLOWAT && lp_d_ptr->flag&ASLP) 
	{
		lp_d_ptr->flag &= ~ASLP;
		wakeup(lp_d_ptr);
	}

	dvi();		/* keep the interrupt stack shallow	  */

	outb(SetControl, ENABLE);

	if (Port[port_no].cyc_started) 
	{
		outb(Control, LOWER);
		outb(Control, RAISE);
	}
}

/*$
 * proc name: lp_sgtty
 * input params:  command, pointer to argument structure
 * returns: 1 for successful completion;  0 for error return  
 * globals changed: lp_dt structure pointed to by *lp_d_ptr
 * description: called by tty ioctl system call through bdevsw table 
 * 		if command is SETLPR this function sets the lp_dt table
 *		according to user supplied lparms structure (defined in
 *		tty.h). Setable params are number of columns on a page,
 *		number of lines in a page, and default indentation.
 *		The command SHOWLPR puts the current parameters into
 *		the user's lparms structure.
 *
 $*/

lp_sgtty(dev, cmd, argptr, flag)
int		dev;		/*	not used by this proc	*/
int		cmd;
uaddr_t		argptr;		/* pointer to struct lparms 	*/
int		flag;		/*	not used by this proc	*/
{
	struct	lparms		mystruct;
	struct  lp_dtype 	*lp_d_ptr;
	unsigned  		port_no;

	port_no = (minor(dev) & 3);

	lp_d_ptr = &Port[port_no].lpr_data;

	if (cmd == SHOWLPR)	/* 	show current values	*/
	{
		/* 
		 * put current values into a temporary lparms structure	
		 */
		mystruct.lines  = lp_d_ptr->line;
		mystruct.cols   = lp_d_ptr->col;
		mystruct.indent = lp_d_ptr->ind;

		/*
		 * copy current temporary lparms structure into user space
		 */
		if (copyout(&mystruct, argptr, sizeof(mystruct)) < 0)
		{
			u.u_error = EFAULT;
			return(0);
		} 
		else
			return(1);
	} 
	else		/*	command is SETLPR	*/
	{
		/*
		 * copy lparms structure from user space into temporary 
 		 * structure
		 */
		if (copyin(argptr, &mystruct, sizeof(mystruct)) < 0)
		{
			u.u_error = EFAULT;
			return(0);
		}

		if (mystruct.cols < 1 || mystruct.lines < 0)
		{
			u.u_error = EINVAL;
			return(0);
		}

		if (mystruct.cols < mystruct.indent)
		{
			u.u_error = EINVAL;
			return(0);
		}

		/* 
		 * update lp_dt structure	
		 */
		lp_d_ptr->ind   =  mystruct.indent;
		lp_d_ptr->line  =  mystruct.lines;
		lp_d_ptr->col   =  mystruct.cols;
		return(1);
	}
}

lpdelay()	/* allow the NEC printer to decide if it is busy or not */
{
	int i;
	i++;	/* keep overzealous optimizers off our ass */
}
