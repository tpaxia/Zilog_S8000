# Extracted SADIE diagnostics

These are exact, named copies of the logical files on SADIE track 1. They are flat standalone images, not `s.out` files. SADIE command numbers are two greater than the track-1 file number; for example, command/test 24 loads track 1 file 22, `MMUTST`.

`support-FPP-U-CODE.bin` is control-store data used by the floating-point diagnostics and is not itself a menu command. `manifest.tsv` records every mapping, size, and SHA-256 digest. Regenerate this directory with `python3 tapes/extract_tape_images.py`.
