/*
 * XMODEM-framed serial replacement for the ZEUS 3.21 standalone ct.o.
 *
 * The open request selects a logical tape file.  Each standalone strategy
 * call then requests the next byte count and receives one short XMODEM
 * session: 128-byte CRC-16 packets followed by EOT.  Resetting the XMODEM
 * block number for each strategy call lets sarestor stop between tape reads
 * while it writes the disk, without overrunning the polled UART.
 *
 * This is position-independent and is assembled at address zero.  The same
 * image is installed over the 700-byte ct.o body in tape files 1 and 4.
 *
 * Standalone ABI:
 *      r6      READ (1) or WRITE (2)
 *      r7      struct iob *
 *      r2      return value
 */

	.section .text
	.globl _ctopen
	.globl _ctclose
	.globl _ctstrategy
	.globl _ctioctl

	.equ SOH,  0x01
	.equ EOT,  0x04
	.equ ACK,  0x06
	.equ NAK,  0x15
	.equ CAN,  0x18

	.equ TTY0_DATA, 0xff81
	.equ TTY0_CTL,  0xff85

	.equ I_BOFF_LO, 0x55
	.equ I_OFFSET,  0x5e
	.equ I_MA,      0x62
	.equ I_CC,      0x64

	.macro PUTBYTE
	calr	.Lputbyte
	.endm

	.macro GETBYTE
	calr	.Lgetbyte
	.endm

/* Open request: SOH, 'S', '8', protocol version 3, tape file, XOR. */
_ctopen:
	ldb	rl0,#SOH
	PUTBYTE
	ldb	rl0,#'S'
	PUTBYTE
	ldb	rl0,#'8'
	PUTBYTE
	ldb	rl0,#3
	PUTBYTE
	ldb	rl0,I_BOFF_LO(r7)
	PUTBYTE
	xorb	rl0,#(SOH ^ 'S' ^ '8' ^ 3)
	PUTBYTE
	GETBYTE
	test	r0
	jr	z,.Lopen_error
	cpb	rl3,#ACK
	jr	z,.Lopen_ok
.Lopen_error:
	ld	r2,#-1
	ret
.Lopen_ok:
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
 * Request: 'R', 32-bit i_offset, 16-bit count, XOR.
 * Response: CRC-16/XMODEM-128 packets, then EOT. Block numbers restart at
 * one for every strategy call.  A repeated preceding block is ACKed without
 * copying, which is the normal XMODEM recovery for a lost ACK.
 */
	.org 0x76
_ctstrategy:
	cp	r6,#1
	jr	z,.Lstrategy_body
	ld	r2,#-1
	ret

/*
 * devsw's fourth ct entry is the original ctcommand address, ct.o + 0x9c.
 * sarestor calls ioctl(tape_fd, 6, 1) between the common and special dump
 * files.  The packed command arrives as 0x0106: low byte command 6 (space
 * file forward), high byte count 1.
 */
	.org 0x9c
_ctioctl:
	cpb	rl6,#6
	jr	z,.Lspace_file
	ld	r2,#-1
	ret
.Lspace_file:
	ldb	rl0,#'F'
	PUTBYTE
	ldb	rl0,rh6
	PUTBYTE
	xorb	rl0,#'F'
	PUTBYTE
	GETBYTE
	test	r0
	jr	z,.Lioctl_error
	cpb	rl3,#ACK
	jr	z,.Lioctl_ok
.Lioctl_error:
	ld	r2,#-1
	ret
.Lioctl_ok:
	ldk	r2,#0
	ret

	.org 0xd0
.Lstrategy_body:
	ld	r4,I_CC(r7)
	ld	r5,I_MA(r7)

	ldb	rl0,#'R'
	PUTBYTE
	ldb	rl1,#'R'
	ldb	rl0,I_OFFSET+0(r7)
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,I_OFFSET+1(r7)
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,I_OFFSET+2(r7)
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,I_OFFSET+3(r7)
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rh4
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rl4
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rl1
	PUTBYTE

	ldb	rh2,#1		/* expected XMODEM block */
	clrb	rh3		/* consecutive damaged-packet count */

	.include "xmodem_receive.inc"
	ldb	rl0,#ACK
	PUTBYTE
	incb	rh2,#1
	clrb	rh3
	sub	r4,#128
	jr	.Lresponse

.Lbad:
	incb	rh3,#1
	cpb	rh3,#10
	jr	ugt,.Lerror
	/* Discard through one complete inter-byte timeout before asking again. */
.Ldrain:
	GETBYTE
	test	r0
	jr	nz,.Ldrain
	ldb	rl0,#NAK
	PUTBYTE
	jr	.Lresponse

.Leot:
	ldb	rl0,#ACK
	PUTBYTE
	ld	r2,I_CC(r7)
	sub	r2,r4
	ret

.Lerror:
	ld	r2,#-1
	ret

.Lputbyte:
	inb	rl2,#TTY0_CTL
	bitb	rl2,#2
	jr	z,.Lputbyte
	outb	#TTY0_DATA,rl0
	ret

.Lgetbyte:
	ld	r0,#0xffff
.Lget_wait:
	inb	rl2,#TTY0_CTL
	bitb	rl2,#0
	jr	nz,.Lgotbyte
	djnz	r0,.Lget_wait
	ret			/* r0 == 0 reports an inter-byte timeout */
.Lgotbyte:
	inb	rl3,#TTY0_DATA
	ret

/* CRC-16/XMODEM update: r1 = crc(r1, rl3), polynomial 0x1021. */
.Lcrcbyte:
	xorb	rh1,rl3
	ldk	r0,#8
.Lcrcbit:
	add	r1,r1
	jr	nc/uge,.Lcrcnopoly
	xor	r1,#0x1021
.Lcrcnopoly:
	djnz	r0,.Lcrcbit
	ret
