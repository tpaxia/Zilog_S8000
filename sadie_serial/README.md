# SADIE 3.5 serial diagnostic loader

This directory provides a read-only serial replacement for the SADIE 3.5
diagnostic tape transport. It preserves the recovered multi-track tape layout
and loads diagnostics through the unmodified System 8000 ROM monitor's `L`
command. The working ZEUS installer remains a separate client of the same
shared XMODEM receive core.

The server supports MAME sockets and real 9600-baud, 8-N-2 serial ports. The
operator console is SIO0 channel B; tape data uses TTY0 on SIO0 channel A. Keep
the server running after the command menu appears because selected diagnostics
can request additional tracks, files, and records.

## Build and test

Build the generated tape first if necessary, then build and test the loader:

```sh
python3 tapes/build_tape_images.py
cd sadie_serial
make test
```

The build:

- loads a small serial primary through the ROM monitor;
- substitutes a patched 27,648-byte track-0/file-1 executive;
- replaces only the executive's tape routines at `0x2874..0x2d35`;
- links that replacement at its real runtime address, `0x2874`;
- uses `../serial_installer/xmodem_receive.inc`, the exact receive core used by
  the verified ZEUS serial installer;
- preserves SADIE's physical track/file/record addressing.

The ZEUS driver remains byte-for-byte unchanged by the shared-source refactor:
its 526-byte `serial_ct.bin` has SHA-256
`f9755c920ef8b747c6f1291f327afb385e7d882683bd37d0f781a093823495b8`.

## MAME test

Start the server from the repository:

```sh
cd sadie_serial
python3 serve_sadie.py ../tapes/images/sadie-3.5.tap \
  --listen 127.0.0.1:8150 -v
```

Start MAME from a second terminal. Do not use an autostart script for the
manual test:

```sh
./s8000 s8000 -rp roms \
  -cfg_directory /path/to/Zilog_S8000/serial_installer/mame_cfg \
  -slot_cpu:cpu_a:sio0:cha:tty0 null_modem \
  -slot_cpu:cpu_a:sio0:chb:console terminal \
  -bitb socket.127.0.0.1:8150 \
  -skip_gameinfo -window -sound none
```

In the MAME console:

1. Enter `L` and wait for `ENTRY POINT F000`.
2. Enter `J F000`.
3. Wait while the primary and executive load, then use SADIE's `COMMAND LEVEL`
   menu normally.

The visible test has verified all 14 monitor records, the complete patched
executive, CRC-protected diagnostic records, physical-memory writes, automatic
track/file positioning, the `COMMAND LEVEL` menu, console input, and execution
of the MMU diagnostic. One observed MMU diagnostic result was `no trap on MMU
violation`; that is a diagnostic failure reported by SADIE, not a tape or
serial-transfer error.

## Real hardware

Connect the tape server to the monitor download port and use a separate
terminal on the operator console:

```sh
cd sadie_serial
python3 serve_sadie.py ../tapes/images/sadie-3.5.tap \
  /dev/ttyUSB0 --baud 9600 -v
```

The serial port is opened as 8 data bits, no parity, and 2 stop bits. Follow
the same `L`, `J F000`, and SADIE menu sequence from the hardware console.

## Automated diagnostic runs

Loading is the only slow part of a run: the executive is 27,648 bytes and each
diagnostic 8 to 27 KB, all at 9600 baud, which is about 45 to 70 seconds of
emulated time before a test starts. `make snapshot` pays that once and keeps a
MAME save state taken at `COMMAND LEVEL`; `make diagnostics` restores it and
writes the diagnostic straight into the executive's load window.

```sh
cd sadie_serial
make snapshot                  # once, and again after rebuilding MAME
make diagnostics T=MMUTST      # one test; omit T to run all 36
```

Both drive MAME headless with the operator console on a second socket, so
transcripts land in `build/logs/<NAME>.log` instead of a terminal window. Set
`S8000_MAME` if the `s8000` binary is not at `../../mame_latest/mame/s8000`.

A save state is only valid for the MAME build and slot layout it was taken
with, so both commands use the same configuration and `make snapshot` must be
re-run after either changes. The state itself is generated, not committed.

The tape channel still runs during a diagnostic, primed at that diagnostic's own
track and file, so a test that asks for further records is served normally. The
same thing is available directly:

```sh
python3 serve_sadie.py ../tapes/images/sadie-3.5.tap \
  --listen 127.0.0.1:8150 --serve-only --position 1,22,0 -v
```

A diagnostic is selected the way an operator selects it: `T` at COMMAND LEVEL
opens the chooser, the test's own number picks it, and a bare return accepts the
test line. The chooser's numbering is the manifest's command column, and a
number on a later page can be typed without paging to it. A run ends with
`EXITING <NAME>` and `Hit <CR> to return to COMMAND LEVEL`; the verdict is the
diagnostic's own `ERRORS=` count in its lap summary, not any single message.
MMUTST prints 252 individual `No trap on ...` lines before that total.

