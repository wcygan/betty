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
    just --fmt --check
