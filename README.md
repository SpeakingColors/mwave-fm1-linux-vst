# M-VAVE FM-1 for Linux 🐈

<img src="assets/icon.svg" width="96" align="right" alt="icon">

Controller plugin for the M-VAVE FM-1 on Linux.

## Status
Early work in progress. No FM-1 controller plugin yet (no MIDI map in our files).

**Gear updater, first piece:** `tools/gear_updater/` can list MIDI ports and check a firmware `.syx` file (framing, size, SHA-256) with a safety checklist. It does **not** flash anything: the FM-1 update protocol still has to be captured and verified. Run `python3 tools/gear_updater/gear_updater.py dry-run FILE.syx`. A separate `gear-updater` repo does not exist yet; this folder is its seed.

<p align="center">
  <a href="https://ko-fi.com/studio87"><img src="https://img.shields.io/badge/Support_Studio_87-on_Ko--fi-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white" alt="Support Studio 87 on Ko-fi"></a>
</p>

☕ Free and open source, made by one person. If it helps your music, a coffee on [Ko-fi](https://ko-fi.com/studio87) keeps it coming. 💜

## Docs
- [Roadmap](ROADMAP.md)
- [Device notes](docs/DEVICE-NOTES.md)
- [Firmware notes](docs/FIRMWARE-NOTES.md)
- [Updater design](docs/UPDATER-DESIGN.md) (gear updater, FM-1 first)

## License
AGPL-3.0-or-later, see [LICENSE](LICENSE).

Not affiliated with or endorsed by any hardware maker named here. All trademarks belong to their owners.
