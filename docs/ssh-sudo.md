# SSH and remote sudo through 1Password

## Intended behavior

The Mac holds the administrator key in 1Password. SSH login, remote Git/SSH,
and remote sudo can request signatures through its SSH agent. Private keys and
Linux account passwords are never copied into this repository or to remote
staging directories. Only a public key and compiled PAM module are deployed.

Touch ID happens on the Mac. Neither server needs a biometric reader or a
1Password desktop installation. This does not configure local Linux console
login or local Linux fingerprint authentication.

Support is deliberately limited to these inspected machines:

| Host | OS | Architecture | Initial sudo policy |
| --- | --- | --- | --- |
| betty | Fedora Asahi Remix 44 | aarch64, 16 KiB pages | Password required |
| gertrude | Debian 12 Bookworm (Raspberry Pi) | aarch64 | Two `NOPASSWD: ALL` rules |

`ssh-sudo/config.toml` records the public fingerprint of the `betty` key from
1Password and the supported SSH names/user. The test transport uses these
Tailscale-resolvable names, port 22, normal known-hosts verification, and a
temporary public-only identity file. It intentionally ignores user SSH config
so a local private key, proxy rule, or multiplexed connection cannot hide failure
of the 1Password path. Unknown host keys must be verified and enrolled separately.

## Mac prerequisites

1. Open and unlock 1Password. Enable **Settings → Developer → SSH Agent**.
2. Enable Touch ID for 1Password and choose the SSH authorization policy you want.
3. Confirm that the `betty` key is available to the agent. A changed key requires
   updating the fingerprint, SSH login authorization on each server, and the
   root-owned sudo key file. Keep existing access until all replacements pass.
4. Forward the agent only to Betty and Gertrude. The socket is
   `~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock`.

The original Mac config selected that socket globally but also allowed the
local `~/.ssh/id_ed25519` key. When the app was not running, the socket refused
connections and SSH silently used that local key. `ssh-sudo-test` prevents this
false positive by authenticating with a public-only identity from the agent.

For everyday SSH, select a public-only key file containing the matching agent
key and configure it in the existing host block:

```sshconfig
Host betty gertrude
    User wcygan
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
    IdentityFile ~/.ssh/1password-admin.pub
    IdentitiesOnly yes
    ForwardAgent yes
```

Replace the existing host-specific private `IdentityFile` rather than adding
another one. Keep OrbStack's required top-of-file Include. Keep a backup of the
original config and retain the old private key for recovery during migration.
This host block does not change GitHub's key selection.

## Build and install

Run from the Mac in this checkout:

```sh
just check
just ssh-sudo-build
just ssh-sudo-container-test
just ssh-sudo-enroll           # Bootstrap once, using existing recovery-key access
just ssh-sudo-configure-mac    # Back up and update the inspected Mac SSH host blocks
just ssh-sudo-doctor
just ssh-sudo-install gertrude
just ssh-sudo-test gertrude
just ssh-sudo-install betty
just ssh-sudo-test
```

The build uses local Docker/OrbStack, the pinned ARM64 Rust 1.90 Bookworm image,
and upstream pam_rssh v1.2.1 commit
`e8dd046c423f85df266c23bcc3d7033bfee81255` with its locked Cargo dependencies and
pinned submodule. Upstream's Cargo manifest reports version 1.2.0 even at this
tag. No release-candidate binaries are used. A Debian 12 build uses glibc and
OpenSSL 3 compatible with the inspected hosts; actual loading is checked on
each host. The ELF load segments use 64 KiB alignment, compatible with Betty's
16 KiB pages. The base image is digest-pinned, but apt inputs are not snapshot
pinned, so a clean rebuild is not promised to be byte-for-byte identical.

The resulting `.cache/ssh-sudo/libpam_rssh.so` is ignored by Git. The build prints
its SHA256. The installer verifies the exact staged bytes before loading them.
No packages are installed on either host by this workflow.

`enroll` explicitly uses the existing `~/.ssh/id_ed25519` recovery key to append
the 1Password public key to each host's SSH login authorization, retaining all
existing keys. This is a bootstrap operation, not an agent verification test.
`configure-mac` writes `~/.ssh/1password-admin.pub`, backs up `~/.ssh/config`, and
updates only the exact inspected host-block layout. It refuses unfamiliar
configuration or symlinks rather than rewriting them. Repeating it is harmless.

