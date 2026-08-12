/* @[$]signal.h	1.1  06/11/84 12:31:19 - Zilog Inc */
/*
 * signals: dont change
 */

# define NSIG		20

/*
 * No more than 32 signals (1-32) because they are stored in bits in a long.
 */
# define SIGHUP		1	/* hangup 			*/
# define SIGINT		2	/* interrupt (rubout) 		*/
# define SIGQUIT	3	/* quit (FS) 			*/
# define SIGILL		4	/* illegal instruction 		*/
# define SIGTRAP	5	/* trace or breakpoint 		*/
# define SIGIOT		6	/* iot 				*/
# define SIGEMT		7	/* emt 				*/
# define SIGFPE		8	/* floating exception 		*/
# define SIGKILL	9	/* kill, uncatchable termination*/
# define SIGBUS		10	/* bus error 			*/
# define SIGSEG		11	/* segmentation violation 	*/
# define SIGSEGV	11	/* segmentation violation 	*/
# define SIGSYS		12	/* bad system call 		*/
# define SIGPIPE	13	/* end of pipe 			*/
# define SIGALRM	14	/* alarm clock 			*/
# define SIGTRM		15	/* catchable termination 	*/
# define SIGTERM	15	/* catchable termination 	*/
# define SIGUSR1	16	/* user defined signal 1 	*/
# define SIGUSR2	17	/* user defined signal 2 	*/
# define SIGCLD		18	/* child death 			*/
# define SIGPWR		19	/* power fail 			*/

#if RT
#define	SIGQIT	3	/* quit 				*/
#define	SIGTRC	5	/* trace trap (not reset when caught) 	*/
#endif
