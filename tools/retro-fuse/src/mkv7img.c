/*
 * mkv7img - build a (big-endian, ZEUS/S8000-compatible) Unix V7 filesystem
 *           image and populate it from one or more host directory trees,
 *           WITHOUT using FUSE.  Drives the retro-fuse v7fs C API directly.
 *
 * usage: mkv7img <image> <fssize-blocks> <offset-blocks> <create> [<srcdir> <fsdestdir>]...
 *
 *   <image>          output image file
 *   <fssize-blocks>  filesystem size in 512-byte blocks
 *   <offset-blocks>  block offset within <image> where this filesystem starts
 *   <create>         1 = create/overwrite the image file (sized to offset+fssize);
 *                    0 = open an existing image and write the fs at <offset>
 *   <srcdir>         host directory whose *contents* are copied
 *   <fsdestdir>      destination path inside the image (e.g. "/" or "/usr")
 *
 * Files are created owned by root (uid/gid 0), which is what a bootable
 * system disk needs.  AppleDouble (._*) and .DS_Store droppings are skipped.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

#include "dskio.h"
#include "v7fs.h"

static int g_errors = 0;
static int g_links  = 0;

/* Hard-link reconstruction: the extracted trees lost hard links (every file
 * shows st_nlink==1), but many V7 files are genuinely linked (sh/rsh, od/hd,
 * more/page, the two kernels, ...).  We rebuild links by content identity:
 * the first occurrence of a given (size,hash) is copied; later identical,
 * non-empty files are hard-linked to it instead of duplicated. */
struct dedup_ent { off_t size; uint64_t hash; char *fspath; };
static struct dedup_ent *g_ded = NULL;
static size_t g_dedn = 0, g_dedcap = 0;

/* FNV-1a 64-bit over a file's contents; returns 0 and sets *ok=0 on error. */
static uint64_t hash_file(const char *hostpath, int *ok)
{
    int fd = open(hostpath, O_RDONLY);
    if (fd < 0) { *ok = 0; return 0; }
    uint64_t h = 1469598103934665603ULL;
    unsigned char buf[65536];
    ssize_t n;
    while ((n = read(fd, buf, sizeof buf)) > 0)
        for (ssize_t i = 0; i < n; i++) { h ^= buf[i]; h *= 1099511628211ULL; }
    close(fd);
    *ok = (n == 0);
    return h;
}

/* return the fspath of a previously-copied identical file, or NULL */
static const char *dedup_lookup(off_t size, uint64_t hash)
{
    for (size_t i = 0; i < g_dedn; i++)
        if (g_ded[i].size == size && g_ded[i].hash == hash)
            return g_ded[i].fspath;
    return NULL;
}

static void dedup_add(off_t size, uint64_t hash, const char *fspath)
{
    if (g_dedn == g_dedcap) {
        g_dedcap = g_dedcap ? g_dedcap * 2 : 256;
        g_ded = realloc(g_ded, g_dedcap * sizeof *g_ded);
    }
    g_ded[g_dedn].size = size;
    g_ded[g_dedn].hash = hash;
    g_ded[g_dedn].fspath = strdup(fspath);
    g_dedn++;
}

static int skip_name(const char *n)
{
    if (strcmp(n, ".") == 0 || strcmp(n, "..") == 0)
        return 1;
    if (n[0] == '.' && n[1] == '_')          /* AppleDouble */
        return 1;
    if (strcmp(n, ".DS_Store") == 0)
        return 1;
    return 0;
}

/* copy one regular file's contents into the image, or hard-link it to an
 * already-copied identical file (reconstructing lost V7 hard links) */
static void copy_file(const char *hostpath, const char *fspath, mode_t mode, off_t size)
{
    if (size > 0) {
        int ok = 0;
        uint64_t h = hash_file(hostpath, &ok);
        if (ok) {
            const char *target = dedup_lookup(size, h);
            if (target != NULL) {
                int lr = v7fs_link(target, fspath);
                if (lr == 0) { g_links++; return; }
                /* fall through to a plain copy if linking fails */
            }
        }
    }

    int in = open(hostpath, O_RDONLY);
    if (in < 0) { fprintf(stderr, "  ! open host %s: %s\n", hostpath, strerror(errno)); g_errors++; return; }

    int out = v7fs_open(fspath, O_CREAT | O_WRONLY | O_TRUNC, mode & 07777);
    if (out < 0) { fprintf(stderr, "  ! v7 create %s: %s\n", fspath, strerror(-out)); g_errors++; close(in); return; }

    char buf[65536];
    ssize_t n;
    while ((n = read(in, buf, sizeof buf)) > 0) {
        ssize_t off = 0;
        while (off < n) {
            ssize_t w = v7fs_write(out, buf + off, (size_t)(n - off));
            if (w < 0) { fprintf(stderr, "  ! v7 write %s: %s\n", fspath, strerror((int)-w)); g_errors++; break; }
            off += w;
        }
    }
    close(in);
    v7fs_close(out);
    v7fs_chown(fspath, 0, 0);
    if (size > 0) {
        int ok = 0;
        uint64_t h = hash_file(hostpath, &ok);
        if (ok) dedup_add(size, h, fspath);
    }
}

