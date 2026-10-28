# Migrate Betty to macOS

Reuse the existing macOS installation if it works. Keep Linux and the original
Immich disk until macOS, remote access, Immich, and an independent Mac-side
backup have been verified. Job Scanner and other Linux services are out of scope.

## Repositories and dependencies

| Repository | Role in the migration |
| --- | --- |
| [betty](https://github.com/wcygan/betty) | This plan and Betty's host and access procedures. |
| [immich-infra](https://github.com/wcygan/immich-infra) (private) | Immich Compose configuration, backup and restore tools, and the authoritative backup runbook. |
| [dotfiles](https://github.com/wcygan/dotfiles) | Supported macOS bootstrap and Determinate Nix setup. |
| [agent-skills](https://github.com/wcygan/agent-skills) | Reusable Codex skills; the dotfiles repository pins and installs its catalog. |

Authenticate GitHub on the Mac with an account that can access private
repositories. Install 1Password and configure its SSH agent and authorized
GitHub key, or use another existing authorized sign-in. Test access before
cloning `immich-infra`; do not copy private keys or commit secrets. Restore
required machine-local credentials and configuration from their secure sources.

Betty's Linux checkout also contains `job-scanner-v1`, `lab-homepage`,
`csgoplant`, and `license-server`; these are not selected for migration.
Other private repositories should be cloned as needed, not installed merely
because they exist on GitHub. This inventory does not establish that every
personal repository or machine-local configuration has been identified.

On 2026-10-28 the live Betty `immich-infra` checkout contained modified Compose,
backup and restore files and untracked operational code; its `.env` also
contains machine-local configuration and secrets. The GitHub clone alone is not
proof that those files are preserved. Before erasing Linux, compare that checkout
with the other checkout and GitHub, preserve the required uncommitted and
untracked code in a reviewed private location, and securely preserve the needed
configuration. Do not commit `.env`, API keys, database passwords or backup logs.
Betty's own Linux checkout also has a modified `AGENTS.md`; review it for
anything needed before removal.

## 1. Protect the current Immich library

1. Check the live Compose services, the identity and mount of `/mnt/immich`,
   available space, and the backup retention preview. Follow the
   [Immich backup runbook](https://github.com/wcygan/immich-infra/blob/main/docs/backup.md)
   and compare it with the actual live checkout.
2. Create a fresh v3.2.0 full backup with an attachable session and mount guard.
   Preserve the September artifact. The server is stopped during the backup.
3. Confirm successful publication and that the server returns healthy. Record
   the artifact path, version, and result. A content-sealed backup is not a
   restore test.
4. Copy the complete artifact to independent storage and verify the copy's
   content against its manifest. Confirm its capacity and mount identity first;
   preview any new transfer or retention policy. The current Crucial backup is
   on the same drive as the live data. Gertrude is a possible destination, not
   an established backup until the copy and verification succeed.
   The 2026-10-28 SanDisk copy runs in Betty's `immich-sandisk-copy` tmux
   session; its result is recorded in `backup-logs/copy-sandisk-2026-10-28.log`.
   Confirm the success marker, exit status, destination identity and content
   checks before treating it as complete. It is not a restore drill.

## 2. Try the existing macOS installation

1. With a display and keyboard connected, shut Betty down normally. Immich
   will be unavailable while macOS is running.
2. Hold the power button until startup options appear. Select the existing
   macOS startup disk if available and sign in. The 74.5 GB APFS container
   observed from Linux suggests an installation but does not prove it boots.
3. If macOS does not boot, inspect Recovery and determine whether a repair or
   reinstall is needed. Do not erase partitions or external drives as part of
   this test. Preserve Linux until the later verification gates pass.

## 3. Set up and verify access

1. Connect macOS to the network, install Tailscale, and sign in to the correct
   tailnet. Enable macOS Remote Login for the intended account.
2. Configure the authorized public SSH key and the existing 1Password SSH agent
   workflow on the connecting Mac. Verify host identity and connect through
   Tailscale; a reinstalled OS can have a new SSH host key and tailnet identity.
3. Test access after restart and login. Record whether Tailscale and remote
   access are available before login; do not assume the Linux behavior carries
   over to macOS.
4. Set up GitHub access; clone the Betty and private Immich repositories as well
   as `https://github.com/wcygan/dotfiles.git`. Reconcile preserved live changes
   before using the Immich checkout. Run `./bootstrap.sh` in dotfiles.
   If Nix is missing, finish the Determinate macOS installer it opens, start a
   fresh shell, and rerun the bootstrap. Run the repository's strict verify.
5. Install and sign in to the ChatGPT desktop app. Enable the Computer Use
   plugin and grant its Accessibility and Screen Recording permissions.
   Set up the remote connection in Settings > Connections and verify a remote
   task and Computer Use. For an SSH project, also verify that `codex` is on
   the remote login shell's PATH.

## 4. Restore Immich on macOS

1. Prepare separate Mac-compatible storage with enough space for the restored
   library, database, backup, and growth. The current Crucial drive is ext4;
   do not erase it to make it readable on macOS.
2. Install a container runtime and restore the verified fresh artifact into
   isolated paths using the matching Immich version and compatible database
   image. Adapt and test the restore tooling for macOS before relying on it;
   do not point a restore at the original Linux data.
3. Sign in and check recent originals and videos, albums, users, and sharing.
   Verify service startup and access after restarting the Mac. Record the
   artifact, versions, paths, and result.
4. Create a new backup from the working Mac deployment on independent storage.
   Verify its contents and perform an isolated restore drill; check the same
   user-visible data. Keep the original drive and the pre-migration copy.

## 5. Reclaim the internal Linux space

Proceed only after macOS access and the Immich restore and independent backup
drill succeed. From macOS, identify the actual APFS containers and Asahi
partitions; use the [Asahi removal instructions](https://asahilinux.org/docs/sw/deleting-an-install/)
for this exact layout. Remove only the identified Asahi installation and expand
the macOS APFS container into the freed space. Do not copy example disk numbers.
Check the resulting capacity, reboot into macOS, and retest remote access.

## 6. Reclaim the external Immich disk

After the Mac-side backup and isolated restore are proven, identify the Crucial
disk by model and physical device, then reformat it for macOS. Formatting erases
both its Linux library and its old same-device backup. Choose whether it will
hold the live library or an additional backup. If moving the live library, copy
and verify it, update the Mac deployment, restart Immich, and check the data
again before removing the temporary copy. Keep an independent backup afterwards.

## References

- [Apple startup options](https://support.apple.com/en-us/102342)
- [Immich backup and restore](https://docs.immich.app/administration/backup-and-restore/)
- [Computer Use setup](https://learn.chatgpt.com/docs/computer-use)
- [Remote connections](https://learn.chatgpt.com/docs/remote-connections)
