import importlib.util
import runpy
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


MODULE_PATH = Path(__file__).parents[2] / "packaging" / "NSIS" / "create_windows_installer.py"
with patch.dict(
    sys.modules,
    {
        "semver": types.SimpleNamespace(Version=object),
        "jinja2": types.SimpleNamespace(Template=object),
    },
):
    SPEC = importlib.util.spec_from_file_location("create_windows_installer", MODULE_PATH)
    installer = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(installer)


def test_build_uses_check_and_requires_nonempty_output(tmp_path):
    (tmp_path / "UltiMaker-Cura.nsi").write_text("nsi", encoding="utf-8")

    def successful(command, check, cwd):
        assert check is True
        assert cwd == tmp_path
        (tmp_path / "cura.exe").write_bytes(b"exe")

    with patch.object(installer.subprocess, "run", side_effect=successful) as run:
        installer.build(str(tmp_path), "cura.exe")
    assert run.call_args.kwargs["check"] is True
    assert run.call_args.kwargs["cwd"] == tmp_path


def test_nonzero_tool_failure_propagates(tmp_path):
    with patch.object(
        installer.subprocess,
        "run",
        side_effect=subprocess.CalledProcessError(1, ["makensis"]),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            installer.build(str(tmp_path), "cura.exe")


def test_cli_requires_packaging_inputs(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH)])
    with patch.dict(
        sys.modules,
        {
            "semver": types.SimpleNamespace(Version=object),
            "jinja2": types.SimpleNamespace(Template=object),
        },
    ):
        with pytest.raises(SystemExit) as error:
            runpy.run_path(str(MODULE_PATH), run_name="__main__")
    assert error.value.code == 2
    assert "required" in capsys.readouterr().err


@pytest.mark.parametrize("empty", [False, True])
def test_success_with_missing_or_empty_output_fails(tmp_path, empty):
    (tmp_path / "UltiMaker-Cura.nsi").write_text("nsi", encoding="utf-8")
    if empty:
        (tmp_path / "cura.exe").touch()
    with patch.object(installer.subprocess, "run", return_value=None):
        with pytest.raises(RuntimeError, match="not created or is empty"):
            installer.build(str(tmp_path), "cura.exe")
