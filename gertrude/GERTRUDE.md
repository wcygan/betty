# Gertrude

## Nix resource limits (2026-09-27)

Gertrude is a Raspberry Pi 3 Model B with 907 MiB of usable RAM and a 512 MiB
swap file. After it became unresponsive, the previous boot's logs showed
multiple Nix and npm processes, blocked Nix tasks, and out-of-memory events.
Memory pressure is a likely contributor, but the logs do not prove a single
root cause.

Gertrude uses Determinate Nix 3.12.0 (Nix 2.32.1). Its generated
`/etc/nix/nix.conf` must not be edited directly. The following overrides were
added to `/etc/nix/nix.custom.conf` on Gertrude:

```ini
# Keep local builds serial on this 1 GiB Raspberry Pi.
max-jobs = 1
cores = 1
```

Previously, `max-jobs` was `4` and `cores` was `0` (all four CPU cores).
`eval-cores` was already `1`. The original custom file is backed up on
Gertrude as `/etc/nix/nix.custom.conf.bak-20260927`.

`max-jobs = 1` permits one local Nix build at a time. `cores = 1` tells each
builder to use one core, but build scripts must honor that request. These
settings do not cap RAM or prevent separate Nix evaluations and npm processes
from running at the same time. A single large build can still exhaust memory.

### Verification

The custom file was changed while the socket-activated Nix daemon was stopped.
The daemon started six seconds later, so no reboot or further restart was
needed. `nix config show` reported both limits as `1`, and a three-derivation
smoke test completed. Its two independent builds ran one after the other.
There were no new out-of-memory kernel messages after the test; SSH, Tailscale,
and NetworkManager remained active.

Check the effective settings:

```sh
ssh gertrude 'nix config show | grep -E "^(max-jobs|cores|eval-cores) ="'
```

During the next normal Nix update, watch memory and swap in another session:

```sh
ssh gertrude 'vmstat 2'
```

Afterward, check for out-of-memory events in the current boot:

```sh
ssh gertrude 'journalctl -k -b --no-pager | grep -Ei "out of memory|oom-kill|killed process"'
```

The smoke test confirms that Nix builds with the limits and schedules local
builds serially. The next real update is the useful test of whether its memory
use stays within Gertrude's capacity.

