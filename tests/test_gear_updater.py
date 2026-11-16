import sys, unittest, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "gear_updater"))
import sysex, gear_updater, fm1_frames


class T(unittest.TestCase):
    def test_good(self):
        r = sysex.check(bytes([0xF0, 1, 2, 3, 0xF7, 0xF0, 9, 0xF7]))
        self.assertTrue(r.ok); self.assertEqual(r.messages, 2); self.assertEqual(r.largest, 5)

    def test_bad(self):
        for data in (b"", bytes([0xF0, 1, 2]), bytes([1, 2, 0xF7]), bytes([0xF0, 0xF0, 0xF7]), bytes([0xF0, 0x90, 0xF7])):
            self.assertFalse(sysex.check(data).ok, data)

    def test_amidi(self):
        t = "Dir Device    Name\nIO  hw:2,0,0  FM-1 MIDI 1\nI   hw:3,0,0  Other\n"
        p = gear_updater.parse_amidi(t)
        self.assertEqual([x["id"] for x in p], ["hw:2,0,0", "hw:3,0,0"])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "a.syx"); open(f, "wb").write(bytes([0xF0, 1, 0xF7]))
            self.assertEqual(gear_updater.main(["dry-run", f]), 0)
            self.assertEqual(gear_updater.main(["dry-run", f, "--sha256", "00"]), 2)
            self.assertEqual(gear_updater.main(["dry-run", os.path.join(d, "nope.syx")]), 1)

    def test_ports_helpers(self):
        t = "Dir Device    Name\nIO  hw:2,0,0  FM-1 Midi\nI   hw:3,0  Other\n"
        ports = gear_updater.parse_amidi(t)
        self.assertEqual([p["id"] for p in gear_updater.filter_ports(ports, "fm-1")], ["hw:2,0,0"])
        self.assertEqual(len(gear_updater.filter_ports(ports)), 2)
        self.assertIsNone(gear_updater.select_port(ports, "hw:9,0,0"))  # unplugged
        self.assertTrue(gear_updater.valid_port_id("hw:2,0,0"))
        for bad in ("", "hw:2;rm", "plughw:1,0", "hw:", "-d"):
            self.assertFalse(gear_updater.valid_port_id(bad), bad)

    def test_dump_parse(self):
        self.assertEqual(gear_updater.parse_dump("F0 00 32\n45 F7\nxx 1"), bytes([0xF0, 0, 0x32, 0x45, 0xF7]))

    def test_monitor_rejects_bad_port_without_running_amidi(self):
        self.assertEqual(gear_updater.main(["monitor", "--port", "hw:2;ls"]), 1)

    def test_no_write_path(self):
        src = (Path(gear_updater.__file__)).read_text()
        for word in ('"-s"', "--send-hex", "-S", "send_hex"):
            self.assertNotIn(word, src)

    def test_size_and_message_caps(self):
        self.assertFalse(sysex.check(bytes([0xF0] + [1] * 20 + [0xF7]), max_message=10).ok)
        self.assertFalse(sysex.check(bytes([0xF0, 1, 0xF7]), max_file=2).ok)

    def test_dx7_bank_checksum(self):
        payload = bytes(range(64)) * 64
        good = bytes([0xF0, 0x43, 0x00, 0x09, 0x20, 0x00]) + payload + bytes([sysex.dx7_checksum(payload), 0xF7])
        self.assertEqual(len(good), 4104)
        self.assertTrue(sysex.check(good).ok)
        bad = bytearray(good); bad[-2] ^= 1
        r = sysex.check(bytes(bad))
        self.assertFalse(r.ok)
        self.assertIn("checksum", " ".join(r.problems))
        short = good[:-3] + bytes([0xF7])
        self.assertFalse(sysex.check(short).ok)
        self.assertEqual(sysex.dx7_checksum(bytes([1, 2, 3])), 122)

    def test_pack7_documented_header(self):
        # the documented header 00 59 30 + body_length 8 packs to 00 32 41 41 (AL-255 / aroum docs)
        self.assertEqual(fm1_frames.pack7(bytes([0x00, 0x59, 0x30, 0x08, 0x00, 0x00]))[:4], bytes([0x00, 0x32, 0x41, 0x41]))
        for n in range(0, 40):
            d = bytes((i * 37 + 5) & 0xFF for i in range(n))
            w = fm1_frames.pack7(d)
            self.assertTrue(all(b < 0x80 for b in w))
            self.assertEqual(fm1_frames.unpack7(w, n), d)
        with self.assertRaises(ValueError):
            fm1_frames.unpack7(bytes([0x80]), 1)
        with self.assertRaises(ValueError):
            fm1_frames.unpack7(bytes([1]), 5)

    @staticmethod
    def _frame(flash, addr, req, data=b""):
        body = bytes([flash]) + addr.to_bytes(4, "little") + req.to_bytes(3, "little") + data
        dec = bytes([0, 0x59, 0x30]) + (len(data) + 8).to_bytes(3, "little") + body
        dec += bytes([fm1_frames.ota_checksum(body)])
        return bytes([0xF0]) + fm1_frames.pack7(dec) + bytes([0xF7])

    def test_ota_frame_decode(self):
        info, pr = fm1_frames.decode_ota_frame(self._frame(1, 0x1000, 16))
        self.assertEqual(pr, []); self.assertEqual((info["kind"], info["address"], info["requested_length"]), ("request", 0x1000, 16))
        data = bytes(range(481 % 256)) + b"" * 200
        info, pr = fm1_frames.decode_ota_frame(self._frame(1, 0xF0000000, len(data), data))
        self.assertEqual(pr, []); self.assertEqual(info["data"], data); self.assertEqual(info["address"], 0xF0000000)

    def test_ota_frame_rejects(self):
        good = self._frame(1, 0x20, 4, b"abcd")
        bad = bytearray(good); bad[6] ^= 0x01
        info, pr = fm1_frames.decode_ota_frame(bytes(bad))
        self.assertTrue(pr or info is None)
        self.assertIsNone(fm1_frames.decode_ota_frame(b"")[0])
        self.assertIsNone(fm1_frames.decode_ota_frame(bytes([0xF0, 1, 2, 0xF7]))[0])
        self.assertIsNone(fm1_frames.decode_ota_frame(bytes([0xF0, 0x90, 0xF7]))[0])
        # wrong declared length: drop one wire byte pair so length rule fails
        trunc = good[:-3] + good[-1:]
        i2, p2 = fm1_frames.decode_ota_frame(trunc)
        self.assertTrue(p2)
        # flipping a data byte but keeping the old checksum must be caught
        dec_bad = bytearray(fm1_frames.unpack7(good[1:-1], (len(good) - 2) * 7 // 8)); dec_bad[15] ^= 0xFF
        frame = bytes([0xF0]) + fm1_frames.pack7(bytes(dec_bad)) + bytes([0xF7])
        self.assertIn("checksum does not match", fm1_frames.decode_ota_frame(frame)[1])


if __name__ == "__main__":
    unittest.main()
