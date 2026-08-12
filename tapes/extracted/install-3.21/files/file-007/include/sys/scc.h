/* @[$]scc.h	1.2  06/11/84 12:31:17 - Zilog Inc */
/*
**	SCC Programming Constants
*/

#define	SCCNULL	0		/* Null command code			*/

	/*
	**	These codes address the appropriate register (read or
	** write) in the SIO or 8530 SCC serial port chips. Note that
	** the default is RR0 or WR0 if a command is not preceeded
	** by one of these register select values.
	*/

#define	SPR0	0x0
#define	SPR1	0x1
#define	SPR2	0x2
#define	SPR3	0x3
#define	SPR4	0x4
#define	SPR5	0x5
#define	SPR6	0x6
#define	SPR7	0x7
#define	SPR8	0x8
#define	SPR9	0x9
#define	SPR10	0xA
#define	SPR11	0xB
#define	SPR12	0xC
#define	SPR13	0xD
#define	SPR14	0xE
#define	SPR15	0xF


	/*
	**	Write Register Bit Definitions
	**
	**	WR0
	*/

#define	RSTEXT	0x10		/* Reset external/status interrupts	*/
#define	SNDABT	0x18		/* Send abort				*/
#define	NRXINT	0x20		/* Enable interrupt on next RX char	*/
#define	RSTTXI	0x28		/* Reset TX interrupt pending		*/
#define	ERRRST	0x30		/* Error reset				*/
#define	RSTIUS	0x38		/* Reset highest IUS			*/

#define	RSTRXC	0x40		/* Reset RX CRC checker			*/
#define	RSTTXC	0x80		/* Reset TX CRC checker			*/
#define	RSTUEOM	0xC0		/* Reset TX underrun/EOM latch		*/

	/*
	**	WR1
	*/

#define	DISINT	0x00		/* Disable all interrupts		*/
#define	EXTIE	0x01		/* External interrupt enable		*/

#define	TXIE	0x02		/* TX interrupt enable			*/

#define	PARSPL	0x04		/* Parity is a special condition	*/

#define	RXIE1S	0x08		/* Enable RX interrupts on first char	*/
				/*   or special condition		*/
#define	RXIEAS	0x10		/* Enable RX interrupts on all chars or	*/
				/*   special condition			*/
#define	RXIESP	0x18		/* Enable RX interrupts on special	*/
				/*   condition only			*/

#define	WDREQTR	0x20		/* WAIT/DMA request on R/~T		*/
#define	WDREQF	0x40		/* WAIT/DMA request function		*/
#define	WDREQE	0x80		/* WAIT/DMA request enable		*/

	/*
	**	WR3
	*/

#define	RXEN	0x01		/* RX enable				*/

#define	SYNLIN	0x02		/* Sync character load inhibit		*/

#define	ADRSM	0x04		/* Address search mode (SDLC)		*/

#define	RXCRCEN	0x08		/* RX CRC check enable			*/

#define	EHMOD	0x10		/* Enter hunt mode			*/

#define	AUTOEN	0x20		/* Auto enables				*/

#define	RX5BITS	0x00		/* Five bit RX characters		*/
#define	RX7BITS	0x40		/* Seven  "        "			*/
#define	RX6BITS	0x80		/* Six    "        "			*/
#define	RX8BITS	0xC0		/* Eight  "        "			*/

	/*
	**	WR4
	*/

#define	PAREN	0x01		/* Parity enable			*/
#define	PEVEN	0x02		/* Parity even				*/
#define	SYNMEN	0x00		/* SYNC mode enable			*/
#define	ONESB	0x04		/* One stop bit/character		*/
#define	ONEHSB	0x08		/* One and a half stop bits/character	*/
#define	TWOSB	0x0C		/* Two stop bits/character		*/

#define	SY8BIT	0x00		/* Eight bit sync character		*/
#define	SY16BIT	0x10		/* Sixteen bit sync character		*/
#define	SDLCMOD	0x20		/* SDLC mode				*/
#define	EXTSYNM	0x30		/* External sync mode			*/

#define	X1CLK	0x00		/* X1 clock mode			*/
#define	X16CLK	0x40		/* X16 clock mode			*/
#define	X32CLK	0x80		/* X32 clock mode			*/
#define	X64CLK	0xC0		/* X64 clock mode			*/

	/*
	**	WR5
	*/

#define	TXCRCEN	0x01		/* TX CRC check enable			*/

#define	RTSON	0x02		/* RTS active				*/

#define	SDLCCK	0x00		/* SDLC error checking mode		*/

#define	CRC16CK	0x04		/* CRC16 error checking			*/

#define	TXEN	0x08		/* TX enable				*/

#define	SNDBK	0x10		/* Send break 				*/

