/*
 * Read-only serial replacement for the tape routines embedded in the
 * SADIE 3.5 track-0/file-1 executive.
 *
 * This is deliberately separate from serial_installer/serial_ct.s.  SADIE
 * does not use the ZEUS standalone ct.o ABI: it passes a physical destination
 * segment/offset to its read routine and has a separate track/file/record
 * positioning entry.  The patcher installs this image over 0x2874..0x2d35
 * while preserving every entry called by the unmodified executive.
 *
 * Public SADIE ABI recovered from the original executable:
 *
 *   read, address 0x2874
 *       r3  maximum number of physical records
 *       r4  pointer to returned byte count
 *       r5  maximum total byte count
 *       r6  physical destination offset
 *       r7  physical destination segment
 *       r2  zero on success, -1 on transport failure
 *
 *   write, address 0x29b8
 *       unsupported; returns -1
 *
 *   position, address 0x2a88
 *       r5  record number within the file
 *       r6  logical file number
 *       r7  track number
 *       r2  zero on success, -1 on failure
 *
 * The host protocol is SADIE-specific and preserves physical records:
 *
 *   position: SOH "SD" 1 track file record_hi record_lo xor -> ACK/CAN
 *   read:     'R' max_hi max_lo xor
 *   EOF:      EOT -> ACK
 *   record:   STX length_hi length_lo -> 'C', then CRC-16/XMODEM packets,
 *             followed by EOT -> ACK
 *
 * XMODEM packets are SOH, block, 0xff-block, 128 data bytes, CRC high/low.
 * The final packet is padded by the host; only the announced record length is
 * copied.  A read consumes at most one physical record, matching the TCC.
 *
 * Validated bytes are copied from the logical stack buffer into physical
 * memory one byte at a time.  SADIE's SC #1/#2 mapping switch is used only
 * around the physical store, so the source never needs a guessed physical
 * segment.  This supports the original segment-0 and segment-1 callers.
 */

	.section .text
	.globl _sadie_read
	.globl _sadie_write
	.globl _sadie_position
	.globl _sadie_load
	.globl _sadie_command
	.globl _sadie_rewind
	.globl _sadie_unload

	.equ SOH,  0x01
	.equ STX,  0x02
	.equ EOT,  0x04
	.equ ACK,  0x06
	.equ NAK,  0x15
	.equ CAN,  0x18
	.equ CRC_REQUEST, 'C'
	.equ TRACE_BEFORE_STORE, 0x10
	.equ TRACE_AFTER_STORE,  0x11

	.equ TTY0_DATA, 0xff81
	.equ TTY0_CTL,  0xff85
	/* Stack frame used by _sadie_read. */
	.equ BUFFER,       0x00
	.equ DEST_SEG,     0x80
	.equ DEST_OFF,     0x82
	.equ REMAINING,    0x84
	.equ COUNT_PTR,    0x86
	.equ RECORDS_LEFT, 0x88
	.equ TOTAL,        0x8a
	.equ RECORD_LEFT,  0x8c
	.equ SAVED_REGS,   0x94
	.equ READ_FRAME,   0x9e

	.macro PUTBYTE
	calr	.Lputbyte
	.endm

	.macro GETBYTE
	calr	.Lgetbyte
	.endm

/* Fixed original entry 0x2874. */
_sadie_read:
	sub	r15,#READ_FRAME
	ldm	SAVED_REGS(r15),r3,#5
	ld	DEST_SEG(r15),r7
	ld	DEST_OFF(r15),r6
	ld	REMAINING(r15),r5
	ld	COUNT_PTR(r15),r4
	ld	RECORDS_LEFT(r15),r3
	clr	TOTAL(r15)
	clr	@r4

.Lread_next:
	test	REMAINING(r15)
	jr	z,.Lread_ok
	test	RECORDS_LEFT(r15)
	jr	z,.Lread_ok
	ldb	rl0,#'R'
	PUTBYTE
	ldb	rl1,#'R'
	ldb	rl0,REMAINING+0(r15)
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,REMAINING+1(r15)
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rl1
	PUTBYTE
	GETBYTE
	test	r0
	jr	z,.Lread_error
	cpb	rl3,#EOT
	jr	z,.Lread_eof
	cpb	rl3,#STX
	jr	nz,.Lread_error
	GETBYTE
	test	r0
	jr	z,.Lread_error
	ldb	RECORD_LEFT+0(r15),rl3
	ldb	rl1,rl3
	GETBYTE
	test	r0
	jr	z,.Lread_error
	ldb	RECORD_LEFT+1(r15),rl3
	ld	r2,RECORD_LEFT(r15)
	cp	r2,REMAINING(r15)
	jr	ugt,.Lread_error
	ldb	rh2,#1
	clrb	rh3
	/* A distinct CRC request starts the shared XMODEM receiver. */
	ldb	rl0,#CRC_REQUEST
	PUTBYTE
	jp	.Lpacket_loop

