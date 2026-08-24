#!/usr/bin/env python3
"""Shared plumbing for driving SADIE under MAME: tape channel, console, MAME."""

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import serve_sadie

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
MAME = Path(os.environ.get("S8000_MAME", REPO.parent / "mame_latest" / "mame" / "s8000"))
# MAME resolves a ROM path as <rompath>/<setname>/, so it needs the directory
# holding the s8000 set, not the loose files in the repository's own roms/.
ROMS = Path(os.environ.get("S8000_ROMS", MAME.parent / "roms"))
MAME_CFG = REPO / "serial_installer" / "mame_cfg"
TAPE = REPO / "tapes" / "images" / "sadie-3.5.tap"
STATE_DIRECTORY = HERE / "build" / "sta"

TAPE_PORT = 8150
CONSOLE_PORT = 8151


def listen(port, what):
    listener = socket.create_server(("127.0.0.1", port))
    listener.settimeout(60)
    print(f"{what}: waiting on 127.0.0.1:{port}", file=sys.stderr, flush=True)
    return listener


def accept(listener, what):
    connection, address = listener.accept()
    listener.close()
    print(f"{what}: MAME connected from {address[0]}:{address[1]}",
          file=sys.stderr, flush=True)
    return connection


class TapeChannel(threading.Thread):
    """Serve the SADIE tape on SIO0 channel A for as long as MAME runs."""

    daemon = True

    # Packets are unpaced, so the gap between them is all that keeps the
    # emulated SIO from being overrun.  Too small and records NAK until the
    # driver's ten-error limit aborts the load; the executive then reports a
    # transport failure and skips the test without running it.
    TURNAROUND = float(os.environ.get("S8000_TURNAROUND", 0.010))

    def __init__(self, listener, serve_only=False, position=None, verbose=False):
        super().__init__(name="sadie-tape")
        self.listener = listener
        self.serve_only = serve_only
        self.position = position
        self.verbose = verbose
        self.error = None
        self.ready = threading.Event()

    def run(self):
        try:
            tracks = serve_sadie.read_sadie_tap(TAPE)
            server = serve_sadie.SadieServer(
                tracks,
                serve_sadie.DEFAULT_PRIMARY.read_bytes(),
                serve_sadie.DEFAULT_EXECUTIVE.read_bytes(),
                self.verbose, turnaround_delay=self.TURNAROUND)
            if self.position:
                server.position(*self.position)
            connection = accept(self.listener, "tape")
            with connection.makefile("rwb", buffering=0) as port:
                if not self.serve_only:
                    serve_sadie.send_monitor_image(
                        port, serve_sadie.DEFAULT_BOOTSTRAP.read_bytes(),
                        self.verbose)
                    print("tape: bootstrap loaded", file=sys.stderr, flush=True)
                self.ready.set()
                server.serve(port)
        except Exception as error:            # reported by the caller on exit
            self.error = error
        finally:
            self.ready.set()


class Console:
    """The operator console on SIO0 channel B, matched against visible text."""

    def __init__(self, connection, transcript=None, echo=True):
        self.connection = connection
        self.connection.settimeout(0.5)
        self.transcript = transcript
        self.echo = echo
        self.seen = bytearray()
        self.text = bytearray()

    def pump(self):
        try:
            data = self.connection.recv(4096)
        except (TimeoutError, socket.timeout):
            return b""
        if not data:
            raise EOFError("console: connection closed")
        if self.transcript:
            self.transcript.write(data)
            self.transcript.flush()
        if self.echo:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        self.seen.extend(data)
        self.text.extend(data)
        if len(self.seen) > 65536:
            del self.seen[:-32768]
        return data

    def expect(self, needle, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if needle in self.seen:
                return True
            self.pump()
        return False

    def send(self, reply, delay=0.010):
        for byte in reply:
            self.connection.sendall(bytes((byte,)))
            time.sleep(delay)
        self.seen.clear()

    def drain(self, quiet_for, timeout):
        """Read until nothing new arrives for quiet_for seconds, or timeout."""
        deadline = time.monotonic() + timeout
        last = time.monotonic()
        while time.monotonic() < deadline:
            if self.pump():
                last = time.monotonic()
            elif time.monotonic() - last >= quiet_for:
                return True
        return False


# The monitor download only starts once "L" is typed on the console, and the
# relocated primary only runs once "J F000" follows it.  Prompt text is matched
# against what the machine actually prints; adjust here if a banner differs.
BOOT_DIALOGUE = (
    (b"S8000 Monitor", b"L\r", "monitor download"),
    (b"ENTRY POINT F000", b"J F000\r", "enter the serial primary"),
)
COMMAND_LEVEL = b"COMMAND LEVEL"


def run_dialogue(console, dialogue, step):
    """Answer the next prompt of a dialogue if it has appeared; returns step."""
    if step < len(dialogue) and dialogue[step][0] in console.seen:
        _, reply, description = dialogue[step]
        console.send(reply)
        print(f"\nconsole: {description}", file=sys.stderr, flush=True)
        step += 1
    return step


def mame_command(machine="s8000", state=None, script=None, extra=()):
    command = [
        str(MAME), machine,
        "-rp", str(ROMS),
        "-cfg_directory", str(MAME_CFG),
        "-state_directory", str(STATE_DIRECTORY),
        # With two null_modems MAME numbers the bitbangers; cha:tty0 is created
        # before chb:console, so bitb1 is the tape and bitb2 the console.
        "-slot_cpu:cpu_a:sio0:cha:tty0", "null_modem",
        "-bitb1", f"socket.127.0.0.1:{TAPE_PORT}",
        "-slot_cpu:cpu_a:sio0:chb:console", "null_modem",
        "-bitb2", f"socket.127.0.0.1:{CONSOLE_PORT}",
        "-skip_gameinfo", "-video", "none", "-sound", "none", "-nothrottle",
    ]
    if state:
        command += ["-state", state]
    if script:
        command += ["-autoboot_delay", "1", "-autoboot_script", str(script)]
    return command + list(extra)


def start_mame(command, environment=None, log=None):
    print("mame: " + " ".join(command), file=sys.stderr, flush=True)
    merged = dict(os.environ, **(environment or {}))
    return subprocess.Popen(command, env=merged, stdout=log or subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)


class MameOutput(threading.Thread):
    """Collect MAME's stdout off the main thread so the console keeps pumping."""

    daemon = True

    def __init__(self, process, echo=True):
        super().__init__(name="mame-stdout")
        self.process = process
        self.echo = echo
        self.lines = []
        self.closed = False

    def run(self):
        for line in self.process.stdout:
            self.lines.append(line)
            if self.echo:
                print("mame| " + line.rstrip(), file=sys.stderr, flush=True)
        self.closed = True

    def saw(self, marker):
        return any(marker in line for line in tuple(self.lines))

    def text(self):
        return "".join(tuple(self.lines))
