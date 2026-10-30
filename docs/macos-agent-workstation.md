# Betty as a remote macOS development workstation

Prepared 2026-10-29. This is the setup and verification plan. See
[macOS setup progress](macos-setup-progress.md) for completed checks: macOS
26.7.2 is installed, the standard account is `rat`, and SSH over Tailscale works.
Native remote access, unlocked Computer Use, dotfiles and shared skills also
have recorded successful tests. Locked use and unattended reboot remain
unproven; the progress record distinguishes fresh checks from earlier evidence.

## Recommended layout

Use Betty as a dedicated development desktop. Run the native ChatGPT desktop
app, Codex, browser, IDE and native Computer Use in its development account.
Keep personal vault contents and human approval on the MacBook or phone.

- A human-only administrator account maintains the machine. Its password and
  FileVault recovery key stay in the human's 1Password, outside Betty's agent
  account. Do not grant passwordless sudo.
- The existing standard account `rat` owns
  development projects and the agent desktop. Install tools requiring admin
  approval through a human-controlled setup session. If setup already created
  `wcygan` as admin, create and test the separate administrator first, then
  demote the development account and retest access and FileVault unlock.
- Do not sync the personal 1Password vault, personal browser profile, personal
  iCloud Drive, or personal passwords into the agent account. Use development
  accounts and scoped credentials for websites the agent needs.
- Tailscale carries SSH and Apple Screen Sharing. OpenAI's native host pairing
  provides a separate way to continue Codex and Computer Use tasks remotely.
  SSH project connections alone are not a remote desktop connection.

The MacBook is a human control device in this design. Agent tasks must execute
on Betty, with their tools scoped to Betty. Giving the same agent unrestricted
local shell or Computer Use on the vault-bearing MacBook defeats this boundary.
Check each task's execution host; human approval is not equivalent to granting
the agent access to the approving device.

## What "the agent never sees the secret" can mean

Biometric approval can prevent the agent from independently unlocking a vault.
It does not isolate an unlocked vault from an agent controlling the same user
session. Full desktop and unrestricted shell access are incompatible with an
absolute promise that arbitrary credentials used in that session remain secret.
This is an architectural inference, not a claimed product guarantee.

| Need | Proposed approach | Boundary |
| --- | --- | --- |
| MacBook connects to Betty | 1Password SSH agent on the MacBook; install only the corresponding public key on Betty | Private SSH key need not be exported; its approved signing capability can still be used |
| Betty accesses GitHub | Dedicated narrowly authorized development key/account; use human-reviewed signing approval if an isolated signing service is available | A key/socket available in the agent session is usable authority; avoid forwarding the personal SSH agent |
| Website login | Human completes passkey/login on a trusted device or during a paused Computer Use session; prefer scoped development accounts | An authenticated browser session is itself usable authority; password masking does not establish secrecy from the same desktop/shell |
| Application API key must remain unknown to agent | Separate credential broker/proxy outside the agent account, with allowlisted destinations and operations | Service code/config and secrets must not be writable/readable by the agent; short-lived revocable capabilities still grant access |
| Ordinary development secret accepted as exposed to runtime | Restricted development credential with explicit owner approval | `op run`, `.env` mounting and output redaction do not hide values from arbitrary agent-controlled code in that runtime |

Start with SSH and human-assisted logins. Add a broker only for a concrete API
workflow requiring value secrecy. Do not install a general vault-reading MCP
server or personal-vault CLI integration in Betty's agent account.

1Password's SSH agent keeps private keys inside 1Password and supports approval
per key and per request. Prefer per-request approval for sensitive keys; do not
select approval for all applications. For any deliberately approved development
vault on Betty, use a genuinely separate account or enforced vault access, not
just a UI collection that hides other vaults.

Apply the same boundary to service credentials. An agent that controls a
container daemon can often access that daemon's mounted data and secrets;
ordinary file permissions alone do not fix that. Decide service/runtime
separation before giving the development account control over an Immich
deployment containing credentials intended to remain private.

On the human's device, require manual biometric approval, disable automatic
unlock with device and Mac-password unlock fallback where available, and lock
after the sensitive operation. Confirm actual settings on that installation.
Touch ID on an M2 mini requires a compatible Magic Keyboard with Touch ID;
the MacBook's fingerprint sensor does not become Betty's sensor. A passkey,
Touch ID and an SSH signing approval are different mechanisms. We have not
verified the user's 1Password account-passkey eligibility or a supported remote
biometric approval path for Betty; do not promise either.

1Password now documents AI-oriented integrations including placeholder-based
NVIDIA OpenShell isolation and Environments MCP. Their availability and native
macOS GUI compatibility remain unverified here. They are candidates for scoped
workflows, not established protection for unrestricted native desktop access.

## Setup order after installation

1. Finish setup, record macOS version and internal disk layout, save account
   credentials and recovery information privately. Do not assume the Recovery
   erase reclaimed Linux space; inspect first. Keep external Immich disks intact.
2. Establish the human-admin and standard-development accounts. Keep FileVault
   enabled, automatic login disabled, and recovery credentials off the agent
   desktop. Keep the display available until restart access is proven.
3. Install one Tailscale variant. Start with the vendor-recommended standalone
   app, approve its system extension and VPN configuration, and restrict tailnet
   access to the intended devices. If before-login access is required, evaluate
   the documented `tailscaled` system-service variant separately; do not assume
   the GUI variant provides it or run conflicting variants.
