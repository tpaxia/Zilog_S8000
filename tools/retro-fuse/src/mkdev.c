/*
 * mkdev - create device nodes in an existing (big-endian V7 / ZEUS) filesystem
 *         image at a given block offset, via the retro-fuse v7fs C API.
 *
 * usage: mkdev <image> <fssize-blocks> <offset-blocks> <devs-file>
 *
 * devs-file lines:  <path> <c|b> <major> <minor> <octal-mode>
 *   e.g.            /dev/console c 0 0 622
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include "dskio.h"
#include "v7fs.h"

/* v7 makedev: (major<<8)|minor */
static dev_t v7makedev(int maj, int min) { return (dev_t)((maj << 8) | (min & 0xff)); }

int main(int argc, char **argv)
{
    if (argc != 5) {
        fprintf(stderr, "usage: %s <image> <fssize-blocks> <offset-blocks> <devs-file>\n", argv[0]);
        return 2;
    }
    const char *image = argv[1];
    uint32_t fssize = (uint32_t)strtoul(argv[2], NULL, 0);
    off_t    offset = (off_t)strtoull(argv[3], NULL, 0);

    int r = dsk_open(image, (off_t)fssize, offset, 0, 0, 0);
    if (r != 0) { fprintf(stderr, "ERROR dsk_open: %s\n", strerror(-r)); return 1; }
    r = v7fs_init(0);
    if (r != 0) { fprintf(stderr, "ERROR v7fs_init: %s\n", strerror(-r)); return 1; }
    v7fs_setreuid(0, 0); v7fs_setregid(0, 0);

    /* make sure /dev exists */
    v7fs_mkdir("/dev", 0755); v7fs_chown("/dev", 0, 0);

    FILE *f = fopen(argv[4], "r");
    if (!f) { fprintf(stderr, "ERROR open %s: %s\n", argv[4], strerror(errno)); return 1; }
    char line[256]; int made = 0, err = 0;
    while (fgets(line, sizeof line, f)) {
        char path[128], type; int maj, min, mode;
        if (line[0] == '#' || line[0] == '\n') continue;
        if (sscanf(line, "%127s %c %d %d %o", path, &type, &maj, &min, &mode) != 5) continue;
        mode_t m = (mode & 07777) | ((type == 'b') ? S_IFBLK : S_IFCHR);
        v7fs_unlink(path);                       /* in case it exists */
        int e = v7fs_mknod(path, m, v7makedev(maj, min));
        if (e < 0) { fprintf(stderr, "  ! mknod %s: %s\n", path, strerror(-e)); err++; }
        else { v7fs_chown(path, 0, 0); made++; printf("  %s %c %d,%d %o\n", path, type, maj, min, mode); }
    }
    fclose(f);
    v7fs_sync(); v7fs_shutdown(); dsk_flush(); dsk_close();
    printf("Done. %d node(s) created, %d error(s)\n", made, err);
    return err ? 1 : 0;
}
