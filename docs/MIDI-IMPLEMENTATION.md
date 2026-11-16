# FM-1: MIDI implementation (verified map)

Device: M-VAVE (Cuvave) FM-1, a pocket DX7-style FM synthesizer (JieLi AC791N). The repo name says "mwave"; the device is the M-VAVE FM-1, not a Waldorf microWave.

Read this first: **the official M-VAVE MIDI control reference was not available to us.** The awesome-fm-1 list links an official file "FM-1 MIDI EN.docx" (hosted on yms-file-store.oss-cn-hongkong.aliyuncs.com, `software/releaseNote/firmware/`) and says it holds the CC map with effects on their own MIDI channel. Our network blocked that host on 2026-11-16, so we could not read it. **No CC, NRPN or program-change number is written here.** When someone downloads that file from m-vave.com/download (or the link above) and checks it, this document is where its table goes, with the file name, version and page.

Status column meaning: `documented` = stated in a manufacturer document (none yet), `community` = stated in a community reverse-engineering document we read, not captured by us, `captured` = from the owner's device (none yet), `untested` = nothing confirms it on the owner's unit. Nothing in this file is hardware verified.

## Sources read (2026-11-16)
| Short name | Document | Kind |
|---|---|---|
| AL-255 OTA | AL-255/FM-1-RE, `docs/io/11-ota-protocol.md` (no version number; says it is byte-verified against ALSA-seq captures of M-UPGRADE under Wine, and a Windows reflash on 2026-09-04) | community |
| aroum RE | aroum/fm1-custom-fw, `REVERSE_ENGINEERING.md` sections 2 and 4 | community |
| KingParamount | KingParamount/fm1-factory-presets, `docs/protocol-and-provenance.md` | community |
| awesome-fm-1 | cicloid/awesome-fm-1 README (links only) | list |

Not opened: the manuals.plus and device.report copies of the user manual, and the SynthHub CC chart pages (SynthHub says its own chart is "real unit not yet checked"; that host was also unreachable). A search summary said the manual lists USB MIDI, BLE MIDI, 3.5 mm MIDI IN (31250 baud), note on/off with velocity, pitch bend, control change, program change 0 to 127 and DX7-style bank import. That is a search summary, not a page we read, so it is not in the tables below.

## Transport
| Item | Value | Source | Status |
|---|---|---|---|
| USB MIDI, normal mode | VID:PID `4c4a:c755`, "FM-1 Midi" composite (USB MIDI + audio) | AL-255 OTA | community |
| USB MIDI, OTA loader | VID:PID `4d4a:4155`, "ota-FM-1" | AL-255 OTA | community |
| Linux ALSA port name | seen as `USB Composite Device MIDI 1` in a Wine capture on the author's machine | AL-255 OTA | untested here |
| 3.5 mm TRS MIDI IN, 31250 baud, input only | | aroum RE section 1.2 | community |
| Firmware V16 (2026-10-21): 8 parts on MIDI channels 1 to 8 | | aroum RE section 1.1 | community |
| The unit accepts DX7 bank SysEx but has no export of its own ("receives SysEx but never sends it", apart from identify replies and acknowledgements) | | KingParamount | community |

## SysEx (all manufacturer bytes `00 32`)
| Message | Bytes | Direction | Source | Status |
|---|---|---|---|---|
| Identify query | `F0 00 32 45 00 00 00 40 7F F7` | host to FM-1 | AL-255 OTA, KingParamount | community, untested here |
| Identify reply | `F0 00 32 45 58 01 00 00 23 4D 5A 44 ...` 41 bytes, 34 bytes after 7-bit unpack, holds `FM-1_014` or `FM-1_015` style id | FM-1 to host | AL-255 OTA, aroum RE 4.1 | community |
| Enter-upgrade command | `F0 22 24 35 7F F7` | host to FM-1 | AL-255 OTA, aroum RE 4.2 | community; **starts a firmware update, this tool never sends it** |
| Read request / data response frame | after unpack: `00 59 30`, body_length u24le, flash_type u8, address u32le, requested_length u24le, data, checksum | both | AL-255 OTA | community |
| Frame checksum | `~sum(bytes from flash_type through data) & 0xFF`; frame valid only if `body_length + 7 == decoded length` | | AL-255 OTA | community |
| 7-bit packing | continuous LSB-first 8-to-7 bit stream | | AL-255 OTA, aroum RE 4.3 | community |
| Finish | device asks address `0xF0000000`, length 8; host answers `"success\0"` | | AL-255 OTA | community |
| Preset restore, setup message | `F0 00 32 05 29 00 00 40 02 00 <slot> 00 00 20 <ck> F7`, slot 00/20/40/60 | host to FM-1 | KingParamount | community; meaning unknown, do not send |
| Preset restore, voice block | `F0 00 32 09 41 40 00 40 02 00 <slot> ...` 1190 bytes, slot 00 to 78 step 08; checksum method not known | host to FM-1 | KingParamount | community; do not send |
| Acknowledgement | `F0 00 32 01 08 00 00 00 00 7F 01 F7` | FM-1 to host | KingParamount | community |
| DX7 32-voice bank import | `F0 43 00 09 20 00 <4096 bytes> <checksum> F7`, checksum `(128 - (sum & 0x7F)) & 0x7F` | host to FM-1 | KingParamount (standard Yamaha format) | community; import overwrites the stored banks |
| Stock updater timing | 2000 ms pause after the upgrade command, 8000 ms receive timeout, reply to `0xE0000000` (verify done) with `success\0` | | AL-255 OTA (decompiled M-UPGRADE worker) | community |

The aroum RE document says the device answers only to parameter id `0x40` on the identify query; other ids give no reply. The "syscmd" commands 17 to 48 in AL-255 OTA are normal-mode device control; that document warns that guessed requests (especially 33 to 36 and 48) must not be sent to the only recoverable device. We do not send them.

## CC, NRPN, program change
Nothing verified. Community pages exist (SynthHub charts for stock V15 and custom firmwares, the Felucca emulator mapping CC 20 to 27 to panel knobs) but they are firmware specific, one is marked unchecked by its own author, and we have not read the official table. Left unmapped on purpose.

## What the updater in this repo does with this
- `tools/gear_updater/fm1_frames.py` decodes frames that were *received* (7-bit unpack, length rule, checksum). It has no request builder and the tool has no send path.
- `tools/gear_updater/sysex.py` checks `.syx` files, including the DX7 bank length and checksum.
- `gear_updater.py monitor` listens to one port and prints bytes; it sends nothing.
- Identify is a plain query, but it is still a write to the device, so it stays unsent until the owner confirms it is wanted and we have a capture from the owner's unit.
