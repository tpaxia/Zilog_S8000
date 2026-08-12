# Recovered 1991 `/usr` archive

`0dump-1991-06-18-usr-recovered.tar` was produced once from the damaged
`0dump.t0-94.tar` capture. One single-bit error was repaired and one trailing
block was recovered from the raw stream. The source still lacked 18 tape
records and ended after 96 of 1,010 scheduled inodes.

The archive contains the 15 regular files that reached tape. Twelve match the
other recovered archives exactly. Missing blocks in `usr/dict/words`, `hstop`,
and `hlistb` are represented by zero-filled data. Their names were identified
from size, inode order, and surviving content; they are not complete files.

Original capture SHA-256: `74a38372c2fb5e634c63e410c9cb42c6e6297ca5f52ce0ca411ebc0e91715710`.
