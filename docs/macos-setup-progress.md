# macOS setup progress

Updated 2026-10-30. This records completed checks separately from user-reported
setup and work still pending. No passwords, private keys, recovery codes,
authentication tokens, or private backup archives belong in this repository.

## Current checkpoint

Betty boots macOS Tahoe 26.7.2. Key-based SSH from the MacBook works as `rat`
over Tailscale. Native OpenAI remote connections and unlocked Computer Use
have passed recorded tests; locked use is intermittent and unattended reboot
recovery remains unproven.
On 2026-10-30 the owner chose unattended recovery: FileVault off and automatic
login as `rat`. See [unattended recovery](macos-unattended-recovery.md).
The existing [workstation plan](macos-agent-workstation.md) describes the wider
setup; this progress record supplies its current status.

## Accounts and access

- User confirmed a human administrator account named William, with short
  username reported as `cygan`, and a standard agent account named Rat.
- Verified the agent account's actual username is `rat`, with home directory
  `/Users/rat`. Use this account instead of the plan's earlier `wcygan` example.
- Remote Login is enabled and accepts connections as `rat`.
- User compared the new ED25519 host fingerprint from Betty's own Terminal
  with the fingerprint presented to the MacBook and confirmed a match.
- Backed up the MacBook's SSH configuration and known-hosts file locally before
  replacing the obsolete host record and updating the alias. Keep those backups
  outside this repository.
- Installed the MacBook's existing approved public key in Rat's
  `~/.ssh/authorized_keys`. The corresponding private key remains in the
  MacBook's 1Password SSH agent; it was not copied to Betty.
- Verified `~/.ssh` is owned by `rat` with mode `700`, and `authorized_keys` is
  owned by `rat` with mode `600`.
- Updated the MacBook's `betty` alias to use Rat and Betty's full Tailscale DNS
  name. Retained `HostKeyAlias betty`, the existing public-key selector and
  1Password agent; set `IdentitiesOnly yes` and `ForwardAgent no`. Gertrude's
  configuration was preserved.
- Verified a fresh SSH connection with password and keyboard-interactive
  authentication disabled for that test. OpenSSH reported public-key
  authentication; remote commands returned `rat` and macOS `26.7.2`.
- Verified that connection did not expose a forwarded SSH agent socket.

Disabling password authentication for a client-side test does not disable it
on Betty's SSH server. No server-side password-authentication change or
passwordless sudo setup was performed. Native macOS administration still
requires the human administrator's approval.

## Decision: scoped GitHub access for Rat

On 2026-10-29, we chose to start with a fine-grained personal access token on
the existing GitHub account, restricted to the repositories Rat needs. A
separate GitHub account can be considered later if a distinct identity or
independently assigned collaborator permissions become useful.

- Select only the required repositories and use an expiration; 30 days is the
  starting recommendation. Choose read-only contents for inspection, or
  read/write when pushing is needed. Grant pull-request or issue permissions
  only when required; leave administration, secrets and workflow permissions
  ungranted initially.
- Use the scoped token for GitHub CLI and Git access. GitHub CLI recommends
  `GH_TOKEN` for fine-grained tokens; confirm the intended commands and Git
  credential-helper behavior work before relying on the setup. Avoid normal
  CLI browser authorization if its broader permissions are not intended.
- Treat a token available to Rat as accessible and usable by the agent. Its
  scope limits authority; it does not hide the credential from that account.
  Keep personal vaults, private keys and SSH agent forwarding off Rat. Never
  place tokens in this repository, shell history, logs or chat.
- The later Betty setup session records this credential as installed through the
  GitHub CLI Keychain helper, limited to `betty`, `dotfiles`, `agent-skills`,
  and `immich-infra`, with contents read/write and expiration November 28, 2026.
  Scope and expiration are recorded evidence, not independently re-audited in
  this check; no credential value was read or printed.