Injection is only worth trusting once it has been shown to reproduce a real
tape load. `--compare` runs a diagnostic both ways and diffs what it printed:

```sh
python3 run_diagnostics.py MMUTST --compare
```

`MATCH` means both runs produced the same diagnostic output. `DIFFER` writes
`build/logs/<NAME>.diff`. `--tape` on its own runs only the slow path, which
also works without a save state.

### Verification status and remaining work

The serial loader and injected diagnostic path work. The seven loader unit
tests pass, and an injected MMUTST run reaches its lap summary, prints
`EXITING MMUTST`, and returns to `COMMAND LEVEL`. Its current result under MAME
is `ERRORS=252`: 126 DATA-MMU and 126 STACK-MMU read-only/limit violations do
not trap. Those are emulator results reported by SADIE, not transport or
injection failures.

Injection has also been checked against the real tape path once: MMUTST
matched line for line across all 537 lines of diagnostic output, including the
same subtests, error count, and per-MMU totals. That comparison is not
reproducibly green because the slow reference path is unreliable. Reading a
diagnostic over the tape channel under MAME can NAK until the driver's
ten-error retry limit aborts the load; the executive then reports a transport
failure and skips the test, leaving a transcript that stops at
`CHECK COMPLETE`. Raising `S8000_TURNAROUND` (default 10 ms between packets)
reduces but does not eliminate this problem.

The automated diagnostic campaign is therefore still work in progress. The
snapshot/injection mechanism is usable, but all 36 diagnostics have not been
run and classified, save states must be regenerated for each relevant MAME
build, and the slow tape-reference path still needs reliable packet pacing.
Injection sidesteps that transfer and is currently the dependable way to run
the tests; its reported PASS/FAIL result is the diagnostic's assessment of
MAME, not a claim that the automation itself passed or failed.

## Implementation notes

The extended SIMH image uses private markers `0x70000000..0x70000002` for the
three physical tracks. Position requests select track, logical file, and record
explicitly. Each record begins with `STX` and a two-byte length; the target
answers `C` to start XMODEM-CRC packets. Packets are unpaced and use CRC-16,
duplicate-block acknowledgement, retransmission after `NAK`, and `EOT`.

Two details are required for correct execution:

- The tape replacement contains absolute internal jumps and therefore must be
  linked at `0x2874`. Linking it at zero encoded a jump to `0x0390`, causing a
  reset immediately after the XMODEM `C` request.
- The ROM leaves channel-A receive interrupts enabled, but the serial tape
  transport polls that channel. Before entering SADIE, the serial primary
  disables and clears only channel-A interrupt state. The receiver itself
  remains enabled, so later diagnostic tape requests still work by polling;
  channel B and the operator console are untouched.

### How the executive loads and enters a diagnostic

Recovered by disassembling the unpatched track-0/file-1 executive; all addresses
are logical addresses in the executive, which runs at zero.

| Address | What it does |
| --- | --- |
| `0x14c0` | looks the selected test up in the descriptor table, by name |
| `0x14ca`, `0x14d8` | compares the descriptor's track and file with `0x4936` and `0x4938` |
| `0x14dc` | **skips the load entirely when they already match** |
| `0x14ee` | `position(track, file, record 0)` |
| `0x14f2`–`0x1500` | destination physical segment 0, offset `0x9000`; at most `0x6d60` bytes in 99 records |
| `0x1504` | `read(...)`, then `test r2` for the transport status |
| `0x1562` | `call 0x18f2`, which fills the parameter block at `0x852c` from the menu entry |
| `0x033e` | `call 0x9000` — the diagnostic is called, not jumped to, and returns |

Restoring the state has one MAME-specific trap. A `-state` restore runs before
the autoboot script and discards MAME's pending timers, so the script never
fires at all; a restore requested later from Lua discards them too, stranding
anything parked in `emu.wait()` and cancelling `emu.register_periodic`
callbacks, with no error printed either way. `sadie_inject.lua` therefore asks
for the restore itself and does its work from
`emu.add_machine_post_load_notifier`, the one hook that survives.

Two consequences matter. The loaded byte count is kept only in a local and is
never passed to the diagnostic, so a diagnostic of a different size needs no
other adjustment. And because the serial replacement does not maintain `0x4936`
and `0x4938` — the original tape driver's position words lived inside the region
it replaces — those words can be primed from the host, after which the executive
takes its own already-loaded path and runs whatever is at `0x9000`. That is what
`sadie_inject.lua` does; nothing forces a PC or a register.

The current recovery includes the CRC-valid final block missing from the older
track-0/file-1 capture. See [the tape documentation](../tapes/README.md) for
the source archive, hashes, and generated image format.
