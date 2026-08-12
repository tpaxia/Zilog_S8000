#!/bin/sh
# Build the no-FUSE V7 image builder (big-endian / ZEUS-compatible).
set -e
cd "$(dirname "$0")"
cc -std=c11 -g -O1 -Wall -fno-common \
   -D_FILE_OFFSET_BITS=64 -D_DARWIN_C_SOURCE \
   -I./src -I./ancient-src/v7 \
   -o mkv7img \
   ancient-src/v7/sys/alloc.c ancient-src/v7/dev/bio.c ancient-src/v7/sys/subr.c \
   ancient-src/v7/sys/iget.c ancient-src/v7/sys/rdwri.c ancient-src/v7/sys/nami.c \
   ancient-src/v7/sys/fio.c ancient-src/v7/sys/pipe.c ancient-src/v7/sys/sys2.c \
   ancient-src/v7/sys/sys3.c ancient-src/v7/sys/sys4.c ancient-src/v7/sys/main.c \
   src/v7fs.c src/v7adapt.c src/idmap.c src/dskio.c src/mkv7img.c
echo "built ./mkv7img"
