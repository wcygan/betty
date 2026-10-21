# List supported Betty desktop harness commands.
default:
    @just --list

# Check Mac and Betty desktop prerequisites without changing state.
doctor:
    uv run --no-project scripts/betty_desktop.py doctor

# Install the macOS FreeRDP client only when it is unavailable.
install-rdp-client:
    uv run --no-project scripts/betty_desktop.py install-rdp-client

# Open the RDP client without putting credentials in shell history.
connect-rdp:
    uv run --no-project scripts/betty_desktop.py connect-rdp

# Download and checksum-verify the official RustDesk ARM64 RPM on Betty.
rustdesk-stage:
    uv run --no-project scripts/betty_desktop.py rustdesk-stage

# Verify the staged RPM and preview the remote DNF transaction.
rustdesk-preview:
    uv run --no-project scripts/betty_desktop.py rustdesk-preview

# Install the verified RustDesk RPM through an interactive remote sudo prompt.
rustdesk-install:
    uv run --no-project scripts/betty_desktop.py rustdesk-install --apply

# Check the harness behavior and justfile formatting.
check:
    uv run --no-project scripts/betty_desktop.py self-test
    uv run --no-project python -m unittest discover -s ssh-sudo -p 'test_*.py'
    just --fmt --check

# Build the pinned ARM64 PAM module in a Debian 12 container on the Mac.
ssh-sudo-build:
    #!/usr/bin/env bash
    set -euo pipefail
    docker build --platform linux/arm64 -t betty-pam-rssh:1.2.1 ssh-sudo
    mkdir -p .cache/ssh-sudo
    container=$(docker create betty-pam-rssh:1.2.1)
    trap 'docker rm "$container" >/dev/null' EXIT
    docker cp "$container:/src/target/release/libpam_rssh.so" .cache/ssh-sudo/libpam_rssh.so
    shasum -a 256 .cache/ssh-sudo/libpam_rssh.so

# Exercise real PAM/sudo and rollback in a disposable ARM64 Debian container.
ssh-sudo-container-test:
    docker build --platform linux/arm64 -f ssh-sudo/test.Dockerfile -t betty-pam-rssh-test ssh-sudo
    docker run --rm --platform linux/arm64 --mount "type=bind,source={{ justfile_directory() }}/ssh-sudo,target=/test,readonly" betty-pam-rssh-test bash /test/container-test.sh

# Inspect strict 1Password-only SSH and forwarded-agent prerequisites.
[positional-arguments]
ssh-sudo-doctor *hosts:
    uv run --no-project scripts/ssh_sudo.py doctor "$@"

# Test agent-only login, forwarding, root execution, and missing-agent denial.
[positional-arguments]
ssh-sudo-test *hosts:
    uv run --no-project scripts/ssh_sudo.py test "$@"

# Stage the module and installer without changing authentication policy.
[positional-arguments]
ssh-sudo-stage *hosts:
    uv run --no-project scripts/ssh_sudo.py stage "$@"

# Bootstrap public-key enrollment using existing recovery SSH access; retain old keys.
[positional-arguments]
ssh-sudo-enroll *hosts:
    uv run --no-project scripts/ssh_sudo.py enroll "$@"

# Select public-only 1Password identity for both hosts; back up Mac SSH config.
ssh-sudo-configure-mac:
    uv run --no-project scripts/ssh_sudo.py configure-mac

# Install with rollback on failed behavior checks; may prompt for sudo/Touch ID.
[positional-arguments]
ssh-sudo-install host:
    uv run --no-project scripts/ssh_sudo.py install "$@"
