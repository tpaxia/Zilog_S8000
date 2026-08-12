/* @[$]block0.h	1.2  06/11/84 12:30:44 - Zilog Inc */

#define VDMASK	     	(0x0F)				/* Vir. disk mask    */
#define UNMASK	     	(0xF0)				/* Unit mask	     */
#define VD(dev)      	( minor(dev)&VDMASK )		/* Gets vir. dsk. no.*/
#define DSK_UNIT(dev)  	(( minor(dev)&UNMASK ) >>4)	/* Gets disk unit    */
#define BIT		(0x1)				/* ONE as we know it */

/*
** Macro's to access virtual disk size and offset
*/
#define VD_SIZ(tbl,dev)    (tbl[DSK_UNIT(dev)].vd_ptr[VD(dev)].vd_nblocks)
#define VD_OFF(tbl,dev)    (tbl[DSK_UNIT(dev)].vd_ptr[VD(dev)].vd_blkoff)

/*
** Macro's to determine if a fs is active, or mark a fs as closed or open
*/
#define VD_RAWOPEN(tbl,dev)  (tbl[DSK_UNIT(dev)].vd_rawflgs |= (BIT <<VD(dev)))
#define VD_RAWCLOSE(tbl,dev) (tbl[DSK_UNIT(dev)].vd_rawflgs &= ~(BIT <<VD(dev)))
#define VD_BLKOPEN(tbl,dev)  (tbl[DSK_UNIT(dev)].vd_blkflgs |= (BIT <<VD(dev)))
#define VD_BLKCLOSE(tbl,dev) (tbl[DSK_UNIT(dev)].vd_blkflgs &= ~(BIT <<VD(dev)))
#define VD_RESET(tbl,dev)    (tbl[DSK_UNIT(dev)].vd_ptr = vd_dflt)
#define VD_ACTIVE(tbl,dev)   (tbl[DSK_UNIT(dev)].vd_rawflgs || \
			      		tbl[DSK_UNIT(dev)].vd_blkflgs)

#define MAXFS		16	    /* Max. no. of filesystems per drive */
#define BLK0MAGIC  	0xDEADBABE  /* Block zero magic number		 */

/*
** The following are defined in ../h/systm.h
*/
extern dev_t 		rootdev;	/* unit on which root resides */
extern dev_t 		swapdev;	/* unit on which swap resides */
extern dev_t 		pipedev;	/* unit on which pipes resides*/
extern int		nswap;		/* swap size		      */

/*
** The following are defined in ../conf/z.c
*/
extern struct vd_size   vd_dflt[];      /* Default disk layout */

/*
** The following are defined in ../h/systm.h
*/
extern int boot;			/* bootime flag */

union	block0 {
	struct b0_info
	{
		unsigned long	b0_MAGIC; 	/* MAGIC == 0xDEADBABE 	     */
		unsigned long	b0_bfstype;	/* Secondary boot fstype     */
		unsigned short	b0_bdrv;	/* Secondary boot unit 	     */
		unsigned long	b0_boff;	/* Secondary boot offset     */
		unsigned long	b0_rfstype;	/* Root fstype		     */
		unsigned short	b0_rdrv;	/* Root unit		     */
		unsigned long	b0_roff;	/* Root offset		     */
		unsigned short	b0_rdev;	/* Root device (major/minor) */
		unsigned short	b0_sdev;	/* Swap device (major/minor) */
		unsigned short	b0_pdev;	/* Pipe device (major/minor) */
		unsigned long	b0_ssz;		/* Swap size		     */
		struct	vd_size b0_vfs[MAXFS];  /* Virtual filesystem layout */
	} info;
	char pad[BSIZE];
};


/*
**	Virtual Disk Open Table
*/
static struct opn_tbl	
{
	unsigned short 	 vd_rawflgs;	/* VD raw device open flags */
	unsigned short 	 vd_blkflgs;	/* VD blocked open flags    */
	struct vd_size  *vd_ptr;	/* VD layout pointer 	    */
};
