---
name: gertrude
description: Operate Gertrude over SSH using this repository's uv harness. Use for health checks, monitoring installation or repair, and investigating Nix upgrade overload on the Raspberry Pi.
---

# Gertrude operations

Run from the repository root. Read `gertrude/GERTRUDE.md` for incident history,
installed monitoring, and verified limitations. The laptop runs Python through
uv; Gertrude runs the deployed shell sampler and systemd timer.

## Inspect and diagnose

Start with `uv run gertrude/manage.py doctor` and
`uv run gertrude/manage.py status`. Use `check` for a fresh sample and `logs`
for recent sampler events. Use `history --days 30` for trends and `history
--days 7 --json` for complete exported records. A nonzero status can mean an unhealthy or stale
sample, a disabled timer, or SSH failure; distinguish the output before acting.
Read `gertrude/config.toml` for the host, thresholds, and expected services.

Gertrude is Debian with Determinate Nix, not NixOS. On the verified September
2026 boot, PSI and the cgroup memory controller are unavailable. Recheck these
capabilities before proposing MemoryHigh/MemoryMax; configuration text alone
is not proof of enforcement. Existing swap occupancy is not evidence of active
thrashing: compare available memory, swap deltas, and OOM events.

## Install or repair monitoring

For authorized setup work, edit the repository payloads, run
`uv run --no-project python -m unittest discover -s gertrude`, then run `plan`,
`apply`, and `plan` again. Completion requires a healthy fresh sample and a
second plan showing all files unchanged. The harness uses existing SSH keys
and noninteractive sudo. If sudo is unavailable, report that specific blocker;
keep credentials out of scripts and tracked files.

The installer owns only its marked files. Resolve an unmanaged-file conflict
by examining ownership rather than overwriting it. `uninstall` removes only
files matching the current payload/config; inspect drift before removal.
Uninstall preserves `/var/lib/gertrude-health/history`. Retention keeps UTC
calendar dates including today; reducing `retention_days` deletes older samples
on the next check. History starts at installation, and gaps are not evidence of
health. An incomplete-record warning means a torn/invalid record was skipped;
inspect surrounding timestamps and sampler failures. Writes are flushed before
a fresh status is published. Do not interpret a failed history write as a
successful check merely because a previous snapshot remains readable.

## Nix overload

Check effective `max-jobs`, `cores`, and `eval-cores` with `doctor`. Determinate
Nix owns `/etc/nix/nix.conf`; overrides belong in `/etc/nix/nix.custom.conf`.
The current serial build settings do not bound memory or serialize independent
Nix clients and npm processes. Inspect the actual upgrade entry point before
wrapping it. Any future containment must cover evaluation/client processes
and daemon-side builds. Keep kernel boot changes, reboot, and a real package
upgrade explicit in the requested scope.

Monitoring is local observation, not external notification. An always-on host
and an alert destination still need configuration for unattended outage alerts.
Report installed changes, measured overhead, health evidence, and any remaining
protection gaps. Avoid claiming an upgrade is safe based only on an idle check.
