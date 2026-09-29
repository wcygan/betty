"""Run with uv run --no-project python -m unittest discover -s gertrude."""
import os
import pathlib
import subprocess
import tempfile
import sys
import shutil
import unittest
import manage


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.proc = self.root / 'proc'
        self.proc.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name, body in {
            'flock': 'exit 0',
            'systemctl': 'echo active',
            'df': "printf 'Filesystem Blocks Used Available Capacity Mounted\\nfixture 100 10 90 10%% /\\n'",
        }.items():
            path = self.bin / name
            path.write_text('#!/bin/sh\n' + body + '\n')
            path.chmod(0o755)
        # Model GNU date/sync on macOS; production uses Debian coreutils.
        date = self.bin / 'date'
        date.write_text(f"#!{sys.executable}\n" + '''import datetime, os, sys
args = sys.argv[1:]
now = int(os.environ.get('FIXTURE_TIME', '1790685000'))
if args == ['+%s']:
    print(now)
else:
    timestamp = int(args[args.index('-d')+1][1:])
    print(datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).strftime(args[-1][1:]))
''')
        date.chmod(0o755)
        sync = self.bin / 'sync'
        sync.write_text('#!/bin/sh\nexit "${FIXTURE_SYNC_EXIT:-0}"\n')
        sync.chmod(0o755)
        boot = self.proc / 'sys/kernel/random'
        boot.mkdir(parents=True)
        (boot / 'boot_id').write_text('fixture-boot-1\n')
        config = self.root / 'config' 
        config.write_text('MIN_AVAILABLE_MIB=100\nMIN_DISK_FREE_PERCENT=15\nPRESSURE_FULL_PERCENT=5\nCONSECUTIVE_SAMPLES=3\nRETENTION_DAYS=30\nSERVICES=ssh.service\n')
        self.env = dict(os.environ, GERTRUDE_CONFIG=str(config), GERTRUDE_PROC=str(self.proc),
                        GERTRUDE_STATE=str(self.root / 'state'), GERTRUDE_HISTORY=str(self.root / 'history'), PATH=str(self.bin)+':'+os.environ['PATH'])
        self.memory(600)
        self.vm(0)

    def memory(self, mib):
        (self.proc / 'meminfo').write_text(f'MemAvailable: {mib*1024} kB\nSwapFree: 200000 kB\n')

    def vm(self, oom):
        (self.proc / 'vmstat').write_text(f'oom_kill {oom}\npswpin 0\npswpout 0\n')

    def sample(self):
        result = subprocess.run(['sh', str(manage.ROOT / 'remote/health-check.sh')],
                                env=self.env, capture_output=True, text=True, check=True)
        return (self.root / 'state/status').read_text(), result.stdout

    def test_low_memory_debounce_and_recovery(self):
        self.memory(50)
        for _ in range(2): self.assertIn('incidents=healthy', self.sample()[0])
        self.assertIn('incidents=low-memory,', self.sample()[0])
        self.assertEqual(self.sample()[1], '')
        self.memory(600)
        status, log = self.sample()
        self.assertIn('incidents=healthy', status)
        self.assertIn('low-memory, -> healthy', log)

    def test_oom_delta_and_missing_pressure(self):
        self.vm(8)
        self.assertIn('oom_kills_since_sample=0', self.sample()[0])
        self.vm(9)
        status, _ = self.sample()
        self.assertIn('incidents=oom-kill,', status)
        self.assertIn('memory_full_avg60=unavailable', status)
        self.assertIn('incidents=healthy', self.sample()[0])

    def test_pressure_and_service_failure(self):
        (self.proc / 'pressure').mkdir()
        (self.proc / 'pressure/memory').write_text('full avg10=8.0 avg60=6.0 avg300=1.0 total=1\n')
        self.sample(); self.sample()
        self.assertIn('incidents=memory-pressure,', self.sample()[0])
        (self.bin / 'systemctl').write_text('#!/bin/sh\necho failed\nexit 3\n')
        self.assertIn('service:ssh.service,', self.sample()[0])

    def test_disk_and_inode_shortage(self):
        (self.bin / 'df').write_text("#!/bin/sh\nprintf 'Filesystem Blocks Used Available Capacity Mounted\\nfixture 100 95 5 95%% /\\n'\n")
        status, _ = self.sample()
        self.assertIn('disk:/,', status)
        self.assertIn('inodes:/,', status)

    def test_stale_and_failed_status(self):
        (self.bin / 'systemctl').write_text('#!/bin/sh\necho success\n')
        path = self.root / 'status'
        script = manage.STATUS.replace('/run/gertrude-health/status', str(path))
        def status(timestamp, incidents='healthy'):
            path.write_text(f'timestamp={timestamp}\nincidents={incidents}\n')
            return subprocess.run(['sh', '-c', script], env=self.env, capture_output=True).returncode
        now = 1790685000
        self.assertEqual(status(now), 0)
        self.assertEqual(status(now-200), 2)
        self.assertEqual(status(now, 'low-memory,'), 2)
        (self.bin / 'systemctl').write_text('#!/bin/sh\necho timeout\n')
        self.assertEqual(status(now), 2)

    def history_records(self):
        return manage.parse_history(''.join(p.read_text() for p in sorted((self.root / 'history').glob('*.samples'))))

    def test_history_survives_runtime_reset_and_torn_tail(self):
        self.sample()
        path = next((self.root / 'history').glob('*.samples'))
        with path.open('a') as f:
            f.write('v1\ttimestamp=123\tavailable_mib=')
        shutil.rmtree(self.root / 'state')  # /run is lost at reboot
        (self.proc / 'sys/kernel/random/boot_id').write_text('fixture-boot-2\n')
        self.sample()
        records, damaged = self.history_records()
        self.assertEqual(len(records), 2)
        self.assertEqual(damaged, 1)
        self.assertEqual({r['boot_id'] for r in records}, {'fixture-boot-1', 'fixture-boot-2'})
        self.assertIn('Observed boots: 2', manage.summarize_history(records))

    def test_retention_utc_boundary_and_daily_pruning(self):
        directory = self.root / 'history'
        directory.mkdir()
        # Fixture clock: 2026-09-29. Keep Aug 31 through Sep 29 inclusive.
        for name in ('20260830.samples', '20260831.samples', '20260928.samples', 'notes.txt'):
            (directory / name).write_text('old fixture')
        self.sample()
        self.assertFalse((directory / '20260830.samples').exists())
        self.assertTrue((directory / '20260831.samples').exists())
        self.assertTrue((directory / 'notes.txt').exists())
        # Once-per-day pruning leaves this artificial expired file until tomorrow.
        (directory / '20260830.samples').write_text('late file')
        self.sample()
        self.assertTrue((directory / '20260830.samples').exists())
        self.env['FIXTURE_TIME'] = str(1790685000 + 86400)
        self.sample()
        self.assertFalse((directory / '20260830.samples').exists())
        self.assertFalse((directory / '20260831.samples').exists())
        self.assertTrue((directory / '20260928.samples').exists())
        self.assertTrue((directory / '20260930.samples').exists())

    def test_durability_failure_does_not_publish_fresh_status(self):
        self.sample()
        before = (self.root / 'state/status').read_text()
        self.env['FIXTURE_TIME'] = str(1790685000 + 60)
        self.env['FIXTURE_SYNC_EXIT'] = '1'
        with self.assertRaises(subprocess.CalledProcessError):
            self.sample()
        self.assertEqual((self.root / 'state/status').read_text(), before)

    def test_history_window_and_empty_summary(self):
        self.assertIn('No complete samples', manage.summarize_history([]))
        self.sample()
        self.env['FIXTURE_TIME'] = str(1790685000 + 86400)
        self.sample()
        script = manage.history_script(1).replace('/var/lib/gertrude-health/history', str(self.root / 'history'))
        result = subprocess.run(['sh', '-c', script], env=self.env, text=True, capture_output=True, check=True)
        records, damaged = manage.parse_history(result.stdout)
        self.assertEqual(damaged, 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(int(records[0]['timestamp']), 1790685000 + 86400)

    def test_invalid_config_rejected(self):
        content = (manage.ROOT / 'config.toml').read_text().replace('ssh.service', "ssh.service;id")
        path = self.root / 'bad.toml'
        path.write_text(content)
        with self.assertRaises(ValueError): manage.load_config(path)


if __name__ == '__main__': unittest.main()
