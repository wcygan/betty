# Betty remote access and Computer Use reliability

Updated 2026-10-29. This record concerns remote access and native Computer Use. The aim is reliable, secure access to the existing `rat` session, with clear recovery when a lock or restart interrupts it. It is not an always-available or unattended-reboot acceptance claim.

## Evidence

| Date / condition | Evidence and limits |
| --- | --- |
| October 29, off home network | The user reported successful SSH and Apple Screen Sharing over the phone hotspot. This is a user-observed network test, not evidence that every future connection will work. |
| October 29, supervised restart | The user reported that login was needed before the GUI session and Tailscale recovered. FileVault was separately verified on. This does not establish unattended pre-login access. ChatGPT and Tailscale are listed as login items; ChatGPT's later automatic launch has not been tested. |
| Earlier locked-use attempts | One native error explicitly reported automatic unlock paused because physical input was detected and requested manual unlock. Another reported that the Mac was locked and automatic unlock could not unlock it. The latter gave no cause; do not conflate the two failures. |
| October 29, 21:22 UTC | After the user reported manually unlocking Betty, native Calculator showed `4 + 3 = 7` and a screenshot. After issuing the lock shortcut, native Calculator showed `7 + 6 = 13` and a screenshot. The lock was not independently confirmed immediately before the second action, nor was continuous display cover observed. |
| October 29, 21:29 UTC | The user reported seeing the lock screen after the preceding test and then manually unlocked Betty. This confirms the observed later screen state, not the exact state during the earlier action. |
| October 29, 21:33–21:48 UTC | A controlled idle trial began after Calculator showed `2 + 5 = 7`; the last GUI activity was approximately 21:33:04 UTC. After more than 15 minutes without another worker using the desktop, at 21:48:28 shell access responded as `rat`, ChatGPT and Tailscale processes were present, and native Calculator showed `9 + 6 = 15`. No native error occurred. The pre-attempt lock state and physical display cover were not independently observed; elapsed time alone does not establish either. The intermittent failure was not reproduced. |
| October 29, approximately 22:22 UTC | The user confirmed Betty was locked. The single native Calculator access attempt returned: ‘The Mac is locked and automatic unlock could not unlock it. Ask the user to unlock the Mac manually before continuing.’ No Calculator action occurred. Shell access still responded as `rat` on `betty`, and ChatGPT and Tailscale processes were present. The error did not identify its cause. No retry or security change was made. |

The sanitized local timing record is `/Users/rat/Documents/Codex/2026-10-29/task/betty-idle-reliability-2026-10-29.txt`. System unified-log access was denied during earlier diagnosis. No debug-verbosity setting was found or changed, and no root cause has been established. The app's presence or shell reachability alone does not prove native GUI control works.

## Next controlled test and recovery

1. Record separately whether the network path, SSH shell, ChatGPT process, and native GUI action work. Use one harmless Calculator action and UTC timestamps; capture the exact sanitized error if it fails.
2. Test a **confirmed locked state** separately from **natural idle**. With a person present, record the observed lock screen before the native attempt and the observed screen afterward. Record whether display coverage was actually observed; do not infer it. Avoid local keyboard and pointer input during the attempt.
3. For an idle test, record the last GUI activity, leave the desktop untouched for longer than the configured display timeout, then make one attempt. Avoid periodic GUI checks or keepalives that would contaminate the interval. Repeat under controlled conditions only when useful to investigate a new observation; one success is not sustained reliability.
4. If Computer Use reports the physical-input safeguard or asks for authentication, stop retries and have the user manually unlock Betty. Do not bypass the lock or collect passwords. For a generic failure, capture permitted, bounded local diagnostics and timing; do not retry denied logs through an alternate route or publish private logs.
5. Treat reboot recovery separately. With FileVault enabled, preserve the human unlock and login route, and coordinate a supervised restart before testing post-reboot reachability, GUI login, Tailscale, ChatGPT and Computer Use as distinct stages. Do not weaken encryption, login or approval settings to make a test pass.

Readiness for the **current logged-in session** would require repeatable off-network access and native GUI actions after both an independently confirmed lock and representative idle periods, with the screen protection observed and a documented recovery path. **Unattended reboot readiness** additionally requires an explicitly chosen and tested pre-login recovery design. Neither is established by the single idle pass. The prior headless setup findings are in [macOS headless recovery findings](macos-headless-recovery-findings-2026-10-29.md).

References: [OpenAI Computer Use and Locked use](https://learn.chatgpt.com/docs/computer-use) and [remote connections](https://learn.chatgpt.com/docs/remote-connections).
