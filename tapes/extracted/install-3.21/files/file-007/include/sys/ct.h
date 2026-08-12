/* @[$]ct.h	4.1  06/11/84 12:30:54 - Zilog Inc */

/*
 * Cartridge tape unit device error codes
 */

# define DNOT_CT	1	/* No tape in drive 			*/
# define DPRO_CT	2	/* Tape write protected 		*/
# define DEOF_CT	3	/* End of files (rest of tape is blank) */
# define DEOT_CT	4	/* End of tape 				*/
