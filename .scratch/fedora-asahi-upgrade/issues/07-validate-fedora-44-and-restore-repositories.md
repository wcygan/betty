# 07 — Validate Fedora 44 and restore repository access

**What to build:** A stable Fedora Asahi Remix 44 Server baseline with working required repositories and services.

**Blocked by:** 06 — Upgrade Betty from Fedora 43 to Fedora 44.

**Status:** complete

- [x] Confirm the operating system, kernel, architecture, boot target, and Asahi release packages.
- [x] Confirm no failed systemd units remain.
- [x] Confirm SSH, Tailscale, Docker, and Netdata are healthy.
- [x] Revalidate the 1Password and Tailscale signing keys before enabling those repositories.
- [x] Run a normal Fedora 44 package refresh after repository restoration.
- [x] Record DNF history and the final headless-service baseline.

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

The user approved the Step 7 repository metadata refresh after the configured
official key URLs and installed key fingerprints were compared successfully.
Both repositories were already enabled, so no repository setting needs to
change before the refresh.

## Validation evidence to date

At `2026-08-12T18:50:30Z`, Betty reported Fedora `44`, kernel
`7.1.6-400.asahi.fc44.aarch64+16k`, architecture `aarch64`, and
`multi-user.target`. It had the `44-15` Asahi common, Server identity, and
Server release packages installed. The system state was `running`. SSH,
Tailscale, Docker, and Netdata were active. No system unit failed. Netdata's
local API returned its version and host data.

The `1password` and `tailscale-stable` repository files use their providers'
official key URLs. The installed and provider-served 1Password key fingerprints
matched: `3FEF9748469ADBE15DA7CA80AC2D62742012EA22`. The installed and
provider-served Tailscale primary and subkey fingerprints also matched.

The initial repository listing used cached metadata. A fresh DNF query at
`2026-08-12T18:57:44Z` requested import of the same verified 1Password and
Tailscale keys for new repository metadata. It did not complete a successful
refresh. Import the verified keys through the approved DNF prompt, then repeat
the refresh before completing this ticket. DNF history remains transaction
`25`, status `Ok`, because metadata refresh does not alter installed packages.

The user approved import of the verified 1Password and Tailscale repository
keys after the fresh metadata check requested them.

The approved `dnf makecache --refresh` completed with `Repositories loaded`
and `Metadata cache created`. At `2026-08-12T19:02:10Z`, every enabled
repository loaded without a signature error. The system was `running`; SSH,
Tailscale, Docker, and Netdata were active; and no system unit failed. The
Immich mount points remained absent.

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
