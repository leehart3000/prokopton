"""Load TOML configuration files into validated Pydantic models.

Example::

    from pydantic import Field

    from prokopton.core.config import ConfigModel, load_config


    class TrainingConfig(ConfigModel):
        seed: int = 42


    class AppConfig(ConfigModel):
        name: str
        training: TrainingConfig = Field(default_factory=TrainingConfig)


    config = load_config("app.toml", AppConfig, env_prefix="MYAPP_")

With ``env_prefix="MYAPP_"``, the environment variable ``MYAPP_TRAINING__SEED=7``
overrides ``seed`` in the ``[training]`` table of ``app.toml``. A double
underscore (``__``) separates nested keys.
"""

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

__all__ = ["ENV_NESTED_DELIMITER", "ConfigError", "ConfigModel", "load_config"]

ENV_NESTED_DELIMITER = "__"
"""Separator between nested keys in environment variable names."""


class ConfigError(Exception):
    """Raised when a configuration file cannot be loaded or is invalid."""


class ConfigModel(BaseModel):
    """Base class for configuration models.

    Unknown keys are rejected, so typos in config files are caught early, and
    instances are immutable once loaded.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


def load_config[M: BaseModel](
    path: str | os.PathLike[str],
    model: type[M],
    *,
    env_prefix: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> M:
    """Load a TOML file and validate it against a Pydantic model.

    Args:
        path: Path to the TOML configuration file.
        model: The Pydantic model class to validate against.
        env_prefix: If given, environment variables starting with this prefix
            override values from the file. For example, with the prefix
            ``"MYAPP_"``, ``MYAPP_TRAINING__SEED`` overrides ``training.seed``.
        environ: Environment variables to read overrides from. Defaults to
            ``os.environ``; mainly useful for testing.

    Returns:
        A validated instance of ``model``.

    Raises:
        ConfigError: If the file is missing, is not valid TOML, or does not
            match the model.
    """
    config_path = Path(path)
    try:
        with config_path.open("rb") as file:
            data: dict[str, Any] = tomllib.load(file)
    except FileNotFoundError as error:
        msg = f"Config file not found: {config_path}"
        raise ConfigError(msg) from error
    except tomllib.TOMLDecodeError as error:
        msg = f"Invalid TOML in {config_path}: {error}"
        raise ConfigError(msg) from error

    if env_prefix is not None:
        source = os.environ if environ is None else environ
        data = _deep_merge(data, _env_overrides(env_prefix, source))

    try:
        return model.model_validate(data)
    except ValidationError as error:
        msg = f"Invalid configuration in {config_path}:\n{error}"
        raise ConfigError(msg) from error


def _env_overrides(prefix: str, environ: Mapping[str, str]) -> dict[str, Any]:
    """Build nested overrides from variables such as ``PREFIX_SECTION__KEY``."""
    upper_prefix = prefix.upper()
    overrides: dict[str, Any] = {}
    for name, value in environ.items():
        if not name.upper().startswith(upper_prefix):
            continue
        keys = name[len(prefix) :].lower().split(ENV_NESTED_DELIMITER)
        if not all(keys):
            continue
        target = overrides
        for key in keys[:-1]:
            child = target.setdefault(key, {})
            if not isinstance(child, dict):
                msg = f"Environment variable {name} conflicts with another override"
                raise ConfigError(msg)
            target = child
        if isinstance(target.get(keys[-1]), dict):
            msg = f"Environment variable {name} conflicts with another override"
            raise ConfigError(msg)
        target[keys[-1]] = value
    return overrides


def _deep_merge(
    base: Mapping[str, Any], overrides: Mapping[str, Any]
) -> dict[str, Any]:
    """Merge ``overrides`` into ``base``, combining nested tables."""
    merged = dict(base)
    for key, value in overrides.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged
