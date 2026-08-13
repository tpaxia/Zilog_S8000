/*
 * Serial replacement for installation-tape file 0.
 *
 * Its first operation and handoff are the original file-0 flow: relocate the
 * working body from low memory to 0xf800, run there, load file 1 directly at
 * address zero, then jump to zero.  Only the cartridge-controller reads have
 * been replaced by the TTY0 protocol.
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

_start:
	ld	r0,#0x4000
	ldctl	fcw,r0
	ld	r2,#0xf800
	lda	r1,.Lrelocated
	ld	r0,#(.Lend - .Lrelocated)
	ldirb	@r2,@r1,r0
	jp	0xf800

	.macro PUTBYTE
	calr	.Lputbyte
	.endm
	.macro GETBYTE
	calr	.Lgetbyte
	.endm

.Lrelocated:
	ld	r15,#0xf800
	ldb	rl0,#1
	outb	#SCR,rl0
	/* Original file 0 preserves these monitor configuration registers. */
	ld	r8,r4
	ld	r9,r5
	ld	r10,r7

	/* Open installation-tape file 1 (the secondary loader). */
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
	ld	r4,r8
	ld	r5,r9
	ld	r7,r10
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
