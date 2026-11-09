"""Tests for prokopton.core.config."""

from pathlib import Path

import pytest
from pydantic import Field, ValidationError

from prokopton.core.config import ConfigError, ConfigModel, load_config


class TrainingConfig(ConfigModel):
    seed: int = 42
    test_size: float = 0.2


class AppConfig(ConfigModel):
    name: str
    training: TrainingConfig = Field(default_factory=TrainingConfig)


def write_toml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_valid_file(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n\n[training]\nseed = 7\n')

    config = load_config(path, AppConfig)

    assert config.name == "demo"
    assert config.training.seed == 7
    assert config.training.test_size == 0.2


def test_uses_defaults_for_missing_tables(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n')

    config = load_config(path, AppConfig)

    assert config.training == TrainingConfig()


def test_accepts_string_path(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n')

    assert load_config(str(path), AppConfig).name == "demo"


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "missing.toml", AppConfig)


def test_invalid_toml_raises_config_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, "name = \n")

    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_config(path, AppConfig)


def test_wrong_type_raises_config_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n\n[training]\nseed = "abc"\n')

    with pytest.raises(ConfigError, match="Invalid configuration"):
        load_config(path, AppConfig)


def test_unknown_key_raises_config_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\nnmae = "typo"\n')

    with pytest.raises(ConfigError, match="nmae"):
        load_config(path, AppConfig)


def test_config_is_immutable(tmp_path: Path) -> None:
    config = load_config(write_toml(tmp_path, 'name = "demo"\n'), AppConfig)

    with pytest.raises(ValidationError):
        config.name = "changed"  # type: ignore[misc]


def test_env_overrides_nested_value(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n\n[training]\nseed = 7\n')
    environ = {"MYAPP_TRAINING__SEED": "99", "MYAPP_NAME": "from-env"}

    config = load_config(path, AppConfig, env_prefix="MYAPP_", environ=environ)

    assert config.name == "from-env"
    assert config.training.seed == 99
    assert config.training.test_size == 0.2


def test_env_ignored_without_prefix(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n')
    environ = {"MYAPP_NAME": "from-env"}

    config = load_config(path, AppConfig, environ=environ)

    assert config.name == "demo"


def test_env_ignores_other_prefixes(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n')
    environ = {"OTHER_NAME": "from-env", "MYAPP_": "empty-key"}

    config = load_config(path, AppConfig, env_prefix="MYAPP_", environ=environ)

    assert config.name == "demo"


@pytest.mark.parametrize(
    "environ",
    [
        {"MYAPP_TRAINING": "x", "MYAPP_TRAINING__SEED": "1"},
        {"MYAPP_TRAINING__SEED": "1", "MYAPP_TRAINING": "x"},
    ],
    ids=["parent-first", "child-first"],
)
def test_conflicting_env_overrides_raise_config_error(
    tmp_path: Path, environ: dict[str, str]
) -> None:
    path = write_toml(tmp_path, 'name = "demo"\n')

    with pytest.raises(ConfigError, match="conflicts"):
        load_config(path, AppConfig, env_prefix="MYAPP_", environ=environ)
