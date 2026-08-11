# 06 — Upgrade Betty from Fedora 43 to Fedora 44

**What to build:** Betty boots the current Fedora Asahi Remix 44 Server release with the expected ARM64 Asahi platform packages.

**Blocked by:** 05 — Validate Betty after the Fedora 43 upgrade.

**Status:** ready-for-agent

- [ ] Refresh Fedora and Asahi metadata for Fedora 44.
- [ ] Stage the reviewed Fedora 44 system-upgrade transaction.
- [ ] Reboot through Fedora’s offline upgrade process.
- [ ] Confirm Betty returns on the expected ARM64 Asahi kernel.
- [ ] Confirm SSH and Tailscale access after the reboot.

## Read-only preflight checks

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'sudo dnf repolist --enabled; sudo dnf history info last'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected baseline is Fedora `43`, `aarch64`, `multi-user.target`, healthy management services, and a clean ticket 05 validation.

## Upgrade commands

Run the metadata refresh and transaction staging with the repository IDs approved in ticket 07. Keep the data drives detached.

```bash
sudo dnf makecache --refresh
sudo dnf system-upgrade download --releasever=44 --allowerasing
sudo dnf history info last
sudo dnf system-upgrade reboot
```

Review the transaction before the reboot. Stop on signing errors, unexpected package removals, or a missing Asahi `kernel-16k` package.

## Post-reboot checks

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'systemctl is-system-running; sudo systemctl --failed --no-legend'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected responses include Fedora `44`, an Asahi `aarch64` kernel, `multi-user`, `running`, no failed units, and active SSH, Tailscale, and Docker services.

## Resources

- [Fedora offline upgrade guide](https://docs.fedoraproject.org/en-US/quick-docs/upgrading-fedora-offline/)
- [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/)
