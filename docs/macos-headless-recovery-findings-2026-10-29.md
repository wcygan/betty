# Betty macOS setup and recovery findings — 2026-10-29

This preserves the earlier setup session's point-in-time evidence. It has now
been reconciled with the MacBook checkout; use [macOS setup progress](macos-setup-progress.md)
for the latest revalidation and remaining work. Historical values below, including
the display timeout and free space, are snapshots rather than current settings.
This is not a claim of unattended or headless readiness. The actual standard
account is `rat`.

## Verified setup

- Betty is an M2 Mac mini running macOS Tahoe 26.7.2. `rat` is the standard development user; `cygan` is the human-controlled administrator. Keep administrator credentials and recovery keys outside the agent session; no passwordless sudo or personal vault copy.
- Apple Command Line Tools, Git, and Determinate Nix are installed. The durable dotfiles checkout is `/Users/rat/Software/dotfiles`, at `ef8d887475928fd8b7b83628840c00635050d4d8`. Bootstrap strict verification passed for its Nix profile, managed links and pinned Rust tooling. Existing local Codex configuration was preserved; the repository's `never`/`danger-full-access` template was not applied. Prior link backups and the original task checkout were retained.
- The pinned shared catalog contains 72 skills in `/Users/rat/.agents/skills`, from `wcygan/agent-skills` at `d256cb03668ada9c0e0326c5a3949615cdc49487`; the catalog check passed. Fresh login shells found Nix, Git, GitHub CLI, ripgrep and Fish.
- Git uses the existing scoped GitHub CLI Keychain credential through a persistent helper. Its fine-grained repository access is limited to `wcygan/betty`, `dotfiles`, `agent-skills`, and `immich-infra`, with contents read/write and no PR, issue, workflow, secret or administration rights; it expires November 28, 2026. A credential available to the agent is usable by it; do not treat it as hidden. Never record its value, keys, or authentication URLs here.
- On AC, automatic system sleep is disabled, display sleep is 10 minutes, and startup after power failure is enabled. Screen locking remains in use. FileVault status was verified **on**; the system `autoLoginUser` preference had no entry. No automatic-login configuration change was made.
- The signed Tailscale macOS `macsys` app is version 1.104.4; its backend reported running and online after desktop login. Its `RunSSH` preference is false: use ordinary macOS OpenSSH, not Tailscale SSH. Remote Login and Screen Sharing are enabled for Administrators and Rat. Screen Sharing's public control requests and legacy VNC password control are off. Remote Login's full disk access for remote users was observed on and merits a separate review; it was not changed.
- ChatGPT desktop version 26.1023.51421 and Tailscale are now listed under Open at Login. ChatGPT was absent after the restart and the user subsequently added it; its automatic launch on a later login has not been tested.

For the focused remote-access and idle test record, see [Computer Use reliability](macos-remote-computer-use-reliability.md).

## Evidence and limits

The user confirmed the Mac was on its lock screen, then native Computer Use calculated `7 + 6 = 13`; the user confirmed the screen was locked afterward. Continuous display coverage during the operation was not independently observed. Physical keyboard or pointer input was separately reported to pause automatic unlock until a manual unlock; avoid local input during a controlled test.

With peripherals disconnected and Screen Sharing closed, a locked-headless Computer Use attempt at 18:59 UTC failed: automatic unlock could not unlock the Mac. The cause was not established. The user then unlocked `rat` through Screen Sharing and closed that session. At 19:01 UTC, native Computer Use opened Calculator in the unlocked, logged-in headless session; both the accessibility result and a screenshot showed `8 + 9 = 17`. This verifies current unlocked-headless display capture and native control, not locked-headless or cold-boot recovery. No virtual display or security changes were made.

The user performed a normal restart. Their observations: LAN port 22 initially accepted connections while port 5900 was refused; a first password entry was followed by a boot transition and disconnection; after a second password entry, SSH as `rat` worked. LAN Apple Screen Sharing as `rat` then worked, and Tailscale recovered after desktop login. These observations are consistent with a staged startup, but do not alone prove the identity of each login screen or establish unattended pre-login access. FileVault being on was subsequently confirmed independently. No power-cut test or no-peripherals acceptance test has been performed.

The original Immich disk and the independent SanDisk backup must remain intact. The backup had a checksum reread, not a restore drill. No erase, reformat, restore drill, or migration of unrelated Linux services is authorized by this note.

## Later headless and shell checks

After relocation to its current location and a 15-minute idle window, native Computer Use calculated `6 + 8 = 14` and captured a screenshot. The starting lock state was not independently established, so this verifies post-idle native access, not locked-headless recovery.

The dotfiles optional shell handoff was enabled: an interactive TTY started Fish 4.7.1, while clean-environment non-interactive zsh commands remained zsh and found Nix tools. Interactive SSH with a TTY also enters Fish. Ghostty 1.4.0 was installed in the user Applications folder from the official signed macOS distribution; signature and macOS assessment passed. Its linked config no longer contains the stale `/Users/wcygan` shell path; the repository change is uncommitted. Ghostty configuration validation passed, as did the 18-test focused shell suite and the 366-test `test-pre` suite. Ghostty has not been verified as a system-wide default or tested in an interactive window.

The user subsequently confirmed they selected Ghostty’s default-terminal menu action and that Fish works in an actual terminal. Scope beyond that user-observed interaction is not independently verified. The Dock’s persistent app shortcuts were narrowed to App Store, System Settings, Tailscale, ChatGPT, Google Chrome, and Ghostty; the existing folder was preserved. This removes shortcuts only, not apps or data. A Dock preference backup is at `~/.local/state/betty-setup/dock-before-2026-10-29.plist`. Recent apps may still appear separately. As of this check the system volume reported about 23 GiB available; monitor capacity before large development or Immich workloads.

