#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Manage Gertrude's small health sampler over the existing SSH connection."""
import argparse
import base64
import collections
import datetime
import json
import pathlib
import re
import shlex
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
MARKER = '# Managed by gertrude/manage.py'
STATUS = '''set -eu
systemctl is-enabled gertrude-health.timer
systemctl is-active gertrude-health.timer
result=$(systemctl show gertrude-health.service -p Result --value)
[ "$result" = success ] || { echo "ERROR: sampler result=$result"; exit 2; }
cat /run/gertrude-health/status
sample=$(sed -n 's/^timestamp=//p' /run/gertrude-health/status)
age=$(($(date +%s)-sample))
echo "sample_age_seconds=$age"
[ "$age" -ge 0 ] && [ "$age" -le 150 ] || { echo 'ERROR: stale snapshot'; exit 2; }
grep -qx 'incidents=healthy' /run/gertrude-health/status || exit 2
'''
DOCTOR = '''set -eu
uname -a
cat /etc/os-release
free -m
df -h / /nix
systemctl --version | head -1
printf '\\nCgroup controllers: '
cat /sys/fs/cgroup/cgroup.controllers
if [ -r /proc/pressure/memory ]; then cat /proc/pressure/memory; else echo 'PSI: unavailable'; fi
if grep -qw memory /sys/fs/cgroup/cgroup.controllers; then echo 'Memory limits: supported'; else echo 'Memory limits: unavailable'; fi
systemctl is-active ssh tailscaled NetworkManager || true
systemctl list-timers --all --no-pager
systemctl --user list-timers --all --no-pager || true
/nix/var/nix/profiles/default/bin/nix config show | grep -E '^(max-jobs|cores|eval-cores) ='
sudo -n true && echo 'Remote sudo: available without prompt'
'''


def load_config(path):
    with open(path, 'rb') as f:
        config = tomllib.load(f)
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', config['host']):
        raise ValueError('host must be an SSH hostname/alias')
    for key, upper in [('min_available_mib', 100000), ('min_disk_free_percent', 100),
                       ('pressure_full_percent', 100), ('consecutive_samples', 100), ('retention_days', 365)]:
        value = config[key]
        if type(value) is not int or not 1 <= value <= upper:
            raise ValueError(f'invalid {key}')
    services = config['services']
    if not isinstance(services, list) or not services or not all(
        isinstance(s, str) and re.fullmatch(r'[A-Za-z0-9_@.-]+\.service', s) for s in services
    ):
        raise ValueError('services must contain simple systemd .service names')
    return config


def payloads(config):
    conf = '\n'.join(f'{key.upper()}={config[key]}' for key in (
        'min_available_mib', 'min_disk_free_percent', 'pressure_full_percent', 'consecutive_samples', 'retention_days'))
    conf += '\nSERVICES=' + shlex.quote(' '.join(config['services'])) + '\n'
    files = {'/etc/gertrude-health.conf': (conf, '644')}
    for name in ('gertrude-health.service', 'gertrude-health.timer'):
        files['/etc/systemd/system/' + name] = ((ROOT / 'remote' / name).read_text(), '644')
    files['/usr/local/libexec/gertrude-health'] = ((ROOT / 'remote/health-check.sh').read_text(), '755')
    return {path: (content + '\n' + MARKER + '\n', mode) for path, (content, mode) in files.items()}


def deployment(files, apply=False):
    script = '''set -eu
if [ -e /etc/NIXOS ]; then echo 'NixOS detected: manage units through Nix configuration' >&2; exit 1; fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
'''
    # Preflight every destination before performing any mutation.
    for i, (path, (content, mode)) in enumerate(files.items()):
        dest = shlex.quote(path)
        data = base64.b64encode(content.encode()).decode()
        script += f"printf %s {shlex.quote(data)} | base64 -d > \"$tmp/{i}\"\n"
        script += f'''if [ -L {dest} ] || {{ [ -e {dest} ] && ! grep -qF {shlex.quote(MARKER)} {dest}; }}; then
 echo 'Unmanaged destination: {path}' >&2; exit 1
fi
'''
    script += 'changed=0\n'
    for i, (path, (_, mode)) in enumerate(files.items()):
        dest = shlex.quote(path)
        script += f'''if [ -f {dest} ] && cmp -s "$tmp/{i}" {dest} && [ "$(stat -c '%a:%u:%g' {dest})" = '{mode}:0:0' ]; then
 echo 'unchanged {path}'
else
 echo 'change {path}'
 if [ -f {dest} ]; then diff -u {dest} "$tmp/{i}" || true; else diff -u /dev/null "$tmp/{i}" || true; fi
'''
        if apply:
            script += f'''install -d -m 755 {shlex.quote(str(pathlib.PurePosixPath(path).parent))}
 stage=$(mktemp {dest}.XXXXXX)
 install -o root -g root -m {mode} "$tmp/{i}" "$stage"
 mv -f "$stage" {dest}
 changed=1
'''
        script += 'fi\n'
    if apply:
        script += '''if [ "$changed" = 1 ]; then systemctl daemon-reload; fi
if ! systemctl is-enabled --quiet gertrude-health.timer; then systemctl enable gertrude-health.timer; fi
if ! systemctl is-active --quiet gertrude-health.timer; then systemctl start gertrude-health.timer; fi
systemctl start gertrude-health.service
'''
    return script


def ssh_command(host, root=False):
    return ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
               '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
               host, 'sudo -n sh -s' if root else 'sh -s']


def remote(host, script, root=False):
    return subprocess.run(ssh_command(host, root), input=script, text=True, timeout=90).returncode


def history_script(days):
    # Use the remote clock, matching the collector's UTC calendar retention.
    return f'''set -eu
history=/var/lib/gertrude-health/history
[ -d "$history" ] || {{ echo 'No history directory: run apply first' >&2; exit 1; }}
now=$(date +%s)
cutoff=$(date -u -d "@$(( (now / 86400 - {days} + 1) * 86400 ))" +%Y%m%d)
for file in "$history"/*.samples; do
 [ -f "$file" ] && [ ! -L "$file" ] || continue
 name=${{file##*/}}
 case "$name" in
  [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].samples)
   if [ "${{name%.samples}}" -ge "$cutoff" ]; then cat -- "$file"; printf '\\n'; fi ;;
 esac
done
'''


def parse_history(text):
    records = []
    damaged = 0
    for line in text.splitlines():
        if not line:
            continue
        fields = line.split('\t')
        try:
            if fields[0] != 'v1' or fields[-1] != 'end':
                raise ValueError('incomplete record')
            record = dict(field.split('=', 1) for field in fields[1:-1])
            if len(record) != len(fields)-2:
                raise ValueError('duplicate field')
            for key in ('timestamp', 'available_mib', 'swap_free_mib'):
                if int(record[key]) < 0:
                    raise ValueError('negative value')
            if not record['boot_id'] or not record['incidents']:
                raise ValueError('missing context')
            # Validate before rendering dates in summaries.
            datetime.datetime.fromtimestamp(int(record['timestamp']), datetime.timezone.utc)
            records.append(record)
        except (ValueError, KeyError, OverflowError, OSError):
            damaged += 1
    return sorted(records, key=lambda r: int(r['timestamp'])), damaged


def summarize_history(records):
    if not records:
        return 'No complete samples in the requested window.'
    def stamp(record):
        return datetime.datetime.fromtimestamp(int(record['timestamp']), datetime.timezone.utc).isoformat()
    memory = [int(r['available_mib']) for r in records]
    unhealthy = [r for r in records if r['incidents'] != 'healthy']
    incidents = collections.Counter(i for r in unhealthy for i in r['incidents'].strip(',').split(','))
    gaps = [int(b['timestamp'])-int(a['timestamp']) for a, b in zip(records, records[1:])]
    return '\n'.join([
        f'Samples: {len(records)} ({stamp(records[0])} to {stamp(records[-1])})',
        f'Observed boots: {len({r["boot_id"] for r in records})}',
        f'Available RAM MiB: min={min(memory)}, mean={sum(memory)/len(memory):.1f}, max={max(memory)}',
        f'Unhealthy samples: {len(unhealthy)}',
        f'Incident sample counts: {dict(incidents)}',
        f'Largest gap between samples: {max(gaps, default=0)} seconds',
        'Coverage starts at installation; missing intervals are not assumed healthy.',
    ])


def history(host, days, as_json=False):
    result = subprocess.run(ssh_command(host, True), input=history_script(days),
                            text=True, capture_output=True, timeout=90)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')
    if result.returncode:
        return result.returncode
    records, damaged = parse_history(result.stdout)
    if as_json:
        for record in records:
            print(json.dumps(record, sort_keys=True))
    else:
        print(summarize_history(records))
    if damaged:
        print(f'Warning: skipped {damaged} incomplete or invalid history records.', file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=pathlib.Path, default=ROOT / 'config.toml')
    parser.add_argument('command', choices=['doctor', 'plan', 'apply', 'status', 'check', 'logs', 'uninstall', 'history'])
    parser.add_argument('--days', type=int, default=30, help='History window in UTC dates including today (1–365)')
    parser.add_argument('--json', action='store_true', help='Export history as JSON Lines instead of a summary')
    args = parser.parse_args()
    if not 1 <= args.days <= 365:
        parser.error('--days must be between 1 and 365')
    if args.command != 'history' and (args.json or args.days != 30):
        parser.error('--days and --json apply only to history')
    config = load_config(args.config)
    files = payloads(config)
    command = args.command
    if command == 'history': return history(config['host'], args.days, args.json)
    if command == 'doctor': return remote(config['host'], DOCTOR)
    if command in ('plan', 'apply'):
        result = remote(config['host'], deployment(files, command == 'apply'), command == 'apply')
        if result or command == 'plan': return result
        return remote(config['host'], STATUS)
    if command == 'status': return remote(config['host'], STATUS)
    if command == 'check':
        result = remote(config['host'], 'systemctl start gertrude-health.service', True)
        return result or remote(config['host'], STATUS)
    if command == 'logs':
        return remote(config['host'], 'journalctl -u gertrude-health.service -n 40 --no-pager', True)
    # Only remove files with exact content installed by this version/configuration.
    script = deployment(files).split('changed=0')[0]
    for i, path in enumerate(files):
        script += f'[ ! -e {shlex.quote(path)} ] || cmp -s "$tmp/{i}" {shlex.quote(path)} || {{ echo "Modified managed file: {path}"; exit 1; }}\n'
    script += 'if systemctl cat gertrude-health.timer >/dev/null 2>&1; then systemctl disable --now gertrude-health.timer; fi\nif systemctl cat gertrude-health.service >/dev/null 2>&1; then systemctl stop gertrude-health.service; fi\n'
    script += 'rm -f ' + ' '.join(shlex.quote(p) for p in files) + '\nsystemctl daemon-reload\n'
    return remote(config['host'], script, True)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(1)
