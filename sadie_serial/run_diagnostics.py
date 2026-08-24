#!/usr/bin/env python3
"""Run SADIE 3.5 diagnostics under MAME from a saved COMMAND LEVEL state.

Each diagnostic is written straight into the executive's load window instead of
being read over the tape channel, so a run costs a state restore rather than the
27,648-byte executive plus an 8-27 KB diagnostic at 9600 baud.  See
sadie_inject.lua for why priming the executive's tape position is enough to make
it skip the load and run what is already there.

The tape channel still runs, primed at the diagnostic's own track and file, so a
diagnostic that asks for further records is served normally.

--tape loads the slow way instead, and --compare runs both and diffs the two
transcripts.  Until a diagnostic has been compared, the injected result is only
as trustworthy as the assumption that injection reproduces a real load.
"""

import argparse
import csv
import difflib
import re
import sys
import time

import mame_harness as harness

TESTS = harness.REPO / "tapes" / "extracted" / "sadie-3.5" / "tests"
MANIFEST = TESTS / "manifest.tsv"

# COMMAND LEVEL offers letters, not test numbers: "T" opens the test chooser,
# the test's own number selects it, and a bare return accepts the test line as
# shown.  The numbering matches the manifest's command column.
CHOOSER = b"CHOOSE A TEST OR CONTROL LINE"
TEST_LINE = b"RESET TEST LINE"
# Every menu ends with this prompt.  Waiting for it before replying matters:
# the banner alone arrives well before the options, and answering early races
# the rest of the menu onto the wire.
PROMPT = b"Enter your choice ]=>"
# Must be the full sentence.  Menus offer "^  return to COMMAND LEVEL" as an
# option, so the bare phrase matches before the diagnostic has run at all.
COMPLETION = b"Hit <CR> to return to COMMAND LEVEL"
# Where the run itself begins.  Anchoring the captured body on this rather than
# on a stream offset keeps a --compare diff free of the menu banner, which
# otherwise splits across reads at a different byte in each run.
RUN_START = b"CHECKING TEST LIST"

# A finished diagnostic prints its own lap summary; that error count is the
# verdict, not any individual message.  MMUTST for instance prints hundreds of
# "No trap on READ ONLY violation" lines and then ERRORS=252.
LAP_ERRORS = re.compile(rb"ERRORS\s*=\s*(\d+)")


def load_manifest():
    with MANIFEST.open() as handle:
        rows = [row for row in csv.DictReader(handle, delimiter="\t")
                if row["kind"] == "diagnostic"]
    return {row["name"]: row for row in rows}


def select(manifest, names):
    if not names:
        return list(manifest.values())
    chosen = []
    for name in names:
        row = manifest.get(name.upper())
        if row is None:
            raise SystemExit(f"unknown diagnostic {name!r}; "
                             f"choose from {', '.join(sorted(manifest))}")
        chosen.append(row)
    return chosen


def classify(body):
    if COMPLETION not in body:
        return "TIMEOUT", "no completion prompt; it may be waiting for input"
    counts = [int(match.group(1)) for match in LAP_ERRORS.finditer(body)]
    if not counts:
        return "DONE", "completed without printing an error summary"
    if counts[-1] == 0:
        return "PASS", "completed with ERRORS=0"
    return "FAIL", f"completed with ERRORS={counts[-1]}"


def transcript_path(name, tape_mode):
    path = harness.HERE / "build" / "logs" / f"{name}{'-tape' if tape_mode else ''}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def select_and_watch(console, command, args):
    """Walk the COMMAND LEVEL menu and capture only what the diagnostic prints."""
    console.send(b"T\r")
    if not (console.expect(CHOOSER, timeout=args.menu_timeout) and
            console.expect(PROMPT, timeout=args.menu_timeout)):
        return "ERROR", "the test chooser never appeared", b""
    console.send(f"{command}\r".encode("ascii"))
    if not (console.expect(TEST_LINE, timeout=args.menu_timeout) and
            console.expect(PROMPT, timeout=args.menu_timeout)):
        return "ERROR", f"test {command} was not accepted by the chooser", b""

    # Everything from here is the diagnostic's own output, which is what a
    # --compare run diffs; the menu navigation above is not part of it.
    start = len(console.text)
    console.send(b"\r")
    if console.expect(COMPLETION, timeout=args.timeout):
        # expect() returns on the matching byte, leaving the rest of the prompt
        # in flight; let it land so the captured tail is the same every run.
        console.drain(quiet_for=1, timeout=10)
    else:
        console.drain(quiet_for=args.quiet, timeout=args.quiet * 2)
    body = bytes(console.text[start:])
    anchor = body.find(RUN_START)
    if anchor > 0:
        body = body[anchor:]
    verdict, detail = classify(body)
    return verdict, detail, body


def run_one(row, args):
    """Restore the COMMAND LEVEL state and inject the diagnostic."""
    name, command = row["name"], row["command"]
    track, file_number = int(row["track"]), int(row["file"])
    image = TESTS / f"test-{int(command):02d}-{name}.bin"
    if not image.exists():
        return "SKIP", f"{image.name} is missing", b""

    tape_listener = harness.listen(harness.TAPE_PORT, "tape")
    console_listener = harness.listen(harness.CONSOLE_PORT, "console")
    tape = harness.TapeChannel(tape_listener, serve_only=True,
                               position=(track, file_number, 0),
                               verbose=args.verbose)
    tape.start()

    # No -state here: sadie_inject.lua restores it, because a -state restore
    # runs before the autoboot script and cancels it outright.
    process = harness.start_mame(
        harness.mame_command(args.machine,
                             script=harness.HERE / "sadie_inject.lua"),
        environment={
            "SADIE_IMAGE": str(image),
            "SADIE_STATE": args.state,
            "SADIE_TRACK": str(track),
            "SADIE_FILE": str(file_number),
        })
    output = harness.MameOutput(process, echo=args.verbose)
    output.start()

    transcript = open(transcript_path(name, False), "wb")
    console = harness.Console(harness.accept(console_listener, "console"),
                              transcript=transcript, echo=args.verbose)
    try:
        deadline = time.monotonic() + args.timeout
        while not output.saw("sadie-inject: ready"):
            console.pump()
            if process.poll() is not None:
                return "ERROR", "MAME exited during injection\n" + output.text(), b""
            if time.monotonic() > deadline:
                return "ERROR", "injection never completed\n" + output.text(), b""
        return select_and_watch(console, command, args)
    finally:
        process.terminate()
        transcript.close()
        if tape.error:
            print(f"tape channel: {tape.error}", file=sys.stderr, flush=True)