`install` opens an SSH terminal for bootstrap sudo. Enter Betty's Linux password
in that terminal if asked; never paste it into chat. `stage` only uploads files
to a private `/tmp/ssh-sudo.*` directory and prints the root-side install command
for manual execution in an agent-forwarded session.

The root installer:

- Checks the exact supported OS/architecture and loads the verified module
  before changing PAM.
- Backs up every changed file under `/var/backups/ssh-sudo/<UTC timestamp>/`.
- Installs the module under the distribution's PAM directory and restores
  SELinux labels where available. SELinux remains enforcing.
- Writes the public key to `/etc/security/ssh-sudo/wcygan.keys`, owned by root.
  It never trusts user-writable `~/.ssh/authorized_keys` for sudo authorization.
- Adds an `auth sufficient` rule only to `/etc/pam.d/sudo`, retaining existing
  password, account, and session rules. It does not edit Fedora's generated
  `system-auth` or Debian's generated `common-auth`.
- Adds `/etc/sudoers.d/90-ssh-sudo`, preserving `SSH_AUTH_SOCK` and enabling
  `noninteractive_auth` only for `wcygan`. Sudo >=1.9.10 is required.
- Removes only Gertrude's two observed exact `wcygan ALL=(ALL) NOPASSWD: ALL`
  lines, in `/etc/sudoers` and `/etc/sudoers.d/010_pi-nopasswd`.
- Validates sudoers and tests root execution as the invoking user with and
  without the agent. On exceptions or failed checks, restores the original
  files. Abrupt termination, host failure, or SIGKILL still requires recovery.

Unknown sudo bypasses cause verification to fail and rollback. They are never
automatically rewritten. SSH login policy and Docker membership are unchanged.

## Integration suite and approval semantics

```sh
just ssh-sudo-doctor           # Agent, strict SSH, remote baseline and sudo policy
just ssh-sudo-test             # Both hosts; nonzero if any host fails
just ssh-sudo-test betty       # One host
just check                    # Local behavior tests and existing harness checks
just ssh-sudo-container-test   # Real module/sudo/rollback with an ephemeral test key
```

Every live host check authenticates using the expected 1Password key. It then
tests agent forwarding, `sudo -k -n /usr/bin/id -u` returning exactly `0`, denial
when `SSH_AUTH_SOCK` is unset, and denial in a separate session without agent
forwarding. `-k` with the command ignores sudo's timestamp for that invocation;
the suite does not use `sudo -K` or invalidate other sessions' credentials.
SSH/timeout failures are failures, not evidence of a successful denial.

Background clients may not show an immediate dialog: 1Password records
`Notifying user through tray icon that they have a background prompt waiting`
and eventually `ssh authorization prompt timed out`. Open its menu-bar icon to
inspect the pending request, or run the command with Ghostty in the foreground.
Confirm the requested key is `betty`. Unrelated GitHub requests are not this flow.
Do not change approval scope or weaken authentication to work around a hidden prompt.

`-n` prevents terminal password prompts. `noninteractive_auth` allows PAM to
try the agent anyway; authorization can still show a GUI prompt on the Mac.
The harness bounds agent listing and remote command execution to 90 seconds;
installation permits up to 300 seconds for a bootstrap password and live checks.

Successful signatures prove access to an authorized key, not a fresh fingerprint
scan. 1Password may remember approval for the connecting app/key, and normal
sudo commands may reuse sudo timestamps. For manual acceptance, lock 1Password,
start a new terminal SSH session, approve the request on the Mac, and rerun the
suite. Also test denying the approval: the operation must fail without granting
new sudo access. Cancellation/Touch ID observation is a human test, never an
automated PASS claim.

## Existing tools and unattended operation

`scripts/betty_desktop.py` previously forced `IdentityAgent=none`. That override
has been removed so it honors the Mac's SSH config. Once the public-only host
identity is configured, desktop commands use 1Password with no private fallback.

Gertrude's `gertrude/manage.py` uses `sudo -n` for management. After migration,
run it from the Mac with forwarding enabled and an available 1Password agent.
It may need Mac approval. It is no longer guaranteed to work from unattended
clients with no agent. Its installed root-owned health timer continues to run
independently of SSH/1Password. Truly unattended administration needs a separate,
explicitly scoped authorization policy; do not restore blanket `NOPASSWD: ALL`.