Evidence: [GitHub fine-grained token documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
and [GitHub CLI authentication documentation](https://cli.github.com/manual/gh_auth_login).

## Tailscale

- Tailscale is installed in `/Applications`, available to both accounts.
- Found the network extension running but Tailscale stopped when queried as
  Rat. Installing the app under the administrator did not establish that Rat's
  session was connected.
- Connected Tailscale from Rat's session. Removed the saved accept-subnet-routes
  and advertise-exit-node options; neither is needed for access to this Mac.
- Verified Tailscale reports `Running`, Betty is online in the same tailnet as
  the MacBook, and the local health list is empty.
- Verified SSH to Betty's Tailscale IP and then its full Tailscale DNS name,
  using the previously verified host key and 1Password-backed public key.
- Tailscale diagnostic ping timed out during the check, but actual SSH over
  the Tailscale address succeeded. Do not describe the diagnostic ping as passed.
- User confirmed Tailscale is signed in and was added to Open at Login while
  logged into Rat. Tailscale recovered after desktop login in the supervised restart test.
  Pre-login Tailscale availability remains unproven.

The macOS GUI client depends on a user login session. Keep Rat logged in and
Betty awake until restart recovery has been tested. The user reported SSH and Screen Sharing success from a phone hotspot.
That does not establish pre-login availability or sustained reliability.

## Revalidation from the MacBook — October 29

Fresh key-based SSH succeeded with password and keyboard-interactive
fallback disabled and strict host-key checking. Read-only observations:

- macOS Tahoe 26.7.2 (25G332); user `rat`, UID 502. Admin membership is
  `root cygan`; Rat is not an administrator.
- SSH directory/file permissions remain `700`/`600`; no forwarded agent socket.
- ChatGPT and Tailscale processes are running. Screen Sharing accepts a local
  TCP connection on port 5900. This checks the listener, not a fresh GUI session.
- FileVault is on. No `autoLoginUser` preference entry was returned.
- AC power settings: `sleep 0`, `displaysleep 0`, `autorestart 1`.
  Earlier records showed a 10-minute display timeout; the current value is zero.
  This validation did not change the setting.
- A fresh login shell finds Nix, Git, GitHub CLI, ripgrep and Fish. `codex`
  is not found on that shell's PATH; native ChatGPT remote tools must not be
  confused with an installed Codex CLI.
- Dotfiles checkout is at `ef8d887475928fd8b7b83628840c00635050d4d8`;
  its Ghostty config has an uncommitted change. The skills directory has 72 entries.
- The internal disk is 500.3 GB. The macOS APFS container is still 82.5 GB;
  EFI - FEDOR (524 MB), Linux (1.1 GB), and Linux (410.3 GB) remain after it.
  Apple boot and recovery partitions also remain. No space was reclaimed.
- Root filesystem reports about 15 GiB available. Do not place the approximately
  348 GB Immich restore on the current internal volume.

## Revalidation from the MacBook — October 30

Read-only SSH checks as `rat` after the owner changed settings as `cygan`:

- `fdesetup status`: FileVault is off.
- `autoLoginUser` is `rat`. No restart has exercised it yet; `cygan` held the
  console during the check.
- AC power: `autorestart 1`, `sleep 0`, `displaysleep 0`. Default route is
  wired Ethernet `en0`. `pmset -g ps` reports AC power only (no UPS).
- Tailscale is the standalone `macsys` app (`io.tailscale.ipn.macsys`), not the
  App Store build or a `tailscaled` LaunchDaemon.
- Dotfiles fast-forwarded to `bc86408`, preserving the uncommitted Ghostty
  change, and `./bootstrap.sh link` linked `~/.config/rex`.
- Rex and the `claude`, `codex` and `pi` CLIs are not installed.

Historical evidence is preserved in [headless recovery findings](macos-headless-recovery-findings-2026-10-29.md)
and [Computer Use reliability](macos-remote-computer-use-reliability.md).
The supported `./bootstrap.sh verify` and `./bootstrap.sh agent-skills --check`
both passed with exit 0. All managed-profile/link checks passed and all 72
pinned skills matched `agent-skills@d256cb03668ada9c0e0326c5a3949615cdc49487`.
The verifier fetched missing Nix development dependencies into the store; it
did not reinstall the profile or change managed configuration.
No native GUI action, restart, external-disk read or credential extraction
was performed in this revalidation.

## Completed and remaining checkpoints

- [x] Separate human administrator and standard Rat account; key-based SSH.
- [x] Tailscale access and user-reported off-network SSH/Screen Sharing.
- [x] Native OpenAI pairing and harmless Computer Use actions in an unlocked
  headless session, with screenshots and accessibility results recorded.
- [x] Determinate Nix, dotfiles bootstrap and pinned shared skills installed;
  previous strict checks passed. See current recheck result below.
- [x] Inspect internal layout; Linux partitions remain and constrain APFS growth.
- [ ] Resolve intermittent confirmed-lock Computer Use failure. A confirmed-lock
  attempt failed at approximately 22:22 UTC; later manual unlock restored access.
  One successful idle trial does not establish locked-use reliability.
- [x] Choose a recovery design: FileVault off, automatic login as `rat`
  ([unattended recovery](macos-unattended-recovery.md)).
- [ ] Install Rex and the agent CLIs as `rat`; add Rex to Open at Login; sign
  in Rex's built-in Tailscale as `betty-rex`.
- [x] Restart test: automatic login and Tailscale recovered in about 40 s
  without input (2026-10-30).
- [ ] Pass the power-cut acceptance test in the unattended recovery record.
- [ ] Install/authenticate Codex CLI if SSH-based Codex projects are desired,
  then test it in a fresh remote login shell.
- [ ] Re-audit scoped GitHub permissions/expiration without exposing the token;
  review Remote Login's previously observed full-disk-access grant.
- [ ] Review and deliver the Ghostty config change in the dotfiles repository.
- [ ] Restore Immich on suitable Mac storage, verify real operation, create a
  new independent backup and complete an isolated restore drill.
- [ ] Reclaim internal Linux space only after the documented backup/recovery
  gates and exact partition identities are established. Preserve Apple boot
  and recovery. External disk reformatting remains a separate later step.

## Immich protection remains in force

The [migration record](macos-migration.md) records the independent SanDisk
backup's full macOS checksum verification: 348,309,621,133 bytes, all checks
passed, exit 0. This access-setup session did not rerun that verification or
perform an Immich restore drill.

Keep the original Immich disk and verified independent backup intact. Restore
using the private [immich-infra](https://github.com/wcygan/immich-infra)
repository, verify the Mac deployment, and create and verify a fresh independent
backup with a restore drill before reclaiming the original data disks. Job
Scanner and the retired Linux monitoring services remain out of scope.

## Safe handoff evidence

Record outcomes and non-secret configuration choices here. Keep actual
passwords, private keys, recovery keys, tokens, `.env` files, authentication
links, raw SSH debug logs, and private preservation archives outside Git.
This record deliberately omits tailnet addresses, key material and fingerprints;
the trusted host record and connection configuration remain on the MacBook.

Useful checks from the MacBook:

```sh
ssh -G betty | rg '^(hostname|user|identitiesonly|forwardagent) '
ssh -o BatchMode=yes -o PasswordAuthentication=no \
  -o KbdInteractiveAuthentication=no -o StrictHostKeyChecking=yes \
  betty 'whoami; sw_vers -productVersion'
```

The second check can require a human 1Password authorization prompt. A successful
test does not prove the per-request approval policy or vault-lock revocation
behavior; those remain separate credential-boundary checks in the workstation plan.