## Future reliability decision

The desired long-term outcome is one always-on Betty with power and Ethernet, without a second gateway, and reliable recovery after reboot; ChatGPT availability is optional. Today, leave the current working setup and security boundaries intact. In particular, login items run after user login and do not establish pre-login Tailscale availability.

Options to investigate, not approved or implemented:

1. Retain FileVault and evaluate the advanced open-source `tailscaled` system LaunchDaemon after disk unlock but before GUI login. It cannot itself unlock an encrypted startup disk. Tailscale's variant documentation and wiki describe an advanced launchd option; its unattended-access guidance states a standalone system daemon on macOS is not currently supported. Resolve that documentation inconsistency with Tailscale before relying on it. Do not run conflicting app variants or assume this is vendor-supported for this exact setup.
2. Consider FileVault off with system-daemon Tailscale and ordinary SSH, if the owner explicitly accepts the loss of startup-disk encryption protection. This is a material security tradeoff, not a default.
3. Consider FileVault off and standard-user automatic login with Tailscale and ChatGPT login items, if the owner explicitly accepts the increased local exposure and understands session and Keychain behavior. Automatic login does not prove either app or remote access recovers reliably.

A bounded user LaunchAgent watchdog might be considered only after an actual post-login failure is observed; none has been installed. Do not introduce a blanket watchdog or store administrator passwords. Preserve the standard `rat` account, verified SSH host key and no agent forwarding. No network ACL, VPN, encryption, login, permission, or daemon changes are approved by this record.

## Before any future change

- Review vendor support, version-specific requirements, disk-encryption and account risks, network exposure, and a concrete recovery path with the owner. Obtain specific approval for each security-sensitive change and have the owner handle macOS authentication and prompts.
- Record current settings, startup registrations, Tailscale variant, SSH host identity, profile and data backups. Plan rollback before changing a daemon or variant; preserve the existing working access path and avoid simultaneous conflicting variants.
- With a person present and display/keyboard available, conduct a coordinated normal reboot. Record separately: pre-unlock LAN reachability, disk unlock, pre-GUI network/SSH, user login, Tailscale, Screen Sharing, ChatGPT, and locked Computer Use. Verify the physical screen and recovery after any failure. Only claim the stages actually observed.
- Test ChatGPT's newly added login item on a future supervised login. Separately review whether Remote Login full disk access is needed. Do not claim unattended or headless readiness until the chosen recovery path has passed end-to-end tests.

## Internal capacity investigation (read-only snapshot)

The internal 500.3 GB physical disk was `disk0` at inspection. In physical order it contained `disk0s1` Apple APFS ISC (524 MB), `disk0s2` macOS APFS container (82.5 GB), `disk0s3` EFI - FEDOR (524 MB), `disk0s4` Linux Filesystem (1.1 GB), `disk0s5` Linux Filesystem (410.3 GB), then `disk0s6` Apple APFS Recovery (5.4 GB). Identifiers can change: re-enumerate and verify immediately before any operation. The running root snapshot belongs to the macOS container on `disk0s2`; `bless --getBoot` returned `/dev/disk3s3`. `systemsetup -getstartupdisk` required administrator access and was not authenticated. The APFS resize-limits query showed a current maximum of 82.5 GB, constrained by the following partitions. If the candidates were verified and safely removed, roughly 494 GB total APFS capacity may be possible, less partitioning overhead; exact limits must be rechecked. Preserve Apple ISC and Apple Recovery.

EFI - FEDOR and the two Linux-labeled partitions are candidates, not confirmed disposable targets. macOS does not identify the Linux filesystem contents; labels do not prove boot dependencies or that all needed data is backed up. Asahi documents that a typical install can also involve a separate APFS boot stub, and explicitly warns never to delete Apple APFS Recovery. The observed layout is not proof of every dependency. `tmutil destinationinfo` reported no Time Machine destinations, so there is no established current internal macOS backup from that check. The separate Immich backup is not a full Mac backup. The existing migration plan also calls for verified Immich restoration and an independent backup drill before reclamation; those gates have not been established.

A future supervised operation needs current disk and startup identity, candidate and boot-dependency confirmation, verified backups of all needed internal data, an available local recovery route, a reviewed rollback/recovery plan, and explicit approval for the exact irreversible deletions. The owner must be present for administrator prompts. APFS may be expandable online if contiguous free space becomes available, but that is not guaranteed; errors can require a restart or recovery environment. Never select external disks or delete the Apple ISC or system recovery partition. No deletion, resize, unmount, repair or restart was performed in this investigation.

## References

- [Apple: manage FileVault and SSH unlock on supported Apple silicon](https://support.apple.com/guide/security/managing-filevault-sec8447f5049/web); [FileVault overview](https://support.apple.com/guide/mac-help/protect-data-on-your-mac-with-filevault-mh11785/mac); [automatic login](https://support.apple.com/en-us/102316).
- [Tailscale macOS variants](https://tailscale.com/docs/concepts/macos-variants); [open-source tailscaled on macOS](https://github.com/tailscale/tailscale/wiki/Tailscaled-on-macOS); [tailscaled reference](https://tailscale.com/docs/reference/tailscaled); [unattended access](https://tailscale.com/docs/how-to/run-unattended).
- [OpenAI Computer Use and Locked use](https://learn.chatgpt.com/docs/computer-use); [remote connections](https://learn.chatgpt.com/docs/remote-connections).
