# 06 — Upgrade Betty from Fedora 43 to Fedora 44

**What to build:** Betty boots the current Fedora Asahi Remix 44 Server release with the expected ARM64 Asahi platform packages.

**Blocked by:** 05 — Validate Betty after the Fedora 43 upgrade.

**Status:** complete

- [x] Refresh Fedora and Asahi metadata for Fedora 44.
- [x] Stage the reviewed Fedora 44 system-upgrade transaction.
- [x] Reboot through Fedora’s offline upgrade process.
- [x] Confirm Betty returns on the expected ARM64 Asahi kernel.
- [x] Confirm SSH and Tailscale access after the reboot.

## Read-only preflight checks

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'sudo dnf repolist --enabled; sudo dnf history info last'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected baseline is Fedora `43`, `aarch64`, `multi-user.target`, healthy management services, and a clean ticket 05 validation.

## Upgrade commands

Keep the data drives detached. For this upgrade, disable `1password` and
`tailscale-stable`. Ticket 03 excluded both repositories after signing errors.
Ticket 07 will verify their official keys before it enables them again.

```bash
sudo dnf --disablerepo=1password --disablerepo=tailscale-stable makecache --refresh
sudo dnf --disablerepo=1password --disablerepo=tailscale-stable system-upgrade download --releasever=44 --allowerasing
sudo dnf history info last
sudo dnf system-upgrade reboot
```

Review the transaction before the reboot. Stop on signing errors, unexpected package removals, or a missing Asahi `kernel-16k` package.

The user approved the Fedora 44 offline reboot after `dnf system-upgrade
status` confirmed the prepared transaction. The staged command excludes
`1password` and `tailscale-stable`.

## Post-reboot checks

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'systemctl is-system-running; sudo systemctl --failed --no-legend'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected responses include Fedora `44`, an Asahi `aarch64` kernel, `multi-user`, `running`, no failed units, and active SSH, Tailscale, and Docker services.

## Completion evidence

The user approved the Fedora 44 offline reboot. At `2026-08-12T18:27:24Z`,
Betty reported Fedora `44`, kernel
`7.1.6-400.asahi.fc44.aarch64+16k`, architecture `aarch64`, and
`multi-user.target`. The system state was `running`. SSH, Tailscale, and
Docker were all `active`. `systemctl --failed --no-legend` returned no units.
Both Immich drive mount points remained absent.

DNF transaction `25` completed with status `Ok` at `2026-08-12 13:24:21`.
It recorded the approved Fedora 44 staging command with `1password` and
`tailscale-stable` disabled.

## Resources

- [Fedora offline upgrade guide](https://docs.fedoraproject.org/en-US/quick-docs/upgrading-fedora-offline/)
- [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/)