Forwarding exposes signing capability to trusted remote processes during the
authorized session. This is not per-command approval: the Mac prompt does not
prove which remote sudo command is being executed. Betty's `docker` group can
also access a root-owned Docker socket; sudo authentication alone does not gate
all possible root access. Docker membership changes are outside this migration.

## Recovery and rollback

Keep a known-working SSH/root session open during the first installation. The
installer prints the exact rollback command and backup path. Rollback restores
original content, modes, owners, and SELinux labels, including Gertrude's former
passwordless policy. It deletes newly created files listed in that backup.

```sh
sudo python3 /tmp/ssh-sudo.EXAMPLE/install.py rollback \
  --backup /var/backups/ssh-sudo/EXACT_TIMESTAMP
```

If the staging directory was cleaned, copy `ssh-sudo/install.py` back to the
host and run it with the same backup path. Revert the Mac SSH config from its
backup if the agent is unavailable; existing local recovery keys are retained.
If PAM is broken and no root session remains, use the host's console/recovery
access to restore the root-owned backups. Password fallback still requires a
known, usable Linux account password; do not assume the Raspberry Pi's password
is known just because its former sudo policy was passwordless.

## Execution record: 2026-10-21

- Read-only inspection confirmed both OS versions, existing PAM policies, and
  Gertrude's duplicate passwordless rules.
- Opened 1Password on the Mac; the previously refusing socket began responding
  and offered the expected key. Biometric approval is still a separate live step.
- Built the pinned source successfully. Initial module SHA256:
  `6acc48cb19a756a70402e316f91490f7afc8fe4d6fafee7a0a693817d92d1f1a`.
- The isolated ARM64 Debian container passed real PAM signing, root sudo,
  missing-agent denial, repeat installation, rollback, digest rejection, and
  automatic recovery after a failed install.
- Gertrude's 1Password public key was enrolled, preserving existing login keys.
  Its sudo migration succeeded with backup
  `/var/backups/ssh-sudo/20261021T131146.013833Z`. Both observed passwordless
  bypasses were removed. The complete live suite passed from Ghostty and from
  the agent's shell. Ordinary `ssh gertrude 'sudo -k -n id -u'` returned `0`.
- Mac host configuration now selects the public-only 1Password identity and
  forwards the agent to both hosts. Original config:
  `~/.ssh/config.before-ssh-sudo-20261021T131227Z`.
- Betty's migration succeeded after the user entered the bootstrap sudo password
  directly in Ghostty. Backup:
  `/var/backups/ssh-sudo/20261021T131423.233495Z`. Its staging directory is
  `/tmp/ssh-sudo.Aop7Myyu`. The complete live suite passed and SELinux remained
  enforcing. Ordinary `ssh betty 'sudo -k -n id -u'` returned `0`.
- Both installed modules match the recorded SHA256, and both sudo key lists and
  modules are owned by `root:root` with mode `0644`.
- `just ssh-sudo-test` and `just ssh-sudo-doctor` passed for both machines.
  `just check` passed nine local behavior tests and the existing desktop harness
  self-test. All ten Gertrude management tests passed, Compose validation passed,
  and Gertrude's installed health sampler still reported `incidents=healthy`.
- The UI showed the agent enabled, per-application approval, and 24-hour approval
  retention. These settings were left unchanged. The logs confirmed that initial
  signing failures were background-prompt timeouts; a foreground Ghostty request
  subsequently succeeded. Fresh biometric and cancellation behavior still need
  human observation and are not claimed by automated tests.

## Sources

- [1Password agent forwarding and authorization model](https://www.1password.dev/ssh/agent/forwarding)
- [pam_rssh source and configuration at the pinned revision](https://github.com/z4yx/pam_rssh/tree/e8dd046c423f85df266c23bcc3d7033bfee81255)
- [Fedora's retirement of the older pam_ssh_agent_auth component](https://fedoraproject.org/wiki/Changes/DeprecatePamSshAgent)
- [Original macOS Secure Enclave article](https://nmattia.com/posts/2026-10-19-setting-up-ssh-keys-touch-id/)

The original article's device-bound key mechanism is not installed: 1Password
remains the single key provider for this workflow.
