/*
 * Serial equivalent of the monitor's tape-boot routine at ROM 0x32cc.
 *
 * The monitor loads this at 0xf000.  Like the original tape path, it selects
 * system mode and off-board RAM, loads tape file 0 directly at address zero,
 * and jumps to zero.  There is no intermediate image or relocated file 1.
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
	.equ SCR,       0xffc1

	.macro PUTBYTE
.Lput\@:
	inb	rh1,#TTY0_CTL
	bitb	rh1,#2
	jr	z,.Lput\@
	outb	#TTY0_DATA,rl0
	.endm

	.macro GETBYTE
.Lget\@:
	inb	rh1,#TTY0_CTL
	bitb	rh1,#0
	jr	z,.Lget\@
	inb	rl3,#TTY0_DATA
	.endm

_start:
	/* Preserve the jumper/configuration word across our serial receive. */
	ld	r10,r7
	/* This is the same FCW and RAM-overlay transition used by tape boot. */
	ld	r0,#0x4000
	ldctl	fcw,r0
	ldb	rl0,#1
	outb	#SCR,rl0
	ld	r15,#0xf000

	/* Open installation-tape file 0. */
	ldb	rl0,#SOH
	PUTBYTE
	ldb	rl0,#'S'
	PUTBYTE
	ldb	rl0,#'8'
	PUTBYTE
	ldb	rl0,#1
	PUTBYTE
	clrb	rl0
	PUTBYTE
	ldb	rl0,#(SOH ^ 'S' ^ '8' ^ 1)
	PUTBYTE
	GETBYTE
	cpb	rl3,#ACK
	jp	nz,.Lhalt

	ldk	r5,#0
	ld	r4,#512
	calr	.Lread_packet
	cp	r2,r4
	jp	nz,.Lhalt
	calr	.Lread_packet
	test	r2
	jp	nz,.Lhalt
	/* Reproduce the measured ROM ZT handoff; J enters with different values. */
	ldk	r4,#1
	ld	r5,#0x10
	ld	r7,r10
	ldk	r2,#0
	jp	@r2

/* Read one protocol block of at most r4 bytes into @r5; return count in r2. */
.Lread_packet:
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
	jr	z,.Leof
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
	jr	nz,.Lhalt
	GETBYTE
	cpb	rl3,#ETX
	jr	nz,.Lhalt
	ldb	rl0,#ACK
	PUTBYTE
	ret
.Leof:
	ldk	r2,#0
	ret
.Lhalt:
	ldb	rl0,#CAN
	PUTBYTE
	di	vi,nvi
	jr	.Lhalt
