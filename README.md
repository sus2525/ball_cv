# ball_cv

Development environment and infrastructure scaffold for the `ball_cv` MVP.

`ball_cv` is intended to process football video from a fixed camera and evolve toward this pipeline:

```text
video -> frames -> field calibration -> ball detection -> tracking
      -> field coordinates -> evaluation -> retraining
```

This repository currently provides the **development/runtime foundation** for that pipeline. The CV pipeline itself is not implemented yet.

## Architecture

The environment is intentionally split into two layers:

```text
Ubuntu host (WSL2 or VPS)
├── Git
├── Docker Engine + Buildx + Compose
├── Codex CLI
└── basic shell utilities
        |
        v
Docker container: ball-cv
├── Python 3.12
├── uv
├── FFmpeg
├── OpenCV
├── PyTorch
├── Ultralytics
└── project Python dependencies
```

Rules:

- Ansible prepares the **host** only.
- Docker owns the `ball_cv` application runtime.
- Python dependencies are declared in `pyproject.toml` and locked in `uv.lock`.
- Do not install application Python packages globally on the host.
- `data/`, `models/`, and `artifacts/` are runtime directories and are not committed to Git.
- The current environment is **CPU-first**. GPU/CUDA support should be added only when a concrete GPU target is selected.

## Repository layout

```text
.
├── AGENTS.md                  # instructions/context for coding agents
├── Dockerfile                 # development and runtime images
├── compose.yml                # local development service
├── Makefile                   # common development commands
├── pyproject.toml             # Python project + dependencies
├── uv.lock                    # generated dependency lockfile; commit it
├── .env.example               # environment variable template
├── host/
│   ├── host.yml               # Ubuntu host provisioning
│   ├── inventory.local.ini    # local WSL/Ubuntu inventory
│   └── inventory.vps.example.ini
├── src/ball_cv/               # application package
├── tests/                     # tests
├── scripts/                   # development helper scripts
├── data/                      # input video/datasets; not committed
├── models/                    # model weights; not committed
└── artifacts/                 # generated outputs; not committed
```

# Quick start

If Docker and the host utilities are already installed, the shortest path is:

```bash
cp .env.example .env
docker compose up -d --build
make doctor
make test
```

Then enter the development container:

```bash
make shell
```

For a new machine, follow the full setup below.

# 1. Requirements

Supported host environment:

- Ubuntu 22.04 or newer;
- x86_64 or arm64;
- either Ubuntu in WSL2 or a normal Ubuntu VPS/VM;
- internet access for the initial provisioning/build.

The host playbook installs Docker, Git, Codex CLI, and the small utilities required for development.

Ansible itself must be available before running the playbook.

# 2. WSL2 setup

## 2.1 Install/open Ubuntu

If WSL2 + Ubuntu are already working, skip this step.

From Windows PowerShell as Administrator:

```powershell
wsl --install -d Ubuntu
```

After installation, open Ubuntu and create your Linux user.

Keep the repository in the Linux filesystem, for example:

```text
~/projects/ball_cv
```

Prefer this over `/mnt/c/...` for repositories with many video/image files.
This working copy is under `/mnt/f`; it can run, but WSL file access and Docker
bind mounts may be slower there. For video-heavy work, place the repository and
large inputs in the WSL Linux filesystem.

## 2.2 Enable systemd in WSL

Docker Engine in this setup runs directly inside Ubuntu and expects systemd.

Check it:

```bash
ps -p 1 -o comm=
```

Expected result:

```text
systemd
```

If it is not enabled, create/edit `/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Then run from Windows PowerShell:

```powershell
wsl --shutdown
```

Open Ubuntu again.

## 2.3 Install Ansible

Inside Ubuntu:

```bash
sudo apt update
sudo apt install -y ansible
```

Verify:

```bash
ansible --version
```

## 2.4 Provision the WSL host

From the repository root:

```bash
ansible-playbook \
  -i host/inventory.local.ini \
  host/host.yml \
  --ask-become-pass \
  -e "dev_user=$USER"
```

The playbook installs:

- Git;
- Docker Engine;
- Docker Buildx;
- Docker Compose plugin;
- Codex CLI;
- `curl`, `wget`, `jq`, `rg`, `fd`, `tmux`, `htop`, `tree` and related utilities.

The user is added to the `docker` group. Group membership becomes active only after a new login/session.

Close and reopen the WSL terminal, or restart WSL:

```powershell
wsl --shutdown
```

Then verify inside Ubuntu:

```bash
docker version
docker compose version
codex --version
git --version
```

Test the Docker daemon:

```bash
docker run --rm hello-world
```

# 3. Ubuntu VPS setup

You can provision a VPS remotely from WSL/Linux using the same playbook.

## 3.1 Create the inventory

Copy the example:

```bash
cp host/inventory.vps.example.ini host/inventory.vps.ini
```

Edit `host/inventory.vps.ini`:

```ini
[ball_cv]
ball-vps ansible_host=YOUR_VPS_IP ansible_user=ubuntu
```

Do not commit a private inventory containing sensitive infrastructure details unless that is intentional.

## 3.2 Check SSH/Ansible access

```bash
ansible -i host/inventory.vps.ini ball_cv -m ping
```

Expected:

```text
pong
```

## 3.3 Provision the VPS

```bash
ansible-playbook \
  -i host/inventory.vps.ini \
  host/host.yml
```

If the remote user requires a sudo password:

```bash
ansible-playbook \
  -i host/inventory.vps.ini \
  host/host.yml \
  --ask-become-pass
```

Reconnect over SSH after provisioning so the new Docker group membership is applied.

Verify:

```bash
docker version
docker compose version
codex --version
```

# 4. Configure ball_cv

From the repository root:

```bash
cp .env.example .env
```

Default configuration:

```env
BALL_CV_LOG_LEVEL=INFO
BALL_CV_DEVICE=cpu
BALL_CV_MODEL_PATH=/models/ball.pt
BALL_CV_DATA_DIR=/data
BALL_CV_MODELS_DIR=/models
BALL_CV_ARTIFACTS_DIR=/artifacts
```

Optional S3-compatible storage variables are also defined in `.env.example`:

```env
S3_ENDPOINT_URL=
S3_REGION=us-east-1
S3_BUCKET=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

`.env` is ignored by Git. Never commit real credentials.

# 5. Build and start the development environment

Run:

```bash
docker compose up -d --build
```

or:

```bash
make up
```

What happens:

1. Docker builds the development image.
2. The repository is mounted to `/workspace`.
3. `uv` synchronizes Python dependencies.
4. If `uv.lock` is missing, the first startup resolves dependencies and writes
   the lock into the repository. Review and commit that file; subsequent
   builds synchronize against the committed lock.
5. `ball_cv doctor` checks the Python/CV imports, FFmpeg, and writable runtime
   directories. It exits with an error if a required check fails.
6. The container stays running for development.

Check status:

```bash
docker compose ps
```

Check logs:

```bash
make logs
```

or:

```bash
docker compose logs -f ball-cv
```

# 6. Verify the environment

Run the environment doctor:

```bash
make doctor
```

Equivalent command:

```bash
docker compose exec ball-cv python -m ball_cv doctor
```

A healthy environment reports versions/status for at least:

- Python;
- NumPy;
- OpenCV;
- PyTorch;
- Ultralytics;
- FFmpeg;
- CUDA availability;
- configured runtime paths.

Example shape of the output:

```text
ball_cv environment
python=3.12.x
numpy=...
opencv=...
torch=...
ultralytics=...
torch_cuda_available=False
configured_device=cpu
ffmpeg=ffmpeg version ...
data_dir=/data
models_dir=/models
artifacts_dir=/artifacts
model_path=/models/ball.pt
```

# 7. Daily development workflow

Start/update the environment:

```bash
make up
```

Open a shell inside the container:

```bash
make shell
```

Run tests:

```bash
make test
```

Run linting:

```bash
make lint
```

Run environment diagnostics:

```bash
make doctor
```

Follow logs:

```bash
make logs
```

Stop containers:

```bash
make down
```

The most common commands are therefore:

```text
make up       build + start
make shell    enter container
make doctor   verify runtime
make test     run pytest
make lint     run Ruff
make logs     follow container logs
make down     stop environment
```

The current application CLI only implements `ball-cv doctor`. Video extraction,
detection/inference, tracking, calibration, evaluation, training, and S3 workflows
are not implemented yet; roadmap items in `ball.md` should not be treated as
available commands.

# 8. Python dependencies

Do not use host-level `pip install` for project dependencies.

Add a runtime dependency from inside the running container:

```bash
docker compose exec ball-cv uv add PACKAGE_NAME
```

Example:

```bash
docker compose exec ball-cv uv add supervision
```

This updates:

```text
pyproject.toml
uv.lock
```

Commit both files.

If only `pyproject.toml` was edited manually, update the lockfile:

```bash
make lock
```

After dependency changes, rebuild the image:

```bash
make build
```

or:

```bash
docker compose up -d --build
```

## Why both Docker and uv?

They solve different layers:

```text
Docker
└── OS/runtime dependencies
    ├── Python
    ├── FFmpeg
    └── system libraries

uv
└── Python dependency graph
    ├── NumPy
    ├── OpenCV
    ├── PyTorch
    ├── Ultralytics
    └── application libraries
```

# 9. Working with data, models, and outputs

The Compose service mounts these host directories:

