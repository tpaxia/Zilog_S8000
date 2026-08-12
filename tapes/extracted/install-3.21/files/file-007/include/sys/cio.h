/* @[$]cio.h	1.2  06/11/84 12:30:50 - Zilog Inc */
/*
**   	Defines for programming/reading Z8536 CIO's
**		(Counter/Timer and Parallel I/O)
*/
#define	BIT0		0x01
#define	BIT1		0x02
#define	BIT2		0x04
#define	BIT3		0x08
#define	BIT4		0x10
#define	BIT5		0x20
#define	BIT6		0x40
#define	BIT7		0x80

/*
**		Main Control Registers
*/
#define	MASTERINT	0	/* Master Interrupt Control		*/
#define MASTERCONF	1	/* Master Configuration Control		*/
#define A_INTVECT	2	/* Port A Interrupt Vector		*/
#define B_INTVECT	3	/* Port B Interrupt Vector		*/
#define CT_INTVECT	4	/* Counter/Timer Interrupt Vector	*/
#define C_DATAPOL	5	/* Port C Data Path Polarity		*/
#define C_DATADIR	6	/* Port C Data Direction		*/
#define C_SPIOCTL	7	/* Port C Special I/O Control		*/

/*
**		"Most Often Accessed Registers"
*/
#define A_CMDSTAT	8	/* Port A Command and Status		*/
#define B_CMDSTAT	9	/* Port B Command and Status		*/
#define CT1_CMDSTAT	0x0a	/* Counter/Timer 1 Command and Status	*/
#define CT2_CMDSTAT	0x0b	/* Counter/Timer 2 Command and Status	*/
#define CT3_CMDSTAT	0x0c	/* Counter/Timer 3 Command and Status	*/
#define A_DATA		0x0d	/* Port A Data				*/
#define B_DATA		0x0e	/* Port B Data				*/
#define C_DATA		0x0f	/* Port C Data				*/				

/*
**	Counter/Timer Related Registers
*/

#define	CT1_MSCNT	0x10	/* Counter/Timer 1 Current Count MS Byte*/  
#define	CT1_LSCNT	0x11	/* Counter/Timer 1 Current Count LS Byte*/  
#define	CT2_MSCNT	0x12	/* Counter/Timer 2 Current Count MS Byte*/  
#define	CT2_LSCNT	0x13	/* Counter/Timer 2 Current Count LS Byte*/  
#define	CT3_MSCNT	0x14	/* Counter/Timer 3 Current Count MS Byte*/  
#define	CT3_LSCNT	0x15	/* Counter/Timer 3 Current Count LS Byte*/  
#define	CT1_MSTIM	0x16	/* Counter/Timer 1 Time Constant MS Byte*/  
#define	CT1_LSTIM	0x17	/* Counter/Timer 1 Time Constant LS Byte*/  
#define	CT2_MSTIM	0x18	/* Counter/Timer 2 Time Constant MS Byte*/  
#define	CT2_LSTIM	0x19	/* Counter/Timer 2 Time Constant LS Byte*/  
#define	CT3_MSTIM	0x1a	/* Counter/Timer 3 Time Constant MS Byte*/  
#define	CT3_LSTIM	0x1b	/* Counter/Timer 3 Time Constant LS Byte*/  
#define	CT1_MODE	0x1c	/* Counter/Timer 1 Mode Specification 	*/  
#define	CT2_MODE	0x1d	/* Counter/Timer 2 Mode Specification 	*/  
#define	CT3_MODE	0x1e	/* Counter/Timer 3 Mode Specification 	*/  
#define CURRVECT	0x1f	/* Current Vector			*/

/*
**	Port A Specification Registers
*/
#define	A_MODE		0x20	/* Port A Mode Specification		*/
#define	A_SHAKE		0x21	/* Port A Handshake Specification	*/
#define	A_DATAPOL	0x22	/* Port A Data Path Polarity 		*/
#define	A_DATADIR	0x23	/* Port A Data Direction		*/
#define	A_SPIOCTL	0x24	/* Port A Special I/O Control		*/
#define	A_PATPOL	0x25	/* Port A Pattern Polarity 		*/
#define	A_PATTRAN	0x26	/* Port A Pattern Transition 		*/
#define	A_PATMASK	0x27	/* Port A Pattern Mask 			*/

/*
**	Port B Specification Registers
*/
#define	B_MODE		0x28	/* Port B Mode Specification		*/
#define	B_SHAKE		0x29	/* Port B Handshake Specification	*/
#define	B_DATAPOL	0x2a	/* Port B Data Path Polarity 		*/
#define	B_DATADIR	0x2b	/* Port B Data Direction		*/
#define	B_SPIOCTL	0x2c	/* Port B Special I/O Control		*/
#define	B_PATPOL	0x2d	/* Port B Pattern Polarity 		*/
#define	B_PATTRAN	0x2e	/* Port B Pattern Transition 		*/
#define	B_PATMASK	0x2f	/* Port B Pattern Mask 			*/

