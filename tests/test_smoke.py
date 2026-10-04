from pathlib import Path

from ball_cv.config import Settings
from ball_cv.doctor import _check_runtime_directories


def test_settings_have_runtime_directories() -> None:
    settings = Settings()
    assert str(settings.data_dir)
    assert str(settings.models_dir)
    assert str(settings.artifacts_dir)


def test_runtime_directories_must_exist(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    assert _check_runtime_directories((missing,)) == [f"{missing}: directory is missing"]


def test_runtime_directories_must_be_writable(tmp_path: Path, monkeypatch) -> None:
    directory = tmp_path / "runtime"
    directory.mkdir()
    monkeypatch.setattr("ball_cv.doctor.os.access", lambda *_args: False)

    assert _check_runtime_directories((directory,)) == [
        f"{directory}: directory is not writable"
    ]
