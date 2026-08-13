/*
 * taperestore - make a V7 fs or replay a ZEUS dump-derived manifest.
 *
 * This is the host-side equivalent of tape files 3 (standalone mkfs) and 4
 * (standalone restor).  It consumes data and metadata decoded directly from
 * tape dump files; no reconstructed host filesystem tree is involved.
 *
 * Manifest fields are tab-separated:
 *   kind mode uid gid atime mtime aux path
 * kind: d directory, f regular file, b/c device, h hard link, u unlink.
 * aux is a host payload path, numeric V7 rdev, or existing link target.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include "dskio.h"
#include "v7fs.h"

#if defined(__APPLE__)
#include <sys/types.h>
#elif defined(__linux__)
#include <sys/sysmacros.h>
#endif

struct entry {
    char kind;
    mode_t mode;
    uid_t uid;
    gid_t gid;
    time_t atime;
    time_t mtime;
    char *aux;
    char *path;
};

static int failures;

static void fail(const char *op, const char *path, int err)
{
    fprintf(stderr, "  ! %s %s: %s\n", op, path, strerror(err < 0 ? -err : err));
    failures++;
}

static int parse_entry(char *line, struct entry *e)
{
    char *field[8], *p = line;
    for (int i = 0; i < 8; i++) {
        field[i] = p;
        char *tab = strchr(p, i == 7 ? '\n' : '\t');
        if (tab == NULL) {
            if (i == 7) tab = p + strlen(p);
            else return -1;
        }
        *tab = '\0';
        p = tab + 1;
    }
    e->kind = field[0][0];
    e->mode = (mode_t)strtoul(field[1], NULL, 8);
    e->uid = (uid_t)strtoul(field[2], NULL, 10);
    e->gid = (gid_t)strtoul(field[3], NULL, 10);
    e->atime = (time_t)strtoll(field[4], NULL, 10);
    e->mtime = (time_t)strtoll(field[5], NULL, 10);
    e->aux = strdup(field[6]);
    e->path = strdup(field[7]);
    return e->aux && e->path ? 0 : -1;
}

static int copy_file(const char *source, const char *path, mode_t mode)
{
    int in = open(source, O_RDONLY);
    if (in < 0) return -errno;
    int out = v7fs_open(path, O_CREAT | O_WRONLY | O_TRUNC, mode & 07777);
    if (out < 0) { close(in); return out; }
    char buf[65536];
    ssize_t nr;
    int result = 0;
    while ((nr = read(in, buf, sizeof buf)) > 0) {
        ssize_t pos = 0;
        while (pos < nr) {
            ssize_t nw = v7fs_write(out, buf + pos, (size_t)(nr - pos));
            if (nw < 0) { result = (int)nw; goto done; }
            pos += nw;
        }
    }
    if (nr < 0) result = -errno;
done:
    close(in);
    if (v7fs_close(out) < 0 && result == 0) result = -EIO;
    return result;
}

static void set_metadata(const struct entry *e)
{
    int r = v7fs_chown(e->path, e->uid, e->gid);
    if (r < 0) fail("chown", e->path, r);
    r = v7fs_chmod(e->path, e->mode & 07777);
    if (r < 0) fail("chmod", e->path, r);
    struct timespec times[2] = {{e->atime, 0}, {e->mtime, 0}};
    r = v7fs_utimens(e->path, times);
    if (r < 0) fail("utimens", e->path, r);
}

int main(int argc, char **argv)
{
    if (argc != 8) {
        fprintf(stderr, "usage: %s image fssize offset interleave sectors-per-cylinder mkfs|restore manifest\n", argv[0]);
        return 2;
    }
    const char *image = argv[1], *action = argv[6], *manifest = argv[7];
    uint32_t fssize = (uint32_t)strtoul(argv[2], NULL, 0);
    off_t offset = (off_t)strtoull(argv[3], NULL, 0);
    struct v7fs_flparams fl = {
        .m = (uint16_t)strtoul(argv[4], NULL, 0),
        .n = (uint16_t)strtoul(argv[5], NULL, 0),
    };

    struct entry *entries = NULL;
    size_t count = 0, cap = 0;
    if (strcmp(action, "restore") == 0) {
        FILE *mf = fopen(manifest, "r");
        if (!mf) { perror(manifest); return 1; }
        char *line = NULL;
        size_t linesz = 0;
        while (getline(&line, &linesz, mf) >= 0) {
            if (line[0] == '#' || line[0] == '\n') continue;
            if (count == cap) {
                cap = cap ? cap * 2 : 512;
                entries = realloc(entries, cap * sizeof *entries);
                if (!entries) { perror("realloc"); return 1; }
            }
            if (parse_entry(line, &entries[count]) < 0) {
                fprintf(stderr, "bad manifest line %zu\n", count + 1);
                return 1;
            }
            count++;
        }
        free(line);
        fclose(mf);
    } else if (strcmp(action, "mkfs") != 0) {
        fprintf(stderr, "action must be mkfs or restore\n");
        return 2;
    }

    int r = dsk_open(image, (off_t)fssize, offset, 0, 0, 0);
    if (r < 0) { fprintf(stderr, "dsk_open: %s\n", strerror(-r)); return 1; }
    if (strcmp(action, "mkfs") == 0) {
        r = v7fs_mkfs(fssize, 0, &fl);
        if (r < 0) { fprintf(stderr, "mkfs: %s\n", strerror(-r)); return 1; }
        dsk_flush();
        dsk_close();
        printf("made filesystem at block %llu (%u blocks), interleave %u/%u\n",
               (unsigned long long)offset, fssize, fl.m, fl.n);
        return 0;
    }
    r = v7fs_init(0);
    if (r < 0) { fprintf(stderr, "v7fs_init: %s\n", strerror(-r)); return 1; }
    v7fs_setreuid(0, 0);
    v7fs_setregid(0, 0);

    /* The manifest is ordered: parent directories, objects, hard links. */
    for (size_t i = 0; i < count; i++) {
        struct entry *e = &entries[i];
        r = 0;
        switch (e->kind) {
        case 'd':
            if (strcmp(e->path, "/") != 0) {
                r = v7fs_mkdir(e->path, 0700);
                if (r < 0 && r != -EEXIST) fail("mkdir", e->path, r);
            }
            break;
        case 'f':
            r = copy_file(e->aux, e->path, e->mode);
            if (r < 0) fail("restore", e->path, r);
            break;
        case 'b':
        case 'c': {
            unsigned long vd = strtoul(e->aux, NULL, 0);
            mode_t type = e->kind == 'b' ? S_IFBLK : S_IFCHR;
            dev_t hd = makedev((vd >> 8) & 0xff, vd & 0xff);
            r = v7fs_mknod(e->path, type | (e->mode & 07777), hd);
            if (r < 0) fail("mknod", e->path, r);
            break;
        }
        case 'h':
            r = v7fs_link(e->aux, e->path);
            if (r < 0) fail("link", e->path, r);
            break;
        case 'u':
            r = v7fs_unlink(e->path);
            if (r < 0) fail("unlink", e->path, r);
            break;
        default:
            fprintf(stderr, "unknown manifest kind %c for %s\n", e->kind, e->path);
            failures++;
        }
        if (e->kind != 'h' && e->kind != 'u' && r >= 0) set_metadata(e);
    }

    /* Directory mtimes were disturbed while their children were installed. */
    for (size_t i = count; i-- > 0;)
        if (entries[i].kind == 'd') set_metadata(&entries[i]);

    v7fs_sync();
    v7fs_shutdown();
    dsk_flush();
    dsk_close();
    printf("restored %zu manifest entries at block %llu (%u blocks), %d error(s)\n",
           count, (unsigned long long)offset, fssize, failures);
    return failures ? 1 : 0;
}