/*
** 	Defines for the Master Interrupt Control Register
*/
#define	MIE		BIT7	/* Master Interrupt Enable		*/
#define	DLC		BIT6	/* Disable Lower Chain			*/
#define NOVECTOR	BIT5	/* Do not assert vector during IACK	*/
#define PA_VIS		BIT4	/* Port A Vector includes status	*/	
#define PB_VIS		BIT3	/* Port B Vector includes status	*/	
#define CT_VIS		BIT2	/* Counter/Timer Vector includes status	*/	
#define RJA		BIT1	/* Right Justified Address		*/
#define RESET		BIT0	/* Reset the whole device		*/

/*
** 	Defines for the Master Configuration Control Register
*/
#define	PBE		BIT7	/* Port B enable			*/	
#define	CT1E		BIT6	/* Counter/Timer 1 enable		*/	
#define	CT2E		BIT5	/* Counter/Timer 2 enable		*/	
#define	PCECT3E		BIT4	/* Port C and Counter/Timer 3 enable	*/	
#define	PLC		BIT3	/* Port Link Control			*/	
#define	PAE		BIT2	/* Port A enable			*/	
#define	LC1		BIT1	/* Counter/Timer Link Control 1		*/	
#define	LC0		BIT0	/* Counter/Timer Link Control 0		*/	
#define	INDEP_LC	0	/* C/T's 1 & 2 are independent		*/
#define	GATE_LC		LC0	/* C/T 1's inverted output gates C/T 2	*/
#define	TRIG_LC		LC1	/* C/T 1's inverted output triggers 	*/
				/* C/T 2				*/
#define	CASCADE_LC	LC1|LC0	/* C/T 1's inverted output is C/T 2's 	*/
				/* count input 				*/

/*
**	Port Mode Specification Register Bits
*/
#define PTS1		BIT7	/* Port Type Specification Register 1	*/
#define PTS0		BIT6	/* Port Type Specification Register 0	*/

/* OR one of the following four defines into a port's bit pattern	*/
#define BITPORT		0		/* Bit port (no handshake)	*/
#define INP4SHAKE	PTS0		/* Input port (one of 4 	*/
					/* handshakes)			*/
#define OUT4SHAKE	PTS1		/* Ouput port (one of 4 	*/
					/* handshakes)			*/
#define BI2SHAKE	PTS1|PTS0	/* Bi-directional port (one of	*/
					/* 2 handshakes)		*/

#define ITB		BIT5	/* Interrupt on Two Bytes		*/
#define SBUF		BIT4	/* Single Buffer			*/
#define IMO		BIT3	/* Interrupt on Match Only		*/
#define PMS1		BIT2	/* Pattern Mode Specification 1		*/
#define PMS0		BIT1	/* Pattern Mode Specification 0		*/

/* OR one of the following four defines into a port's bit pattern	*/
#define	DIPATMATCH	0		/* Disable Pattern Match	*/
#define	ANDMODE		PMS2		/* AND matching mode		*/
#define	ORMODE		PMS1		/* OR matching mode		*/
#define	ORPRIMODE	PMS1|PMS2	/* OR -Priority Encoded Vector 
					/* Mode (not for bit ports with	*/
					/* LPM set, or handshake ports)	*/
#define LPM		BIT0	/* Latch on Pattern Match (dual fcn bit)*/
#define DTE		BIT0	/* Deskew Timer Enable (dual fcn bit)	*/

