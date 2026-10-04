# ball_cv

## Goal

`ball_cv` — MVP computer vision системы для определения положения футбольного мяча на площадке по видео с **одной фиксированной камеры**.

Главная задача:

```text
video
→ frames
→ field calibration
→ ball detection
→ tracking
→ pixel coordinates
→ field coordinates
→ evaluation
→ retraining
```

Цель MVP — не production-система, а воспроизводимый экспериментальный pipeline, позволяющий быстро проверять качество детекции мяча на реальном видео.

## Constraints

- 1 developer + AI coding agents.
- GitHub repository.
- VPS: 1 CPU / 2 GB RAM — только лёгкие служебные задачи, не ML training.
- Основные вычисления: локальный PC/laptop или временный cloud GPU.
- Видео важнее realtime stream.
- Одна фиксированная камера.
- Ручная калибровка поля допустима.
- Простота важнее масштабируемости.

Не использовать без необходимости:

- Kubernetes;
- microservices;
- Airflow / Kubeflow;
- distributed ML;
- собственную agent platform;
- сложный MLOps stack.

---

# Roadmap

## Stage 1 — Infrastructure

Подготовить минимальное воспроизводимое окружение для разработки и первого
покадрового baseline.

### Реализовано сейчас

- Docker Compose dev-контейнер: Python 3.12, `uv`, FFmpeg и headless CV/ML зависимости.
- PyTorch/torchvision устанавливаются из CPU-only индекса; GPU/CUDA не настраивается.
- CLI: `ball-cv doctor` и `ball-cv track-video`.
- `track-video` декодирует пользовательское видео, выполняет YOLO детекцию на каждом
  кадре, связывает один объект простым предсказанием движения и пишет JSONL плюс MP4
  с наложением.
- Make-команды: `up`, `down`, `build`, `logs`, `shell`, `doctor`, `track`, `test`,
  `lint`, `lock`.
- S3-переменные описаны, но загрузка/выгрузка в object storage не реализована.
- `uv.lock` должен быть сгенерирован первым запуском контейнера и добавлен в Git.
- Первый трекер — стартовая эвристика, качество детектора и точность траектории
  на реальном видео ещё не измерены.

`make extract`, `make infer`, `make evaluate`, `make train` и `make setup` пока не
реализованы. Кадры пользователь подготавливает и размечает самостоятельно; `track-video`
декодирует кадры на лету и не сохраняет их отдельным набором.

Первый запуск после клонирования:

```bash
cp .env.example .env   # необязательно, если устраивают значения по умолчанию
make up                # первый build и запуск могут занять время
make doctor
make test
make lint
```

Положить собственные веса в `models/ball.pt`, видео в `data/videos/`, затем:

```bash
make track VIDEO=/data/videos/match.mp4 ARGS="--class-id 0"
```

Результаты появятся в `artifacts/match/`: `tracking.jsonl` и `overlay.mp4`.
Уточнить `--class-id` по меткам конкретной модели. Если модель одноклассовая,
ID часто равен `0`, но это нужно проверить по выбранным весам.

Нужно:

```text
GitHub
↓
Python project
↓
local development environment
↓
tests + evaluation
↓
object storage
↓
optional GPU runner
```

Основные компоненты:

- Python 3.12.
- `uv` + `pyproject.toml` + `uv.lock`.
- Ruff.
- Pytest.
- Pyright для собственного кода.
- GitHub Actions для lint/tests.
- S3-compatible storage для видео, datasets, weights и results.
- Docker только там, где требуется изоляция ML dependencies.
- CLI / Makefile как единый интерфейс запуска pipeline.

Целевые команды следующих этапов:

```bash
make setup
make lint
make test
make extract
make infer
make evaluate
make train
```

Этот список — целевой интерфейс roadmap. См. «Реализовано сейчас» для команд,
которые уже доступны в репозитории.

Pipeline — это код проекта, а не отдельный orchestration service.

Он должен одинаково запускаться:

```text
local PC
GPU PC
cloud GPU
```

---

## Stage 2 — Field Calibration

Для MVP **не обучать модель распознавать поле**.

Камера фиксированная, поэтому используется ручная calibration.

Процесс:

```text
frame
↓
manual selection of known field points
↓
pixel coordinates
+
known field coordinates
↓
OpenCV homography
↓
pixel → field coordinates
```

Использовать:

- OpenCV;
- `cv2.findHomography`;
- JSON calibration file.

Пример:

```text
pixel (x, y)
→
field (x_meters, y_meters)
```

Если камера не двигается, calibration выполняется один раз.

Автоматическое распознавание линий поля — не часть первого MVP.

---

## Stage 3 — Ball Detection

Главная ML-задача:

```text
frame/video
→
ball position
```

Сначала проверить готовые pretrained models. Текущая команда `track-video` уже
умеет загружать предоставленные YOLO weights, но репозиторий не выбирает и не
скачивает веса автоматически. Для первого запуска пользователь предоставляет
видео и совместимую модель.

Первый feasibility dataset:

```text
~200 annotated frames
```

Использовать несколько последовательных сложных эпизодов:

