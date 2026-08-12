/* @[$]map.h	4.1  06/11/84 12:31:03 - Zilog Inc */

struct map
{
	short		m_size;
	unsigned short 	m_addr;
};

struct map 	coremap[CMAPSIZ];	/* space for core allocation 	*/
struct map 	swapmap[SMAPSIZ];	/* space for swap allocation 	*/
