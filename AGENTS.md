# ball_cv agent guide

## Goal

Use `ball.md` for the product goal and CV roadmap. It is a roadmap, not a claim
that future pipeline stages or commands are already implemented.

## Architecture

- Host: Ubuntu 22.04+ (WSL2/VPS), provisioned by `host/host.yml`.
- Host owns: Git, Docker/Compose/Buildx, Codex, shell utilities.
- App runtime lives in Docker; do not install project Python deps on host.
- Container: Python 3.12 + uv + FFmpeg + OpenCV/PyTorch/Ultralytics.
- Python deps: `pyproject.toml` + committed `uv.lock`.
- Compose service: `ball-cv`; repo mounted at `/workspace`.
- Runtime mounts: `data/ -> /data`, `models/ -> /models`, `artifacts/ -> /artifacts`.
- CPU-first. Do not add CUDA/GPU setup without an explicit target/requirement.
- A 1 CPU / 2 GB VPS is for light host and maintenance tasks; run image builds,
  video processing, and model work on a workstation with adequate resources.
- The current CLI only implements `ball-cv doctor`; extraction, inference,
  evaluation, training, tracking, and S3 workflows are future work.

## Key files

- `Dockerfile`: `dev` and `runtime` images.
- `compose.yml`: dev container.
- `pyproject.toml`: Python deps/config.
- `host/host.yml`: host-only provisioning.
- `src/ball_cv/`: app code.
- `tests/`: pytest.
- `scripts/dev-start.sh`: container startup/dependency sync.
- `.env.example`: config template; `.env` is optional and contains local settings/secrets.

## Commands

Prefer Make targets:

```bash
make up       # build/start dev container
make shell    # container shell
make doctor   # runtime check
make test     # pytest
make lint     # ruff
make lock     # update uv.lock
make down
```

Direct checks when relevant:

```bash
docker compose config
docker compose build
ansible-playbook --syntax-check host/host.yml
```

## Change rules

- Keep changes minimal; solve current MVP need, not hypothetical future architecture.
- Run Python/app commands in container, not host.
- Add deps with `docker compose exec ball-cv uv add <pkg>`; commit `pyproject.toml` + `uv.lock`.
- Never commit `.env`, credentials, videos, datasets, model weights, or generated artifacts.
- Keep large/runtime files under `data/`, `models/`, `artifacts/` or external object storage.
- Commit `uv.lock`. The first dev-container startup can generate it when absent;
  review and commit it so later builds use the locked dependency graph.
- Preserve host/container boundary: host playbook must not become the Python/CV environment.
- Do not silently add services/databases/queues/cloud components. Require a concrete use case.
- Do not add GPU/CUDA until hardware/runtime target is specified.
- Prefer headless/server-safe libraries; no GUI dependency unless required.
- Update tests for behavior changes.
- Do not claim a command/build passed unless it was actually run.

## Validation

Before finishing a code change, run the smallest relevant set, normally:

```bash
make lint
make test
make doctor
```

Additionally:

- Docker/Compose change -> `docker compose config` + build if Docker is available.
- Ansible change -> `ansible-playbook --syntax-check host/host.yml`.
- Dependency change -> ensure `uv.lock` is updated and consistent.
- If Docker socket access is unavailable, report that container checks and lock
  generation could not run; do not resolve/install project dependencies on the host.

If a check cannot run, state exactly which check and why.

## Python style

- Python 3.12.
- Ruff config in `pyproject.toml`; line length 100.
- Prefer small typed functions/modules and explicit paths/config.
- Keep CLI commands under `ball-cv`; add tests for non-trivial logic.

## Project constraints

- Initial VPS is resource-constrained; do not plan model training there by default.
- Training/heavy video processing may run on workstation/GPU/cloud later.
- S3-compatible storage is planned; env fields already exist, but storage workflows are not implemented.
- Ultralytics is currently used for MVP speed; licensing must be reconsidered before a closed commercial product.
