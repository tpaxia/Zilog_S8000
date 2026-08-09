# ZEUS 3.21 `init` source reconstruction

`init.c` is a source-level reconstruction of the stripped Zilog binary:

```text
archive/INIT.zeus-3.21-original
SHA-256 5873ac91acf5db951bb072fd39f3fe60f50bf9ea62e1be9aac31babb05950ea1
```

The binary identifies its source as:

```text
@[$]init.c
2.6  08/20/84 10:46:50 - Zilog Inc
```

The System III source in `init.sysiii.c` supplies the process-management
core.  `init.c` adds the behavior found in the ZEUS disassembly:

* a fixed initial environment containing `HOME`, `PATH`, `TERM`, `SHELL`,
  and `LOGNAME`;
* console terminal-type lookup through `/etc/ttytype`;
* selection of initial state 2 when `argv[0]` begins with `m`;
* explicit termination of the `co` console process group during a state
  1-to-2 transition;
* the ZEUS signal-state handler: save the previous state and request an
  inittab reread, force state 1 for signal 1, ignore signal 2 after recording
  the reread request, and map the remaining run-state signals through `ST`.

The following binary evidence anchors those additions:

| Loaded address | Reconstructed operation |
|---:|---|
| `0x010a`–`0x0122` | `stypeof("/dev/console")`, copy after `TERM=`, install `environ` |
| `0x0128`–`0x013a` | test `argv[0][0] == 'm'`, set state `'2'` |
| `0x0168`–`0x01b6` | on state `2`, previous state `1`, signal `co` group with 15 then 9 |
| `0x0a62`–`0x0ac2` | ZEUS `chst`: save state, set `rdstate`, handle signals 1 and 2 specially |
| `0x0dc8`–`0x0e26` | scan `/etc/ttytype` with `fscanf("%s%s", ...)` |
| `0x0e28`–`0x0e40` | extract device basename with `strrchr` and call `_ttytype` |

The remaining init-specific functions correspond directly, in order, to the
System III source: `fit`, `invttys`, `iexec`, `waitttys`, `runrc`,
`readttys`, `lookproc`, `lookid`, `chst`, `rckill`, `ignsigs`, `setsigs`,
`rsetsigs`, `err`, and `itoa`.

This is intended-source equivalence, not a claim that a modern compiler will
reproduce the original bytes.  A byte-for-byte comparison requires Zilog's
1984 compiler, startup object, linker, and matching libraries.  The source
also intentionally does not reproduce the shipped binary's corrupt second
`malloc` call to `0x3578`; a normal rebuild calls the real `sbrk` routine and
therefore incorporates the repair documented by `patch_init.py`.

## Superseded: this reconstruction is no longer installed

**The production image now installs the original Zilog binary**,
`build/init.pristine-911118`, recovered from a pristine 1991-11-18 level-0 root
dump. The reconstruction described here survives as source only — `init.c` in
this directory — and is no longer built or installed. The compiled artifact has
been removed.

The reconstruction existed because the only copy of the original then
available, `archive/INIT.zeus-3.21-original`, had one corrupt 512-byte sector.
The pristine binary differs from it in nine bytes, all inside 0x2200–0x23FF,
seven of them single-bit flips.

The dump vindicates the analysis recorded here on both counts:

- the byte patched at 0x220c by `patch_init.py` (`0x35` → `0x25`) is exactly
  what the pristine original contains;
- the corrupt second `malloc` call to `0x3578` is a two-byte corruption — the
  pristine binary holds `0004` at 0x2284 where the damaged copy holds `f464`.

So the "corrupt shipped binary" was never shipped corrupt; the archive copy had
rotted. The intended-source equivalence argument above still stands on its own
terms, and the reconstruction remains the only readable account of what ZEUS
init does.

The installed `rc.clean` reconnects init's standard descriptors to
`/dev/console`. `rc_csh.clean` performs the multi-user filesystem checks and
mounts, and `inittab.clean` starts the console login wrapper. The wrapper and
configuration files are scripts/data; they do not replace the original ZEUS
`getty` or `login` executables.

With the original init restored, **no userland executable in the image is
recompiled**; all are original recovered ZEUS binaries. The kernel is
separately relinked from original ZEUS objects, and the main README documents
the narrow `date`/`datem` compatibility patches.
