# FM-1: device notes

What we know, and where it comes from. Everything about the FM-1 here is from community projects (see FIRMWARE-NOTES.md for links) and the project notes of 2026-10-17. We have no M-VAVE manual or MIDI chart in our files, so no CC parameter map is written here. The SysEx framing that community projects documented is collected, with sources and status, in [MIDI-IMPLEMENTATION.md](MIDI-IMPLEMENTATION.md). The official MIDI reference ("FM-1 MIDI EN.docx", linked from m-vave.com/download) is the first thing to read next.

## Official M-VAVE documents (found, not yet read by us)
- User manual PDF, hosted by M-VAVE: https://manualf.oss-cn-hongkong.aliyuncs.com/manual/MIDI-KEYBOARD/FM-1-manual.pdf . In the review for this note the PDF text could not be extracted, so we have NOT confirmed what it says about MIDI.
- Firmware download page: https://www.m-vave.com/product?id=fm-1 (not opened in the review).
- Press reports (matrixsynth.com, July 2026, V15 firmware) say V15 added a "FM-1 MIDI CC Control Parameter Guide". We could not find or read that guide. Source: secondhand report only, UNVERIFIED.
- No CC, NRPN or SysEx value from M-VAVE is recorded in this repo. Any value added later needs a tag: "official: <document and page>" or "owner capture". Nothing here is tested on hardware.

## Confirmed (community sources)
- Firmware updates run only over USB MIDI SysEx. No DFU mode, no debug port, no recovery button.
- Stock updater is M-UPGRADE. A custom firmware must keep a way back into the bootloader.
- Custom firmwares in circulation: Felucca (GPL-3, 13 engines), Baud Girl, Sloop, Jangada, fm1-custom-fw.
- An FM-1 emulator runs in the browser (joakimeriksson.github.io/fm1-emu); it is the safe place to test.

## Missing before an editor can be built
1. Read the M-VAVE manual and the V15 MIDI CC guide (see above) and copy the CC table with page numbers.
2. Per firmware: which parameters are exposed as CC or SysEx. Felucca and Baud Girl docs are the first places to read.
3. A capture of the stock M-UPGRADE session (USBPcap on Windows) to confirm the SysEx update framing before our tool sends anything.
4. USB MIDI port names on Linux (a Wine capture by a community author shows `USB Composite Device MIDI 1`; not seen on our unit).

## Plan
- Phase 1: firmware-aware helper: detect firmware, back up what can be backed up, guide the safe route (see UPDATER-DESIGN.md).
- Phase 2: parameter editor for the firmwares whose docs give a MIDI map.
