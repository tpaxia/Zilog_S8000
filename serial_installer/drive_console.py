#!/usr/bin/env python3
"""Drive the separate S8000 operator console by matching visible prompts."""

import argparse
import socket
import sys
import time


def listen(specification):
    host, separator, port_text = specification.rpartition(":")
    if not separator or not port_text.isdigit():
        raise ValueError("--listen must be HOST:PORT")
    host = host or "127.0.0.1"
    listener = socket.create_server((host, int(port_text)), reuse_port=False)
    print(f"console: waiting on {host}:{port_text}", flush=True)
    connection, address = listener.accept()
    listener.close()
    print(f"console: MAME connected from {address[0]}:{address[1]}", flush=True)
    return connection


def send_paced(connection, data, delay=0.010):
    for byte in data:
        connection.sendall(bytes((byte,)))
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen", default="127.0.0.1:8149")
    parser.add_argument("--transcript", help="append raw console output to this file")
    args = parser.parse_args()

    # Root-only recovery.  /usr remains untouched.  Each response is sent only
    # after its complete prompt has appeared on the separate console channel.
    dialogue = [
        (b"S8000 Monitor", b"L SERIAL\r", "monitor load"),
        (b"ENTRY POINT F000", b"J F000\r", "jump to file 0"),
        (b"Boot\r\n: ", b"ct(0,3)\r", "load mkfs"),
        (b"file sys size: ", b"6000\r", "root size"),
        (b"file system:", b"smd(0,15200)\r", "root device"),
        (b"interleaving factor (m n): ", b"16 256\r", "root interleave"),
        (b"Boot\r\n: ", b"ct(0,4)\r", "load sarestor"),
        (b"factory-supplied Zilog release tape", b"y\r", "factory tape"),
        (b"Do you want instructions", b"n\r", "skip instructions"),
        (b"configuration information in block 0", b"y\r", "use block zero"),
        (b"restor the root filesystem", b"y\r", "restore root"),
        (b"restor the /usr filesystem", b"n\r", "keep /usr"),
        (b"smd type disk:", b"\r", "root type"),
        (b"disk unit 0:", b"\r", "root unit"),
        (b"offset 15200:", b"\r", "root offset"),
        (b"Tape unit number?", b"0\r", "tape unit"),
        (b"OK to restor", b"y\r", "approve restore"),
    ]

    transcript = open(args.transcript, "ab", buffering=0) if args.transcript else None
    matched = bytearray()
    step = 0
    with listen(args.listen) as connection:
        connection.settimeout(1.0)
        while True:
            try:
                data = connection.recv(4096)
            except (TimeoutError, socket.timeout):
                continue
            if not data:
                raise SystemExit("console: connection closed")
            if transcript:
                transcript.write(data)
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
            matched.extend(data)
            if len(matched) > 16384:
                del matched[:-8192]
            while step < len(dialogue) and dialogue[step][0] in matched:
                prompt, answer, description = dialogue[step]
                send_paced(connection, answer)
                printable = answer.rstrip(b"\r") or b"RETURN"
                print(
                    f"\nconsole [{step + 1}/{len(dialogue)}] {description}: "
                    f"sent {printable.decode('ascii')}",
                    flush=True,
                )
                matched.clear()
                step += 1
            if step == len(dialogue):
                print("console: root restore started; monitoring output", flush=True)
                step += 1


if __name__ == "__main__":
    main()