#define	TX5BITS	0x00		/* Five bit TX characters		*/
#define	TX7BITS	0x20		/* Seven  "        "			*/
#define	TX6BITS	0x40		/* Six    "        "			*/
#define	TX8BITS	0x60		/* Eight  "        "			*/

#define	DTRON	0x80		/* DTR active				*/

	/*
	**	WR9
	*/

#define	SCCVIS	0x01		/*					*/
#define	SCCNV	0x02		/*					*/
#define	SCCDLC	0x04		/* Disable lower chain			*/
#define	SCCMIE	0x08		/* Master interrupt enable		*/

#define	STATLO	0x00		/*					*/
#define	STATHI	0x10		/*					*/

#define	RSTCHB	0x40		/* Reset channel B only			*/
#define	RSTCHA	0x80		/* Reset channel A only			*/
#define	RSTSCC	0xC0		/* Hard reset of whole chip		*/

	/*
	**	WR10
	*/

#define	SYNC8	0x00		/* Eight bit sync			*/
#define	SYNC6	0x01		/* Six bit sync				*/
#define	LOOPMOD	0x02		/* Loop mode				*/
#define	UNDFLG	0x00		/* Flag on underrun			*/
#define	UNDABT	0x04		/* Abort on underrun			*/
#define	IDLFLG	0x00		/* Flag on idle				*/
#define	IDLMK	0x08		/* Mark on idle				*/
#define	POLACT	0x10		/* Go active on poll			*/

#define	SCCNRZ	0x00		/* NRZ mode				*/
#define	SCCNRZI	0x20		/* NRZI mode				*/
#define	SCCFM1	0x40		/* Transition = 1			*/
#define	SCCFM0	0x60		/* Transition = 0			*/

#define	CRCPREO	0x00		/* CRC preset out			*/
#define	CRCPREI	0x80		/* CRC preset in			*/

	/*
	**	WR11
	*/

#define	TRxCX	0x00		/* TRxC out = xtal output		*/
#define	TRxCTXC	0x01		/* TRxC out = transmit clock		*/
#define	TRxCBR	0x02		/* TRxC out = BR generator output	*/
#define	TRxCPLL	0x03		/* TRxC out = DPLL output		*/
#define	TRxCIN	0x00		/* TRxC is input			*/
#define	TRxCOUT	0x04		/* TRxC is output			*/

#define	TXCRTxC	0x00		/* Transmit clock = ~RTxC pin		*/
#define	TXCTRxC	0x08		/*    "       "   = ~TRxC pin		*/
#define	TXCBR	0x10		/*    "       "   = BR gen. output	*/
#define	TXCPLL	0x18		/*    "       "   = DPLL output		*/

#define	RXCRTxC	0x00		/* Receive clock = ~RTxC pin		*/
#define	RXCTRxC	0x20		/*    "      "   = ~TRxC pin		*/
#define	RXCBR	0x40		/*    "      "   = BR gen. output	*/
#define	RXCPLL	0x60		/*    "      "   = DPLL output		*/

#define	NOXTAL	0x00		/* No crystal				*/
#define	RTxCX	0x80		/* Crystal input			*/

	/*
	**	WR14
	*/

#define	BRGEN	0x01		/* Baud rate generator enable		*/
#define	BRGSRC	0x02		/* Baud rate generator source		*/
#define	REQFUNC	0x04		/* ~DTR/request function		*/
#define	AECHO	0x08		/* Auto echo				*/
#define	LLOOPB	0x10		/* Local loop back			*/

#define	SRCHMOD	0x20		/* Enter search mode			*/
#define	RSTMCLK	0x40		/* Reset missing clock			*/
#define	DISPLL	0x60		/* Disable DPLL				*/
#define	SRCBRG	0x80		/* Source = BR gen.			*/
#define	SRCRTxC	0xA0		/* Source = RTxC			*/
#define	FMMODE	0xC0		/* Set FM mode				*/
#define	NRZIMOD	0xE0		/* Set NRZI mode			*/

	/*
	**	WR15
	*/

#define	CNT0IE	0x02		/* Zero count interrupt enable		*/
#define	DCDIE	0x08		/* DCD interrupt enable			*/
#define	SYHNTIE	0x10		/* Sync/hunt interrupt enable		*/
#define	CTSIE	0x20		/* CTS interrupt enable			*/
#define	TXUEIE	0x40		/* TX underrun/EOM interrupt enable	*/
#define	BKABTIE	0x80		/* Break/abort interrupt enable		*/


	/*
	**	Read Register Bit Definitions
	**
	**	RR0
	*/

#define	RCA	0x01		/* Receive character available		*/
#define	TXRDY	0x04		/* Transmitter empty (ready for char)	*/
