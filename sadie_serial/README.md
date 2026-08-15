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

The current recovery includes the CRC-valid final block missing from the older
track-0/file-1 capture. See [the tape documentation](../tapes/README.md) for
the source archive, hashes, and generated image format.
