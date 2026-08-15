/*
 * Serial replacement for SADIE 3.5 track 0, file 0.
 *
 * The monitor bootstrap loads this at zero.  Like the original SADIE primary,
 * it relocates out of the way to 0xe800, loads track 0/file 1 at address zero,
 * and jumps to the executive.  The host substitutes the patched executive.
 */

	.section .text
	.globl _start
	.equ SOH,  0x01
	.equ STX,  0x02
	.equ ETX,  0x03
	.equ EOT,  0x04
	.equ ACK,  0x06
	.equ CAN,  0x18
	.equ TTY0_DATA, 0xff81
	.equ TTY0_CTL,  0xff85

_start:
	ld	r0,#0x4000
	ldctl	fcw,r0
	ld	r2,#0xe800
	lda	r1,.Lrelocated
	ld	r0,#(.Lend - .Lrelocated)
	ldirb	@r2,@r1,r0
	jp	0xe800

	.macro PUTBYTE
	calr	.Lputbyte
	.endm
	.macro GETBYTE
	calr	.Lgetbyte
	.endm

.Lrelocated:
	ld	r15,#0xfffe
	ld	r8,r7		/* Preserve the monitor configuration for SADIE. */

	/* Legacy stream-open for track 0/file 1. */
	ldb	rl0,#SOH
	PUTBYTE
	ldb	rl0,#'S'
	PUTBYTE
	ldb	rl0,#'8'
	PUTBYTE
	ldb	rl0,#1
	PUTBYTE
	ldb	rl0,#1
	PUTBYTE
	ldb	rl0,#(SOH ^ 'S' ^ '8')
	PUTBYTE
	GETBYTE
	cpb	rl3,#ACK
	jr	nz,.Lhalt

	ldk	r5,#0
.Lrequest:
	ld	r4,#512
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
	GETBYTE
	cpb	rl3,#EOT
	jr	z,.Lloaded
	cpb	rl3,#STX
	jr	nz,.Lhalt
	GETBYTE
	ldb	rh6,rl3
	ldb	rl1,rl3
	GETBYTE
	ldb	rl6,rl3
	xorb	rl1,rl3
	cp	r6,r4
	jr	ugt,.Lhalt
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
	jr	nz,.Lhalt
	GETBYTE
	cpb	rl3,#ETX
	jr	nz,.Lhalt
	ldb	rl0,#ACK
	PUTBYTE
	jr	.Lrequest

.Lloaded:
	/*
	 * The real tape primary never uses SIO0-A.  Our polled transport does, but
	 * the ROM left that channel's receive interrupts enabled.  Remove the
	 * transport's interrupt state before SADIE enables vectored interrupts;
	 * otherwise channel A can mask the lower-priority channel-B console.
	 * Channel B and all of its monitor configuration remain untouched.
	 */
	ldb	rl0,#1		/* select channel-A WR1 */
	outb	#TTY0_CTL,rl0
	clrb	rl0		/* disable channel-A interrupts */
	outb	#TTY0_CTL,rl0
	ldb	rl0,#0x30		/* reset receive error state */
	outb	#TTY0_CTL,rl0
	ldb	rl0,#0x38		/* clear any in-service interrupt */
	outb	#TTY0_CTL,rl0
	ld	r7,r8
	ldk	r2,#0
	jp	@r2
.Lhalt:
	ldb	rl0,#CAN
	PUTBYTE
	di	vi,nvi
	jr	.Lhalt
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
.Lend:
