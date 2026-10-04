# ball_cv agent guide

## Product goal

Use `ball.md` for the product goal and roadmap. Current scope is a reproducible
CPU-first baseline that takes a user-provided fixed-camera football video,
detects one ball per frame, associates detections over time, and saves reviewable
outputs. Roadmap items are not implemented unless listed below.

## Architecture and boundaries

- Host: Ubuntu 22.04+ (WSL2/VPS), provisioned by `host/host.yml`.
- Host owns Git, Docker/Compose/Buildx, Codex, and shell utilities.
- App runtime and Python dependencies live in Docker; do not install project
  Python dependencies on the host.
- Container: Python 3.12, uv, FFmpeg, OpenCV, CPU PyTorch, and Ultralytics.
- Dependencies are declared in `pyproject.toml` and pinned in committed `uv.lock`.
- Compose service: `ball-cv`; repo mounted at `/workspace`.
- Runtime mounts: `data/ -> /data`, `models/ -> /models`, `artifacts/ -> /artifacts`.
- CPU-first. Do not add CUDA/GPU setup without an explicit target/requirement.
- A 1 CPU / 2 GB VPS is for light host maintenance. Build images and process
  video on a workstation with adequate resources.
- Do not add services, databases, queues, cloud components, or orchestration
  without a concrete use case.

## Implemented CLI

- `ball-cv doctor` checks the runtime and writable mount directories.
- `ball-cv track-video VIDEO` runs YOLO on each decoded frame, associates one
  detection using a simple constant-velocity nearest-center tracker, and writes
  `tracking.jsonl` plus `overlay.mp4`.
- `track-video` is a starter baseline, not a validated sports-ball detector.
  Calibration, evaluation metrics, training, and S3 workflows remain future work.
- Model weights are supplied by the user at `models/ball.pt` or via `--model`.
  Never silently download weights. For multi-class weights, pass `--class-id`.
- Do not create, edit, inspect, or commit user videos, frames, annotations, or
  model weights unless explicitly requested. Use synthetic fixtures in tests.

## Key files

- `Dockerfile`: development and runtime images.
- `compose.yml`: development service and runtime mounts.
- `pyproject.toml`, `uv.lock`: Python dependencies and lock.
- `src/ball_cv/video_tracking.py`: video inference and output writing.
- `src/ball_cv/tracking.py`: single-object detection association.
- `src/ball_cv/`: application and CLI code.
- `tests/`: synthetic tests; do not require user data or downloaded weights.
- `scripts/dev-start.sh`: container startup, dependency sync, and doctor.
- `.env.example`: configuration template; `.env` is local and ignored.

## Commands

Prefer Make targets:

```bash
make up
make doctor
make track VIDEO=/data/videos/match.mp4 ARGS="--class-id 0"
make test
make lint
make shell
make down
```

Direct checks when relevant:

```bash
docker compose config
docker compose build
ansible-playbook --syntax-check host/host.yml
```

Run project Python/app commands in the container. Add dependencies with
`docker compose exec ball-cv uv add <pkg>`; keep `pyproject.toml` and `uv.lock`
in sync. Preserve the CPU-only PyTorch index unless the user gives a GPU target.

## Agent collaboration

- The lead agent owns the task plan, interfaces, and integration.
- Delegate bounded work with explicit file ownership, acceptance criteria, and
  required validation commands.
- Avoid parallel edits to the same files; use separate branches/worktrees for
  independent multi-file changes and review before merging.
- Useful roles are infrastructure/reproducibility, video pipeline, detector and
  license research, tracking/evaluation, and final reviewer. Use only the roles
  needed for the current milestone.
- There is no project-specific CV skill installed. Read this file and `ball.md`
  for project context; do not invent requirements from future roadmap sections.

## Change and validation rules

- Keep changes minimal and tied to the current MVP need.
- Never commit `.env`, credentials, videos, datasets, model weights, or generated
  artifacts. Keep runtime files under `data/`, `models/`, `artifacts/` or object
  storage; those directories are ignored except `.gitkeep`.
- Preserve the host/container boundary and headless/server-safe dependencies.
- Update tests for behavior changes. Do not claim quality improvement without
  measured evaluation on user-provided annotations.
- Before finishing, run `make lint`, `make test`, and `make doctor` when the
  container is available. Docker changes also require Compose config and build;
  dependency changes require a consistent committed lockfile.
- If a check cannot run, state which command failed and why. Do not resolve or
  install project dependencies on the host.

## Project constraints

- The first tracking association assumes one ball and uses pixel-distance
  thresholds; the threshold depends on input resolution and should be tuned on
  user video. Do not describe it as robust occlusion handling.
- Training/heavy processing belongs on a suitable workstation or cloud runner,
  not the initial resource-constrained VPS.
- Ultralytics licensing must be reviewed before any closed commercial use.
