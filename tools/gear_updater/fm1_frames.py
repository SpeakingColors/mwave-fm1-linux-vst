"""Read-only decoder for FM-1 SysEx frames as documented by the community. Pure Python, nothing here
talks to a device and there is no builder for requests: this module only checks bytes that were received.

Sources (community reverse engineering, not an M-VAVE document; see docs/MIDI-IMPLEMENTATION.md):
  AL-255/FM-1-RE docs/io/11-ota-protocol.md ("Read-request / data-response framing")
  aroum/fm1-custom-fw REVERSE_ENGINEERING.md section 4.3
Status of everything here: community-documented, NOT confirmed on the owner's unit."""

MANUFACTURER_PREFIX = bytes([0x00, 0x32])  # first two bytes after F0 in every FM-1 frame in the sources above


def unpack7(wire: bytes, nbytes: int) -> bytes:
    """Continuous LSB-first 7-bit to 8-bit unpack (7 wire bytes carry 49 bits, i.e. 8 data bytes need
    ceil(64/7) = 10 wire bytes in the sources' scheme, 8 per 7). Returns the first nbytes, or raises."""
    if any(b & 0x80 for b in wire):
        raise ValueError("wire byte with bit 7 set")
    acc = bits = 0
    out = bytearray()
    for b in wire:
        acc |= b << bits
        bits += 7
        while bits >= 8:
            out.append(acc & 0xFF)
            acc >>= 8
            bits -= 8
    if len(out) < nbytes:
        raise ValueError(f"only {len(out)} bytes available, {nbytes} requested")
    return bytes(out[:nbytes])


def pack7(data: bytes) -> bytes:
    """Inverse of unpack7. The last partial septet is zero padded (the padding value is our assumption)."""
    acc = bits = 0
    out = bytearray()
    for b in data:
        acc |= b << bits
        bits += 8
        while bits >= 7:
            out.append(acc & 0x7F)
            acc >>= 7
            bits -= 7
    if bits:
        out.append(acc & 0x7F)
    return bytes(out)


def ota_checksum(decoded_from_flashtype: bytes) -> int:
    """~sum(bytes from flash_type through the end of data) & 0xFF (AL-255 doc, current form)."""
    return (~sum(decoded_from_flashtype)) & 0xFF


def decode_ota_frame(msg: bytes):
    """Decode one received F0 ... F7 frame of the read-request/data-response form.
    Returns (info, problems). Layout after unpacking:
      00 59 30 | body_length:u24le | flash_type:u8 | address:u32le | requested_length:u24le | data | checksum
    Rules from the source: body_length + 7 must equal the decoded packet length; checksum covers flash_type..data."""
    problems = []
    if len(msg) < 6 or msg[0] != 0xF0 or msg[-1] != 0xF7:
        return None, ["not a complete F0 ... F7 message"]
    wire = msg[1:-1]
    if any(b & 0x80 for b in wire):
        return None, ["byte with bit 7 set inside the message"]
    # 7 bits per wire byte; the decoded length is floor(7*len/8) and may include padding bits we cannot see
    n = (len(wire) * 7) // 8
    try:
        dec = unpack7(wire, n)
    except ValueError as e:
        return None, [str(e)]
    if dec[:3] != bytes([0x00, 0x59, 0x30]):
        return None, ["header is not 00 59 30 (not a read-request/data-response frame)"]
    if len(dec) < 3 + 3 + 1 + 4 + 3 + 1:
        return None, ["frame too short"]
    body_len = int.from_bytes(dec[3:6], "little")
    if body_len + 7 != len(dec):
        problems.append(f"body_length {body_len} + 7 does not equal decoded length {len(dec)}")
        return None, problems
    flash_type = dec[6]
    address = int.from_bytes(dec[7:11], "little")
    req_len = int.from_bytes(dec[11:14], "little")
    data = dec[14:-1]
    chk = dec[-1]
    if ota_checksum(dec[6:-1]) != chk:
        problems.append("checksum does not match")
    if body_len != len(data) + 8:
        problems.append("body_length does not match the data length")
    kind = "request" if not data else "response"
    if kind == "response" and req_len != len(data):
        problems.append(f"requested_length {req_len} differs from data length {len(data)}")
    info = {"kind": kind, "flash_type": flash_type, "address": address, "requested_length": req_len, "data": data}
    return info, problems
