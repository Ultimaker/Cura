import importlib.util
import runpy
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


MODULE_PATH = Path(__file__).parents[2] / "packaging" / "msi" / "create_windows_msi.py"
with patch.dict(
    sys.modules,
    {
        "semver": types.SimpleNamespace(Version=object),
        "jinja2": types.SimpleNamespace(Template=object),
    },
):
    SPEC = importlib.util.spec_from_file_location("create_windows_msi", MODULE_PATH)
    msi = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(msi)


def successful_tools(command, check):
    assert check is True
    if command[0] == "heat":
        Path(command[-1]).write_text("heat", encoding="utf-8")
    elif command[0] == "candle":
        output = Path(command[command.index("-out") + 1].rstrip("\\"))
        output.mkdir(parents=True, exist_ok=True)
        for source in command[-2:]:
            (output / Path(source).with_suffix(".wixobj").name).write_bytes(b"obj")
    elif command[0] == "light":
        Path(command[command.index("-out") + 1]).write_bytes(b"msi")


@pytest.mark.parametrize("architecture", ["x64", "arm64"])
def test_build_passes_architecture_and_checks_outputs(tmp_path, architecture):
    dist = tmp_path / "payload"
    dist.mkdir()
    (tmp_path / "UltiMaker-Cura.wxs").write_text("wxs", encoding="utf-8")
    (tmp_path / "ExcludeComponents.xslt").write_text("xslt", encoding="utf-8")
    output = tmp_path / "cura.msi"
    with patch.object(msi.subprocess, "run", side_effect=successful_tools) as run:
        msi.build(dist, output, architecture)
    candle = run.call_args_list[1].args[0]
    assert candle[candle.index("-arch") + 1] == architecture
    assert all(call.kwargs["check"] is True for call in run.call_args_list)


def test_nonzero_tool_failure_propagates(tmp_path):
    with patch.object(
        msi.subprocess,
        "run",
        side_effect=subprocess.CalledProcessError(2, ["heat"]),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            msi.build(tmp_path, tmp_path / "cura.msi", "x64")


def test_success_without_output_fails(tmp_path):
    with patch.object(msi.subprocess, "run", return_value=None):
        with pytest.raises(RuntimeError, match="heat output"):
            msi.build(tmp_path, tmp_path / "cura.msi", "x64")


def test_empty_output_fails(tmp_path):
    def empty_heat(command, check):
        Path(command[-1]).touch()

    with patch.object(msi.subprocess, "run", side_effect=empty_heat):
        with pytest.raises(RuntimeError, match="heat output"):
            msi.build(tmp_path, tmp_path / "cura.msi", "arm64")


def test_success_without_candle_outputs_fails(tmp_path):
    def tools(command, check):
        if command[0] == "heat":
            Path(command[-1]).write_bytes(b"heat")

    with patch.object(msi.subprocess, "run", side_effect=tools):
        with pytest.raises(RuntimeError, match="candle application object"):
            msi.build(tmp_path, tmp_path / "cura.msi", "x64")


def test_success_without_light_output_fails(tmp_path):
    def tools(command, check):
        if command[0] == "heat":
            Path(command[-1]).write_bytes(b"heat")
        elif command[0] == "candle":
            output = Path(command[command.index("-out") + 1].rstrip("\\"))
            output.mkdir(parents=True, exist_ok=True)
            for source in command[-2:]:
                (output / Path(source).with_suffix(".wixobj").name).write_bytes(b"obj")

    with patch.object(msi.subprocess, "run", side_effect=tools):
        with pytest.raises(RuntimeError, match="MSI output"):
            msi.build(tmp_path, tmp_path / "cura.msi", "arm64")


def test_invalid_architecture_rejected(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--architecture", "sparc"])
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
    assert "invalid choice" in capsys.readouterr().err


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