.Lread_eof:
	ldb	rl0,#ACK
	PUTBYTE
.Lread_ok:
	ld	r4,COUNT_PTR(r15)
	ld	r2,TOTAL(r15)
	ld	@r4,r2
	ldk	r2,#0
	jr	.Lread_return
.Lread_error:
	ld	r2,#-1
.Lread_return:
	ldm	r3,SAVED_REGS(r15),#5
	add	r15,#READ_FRAME
	ret

	/* Fixed original write entry 0x29b8: read-only transport. */
	.org 0x144
_sadie_write:
	ld	r2,#-1
	ret

/* SADIE-only sink for a block already validated by the shared ZEUS core. */
.Lpacket_valid:
	ld	r4,RECORD_LEFT(r15)
	cp	r4,#128
	jr	ule,.Lcopy_size_ready
	ld	r4,#128
.Lcopy_size_ready:
	ldb	rl0,#TRACE_BEFORE_STORE
	PUTBYTE
	ld	r5,r15
	ld	r6,DEST_SEG(r15)
	exb	rh6,rl6
	ld	r7,DEST_OFF(r15)
	ld	r3,r4
.Lphysical_byte:
	ldb	rl0,@r5
	inc	r5,#1
	sc	#1
	ldb	@r6,rl0
	sc	#2
	inc	r7,#1
	djnz	r3,.Lphysical_byte
	ldb	rl0,#TRACE_AFTER_STORE
	PUTBYTE

	ld	r3,DEST_OFF(r15)
	add	r3,r4
	ld	DEST_OFF(r15),r3
	jr	nc/uge,.Lno_segment_carry
	ld	r3,DEST_SEG(r15)
	inc	r3,#1
	ld	DEST_SEG(r15),r3
.Lno_segment_carry:
	ld	r3,RECORD_LEFT(r15)
	sub	r3,r4
	ld	RECORD_LEFT(r15),r3
	ld	r3,REMAINING(r15)
	sub	r3,r4
	ld	REMAINING(r15),r3
	ld	r3,TOTAL(r15)
	add	r3,r4
	ld	TOTAL(r15),r3
	ldb	rl0,#ACK
	PUTBYTE
	incb	rh2,#1
	clrb	rh3
	jp	.Lpacket_loop

/*
 * Fixed original positioning entry 0x2a88.  The request selects all three
 * levels explicitly, so switching track also resets that track's logical BOT.
 */
	.org 0x214
_sadie_position:
	push	@r15,r5
	push	@r15,r6
	push	@r15,r7
	ldb	rl0,#SOH
	PUTBYTE
	ldb	rl1,#SOH
	ldb	rl0,#'S'
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,#'D'
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,#1
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rl7
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rl6
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rh5
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rl5
	xorb	rl1,rl0
	PUTBYTE
	ldb	rl0,rl1
	PUTBYTE
	GETBYTE
	test	r0
	jr	z,.Lposition_error
	cpb	rl3,#ACK
	jr	nz,.Lposition_error
	ldk	r2,#0
	jr	.Lposition_return
.Lposition_error:
	ld	r2,#-1
.Lposition_return:
	pop	r7,@r15
	pop	r6,@r15
	pop	r5,@r15
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
	ret
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

/* Original LOAD helper at 0x2bee. Position requests already establish BOT. */
	.org 0x37a
_sadie_load:
	ldk	r2,#0
	ret

/* Original command/status helper at 0x2c00. */
	.org 0x38c
_sadie_command:
	ldk	r2,#0
	ret

.Lpacket_loop:
	/* The exact shared ZEUS core writes a validated block to r5. */
	ld	r4,#128
	ld	r5,r15
	.include "../serial_installer/xmodem_receive.inc"
	jp	.Lpacket_valid
.Lbad:
	jp	.Lpacket_bad
.Lerror:
	jp	.Lread_error
.Leot:
	jp	.Lrecord_eot
.Lpacket_bad:
	incb	rh3,#1
	cpb	rh3,#10
	jp	ugt,.Lread_error
	/* Exact ZEUS recovery: drain to a full inter-byte timeout, then NAK. */
.Ldrain:
	GETBYTE
	test	r0
	jr	nz,.Ldrain
	ldb	rl0,#NAK
	PUTBYTE
	jp	.Lpacket_loop

.Lrecord_eot:
	test	RECORD_LEFT(r15)
	jp	nz,.Lread_error
	ldb	rl0,#ACK
	PUTBYTE
	dec	RECORDS_LEFT(r15),#1
	jp	.Lread_next

/* Original rewind/unload menu entries. They are harmless read-only no-ops. */
	.org 0x4a4
_sadie_rewind:
	ldk	r2,#0
	ret
	.org 0x4b0
_sadie_unload:
	ldk	r2,#0
	ret

	.org 0x4c2
