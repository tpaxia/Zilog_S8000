.po 1i
.TH MODEL M Zilog
.V 08/15/84 17:41:19
.\" @[$]model.M	1.3  08/15/84 17:41:19 - Zilog Inc.
.ad
.fi
.SH NAME
model \- determine the System 8000 model type
.SH SYNOPSIS
.B /etc/model
.SH DESCRIPTION
.B Model
determines the System 8000 model type by examining the switch settings
on the CPU board; this program is used by
\fBmakenewfs\fR(M).
The possible types returned by
.B model
are:
.nf

   11   - Model 11
   11P  - Model 11 Plus 
   21   - Model 21
   21P  - Model 21 Plus or Model 11 Plus
   22   - Model 22
   31   - Model 31
   31P  - Model 31 Plus
   32   - Model 32
.fi
.SH SEE ALSO
makenewfs(M)