4. Enable System Settings > General > Sharing > Remote Login and Screen Sharing
   for intended users only. Use ordinary macOS OpenSSH over Tailscale. Avoid
   public port forwarding, public VNC, and legacy shared VNC passwords. Test
   Apple Screen Sharing from the MacBook to Betty's Tailscale address.
5. Install the MacBook's approved public SSH key on Betty, verify Betty's new
   host fingerprint through the local screen, and update the `betty` SSH alias.
   Preserve the old identity record until the new host is verified. Disable SSH
   agent forwarding. Prove key login before changing password-auth settings.
6. Clone https://github.com/wcygan/dotfiles and run `./bootstrap.sh` in the
   development account. It opens the Determinate macOS installer when Nix is
   absent. Human approves that installer; open a fresh shell and rerun bootstrap.
   Use `./bootstrap.sh install --shell-handoff` if startup-file integration is
   wanted; finish with `./bootstrap.sh verify`. Install and verify the pinned
   reusable skills from https://github.com/wcygan/agent-skills using
   `./bootstrap.sh agent-skills` and `./bootstrap.sh agent-skills --check`.
   Run these as the development user, not root. Review conflicts instead of
   overwriting unrelated skills; the dotfiles lock file chooses the revision.
7. Install the current native ChatGPT desktop app and Codex CLI. Human signs in
   to the intended account/workspace. In the development user's app, enable
   Settings > Connections > Control this Mac or PC. On the MacBook use Control
   other devices to pair Betty if available; pair the phone using the documented
   QR flow. Rollout/workspace policy can affect availability.
8. Install the native Computer Use plugin. Enable its server and skill; grant
   Accessibility and Screen Recording to Codex Computer Use in the development
   account. Approve only needed apps; exclude 1Password and human-admin tools.
   App approvals are an additional control, not a substitute for OS isolation.
   Install the official Chrome extension in the development browser if needed.
9. Set up Codex SSH projects separately through Settings > Connections. Verify
   `codex` is authenticated and on Betty's remote login-shell PATH. Do not expose
   Codex app-server listeners publicly.
10. Allow the host app to start at login and keep Betty awake for work while
    allowing the display to sleep. Verify a GUI session exists for desktop work.
    Do not disable FileVault or enable automatic login just to avoid login steps.
11. Establish scoped GitHub access and clone `betty`, private `immich-infra`,
    and requested projects. Reconcile the securely preserved live Linux source
    and configuration; no bulk restoration of old development folders is needed.

## Prove remote operation before returning Betty to a headless location

- SSH from the MacBook over Tailscale works; the development account cannot
  administer the machine without separate human authorization.
- Apple Screen Sharing shows and controls Betty's actual development desktop.
- A task started remotely through the native OpenAI app creates a test file on
  Betty; native Computer Use opens a harmless app there and verifies its state.
- An SSH project task runs in the correct checkout and can find `codex` in its
  login shell. Check private GitHub repository access without printing tokens.
- A locked personal vault is absent from the agent desktop. A scoped SSH test
  requires the configured human approval. Locking the human's vault revokes
  the intended signing access; unauthorized requests fail. Test with dummy
  credentials rather than asking the agent to display real secret values.
- If a credential broker is introduced, test that the agent cannot read its
  secrets, modify its executable/config, request arbitrary destinations/actions,
  or obtain secrets through errors or logs. Do not call it secret-blind until
  those negative tests pass. Agent-written code must not run with broker secrets.
- Restart Betty and test LAN SSH, Tailscale SSH, human screen access, app host
  availability and Computer Use separately. Test a cold boot before relying on
  unattended recovery. Retain a local recovery path if any prerequisite fails.

Apple documents FileVault unlock over SSH on Apple-silicon Macs running macOS
26 or later when Remote Login and networking are available. Verify this on
Ethernet/LAN; it does not establish that Tailscale or OpenAI's relay runs before
FileVault unlock. Keep a human-controlled LAN/subnet route if needed. Desktop
availability, OS unlock and vault unlock are separate conditions.

## Principles behind these choices

- **Boundary Discipline:** keep personal secrets and approvals outside the
  agent's desktop/account; separate admin authority from daily development.
- **Prove It Works:** remote restart, Computer Use and credential-denial checks
  are acceptance gates, not assumptions based on successful installation.

## Sources

- [OpenAI remote connections](https://learn.chatgpt.com/docs/remote-connections)
- [Native Computer Use](https://learn.chatgpt.com/docs/computer-use)
- [1Password SSH security and authorization](https://www.1password.dev/ssh/agent/security)
- [1Password environment-variable exposure](https://www.1password.dev/cli/secrets-environment-variables)
- [1Password unlock settings](https://support.1password.com/unlock-auto-lock/)
- [Touch ID hardware requirements](https://support.1password.com/touch-id-mac/)
- [1Password Security for AI](https://www.1password.dev/security-for-ai)
- [Tailscale macOS variants](https://tailscale.com/docs/concepts/macos-variants)
- [Apple Remote Login](https://support.apple.com/en-au/guide/mac-help/mchlp1066/mac)
- [Apple Platform Security, FileVault SSH unlock, page 108](https://help.apple.com/pdf/security/en_US/apple-platform-security-guide.pdf)

Live setup, application approval availability, headless display behavior, and
the credential-broker choice remain to be verified on Betty after installation.
