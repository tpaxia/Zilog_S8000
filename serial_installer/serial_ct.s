/*
 * Serial replacement for the ZEUS 3.21 standalone sarestor ct.o driver.
 *
 * This is position-independent and is assembled at address zero.  The patcher
 * installs it over 0x2de6..0x30a2 in install-tape file 4.  It uses monitor
 * channel A (TTY0), leaving the standalone console on the other serial port.
 *
 * Standalone ABI:
 *      r6      READ (1) or WRITE (2)
 *      r7      struct iob *
 *      r2      return value
 *
 * Channel A is polled directly because the secondary loader replaces the
 * monitor PSAP.  Monitor SC services therefore do not survive its handoff.
 */

	.section .text
	.globl _ctopen
	.globl _ctclose
	.globl _ctstrategy

	.equ SOH,  0x01
	.equ STX,  0x02
	.equ ETX,  0x03
	.equ EOT,  0x04
	.equ ACK,  0x06
	.equ NAK,  0x15
	.equ CAN,  0x18

	.equ TTY0_DATA, 0xff81
	.equ TTY0_CTL,  0xff85

	.equ I_BOFF_LO, 0x55
	.equ I_MA,      0x62
	.equ I_CC,      0x64

	.macro PUTBYTE
	calr	.Lputbyte
	.endm

	.macro GETBYTE
	calr	.Lgetbyte
	.endm

/* Open request: SOH, 'S', '8', protocol version, tape file, XOR checksum. */
_ctopen:
	ldb	rl0,#SOH
	PUTBYTE
	ldb	rl0,#'S'
	PUTBYTE
	ldb	rl0,#'8'
	PUTBYTE
	ldb	rl0,#1
	PUTBYTE
	ldb	rl0,I_BOFF_LO(r7)
	PUTBYTE
	xorb	rl0,#(SOH ^ 'S' ^ '8' ^ 1)
	PUTBYTE
	GETBYTE
	cpb	rl3,#ACK
	jr	nz,.Lerror
	ldk	r2,#0
	ret

	/* devsw contains the original absolute ctclose address, ct.o + 0x62. */
	.org 0x62
_ctclose:
	ldb	rl0,#CAN
	PUTBYTE
	ldk	r2,#0
	ret

/*
 * A read request is 'R', count high, count low, XOR checksum.  The host
 * replies with EOT, CAN, or STX/count/payload/XOR/ETX.  Bad response packets
 * are NAKed and the host retransmits the same packet; good packets are ACKed.
 */
	/* devsw contains the original absolute ctstrategy address, ct.o + 0x76. */
	.org 0x76
_ctstrategy:
	cp	r6,#1
	jr	nz,.Lerror
	ld	r4,I_CC(r7)
	ld	r5,I_MA(r7)

	ldb	rl0,#'R'
	PUTBYTE
	ldb	rl0,rh4
	PUTBYTE
	xorb	rl0,#'R'
	ldb	rl1,rl0
	ldb	rl0,rl4
	PUTBYTE
	xorb	rl0,rl1
	PUTBYTE

.Lresponse:
	GETBYTE
	cpb	rl3,#EOT
	jr	z,.Leof
	cpb	rl3,#CAN
	jr	z,.Lerror
	cpb	rl3,#STX
	jr	nz,.Lbad

	GETBYTE
	ldb	rh6,rl3
	ldb	rl1,rl3
	GETBYTE
	ldb	rl6,rl3
	xorb	rl1,rl3
	cp	r6,r4
	jr	ugt,.Lbad
	ld	r2,r6
	test	r6
	jr	z,.Ltrailer

.Lcopy:
	GETBYTE
	xorb	rl1,rl3
	ldb	@r5,rl3
	inc	r5,#1
	djnz	r6,.Lcopy

.Ltrailer:
	GETBYTE
	cpb	rl3,rl1
	jr	nz,.Lbad
	GETBYTE
	cpb	rl3,#ETX
	jr	nz,.Lbad
	ldb	rl0,#ACK
	PUTBYTE
	ret

.Lbad:
	ldb	rl0,#NAK
	PUTBYTE
	jr	.Lresponse

.Leof:
	ldk	r2,#0
	ret

.Lerror:
	ld	r2,#-1
	ret

.Lputbyte:
	inb	rh1,#TTY0_CTL
	bitb	rh1,#2
	jr	z,.Lputbyte
	outb	#TTY0_DATA,rl0
	ret

.Lgetbyte:
	inb	rh1,#TTY0_CTL
	bitb	rh1,#0
	jr	z,.Lgetbyte
	inb	rl3,#TTY0_DATA
	ret
