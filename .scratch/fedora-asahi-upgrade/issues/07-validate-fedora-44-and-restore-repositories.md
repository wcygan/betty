# 07 — Validate Fedora 44 and restore repository access

**What to build:** A stable Fedora Asahi Remix 44 Server baseline with working required repositories and services.

**Blocked by:** 06 — Upgrade Betty from Fedora 43 to Fedora 44.

**Status:** ready-for-agent

- [ ] Confirm the operating system, kernel, architecture, boot target, and Asahi release packages.
- [ ] Confirm no failed systemd units remain.
- [ ] Confirm SSH, Tailscale, Docker, and Netdata are healthy.
- [ ] Revalidate the 1Password and Tailscale signing keys before enabling those repositories.
- [ ] Run a normal Fedora 44 package refresh after repository restoration.
- [ ] Record DNF history and the final headless-service baseline.

## Read-only validation commands

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'rpm -q fedora-asahi-remix-release-common fedora-asahi-remix-release-identity-server fedora-asahi-remix-release-server'
ssh betty 'systemctl is-system-running; sudo systemctl --failed --no-legend'
ssh betty 'sudo systemctl is-active sshd tailscaled docker; curl -fsS http://127.0.0.1:19999/api/v1/info | head -c 200'
ssh betty 'sudo dnf repolist --all'
```

Expected evidence is Fedora `44`, `aarch64`, the Asahi Server release packages, `multi-user.target`, no failed units, healthy SSH/Tailscale/Docker/Netdata, and visible third-party repository state.

## Repository restoration checks

First inspect repository IDs and key settings. Re-enable 1Password or Tailscale only after their official keys and metadata are verified.

```bash
sudo dnf repolist --all
sudo dnf config-manager setopt 1password.enabled=1 tailscale-stable.enabled=1
sudo dnf makecache --refresh
sudo dnf history info last
```

The known repository IDs are `1password` and `tailscale-stable`; re-enable them only after their keys and metadata are verified. Expected response is a successful refresh without GPG signature errors. Record any repository that remains disabled and why.

## Troubleshooting commands

```bash
sudo journalctl -b -p warning..alert --no-pager
sudo dnf history list | head -n 12
sudo systemctl status sshd tailscaled docker --no-pager
```

Do not reconnect the Immich drives or change the desktop target in this ticket. This ticket establishes the stable headless baseline for the desktop decision.

## Resources

- [Fedora Asahi Remix](https://asahilinux.org/fedora/)
- [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/)
- [Fedora current releases](https://fedoraproject.org/wiki/Releases)
