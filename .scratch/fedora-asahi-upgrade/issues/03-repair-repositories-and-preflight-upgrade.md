# 03 — Repair repositories and preflight the Fedora upgrade

**What to build:** A reviewed Fedora Asahi upgrade transaction with valid signing keys and no unexpected package removals.

**Blocked by:** 02 — Quiesce Immich and detach data drives.

**Status:** ready-for-agent

- [ ] Refresh Fedora and Asahi repository metadata.
- [ ] Resolve or intentionally disable the 1Password and Tailscale repositories with signature errors.
- [ ] Confirm Fedora Asahi 43 ARM64 release and kernel packages are available.
- [ ] Run the Fedora system-upgrade dependency preflight for Fedora 43.
- [ ] Review all removals, replacements, and third-party package changes.
- [ ] Stop if the transaction requires unreviewed package erasure or unsigned metadata.

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

## Resources

- [Fedora DNF system upgrade](https://docs.fedoraproject.org/en-US/quick-docs/upgrading-fedora-offline/)
- [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/)
- [Fedora current releases](https://fedoraproject.org/wiki/Releases)