- мяч далеко;
- обычная игра;
- быстрый мяч / blur;
- occlusion;
- кадры без мяча.

Разметка выполняется пользователем отдельно; проект не создаёт и не редактирует
исходные видео, кадры или annotations. Для измерения качества нужны annotations.

Формат разметки:

```text
class: ball
annotation: bounding box
```

Инструмент:

```text
CVAT
```

Ground truth должен позволять получить:

```text
ball center x,y
ball width/height
visible / not visible
```

Особенно важно измерить реальный размер мяча в пикселях.

---

## Detector Baseline

Перед собственным training проверить готовые модели:

1. WASB Soccer pretrained.
2. FootAndBall pretrained.
3. Generic detector baseline позже:
   - RF-DETR;
   - YOLO-family benchmark.

Все модели приводить к общему результату:

```json
{
  "frame": "...",
  "visible": true,
  "x": 1000,
  "y": 500,
  "confidence": 0.93
}
```

Не выбирать архитектуру только по COCO mAP.

Для проекта важны:

- small object recall;
- false positives;
- motion blur;
- occlusion;
- video consistency;
- latency;
- resolution requirements.

Если generic detector и sports-ball detector дают разные результаты:

```text
UNKNOWN — requires experiment
```

Решение принимается по evaluation на нашем видео.

---

## Stage 4 — Training

Training начинается только после первого pretrained benchmark.

Dataset:

```text
raw video
→ selected frames
→ CVAT annotation
→ dataset v001
→ train
→ evaluate
→ failure analysis
→ dataset v002
```

Обучение выполняется:

- локально при наличии NVIDIA GPU;
- либо на временной cloud GPU.

VPS с 1 CPU и 2 GB RAM предназначен для лёгких host-задач. Не выполняйте там
сборку ML-образа, обработку больших видео или обучение; используйте workstation
с достаточной памятью и диском.

VPS 1 CPU / 2 GB не использовать для training.

Не вводить MLflow, W&B или DVC, пока они не решают конкретную проблему.

---

## Stage 5 — Tracking

Текущая команда уже включает минимальный temporal association для получения
первой визуальной траектории. После проверки на пользовательском видео сравнить
результат с annotations и улучшать детектор/ассоциацию только по измерениям.

Так как интересует один объект:

```text
0 or 1 ball
```

текущий baseline:

```text
detector
→ confidence filtering
→ temporal gating
→ constant-velocity prediction + nearest-center association
```

Параметры `--max-distance` (пиксели) и `--max-gap` (число пропущенных кадров)
зависят от разрешения и движения в кадре; настроить их после первого прогона.
Этот алгоритм не решает сложные окклюзии или неоднозначные переключения между
кандидатами. Не использовать ReID / DeepSORT без необходимости.

---

## Stage 6 — Coordinates

После detection/tracking:

```text
ball pixel center
↓
homography
↓
field x,y
```

Результат каждого кадра:

```json
{
  "frame": 100,
  "ball_visible": true,
  "pixel": [1240, 680],
  "field": [21.3, 8.7],
  "confidence": 0.91
}
```

---

# Evaluation

Evaluation обязательна для каждого изменения detector/tracker.

Минимальные метрики:

```text
precision
recall
detection rate
false positives
pixel error
field coordinate error
latency
FPS
```

Результат:

```text
metrics.json
```

Будущая команда:

```bash
make evaluate
```

Утверждение AI agent о том, что модель «стала лучше», не считается доказательством.

Улучшение должно подтверждаться evaluation.

---

# Storage

Git хранит:

```text
source code
configs
tests
evaluation code
dataset manifests
calibration metadata
small annotations
docs
```

Object storage хранит:

```text
videos
frames
datasets
model weights
predictions
training artifacts
evaluation artifacts
```

Не хранить большие бинарные данные в Git.

---

# AI Agent Rules

Agent должен:

1. понимать текущий stage roadmap;
2. выбирать минимальное решение;
3. не добавлять инфраструктуру без текущей необходимости;
4. сохранять reproducibility;
5. запускать tests после изменений;
6. запускать evaluation после изменений CV/ML logic;
7. не менять model baseline без измеримого сравнения;
8. не утверждать качество модели без metrics;
9. сохранять совместимость CLI;
10. избегать provider-specific architecture без необходимости.

Перед завершением задачи agent должен проверить:

```bash
make lint
make test
```

Для CV/ML изменений дополнительно:

```bash
make evaluate
```

---

# MVP Success Criterion

Первый вертикальный срез готов, когда система может:

```text
take user-provided video and model weights
→ detect a candidate ball per frame
→ maintain a basic single-object trajectory
→ save frame-indexed JSONL and an annotated video
```

Полный MVP считается рабочим, когда дополнительно выполнены:

```text
take real football video
→ detect ball
→ maintain basic trajectory
→ convert detection to field coordinates
→ save predictions
→ calculate deterministic metrics
```

Не требуется:

```text
frontend
realtime production inference
multi-camera
automatic field recognition
production scaling
perfect accuracy
```

Главная цель — получить **измеримый baseline на реальном видео**, после которого можно итеративно улучшать dataset, detector и tracking.
