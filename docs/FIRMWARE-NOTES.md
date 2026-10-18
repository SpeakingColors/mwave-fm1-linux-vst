# FM-1 firmware notes

Collected from community projects (links at the bottom). Check them again before relying on anything here; firmware work can brick a unit.

## How updates work
- Updates go over USB MIDI SysEx only: no DFU, no debug port, no recovery button.
- Only checksum and size checks, no signatures.
- A custom firmware must keep a way back into the bootloader (a SysEx command or a startup button combo). Without it the unit cannot be updated or rolled back.
- Stock updater (M-UPGRADE): to go from stock V15 to a patched V15, go to V14 first, then upgrade. The same route works back.
- A crash during flashing may need hardware tools to recover.

## Known firmwares
- Felucca: GPL-3, 13 engines, web installer (Chrome/Edge) and `tools/fm1_install.py`, with a "Return to official V15" option.
- Baud Girl, Sloop, Jangada, fm1-custom-fw: see their pages.

## Rules for our tool
1. Only flash firmware that keeps bootloader re-entry; try it in the FM-1 emulator first when possible.
2. Default path: custom, then official V15, then another custom, unless that firmware's docs confirm direct switching.
3. Check battery or USB power, block sleep, never flash over Bluetooth, verify the checksum before and after.
4. Do not redistribute M-VAVE stock firmware (copyrighted). The user downloads it from M-VAVE or picks their own file.

## Links
- https://github.com/hugelton/Felucca
- https://github.com/aroum/fm1-custom-fw
- https://github.com/czietz/fm1-firmware-patcher
- https://joakimeriksson.github.io/fm1-emu
