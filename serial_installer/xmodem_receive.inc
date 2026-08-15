/*
 * Shared, proven ZEUS XMODEM-CRC receive core.
 *
 * Inputs: r4 bytes available, r5 logical destination, rh2 expected block,
 * rh3 consecutive-error count.  GETBYTE, PUTBYTE, SOH/EOT/CAN/ACK and the
 * local labels .Lbad, .Leot and .Lerror are supplied by the including driver.
 * A newly validated 128-byte block falls through; duplicates are consumed and
 * ACKed here before returning to .Lresponse.
 */
.Lresponse:
	GETBYTE
	test	r0
	jr	z,.Lbad
	cpb	rl3,#EOT
	jr	z,.Leot
	cpb	rl3,#CAN
	jr	z,.Lerror
	cpb	rl3,#SOH
	jr	nz,.Lbad

	GETBYTE
	test	r0
	jr	z,.Lbad
	ldb	rh6,rl3		/* block number */
	GETBYTE
	test	r0
	jr	z,.Lbad
	xorb	rl3,rh6		/* block and complement must XOR to ff */
	cpb	rl3,#0xff
	jr	nz,.Lbad

	cpb	rh6,rh2
	jr	z,.Lnew
	ldb	rl0,rh2
	decb	rl0,#1
	cpb	rh6,rl0
	jr	nz,.Lbad

	/* Duplicate of the preceding block: validate, discard, and ACK it. */
	sub	r1,r1		/* CRC-16/XMODEM, initial value zero */
	ld	r6,#128
.Ldiscard:
	GETBYTE
	test	r0
	jr	z,.Lbad
	calr	.Lcrcbyte
	djnz	r6,.Ldiscard
	GETBYTE
	test	r0
	jr	z,.Lbad
	cpb	rl3,rh1
	jr	nz,.Lbad
	GETBYTE
	test	r0
	jr	z,.Lbad
	cpb	rl3,rl1
	jr	nz,.Lbad
	ldb	rl0,#ACK
	PUTBYTE
	clrb	rh3
	jr	.Lresponse

.Lnew:
	cp	r4,#128
	jr	ult,.Lbad
	sub	r1,r1		/* CRC-16/XMODEM, initial value zero */
	ld	r6,#128
.Lcopy:
	GETBYTE
	test	r0
	jr	z,.Lbad
	calr	.Lcrcbyte
	ldb	@r5,rl3
	inc	r5,#1
	djnz	r6,.Lcopy
	GETBYTE
	test	r0
	jr	z,.Lbad
	cpb	rl3,rh1
	jr	nz,.Lbad
	GETBYTE
	test	r0
	jr	z,.Lbad
	cpb	rl3,rl1
	jr	nz,.Lbad
