# Roadmap: M-VAVE FM-1 controller

Controller for the M-VAVE FM-1 that handles its custom firmwares (Felucca and others).

## Next
- [x] Device notes and updater design written
- [ ] Study the firmware formats (capture M-UPGRADE)
- [ ] Preset and parameter editor
- [ ] Firmware update tool (shared with the gear updater idea)

## Every cat plugin
- Draw through `catui::RenderGate` so meters and animations stop when the window is not in front (audio, automation and MIDI keep running)
- Settings page with MIDI filters on by default, selectable preset/backup folders, UI size reset to 100%

## Gear updater (seed in tools/gear_updater)
- [x] SysEx file check, port listing, dry run, unit tests
- [ ] Capture M-UPGRADE with USBPcap and document the FM-1 update framing
- [ ] Flash and rollback for the FM-1 only after the above is verified
- [ ] Move to its own `gear-updater` repo (needs creating on GitHub)
