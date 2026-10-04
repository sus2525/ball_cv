from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    log_level: str = os.getenv("BALL_CV_LOG_LEVEL", "INFO")
    device: str = os.getenv("BALL_CV_DEVICE", "cpu")
    model_path: Path = Path(os.getenv("BALL_CV_MODEL_PATH", "/models/ball.pt"))
    data_dir: Path = Path(os.getenv("BALL_CV_DATA_DIR", "/data"))
    models_dir: Path = Path(os.getenv("BALL_CV_MODELS_DIR", "/models"))
    artifacts_dir: Path = Path(os.getenv("BALL_CV_ARTIFACTS_DIR", "/artifacts"))
    s3_endpoint_url: str | None = os.getenv("S3_ENDPOINT_URL") or None
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_bucket: str | None = os.getenv("S3_BUCKET") or None
