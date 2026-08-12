#
# "@[$]Makefile for getfile, putfile, local"
# `make INSTALL=' will make and install all programs
# `make' will make all programs, without installation
#

#
#  The following are general definitions
#

# Kludge to decide on if installation should happen
# Last two lines of a command should have $(DOMV) $@ directory
# and $(INSTALL) protection-cmd directory
# Install
INSTALL = @/bin/test -n

# Domv, do mv
DOMV = $(INSTALL) $(MV)

# YACC
YACC = /usr/bin/yacc

RENAME = /bin/mv a.out
STRIP = /usr/bin/strip a.out
ECHO = @/bin/echo
MV = /bin/mv
RM = /bin/rm -f
CHMOD = /bin/chmod

# Chmog
CHMOG = /etc/chmog

# Ln
LN = /bin/ln

# Set uid to bin, owner to bin, group 0
SBIN = /etc/chmog 4751 bin 0

# set uid to super-user, owner to super-user, group 0
SROOT = /etc/chmog 4751 0 0

# Set mode (0555), owner bin, group 0
CHBIN = /etc/chmog 0751 bin 0

# Set mode (0555), owner super-user, group 0
CHROOT = /etc/chmog 0751 0 0

# Installation directories
BINDIR = $(ROOT)/bin
UBINDIR = $(ROOT)/usr/bin
ETCDIR = $(ROOT)/etc
LIBDIR = $(ROOT)/lib
ULIBDIR = $(ROOT)/usr/lib

# Installation messages
BIN =  is ready for installation in $(BINDIR)
UBIN = is ready for installation in $(UBINDIR)
ETC =  is ready for installation in $(ETCDIR)
LIB =  is ready for installation in $(LIBDIR)
ULIB = is ready for installation in $(ULIBDIR)

SUIDR = and must be setuid super-user
SUIDB = and must be setuid bin

INCL = /usr/include

# Cflags
CFLAGS = -O -s

#
# the following definitions are local to this Makefile
#

#
# here are the actions and dependencies
#

default:	putfile getfile local

putfile:	putfile.c $(INCL)/sgtty.h $(INCL)/sys/types.h \
	$(INCL)/sys/stat.h $(INCL)/signal.h
	$(CC) $(CFLAGS) putfile.c -o $@
	$(ECHO) $@ $(BIN)
	$(ECHO) with mode: 751  owner: bin  group: 0

local:	local.c $(INCL)/sgtty.h
	$(CC) $(CFLAGS) local.c -o $@
	$(ECHO) $@ $(BIN)
	$(ECHO) with mode: 751  owner: bin  group: 0

getfile:	getfile.c $(INCL)/sgtty.h $(INCL)/signal.h
	$(CC) $(CFLAGS) getfile.c -o $@
	$(ECHO) $@ $(BIN)
	$(ECHO) with mode: 751  owner: bin  group: 0

remote:	remote.c $(INCL)/termio.h $(INCL)/signal.h $(INCL)/stdio.h \
	$(INCL)/sys/types.h $(INCL)/sys/stat.h $(INCL)/pwd.h
	$(CC) $(CFLAGS) remote.c -o $@
	$(ECHO) $@ $(BIN)
	$(ECHO) with mode: 751  owner: bin  group: 0
