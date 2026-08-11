# 05 — Validate Betty after the Fedora 43 upgrade

**What to build:** A known-good Fedora 43 headless baseline before the next release transition.

**Blocked by:** 04 — Upgrade Betty from Fedora 42 to Fedora 43.

**Status:** ready-for-agent

- [ ] Confirm the operating system, kernel, architecture, and boot target.
- [ ] Confirm no failed systemd units remain.
- [ ] Confirm SSH, Tailscale, Docker, and Netdata are healthy.
- [ ] Confirm storage and service configuration remain intact.
- [ ] Record DNF transaction history and any migration warnings.

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
