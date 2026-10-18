# FM-1: device notes

What we know, and where it comes from. Everything about the FM-1 here is from community projects (see FIRMWARE-NOTES.md for links) and the project notes of 2026-10-17. We have no M-VAVE manual or MIDI chart in our files, so no CC or SysEx parameter map is written here.

## Confirmed (community sources)
- Firmware updates run only over USB MIDI SysEx. No DFU mode, no debug port, no recovery button.
- Stock updater is M-UPGRADE. A custom firmware must keep a way back into the bootloader.
- Custom firmwares in circulation: Felucca (GPL-3, 13 engines), Baud Girl, Sloop, Jangada, fm1-custom-fw.
- An FM-1 emulator runs in the browser (joakimeriksson.github.io/fm1-emu); it is the safe place to test.

## Missing before an editor can be built
1. M-VAVE manual and MIDI implementation chart (if any exist).
2. Per firmware: which parameters are exposed as CC or SysEx. Felucca and Baud Girl docs are the first places to read.
3. A capture of the stock M-UPGRADE session (USBPcap on Windows) to confirm the SysEx update framing before our tool sends anything.
4. USB MIDI port names on Linux.

## Plan
- Phase 1: firmware-aware helper: detect firmware, back up what can be backed up, guide the safe route (see UPDATER-DESIGN.md).
- Phase 2: parameter editor for the firmwares whose docs give a MIDI map.
