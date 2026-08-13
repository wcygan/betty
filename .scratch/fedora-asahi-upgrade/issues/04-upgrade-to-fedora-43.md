# 04 — Upgrade Betty from Fedora 42 to Fedora 43

**What to build:** Betty boots Fedora Asahi Remix 43 Server and remains reachable through its headless management path.

**Blocked by:** 03 — Repair repositories and preflight the Fedora upgrade.

**Status:** complete

- [x] Stage the reviewed Fedora 43 system-upgrade transaction.
- [x] Reboot through Fedora’s offline upgrade process.
- [x] Confirm Betty returns on the expected ARM64 Asahi kernel.
- [x] Confirm SSH and Tailscale access after the reboot.

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

## Completion evidence

The user approved the offline Fedora 43 reboot. They ran
`sudo dnf system-upgrade reboot` from the Betty local console. The first
Tailscale ping timed out during the expected reboot window. A later ping
returned a 2 ms reply. The user then returned to Betty through SSH.

The post-reboot SSH check ran at `2026-08-12T15:44:04Z`:

```text
Host: betty
Fedora: 43
Kernel: 7.1.6-400.asahi.fc43.aarch64+16k
Architecture: aarch64
Default target: multi-user.target
System state: running
Failed units: none
sshd: active
tailscaled: active
docker: active
Tailscale backend: Running
```

The Fedora 43 offline transaction applied successfully. SSH and Tailscale are
available after the reboot. Immich remains stopped. Both external drives remain
detached.

## Resources

- [Fedora offline upgrade guide](https://docs.fedoraproject.org/en-US/quick-docs/upgrading-fedora-offline/)
- [Fedora DNF system-upgrade reference](https://fedoraproject.org/wiki/DNF_system_upgrade)