def run_one_from_tape(row, args):
    """Boot from scratch and let the executive load the diagnostic itself.

    Slow on purpose: this is the reference a --compare run is diffed against, so
    it uses no save state and no injection.
    """
    name, command = row["name"], row["command"]
    tape_listener = harness.listen(harness.TAPE_PORT, "tape")
    console_listener = harness.listen(harness.CONSOLE_PORT, "console")
    tape = harness.TapeChannel(tape_listener, verbose=args.verbose)
    tape.start()

    process = harness.start_mame(harness.mame_command(args.machine))
    output = harness.MameOutput(process, echo=args.verbose)
    output.start()

    transcript = open(transcript_path(name, True), "wb")
    console = harness.Console(harness.accept(console_listener, "console"),
                              transcript=transcript, echo=args.verbose)
    try:
        deadline = time.monotonic() + args.boot_timeout
        step = 0
        while step < len(harness.BOOT_DIALOGUE):
            console.pump()
            step = harness.run_dialogue(console, harness.BOOT_DIALOGUE, step)
            if process.poll() is not None:
                return "ERROR", "MAME exited during boot\n" + output.text(), b""
            if time.monotonic() > deadline:
                return "ERROR", f"boot stalled at step {step}", b""
        # SADIE prints its banner, reads its configuration off track 2, and only
        # then offers the prompt.  Typing at the banner loses the keystroke.
        remaining = max(deadline - time.monotonic(), 1)
        if not (console.expect(harness.COMMAND_LEVEL, timeout=remaining) and
                console.expect(PROMPT, timeout=args.menu_timeout)):
            return "ERROR", f"no COMMAND LEVEL prompt within {args.boot_timeout:.0f}s", b""
        return select_and_watch(console, command, args)
    finally:
        process.terminate()
        transcript.close()
        if tape.error:
            print(f"tape channel: {tape.error}", file=sys.stderr, flush=True)


def normalise(body):
    return [line.rstrip() for line in body.decode("ascii", "replace").splitlines()
            if line.strip()]


def compare(row, args):
    """Run a diagnostic both ways and diff what it printed."""
    name = row["name"]
    injected_verdict, injected_detail, injected = run_one(row, args)
    if injected_verdict in ("SKIP", "ERROR"):
        return injected_verdict, f"injected run: {injected_detail}"
    tape_verdict, tape_detail, from_tape = run_one_from_tape(row, args)
    if tape_verdict in ("SKIP", "ERROR"):
        return tape_verdict, f"tape run: {tape_detail}"

    difference = list(difflib.unified_diff(
        normalise(from_tape), normalise(injected),
        fromfile=f"{name} from tape", tofile=f"{name} injected", lineterm=""))
    if not difference:
        return "MATCH", f"injected and tape runs agree ({injected_verdict})"
    path = transcript_path(name, False).with_suffix(".diff")
    path.write_text("\n".join(difference) + "\n")
    return "DIFFER", f"{len(difference)} diff lines; see {path.name}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tests", nargs="*", help="diagnostic names; default all")
    parser.add_argument("--state", default="sadie-cmdlevel")
    parser.add_argument("--machine", default="s8000")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--boot-timeout", type=float, default=900,
                        help="seconds to reach COMMAND LEVEL in --tape mode")
    parser.add_argument("--quiet", type=float, default=10,
                        help="seconds of console silence that ends a stalled run")
    parser.add_argument("--menu-timeout", type=float, default=60,
                        help="seconds to wait for each COMMAND LEVEL prompt")
    parser.add_argument("--tape", action="store_true",
                        help="load from the tape channel instead of injecting")
    parser.add_argument("--compare", action="store_true",
                        help="run each test both ways and diff the transcripts")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    state_file = harness.STATE_DIRECTORY / args.machine / f"{args.state}.sta"
    if not (args.tape or state_file.exists()):
        raise SystemExit(f"no save state at {state_file}; run make_snapshot.py first")

    results = []
    for row in select(load_manifest(), args.tests):
        print(f"\n=== {row['name']} (command {row['command']}) ===",
              file=sys.stderr, flush=True)
        if args.compare:
            verdict, detail = compare(row, args)
        elif args.tape:
            verdict, detail, _ = run_one_from_tape(row, args)
        else:
            verdict, detail, _ = run_one(row, args)
        results.append((row["name"], verdict, detail))
        print(f"{row['name']}: {verdict} -- {detail.splitlines()[0]}",
              file=sys.stderr, flush=True)

    print("\n" + "=" * 60)
    for name, verdict, detail in results:
        print(f"{verdict:8} {name:10} {detail.splitlines()[0]}")
    print(f"transcripts in {harness.HERE / 'build' / 'logs'}")
    return 1 if any(verdict in ("FAIL", "ERROR", "DIFFER")
                    for _, verdict, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
