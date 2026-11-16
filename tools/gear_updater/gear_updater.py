#!/usr/bin/env python3
"""gear-updater (early): checks firmware files and lists MIDI ports. It does NOT flash anything yet.

  gear_updater.py ports [--name TEXT] [--json]   list the ALSA MIDI ports (needs `amidi`)
  gear_updater.py monitor --port hw:X,Y,Z [--seconds N]   receive only: print what the device sends
  gear_updater.py dry-run FILE.syx    check the file and print what a flash would involve

This tool never sends anything to a MIDI port: there is no code path that writes to a device.
Flashing is not implemented on purpose: the update protocol of each device must first be captured and
verified (see docs/UPDATER-DESIGN.md). Never redistribute vendor firmware; use your own file."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sysex  # noqa: E402

CHECKLIST = [
    "Power: use mains power or a full battery, and block computer sleep.",
    "Cable: USB only, never Bluetooth.",
    "Backup: save the device's presets and settings first.",
    "Way back: only flash a firmware that keeps a way into the bootloader, and know the route back to the official firmware.",
    "Source: only a file you downloaded yourself from the vendor or the project that made it.",
]


def parse_amidi(text: str):
    ports = []
    for line in text.splitlines():
        m = re.match(r"^\s*([IO]{1,2})\s+(hw:\d+,\d+(?:,\d+)?)\s+(.*?)\s*$", line)
        if m:
            ports.append({"dir": m.group(1), "id": m.group(2), "name": m.group(3)})
    return ports


def list_ports(timeout=10):
    """Scan the ALSA raw MIDI ports. Raises OSError/SubprocessError when amidi is missing or fails.
    Call it again to pick up hot plug and unplug: nothing is cached."""
    out = subprocess.run(["amidi", "-l"], capture_output=True, text=True, timeout=timeout, check=True).stdout
    return parse_amidi(out)


def filter_ports(ports, name=None):
    """Case-insensitive substring filter on the port name."""
    if not name:
        return list(ports)
    n = name.lower()
    return [p for p in ports if n in p["name"].lower()]


def valid_port_id(port: str) -> bool:
    return bool(re.fullmatch(r"hw:\d+(,\d+(,\d+)?)?", port or ""))


def select_port(ports, port_id):
    """Return the port dict for port_id, or None when it is not (or no longer) present."""
    for p in ports:
        if p["id"] == port_id:
            return p
    return None


def parse_dump(text: str):
    """Parse `amidi -d` output (lines of hex bytes) to bytes. Tolerates a trailing partial line."""
    out = bytearray()
    for tok in text.split():
        if re.fullmatch(r"[0-9A-Fa-f]{2}", tok):
            out.append(int(tok, 16))
    return bytes(out)


def cmd_ports(a):
    try:
        ports = filter_ports(list_ports(), a.name)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Could not run amidi ({e}). Install alsa-utils.", file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(ports, indent=2))
    else:
        for p in ports:
            print(f"{p['id']:10} {p['dir']:3} {p['name']}")
    if not ports:
        print("No matching MIDI ports. Is the device connected and powered?", file=sys.stderr)
        return 3
    return 0


def cmd_monitor(a):
    """Receive only. Re-scans ports first so an unplugged device is reported instead of hanging."""
    if not valid_port_id(a.port):
        print(f"Not a port id like hw:2,0,0: {a.port!r}", file=sys.stderr)
        return 1
    secs = max(1, min(int(a.seconds), 300))
    try:
        port = select_port(list_ports(), a.port)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Could not run amidi ({e}). Install alsa-utils.", file=sys.stderr)
        return 1
    if port is None:
        print(f"Port {a.port} is not present (unplugged or renumbered). Run `ports` again.", file=sys.stderr)
        return 3
    if "I" not in port["dir"]:
        print(f"Port {a.port} has no input direction, nothing to receive.", file=sys.stderr)
        return 3
    try:
        r = subprocess.run(["amidi", "-p", a.port, "-d", "-t", str(secs)], capture_output=True, text=True, timeout=secs + 10)
    except subprocess.TimeoutExpired:
        print("amidi did not stop in time; it was killed.", file=sys.stderr)
        return 4
    except OSError as e:
        print(f"Could not run amidi ({e}).", file=sys.stderr)
        return 1
    data = parse_dump(r.stdout)
    if r.returncode not in (0, 1) and not data:
        print(f"amidi failed ({r.returncode}): {r.stderr.strip()}. The device may have been unplugged.", file=sys.stderr)
        return 3
    print(f"Received {len(data)} bytes in {secs} s from {a.port}.")
    if data:
        print(data.hex(" "))
        msgs, problems = sysex.split_messages(data)
        print(f"SysEx messages: {len(msgs)}")
        for pr in problems:
            print(f"NOTE: {pr}")
    print("Nothing was sent to any device.")
    return 0


def cmd_dry_run(a):
    p = Path(a.file)
    if not p.is_file():
        print(f"No such file: {p}", file=sys.stderr)
        return 1
    try:
        rep = sysex.check(p.read_bytes())
    except OSError as e:
        print(f"Could not read {p}: {e}", file=sys.stderr)
        return 1
    print(f"File: {p.name}\nSize: {rep.size} bytes\nSHA-256: {rep.sha256}\nSysEx messages: {rep.messages} (largest {rep.largest} bytes)")
    for n in rep.notes:
        print(f"Note: {n}")
    if a.sha256 and a.sha256.lower() != rep.sha256:
        rep.problems.append("SHA-256 does not match the value you gave")
    for pr in rep.problems:
        print(f"PROBLEM: {pr}")
    print("\nBefore any flash:")
    for c in CHECKLIST:
        print(f"  - {c}")
    print("\nResult:", "file looks well formed (this does not prove it is the right firmware)" if rep.ok else "NOT OK, do not flash")
    print("Nothing was sent to any device.")
    return 0 if rep.ok else 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("ports"); pp.add_argument("--name", help="only ports whose name contains this text (e.g. FM-1)"); pp.add_argument("--json", action="store_true"); pp.set_defaults(fn=cmd_ports)
    m = sub.add_parser("monitor"); m.add_argument("--port", required=True); m.add_argument("--seconds", type=int, default=10); m.set_defaults(fn=cmd_monitor)
    d = sub.add_parser("dry-run"); d.add_argument("file"); d.add_argument("--sha256", help="expected SHA-256 from the source"); d.set_defaults(fn=cmd_dry_run)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
