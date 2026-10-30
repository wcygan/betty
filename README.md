# Betty

## macOS migration

See [macOS setup progress](docs/macos-setup-progress.md) for the current verified setup and
remaining locked-use, reboot recovery, Immich and disk-reclamation work.

Follow [the macOS migration plan](docs/macos-migration.md) for backup, startup,
remote access, repository setup, Immich recovery, and reclaiming disk space.

## SSH and sudo through 1Password

The commands below describe the earlier Linux access workflow. Rat on macOS
uses ordinary OpenSSH with no agent forwarding or passwordless sudo; follow
[the current progress record](docs/macos-setup-progress.md) for this host.

The Mac's 1Password SSH agent is the intended authentication provider for Betty
and Gertrude. Read [the setup, support contract, and recovery guide](docs/ssh-sudo.md).

```sh
just ssh-sudo-doctor
just ssh-sudo-test
```

These commands require local 1Password authorization. The test suite verifies
agent-only SSH, forwarding, sudo root execution, and denial without the agent.
It cannot certify that you physically touched the fingerprint sensor.

## Desktop harness

Run these commands from the Mac that connects to Betty. The harness uses the
existing SSH configuration. It does not store or print passwords.

```sh
just doctor
just connect-rdp
```

Set `BETTY_HOST`, `BETTY_RDP_HOST`, or `BETTY_RDP_PORT` only when the default
`betty:3389` connection is not correct.

The commands below change state. Run them only after you review their purpose.

```sh
just install-rdp-client
just rustdesk-stage
just rustdesk-preview
just rustdesk-install
```

`rustdesk-stage` downloads the official ARM64 Fedora RPM to a named directory
on Betty. It checks the SHA-256 digest published in the official GitHub release.
`rustdesk-preview` checks that RPM and opens an interactive remote sudo prompt
for a DNF preview. `rustdesk-install` installs the staged RPM through the same
interactive remote sudo boundary.

Read [the RustDesk role and test plan](docs/rustdesk-role-and-test-plan.md)
before you install RustDesk. RustDesk is not Betty's boot or GNOME-login path.
