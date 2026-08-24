#!/usr/bin/env python3
"""Boot SADIE under MAME once and save the COMMAND LEVEL state for reuse.

The state is the only slow step in a diagnostic run: the executive is 27,648
bytes over a 9600-baud link.  Every later run restores this state instead, so
the machine configuration recorded here is also the one run_diagnostics.py must
use -- a MAME save state is only valid for the slot layout it was taken with.
"""

import argparse
import sys
import time

import mame_harness as harness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default="sadie-cmdlevel")
    parser.add_argument("--machine", default="s8000")
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--settle", type=float, default=8,
                        help="seconds to let the menu finish printing before saving")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    harness.STATE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    transcript_path = harness.HERE / "build" / f"{args.state}-console.log"
    trigger = harness.HERE / "build" / f"{args.state}.trigger"
    trigger.unlink(missing_ok=True)
    tape_listener = harness.listen(harness.TAPE_PORT, "tape")
    console_listener = harness.listen(harness.CONSOLE_PORT, "console")

    tape = harness.TapeChannel(tape_listener, verbose=args.verbose)
    tape.start()

    command = harness.mame_command(args.machine, script=harness.HERE / "sadie_snapshot.lua")
    process = harness.start_mame(command, environment={
        "SADIE_STATE": args.state,
        "SADIE_TRIGGER": str(trigger),
    })

    output = harness.MameOutput(process)
    output.start()
    console = harness.Console(harness.accept(console_listener, "console"),
                              transcript=open(transcript_path, "wb"))

    deadline = time.monotonic() + args.timeout
    step = 0
    at_command_level = None
    saved = False
    try:
        while time.monotonic() < deadline and not saved:
            console.pump()
            step = harness.run_dialogue(console, harness.BOOT_DIALOGUE, step)
            if tape.error:
                raise SystemExit(f"tape channel failed: {tape.error}")
            # SADIE reads its own configuration off track 2 after the executive
            # arrives, so only the console says when it is really idle.  Give it
            # a moment after the prompt for the menu to finish printing.
            if at_command_level is None and harness.COMMAND_LEVEL in console.text:
                at_command_level = time.monotonic()
                print("\nconsole: COMMAND LEVEL reached", file=sys.stderr, flush=True)
            if (at_command_level and not trigger.exists() and
                    time.monotonic() - at_command_level >= args.settle):
                trigger.touch()
                print("console: asked MAME to save", file=sys.stderr, flush=True)
            saved = output.saw("sadie-snapshot: ready")
            if not saved and process.poll() is not None:
                raise SystemExit("MAME exited before the state was saved\n"
                                 + output.text())
    finally:
        process.terminate()
        trigger.unlink(missing_ok=True)

    if not saved:
        reason = ("COMMAND LEVEL never appeared" if at_command_level is None
                  else "the state was never written")
        raise SystemExit(f"{reason} within {args.timeout:.0f}s; see {transcript_path}")
    print(f"\nsaved {harness.STATE_DIRECTORY}/{args.machine}/{args.state}.sta")
    print(f"console transcript: {transcript_path}")


if __name__ == "__main__":
    main()
