# Betty

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
