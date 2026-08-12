.po 1i
.TH PACKAGE M ZEUS
.ad
.fi
.SH NAME
package \- extract an optional package from a ZEUS release tape.
.SH SYNOPSIS
\fB/etc/package\fR
.SH DESCRIPTION
This shell procedure aids the system administrator in removing an
optional package from the ZEUS release tape. 
.B Package
is interactive and prompts for all needed information. 
To determine if the optional package will fit, the number of
free blocks required in the root and /usr filesystems is compared 
against the number of blocks available on the user's system.
If the package will fit, the
appropriate files are extracted from the release tape using 
\fBtar\fR(1).  
See the format of the release tape in the Note to User
for more information.
.PP
If the optional package will not fit, the system administrator must
provide space in the appropriate file systems.  This can be done
by removing programs in the file systems in question that the system
administrator does not believe are necessary.
Once removable programs have been identified, the dependency
list in the \fBNote to User\fR should be reviewed to ensure that no necessary
programs depend on the programs to be removed.  Alternatively, the file
system size may be increased by reconfiguring the disk allocation. See
\fBsysgen\fR(M)
and the ZEUS Administrator Manual for more information on
reconfiguring a ZEUS system.  After creating the required space 
in the appropriate file systems, the package script can be rerun 
to extract the desired package.
.SH SEE ALSO
dd(1), df(1), tar(1) 
.SH DIAGNOSTICS
Invalid inputs are rejected and re-requested.
.SH LIMITATIONS
\fBPackage\fR
must skip to the end of the release tape and this requires some time.
