import pytest
from pydantic import ValidationError
from app.conf_procss_pydantic import Config


def test_config_with_default_values():
    config = Config(_env_file=None, width=20,
                    height=10, entry=(0, 0), exit=(19, 9))
    assert config.width == 20
    assert config.height == 10
    assert config.entry == (0, 0)
    assert config.exit == (19, 9)
    assert config.perfect is True
    assert config.seed is None
    assert config.algorithm is None


def test_config_invalid_width():
    for invalid_width in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=invalid_width,
                   height=10, entry=(0, 0), exit=(19, 9))


def test_config_invalid_height():
    for invalid_height in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=invalid_height, entry=(0, 0), exit=(19, 9))


def test_config_invalid_entry():
    for invalid_entry in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=10, entry=invalid_entry, exit=(19, 9))


def test_config_invalid_exit():
    for invalid_exit in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=10, entry=(0, 0), exit=invalid_exit)


def test_config_invalid_perfect():
    for invalid_perfect in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=10, entry=(0, 0), exit=(19, 9),
                   perfect=invalid_perfect)


def test_config_invalid_seed():
    for invalid_seed in ["invalid", 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20, height=10,
                   entry=(0, 0), exit=(19, 9), seed=invalid_seed)


def test_config_invalid_algorithm():
    assert Config(_env_file=None, width=20, height=10, entry=(0, 0),
                  exit=(19, 9), algorithm="").algorithm is None

    assert Config(_env_file=None, width=20, height=10, entry=(0, 0),
                  exit=(19, 9), algorithm="   ").algorithm is None

    assert Config(_env_file=None, width=20, height=10, entry=(0, 0),
                  exit=(19, 9), algorithm=None).algorithm is None

    assert Config(_env_file=None, width=20, height=10, entry=(0, 0),
                  exit=(19, 9),
                  algorithm="algorithm  space").algorithm == "algorithm space"

    for invalid_algorithm in [{"key": "value"}, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20, height=10, entry=(0, 0),
                   exit=(19, 9), algorithm=invalid_algorithm)
