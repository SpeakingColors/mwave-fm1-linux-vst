"""SysEx file checks for the gear updater. Pure Python, standard library only. Nothing here talks to a device."""
import hashlib
from dataclasses import dataclass, field


# Safety caps for files handed to the dry run. These are our own limits, not device limits.
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_MESSAGE_BYTES = 1024 * 1024


@dataclass
class SysexReport:
    size: int
    sha256: str
    messages: int = 0
    largest: int = 0
    problems: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.problems and self.messages > 0


def split_messages(data: bytes):
    """Split a .syx byte string into F0 ... F7 messages. Returns (messages, problems)."""
    msgs, problems, start = [], [], None
    for i, b in enumerate(data):
        if b == 0xF0:
            if start is not None:
                problems.append(f"F0 at byte {i} before the previous message ended")
            start = i
        elif b == 0xF7:
            if start is None:
                problems.append(f"F7 at byte {i} without a start")
            else:
                msgs.append(data[start:i + 1]); start = None
        elif b & 0x80:
            problems.append(f"status byte {b:#04x} at byte {i} inside or between SysEx messages")
        elif start is None:
            problems.append(f"data byte at {i} outside a message")
    if start is not None:
        problems.append("file ends inside a message (no F7)")
    return msgs, problems


def dx7_checksum(payload: bytes) -> int:
    """Yamaha DX7 bulk-dump checksum: (128 - (sum & 0x7F)) & 0x7F over the data bytes.
    Source: KingParamount/fm1-factory-presets docs/protocol-and-provenance.md (community), standard DX7 format."""
    return (128 - (sum(payload) & 0x7F)) & 0x7F


def check_dx7_bank(msg: bytes):
    """If msg looks like a DX7 32-voice bulk dump (F0 43 0n 09 20 00 <4096 bytes> <checksum> F7), verify
    length and checksum. Returns None if it is not that kind of message, else a list of problems (empty = ok)."""
    if len(msg) < 6 or msg[1] != 0x43 or msg[3] != 0x09:
        return None
    problems = []
    if len(msg) != 4104:
        problems.append(f"DX7 bank message is {len(msg)} bytes, expected 4104")
        return problems
    if msg[4:6] != bytes([0x20, 0x00]):
        problems.append("DX7 bank byte count field is not 20 00 (4096)")
    if dx7_checksum(msg[6:6 + 4096]) != msg[6 + 4096]:
        problems.append("DX7 bank checksum does not match")
    return problems


def check(data: bytes, max_file: int = MAX_FILE_BYTES, max_message: int = MAX_MESSAGE_BYTES) -> SysexReport:
    if len(data) > max_file:
        return SysexReport(size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                           problems=[f"file is larger than the safety cap of {max_file} bytes, not parsed"])
    msgs, problems = split_messages(data)
    if not data:
        problems.append("file is empty")
    rep = SysexReport(size=len(data), sha256=hashlib.sha256(data).hexdigest(), messages=len(msgs),
                      largest=max((len(m) for m in msgs), default=0), problems=problems)
    for i, m in enumerate(msgs):
        if len(m) > max_message:
            problems.append(f"message {i} is {len(m)} bytes, over the safety cap of {max_message}")
        dx = check_dx7_bank(m)
        if dx is None:
            continue
        rep.notes.append(f"message {i}: DX7 32-voice bank " + ("(checksum ok)" if not dx else "(problem)"))
        problems.extend(f"message {i}: {x}" for x in dx)
    return rep
