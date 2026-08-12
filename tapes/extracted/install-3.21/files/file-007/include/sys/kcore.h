/* @[$]kcore.h	4.1 06/11/84 12:31:02 - Zilog Inc.
 * The crash dump tape image.  Contains a copy of the state structure (padded
 * to 256 bytes), then copies of the contents of each of the three mmu devices'
 * registers (mmut, mmud then mmus).  This initial 1024 bytes is followed
 * immediately by a copy of all of physical memory.
 */


struct crd_hdr{				/* crash dump header */
	union{
		struct state crd_st;
		char crd_fill[256];	/* occupies 256 bytes on tape */
	} crd_state;
	struct segd crd_mmu1[64];	/* kernel mmu (mmut) */
	struct segd crd_mmu2[64];	/* mmud */
	struct segd crd_mmu3[64];	/* mmus */
};

#define kstate crd_state.crd_st
#define kmmu	crd_mmu1
