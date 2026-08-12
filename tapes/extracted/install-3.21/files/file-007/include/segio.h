/* @[$]segio.h	1.1  07/23/82 17:36:15 - Zilog Inc */



				/*  segiocalls.h - header for runtime	 */
				/*	environment modules		 */
				/*	3/11/80				 */
				/*	Alan Greenspan - Zilog Inc.	 */

				/* file should be moved to /usr/include  */
				/* before compiling runtime env. modules */



						/* open file flag values */
# define	F_READ  001			/* open for reading      */
# define	F_WRITE 002			/* open for writing      */


 						/* I/O devices           */
						/* in Prom monitor	 */
# define	TTYRD	0x0ad8			/* read line from tty    */
# define 	TTYWR 	0x0b76			/* write char to tty     */
# define	PDPRD	0x169e			/* read char from pdp    */
# define	PDPWR	0x0f3c			/* write a char to pdp   */
# define	STOPS	8			/* separation of tabs    */
# define	NULL	-1			/* null device           */



						/* codes for calls to 11 */
# define	READ	"0"			/* note they are strings */
# define	WRITE	"1"			/* not chars             */
# define	OPEN	"2"			/* this is more general  */
# define	CREAT	"3" 			/* and you can have more */
# define	CLOSE	"4"			/* than 10 types of call */
# define	LSEEK	"5"




# define	BUFFSIZ	80			/* size of ttyline buffer*/
# define	MAXOPEN 11			/* max # of open files   */
# define	MAXARGS  6			/* max # of args to call */





struct device {					/* template for devices  */

  int   indev  ;				/* input function        */
  int   outdev ;				/* output function       */
  int	flags  ;				/* status bits           */

} ;


