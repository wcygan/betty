# 04 — Upgrade Betty from Fedora 42 to Fedora 43

**What to build:** Betty boots Fedora Asahi Remix 43 Server and remains reachable through its headless management path.

**Blocked by:** 03 — Repair repositories and preflight the Fedora upgrade.

**Status:** ready-for-agent

- [ ] Stage the reviewed Fedora 43 system-upgrade transaction.
- [ ] Reboot through Fedora’s offline upgrade process.
- [ ] Confirm Betty returns on the expected ARM64 Asahi kernel.
- [ ] Confirm SSH and Tailscale access after the reboot.

## Read-only pre-reboot checks

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'sudo dnf history info last'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected baseline is Fedora `42`, `aarch64`, `multi-user.target`, and active SSH, Tailscale, and Docker services.

## Upgrade commands

Run only after ticket 03 records an approved transaction and the data drives are detached.

```bash
sudo dnf system-upgrade reboot
```

The command reboots into Fedora's offline upgrade environment. Keep a separate Tailscale and local-console recovery path available because SSH will disconnect during reboot.

## Post-reboot checks

```bash
ssh betty 'rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'systemctl is-system-running; sudo systemctl --failed --no-legend'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected responses include Fedora `43`, an Asahi `aarch64` kernel, `multi-user`, `running`, no failed units, and active management services. If SSH does not return, use the console path and do not continue to ticket 05.

## Resources

- [Fedora offline upgrade guide](https://docs.fedoraproject.org/en-US/quick-docs/upgrading-fedora-offline/)
- [Fedora DNF system-upgrade reference](https://fedoraproject.org/wiki/DNF_system_upgrade)