/* recursively copy the CONTENTS of hostdir into fsdir (which must already exist) */
static void copy_tree(const char *hostdir, const char *fsdir)
{
    DIR *d = opendir(hostdir);
    if (!d) { fprintf(stderr, "  ! opendir %s: %s\n", hostdir, strerror(errno)); g_errors++; return; }

    struct dirent *de;
    while ((de = readdir(d)) != NULL) {
        if (skip_name(de->d_name))
            continue;

        char hp[4096], fp[4096];
        snprintf(hp, sizeof hp, "%s/%s", hostdir, de->d_name);
        snprintf(fp, sizeof fp, "%s%s%s", fsdir,
                 (strcmp(fsdir, "/") == 0) ? "" : "/", de->d_name);

        struct stat st;
        if (lstat(hp, &st) != 0) { fprintf(stderr, "  ! lstat %s: %s\n", hp, strerror(errno)); g_errors++; continue; }

        if (S_ISDIR(st.st_mode)) {
            int r = v7fs_mkdir(fp, st.st_mode & 07777);
            if (r < 0 && r != -EEXIST) { fprintf(stderr, "  ! v7 mkdir %s: %s\n", fp, strerror(-r)); g_errors++; continue; }
            v7fs_chown(fp, 0, 0);
            copy_tree(hp, fp);
        } else if (S_ISREG(st.st_mode)) {
            copy_file(hp, fp, st.st_mode, st.st_size);
        } else if (S_ISLNK(st.st_mode)) {
            fprintf(stderr, "  ~ skip symlink (V7 has none): %s\n", fp);
        } else {
            fprintf(stderr, "  ~ skip special file: %s (mode %o)\n", fp, st.st_mode);
        }
    }
    closedir(d);
}

int main(int argc, char **argv)
{
    if (argc < 5 || (argc % 2) != 1) {
        fprintf(stderr, "usage: %s <image> <fssize-blocks> <offset-blocks> <create> [<srcdir> <fsdestdir>]...\n", argv[0]);
        return 2;
    }

    const char *image = argv[1];
    uint32_t fssize = (uint32_t)strtoul(argv[2], NULL, 0);
    off_t    offset = (off_t)strtoull(argv[3], NULL, 0);
    int      create = (int)strtol(argv[4], NULL, 0);
    int      argbase = 5;

    /* If creating, pre-size the whole image file to offset+fssize blocks so
     * that a filesystem placed at a nonzero offset still fits. */
    if (create) {
        FILE *f = fopen(image, "wb");
        if (!f) { fprintf(stderr, "ERROR: create %s: %s\n", image, strerror(errno)); return 1; }
        if (ftruncate(fileno(f), (off_t)(offset + fssize) * 512) != 0) {
            fprintf(stderr, "ERROR: size %s: %s\n", image, strerror(errno)); return 1;
        }
        fclose(f);
    }

    /* open the (existing) image and map fs block 0 to <offset> (1 fs-blk == 512B) */
    int r = dsk_open(image, (off_t)fssize, offset, 0 /*no create*/, 0 /*no overwrite*/, 0 /*rw*/);
    if (r != 0) { fprintf(stderr, "ERROR: dsk_open %s: %s\n", image, strerror(-r)); return 1; }

    /* Official System 8000 Model 31 SMD interleave parameters. */
    struct v7fs_flparams fl = { .m = 16, .n = 224 };
    r = v7fs_mkfs(fssize, 0 /*auto isize*/, &fl);
    if (r != 0) { fprintf(stderr, "ERROR: v7fs_mkfs: %s\n", strerror(-r)); return 1; }

    r = v7fs_init(0);
    if (r != 0) { fprintf(stderr, "ERROR: v7fs_init: %s\n", strerror(-r)); return 1; }

    /* create everything as root */
    v7fs_setreuid(0, 0);
    v7fs_setregid(0, 0);

    for (int i = argbase; i + 1 < argc; i += 2) {
        const char *src = argv[i];
        const char *dst = argv[i + 1];
        printf("Copying %s  ->  %s\n", src, dst);
        if (strcmp(dst, "/") != 0) {
            int m = v7fs_mkdir(dst, 0755);
            if (m < 0 && m != -EEXIST) fprintf(stderr, "  ! v7 mkdir %s: %s\n", dst, strerror(-m));
            v7fs_chown(dst, 0, 0);
        }
        copy_tree(src, dst);
    }

    v7fs_sync();
    v7fs_shutdown();
    dsk_flush();
    dsk_close();

    printf("Done. Image: %s  (%u blocks / %u KB), %d hard-link(s), %d error(s)\n",
           image, fssize, fssize / 2, g_links, g_errors);
    return g_errors ? 1 : 0;
}