```text
./data       -> /data
./models     -> /models
./artifacts  -> /artifacts
```

Use them as follows:

- `data/` — source video, extracted frames, datasets;
- `models/` — model weights and exported models;
- `artifacts/` — generated videos, detection/tracking output, reports and other results.

Example:

```text
host:      ./data/videos/match_001.mp4
container: /data/videos/match_001.mp4
```

The contents of these directories are ignored by Git. Only `.gitkeep` files are committed.

Large videos, datasets, model weights and generated artifacts should not be committed to the repository. The intended next storage layer is S3-compatible object storage.

The 1 CPU / 2 GB VPS described in `ball.md` is for light host maintenance. Build
the ML image and process video on a workstation with enough memory and disk; do
not plan training or large video processing on that VPS.

# 10. Running commands inside the container

General pattern:

```bash
docker compose exec ball-cv COMMAND
```

Examples:

```bash
docker compose exec ball-cv python --version
docker compose exec ball-cv uv --version
docker compose exec ball-cv ffmpeg -version
docker compose exec ball-cv pytest
docker compose exec ball-cv ruff check .
```

The `ball-cv` CLI currently exposes the environment doctor:

```bash
docker compose exec ball-cv ball-cv doctor
```

More commands will be added as the video/detection/tracking pipeline is implemented.

# 11. Runtime image

The Dockerfile has separate `dev` and `runtime` targets.

Development uses the Compose `dev` target with tests, Ruff, bind mounts and an interactive container.

To build the smaller runtime target:

```bash
docker build --target runtime -t ball-cv:runtime .
```

Run it:

```bash
docker run --rm ball-cv:runtime
```

At the current stage its default command runs the environment doctor. Application runtime commands will replace this as the MVP pipeline is implemented.

# 12. Using Codex / coding agents

`AGENTS.md` in the repository root contains the persistent technical context and working rules for coding agents.

Start Codex from the repository root so it sees the correct project context:

```bash
cd ~/projects/ball_cv
codex
```

When giving a task, describe the desired change and acceptance criteria rather than repeating the whole repository architecture; the persistent rules are already in `AGENTS.md`.

Example task:

```text
Implement video frame extraction from /data/videos/input.mp4.
Store frames under /artifacts/frames.
Add tests for path handling and run lint/tests.
```

# 13. Troubleshooting

## Docker: permission denied

Example:

```text
permission denied while trying to connect to the Docker daemon socket
```

The current shell probably does not have the new `docker` group membership yet.

Check:

```bash
groups
```

If `docker` is missing, start a new login session. In WSL, the simple option is:

```powershell
wsl --shutdown
```

Then reopen Ubuntu.

## Docker daemon is not running in WSL

Check:

```bash
systemctl status docker
```

and:

```bash
ps -p 1 -o comm=
```

If PID 1 is not `systemd`, enable systemd as described in the WSL setup section.

## `.env` is missing

Create it from the template:

```bash
cp .env.example .env
```

## Python package is missing

Do not install it on the host.

Add it to the project:

```bash
docker compose exec ball-cv uv add PACKAGE_NAME
```

## Dependency state is inconsistent

Inside the running environment:

```bash
docker compose exec ball-cv uv sync --locked --group dev
```

If dependencies intentionally changed, regenerate the lock first:

```bash
make lock
```

## Rebuild everything after Docker/dependency changes

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
make doctor
make test
```

Use `--no-cache` only for troubleshooting; normal development should use Docker's build cache.

# 14. Validation before committing

For normal Python changes:

```bash
make lint
make test
make doctor
```

For Docker/Compose changes also run:

```bash
docker compose config
docker compose build
```

For host Ansible changes:

```bash
ansible-playbook --syntax-check host/host.yml
```

If the change affects host behavior, test the playbook on the intended Ubuntu/WSL host before relying on it.

# Current scope and next steps

Current repository scope:

- reproducible host bootstrap;
- reproducible CPU-first Python/CV environment;
- Docker-based development workflow;
- basic environment diagnostics and smoke tests;
- placeholders for video/data/model/artifact storage.

Not implemented yet:

- video ingestion pipeline;
- frame extraction pipeline;
- football field calibration;
- ball detector workflow;
- tracking;
- conversion to field coordinates;
- evaluation/retraining pipeline;
- GPU/CUDA image/profile;
- production deployment/orchestration.

These should be added incrementally rather than pre-building infrastructure before the MVP requires it.

## Licensing note

The current MVP dependency set uses `ultralytics-opencv-headless` for a fast headless YOLO workflow. Ultralytics is distributed under AGPL-3.0 with a separate commercial/enterprise licensing option.

Before using this stack for a closed commercial product or service, explicitly review the licensing requirements or replace the detector/training stack.
