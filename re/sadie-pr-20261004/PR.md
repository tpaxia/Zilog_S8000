# zilog/s8000: fix issues found by running SADIE diagnostics

This fixes System 8000 behavior exercised by SADIE 3.5. The Z8010 changes correct descriptor-counter wrapping, distinguish address drive from access suppression, retain suppression until the instruction boundary, and keep protection checks active when translation is bypassed. The CPU boards now capture the correct trap addresses and acknowledge interrupts consistently. Parity RAM generates and checks parity, with memory errors delivered through the board's enabled, latched NMI interface.

The SMDC changes fix queued completion interrupts, implement format/read-format operations, and correct geometry checks and transfers across tracks and cylinders. The HPCPU SCC disconnects external RxD from the receiver during internal loopback.

The Z8001 change preserves bit 15 of loaded PC segment words in LDAR and saved return addresses, matching measurements on physical hardware.

To test, use the [SADIE tape and serial loader](https://github.com/tpaxia/Zilog_S8000/tree/main/sadie_serial). The repository includes the tape image, compiled loader binaries in `sadie_serial/build/`, Python tape server and serial configuration. With Python 3 installed, start the tape server first and leave it running:

```sh
git clone https://github.com/tpaxia/Zilog_S8000.git
export S8000_ASSETS="$PWD/Zilog_S8000"
python3 "$S8000_ASSETS/sadie_serial/serve_sadie.py" \
  "$S8000_ASSETS/tapes/images/sadie-3.5.tap" --listen 127.0.0.1:8150 -v
```

From the MAME build directory, start CPU-A with the tape on virtual serial channel A and the console on channel B. Set the asset path in this terminal too. The supplied configuration selects 9600 baud, 8-N-2 and the segmented-OS jumper required by SADIE:

```sh
export S8000_ASSETS=/absolute/path/to/Zilog_S8000
./s8000 s8000 -noreadconfig -rp /absolute/path/to/mame/roms \
  -cfg_directory "$S8000_ASSETS/sadie_serial/mame_cfg" \
  -slot_cpu:cpu_a:sio0:cha:tty0 null_modem \
  -slot_cpu:cpu_a:sio0:chb:console terminal \
  -bitb socket.127.0.0.1:8150 -skip_gameinfo -window -sound none
```

Enter `L`, wait for `ENTRY POINT F000`, then enter `J F000`. At SADIE's `COMMAND LEVEL` prompt, enter `T`, choose `24` for MMUTST or `23` for MEMTEST, and press return to accept the test line. Allow several minutes for loading and execution. For HPCPU, use `s8000s2` and replace the slot prefixes `cpu_a:sio0` with `hpcpu:scc`. Its monitor requires `L SERIAL`; after downloading, enter `R R7`, enter `0001` at the value prompt, then `Q` at the next register prompt before `J F000`. To test SCC internal loopback, select `21`, enter `A` followed by return at port selection, then press `R` **without return** at the readiness prompt.

## AI disclosure

These changes (and the accompanying test fixtures) have been developed with strong assistance from AI coding agents (codex sol 6.0 and opus 5.5) and with humans leading the ideas, testing, and debugging.
