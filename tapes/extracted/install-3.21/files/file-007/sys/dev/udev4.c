char udev4wstr[] = "@[$]udev4.c		Rev : 4.2 	05/27/84 15:14:26" ;

/*
 * This file contains all the dummy device driver routines included
 * in the bdevsw and cdevsw tables in conf.c. These routines are 
 * required for the SYSGEN procedure, in which the ZEUS customer
 * may add up to 6 character or block i/o devices. Each of these 
 * dummy routines is equivalent to nodev() (subr.c).
 */

#include	"../h/signal.h"
#include	"../h/param.h"
#include	"../h/sysinfo.h"
#include	"../h/systm.h"
#include	"../h/dir.h"
#include	"../h/state.h"
#include	"../h/mmu.h"
#include	"../h/s.out.h"
#include	"../h/user.h"

usr4int (s) 
register struct state *s;
{
	prstate (s);
	panic ("usr4: unexpected interrupt");
	evi ();
}

/*
 ***  block i/o devices  ***
 */
usr4open () 
{
	u.u_error = ENODEV ;
} 

usr4close ()
{
	u.u_error = ENODEV ;
} 

usr4strategy ()
{
	u.u_error = ENODEV ;
} 

/*
 ***  character i/o devices  ***
 */
u4open () 
{
	u.u_error = ENODEV ;
}

u4close ()
{
	u.u_error = ENODEV ;
}

u4read () 
{
	u.u_error = ENODEV ;
}

u4write () 
{
	u.u_error = ENODEV ;
}

u4ioctl () 
{
	u.u_error = ENODEV ;
}