/*
** 	Port Handshake Specification Registers 
*/
#define	HTS1	BIT7		/* Handshake type specification bit 1	*/
#define	HTS0	BIT6		/* Handshake type specification bit 0	*/
/* OR one of the following four defines into a port's bit pattern	*/
#define	INTERLCK_HS	0		/* Interlocked Handshake		*/
#define	STROBE_HS	HTS0		/* Strobed Handshake			*/
#define	PULSE_HS	HTS1		/* Pulsed handshake			*/
#define	THREE_HS	HTS1|HTS0	/* 3-wire handshake		*/
#define	RWS2		BIT5	/* Request/wait specification bit #2	*/
#define	RWS1		BIT4	/* Request/wait specification bit #1	*/
#define	RWS0		BIT3	/* Request/wait specification bit #0	*/
/* OR one of the following six defines into a port's bit pattern	*/
#define	DISABLE_RW	0		/* Request/wait disabled		*/
#define	OUTW_RW		RWS0		/* Output wait 				*/
#define	INPW_RW		RWS1|RWS0 	/* Input wait 			*/
#define	SPECR_RW	RWS2		/* Special request 			*/
#define	OUTR_RW		RWS2|RWS0 	/* Output request			*/
#define	INPR_RW		RWS2|RWS1||RWS0 /* Output request		*/
#define	DTS3		BIT2	/* Deskew time specification bit #3	*/
#define	DTS2		BIT1	/* Deskew time specification bit #2	*/
#define	DTS1		BIT0	/* Deskew time specification bit #1	*/
/* OR one of the following eight defines into a port's bit pattern	*/
#define	DESKEW2		0		/* Deskew time of 2 pclk cycles	*/
#define	DESKEW4		DTS1		/* Deskew time of 4 pclk cycles	*/
#define	DESKEW6		DTS2 		/* Deskew time of 8 pclk cycles	*/
#define	DESKEW8		DTS2|DTS1 	/* Deskew time of 8 pclk cycles	*/
#define	DESKEW10	DTS3 		/* Deskew time of 10 pclk cycles*/
#define	DESKEW12	DTS3|DTS1 	/* Deskew time of 12 pclk cycles*/
#define	DESKEW14	DTS3|DTS2 	/* Deskew time of 14 pclk cycles*/
#define	DESKEW16	DTS3|DTS2|DTS1 	/* Deskew time of 16 pclk cycles*/
 
/*
**	Port Command and Status Registers
**	    readable bits:
*/
#define	IUS		BIT7	 /* Interrupt under service		*/
#define	IENABLE		BIT6	 /* Interrupt enable			*/
#define	IPENDING	BIT5	 /* Interrupt pending			*/
#define	IERR		BIT4	 /* Interrupt error			*/
#define	ORE		BIT3	 /* Output register empty		*/
#define	IRF		BIT2	 /* Input register full			*/
#define	PATMATCH	BIT1	 /* Pattern match			*/
#define	IONERR		BIT0	 /* Interrupt on error			*/
/*
** 	   writable bits:
*/
#define	CLRIPIUS	IPENDING	/* Clear IP and IUS		*/
#define	SETIUS		IENABLE		/* Set IUS			*/
#define	CLRIUS		IENABLE|IPENDING	/* Clear IUS		*/
#define	SETIP		IUS		/* Set IP			*/
#define	CLRIP		IUS|IPENDING	/* Clear IP			*/
#define	SETIE		IUS|IENABLE		/* Set IENABLE		*/
#define	CLRIE		IUS|IENABLE|IPENDING	/* Clear IENABLE	*/

/*
**		Counter/Timer Mode Specification Registers
*/
#define	CONTINUOUS	BIT7	/* Continuous/Single cycle bit		*/
#define	EOE	BIT6	/* External Output Enable			*/
#define	ECE	BIT5	/* External Count Enable			*/
#define	ETE	BIT4	/* External Trigger Enable			*/
#define	EGE	BIT3	/* External Gate Enable				*/
#define	RETRIGGER BIT2 	/* Retrigger Enable Bit				*/
#define	DCS1	BIT1 	/* Duty Cycle Select bit 1			*/
#define	DCS0	BIT0 	/* Duty Cycle Select bit 0			*/
#define	PULSE_DC	0 	/* Pulse Output				*/
#define	ONESHOT_DC	DCS0 	/* One-Shot Output			*/
#define	SQUARE_DC	DCS1 	/* Square-Wave Output			*/

/*
**	Counter/Timer Command and Status Registers
**	 (upper four bits are the same as for port 
**	  command and status registers)
*/
#define	READCOUNT  BIT3		/* Read Counter Control 		*/	
#define	GATE_BIT   BIT2		/* Gate Command Bit	 		*/	
#define	TRIG_BIT   BIT1		/* Trigger Command Bit	 		*/	
#define	CIP	   BIT0		/* Count in Progress	 		*/	

/*
**	Register I/O Addresses of the HPCPU's on-board CIO
*/
#define	CIO_CNTRL	0xFFA1	/* Control Register			*/
#define	CIOA_DATA	0xFFA3	/* Channel A Data			*/
#define	CIOB_DATA	0xFFA5	/* Channel B Data			*/
#define	CIOC_DATA	0xFFA7	/* Channel C Data			*/

/*
** 	Misc. definitions
*/
#define	cio_cmd(register,byte)	outb(CIO_CNTRL,register);outb(CIO_CNTRL,byte)
#define	cio_stat(register,byte) outb(CIO_CNTRL,register);byte=inb(CIO_CNTRL)
#define	STEP	0	/* Offset to CIO base vector in cio_intv[]	*/
#define	CLOCK	1	/* offset into cio_intv[] for clock vector (CT2)*/
#define	NOTUSED	2	/*   "     "      "        "  CT1 vector	*/
#define	ERRVECT	3	/* offset into cio_intv[] for CT error vector 	*/
