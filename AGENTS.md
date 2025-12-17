# Repository Guidelines

## System Overview
- **Architecture**: ARM64 (aarch64) — Apple Silicon running Asahi Linux
- **OS**: Fedora 42 (Linux 6.14.2-401.asahi.fc42.aarch64+16k)
- **Purpose**: Development server for small-scale experiments and home projects
- **Role**: Non-production workload host; production (customer-facing) runs on adjacent 3-node Kubernetes cluster
- **Scope**: Testing, development, observability, and personal services

## Project Structure & Module Organization
- Root: `docker-compose.yml` defines the `netdata` service and volumes.
- Config: `.env` for local overrides, `.env.example` as the template to copy.
- Data: Docker named volumes `netdataconfig`, `netdatalib`, `netdatacache` persist service state.
- Docs: `README.md` and this guide. No app source directory in this repo.

## Build, Test, and Development Commands
- Start: `docker compose up -d` — launches Netdata bound to `TS_IP`.
- Stop: `docker compose down` — stops and removes the container (volumes kept).
- Logs: `docker compose logs -f netdata` — tails service logs.
- Validate: `docker compose config` — verifies YAML/env expansion.
- Clean volumes (destructive): `docker volume rm netdataconfig netdatalib netdatacache`.

## Coding Style & Naming Conventions
- YAML: 2‑space indentation, keys ordered logically (service → ports → volumes → restart).
- Env vars: UPPER_SNAKE_CASE in `.env`; document new vars in `.env.example` with comments.
- Services/volumes: concise, lowercase names (e.g., `netdata`, `netdatacache`).
- Comments: prefer short, actionable notes next to sensitive settings (ports, security opts).

## Testing Guidelines
- Lint (optional): run `yamllint docker-compose.yml` if available.
- Local check: `docker compose config` must succeed before committing.
- Connectivity: after `up`, visit `http://$TS_IP:19999` (binds to `127.0.0.1` if `TS_IP` unset).
- Config changes should include a brief test note in the PR description.

## Commit & Pull Request Guidelines
- Commits: use Conventional Commits (e.g., `feat: add claim envs`, `chore: tidy compose`).
- PRs: include purpose, summary of changes, any security impact (ports/caps), and test steps.
- Env changes: update `.env.example` and mention migration notes if breaking.
- Screenshots/logs: attach Netdata UI or relevant logs when troubleshooting.

## Security & Configuration Tips
- Bind cautiously: keep `TS_IP` set to a private/Tailscale IP; avoid `0.0.0.0`.
- Secrets: never commit real tokens; use commented placeholders in `.env.example`.
- Platforms: for SELinux, prefer the provided comment to adjust labels if needed.
- Cloud claim (optional): set `NETDATA_CLAIM_*` via environment, not committed files.

