# 05 — Validate Betty after the Fedora 43 upgrade

**What to build:** A known-good Fedora 43 headless baseline before the next release transition.

**Blocked by:** 04 — Upgrade Betty from Fedora 42 to Fedora 43.

**Status:** complete

- [x] Confirm the operating system, kernel, architecture, and boot target.
- [x] Confirm no failed systemd units remain.
- [x] Confirm SSH, Tailscale, Docker, and Netdata are healthy.
- [x] Confirm storage and service configuration remain intact.
- [x] Record DNF transaction history and any migration warnings.

## Read-only validation commands

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'systemctl is-system-running; sudo systemctl --failed --no-legend'
ssh betty 'sudo systemctl is-active sshd tailscaled docker; docker ps --format "table {{.Names}}\\t{{.Status}}"'
ssh betty 'findmnt /; findmnt /boot /boot/efi; findmnt /mnt/immich /mnt/externalhd || true'
ssh betty 'sudo dnf history list | head -n 8'
ssh betty 'curl -fsS http://127.0.0.1:19999/api/v1/info | head -c 200'
```

Expected evidence is Fedora `43`, `aarch64`, `multi-user.target`, system state `running`, no failed units, healthy management services, internal NVMe root and boot mounts, no detached data mounts, and a Netdata API response.

Do not restart Immich or reconnect the data drives during this validation. That belongs after the upgrade chain is complete and the recovery evidence is preserved.

## Completion evidence

The main host check ran at `2026-08-12T15:46:12Z`.

```text
Fedora: 43
Kernel: 7.1.6-400.asahi.fc43.aarch64+16k
Architecture: aarch64
Default target: multi-user.target
System state: running
System failed units: none
sshd: active
tailscaled: active
docker: active
netdata: active
```

Netdata returned a local API response from `127.0.0.1:19999`. Docker has the
expected non-Immich containers, `vmsingle` and `glance`. Immich remains stopped.

The root, boot, and EFI filesystems remain on the internal NVMe device:

```text
/         /dev/nvme0n1p6[/root]
/boot     /dev/nvme0n1p5
/boot/efi /dev/nvme0n1p4
```

No mount exists at `/mnt/immich` or `/mnt/externalhd`. DNF history entry 24
records the completed Fedora 43 system-upgrade transaction.

### Resolved migration warning

At `2026-08-12T15:46:53 CDT`, the user service `clawdbot-gateway.service` was
loaded but in `activating (auto-restart)`. Its latest exit status was 1 and it
had 430 restarts. Its configured Node entrypoint did not exist. The user
requested removal of Clawdbot.

At `2026-08-12T16:44:02Z`, the gateway service was stopped and disabled. The
only discovered Clawdbot artifacts were its user unit and enablement link. Both
were removed. No installed global Clawdbot package or user data path was found.

The final check at `2026-08-12T16:44:19Z` showed no Clawdbot unit, path, or
Node process. The system and user service managers showed no failed units.
SSH, Tailscale, Docker, and Netdata remained active.

## Troubleshooting commands

```bash
ssh betty 'sudo journalctl -b -p warning..alert --no-pager'
ssh betty 'sudo dnf history info last'
ssh betty 'sudo systemctl status sshd tailscaled docker --no-pager'
```

Save output with the ticket if any check fails. A failed unit or missing SSH/Tailscale path blocks ticket 06.

## Resources

- [systemctl manual](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
- [Docker Compose logs](https://docs.docker.com/reference/cli/docker/compose/logs/)
