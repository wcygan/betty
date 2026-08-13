# 03 — Repair repositories and preflight the Fedora upgrade

**What to build:** A reviewed Fedora Asahi upgrade transaction with valid signing keys and no unexpected package removals.

**Blocked by:** 02 — Quiesce Immich and detach data drives.

**Status:** complete

- [x] Refresh Fedora and Asahi repository metadata.
- [x] Resolve or intentionally disable the 1Password and Tailscale repositories with signature errors.
- [x] Confirm Fedora Asahi 43 ARM64 release and kernel packages are available.
- [x] Run the Fedora system-upgrade dependency preflight for Fedora 43.
- [x] Review all removals, replacements, and third-party package changes.
- [x] Stop if the transaction requires unreviewed package erasure or unsigned metadata.

## Read-only repository checks

```bash
ssh betty 'rpm -E %fedora; uname -m; dnf --version | head -n 1'
ssh betty 'sudo dnf repolist --enabled'
ssh betty 'grep -RHE "^\[(1password|tailscale[^]]*)\]" /etc/yum.repos.d || true'
ssh betty 'sudo dnf --disablerepo=1password --disablerepo=tailscale-stable list --showduplicates fedora-asahi-remix-release-server'
```

Expected baseline is Fedora `42`, architecture `aarch64`, DNF5, and repository metadata that loads after the known 1Password and Tailscale repositories are excluded. Do not import an unfamiliar signing key without recording its source.

## Preflight commands

```bash
sudo dnf clean all
sudo dnf --disablerepo=1password --disablerepo=tailscale-stable makecache --refresh
sudo dnf --disablerepo=1password --disablerepo=tailscale-stable \
  system-upgrade download --releasever=43 --allowerasing
sudo dnf history info last
```

Expected evidence includes a staged Fedora 43 transaction, valid Fedora and Asahi metadata, and a reviewed package-removal list. Stop on GPG errors, unsigned metadata, or unexpected removal of SSH, Tailscale, Docker, or the Asahi kernel.

## Completion evidence

The user approved metadata refresh and Fedora 43 transaction staging before the
commands ran. The external drives were disconnected and Immich was stopped.

The baseline check ran at `2026-08-12T11:56:11Z`:

```text
Fedora: 42
Architecture: aarch64
DNF: dnf5 version 5.2.12.0
```

The enabled repository list loaded without an error. The known `1password` and
`tailscale-stable` repositories were disabled for the refresh and upgrade
commands. No signing key import was requested. The staged command was:

```text
dnf --disablerepo=1password --disablerepo=tailscale-stable \
  system-upgrade download --releasever=43 --allowerasing
```

DNF completed the download at `2026-08-12T13:28:24Z`. Its offline transaction
state records `system_releasever = "42"`, `target_releasever = "43"`, and
`status = "download-complete"`. It has 1035 cached RPMs, totaling 1.1G.

The transaction record contains 135 `Install`, 900 `Upgrade`, and 902
`Replaced` actions. It has no standalone `Remove` action. The `Replaced`
entries are the Fedora 42 package records that their transaction counterparts
replace.

The staged package set includes these required packages:

- Fedora Asahi Server release packages upgraded from `42-10` to `43-15`.
- `kernel-16k-7.1.6-400.asahi.fc43` and its core and module packages.
- OpenSSH upgraded from `9.9p1-11.fc42` to `10.0p1-11.fc43`.
- Tailscale upgraded from `1.94.2-1.fc42` to `1.94.2-1.fc43`.
- Docker CLI, Compose, Buildx, Moby Engine, and related packages upgraded to
  Fedora 43 packages.

The only non-Asahi third-party package action is the expected LazyGit upgrade
from its `atim:lazygit` COPR. DNF log review found no GPG, signature, unsigned,
error, or failure entry from the upgrade download.

Fedora 43 is staged but not installed. No reboot has started. The next ticket
requires separate approval to reboot into the offline Fedora 43 transaction.

## Resources

- [Fedora DNF system upgrade](https://docs.fedoraproject.org/en-US/quick-docs/upgrading-fedora-offline/)
- [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/)
- [Fedora current releases](https://fedoraproject.org/wiki/Releases)