References: [Determinate Nix configuration](https://docs.determinate.systems/determinate-nix/)
and [Nix cores and jobs](https://nix.dev/manual/nix/2.32/advanced-topics/cores-vs-jobs).

## Lightweight monitoring (2026-09-29)

The laptop-side CLI is a dependency-free Python script with inline uv metadata.
It uses the existing SSH alias in `config.toml`, with bounded connection and
command timeouts. Gertrude needs no uv, Python environment, or new packages.
Remote installation requires noninteractive sudo; missing access fails clearly.

From the repository root:

```sh
uv run gertrude/manage.py doctor
uv run gertrude/manage.py plan
uv run gertrude/manage.py apply
uv run gertrude/manage.py status
uv run gertrude/manage.py check
uv run gertrude/manage.py logs
uv run gertrude/manage.py history --days 30
uv run gertrude/manage.py history --days 7 --json
uv run --no-project python -m unittest discover -s gertrude
```

`plan` prints content differences. `apply` compares content, ownership, and mode,
atomically replaces changed files, enables the timer if necessary, and runs a
fresh check. Repeat applications preserve identical files. `uninstall` removes
only files matching this checkout's payload and configuration; modified files
require inspection. Uninstall preserves recorded history on disk. SSH failure is nonzero; status exits 2 for a stale or
unhealthy snapshot. A disabled/inactive timer also returns nonzero.

The installer owns four files:

- `/etc/gertrude-health.conf`
- `/etc/systemd/system/gertrude-health.service`
- `/etc/systemd/system/gertrude-health.timer`
- `/usr/local/libexec/gertrude-health`

Existing unmarked files and symlinks are rejected before writes. NixOS hosts are
rejected because their units should be managed declaratively. This installer
is intended for Gertrude's verified Debian/systemd environment.

The timer samples about once a minute. Counters and the latest snapshot live in
`/run/gertrude-health`, reset at reboot, and are atomically replaced. Historical
samples persist separately on disk (see below). The shell sampler logs health
transitions; systemd also logs service start/stop events. No database is
installed. Journal retention remains under the host's existing policy.

Default checks include available memory below 100 MiB for three samples,
memory full-pressure above 5% for three samples when supported, new OOM kills,
filesystem/inode free percentages below 15%, and SSH/Tailscale/NetworkManager
service health. Swap-in/out page deltas and elapsed time are diagnostic context.
Manual checks also count as samples. An OOM event is logged on detection and
appears in that sample; the cumulative boot counter remains visible afterward.
The initial OOM sample establishes a baseline rather than treating old events
as new. Snapshot age over 150 seconds is unhealthy.

### Live findings and verification

On 2026-09-29 Gertrude was running Debian 12, Raspberry Pi kernel
`6.6.51+rpt-rpi-v8`, systemd 252, and aarch64 userspace. Effective Nix values were
`max-jobs = 1`, `cores = 1`, and `eval-cores = 1`.

- PSI files are absent. Pressure monitoring explicitly reports `unavailable`.
- Cgroup v2 exposes `cpuset cpu io pids`, but no memory controller. RAM limits
  cannot be enforced through systemd on this boot.
- Idle available RAM was approximately 640–647 MiB; about 167 MiB swap remained
  occupied, with no swap traffic between the observed samples.
- Zero OOM kills were reported in the current boot.
- `/` and `/nix` share the SD-card filesystem: 86% free by `df` usage and 92%
  free inodes. All three configured services were active.
- The first sampler invocation used approximately 0.21 CPU seconds. Memory
  accounting is unavailable, so no measured peak-RAM claim is made.
- Two applications succeeded; the second reported all four files unchanged.
  Status, manual check, and bounded logs were exercised over SSH.

### Remaining protection gaps

Monitoring does not enforce a RAM budget or serialize upgrades. Enabling the
memory controller/PSI requires separate kernel/boot investigation, potentially
a reboot. No boot parameters or Nix settings were changed by this installation.
The system has APT maintenance timers; no user timers were listed. A managed
Nix upgrade entry point has not been established, and no real upgrade was run.

External outage detection and notifications are not installed. An always-on
host can run the CLI's `status` command and track nonzero results, but needs its
own scheduler, SSH access, incident state, and chosen notification destination.
A sleeping laptop cannot provide that coverage.

The original six local fixture tests covered low-memory debounce/recovery, OOM deltas,
missing PSI, pressure/service failure, disk/inode shortage, stale/failed
snapshots, and configuration rejection. Remote `systemd-analyze verify` passed,
and an automatic timer invocation produced a fresh healthy snapshot with a
61-second interval. The project skill passed the skill validator (PyYAML was
provided through a temporary uv environment on the laptop).


### Durable 30-day history

Each successful check appends a compact, versioned record to
`/var/lib/gertrude-health/history/YYYYMMDD.samples`. UTC dates determine daily
files and retention. `retention_days = 30` in `config.toml` keeps today and the
preceding 29 dates; the first successful sample each day deletes older dated
sample files. Cleanup also runs after reboot or a retention-setting change.
If the host is off, cleanup resumes on its next sample. Unrelated filenames
are left alone. Shortening retention deletes older data on the next check.

Every sample includes its timestamp, boot ID, all health values and service
states, and any incident labels. The sampler flushes the sample file and its
directory through GNU `sync` with named paths (fsync), then publishes the fresh
status. Newly created history directories are also flushed. This adds one
small durable write per check, rather than keeping a five-minute RAM buffer.
A write/flush failure fails the service; it does not publish a fresh snapshot.
Directory permissions are 0750 and sample files are 0640, owned by root.

Records carry a version prefix and an end marker. A leading separator on each
append prevents an interrupted record from merging with the next record. The
reader skips incomplete/invalid records with a warning. This handles torn
appends; it is not an off-machine backup or a guarantee against SD-card failure.

`history --days 30` summarizes the available samples, observed boots, available
RAM, unhealthy sample counts, and the largest gap between recorded samples.
`--days 7` selects today plus six preceding UTC dates. `--json` exports one JSON
object per complete record, with metric values preserved as strings (including
`unavailable`). Retrieval uses remote sudo and the remote clock. The summary
reports its actual coverage; absent samples are not interpreted as healthy.
Manual checks and `apply` also append samples.

Recording began on 2026-09-29 at 12:33:38 UTC; earlier data cannot be backfilled.
The first durable record was 464 bytes, suggesting approximately 20 MB for
43,200 similar samples over 30 days. This is an estimate, not a size quota.
The first durable check consumed approximately 0.22 CPU seconds. No packages,
boot settings, or Nix settings were changed for history support.

Ten fixture tests passed, including UTC retention boundaries and daily cleanup,
recovery after loss of runtime state, torn-tail parsing, history-window queries,
and rejection of fresh status on flush failure. The actual Debian deployment
successfully wrote/flushed its first record, served a summary and JSON export,
and passed systemd unit validation. An isolated temporary directory on Gertrude
also passed retention-cutoff, repeated-append, and runtime-state-loss checks
using the real GNU sync implementation. No physical reboot or power-loss test
was performed.

The live timer subsequently appended a third healthy history record without a
manual check (64 seconds after the previous sample). A final plan reported all
four deployed files unchanged.
